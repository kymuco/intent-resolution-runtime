from __future__ import annotations

import inspect
from dataclasses import replace

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
    CapabilityExecutionBoundary,
    CapabilityExecutionBoundaryKind,
    CapabilityInvocationRequest,
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
    EvidenceRelation,
    ExecutorIntegrationError,
    ExecutorReplayBlockedError,
    InMemoryAdmittedHistoryRepository,
    OutcomeCompletionAssessment,
    OutcomeCompletionState,
    OutcomeEffectAssessment,
    OutcomeEffectCertainty,
    OutcomeEvidence,
    OutcomeEvidenceRole,
    OutcomeLifecycleAssessment,
    OutcomeLifecycleState,
    RecordIdentity,
    SourceAttribution,
    StableRef,
    ValidationError,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
    build_capability_invocation_request,
    invoke_executor,
)

RESOLVED = RecordIdentity("sha256", "a" * 64)
SOURCE_IDENTITY = RecordIdentity("sha256", "b" * 64)
TEMPORAL = RecordIdentity("sha256", "c" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _evaluation(
    executor_boundaries: tuple[CapabilityExecutionBoundary, ...] = (),
) -> CapabilityMatchEvaluation:
    plan_ref = _ref("irr.work_plan", "publish-m3-4")
    step_ref = _ref("irr.work_step", "publish")
    completion = "Confirm the bounded artifact publication for the requested target."
    step = WorkStep(
        RESOLVED,
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
        RESOLVED,
        plan_ref,
        (step,),
        "Complete the bounded artifact publication plan.",
        "M3.4 publication plan.",
    )
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "artifact"),
        "artifact.path_scope",
        "workspace:artifact/report.txt",
        "Exact artifact target.",
    )
    requested_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "publish"),
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
        "Exact M3.4 publication capability requirement.",
    )
    descriptor_scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "artifact-publish"),
        "artifact.path_scope",
        "Invocation must remain inside the exact artifact target.",
    )
    descriptor_effect = CapabilityEffect(
        _ref("irr.capability_effect", "external-publish"),
        "external.publish",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (descriptor_scope.requirement_ref,),
        "Publishing necessarily creates the requested external effect.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "artifact.publish.m3-4"),
        "artifact.publish",
        (),
        (),
        (descriptor_scope,),
        (descriptor_effect,),
        executor_boundaries,
        completion,
        "Bounded M3.4 artifact publication capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "m3-4"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", "catalog-m3-4"),
        ),
        "Exact bounded M3.4 planning surface.",
        (descriptor,),
        "M3.4 Catalog snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "exact-v1"),
            _ref("irr.event", "match-m3-4"),
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
        "Exact M3.4 capability match.",
    )
    return CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", "evaluation-m3-4"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for M3.4.",
    )


def _attempt(
    *,
    event: str = "attempt-m3-4",
    executor: str = "artifact-executor",
    executor_boundaries: tuple[CapabilityExecutionBoundary, ...] = (),
) -> CapabilityAttempt:
    evaluation = _evaluation(executor_boundaries)
    return CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", executor),
            _ref("irr.event", event),
        ),
        evaluation,
        evaluation.requirement.step_ref,
        (),
        (),
        "One exact M3.4 capability invocation Attempt.",
    )


def _outcome(attempt: CapabilityAttempt, *, event: str = "outcome-m3-4") -> CapabilityOutcome:
    lifecycle = OutcomeEvidence(
        _ref("irr.outcome_evidence", f"lifecycle-{event}"),
        SourceAttribution(
            _ref("executor.source", "artifact-executor"),
            _ref("executor.event", f"lifecycle-{event}"),
        ),
        SOURCE_IDENTITY,
        EvidenceRelation.SUPPORTS,
        (OutcomeEvidenceRole.LIFECYCLE,),
        (TEMPORAL,),
        "artifact.publish attempt",
        "The bounded executor result protocol completed normally.",
    )
    receipt = OutcomeEvidence(
        _ref("irr.outcome_evidence", f"receipt-{event}"),
        SourceAttribution(
            _ref("executor.source", "artifact-executor"),
            _ref("executor.event", f"receipt-{event}"),
        ),
        SOURCE_IDENTITY,
        EvidenceRelation.SUPPORTS,
        (OutcomeEvidenceRole.COMPLETION, OutcomeEvidenceRole.EFFECT),
        (TEMPORAL,),
        "artifact.publish attempt",
        "Attributable result evidence confirms the requested publication.",
    )
    effect_ref = attempt.capability_evaluation.requirement.requested_effects[0].effect_ref
    return CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "m3-4-test"),
            _ref("irr.event", event),
        ),
        attempt,
        (lifecycle, receipt),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
            (lifecycle.evidence_ref,),
            "The executor result protocol completed.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.SATISFIED,
            (receipt.evidence_ref,),
            "The exact WorkStep completion contract is satisfied.",
        ),
        (
            OutcomeEffectAssessment(
                effect_ref,
                OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                (receipt.evidence_ref,),
                "The requested publication effect is confirmed.",
            ),
        ),
        "Exact M3.4 capability Outcome.",
    )


