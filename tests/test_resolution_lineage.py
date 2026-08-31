from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    CandidateAttribution,
    CandidateResolution,
    ClarificationNeed,
    InformationNeed,
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


def candidate(*, request: str = "1", context: str = "2") -> CandidateResolution:
    return CandidateResolution(
        intent_request_identity=rid(request),
        context_envelope_identity=rid(context),
        attribution=CandidateAttribution(
            provider_ref=StableRef("irr.provider", "llm-a"),
            invocation_ref=StableRef("irr.provider_invocation", f"inv-{request}-{context}"),
        ),
        proposed_semantics="Candidate semantics for lineage hardening regression.",
    )


def admission() -> ResolutionAttribution:
    return ResolutionAttribution(
        resolver_ref=StableRef("irr.resolver", "core"),
        admission_event_ref=StableRef("irr.resolution_event", "admit-lineage"),
    )


def blocking_issue() -> ResolutionIssue:
    return ResolutionIssue(
        kind=ResolutionIssueKind.MISSING_INFORMATION,
        impact=ResolutionIssueImpact.BLOCKING,
        scope="bounded information",
        description="Additional attributable information is required.",
    )


@pytest.mark.parametrize("output_type", (ResolvedIntent, ClarificationNeed, InformationNeed))
def test_irr_owned_outputs_reject_candidate_from_other_request(output_type: type) -> None:
    kwargs = {
        "intent_request_identity": rid("1"),
        "context_envelope_identity": rid("2"),
        "admission_attribution": admission(),
        "candidate_inputs": (candidate(request="3", context="2"),),
    }
    if output_type is ResolvedIntent:
        kwargs["semantics"] = "Answer-only resolution."
    elif output_type is ClarificationNeed:
        kwargs.update(
            question="Which value should be used?",
            scope="bounded information",
            blocking_issues=(blocking_issue(),),
        )
    else:
        kwargs.update(
            description="Attributable bounded information.",
            scope="bounded information",
            reason="Required to continue resolution.",
            blocking_issues=(blocking_issue(),),
        )

    with pytest.raises(ValidationError, match="same IntentRequest identity"):
        output_type(**kwargs)


@pytest.mark.parametrize("output_type", (ResolvedIntent, ClarificationNeed, InformationNeed))
def test_irr_owned_outputs_reject_candidate_from_other_context(output_type: type) -> None:
    kwargs = {
        "intent_request_identity": rid("1"),
        "context_envelope_identity": rid("2"),
        "admission_attribution": admission(),
        "candidate_inputs": (candidate(request="1", context="3"),),
    }
    if output_type is ResolvedIntent:
        kwargs["semantics"] = "Answer-only resolution."
    elif output_type is ClarificationNeed:
        kwargs.update(
            question="Which value should be used?",
            scope="bounded information",
            blocking_issues=(blocking_issue(),),
        )
    else:
        kwargs.update(
            description="Attributable bounded information.",
            scope="bounded information",
            reason="Required to continue resolution.",
            blocking_issues=(blocking_issue(),),
        )

    with pytest.raises(ValidationError, match="same ContextEnvelope identity"):
        output_type(**kwargs)
