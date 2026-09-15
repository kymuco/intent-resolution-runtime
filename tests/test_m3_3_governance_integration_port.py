from __future__ import annotations

from dataclasses import replace
from inspect import signature

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
    GovernanceIntegrationError,
    GovernancePort,
    GovernanceReviewRequest,
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
    build_governance_review_request,
    invoke_governance,
    orchestrate_capability_governance,
)

RESOLVED = RecordIdentity("sha256", "3" * 64)
SOURCE_ID = RecordIdentity("sha256", "4" * 64)
AUTHORITY_CONTEXT_ID = RecordIdentity("sha256", "5" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _proposal(label: str = "primary") -> WorkProposal:
    plan_ref = _ref("irr.work_plan", f"inspect-{label}")
    step_ref = _ref("irr.work_step", f"inspect-{label}")
    completion = "Return the bounded workspace inspection result."
    step = WorkStep(
        RESOLVED,
        plan_ref,
        step_ref,
        "workspace.inspect",
        f"workspace:{label}",
        (),
        (),
        (),
        WorkContinuationMode.NONE,
        completion,
        f"Inspect bounded workspace {label}.",
    )
    plan = WorkPlan(
        RESOLVED,
        plan_ref,
        (step,),
        "Complete the bounded inspection plan.",
        f"Inspection plan {label}.",
    )
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", f"workspace-{label}"),
        "filesystem.path_scope",
        f"workspace:{label}",
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
        _ref("irr.capability_scope_requirement", f"workspace-{label}"),
        "filesystem.path_scope",
        "Invocation must remain inside one bounded workspace.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", f"workspace.inspect.{label}"),
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
        _ref("irr.capability_catalog", f"governance-{label}"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", f"catalog-{label}"),
        ),
        "Exact bounded Governance planning surface.",
        (descriptor,),
        "Capability Governance test snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "exact-v1"),
            _ref("irr.event", f"match-{label}"),
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
        "Exact match for bounded workspace inspection.",
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", f"evaluation-{label}"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for Governance.",
    )
    material = WorkProposalMaterial(
        _ref("irr.work_proposal_material", f"resource-{label}"),
        WorkProposalMaterialKind.AFFECTED_RESOURCE,
        (step_ref,),
        _ref("irr.source", "proposal-admission"),
        SOURCE_ID,
        f"workspace:{label}",
        "The bounded workspace is authority-relevant affected-resource material.",
    )
    return WorkProposal(
        WorkProposalAttribution(
            _ref("irr.proposer", "irr-core"),
            _ref("irr.event", f"proposal-{label}"),
        ),
        plan,
        (ProposedWorkStep(step_ref, evaluation),),
        (material,),
        "Bounded inspection work proposed to external Governance.",
    )


def _request(
    proposal: WorkProposal,
    *,
    label: str = "primary",
) -> GovernanceReviewRequest:
    return build_governance_review_request(
        governance_ref=_ref("irr.governance", f"host-policy-{label}"),
        decision_event_ref=_ref("irr.event", f"governance-decision-{label}"),
        authority_context_ref=_ref("irr.authority_context", f"authority-{label}"),
        authority_context_identity=AUTHORITY_CONTEXT_ID,
        proposal=proposal,
    )


def _decision(
    request: GovernanceReviewRequest,
    *,
    kind: GovernanceDecisionKind = GovernanceDecisionKind.AUTHORIZE,
) -> GovernanceDecision:
    component = GovernanceDecisionComponent(
        _ref("irr.governance_component", f"component-{kind.value}"),
        kind,
        (request.proposal.proposed_steps[0].step_ref,),
        (),
        f"Governance returned {kind.value} for the exact proposed step.",
    )
    return GovernanceDecision(
        GovernanceDecisionAttribution(
            request.governance_ref,
            request.decision_event_ref,
            request.authority_context_ref,
            request.authority_context_identity,
        ),
        request.proposal,
        (component,),
        "External Governance reviewed the exact WorkProposal.",
    )


