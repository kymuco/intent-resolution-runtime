from __future__ import annotations

import copy
from inspect import signature

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
    ClarificationNeed,
    ContextEnvelope,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    HistoryRecord,
    InMemoryAdmittedHistoryRepository,
    InformationNeed,
    InterchangeableChoicePolicy,
    RecordIdentity,
    ResolutionAttribution,
    ResolutionIssue,
    ResolutionIssueImpact,
    ResolutionIssueKind,
    ResolvedIntent,
    SerializationError,
    SourceAttribution,
    StableRef,
    SuccessorCandidateResolution,
    SuccessorResolutionFrontierKind,
    SuccessorResolutionLineage,
    SymbolicReference,
    ValidationError,
    evaluate_binding,
    orchestrate_successor_resolution,
)

REQUEST = RecordIdentity("sha256", "1" * 64)
PREDECESSOR_CONTEXT = RecordIdentity("sha256", "2" * 64)
SOURCE_ID = RecordIdentity("sha256", "3" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _predecessor(
    *,
    event: str = "resolve-predecessor-m4",
    request_identity: RecordIdentity = REQUEST,
) -> ResolvedIntent:
    return ResolvedIntent(
        intent_request_identity=request_identity,
        context_envelope_identity=PREDECESSOR_CONTEXT,
        admission_attribution=ResolutionAttribution(
            _ref("irr.resolver", "m4-test"),
            _ref("irr.event", event),
        ),
        semantics="Inspect one bounded project and continue from explicit re-entry.",
        assumptions=(),
        unresolved_issues=(),
        candidate_inputs=(),
    )


def _context(
    predecessor: ResolvedIntent,
    *,
    label: str = "successor-context",
) -> ContextEnvelope:
    return ContextEnvelope(
        intent_request_identity=predecessor.intent_request_identity,
        boundary_attribution=SourceAttribution(
            source_ref=_ref("irr.context_source", "host"),
            source_event_ref=_ref("irr.event", label),
        ),
        records=(),
    )


def _binding_issue(predecessor: ResolvedIntent, suffix: str) -> BindingIssue:
    scope = f"workspace:{suffix}"
    symbolic = SymbolicReference(
        predecessor.identity,
        _ref("irr.slot", f"selected-{suffix}"),
        "artifact.path",
        scope,
        f"Select one exact path for {suffix}.",
    )
    rule = BindingRule(
        predecessor.identity,
        _ref("irr.binding_rule", f"select-{suffix}"),
        symbolic,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (_ref("host.source", f"filesystem-{suffix}"),),
        (SOURCE_ID,),
        "artifact.path",
        scope,
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.REQUIRE_UNIQUE,
            (),
            (),
            InterchangeableChoicePolicy.NONE,
        ),
        f"Require one exact admitted path for {suffix}.",
        (),
        (),
        (),
    )
    issue = evaluate_binding(
        rule,
        (),
        attribution=BindingAttribution(
            _ref("irr.evaluator", "mechanical-binding-v1"),
            _ref("irr.event", f"binding-{suffix}-001"),
        ),
    )
    assert type(issue) is BindingIssue
    return issue


def _continuation(
    predecessor: ResolvedIntent,
    suffix: str = "primary",
    *,
    event: str | None = None,
) -> ContinuationInput:
    return ContinuationInput(
        attribution=ContinuationInputAttribution(
            _ref("irr.host", "m4-test"),
            _ref("irr.event", event or f"reentry-{suffix}-001"),
        ),
        source_kind=ContinuationSourceKind.BINDING_ISSUE,
        source=_binding_issue(predecessor, suffix),
    )


def _candidate_body(
    predecessor: ResolvedIntent,
    context: ContextEnvelope,
    *,
    provider: str = "provider-a",
    invocation: str = "invocation-a",
    semantics: str = "Continue with the exact selected bounded workspace.",
) -> CandidateResolution:
    return CandidateResolution(
        intent_request_identity=predecessor.intent_request_identity,
        context_envelope_identity=context.identity,
        attribution=CandidateAttribution(
            provider_ref=_ref("irr.provider", provider),
            invocation_ref=_ref("irr.invocation", invocation),
        ),
        proposed_semantics=semantics,
        assumptions=(),
        issues=(),
        clarification_proposals=(),
        information_need_proposals=(),
    )


