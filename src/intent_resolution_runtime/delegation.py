from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, cast

from .canonical import canonical_json_bytes, parse_json_object
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef


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


def _record_identity_key(value: RecordIdentity) -> tuple[str, str]:
    return value.algorithm, value.digest


def _normalize_stable_refs(
    value: object, *, field: str, nonempty: bool = False
) -> tuple[StableRef, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is StableRef for item in value):
        raise ValidationError(f"{field} must contain StableRef values")
    refs = cast(tuple[StableRef, ...], value)
    if nonempty and not refs:
        raise ValidationError(f"{field} must not be empty")
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(refs, key=_stable_ref_key))


def _normalize_record_identities(
    value: object, *, field: str, max_items: int | None = None
) -> tuple[RecordIdentity, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is RecordIdentity for item in value):
        raise ValidationError(f"{field} must contain RecordIdentity values")
    refs = cast(tuple[RecordIdentity, ...], value)
    if max_items is not None and len(refs) > max_items:
        raise ValidationError(f"{field} must contain at most {max_items} value(s)")
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(refs, key=_record_identity_key))


class _CanonicalDelegationRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class DelegationConstraintKind(str, Enum):
    MATERIAL = "material"
    FORBIDDEN_EFFECT = "forbidden_effect"
    AUTHORITY_REQUIREMENT = "authority_requirement"


