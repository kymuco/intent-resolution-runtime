from __future__ import annotations

from dataclasses import replace

import pytest

from intent_resolution_runtime import (
    AttemptBoundInput,
    Authorization,
    BindingAttribution,
    BindingInput,
    BindingInputRole,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    BoundValue,
    CapabilityAttempt,
    CapabilityAttemptAttribution,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityInputContract,
    CapabilityInputMatch,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    GovernanceDecision,
    GovernanceDecisionAttribution,
    GovernanceDecisionComponent,
    GovernanceDecisionKind,
    ProposedWorkStep,
    RecordIdentity,
    SerializationError,
    SourceAttribution,
    StableRef,
    SymbolicReference,
    ValidationError,
    WorkContinuationMode,
    WorkPlan,
    WorkProposal,
    WorkProposalAttribution,
    WorkStep,
    WorkSymbolicInput,
)


RESOLVED = RecordIdentity("sha256", "3" * 64)
SOURCE_ID = RecordIdentity("sha256", "4" * 64)
AUTHORITY_CONTEXT_ID = RecordIdentity("sha256", "5" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> tuple[
    CapabilityAttempt,
    WorkProposal,
    BoundValue,
    Authorization,
    StableRef,
]:
    plan_ref = _ref("irr.work_plan", "inspect-001")
    step_ref = _ref("irr.work_step", "inspect")
    slot_ref = _ref("irr.slot", "workspace")
    symbolic = SymbolicReference(
        resolved_intent_identity=RESOLVED,
        slot_ref=slot_ref,
        semantic_type="filesystem.path",
        selection_scope="workspace:project",
        description="Concrete workspace path selected before the attempt.",
    )
    step = WorkStep(
        resolved_intent_identity=RESOLVED,
        work_plan_ref=plan_ref,
        step_ref=step_ref,
        operation="workspace.inspect",
        scope="workspace:project",
        inputs=(WorkSymbolicInput("workspace", symbolic),),
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract="Return the bounded workspace inspection result.",
        description="Inspect one concrete bounded workspace.",
    )
    plan = WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="Complete the bounded inspection plan.",
        description="Inspection plan.",
    )

    requested_scope = CapabilityRequestedScope(
        scope_ref=_ref("irr.capability_requested_scope", "workspace"),
        semantic_type="filesystem.path_scope",
        value="workspace:project",
        description="Bounded workspace scope.",
    )
    requirement = CapabilityRequirement(
        work_plan=plan,
        step_ref=step_ref,
        primary_scope_ref=requested_scope.scope_ref,
        requested_scopes=(requested_scope,),
        requested_effects=(),
        execution_boundary_requirements=(),
        description="Exact inspection capability requirement.",
    )
    descriptor_scope = CapabilityScopeRequirement(
        requirement_ref=_ref(
            "irr.capability_scope_requirement", "workspace-workspace.inspect.local"
        ),
        semantic_type="filesystem.path_scope",
        statement="Invocation must remain inside one bounded workspace.",
    )
    descriptor_input = CapabilityInputContract(
        input_ref=_ref("irr.capability_input", "workspace"),
        semantic_type="filesystem.path",
        scope_requirement_refs=(descriptor_scope.requirement_ref,),
        description="Concrete bounded workspace path.",
    )
    descriptor = CapabilityDescriptor(
        capability_ref=_ref("irr.capability", "workspace.inspect.local"),
        operation="workspace.inspect",
        input_contracts=(descriptor_input,),
        output_contracts=(),
        scope_requirements=(descriptor_scope,),
        effects=(),
        execution_boundaries=(),
        completion_contract=step.completion_contract,
        description="Bounded local workspace inspection capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", "attempt-test"),
        attribution=CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", "catalog-attempt-001"),
        ),
        scope_statement="Exact bounded Attempt planning surface.",
        descriptors=(descriptor,),
        description="Capability Attempt test snapshot.",
    )
    match = CapabilityMatch(
        attribution=CapabilityMatchAttribution(
            _ref("irr.matcher", "exact-v1"),
            _ref("irr.event", "match-attempt-001"),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        scope_matches=(
            CapabilityScopeMatch(
                requested_scope.scope_ref,
                descriptor_scope.requirement_ref,
            ),
        ),
        input_matches=(
            CapabilityInputMatch(
                work_input_name="workspace",
                descriptor_input_ref=descriptor_input.input_ref,
                requested_scope_refs=(requested_scope.scope_ref,),
            ),
        ),
        output_matches=(),
        effect_matches=(),
        description="Exact workspace.inspect match.",
    )
    evaluation = CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", "evaluation-attempt-001"),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        compatible_matches=(match,),
        incompatible_assessments=(),
        description="Exhaustive exact Catalog evaluation for one Attempt.",
    )
    proposal = WorkProposal(
        attribution=WorkProposalAttribution(
            _ref("irr.proposer", "irr-core"),
            _ref("irr.event", "proposal-attempt-001"),
        ),
        work_plan=plan,
        proposed_steps=(ProposedWorkStep(step_ref, evaluation),),
        authority_material=(),
        description="Bounded inspection work proposed to Governance.",
    )

    source_ref = _ref("irr.source", "workspace-binding")
    binding_input = BindingInput(
        resolved_intent_identity=RESOLVED,
        input_ref=_ref("irr.binding_input", "workspace-concrete"),
        attribution=SourceAttribution(
            source_ref,
            _ref("irr.event", "binding-source-attempt-001"),
        ),
        role=BindingInputRole.CONTEXT,
        source_identity=SOURCE_ID,
        semantic_type="filesystem.path",
        value="/workspace/project",
        selection_scope="workspace:project",
        value_scope="/workspace/project",
    )
    rule = BindingRule(
        resolved_intent_identity=RESOLVED,
        rule_ref=_ref("irr.binding_rule", "workspace-exact"),
        symbolic_reference=symbolic,
        allowed_input_roles=(BindingInputRole.CONTEXT,),
        allowed_source_refs=(source_ref,),
        allowed_source_identities=(SOURCE_ID,),
        input_semantic_type="filesystem.path",
        required_selection_scope="workspace:project",
        constraints=(),
        selection_policy=BindingSelectionPolicy(BindingSelectionMode.REQUIRE_UNIQUE),
        description="Require one exact concrete workspace path.",
    )
    bound = BoundValue(
        binding_attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "exact-v1"),
            _ref("irr.event", "binding-attempt-001"),
        ),
        rule=rule,
        binding_inputs=(binding_input,),
        selected_input_identity=binding_input.identity,
        semantic_type="filesystem.path",
        value="/workspace/project",
        selection_scope="workspace:project",
        value_scope="/workspace/project",
    )

    authorize_component = GovernanceDecisionComponent(
        component_ref=_ref("irr.governance_component", "authorize-inspect"),
        kind=GovernanceDecisionKind.AUTHORIZE,
        step_refs=(step_ref,),
        directives=(),
        rationale="Governance authorizes this exact bounded inspection step.",
    )
    decision = GovernanceDecision(
        attribution=GovernanceDecisionAttribution(
            governance_ref=_ref("irr.governance", "test-governance"),
            decision_event_ref=_ref("irr.event", "governance-attempt-001"),
            authority_context_ref=_ref("irr.authority_context", "test"),
            authority_context_identity=AUTHORITY_CONTEXT_ID,
        ),
        proposal=proposal,
        components=(authorize_component,),
        description="Exact Governance decision for the bounded inspection proposal.",
    )
    authorization = Authorization(decision, authorize_component.component_ref)
    attempt = CapabilityAttempt(
        attribution=CapabilityAttemptAttribution(
            _ref("irr.executor", "workspace-local"),
            _ref("irr.event", "attempt-001"),
        ),
        capability_evaluation=evaluation,
        step_ref=step_ref,
        bound_inputs=(AttemptBoundInput("workspace", bound),),
        presented_authorizations=(authorization,),
        description="One attributable effort to inspect the concrete workspace.",
    )
    return attempt, proposal, bound, authorization, step_ref


