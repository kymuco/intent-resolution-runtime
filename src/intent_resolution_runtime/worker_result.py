from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, cast

from .canonical import canonical_json_bytes, parse_json_object
from .delegation import DelegatedWorkHandoff
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
    value: object, *, field: str
) -> tuple[RecordIdentity, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is RecordIdentity for item in value):
        raise ValidationError(f"{field} must contain RecordIdentity values")
    refs = cast(tuple[RecordIdentity, ...], value)
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(refs, key=_record_identity_key))


class _CanonicalWorkerResultRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class WorkerResultMaterialRole(str, Enum):
    DELIVERABLE = "deliverable"
    FINDING = "finding"
    ARTIFACT_REFERENCE = "artifact_reference"
    COMPLETION_CLAIM = "completion_claim"
    UNCERTAINTY = "uncertainty"
    SCOPE_COVERAGE = "scope_coverage"
    OMISSION = "omission"
    OTHER_EXPLICIT = "other_explicit"


class WorkerNeedKind(str, Enum):
    INFORMATION = "information"
    CAPABILITY = "capability"
    AUTHORITY = "authority"
    SCOPE = "scope"
    CLARIFICATION = "clarification"
    OBJECTIVE_CHANGE = "objective_change"
    EFFECT_BOUNDARY = "effect_boundary"
    OTHER_EXPLICIT = "other_explicit"