class _Executor:
    def __init__(self, outcome: CapabilityOutcome) -> None:
        self.outcome = outcome
        self.calls = 0
        self.requests: list[CapabilityInvocationRequest] = []

    def invoke(self, request: CapabilityInvocationRequest) -> CapabilityOutcome:
        self.calls += 1
        self.requests.append(request)
        return self.outcome


class _FailingExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, request: CapabilityInvocationRequest) -> CapabilityOutcome:
        self.calls += 1
        raise RuntimeError("transport lost after dispatch")


class _WrongTypeExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, request: CapabilityInvocationRequest) -> CapabilityOutcome:
        self.calls += 1
        return object()  # type: ignore[return-value]


def _executor_boundary(value: str) -> CapabilityExecutionBoundary:
    return CapabilityExecutionBoundary(
        _ref("irr.executor", value),
        CapabilityExecutionBoundaryKind.EXECUTOR,
        "Exact executor boundary for the M3.4 test capability.",
    )


def test_fresh_attempt_is_committed_before_one_executor_invocation() -> None:
    boundary = _executor_boundary("artifact-executor")
    attempt = _attempt(executor_boundaries=(boundary,))
    outcome = _outcome(attempt)
    executor = _Executor(outcome)
    repository = InMemoryAdmittedHistoryRepository()
    request = build_capability_invocation_request(attempt)

    returned = invoke_executor(
        executor,
        repository,
        request,
        attempt=attempt,
    )

    assert returned == outcome
    assert executor.calls == 1
    assert executor.requests == [request]
    persisted = repository.get(attempt.identity)
    assert persisted is not None
    assert persisted.record_type == CapabilityAttempt.SCHEMA
    assert persisted.canonical_record_bytes == attempt.canonical_bytes()
    assert repository.get(outcome.identity) is None


def test_exact_attempt_replay_is_blocked_before_second_executor_call() -> None:
    attempt = _attempt()
    executor = _Executor(_outcome(attempt))
    repository = InMemoryAdmittedHistoryRepository()
    request = build_capability_invocation_request(attempt)

    invoke_executor(executor, repository, request, attempt=attempt)
    with pytest.raises(ExecutorReplayBlockedError):
        invoke_executor(executor, repository, request, attempt=attempt)

    assert executor.calls == 1


def test_transport_failure_leaves_attempt_durable_and_same_attempt_cannot_retry() -> None:
    attempt = _attempt()
    executor = _FailingExecutor()
    repository = InMemoryAdmittedHistoryRepository()
    request = build_capability_invocation_request(attempt)

    with pytest.raises(RuntimeError, match="transport lost after dispatch"):
        invoke_executor(executor, repository, request, attempt=attempt)

    assert repository.get(attempt.identity) is not None
    assert executor.calls == 1

    with pytest.raises(ExecutorReplayBlockedError):
        invoke_executor(executor, repository, request, attempt=attempt)
    assert executor.calls == 1


def test_new_retry_requires_a_distinct_attempt_occurrence() -> None:
    first = _attempt(event="attempt-first")
    second = _attempt(event="attempt-second")
    assert first.identity != second.identity

    repository = InMemoryAdmittedHistoryRepository()
    first_executor = _Executor(_outcome(first, event="outcome-first"))
    second_executor = _Executor(_outcome(second, event="outcome-second"))

    invoke_executor(
        first_executor,
        repository,
        build_capability_invocation_request(first),
        attempt=first,
    )
    invoke_executor(
        second_executor,
        repository,
        build_capability_invocation_request(second),
        attempt=second,
    )

    assert first_executor.calls == 1
    assert second_executor.calls == 1
    assert repository.get(first.identity) is not None
    assert repository.get(second.identity) is not None


def test_forged_request_source_is_rejected_before_persistence_or_executor() -> None:
    source = _attempt(event="attempt-source")
    foreign = _attempt(event="attempt-foreign")
    executor = _Executor(_outcome(source))
    repository = InMemoryAdmittedHistoryRepository()

    with pytest.raises(ValidationError, match="exact source CapabilityAttempt"):
        invoke_executor(
            executor,
            repository,
            CapabilityInvocationRequest(foreign),
            attempt=source,
        )

    assert executor.calls == 0
    assert repository.get(source.identity) is None
    assert repository.get(foreign.identity) is None