def test_capability_attempt_round_trip_preserves_identity() -> None:
    attempt, _, _, _, _ = _fixture()
    decoded = CapabilityAttempt.from_json_bytes(attempt.canonical_bytes())
    assert decoded == attempt
    assert decoded.identity == attempt.identity
    assert decoded.work_step == attempt.work_step
    assert decoded.capability_match == attempt.capability_match


def test_attempt_occurrence_changes_identity_without_mutating_work() -> None:
    attempt, _, _, _, _ = _fixture()
    other = replace(
        attempt,
        attribution=CapabilityAttemptAttribution(
            attempt.attribution.executor_ref,
            _ref("irr.event", "attempt-002"),
        ),
    )
    assert other.capability_evaluation == attempt.capability_evaluation
    assert other.identity != attempt.identity


def test_attempt_can_record_no_presented_authorization() -> None:
    attempt, _, _, _, _ = _fixture()
    historical = replace(attempt, presented_authorizations=())
    assert historical.presented_authorizations == ()
    assert historical.identity != attempt.identity


def test_attempt_requires_unique_capability_match_evaluation() -> None:
    attempt, _, _, _, _ = _fixture()
    empty_snapshot = replace(
        attempt.capability_evaluation.catalog_snapshot,
        descriptors=(),
    )
    no_match_evaluation = CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", "evaluation-attempt-no-match"),
        ),
        requirement=attempt.capability_evaluation.requirement,
        catalog_snapshot=empty_snapshot,
        compatible_matches=(),
        incompatible_assessments=(),
        description="Exhaustive empty Catalog evaluation for Attempt rejection.",
    )
    with pytest.raises(ValidationError, match="exactly one admitted CapabilityMatch"):
        replace(
            attempt,
            capability_evaluation=no_match_evaluation,
            presented_authorizations=(),
        )


