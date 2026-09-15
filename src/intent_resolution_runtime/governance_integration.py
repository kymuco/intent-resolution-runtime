from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .errors import IntentIRError, ValidationError
from .governance import GovernanceDecision
from .identity import RecordIdentity
from .intent import StableRef
from .work_proposal import WorkProposal


class GovernanceIntegrationError(IntentIRError):
    """Raised when external Governance violates the frozen M3.3 boundary."""


@dataclass(frozen=True, slots=True)
class GovernanceReviewRequest:
    """Explicit mechanism state for one external Governance review occurrence.

    This request is not canonical semantic history and does not itself grant authority.
    It binds one exact WorkProposal to one external Governance occurrence and one exact
    authority-context reference/identity supplied by the embedding Host/Governance
    mechanism.
    """

    governance_ref: StableRef
    decision_event_ref: StableRef
    authority_context_ref: StableRef
    authority_context_identity: RecordIdentity
    proposal: WorkProposal

    def __post_init__(self) -> None:
        if type(self.governance_ref) is not StableRef:
            raise ValidationError("GovernanceReviewRequest.governance_ref must be a StableRef")
        if type(self.decision_event_ref) is not StableRef:
            raise ValidationError(
                "GovernanceReviewRequest.decision_event_ref must be a StableRef"
            )
        if type(self.authority_context_ref) is not StableRef:
            raise ValidationError(
                "GovernanceReviewRequest.authority_context_ref must be a StableRef"
            )
        if type(self.authority_context_identity) is not RecordIdentity:
            raise ValidationError(
                "GovernanceReviewRequest.authority_context_identity must be a RecordIdentity"
            )
        if type(self.proposal) is not WorkProposal:
            raise ValidationError("GovernanceReviewRequest.proposal must be a WorkProposal")
        if self.decision_event_ref == self.proposal.attribution.proposal_event_ref:
            raise ValidationError(
                "Governance review decision occurrence must differ from proposal occurrence"
            )


@runtime_checkable
class GovernancePort(Protocol):
    """Narrow external Governance review surface.

    The port reviews an exact proposal under explicit authority-context attribution and
    returns a GovernanceDecision. It does not materialize Authorization and has no
    execution, retrieval, or IRR admission authority through this protocol.
    """

    def review(self, request: GovernanceReviewRequest) -> GovernanceDecision: ...


def build_governance_review_request(
    *,
    governance_ref: StableRef,
    decision_event_ref: StableRef,
    authority_context_ref: StableRef,
    authority_context_identity: RecordIdentity,
    proposal: WorkProposal,
) -> GovernanceReviewRequest:
    """Construct one explicit review request for exact already-proposed work."""

    return GovernanceReviewRequest(
        governance_ref=governance_ref,
        decision_event_ref=decision_event_ref,
        authority_context_ref=authority_context_ref,
        authority_context_identity=authority_context_identity,
        proposal=proposal,
    )


def _validate_request_source(
    request: GovernanceReviewRequest,
    *,
    proposal: WorkProposal,
) -> None:
    if type(proposal) is not WorkProposal:
        raise ValidationError("proposal must be a WorkProposal")
    if request.proposal != proposal:
        raise ValidationError(
            "Governance review request must preserve the exact source WorkProposal"
        )


def invoke_governance(
    governance: GovernancePort,
    request: GovernanceReviewRequest,
    *,
    proposal: WorkProposal,
) -> GovernanceDecision:
    """Invoke external Governance and validate exact decision binding.

    Governance/transport exceptions propagate as mechanism failures. A successful return
    is still only GovernanceDecision history. AUTHORIZE components remain separate from
    the M2.3 Authorization materialization transition.
    """

    if not isinstance(governance, GovernancePort):
        raise ValidationError("governance must satisfy GovernancePort")
    if type(request) is not GovernanceReviewRequest:
        raise ValidationError("request must be a GovernanceReviewRequest")
    _validate_request_source(request, proposal=proposal)

    decision = governance.review(request)
    if type(decision) is not GovernanceDecision:
        raise GovernanceIntegrationError(
            "Governance must return an exact GovernanceDecision"
        )
    if decision.proposal != request.proposal:
        raise GovernanceIntegrationError(
            "GovernanceDecision belongs to a foreign WorkProposal"
        )

    attribution = decision.attribution
    if attribution.governance_ref != request.governance_ref:
        raise GovernanceIntegrationError(
            "GovernanceDecision attribution has the wrong governance_ref"
        )
    if attribution.decision_event_ref != request.decision_event_ref:
        raise GovernanceIntegrationError(
            "GovernanceDecision attribution has the wrong decision_event_ref"
        )
    if attribution.authority_context_ref != request.authority_context_ref:
        raise GovernanceIntegrationError(
            "GovernanceDecision attribution has the wrong authority_context_ref"
        )
    if attribution.authority_context_identity != request.authority_context_identity:
        raise GovernanceIntegrationError(
            "GovernanceDecision attribution has the wrong authority_context_identity"
        )
    return decision


__all__ = (
    "GovernanceIntegrationError",
    "GovernancePort",
    "GovernanceReviewRequest",
    "build_governance_review_request",
    "invoke_governance",
)
