from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from fractions import Fraction
from typing import Any, ClassVar, TypeAlias, cast

from .canonical import canonical_json_bytes, parse_json_object
from .context import SourceAttribution
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef


_RFC3339_PATTERN = re.compile(
    r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
    r"(?P<fraction>\.\d+)?(?P<zone>Z|[+-]\d{2}:\d{2})$"
)


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


def _require_token(value: object, *, field: str) -> str:
    if type(value) is not str:
        raise ValidationError(f"{field} must be a string")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if value != value.strip():
        raise ValidationError(f"{field} must not contain leading or trailing whitespace")
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


def _normalize_identity_tuple(
    value: object, *, field: str, nonempty: bool = False
) -> tuple[RecordIdentity, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is RecordIdentity for item in value):
        raise ValidationError(f"{field} must contain RecordIdentity values")
    if nonempty and not value:
        raise ValidationError(f"{field} must not be empty")
    if len(set(value)) != len(value):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(value, key=str))


def _normalize_ref_tuple(
    value: object, *, field: str, nonempty: bool = False
) -> tuple[StableRef, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is StableRef for item in value):
        raise ValidationError(f"{field} must contain StableRef values")
    if nonempty and not value:
        raise ValidationError(f"{field} must not be empty")
    if len(set(value)) != len(value):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(value, key=lambda item: (item.namespace, item.value)))


def _normalize_text_tuple(
    value: object, *, field: str, nonempty: bool = False
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is str for item in value):
        raise ValidationError(f"{field} must contain strings")
    if nonempty and not value:
        raise ValidationError(f"{field} must not be empty")
    for index, item in enumerate(value):
        _require_token(item, field=f"{field}[{index}]")
    if len(set(value)) != len(value):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(value))


def _parse_rfc3339(value: str, *, field: str) -> Fraction:
    match = _RFC3339_PATTERN.fullmatch(value)
    if match is None:
        raise ValidationError(f"{field} must be an RFC3339 timestamp with an explicit known offset")

    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second"))
    fraction = match.group("fraction")
    zone = match.group("zone")

    if hour > 23 or minute > 59:
        raise ValidationError(f"{field} has an invalid clock time")
    if second > 59:
        raise ValidationError(f"{field} leap-second notation is not supported by M1.4 v1")
    try:
        calendar_day = date(year, month, day)
    except ValueError as exc:
        raise ValidationError(f"{field} has an invalid calendar date") from exc

    if zone == "-00:00":
        raise ValidationError(f"{field} uses RFC3339 unknown-offset form -00:00")
    if zone == "Z":
        offset_seconds = 0
    else:
        sign = 1 if zone[0] == "+" else -1
        offset_hour = int(zone[1:3])
        offset_minute = int(zone[4:6])
        if offset_hour > 23 or offset_minute > 59:
            raise ValidationError(f"{field} has an invalid timezone offset")
        offset_seconds = sign * (offset_hour * 3600 + offset_minute * 60)

    whole_seconds = (
        calendar_day.toordinal() * 86400
        + hour * 3600
        + minute * 60
        + second
        - offset_seconds
    )
    instant = Fraction(whole_seconds, 1)
    if fraction is not None:
        digits = fraction[1:]
        instant += Fraction(int(digits), 10 ** len(digits))
    return instant


class _CanonicalBindingRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class BindingInputRole(str, Enum):
    PLAN_LOCAL_OUTPUT = "plan_local_output"
    CONTEXT = "context"
    OBSERVATION = "observation"
    OUTCOME = "outcome"
    OTHER_EXPLICIT = "other_explicit"


class BindingAttributeKind(str, Enum):
    TEXT = "text"
    RFC3339_TIMESTAMP = "rfc3339_timestamp"


class BindingConstraintOperator(str, Enum):
    EQUALS = "equals"


class BindingSelectionMode(str, Enum):
    REQUIRE_UNIQUE = "require_unique"
    MAX_ATTRIBUTE = "max_attribute"
    MIN_ATTRIBUTE = "min_attribute"
    ANY_INTERCHANGEABLE = "any_interchangeable"


class InterchangeableChoicePolicy(str, Enum):
    NONE = "none"
    CANONICAL_IDENTITY_MIN = "canonical_identity_min"


class BindingIssueKind(str, Enum):
    ZERO_MATCHES = "zero_matches"
    MULTIPLE_MATCHES = "multiple_matches"
    TIE = "tie"
    MISSING_REQUIRED_DATA = "missing_required_data"
    INCOMPATIBLE_INPUT = "incompatible_input"


