from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    Authorization,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityIncompatibleDescriptorAssessment,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityMatchIssueKind,
    CapabilityMismatchKind,
    CapabilityMismatchReason,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    GovernanceDecision,
    GovernanceDecisionAttribution,
    GovernanceDecisionComponent,
    GovernanceDecisionKind,
    GovernanceDirective,
    ProposedWorkStep,
    RecordIdentity,
    StableRef,
    ValidationError,
    WorkContinuationMode,
    WorkPlan,
    WorkProposal,
    WorkProposalAttribution,
    WorkStep,
)
from intent_resolution_runtime.capability_governance import (
    CapabilityGovernanceFrontier,
    orchestrate_capability_governance,
)


RESOLVED = RecordIdentity("sha256", "3" * 64)
AUTHORITY_CONTEXT = RecordIdentity("sha256", "5" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _plan(*names: str, label: str = "plan") -> WorkPlan:
    if not names:
        names = ("inspect",)
    plan_ref = _ref("irr.work_plan", label)
    steps = tuple(
        WorkStep(
            resolved_intent_identity=RESOLVED,
            work_plan_ref=plan_ref,
            step_ref=_ref("irr.work_step", name),
            operation=f"workspace.{name}",
            scope=f"workspace:{name}",
            inputs=(),
            outputs=(),
            depends_on=(),
            continuation=WorkContinuationMode.NONE,
            completion_contract=f"Return the bounded {name} result.",
            description=f"Perform bounded {name} work.",
        )
        for name in names
    )
    return WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=plan_ref,
        steps=steps,
        completion_contract="Complete the bounded test plan.",
        description="M2.3 capability/Governance test plan.",
    )


def _step(plan: WorkPlan, name: str) -> WorkStep:
    target = _ref("irr.work_step", name)
    return next(step for step in plan.steps if step.step_ref == target)


def _requirement(plan: WorkPlan, name: str) -> CapabilityRequirement:
    step = _step(plan, name)
    scope = CapabilityRequestedScope(
        scope_ref=_ref("irr.capability_requested_scope", name),
        semantic_type="filesystem.path_scope",
        value=step.scope,
        description=f"Bounded scope for {name}.",
    )
    return CapabilityRequirement(
        work_plan=plan,
        step_ref=step.step_ref,
        primary_scope_ref=scope.scope_ref,
        requested_scopes=(scope,),
        requested_effects=(),
        execution_boundary_requirements=(),
        description=f"Exact capability requirement for {name}.",
    )


def _descriptor(plan: WorkPlan, name: str, *, capability_name: str | None = None) -> CapabilityDescriptor:
    step = _step(plan, name)
    capability_name = capability_name or f"{name}.local"
    scope = CapabilityScopeRequirement(
        requirement_ref=_ref("irr.capability_scope_requirement", f"{name}-{capability_name}"),
        semantic_type="filesystem.path_scope",
        statement=f"Invocation must remain inside the bounded {name} scope.",
    )
    return CapabilityDescriptor(
        capability_ref=_ref("irr.capability", capability_name),
        operation=step.operation,
        input_contracts=(),
        output_contracts=(),
        scope_requirements=(scope,),
        effects=(),
        execution_boundaries=(),
        completion_contract=step.completion_contract,
        description=f"Capability {capability_name} for {name}.",
    )


def _snapshot(
    descriptors: tuple[CapabilityDescriptor, ...],
    *,
    event: str,
) -> CapabilityCatalogSnapshot:
    return CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", "m2.3-test"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=_ref("irr.host", "m2.3-test-host"),
            snapshot_event_ref=_ref("irr.event", event),
        ),
        scope_statement="Exact bounded M2.3 planning surface.",
        descriptors=descriptors,
        description="M2.3 capability catalog snapshot.",
    )


