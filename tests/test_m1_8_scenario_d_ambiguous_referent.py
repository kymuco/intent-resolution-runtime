from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    CandidateAttribution,
    CandidateResolution,
    ClarificationNeed,
    ClarificationProposal,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    RecordIdentity,
    ResolutionAttribution,
    ResolutionIssue,
    ResolutionIssueImpact,
    ResolutionIssueKind,
    ResolvedIntent,
    StableRef,
    ValidationError,
)


CONTEXT_IDENTITY = RecordIdentity("sha256", "2" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> tuple[IntentRequest, CandidateResolution, ClarificationNeed]:
    request = IntentRequest(
        origin=OriginAttribution(
            OriginKind.HUMAN,
            _ref("human", "user"),
            _ref("host.event", "scenario-d-request"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression("Запусти его."),
    )

    ambiguity = ResolutionIssue(
        ResolutionIssueKind.MATERIAL_AMBIGUITY,
        ResolutionIssueImpact.BLOCKING,
        "launch target referent",
        (
            "Admitted Context does not identify one unique referent for 'его'; a provider "
            "preference cannot choose the target."
        ),
        ("organism_lab workspace", "voice_engine workspace"),
    )
    candidate = CandidateResolution(
        intent_request_identity=request.identity,
        context_envelope_identity=CONTEXT_IDENTITY,
        attribution=CandidateAttribution(
            _ref("provider", "scenario-d-provider"),
            _ref("provider.invocation", "scenario-d-guess"),
        ),
        proposed_semantics=(
            "Provider proposes organism_lab as the more likely launch referent, but this is "
            "candidate semantics only and does not resolve the blocking ambiguity."
        ),
        assumptions=(),
        issues=(ambiguity,),
        clarification_proposals=(
            ClarificationProposal(
                "Что именно запустить: organism_lab или voice_engine?",
                "launch target referent",
                "The material referent must be explicitly disambiguated before operational work.",
            ),
        ),
        information_need_proposals=(),
    )
    clarification = ClarificationNeed(
        intent_request_identity=request.identity,
        context_envelope_identity=CONTEXT_IDENTITY,
        admission_attribution=ResolutionAttribution(
            _ref("irr.resolver", "scenario-d"),
            _ref("irr.resolution_event", "scenario-d-clarification"),
        ),
        question="Что именно запустить: organism_lab или voice_engine?",
        scope="launch target referent",
        blocking_issues=(ambiguity,),
        candidate_inputs=(candidate,),
    )
    return request, candidate, clarification


def _all_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys.update(_all_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_all_keys(item))
    return keys


def test_scenario_d_material_ambiguity_yields_clarification_not_resolved_work() -> None:
    request, candidate, clarification = _fixture()

    assert request.expression.text == "Запусти его."
    assert candidate.issues[0].kind is ResolutionIssueKind.MATERIAL_AMBIGUITY
    assert candidate.issues[0].impact is ResolutionIssueImpact.BLOCKING
    assert clarification.blocking_issues == candidate.issues
    assert clarification.candidate_inputs == (candidate,)

    keys = _all_keys(clarification.to_primitive())
    assert "work_plan" not in keys
    assert "work_step" not in keys
    assert "operation" not in keys
    assert "process.launch" not in repr(clarification.to_primitive())
    assert "authorization" not in keys
    assert "authorized" not in keys


def test_scenario_d_provider_proposal_cannot_be_admitted_while_material_ambiguity_blocks() -> None:
    request, candidate, _ = _fixture()
    ambiguity = candidate.issues[0]

    with pytest.raises(ValidationError, match="Material Ambiguity"):
        ResolvedIntent(
            request.identity,
            CONTEXT_IDENTITY,
            ResolutionAttribution(
                _ref("irr.resolver", "scenario-d"),
                _ref("irr.resolution_event", "scenario-d-invalid-resolved"),
            ),
            candidate.proposed_semantics,
            (),
            (ambiguity,),
            (candidate,),
        )


def test_scenario_d_candidate_confidence_or_authority_cannot_replace_referent_evidence() -> None:
    _, candidate, clarification = _fixture()

    # The provider may propose one alternative, but the canonical blocking issue preserves both.
    assert "organism_lab" in candidate.proposed_semantics
    assert candidate.issues[0].alternatives == (
        "organism_lab workspace",
        "voice_engine workspace",
    )
    assert clarification.question.startswith("Что именно запустить")

    # Clarification carries no authority or ambient-context escape hatch.
    primitive = clarification.to_primitive()
    keys = _all_keys(primitive)
    for forbidden in (
        "authorization",
        "authorized",
        "foreground_window",
        "running_processes",
        "shell_history",
        "recent_files",
        "ambient_context",
    ):
        assert forbidden not in keys


def test_scenario_d_clarification_round_trip_preserves_blocking_ambiguity() -> None:
    _, _, clarification = _fixture()

    decoded = ClarificationNeed.from_json_bytes(clarification.canonical_bytes())
    assert decoded == clarification
    assert decoded.identity == clarification.identity
    assert decoded.blocking_issues[0].kind is ResolutionIssueKind.MATERIAL_AMBIGUITY
