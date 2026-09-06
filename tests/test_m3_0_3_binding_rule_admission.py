from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    AdmittedBindingRule,
    BindingInputRole,
    BindingRule,
    BindingRuleAdmissionAttribution,
    BindingRuleAdmissionFrontierKind,
    BindingRuleProposalAttribution,
    BindingSelectionMode,
    BindingSelectionPolicy,
    CandidateBindingRule,
    ContextEnvelope,
    IntentExpression,
    IntentRequest,
    InterchangeableChoicePolicy,
    OriginAttribution,
    OriginKind,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    SymbolicReference,
    ValidationError,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
    WorkSymbolicInput,
    orchestrate_binding_rule_admission,
    orchestrate_work_binding,
)


def _id(character: str) -> RecordIdentity:
    return RecordIdentity(algorithm="sha256", digest=character * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace=namespace, value=value)


def _symbolic(label: str = "main") -> SymbolicReference:
    return SymbolicReference(
        resolved_intent_identity=_id("1" if label == "main" else "2"),
        slot_ref=_ref("irr.slot", f"selected-report:{label}"),
        semantic_type="artifact.path",
        selection_scope=f"reports:{label}",
        description="The exact report artifact required by the admitted work plan.",
    )


def _rule(
    symbolic: SymbolicReference,
    *,
    label: str = "main",
    interchangeable: bool = False,
) -> BindingRule:
    policy = (
        BindingSelectionPolicy(
            mode=BindingSelectionMode.ANY_INTERCHANGEABLE,
            interchangeable_choice=InterchangeableChoicePolicy.CANONICAL_IDENTITY_MIN,
        )
        if interchangeable
        else BindingSelectionPolicy(mode=BindingSelectionMode.REQUIRE_UNIQUE)
    )
    return BindingRule(
        resolved_intent_identity=symbolic.resolved_intent_identity,
        rule_ref=_ref("irr.binding_rule", label),
        symbolic_reference=symbolic,
        allowed_input_roles=(BindingInputRole.CONTEXT,),
        allowed_source_refs=(_ref("hde.binding_source", "reviewed-context"),),
        allowed_source_identities=(_id("3"),),
        input_semantic_type=symbolic.semantic_type,
        required_selection_scope=symbolic.selection_scope,
        constraints=(),
        selection_policy=policy,
        description="Use exact reviewed context material for this symbolic slot.",
    )


def _candidate(
    symbolic: SymbolicReference,
    *,
    label: str = "main",
    rule: BindingRule | None = None,
    rationale: str = "This exact slot requires the proposed bounded rule.",
) -> CandidateBindingRule:
    return CandidateBindingRule(
        attribution=BindingRuleProposalAttribution(
            proposer_ref=_ref("irr.binding_rule_proposer", f"planner:{label}"),
            proposal_event_ref=_ref(
                "irr.binding_rule_proposal",
                f"proposal:{label}",
            ),
        ),
        rule=_rule(symbolic, label=label) if rule is None else rule,
        rationale=rationale,
    )


def _admission(label: str = "main") -> BindingRuleAdmissionAttribution:
    return BindingRuleAdmissionAttribution(
        resolver_ref=_ref("irr.binding_rule_resolver", "m3.0.3-test"),
        admission_event_ref=_ref("irr.binding_rule_admission", f"admission:{label}"),
    )


def _admit_exact(symbolic: SymbolicReference, candidate: CandidateBindingRule):
    attribution = _admission()

    def admitter(target, candidates, supplied_attribution):
        assert target == symbolic
        return AdmittedBindingRule(
            admission_attribution=supplied_attribution,
            rule=candidates[0].rule,
            candidate_inputs=candidates,
        )

    return orchestrate_binding_rule_admission(
        symbolic,
        candidate_inputs=(candidate,),
        admitter=admitter,
        admission_attribution=attribution,
    )


def test_canonical_records_round_trip() -> None:
    symbolic = _symbolic()
    candidate = _candidate(symbolic)
    admitted = AdmittedBindingRule(
        admission_attribution=_admission(),
        rule=candidate.rule,
        candidate_inputs=(candidate,),
    )

    assert (
        BindingRuleProposalAttribution.from_json_bytes(
            candidate.attribution.canonical_bytes()
        )
        == candidate.attribution
    )
    assert CandidateBindingRule.from_json_bytes(candidate.canonical_bytes()) == candidate
    assert (
        BindingRuleAdmissionAttribution.from_json_bytes(
            admitted.admission_attribution.canonical_bytes()
        )
        == admitted.admission_attribution
    )
    assert AdmittedBindingRule.from_json_bytes(admitted.canonical_bytes()) == admitted


