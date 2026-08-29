from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from .canonical import canonical_json_bytes, parse_json_object
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes


class OriginKind(str, Enum):
    HUMAN = "human"
    COMPANION = "companion"
    WORKER = "worker"
    SYSTEM = "system"


def _require_token(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if value != value.strip():
        raise ValidationError(f"{field} must not contain leading or trailing whitespace")
    return value


def _require_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string")
    if not value.strip():
        raise ValidationError(f"{field} must contain non-whitespace text")
    return value


def _expect_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SerializationError(f"{field} must be a JSON object")
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


@dataclass(frozen=True, slots=True)
class StableRef:
    """Opaque namespaced reference supplied by the Host boundary."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        _require_token(self.namespace, field="StableRef.namespace")
        _require_token(self.value, field="StableRef.value")

    def to_primitive(self) -> dict[str, str]:
        return {"namespace": self.namespace, "value": self.value}

    @classmethod
    def from_primitive(cls, value: object, *, field: str) -> "StableRef":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"namespace", "value"}, field=field)
        try:
            return cls(namespace=obj["namespace"], value=obj["value"])
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


@dataclass(frozen=True, slots=True)
class OriginAttribution:
    """Attributed producer of an IntentRequest; this is not identity verification."""

    kind: OriginKind
    actor_ref: StableRef
    source_event_ref: StableRef

    def __post_init__(self) -> None:
        if not isinstance(self.kind, OriginKind):
            raise ValidationError("OriginAttribution.kind must be an OriginKind")
        if not isinstance(self.actor_ref, StableRef):
            raise ValidationError("OriginAttribution.actor_ref must be a StableRef")
        if not isinstance(self.source_event_ref, StableRef):
            raise ValidationError("OriginAttribution.source_event_ref must be a StableRef")

    def to_primitive(self) -> dict[str, object]:
        return {
            "actor_ref": self.actor_ref.to_primitive(),
            "kind": self.kind.value,
            "source_event_ref": self.source_event_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(cls, value: object) -> "OriginAttribution":
        obj = _expect_object(value, field="origin")
        _expect_exact_keys(obj, {"kind", "actor_ref", "source_event_ref"}, field="origin")
        kind_value = obj["kind"]
        if not isinstance(kind_value, str):
            raise SerializationError("origin.kind must be a string")
        try:
            kind = OriginKind(kind_value)
        except ValueError as exc:
            raise SerializationError(f"unsupported origin.kind: {kind_value!r}") from exc
        return cls(
            kind=kind,
            actor_ref=StableRef.from_primitive(obj["actor_ref"], field="origin.actor_ref"),
            source_event_ref=StableRef.from_primitive(
                obj["source_event_ref"], field="origin.source_event_ref"
            ),
        )


@dataclass(frozen=True, slots=True)
class IntentExpression:
    """M1.1 textual intent expression. Other expression schemas may be added later."""

    text: str

    def __post_init__(self) -> None:
        _require_text(self.text, field="IntentExpression.text")

    def to_primitive(self) -> dict[str, str]:
        return {"text": self.text}

    @classmethod
    def from_primitive(cls, value: object) -> "IntentExpression":
        obj = _expect_object(value, field="expression")
        _expect_exact_keys(obj, {"text"}, field="expression")
        try:
            return cls(text=obj["text"])
        except ValidationError as exc:
            raise SerializationError("invalid expression") from exc


@dataclass(frozen=True, slots=True)
class IntentRequest:
    """Immutable v1 request record at the IRR input boundary."""

    SCHEMA: ClassVar[str] = "irr.intent_request.v1"

    origin: OriginAttribution
    principal_ref: StableRef
    expression: IntentExpression

    def __post_init__(self) -> None:
        if not isinstance(self.origin, OriginAttribution):
            raise ValidationError("IntentRequest.origin must be an OriginAttribution")
        if not isinstance(self.principal_ref, StableRef):
            raise ValidationError("IntentRequest.principal_ref must be a StableRef")
        if not isinstance(self.expression, IntentExpression):
            raise ValidationError("IntentRequest.expression must be an IntentExpression")

    def to_primitive(self) -> dict[str, object]:
        return {
            "expression": self.expression.to_primitive(),
            "origin": self.origin.to_primitive(),
            "principal_ref": self.principal_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "IntentRequest":
        obj = parse_json_object(data)
        _expect_exact_keys(
            obj,
            {"schema", "origin", "principal_ref", "expression"},
            field="IntentRequest",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported IntentRequest schema: {obj['schema']!r}")
        return cls(
            origin=OriginAttribution.from_primitive(obj["origin"]),
            principal_ref=StableRef.from_primitive(obj["principal_ref"], field="principal_ref"),
            expression=IntentExpression.from_primitive(obj["expression"]),
        )
