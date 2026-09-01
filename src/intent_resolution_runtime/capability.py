from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, cast

from .canonical import canonical_json_bytes, parse_json_object
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef


_OPERATION_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")


def _reject_surrogates(value: str, *, field: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValidationError(f"{field} must contain only Unicode scalar values")


def _require_string(value: object, *, field: str) -> str:
    if type(value) is not str:
        raise ValidationError(f"{field} must be a string")
    _reject_surrogates(value, field=field)
    return value


def _require_text(value: object, *, field: str) -> str:
    value = _require_string(value, field=field)
    if not value.strip():
        raise ValidationError(f"{field} must contain non-whitespace text")
    return value


def _require_token(value: object, *, field: str) -> str:
    value = _require_string(value, field=field)
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if value != value.strip():
        raise ValidationError(f"{field} must not contain leading or trailing whitespace")
    return value


def _require_operation(value: object, *, field: str) -> str:
    value = _require_token(value, field=field)
    if _OPERATION_PATTERN.fullmatch(value) is None:
        raise ValidationError(
            f"{field} must be a lowercase dotted semantic operation identifier"
        )
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


def _stable_ref_key(value: StableRef) -> tuple[str, str]:
    return value.namespace, value.value


def _normalize_stable_refs(value: object, *, field: str) -> tuple[StableRef, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is StableRef for item in value):
        raise ValidationError(f"{field} must contain StableRef values")
    items = cast(tuple[StableRef, ...], value)
    if len(set(items)) != len(items):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(items, key=_stable_ref_key))


class _CanonicalCapabilityRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class CapabilityEffectRequirement(str, Enum):
    POSSIBLE = "possible"
    UNAVOIDABLE = "unavoidable"


