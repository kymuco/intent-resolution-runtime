from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, TypeAlias

from .canonical import canonical_json_bytes, parse_json_object
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef


def _reject_surrogates(value: str, *, field: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValidationError(f"{field} must contain only Unicode scalar values")


def _require_text(value: object, *, field: str) -> str:
    if type(value) is not str:
        raise ValidationError(f"{field} must be a string")
    if not value.strip():
        raise ValidationError(f"{field} must contain non-whitespace text")
    _reject_surrogates(value, field=field)
    return value


def _expect_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SerializationError(f"{field} must be a JSON object")
    return value


def _expect_array(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise SerializationError(f"{field} must be a JSON array")
    return value


def _expect_exact_keys(value: dict[str, Any], expected: set[str], *, field: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        detail: list[str] = []
        if missing:
            detail.append(f"missing={missing}")
        if extra:
            detail.append(f"extra={extra}")
        raise SerializationError(f"{field} has invalid fields ({', '.join(detail)})")


class _CanonicalRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class SourceAttribution:
    """Attributed source of context material; not source verification."""

    source_ref: StableRef
    source_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.source_ref) is not StableRef:
            raise ValidationError("SourceAttribution.source_ref must be a StableRef")
        if type(self.source_event_ref) is not StableRef:
            raise ValidationError("SourceAttribution.source_event_ref must be a StableRef")

    def to_primitive(self) -> dict[str, object]:
        return {
            "source_event_ref": self.source_event_ref.to_primitive(),
            "source_ref": self.source_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(cls, value: object, *, field: str = "attribution") -> "SourceAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"source_ref", "source_event_ref"}, field=field)
        try:
            return cls(
                source_ref=StableRef.from_primitive(obj["source_ref"], field=f"{field}.source_ref"),
                source_event_ref=StableRef.from_primitive(
                    obj["source_event_ref"], field=f"{field}.source_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


class EvidenceRelation(str, Enum):
    SUPPORTS = "supports"
    WEAKENS = "weakens"


class EvidenceTargetKind(str, Enum):
    CLAIM = "claim"
    ATTRIBUTION = "attribution"
    ORIGIN_ATTRIBUTION = "origin_attribution"


class TemporalBasisKind(str, Enum):
    RESOLUTION_TIME = "resolution_time"
    TIMESTAMP = "timestamp"
    SEQUENCE = "sequence"
    NAMED = "named"


@dataclass(frozen=True, slots=True)
class ClaimRecord(_CanonicalRecord):
    SCHEMA: ClassVar[str] = "irr.claim.v1"

    attribution: SourceAttribution
    statement: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not SourceAttribution:
            raise ValidationError("ClaimRecord.attribution must be a SourceAttribution")
        _require_text(self.statement, field="ClaimRecord.statement")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "schema": self.SCHEMA,
            "statement": self.statement,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "ClaimRecord":
        obj = _expect_object(value, field="ClaimRecord")
        _expect_exact_keys(obj, {"schema", "attribution", "statement"}, field="ClaimRecord")
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported ClaimRecord schema: {obj['schema']!r}")
        try:
            return cls(
                attribution=SourceAttribution.from_primitive(obj["attribution"]),
                statement=obj["statement"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid ClaimRecord") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "ClaimRecord":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class EvidenceRecord(_CanonicalRecord):
    SCHEMA: ClassVar[str] = "irr.evidence.v1"

    attribution: SourceAttribution
    relation: EvidenceRelation
    target_kind: EvidenceTargetKind
    target_identity: RecordIdentity
    scope: str
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not SourceAttribution:
            raise ValidationError("EvidenceRecord.attribution must be a SourceAttribution")
        if type(self.relation) is not EvidenceRelation:
            raise ValidationError("EvidenceRecord.relation must be an EvidenceRelation")
        if type(self.target_kind) is not EvidenceTargetKind:
            raise ValidationError("EvidenceRecord.target_kind must be an EvidenceTargetKind")
        if type(self.target_identity) is not RecordIdentity:
            raise ValidationError("EvidenceRecord.target_identity must be a RecordIdentity")
        _require_text(self.scope, field="EvidenceRecord.scope")
        _require_text(self.description, field="EvidenceRecord.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "description": self.description,
            "relation": self.relation.value,
            "schema": self.SCHEMA,
            "scope": self.scope,
            "target_identity": self.target_identity.to_primitive(),
            "target_kind": self.target_kind.value,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "EvidenceRecord":
        obj = _expect_object(value, field="EvidenceRecord")
        _expect_exact_keys(
            obj,
            {"schema", "attribution", "relation", "target_kind", "target_identity", "scope", "description"},
            field="EvidenceRecord",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported EvidenceRecord schema: {obj['schema']!r}")
        try:
            relation = EvidenceRelation(obj["relation"])
            target_kind = EvidenceTargetKind(obj["target_kind"])
        except (ValueError, TypeError) as exc:
            raise SerializationError("unsupported EvidenceRecord relation or target_kind") from exc
        try:
            return cls(
                attribution=SourceAttribution.from_primitive(obj["attribution"]),
                relation=relation,
                target_kind=target_kind,
                target_identity=RecordIdentity.from_primitive(
                    obj["target_identity"], field="EvidenceRecord.target_identity"
                ),
                scope=obj["scope"],
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid EvidenceRecord") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "EvidenceRecord":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class TemporalBasisRecord(_CanonicalRecord):
    SCHEMA: ClassVar[str] = "irr.temporal_basis.v1"

    attribution: SourceAttribution
    kind: TemporalBasisKind
    value: str
    scope: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not SourceAttribution:
            raise ValidationError("TemporalBasisRecord.attribution must be a SourceAttribution")
        if type(self.kind) is not TemporalBasisKind:
            raise ValidationError("TemporalBasisRecord.kind must be a TemporalBasisKind")
        _require_text(self.value, field="TemporalBasisRecord.value")
        _require_text(self.scope, field="TemporalBasisRecord.scope")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "kind": self.kind.value,
            "schema": self.SCHEMA,
            "scope": self.scope,
            "value": self.value,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "TemporalBasisRecord":
        obj = _expect_object(value, field="TemporalBasisRecord")
        _expect_exact_keys(
            obj, {"schema", "attribution", "kind", "value", "scope"}, field="TemporalBasisRecord"
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported TemporalBasisRecord schema: {obj['schema']!r}")
        try:
            kind = TemporalBasisKind(obj["kind"])
        except (ValueError, TypeError) as exc:
            raise SerializationError("unsupported TemporalBasisRecord.kind") from exc
        try:
            return cls(
                attribution=SourceAttribution.from_primitive(obj["attribution"]),
                kind=kind,
                value=obj["value"],
                scope=obj["scope"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid TemporalBasisRecord") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "TemporalBasisRecord":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CompletenessRecord(_CanonicalRecord):
    SCHEMA: ClassVar[str] = "irr.completeness.v1"

    attribution: SourceAttribution
    bounded_domain: str
    purpose: str
    temporal_basis_refs: tuple[RecordIdentity, ...] = ()

    def __post_init__(self) -> None:
        if type(self.attribution) is not SourceAttribution:
            raise ValidationError("CompletenessRecord.attribution must be a SourceAttribution")
        _require_text(self.bounded_domain, field="CompletenessRecord.bounded_domain")
        _require_text(self.purpose, field="CompletenessRecord.purpose")
        if type(self.temporal_basis_refs) is not tuple:
            raise ValidationError("CompletenessRecord.temporal_basis_refs must be a tuple")
        if not all(type(item) is RecordIdentity for item in self.temporal_basis_refs):
            raise ValidationError(
                "CompletenessRecord.temporal_basis_refs must contain RecordIdentity values"
            )
        if len(set(self.temporal_basis_refs)) != len(self.temporal_basis_refs):
            raise ValidationError("CompletenessRecord.temporal_basis_refs must not contain duplicates")
        object.__setattr__(
            self, "temporal_basis_refs", tuple(sorted(self.temporal_basis_refs, key=str))
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "bounded_domain": self.bounded_domain,
            "purpose": self.purpose,
            "schema": self.SCHEMA,
            "temporal_basis_refs": [
                identity.to_primitive() for identity in self.temporal_basis_refs
            ],
        }

    @classmethod
    def from_primitive(cls, value: object) -> "CompletenessRecord":
        obj = _expect_object(value, field="CompletenessRecord")
        _expect_exact_keys(
            obj,
            {"schema", "attribution", "bounded_domain", "purpose", "temporal_basis_refs"},
            field="CompletenessRecord",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported CompletenessRecord schema: {obj['schema']!r}")
        refs = _expect_array(obj["temporal_basis_refs"], field="CompletenessRecord.temporal_basis_refs")
        try:
            return cls(
                attribution=SourceAttribution.from_primitive(obj["attribution"]),
                bounded_domain=obj["bounded_domain"],
                purpose=obj["purpose"],
                temporal_basis_refs=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"CompletenessRecord.temporal_basis_refs[{index}]"
                    )
                    for index, item in enumerate(refs)
                ),
            )
        except ValidationError as exc:
            raise SerializationError("invalid CompletenessRecord") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "CompletenessRecord":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class ContextReferenceRecord(_CanonicalRecord):
    SCHEMA: ClassVar[str] = "irr.context_reference.v1"

    attribution: SourceAttribution
    reference: StableRef
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not SourceAttribution:
            raise ValidationError("ContextReferenceRecord.attribution must be a SourceAttribution")
        if type(self.reference) is not StableRef:
            raise ValidationError("ContextReferenceRecord.reference must be a StableRef")
        _require_text(self.description, field="ContextReferenceRecord.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "description": self.description,
            "reference": self.reference.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "ContextReferenceRecord":
        obj = _expect_object(value, field="ContextReferenceRecord")
        _expect_exact_keys(
            obj, {"schema", "attribution", "reference", "description"}, field="ContextReferenceRecord"
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported ContextReferenceRecord schema: {obj['schema']!r}")
        try:
            return cls(
                attribution=SourceAttribution.from_primitive(obj["attribution"]),
                reference=StableRef.from_primitive(
                    obj["reference"], field="ContextReferenceRecord.reference"
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid ContextReferenceRecord") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "ContextReferenceRecord":
        return cls.from_primitive(parse_json_object(data))


ContextRecord: TypeAlias = (
    ClaimRecord
    | EvidenceRecord
    | TemporalBasisRecord
    | CompletenessRecord
    | ContextReferenceRecord
)


_RECORD_BY_SCHEMA = {
    ClaimRecord.SCHEMA: ClaimRecord,
    EvidenceRecord.SCHEMA: EvidenceRecord,
    TemporalBasisRecord.SCHEMA: TemporalBasisRecord,
    CompletenessRecord.SCHEMA: CompletenessRecord,
    ContextReferenceRecord.SCHEMA: ContextReferenceRecord,
}


def _parse_context_record(value: object, *, index: int) -> ContextRecord:
    obj = _expect_object(value, field=f"ContextEnvelope.records[{index}]")
    schema = obj.get("schema")
    if type(schema) is not str:
        raise SerializationError(f"ContextEnvelope.records[{index}].schema must be a string")
    record_type = _RECORD_BY_SCHEMA.get(schema)
    if record_type is None:
        raise SerializationError(f"unsupported context record schema: {schema!r}")
    return record_type.from_primitive(obj)


@dataclass(frozen=True, slots=True)
class ContextEnvelope(_CanonicalRecord):
    """Explicit bounded Host-supplied context for one IntentRequest lineage."""

    SCHEMA: ClassVar[str] = "irr.context_envelope.v1"

    intent_request_identity: RecordIdentity
    boundary_attribution: SourceAttribution
    records: tuple[ContextRecord, ...]

    def __post_init__(self) -> None:
        if type(self.intent_request_identity) is not RecordIdentity:
            raise ValidationError("ContextEnvelope.intent_request_identity must be a RecordIdentity")
        if type(self.boundary_attribution) is not SourceAttribution:
            raise ValidationError("ContextEnvelope.boundary_attribution must be a SourceAttribution")
        if type(self.records) is not tuple:
            raise ValidationError("ContextEnvelope.records must be a tuple")
        allowed = (
            ClaimRecord,
            EvidenceRecord,
            TemporalBasisRecord,
            CompletenessRecord,
            ContextReferenceRecord,
        )
        if not all(type(record) in allowed for record in self.records):
            raise ValidationError("ContextEnvelope.records contains an unsupported record type")

        identities = [record.identity for record in self.records]
        if len(set(identities)) != len(identities):
            raise ValidationError("ContextEnvelope.records must not contain duplicate record identities")

        ordered = tuple(sorted(self.records, key=lambda record: str(record.identity)))
        object.__setattr__(self, "records", ordered)
        self._validate_links()

    def _validate_links(self) -> None:
        records_by_identity = {record.identity: record for record in self.records}
        for record in self.records:
            if type(record) is EvidenceRecord:
                if record.target_kind is EvidenceTargetKind.ORIGIN_ATTRIBUTION:
                    if record.target_identity != self.intent_request_identity:
                        raise ValidationError(
                            "origin_attribution evidence must target this envelope's IntentRequest"
                        )
                    continue
                target = records_by_identity.get(record.target_identity)
                if target is None:
                    raise ValidationError(
                        "EvidenceRecord target must be present in the bounded ContextEnvelope"
                    )
                if record.target_kind is EvidenceTargetKind.CLAIM and type(target) not in (
                    ClaimRecord, CompletenessRecord
                ):
                    raise ValidationError(
                        "claim evidence must target a ClaimRecord or CompletenessRecord"
                    )
            elif type(record) is CompletenessRecord:
                for temporal_ref in record.temporal_basis_refs:
                    target = records_by_identity.get(temporal_ref)
                    if type(target) is not TemporalBasisRecord:
                        raise ValidationError(
                            "CompletenessRecord temporal basis must resolve to a TemporalBasisRecord "
                            "inside the same ContextEnvelope"
                        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "boundary_attribution": self.boundary_attribution.to_primitive(),
            "intent_request_identity": self.intent_request_identity.to_primitive(),
            "records": [record.to_primitive() for record in self.records],
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "ContextEnvelope":
        obj = _expect_object(value, field="ContextEnvelope")
        _expect_exact_keys(
            obj,
            {"schema", "intent_request_identity", "boundary_attribution", "records"},
            field="ContextEnvelope",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported ContextEnvelope schema: {obj['schema']!r}")
        records = _expect_array(obj["records"], field="ContextEnvelope.records")
        try:
            return cls(
                intent_request_identity=RecordIdentity.from_primitive(
                    obj["intent_request_identity"], field="ContextEnvelope.intent_request_identity"
                ),
                boundary_attribution=SourceAttribution.from_primitive(
                    obj["boundary_attribution"], field="ContextEnvelope.boundary_attribution"
                ),
                records=tuple(
                    _parse_context_record(item, index=index) for index, item in enumerate(records)
                ),
            )
        except ValidationError as exc:
            raise SerializationError("invalid ContextEnvelope") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "ContextEnvelope":
        return cls.from_primitive(parse_json_object(data))