@dataclass(frozen=True, slots=True)
class BindingAttribute:
    name: str
    kind: BindingAttributeKind
    value: str

    def __post_init__(self) -> None:
        _require_token(self.name, field="BindingAttribute.name")
        if type(self.kind) is not BindingAttributeKind:
            raise ValidationError("BindingAttribute.kind must be a BindingAttributeKind")
        _require_text(self.value, field="BindingAttribute.value")
        if self.kind is BindingAttributeKind.RFC3339_TIMESTAMP:
            _parse_rfc3339(self.value, field="BindingAttribute.value")

    def to_primitive(self) -> dict[str, object]:
        return {"kind": self.kind.value, "name": self.name, "value": self.value}

    @classmethod
    def from_primitive(cls, value: object, *, field: str = "BindingAttribute") -> "BindingAttribute":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"name", "kind", "value"}, field=field)
        if type(obj["kind"]) is not str:
            raise SerializationError(f"{field}.kind must be a string")
        try:
            kind = BindingAttributeKind(obj["kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.kind") from exc
        try:
            return cls(name=obj["name"], kind=kind, value=obj["value"])
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


@dataclass(frozen=True, slots=True)
class BindingConstraint:
    attribute_name: str
    operator: BindingConstraintOperator
    expected_kind: BindingAttributeKind
    expected_value: str

    def __post_init__(self) -> None:
        _require_token(self.attribute_name, field="BindingConstraint.attribute_name")
        if type(self.operator) is not BindingConstraintOperator:
            raise ValidationError("BindingConstraint.operator must be a BindingConstraintOperator")
        if type(self.expected_kind) is not BindingAttributeKind:
            raise ValidationError("BindingConstraint.expected_kind must be a BindingAttributeKind")
        _require_text(self.expected_value, field="BindingConstraint.expected_value")
        if self.expected_kind is BindingAttributeKind.RFC3339_TIMESTAMP:
            _parse_rfc3339(self.expected_value, field="BindingConstraint.expected_value")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribute_name": self.attribute_name,
            "expected_kind": self.expected_kind.value,
            "expected_value": self.expected_value,
            "operator": self.operator.value,
        }

    @classmethod
    def from_primitive(cls, value: object, *, field: str = "BindingConstraint") -> "BindingConstraint":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"attribute_name", "operator", "expected_kind", "expected_value"},
            field=field,
        )
        if type(obj["operator"]) is not str or type(obj["expected_kind"]) is not str:
            raise SerializationError(f"{field}.operator and expected_kind must be strings")
        try:
            operator = BindingConstraintOperator(obj["operator"])
            expected_kind = BindingAttributeKind(obj["expected_kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field} operator or expected_kind") from exc
        try:
            return cls(
                attribute_name=obj["attribute_name"],
                operator=operator,
                expected_kind=expected_kind,
                expected_value=obj["expected_value"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


@dataclass(frozen=True, slots=True)
class BindingSelectionPolicy:
    mode: BindingSelectionMode
    selector_attributes: tuple[str, ...] = ()
    selector_kinds: tuple[BindingAttributeKind, ...] = ()
    interchangeable_choice: InterchangeableChoicePolicy = InterchangeableChoicePolicy.NONE

    def __post_init__(self) -> None:
        if type(self.mode) is not BindingSelectionMode:
            raise ValidationError("BindingSelectionPolicy.mode must be a BindingSelectionMode")
        if type(self.interchangeable_choice) is not InterchangeableChoicePolicy:
            raise ValidationError(
                "BindingSelectionPolicy.interchangeable_choice must be an InterchangeableChoicePolicy"
            )
        object.__setattr__(
            self,
            "selector_attributes",
            _normalize_text_tuple(
                self.selector_attributes,
                field="BindingSelectionPolicy.selector_attributes",
            ),
        )
        if type(self.selector_kinds) is not tuple:
            raise ValidationError("BindingSelectionPolicy.selector_kinds must be a tuple")
        if not all(type(item) is BindingAttributeKind for item in self.selector_kinds):
            raise ValidationError(
                "BindingSelectionPolicy.selector_kinds must contain BindingAttributeKind values"
            )
        if self.mode in (BindingSelectionMode.MAX_ATTRIBUTE, BindingSelectionMode.MIN_ATTRIBUTE):
            if len(self.selector_attributes) != 1 or len(self.selector_kinds) != 1:
                raise ValidationError(
                    "max_attribute/min_attribute selection requires exactly one selector attribute and kind"
                )
            if self.interchangeable_choice is not InterchangeableChoicePolicy.NONE:
                raise ValidationError("extremum selection cannot define an interchangeable choice policy")
        elif self.mode is BindingSelectionMode.ANY_INTERCHANGEABLE:
            if self.selector_attributes or self.selector_kinds:
                raise ValidationError(
                    "any_interchangeable selection cannot define selector attributes or kinds"
                )
            if self.interchangeable_choice is not InterchangeableChoicePolicy.CANONICAL_IDENTITY_MIN:
                raise ValidationError(
                    "any_interchangeable requires canonical_identity_min as its explicit mechanical policy"
                )
        else:
            if self.selector_attributes or self.selector_kinds:
                raise ValidationError(
                    "require_unique selection cannot define selector attributes or kinds"
                )
            if self.interchangeable_choice is not InterchangeableChoicePolicy.NONE:
                raise ValidationError("require_unique selection cannot define an interchangeable choice policy")

    def to_primitive(self) -> dict[str, object]:
        return {
            "interchangeable_choice": self.interchangeable_choice.value,
            "mode": self.mode.value,
            "selector_attributes": list(self.selector_attributes),
            "selector_kinds": [kind.value for kind in self.selector_kinds],
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "BindingSelectionPolicy"
    ) -> "BindingSelectionPolicy":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"mode", "selector_attributes", "selector_kinds", "interchangeable_choice"},
            field=field,
        )
        selectors = _expect_array(obj["selector_attributes"], field=f"{field}.selector_attributes")
        selector_kinds = _expect_array(obj["selector_kinds"], field=f"{field}.selector_kinds")
        if type(obj["mode"]) is not str or type(obj["interchangeable_choice"]) is not str:
            raise SerializationError(f"{field}.mode and interchangeable_choice must be strings")
        try:
            mode = BindingSelectionMode(obj["mode"])
            choice = InterchangeableChoicePolicy(obj["interchangeable_choice"])
            parsed_selector_kinds = tuple(BindingAttributeKind(item) for item in selector_kinds)
        except (ValueError, TypeError) as exc:
            raise SerializationError(f"unsupported {field} selection policy") from exc
        try:
            return cls(
                mode=mode,
                selector_attributes=tuple(selectors),
                selector_kinds=parsed_selector_kinds,
                interchangeable_choice=choice,
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


@dataclass(frozen=True, slots=True)
class BindingAttribution:
    """Attribution of one mechanical binding evaluation; not authority."""

    evaluator_ref: StableRef
    binding_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.evaluator_ref) is not StableRef:
            raise ValidationError("BindingAttribution.evaluator_ref must be a StableRef")
        if type(self.binding_event_ref) is not StableRef:
            raise ValidationError("BindingAttribution.binding_event_ref must be a StableRef")

    def to_primitive(self) -> dict[str, object]:
        return {
            "binding_event_ref": self.binding_event_ref.to_primitive(),
            "evaluator_ref": self.evaluator_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "binding_attribution"
    ) -> "BindingAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"evaluator_ref", "binding_event_ref"}, field=field)
        try:
            return cls(
                evaluator_ref=StableRef.from_primitive(
                    obj["evaluator_ref"], field=f"{field}.evaluator_ref"
                ),
                binding_event_ref=StableRef.from_primitive(
                    obj["binding_event_ref"], field=f"{field}.binding_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


@dataclass(frozen=True, slots=True)
class SymbolicReference(_CanonicalBindingRecord):
    SCHEMA: ClassVar[str] = "irr.symbolic_reference.v1"

    resolved_intent_identity: RecordIdentity
    slot_ref: StableRef
    semantic_type: str
    selection_scope: str
    description: str

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError("SymbolicReference.resolved_intent_identity must be a RecordIdentity")
        if type(self.slot_ref) is not StableRef:
            raise ValidationError("SymbolicReference.slot_ref must be a StableRef")
        _require_token(self.semantic_type, field="SymbolicReference.semantic_type")
        _require_text(self.selection_scope, field="SymbolicReference.selection_scope")
        _require_text(self.description, field="SymbolicReference.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "resolved_intent_identity": self.resolved_intent_identity.to_primitive(),
            "schema": self.SCHEMA,
            "selection_scope": self.selection_scope,
            "semantic_type": self.semantic_type,
            "slot_ref": self.slot_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(cls, value: object) -> "SymbolicReference":
        obj = _expect_object(value, field="SymbolicReference")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "resolved_intent_identity",
                "slot_ref",
                "semantic_type",
                "selection_scope",
                "description",
            },
            field="SymbolicReference",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported SymbolicReference schema: {obj['schema']!r}")
        try:
            return cls(
                resolved_intent_identity=RecordIdentity.from_primitive(
                    obj["resolved_intent_identity"],
                    field="SymbolicReference.resolved_intent_identity",
                ),
                slot_ref=StableRef.from_primitive(obj["slot_ref"], field="SymbolicReference.slot_ref"),
                semantic_type=obj["semantic_type"],
                selection_scope=obj["selection_scope"],
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid SymbolicReference") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "SymbolicReference":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class BindingInput(_CanonicalBindingRecord):
    SCHEMA: ClassVar[str] = "irr.binding_input.v1"

    resolved_intent_identity: RecordIdentity
    input_ref: StableRef
    attribution: SourceAttribution
    role: BindingInputRole
    source_identity: RecordIdentity
    semantic_type: str
    value: str
    selection_scope: str
    value_scope: str
    attributes: tuple[BindingAttribute, ...] = ()
    temporal_basis_refs: tuple[RecordIdentity, ...] = ()
    completeness_refs: tuple[RecordIdentity, ...] = ()
    evidence_refs: tuple[RecordIdentity, ...] = ()

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError("BindingInput.resolved_intent_identity must be a RecordIdentity")
        if type(self.input_ref) is not StableRef:
            raise ValidationError("BindingInput.input_ref must be a StableRef")
        if type(self.attribution) is not SourceAttribution:
            raise ValidationError("BindingInput.attribution must be a SourceAttribution")
        if type(self.role) is not BindingInputRole:
            raise ValidationError("BindingInput.role must be a BindingInputRole")
        if type(self.source_identity) is not RecordIdentity:
            raise ValidationError("BindingInput.source_identity must be a RecordIdentity")
        _require_token(self.semantic_type, field="BindingInput.semantic_type")
        _require_text(self.value, field="BindingInput.value")
        _require_text(self.selection_scope, field="BindingInput.selection_scope")
        _require_text(self.value_scope, field="BindingInput.value_scope")
        if type(self.attributes) is not tuple:
            raise ValidationError("BindingInput.attributes must be a tuple")
        if not all(type(item) is BindingAttribute for item in self.attributes):
            raise ValidationError("BindingInput.attributes must contain BindingAttribute values")
        names = [item.name for item in self.attributes]
        if len(set(names)) != len(names):
            raise ValidationError("BindingInput.attributes must not contain duplicate names")
        object.__setattr__(self, "attributes", tuple(sorted(self.attributes, key=lambda item: item.name)))
        object.__setattr__(
            self,
            "temporal_basis_refs",
            _normalize_identity_tuple(
                self.temporal_basis_refs, field="BindingInput.temporal_basis_refs"
            ),
        )
        object.__setattr__(
            self,
            "completeness_refs",
            _normalize_identity_tuple(
                self.completeness_refs, field="BindingInput.completeness_refs"
            ),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_identity_tuple(self.evidence_refs, field="BindingInput.evidence_refs"),
        )

    def attribute_map(self) -> dict[str, BindingAttribute]:
        return {attribute.name: attribute for attribute in self.attributes}

    def to_primitive(self) -> dict[str, object]:
        return {
            "attributes": [attribute.to_primitive() for attribute in self.attributes],
            "attribution": self.attribution.to_primitive(),
            "completeness_refs": [identity.to_primitive() for identity in self.completeness_refs],
            "evidence_refs": [identity.to_primitive() for identity in self.evidence_refs],
            "input_ref": self.input_ref.to_primitive(),
            "resolved_intent_identity": self.resolved_intent_identity.to_primitive(),
            "role": self.role.value,
            "schema": self.SCHEMA,
            "selection_scope": self.selection_scope,
            "semantic_type": self.semantic_type,
            "source_identity": self.source_identity.to_primitive(),
            "temporal_basis_refs": [identity.to_primitive() for identity in self.temporal_basis_refs],
            "value": self.value,
            "value_scope": self.value_scope,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "BindingInput":
        obj = _expect_object(value, field="BindingInput")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "resolved_intent_identity",
                "input_ref",
                "attribution",
                "role",
                "source_identity",
                "semantic_type",
                "value",
                "selection_scope",
                "value_scope",
                "attributes",
                "temporal_basis_refs",
                "completeness_refs",
                "evidence_refs",
            },
            field="BindingInput",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported BindingInput schema: {obj['schema']!r}")
        if type(obj["role"]) is not str:
            raise SerializationError("BindingInput.role must be a string")
        try:
            role = BindingInputRole(obj["role"])
        except ValueError as exc:
            raise SerializationError("unsupported BindingInput.role") from exc
        attributes = _expect_array(obj["attributes"], field="BindingInput.attributes")
        temporal = _expect_array(obj["temporal_basis_refs"], field="BindingInput.temporal_basis_refs")
        completeness = _expect_array(obj["completeness_refs"], field="BindingInput.completeness_refs")
        evidence = _expect_array(obj["evidence_refs"], field="BindingInput.evidence_refs")
        try:
            return cls(
                resolved_intent_identity=RecordIdentity.from_primitive(
                    obj["resolved_intent_identity"],
                    field="BindingInput.resolved_intent_identity",
                ),
                input_ref=StableRef.from_primitive(obj["input_ref"], field="BindingInput.input_ref"),
                attribution=SourceAttribution.from_primitive(
                    obj["attribution"], field="BindingInput.attribution"
                ),
                role=role,
                source_identity=RecordIdentity.from_primitive(
                    obj["source_identity"], field="BindingInput.source_identity"
                ),
                semantic_type=obj["semantic_type"],
                value=obj["value"],
                selection_scope=obj["selection_scope"],
                value_scope=obj["value_scope"],
                attributes=tuple(
                    BindingAttribute.from_primitive(item, field=f"BindingInput.attributes[{index}]")
                    for index, item in enumerate(attributes)
                ),
                temporal_basis_refs=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"BindingInput.temporal_basis_refs[{index}]"
                    )
                    for index, item in enumerate(temporal)
                ),
                completeness_refs=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"BindingInput.completeness_refs[{index}]"
                    )
                    for index, item in enumerate(completeness)
                ),
                evidence_refs=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"BindingInput.evidence_refs[{index}]"
                    )
                    for index, item in enumerate(evidence)
                ),
            )
        except ValidationError as exc:
            raise SerializationError("invalid BindingInput") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "BindingInput":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class BindingRule(_CanonicalBindingRecord):
    SCHEMA: ClassVar[str] = "irr.binding_rule.v1"

    resolved_intent_identity: RecordIdentity
    rule_ref: StableRef
    symbolic_reference: SymbolicReference
    allowed_input_roles: tuple[BindingInputRole, ...]
    allowed_source_refs: tuple[StableRef, ...]
    allowed_source_identities: tuple[RecordIdentity, ...]
    input_semantic_type: str
    required_selection_scope: str
    constraints: tuple[BindingConstraint, ...]
    selection_policy: BindingSelectionPolicy
    description: str
    required_temporal_basis_refs: tuple[RecordIdentity, ...] = ()
    required_completeness_refs: tuple[RecordIdentity, ...] = ()
    required_evidence_refs: tuple[RecordIdentity, ...] = ()

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError("BindingRule.resolved_intent_identity must be a RecordIdentity")
        if type(self.rule_ref) is not StableRef:
            raise ValidationError("BindingRule.rule_ref must be a StableRef")
        if type(self.symbolic_reference) is not SymbolicReference:
            raise ValidationError("BindingRule.symbolic_reference must be a SymbolicReference")
        if self.symbolic_reference.resolved_intent_identity != self.resolved_intent_identity:
            raise ValidationError("BindingRule symbolic reference must belong to the same ResolvedIntent")
        if type(self.allowed_input_roles) is not tuple:
            raise ValidationError("BindingRule.allowed_input_roles must be a tuple")
        if not self.allowed_input_roles:
            raise ValidationError("BindingRule.allowed_input_roles must not be empty")
        if not all(type(item) is BindingInputRole for item in self.allowed_input_roles):
            raise ValidationError("BindingRule.allowed_input_roles contains an unsupported role")
        if len(set(self.allowed_input_roles)) != len(self.allowed_input_roles):
            raise ValidationError("BindingRule.allowed_input_roles must not contain duplicates")
        object.__setattr__(
            self,
            "allowed_input_roles",
            tuple(sorted(self.allowed_input_roles, key=lambda item: item.value)),
        )
        object.__setattr__(
            self,
            "allowed_source_refs",
            _normalize_ref_tuple(
                self.allowed_source_refs,
                field="BindingRule.allowed_source_refs",
                nonempty=True,
            ),
        )
        object.__setattr__(
            self,
            "allowed_source_identities",
            _normalize_identity_tuple(
                self.allowed_source_identities,
                field="BindingRule.allowed_source_identities",
                nonempty=True,
            ),
        )
        _require_token(self.input_semantic_type, field="BindingRule.input_semantic_type")
        if self.input_semantic_type != self.symbolic_reference.semantic_type:
            raise ValidationError(
                "BindingRule.input_semantic_type must match SymbolicReference.semantic_type"
            )
        _require_text(
            self.required_selection_scope,
            field="BindingRule.required_selection_scope",
        )
        if self.required_selection_scope != self.symbolic_reference.selection_scope:
            raise ValidationError(
                "BindingRule.required_selection_scope must match SymbolicReference.selection_scope"
            )
        if type(self.constraints) is not tuple:
            raise ValidationError("BindingRule.constraints must be a tuple")
        if not all(type(item) is BindingConstraint for item in self.constraints):
            raise ValidationError("BindingRule.constraints must contain BindingConstraint values")
        names = [item.attribute_name for item in self.constraints]
        if len(set(names)) != len(names):
            raise ValidationError("BindingRule.constraints must not target the same attribute twice")
        object.__setattr__(
            self,
            "constraints",
            tuple(
                sorted(
                    self.constraints,
                    key=lambda item: (
                        item.attribute_name,
                        item.operator.value,
                        item.expected_kind.value,
                        item.expected_value,
                    ),
                )
            ),
        )
        if type(self.selection_policy) is not BindingSelectionPolicy:
            raise ValidationError("BindingRule.selection_policy must be a BindingSelectionPolicy")
        object.__setattr__(
            self,
            "required_temporal_basis_refs",
            _normalize_identity_tuple(
                self.required_temporal_basis_refs,
                field="BindingRule.required_temporal_basis_refs",
            ),
        )
        object.__setattr__(
            self,
            "required_completeness_refs",
            _normalize_identity_tuple(
                self.required_completeness_refs,
                field="BindingRule.required_completeness_refs",
            ),
        )
        object.__setattr__(
            self,
            "required_evidence_refs",
            _normalize_identity_tuple(
                self.required_evidence_refs,
                field="BindingRule.required_evidence_refs",
            ),
        )
        _require_text(self.description, field="BindingRule.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "allowed_input_roles": [role.value for role in self.allowed_input_roles],
            "allowed_source_identities": [
                identity.to_primitive() for identity in self.allowed_source_identities
            ],
            "allowed_source_refs": [ref.to_primitive() for ref in self.allowed_source_refs],
            "constraints": [constraint.to_primitive() for constraint in self.constraints],
            "description": self.description,
            "input_semantic_type": self.input_semantic_type,
            "required_completeness_refs": [
                identity.to_primitive() for identity in self.required_completeness_refs
            ],
            "required_evidence_refs": [
                identity.to_primitive() for identity in self.required_evidence_refs
            ],
            "required_selection_scope": self.required_selection_scope,
            "required_temporal_basis_refs": [
                identity.to_primitive() for identity in self.required_temporal_basis_refs
            ],
            "resolved_intent_identity": self.resolved_intent_identity.to_primitive(),
            "rule_ref": self.rule_ref.to_primitive(),
            "schema": self.SCHEMA,
            "selection_policy": self.selection_policy.to_primitive(),
            "symbolic_reference": self.symbolic_reference.to_primitive(),
        }

    @classmethod
    def from_primitive(cls, value: object) -> "BindingRule":
        obj = _expect_object(value, field="BindingRule")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "resolved_intent_identity",
                "rule_ref",
                "symbolic_reference",
                "allowed_input_roles",
                "allowed_source_refs",
                "allowed_source_identities",
                "input_semantic_type",
                "required_selection_scope",
                "constraints",
                "selection_policy",
                "required_temporal_basis_refs",
                "required_completeness_refs",
                "required_evidence_refs",
                "description",
            },
            field="BindingRule",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported BindingRule schema: {obj['schema']!r}")
        roles = _expect_array(obj["allowed_input_roles"], field="BindingRule.allowed_input_roles")
        source_refs = _expect_array(obj["allowed_source_refs"], field="BindingRule.allowed_source_refs")
        sources = _expect_array(
            obj["allowed_source_identities"], field="BindingRule.allowed_source_identities"
        )
        constraints = _expect_array(obj["constraints"], field="BindingRule.constraints")
        temporal = _expect_array(
            obj["required_temporal_basis_refs"], field="BindingRule.required_temporal_basis_refs"
        )
        completeness = _expect_array(
            obj["required_completeness_refs"], field="BindingRule.required_completeness_refs"
        )
        evidence = _expect_array(
            obj["required_evidence_refs"], field="BindingRule.required_evidence_refs"
        )
        try:
            parsed_roles = tuple(BindingInputRole(item) for item in roles)
        except (ValueError, TypeError) as exc:
            raise SerializationError("unsupported BindingRule.allowed_input_roles") from exc
        try:
            return cls(
                resolved_intent_identity=RecordIdentity.from_primitive(
                    obj["resolved_intent_identity"],
                    field="BindingRule.resolved_intent_identity",
                ),
                rule_ref=StableRef.from_primitive(obj["rule_ref"], field="BindingRule.rule_ref"),
                symbolic_reference=SymbolicReference.from_primitive(obj["symbolic_reference"]),
                allowed_input_roles=parsed_roles,
                allowed_source_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"BindingRule.allowed_source_refs[{index}]"
                    )
                    for index, item in enumerate(source_refs)
                ),
                allowed_source_identities=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"BindingRule.allowed_source_identities[{index}]"
                    )
                    for index, item in enumerate(sources)
                ),
                input_semantic_type=obj["input_semantic_type"],
                required_selection_scope=obj["required_selection_scope"],
                constraints=tuple(
                    BindingConstraint.from_primitive(
                        item, field=f"BindingRule.constraints[{index}]"
                    )
                    for index, item in enumerate(constraints)
                ),
                selection_policy=BindingSelectionPolicy.from_primitive(
                    obj["selection_policy"], field="BindingRule.selection_policy"
                ),
                required_temporal_basis_refs=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"BindingRule.required_temporal_basis_refs[{index}]"
                    )
                    for index, item in enumerate(temporal)
                ),
                required_completeness_refs=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"BindingRule.required_completeness_refs[{index}]"
                    )
                    for index, item in enumerate(completeness)
                ),
                required_evidence_refs=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"BindingRule.required_evidence_refs[{index}]"
                    )
                    for index, item in enumerate(evidence)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid BindingRule") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "BindingRule":
        return cls.from_primitive(parse_json_object(data))


