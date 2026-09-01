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
    GovernanceDirective,
    ProposedWorkStep,
    RecordIdentity,
    StableRef,
    WorkContinuationMode,
    WorkPlan,
    WorkProposal,
    WorkProposalAttribution,
    WorkProposalMaterial,
    WorkProposalMaterialKind,
    WorkStep,
)


RESOLVED = RecordIdentity("sha256", "3" * 64)
SOURCE_ID = RecordIdentity("sha256", "4" * 64)
AUTHORITY_CONTEXT_ID = RecordIdentity("sha256", "5" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _proposal() -> WorkProposal:
    plan_ref = _ref("irr.work_plan", "inspect-001")
    step_ref = _ref("irr.work_step", "inspect")
    completion = "Return the bounded workspace inspection result."
    step = WorkStep(
        RESOLVED,
        plan_ref,
        step_ref,
        "workspace.inspect",
        "workspace:project",
        (),
        (),
        (),
        WorkContinuationMode.NONE,
        completion,
        "Inspect one bounded workspace.",
    )
    plan = WorkPlan(
        RESOLVED,
        plan_ref,
        (step,),
        "Complete the bounded inspection plan.",
        "Inspection plan.",
    )
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "workspace"),
        "filesystem.path_scope",
        "workspace:project",
        "Bounded workspace scope.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        requested_scope.scope_ref,
        (requested_scope,),
        (),
        (),
        "Exact inspection capability requirement.",
    )
    descriptor_scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "workspace-workspace.inspect.local"),
        "filesystem.path_scope",
        "Invocation must remain inside one bounded workspace.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "workspace.inspect.local"),
        "workspace.inspect",
        (),
        (),
        (descriptor_scope,),
        (),
        (),
        completion,
        "Bounded workspace inspection capability workspace.inspect.local.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "proposal-test"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", "catalog-proposal-001"),
        ),
        "Exact bounded proposal planning surface.",
        (descriptor,),
        "Capability proposal test snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "exact-v1"),
            _ref("irr.event", "match-proposal-001"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityScopeMatch(
                requested_scope.scope_ref,
                descriptor_scope.requirement_ref,
            ),
        ),
        (),
        (),
        (),
        "Exact match for workspace.inspect.local.",
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", "evaluation-proposal-001"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for Governance proposal materialization.",
    )
    material = WorkProposalMaterial(
        _ref("irr.work_proposal_material", "resource"),
        WorkProposalMaterialKind.AFFECTED_RESOURCE,
        (step_ref,),
        _ref("irr.source", "proposal-admission"),
        SOURCE_ID,
        "workspace:project",
        "The bounded workspace is authority-relevant affected-resource material.",
    )
    return WorkProposal(
        WorkProposalAttribution(
            _ref("irr.proposer", "irr-core"),
            _ref("irr.event", "proposal-001"),
        ),
        plan,
        (ProposedWorkStep(step_ref, evaluation),),
        (material,),
        "Bounded inspection work proposed to external Governance.",
    )


def _fixture() -> tuple[
    WorkProposal,
    GovernanceDecisionAttribution,
    GovernanceDirective,
    GovernanceDecisionComponent,
    GovernanceDecision,
    Authorization,
]:
    proposal = _proposal()
    attribution = GovernanceDecisionAttribution(
        _ref("irr.governance", "host-policy"),
        _ref("irr.event", "decision-golden-001"),
        _ref("irr.authority_context", "session-001"),
        AUTHORITY_CONTEXT_ID,
    )
    directive = GovernanceDirective(
        _ref("irr.governance_directive", "one-use"),
        "one_use",
        "proposal:inspect",
        "Authority applies to one downstream use of the exact authorized step.",
    )
    component = GovernanceDecisionComponent(
        _ref("irr.governance_component", "authorize-inspect"),
        GovernanceDecisionKind.AUTHORIZE,
        (proposal.proposed_steps[0].step_ref,),
        (directive,),
        "Governance authorize decision for the exact proposed inspection step.",
    )
    decision = GovernanceDecision(
        attribution,
        proposal,
        (component,),
        "External Governance authorized the exact proposed step.",
    )
    authorization = Authorization(decision, component.component_ref)
    return proposal, attribution, directive, component, decision, authorization


def test_m16c2_governance_authorization_golden_digests_are_frozen() -> None:
    proposal, attribution, directive, component, decision, authorization = _fixture()
    expected = {
        "proposal": "6681affd3bd666e63d34a609f4750755232167f5e5a8f1d724cffaeafb4a395a",
        "attribution": "9b195cef7edb27cd6fb1a7298a74c53647eaddd530970f6184b85a9ec875ff64",
        "directive": "8ef10f2c67a34abdc53d3951b4ea7ea5db3fef6de460e7177145956e25ed3a39",
        "component": "5aa7ef09b5b7a1c007bc18c9a58137d304e1e4b3dbdd005ba3b1b5eb5aad5a6b",
        "decision": "40d754c9f2e1282b42659a3570fdf043098571f606de74f9cebd0bcc07edd63f",
        "authorization": "fb2a8fd3ba1bc790a1a3e879a2e96d594430a3f31ecf07658888fc938d19d935",
    }
    actual = {
        "proposal": proposal.identity.digest,
        "attribution": attribution.identity.digest,
        "directive": directive.identity.digest,
        "component": component.identity.digest,
        "decision": decision.identity.digest,
        "authorization": authorization.identity.digest,
    }
    assert actual == expected


def test_m16c2_governance_authorization_golden_round_trip_preserves_identity() -> None:
    _, attribution, directive, component, decision, authorization = _fixture()
    decoded_attribution = GovernanceDecisionAttribution.from_json_bytes(
        attribution.canonical_bytes()
    )
    decoded_directive = GovernanceDirective.from_json_bytes(directive.canonical_bytes())
    decoded_component = GovernanceDecisionComponent.from_json_bytes(
        component.canonical_bytes()
    )
    decoded_decision = GovernanceDecision.from_json_bytes(decision.canonical_bytes())
    decoded_authorization = Authorization.from_json_bytes(authorization.canonical_bytes())

    assert decoded_attribution == attribution
    assert decoded_attribution.identity == attribution.identity
    assert decoded_directive == directive
    assert decoded_directive.identity == directive.identity
    assert decoded_component == component
    assert decoded_component.identity == component.identity
    assert decoded_decision == decision
    assert decoded_decision.identity == decision.identity
    assert decoded_authorization == authorization
    assert decoded_authorization.identity == authorization.identity


def test_m16c2_authorization_materialization_is_identity_idempotent() -> None:
    _, _, _, component, decision, authorization = _fixture()
    repeated = Authorization(decision, component.component_ref)
    assert repeated == authorization
    assert repeated.canonical_bytes() == authorization.canonical_bytes()
    assert repeated.identity == authorization.identity
