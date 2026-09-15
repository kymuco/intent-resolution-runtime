from __future__ import annotations

from inspect import signature

import pytest

from intent_resolution_runtime.context import (
    ClaimRecord,
    CompletenessRecord,
    ContextEnvelope,
    EvidenceRecord,
    EvidenceRelation,
    EvidenceTargetKind,
    SourceAttribution,
    TemporalBasisKind,
    TemporalBasisRecord,
)
from intent_resolution_runtime.errors import ValidationError
from intent_resolution_runtime.intent import (
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    StableRef,
)
from intent_resolution_runtime.resolution import CandidateAttribution, CandidateResolution
from intent_resolution_runtime.cognitive_provider import (
    CognitiveProviderIntegrationError,
    CognitiveProviderPort,
    CognitiveProviderRequest,
    build_cognitive_provider_request,
    invoke_cognitive_provider,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace=namespace, value=value)


def _request(label: str = "primary") -> IntentRequest:
    return IntentRequest(
        origin=OriginAttribution(
            kind=OriginKind.HUMAN,
            actor_ref=_ref("principal", "user"),
            source_event_ref=_ref("event", f"intent:{label}"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression(text=f"Inspect project {label}"),
    )


def _context(request: IntentRequest, label: str = "primary") -> ContextEnvelope:
    source = SourceAttribution(
        source_ref=_ref("source", "host"),
        source_event_ref=_ref("event", f"context:{label}"),
    )
    claim = ClaimRecord(
        attribution=source,
        statement=f"Project {label} is ready for inspection.",
    )
    evidence = EvidenceRecord(
        attribution=source,
        relation=EvidenceRelation.SUPPORTS,
        target_kind=EvidenceTargetKind.CLAIM,
        target_identity=claim.identity,
        scope="project readiness",
        description="The Host has an explicit bounded readiness record.",
    )
    temporal = TemporalBasisRecord(
        attribution=source,
        kind=TemporalBasisKind.NAMED,
        value="current-project-snapshot",
        scope="project readiness",
    )
    completeness = CompletenessRecord(
        attribution=source,
        bounded_domain="project readiness records",
        purpose="provider context projection test",
        temporal_basis_refs=(temporal.identity,),
    )
    return ContextEnvelope(
        intent_request_identity=request.identity,
        boundary_attribution=source,
        records=(claim, evidence, temporal, completeness),
    )


def _provider_ref(label: str = "primary") -> StableRef:
    return _ref("irr.cognitive_provider", label)


def _invocation_ref(label: str = "primary") -> StableRef:
    return _ref("irr.cognitive_provider_invocation", label)


def _candidate(
    request: CognitiveProviderRequest,
    *,
    provider_ref: StableRef | None = None,
    invocation_ref: StableRef | None = None,
    intent_request_identity=None,
    context_envelope_identity=None,
) -> CandidateResolution:
    return CandidateResolution(
        intent_request_identity=(
            request.intent_request_identity
            if intent_request_identity is None
            else intent_request_identity
        ),
        context_envelope_identity=(
            request.context_envelope_identity
            if context_envelope_identity is None
            else context_envelope_identity
        ),
        attribution=CandidateAttribution(
            provider_ref=request.provider_ref if provider_ref is None else provider_ref,
            invocation_ref=(
                request.invocation_ref if invocation_ref is None else invocation_ref
            ),
        ),
        proposed_semantics="Inspect the explicitly identified bounded project.",
    )


class _StaticProvider:
    def __init__(self, candidate: CandidateResolution) -> None:
        self._candidate = candidate
        self.requests: list[CognitiveProviderRequest] = []

    def propose(self, request: CognitiveProviderRequest) -> CandidateResolution:
        self.requests.append(request)
        return self._candidate


class _WrongTypeProvider:
    def propose(self, request: CognitiveProviderRequest) -> object:
        return object()


class _ExplodingProvider:
    def propose(self, request: CognitiveProviderRequest) -> CandidateResolution:
        raise RuntimeError("transport unavailable")


def test_projection_discloses_expression_and_only_selected_context_records() -> None:
    intent_request = _request()
    context = _context(intent_request)
    claim = next(record for record in context.records if type(record) is ClaimRecord)

    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref(),
        invocation_ref=_invocation_ref(),
        intent_request=intent_request,
        context_envelope=context,
        disclosed_context_identities=(claim.identity,),
    )

    assert provider_request.intent_request_identity == intent_request.identity
    assert provider_request.context_envelope_identity == context.identity
    assert provider_request.intent_expression == intent_request.expression
    assert provider_request.context_records == (claim,)

    for forbidden in (
        "principal_ref",
        "origin",
        "context_envelope",
        "history_repository",
        "repository",
        "acquisition",
        "executor",
        "governance",
        "authorization",
    ):
        assert not hasattr(provider_request, forbidden)


def test_empty_context_projection_is_explicitly_supported() -> None:
    intent_request = _request("empty")
    context = _context(intent_request, "empty")

    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("empty"),
        invocation_ref=_invocation_ref("empty"),
        intent_request=intent_request,
        context_envelope=context,
    )

    assert provider_request.context_records == ()
    assert provider_request.intent_expression == intent_request.expression