def _normalize_binding_inputs(
    value: object, *, field: str, nonempty: bool = False
) -> tuple[BindingInput, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is BindingInput for item in value):
        raise ValidationError(f"{field} must contain BindingInput values")
    if nonempty and not value:
        raise ValidationError(f"{field} must not be empty")
    identities = [item.identity for item in value]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate input identities")
    return tuple(sorted(value, key=lambda item: str(item.identity)))


@dataclass(frozen=True, slots=True)
class _SelectionDecision:
    issue_kind: BindingIssueKind | None
    selected_input: BindingInput | None


def _compare_attribute(attribute: BindingAttribute) -> str | Fraction:
    if attribute.kind is BindingAttributeKind.TEXT:
        return attribute.value
    if attribute.kind is BindingAttributeKind.RFC3339_TIMESTAMP:
        return _parse_rfc3339(attribute.value, field=f"BindingAttribute[{attribute.name}]")
    raise AssertionError("unsupported BindingAttributeKind")


def _attribute_equals_constraint(
    attribute: BindingAttribute, constraint: BindingConstraint
) -> bool:
    if attribute.kind is BindingAttributeKind.TEXT:
        return attribute.value == constraint.expected_value
    if attribute.kind is BindingAttributeKind.RFC3339_TIMESTAMP:
        return _parse_rfc3339(
            attribute.value, field=f"BindingAttribute[{attribute.name}]"
        ) == _parse_rfc3339(
            constraint.expected_value,
            field=f"BindingConstraint[{constraint.attribute_name}].expected_value",
        )
    raise AssertionError("unsupported BindingAttributeKind")


