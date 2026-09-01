from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    CapabilityAttempt,
    CapabilityAttemptAttribution,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffect,
    CapabilityEffectMatch,
    CapabilityEffectRequirement,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityOutcome,
    CapabilityOutcomeAttribution,
    CapabilityRequestedEffect,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    ContextEnvelope,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    EvidenceRelation,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    OutcomeCompletionAssessment,
    OutcomeCompletionState,
    OutcomeEffectAssessment,
    OutcomeEffectCertainty,
    OutcomeEvidence,
    OutcomeEvidenceRole,
    OutcomeLifecycleAssessment,
    OutcomeLifecycleState,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    SuccessorResolutionKind,
    SuccessorResolutionLineage,
    ValidationError,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
)
from intent_resolution_runtime.attempt_outcome_continuation import (
    AttemptOutcomeContinuationFrontier,
    orchestrate_attempt_outcome_continuation,
)


SOURCE_IDENTITY = RecordIdentity("sha256", "8" * 64)
TEMPORAL_IDENTITY = RecordIdentity("sha256", "9" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _predecessor(label: str = "main") -> ResolvedIntent:
    request = IntentRequest(
        origin=OriginAttribution(
            OriginKind.HUMAN,
            _ref("human", "user"),
            _ref("host.event", f"request-{label}"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression("Publish the bounded artifact."),
    )
    context = ContextEnvelope(
        request.identity,
        SourceAttribution(
            _ref("host.source", "context"),
            _ref("host.event", f"context-{label}"),
        ),
        (),
    )
    return ResolvedIntent(
        request.identity,
        context.identity,
        ResolutionAttribution(
            _ref("irr.resolver", "m2.4-test"),
            _ref("irr.resolution_event", f"predecessor-{label}"),
        ),
        "Publish exactly one bounded artifact using already admitted semantics.",
    )


def _evaluation(predecessor: ResolvedIntent, label: str = "main") -> CapabilityMatchEvaluation:
    plan_ref = _ref("irr.work_plan", f"publish-{label}")
    step_ref = _ref("irr.work_step", "publish")
    completion = "Confirm the bounded artifact publication for the requested target."
    step = WorkStep(
        predecessor.identity,
        plan_ref,
        step_ref,
        "artifact.publish",
        "workspace:artifact/report.txt",
        (),
        (),
        (),
        WorkContinuationMode.NONE,
        completion,
        "Publish one bounded artifact.",
    )
    plan = WorkPlan(
        predecessor.identity,
        plan_ref,
        (step,),
        "Complete the bounded artifact publication plan.",
        "Publication plan.",
    )
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", f"artifact-{label}"),
        "artifact.path_scope",
        "workspace:artifact/report.txt",
        "Exact artifact target.",
    )
    requested_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", f"publish-{label}"),
        "external.publish",
        (requested_scope.scope_ref,),
        "Publish the bounded artifact to the admitted target.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        requested_scope.scope_ref,
        (requested_scope,),
        (requested_effect,),
        (),
        "Exact effectful publication capability requirement.",
    )
    descriptor_scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", f"artifact-publish-{label}"),
        "artifact.path_scope",
        "Invocation must remain inside the exact artifact target.",
    )
    descriptor_effect = CapabilityEffect(
        _ref("irr.capability_effect", f"external-publish-{label}"),
        "external.publish",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (descriptor_scope.requirement_ref,),
        "Publishing necessarily creates the requested external effect.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", f"artifact.publish.{label}"),
        "artifact.publish",
        (),
        (),
        (descriptor_scope,),
        (descriptor_effect,),
        (),
        completion,
        "Bounded artifact publication capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", f"m2.4-{label}"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", f"catalog-{label}"),
        ),
        "Exact bounded M2.4 planning surface.",
        (descriptor,),
        "M2.4 Catalog snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "exact-v1"),
            _ref("irr.event", f"match-{label}"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityScopeMatch(
                requested_scope.scope_ref,
                descriptor_scope.requirement_ref,
            ),
        ),
        (),
        (),
        (
            CapabilityEffectMatch(
                requested_effect.effect_ref,
                descriptor_effect.effect_ref,
            ),
        ),
        "Exact effectful publication capability match.",
    )
    return CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", f"evaluation-{label}"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for M2.4.",
    )


