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
    mode: BindingSelectionMode = BindingSelectionMode.REQUIRE_UNIQUE,
) -> BindingRule:
    policy = (
        BindingSelectionPolicy(mode=mode)
        if mode is BindingSelectionMode.REQUIRE_UNIQUE
        else BindingSelectionPolicy(
            mode=BindingSelectionMode.ANY_INTERCHANGEABLE,
            interchangeable_choice="canonical_identity_min",  # type: ignore[arg-type]
        )
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
        description="Use one exact reviewed context artifact for this symbolic slot.",
    )


def _proposal_attribution(label: str) -> BindingRuleProposalAttribution:
    return BindingRuleProposalAttribution(
        proposer_ref=_ref("irr.binding_rule_proposer", f"planner:{label}"),
        proposal_event_ref=_ref("irr.binding_rule_proposal", f"proposal:{label}"),
    )


def _admission_attribution(label: str = "main") -> BindingRuleAdmissionAttribution:
    return BindingRuleAdmissionAttribution(
        resolver_ref=_ref("irr.binding_rule_resolver", "m3.0.3-test"),
        admission_event_ref=_ref("irr.binding_rule_admission", f"admission:{label}"),
    )


def _candidate(
    symbolic: SymbolicReference,
    *,
    label: str = "main",
    rule: BindingRule | None = None,
    rationale: str = "The exact symbolic slot requires this bounded selection rule.",
) -> CandidateBindingRule:
    return CandidateBindingRule(
        attribution=_proposal_attribution(label),
        rule=_rule(symbolic, label=label) if rule is None else rule,
        rationale=rationale,
    )


def test_canonical_records_round_trip_and_identity_are_stable() -> None:
    symbolic = _symbolic()
    candidate = _candidate(symbolic)
    attribution = _admission_attribution()
    admitted = AdmittedBindingRule(
        admission_attribution=attribution,
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
        BindingRuleAdmissionAttribution.from_json_bytes(attribution.canonical_bytes())
        == attribution
    )
    assert AdmittedBindingRule.from_json_bytes(admitted.canonical_bytes()) == admitted
    assert AdmittedBindingRule.from_json_bytes(admitted.canonical_bytes()).identity == admitted.identity


def test_no_candidates_requires_proposal_input_and_does_not_infer_a_rule() -> None:
    symbolic = _symbolic()
    frontier = orchestrate_binding_rule_admission(symbolic)

    assert frontier.kind is BindingRuleAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
    assert frontier.candidate_inputs == ()
    assert frontier.admitted_rule is None
    assert not hasattr(frontier, "identity")
    assert not hasattr(frontier, "canonical_bytes")


def test_exact_rule_with_different_attribution_and_rationale_is_not_voting() -> None:
    symbolic = _symbolic()
    rule = _rule(symbolic)
    candidates = (
        _candidate(
            symbolic,
            label="a",
            rule=rule,
            rationale="First explanation.",
        ),
        _candidate(
            symbolic,
            label="b",
            rule=rule,
            rationale="Different explanation for the same exact rule.",
        ),
    )

    frontier = orchestrate_binding_rule_admission(
        symbolic,
        candidate_inputs=tuple(reversed(candidates)),
    )

    assert frontier.kind is BindingRuleAdmissionFrontierKind.ADMISSION_REQUIRED
    assert set(item.identity for item in frontier.candidate_inputs) == set(
        item.identity for item in candidates
    )
    assert frontier.admitted_rule is None


def test_distinct_rule_semantics_require_adjudication() -> None:
    symbolic = _symbolic()
    first = _candidate(symbolic, label="unique")
    second_rule = _rule(
        symbolic,
        label="interchangeable",
        mode=BindingSelectionMode.ANY_INTERCHANGEABLE,
    )
    second = _candidate(
        symbolic,
        label="interchangeable",
        rule=second_rule,
    )

    frontier = orchestrate_binding_rule_admission(
        symbolic,
        candidate_inputs=(first, second),
    )

    assert frontier.kind is BindingRuleAdmissionFrontierKind.ADJUDICATION_REQUIRED
    assert frontier.admitted_rule is None


def test_candidate_for_foreign_symbolic_target_fails_closed() -> None:
    symbolic = _symbolic("main")
    foreign = _symbolic("foreign")
    candidate = _candidate(foreign, label="foreign")

    with pytest.raises(ValidationError, match="foreign symbolic-reference target"):
        orchestrate_binding_rule_admission(
            symbolic,
            candidate_inputs=(candidate,),
        )