def _structural_incompatibilities(
    rule: BindingRule, binding_inputs: tuple[BindingInput, ...]
) -> tuple[str, ...]:
    reasons: set[str] = set()
    for binding_input in binding_inputs:
        if binding_input.resolved_intent_identity != rule.resolved_intent_identity:
            reasons.add("foreign_resolved_intent")
        if binding_input.role not in rule.allowed_input_roles:
            reasons.add("unadmitted_input_role")
        if binding_input.attribution.source_ref not in rule.allowed_source_refs:
            reasons.add("unadmitted_source_ref")
        if binding_input.source_identity not in rule.allowed_source_identities:
            reasons.add("unadmitted_source_identity")
        if binding_input.semantic_type != rule.input_semantic_type:
            reasons.add("incompatible_semantic_type")
        if binding_input.selection_scope != rule.required_selection_scope:
            reasons.add("incompatible_selection_scope")
    return tuple(sorted(reasons))


def _missing_provenance(
    rule: BindingRule, binding_inputs: tuple[BindingInput, ...]
) -> tuple[str, ...]:
    reasons: set[str] = set()
    required_temporal = set(rule.required_temporal_basis_refs)
    required_completeness = set(rule.required_completeness_refs)
    required_evidence = set(rule.required_evidence_refs)
    for binding_input in binding_inputs:
        if not required_temporal.issubset(binding_input.temporal_basis_refs):
            reasons.add("missing_temporal_basis")
        if not required_completeness.issubset(binding_input.completeness_refs):
            reasons.add("missing_completeness")
        if not required_evidence.issubset(binding_input.evidence_refs):
            reasons.add("missing_evidence")
    return tuple(sorted(reasons))