@dataclass(frozen=True, slots=True)
class CapabilityCatalogAttribution(_CanonicalCapabilityRecord):
    SCHEMA: ClassVar[str] = "irr.capability_catalog_attribution.v1"

    supplier_ref: StableRef
    snapshot_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.supplier_ref) is not StableRef:
            raise ValidationError(
                "CapabilityCatalogAttribution.supplier_ref must be a StableRef"
            )
        if type(self.snapshot_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityCatalogAttribution.snapshot_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "schema": self.SCHEMA,
            "snapshot_event_ref": self.snapshot_event_ref.to_primitive(),
            "supplier_ref": self.supplier_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityCatalogAttribution"
    ) -> "CapabilityCatalogAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "supplier_ref", "snapshot_event_ref"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                supplier_ref=StableRef.from_primitive(
                    obj["supplier_ref"], field=f"{field}.supplier_ref"
                ),
                snapshot_event_ref=StableRef.from_primitive(
                    obj["snapshot_event_ref"], field=f"{field}.snapshot_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityCatalogAttribution":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityScopeRequirement(_CanonicalCapabilityRecord):
    SCHEMA: ClassVar[str] = "irr.capability_scope_requirement.v1"

    requirement_ref: StableRef
    semantic_type: str
    statement: str

    def __post_init__(self) -> None:
        if type(self.requirement_ref) is not StableRef:
            raise ValidationError(
                "CapabilityScopeRequirement.requirement_ref must be a StableRef"
            )
        _require_token(
            self.semantic_type, field="CapabilityScopeRequirement.semantic_type"
        )
        _require_text(self.statement, field="CapabilityScopeRequirement.statement")

    def to_primitive(self) -> dict[str, object]:
        return {
            "requirement_ref": self.requirement_ref.to_primitive(),
            "schema": self.SCHEMA,
            "semantic_type": self.semantic_type,
            "statement": self.statement,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityScopeRequirement"
    ) -> "CapabilityScopeRequirement":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "requirement_ref", "semantic_type", "statement"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                requirement_ref=StableRef.from_primitive(
                    obj["requirement_ref"], field=f"{field}.requirement_ref"
                ),
                semantic_type=obj["semantic_type"],
                statement=obj["statement"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityScopeRequirement":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityInputContract(_CanonicalCapabilityRecord):
    SCHEMA: ClassVar[str] = "irr.capability_input_contract.v1"

    input_ref: StableRef
    semantic_type: str
    scope_requirement_refs: tuple[StableRef, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.input_ref) is not StableRef:
            raise ValidationError("CapabilityInputContract.input_ref must be a StableRef")
        _require_token(self.semantic_type, field="CapabilityInputContract.semantic_type")
        object.__setattr__(
            self,
            "scope_requirement_refs",
            _normalize_stable_refs(
                self.scope_requirement_refs,
                field="CapabilityInputContract.scope_requirement_refs",
            ),
        )
        _require_text(self.description, field="CapabilityInputContract.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "input_ref": self.input_ref.to_primitive(),
            "schema": self.SCHEMA,
            "scope_requirement_refs": [
                item.to_primitive() for item in self.scope_requirement_refs
            ],
            "semantic_type": self.semantic_type,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityInputContract"
    ) -> "CapabilityInputContract":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "input_ref",
                "semantic_type",
                "scope_requirement_refs",
                "description",
            },
            field=field,
        )
        refs = _expect_array(
            obj["scope_requirement_refs"], field=f"{field}.scope_requirement_refs"
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                input_ref=StableRef.from_primitive(
                    obj["input_ref"], field=f"{field}.input_ref"
                ),
                semantic_type=obj["semantic_type"],
                scope_requirement_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.scope_requirement_refs[{index}]"
                    )
                    for index, item in enumerate(refs)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityInputContract":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityOutputContract(_CanonicalCapabilityRecord):
    SCHEMA: ClassVar[str] = "irr.capability_output_contract.v1"

    output_ref: StableRef
    semantic_type: str
    description: str

    def __post_init__(self) -> None:
        if type(self.output_ref) is not StableRef:
            raise ValidationError("CapabilityOutputContract.output_ref must be a StableRef")
        _require_token(self.semantic_type, field="CapabilityOutputContract.semantic_type")
        _require_text(self.description, field="CapabilityOutputContract.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "output_ref": self.output_ref.to_primitive(),
            "schema": self.SCHEMA,
            "semantic_type": self.semantic_type,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityOutputContract"
    ) -> "CapabilityOutputContract":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "output_ref", "semantic_type", "description"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                output_ref=StableRef.from_primitive(
                    obj["output_ref"], field=f"{field}.output_ref"
                ),
                semantic_type=obj["semantic_type"],
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityOutputContract":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityEffect(_CanonicalCapabilityRecord):
    SCHEMA: ClassVar[str] = "irr.capability_effect.v1"

    effect_ref: StableRef
    semantic_type: str
    requirement: CapabilityEffectRequirement
    scope_requirement_refs: tuple[StableRef, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.effect_ref) is not StableRef:
            raise ValidationError("CapabilityEffect.effect_ref must be a StableRef")
        _require_token(self.semantic_type, field="CapabilityEffect.semantic_type")
        if type(self.requirement) is not CapabilityEffectRequirement:
            raise ValidationError(
                "CapabilityEffect.requirement must be a CapabilityEffectRequirement"
            )
        object.__setattr__(
            self,
            "scope_requirement_refs",
            _normalize_stable_refs(
                self.scope_requirement_refs,
                field="CapabilityEffect.scope_requirement_refs",
            ),
        )
        _require_text(self.description, field="CapabilityEffect.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "effect_ref": self.effect_ref.to_primitive(),
            "requirement": self.requirement.value,
            "schema": self.SCHEMA,
            "scope_requirement_refs": [
                item.to_primitive() for item in self.scope_requirement_refs
            ],
            "semantic_type": self.semantic_type,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityEffect"
    ) -> "CapabilityEffect":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "effect_ref",
                "semantic_type",
                "requirement",
                "scope_requirement_refs",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["requirement"]) is not str:
            raise SerializationError(f"{field}.requirement must be a string")
        try:
            requirement = CapabilityEffectRequirement(obj["requirement"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.requirement") from exc
        refs = _expect_array(
            obj["scope_requirement_refs"], field=f"{field}.scope_requirement_refs"
        )
        try:
            return cls(
                effect_ref=StableRef.from_primitive(
                    obj["effect_ref"], field=f"{field}.effect_ref"
                ),
                semantic_type=obj["semantic_type"],
                requirement=requirement,
                scope_requirement_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.scope_requirement_refs[{index}]"
                    )
                    for index, item in enumerate(refs)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityEffect":
        return cls.from_primitive(parse_json_object(data))


def _normalize_scope_requirements(
    value: object, *, field: str
) -> tuple[CapabilityScopeRequirement, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityScopeRequirement for item in value):
        raise ValidationError(f"{field} must contain CapabilityScopeRequirement values")
    items = cast(tuple[CapabilityScopeRequirement, ...], value)
    refs = [item.requirement_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(
            f"{field} must not contain duplicate requirement_ref values"
        )
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.requirement_ref)))


