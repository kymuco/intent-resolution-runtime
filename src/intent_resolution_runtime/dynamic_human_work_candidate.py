"""G7A.4: bridge one unadmitted dynamic plan to existing IRR M32 candidacy.

This is a lineage/type boundary ONLY. Python records cannot authenticate a
HUMAN gesture, a Host policy revision or a Core consent: the calling trusted
Host must verify those independently, including current revocation state.
No M32 admitter, capability admission, Governance, Authorization or executor
is called here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bound_work_plan import (
    BoundWorkPlanError,
    UnadmittedBoundWorkPlan,
    assert_current_unadmitted_work_plan,
)
from .candidate_planning_surface import CandidatePlanningSurface
from .context import ContextEnvelope
from .intent import IntentRequest, OriginKind
from .resolution import ResolvedIntent
from .work_disposition import (
    CandidateWorkDisposition,
    WorkDispositionKind,
    WorkDispositionProposalAttribution,
)

IRR_G7A4_HUMAN_DISPOSITION_CONTRACT_VERSION = "1"


class DynamicHumanWorkCandidateError(ValueError):
    """Unsafe or stale lineage cannot be treated as a proposal for M32."""


@dataclass(frozen=True, slots=True)
class PendingDynamicHumanWork:
    """Read-only M32 input, NOT an AdmittedWorkPlan or Governance grant."""

    intent_request: IntentRequest
    context_envelope: ContextEnvelope
    resolved_intent: ResolvedIntent
    bound_work: UnadmittedBoundWorkPlan
    candidate: CandidateWorkDisposition

    @property
    def admitted(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


def _check_lineage(
    *,
    request: IntentRequest,
    context: ContextEnvelope,
    resolved: ResolvedIntent,
    bound: UnadmittedBoundWorkPlan,
    surface: CandidatePlanningSurface,
) -> None:
    if (
        type(request) is not IntentRequest
        or type(context) is not ContextEnvelope
        or type(resolved) is not ResolvedIntent
        or type(bound) is not UnadmittedBoundWorkPlan
        or type(surface) is not CandidatePlanningSurface
    ):
        raise DynamicHumanWorkCandidateError("exact original IRR types required")
    if request.origin.kind is not OriginKind.HUMAN:
        raise DynamicHumanWorkCandidateError("non-HUMAN origin is not admissible")
    if request.origin.actor_ref != request.principal_ref:
        raise DynamicHumanWorkCandidateError(
            "HUMAN actor/principal attribution mismatch"
        )
    if (
        context.intent_request_identity != request.identity
        or resolved.intent_request_identity != request.identity
        or resolved.context_envelope_identity != context.identity
    ):
        raise DynamicHumanWorkCandidateError(
            "resolved intent lacks exact original HUMAN request/context lineage"
        )
    if (
        bound.work_plan.resolved_intent_identity != resolved.identity
        or bound.actor_ref != request.principal_ref
        or surface.actor_ref != request.principal_ref
    ):
        raise DynamicHumanWorkCandidateError(
            "dynamic plan or policy actor differs from resolved HUMAN intent"
        )
    try:
        assert_current_unadmitted_work_plan(bound, surface)
    except BoundWorkPlanError as exc:
        raise DynamicHumanWorkCandidateError(
            "dynamic plan is stale or not present in current catalog/policy"
        ) from exc


def prepare_dynamic_human_work_candidate(
    *,
    intent_request: IntentRequest,
    context_envelope: ContextEnvelope,
    resolved_intent: ResolvedIntent,
    bound_work: UnadmittedBoundWorkPlan,
    current_surface: CandidatePlanningSurface,
    attribution: WorkDispositionProposalAttribution,
    rationale: str,
) -> PendingDynamicHumanWork:
    """Produce the exact existing CandidateWorkDisposition for M32 review.

    This constructs no new IntentRequest or ResolvedIntent. The original
    admission/replay path MUST independently authenticate the caller's
    original HUMAN/Core/Host evidence, then explicitly invoke the existing
    M32 disposition admitter. A matching typed object is not that evidence.
    """
    _check_lineage(
        request=intent_request,
        context=context_envelope,
        resolved=resolved_intent,
        bound=bound_work,
        surface=current_surface,
    )
    if type(attribution) is not WorkDispositionProposalAttribution:
        raise DynamicHumanWorkCandidateError("exact proposer attribution required")
    if type(rationale) is not str or not rationale.strip():
        raise DynamicHumanWorkCandidateError("nonempty review rationale required")
    candidate = CandidateWorkDisposition(
        resolved_intent_identity=resolved_intent.identity,
        attribution=attribution,
        kind=WorkDispositionKind.WORK_PLAN,
        work_plan=bound_work.work_plan,
        rationale=rationale,
    )
    return PendingDynamicHumanWork(
        intent_request=intent_request,
        context_envelope=context_envelope,
        resolved_intent=resolved_intent,
        bound_work=bound_work,
        candidate=candidate,
    )


def assert_current_dynamic_human_work_candidate(
    pending: PendingDynamicHumanWork,
    current_surface: CandidatePlanningSurface,
) -> None:
    """Revalidate before any separate human M32 action; grant nothing."""
    if type(pending) is not PendingDynamicHumanWork:
        raise DynamicHumanWorkCandidateError("exact pending candidate required")
    _check_lineage(
        request=pending.intent_request,
        context=pending.context_envelope,
        resolved=pending.resolved_intent,
        bound=pending.bound_work,
        surface=current_surface,
    )
    if (
        pending.candidate.work_plan != pending.bound_work.work_plan
        or pending.candidate.resolved_intent_identity
        != pending.resolved_intent.identity
        or pending.candidate.kind is not WorkDispositionKind.WORK_PLAN
    ):
        raise DynamicHumanWorkCandidateError(
            "pending WorkDisposition diverged from reviewed dynamic WorkPlan"
        )