def _match(
    requirement: CapabilityRequirement,
    snapshot: CapabilityCatalogSnapshot,
    descriptor: CapabilityDescriptor,
    *,
    event: str,
) -> CapabilityMatch:
    return CapabilityMatch(
        attribution=CapabilityMatchAttribution(
            matcher_ref=_ref("irr.matcher", "exact-v1"),
            match_event_ref=_ref("irr.event", event),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        scope_matches=(
            CapabilityScopeMatch(
                requested_scope_ref=requirement.requested_scopes[0].scope_ref,
                descriptor_scope_requirement_ref=descriptor.scope_requirements[0].requirement_ref,
            ),
        ),
        input_matches=(),
        output_matches=(),
        effect_matches=(),
        description=f"Exact match for {descriptor.capability_ref.value}.",
    )


def _incompatible(descriptor: CapabilityDescriptor, *, name: str) -> CapabilityIncompatibleDescriptorAssessment:
    return CapabilityIncompatibleDescriptorAssessment(
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        reasons=(
            CapabilityMismatchReason(
                kind=CapabilityMismatchKind.OPERATION_MISMATCH,
                scope=f"descriptor:{descriptor.capability_ref.value}",
                description=f"Descriptor is not the admitted operation for {name}.",
            ),
        ),
    )


def _unique_evaluation(
    plan: WorkPlan,
    name: str,
    *,
    event: str | None = None,
) -> tuple[CapabilityRequirement, CapabilityMatchEvaluation]:
    requirement = _requirement(plan, name)
    descriptor = _descriptor(plan, name)
    snapshot = _snapshot((descriptor,), event=f"catalog-{event or name}")
    match = _match(requirement, snapshot, descriptor, event=f"match-{event or name}")
    evaluation = CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            evaluator_ref=_ref("irr.evaluator", "m2.3"),
            evaluation_event_ref=_ref("irr.event", f"evaluation-{event or name}"),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        compatible_matches=(match,),
        incompatible_assessments=(),
        description=f"Exact unique capability evaluation for {name}.",
    )
    return requirement, evaluation


def _no_match_evaluation(plan: WorkPlan, name: str) -> tuple[CapabilityRequirement, CapabilityMatchEvaluation]:
    requirement = _requirement(plan, name)
    snapshot = _snapshot((), event=f"catalog-empty-{name}")
    evaluation = CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "m2.3"),
            _ref("irr.event", f"evaluation-empty-{name}"),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        compatible_matches=(),
        incompatible_assessments=(),
        description=f"No compatible capability for {name} in the exact empty snapshot.",
    )
    return requirement, evaluation


def _multiple_match_evaluation(plan: WorkPlan, name: str) -> tuple[CapabilityRequirement, CapabilityMatchEvaluation]:
    requirement = _requirement(plan, name)
    first = _descriptor(plan, name, capability_name=f"{name}.a")
    second = _descriptor(plan, name, capability_name=f"{name}.b")
    snapshot = _snapshot((first, second), event=f"catalog-multiple-{name}")
    evaluation = CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "m2.3"),
            _ref("irr.event", f"evaluation-multiple-{name}"),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        compatible_matches=(
            _match(requirement, snapshot, first, event=f"match-{name}-a"),
            _match(requirement, snapshot, second, event=f"match-{name}-b"),
        ),
        incompatible_assessments=(),
        description=f"Multiple compatible capabilities for {name}.",
    )
    return requirement, evaluation


def _two_step_evaluations(
    plan: WorkPlan,
) -> tuple[
    tuple[CapabilityRequirement, CapabilityRequirement],
    tuple[CapabilityMatchEvaluation, CapabilityMatchEvaluation],
]:
    alpha_req = _requirement(plan, "alpha")
    beta_req = _requirement(plan, "beta")
    alpha_desc = _descriptor(plan, "alpha")
    beta_desc = _descriptor(plan, "beta")
    snapshot = _snapshot((alpha_desc, beta_desc), event="catalog-two-step")

    alpha_eval = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "m2.3"),
            _ref("irr.event", "evaluation-alpha"),
        ),
        alpha_req,
        snapshot,
        (_match(alpha_req, snapshot, alpha_desc, event="match-alpha"),),
        (_incompatible(beta_desc, name="alpha"),),
        "Exhaustive alpha evaluation over the shared catalog.",
    )
    beta_eval = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "m2.3"),
            _ref("irr.event", "evaluation-beta"),
        ),
        beta_req,
        snapshot,
        (_match(beta_req, snapshot, beta_desc, event="match-beta"),),
        (_incompatible(alpha_desc, name="beta"),),
        "Exhaustive beta evaluation over the shared catalog.",
    )
    return (alpha_req, beta_req), (alpha_eval, beta_eval)