def _normalize_input_contracts(
    value: object, *, field: str
) -> tuple[CapabilityInputContract, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityInputContract for item in value):
        raise ValidationError(f"{field} must contain CapabilityInputContract values")
    items = cast(tuple[CapabilityInputContract, ...], value)
    refs = [item.input_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate input_ref values")
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.input_ref)))


def _normalize_output_contracts(
    value: object, *, field: str
) -> tuple[CapabilityOutputContract, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityOutputContract for item in value):
        raise ValidationError(f"{field} must contain CapabilityOutputContract values")
    items = cast(tuple[CapabilityOutputContract, ...], value)
    refs = [item.output_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate output_ref values")
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.output_ref)))


def _normalize_effects(value: object, *, field: str) -> tuple[CapabilityEffect, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityEffect for item in value):
        raise ValidationError(f"{field} must contain CapabilityEffect values")
    items = cast(tuple[CapabilityEffect, ...], value)
    refs = [item.effect_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate effect_ref values")
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.effect_ref)))


@dataclass(frozen=True, slots=True)
class CapabilityDescriptor(_CanonicalCapabilityRecord):
    SCHEMA: ClassVar[str] = "irr.capability_descriptor.v1"

    capability_ref: StableRef
    operation: str
    input_contracts: tuple[CapabilityInputContract, ...]
    output_contracts: tuple[CapabilityOutputContract, ...]
    scope_requirements: tuple[CapabilityScopeRequirement, ...]
    effects: tuple[CapabilityEffect, ...]
    execution_boundary_refs: tuple[StableRef, ...]
    completion_contract: str
    description: str

    def __post_init__(self) -> None:
        if type(self.capability_ref) is not StableRef:
            raise ValidationError("CapabilityDescriptor.capability_ref must be a StableRef")
        _require_operation(self.operation, field="CapabilityDescriptor.operation")

        scope_requirements = _normalize_scope_requirements(
            self.scope_requirements, field="CapabilityDescriptor.scope_requirements"
        )
        object.__setattr__(self, "scope_requirements", scope_requirements)
        scope_refs = {item.requirement_ref for item in scope_requirements}

        input_contracts = _normalize_input_contracts(
            self.input_contracts, field="CapabilityDescriptor.input_contracts"
        )
        if any(
            ref not in scope_refs
            for item in input_contracts
            for ref in item.scope_requirement_refs
        ):
            raise ValidationError(
                "CapabilityDescriptor input contracts must reference admitted scope requirements"
            )
        object.__setattr__(self, "input_contracts", input_contracts)

        object.__setattr__(
            self,
            "output_contracts",
            _normalize_output_contracts(
                self.output_contracts, field="CapabilityDescriptor.output_contracts"
            ),
        )

        effects = _normalize_effects(self.effects, field="CapabilityDescriptor.effects")
        if any(
            ref not in scope_refs
            for item in effects
            for ref in item.scope_requirement_refs
        ):
            raise ValidationError(
                "CapabilityDescriptor effects must reference admitted scope requirements"
            )
        object.__setattr__(self, "effects", effects)

        object.__setattr__(
            self,
            "execution_boundary_refs",
            _normalize_stable_refs(
                self.execution_boundary_refs,
                field="CapabilityDescriptor.execution_boundary_refs",
            ),
        )
        _require_text(
            self.completion_contract, field="CapabilityDescriptor.completion_contract"
        )
        _require_text(self.description, field="CapabilityDescriptor.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "capability_ref": self.capability_ref.to_primitive(),
            "completion_contract": self.completion_contract,
            "description": self.description,
            "effects": [item.to_primitive() for item in self.effects],
            "execution_boundary_refs": [
                item.to_primitive() for item in self.execution_boundary_refs
            ],
            "input_contracts": [item.to_primitive() for item in self.input_contracts],
            "operation": self.operation,
            "output_contracts": [item.to_primitive() for item in self.output_contracts],
            "schema": self.SCHEMA,
            "scope_requirements": [
                item.to_primitive() for item in self.scope_requirements
            ],
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityDescriptor"
    ) -> "CapabilityDescriptor":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "capability_ref",
                "operation",
                "input_contracts",
                "output_contracts",
                "scope_requirements",
                "effects",
                "execution_boundary_refs",
                "completion_contract",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        inputs = _expect_array(obj["input_contracts"], field=f"{field}.input_contracts")
        outputs = _expect_array(
            obj["output_contracts"], field=f"{field}.output_contracts"
        )
        scopes = _expect_array(
            obj["scope_requirements"], field=f"{field}.scope_requirements"
        )
        effects = _expect_array(obj["effects"], field=f"{field}.effects")
        boundaries = _expect_array(
            obj["execution_boundary_refs"],
            field=f"{field}.execution_boundary_refs",
        )
        try:
            return cls(
                capability_ref=StableRef.from_primitive(
                    obj["capability_ref"], field=f"{field}.capability_ref"
                ),
                operation=obj["operation"],
                input_contracts=tuple(
                    CapabilityInputContract.from_primitive(
                        item, field=f"{field}.input_contracts[{index}]"
                    )
                    for index, item in enumerate(inputs)
                ),
                output_contracts=tuple(
                    CapabilityOutputContract.from_primitive(
                        item, field=f"{field}.output_contracts[{index}]"
                    )
                    for index, item in enumerate(outputs)
                ),
                scope_requirements=tuple(
                    CapabilityScopeRequirement.from_primitive(
                        item, field=f"{field}.scope_requirements[{index}]"
                    )
                    for index, item in enumerate(scopes)
                ),
                effects=tuple(
                    CapabilityEffect.from_primitive(
                        item, field=f"{field}.effects[{index}]"
                    )
                    for index, item in enumerate(effects)
                ),
                execution_boundary_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.execution_boundary_refs[{index}]"
                    )
                    for index, item in enumerate(boundaries)
                ),
                completion_contract=obj["completion_contract"],
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityDescriptor":
        return cls.from_primitive(parse_json_object(data))


