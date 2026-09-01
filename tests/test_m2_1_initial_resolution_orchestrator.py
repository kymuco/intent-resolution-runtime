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


def _uncertainty() -> ResolutionIssue:
    return ResolutionIssue(
        ResolutionIssueKind.UNCERTAINTY,
        ResolutionIssueImpact.BLOCKING,
        "target state",
        "The admitted material does not establish the target state.",
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


def test_no_candidate_material_yields_explicit_candidate_input_requirement() -> None:
    request = _request()
    context = _context(request)

    frontier = orchestrate_initial_resolution(request, context)

    assert frontier.kind is InitialResolutionFrontierKind.CANDIDATE_INPUT_REQUIRED
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
            admission_attribution=_admission(),
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
            admission_attribution=_admission(),
        )


def test_one_unblocked_candidate_admits_resolved_intent() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admission_attribution=_admission(),
    )

    assert frontier.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert isinstance(frontier.resolution_output, ResolvedIntent)
    assert frontier.resolution_output.semantics == candidate.proposed_semantics
    assert frontier.resolution_output.candidate_inputs == (candidate,)
    assert frontier.candidate_inputs == frontier.resolution_output.candidate_inputs


def test_equivalent_provider_candidates_preserve_provenance_without_precedence() -> None:
    request = _request()
    context = _context(request)
    first = _candidate(request, context, provider="provider-a", invocation="inv-a")
    second = _candidate(request, context, provider="provider-b", invocation="inv-b")

    a = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(first, second),
        admission_attribution=_admission("equivalent"),
    )
    b = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(second, first),
        admission_attribution=_admission("equivalent"),
    )

    assert a.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert isinstance(a.resolution_output, ResolvedIntent)
    assert a == b
    assert a.resolution_output == b.resolution_output
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
        admission_attribution=_admission("unused-a"),
    )
    b = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(second, first),
        admission_attribution=_admission("unused-b"),
    )

    assert a.kind is InitialResolutionFrontierKind.ADJUDICATION_REQUIRED
    assert b.kind is InitialResolutionFrontierKind.ADJUDICATION_REQUIRED
    assert a.candidate_inputs == b.candidate_inputs
    assert a.resolution_output is None
    assert b.resolution_output is None


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
        admission_attribution=_admission("majority"),
    )

    assert frontier.kind is InitialResolutionFrontierKind.ADJUDICATION_REQUIRED
    assert frontier.resolution_output is None


def test_single_blocking_issue_with_unique_clarification_path_admits_pause() -> None:
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
        admission_attribution=_admission("clarification"),
    )

    assert frontier.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert isinstance(frontier.resolution_output, ClarificationNeed)
    assert frontier.resolution_output.blocking_issues == (_ambiguity(),)
    assert frontier.resolution_output.candidate_inputs == (candidate,)


def test_single_blocking_issue_with_unique_information_path_admits_information_need() -> None:
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

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admission_attribution=_admission("information"),
    )

    assert frontier.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert isinstance(frontier.resolution_output, InformationNeed)
    assert frontier.resolution_output.blocking_issues == (_missing(),)
    assert frontier.resolution_output.candidate_inputs == (candidate,)


def test_multiple_blocking_issues_do_not_get_guessed_into_one_pause() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(
        request,
        context,
        semantics="Multiple independent blockers remain.",
        issues=(_missing(), _uncertainty()),
        clarifications=(
            ClarificationProposal(
                "Please clarify the missing material.",
                "resolution blockers",
                "M2.1 has no typed mapping from one proposal to multiple blockers.",
            ),
        ),
    )

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admission_attribution=_admission("multiple-blockers"),
    )

    assert frontier.kind is InitialResolutionFrontierKind.ADJUDICATION_REQUIRED
    assert frontier.resolution_output is None


def test_competing_pause_modes_require_adjudication() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(
        request,
        context,
        semantics="The missing fact could be obtained or clarified by the caller.",
        issues=(_missing(),),
        clarifications=(
            ClarificationProposal(
                "Which bounded listing should be used?",
                "report source",
                "Caller selection would resolve the source semantics.",
            ),
        ),
        information_needs=(
            InformationNeedProposal(
                "An attributable bounded report listing.",
                "reports",
                "Freshness is otherwise unknown.",
            ),
        ),
    )

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admission_attribution=_admission("competing-pause"),
    )

    assert frontier.kind is InitialResolutionFrontierKind.ADJUDICATION_REQUIRED
    assert frontier.resolution_output is None


def test_deterministic_admission_requires_explicit_irr_admission_occurrence() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)

    with pytest.raises(ValidationError, match="explicit ResolutionAttribution"):
        orchestrate_initial_resolution(
            request,
            context,
            candidate_inputs=(candidate,),
        )


def test_existing_admitted_output_is_reused_without_rewriting_history() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)
    output = ResolvedIntent(
        request.identity,
        context.identity,
        _admission("historical"),
        candidate.proposed_semantics,
        (),
        (),
        (candidate,),
    )

    frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admitted_outputs=(output,),
        admission_attribution=_admission("ignored-new"),
    )

    assert frontier.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert frontier.resolution_output is output
    assert frontier.resolution_output.admission_attribution == _admission("historical")


def test_competing_admitted_initial_outputs_fail_closed() -> None:
    request = _request()
    context = _context(request)
    candidate = _candidate(request, context)
    first = ResolvedIntent(
        request.identity,
        context.identity,
        _admission("first"),
        candidate.proposed_semantics,
        candidate_inputs=(candidate,),
    )
    second = ResolvedIntent(
        request.identity,
        context.identity,
        _admission("second"),
        candidate.proposed_semantics,
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
        admitted_candidate.proposed_semantics,
        candidate_inputs=(admitted_candidate,),
    )

    with pytest.raises(ValidationError, match="orphaned"):
        orchestrate_initial_resolution(
            request,
            context,
            candidate_inputs=(late_candidate,),
            admitted_outputs=(output,),
        )
