from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    CandidateAttribution,
    CandidateResolution,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    StableRef,
    ValidationError,
    WorkPlan,
)


CONTEXT_IDENTITY = RecordIdentity("sha256", "2" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> tuple[IntentRequest, CandidateResolution, ResolvedIntent]:
    request = IntentRequest(
        origin=OriginAttribution(
            OriginKind.HUMAN,
            _ref("human", "user"),
            _ref("host.event", "scenario-g-request"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression("Как ты думаешь, этот эксперимент хороший?"),
    )

    candidate = CandidateResolution(
        intent_request_identity=request.identity,
        context_envelope_identity=CONTEXT_IDENTITY,
        attribution=CandidateAttribution(
            _ref("provider", "scenario-g-provider"),
            _ref("provider.invocation", "scenario-g-evaluation"),
        ),
        proposed_semantics=(
            "The principal asks for a conversational evaluation of the already admitted experiment "
            "material. Answer from admitted context only; no operational work is requested."
        ),
        assumptions=(),
        issues=(),
        clarification_proposals=(),
        information_need_proposals=(),
    )

    resolved = ResolvedIntent(
        intent_request_identity=request.identity,
        context_envelope_identity=CONTEXT_IDENTITY,
        admission_attribution=ResolutionAttribution(
            _ref("irr.resolver", "scenario-g"),
            _ref("irr.resolution_event", "scenario-g-resolved"),
        ),
        semantics=(
            "The principal requests an evaluative conversational answer from already admitted "
            "experiment context. This resolution requires no operational work."
        ),
        assumptions=(),
        unresolved_issues=(),
        candidate_inputs=(candidate,),
    )
    return request, candidate, resolved


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


def test_scenario_g_conversational_evaluation_resolves_without_operational_work() -> None:
    request, candidate, resolved = _fixture()

    assert request.expression.text == "Как ты думаешь, этот эксперимент хороший?"
    assert candidate.issues == ()
    assert candidate.clarification_proposals == ()
    assert candidate.information_need_proposals == ()
    assert resolved.unresolved_issues == ()
    assert resolved.candidate_inputs == (candidate,)
    assert "no operational work" in resolved.semantics.lower()


def test_scenario_g_non_operational_resolution_does_not_synthesize_downstream_work_or_authority() -> None:
    _, _, resolved = _fixture()

    primitive = resolved.to_primitive()
    keys = _all_keys(primitive)
    for forbidden in (
        "work_plan",
        "work_step",
        "operation",
        "capability_requirement",
        "capability_match",
        "work_proposal",
        "governance_decision",
        "authorization",
        "authorized",
        "capability_attempt",
        "delegated_work",
        "handoff",
    ):
        assert forbidden not in keys

    serialized = repr(primitive)
    for forbidden_semantics in (
        "process.launch",
        "filesystem.search",
        "shell.execute",
        "browser",
        "network.use",
        "external.disclosure",
    ):
        assert forbidden_semantics not in serialized


def test_scenario_g_no_work_is_not_encoded_as_an_empty_or_noop_work_plan() -> None:
    _, _, resolved = _fixture()

    with pytest.raises(ValidationError, match="WorkPlan.steps must not be empty"):
        WorkPlan(
            resolved.identity,
            _ref("irr.work_plan", "scenario-g-invalid-noop"),
            (),
            "No operational work is required.",
            "An empty WorkPlan must not stand in for a non-operational resolution.",
        )


def test_scenario_g_non_operational_resolution_round_trip_preserves_lineage() -> None:
    request, candidate, resolved = _fixture()

    decoded = ResolvedIntent.from_json_bytes(resolved.canonical_bytes())
    assert decoded == resolved
    assert decoded.identity == resolved.identity
    assert decoded.intent_request_identity == request.identity
    assert decoded.candidate_inputs == (candidate,)