def _successor_candidate(
    predecessor: ResolvedIntent,
    context: ContextEnvelope,
    continuation: ContinuationInput,
    *,
    provider: str = "provider-a",
    invocation: str = "invocation-a",
    semantics: str = "Continue with the exact selected bounded workspace.",
) -> SuccessorCandidateResolution:
    return SuccessorCandidateResolution(
        predecessor=predecessor,
        continuation_inputs=(continuation,),
        candidate=_candidate_body(
            predecessor,
            context,
            provider=provider,
            invocation=invocation,
            semantics=semantics,
        ),
    )


def _admission(label: str = "successor") -> ResolutionAttribution:
    return ResolutionAttribution(
        _ref("irr.resolver", "m4-successor-admitter"),
        _ref("irr.event", f"admit-{label}"),
    )


def _nested(
    candidates: tuple[SuccessorCandidateResolution, ...],
) -> tuple[CandidateResolution, ...]:
    return tuple(sorted((item.candidate for item in candidates), key=lambda item: str(item.identity)))


def _resolved_admitter(
    predecessor: ResolvedIntent,
    context: ContextEnvelope,
    inputs: tuple[ContinuationInput, ...],
    candidates: tuple[SuccessorCandidateResolution, ...],
    attribution: ResolutionAttribution,
) -> ResolvedIntent:
    assert inputs
    return ResolvedIntent(
        intent_request_identity=predecessor.intent_request_identity,
        context_envelope_identity=context.identity,
        admission_attribution=attribution,
        semantics="Successor semantics admitted from exact re-entry material.",
        assumptions=(),
        unresolved_issues=(),
        candidate_inputs=_nested(candidates),
    )


def _ambiguity() -> ResolutionIssue:
    return ResolutionIssue(
        ResolutionIssueKind.MATERIAL_AMBIGUITY,
        ResolutionIssueImpact.BLOCKING,
        "workspace:selection",
        "Two material successor scopes remain possible.",
        ("workspace:a", "workspace:b"),
    )


def _missing() -> ResolutionIssue:
    return ResolutionIssue(
        ResolutionIssueKind.MISSING_INFORMATION,
        ResolutionIssueImpact.BLOCKING,
        "workspace:path",
        "One exact path is still missing.",
        (),
    )


def _clarification_admitter(
    predecessor: ResolvedIntent,
    context: ContextEnvelope,
    inputs: tuple[ContinuationInput, ...],
    candidates: tuple[SuccessorCandidateResolution, ...],
    attribution: ResolutionAttribution,
) -> ClarificationNeed:
    assert inputs
    return ClarificationNeed(
        intent_request_identity=predecessor.intent_request_identity,
        context_envelope_identity=context.identity,
        admission_attribution=attribution,
        question="Which exact successor workspace should be used?",
        scope="workspace:selection",
        blocking_issues=(_ambiguity(),),
        candidate_inputs=_nested(candidates),
    )


def _information_admitter(
    predecessor: ResolvedIntent,
    context: ContextEnvelope,
    inputs: tuple[ContinuationInput, ...],
    candidates: tuple[SuccessorCandidateResolution, ...],
    attribution: ResolutionAttribution,
) -> InformationNeed:
    assert inputs
    return InformationNeed(
        intent_request_identity=predecessor.intent_request_identity,
        context_envelope_identity=context.identity,
        admission_attribution=attribution,
        description="Obtain one exact successor workspace path.",
        scope="workspace:path",
        reason="Successor semantics cannot proceed without the exact path.",
        blocking_issues=(_missing(),),
        candidate_inputs=_nested(candidates),
    )


def test_successor_candidate_is_canonical_and_history_round_trips() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)
    candidate = _successor_candidate(predecessor, context, continuation)

    decoded = SuccessorCandidateResolution.from_json_bytes(candidate.canonical_bytes())
    assert decoded == candidate
    assert decoded.identity == candidate.identity

    repository = InMemoryAdmittedHistoryRepository()
    record = HistoryRecord.from_canonical_bytes(candidate.canonical_bytes())
    repository.persist(record)
    restored = repository.get(candidate.identity)
    assert restored is not None
    assert restored.record_type == SuccessorCandidateResolution.SCHEMA
    assert (
        SuccessorCandidateResolution.from_json_bytes(restored.canonical_record_bytes)
        == candidate
    )


def test_successor_candidate_requires_nonempty_exact_continuation_tuple() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    body = _candidate_body(predecessor, context)

    with pytest.raises(ValidationError, match="must be a tuple"):
        SuccessorCandidateResolution(
            predecessor,
            [],  # type: ignore[arg-type]
            body,
        )
    with pytest.raises(ValidationError, match="must not be empty"):
        SuccessorCandidateResolution(predecessor, (), body)