def test_attempt_requires_exact_symbolic_input_coverage() -> None:
    attempt, _, _, _, _ = _fixture()
    with pytest.raises(ValidationError, match="exactly cover all symbolic"):
        replace(attempt, bound_inputs=())


def test_attempt_rejects_unadmitted_extra_bound_input_name() -> None:
    attempt, _, bound, _, _ = _fixture()
    with pytest.raises(ValidationError, match="exactly cover all symbolic"):
        replace(
            attempt,
            bound_inputs=(
                AttemptBoundInput("workspace", bound),
                AttemptBoundInput("other", bound),
            ),
        )


def test_attempt_rejects_bound_value_for_different_symbolic_reference() -> None:
    attempt, _, bound, _, _ = _fixture()
    other_symbolic = replace(
        bound.rule.symbolic_reference,
        slot_ref=_ref("irr.slot", "different-workspace"),
    )
    other_rule = replace(bound.rule, symbolic_reference=other_symbolic)
    other_bound = replace(bound, rule=other_rule)
    with pytest.raises(ValidationError, match="exact WorkSymbolicInput reference"):
        replace(attempt, bound_inputs=(AttemptBoundInput("workspace", other_bound),))


def test_attempt_rejects_foreign_work_proposal_step() -> None:
    attempt, _, _, _, _ = _fixture()
    with pytest.raises(ValidationError, match="exact capability requirement WorkStep"):
        replace(attempt, step_ref=_ref("irr.work_step", "other"))


def test_attempt_occurrence_must_differ_from_evaluation_occurrence() -> None:
    attempt, _, _, _, _ = _fixture()
    with pytest.raises(ValidationError, match="differ from CapabilityMatchEvaluation occurrence"):
        replace(
            attempt,
            attribution=CapabilityAttemptAttribution(
                attempt.attribution.executor_ref,
                attempt.capability_evaluation.attribution.evaluation_event_ref,
            ),
        )


def test_attempt_occurrence_must_differ_from_binding_occurrence() -> None:
    attempt, _, bound, _, _ = _fixture()
    with pytest.raises(ValidationError, match="differ from Binding occurrence"):
        replace(
            attempt,
            attribution=CapabilityAttemptAttribution(
                attempt.attribution.executor_ref,
                bound.binding_attribution.binding_event_ref,
            ),
        )