def test_projection_rejects_record_not_present_in_exact_context_envelope() -> None:
    intent_request = _request("primary")
    context = _context(intent_request, "primary")
    foreign_request = _request("foreign")
    foreign_context = _context(foreign_request, "foreign")
    foreign_claim = next(
        record for record in foreign_context.records if type(record) is ClaimRecord
    )

    with pytest.raises(ValidationError, match="only records from the exact ContextEnvelope"):
        build_cognitive_provider_request(
            provider_ref=_provider_ref(),
            invocation_ref=_invocation_ref(),
            intent_request=intent_request,
            context_envelope=context,
            disclosed_context_identities=(foreign_claim.identity,),
        )


def test_projection_rejects_context_from_foreign_intent_request() -> None:
    first_request = _request("first")
    second_request = _request("second")
    second_context = _context(second_request, "second")

    with pytest.raises(ValidationError, match="exact IntentRequest"):
        build_cognitive_provider_request(
            provider_ref=_provider_ref(),
            invocation_ref=_invocation_ref(),
            intent_request=first_request,
            context_envelope=second_context,
        )


def test_projection_requires_disclosed_evidence_target_to_be_disclosed() -> None:
    intent_request = _request("evidence")
    context = _context(intent_request, "evidence")
    evidence = next(record for record in context.records if type(record) is EvidenceRecord)

    with pytest.raises(ValidationError, match="target of every disclosed EvidenceRecord"):
        build_cognitive_provider_request(
            provider_ref=_provider_ref("evidence"),
            invocation_ref=_invocation_ref("evidence"),
            intent_request=intent_request,
            context_envelope=context,
            disclosed_context_identities=(evidence.identity,),
        )


def test_projection_accepts_dependency_closed_evidence_subset() -> None:
    intent_request = _request("closed-evidence")
    context = _context(intent_request, "closed-evidence")
    claim = next(record for record in context.records if type(record) is ClaimRecord)
    evidence = next(record for record in context.records if type(record) is EvidenceRecord)

    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("closed-evidence"),
        invocation_ref=_invocation_ref("closed-evidence"),
        intent_request=intent_request,
        context_envelope=context,
        disclosed_context_identities=(evidence.identity, claim.identity),
    )

    assert {record.identity for record in provider_request.context_records} == {
        claim.identity,
        evidence.identity,
    }


def test_projection_requires_completeness_temporal_basis_to_be_disclosed() -> None:
    intent_request = _request("completeness")
    context = _context(intent_request, "completeness")
    completeness = next(
        record for record in context.records if type(record) is CompletenessRecord
    )

    with pytest.raises(ValidationError, match="every TemporalBasisRecord"):
        build_cognitive_provider_request(
            provider_ref=_provider_ref("completeness"),
            invocation_ref=_invocation_ref("completeness"),
            intent_request=intent_request,
            context_envelope=context,
            disclosed_context_identities=(completeness.identity,),
        )


def test_provider_port_is_one_request_to_one_candidate_proposal_surface() -> None:
    parameters = signature(CognitiveProviderPort.propose).parameters

    assert tuple(parameters) == ("self", "request")
    assert not hasattr(CognitiveProviderPort, "retrieve")
    assert not hasattr(CognitiveProviderPort, "search")
    assert not hasattr(CognitiveProviderPort, "admit")
    assert not hasattr(CognitiveProviderPort, "authorize")
    assert not hasattr(CognitiveProviderPort, "execute")


def test_matching_provider_candidate_crosses_boundary_unchanged() -> None:
    intent_request = _request("valid")
    context = _context(intent_request, "valid")
    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("valid"),
        invocation_ref=_invocation_ref("valid"),
        intent_request=intent_request,
        context_envelope=context,
    )
    expected = _candidate(provider_request)
    provider = _StaticProvider(expected)

    actual = invoke_cognitive_provider(provider, provider_request)

    assert isinstance(provider, CognitiveProviderPort)
    assert actual is expected
    assert provider.requests == [provider_request]
    assert actual.attribution.provider_ref == provider_request.provider_ref
    assert actual.attribution.invocation_ref == provider_request.invocation_ref