def test_explicit_executor_boundary_mismatch_fails_before_attempt_commit() -> None:
    attempt = _attempt(
        executor="substituted-executor",
        executor_boundaries=(_executor_boundary("admitted-executor"),),
    )
    executor = _Executor(_outcome(attempt))
    repository = InMemoryAdmittedHistoryRepository()

    with pytest.raises(ExecutorIntegrationError, match="exact admitted Executor boundary"):
        invoke_executor(
            executor,
            repository,
            build_capability_invocation_request(attempt),
            attempt=attempt,
        )

    assert executor.calls == 0
    assert repository.get(attempt.identity) is None


def test_multiple_explicit_executor_boundaries_are_not_selected_by_order() -> None:
    attempt = _attempt(
        executor="executor-a",
        executor_boundaries=(
            _executor_boundary("executor-a"),
            _executor_boundary("executor-b"),
        ),
    )
    executor = _Executor(_outcome(attempt))
    repository = InMemoryAdmittedHistoryRepository()

    with pytest.raises(ExecutorIntegrationError, match="does not select"):
        invoke_executor(
            executor,
            repository,
            build_capability_invocation_request(attempt),
            attempt=attempt,
        )

    assert executor.calls == 0
    assert repository.get(attempt.identity) is None


def test_absent_explicit_executor_boundary_does_not_invent_routing_semantics() -> None:
    service_boundary = CapabilityExecutionBoundary(
        _ref("irr.service", "artifact-service"),
        CapabilityExecutionBoundaryKind.SERVICE,
        "Material service boundary without an explicit executor identity.",
    )
    attempt = _attempt(
        executor="host-owned-executor",
        executor_boundaries=(service_boundary,),
    )
    executor = _Executor(_outcome(attempt))
    repository = InMemoryAdmittedHistoryRepository()

    returned = invoke_executor(
        executor,
        repository,
        build_capability_invocation_request(attempt),
        attempt=attempt,
    )

    assert returned.attempt == attempt
    assert executor.calls == 1


def test_foreign_outcome_is_rejected_after_exact_attempt_remains_committed() -> None:
    attempt = _attempt(event="attempt-source")
    foreign = _attempt(event="attempt-foreign")
    executor = _Executor(_outcome(foreign, event="outcome-foreign"))
    repository = InMemoryAdmittedHistoryRepository()

    with pytest.raises(ExecutorIntegrationError, match="foreign CapabilityAttempt"):
        invoke_executor(
            executor,
            repository,
            build_capability_invocation_request(attempt),
            attempt=attempt,
        )

    assert executor.calls == 1
    assert repository.get(attempt.identity) is not None


def test_wrong_executor_return_type_does_not_erase_committed_attempt() -> None:
    attempt = _attempt()
    executor = _WrongTypeExecutor()
    repository = InMemoryAdmittedHistoryRepository()

    with pytest.raises(ExecutorIntegrationError, match="exact CapabilityOutcome"):
        invoke_executor(
            executor,
            repository,
            build_capability_invocation_request(attempt),
            attempt=attempt,
        )

    assert executor.calls == 1
    assert repository.get(attempt.identity) is not None


def test_invocation_request_and_port_expose_no_retry_or_authority_decision_surface() -> None:
    assert set(CapabilityInvocationRequest.__dataclass_fields__) == {"attempt"}
    parameters = inspect.signature(invoke_executor).parameters
    for forbidden in (
        "retry",
        "fallback",
        "select_capability",
        "governance",
        "authorize",
        "continuation",
    ):
        assert forbidden not in parameters


def test_attempt_authorization_applicability_is_not_reclassified_by_m3_4() -> None:
    attempt = _attempt()
    assert attempt.presented_authorizations == ()

    executor = _Executor(_outcome(attempt))
    repository = InMemoryAdmittedHistoryRepository()
    returned = invoke_executor(
        executor,
        repository,
        build_capability_invocation_request(attempt),
        attempt=attempt,
    )

    assert returned.attempt.presented_authorizations == ()
    assert executor.calls == 1


def test_mechanism_request_is_not_a_canonical_ir_record() -> None:
    request = build_capability_invocation_request(_attempt())
    assert not hasattr(request, "SCHEMA")
    assert not hasattr(request, "identity")
    assert not hasattr(request, "canonical_bytes")


def test_request_is_immutable_mechanism_state() -> None:
    request = build_capability_invocation_request(_attempt())
    with pytest.raises(AttributeError):
        request.attempt = replace(  # type: ignore[misc]
            request.attempt,
            description="forged",
        )
