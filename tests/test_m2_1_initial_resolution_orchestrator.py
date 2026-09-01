from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    CandidateAttribution,
    CandidateResolution,
    ClarificationNeed,
    ClarificationProposal,
    ContextEnvelope,
    InformationNeed,
    InformationNeedProposal,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    ResolutionAttribution,
    ResolutionIssue,
    ResolutionIssueImpact,
    ResolutionIssueKind,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    ValidationError,
)
from intent_resolution_runtime.initial_resolution import (
    InitialResolutionFrontier,
    InitialResolutionFrontierKind,
    orchestrate_initial_resolution,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _request(label: str = "main") -> IntentRequest:
    return IntentRequest(
        origin=OriginAttribution(
            OriginKind.HUMAN,
            _ref("human", "user"),
            _ref("host.event", f"request-{label}"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression("Evaluate the admitted intent."),
    )


def _context(request: IntentRequest, label: str = "main") -> ContextEnvelope:
    return ContextEnvelope(
        request.identity,
        SourceAttribution(
            _ref("host.source", "context"),
            _ref("host.event", f"context-{label}"),
        ),
        (),
    )


def _admission(label: str = "main") -> ResolutionAttribution:
    return ResolutionAttribution(
        _ref("irr.resolver", "m2.1-initial-resolution"),
        _ref("irr.resolution_event", f"admit-{label}"),
    )


def _ambiguity() -> ResolutionIssue:
    return ResolutionIssue(
        ResolutionIssueKind.MATERIAL_AMBIGUITY,
        ResolutionIssueImpact.BLOCKING,
        "launch target",
        "Two admitted referents remain materially possible.",
        ("target:alpha", "target:beta"),
    )


def _missing() -> ResolutionIssue:
    return ResolutionIssue(
        ResolutionIssueKind.MISSING_INFORMATION,
        ResolutionIssueImpact.BLOCKING,
        "report freshness",
        "No attributable bounded freshness listing is admitted.",
    )


def _candidate(
    request: IntentRequest,
    context: ContextEnvelope,
    *,
    provider: str = "provider-a",
    invocation: str = "inv-001",
    semantics: str = "Answer the question from the admitted bounded context.",
    issues: tuple[ResolutionIssue, ...] = (),
    clarifications: tuple[ClarificationProposal, ...] = (),
    information_needs: tuple[InformationNeedProposal, ...] = (),
) -> CandidateResolution:
    return CandidateResolution(
        request.identity,
        context.identity,
        CandidateAttribution(
            _ref("irr.provider", provider),
            _ref("irr.provider_invocation", invocation),
        ),
        semantics,
        (),
        issues,
        clarifications,
        information_needs,
    )


def _resolved_admitter(
    request: IntentRequest,
    context: ContextEnvelope,
    candidates: tuple[CandidateResolution, ...],
    attribution: ResolutionAttribution,
) -> ResolvedIntent:
    return ResolvedIntent(
        request.identity,
        context.identity,
        attribution,
        "IRR independently admits the bounded answer semantics.",
        candidate_inputs=candidates,
    )


def _deterministic_admitter(
    request: IntentRequest,
    context: ContextEnvelope,
    candidates: tuple[CandidateResolution, ...],
    attribution: ResolutionAttribution,
) -> ResolvedIntent:
    assert candidates == ()
    return ResolvedIntent(
        request.identity,
        context.identity,
        attribution,
        "A deterministic IRR path resolves the simple request without provider candidate material.",
    )


def _clarification_admitter(
    request: IntentRequest,
    context: ContextEnvelope,
    candidates: tuple[CandidateResolution, ...],
    attribution: ResolutionAttribution,
) -> ClarificationNeed:
    issue = candidates[0].issues[0]
    return ClarificationNeed(
        request.identity,
        context.identity,
        attribution,
        "Which target do you mean: alpha or beta?",
        "launch target",
        (issue,),
        candidates,
    )


def _information_admitter(
    request: IntentRequest,
    context: ContextEnvelope,
    candidates: tuple[CandidateResolution, ...],
    attribution: ResolutionAttribution,
) -> InformationNeed:
    issue = candidates[0].issues[0]
    return InformationNeed(
        request.identity,
        context.identity,
        attribution,
        "An attributable bounded report listing with modification timestamps.",
        "admitted reports directory",
        "The term latest cannot be grounded from current Context.",
        (issue,),
        candidates,
    )


def test_no_resolution_material_yields_explicit_input_requirement_without_provider_call() -> None:
    request = _request()
    context = _context(request)

    frontier = orchestrate_initial_resolution(request, context)

    assert frontier.kind is InitialResolutionFrontierKind.RESOLUTION_INPUT_REQUIRED
    assert frontier.candidate_inputs == ()
    assert frontier.resolution_output is None
    assert frontier.intent_request_identity == request.identity
    assert frontier.context_envelope_identity == context.identity


def test_frontier_is_derived_runtime_view_not_new_canonical_ir_record() -> None:
    request = _request()
    frontier = orchestrate_initial_resolution(request, _context(request))

    assert isinstance(frontier, InitialResolutionFrontier)
    assert not hasattr(frontier, "canonical_bytes")
    assert not hasattr(frontier, "identity")


def test_context_must_belong_to_exact_request() -> None:
    request = _request("a")
    foreign_request = _request("b")
    foreign_context = _context(foreign_request)

    with pytest.raises(ValidationError, match="exact supplied IntentRequest"):
        orchestrate_initial_resolution(request, foreign_context)


def test_candidate_must_belong_to_exact_request_and_context_graph_slice() -> None:
    request = _request()
    context = _context(request, "a")
    other_context = _context(request, "b")
    foreign = _candidate(request, other_context)

    with pytest.raises(ValidationError, match="foreign ContextEnvelope lineage"):
        orchestrate_initial_resolution(
            request,
            context,
            candidate_inputs=(foreign,),
        )


def test_duplicate_candidate_delivery_cannot_amplify_semantic_weight() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)

    with pytest.raises(ValidationError, match="duplicate candidate identities"):
        orchestrate_initial_resolution(
            request,
            context,
            candidate_inputs=(candidate, candidate),
        )


def test_one_provider_candidate_is_not_automatically_admitted() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
    )

    assert frontier.kind is InitialResolutionFrontierKind.ADMISSION_REQUIRED
    assert frontier.candidate_inputs == (candidate,)
    assert frontier.resolution_output is None


def test_explicit_irr_admitter_can_admit_candidate_without_becoming_provider_authority() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admitter=_resolved_admitter,
        admission_attribution=_admission("resolved"),
    )

    assert frontier.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert isinstance(frontier.resolution_output, ResolvedIntent)
    assert frontier.resolution_output.semantics != candidate.proposed_semantics
    assert frontier.resolution_output.candidate_inputs == (candidate,)
    assert frontier.resolution_output.admission_attribution == _admission("resolved")