def test_provider_candidate_with_foreign_intent_lineage_fails_closed() -> None:
    intent_request = _request("lineage")
    context = _context(intent_request, "lineage")
    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("lineage"),
        invocation_ref=_invocation_ref("lineage"),
        intent_request=intent_request,
        context_envelope=context,
    )
    foreign = _request("foreign-lineage")
    provider = _StaticProvider(
        _candidate(provider_request, intent_request_identity=foreign.identity)
    )

    with pytest.raises(CognitiveProviderIntegrationError, match="foreign IntentRequest"):
        invoke_cognitive_provider(provider, provider_request)


def test_provider_candidate_with_foreign_context_lineage_fails_closed() -> None:
    intent_request = _request("context-lineage")
    context = _context(intent_request, "context-lineage")
    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("context-lineage"),
        invocation_ref=_invocation_ref("context-lineage"),
        intent_request=intent_request,
        context_envelope=context,
    )
    foreign_request = _request("foreign-context")
    foreign_context = _context(foreign_request, "foreign-context")
    provider = _StaticProvider(
        _candidate(
            provider_request,
            context_envelope_identity=foreign_context.identity,
        )
    )

    with pytest.raises(CognitiveProviderIntegrationError, match="foreign ContextEnvelope"):
        invoke_cognitive_provider(provider, provider_request)


def test_provider_candidate_with_wrong_provider_attribution_fails_closed() -> None:
    intent_request = _request("wrong-provider")
    context = _context(intent_request, "wrong-provider")
    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("expected"),
        invocation_ref=_invocation_ref("expected"),
        intent_request=intent_request,
        context_envelope=context,
    )
    provider = _StaticProvider(
        _candidate(provider_request, provider_ref=_provider_ref("foreign"))
    )

    with pytest.raises(CognitiveProviderIntegrationError, match="wrong provider_ref"):
        invoke_cognitive_provider(provider, provider_request)


def test_provider_candidate_with_wrong_invocation_attribution_fails_closed() -> None:
    intent_request = _request("wrong-invocation")
    context = _context(intent_request, "wrong-invocation")
    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("expected"),
        invocation_ref=_invocation_ref("expected"),
        intent_request=intent_request,
        context_envelope=context,
    )
    provider = _StaticProvider(
        _candidate(provider_request, invocation_ref=_invocation_ref("foreign"))
    )

    with pytest.raises(CognitiveProviderIntegrationError, match="wrong invocation_ref"):
        invoke_cognitive_provider(provider, provider_request)


def test_provider_must_return_exact_candidate_resolution() -> None:
    intent_request = _request("wrong-type")
    context = _context(intent_request, "wrong-type")
    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("wrong-type"),
        invocation_ref=_invocation_ref("wrong-type"),
        intent_request=intent_request,
        context_envelope=context,
    )

    with pytest.raises(CognitiveProviderIntegrationError, match="exact CandidateResolution"):
        invoke_cognitive_provider(_WrongTypeProvider(), provider_request)  # type: ignore[arg-type]


def test_transport_failure_is_not_converted_into_semantic_ir() -> None:
    intent_request = _request("transport")
    context = _context(intent_request, "transport")
    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("transport"),
        invocation_ref=_invocation_ref("transport"),
        intent_request=intent_request,
        context_envelope=context,
    )

    with pytest.raises(RuntimeError, match="transport unavailable"):
        invoke_cognitive_provider(_ExplodingProvider(), provider_request)


def test_provider_output_remains_proposal_not_admission_or_authority() -> None:
    intent_request = _request("authority")
    context = _context(intent_request, "authority")
    provider_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("authority"),
        invocation_ref=_invocation_ref("authority"),
        intent_request=intent_request,
        context_envelope=context,
    )
    candidate = invoke_cognitive_provider(
        _StaticProvider(_candidate(provider_request)),
        provider_request,
    )

    assert type(candidate) is CandidateResolution
    for forbidden in (
        "admission_attribution",
        "resolved_intent",
        "governance",
        "authorization",
        "permission",
        "approved",
        "executor",
        "execute",
        "outcome",
    ):
        assert not hasattr(candidate, forbidden)


def test_separate_provider_invocations_remain_separate_candidate_provenance() -> None:
    intent_request = _request("multiple")
    context = _context(intent_request, "multiple")
    first_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("one"),
        invocation_ref=_invocation_ref("one"),
        intent_request=intent_request,
        context_envelope=context,
    )
    second_request = build_cognitive_provider_request(
        provider_ref=_provider_ref("two"),
        invocation_ref=_invocation_ref("two"),
        intent_request=intent_request,
        context_envelope=context,
    )

    first = invoke_cognitive_provider(
        _StaticProvider(_candidate(first_request)),
        first_request,
    )
    second = invoke_cognitive_provider(
        _StaticProvider(_candidate(second_request)),
        second_request,
    )

    assert first.attribution != second.attribution
    assert first.intent_request_identity == second.intent_request_identity
    assert first.context_envelope_identity == second.context_envelope_identity
    assert first != second