def _apply_constraints(
    rule: BindingRule, binding_inputs: tuple[BindingInput, ...]
) -> tuple[BindingIssueKind | None, tuple[BindingInput, ...]]:
    missing_attributes = False
    wrong_kind_attributes = False
    compatible: list[BindingInput] = []

    for binding_input in binding_inputs:
        attributes = binding_input.attribute_map()
        excluded = False
        for constraint in rule.constraints:
            attribute = attributes.get(constraint.attribute_name)
            if attribute is None:
                missing_attributes = True
                continue
            if attribute.kind is not constraint.expected_kind:
                wrong_kind_attributes = True
                continue
            if constraint.operator is BindingConstraintOperator.EQUALS:
                if not _attribute_equals_constraint(attribute, constraint):
                    excluded = True
            else:
                raise AssertionError("unsupported BindingConstraintOperator")
        if not excluded:
            compatible.append(binding_input)

    if wrong_kind_attributes:
        return BindingIssueKind.INCOMPATIBLE_INPUT, ()
    if missing_attributes:
        return BindingIssueKind.MISSING_REQUIRED_DATA, ()
    return None, tuple(compatible)


def _determine_selection(
    rule: BindingRule, binding_inputs: tuple[BindingInput, ...]
) -> _SelectionDecision:
    if not binding_inputs:
        return _SelectionDecision(BindingIssueKind.ZERO_MATCHES, None)

    if _structural_incompatibilities(rule, binding_inputs):
        return _SelectionDecision(BindingIssueKind.INCOMPATIBLE_INPUT, None)

    if _missing_provenance(rule, binding_inputs):
        return _SelectionDecision(BindingIssueKind.MISSING_REQUIRED_DATA, None)

    constraint_issue, compatible = _apply_constraints(rule, binding_inputs)
    if constraint_issue is not None:
        return _SelectionDecision(constraint_issue, None)

    if not compatible:
        return _SelectionDecision(BindingIssueKind.ZERO_MATCHES, None)

    policy = rule.selection_policy
    if policy.mode is BindingSelectionMode.REQUIRE_UNIQUE:
        if len(compatible) != 1:
            return _SelectionDecision(BindingIssueKind.MULTIPLE_MATCHES, None)
        return _SelectionDecision(None, compatible[0])

    if policy.mode in (BindingSelectionMode.MAX_ATTRIBUTE, BindingSelectionMode.MIN_ATTRIBUTE):
        selector_name = policy.selector_attributes[0]
        selector_kind = policy.selector_kinds[0]
        missing_selector = False
        wrong_selector_kind = False
        ranked: list[tuple[str | Fraction, BindingInput]] = []

        for binding_input in compatible:
            attribute = binding_input.attribute_map().get(selector_name)
            if attribute is None:
                missing_selector = True
                continue
            if attribute.kind is not selector_kind:
                wrong_selector_kind = True
                continue
            ranked.append((_compare_attribute(attribute), binding_input))

        if wrong_selector_kind:
            return _SelectionDecision(BindingIssueKind.INCOMPATIBLE_INPUT, None)
        if missing_selector:
            return _SelectionDecision(BindingIssueKind.MISSING_REQUIRED_DATA, None)

        values = [item[0] for item in ranked]
        winning_value = (
            max(values)
            if policy.mode is BindingSelectionMode.MAX_ATTRIBUTE
            else min(values)
        )
        winners = [item[1] for item in ranked if item[0] == winning_value]
        if len(winners) != 1:
            return _SelectionDecision(BindingIssueKind.TIE, None)
        return _SelectionDecision(None, winners[0])

    if policy.mode is BindingSelectionMode.ANY_INTERCHANGEABLE:
        selected = min(compatible, key=lambda item: str(item.identity))
        return _SelectionDecision(None, selected)

    raise AssertionError("unsupported BindingSelectionMode")


