from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    StableRef,
)
from intent_resolution_runtime.errors import ValidationError
from intent_resolution_runtime.work import (
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
)
from intent_resolution_runtime.work_binding import orchestrate_work_binding
from intent_resolution_runtime.work_disposition import (
    AdmittedWorkPlan,
    CandidateWorkDisposition,
    NoOperationalWork,
    WorkDispositionAdmissionAttribution,
    WorkDispositionFrontierKind,
    WorkDispositionKind,
    WorkDispositionProposalAttribution,
    orchestrate_work_disposition,
)


def _rid(ch: str) -> RecordIdentity:
    return RecordIdentity("sha256", ch * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _resolved(label: str = "main") -> ResolvedIntent:
    return ResolvedIntent(
        intent_request_identity=_rid("1" if label == "main" else "3"),
        context_envelope_identity=_rid("2" if label == "main" else "4"),
        admission_attribution=ResolutionAttribution(
            _ref("irr.resolver", "m3.0.2-test"),
            _ref("irr.resolution_event", f"resolved-{label}"),
        ),
        semantics=f"Resolved semantics for {label}.",
    )


def _plan(resolved: ResolvedIntent, label: str = "main") -> WorkPlan:
    plan_ref = _ref("irr.work_plan", label)
    step = WorkStep(
        resolved_intent_identity=resolved.identity,
        work_plan_ref=plan_ref,
        step_ref=_ref("irr.work_step", f"{label}-step"),
        operation="artifact.inspect",
        scope="the explicitly resolved artifact",
        inputs=(),
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract="The bounded artifact is inspected.",
        description="Inspect one admitted artifact.",
    )
    return WorkPlan(
        resolved_intent_identity=resolved.identity,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="The bounded inspection plan completes.",
        description="One bounded operational plan.",
    )


def _proposal_attribution(label: str) -> WorkDispositionProposalAttribution:
    return WorkDispositionProposalAttribution(
        proposer_ref=_ref("irr.work_disposition_proposer", f"planner-{label}"),
        proposal_event_ref=_ref("irr.work_disposition_proposal", f"proposal-{label}"),
    )


def _admission_attribution(label: str = "main") -> WorkDispositionAdmissionAttribution:
    return WorkDispositionAdmissionAttribution(
        resolver_ref=_ref("irr.work_disposition_resolver", "m3.0.2-test"),
        admission_event_ref=_ref(
            "irr.work_disposition_admission", f"admission-{label}"
        ),
    )


def _work_candidate(
    resolved: ResolvedIntent,
    *,
    label: str = "work",
    plan: WorkPlan | None = None,
) -> CandidateWorkDisposition:
    return CandidateWorkDisposition(
        resolved_intent_identity=resolved.identity,
        attribution=_proposal_attribution(label),
        kind=WorkDispositionKind.WORK_PLAN,
        work_plan=plan or _plan(resolved, label),
        rationale="Operational work is required to satisfy the resolved intent.",
    )


def _no_work_candidate(
    resolved: ResolvedIntent,
    *,
    label: str = "no-work",
) -> CandidateWorkDisposition:
    return CandidateWorkDisposition(
        resolved_intent_identity=resolved.identity,
        attribution=_proposal_attribution(label),
        kind=WorkDispositionKind.NO_OPERATIONAL_WORK,
        work_plan=None,
        rationale="The admitted context already satisfies the conversational request.",
    )


def test_candidate_and_outputs_round_trip_exact_canonical_bytes() -> None:
    resolved = _resolved()
    work_candidate = _work_candidate(resolved)
    no_work_candidate = _no_work_candidate(resolved)
    attribution = _admission_attribution()

    no_work = NoOperationalWork(
        resolved_intent_identity=resolved.identity,
        admission_attribution=attribution,
        rationale="No external or operational action is required.",
        candidate_inputs=(no_work_candidate,),
    )
    admitted_plan = AdmittedWorkPlan(
        resolved_intent_identity=resolved.identity,
        admission_attribution=attribution,
        work_plan=work_candidate.work_plan,
        candidate_inputs=(work_candidate,),
    )

    for record in (work_candidate, no_work_candidate, no_work, admitted_plan):
        parsed = record.__class__.from_json_bytes(record.canonical_bytes())
        assert parsed == record
        assert parsed.canonical_bytes() == record.canonical_bytes()
        assert parsed.identity == record.identity


def test_no_candidate_requires_proposal_input_without_claiming_no_work() -> None:
    frontier = orchestrate_work_disposition(_resolved())

    assert frontier.kind is WorkDispositionFrontierKind.PROPOSAL_INPUT_REQUIRED
    assert frontier.candidate_inputs == ()
    assert frontier.disposition_output is None
    assert not hasattr(frontier, "identity")
    assert not hasattr(frontier, "canonical_bytes")


def test_unique_candidate_requires_explicit_admission() -> None:
    resolved = _resolved()
    candidate = _work_candidate(resolved)

    frontier = orchestrate_work_disposition(
        resolved,
        candidate_inputs=(candidate,),
    )

    assert frontier.kind is WorkDispositionFrontierKind.ADMISSION_REQUIRED
    assert frontier.candidate_inputs == (candidate,)
    assert frontier.disposition_output is None


def test_equivalent_candidates_do_not_gain_voting_authority() -> None:
    resolved = _resolved()
    plan = _plan(resolved)
    first = _work_candidate(resolved, label="alpha", plan=plan)
    second = CandidateWorkDisposition(
        resolved_intent_identity=resolved.identity,
        attribution=_proposal_attribution("beta"),
        kind=WorkDispositionKind.WORK_PLAN,
        work_plan=plan,
        rationale=first.rationale,
    )

    frontier = orchestrate_work_disposition(
        resolved,
        candidate_inputs=(second, first),
    )

    assert frontier.kind is WorkDispositionFrontierKind.ADMISSION_REQUIRED
    assert set(frontier.candidate_inputs) == {first, second}


def test_divergent_work_and_no_work_candidates_require_adjudication() -> None:
    resolved = _resolved()

    frontier = orchestrate_work_disposition(
        resolved,
        candidate_inputs=(_work_candidate(resolved), _no_work_candidate(resolved)),
    )

    assert frontier.kind is WorkDispositionFrontierKind.ADJUDICATION_REQUIRED
    assert frontier.disposition_output is None


def test_explicit_admitter_can_admit_no_operational_work() -> None:
    resolved = _resolved()
    candidate = _no_work_candidate(resolved)
    attribution = _admission_attribution("no-work")
    calls = 0

    def admitter(resolved_intent, candidates, supplied_attribution):
        nonlocal calls
        calls += 1
        assert resolved_intent is resolved
        return NoOperationalWork(
            resolved_intent_identity=resolved_intent.identity,
            admission_attribution=supplied_attribution,
            rationale="The request is fully answerable from admitted semantics.",
            candidate_inputs=candidates,
        )

    frontier = orchestrate_work_disposition(
        resolved,
        candidate_inputs=(candidate,),
        admitter=admitter,
        admission_attribution=attribution,
    )

    assert calls == 1
    assert frontier.kind is WorkDispositionFrontierKind.DISPOSITION_OUTPUT_AVAILABLE
    assert frontier.disposition_output.__class__ is NoOperationalWork
    assert frontier.disposition_output.admission_attribution == attribution
    assert frontier.disposition_output.candidate_inputs == (candidate,)


def test_explicit_admitter_can_admit_bounded_work_plan() -> None:
    resolved = _resolved()
    candidate = _work_candidate(resolved)
    attribution = _admission_attribution("work")

    def admitter(resolved_intent, candidates, supplied_attribution):
        return AdmittedWorkPlan(
            resolved_intent_identity=resolved_intent.identity,
            admission_attribution=supplied_attribution,
            work_plan=candidates[0].work_plan,
            candidate_inputs=candidates,
        )

    frontier = orchestrate_work_disposition(
        resolved,
        candidate_inputs=(candidate,),
        admitter=admitter,
        admission_attribution=attribution,
    )

    output = frontier.disposition_output
    assert output.__class__ is AdmittedWorkPlan
    assert output.work_plan == candidate.work_plan

    binding_frontier = orchestrate_work_binding(
        resolved,
        work_plans=(output.work_plan,),
    )
    assert binding_frontier.work_plan == output.work_plan
    assert binding_frontier.work_disposition_required is False


def test_admitter_abstention_preserves_unresolved_frontier() -> None:
    resolved = _resolved()
    candidate = _work_candidate(resolved)

    before = orchestrate_work_disposition(resolved, candidate_inputs=(candidate,))
    after = orchestrate_work_disposition(
        resolved,
        candidate_inputs=(candidate,),
        admitter=lambda *_: None,
        admission_attribution=_admission_attribution("abstain"),
    )

    assert after == before


def test_admitter_cannot_erase_candidate_provenance() -> None:
    resolved = _resolved()
    candidate = _work_candidate(resolved)

    def admitter(resolved_intent, _candidates, supplied_attribution):
        return AdmittedWorkPlan(
            resolved_intent_identity=resolved_intent.identity,
            admission_attribution=supplied_attribution,
            work_plan=candidate.work_plan,
            candidate_inputs=(),
        )

    with pytest.raises(ValidationError, match="complete exact candidate provenance"):
        orchestrate_work_disposition(
            resolved,
            candidate_inputs=(candidate,),
            admitter=admitter,
            admission_attribution=_admission_attribution("erase"),
        )


def test_admitter_cannot_replace_admission_attribution() -> None:
    resolved = _resolved()
    candidate = _no_work_candidate(resolved)

    def admitter(resolved_intent, candidates, _supplied_attribution):
        return NoOperationalWork(
            resolved_intent_identity=resolved_intent.identity,
            admission_attribution=_admission_attribution("foreign"),
            rationale="No work.",
            candidate_inputs=candidates,
        )

    with pytest.raises(
        ValidationError, match="preserve exact WorkDispositionAdmissionAttribution"
    ):
        orchestrate_work_disposition(
            resolved,
            candidate_inputs=(candidate,),
            admitter=admitter,
            admission_attribution=_admission_attribution("expected"),
        )


def test_foreign_candidate_and_work_plan_lineage_fail_closed() -> None:
    resolved = _resolved("main")
    foreign = _resolved("foreign")
    foreign_candidate = _work_candidate(foreign)

    with pytest.raises(ValidationError, match="foreign ResolvedIntent lineage"):
        orchestrate_work_disposition(
            resolved,
            candidate_inputs=(foreign_candidate,),
        )

    with pytest.raises(ValidationError, match="exact ResolvedIntent"):
        CandidateWorkDisposition(
            resolved_intent_identity=resolved.identity,
            attribution=_proposal_attribution("launder"),
            kind=WorkDispositionKind.WORK_PLAN,
            work_plan=_plan(foreign),
            rationale="Attempt to launder a foreign plan.",
        )


def test_existing_admitted_output_replays_without_reinvoking_admission() -> None:
    resolved = _resolved()
    candidate = _work_candidate(resolved)
    output = AdmittedWorkPlan(
        resolved_intent_identity=resolved.identity,
        admission_attribution=_admission_attribution("history"),
        work_plan=candidate.work_plan,
        candidate_inputs=(candidate,),
    )

    frontier = orchestrate_work_disposition(
        resolved,
        admitted_outputs=(output,),
    )

    assert frontier.kind is WorkDispositionFrontierKind.DISPOSITION_OUTPUT_AVAILABLE
    assert frontier.disposition_output is output
    assert frontier.candidate_inputs == (candidate,)


def test_competing_admitted_outputs_are_not_resolved_by_order() -> None:
    resolved = _resolved()
    no_work_candidate = _no_work_candidate(resolved)
    work_candidate = _work_candidate(resolved)
    attribution = _admission_attribution("competing")
    no_work = NoOperationalWork(
        resolved_intent_identity=resolved.identity,
        admission_attribution=attribution,
        rationale="No work is required.",
        candidate_inputs=(no_work_candidate,),
    )
    admitted_plan = AdmittedWorkPlan(
        resolved_intent_identity=resolved.identity,
        admission_attribution=attribution,
        work_plan=work_candidate.work_plan,
        candidate_inputs=(work_candidate,),
    )

    with pytest.raises(ValidationError, match="competing admitted outputs"):
        orchestrate_work_disposition(
            resolved,
            admitted_outputs=(admitted_plan, no_work),
        )


def test_no_operational_work_is_not_an_empty_or_noop_work_plan() -> None:
    resolved = _resolved()
    output = NoOperationalWork(
        resolved_intent_identity=resolved.identity,
        admission_attribution=_admission_attribution("terminal"),
        rationale="Conversation is already semantically satisfied.",
    )

    assert not hasattr(output, "work_plan")
    with pytest.raises(ValidationError, match="steps must not be empty"):
        WorkPlan(
            resolved_intent_identity=resolved.identity,
            plan_ref=_ref("irr.work_plan", "empty"),
            steps=(),
            completion_contract="Nothing happens.",
            description="Invalid placeholder plan.",
        )
