from __future__ import annotations

from intent_resolution_runtime import (
    Authorization,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
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
    StableRef,
    WorkContinuationMode,
    WorkPlan,
    WorkProposal,
    WorkProposalAttribution,
    WorkStep,
)
from intent_resolution_runtime.capability_governance import orchestrate_capability_governance


RESOLVED = RecordIdentity("sha256", "6" * 64)
AUTHORITY_CONTEXT = RecordIdentity("sha256", "7" * 64)


def ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def build_plan() -> WorkPlan:
    plan_ref = ref("irr.work_plan", "shared-component-ref")
    steps = tuple(
        WorkStep(
            resolved_intent_identity=RESOLVED,
            work_plan_ref=plan_ref,
            step_ref=ref("irr.work_step", name),
            operation=f"workspace.{name}",
            scope=f"workspace:{name}",
            inputs=(),
            outputs=(),
            depends_on=(),
            continuation=WorkContinuationMode.NONE,
            completion_contract=f"Return bounded {name} result.",
            description=f"Bounded {name} step.",
        )
        for name in ("alpha", "beta")
    )
    return WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=plan_ref,
        steps=steps,
        completion_contract="Complete alpha and beta.",
        description="Two independent steps.",
    )


def requirement_and_evaluation(
    plan: WorkPlan, name: str
) -> tuple[CapabilityRequirement, CapabilityMatchEvaluation]:
    step_ref = ref("irr.work_step", name)
    step = next(item for item in plan.steps if item.step_ref == step_ref)
    requested_scope = CapabilityRequestedScope(
        scope_ref=ref("irr.capability_requested_scope", name),
        semantic_type="filesystem.path_scope",
        value=step.scope,
        description=f"Scope for {name}.",
    )
    requirement = CapabilityRequirement(
        work_plan=plan,
        step_ref=step_ref,
        primary_scope_ref=requested_scope.scope_ref,
        requested_scopes=(requested_scope,),
        requested_effects=(),
        execution_boundary_requirements=(),
        description=f"Requirement for {name}.",
    )
    descriptor_scope = CapabilityScopeRequirement(
        requirement_ref=ref("irr.capability_scope_requirement", name),
        semantic_type="filesystem.path_scope",
        statement=f"Stay inside {name} scope.",
    )
    descriptor = CapabilityDescriptor(
        capability_ref=ref("irr.capability", f"{name}.local"),
        operation=step.operation,
        input_contracts=(),
        output_contracts=(),
        scope_requirements=(descriptor_scope,),
        effects=(),
        execution_boundaries=(),
        completion_contract=step.completion_contract,
        description=f"Capability for {name}.",
    )
    snapshot = CapabilityCatalogSnapshot(
        catalog_ref=ref("irr.capability_catalog", name),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=ref("irr.host", "test"),
            snapshot_event_ref=ref("irr.event", f"catalog-{name}"),
        ),
        scope_statement=f"Catalog for {name}.",
        descriptors=(descriptor,),
        description=f"Exact catalog for {name}.",
    )
    match = CapabilityMatch(
        attribution=CapabilityMatchAttribution(
            matcher_ref=ref("irr.matcher", "exact"),
            match_event_ref=ref("irr.event", f"match-{name}"),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        scope_matches=(
            CapabilityScopeMatch(
                requested_scope_ref=requested_scope.scope_ref,
                descriptor_scope_requirement_ref=descriptor_scope.requirement_ref,
            ),
        ),
        input_matches=(),
        output_matches=(),
        effect_matches=(),
        description=f"Exact match for {name}.",
    )
    evaluation = CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            evaluator_ref=ref("irr.evaluator", "exact"),
            evaluation_event_ref=ref("irr.event", f"evaluation-{name}"),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        compatible_matches=(match,),
        incompatible_assessments=(),
        description=f"Evaluation for {name}.",
    )
    return requirement, evaluation


def proposal(plan: WorkPlan, evaluation: CapabilityMatchEvaluation, name: str) -> WorkProposal:
    return WorkProposal(
        attribution=WorkProposalAttribution(
            proposer_ref=ref("irr.proposer", "test"),
            proposal_event_ref=ref("irr.event", f"proposal-{name}"),
        ),
        work_plan=plan,
        proposed_steps=(
            ProposedWorkStep(evaluation.requirement.step_ref, evaluation),
        ),
        authority_material=(),
        description=f"Proposal for {name}.",
    )


def decision(proposal_value: WorkProposal, name: str) -> GovernanceDecision:
    # Reusing this ref across distinct GovernanceDecision records is valid.
    component = GovernanceDecisionComponent(
        component_ref=ref("irr.governance_component", "authorize"),
        kind=GovernanceDecisionKind.AUTHORIZE,
        step_refs=(proposal_value.proposed_steps[0].step_ref,),
        directives=(),
        rationale=f"Authorize {name}.",
    )
    return GovernanceDecision(
        attribution=GovernanceDecisionAttribution(
            governance_ref=ref("irr.governance", "test"),
            decision_event_ref=ref("irr.event", f"decision-{name}"),
            authority_context_ref=ref("irr.authority_context", "session"),
            authority_context_identity=AUTHORITY_CONTEXT,
        ),
        proposal=proposal_value,
        components=(component,),
        description=f"Decision for {name}.",
    )


def test_same_component_ref_in_distinct_decisions_preserves_exact_authorization_identity() -> None:
    plan = build_plan()
    alpha_req, alpha_eval = requirement_and_evaluation(plan, "alpha")
    beta_req, beta_eval = requirement_and_evaluation(plan, "beta")
    alpha_proposal = proposal(plan, alpha_eval, "alpha")
    beta_proposal = proposal(plan, beta_eval, "beta")
    alpha_decision = decision(alpha_proposal, "alpha")
    beta_decision = decision(beta_proposal, "beta")

    frontier = orchestrate_capability_governance(
        plan,
        capability_requirements=(alpha_req, beta_req),
        capability_evaluations=(alpha_eval, beta_eval),
        work_proposals=(alpha_proposal, beta_proposal),
        governance_decisions=(alpha_decision, beta_decision),
    )

    expected = tuple(
        sorted(
            (
                Authorization(alpha_decision, ref("irr.governance_component", "authorize")),
                Authorization(beta_decision, ref("irr.governance_component", "authorize")),
            ),
            key=lambda item: str(item.identity),
        )
    )
    assert frontier.authorization_materialization_frontier == expected
    assert expected[0].identity != expected[1].identity

    admitted = expected[0]
    partially_materialized = orchestrate_capability_governance(
        plan,
        capability_requirements=(alpha_req, beta_req),
        capability_evaluations=(alpha_eval, beta_eval),
        work_proposals=(alpha_proposal, beta_proposal),
        governance_decisions=(alpha_decision, beta_decision),
        authorizations=(admitted,),
    )
    assert len(partially_materialized.authorization_materialization_frontier) == 1
    assert partially_materialized.authorization_materialization_frontier[0].identity != admitted.identity
