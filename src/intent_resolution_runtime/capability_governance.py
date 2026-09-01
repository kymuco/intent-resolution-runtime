from __future__ import annotations

from dataclasses import dataclass

from .capability_match import CapabilityMatch, CapabilityRequirement
from .capability_match_evaluation import (
    CapabilityMatchEvaluation,
    CapabilityMatchIssue,
    evaluate_capability_match_evaluation,
)
from .errors import ValidationError
from .governance import Authorization, GovernanceDecision, GovernanceDecisionKind
from .intent import StableRef
from .work import WorkPlan
from .work_proposal import WorkProposal


def _ref_key(value: StableRef) -> tuple[str, str]:
    return value.namespace, value.value


def _normalize_step_refs(value: object, *, field: str) -> tuple[StableRef, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is StableRef for item in value):
        raise ValidationError(f"{field} must contain StableRef values")
    refs = tuple(value)
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate step refs")
    return tuple(sorted(refs, key=_ref_key))


def _normalize_requirements(
    value: object, *, field: str
) -> tuple[CapabilityRequirement, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityRequirement for item in value):
        raise ValidationError(f"{field} must contain CapabilityRequirement values")
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate requirement identities")
    return tuple(sorted(items, key=lambda item: str(item.identity)))


def _normalize_evaluations(
    value: object, *, field: str
) -> tuple[CapabilityMatchEvaluation, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityMatchEvaluation for item in value):
        raise ValidationError(f"{field} must contain CapabilityMatchEvaluation values")
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate evaluation identities")
    return tuple(sorted(items, key=lambda item: str(item.identity)))


def _normalize_matches(value: object, *, field: str) -> tuple[CapabilityMatch, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityMatch for item in value):
        raise ValidationError(f"{field} must contain CapabilityMatch values")
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate match identities")
    return tuple(sorted(items, key=lambda item: str(item.identity)))


def _normalize_issues(value: object, *, field: str) -> tuple[CapabilityMatchIssue, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityMatchIssue for item in value):
        raise ValidationError(f"{field} must contain CapabilityMatchIssue values")
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate issue identities")
    return tuple(sorted(items, key=lambda item: str(item.identity)))


def _normalize_proposals(value: object, *, field: str) -> tuple[WorkProposal, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is WorkProposal for item in value):
        raise ValidationError(f"{field} must contain WorkProposal values")
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate WorkProposal identities")
    return tuple(sorted(items, key=lambda item: str(item.identity)))


def _normalize_decisions(
    value: object, *, field: str
) -> tuple[GovernanceDecision, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is GovernanceDecision for item in value):
        raise ValidationError(f"{field} must contain GovernanceDecision values")
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate GovernanceDecision identities")
    return tuple(sorted(items, key=lambda item: str(item.identity)))


def _normalize_authorizations(
    value: object, *, field: str
) -> tuple[Authorization, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is Authorization for item in value):
        raise ValidationError(f"{field} must contain Authorization values")
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate Authorization identities")
    return tuple(sorted(items, key=lambda item: str(item.identity)))


@dataclass(frozen=True, slots=True)
class CapabilityGovernanceFrontier:
    """Derived non-canonical M2.3 view over capability and Governance graph state."""

    work_plan: WorkPlan
    capability_disposition_required_step_refs: tuple[StableRef, ...] = ()
    pending_capability_requirements: tuple[CapabilityRequirement, ...] = ()
    capability_matches: tuple[CapabilityMatch, ...] = ()
    capability_issues: tuple[CapabilityMatchIssue, ...] = ()
    proposal_disposition_required_step_refs: tuple[StableRef, ...] = ()
    work_proposals: tuple[WorkProposal, ...] = ()
    governance_pending_proposals: tuple[WorkProposal, ...] = ()
    governance_decisions: tuple[GovernanceDecision, ...] = ()
    governance_unmentioned_step_refs: tuple[StableRef, ...] = ()
    authorization_projection_pending_component_refs: tuple[StableRef, ...] = ()
    authorizations: tuple[Authorization, ...] = ()
    materialized_authorized_step_refs: tuple[StableRef, ...] = ()
    denied_step_refs: tuple[StableRef, ...] = ()
    constrained_step_refs: tuple[StableRef, ...] = ()
    review_required_step_refs: tuple[StableRef, ...] = ()

    def __post_init__(self) -> None:
        if type(self.work_plan) is not WorkPlan:
            raise ValidationError("CapabilityGovernanceFrontier.work_plan must be a WorkPlan")

        for field_name in (
            "capability_disposition_required_step_refs",
            "proposal_disposition_required_step_refs",
            "governance_unmentioned_step_refs",
            "authorization_projection_pending_component_refs",
            "materialized_authorized_step_refs",
            "denied_step_refs",
            "constrained_step_refs",
            "review_required_step_refs",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_step_refs(getattr(self, field_name), field=f"CapabilityGovernanceFrontier.{field_name}"),
            )

        object.__setattr__(
            self,
            "pending_capability_requirements",
            _normalize_requirements(
                self.pending_capability_requirements,
                field="CapabilityGovernanceFrontier.pending_capability_requirements",
            ),
        )
        object.__setattr__(
            self,
            "capability_matches",
            _normalize_matches(
                self.capability_matches,
                field="CapabilityGovernanceFrontier.capability_matches",
            ),
        )
        object.__setattr__(
            self,
            "capability_issues",
            _normalize_issues(
                self.capability_issues,
                field="CapabilityGovernanceFrontier.capability_issues",
            ),
        )
        object.__setattr__(
            self,
            "work_proposals",
            _normalize_proposals(
                self.work_proposals,
                field="CapabilityGovernanceFrontier.work_proposals",
            ),
        )
        object.__setattr__(
            self,
            "governance_pending_proposals",
            _normalize_proposals(
                self.governance_pending_proposals,
                field="CapabilityGovernanceFrontier.governance_pending_proposals",
            ),
        )
        object.__setattr__(
            self,
            "governance_decisions",
            _normalize_decisions(
                self.governance_decisions,
                field="CapabilityGovernanceFrontier.governance_decisions",
            ),
        )
        object.__setattr__(
            self,
            "authorizations",
            _normalize_authorizations(
                self.authorizations,
                field="CapabilityGovernanceFrontier.authorizations",
            ),
        )

        plan_step_refs = {step.step_ref for step in self.work_plan.steps}
        for field_name in (
            "capability_disposition_required_step_refs",
            "proposal_disposition_required_step_refs",
            "governance_unmentioned_step_refs",
            "materialized_authorized_step_refs",
            "denied_step_refs",
            "constrained_step_refs",
            "review_required_step_refs",
        ):
            if not set(getattr(self, field_name)).issubset(plan_step_refs):
                raise ValidationError(
                    f"CapabilityGovernanceFrontier.{field_name} must reference WorkPlan steps"
                )



