from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from .canonical import canonical_json_bytes, parse_json_object
from .errors import IntentIRError, SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes

MAX_HISTORY_PAGE_SIZE = 256


class HistoryIntegrityError(IntentIRError):
    """Raised when persisted history cannot preserve exact record identity/content."""


class HistoryPersistResult(str, Enum):
    INSERTED = "inserted"
    ALREADY_PRESENT = "already_present"


def _require_record_type(value: object, *, field: str) -> str:
    if type(value) is not str:
        raise ValidationError(f"{field} must be a string")
    if not value or value != value.strip():
        raise ValidationError(f"{field} must be a non-empty trimmed string")
    if not value.startswith("irr."):
        raise ValidationError(f"{field} must use the irr.* record namespace")
    return value


@dataclass(frozen=True, slots=True)
class HistoryRecord:
    """Exact persisted canonical IRR record bytes plus content identity and type.

    This is a Host persistence value, not a new canonical semantic lifecycle record.
    Presence in a repository does not by itself establish active lineage, precedence,
    Authorization, completion, or any other semantic claim.
    """

    identity: RecordIdentity
    record_type: str
    canonical_record_bytes: bytes

    def __post_init__(self) -> None:
        if type(self.identity) is not RecordIdentity:
            raise ValidationError("HistoryRecord.identity must be a RecordIdentity")
        _require_record_type(self.record_type, field="HistoryRecord.record_type")
        if type(self.canonical_record_bytes) is not bytes:
            raise ValidationError(
                "HistoryRecord.canonical_record_bytes must be exact immutable bytes"
            )
        if not self.canonical_record_bytes:
            raise HistoryIntegrityError("history record bytes must not be empty")

        try:
            primitive = parse_json_object(self.canonical_record_bytes)
            canonical = canonical_json_bytes(primitive)
        except SerializationError as exc:
            raise HistoryIntegrityError(
                "history record bytes must be valid canonical IRR JSON"
            ) from exc

        if canonical != self.canonical_record_bytes:
            raise HistoryIntegrityError(
                "history record bytes must already be in exact canonical form"
            )

        schema = primitive.get("schema")
        if type(schema) is not str:
            raise HistoryIntegrityError(
                "history record bytes must contain a top-level string schema"
            )
        if schema != self.record_type:
            raise HistoryIntegrityError(
                "history record type must equal the canonical record schema"
            )

        expected_identity = identity_for_bytes(self.canonical_record_bytes)
        if self.identity != expected_identity:
            raise HistoryIntegrityError(
                "history record identity must equal the exact canonical record bytes"
            )

    @classmethod
    def from_canonical_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> HistoryRecord:
        try:
            raw = bytes(data)
        except (TypeError, ValueError) as exc:
            raise HistoryIntegrityError(
                "history record input must be bytes-like"
            ) from exc
        if not raw:
            raise HistoryIntegrityError("history record bytes must not be empty")
        try:
            primitive = parse_json_object(raw)
        except SerializationError as exc:
            raise HistoryIntegrityError(
                "history record bytes must be valid canonical IRR JSON"
            ) from exc
        schema = primitive.get("schema")
        if type(schema) is not str:
            raise HistoryIntegrityError(
                "history record bytes must contain a top-level string schema"
            )
        return cls(
            identity=identity_for_bytes(raw),
            record_type=schema,
            canonical_record_bytes=raw,
        )


@dataclass(frozen=True, slots=True)
class HistoryQuery:
    """Bounded mechanical history retrieval request.

    Identity ordering is only a deterministic pagination mechanism. It carries no
    lifecycle chronology, active-lineage, recency, or semantic-precedence meaning.
    """

    limit: int
    record_type: str | None = None
    after_identity: RecordIdentity | None = None

    def __post_init__(self) -> None:
        if type(self.limit) is not int or not 1 <= self.limit <= MAX_HISTORY_PAGE_SIZE:
            raise ValidationError(
                f"HistoryQuery.limit must be an integer from 1 to {MAX_HISTORY_PAGE_SIZE}"
            )
        if self.record_type is not None:
            _require_record_type(self.record_type, field="HistoryQuery.record_type")
        if (
            self.after_identity is not None
            and type(self.after_identity) is not RecordIdentity
        ):
            raise ValidationError(
                "HistoryQuery.after_identity must be a RecordIdentity or None"
            )


