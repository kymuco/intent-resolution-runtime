from __future__ import annotations

from dataclasses import replace

import pytest

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
    ValidationError,
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
        "Bounded workspace inspection capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "governance-test"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", "catalog-governance-001"),
        ),
        "Exact bounded Governance planning surface.",
        (descriptor,),
        "Capability Governance test snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "exact-v1"),
            _ref("irr.event", "match-governance-001"),
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
            _ref("irr.event", "evaluation-governance-001"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for Governance.",
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
            _ref("irr.event", "proposal-governance-001"),
        ),
        plan,
        (ProposedWorkStep(step_ref, evaluation),),
        (material,),
        "Bounded inspection work proposed to external Governance.",
    )


def _attribution(event: str = "decision-001") -> GovernanceDecisionAttribution:
    return GovernanceDecisionAttribution(
        _ref("irr.governance", "host-policy"),
        _ref("irr.event", event),
        _ref("irr.authority_context", "session-001"),
        AUTHORITY_CONTEXT_ID,
    )


def _directive(
    value: str = "one-use",
    semantic_type: str = "one_use",
) -> GovernanceDirective:
    return GovernanceDirective(
        _ref("irr.governance_directive", value),
        semantic_type,
        "proposal:inspect",
        "Authority applies to one downstream use of the exact authorized step.",
    )


def _component(
    proposal: WorkProposal,
    kind: GovernanceDecisionKind = GovernanceDecisionKind.AUTHORIZE,
    *,
    ref: str = "authorize-inspect",
    directives: tuple[GovernanceDirective, ...] = (),
) -> GovernanceDecisionComponent:
    return GovernanceDecisionComponent(
        _ref("irr.governance_component", ref),
        kind,
        (proposal.proposed_steps[0].step_ref,),
        directives,
        f"Governance {kind.value} decision for the exact proposed inspection step.",
    )


def test_authorize_component_materializes_separate_authorization() -> None:
    proposal = _proposal()
    condition = _directive()
    component = _component(proposal, directives=(condition,))
    decision = GovernanceDecision(
        _attribution(),
        proposal,
        (component,),
        "External Governance authorized the exact proposed step.",
    )
    authorization = Authorization(decision, component.component_ref)

    assert authorization.authorized_step_refs == component.step_refs
    assert authorization.conditions == (condition,)
    assert authorization.decision.proposal == proposal
    assert Authorization.from_json_bytes(authorization.canonical_bytes()) == authorization
    assert GovernanceDecision.from_json_bytes(decision.canonical_bytes()) == decision


def test_repeated_authorization_materialization_is_identity_idempotent() -> None:
    proposal = _proposal()
    component = _component(proposal, directives=(_directive(),))
    decision = GovernanceDecision(
        _attribution(),
        proposal,
        (component,),
        "External Governance authorized the exact proposed step.",
    )
    first = Authorization(decision, component.component_ref)
    second = Authorization(decision, component.component_ref)

    assert first == second
    assert first.identity == second.identity


@pytest.mark.parametrize(
    "kind",
    [
        GovernanceDecisionKind.DENY,
        GovernanceDecisionKind.CONSTRAIN,
        GovernanceDecisionKind.REQUIRE_REVIEW,
    ],
)
def test_non_authorize_components_cannot_materialize_authorization(
    kind: GovernanceDecisionKind,
) -> None:
    proposal = _proposal()
    directives = ()
    if kind in (GovernanceDecisionKind.CONSTRAIN, GovernanceDecisionKind.REQUIRE_REVIEW):
        directives = (_directive("directive", "semantic_constraint"),)
    component = _component(
        proposal,
        kind,
        ref=kind.value,
        directives=directives,
    )
    decision = GovernanceDecision(
        _attribution(),
        proposal,
        (component,),
        f"External Governance returned {kind.value}.",
    )
    with pytest.raises(ValidationError):
        Authorization(decision, component.component_ref)


def test_constrain_and_require_review_require_explicit_directives() -> None:
    proposal = _proposal()
    for kind in (
        GovernanceDecisionKind.CONSTRAIN,
        GovernanceDecisionKind.REQUIRE_REVIEW,
    ):
        with pytest.raises(ValidationError):
            _component(proposal, kind, ref=kind.value, directives=())


def test_deny_does_not_admit_directives_as_hidden_conditions() -> None:
    proposal = _proposal()
    with pytest.raises(ValidationError):
        _component(
            proposal,
            GovernanceDecisionKind.DENY,
            ref="deny",
            directives=(_directive(),),
        )


def test_governance_component_cannot_reference_unproposed_step() -> None:
    proposal = _proposal()
    component = GovernanceDecisionComponent(
        _ref("irr.governance_component", "authorize-other"),
        GovernanceDecisionKind.AUTHORIZE,
        (_ref("irr.work_step", "other"),),
        (),
        "Attempt to authorize a non-proposed step.",
    )
    with pytest.raises(ValidationError):
        GovernanceDecision(
            _attribution(),
            proposal,
            (component,),
            "Must fail closed.",
        )


def test_one_step_cannot_receive_two_decision_components_in_v1() -> None:
    proposal = _proposal()
    authorize = _component(proposal, ref="authorize")
    deny = _component(
        proposal,
        GovernanceDecisionKind.DENY,
        ref="deny",
    )
    with pytest.raises(ValidationError):
        GovernanceDecision(
            _attribution(),
            proposal,
            (authorize, deny),
            "Contradictory overlap must fail closed.",
        )


def test_decision_occurrence_must_differ_from_proposal_occurrence() -> None:
    proposal = _proposal()
    attribution = replace(
        _attribution(),
        decision_event_ref=proposal.attribution.proposal_event_ref,
    )
    with pytest.raises(ValidationError):
        GovernanceDecision(
            attribution,
            proposal,
            (_component(proposal),),
            "Same occurrence cannot be proposal and decision.",
        )


def test_authorization_component_must_belong_to_exact_decision() -> None:
    proposal = _proposal()
    component = _component(proposal)
    decision = GovernanceDecision(
        _attribution(),
        proposal,
        (component,),
        "Authorize exact proposal.",
    )
    with pytest.raises(ValidationError):
        Authorization(
            decision,
            _ref("irr.governance_component", "missing"),
        )


def test_canonical_order_of_directives_is_not_presentation_precedence() -> None:
    proposal = _proposal()
    a = _directive("a", "one_use")
    b = _directive("b", "provider_condition")
    component_left = _component(proposal, directives=(b, a))
    component_right = _component(proposal, directives=(a, b))
    assert component_left == component_right
    assert component_left.identity == component_right.identity


def test_authority_context_identity_and_exact_proposal_are_identity_covered() -> None:
    proposal = _proposal()
    component = _component(proposal)
    first = GovernanceDecision(
        _attribution(),
        proposal,
        (component,),
        "Authorize exact proposal.",
    )
    changed_context = replace(
        _attribution(),
        authority_context_identity=RecordIdentity("sha256", "6" * 64),
    )
    second = GovernanceDecision(
        changed_context,
        proposal,
        (component,),
        "Authorize exact proposal.",
    )
    changed_proposal = replace(
        proposal,
        description="Same represented work with a changed identity-covered description.",
    )
    changed_component = _component(changed_proposal)
    third = GovernanceDecision(
        _attribution("decision-002"),
        changed_proposal,
        (changed_component,),
        "Authorize exact proposal.",
    )

    assert first.identity != second.identity
    assert first.identity != third.identity


def test_governance_ir_types_are_closed() -> None:
    with pytest.raises(TypeError):
        class _BadAuthorization(Authorization):
            pass