def _attempt(
    predecessor: ResolvedIntent,
    label: str,
    *,
    evaluation: CapabilityMatchEvaluation | None = None,
) -> CapabilityAttempt:
    evaluation = _evaluation(predecessor) if evaluation is None else evaluation
    return CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", "artifact-local"),
            _ref("irr.event", f"attempt-{label}"),
        ),
        evaluation,
        evaluation.requirement.step_ref,
        (),
        (),
        f"Exact attributable publication attempt {label}.",
    )


def _evidence(
    label: str,
    roles: tuple[OutcomeEvidenceRole, ...],
    statement: str,
) -> OutcomeEvidence:
    return OutcomeEvidence(
        _ref("irr.outcome_evidence", label),
        SourceAttribution(
            _ref("executor.source", "artifact-local"),
            _ref("executor.event", f"evidence-{label}"),
        ),
        SOURCE_IDENTITY,
        EvidenceRelation.SUPPORTS,
        roles,
        (TEMPORAL_IDENTITY,),
        "artifact.publish attempt",
        statement,
    )


def _outcome(
    attempt: CapabilityAttempt,
    label: str,
    *,
    unknown: bool = False,
) -> CapabilityOutcome:
    effect_ref = attempt.capability_evaluation.requirement.requested_effects[0].effect_ref
    if unknown:
        evidence = _evidence(
            f"disconnect-{label}",
            (
                OutcomeEvidenceRole.LIFECYCLE,
                OutcomeEvidenceRole.UNCERTAINTY,
                OutcomeEvidenceRole.TRANSPORT,
            ),
            "Connection ended without enough evidence to establish completion or effect certainty.",
        )
        return CapabilityOutcome(
            CapabilityOutcomeAttribution(
                _ref("irr.outcome_evaluator", "bounded-v1"),
                _ref("irr.event", f"outcome-{label}"),
            ),
            attempt,
            (evidence,),
            OutcomeLifecycleAssessment(
                OutcomeLifecycleState.INTERRUPTED,
                (evidence.evidence_ref,),
                "The normal protocol was interrupted.",
            ),
            OutcomeCompletionAssessment(
                OutcomeCompletionState.UNKNOWN,
                (evidence.evidence_ref,),
                "Completion remains materially unknown.",
            ),
            (
                OutcomeEffectAssessment(
                    effect_ref,
                    OutcomeEffectCertainty.UNKNOWN,
                    (evidence.evidence_ref,),
                    "The requested effect remains materially unknown.",
                ),
            ),
            f"Interrupted materially unknown Outcome {label}.",
        )

    lifecycle = _evidence(
        f"lifecycle-{label}",
        (OutcomeEvidenceRole.LIFECYCLE,),
        "The normal protocol completed.",
    )
    receipt = _evidence(
        f"receipt-{label}",
        (OutcomeEvidenceRole.COMPLETION, OutcomeEvidenceRole.EFFECT),
        "The authoritative receipt confirms completion and the requested effect.",
    )
    return CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "bounded-v1"),
            _ref("irr.event", f"outcome-{label}"),
        ),
        attempt,
        (lifecycle, receipt),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
            (lifecycle.evidence_ref,),
            "The normal result protocol completed.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.SATISFIED,
            (receipt.evidence_ref,),
            "The WorkStep completion contract is satisfied for this Attempt.",
        ),
        (
            OutcomeEffectAssessment(
                effect_ref,
                OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                (receipt.evidence_ref,),
                "The requested publication effect is confirmed.",
            ),
        ),
        f"Confirmed bounded publication Outcome {label}.",
    )


def _continuation(outcome: CapabilityOutcome, label: str) -> ContinuationInput:
    return ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "m2.4-test"),
            _ref("irr.reentry_event", f"reentry-{label}"),
        ),
        ContinuationSourceKind.CAPABILITY_OUTCOME,
        outcome,
    )


def _successor(predecessor: ResolvedIntent, label: str) -> ResolvedIntent:
    return ResolvedIntent(
        predecessor.intent_request_identity,
        predecessor.context_envelope_identity,
        ResolutionAttribution(
            _ref("irr.resolver", "m2.4-successor"),
            _ref("irr.resolution_event", f"successor-{label}"),
        ),
        f"Successor semantics after exact continuation material {label}.",
    )


def _lineage(
    predecessor: ResolvedIntent,
    continuation: ContinuationInput,
    label: str,
) -> SuccessorResolutionLineage:
    successor = _successor(predecessor, label)
    return SuccessorResolutionLineage(
        predecessor,
        (continuation,),
        SuccessorResolutionKind.RESOLVED_INTENT,
        successor,
    )