class _StaticGovernance:
    def __init__(self, decision: GovernanceDecision) -> None:
        self._decision = decision
        self.requests: list[GovernanceReviewRequest] = []

    def review(self, request: GovernanceReviewRequest) -> GovernanceDecision:
        self.requests.append(request)
        return self._decision


class _WrongTypeGovernance:
    def review(self, request: GovernanceReviewRequest) -> object:
        return object()


class _ExplodingGovernance:
    def review(self, request: GovernanceReviewRequest) -> GovernanceDecision:
        raise RuntimeError("Governance transport unavailable")


def test_request_binds_exact_proposal_occurrence_and_authority_context() -> None:
    proposal = _proposal()
    request = _request(proposal)

    assert request.proposal is proposal
    assert request.governance_ref == _ref("irr.governance", "host-policy-primary")
    assert request.decision_event_ref == _ref(
        "irr.event", "governance-decision-primary"
    )
    assert request.authority_context_ref == _ref(
        "irr.authority_context", "authority-primary"
    )
    assert request.authority_context_identity == AUTHORITY_CONTEXT_ID
    assert request.decision_event_ref != proposal.attribution.proposal_event_ref


def test_request_has_no_ambient_authority_or_execution_surface() -> None:
    request = _request(_proposal())

    for forbidden in (
        "authorization",
        "authorized",
        "approved",
        "permission",
        "principal",
        "user",
        "session",
        "policy_engine",
        "repository",
        "history_repository",
        "executor",
        "execute",
        "capability_attempt",
    ):
        assert not hasattr(request, forbidden)


def test_governance_port_is_review_only() -> None:
    parameters = signature(GovernancePort.review).parameters

    assert tuple(parameters) == ("self", "request")
    for forbidden in (
        "authorize",
        "materialize_authorization",
        "execute",
        "invoke",
        "retrieve",
        "search",
    ):
        assert not hasattr(GovernancePort, forbidden)


def test_matching_governance_decision_crosses_boundary_unchanged() -> None:
    proposal = _proposal("valid")
    request = _request(proposal, label="valid")
    expected = _decision(request)
    governance = _StaticGovernance(expected)

    actual = invoke_governance(
        governance,
        request,
        proposal=proposal,
    )

    assert isinstance(governance, GovernancePort)
    assert actual is expected
    assert governance.requests == [request]
    assert actual.proposal is proposal


def test_forged_request_with_foreign_proposal_fails_before_governance_call() -> None:
    source = _proposal("source")
    foreign = _proposal("foreign")
    forged = GovernanceReviewRequest(
        governance_ref=_ref("irr.governance", "host-policy"),
        decision_event_ref=_ref("irr.event", "decision-forged"),
        authority_context_ref=_ref("irr.authority_context", "authority"),
        authority_context_identity=AUTHORITY_CONTEXT_ID,
        proposal=foreign,
    )
    governance = _StaticGovernance(_decision(forged))

    with pytest.raises(ValidationError, match="exact source WorkProposal"):
        invoke_governance(
            governance,
            forged,
            proposal=source,
        )

    assert governance.requests == []


def test_governance_decision_with_foreign_proposal_fails_closed() -> None:
    proposal = _proposal("source")
    request = _request(proposal, label="source")
    foreign_request = _request(_proposal("foreign"), label="foreign")
    foreign_decision = _decision(foreign_request)

    with pytest.raises(GovernanceIntegrationError, match="foreign WorkProposal"):
        invoke_governance(
            _StaticGovernance(foreign_decision),
            request,
            proposal=proposal,
        )


