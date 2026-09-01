from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, cast

from .canonical import canonical_json_bytes, parse_json_object
from .capability import (
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffectRequirement,
    CapabilityExecutionBoundaryKind,
)
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef
from .work import WorkInput, WorkLiteralInput, WorkOutput, WorkPlan, WorkStep, WorkSymbolicInput


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


class _CanonicalCapabilityMatchRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class CapabilityRequestedScope(_CanonicalCapabilityMatchRecord):
    SCHEMA: ClassVar[str] = "irr.capability_requested_scope.v1"

    scope_ref: StableRef
    semantic_type: str
    value: str
    description: str

    def __post_init__(self) -> None:
        if type(self.scope_ref) is not StableRef:
            raise ValidationError("CapabilityRequestedScope.scope_ref must be a StableRef")
        _require_token(self.semantic_type, field="CapabilityRequestedScope.semantic_type")
        _require_text(self.value, field="CapabilityRequestedScope.value")
        _require_text(self.description, field="CapabilityRequestedScope.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "schema": self.SCHEMA,
            "scope_ref": self.scope_ref.to_primitive(),
            "semantic_type": self.semantic_type,
            "value": self.value,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityRequestedScope"
    ) -> "CapabilityRequestedScope":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "scope_ref", "semantic_type", "value", "description"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                scope_ref=StableRef.from_primitive(
                    obj["scope_ref"], field=f"{field}.scope_ref"
                ),
                semantic_type=obj["semantic_type"],
                value=obj["value"],
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityRequestedScope":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityRequestedEffect(_CanonicalCapabilityMatchRecord):
    SCHEMA: ClassVar[str] = "irr.capability_requested_effect.v1"

    effect_ref: StableRef
    semantic_type: str
    requested_scope_refs: tuple[StableRef, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.effect_ref) is not StableRef:
            raise ValidationError("CapabilityRequestedEffect.effect_ref must be a StableRef")
        _require_token(self.semantic_type, field="CapabilityRequestedEffect.semantic_type")
        if type(self.requested_scope_refs) is not tuple:
            raise ValidationError(
                "CapabilityRequestedEffect.requested_scope_refs must be a tuple"
            )
        if not all(type(item) is StableRef for item in self.requested_scope_refs):
            raise ValidationError(
                "CapabilityRequestedEffect.requested_scope_refs must contain StableRef values"
            )
        if len(set(self.requested_scope_refs)) != len(self.requested_scope_refs):
            raise ValidationError(
                "CapabilityRequestedEffect.requested_scope_refs must not contain duplicates"
            )
        object.__setattr__(
            self,
            "requested_scope_refs",
            tuple(sorted(self.requested_scope_refs, key=_stable_ref_key)),
        )
        _require_text(self.description, field="CapabilityRequestedEffect.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "effect_ref": self.effect_ref.to_primitive(),
            "requested_scope_refs": [
                item.to_primitive() for item in self.requested_scope_refs
            ],
            "schema": self.SCHEMA,
            "semantic_type": self.semantic_type,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityRequestedEffect"
    ) -> "CapabilityRequestedEffect":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "effect_ref",
                "semantic_type",
                "requested_scope_refs",
                "description",
            },
            field=field,
        )
        refs = _expect_array(
            obj["requested_scope_refs"], field=f"{field}.requested_scope_refs"
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                effect_ref=StableRef.from_primitive(
                    obj["effect_ref"], field=f"{field}.effect_ref"
                ),
                semantic_type=obj["semantic_type"],
                requested_scope_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.requested_scope_refs[{index}]"
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
    ) -> "CapabilityRequestedEffect":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityExecutionBoundaryRequirement(_CanonicalCapabilityMatchRecord):
    SCHEMA: ClassVar[str] = "irr.capability_execution_boundary_requirement.v1"

    kind: CapabilityExecutionBoundaryKind
    boundary_ref: StableRef
    description: str

    def __post_init__(self) -> None:
        if type(self.kind) is not CapabilityExecutionBoundaryKind:
            raise ValidationError(
                "CapabilityExecutionBoundaryRequirement.kind must be a "
                "CapabilityExecutionBoundaryKind"
            )
        if type(self.boundary_ref) is not StableRef:
            raise ValidationError(
                "CapabilityExecutionBoundaryRequirement.boundary_ref must be a StableRef"
            )
        _require_text(
            self.description,
            field="CapabilityExecutionBoundaryRequirement.description",
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "boundary_ref": self.boundary_ref.to_primitive(),
            "description": self.description,
            "kind": self.kind.value,
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "CapabilityExecutionBoundaryRequirement",
    ) -> "CapabilityExecutionBoundaryRequirement":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "kind", "boundary_ref", "description"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["kind"]) is not str:
            raise SerializationError(f"{field}.kind must be a string")
        try:
            kind = CapabilityExecutionBoundaryKind(obj["kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.kind") from exc
        try:
            return cls(
                kind=kind,
                boundary_ref=StableRef.from_primitive(
                    obj["boundary_ref"], field=f"{field}.boundary_ref"
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityExecutionBoundaryRequirement":
        return cls.from_primitive(parse_json_object(data))


def _normalize_requested_scopes(
    value: object, *, field: str
) -> tuple[CapabilityRequestedScope, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if not all(type(item) is CapabilityRequestedScope for item in value):
        raise ValidationError(f"{field} must contain CapabilityRequestedScope values")
    items = cast(tuple[CapabilityRequestedScope, ...], value)
    refs = [item.scope_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate scope_ref values")
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.scope_ref)))


def _normalize_requested_effects(
    value: object, *, field: str
) -> tuple[CapabilityRequestedEffect, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityRequestedEffect for item in value):
        raise ValidationError(f"{field} must contain CapabilityRequestedEffect values")
    items = cast(tuple[CapabilityRequestedEffect, ...], value)
    refs = [item.effect_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate effect_ref values")
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.effect_ref)))