def test_empty_frontier_is_exact_noncanonical_history_view() -> None:
    predecessor = _predecessor()
    frontier = orchestrate_attempt_outcome_continuation(predecessor)

    assert isinstance(frontier, AttemptOutcomeContinuationFrontier)
    assert frontier.predecessor is predecessor
    assert frontier.attempts == ()
    assert frontier.outcomes == ()
    assert frontier.continuation_sources == ()
    assert frontier.continuation_inputs == ()
    assert frontier.successor_lineage is None
    assert not hasattr(frontier, "canonical_bytes")
    assert not hasattr(frontier, "identity")


def test_attempt_must_descend_from_exact_predecessor() -> None:
    predecessor = _predecessor("active")
    foreign = _predecessor("foreign")
    attempt = _attempt(foreign, "foreign")

    with pytest.raises(ValidationError, match="exact predecessor ResolvedIntent"):
        orchestrate_attempt_outcome_continuation(predecessor, attempts=(attempt,))


def test_repeated_attempts_on_same_step_remain_distinct_history() -> None:
    predecessor = _predecessor()
    evaluation = _evaluation(predecessor)
    first = _attempt(predecessor, "first", evaluation=evaluation)
    second = _attempt(predecessor, "second", evaluation=evaluation)

    frontier = orchestrate_attempt_outcome_continuation(
        predecessor,
        attempts=(second, first),
    )

    assert set(frontier.attempts) == {first, second}
    assert set(frontier.outcome_pending_attempts) == {first, second}
    assert first.identity != second.identity
    assert not hasattr(frontier, "retry")
    assert not hasattr(frontier, "retry_candidate")


def test_outcome_requires_exact_supplied_attempt_history() -> None:
    predecessor = _predecessor()
    attempt = _attempt(predecessor, "one")
    outcome = _outcome(attempt, "one")

    with pytest.raises(ValidationError, match="orphaned from the exact supplied CapabilityAttempt"):
        orchestrate_attempt_outcome_continuation(predecessor, outcomes=(outcome,))


def test_competing_outcomes_for_one_attempt_fail_closed_without_latest_wins() -> None:
    predecessor = _predecessor()
    attempt = _attempt(predecessor, "one")
    success = _outcome(attempt, "success")
    unknown = _outcome(attempt, "unknown", unknown=True)

    with pytest.raises(ValidationError, match="competing active CapabilityOutcome"):
        orchestrate_attempt_outcome_continuation(
            predecessor,
            attempts=(attempt,),
            outcomes=(success, unknown),
        )


def test_outcome_does_not_automatically_become_continuation_source() -> None:
    predecessor = _predecessor()
    attempt = _attempt(predecessor, "one")
    outcome = _outcome(attempt, "one")

    frontier = orchestrate_attempt_outcome_continuation(
        predecessor,
        attempts=(attempt,),
        outcomes=(outcome,),
    )

    assert frontier.outcome_pending_attempts == ()
    assert frontier.outcomes_not_selected_for_continuation == (outcome,)
    assert frontier.continuation_sources == ()
    assert frontier.reentry_pending_sources == ()


def test_selected_outcome_source_without_host_reentry_is_pending_not_automatic_continuation() -> None:
    predecessor = _predecessor()
    attempt = _attempt(predecessor, "one")
    outcome = _outcome(attempt, "one", unknown=True)

    frontier = orchestrate_attempt_outcome_continuation(
        predecessor,
        attempts=(attempt,),
        outcomes=(outcome,),
        continuation_sources=(outcome,),
    )

    assert frontier.outcomes_not_selected_for_continuation == ()
    assert frontier.reentry_pending_sources == (outcome,)
    assert frontier.continuation_inputs == ()
    assert frontier.material_unknown_outcomes == (outcome,)
    assert frontier.interrupted_outcomes == (outcome,)
    assert not hasattr(frontier, "retry")


def test_continuation_input_must_descend_from_exact_selected_source() -> None:
    predecessor = _predecessor()
    attempt = _attempt(predecessor, "one")
    outcome = _outcome(attempt, "one", unknown=True)
    continuation = _continuation(outcome, "one")

    with pytest.raises(ValidationError, match="orphaned from the exact selected continuation source"):
        orchestrate_attempt_outcome_continuation(
            predecessor,
            attempts=(attempt,),
            outcomes=(outcome,),
            continuation_inputs=(continuation,),
        )