def _proposal(
    plan: WorkPlan,
    evaluations: tuple[CapabilityMatchEvaluation, ...],
    *,
    event: str,
) -> WorkProposal:
    return WorkProposal(
        attribution=WorkProposalAttribution(
            proposer_ref=_ref("irr.proposer", "m2.3"),
            proposal_event_ref=_ref("irr.event", event),
        ),
        work_plan=plan,
        proposed_steps=tuple(
            ProposedWorkStep(evaluation.requirement.step_ref, evaluation)
            for evaluation in evaluations
        ),
        authority_material=(),
        description=f"M2.3 proposal {event}.",
    )


def _governance_attr(event: str) -> GovernanceDecisionAttribution:
    return GovernanceDecisionAttribution(
        governance_ref=_ref("irr.governance", "m2.3-host"),
        decision_event_ref=_ref("irr.event", event),
        authority_context_ref=_ref("irr.authority_context", "m2.3-session"),
        authority_context_identity=AUTHORITY_CONTEXT,
    )


def _directive(label: str) -> GovernanceDirective:
    return GovernanceDirective(
        directive_ref=_ref("irr.governance_directive", label),
        semantic_type="semantic_constraint",
        scope="exact proposed work subset",
        statement=f"Explicit Governance directive {label}.",
    )


def _component(
    kind: GovernanceDecisionKind,
    step_refs: tuple[StableRef, ...],
    *,
    label: str,
) -> GovernanceDecisionComponent:
    directives = ()
    if kind in (GovernanceDecisionKind.CONSTRAIN, GovernanceDecisionKind.REQUIRE_REVIEW):
        directives = (_directive(label),)
    return GovernanceDecisionComponent(
        component_ref=_ref("irr.governance_component", label),
        kind=kind,
        step_refs=step_refs,
        directives=directives,
        rationale=f"Governance {kind.value} for {label}.",
    )


def test_no_requirements_is_neutral_capability_disposition_not_missing_capability() -> None:
    plan = _plan("inspect")

    frontier = orchestrate_capability_governance(plan)

    assert frontier.capability_disposition_required_step_refs == (_ref("irr.work_step", "inspect"),)
    assert frontier.pending_capability_requirements == ()
    assert frontier.capability_matches == ()
    assert frontier.capability_issues == ()


def test_frontier_is_noncanonical_and_constructor_revalidates_exact_graph() -> None:
    plan = _plan("inspect")
    frontier = CapabilityGovernanceFrontier(plan)

    assert not hasattr(frontier, "canonical_bytes")
    assert not hasattr(frontier, "identity")
    assert frontier.capability_disposition_required_step_refs


def test_requirement_without_evaluation_is_pending_without_implying_unavailability() -> None:
    plan = _plan("inspect")
    requirement = _requirement(plan, "inspect")

    frontier = orchestrate_capability_governance(
        plan,
        capability_requirements=(requirement,),
    )

    assert frontier.capability_disposition_required_step_refs == ()
    assert frontier.pending_capability_requirements == (requirement,)
    assert frontier.capability_matches == ()
    assert frontier.capability_issues == ()


