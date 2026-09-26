from __future__ import annotations

from dataclasses import replace

import pytest

from intent_resolution_runtime import (
    BindingAttribution,
    BindingInputRole,
    BindingIssue,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    CandidateAttribution,
    CandidateResolution,
    ClaimRecord,
    ContextEnvelope,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    IntentExpression,
    IntentRequest,
    InterchangeableChoicePolicy,
    OriginAttribution,
    OriginKind,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    SuccessorCandidateResolution,
    SuccessorCognitiveProviderIntegrationError,
    SuccessorCognitiveProviderPort,
    SuccessorCognitiveProviderRequest,
    SymbolicReference,
    ValidationError,
    build_successor_cognitive_provider_request,
    evaluate_binding,
    invoke_successor_cognitive_provider,
)

SOURCE_ID = RecordIdentity("sha256", "3" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _request() -> IntentRequest:
    return IntentRequest(
        origin=OriginAttribution(
            kind=OriginKind.HUMAN,
            actor_ref=_ref("principal", "user"),
            source_event_ref=_ref("event", "intent-m4.1"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression(text="Continue the exact bounded project."),
    )


def _claim() -> ClaimRecord:
    return ClaimRecord(
        attribution=SourceAttribution(
            source_ref=_ref("source", "host"),
            source_event_ref=_ref("event", "claim-m4.1"),
        ),
        statement="The bounded project workspace is available.",
    )


def _context(request: IntentRequest) -> ContextEnvelope:
    claim = _claim()
    return ContextEnvelope(
        intent_request_identity=request.identity,
        boundary_attribution=SourceAttribution(
            source_ref=_ref("source", "host"),
            source_event_ref=_ref("event", "context-m4.1"),
        ),
        records=(claim,),
    )


def _predecessor(request: IntentRequest, context: ContextEnvelope) -> ResolvedIntent:
    return ResolvedIntent(
        intent_request_identity=request.identity,
        context_envelope_identity=context.identity,
        admission_attribution=ResolutionAttribution(
            _ref("irr.resolver", "m4.1-test"),
            _ref("event", "predecessor-m4.1"),
        ),
        semantics="Continue only from exact attributable re-entry material.",
        assumptions=(),
        unresolved_issues=(),
        candidate_inputs=(),
    )


def _issue(predecessor: ResolvedIntent) -> BindingIssue:
    symbolic = SymbolicReference(
        predecessor.identity,
        _ref("irr.slot", "workspace"),
        "artifact.path",
        "workspace:project",
        "Select the exact workspace path.",
    )
    rule = BindingRule(
        predecessor.identity,
        _ref("irr.binding_rule", "workspace"),
        symbolic,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (_ref("host.source", "filesystem"),),
        (SOURCE_ID,),
        "artifact.path",
        "workspace:project",
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.REQUIRE_UNIQUE,
            (),
            (),
            InterchangeableChoicePolicy.NONE,
        ),
        "Require one exact admitted workspace path.",
        (),
        (),
        (),
    )
    issue = evaluate_binding(
        rule,
        (),
        attribution=BindingAttribution(
            _ref("irr.evaluator", "binding"),
            _ref("event", "binding-m4.1"),
        ),
    )
    assert type(issue) is BindingIssue
    return issue


def _continuation(predecessor: ResolvedIntent) -> ContinuationInput:
    return ContinuationInput(
        attribution=ContinuationInputAttribution(
            _ref("irr.host", "hde-shell"),
            _ref("event", "reentry-m4.1"),
        ),
        source_kind=ContinuationSourceKind.BINDING_ISSUE,
        source=_issue(predecessor),
    )


def _candidate(
    request: SuccessorCognitiveProviderRequest,
    *,
    provider_ref: StableRef | None = None,
    invocation_ref: StableRef | None = None,
    intent_request_identity: RecordIdentity | None = None,
    context_envelope_identity: RecordIdentity | None = None,
) -> CandidateResolution:
    return CandidateResolution(
        intent_request_identity=(
            intent_request_identity or request.intent_request_identity
        ),
        context_envelope_identity=(
            context_envelope_identity or request.context_envelope_identity
        ),
        attribution=CandidateAttribution(
            provider_ref or request.provider_ref,
            invocation_ref or request.invocation_ref,
        ),
        proposed_semantics="Continue from the exact re-entry material.",
    )


class _Provider:
    def __init__(self) -> None:
        self.seen: SuccessorCognitiveProviderRequest | None = None

    def propose_successor(
        self,
        request: SuccessorCognitiveProviderRequest,
    ) -> CandidateResolution:
        self.seen = request
        return _candidate(request)


def _sources():
    request = _request()
    context = _context(request)
    predecessor = _predecessor(request, context)
    continuation = _continuation(predecessor)
    return request, context, predecessor, continuation


def test_builder_preserves_exact_successor_projection_without_candidate_provenance() -> None:
    request, context, predecessor, continuation = _sources()
    claim = context.records[0]

    projection = build_successor_cognitive_provider_request(
        provider_ref=_ref("provider", "professor"),
        invocation_ref=_ref("invocation", "m4.1"),
        intent_request=request,
        predecessor=predecessor,
        context_envelope=context,
        continuation_inputs=(continuation,),
        disclosed_context_identities=(claim.identity,),
    )

    assert projection.intent_expression == request.expression
    assert projection.predecessor_identity == predecessor.identity
    assert projection.predecessor_semantics == predecessor.semantics
    assert projection.predecessor_assumptions == predecessor.assumptions
    assert projection.predecessor_unresolved_issues == predecessor.unresolved_issues
    assert projection.continuation_inputs == (continuation,)
    assert projection.context_records == (claim,)
    assert not hasattr(projection, "predecessor_candidate_inputs")


def test_builder_discloses_only_explicit_context_records() -> None:
    request, context, predecessor, continuation = _sources()

    projection = build_successor_cognitive_provider_request(
        provider_ref=_ref("provider", "local"),
        invocation_ref=_ref("invocation", "empty-context"),
        intent_request=request,
        predecessor=predecessor,
        context_envelope=context,
        continuation_inputs=(continuation,),
    )

    assert projection.context_records == ()


def test_request_requires_nonempty_exact_continuation_material() -> None:
    request, context, predecessor, continuation = _sources()
    base = build_successor_cognitive_provider_request(
        provider_ref=_ref("provider", "local"),
        invocation_ref=_ref("invocation", "valid"),
        intent_request=request,
        predecessor=predecessor,
        context_envelope=context,
        continuation_inputs=(continuation,),
    )

    with pytest.raises(ValidationError, match="must not be empty"):
        replace(base, continuation_inputs=())


def test_builder_rejects_foreign_continuation_predecessor() -> None:
    request, context, predecessor, _continuation_value = _sources()
    foreign = ResolvedIntent(
        request.identity,
        context.identity,
        ResolutionAttribution(
            _ref("irr.resolver", "m4.1-test"),
            _ref("event", "foreign-predecessor"),
        ),
        "Foreign predecessor.",
    )

    with pytest.raises(ValidationError, match="exact predecessor"):
        build_successor_cognitive_provider_request(
            provider_ref=_ref("provider", "local"),
            invocation_ref=_ref("invocation", "foreign"),
            intent_request=request,
            predecessor=predecessor,
            context_envelope=context,
            continuation_inputs=(_continuation(foreign),),
        )


def test_manual_request_drift_is_rejected_before_provider_invocation() -> None:
    request, context, predecessor, continuation = _sources()
    projection = build_successor_cognitive_provider_request(
        provider_ref=_ref("provider", "local"),
        invocation_ref=_ref("invocation", "drift"),
        intent_request=request,
        predecessor=predecessor,
        context_envelope=context,
        continuation_inputs=(continuation,),
    )
    drifted = replace(projection, predecessor_semantics="Changed semantics.")
    provider = _Provider()

    with pytest.raises(ValidationError, match="exact predecessor semantics"):
        invoke_successor_cognitive_provider(
            provider,
            drifted,
            intent_request=request,
            predecessor=predecessor,
            context_envelope=context,
            continuation_inputs=(continuation,),
        )

    assert provider.seen is None


def test_provider_protocol_is_separate_from_initial_provider_port() -> None:
    provider = _Provider()

    assert isinstance(provider, SuccessorCognitiveProviderPort)
    assert hasattr(provider, "propose_successor")
    assert not hasattr(provider, "propose")


def test_successful_invocation_returns_exact_successor_candidate() -> None:
    request, context, predecessor, continuation = _sources()
    projection = build_successor_cognitive_provider_request(
        provider_ref=_ref("provider", "professor"),
        invocation_ref=_ref("invocation", "success"),
        intent_request=request,
        predecessor=predecessor,
        context_envelope=context,
        continuation_inputs=(continuation,),
    )
    provider = _Provider()

    result = invoke_successor_cognitive_provider(
        provider,
        projection,
        intent_request=request,
        predecessor=predecessor,
        context_envelope=context,
        continuation_inputs=(continuation,),
    )

    assert type(result) is SuccessorCandidateResolution
    assert provider.seen == projection
    assert result.predecessor == predecessor
    assert result.continuation_inputs == (continuation,)
    assert result.candidate == _candidate(projection)


class _WrongTypeProvider:
    def propose_successor(self, request: SuccessorCognitiveProviderRequest):
        return "not-a-candidate"


def test_provider_must_return_exact_candidate_resolution() -> None:
    request, context, predecessor, continuation = _sources()
    projection = build_successor_cognitive_provider_request(
        provider_ref=_ref("provider", "wrong-type"),
        invocation_ref=_ref("invocation", "wrong-type"),
        intent_request=request,
        predecessor=predecessor,
        context_envelope=context,
        continuation_inputs=(continuation,),
    )

    with pytest.raises(
        SuccessorCognitiveProviderIntegrationError,
        match="exact CandidateResolution",
    ):
        invoke_successor_cognitive_provider(
            _WrongTypeProvider(),
            projection,
            intent_request=request,
            predecessor=predecessor,
            context_envelope=context,
            continuation_inputs=(continuation,),
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "intent_request_identity",
            RecordIdentity("sha256", "9" * 64),
            "foreign IntentRequest",
        ),
        (
            "context_envelope_identity",
            RecordIdentity("sha256", "8" * 64),
            "foreign ContextEnvelope",
        ),
    ],
)
def test_provider_candidate_lineage_must_match_request(
    field,
    value,
    message,
) -> None:
    request, context, predecessor, continuation = _sources()
    projection = build_successor_cognitive_provider_request(
        provider_ref=_ref("provider", "lineage"),
        invocation_ref=_ref("invocation", "lineage"),
        intent_request=request,
        predecessor=predecessor,
        context_envelope=context,
        continuation_inputs=(continuation,),
    )

    class _ForeignProvider:
        def propose_successor(
            self,
            provider_request: SuccessorCognitiveProviderRequest,
        ) -> CandidateResolution:
            kwargs = {field: value}
            return _candidate(provider_request, **kwargs)

    with pytest.raises(SuccessorCognitiveProviderIntegrationError, match=message):
        invoke_successor_cognitive_provider(
            _ForeignProvider(),
            projection,
            intent_request=request,
            predecessor=predecessor,
            context_envelope=context,
            continuation_inputs=(continuation,),
        )