def test_successor_candidate_rejects_duplicate_and_same_source_amplification() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    first = _continuation(predecessor, "duplicate")
    body = _candidate_body(predecessor, context)

    with pytest.raises(ValidationError, match="duplicate ContinuationInput"):
        SuccessorCandidateResolution(predecessor, (first, first), body)

    source = _binding_issue(predecessor, "same-source")
    a = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "m4-test"),
            _ref("irr.event", "reentry-same-a"),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        source,
    )
    b = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "m4-test"),
            _ref("irr.event", "reentry-same-b"),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        source,
    )
    with pytest.raises(ValidationError, match="must not amplify one source"):
        SuccessorCandidateResolution(predecessor, (a, b), body)


def test_successor_candidate_rejects_foreign_predecessor_or_request() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)
    foreign = _predecessor(
        event="foreign-predecessor",
        request_identity=RecordIdentity("sha256", "9" * 64),
    )

    with pytest.raises(ValidationError, match="exact predecessor"):
        SuccessorCandidateResolution(
            predecessor,
            (_continuation(foreign, "foreign"),),
            _candidate_body(predecessor, context),
        )

    foreign_body = CandidateResolution(
        intent_request_identity=foreign.intent_request_identity,
        context_envelope_identity=context.identity,
        attribution=CandidateAttribution(
            _ref("irr.provider", "foreign"),
            _ref("irr.invocation", "foreign"),
        ),
        proposed_semantics="Foreign request semantics.",
    )
    with pytest.raises(ValidationError, match="predecessor IntentRequest"):
        SuccessorCandidateResolution(
            predecessor,
            (continuation,),
            foreign_body,
        )


def test_wire_is_closed_and_does_not_reclassify_continuation_as_context() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    candidate = _successor_candidate(
        predecessor,
        context,
        _continuation(predecessor),
    )
    primitive = candidate.to_primitive()

    assert set(primitive) == {
        "schema",
        "predecessor",
        "continuation_inputs",
        "candidate",
    }
    assert "context" not in primitive
    assert "context_records" not in primitive

    mutated = copy.deepcopy(primitive)
    mutated["authorized"] = "true"
    with pytest.raises(SerializationError, match="invalid fields"):
        SuccessorCandidateResolution.from_primitive(mutated)


def test_no_candidates_requires_resolution_input() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)

    frontier = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
    )

    assert frontier.kind is SuccessorResolutionFrontierKind.RESOLUTION_INPUT_REQUIRED
    assert frontier.candidate_inputs == ()
    assert frontier.resolution_output is None
    assert frontier.successor_lineage is None


def test_equivalent_candidates_require_admission_without_provider_voting() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)
    first = _successor_candidate(
        predecessor,
        context,
        continuation,
        provider="provider-a",
        invocation="a",
    )
    second = _successor_candidate(
        predecessor,
        context,
        continuation,
        provider="provider-b",
        invocation="b",
    )

    a = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        candidate_inputs=(first, second),
    )
    b = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        candidate_inputs=(second, first),
    )

    assert a.kind is SuccessorResolutionFrontierKind.ADMISSION_REQUIRED
    assert a == b
    assert a.resolution_output is None


def test_divergent_candidates_require_adjudication_and_majority_has_no_authority() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)
    alpha_a = _successor_candidate(
        predecessor,
        context,
        continuation,
        provider="provider-a",
        invocation="alpha-a",
        semantics="Use alpha.",
    )
    alpha_b = _successor_candidate(
        predecessor,
        context,
        continuation,
        provider="provider-b",
        invocation="alpha-b",
        semantics="Use alpha.",
    )
    beta = _successor_candidate(
        predecessor,
        context,
        continuation,
        provider="provider-c",
        invocation="beta",
        semantics="Use beta.",
    )

    frontier = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        candidate_inputs=(alpha_a, alpha_b, beta),
    )

    assert frontier.kind is SuccessorResolutionFrontierKind.ADJUDICATION_REQUIRED
    assert frontier.resolution_output is None


def test_orchestrator_rejects_foreign_context_candidate_and_continuation_set() -> None:
    predecessor = _predecessor()
    context = _context(predecessor, label="current-context")
    foreign_context = _context(predecessor, label="foreign-context")
    primary = _continuation(predecessor, "primary")
    other = _continuation(predecessor, "other")

    foreign_context_candidate = _successor_candidate(
        predecessor,
        foreign_context,
        primary,
    )
    with pytest.raises(ValidationError, match="foreign ContextEnvelope"):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (primary,),
            candidate_inputs=(foreign_context_candidate,),
        )

    foreign_input_candidate = _successor_candidate(
        predecessor,
        context,
        other,
    )
    with pytest.raises(ValidationError, match="foreign continuation"):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (primary,),
            candidate_inputs=(foreign_input_candidate,),
        )