def test_unique_evaluation_surfaces_match_without_implying_availability_or_authority() -> None:
    plan = _plan("inspect")
    requirement, evaluation = _unique_evaluation(plan, "inspect")

    frontier = orchestrate_capability_governance(
        plan,
        capability_requirements=(requirement,),
        capability_evaluations=(evaluation,),
    )

    assert frontier.capability_matches == (evaluation.compatible_matches[0],)
    assert frontier.capability_issues == ()
    assert frontier.proposal_disposition_required_step_refs == (_ref("irr.work_step", "inspect"),)
    assert frontier.materialized_authorized_step_refs == ()


def test_zero_and_multiple_match_results_remain_capability_issues_not_hidden_selection() -> None:
    no_plan = _plan("inspect", label="no-match")
    no_req, no_eval = _no_match_evaluation(no_plan, "inspect")
    no_frontier = orchestrate_capability_governance(
        no_plan,
        capability_requirements=(no_req,),
        capability_evaluations=(no_eval,),
    )
    assert no_frontier.capability_issues[0].kind is CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY
    assert no_frontier.proposal_disposition_required_step_refs == ()

    multi_plan = _plan("inspect", label="multi-match")
    multi_req, multi_eval = _multiple_match_evaluation(multi_plan, "inspect")
    multi_frontier = orchestrate_capability_governance(
        multi_plan,
        capability_requirements=(multi_req,),
        capability_evaluations=(multi_eval,),
    )
    assert multi_frontier.capability_issues[0].kind is CapabilityMatchIssueKind.MULTIPLE_COMPATIBLE_MATCHES
    assert multi_frontier.proposal_disposition_required_step_refs == ()


def test_foreign_or_competing_requirement_fails_closed() -> None:
    plan = _plan("inspect", label="main")
    foreign = _plan("inspect", label="foreign")
    foreign_requirement = _requirement(foreign, "inspect")
    with pytest.raises(ValidationError, match="exact active WorkPlan"):
        orchestrate_capability_governance(
            plan,
            capability_requirements=(foreign_requirement,),
        )

    first = _requirement(plan, "inspect")
    scope = first.requested_scopes[0]
    competing = CapabilityRequirement(
        work_plan=plan,
        step_ref=first.step_ref,
        primary_scope_ref=scope.scope_ref,
        requested_scopes=(scope,),
        requested_effects=(),
        execution_boundary_requirements=(),
        description="Different active requirement occurrence/semantics for the same step.",
    )
    assert competing.identity != first.identity
    with pytest.raises(ValidationError, match="competing CapabilityRequirement"):
        CapabilityGovernanceFrontier(plan, (first, competing))


def test_orphan_or_competing_evaluation_fails_closed() -> None:
    plan = _plan("inspect")
    requirement, evaluation = _unique_evaluation(plan, "inspect", event="first")
    with pytest.raises(ValidationError, match="orphaned from the active CapabilityRequirement"):
        orchestrate_capability_governance(plan, capability_evaluations=(evaluation,))

    _, second = _unique_evaluation(plan, "inspect", event="second")
    assert second.requirement == requirement
    with pytest.raises(ValidationError, match="competing active CapabilityMatchEvaluation"):
        orchestrate_capability_governance(
            plan,
            capability_requirements=(requirement,),
            capability_evaluations=(evaluation, second),
        )


def test_matched_step_without_proposal_is_neutral_proposal_disposition() -> None:
    plan = _plan("inspect")
    requirement, evaluation = _unique_evaluation(plan, "inspect")

    frontier = orchestrate_capability_governance(
        plan,
        capability_requirements=(requirement,),
        capability_evaluations=(evaluation,),
    )

    assert frontier.proposal_disposition_required_step_refs == (_ref("irr.work_step", "inspect"),)
    assert frontier.governance_pending_proposals == ()


