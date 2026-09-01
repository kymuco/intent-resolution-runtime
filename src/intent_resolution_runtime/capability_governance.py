from __future__ import annotations

from dataclasses import dataclass, field

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


def _normalize_refs(value: object, *, field: str) -> tuple[StableRef, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is StableRef for item in value):
        raise ValidationError(f"{field} must contain StableRef values")
    refs = tuple(value)
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicates")
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
class _CapabilityGovernanceState:
    capability_disposition_required_step_refs: tuple[StableRef, ...]
    pending_capability_requirements: tuple[CapabilityRequirement, ...]
    capability_matches: tuple[CapabilityMatch, ...]
    capability_issues: tuple[CapabilityMatchIssue, ...]
    proposal_disposition_required_step_refs: tuple[StableRef, ...]
    governance_pending_proposals: tuple[WorkProposal, ...]
    governance_unmentioned_step_refs: tuple[StableRef, ...]
    authorization_projection_pending_component_refs: tuple[StableRef, ...]
    materialized_authorized_step_refs: tuple[StableRef, ...]
    denied_step_refs: tuple[StableRef, ...]
    constrained_step_refs: tuple[StableRef, ...]
    review_required_step_refs: tuple[StableRef, ...]


def _derive_state(
    work_plan: WorkPlan,
    requirements: tuple[CapabilityRequirement, ...],
    evaluations: tuple[CapabilityMatchEvaluation, ...],
    proposals: tuple[WorkProposal, ...],
    decisions: tuple[GovernanceDecision, ...],
    grants: tuple[Authorization, ...],
) -> _CapabilityGovernanceState:
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
    active_evaluation_by_step: dict[StableRef, CapabilityMatchEvaluation] = {}
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
        active_evaluation_by_step[evaluation.requirement.step_ref] = evaluation
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

    return _CapabilityGovernanceState(
        capability_disposition_required_step_refs=_normalize_refs(
            tuple(capability_disposition), field="capability_disposition_required_step_refs"
        ),
        pending_capability_requirements=tuple(
            sorted(pending_requirements, key=lambda item: str(item.identity))
        ),
        capability_matches=tuple(sorted(matches, key=lambda item: str(item.identity))),
        capability_issues=tuple(sorted(issues, key=lambda item: str(item.identity))),
        proposal_disposition_required_step_refs=_normalize_refs(
            tuple(proposal_disposition), field="proposal_disposition_required_step_refs"
        ),
        governance_pending_proposals=tuple(
            sorted(governance_pending, key=lambda item: str(item.identity))
        ),
        governance_unmentioned_step_refs=_normalize_refs(
            tuple(unmentioned), field="governance_unmentioned_step_refs"
        ),
        authorization_projection_pending_component_refs=_normalize_refs(
            pending_authorization_components,
            field="authorization_projection_pending_component_refs",
        ),
        materialized_authorized_step_refs=_normalize_refs(
            tuple(materialized_authorized), field="materialized_authorized_step_refs"
        ),
        denied_step_refs=_normalize_refs(tuple(denied), field="denied_step_refs"),
        constrained_step_refs=_normalize_refs(
            tuple(constrained), field="constrained_step_refs"
        ),
        review_required_step_refs=_normalize_refs(
            tuple(review_required), field="review_required_step_refs"
        ),
    )