def test_explicit_admitter_creates_exact_admitted_rule() -> None:
    symbolic = _symbolic()
    candidate = _candidate(symbolic)
    attribution = _admission_attribution()
    calls: list[tuple[object, object, object]] = []

    def admitter(target, candidates, supplied_attribution):
        calls.append((target, candidates, supplied_attribution))
        return AdmittedBindingRule(
            admission_attribution=supplied_attribution,
            rule=candidates[0].rule,
            candidate_inputs=candidates,
        )

    frontier = orchestrate_binding_rule_admission(
        symbolic,
        candidate_inputs=(candidate,),
        admitter=admitter,
        admission_attribution=attribution,
    )

    assert frontier.kind is BindingRuleAdmissionFrontierKind.RULE_OUTPUT_AVAILABLE
    assert frontier.admitted_rule is not None
    assert frontier.admitted_rule.rule == candidate.rule
    assert frontier.admitted_rule.admission_attribution == attribution
    assert frontier.admitted_rule.candidate_inputs == (candidate,)
    assert calls == [(symbolic, (candidate,), attribution)]


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
        admission_attribution=_admission_attribution(),
    )

    assert after == before


def test_admitter_cannot_erase_candidate_provenance() -> None:
    symbolic = _symbolic()
    candidate = _candidate(symbolic)

    def admitter(_target, candidates, attribution):
        return AdmittedBindingRule(
            admission_attribution=attribution,
            rule=candidates[0].rule,
            candidate_inputs=(),
        )

    with pytest.raises(ValidationError, match="complete exact candidate provenance"):
        orchestrate_binding_rule_admission(
            symbolic,
            candidate_inputs=(candidate,),
            admitter=admitter,
            admission_attribution=_admission_attribution(),
        )


def test_admitter_cannot_replace_admission_attribution() -> None:
    symbolic = _symbolic()
    candidate = _candidate(symbolic)

    def admitter(_target, candidates, _attribution):
        return AdmittedBindingRule(
            admission_attribution=_admission_attribution("forged"),
            rule=candidates[0].rule,
            candidate_inputs=candidates,
        )

    with pytest.raises(ValidationError, match="preserve exact"):
        orchestrate_binding_rule_admission(
            symbolic,
            candidate_inputs=(candidate,),
            admitter=admitter,
            admission_attribution=_admission_attribution("expected"),
        )


def test_existing_admitted_rule_replays_without_new_admission_transition() -> None:
    symbolic = _symbolic()
    candidate = _candidate(symbolic)
    admitted = AdmittedBindingRule(
        admission_attribution=_admission_attribution(),
        rule=candidate.rule,
        candidate_inputs=(candidate,),
    )

    frontier = orchestrate_binding_rule_admission(
        symbolic,
        admitted_outputs=(admitted,),
    )

    assert frontier.kind is BindingRuleAdmissionFrontierKind.RULE_OUTPUT_AVAILABLE
    assert frontier.admitted_rule == admitted
    assert frontier.candidate_inputs == admitted.candidate_inputs


def test_competing_admitted_rules_fail_closed() -> None:
    symbolic = _symbolic()
    first_candidate = _candidate(symbolic, label="a")
    second_rule = _rule(
        symbolic,
        label="b",
        mode=BindingSelectionMode.ANY_INTERCHANGEABLE,
    )
    second_candidate = _candidate(symbolic, label="b", rule=second_rule)
    first = AdmittedBindingRule(
        admission_attribution=_admission_attribution("a"),
        rule=first_candidate.rule,
        candidate_inputs=(first_candidate,),
    )
    second = AdmittedBindingRule(
        admission_attribution=_admission_attribution("b"),
        rule=second_candidate.rule,
        candidate_inputs=(second_candidate,),
    )

    with pytest.raises(ValidationError, match="competing admitted outputs"):
        orchestrate_binding_rule_admission(
            symbolic,
            admitted_outputs=(first, second),
        )


def test_deterministic_admission_without_candidate_provider_is_explicit() -> None:
    symbolic = _symbolic()
    rule = _rule(symbolic)
    attribution = _admission_attribution("deterministic")

    def admitter(target, candidates, supplied_attribution):
        assert target == symbolic
        assert candidates == ()
        return AdmittedBindingRule(
            admission_attribution=supplied_attribution,
            rule=rule,
            candidate_inputs=(),
        )

    frontier = orchestrate_binding_rule_admission(
        symbolic,
        admitter=admitter,
        admission_attribution=attribution,
    )

    assert frontier.kind is BindingRuleAdmissionFrontierKind.RULE_OUTPUT_AVAILABLE
    assert frontier.candidate_inputs == ()
    assert frontier.admitted_rule is not None
    assert frontier.admitted_rule.rule == rule


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


def test_only_admitted_rule_can_be_projected_as_pending_m2_2_rule() -> None:
    resolved, symbolic = _resolved_and_symbolic()
    rule = _rule(symbolic)
    candidate = _candidate(symbolic, rule=rule)

    def admitter(_target, candidates, attribution):
        return AdmittedBindingRule(
            admission_attribution=attribution,
            rule=candidates[0].rule,
            candidate_inputs=candidates,
        )

    admitted_frontier = orchestrate_binding_rule_admission(
        symbolic,
        candidate_inputs=(candidate,),
        admitter=admitter,
        admission_attribution=_admission_attribution("integration"),
    )
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
        description="One bounded work plan requiring an external report binding.",
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