def _normalize_descriptors(
    value: object, *, field: str
) -> tuple[CapabilityDescriptor, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityDescriptor for item in value):
        raise ValidationError(f"{field} must contain CapabilityDescriptor values")
    items = cast(tuple[CapabilityDescriptor, ...], value)
    refs = [item.capability_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate capability_ref values")
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.capability_ref)))


@dataclass(frozen=True, slots=True)
class CapabilityCatalogSnapshot(_CanonicalCapabilityRecord):
    SCHEMA: ClassVar[str] = "irr.capability_catalog_snapshot.v1"

    catalog_ref: StableRef
    attribution: CapabilityCatalogAttribution
    scope_statement: str
    descriptors: tuple[CapabilityDescriptor, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.catalog_ref) is not StableRef:
            raise ValidationError(
                "CapabilityCatalogSnapshot.catalog_ref must be a StableRef"
            )
        if type(self.attribution) is not CapabilityCatalogAttribution:
            raise ValidationError(
                "CapabilityCatalogSnapshot.attribution must be a CapabilityCatalogAttribution"
            )
        _require_text(
            self.scope_statement, field="CapabilityCatalogSnapshot.scope_statement"
        )
        object.__setattr__(
            self,
            "descriptors",
            _normalize_descriptors(
                self.descriptors, field="CapabilityCatalogSnapshot.descriptors"
            ),
        )
        _require_text(self.description, field="CapabilityCatalogSnapshot.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "catalog_ref": self.catalog_ref.to_primitive(),
            "description": self.description,
            "descriptors": [item.to_primitive() for item in self.descriptors],
            "schema": self.SCHEMA,
            "scope_statement": self.scope_statement,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityCatalogSnapshot"
    ) -> "CapabilityCatalogSnapshot":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "catalog_ref",
                "attribution",
                "scope_statement",
                "descriptors",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        descriptors = _expect_array(obj["descriptors"], field=f"{field}.descriptors")
        try:
            return cls(
                catalog_ref=StableRef.from_primitive(
                    obj["catalog_ref"], field=f"{field}.catalog_ref"
                ),
                attribution=CapabilityCatalogAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                scope_statement=obj["scope_statement"],
                descriptors=tuple(
                    CapabilityDescriptor.from_primitive(
                        item, field=f"{field}.descriptors[{index}]"
                    )
                    for index, item in enumerate(descriptors)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityCatalogSnapshot":
        return cls.from_primitive(parse_json_object(data))
