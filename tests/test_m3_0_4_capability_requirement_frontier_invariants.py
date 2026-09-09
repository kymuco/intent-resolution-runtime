from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    CandidateCapabilityRequirement,
    CapabilityExecutionBoundaryKind,
    CapabilityExecutionBoundaryRequirement,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityRequirementAdmissionFrontier,
    CapabilityRequirementAdmissionFrontierKind,
    CapabilityRequirementProposalAttribution,
    RecordIdentity,
    StableRef,
    ValidationError,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace=namespace, value=value)


def _plan() -> WorkPlan:
    resolved = RecordIdentity("sha256", "1" * 64)
    plan_ref = _ref("irr.work_plan", "m3.0.4-frontier-invariants")
    step = WorkStep(
        resolved_intent_identity=resolved,
        work_plan_ref=plan_ref,
        step_ref=_ref("irr.work_step", "send"),
        operation="telegram.send_file",
        scope="telegram:target",
        inputs=(),
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract="The bounded send operation reports completion.",
        description="Send one exact bounded file through Telegram.",
    )
    return WorkPlan(
        resolved_intent_identity=resolved,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="The bounded Telegram send plan completes.",
        description="One-step frontier invariant fixture.",
    )


def _requirement(plan: WorkPlan, *, include_boundary: bool) -> CapabilityRequirement:
    step = plan.steps[0]
    scope = CapabilityRequestedScope(
        scope_ref=_ref("irr.capability_requested_scope", "telegram-target"),
        semantic_type="messaging.destination_scope",
        value=step.scope,
        description="The exact Telegram destination scope requested by the WorkStep.",
    )
    boundaries = (
        (
            CapabilityExecutionBoundaryRequirement(
                kind=CapabilityExecutionBoundaryKind.PROVIDER,
                boundary_ref=_ref("irr.provider", "telegram-adapter"),
                description="Require the exact Telegram provider boundary.",
            ),
        )
        if include_boundary
        else ()
    )
    return CapabilityRequirement(
        work_plan=plan,
        step_ref=step.step_ref,
        primary_scope_ref=scope.scope_ref,
        requested_scopes=(scope,),
        requested_effects=(),
        execution_boundary_requirements=boundaries,
        description="Exact capability requirement for the WorkStep.",
    )


def _candidate(
    requirement: CapabilityRequirement, *, label: str
) -> CandidateCapabilityRequirement:
    return CandidateCapabilityRequirement(
        attribution=CapabilityRequirementProposalAttribution(
            proposer_ref=_ref("irr.capability_requirement_proposer", label),
            proposal_event_ref=_ref(
                "irr.capability_requirement_proposal", f"proposal:{label}"
            ),
        ),
        requirement=requirement,
        rationale="Exact capability semantics proposed for this WorkStep.",
    )


def test_frontier_constructor_rejects_single_candidate_as_adjudication() -> None:
    plan = _plan()
    candidate = _candidate(_requirement(plan, include_boundary=True), label="single")

    with pytest.raises(ValidationError, match="must match exact candidate semantics"):
        CapabilityRequirementAdmissionFrontier(
            work_plan=plan,
            step_ref=plan.steps[0].step_ref,
            candidate_inputs=(candidate,),
            kind=CapabilityRequirementAdmissionFrontierKind.ADJUDICATION_REQUIRED,
        )


def test_frontier_constructor_rejects_distinct_semantics_as_admission() -> None:
    plan = _plan()
    first = _candidate(_requirement(plan, include_boundary=True), label="with-boundary")
    second = _candidate(
        _requirement(plan, include_boundary=False),
        label="without-boundary",
    )

    with pytest.raises(ValidationError, match="must match exact candidate semantics"):
        CapabilityRequirementAdmissionFrontier(
            work_plan=plan,
            step_ref=plan.steps[0].step_ref,
            candidate_inputs=(first, second),
            kind=CapabilityRequirementAdmissionFrontierKind.ADMISSION_REQUIRED,
        )