def test_successor_context_must_preserve_intent_request_lineage() -> None:
    predecessor = _predecessor()
    foreign = _predecessor(
        event="foreign-request",
        request_identity=RecordIdentity("sha256", "8" * 64),
    )
    foreign_context = _context(foreign)

    with pytest.raises(ValidationError, match="predecessor IntentRequest"):
        orchestrate_successor_resolution(
            predecessor,
            foreign_context,
            (_continuation(predecessor),),
        )


def test_admission_attribution_requires_explicit_admitter() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)

    with pytest.raises(
        ValidationError,
        match="without an explicit successor-resolution admitter",
    ):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (continuation,),
            admission_attribution=_admission("ghost"),
        )


def test_admitter_requires_explicit_resolution_attribution() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)

    with pytest.raises(
        ValidationError,
        match="requires explicit ResolutionAttribution",
    ):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (_continuation(predecessor),),
            admitter=_resolved_admitter,
        )


@pytest.mark.parametrize(
    ("admitter", "expected_type"),
    [
        (_resolved_admitter, ResolvedIntent),
        (_clarification_admitter, ClarificationNeed),
        (_information_admitter, InformationNeed),
    ],
)
def test_explicit_admitter_creates_exact_successor_lineage(
    admitter,
    expected_type,
) -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)
    candidate = _successor_candidate(predecessor, context, continuation)
    attribution = _admission(expected_type.__name__)

    frontier = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        candidate_inputs=(candidate,),
        admitter=admitter,
        admission_attribution=attribution,
    )

    assert frontier.kind is SuccessorResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert type(frontier.resolution_output) is expected_type
    assert frontier.successor_lineage is not None
    assert frontier.successor_lineage.predecessor == predecessor
    assert frontier.successor_lineage.continuation_inputs == (continuation,)
    assert frontier.resolution_output is frontier.successor_lineage.successor
    assert frontier.resolution_output.context_envelope_identity == context.identity
    assert frontier.resolution_output.admission_attribution == attribution
    assert frontier.resolution_output.candidate_inputs == (candidate.candidate,)


def test_deterministic_successor_admission_needs_no_provider_candidate() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)

    frontier = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        admitter=_resolved_admitter,
        admission_attribution=_admission("deterministic"),
    )

    assert frontier.kind is SuccessorResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    assert isinstance(frontier.resolution_output, ResolvedIntent)
    assert frontier.resolution_output.candidate_inputs == ()


def test_admitter_cannot_replace_attribution_context_or_candidate_provenance() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)
    first = _successor_candidate(
        predecessor,
        context,
        continuation,
        provider="provider-a",
        invocation="a",
    )
    second = _successor_candidate(
        predecessor,
        context,
        continuation,
        provider="provider-b",
        invocation="b",
    )

    def wrong_attribution(
        predecessor: ResolvedIntent,
        context: ContextEnvelope,
        inputs: tuple[ContinuationInput, ...],
        candidates: tuple[SuccessorCandidateResolution, ...],
        attribution: ResolutionAttribution,
    ) -> ResolvedIntent:
        return ResolvedIntent(
            predecessor.intent_request_identity,
            context.identity,
            _admission("wrong"),
            "Wrong attribution.",
            candidate_inputs=_nested(candidates),
        )

    with pytest.raises(ValidationError, match="exact supplied ResolutionAttribution"):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (continuation,),
            candidate_inputs=(first, second),
            admitter=wrong_attribution,
            admission_attribution=_admission("expected"),
        )

    foreign_context = _context(predecessor, label="another-context")

    def wrong_context(
        predecessor: ResolvedIntent,
        context: ContextEnvelope,
        inputs: tuple[ContinuationInput, ...],
        candidates: tuple[SuccessorCandidateResolution, ...],
        attribution: ResolutionAttribution,
    ) -> ResolvedIntent:
        return ResolvedIntent(
            predecessor.intent_request_identity,
            foreign_context.identity,
            attribution,
            "Wrong context.",
            candidate_inputs=_nested(candidates),
        )

    with pytest.raises(ValidationError, match="exact ContextEnvelope"):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (continuation,),
            candidate_inputs=(first, second),
            admitter=wrong_context,
            admission_attribution=_admission("context"),
        )

    def erase_candidate(
        predecessor: ResolvedIntent,
        context: ContextEnvelope,
        inputs: tuple[ContinuationInput, ...],
        candidates: tuple[SuccessorCandidateResolution, ...],
        attribution: ResolutionAttribution,
    ) -> ResolvedIntent:
        return ResolvedIntent(
            predecessor.intent_request_identity,
            context.identity,
            attribution,
            "Erased provenance.",
            candidate_inputs=(candidates[0].candidate,),
        )

    with pytest.raises(ValidationError, match="complete exact supplied candidate"):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (continuation,),
            candidate_inputs=(first, second),
            admitter=erase_candidate,
            admission_attribution=_admission("erase"),
        )


