from __future__ import annotations

from dataclasses import replace

import pytest

from intent_resolution_runtime import (
    CapabilityExecutionBoundaryKind,
    CapabilityExecutionBoundaryRequirement,
    CapabilityRequestedEffect,
    CapabilityRequestedScope,
    CapabilityRequirement,
    StableRef,
    ValidationError,
    WorkContinuationMode,
    WorkLiteralInput,
    WorkPlan,
    WorkStep,
)
from intent_resolution_runtime.capability_requirement_admission import (
    AdmittedCapabilityRequirement,
    CandidateCapabilityRequirement,
    CapabilityRequirementAdmissionAttribution,
    CapabilityRequirementAdmissionFrontierKind,
    CapabilityRequirementProposalAttribution,
    orchestrate_capability_requirement_admission,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace=namespace, value=value)


def _plan(label: str = "main") -> WorkPlan:
    from intent_resolution_runtime import RecordIdentity

    resolved = RecordIdentity("sha256", ("1" if label == "main" else "2") * 64)
    plan_ref = _ref("irr.work_plan", f"m3.0.4:{label}")
    step = WorkStep(
        resolved_intent_identity=resolved,
        work_plan_ref=plan_ref,
        step_ref=_ref("irr.work_step", f"send:{label}"),
        operation="telegram.send_file",
        scope=f"telegram:{label}",
        inputs=(
            WorkLiteralInput(
                name="file",
                semantic_type="artifact.path",
                value=f"workspace:{label}/report.pdf",
            ),
        ),
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract="The exact file send operation reports completion.",
        description="Send one exact bounded file through Telegram.",
    )
    return WorkPlan(
        resolved_intent_identity=resolved,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="The bounded Telegram send plan completes.",
        description="One-step capability-requirement fixture.",
    )


def _requirement(
    plan: WorkPlan,
    *,
    label: str = "main",
    include_boundary: bool = True,
) -> CapabilityRequirement:
    step = plan.steps[0]
    primary = CapabilityRequestedScope(
        scope_ref=_ref("irr.capability_requested_scope", f"telegram:{label}"),
        semantic_type="messaging.destination_scope",
        value=step.scope,
        description="The exact Telegram destination scope requested by the WorkStep.",
    )
    effect = CapabilityRequestedEffect(
        effect_ref=_ref("irr.capability_requested_effect", f"external-send:{label}"),
        semantic_type="network.external_disclosure",
        requested_scope_refs=(primary.scope_ref,),
        description="Disclose the exact bound file to the requested Telegram scope.",
    )
    boundaries = (
        (
            CapabilityExecutionBoundaryRequirement(
                kind=CapabilityExecutionBoundaryKind.PROVIDER,
                boundary_ref=_ref("irr.provider", "telegram-adapter"),
                description="Require the exact admitted Telegram provider boundary.",
            ),
        )
        if include_boundary
        else ()
    )
    return CapabilityRequirement(
        work_plan=plan,
        step_ref=step.step_ref,
        primary_scope_ref=primary.scope_ref,
        requested_scopes=(primary,),
        requested_effects=(effect,),
        execution_boundary_requirements=boundaries,
        description="Exact capability requirement for this admitted WorkStep.",
    )


def _candidate(
    requirement: CapabilityRequirement,
    *,
    label: str = "main",
    rationale: str = "This exact WorkStep requires the proposed capability semantics.",
) -> CandidateCapabilityRequirement:
    return CandidateCapabilityRequirement(
        attribution=CapabilityRequirementProposalAttribution(
            proposer_ref=_ref("irr.capability_requirement_proposer", f"planner:{label}"),
            proposal_event_ref=_ref(
                "irr.capability_requirement_proposal",
                f"proposal:{label}",
            ),
        ),
        requirement=requirement,
        rationale=rationale,
    )


def _admission(label: str = "main") -> CapabilityRequirementAdmissionAttribution:
    return CapabilityRequirementAdmissionAttribution(
        resolver_ref=_ref("irr.capability_requirement_resolver", "m3.0.4-test"),
        admission_event_ref=_ref(
            "irr.capability_requirement_admission",
            f"admission:{label}",
        ),
    )


def _admit_exact(plan: WorkPlan, candidate: CandidateCapabilityRequirement):
    attribution = _admission()

    def admitter(work_plan, step, candidates, supplied_attribution):
        assert work_plan == plan
        assert step == plan.steps[0]
        return AdmittedCapabilityRequirement(
            admission_attribution=supplied_attribution,
            requirement=candidates[0].requirement,
            candidate_inputs=candidates,
        )

    return orchestrate_capability_requirement_admission(
        plan,
        plan.steps[0].step_ref,
        candidate_inputs=(candidate,),
        admitter=admitter,
        admission_attribution=attribution,
    )


