from __future__ import annotations

from inspect import signature

import pytest

from intent_resolution_runtime import (
    MAX_HISTORY_PAGE_SIZE,
    AdmittedHistoryRepository,
    ClaimRecord,
    HistoryIntegrityError,
    HistoryPersistResult,
    HistoryQuery,
    HistoryRecord,
    InMemoryAdmittedHistoryRepository,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    RecordIdentity,
    SourceAttribution,
    StableRef,
    ValidationError,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace=namespace, value=value)


def _request(label: str) -> IntentRequest:
    return IntentRequest(
        origin=OriginAttribution(
            kind=OriginKind.HUMAN,
            actor_ref=_ref("principal", "user"),
            source_event_ref=_ref("event", f"intent:{label}"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression(text=f"Inspect project {label}"),
    )


def _claim(label: str) -> ClaimRecord:
    return ClaimRecord(
        attribution=SourceAttribution(
            source_ref=_ref("source", "host"),
            source_event_ref=_ref("event", f"claim:{label}"),
        ),
        statement=f"Project claim {label}",
    )


def _history_record(record: IntentRequest | ClaimRecord) -> HistoryRecord:
    return HistoryRecord.from_canonical_bytes(record.canonical_bytes())


def _all_records(
    repository: InMemoryAdmittedHistoryRepository,
    *,
    limit: int = MAX_HISTORY_PAGE_SIZE,
) -> tuple[HistoryRecord, ...]:
    page = repository.read(HistoryQuery(limit=limit))
    assert page.next_after_identity is None
    return page.records


def test_exact_canonical_record_becomes_exact_history_record() -> None:
    request = _request("exact")

    history_record = HistoryRecord.from_canonical_bytes(request.canonical_bytes())

    assert history_record.identity == request.identity
    assert history_record.record_type == IntentRequest.SCHEMA
    assert history_record.canonical_record_bytes == request.canonical_bytes()


def test_history_record_rejects_noncanonical_bytes_even_when_json_is_valid() -> None:
    request = _request("noncanonical")
    noncanonical = request.canonical_bytes() + b"\n"

    with pytest.raises(HistoryIntegrityError, match="exact canonical form"):
        HistoryRecord.from_canonical_bytes(noncanonical)


def test_history_record_rejects_missing_top_level_schema() -> None:
    with pytest.raises(HistoryIntegrityError, match="top-level string schema"):
        HistoryRecord.from_canonical_bytes(b'{"value":"x"}')


def test_history_record_rejects_non_irr_record_namespace() -> None:
    with pytest.raises(ValidationError, match=r"irr\.\*"):
        HistoryRecord.from_canonical_bytes(b'{"schema":"foreign.record.v1"}')


def test_history_record_rejects_declared_identity_content_mismatch() -> None:
    first = _request("first")
    second = _request("second")

    with pytest.raises(HistoryIntegrityError, match="identity must equal"):
        HistoryRecord(
            identity=first.identity,
            record_type=IntentRequest.SCHEMA,
            canonical_record_bytes=second.canonical_bytes(),
        )


def test_history_record_rejects_declared_type_schema_mismatch() -> None:
    request = _request("type-mismatch")

    with pytest.raises(HistoryIntegrityError, match="type must equal"):
        HistoryRecord(
            identity=request.identity,
            record_type=ClaimRecord.SCHEMA,
            canonical_record_bytes=request.canonical_bytes(),
        )


def test_reference_repository_satisfies_public_repository_protocol() -> None:
    repository = InMemoryAdmittedHistoryRepository()

    assert isinstance(repository, AdmittedHistoryRepository)
    assert tuple(signature(repository.persist).parameters) == ("record",)
    assert tuple(signature(repository.get).parameters) == ("identity",)
    assert tuple(signature(repository.read).parameters) == ("query",)


def test_exact_duplicate_persistence_is_idempotent() -> None:
    repository = InMemoryAdmittedHistoryRepository()
    record = _history_record(_request("duplicate"))

    first = repository.persist(record)
    second = repository.persist(record)

    assert first is HistoryPersistResult.INSERTED
    assert second is HistoryPersistResult.ALREADY_PRESENT
    assert repository.get(record.identity) == record
    assert _all_records(repository) == (record,)


def test_exact_lookup_returns_none_for_absent_identity() -> None:
    repository = InMemoryAdmittedHistoryRepository()
    absent = RecordIdentity("sha256", "0" * 64)

    assert repository.get(absent) is None


def test_history_scan_is_bounded_and_uses_explicit_cursor() -> None:
    repository = InMemoryAdmittedHistoryRepository()
    records = [_history_record(_request(label)) for label in ("a", "b", "c")]
    for record in records:
        repository.persist(record)

    first_page = repository.read(HistoryQuery(limit=2))
    assert len(first_page.records) == 2
    assert first_page.next_after_identity == first_page.records[-1].identity

    second_page = repository.read(
        HistoryQuery(limit=2, after_identity=first_page.next_after_identity)
    )
    assert len(second_page.records) == 1
    assert second_page.next_after_identity is None

    combined = first_page.records + second_page.records
    assert {record.identity for record in combined} == {
        record.identity for record in records
    }


def test_history_query_rejects_unbounded_or_excessive_pages() -> None:
    with pytest.raises(ValidationError, match="HistoryQuery.limit"):
        HistoryQuery(limit=0)
    with pytest.raises(ValidationError, match="HistoryQuery.limit"):
        HistoryQuery(limit=MAX_HISTORY_PAGE_SIZE + 1)


def test_scan_order_is_independent_of_insertion_order() -> None:
    records = tuple(
        _history_record(_request(label)) for label in ("one", "two", "three")
    )
    forward = InMemoryAdmittedHistoryRepository()
    reverse = InMemoryAdmittedHistoryRepository()

    for record in records:
        forward.persist(record)
    for record in reversed(records):
        reverse.persist(record)

    forward_ids = tuple(record.identity for record in _all_records(forward))
    reverse_ids = tuple(record.identity for record in _all_records(reverse))

    assert forward_ids == reverse_ids
    assert forward_ids == tuple(sorted(forward_ids, key=str))


def test_type_filter_returns_only_exact_record_schema() -> None:
    repository = InMemoryAdmittedHistoryRepository()
    request_record = _history_record(_request("typed"))
    claim_record = _history_record(_claim("typed"))
    repository.persist(request_record)
    repository.persist(claim_record)

    page = repository.read(
        HistoryQuery(limit=MAX_HISTORY_PAGE_SIZE, record_type=IntentRequest.SCHEMA)
    )

    assert page.records == (request_record,)
    assert page.next_after_identity is None


def test_multiple_same_type_records_are_retained_without_latest_write_wins() -> None:
    repository = InMemoryAdmittedHistoryRepository()
    first = _history_record(_request("competing-first"))
    second = _history_record(_request("competing-second"))

    repository.persist(first)
    repository.persist(second)

    records = repository.read(
        HistoryQuery(limit=MAX_HISTORY_PAGE_SIZE, record_type=IntentRequest.SCHEMA)
    ).records
    assert {record.identity for record in records} == {first.identity, second.identity}

    for forbidden in (
        "latest",
        "current",
        "active",
        "update",
        "delete",
        "replace",
        "set_status",
    ):
        assert not hasattr(repository, forbidden)


def test_exact_retrieval_is_sufficient_for_typed_record_replay() -> None:
    repository = InMemoryAdmittedHistoryRepository()
    request = _request("replay")
    record = _history_record(request)
    repository.persist(record)

    restored_record = repository.get(request.identity)
    assert restored_record is not None

    replayed = IntentRequest.from_json_bytes(restored_record.canonical_record_bytes)
    assert replayed == request
    assert replayed.identity == request.identity


def test_persistence_surface_adds_no_semantic_or_execution_authority() -> None:
    record = _history_record(_request("authority"))
    repository = InMemoryAdmittedHistoryRepository()
    repository.persist(record)

    for target in (record, repository):
        for forbidden in (
            "governance",
            "authorization",
            "permission",
            "approved",
            "execute",
            "executor",
            "retry",
            "selected_capability",
            "active_lineage",
        ):
            assert not hasattr(target, forbidden)