@dataclass(frozen=True, slots=True)
class BoundValue(_CanonicalBindingRecord):
    SCHEMA: ClassVar[str] = "irr.bound_value.v1"

    binding_attribution: BindingAttribution
    rule: BindingRule
    binding_inputs: tuple[BindingInput, ...]
    selected_input_identity: RecordIdentity
    semantic_type: str
    value: str
    selection_scope: str
    value_scope: str

    def __post_init__(self) -> None:
        if type(self.binding_attribution) is not BindingAttribution:
            raise ValidationError("BoundValue.binding_attribution must be a BindingAttribution")
        if type(self.rule) is not BindingRule:
            raise ValidationError("BoundValue.rule must be a BindingRule")
        object.__setattr__(
            self,
            "binding_inputs",
            _normalize_binding_inputs(
                self.binding_inputs, field="BoundValue.binding_inputs", nonempty=True
            ),
        )
        if type(self.selected_input_identity) is not RecordIdentity:
            raise ValidationError("BoundValue.selected_input_identity must be a RecordIdentity")
        _require_token(self.semantic_type, field="BoundValue.semantic_type")
        _require_text(self.value, field="BoundValue.value")
        _require_text(self.selection_scope, field="BoundValue.selection_scope")
        _require_text(self.value_scope, field="BoundValue.value_scope")

        decision = _determine_selection(self.rule, self.binding_inputs)
        if decision.issue_kind is not None or decision.selected_input is None:
            raise ValidationError(
                "BoundValue cannot be constructed when the BindingRule is unresolved"
            )
        selected = decision.selected_input
        if selected.identity != self.selected_input_identity:
            raise ValidationError("BoundValue.selected_input_identity does not match rule evaluation")
        if self.semantic_type != self.rule.symbolic_reference.semantic_type:
            raise ValidationError("BoundValue.semantic_type must match the SymbolicReference")
        if self.semantic_type != selected.semantic_type:
            raise ValidationError("BoundValue.semantic_type must match the selected BindingInput")
        if self.value != selected.value:
            raise ValidationError("BoundValue.value must equal the selected BindingInput value")
        if self.selection_scope != self.rule.symbolic_reference.selection_scope:
            raise ValidationError("BoundValue.selection_scope must match the SymbolicReference")
        if self.selection_scope != selected.selection_scope:
            raise ValidationError("BoundValue.selection_scope must match the selected BindingInput")
        if self.value_scope != selected.value_scope:
            raise ValidationError("BoundValue.value_scope must equal the selected BindingInput value_scope")

    def to_primitive(self) -> dict[str, object]:
        return {
            "binding_attribution": self.binding_attribution.to_primitive(),
            "binding_inputs": [binding_input.to_primitive() for binding_input in self.binding_inputs],
            "rule": self.rule.to_primitive(),
            "schema": self.SCHEMA,
            "selected_input_identity": self.selected_input_identity.to_primitive(),
            "selection_scope": self.selection_scope,
            "semantic_type": self.semantic_type,
            "value": self.value,
            "value_scope": self.value_scope,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "BoundValue":
        obj = _expect_object(value, field="BoundValue")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "binding_attribution",
                "rule",
                "binding_inputs",
                "selected_input_identity",
                "semantic_type",
                "value",
                "selection_scope",
                "value_scope",
            },
            field="BoundValue",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported BoundValue schema: {obj['schema']!r}")
        inputs = _expect_array(obj["binding_inputs"], field="BoundValue.binding_inputs")
        try:
            return cls(
                binding_attribution=BindingAttribution.from_primitive(
                    obj["binding_attribution"], field="BoundValue.binding_attribution"
                ),
                rule=BindingRule.from_primitive(obj["rule"]),
                binding_inputs=tuple(BindingInput.from_primitive(item) for item in inputs),
                selected_input_identity=RecordIdentity.from_primitive(
                    obj["selected_input_identity"],
                    field="BoundValue.selected_input_identity",
                ),
                semantic_type=obj["semantic_type"],
                value=obj["value"],
                selection_scope=obj["selection_scope"],
                value_scope=obj["value_scope"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid BoundValue") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "BoundValue":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class BindingIssue(_CanonicalBindingRecord):
    SCHEMA: ClassVar[str] = "irr.binding_issue.v1"

    binding_attribution: BindingAttribution
    rule: BindingRule
    binding_inputs: tuple[BindingInput, ...]
    kind: BindingIssueKind
    selection_scope: str

    def __post_init__(self) -> None:
        if type(self.binding_attribution) is not BindingAttribution:
            raise ValidationError("BindingIssue.binding_attribution must be a BindingAttribution")
        if type(self.rule) is not BindingRule:
            raise ValidationError("BindingIssue.rule must be a BindingRule")
        object.__setattr__(
            self,
            "binding_inputs",
            _normalize_binding_inputs(self.binding_inputs, field="BindingIssue.binding_inputs"),
        )
        if type(self.kind) is not BindingIssueKind:
            raise ValidationError("BindingIssue.kind must be a BindingIssueKind")
        _require_text(self.selection_scope, field="BindingIssue.selection_scope")
        if self.selection_scope != self.rule.symbolic_reference.selection_scope:
            raise ValidationError(
                "BindingIssue.selection_scope must match the SymbolicReference selection scope"
            )
        decision = _determine_selection(self.rule, self.binding_inputs)
        if decision.issue_kind is not self.kind:
            raise ValidationError(
                "BindingIssue.kind does not match mechanical BindingRule evaluation"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "binding_attribution": self.binding_attribution.to_primitive(),
            "binding_inputs": [binding_input.to_primitive() for binding_input in self.binding_inputs],
            "kind": self.kind.value,
            "rule": self.rule.to_primitive(),
            "schema": self.SCHEMA,
            "selection_scope": self.selection_scope,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "BindingIssue":
        obj = _expect_object(value, field="BindingIssue")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "binding_attribution",
                "rule",
                "binding_inputs",
                "kind",
                "selection_scope",
            },
            field="BindingIssue",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported BindingIssue schema: {obj['schema']!r}")
        if type(obj["kind"]) is not str:
            raise SerializationError("BindingIssue.kind must be a string")
        try:
            kind = BindingIssueKind(obj["kind"])
        except ValueError as exc:
            raise SerializationError("unsupported BindingIssue.kind") from exc
        inputs = _expect_array(obj["binding_inputs"], field="BindingIssue.binding_inputs")
        try:
            return cls(
                binding_attribution=BindingAttribution.from_primitive(
                    obj["binding_attribution"], field="BindingIssue.binding_attribution"
                ),
                rule=BindingRule.from_primitive(obj["rule"]),
                binding_inputs=tuple(BindingInput.from_primitive(item) for item in inputs),
                kind=kind,
                selection_scope=obj["selection_scope"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid BindingIssue") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "BindingIssue":
        return cls.from_primitive(parse_json_object(data))


BindingEvaluation: TypeAlias = BoundValue | BindingIssue


def evaluate_binding(
    rule: BindingRule,
    binding_inputs: tuple[BindingInput, ...],
    *,
    attribution: BindingAttribution,
) -> BindingEvaluation:
    """Apply one already-admitted bounded BindingRule to supplied attributable BindingInput.

    Evaluation is phase-based over the complete normalized input set. It performs no
    retrieval, ambient lookup, external effect, fallback, semantic-rule mutation, or
    presentation-order-based diagnostic choice. An unresolved result is BindingIssue.
    """

    if type(rule) is not BindingRule:
        raise ValidationError("evaluate_binding.rule must be a BindingRule")
    if type(attribution) is not BindingAttribution:
        raise ValidationError("evaluate_binding.attribution must be a BindingAttribution")
    normalized_inputs = _normalize_binding_inputs(
        binding_inputs, field="evaluate_binding.binding_inputs"
    )
    decision = _determine_selection(rule, normalized_inputs)
    if decision.issue_kind is not None:
        return BindingIssue(
            binding_attribution=attribution,
            rule=rule,
            binding_inputs=normalized_inputs,
            kind=decision.issue_kind,
            selection_scope=rule.symbolic_reference.selection_scope,
        )
    selected = cast(BindingInput, decision.selected_input)
    return BoundValue(
        binding_attribution=attribution,
        rule=rule,
        binding_inputs=normalized_inputs,
        selected_input_identity=selected.identity,
        semantic_type=selected.semantic_type,
        value=selected.value,
        selection_scope=selected.selection_scope,
        value_scope=selected.value_scope,
    )