def test_deterministic_irr_path_can_resolve_without_provider_candidate() -> None:
    request = _request()
    context = _context(request)

    frontier = orchestrate_initial_resolution(
        request,
        context,
        admitter=_deterministic_admitter,
        admission_attribution=_admission("deterministic"),
    )

    assert frontier.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert isinstance(frontier.resolution_output, ResolvedIntent)
    assert frontier.resolution_output.candidate_inputs == ()


def test_equivalent_provider_candidates_require_admission_but_not_provider_precedence() -> None:
    request = _request()
    context = _context(request)
    first = _candidate(request, context, provider="provider-a", invocation="inv-a")
    second = _candidate(request, context, provider="provider-b", invocation="inv-b")

    a = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(first, second),
    )
    b = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(second, first),
    )

    assert a.kind is InitialResolutionFrontierKind.ADMISSION_REQUIRED
    assert b.kind is InitialResolutionFrontierKind.ADMISSION_REQUIRED
    assert a == b
    assert set(a.candidate_inputs) == {first, second}


def test_equivalent_candidates_can_be_admitted_with_all_exact_provenance() -> None:
    request = _request()
    context = _context(request)
    first = _candidate(request, context, provider="provider-a", invocation="inv-a")
    second = _candidate(request, context, provider="provider-b", invocation="inv-b")

    a = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(first, second),
        admitter=_resolved_admitter,
        admission_attribution=_admission("equivalent"),
    )
    b = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(second, first),
        admitter=_resolved_admitter,
        admission_attribution=_admission("equivalent"),
    )

    assert a == b
    assert isinstance(a.resolution_output, ResolvedIntent)
    assert set(a.resolution_output.candidate_inputs) == {first, second}