def test_no_candidates_requires_proposal_input() -> None:
    frontier = orchestrate_binding_rule_admission(_symbolic())
    assert frontier.kind is BindingRuleAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
    assert frontier.candidate_inputs == ()
    assert frontier.admitted_rule is None
    assert not hasattr(frontier, "identity")
    assert not hasattr(frontier, "canonical_bytes")


def test_same_exact_rule_with_different_provenance_is_not_voting() -> None:
    symbolic = _symbolic()
    rule = _rule(symbolic)
    first = _candidate(symbolic, label="a", rule=rule, rationale="Explanation A.")
    second = _candidate(symbolic, label="b", rule=rule, rationale="Explanation B.")

    frontier = orchestrate_binding_rule_admission(
        symbolic,
        candidate_inputs=(second, first),
    )

    assert frontier.kind is BindingRuleAdmissionFrontierKind.ADMISSION_REQUIRED
    assert frontier.admitted_rule is None
    assert {item.identity for item in frontier.candidate_inputs} == {
        first.identity,
        second.identity,
    }


def test_distinct_rule_semantics_require_adjudication() -> None:
    symbolic = _symbolic()
    first = _candidate(symbolic, label="unique")
    second = _candidate(
        symbolic,
        label="interchangeable",
        rule=_rule(symbolic, label="interchangeable", interchangeable=True),
    )

    frontier = orchestrate_binding_rule_admission(
        symbolic,
        candidate_inputs=(first, second),
    )
    assert frontier.kind is BindingRuleAdmissionFrontierKind.ADJUDICATION_REQUIRED
    assert frontier.admitted_rule is None


def test_foreign_symbolic_target_fails_closed() -> None:
    with pytest.raises(ValidationError, match="foreign symbolic-reference target"):
        orchestrate_binding_rule_admission(
            _symbolic("main"),
            candidate_inputs=(_candidate(_symbolic("foreign"), label="foreign"),),
        )


def test_explicit_admission_is_required_for_active_rule() -> None:
    symbolic = _symbolic()
    candidate = _candidate(symbolic)
    unresolved = orchestrate_binding_rule_admission(
        symbolic,
        candidate_inputs=(candidate,),
    )
    admitted = _admit_exact(symbolic, candidate)

    assert unresolved.kind is BindingRuleAdmissionFrontierKind.ADMISSION_REQUIRED
    assert unresolved.admitted_rule is None
    assert admitted.kind is BindingRuleAdmissionFrontierKind.RULE_OUTPUT_AVAILABLE
    assert admitted.admitted_rule is not None
    assert admitted.admitted_rule.rule == candidate.rule


def test_admitter_abstention_preserves_unresolved_frontier() -> None:
    symbolic = _symbolic()
    candidate = _candidate(symbolic)
    before = orchestrate_binding_rule_admission(
        symbolic,
        candidate_inputs=(candidate,),
    )
    after = orchestrate_binding_rule_admission(
        symbolic,
        candidate_inputs=(candidate,),
        admitter=lambda _target, _candidates, _attribution: None,
        admission_attribution=_admission(),
    )
    assert after == before


def test_admitter_cannot_erase_provenance_or_replace_attribution() -> None:
    symbolic = _symbolic()
    candidate = _candidate(symbolic)

    def erase(_target, candidates, attribution):
        return AdmittedBindingRule(
            admission_attribution=attribution,
            rule=candidates[0].rule,
            candidate_inputs=(),
        )

    with pytest.raises(ValidationError, match="complete exact candidate provenance"):
        orchestrate_binding_rule_admission(
            symbolic,
            candidate_inputs=(candidate,),
            admitter=erase,
            admission_attribution=_admission("expected"),
        )

    def replace(_target, candidates, _attribution):
        return AdmittedBindingRule(
            admission_attribution=_admission("forged"),
            rule=candidates[0].rule,
            candidate_inputs=candidates,
        )

    with pytest.raises(ValidationError, match="preserve exact"):
        orchestrate_binding_rule_admission(
            symbolic,
            candidate_inputs=(candidate,),
            admitter=replace,
            admission_attribution=_admission("expected"),
        )


def test_existing_admitted_rule_replays_without_new_admission() -> None:
    symbolic = _symbolic()
    candidate = _candidate(symbolic)
    output = AdmittedBindingRule(
        admission_attribution=_admission(),
        rule=candidate.rule,
        candidate_inputs=(candidate,),
    )
    replayed = orchestrate_binding_rule_admission(
        symbolic,
        admitted_outputs=(output,),
    )
    assert replayed.kind is BindingRuleAdmissionFrontierKind.RULE_OUTPUT_AVAILABLE
    assert replayed.admitted_rule == output
    assert replayed.candidate_inputs == output.candidate_inputs