def test_canonical_records_round_trip() -> None:
    plan = _plan()
    candidate = _candidate(_requirement(plan))
    admitted = AdmittedCapabilityRequirement(
        admission_attribution=_admission(),
        requirement=candidate.requirement,
        candidate_inputs=(candidate,),
    )

    assert (
        CapabilityRequirementProposalAttribution.from_json_bytes(
            candidate.attribution.canonical_bytes()
        )
        == candidate.attribution
    )
    assert (
        CandidateCapabilityRequirement.from_json_bytes(candidate.canonical_bytes())
        == candidate
    )
    assert (
        CapabilityRequirementAdmissionAttribution.from_json_bytes(
            admitted.admission_attribution.canonical_bytes()
        )
        == admitted.admission_attribution
    )
    assert (
        AdmittedCapabilityRequirement.from_json_bytes(admitted.canonical_bytes())
        == admitted
    )


def test_no_candidates_requires_proposal_input() -> None:
    plan = _plan()
    frontier = orchestrate_capability_requirement_admission(
        plan,
        plan.steps[0].step_ref,
    )
    assert (
        frontier.kind
        is CapabilityRequirementAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
    )
    assert frontier.candidate_inputs == ()
    assert frontier.admitted_requirement is None
    assert not hasattr(frontier, "identity")
    assert not hasattr(frontier, "canonical_bytes")


def test_same_requirement_with_different_provenance_is_not_voting() -> None:
    plan = _plan()
    requirement = _requirement(plan)
    first = _candidate(requirement, label="a", rationale="Explanation A.")
    second = _candidate(requirement, label="b", rationale="Explanation B.")

    frontier = orchestrate_capability_requirement_admission(
        plan,
        plan.steps[0].step_ref,
        candidate_inputs=(second, first),
    )
    assert frontier.kind is CapabilityRequirementAdmissionFrontierKind.ADMISSION_REQUIRED
    assert frontier.admitted_requirement is None
    assert {item.identity for item in frontier.candidate_inputs} == {
        first.identity,
        second.identity,
    }


def test_distinct_requirement_semantics_require_adjudication() -> None:
    plan = _plan()
    first = _candidate(_requirement(plan), label="with-boundary")
    second = _candidate(
        _requirement(plan, label="other", include_boundary=False),
        label="without-boundary",
    )

    frontier = orchestrate_capability_requirement_admission(
        plan,
        plan.steps[0].step_ref,
        candidate_inputs=(first, second),
    )
    assert (
        frontier.kind
        is CapabilityRequirementAdmissionFrontierKind.ADJUDICATION_REQUIRED
    )
    assert frontier.admitted_requirement is None


def test_foreign_work_plan_and_step_targets_fail_closed() -> None:
    plan = _plan()
    foreign = _plan("foreign")
    with pytest.raises(ValidationError, match="foreign WorkPlan"):
        orchestrate_capability_requirement_admission(
            plan,
            plan.steps[0].step_ref,
            candidate_inputs=(_candidate(_requirement(foreign), label="foreign"),),
        )

    with pytest.raises(ValidationError, match="identify a step"):
        orchestrate_capability_requirement_admission(
            plan,
            _ref("irr.work_step", "not-in-plan"),
        )


def test_explicit_admission_is_required_for_active_requirement() -> None:
    plan = _plan()
    candidate = _candidate(_requirement(plan))
    unresolved = orchestrate_capability_requirement_admission(
        plan,
        plan.steps[0].step_ref,
        candidate_inputs=(candidate,),
    )
    admitted = _admit_exact(plan, candidate)

    assert unresolved.kind is CapabilityRequirementAdmissionFrontierKind.ADMISSION_REQUIRED
    assert unresolved.admitted_requirement is None
    assert (
        admitted.kind
        is CapabilityRequirementAdmissionFrontierKind.REQUIREMENT_OUTPUT_AVAILABLE
    )
    assert admitted.admitted_requirement is not None
    assert admitted.admitted_requirement.requirement == candidate.requirement


