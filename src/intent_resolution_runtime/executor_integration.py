from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .attempt import CapabilityAttempt
from .capability import CapabilityExecutionBoundaryKind
from .errors import IntentIRError, ValidationError
from .history import (
    AdmittedHistoryRepository,
    HistoryPersistResult,
    HistoryRecord,
)
from .outcome import CapabilityOutcome


class ExecutorIntegrationError(IntentIRError):
    """Raised when an Executor violates the frozen M3.4 invocation boundary."""


class ExecutorReplayBlockedError(ExecutorIntegrationError):
    """Raised when an already-recorded Attempt would otherwise be invoked again."""


@dataclass(frozen=True, slots=True)
class CapabilityInvocationRequest:
    """Explicit mechanism state for one exact capability invocation occurrence.

    The embedded CapabilityAttempt is canonical semantic history. This request is not a
    second semantic record and grants no authority. M3.4 commits the exact Attempt to
    admitted history before crossing the external Executor boundary.
    """

    attempt: CapabilityAttempt

    def __post_init__(self) -> None:
        if type(self.attempt) is not CapabilityAttempt:
            raise ValidationError(
                "CapabilityInvocationRequest.attempt must be a CapabilityAttempt"
            )


@runtime_checkable
class ExecutorPort(Protocol):
    """Narrow external capability invocation surface.

    The port receives one exact already-committed Attempt and returns one exact
    CapabilityOutcome. It has no capability-selection, Governance, retry, fallback,
    history-mutation, or continuation authority through this protocol.
    """

    def invoke(self, request: CapabilityInvocationRequest) -> CapabilityOutcome: ...


def build_capability_invocation_request(
    attempt: CapabilityAttempt,
) -> CapabilityInvocationRequest:
    """Construct one invocation request around an exact CapabilityAttempt."""

    return CapabilityInvocationRequest(attempt=attempt)


def _validate_request_source(
    request: CapabilityInvocationRequest,
    *,
    attempt: CapabilityAttempt,
) -> None:
    if type(attempt) is not CapabilityAttempt:
        raise ValidationError("attempt must be a CapabilityAttempt")
    if request.attempt != attempt:
        raise ValidationError(
            "Capability invocation request must preserve the exact source CapabilityAttempt"
        )


def _validate_executor_route(attempt: CapabilityAttempt) -> None:
    match = attempt.capability_match
    descriptors = {
        descriptor.capability_ref: descriptor
        for descriptor in match.catalog_snapshot.descriptors
    }
    descriptor = descriptors[match.capability_ref]
    executor_boundaries = tuple(
        boundary
        for boundary in descriptor.execution_boundaries
        if boundary.kind is CapabilityExecutionBoundaryKind.EXECUTOR
    )

    if len(executor_boundaries) > 1:
        raise ExecutorIntegrationError(
            "M3.4 does not select among multiple explicit Executor boundaries"
        )
    if (
        executor_boundaries
        and attempt.attribution.executor_ref != executor_boundaries[0].boundary_ref
    ):
        raise ExecutorIntegrationError(
            "CapabilityAttempt executor_ref does not match the exact admitted Executor boundary"
        )


def invoke_executor(
    executor: ExecutorPort,
    repository: AdmittedHistoryRepository,
    request: CapabilityInvocationRequest,
    *,
    attempt: CapabilityAttempt,
) -> CapabilityOutcome:
    """Commit one fresh Attempt, invoke once, and validate the returned Outcome.

    The Attempt is persisted before crossing the external effect boundary. If the exact
    Attempt is already present, M3.4 fails closed instead of replaying the invocation.
    Executor/transport exceptions propagate while the committed Attempt remains available
    for later Outcome reconciliation or explicit recovery.
    """

    if not isinstance(executor, ExecutorPort):
        raise ValidationError("executor must satisfy ExecutorPort")
    if not isinstance(repository, AdmittedHistoryRepository):
        raise ValidationError("repository must satisfy AdmittedHistoryRepository")
    if type(request) is not CapabilityInvocationRequest:
        raise ValidationError("request must be a CapabilityInvocationRequest")

    _validate_request_source(request, attempt=attempt)
    _validate_executor_route(attempt)

    history_record = HistoryRecord.from_canonical_bytes(attempt.canonical_bytes())
    persist_result = repository.persist(history_record)
    if persist_result is HistoryPersistResult.ALREADY_PRESENT:
        raise ExecutorReplayBlockedError(
            "exact CapabilityAttempt is already persisted; automatic reinvocation is forbidden"
        )
    if persist_result is not HistoryPersistResult.INSERTED:
        raise ExecutorIntegrationError(
            "history repository returned an unsupported persistence result"
        )

    outcome = executor.invoke(request)
    if type(outcome) is not CapabilityOutcome:
        raise ExecutorIntegrationError(
            "Executor must return an exact CapabilityOutcome"
        )
    if outcome.attempt != attempt:
        raise ExecutorIntegrationError(
            "CapabilityOutcome belongs to a foreign CapabilityAttempt"
        )
    return outcome


__all__ = (
    "CapabilityInvocationRequest",
    "ExecutorIntegrationError",
    "ExecutorPort",
    "ExecutorReplayBlockedError",
    "build_capability_invocation_request",
    "invoke_executor",
)