@dataclass(frozen=True, slots=True)
class CapabilityGovernanceFrontier:
    """Derived non-canonical M2.3 view over exact active M1.6 graph records."""

    work_plan: WorkPlan
    capability_requirements: tuple[CapabilityRequirement, ...] = ()
    capability_evaluations: tuple[CapabilityMatchEvaluation, ...] = ()
    work_proposals: tuple[WorkProposal, ...] = ()
    governance_decisions: tuple[GovernanceDecision, ...] = ()
    authorizations: tuple[Authorization, ...] = ()
    _state: _CapabilityGovernanceState = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if type(self.work_plan) is not WorkPlan:
            raise ValidationError("CapabilityGovernanceFrontier.work_plan must be a WorkPlan")
        requirements = _normalize_requirements(
            self.capability_requirements,
            field="CapabilityGovernanceFrontier.capability_requirements",
        )
        evaluations = _normalize_evaluations(
            self.capability_evaluations,
            field="CapabilityGovernanceFrontier.capability_evaluations",
        )
        proposals = _normalize_proposals(
            self.work_proposals,
            field="CapabilityGovernanceFrontier.work_proposals",
        )
        decisions = _normalize_decisions(
            self.governance_decisions,
            field="CapabilityGovernanceFrontier.governance_decisions",
        )
        grants = _normalize_authorizations(
            self.authorizations,
            field="CapabilityGovernanceFrontier.authorizations",
        )
        object.__setattr__(self, "capability_requirements", requirements)
        object.__setattr__(self, "capability_evaluations", evaluations)
        object.__setattr__(self, "work_proposals", proposals)
        object.__setattr__(self, "governance_decisions", decisions)
        object.__setattr__(self, "authorizations", grants)
        object.__setattr__(
            self,
            "_state",
            _derive_state(
                self.work_plan,
                requirements,
                evaluations,
                proposals,
                decisions,
                grants,
            ),
        )

    @property
    def capability_disposition_required_step_refs(self) -> tuple[StableRef, ...]:
        return self._state.capability_disposition_required_step_refs

    @property
    def pending_capability_requirements(self) -> tuple[CapabilityRequirement, ...]:
        return self._state.pending_capability_requirements

    @property
    def capability_matches(self) -> tuple[CapabilityMatch, ...]:
        return self._state.capability_matches

    @property
    def capability_issues(self) -> tuple[CapabilityMatchIssue, ...]:
        return self._state.capability_issues

    @property
    def proposal_disposition_required_step_refs(self) -> tuple[StableRef, ...]:
        return self._state.proposal_disposition_required_step_refs

    @property
    def governance_pending_proposals(self) -> tuple[WorkProposal, ...]:
        return self._state.governance_pending_proposals

    @property
    def governance_unmentioned_step_refs(self) -> tuple[StableRef, ...]:
        return self._state.governance_unmentioned_step_refs

    @property
    def authorization_projection_pending_component_refs(self) -> tuple[StableRef, ...]:
        return self._state.authorization_projection_pending_component_refs

    @property
    def materialized_authorized_step_refs(self) -> tuple[StableRef, ...]:
        return self._state.materialized_authorized_step_refs

    @property
    def denied_step_refs(self) -> tuple[StableRef, ...]:
        return self._state.denied_step_refs

    @property
    def constrained_step_refs(self) -> tuple[StableRef, ...]:
        return self._state.constrained_step_refs

    @property
    def review_required_step_refs(self) -> tuple[StableRef, ...]:
        return self._state.review_required_step_refs


def orchestrate_capability_governance(
    work_plan: WorkPlan,
    *,
    capability_requirements: tuple[CapabilityRequirement, ...] = (),
    capability_evaluations: tuple[CapabilityMatchEvaluation, ...] = (),
    work_proposals: tuple[WorkProposal, ...] = (),
    governance_decisions: tuple[GovernanceDecision, ...] = (),
    authorizations: tuple[Authorization, ...] = (),
) -> CapabilityGovernanceFrontier:
    """Derive M2.3 capability/Governance state from explicit exact M1.6 records.

    The function does not infer whether a WorkStep requires capability mediation or
    Governance, does not inspect capability availability, does not choose among multiple
    compatible capabilities, does not call Governance, and does not manufacture
    Authorization. Absence of explicit downstream records remains neutral disposition.
    """

    if type(work_plan) is not WorkPlan:
        raise ValidationError("orchestrate_capability_governance.work_plan must be a WorkPlan")
    return CapabilityGovernanceFrontier(
        work_plan=work_plan,
        capability_requirements=capability_requirements,
        capability_evaluations=capability_evaluations,
        work_proposals=work_proposals,
        governance_decisions=governance_decisions,
        authorizations=authorizations,
    )