@dataclass(frozen=True, slots=True)
class DelegatedScope(_CanonicalDelegationRecord):
    SCHEMA: ClassVar[str] = "irr.delegated_scope.v1"

    scope_ref: StableRef
    semantic_type: str
    value: str
    description: str

    def __post_init__(self) -> None:
        if type(self.scope_ref) is not StableRef:
            raise ValidationError("DelegatedScope.scope_ref must be a StableRef")
        _require_token(self.semantic_type, field="DelegatedScope.semantic_type")
        _require_text(self.value, field="DelegatedScope.value")
        _require_text(self.description, field="DelegatedScope.description")

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
        cls, value: object, *, field: str = "DelegatedScope"
    ) -> "DelegatedScope":
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
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "DelegatedScope":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class DelegatedContextReference(_CanonicalDelegationRecord):
    SCHEMA: ClassVar[str] = "irr.delegated_context_reference.v1"

    context_ref: StableRef
    semantic_type: str
    scope_ref: StableRef
    source_identity_refs: tuple[RecordIdentity, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.context_ref) is not StableRef:
            raise ValidationError(
                "DelegatedContextReference.context_ref must be a StableRef"
            )
        _require_token(
            self.semantic_type, field="DelegatedContextReference.semantic_type"
        )
        if type(self.scope_ref) is not StableRef:
            raise ValidationError(
                "DelegatedContextReference.scope_ref must be a StableRef"
            )
        object.__setattr__(
            self,
            "source_identity_refs",
            _normalize_record_identities(
                self.source_identity_refs,
                field="DelegatedContextReference.source_identity_refs",
            ),
        )
        _require_text(
            self.description, field="DelegatedContextReference.description"
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "context_ref": self.context_ref.to_primitive(),
            "description": self.description,
            "schema": self.SCHEMA,
            "scope_ref": self.scope_ref.to_primitive(),
            "semantic_type": self.semantic_type,
            "source_identity_refs": [
                item.to_primitive() for item in self.source_identity_refs
            ],
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "DelegatedContextReference"
    ) -> "DelegatedContextReference":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "context_ref",
                "semantic_type",
                "scope_ref",
                "source_identity_refs",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        identities = _expect_array(
            obj["source_identity_refs"], field=f"{field}.source_identity_refs"
        )
        try:
            return cls(
                context_ref=StableRef.from_primitive(
                    obj["context_ref"], field=f"{field}.context_ref"
                ),
                semantic_type=obj["semantic_type"],
                scope_ref=StableRef.from_primitive(
                    obj["scope_ref"], field=f"{field}.scope_ref"
                ),
                source_identity_refs=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"{field}.source_identity_refs[{index}]"
                    )
                    for index, item in enumerate(identities)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "DelegatedContextReference":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class DelegationConstraint(_CanonicalDelegationRecord):
    SCHEMA: ClassVar[str] = "irr.delegation_constraint.v1"

    constraint_ref: StableRef
    kind: DelegationConstraintKind
    statement: str

    def __post_init__(self) -> None:
        if type(self.constraint_ref) is not StableRef:
            raise ValidationError(
                "DelegationConstraint.constraint_ref must be a StableRef"
            )
        if type(self.kind) is not DelegationConstraintKind:
            raise ValidationError(
                "DelegationConstraint.kind must be a DelegationConstraintKind"
            )
        _require_text(self.statement, field="DelegationConstraint.statement")

    def to_primitive(self) -> dict[str, object]:
        return {
            "constraint_ref": self.constraint_ref.to_primitive(),
            "kind": self.kind.value,
            "schema": self.SCHEMA,
            "statement": self.statement,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "DelegationConstraint"
    ) -> "DelegationConstraint":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "constraint_ref", "kind", "statement"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["kind"]) is not str:
            raise SerializationError(f"{field}.kind must be a string")
        try:
            kind = DelegationConstraintKind(obj["kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.kind") from exc
        try:
            return cls(
                constraint_ref=StableRef.from_primitive(
                    obj["constraint_ref"], field=f"{field}.constraint_ref"
                ),
                kind=kind,
                statement=obj["statement"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "DelegationConstraint":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class ExpectedDeliverable(_CanonicalDelegationRecord):
    SCHEMA: ClassVar[str] = "irr.expected_deliverable.v1"

    deliverable_ref: StableRef
    semantic_type: str
    scope_ref: StableRef
    description: str

    def __post_init__(self) -> None:
        if type(self.deliverable_ref) is not StableRef:
            raise ValidationError(
                "ExpectedDeliverable.deliverable_ref must be a StableRef"
            )
        _require_token(self.semantic_type, field="ExpectedDeliverable.semantic_type")
        if type(self.scope_ref) is not StableRef:
            raise ValidationError("ExpectedDeliverable.scope_ref must be a StableRef")
        _require_text(self.description, field="ExpectedDeliverable.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "deliverable_ref": self.deliverable_ref.to_primitive(),
            "description": self.description,
            "schema": self.SCHEMA,
            "scope_ref": self.scope_ref.to_primitive(),
            "semantic_type": self.semantic_type,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "ExpectedDeliverable"
    ) -> "ExpectedDeliverable":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "deliverable_ref", "semantic_type", "scope_ref", "description"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                deliverable_ref=StableRef.from_primitive(
                    obj["deliverable_ref"], field=f"{field}.deliverable_ref"
                ),
                semantic_type=obj["semantic_type"],
                scope_ref=StableRef.from_primitive(
                    obj["scope_ref"], field=f"{field}.scope_ref"
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "ExpectedDeliverable":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class DelegatedCapabilityAllowance(_CanonicalDelegationRecord):
    SCHEMA: ClassVar[str] = "irr.delegated_capability_allowance.v1"

    allowance_ref: StableRef
    capability_ref: StableRef
    capability_contract_identity: RecordIdentity
    scope_refs: tuple[StableRef, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.allowance_ref) is not StableRef:
            raise ValidationError(
                "DelegatedCapabilityAllowance.allowance_ref must be a StableRef"
            )
        if type(self.capability_ref) is not StableRef:
            raise ValidationError(
                "DelegatedCapabilityAllowance.capability_ref must be a StableRef"
            )
        if type(self.capability_contract_identity) is not RecordIdentity:
            raise ValidationError(
                "DelegatedCapabilityAllowance.capability_contract_identity "
                "must be a RecordIdentity"
            )
        object.__setattr__(
            self,
            "scope_refs",
            _normalize_stable_refs(
                self.scope_refs,
                field="DelegatedCapabilityAllowance.scope_refs",
                nonempty=True,
            ),
        )
        _require_text(
            self.description, field="DelegatedCapabilityAllowance.description"
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "allowance_ref": self.allowance_ref.to_primitive(),
            "capability_contract_identity": (
                self.capability_contract_identity.to_primitive()
            ),
            "capability_ref": self.capability_ref.to_primitive(),
            "description": self.description,
            "schema": self.SCHEMA,
            "scope_refs": [item.to_primitive() for item in self.scope_refs],
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "DelegatedCapabilityAllowance"
    ) -> "DelegatedCapabilityAllowance":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "allowance_ref",
                "capability_ref",
                "capability_contract_identity",
                "scope_refs",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        scopes = _expect_array(obj["scope_refs"], field=f"{field}.scope_refs")
        try:
            return cls(
                allowance_ref=StableRef.from_primitive(
                    obj["allowance_ref"], field=f"{field}.allowance_ref"
                ),
                capability_ref=StableRef.from_primitive(
                    obj["capability_ref"], field=f"{field}.capability_ref"
                ),
                capability_contract_identity=RecordIdentity.from_primitive(
                    obj["capability_contract_identity"],
                    field=f"{field}.capability_contract_identity",
                ),
                scope_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.scope_refs[{index}]"
                    )
                    for index, item in enumerate(scopes)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "DelegatedCapabilityAllowance":
        return cls.from_primitive(parse_json_object(data))


def _normalize_capability_allowances(
    value: object, *, field: str
) -> tuple[DelegatedCapabilityAllowance, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is DelegatedCapabilityAllowance for item in value):
        raise ValidationError(
            f"{field} must contain DelegatedCapabilityAllowance values"
        )
    items = cast(tuple[DelegatedCapabilityAllowance, ...], value)
    allowance_refs = [item.allowance_ref for item in items]
    if len(set(allowance_refs)) != len(allowance_refs):
        raise ValidationError(
            f"{field} must not contain duplicate allowance_ref values"
        )
    capability_refs = [item.capability_ref for item in items]
    if len(set(capability_refs)) != len(capability_refs):
        raise ValidationError(
            f"{field} must not contain duplicate capability_ref values"
        )
    return tuple(
        sorted(items, key=lambda item: _stable_ref_key(item.allowance_ref))
    )


def _normalize_scopes(
    value: object, *, field: str, nonempty: bool = False
) -> tuple[DelegatedScope, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is DelegatedScope for item in value):
        raise ValidationError(f"{field} must contain DelegatedScope values")
    items = cast(tuple[DelegatedScope, ...], value)
    if nonempty and not items:
        raise ValidationError(f"{field} must not be empty")
    refs = [item.scope_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate scope_ref values")
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.scope_ref)))


def _normalize_context_refs(
    value: object, *, field: str
) -> tuple[DelegatedContextReference, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is DelegatedContextReference for item in value):
        raise ValidationError(
            f"{field} must contain DelegatedContextReference values"
        )
    items = cast(tuple[DelegatedContextReference, ...], value)
    refs = [item.context_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate context_ref values")
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.context_ref)))