def test_semantically_distinct_candidates_require_adjudication_without_ranking() -> None:
    request = _request()
    context = _context(request)
    first = _candidate(
        request,
        context,
        provider="provider-a",
        invocation="inv-a",
        semantics="Interpret the request as target alpha.",
    )
    second = _candidate(
        request,
        context,
        provider="provider-b",
        invocation="inv-b",
        semantics="Interpret the request as target beta.",
    )

    a = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(first, second),
    )
    b = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(second, first),
    )

    assert a.kind is InitialResolutionFrontierKind.ADJUDICATION_REQUIRED
    assert b.kind is InitialResolutionFrontierKind.ADJUDICATION_REQUIRED
    assert a == b
    assert a.resolution_output is None


def test_candidate_majority_does_not_become_semantic_authority() -> None:
    request = _request()
    context = _context(request)
    alpha_a = _candidate(
        request,
        context,
        provider="provider-a",
        invocation="alpha-a",
        semantics="Use alpha.",
    )
    alpha_b = _candidate(
        request,
        context,
        provider="provider-b",
        invocation="alpha-b",
        semantics="Use alpha.",
    )
    beta = _candidate(
        request,
        context,
        provider="provider-c",
        invocation="beta",
        semantics="Use beta.",
    )

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(alpha_a, alpha_b, beta),
    )

    assert frontier.kind is InitialResolutionFrontierKind.ADJUDICATION_REQUIRED
    assert frontier.resolution_output is None


def test_explicit_admitter_can_adjudicate_distinct_candidates_only_with_full_provenance() -> None:
    request = _request()
    context = _context(request)
    first = _candidate(
        request,
        context,
        provider="provider-a",
        invocation="alpha",
        semantics="Use alpha.",
    )
    second = _candidate(
        request,
        context,
        provider="provider-b",
        invocation="beta",
        semantics="Use beta.",
    )

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(first, second),
        admitter=_resolved_admitter,
        admission_attribution=_admission("adjudicated"),
    )

    assert frontier.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert isinstance(frontier.resolution_output, ResolvedIntent)
    assert set(frontier.resolution_output.candidate_inputs) == {first, second}


def test_provider_clarification_proposal_does_not_pause_irr_without_admitter() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(
        request,
        context,
        semantics="The operation target remains ambiguous.",
        issues=(_ambiguity(),),
        clarifications=(
            ClarificationProposal(
                "Which target do you mean: alpha or beta?",
                "launch target",
                "The executable target is a material choice.",
            ),
        ),
    )

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
    )

    assert frontier.kind is InitialResolutionFrontierKind.ADMISSION_REQUIRED
    assert frontier.resolution_output is None

    admitted = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admitter=_clarification_admitter,
        admission_attribution=_admission("clarification"),
    )
    assert isinstance(admitted.resolution_output, ClarificationNeed)
    assert admitted.resolution_output.blocking_issues == (_ambiguity(),)


def test_provider_information_proposal_does_not_create_retrieval_authority() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(
        request,
        context,
        semantics="Latest remains unresolved without bounded freshness data.",
        issues=(_missing(),),
        information_needs=(
            InformationNeedProposal(
                "An attributable report listing with modification timestamps.",
                "admitted reports directory",
                "The term latest cannot be grounded from current Context.",
            ),
        ),
    )

    pending = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
    )
    assert pending.kind is InitialResolutionFrontierKind.ADMISSION_REQUIRED

    admitted = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admitter=_information_admitter,
        admission_attribution=_admission("information"),
    )
    assert isinstance(admitted.resolution_output, InformationNeed)
    assert "authorization" not in repr(admitted)


def test_admitter_may_abstain_without_mutating_frontier_semantics() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)

    def abstain(
        request: IntentRequest,
        context: ContextEnvelope,
        candidates: tuple[CandidateResolution, ...],
        attribution: ResolutionAttribution,
    ) -> None:
        return None

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admitter=abstain,
        admission_attribution=_admission("abstain"),
    )

    assert frontier.kind is InitialResolutionFrontierKind.ADMISSION_REQUIRED
    assert frontier.resolution_output is None


