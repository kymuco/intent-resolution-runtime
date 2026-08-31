from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    RecordIdentity,
    ResolutionAttribution,
    ResolutionIssue,
    ResolutionIssueImpact,
    ResolutionIssueKind,
    ResolvedIntent,
    StableRef,
    ValidationError,
)


def rid(ch: str) -> RecordIdentity:
    return RecordIdentity("sha256", ch * 64)


def admission() -> ResolutionAttribution:
    return ResolutionAttribution(
        resolver_ref=StableRef("irr.resolver", "core"),
        admission_event_ref=StableRef("irr.resolution_event", "admit-uncertainty"),
    )


def uncertainty(impact: ResolutionIssueImpact) -> ResolutionIssue:
    return ResolutionIssue(
        kind=ResolutionIssueKind.UNCERTAINTY,
        impact=impact,
        scope="report freshness interpretation",
        description=(
            "The admitted evidence supports the interpretation but does not establish "
            "freshness beyond the stated temporal scope."
        ),
    )


def test_nonblocking_uncertainty_can_remain_explicit_in_resolved_intent() -> None:
    issue = uncertainty(ResolutionIssueImpact.NON_BLOCKING)
    resolved = ResolvedIntent(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        admission_attribution=admission(),
        semantics="Explain the admitted result within the evidence's stated temporal scope.",
        unresolved_issues=(issue,),
    )
    assert resolved.unresolved_issues == (issue,)
    assert resolved.unresolved_issues[0].kind is ResolutionIssueKind.UNCERTAINTY
    assert ResolvedIntent.from_json_bytes(resolved.canonical_bytes()) == resolved


def test_blocking_uncertainty_prevents_resolved_intent_admission() -> None:
    with pytest.raises(ValidationError, match="blocking"):
        ResolvedIntent(
            intent_request_identity=rid("1"),
            context_envelope_identity=rid("2"),
            admission_attribution=admission(),
            semantics="Select a target whose required factual basis remains uncertain.",
            unresolved_issues=(uncertainty(ResolutionIssueImpact.BLOCKING),),
        )


def test_uncertainty_does_not_invent_competing_alternatives() -> None:
    with pytest.raises(ValidationError, match="must not invent competing alternatives"):
        ResolutionIssue(
            kind=ResolutionIssueKind.UNCERTAINTY,
            impact=ResolutionIssueImpact.NON_BLOCKING,
            scope="report freshness",
            description="Freshness is not fully established.",
            alternatives=("fresh", "stale"),
        )


def test_uncertainty_is_distinct_from_missing_information_and_conflict() -> None:
    issue = uncertainty(ResolutionIssueImpact.NON_BLOCKING)
    primitive = issue.to_primitive()
    assert primitive["kind"] == "uncertainty"
    assert primitive["alternatives"] == []
    assert issue.kind is not ResolutionIssueKind.MISSING_INFORMATION
    assert issue.kind is not ResolutionIssueKind.CONFLICT