def _normalize_constraints(
    value: object, *, field: str
) -> tuple[DelegationConstraint, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is DelegationConstraint for item in value):
        raise ValidationError(f"{field} must contain DelegationConstraint values")
    items = cast(tuple[DelegationConstraint, ...], value)
    refs = [item.constraint_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(
            f"{field} must not contain duplicate constraint_ref values"
        )
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.constraint_ref)))


def _normalize_deliverables(
    value: object, *, field: str, nonempty: bool = False
) -> tuple[ExpectedDeliverable, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is ExpectedDeliverable for item in value):
        raise ValidationError(f"{field} must contain ExpectedDeliverable values")
    items = cast(tuple[ExpectedDeliverable, ...], value)
    if nonempty and not items:
        raise ValidationError(f"{field} must not be empty")
    refs = [item.deliverable_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(
            f"{field} must not contain duplicate deliverable_ref values"
        )
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.deliverable_ref)))


@dataclass(frozen=True, slots=True)
class DelegatedWork(_CanonicalDelegationRecord):
    SCHEMA: ClassVar[str] = "irr.delegated_work.v1"

    resolved_intent_identity: RecordIdentity
    delegation_ref: StableRef
    parent_work_plan_identity_refs: tuple[RecordIdentity, ...]
    objective: str
    scopes: tuple[DelegatedScope, ...]
    context_surface: tuple[DelegatedContextReference, ...]
    allowed_capabilities: tuple[DelegatedCapabilityAllowance, ...]
    constraints: tuple[DelegationConstraint, ...]
    expected_deliverables: tuple[ExpectedDeliverable, ...]
    completion_contract: str
    description: str

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError(
                "DelegatedWork.resolved_intent_identity must be a RecordIdentity"
            )
        if type(self.delegation_ref) is not StableRef:
            raise ValidationError("DelegatedWork.delegation_ref must be a StableRef")
        object.__setattr__(
            self,
            "parent_work_plan_identity_refs",
            _normalize_record_identities(
                self.parent_work_plan_identity_refs,
                field="DelegatedWork.parent_work_plan_identity_refs",
                max_items=1,
            ),
        )
        _require_text(self.objective, field="DelegatedWork.objective")
        scopes = _normalize_scopes(
            self.scopes, field="DelegatedWork.scopes", nonempty=True
        )
        object.__setattr__(self, "scopes", scopes)
        scope_refs = {item.scope_ref for item in scopes}

        context_surface = _normalize_context_refs(
            self.context_surface, field="DelegatedWork.context_surface"
        )
        if any(item.scope_ref not in scope_refs for item in context_surface):
            raise ValidationError(
                "DelegatedWork context entries must reference an admitted delegated scope"
            )
        object.__setattr__(self, "context_surface", context_surface)

        allowed_capabilities = _normalize_capability_allowances(
            self.allowed_capabilities, field="DelegatedWork.allowed_capabilities"
        )
        if any(
            scope_ref not in scope_refs
            for allowance in allowed_capabilities
            for scope_ref in allowance.scope_refs
        ):
            raise ValidationError(
                "DelegatedWork capability allowances must reference admitted delegated scopes"
            )
        object.__setattr__(self, "allowed_capabilities", allowed_capabilities)
        object.__setattr__(
            self,
            "constraints",
            _normalize_constraints(
                self.constraints, field="DelegatedWork.constraints"
            ),
        )
        deliverables = _normalize_deliverables(
            self.expected_deliverables,
            field="DelegatedWork.expected_deliverables",
            nonempty=True,
        )
        if any(item.scope_ref not in scope_refs for item in deliverables):
            raise ValidationError(
                "DelegatedWork deliverables must reference an admitted delegated scope"
            )
        object.__setattr__(self, "expected_deliverables", deliverables)
        _require_text(
            self.completion_contract, field="DelegatedWork.completion_contract"
        )
        _require_text(self.description, field="DelegatedWork.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "allowed_capabilities": [
                item.to_primitive() for item in self.allowed_capabilities
            ],
            "completion_contract": self.completion_contract,
            "constraints": [item.to_primitive() for item in self.constraints],
            "context_surface": [item.to_primitive() for item in self.context_surface],
            "delegation_ref": self.delegation_ref.to_primitive(),
            "description": self.description,
            "expected_deliverables": [
                item.to_primitive() for item in self.expected_deliverables
            ],
            "objective": self.objective,
            "parent_work_plan_identity_refs": [
                item.to_primitive() for item in self.parent_work_plan_identity_refs
            ],
            "resolved_intent_identity": self.resolved_intent_identity.to_primitive(),
            "schema": self.SCHEMA,
            "scopes": [item.to_primitive() for item in self.scopes],
        }

    @classmethod
    def from_primitive(cls, value: object) -> "DelegatedWork":
        obj = _expect_object(value, field="DelegatedWork")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "resolved_intent_identity",
                "delegation_ref",
                "parent_work_plan_identity_refs",
                "objective",
                "scopes",
                "context_surface",
                "allowed_capabilities",
                "constraints",
                "expected_deliverables",
                "completion_contract",
                "description",
            },
            field="DelegatedWork",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported DelegatedWork schema: {obj['schema']!r}"
            )
        parent_refs = _expect_array(
            obj["parent_work_plan_identity_refs"],
            field="DelegatedWork.parent_work_plan_identity_refs",
        )
        scopes = _expect_array(obj["scopes"], field="DelegatedWork.scopes")
        context_surface = _expect_array(
            obj["context_surface"], field="DelegatedWork.context_surface"
        )
        capabilities = _expect_array(
            obj["allowed_capabilities"], field="DelegatedWork.allowed_capabilities"
        )
        constraints = _expect_array(
            obj["constraints"], field="DelegatedWork.constraints"
        )
        deliverables = _expect_array(
            obj["expected_deliverables"], field="DelegatedWork.expected_deliverables"
        )
        try:
            return cls(
                resolved_intent_identity=RecordIdentity.from_primitive(
                    obj["resolved_intent_identity"],
                    field="DelegatedWork.resolved_intent_identity",
                ),
                delegation_ref=StableRef.from_primitive(
                    obj["delegation_ref"], field="DelegatedWork.delegation_ref"
                ),
                parent_work_plan_identity_refs=tuple(
                    RecordIdentity.from_primitive(
                        item,
                        field=f"DelegatedWork.parent_work_plan_identity_refs[{index}]",
                    )
                    for index, item in enumerate(parent_refs)
                ),
                objective=obj["objective"],
                scopes=tuple(
                    DelegatedScope.from_primitive(
                        item, field=f"DelegatedWork.scopes[{index}]"
                    )
                    for index, item in enumerate(scopes)
                ),
                context_surface=tuple(
                    DelegatedContextReference.from_primitive(
                        item, field=f"DelegatedWork.context_surface[{index}]"
                    )
                    for index, item in enumerate(context_surface)
                ),
                allowed_capabilities=tuple(
                    DelegatedCapabilityAllowance.from_primitive(
                        item,
                        field=f"DelegatedWork.allowed_capabilities[{index}]",
                    )
                    for index, item in enumerate(capabilities)
                ),
                constraints=tuple(
                    DelegationConstraint.from_primitive(
                        item, field=f"DelegatedWork.constraints[{index}]"
                    )
                    for index, item in enumerate(constraints)
                ),
                expected_deliverables=tuple(
                    ExpectedDeliverable.from_primitive(
                        item, field=f"DelegatedWork.expected_deliverables[{index}]"
                    )
                    for index, item in enumerate(deliverables)
                ),
                completion_contract=obj["completion_contract"],
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid DelegatedWork") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "DelegatedWork":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class DelegationHandoffAttribution(_CanonicalDelegationRecord):
    SCHEMA: ClassVar[str] = "irr.delegation_handoff_attribution.v1"

    dispatcher_ref: StableRef
    worker_ref: StableRef
    handoff_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.dispatcher_ref) is not StableRef:
            raise ValidationError(
                "DelegationHandoffAttribution.dispatcher_ref must be a StableRef"
            )
        if type(self.worker_ref) is not StableRef:
            raise ValidationError(
                "DelegationHandoffAttribution.worker_ref must be a StableRef"
            )
        if type(self.handoff_event_ref) is not StableRef:
            raise ValidationError(
                "DelegationHandoffAttribution.handoff_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "dispatcher_ref": self.dispatcher_ref.to_primitive(),
            "handoff_event_ref": self.handoff_event_ref.to_primitive(),
            "schema": self.SCHEMA,
            "worker_ref": self.worker_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "DelegationHandoffAttribution"
    ) -> "DelegationHandoffAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "dispatcher_ref", "worker_ref", "handoff_event_ref"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                dispatcher_ref=StableRef.from_primitive(
                    obj["dispatcher_ref"], field=f"{field}.dispatcher_ref"
                ),
                worker_ref=StableRef.from_primitive(
                    obj["worker_ref"], field=f"{field}.worker_ref"
                ),
                handoff_event_ref=StableRef.from_primitive(
                    obj["handoff_event_ref"], field=f"{field}.handoff_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "DelegationHandoffAttribution":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class DelegatedWorkHandoff(_CanonicalDelegationRecord):
    SCHEMA: ClassVar[str] = "irr.delegated_work_handoff.v1"

    attribution: DelegationHandoffAttribution
    delegated_work: DelegatedWork

    def __post_init__(self) -> None:
        if type(self.attribution) is not DelegationHandoffAttribution:
            raise ValidationError(
                "DelegatedWorkHandoff.attribution must be a DelegationHandoffAttribution"
            )
        if type(self.delegated_work) is not DelegatedWork:
            raise ValidationError(
                "DelegatedWorkHandoff.delegated_work must be a DelegatedWork"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "delegated_work": self.delegated_work.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "DelegatedWorkHandoff":
        obj = _expect_object(value, field="DelegatedWorkHandoff")
        _expect_exact_keys(
            obj, {"schema", "attribution", "delegated_work"}, field="DelegatedWorkHandoff"
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported DelegatedWorkHandoff schema: {obj['schema']!r}"
            )
        try:
            return cls(
                attribution=DelegationHandoffAttribution.from_primitive(
                    obj["attribution"], field="DelegatedWorkHandoff.attribution"
                ),
                delegated_work=DelegatedWork.from_primitive(obj["delegated_work"]),
            )
        except ValidationError as exc:
            raise SerializationError("invalid DelegatedWorkHandoff") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "DelegatedWorkHandoff":
        return cls.from_primitive(parse_json_object(data))
