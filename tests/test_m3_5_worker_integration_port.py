from __future__ import annotations

import inspect
from dataclasses import replace

import pytest

from intent_resolution_runtime import (
    DelegatedCapabilityAllowance,
    DelegatedScope,
    DelegatedWork,
    DelegatedWorkHandoff,
    DelegationHandoffAttribution,
    ExpectedDeliverable,
    InMemoryAdmittedHistoryRepository,
    RecordIdentity,
    StableRef,
    ValidationError,
    WorkerHandoffRequest,
    WorkerIntegrationError,
    WorkerNeed,
    WorkerNeedKind,
    WorkerPort,
    WorkerReplayBlockedError,
    WorkerResult,
    WorkerResultAttribution,
    WorkerResultMaterial,
    WorkerResultMaterialRole,
    build_worker_handoff_request,
    invoke_worker,
)

RESOLVED = RecordIdentity("sha256", "1" * 64)
WORK_PLAN = RecordIdentity("sha256", "2" * 64)
CAPABILITY_CONTRACT = RecordIdentity("sha256", "3" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _delegated_work() -> DelegatedWork:
    scope = DelegatedScope(
        scope_ref=_ref("irr.delegated_scope", "project"),
        semantic_type="workspace.surface",
        value="workspace:project",
        description="Exact delegated project scope.",
    )
    deliverable = ExpectedDeliverable(
        deliverable_ref=_ref("irr.expected_deliverable", "report"),
        semantic_type="artifact.report",
        scope_ref=scope.scope_ref,
        description="Inspectable bounded analysis report.",
    )
    return DelegatedWork(
        resolved_intent_identity=RESOLVED,
        delegation_ref=_ref("irr.delegated_work", "analysis-001"),
        parent_work_plan_identity_refs=(WORK_PLAN,),
        objective="Analyze the admitted project material and return the bounded report.",
        scopes=(scope,),
        context_surface=(),
        allowed_capabilities=(
            DelegatedCapabilityAllowance(
                allowance_ref=_ref("irr.delegated_capability_allowance", "read"),
                capability_ref=_ref("irr.capability", "artifact.read"),
                capability_contract_identity=CAPABILITY_CONTRACT,
                scope_refs=(scope.scope_ref,),
                description="Exact admitted read-only capability ceiling.",
            ),
        ),
        constraints=(),
        expected_deliverables=(deliverable,),
        completion_contract="Return the exact expected report or an explicit WorkerNeed.",
        description="Bounded M3.5 Worker delegation.",
    )


def _handoff(
    *,
    worker: str = "analysis-worker-v1",
    event: str = "handoff-m3-5",
) -> DelegatedWorkHandoff:
    return DelegatedWorkHandoff(
        attribution=DelegationHandoffAttribution(
            dispatcher_ref=_ref("irr.dispatcher", "host-worker-boundary"),
            worker_ref=_ref("irr.worker", worker),
            handoff_event_ref=_ref("irr.event", event),
        ),
        delegated_work=_delegated_work(),
    )


def _need_result(
    handoff: DelegatedWorkHandoff,
    *,
    event: str = "result-m3-5",
    kind: WorkerNeedKind = WorkerNeedKind.INFORMATION,
) -> WorkerResult:
    need = WorkerNeed(
        need_ref=_ref("irr.worker_need", event),
        kind=kind,
        related_scope_refs=(),
        statement="Additional explicitly admitted material is required.",
    )
    return WorkerResult(
        attribution=WorkerResultAttribution(
            worker_ref=handoff.attribution.worker_ref,
            result_event_ref=_ref("irr.event", event),
        ),
        handoff=handoff,
        materials=(),
        needs=(need,),
        description="Attributable bounded Worker result.",
    )


def _completion_claim_result(
    handoff: DelegatedWorkHandoff,
    *,
    event: str = "completion-claim-m3-5",
) -> WorkerResult:
    scope_ref = handoff.delegated_work.scopes[0].scope_ref
    material = WorkerResultMaterial(
        material_ref=_ref("irr.worker_result_material", event),
        role=WorkerResultMaterialRole.COMPLETION_CLAIM,
        semantic_type="worker.completion_claim",
        scope_refs=(scope_ref,),
        expected_deliverable_refs=(),
        source_refs=(),
        source_identity_refs=(),
        content="done",
        description="Worker-local completion assertion only.",
    )
    return WorkerResult(
        attribution=WorkerResultAttribution(
            worker_ref=handoff.attribution.worker_ref,
            result_event_ref=_ref("irr.event", event),
        ),
        handoff=handoff,
        materials=(material,),
        needs=(),
        description="Worker completion-claim result.",
    )


class RecordingWorker:
    def __init__(self) -> None:
        self.requests: list[WorkerHandoffRequest] = []

    def perform(self, request: WorkerHandoffRequest) -> WorkerResult:
        self.requests.append(request)
        return _need_result(request.handoff)


class PersistCheckingWorker:
    def __init__(self, repository: InMemoryAdmittedHistoryRepository) -> None:
        self.repository = repository
        self.calls = 0

    def perform(self, request: WorkerHandoffRequest) -> WorkerResult:
        self.calls += 1
        assert self.repository.get(request.handoff.identity) is not None
        return _need_result(request.handoff)


class FailingWorker:
    def __init__(self) -> None:
        self.calls = 0

    def perform(self, request: WorkerHandoffRequest) -> WorkerResult:
        self.calls += 1
        raise RuntimeError("worker transport lost after dispatch")


class WrongTypeWorker:
    def perform(self, request: WorkerHandoffRequest) -> WorkerResult:
        return object()  # type: ignore[return-value]


class ForeignResultWorker:
    def __init__(self, foreign_handoff: DelegatedWorkHandoff) -> None:
        self.foreign_handoff = foreign_handoff
        self.calls = 0

    def perform(self, request: WorkerHandoffRequest) -> WorkerResult:
        self.calls += 1
        return _need_result(self.foreign_handoff, event="foreign-result-m3-5")


def test_build_worker_handoff_request_preserves_exact_handoff() -> None:
    handoff = _handoff()
    request = build_worker_handoff_request(handoff)

    assert request.handoff == handoff
    assert request.handoff.identity == handoff.identity
    assert set(WorkerHandoffRequest.__dataclass_fields__) == {"handoff"}


def test_fresh_handoff_is_persisted_before_worker_and_result_is_not_auto_persisted() -> (
    None
):
    handoff = _handoff()
    request = build_worker_handoff_request(handoff)
    repository = InMemoryAdmittedHistoryRepository()
    worker = PersistCheckingWorker(repository)

    result = invoke_worker(worker, repository, request, handoff=handoff)

    assert worker.calls == 1
    persisted = repository.get(handoff.identity)
    assert persisted is not None
    assert persisted.canonical_record_bytes == handoff.canonical_bytes()
    assert result.handoff == handoff
    assert repository.get(result.identity) is None


def test_forged_request_handoff_fails_before_persistence_or_worker_call() -> None:
    handoff = _handoff(event="source-handoff")
    foreign = _handoff(event="foreign-handoff")
    request = WorkerHandoffRequest(handoff=foreign)
    repository = InMemoryAdmittedHistoryRepository()
    worker = RecordingWorker()

    with pytest.raises(ValidationError, match="exact source DelegatedWorkHandoff"):
        invoke_worker(worker, repository, request, handoff=handoff)

    assert worker.requests == []
    assert repository.get(handoff.identity) is None
    assert repository.get(foreign.identity) is None


def test_existing_exact_handoff_blocks_automatic_redispatch() -> None:
    handoff = _handoff()
    request = build_worker_handoff_request(handoff)
    repository = InMemoryAdmittedHistoryRepository()
    first_worker = RecordingWorker()

    invoke_worker(first_worker, repository, request, handoff=handoff)
    assert len(first_worker.requests) == 1

    second_worker = RecordingWorker()
    with pytest.raises(WorkerReplayBlockedError, match="automatic redispatch"):
        invoke_worker(second_worker, repository, request, handoff=handoff)

    assert second_worker.requests == []


def test_transport_failure_leaves_handoff_durable_and_same_handoff_cannot_retry() -> (
    None
):
    handoff = _handoff(event="failure-handoff")
    request = build_worker_handoff_request(handoff)
    repository = InMemoryAdmittedHistoryRepository()
    failing_worker = FailingWorker()

    with pytest.raises(RuntimeError, match="transport lost"):
        invoke_worker(failing_worker, repository, request, handoff=handoff)

    assert failing_worker.calls == 1
    assert repository.get(handoff.identity) is not None

    replacement_worker = RecordingWorker()
    with pytest.raises(WorkerReplayBlockedError, match="automatic redispatch"):
        invoke_worker(replacement_worker, repository, request, handoff=handoff)
    assert replacement_worker.requests == []


def test_new_handoff_occurrence_is_distinct_and_may_be_dispatched() -> None:
    first = _handoff(event="handoff-1")
    second = _handoff(event="handoff-2")
    assert first.delegated_work == second.delegated_work
    assert first.identity != second.identity

    repository = InMemoryAdmittedHistoryRepository()
    worker = RecordingWorker()

    invoke_worker(
        worker,
        repository,
        build_worker_handoff_request(first),
        handoff=first,
    )
    invoke_worker(
        worker,
        repository,
        build_worker_handoff_request(second),
        handoff=second,
    )

    assert len(worker.requests) == 2
    assert repository.get(first.identity) is not None
    assert repository.get(second.identity) is not None


def test_worker_must_return_exact_worker_result() -> None:
    handoff = _handoff(event="wrong-type-handoff")
    repository = InMemoryAdmittedHistoryRepository()

    with pytest.raises(WorkerIntegrationError, match="exact WorkerResult"):
        invoke_worker(
            WrongTypeWorker(),
            repository,
            build_worker_handoff_request(handoff),
            handoff=handoff,
        )

    assert repository.get(handoff.identity) is not None


def test_foreign_worker_result_handoff_fails_closed_after_dispatch_commit() -> None:
    handoff = _handoff(event="expected-handoff")
    foreign = _handoff(worker="other-worker", event="foreign-handoff")
    repository = InMemoryAdmittedHistoryRepository()
    worker = ForeignResultWorker(foreign)

    with pytest.raises(WorkerIntegrationError, match="foreign DelegatedWorkHandoff"):
        invoke_worker(
            worker,
            repository,
            build_worker_handoff_request(handoff),
            handoff=handoff,
        )

    assert worker.calls == 1
    assert repository.get(handoff.identity) is not None
    assert repository.get(foreign.identity) is None


def test_worker_need_returns_as_data_without_widening_delegation() -> None:
    handoff = _handoff(event="scope-need-handoff")
    original_delegated = handoff.delegated_work

    class ScopeNeedWorker:
        def perform(self, request: WorkerHandoffRequest) -> WorkerResult:
            return _need_result(
                request.handoff,
                event="scope-need-result",
                kind=WorkerNeedKind.SCOPE,
            )

    result = invoke_worker(
        ScopeNeedWorker(),
        InMemoryAdmittedHistoryRepository(),
        build_worker_handoff_request(handoff),
        handoff=handoff,
    )

    assert result.needs[0].kind is WorkerNeedKind.SCOPE
    assert result.needs[0].related_scope_refs == ()
    assert result.handoff.delegated_work == original_delegated
    assert result.handoff.delegated_work.scopes == original_delegated.scopes


def test_completion_claim_remains_worker_material_not_parent_completion() -> None:
    handoff = _handoff(event="claim-handoff")

    class CompletionClaimWorker:
        def perform(self, request: WorkerHandoffRequest) -> WorkerResult:
            return _completion_claim_result(request.handoff)

    result = invoke_worker(
        CompletionClaimWorker(),
        InMemoryAdmittedHistoryRepository(),
        build_worker_handoff_request(handoff),
        handoff=handoff,
    )

    assert result.materials[0].role is WorkerResultMaterialRole.COMPLETION_CLAIM
    assert "parent_completed" not in WorkerResult.__dataclass_fields__
    assert "delegated_complete" not in WorkerResult.__dataclass_fields__


def test_request_and_port_expose_no_ambient_authority_or_retry_surface() -> None:
    assert set(WorkerHandoffRequest.__dataclass_fields__) == {"handoff"}
    signature = inspect.signature(WorkerPort.perform)
    assert tuple(signature.parameters) == ("self", "request")

    for forbidden in (
        "retry",
        "fallback",
        "authorize",
        "govern",
        "widen_scope",
        "grant_capability",
        "retrieve",
        "search",
        "persist",
        "complete_parent",
        "delegate_worker",
    ):
        assert not hasattr(WorkerPort, forbidden)


def test_request_is_immutable_mechanism_state() -> None:
    request = build_worker_handoff_request(_handoff())
    with pytest.raises(Exception):
        replace(request, handoff=object())  # type: ignore[arg-type]
