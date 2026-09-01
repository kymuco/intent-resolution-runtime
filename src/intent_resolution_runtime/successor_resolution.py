from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from .canonical import canonical_json_bytes, parse_json_object
from .continuation import ContinuationInput
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .resolution import ClarificationNeed, InformationNeed, ResolvedIntent


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


def _identity_key(value: RecordIdentity) -> tuple[str, str]:
    return value.algorithm, value.digest


class _CanonicalSuccessorResolutionRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class SuccessorResolutionKind(str, Enum):
    RESOLVED_INTENT = "resolved_intent"
    CLARIFICATION_NEED = "clarification_need"
    INFORMATION_NEED = "information_need"


def _successor_kind(
    successor: ResolvedIntent | ClarificationNeed | InformationNeed,
) -> SuccessorResolutionKind:
    if type(successor) is ResolvedIntent:
        return SuccessorResolutionKind.RESOLVED_INTENT
    if type(successor) is ClarificationNeed:
        return SuccessorResolutionKind.CLARIFICATION_NEED
    if type(successor) is InformationNeed:
        return SuccessorResolutionKind.INFORMATION_NEED
    raise ValidationError(
        "SuccessorResolutionLineage.successor must be a ResolvedIntent, "
        "ClarificationNeed, or InformationNeed"
    )


def _parse_successor(
    kind: SuccessorResolutionKind, value: object
) -> ResolvedIntent | ClarificationNeed | InformationNeed:
    if kind is SuccessorResolutionKind.RESOLVED_INTENT:
        return ResolvedIntent.from_primitive(value)
    if kind is SuccessorResolutionKind.CLARIFICATION_NEED:
        return ClarificationNeed.from_primitive(value)
    if kind is SuccessorResolutionKind.INFORMATION_NEED:
        return InformationNeed.from_primitive(value)
    raise AssertionError("unsupported SuccessorResolutionKind")


def _normalize_continuation_inputs(
    value: object, *, field: str
) -> tuple[ContinuationInput, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if not all(type(item) is ContinuationInput for item in value):
        raise ValidationError(f"{field} must contain ContinuationInput values")

    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate ContinuationInput identities")

    source_identities = [item.source_identity for item in items]
    if len(set(source_identities)) != len(source_identities):
        raise ValidationError(
            f"{field} must not amplify one source through repeated re-entry occurrences"
        )

    return tuple(sorted(items, key=lambda item: _identity_key(item.source_identity)))


@dataclass(frozen=True, slots=True)
class SuccessorResolutionLineage(_CanonicalSuccessorResolutionRecord):
    """Canonical relation from one ResolvedIntent through exact re-entry material to one successor ResolutionOutput."""

    SCHEMA: ClassVar[str] = "irr.successor_resolution_lineage.v1"

    predecessor: ResolvedIntent
    continuation_inputs: tuple[ContinuationInput, ...]
    successor_kind: SuccessorResolutionKind
    successor: ResolvedIntent | ClarificationNeed | InformationNeed

    def __post_init__(self) -> None:
        if type(self.predecessor) is not ResolvedIntent:
            raise ValidationError(
                "SuccessorResolutionLineage.predecessor must be a ResolvedIntent"
            )
        inputs = _normalize_continuation_inputs(
            self.continuation_inputs,
            field="SuccessorResolutionLineage.continuation_inputs",
        )
        if any(
            item.resolved_intent_identity != self.predecessor.identity
            for item in inputs
        ):
            raise ValidationError(
                "SuccessorResolutionLineage continuation inputs must descend from "
                "the exact predecessor ResolvedIntent"
            )
        object.__setattr__(self, "continuation_inputs", inputs)

        if type(self.successor_kind) is not SuccessorResolutionKind:
            raise ValidationError(
                "SuccessorResolutionLineage.successor_kind must be a SuccessorResolutionKind"
            )
        expected_kind = _successor_kind(self.successor)
        if self.successor_kind is not expected_kind:
            raise ValidationError(
                "SuccessorResolutionLineage.successor_kind must match the exact successor type"
            )

        if self.successor.intent_request_identity != self.predecessor.intent_request_identity:
            raise ValidationError(
                "SuccessorResolutionLineage successor must preserve the predecessor IntentRequest identity"
            )

        predecessor_event = self.predecessor.admission_attribution.admission_event_ref
        source_events = {item.source_event_ref for item in inputs}
        reentry_events = {item.attribution.reentry_event_ref for item in inputs}

        if predecessor_event in source_events:
            raise ValidationError(
                "SuccessorResolutionLineage source occurrence must differ from "
                "the predecessor admission occurrence"
            )
        if predecessor_event in reentry_events:
            raise ValidationError(
                "SuccessorResolutionLineage re-entry occurrence must differ from "
                "the predecessor admission occurrence"
            )
        if source_events.intersection(reentry_events):
            raise ValidationError(
                "SuccessorResolutionLineage source occurrences must remain distinct "
                "from Host re-entry occurrences"
            )

        successor_event = self.successor.admission_attribution.admission_event_ref
        if successor_event == predecessor_event:
            raise ValidationError(
                "SuccessorResolutionLineage successor admission occurrence must differ "
                "from the predecessor admission occurrence"
            )
        if successor_event in source_events:
            raise ValidationError(
                "SuccessorResolutionLineage successor admission occurrence must differ "
                "from every source occurrence"
            )
        if successor_event in reentry_events:
            raise ValidationError(
                "SuccessorResolutionLineage successor admission occurrence must differ "
                "from every re-entry occurrence"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "continuation_inputs": [
                item.to_primitive() for item in self.continuation_inputs
            ],
            "predecessor": self.predecessor.to_primitive(),
            "schema": self.SCHEMA,
            "successor": self.successor.to_primitive(),
            "successor_kind": self.successor_kind.value,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "SuccessorResolutionLineage"
    ) -> "SuccessorResolutionLineage":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "predecessor",
                "continuation_inputs",
                "successor_kind",
                "successor",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["successor_kind"]) is not str:
            raise SerializationError(f"{field}.successor_kind must be a string")
        try:
            kind = SuccessorResolutionKind(obj["successor_kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.successor_kind") from exc

        inputs = _expect_array(
            obj["continuation_inputs"], field=f"{field}.continuation_inputs"
        )
        try:
            return cls(
                predecessor=ResolvedIntent.from_primitive(obj["predecessor"]),
                continuation_inputs=tuple(
                    ContinuationInput.from_primitive(
                        item, field=f"{field}.continuation_inputs[{index}]"
                    )
                    for index, item in enumerate(inputs)
                ),
                successor_kind=kind,
                successor=_parse_successor(kind, obj["successor"]),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "SuccessorResolutionLineage":
        return cls.from_primitive(parse_json_object(data))