def orchestrate_capability_governance(
    work_plan: WorkPlan,
    *,
    capability_requirements: tuple[CapabilityRequirement, ...] = (),
    capability_evaluations: tuple[CapabilityMatchEvaluation, ...] = (),
    work_proposals: tuple[WorkProposal, ...] = (),
    governance_decisions: tuple[GovernanceDecision, ...] = (),
    authorizations: tuple[Authorization, ...] = (),
) -> CapabilityGovernanceFrontier:
    """Derive a complete M2.3 capability/Governance frontier from explicit M1.6 records.

    The function does not infer whether a WorkStep requires capability mediation or
    Governance, does not inspect capability availability, does not choose among multiple
    compatible capabilities, does not call Governance, and does not manufacture
    Authorization. Absence of explicit downstream records remains neutral disposition.
    """

    if type(work_plan) is not WorkPlan:
        raise ValidationError("orchestrate_capability_governance.work_plan must be a WorkPlan")

    requirements = _normalize_requirements(
        capability_requirements,
        field="orchestrate_capability_governance.capability_requirements",
    )
    evaluations = _normalize_evaluations(
        capability_evaluations,
        field="orchestrate_capability_governance.capability_evaluations",
    )
    proposals = _normalize_proposals(
        work_proposals,
        field="orchestrate_capability_governance.work_proposals",
    )
    decisions = _normalize_decisions(
        governance_decisions,
        field="orchestrate_capability_governance.governance_decisions",
    )
    grants = _normalize_authorizations(
        authorizations,
        field="orchestrate_capability_governance.authorizations",
    )

    plan_step_refs = {step.step_ref for step in work_plan.steps}

    requirements_by_step: dict[StableRef, CapabilityRequirement] = {}
    requirements_by_identity = {}
    for requirement in requirements:
        if requirement.work_plan != work_plan:
            raise ValidationError(
                "CapabilityRequirement must preserve the exact active WorkPlan"
            )
        if requirement.step_ref in requirements_by_step:
            raise ValidationError(
                "capability/Governance graph must not contain competing CapabilityRequirement records for one WorkStep"
            )
        requirements_by_step[requirement.step_ref] = requirement
        requirements_by_identity[requirement.identity] = requirement

    evaluations_by_requirement = {}
    matches: list[CapabilityMatch] = []
    issues: list[CapabilityMatchIssue] = []
    for evaluation in evaluations:
        active_requirement = requirements_by_identity.get(evaluation.requirement.identity)
        if active_requirement is None:
            raise ValidationError(
                "CapabilityMatchEvaluation is orphaned from the active CapabilityRequirement set"
            )
        if evaluation.requirement != active_requirement:
            raise ValidationError(
                "CapabilityMatchEvaluation must preserve the exact active CapabilityRequirement"
            )
        if evaluation.requirement.identity in evaluations_by_requirement:
            raise ValidationError(
                "capability/Governance graph must not contain competing active CapabilityMatchEvaluation records for one requirement"
            )
        evaluations_by_requirement[evaluation.requirement.identity] = evaluation
        result = evaluate_capability_match_evaluation(evaluation)
        if type(result) is CapabilityMatch:
            matches.append(result)
        else:
            issues.append(result)

    pending_requirements = tuple(
        requirement
        for requirement in requirements
        if requirement.identity not in evaluations_by_requirement
    )
    capability_disposition = tuple(
        step_ref for step_ref in plan_step_refs if step_ref not in requirements_by_step
    )

    active_evaluation_by_step = {
        evaluation.requirement.step_ref: evaluation for evaluation in evaluations
    }
    matched_step_refs = {match.requirement.step_ref for match in matches}

    proposal_by_step: dict[StableRef, WorkProposal] = {}
    proposals_by_identity = {proposal.identity: proposal for proposal in proposals}
    for proposal in proposals:
        if proposal.work_plan != work_plan:
            raise ValidationError("WorkProposal must preserve the exact active WorkPlan")
        for proposed_step in proposal.proposed_steps:
            active_evaluation = active_evaluation_by_step.get(proposed_step.step_ref)
            if active_evaluation is None:
                raise ValidationError(
                    "WorkProposal proposed step is orphaned from the active CapabilityMatchEvaluation set"
                )
            if proposed_step.capability_evaluation != active_evaluation:
                raise ValidationError(
                    "WorkProposal must preserve the exact active CapabilityMatchEvaluation"
                )
            if proposed_step.step_ref in proposal_by_step:
                raise ValidationError(
                    "capability/Governance graph must not contain overlapping active WorkProposal coverage for one WorkStep"
                )
            proposal_by_step[proposed_step.step_ref] = proposal

    proposal_disposition = tuple(
        step_ref for step_ref in matched_step_refs if step_ref not in proposal_by_step
    )

    decisions_by_proposal = {}
    for decision in decisions:
        active_proposal = proposals_by_identity.get(decision.proposal.identity)
        if active_proposal is None:
            raise ValidationError(
                "GovernanceDecision is orphaned from the active WorkProposal set"
            )
        if decision.proposal != active_proposal:
            raise ValidationError(
                "GovernanceDecision must preserve the exact active WorkProposal"
            )
        if decision.proposal.identity in decisions_by_proposal:
            raise ValidationError(
                "capability/Governance graph must not contain competing active GovernanceDecision records for one WorkProposal"
            )
        decisions_by_proposal[decision.proposal.identity] = decision

    governance_pending = tuple(
        proposal for proposal in proposals if proposal.identity not in decisions_by_proposal
    )

    unmentioned: set[StableRef] = set()
    authorize_components = {}
    denied: set[StableRef] = set()
    constrained: set[StableRef] = set()
    review_required: set[StableRef] = set()
    for decision in decisions:
        proposed_refs = {item.step_ref for item in decision.proposal.proposed_steps}
        covered: set[StableRef] = set()
        for component in decision.components:
            covered.update(component.step_refs)
            if component.kind is GovernanceDecisionKind.AUTHORIZE:
                authorize_components[(decision.identity, component.component_ref)] = component
            elif component.kind is GovernanceDecisionKind.DENY:
                denied.update(component.step_refs)
            elif component.kind is GovernanceDecisionKind.CONSTRAIN:
                constrained.update(component.step_refs)
            elif component.kind is GovernanceDecisionKind.REQUIRE_REVIEW:
                review_required.update(component.step_refs)
            else:  # pragma: no cover - exhaustive enum guard
                raise AssertionError("unsupported GovernanceDecisionKind")
        unmentioned.update(proposed_refs - covered)

    grants_by_component = {}
    for grant in grants:
        active_decision = decisions_by_proposal.get(grant.decision.proposal.identity)
        if active_decision is None or grant.decision != active_decision:
            raise ValidationError(
                "Authorization is orphaned from the active GovernanceDecision set"
            )
        key = (grant.decision.identity, grant.component_ref)
        if key not in authorize_components:
            raise ValidationError(
                "Authorization must reference an active authorize GovernanceDecision component"
            )
        if key in grants_by_component:
            raise ValidationError(
                "capability/Governance graph must not contain duplicate active Authorization projection for one authorize component"
            )
        grants_by_component[key] = grant

    pending_authorization_components = tuple(
        component.component_ref
        for key, component in authorize_components.items()
        if key not in grants_by_component
    )
    materialized_authorized: set[StableRef] = set()
    for grant in grants:
        materialized_authorized.update(grant.authorized_step_refs)

    return CapabilityGovernanceFrontier(
        work_plan=work_plan,
        capability_disposition_required_step_refs=capability_disposition,
        pending_capability_requirements=pending_requirements,
        capability_matches=tuple(matches),
        capability_issues=tuple(issues),
        proposal_disposition_required_step_refs=proposal_disposition,
        work_proposals=proposals,
        governance_pending_proposals=governance_pending,
        governance_decisions=decisions,
        governance_unmentioned_step_refs=tuple(unmentioned),
        authorization_projection_pending_component_refs=pending_authorization_components,
        authorizations=grants,
        materialized_authorized_step_refs=tuple(materialized_authorized),
        denied_step_refs=tuple(denied),
        constrained_step_refs=tuple(constrained),
        review_required_step_refs=tuple(review_required),
    )