def test_proposal_without_governance_decision_is_pending_not_denied() -> None:
    plan = _plan("inspect")
    requirement, evaluation = _unique_evaluation(plan, "inspect")
    proposal = _proposal(plan, (evaluation,), event="proposal-inspect")

    frontier = orchestrate_capability_governance(
        plan,
        capability_requirements=(requirement,),
        capability_evaluations=(evaluation,),
        work_proposals=(proposal,),
    )

    assert frontier.proposal_disposition_required_step_refs == ()
    assert frontier.governance_pending_proposals == (proposal,)
    assert frontier.denied_step_refs == ()
    assert frontier.materialized_authorized_step_refs == ()


def test_overlapping_active_proposals_for_one_step_fail_closed() -> None:
    plan = _plan("inspect")
    requirement, evaluation = _unique_evaluation(plan, "inspect")
    first = _proposal(plan, (evaluation,), event="proposal-a")
    second = _proposal(plan, (evaluation,), event="proposal-b")

    with pytest.raises(ValidationError, match="overlapping active WorkProposal"):
        orchestrate_capability_governance(
            plan,
            capability_requirements=(requirement,),
            capability_evaluations=(evaluation,),
            work_proposals=(first, second),
        )


def test_governance_omission_is_unmentioned_and_authorize_component_is_exact_transition_candidate() -> None:
    plan = _plan("alpha", "beta", label="partial")
    requirements, evaluations = _two_step_evaluations(plan)
    proposal = _proposal(plan, evaluations, event="proposal-both")
    alpha_ref = _ref("irr.work_step", "alpha")
    beta_ref = _ref("irr.work_step", "beta")
    authorize_alpha = _component(
        GovernanceDecisionKind.AUTHORIZE,
        (alpha_ref,),
        label="authorize-alpha",
    )
    decision = GovernanceDecision(
        _governance_attr("decision-partial"),
        proposal,
        (authorize_alpha,),
        "Governance decided alpha and omitted beta.",
    )

    frontier = orchestrate_capability_governance(
        plan,
        capability_requirements=requirements,
        capability_evaluations=evaluations,
        work_proposals=(proposal,),
        governance_decisions=(decision,),
    )

    assert frontier.governance_unmentioned_step_refs == (beta_ref,)
    assert frontier.denied_step_refs == ()
    assert frontier.materialized_authorized_step_refs == ()
    assert frontier.authorization_materialization_frontier == (
        Authorization(decision, authorize_alpha.component_ref),
    )


def test_authorize_decision_exposes_idempotent_authorization_transition_until_record_is_admitted() -> None:
    plan = _plan("inspect")
    requirement, evaluation = _unique_evaluation(plan, "inspect")
    proposal = _proposal(plan, (evaluation,), event="proposal-auth")
    component = _component(
        GovernanceDecisionKind.AUTHORIZE,
        (_ref("irr.work_step", "inspect"),),
        label="authorize-inspect",
    )
    decision = GovernanceDecision(
        _governance_attr("decision-auth"),
        proposal,
        (component,),
        "External Governance authorizes the exact proposed step.",
    )
    exact_projection = Authorization(decision, component.component_ref)

    pending = orchestrate_capability_governance(
        plan,
        capability_requirements=(requirement,),
        capability_evaluations=(evaluation,),
        work_proposals=(proposal,),
        governance_decisions=(decision,),
    )
    assert pending.authorization_materialization_frontier == (exact_projection,)
    assert pending.materialized_authorized_step_refs == ()

    materialized = orchestrate_capability_governance(
        plan,
        capability_requirements=(requirement,),
        capability_evaluations=(evaluation,),
        work_proposals=(proposal,),
        governance_decisions=(decision,),
        authorizations=(exact_projection,),
    )
    assert materialized.authorization_materialization_frontier == ()
    assert materialized.materialized_authorized_step_refs == (_ref("irr.work_step", "inspect"),)


