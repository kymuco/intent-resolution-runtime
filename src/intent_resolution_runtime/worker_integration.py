from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .delegation import DelegatedWorkHandoff
from .errors import IntentIRError, ValidationError
from .history import (
    AdmittedHistoryRepository,
    HistoryPersistResult,
    HistoryRecord,
)
from .worker_result import WorkerResult


class WorkerIntegrationError(IntentIRError):
    """Raised when a Worker violates the frozen M3.5 integration boundary."""


class WorkerReplayBlockedError(WorkerIntegrationError):
    """Raised when an already-recorded handoff would otherwise be dispatched again."""


@dataclass(frozen=True, slots=True)
class WorkerHandoffRequest:
    """Explicit mechanism state for one exact Worker handoff occurrence.

    The embedded DelegatedWorkHandoff is canonical semantic history. This request is not
    a second semantic record and grants no scope, capability, disclosure, or authority.
    M3.5 commits the exact handoff before crossing the external Worker boundary.
    """

    handoff: DelegatedWorkHandoff

    def __post_init__(self) -> None:
        if type(self.handoff) is not DelegatedWorkHandoff:
            raise ValidationError(
                "WorkerHandoffRequest.handoff must be a DelegatedWorkHandoff"
            )


@runtime_checkable
class WorkerPort(Protocol):
    """Narrow external bounded Worker surface.

    The port receives one exact already-committed handoff and returns one exact
    WorkerResult. It has no parent-lifecycle, scope-widening, capability-selection,
    Governance, retry, fallback, history-mutation, or continuation authority through
    this protocol.
    """

    def perform(self, request: WorkerHandoffRequest) -> WorkerResult: ...


def build_worker_handoff_request(
    handoff: DelegatedWorkHandoff,
) -> WorkerHandoffRequest:
    """Construct one Worker request around an exact DelegatedWorkHandoff."""

    return WorkerHandoffRequest(handoff=handoff)


def _validate_request_source(
    request: WorkerHandoffRequest,
    *,
    handoff: DelegatedWorkHandoff,
) -> None:
    if type(handoff) is not DelegatedWorkHandoff:
        raise ValidationError("handoff must be a DelegatedWorkHandoff")
    if request.handoff != handoff:
        raise ValidationError(
            "Worker request must preserve the exact source DelegatedWorkHandoff"
        )


def invoke_worker(
    worker: WorkerPort,
    repository: AdmittedHistoryRepository,
    request: WorkerHandoffRequest,
    *,
    handoff: DelegatedWorkHandoff,
) -> WorkerResult:
    """Commit one fresh handoff, dispatch once, and validate returned WorkerResult.

    The handoff is persisted before crossing the external Worker boundary. If the exact
    handoff is already present, M3.5 fails closed instead of replaying the dispatch.
    Worker/transport exceptions propagate while the committed handoff remains available
    for later result reconciliation or explicit recovery.
    """

    if not isinstance(worker, WorkerPort):
        raise ValidationError("worker must satisfy WorkerPort")
    if not isinstance(repository, AdmittedHistoryRepository):
        raise ValidationError("repository must satisfy AdmittedHistoryRepository")
    if type(request) is not WorkerHandoffRequest:
        raise ValidationError("request must be a WorkerHandoffRequest")

    _validate_request_source(request, handoff=handoff)

    history_record = HistoryRecord.from_canonical_bytes(handoff.canonical_bytes())
    persist_result = repository.persist(history_record)
    if persist_result is HistoryPersistResult.ALREADY_PRESENT:
        raise WorkerReplayBlockedError(
            "exact DelegatedWorkHandoff is already persisted; automatic redispatch is forbidden"
        )
    if persist_result is not HistoryPersistResult.INSERTED:
        raise WorkerIntegrationError(
            "history repository returned an unsupported persistence result"
        )

    result = worker.perform(request)
    if type(result) is not WorkerResult:
        raise WorkerIntegrationError("Worker must return an exact WorkerResult")
    if result.handoff != handoff:
        raise WorkerIntegrationError(
            "WorkerResult belongs to a foreign DelegatedWorkHandoff"
        )
    return result


__all__ = (
    "WorkerHandoffRequest",
    "WorkerIntegrationError",
    "WorkerPort",
    "WorkerReplayBlockedError",
    "build_worker_handoff_request",
    "invoke_worker",
)