def test_admitter_abstention_preserves_unresolved_frontier() -> None:
    plan = _plan()
    candidate = _candidate(_requirement(plan))
    before = orchestrate_capability_requirement_admission(
        plan,
        plan.steps[0].step_ref,
        candidate_inputs=(candidate,),
    )
    after = orchestrate_capability_requirement_admission(
        plan,
        plan.steps[0].step_ref,
        candidate_inputs=(candidate,),
        admitter=lambda _plan, _step, _candidates, _attribution: None,
        admission_attribution=_admission(),
    )
    assert after == before


def test_admitter_cannot_erase_provenance_or_replace_attribution() -> None:
    plan = _plan()
    candidate = _candidate(_requirement(plan))

    def erase(_plan, _step, candidates, attribution):
        return AdmittedCapabilityRequirement(
            admission_attribution=attribution,
            requirement=candidates[0].requirement,
            candidate_inputs=(),
        )

    with pytest.raises(ValidationError, match="exact candidate set"):
        orchestrate_capability_requirement_admission(
            plan,
            plan.steps[0].step_ref,
            candidate_inputs=(candidate,),
            admitter=erase,
            admission_attribution=_admission("expected"),
        )

    def replace_attribution(_plan, _step, candidates, _attribution):
        return AdmittedCapabilityRequirement(
            admission_attribution=_admission("forged"),
            requirement=candidates[0].requirement,
            candidate_inputs=candidates,
        )

    with pytest.raises(ValidationError, match="exact admission attribution"):
        orchestrate_capability_requirement_admission(
            plan,
            plan.steps[0].step_ref,
            candidate_inputs=(candidate,),
            admitter=replace_attribution,
            admission_attribution=_admission("expected"),
        )


def test_existing_admitted_requirement_replays_without_new_admission() -> None:
    plan = _plan()
    candidate = _candidate(_requirement(plan))
    output = AdmittedCapabilityRequirement(
        admission_attribution=_admission(),
        requirement=candidate.requirement,
        candidate_inputs=(candidate,),
    )
    replayed = orchestrate_capability_requirement_admission(
        plan,
        plan.steps[0].step_ref,
        candidate_inputs=output.candidate_inputs,
        admitted_outputs=(output,),
    )
    assert (
        replayed.kind
        is CapabilityRequirementAdmissionFrontierKind.REQUIREMENT_OUTPUT_AVAILABLE
    )
    assert replayed.admitted_requirement == output
    assert replayed.candidate_inputs == output.candidate_inputs


def test_competing_admitted_requirements_fail_closed() -> None:
    plan = _plan()
    first_candidate = _candidate(_requirement(plan), label="a")
    second_requirement = replace(
        _requirement(plan),
        description="Materially different exact capability requirement.",
    )
    second_candidate = _candidate(second_requirement, label="b")
    first = AdmittedCapabilityRequirement(
        admission_attribution=_admission("a"),
        requirement=first_candidate.requirement,
        candidate_inputs=(first_candidate,),
    )
    second = AdmittedCapabilityRequirement(
        admission_attribution=_admission("b"),
        requirement=second_candidate.requirement,
        candidate_inputs=(second_candidate,),
    )
    with pytest.raises(ValidationError, match="competing admitted"):
        orchestrate_capability_requirement_admission(
            plan,
            plan.steps[0].step_ref,
            admitted_outputs=(first, second),
        )


def test_explicit_deterministic_admission_can_have_no_provider_candidates() -> None:
    plan = _plan()
    requirement = _requirement(plan)

    def admitter(work_plan, step, candidates, attribution):
        assert work_plan == plan
        assert step == plan.steps[0]
        assert candidates == ()
        return AdmittedCapabilityRequirement(
            admission_attribution=attribution,
            requirement=requirement,
            candidate_inputs=(),
        )

    frontier = orchestrate_capability_requirement_admission(
        plan,
        plan.steps[0].step_ref,
        admitter=admitter,
        admission_attribution=_admission("deterministic"),
    )
    assert (
        frontier.kind
        is CapabilityRequirementAdmissionFrontierKind.REQUIREMENT_OUTPUT_AVAILABLE
    )
    assert frontier.admitted_requirement is not None
    assert frontier.admitted_requirement.requirement == requirement
    assert frontier.candidate_inputs == ()


def test_admitted_requirement_does_not_gain_matching_or_authority_fields() -> None:
    plan = _plan()
    admitted = _admit_exact(plan, _candidate(_requirement(plan))).admitted_requirement
    assert admitted is not None
    for forbidden in (
        "capability_match",
        "available",
        "authorized",
        "authorization",
        "approved",
        "governance",
        "attempt",
        "executor",
        "effect_permitted",
    ):
        assert not hasattr(admitted, forbidden)