def test_deny_constrain_require_review_remain_distinct_and_do_not_create_authorization_transition() -> None:
    for kind, expected_attr in (
        (GovernanceDecisionKind.DENY, "denied_step_refs"),
        (GovernanceDecisionKind.CONSTRAIN, "constrained_step_refs"),
        (GovernanceDecisionKind.REQUIRE_REVIEW, "review_required_step_refs"),
    ):
        plan = _plan("inspect", label=f"plan-{kind.value}")
        requirement, evaluation = _unique_evaluation(plan, "inspect", event=kind.value)
        proposal = _proposal(plan, (evaluation,), event=f"proposal-{kind.value}")
        component = _component(
            kind,
            (_ref("irr.work_step", "inspect"),),
            label=kind.value,
        )
        decision = GovernanceDecision(
            _governance_attr(f"decision-{kind.value}"),
            proposal,
            (component,),
            f"External Governance returned {kind.value}.",
        )
        frontier = orchestrate_capability_governance(
            plan,
            capability_requirements=(requirement,),
            capability_evaluations=(evaluation,),
            work_proposals=(proposal,),
            governance_decisions=(decision,),
        )
        assert getattr(frontier, expected_attr) == (_ref("irr.work_step", "inspect"),)
        assert frontier.materialized_authorized_step_refs == ()
        assert frontier.authorization_materialization_frontier == ()


def test_competing_governance_decisions_for_one_proposal_fail_closed() -> None:
    plan = _plan("inspect")
    requirement, evaluation = _unique_evaluation(plan, "inspect")
    proposal = _proposal(plan, (evaluation,), event="proposal")
    component = _component(
        GovernanceDecisionKind.AUTHORIZE,
        (_ref("irr.work_step", "inspect"),),
        label="authorize",
    )
    first = GovernanceDecision(
        _governance_attr("decision-a"), proposal, (component,), "First decision."
    )
    second = GovernanceDecision(
        _governance_attr("decision-b"), proposal, (component,), "Second decision."
    )

    with pytest.raises(ValidationError, match="competing active GovernanceDecision"):
        orchestrate_capability_governance(
            plan,
            capability_requirements=(requirement,),
            capability_evaluations=(evaluation,),
            work_proposals=(proposal,),
            governance_decisions=(first, second),
        )


def test_orphan_authorization_fails_closed() -> None:
    plan = _plan("inspect", label="active")
    requirement, evaluation = _unique_evaluation(plan, "inspect", event="active")
    proposal = _proposal(plan, (evaluation,), event="proposal-active")

    other_plan = _plan("inspect", label="other")
    _, other_eval = _unique_evaluation(other_plan, "inspect", event="other")
    other_proposal = _proposal(other_plan, (other_eval,), event="proposal-other")
    component = _component(
        GovernanceDecisionKind.AUTHORIZE,
        (_ref("irr.work_step", "inspect"),),
        label="authorize-other",
    )
    other_decision = GovernanceDecision(
        _governance_attr("decision-other"),
        other_proposal,
        (component,),
        "Other decision.",
    )
    orphan = Authorization(other_decision, component.component_ref)

    with pytest.raises(ValidationError, match="orphaned from the active GovernanceDecision"):
        orchestrate_capability_governance(
            plan,
            capability_requirements=(requirement,),
            capability_evaluations=(evaluation,),
            work_proposals=(proposal,),
            authorizations=(orphan,),
        )


def test_input_order_does_not_create_capability_or_governance_precedence() -> None:
    plan = _plan("alpha", "beta", label="order")
    requirements, evaluations = _two_step_evaluations(plan)
    alpha_proposal = _proposal(plan, (evaluations[0],), event="proposal-alpha")
    beta_proposal = _proposal(plan, (evaluations[1],), event="proposal-beta")

    first = orchestrate_capability_governance(
        plan,
        capability_requirements=requirements,
        capability_evaluations=evaluations,
        work_proposals=(alpha_proposal, beta_proposal),
    )
    second = orchestrate_capability_governance(
        plan,
        capability_requirements=tuple(reversed(requirements)),
        capability_evaluations=tuple(reversed(evaluations)),
        work_proposals=(beta_proposal, alpha_proposal),
    )

    assert first == second
    assert first.governance_pending_proposals == second.governance_pending_proposals