def test_attempt_rejects_authorization_for_different_exact_evaluation() -> None:
    attempt, proposal, _, authorization, step_ref = _fixture()
    foreign_evaluation = replace(
        attempt.capability_evaluation,
        attribution=CapabilityMatchEvaluationAttribution(
            attempt.capability_evaluation.attribution.evaluator_ref,
            _ref("irr.event", "evaluation-attempt-foreign"),
        ),
    )
    foreign_proposal = replace(
        proposal,
        attribution=WorkProposalAttribution(
            proposal.attribution.proposer_ref,
            _ref("irr.event", "proposal-attempt-foreign"),
        ),
        proposed_steps=(ProposedWorkStep(step_ref, foreign_evaluation),),
    )
    foreign_decision = replace(authorization.decision, proposal=foreign_proposal)
    foreign_authorization = Authorization(foreign_decision, authorization.component_ref)
    with pytest.raises(ValidationError, match="exact capability evaluation"):
        replace(attempt, presented_authorizations=(foreign_authorization,))


def test_attempt_occurrence_must_differ_from_presented_proposal_occurrence() -> None:
    attempt, proposal, _, _, _ = _fixture()
    with pytest.raises(ValidationError, match="differ from WorkProposal occurrence"):
        replace(
            attempt,
            attribution=CapabilityAttemptAttribution(
                attempt.attribution.executor_ref,
                proposal.attribution.proposal_event_ref,
            ),
        )


def test_attempt_supports_at_most_one_authorization_in_v1() -> None:
    attempt, _, _, authorization, _ = _fixture()
    with pytest.raises(ValidationError, match="at most one Authorization"):
        replace(
            attempt,
            presented_authorizations=(authorization, authorization),
        )


def test_presented_authorization_does_not_become_attempt_authority_boolean() -> None:
    attempt, _, _, authorization, _ = _fixture()
    assert attempt.presented_authorizations == (authorization,)
    primitive = attempt.to_primitive()
    assert "authorized" not in primitive
    assert "authorization_valid" not in primitive
    assert "conditions_satisfied" not in primitive


def test_attempt_has_no_outcome_retry_or_attempt_number_fields() -> None:
    attempt, _, _, _, _ = _fixture()
    primitive = attempt.to_primitive()
    for forbidden in (
        "status",
        "outcome",
        "succeeded",
        "failed",
        "blocked",
        "interrupted",
        "unknown_outcome",
        "retry",
        "attempt_number",
        "predecessor_attempt",
    ):
        assert forbidden not in primitive


def test_attempt_unknown_authority_like_or_outcome_fields_fail_closed() -> None:
    attempt, _, _, _, _ = _fixture()
    primitive = attempt.to_primitive()
    primitive["succeeded"] = True
    with pytest.raises(SerializationError, match="invalid fields"):
        CapabilityAttempt.from_primitive(primitive)


def test_attempt_bound_input_round_trip_preserves_exact_bound_value() -> None:
    _, _, bound, _, _ = _fixture()
    item = AttemptBoundInput("workspace", bound)
    decoded = AttemptBoundInput.from_json_bytes(item.canonical_bytes())
    assert decoded == item
    assert decoded.identity == item.identity


def test_attempt_attribution_round_trip_preserves_occurrence() -> None:
    attempt, _, _, _, _ = _fixture()
    attribution = attempt.attribution
    decoded = CapabilityAttemptAttribution.from_json_bytes(
        attribution.canonical_bytes()
    )
    assert decoded == attribution
    assert decoded.identity == attribution.identity


def test_attempt_public_ir_types_are_closed() -> None:
    with pytest.raises(TypeError, match="closed IR type"):
        class _BadAttempt(CapabilityAttempt):
            pass

    with pytest.raises(TypeError, match="closed IR type"):
        class _BadBoundInput(AttemptBoundInput):
            pass