@dataclass(frozen=True, slots=True)
class HistoryPage:
    """Bounded non-canonical repository view over exact persisted records."""

    records: tuple[HistoryRecord, ...]
    next_after_identity: RecordIdentity | None

    def __post_init__(self) -> None:
        if type(self.records) is not tuple or not all(
            type(record) is HistoryRecord for record in self.records
        ):
            raise ValidationError(
                "HistoryPage.records must contain HistoryRecord values"
            )
        identities = [record.identity for record in self.records]
        if len(set(identities)) != len(identities):
            raise ValidationError(
                "HistoryPage.records must not contain duplicate identities"
            )
        if (
            self.next_after_identity is not None
            and type(self.next_after_identity) is not RecordIdentity
        ):
            raise ValidationError(
                "HistoryPage.next_after_identity must be a RecordIdentity or None"
            )


@runtime_checkable
class AdmittedHistoryRepository(Protocol):
    """Minimum M3.1 persistence/replay mechanism for already-admitted IRR history.

    Persisting a record is not semantic admission. Implementations preserve exact bytes
    and expose bounded retrieval only; they must not infer active lineage or precedence.
    """

    def persist(self, record: HistoryRecord) -> HistoryPersistResult: ...

    def get(self, identity: RecordIdentity) -> HistoryRecord | None: ...

    def read(self, query: HistoryQuery) -> HistoryPage: ...


class InMemoryAdmittedHistoryRepository:
    """Reference M3.1 repository implementation with no semantic ordering policy."""

    __slots__ = ("_records",)

    def __init__(self) -> None:
        self._records: dict[RecordIdentity, HistoryRecord] = {}

    def persist(self, record: HistoryRecord) -> HistoryPersistResult:
        if type(record) is not HistoryRecord:
            raise ValidationError(
                "InMemoryAdmittedHistoryRepository.persist requires a HistoryRecord"
            )
        existing = self._records.get(record.identity)
        if existing is None:
            self._records[record.identity] = record
            return HistoryPersistResult.INSERTED
        if existing != record:
            raise HistoryIntegrityError(
                "record identity collision with different persisted type or content"
            )
        return HistoryPersistResult.ALREADY_PRESENT

    def get(self, identity: RecordIdentity) -> HistoryRecord | None:
        if type(identity) is not RecordIdentity:
            raise ValidationError(
                "InMemoryAdmittedHistoryRepository.get requires a RecordIdentity"
            )
        return self._records.get(identity)

    def read(self, query: HistoryQuery) -> HistoryPage:
        if type(query) is not HistoryQuery:
            raise ValidationError(
                "InMemoryAdmittedHistoryRepository.read requires a HistoryQuery"
            )

        records = tuple(
            sorted(self._records.values(), key=lambda record: str(record.identity))
        )
        if query.record_type is not None:
            records = tuple(
                record for record in records if record.record_type == query.record_type
            )
        if query.after_identity is not None:
            cursor = str(query.after_identity)
            records = tuple(
                record for record in records if str(record.identity) > cursor
            )

        has_more = len(records) > query.limit
        page_records = records[: query.limit]
        next_after_identity = page_records[-1].identity if has_more else None
        return HistoryPage(
            records=page_records,
            next_after_identity=next_after_identity,
        )


__all__ = (
    "MAX_HISTORY_PAGE_SIZE",
    "AdmittedHistoryRepository",
    "HistoryIntegrityError",
    "HistoryPage",
    "HistoryPersistResult",
    "HistoryQuery",
    "HistoryRecord",
    "InMemoryAdmittedHistoryRepository",
)