def test_repeated_host_reentry_of_same_source_is_history_not_semantic_amplification() -> None:
    predecessor = _predecessor()
    attempt = _attempt(predecessor, "one")
    outcome = _outcome(attempt, "one", unknown=True)
    first = _continuation(outcome, "first")
    second = _continuation(outcome, "second")

    frontier = orchestrate_attempt_outcome_continuation(
        predecessor,
        attempts=(attempt,),
        outcomes=(outcome,),
        continuation_sources=(outcome,),
        continuation_inputs=(second, first),
    )

    assert set(frontier.continuation_inputs) == {first, second}
    assert frontier.reentry_pending_sources == ()
    assert frontier.reentry_ambiguity_source_identities == (outcome.identity,)
    assert set(frontier.unconsumed_continuation_inputs) == {first, second}

    with pytest.raises(ValidationError, match="must not amplify one source"):
        SuccessorResolutionLineage(
            predecessor,
            (first, second),
            SuccessorResolutionKind.RESOLVED_INTENT,
            _successor(predecessor, "invalid-amplification"),
        )


def test_exact_successor_lineage_consumes_only_its_exact_reentry_occurrence() -> None:
    predecessor = _predecessor()
    attempt = _attempt(predecessor, "one")
    outcome = _outcome(attempt, "one", unknown=True)
    first = _continuation(outcome, "first")
    second = _continuation(outcome, "second")
    lineage = _lineage(predecessor, first, "one")

    frontier = orchestrate_attempt_outcome_continuation(
        predecessor,
        attempts=(attempt,),
        outcomes=(outcome,),
        continuation_sources=(outcome,),
        continuation_inputs=(first, second),
        successor_lineages=(lineage,),
    )

    assert frontier.successor_lineage is lineage
    assert frontier.unconsumed_continuation_inputs == (second,)
    assert frontier.reentry_ambiguity_source_identities == (outcome.identity,)


def test_successor_lineage_cannot_use_unsupplied_reentry_history() -> None:
    predecessor = _predecessor()
    attempt = _attempt(predecessor, "one")
    outcome = _outcome(attempt, "one", unknown=True)
    continuation = _continuation(outcome, "one")
    lineage = _lineage(predecessor, continuation, "one")

    with pytest.raises(ValidationError, match="outside the exact supplied re-entry history"):
        orchestrate_attempt_outcome_continuation(
            predecessor,
            attempts=(attempt,),
            outcomes=(outcome,),
            continuation_sources=(outcome,),
            successor_lineages=(lineage,),
        )


def test_competing_successor_lineages_fail_closed_without_branch_precedence() -> None:
    predecessor = _predecessor()
    attempt = _attempt(predecessor, "one")
    outcome = _outcome(attempt, "one", unknown=True)
    continuation = _continuation(outcome, "one")
    first = _lineage(predecessor, continuation, "first")
    second = _lineage(predecessor, continuation, "second")

    with pytest.raises(ValidationError, match="competing active SuccessorResolutionLineage"):
        orchestrate_attempt_outcome_continuation(
            predecessor,
            attempts=(attempt,),
            outcomes=(outcome,),
            continuation_sources=(outcome,),
            continuation_inputs=(continuation,),
            successor_lineages=(first, second),
        )


def test_input_order_does_not_create_attempt_outcome_or_reentry_precedence() -> None:
    predecessor = _predecessor()
    evaluation = _evaluation(predecessor)
    first_attempt = _attempt(predecessor, "first", evaluation=evaluation)
    second_attempt = _attempt(predecessor, "second", evaluation=evaluation)
    first_outcome = _outcome(first_attempt, "first", unknown=True)
    second_outcome = _outcome(second_attempt, "second")
    first_input = _continuation(first_outcome, "first")
    second_input = _continuation(second_outcome, "second")

    first = orchestrate_attempt_outcome_continuation(
        predecessor,
        attempts=(first_attempt, second_attempt),
        outcomes=(first_outcome, second_outcome),
        continuation_sources=(first_outcome, second_outcome),
        continuation_inputs=(first_input, second_input),
    )
    second = orchestrate_attempt_outcome_continuation(
        predecessor,
        attempts=(second_attempt, first_attempt),
        outcomes=(second_outcome, first_outcome),
        continuation_sources=(second_outcome, first_outcome),
        continuation_inputs=(second_input, first_input),
    )

    assert first == second
    assert first.material_unknown_outcomes == (first_outcome,)
    assert first.reentry_ambiguity_source_identities == ()