def _normalize_boundary_requirements(
    value: object, *, field: str
) -> tuple[CapabilityExecutionBoundaryRequirement, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(
        type(item) is CapabilityExecutionBoundaryRequirement for item in value
    ):
        raise ValidationError(
            f"{field} must contain CapabilityExecutionBoundaryRequirement values"
        )
    items = cast(tuple[CapabilityExecutionBoundaryRequirement, ...], value)
    keys = [(item.kind.value, item.boundary_ref) for item in items]
    if len(set(keys)) != len(keys):
        raise ValidationError(
            f"{field} must not contain duplicate kind/boundary_ref pairs"
        )
    return tuple(
        sorted(
            items,
            key=lambda item: (item.kind.value, *_stable_ref_key(item.boundary_ref)),
        )
    )


@dataclass(frozen=True, slots=True)
class CapabilityRequirement(_CanonicalCapabilityMatchRecord):
    SCHEMA: ClassVar[str] = "irr.capability_requirement.v1"

    work_plan: WorkPlan
    step_ref: StableRef
    primary_scope_ref: StableRef
    requested_scopes: tuple[CapabilityRequestedScope, ...]
    requested_effects: tuple[CapabilityRequestedEffect, ...]
    execution_boundary_requirements: tuple[
        CapabilityExecutionBoundaryRequirement, ...
    ]
    description: str

    def __post_init__(self) -> None:
        if type(self.work_plan) is not WorkPlan:
            raise ValidationError("CapabilityRequirement.work_plan must be a WorkPlan")
        if type(self.step_ref) is not StableRef:
            raise ValidationError("CapabilityRequirement.step_ref must be a StableRef")
        if type(self.primary_scope_ref) is not StableRef:
            raise ValidationError(
                "CapabilityRequirement.primary_scope_ref must be a StableRef"
            )

        step_map = {step.step_ref: step for step in self.work_plan.steps}
        if self.step_ref not in step_map:
            raise ValidationError(
                "CapabilityRequirement.step_ref must identify a step in the exact WorkPlan"
            )

        requested_scopes = _normalize_requested_scopes(
            self.requested_scopes, field="CapabilityRequirement.requested_scopes"
        )
        object.__setattr__(self, "requested_scopes", requested_scopes)
        scope_map = {item.scope_ref: item for item in requested_scopes}
        if self.primary_scope_ref not in scope_map:
            raise ValidationError(
                "CapabilityRequirement.primary_scope_ref must reference an admitted requested scope"
            )
        if scope_map[self.primary_scope_ref].value != step_map[self.step_ref].scope:
            raise ValidationError(
                "CapabilityRequirement primary requested scope must equal the WorkStep scope"
            )

        requested_effects = _normalize_requested_effects(
            self.requested_effects, field="CapabilityRequirement.requested_effects"
        )
        if any(
            ref not in scope_map
            for effect in requested_effects
            for ref in effect.requested_scope_refs
        ):
            raise ValidationError(
                "CapabilityRequirement requested effects must reference admitted requested scopes"
            )
        object.__setattr__(self, "requested_effects", requested_effects)

        object.__setattr__(
            self,
            "execution_boundary_requirements",
            _normalize_boundary_requirements(
                self.execution_boundary_requirements,
                field="CapabilityRequirement.execution_boundary_requirements",
            ),
        )
        _require_text(self.description, field="CapabilityRequirement.description")

    @property
    def work_step(self) -> WorkStep:
        for step in self.work_plan.steps:
            if step.step_ref == self.step_ref:
                return step
        raise AssertionError("validated CapabilityRequirement lost its WorkStep")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "execution_boundary_requirements": [
                item.to_primitive() for item in self.execution_boundary_requirements
            ],
            "primary_scope_ref": self.primary_scope_ref.to_primitive(),
            "requested_effects": [
                item.to_primitive() for item in self.requested_effects
            ],
            "requested_scopes": [
                item.to_primitive() for item in self.requested_scopes
            ],
            "schema": self.SCHEMA,
            "step_ref": self.step_ref.to_primitive(),
            "work_plan": self.work_plan.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityRequirement"
    ) -> "CapabilityRequirement":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "work_plan",
                "step_ref",
                "primary_scope_ref",
                "requested_scopes",
                "requested_effects",
                "execution_boundary_requirements",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        scopes = _expect_array(
            obj["requested_scopes"], field=f"{field}.requested_scopes"
        )
        effects = _expect_array(
            obj["requested_effects"], field=f"{field}.requested_effects"
        )
        boundaries = _expect_array(
            obj["execution_boundary_requirements"],
            field=f"{field}.execution_boundary_requirements",
        )
        try:
            return cls(
                work_plan=WorkPlan.from_primitive(obj["work_plan"]),
                step_ref=StableRef.from_primitive(
                    obj["step_ref"], field=f"{field}.step_ref"
                ),
                primary_scope_ref=StableRef.from_primitive(
                    obj["primary_scope_ref"], field=f"{field}.primary_scope_ref"
                ),
                requested_scopes=tuple(
                    CapabilityRequestedScope.from_primitive(
                        item, field=f"{field}.requested_scopes[{index}]"
                    )
                    for index, item in enumerate(scopes)
                ),
                requested_effects=tuple(
                    CapabilityRequestedEffect.from_primitive(
                        item, field=f"{field}.requested_effects[{index}]"
                    )
                    for index, item in enumerate(effects)
                ),
                execution_boundary_requirements=tuple(
                    CapabilityExecutionBoundaryRequirement.from_primitive(
                        item,
                        field=f"{field}.execution_boundary_requirements[{index}]",
                    )
                    for index, item in enumerate(boundaries)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityRequirement":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityScopeMatch(_CanonicalCapabilityMatchRecord):
    SCHEMA: ClassVar[str] = "irr.capability_scope_match.v1"

    requested_scope_ref: StableRef
    descriptor_scope_requirement_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.requested_scope_ref) is not StableRef:
            raise ValidationError(
                "CapabilityScopeMatch.requested_scope_ref must be a StableRef"
            )
        if type(self.descriptor_scope_requirement_ref) is not StableRef:
            raise ValidationError(
                "CapabilityScopeMatch.descriptor_scope_requirement_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "descriptor_scope_requirement_ref": (
                self.descriptor_scope_requirement_ref.to_primitive()
            ),
            "requested_scope_ref": self.requested_scope_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityScopeMatch"
    ) -> "CapabilityScopeMatch":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "requested_scope_ref",
                "descriptor_scope_requirement_ref",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                requested_scope_ref=StableRef.from_primitive(
                    obj["requested_scope_ref"],
                    field=f"{field}.requested_scope_ref",
                ),
                descriptor_scope_requirement_ref=StableRef.from_primitive(
                    obj["descriptor_scope_requirement_ref"],
                    field=f"{field}.descriptor_scope_requirement_ref",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityScopeMatch":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityInputMatch(_CanonicalCapabilityMatchRecord):
    SCHEMA: ClassVar[str] = "irr.capability_input_match.v1"

    work_input_name: str
    descriptor_input_ref: StableRef
    requested_scope_refs: tuple[StableRef, ...]

    def __post_init__(self) -> None:
        _require_token(self.work_input_name, field="CapabilityInputMatch.work_input_name")
        if type(self.descriptor_input_ref) is not StableRef:
            raise ValidationError(
                "CapabilityInputMatch.descriptor_input_ref must be a StableRef"
            )
        if type(self.requested_scope_refs) is not tuple:
            raise ValidationError(
                "CapabilityInputMatch.requested_scope_refs must be a tuple"
            )
        if not all(type(item) is StableRef for item in self.requested_scope_refs):
            raise ValidationError(
                "CapabilityInputMatch.requested_scope_refs must contain StableRef values"
            )
        if len(set(self.requested_scope_refs)) != len(self.requested_scope_refs):
            raise ValidationError(
                "CapabilityInputMatch.requested_scope_refs must not contain duplicates"
            )
        object.__setattr__(
            self,
            "requested_scope_refs",
            tuple(sorted(self.requested_scope_refs, key=_stable_ref_key)),
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "descriptor_input_ref": self.descriptor_input_ref.to_primitive(),
            "requested_scope_refs": [
                item.to_primitive() for item in self.requested_scope_refs
            ],
            "schema": self.SCHEMA,
            "work_input_name": self.work_input_name,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityInputMatch"
    ) -> "CapabilityInputMatch":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "work_input_name",
                "descriptor_input_ref",
                "requested_scope_refs",
            },
            field=field,
        )
        refs = _expect_array(
            obj["requested_scope_refs"], field=f"{field}.requested_scope_refs"
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                work_input_name=obj["work_input_name"],
                descriptor_input_ref=StableRef.from_primitive(
                    obj["descriptor_input_ref"],
                    field=f"{field}.descriptor_input_ref",
                ),
                requested_scope_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.requested_scope_refs[{index}]"
                    )
                    for index, item in enumerate(refs)
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityInputMatch":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityOutputMatch(_CanonicalCapabilityMatchRecord):
    SCHEMA: ClassVar[str] = "irr.capability_output_match.v1"

    work_output_name: str
    descriptor_output_ref: StableRef
    requested_scope_refs: tuple[StableRef, ...]

    def __post_init__(self) -> None:
        _require_token(
            self.work_output_name, field="CapabilityOutputMatch.work_output_name"
        )
        if type(self.descriptor_output_ref) is not StableRef:
            raise ValidationError(
                "CapabilityOutputMatch.descriptor_output_ref must be a StableRef"
            )
        if type(self.requested_scope_refs) is not tuple:
            raise ValidationError(
                "CapabilityOutputMatch.requested_scope_refs must be a tuple"
            )
        if not all(type(item) is StableRef for item in self.requested_scope_refs):
            raise ValidationError(
                "CapabilityOutputMatch.requested_scope_refs must contain StableRef values"
            )
        if len(set(self.requested_scope_refs)) != len(self.requested_scope_refs):
            raise ValidationError(
                "CapabilityOutputMatch.requested_scope_refs must not contain duplicates"
            )
        object.__setattr__(
            self,
            "requested_scope_refs",
            tuple(sorted(self.requested_scope_refs, key=_stable_ref_key)),
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "descriptor_output_ref": self.descriptor_output_ref.to_primitive(),
            "requested_scope_refs": [
                item.to_primitive() for item in self.requested_scope_refs
            ],
            "schema": self.SCHEMA,
            "work_output_name": self.work_output_name,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityOutputMatch"
    ) -> "CapabilityOutputMatch":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "work_output_name",
                "descriptor_output_ref",
                "requested_scope_refs",
            },
            field=field,
        )
        refs = _expect_array(
            obj["requested_scope_refs"], field=f"{field}.requested_scope_refs"
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                work_output_name=obj["work_output_name"],
                descriptor_output_ref=StableRef.from_primitive(
                    obj["descriptor_output_ref"],
                    field=f"{field}.descriptor_output_ref",
                ),
                requested_scope_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.requested_scope_refs[{index}]"
                    )
                    for index, item in enumerate(refs)
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityOutputMatch":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityEffectMatch(_CanonicalCapabilityMatchRecord):
    SCHEMA: ClassVar[str] = "irr.capability_effect_match.v1"

    requested_effect_ref: StableRef
    descriptor_effect_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.requested_effect_ref) is not StableRef:
            raise ValidationError(
                "CapabilityEffectMatch.requested_effect_ref must be a StableRef"
            )
        if type(self.descriptor_effect_ref) is not StableRef:
            raise ValidationError(
                "CapabilityEffectMatch.descriptor_effect_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "descriptor_effect_ref": self.descriptor_effect_ref.to_primitive(),
            "requested_effect_ref": self.requested_effect_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityEffectMatch"
    ) -> "CapabilityEffectMatch":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "requested_effect_ref", "descriptor_effect_ref"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                requested_effect_ref=StableRef.from_primitive(
                    obj["requested_effect_ref"],
                    field=f"{field}.requested_effect_ref",
                ),
                descriptor_effect_ref=StableRef.from_primitive(
                    obj["descriptor_effect_ref"],
                    field=f"{field}.descriptor_effect_ref",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityEffectMatch":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityMatchAttribution(_CanonicalCapabilityMatchRecord):
    SCHEMA: ClassVar[str] = "irr.capability_match_attribution.v1"

    matcher_ref: StableRef
    match_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.matcher_ref) is not StableRef:
            raise ValidationError(
                "CapabilityMatchAttribution.matcher_ref must be a StableRef"
            )
        if type(self.match_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityMatchAttribution.match_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "match_event_ref": self.match_event_ref.to_primitive(),
            "matcher_ref": self.matcher_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityMatchAttribution"
    ) -> "CapabilityMatchAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "matcher_ref", "match_event_ref"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                matcher_ref=StableRef.from_primitive(
                    obj["matcher_ref"], field=f"{field}.matcher_ref"
                ),
                match_event_ref=StableRef.from_primitive(
                    obj["match_event_ref"], field=f"{field}.match_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityMatchAttribution":
        return cls.from_primitive(parse_json_object(data))


def _normalize_scope_matches(
    value: object, *, field: str
) -> tuple[CapabilityScopeMatch, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityScopeMatch for item in value):
        raise ValidationError(f"{field} must contain CapabilityScopeMatch values")
    items = cast(tuple[CapabilityScopeMatch, ...], value)
    requested = [item.requested_scope_ref for item in items]
    descriptor = [item.descriptor_scope_requirement_ref for item in items]
    if len(set(requested)) != len(requested):
        raise ValidationError(
            f"{field} must not map one requested scope more than once"
        )
    if len(set(descriptor)) != len(descriptor):
        raise ValidationError(
            f"{field} must not map one descriptor scope requirement more than once"
        )
    return tuple(
        sorted(items, key=lambda item: _stable_ref_key(item.requested_scope_ref))
    )


def _normalize_input_matches(
    value: object, *, field: str
) -> tuple[CapabilityInputMatch, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityInputMatch for item in value):
        raise ValidationError(f"{field} must contain CapabilityInputMatch values")
    items = cast(tuple[CapabilityInputMatch, ...], value)
    names = [item.work_input_name for item in items]
    refs = [item.descriptor_input_ref for item in items]
    if len(set(names)) != len(names):
        raise ValidationError(f"{field} must not map one WorkStep input more than once")
    if len(set(refs)) != len(refs):
        raise ValidationError(
            f"{field} must not map one descriptor input contract more than once"
        )
    return tuple(sorted(items, key=lambda item: item.work_input_name))


def _normalize_output_matches(
    value: object, *, field: str
) -> tuple[CapabilityOutputMatch, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityOutputMatch for item in value):
        raise ValidationError(f"{field} must contain CapabilityOutputMatch values")
    items = cast(tuple[CapabilityOutputMatch, ...], value)
    names = [item.work_output_name for item in items]
    refs = [item.descriptor_output_ref for item in items]
    if len(set(names)) != len(names):
        raise ValidationError(f"{field} must not map one WorkStep output more than once")
    if len(set(refs)) != len(refs):
        raise ValidationError(
            f"{field} must not map one descriptor output contract more than once"
        )
    return tuple(sorted(items, key=lambda item: item.work_output_name))


def _normalize_effect_matches(
    value: object, *, field: str
) -> tuple[CapabilityEffectMatch, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityEffectMatch for item in value):
        raise ValidationError(f"{field} must contain CapabilityEffectMatch values")
    items = cast(tuple[CapabilityEffectMatch, ...], value)
    requested = [item.requested_effect_ref for item in items]
    descriptor = [item.descriptor_effect_ref for item in items]
    if len(set(requested)) != len(requested):
        raise ValidationError(
            f"{field} must not map one requested effect more than once"
        )
    if len(set(descriptor)) != len(descriptor):
        raise ValidationError(
            f"{field} must not map one descriptor effect more than once"
        )
    return tuple(
        sorted(items, key=lambda item: _stable_ref_key(item.requested_effect_ref))
    )


def _work_input_semantic_type(value: WorkInput) -> str:
    if type(value) is WorkLiteralInput:
        return value.semantic_type
    if type(value) is WorkSymbolicInput:
        return value.reference.semantic_type
    raise AssertionError("validated WorkStep contains unsupported input type")


def _work_output_semantic_type(value: WorkOutput) -> str:
    return value.reference.semantic_type


@dataclass(frozen=True, slots=True)
class CapabilityMatch(_CanonicalCapabilityMatchRecord):
    SCHEMA: ClassVar[str] = "irr.capability_match.v1"

    attribution: CapabilityMatchAttribution
    requirement: CapabilityRequirement
    catalog_snapshot: CapabilityCatalogSnapshot
    capability_ref: StableRef
    capability_contract_identity: RecordIdentity
    scope_matches: tuple[CapabilityScopeMatch, ...]
    input_matches: tuple[CapabilityInputMatch, ...]
    output_matches: tuple[CapabilityOutputMatch, ...]
    effect_matches: tuple[CapabilityEffectMatch, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not CapabilityMatchAttribution:
            raise ValidationError(
                "CapabilityMatch.attribution must be a CapabilityMatchAttribution"
            )
        if type(self.requirement) is not CapabilityRequirement:
            raise ValidationError(
                "CapabilityMatch.requirement must be a CapabilityRequirement"
            )
        if type(self.catalog_snapshot) is not CapabilityCatalogSnapshot:
            raise ValidationError(
                "CapabilityMatch.catalog_snapshot must be a CapabilityCatalogSnapshot"
            )
        if type(self.capability_ref) is not StableRef:
            raise ValidationError("CapabilityMatch.capability_ref must be a StableRef")
        if type(self.capability_contract_identity) is not RecordIdentity:
            raise ValidationError(
                "CapabilityMatch.capability_contract_identity must be a RecordIdentity"
            )

        descriptors = {
            descriptor.capability_ref: descriptor
            for descriptor in self.catalog_snapshot.descriptors
        }
        if self.capability_ref not in descriptors:
            raise ValidationError(
                "CapabilityMatch capability_ref must belong to the exact Catalog Snapshot"
            )
        descriptor = descriptors[self.capability_ref]
        if descriptor.identity != self.capability_contract_identity:
            raise ValidationError(
                "CapabilityMatch capability_contract_identity must equal the exact "
                "Catalog descriptor identity"
            )

        step = self.requirement.work_step
        if descriptor.operation != step.operation:
            raise ValidationError(
                "CapabilityMatch descriptor operation must exactly equal WorkStep operation in v1"
            )
        if descriptor.completion_contract != step.completion_contract:
            raise ValidationError(
                "CapabilityMatch completion contract must be lexically exact in v1"
            )

        requested_scopes = {
            item.scope_ref: item for item in self.requirement.requested_scopes
        }
        descriptor_scopes = {
            item.requirement_ref: item for item in descriptor.scope_requirements
        }
        scope_matches = _normalize_scope_matches(
            self.scope_matches, field="CapabilityMatch.scope_matches"
        )
        if {item.requested_scope_ref for item in scope_matches} != set(
            requested_scopes
        ):
            raise ValidationError(
                "CapabilityMatch must map every requested scope exactly once"
            )
        if {item.descriptor_scope_requirement_ref for item in scope_matches} != set(
            descriptor_scopes
        ):
            raise ValidationError(
                "CapabilityMatch must satisfy every descriptor scope requirement exactly once"
            )
        for match in scope_matches:
            if (
                requested_scopes[match.requested_scope_ref].semantic_type
                != descriptor_scopes[
                    match.descriptor_scope_requirement_ref
                ].semantic_type
            ):
                raise ValidationError(
                    "CapabilityMatch scope semantic types must match exactly in v1"
                )
        object.__setattr__(self, "scope_matches", scope_matches)
        requested_to_descriptor_scope = {
            item.requested_scope_ref: item.descriptor_scope_requirement_ref
            for item in scope_matches
        }

        work_inputs = {item.name: item for item in step.inputs}
        descriptor_inputs = {item.input_ref: item for item in descriptor.input_contracts}
        input_matches = _normalize_input_matches(
            self.input_matches, field="CapabilityMatch.input_matches"
        )
        if {item.work_input_name for item in input_matches} != set(work_inputs):
            raise ValidationError(
                "CapabilityMatch must map every WorkStep input exactly once"
            )
        if {item.descriptor_input_ref for item in input_matches} != set(
            descriptor_inputs
        ):
            raise ValidationError(
                "CapabilityMatch must satisfy every descriptor input contract exactly once"
            )
        for match in input_matches:
            work_input = work_inputs[match.work_input_name]
            descriptor_input = descriptor_inputs[match.descriptor_input_ref]
            if _work_input_semantic_type(work_input) != descriptor_input.semantic_type:
                raise ValidationError(
                    "CapabilityMatch input semantic types must match exactly in v1"
                )
            if any(ref not in requested_scopes for ref in match.requested_scope_refs):
                raise ValidationError(
                    "CapabilityMatch input mapping must reference admitted requested scopes"
                )
            mapped_descriptor_scopes = {
                requested_to_descriptor_scope[ref]
                for ref in match.requested_scope_refs
            }
            if mapped_descriptor_scopes != set(
                descriptor_input.scope_requirement_refs
            ):
                raise ValidationError(
                    "CapabilityMatch input scope mapping must exactly cover the "
                    "descriptor input scope requirements"
                )
        object.__setattr__(self, "input_matches", input_matches)

        work_outputs = {item.name: item for item in step.outputs}
        descriptor_outputs = {
            item.output_ref: item for item in descriptor.output_contracts
        }
        output_matches = _normalize_output_matches(
            self.output_matches, field="CapabilityMatch.output_matches"
        )
        if {item.work_output_name for item in output_matches} != set(work_outputs):
            raise ValidationError(
                "CapabilityMatch must map every WorkStep output exactly once"
            )
        if any(
            item.descriptor_output_ref not in descriptor_outputs
            for item in output_matches
        ):
            raise ValidationError(
                "CapabilityMatch output mapping must reference descriptor output contracts"
            )
        for match in output_matches:
            work_output = work_outputs[match.work_output_name]
            descriptor_output = descriptor_outputs[match.descriptor_output_ref]
            if _work_output_semantic_type(work_output) != descriptor_output.semantic_type:
                raise ValidationError(
                    "CapabilityMatch output semantic types must match exactly in v1"
                )
            if any(ref not in requested_scopes for ref in match.requested_scope_refs):
                raise ValidationError(
                    "CapabilityMatch output mapping must reference admitted requested scopes"
                )
            mapped_descriptor_scopes = {
                requested_to_descriptor_scope[ref]
                for ref in match.requested_scope_refs
            }
            if mapped_descriptor_scopes != set(
                descriptor_output.scope_requirement_refs
            ):
                raise ValidationError(
                    "CapabilityMatch output scope mapping must exactly cover the "
                    "descriptor output scope requirements"
                )
        object.__setattr__(self, "output_matches", output_matches)

        requested_effects = {
            item.effect_ref: item for item in self.requirement.requested_effects
        }
        descriptor_effects = {item.effect_ref: item for item in descriptor.effects}
        effect_matches = _normalize_effect_matches(
            self.effect_matches, field="CapabilityMatch.effect_matches"
        )
        if {item.requested_effect_ref for item in effect_matches} != set(
            requested_effects
        ):
            raise ValidationError(
                "CapabilityMatch must map every requested effect exactly once"
            )
        if any(
            item.descriptor_effect_ref not in descriptor_effects
            for item in effect_matches
        ):
            raise ValidationError(
                "CapabilityMatch effect mapping must reference descriptor effects"
            )
        mapped_descriptor_effect_refs = {
            item.descriptor_effect_ref for item in effect_matches
        }
        unavoidable_refs = {
            item.effect_ref
            for item in descriptor.effects
            if item.requirement is CapabilityEffectRequirement.UNAVOIDABLE
        }
        if not unavoidable_refs.issubset(mapped_descriptor_effect_refs):
            raise ValidationError(
                "CapabilityMatch cannot hide an unavoidable descriptor effect"
            )
        for match in effect_matches:
            requested_effect = requested_effects[match.requested_effect_ref]
            descriptor_effect = descriptor_effects[match.descriptor_effect_ref]
            if requested_effect.semantic_type != descriptor_effect.semantic_type:
                raise ValidationError(
                    "CapabilityMatch effect semantic types must match exactly in v1"
                )
            mapped_descriptor_scopes = {
                requested_to_descriptor_scope[ref]
                for ref in requested_effect.requested_scope_refs
            }
            if mapped_descriptor_scopes != set(
                descriptor_effect.scope_requirement_refs
            ):
                raise ValidationError(
                    "CapabilityMatch effect scope mapping must exactly cover the "
                    "descriptor effect scope requirements"
                )
        object.__setattr__(self, "effect_matches", effect_matches)

        descriptor_boundaries = {
            (item.kind, item.boundary_ref) for item in descriptor.execution_boundaries
        }
        for requirement in self.requirement.execution_boundary_requirements:
            if (requirement.kind, requirement.boundary_ref) not in descriptor_boundaries:
                raise ValidationError(
                    "CapabilityMatch descriptor does not satisfy an explicit execution "
                    "boundary requirement"
                )

        _require_text(self.description, field="CapabilityMatch.description")

    @property
    def descriptor(self) -> CapabilityDescriptor:
        for descriptor in self.catalog_snapshot.descriptors:
            if descriptor.capability_ref == self.capability_ref:
                return descriptor
        raise AssertionError("validated CapabilityMatch lost its descriptor")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "capability_contract_identity": (
                self.capability_contract_identity.to_primitive()
            ),
            "capability_ref": self.capability_ref.to_primitive(),
            "catalog_snapshot": self.catalog_snapshot.to_primitive(),
            "description": self.description,
            "effect_matches": [item.to_primitive() for item in self.effect_matches],
            "input_matches": [item.to_primitive() for item in self.input_matches],
            "output_matches": [item.to_primitive() for item in self.output_matches],
            "requirement": self.requirement.to_primitive(),
            "schema": self.SCHEMA,
            "scope_matches": [item.to_primitive() for item in self.scope_matches],
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityMatch"
    ) -> "CapabilityMatch":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "attribution",
                "requirement",
                "catalog_snapshot",
                "capability_ref",
                "capability_contract_identity",
                "scope_matches",
                "input_matches",
                "output_matches",
                "effect_matches",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        scope_matches = _expect_array(
            obj["scope_matches"], field=f"{field}.scope_matches"
        )
        input_matches = _expect_array(
            obj["input_matches"], field=f"{field}.input_matches"
        )
        output_matches = _expect_array(
            obj["output_matches"], field=f"{field}.output_matches"
        )
        effect_matches = _expect_array(
            obj["effect_matches"], field=f"{field}.effect_matches"
        )
        try:
            return cls(
                attribution=CapabilityMatchAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                requirement=CapabilityRequirement.from_primitive(
                    obj["requirement"], field=f"{field}.requirement"
                ),
                catalog_snapshot=CapabilityCatalogSnapshot.from_primitive(
                    obj["catalog_snapshot"], field=f"{field}.catalog_snapshot"
                ),
                capability_ref=StableRef.from_primitive(
                    obj["capability_ref"], field=f"{field}.capability_ref"
                ),
                capability_contract_identity=RecordIdentity.from_primitive(
                    obj["capability_contract_identity"],
                    field=f"{field}.capability_contract_identity",
                ),
                scope_matches=tuple(
                    CapabilityScopeMatch.from_primitive(
                        item, field=f"{field}.scope_matches[{index}]"
                    )
                    for index, item in enumerate(scope_matches)
                ),
                input_matches=tuple(
                    CapabilityInputMatch.from_primitive(
                        item, field=f"{field}.input_matches[{index}]"
                    )
                    for index, item in enumerate(input_matches)
                ),
                output_matches=tuple(
                    CapabilityOutputMatch.from_primitive(
                        item, field=f"{field}.output_matches[{index}]"
                    )
                    for index, item in enumerate(output_matches)
                ),
                effect_matches=tuple(
                    CapabilityEffectMatch.from_primitive(
                        item, field=f"{field}.effect_matches[{index}]"
                    )
                    for index, item in enumerate(effect_matches)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityMatch":
        return cls.from_primitive(parse_json_object(data))