@dataclass(frozen=True, slots=True)
class WorkerResultAttribution(_CanonicalWorkerResultRecord):
    SCHEMA: ClassVar[str] = "irr.worker_result_attribution.v1"

    worker_ref: StableRef
    result_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.worker_ref) is not StableRef:
            raise ValidationError("WorkerResultAttribution.worker_ref must be a StableRef")
        if type(self.result_event_ref) is not StableRef:
            raise ValidationError(
                "WorkerResultAttribution.result_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "result_event_ref": self.result_event_ref.to_primitive(),
            "schema": self.SCHEMA,
            "worker_ref": self.worker_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "WorkerResultAttribution"
    ) -> "WorkerResultAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "worker_ref", "result_event_ref"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                worker_ref=StableRef.from_primitive(
                    obj["worker_ref"], field=f"{field}.worker_ref"
                ),
                result_event_ref=StableRef.from_primitive(
                    obj["result_event_ref"], field=f"{field}.result_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "WorkerResultAttribution":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class WorkerResultMaterial(_CanonicalWorkerResultRecord):
    SCHEMA: ClassVar[str] = "irr.worker_result_material.v1"

    material_ref: StableRef
    role: WorkerResultMaterialRole
    semantic_type: str
    scope_refs: tuple[StableRef, ...]
    expected_deliverable_refs: tuple[StableRef, ...]
    source_refs: tuple[StableRef, ...]
    source_identity_refs: tuple[RecordIdentity, ...]
    content: str
    description: str

    def __post_init__(self) -> None:
        if type(self.material_ref) is not StableRef:
            raise ValidationError("WorkerResultMaterial.material_ref must be a StableRef")
        if type(self.role) is not WorkerResultMaterialRole:
            raise ValidationError(
                "WorkerResultMaterial.role must be a WorkerResultMaterialRole"
            )
        _require_token(self.semantic_type, field="WorkerResultMaterial.semantic_type")
        object.__setattr__(
            self,
            "scope_refs",
            _normalize_stable_refs(
                self.scope_refs, field="WorkerResultMaterial.scope_refs", nonempty=True
            ),
        )
        deliverable_refs = _normalize_stable_refs(
            self.expected_deliverable_refs,
            field="WorkerResultMaterial.expected_deliverable_refs",
        )
        if self.role is WorkerResultMaterialRole.DELIVERABLE:
            if not deliverable_refs:
                raise ValidationError(
                    "deliverable WorkerResultMaterial must reference at least one "
                    "ExpectedDeliverable"
                )
        elif deliverable_refs:
            raise ValidationError(
                "only deliverable WorkerResultMaterial may reference ExpectedDeliverable"
            )
        object.__setattr__(self, "expected_deliverable_refs", deliverable_refs)
        object.__setattr__(
            self,
            "source_refs",
            _normalize_stable_refs(
                self.source_refs, field="WorkerResultMaterial.source_refs"
            ),
        )
        object.__setattr__(
            self,
            "source_identity_refs",
            _normalize_record_identities(
                self.source_identity_refs,
                field="WorkerResultMaterial.source_identity_refs",
            ),
        )
        _require_string(self.content, field="WorkerResultMaterial.content")
        _require_text(self.description, field="WorkerResultMaterial.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "content": self.content,
            "description": self.description,
            "expected_deliverable_refs": [
                item.to_primitive() for item in self.expected_deliverable_refs
            ],
            "material_ref": self.material_ref.to_primitive(),
            "role": self.role.value,
            "schema": self.SCHEMA,
            "scope_refs": [item.to_primitive() for item in self.scope_refs],
            "semantic_type": self.semantic_type,
            "source_identity_refs": [
                item.to_primitive() for item in self.source_identity_refs
            ],
            "source_refs": [item.to_primitive() for item in self.source_refs],
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "WorkerResultMaterial"
    ) -> "WorkerResultMaterial":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "material_ref",
                "role",
                "semantic_type",
                "scope_refs",
                "expected_deliverable_refs",
                "source_refs",
                "source_identity_refs",
                "content",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["role"]) is not str:
            raise SerializationError(f"{field}.role must be a string")
        try:
            role = WorkerResultMaterialRole(obj["role"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.role") from exc
        scopes = _expect_array(obj["scope_refs"], field=f"{field}.scope_refs")
        deliverables = _expect_array(
            obj["expected_deliverable_refs"],
            field=f"{field}.expected_deliverable_refs",
        )
        source_refs = _expect_array(obj["source_refs"], field=f"{field}.source_refs")
        source_identities = _expect_array(
            obj["source_identity_refs"], field=f"{field}.source_identity_refs"
        )
        try:
            return cls(
                material_ref=StableRef.from_primitive(
                    obj["material_ref"], field=f"{field}.material_ref"
                ),
                role=role,
                semantic_type=obj["semantic_type"],
                scope_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.scope_refs[{index}]"
                    )
                    for index, item in enumerate(scopes)
                ),
                expected_deliverable_refs=tuple(
                    StableRef.from_primitive(
                        item,
                        field=f"{field}.expected_deliverable_refs[{index}]",
                    )
                    for index, item in enumerate(deliverables)
                ),
                source_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.source_refs[{index}]"
                    )
                    for index, item in enumerate(source_refs)
                ),
                source_identity_refs=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"{field}.source_identity_refs[{index}]"
                    )
                    for index, item in enumerate(source_identities)
                ),
                content=obj["content"],
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "WorkerResultMaterial":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class WorkerNeed(_CanonicalWorkerResultRecord):
    SCHEMA: ClassVar[str] = "irr.worker_need.v1"

    need_ref: StableRef
    kind: WorkerNeedKind
    related_scope_refs: tuple[StableRef, ...]
    statement: str

    def __post_init__(self) -> None:
        if type(self.need_ref) is not StableRef:
            raise ValidationError("WorkerNeed.need_ref must be a StableRef")
        if type(self.kind) is not WorkerNeedKind:
            raise ValidationError("WorkerNeed.kind must be a WorkerNeedKind")
        object.__setattr__(
            self,
            "related_scope_refs",
            _normalize_stable_refs(
                self.related_scope_refs, field="WorkerNeed.related_scope_refs"
            ),
        )
        _require_text(self.statement, field="WorkerNeed.statement")

    def to_primitive(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "need_ref": self.need_ref.to_primitive(),
            "related_scope_refs": [
                item.to_primitive() for item in self.related_scope_refs
            ],
            "schema": self.SCHEMA,
            "statement": self.statement,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "WorkerNeed"
    ) -> "WorkerNeed":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "need_ref", "kind", "related_scope_refs", "statement"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["kind"]) is not str:
            raise SerializationError(f"{field}.kind must be a string")
        try:
            kind = WorkerNeedKind(obj["kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.kind") from exc
        scopes = _expect_array(
            obj["related_scope_refs"], field=f"{field}.related_scope_refs"
        )
        try:
            return cls(
                need_ref=StableRef.from_primitive(
                    obj["need_ref"], field=f"{field}.need_ref"
                ),
                kind=kind,
                related_scope_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.related_scope_refs[{index}]"
                    )
                    for index, item in enumerate(scopes)
                ),
                statement=obj["statement"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "WorkerNeed":
        return cls.from_primitive(parse_json_object(data))


def _normalize_materials(
    value: object, *, field: str
) -> tuple[WorkerResultMaterial, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is WorkerResultMaterial for item in value):
        raise ValidationError(f"{field} must contain WorkerResultMaterial values")
    items = cast(tuple[WorkerResultMaterial, ...], value)
    refs = [item.material_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate material_ref values")
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.material_ref)))