def test_competing_admitted_rules_fail_closed() -> None:
    symbolic = _symbolic()
    first_candidate = _candidate(symbolic, label="a")
    second_candidate = _candidate(
        symbolic,
        label="b",
        rule=_rule(symbolic, label="b", interchangeable=True),
    )
    first = AdmittedBindingRule(
        admission_attribution=_admission("a"),
        rule=first_candidate.rule,
        candidate_inputs=(first_candidate,),
    )
    second = AdmittedBindingRule(
        admission_attribution=_admission("b"),
        rule=second_candidate.rule,
        candidate_inputs=(second_candidate,),
    )
    with pytest.raises(ValidationError, match="competing admitted outputs"):
        orchestrate_binding_rule_admission(
            symbolic,
            admitted_outputs=(first, second),
        )


def test_explicit_deterministic_admission_can_have_no_provider_candidates() -> None:
    symbolic = _symbolic()
    rule = _rule(symbolic)

    def admitter(target, candidates, attribution):
        assert target == symbolic
        assert candidates == ()
        return AdmittedBindingRule(
            admission_attribution=attribution,
            rule=rule,
            candidate_inputs=(),
        )

    frontier = orchestrate_binding_rule_admission(
        symbolic,
        admitter=admitter,
        admission_attribution=_admission("deterministic"),
    )
    assert frontier.kind is BindingRuleAdmissionFrontierKind.RULE_OUTPUT_AVAILABLE
    assert frontier.admitted_rule is not None
    assert frontier.admitted_rule.rule == rule
    assert frontier.candidate_inputs == ()


def _resolved_and_symbolic() -> tuple[ResolvedIntent, SymbolicReference]:
    request = IntentRequest(
        origin=OriginAttribution(
            kind=OriginKind.HUMAN,
            actor_ref=_ref("hde.subject", "human:test"),
            source_event_ref=_ref("hde.intent", "m3.0.3-test"),
        ),
        principal_ref=_ref("hde.subject", "human:test"),
        expression=IntentExpression(text="Open the selected report."),
    )
    context = ContextEnvelope(
        intent_request_identity=request.identity,
        boundary_attribution=SourceAttribution(
            source_ref=_ref("hde.adapter", "test"),
            source_event_ref=_ref("hde.context", "m3.0.3-test"),
        ),
        records=(),
    )
    resolved = ResolvedIntent(
        intent_request_identity=request.identity,
        context_envelope_identity=context.identity,
        admission_attribution=ResolutionAttribution(
            resolver_ref=_ref("irr.resolver", "test"),
            admission_event_ref=_ref("irr.resolution_admission", "m3.0.3-test"),
        ),
        semantics="Open one exact selected report.",
    )
    symbolic = SymbolicReference(
        resolved_intent_identity=resolved.identity,
        slot_ref=_ref("irr.slot", "selected-report"),
        semantic_type="artifact.path",
        selection_scope="reviewed reports",
        description="The exact report selected for the admitted plan.",
    )
    return resolved, symbolic


def test_admitted_rule_can_enter_m2_2_only_as_pending_rule() -> None:
    resolved, symbolic = _resolved_and_symbolic()
    candidate = _candidate(symbolic, rule=_rule(symbolic))
    admitted_frontier = _admit_exact(symbolic, candidate)
    admitted = admitted_frontier.admitted_rule
    assert admitted is not None

    plan_ref = _ref("irr.work_plan", "m3.0.3-test")
    plan = WorkPlan(
        resolved_intent_identity=resolved.identity,
        plan_ref=plan_ref,
        steps=(
            WorkStep(
                resolved_intent_identity=resolved.identity,
                work_plan_ref=plan_ref,
                step_ref=_ref("irr.work_step", "open-report"),
                operation="artifact.open",
                scope="the admitted selected report",
                inputs=(WorkSymbolicInput(name="report", reference=symbolic),),
                outputs=(),
                depends_on=(),
                continuation=WorkContinuationMode.NONE,
                completion_contract="The selected report is opened.",
                description="Open one exact selected report.",
            ),
        ),
        completion_contract="The bounded report operation completes.",
        description="One bounded plan requiring one external report binding.",
    )

    frontier = orchestrate_work_binding(
        resolved,
        work_plans=(plan,),
        binding_rules=(admitted.rule,),
    )
    assert frontier.work_plan == plan
    assert frontier.missing_rule_references == ()
    assert frontier.pending_rules == (admitted.rule,)
    assert frontier.bound_values == ()
    assert frontier.binding_issues == ()
    assert frontier.external_binding_complete is False