@pytest.mark.parametrize(
    ("field", "replacement_value", "message"),
    [
        (
            "governance_ref",
            _ref("irr.governance", "foreign"),
            "wrong governance_ref",
        ),
        (
            "decision_event_ref",
            _ref("irr.event", "foreign-decision"),
            "wrong decision_event_ref",
        ),
        (
            "authority_context_ref",
            _ref("irr.authority_context", "foreign"),
            "wrong authority_context_ref",
        ),
        (
            "authority_context_identity",
            RecordIdentity("sha256", "8" * 64),
            "wrong authority_context_identity",
        ),
    ],
)
def test_governance_decision_attribution_mismatch_fails_closed(
    field: str,
    replacement_value: object,
    message: str,
) -> None:
    proposal = _proposal(field)
    request = _request(proposal, label=field)
    decision = _decision(request)
    wrong_attribution = replace(
        decision.attribution,
        **{field: replacement_value},
    )
    wrong_decision = replace(decision, attribution=wrong_attribution)

    with pytest.raises(GovernanceIntegrationError, match=message):
        invoke_governance(
            _StaticGovernance(wrong_decision),
            request,
            proposal=proposal,
        )


def test_governance_must_return_exact_governance_decision() -> None:
    proposal = _proposal("wrong-type")
    request = _request(proposal, label="wrong-type")

    with pytest.raises(GovernanceIntegrationError, match="exact GovernanceDecision"):
        invoke_governance(
            _WrongTypeGovernance(),  # type: ignore[arg-type]
            request,
            proposal=proposal,
        )


def test_transport_failure_is_not_converted_into_semantic_decision() -> None:
    proposal = _proposal("transport")
    request = _request(proposal, label="transport")

    with pytest.raises(RuntimeError, match="Governance transport unavailable"):
        invoke_governance(
            _ExplodingGovernance(),
            request,
            proposal=proposal,
        )


def test_authorize_decision_does_not_materialize_authorization_in_port() -> None:
    proposal = _proposal("separation")
    request = _request(proposal, label="separation")

    decision = invoke_governance(
        _StaticGovernance(_decision(request)),
        request,
        proposal=proposal,
    )

    assert type(decision) is GovernanceDecision
    assert not isinstance(decision, Authorization)
    for forbidden in (
        "authorized_step_refs",
        "conditions",
        "execute",
        "executor",
    ):
        assert not hasattr(decision, forbidden)


def test_m2_3_materializes_authorization_only_as_separate_transition() -> None:
    proposal = _proposal("m2-frontier")
    request = _request(proposal, label="m2-frontier")
    decision = invoke_governance(
        _StaticGovernance(_decision(request)),
        request,
        proposal=proposal,
    )
    evaluation = proposal.proposed_steps[0].capability_evaluation
    requirement = evaluation.requirement

    before = orchestrate_capability_governance(
        proposal.work_plan,
        capability_requirements=(requirement,),
        capability_evaluations=(evaluation,),
        work_proposals=(proposal,),
        governance_decisions=(decision,),
    )

    assert before.authorizations == ()
    assert before.materialized_authorized_step_refs == ()
    assert len(before.authorization_materialization_frontier) == 1
    eligible = before.authorization_materialization_frontier[0]
    assert type(eligible) is Authorization
    assert eligible.decision == decision

    after = orchestrate_capability_governance(
        proposal.work_plan,
        capability_requirements=(requirement,),
        capability_evaluations=(evaluation,),
        work_proposals=(proposal,),
        governance_decisions=(decision,),
        authorizations=(eligible,),
    )

    assert after.authorization_materialization_frontier == ()
    assert after.materialized_authorized_step_refs == eligible.authorized_step_refs


def test_separate_governance_occurrences_remain_distinct_attribution() -> None:
    proposal = _proposal("multiple")
    first_request = _request(proposal, label="one")
    second_request = _request(proposal, label="two")

    first = invoke_governance(
        _StaticGovernance(_decision(first_request)),
        first_request,
        proposal=proposal,
    )
    second = invoke_governance(
        _StaticGovernance(_decision(second_request)),
        second_request,
        proposal=proposal,
    )

    assert first.proposal == second.proposal
    assert first.attribution != second.attribution
    assert first.identity != second.identity