def _normalize_needs(value: object, *, field: str) -> tuple[WorkerNeed, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is WorkerNeed for item in value):
        raise ValidationError(f"{field} must contain WorkerNeed values")
    items = cast(tuple[WorkerNeed, ...], value)
    refs = [item.need_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate need_ref values")
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.need_ref)))


@dataclass(frozen=True, slots=True)
class WorkerResult(_CanonicalWorkerResultRecord):
    SCHEMA: ClassVar[str] = "irr.worker_result.v1"

    attribution: WorkerResultAttribution
    handoff: DelegatedWorkHandoff
    materials: tuple[WorkerResultMaterial, ...]
    needs: tuple[WorkerNeed, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not WorkerResultAttribution:
            raise ValidationError(
                "WorkerResult.attribution must be a WorkerResultAttribution"
            )
        if type(self.handoff) is not DelegatedWorkHandoff:
            raise ValidationError("WorkerResult.handoff must be a DelegatedWorkHandoff")
        if self.attribution.worker_ref != self.handoff.attribution.worker_ref:
            raise ValidationError(
                "WorkerResult worker attribution must match the handed-off Worker"
            )

        materials = _normalize_materials(
            self.materials, field="WorkerResult.materials"
        )
        needs = _normalize_needs(self.needs, field="WorkerResult.needs")
        if not materials and not needs:
            raise ValidationError(
                "WorkerResult must contain at least one material or WorkerNeed"
            )

        delegated = self.handoff.delegated_work
        admitted_scopes = {item.scope_ref for item in delegated.scopes}
        expected_by_ref = {
            item.deliverable_ref: item for item in delegated.expected_deliverables
        }

        for material in materials:
            if any(scope_ref not in admitted_scopes for scope_ref in material.scope_refs):
                raise ValidationError(
                    "WorkerResult materials must reference admitted delegated scopes"
                )
            for deliverable_ref in material.expected_deliverable_refs:
                expected = expected_by_ref.get(deliverable_ref)
                if expected is None:
                    raise ValidationError(
                        "WorkerResult deliverable material must reference an admitted "
                        "ExpectedDeliverable"
                    )
                if expected.semantic_type != material.semantic_type:
                    raise ValidationError(
                        "WorkerResult deliverable semantic_type must match the "
                        "ExpectedDeliverable"
                    )
                if expected.scope_ref not in material.scope_refs:
                    raise ValidationError(
                        "WorkerResult deliverable material must cover the "
                        "ExpectedDeliverable scope"
                    )

        for need in needs:
            if any(
                scope_ref not in admitted_scopes
                for scope_ref in need.related_scope_refs
            ):
                raise ValidationError(
                    "WorkerNeed related scopes must reference admitted delegated scopes"
                )

        object.__setattr__(self, "materials", materials)
        object.__setattr__(self, "needs", needs)
        _require_text(self.description, field="WorkerResult.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "description": self.description,
            "handoff": self.handoff.to_primitive(),
            "materials": [item.to_primitive() for item in self.materials],
            "needs": [item.to_primitive() for item in self.needs],
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "WorkerResult":
        obj = _expect_object(value, field="WorkerResult")
        _expect_exact_keys(
            obj,
            {"schema", "attribution", "handoff", "materials", "needs", "description"},
            field="WorkerResult",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported WorkerResult schema: {obj['schema']!r}"
            )
        materials = _expect_array(obj["materials"], field="WorkerResult.materials")
        needs = _expect_array(obj["needs"], field="WorkerResult.needs")
        try:
            return cls(
                attribution=WorkerResultAttribution.from_primitive(
                    obj["attribution"], field="WorkerResult.attribution"
                ),
                handoff=DelegatedWorkHandoff.from_primitive(obj["handoff"]),
                materials=tuple(
                    WorkerResultMaterial.from_primitive(
                        item, field=f"WorkerResult.materials[{index}]"
                    )
                    for index, item in enumerate(materials)
                ),
                needs=tuple(
                    WorkerNeed.from_primitive(
                        item, field=f"WorkerResult.needs[{index}]"
                    )
                    for index, item in enumerate(needs)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid WorkerResult") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "WorkerResult":
        return cls.from_primitive(parse_json_object(data))