def test_lineage_occurrence_collision_fails_closed() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)

    collision = ResolutionAttribution(
        _ref("irr.resolver", "m4-successor-admitter"),
        continuation.attribution.reentry_event_ref,
    )

    with pytest.raises(ValidationError, match="re-entry occurrence"):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (continuation,),
            admitter=_resolved_admitter,
            admission_attribution=collision,
        )


def test_existing_exact_lineage_replays_without_new_admission() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)
    candidate = _successor_candidate(predecessor, context, continuation)

    admitted = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        candidate_inputs=(candidate,),
        admitter=_resolved_admitter,
        admission_attribution=_admission("historical"),
    )
    assert admitted.successor_lineage is not None

    replayed = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        candidate_inputs=(candidate,),
        admitted_lineages=(admitted.successor_lineage,),
    )

    assert replayed == admitted


def test_existing_lineage_rejects_missing_provenance_and_fresh_admitter() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)
    candidate = _successor_candidate(predecessor, context, continuation)

    admitted = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        candidate_inputs=(candidate,),
        admitter=_resolved_admitter,
        admission_attribution=_admission("historical"),
    )
    assert admitted.successor_lineage is not None

    with pytest.raises(ValidationError, match="candidate provenance"):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (continuation,),
            admitted_lineages=(admitted.successor_lineage,),
        )

    with pytest.raises(ValidationError, match="cannot be combined"):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (continuation,),
            candidate_inputs=(candidate,),
            admitted_lineages=(admitted.successor_lineage,),
            admitter=_resolved_admitter,
            admission_attribution=_admission("new"),
        )


def test_competing_admitted_lineages_fail_closed_without_precedence() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)

    first = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        admitter=_resolved_admitter,
        admission_attribution=_admission("first"),
    ).successor_lineage
    second = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        admitter=_resolved_admitter,
        admission_attribution=_admission("second"),
    ).successor_lineage
    assert first is not None
    assert second is not None
    assert first.identity != second.identity

    with pytest.raises(ValidationError, match="competing admitted lineages"):
        orchestrate_successor_resolution(
            predecessor,
            context,
            (continuation,),
            admitted_lineages=(first, second),
        )


def test_admitter_may_abstain_without_mutating_frontier() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    continuation = _continuation(predecessor)
    candidate = _successor_candidate(predecessor, context, continuation)

    def abstain(
        predecessor: ResolvedIntent,
        context: ContextEnvelope,
        inputs: tuple[ContinuationInput, ...],
        candidates: tuple[SuccessorCandidateResolution, ...],
        attribution: ResolutionAttribution,
    ) -> None:
        return None

    frontier = orchestrate_successor_resolution(
        predecessor,
        context,
        (continuation,),
        candidate_inputs=(candidate,),
        admitter=abstain,
        admission_attribution=_admission("abstain"),
    )

    assert frontier.kind is SuccessorResolutionFrontierKind.ADMISSION_REQUIRED
    assert frontier.resolution_output is None


def test_frontier_is_noncanonical_and_surface_has_no_execution_authority() -> None:
    predecessor = _predecessor()
    context = _context(predecessor)
    frontier = orchestrate_successor_resolution(
        predecessor,
        context,
        (_continuation(predecessor),),
    )

    assert not hasattr(frontier, "canonical_bytes")
    assert not hasattr(frontier, "identity")

    parameters = signature(orchestrate_successor_resolution).parameters
    for forbidden in (
        "governance",
        "authorization",
        "executor",
        "worker",
        "retry",
        "fallback",
        "work_plan",
        "parent_complete",
    ):
        assert forbidden not in parameters
        assert not hasattr(frontier, forbidden)