def test_provider_attribution_must_match_request() -> None:
    request, context, predecessor, continuation = _sources()
    projection = build_successor_cognitive_provider_request(
        provider_ref=_ref("provider", "expected"),
        invocation_ref=_ref("invocation", "expected"),
        intent_request=request,
        predecessor=predecessor,
        context_envelope=context,
        continuation_inputs=(continuation,),
    )

    class _WrongProviderRef:
        def propose_successor(
            self,
            provider_request: SuccessorCognitiveProviderRequest,
        ) -> CandidateResolution:
            return _candidate(
                provider_request,
                provider_ref=_ref("provider", "wrong"),
            )

    with pytest.raises(
        SuccessorCognitiveProviderIntegrationError,
        match="wrong provider_ref",
    ):
        invoke_successor_cognitive_provider(
            _WrongProviderRef(),
            projection,
            intent_request=request,
            predecessor=predecessor,
            context_envelope=context,
            continuation_inputs=(continuation,),
        )


def test_provider_exception_remains_mechanism_failure() -> None:
    request, context, predecessor, continuation = _sources()
    projection = build_successor_cognitive_provider_request(
        provider_ref=_ref("provider", "broken"),
        invocation_ref=_ref("invocation", "broken"),
        intent_request=request,
        predecessor=predecessor,
        context_envelope=context,
        continuation_inputs=(continuation,),
    )

    class _BrokenProvider:
        def propose_successor(
            self,
            provider_request: SuccessorCognitiveProviderRequest,
        ) -> CandidateResolution:
            raise RuntimeError("provider transport failed")

    with pytest.raises(RuntimeError, match="provider transport failed"):
        invoke_successor_cognitive_provider(
            _BrokenProvider(),
            projection,
            intent_request=request,
            predecessor=predecessor,
            context_envelope=context,
            continuation_inputs=(continuation,),
        )