def test_admission_attribution_requires_explicit_admitter() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)

    with pytest.raises(ValidationError, match="without an explicit initial-resolution admitter"):
        orchestrate_initial_resolution(
            request,
            context,
            candidate_inputs=(candidate,),
            admission_attribution=_admission("ghost"),
        )


def test_admitter_requires_explicit_irr_admission_occurrence() -> None:
    request = _request()
    context = _context(request)

    with pytest.raises(ValidationError, match="requires explicit ResolutionAttribution"):
        orchestrate_initial_resolution(
            request,
            context,
            admitter=_deterministic_admitter,
        )


def test_admitter_cannot_replace_supplied_admission_attribution() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)

    def wrong_attribution(
        request: IntentRequest,
        context: ContextEnvelope,
        candidates: tuple[CandidateResolution, ...],
        attribution: ResolutionAttribution,
    ) -> ResolvedIntent:
        return ResolvedIntent(
            request.identity,
            context.identity,
            _admission("wrong"),
            "Resolved by a mismatched occurrence.",
            candidate_inputs=candidates,
        )

    with pytest.raises(ValidationError, match="exact supplied ResolutionAttribution"):
        orchestrate_initial_resolution(
            request,
            context,
            candidate_inputs=(candidate,),
            admitter=wrong_attribution,
            admission_attribution=_admission("expected"),
        )


def test_admitter_cannot_erase_or_invent_candidate_provenance() -> None:
    request = _request()
    context = _context(request)
    first = _candidate(request, context, provider="provider-a", invocation="a")
    second = _candidate(request, context, provider="provider-b", invocation="b")

    def erase_one(
        request: IntentRequest,
        context: ContextEnvelope,
        candidates: tuple[CandidateResolution, ...],
        attribution: ResolutionAttribution,
    ) -> ResolvedIntent:
        return ResolvedIntent(
            request.identity,
            context.identity,
            attribution,
            "Invalid provenance erasure.",
            candidate_inputs=(candidates[0],),
        )

    with pytest.raises(ValidationError, match="complete exact supplied candidate provenance"):
        orchestrate_initial_resolution(
            request,
            context,
            candidate_inputs=(first, second),
            admitter=erase_one,
            admission_attribution=_admission("erase"),
        )


def test_existing_admitted_output_is_reused_without_new_admission_transition() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)
    output = ResolvedIntent(
        request.identity,
        context.identity,
        _admission("historical"),
        "Historical independently admitted semantics.",
        candidate_inputs=(candidate,),
    )

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admitted_outputs=(output,),
    )

    assert frontier.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert frontier.resolution_output is output
    assert frontier.resolution_output.admission_attribution == _admission("historical")

    with pytest.raises(ValidationError, match="cannot be combined with a new admission transition"):
        orchestrate_initial_resolution(
            request,
            context,
            admitted_outputs=(output,),
            admitter=_resolved_admitter,
            admission_attribution=_admission("new"),
        )


def test_competing_admitted_initial_outputs_fail_closed() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)
    first = ResolvedIntent(
        request.identity,
        context.identity,
        _admission("first"),
        "First admitted semantics.",
        candidate_inputs=(candidate,),
    )
    second = ResolvedIntent(
        request.identity,
        context.identity,
        _admission("second"),
        "Second admitted semantics.",
        candidate_inputs=(candidate,),
    )

    with pytest.raises(ValidationError, match="competing admitted ResolutionOutput"):
        orchestrate_initial_resolution(
            request,
            context,
            admitted_outputs=(first, second),
        )


def test_candidate_outside_existing_output_provenance_is_orphaned() -> None:
    request = _request()
    context = _context(request)
    admitted_candidate = _candidate(
        request,
        context,
        provider="provider-a",
        invocation="admitted",
    )
    late_candidate = _candidate(
        request,
        context,
        provider="provider-b",
        invocation="late",
    )
    output = ResolvedIntent(
        request.identity,
        context.identity,
        _admission("existing"),
        "Historical semantics.",
        candidate_inputs=(admitted_candidate,),
    )

    with pytest.raises(ValidationError, match="orphaned"):
        orchestrate_initial_resolution(
            request,
            context,
            candidate_inputs=(late_candidate,),
            admitted_outputs=(output,),
        )
