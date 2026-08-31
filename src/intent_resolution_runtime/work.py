from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, TypeAlias, cast

from .binding import SymbolicReference
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


class _CanonicalWorkRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class WorkContinuationMode(str, Enum):
    NONE = "none"
    RETURN_TO_IRR = "return_to_irr"


@dataclass(frozen=True, slots=True)
class WorkLiteralInput(_CanonicalWorkRecord):
    SCHEMA: ClassVar[str] = "irr.work_literal_input.v1"

    name: str
    semantic_type: str
    value: str

    def __post_init__(self) -> None:
        _require_token(self.name, field="WorkLiteralInput.name")
        _require_token(self.semantic_type, field="WorkLiteralInput.semantic_type")
        _require_text(self.value, field="WorkLiteralInput.value")

    def to_primitive(self) -> dict[str, object]:
        return {
            "name": self.name,
            "schema": self.SCHEMA,
            "semantic_type": self.semantic_type,
            "value": self.value,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "WorkLiteralInput"
    ) -> "WorkLiteralInput":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"schema", "name", "semantic_type", "value"}, field=field)
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                name=obj["name"],
                semantic_type=obj["semantic_type"],
                value=obj["value"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "WorkLiteralInput":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class WorkSymbolicInput(_CanonicalWorkRecord):
    SCHEMA: ClassVar[str] = "irr.work_symbolic_input.v1"

    name: str
    reference: SymbolicReference

    def __post_init__(self) -> None:
        _require_token(self.name, field="WorkSymbolicInput.name")
        if type(self.reference) is not SymbolicReference:
            raise ValidationError("WorkSymbolicInput.reference must be a SymbolicReference")

    def to_primitive(self) -> dict[str, object]:
        return {
            "name": self.name,
            "reference": self.reference.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "WorkSymbolicInput"
    ) -> "WorkSymbolicInput":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"schema", "name", "reference"}, field=field)
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                name=obj["name"],
                reference=SymbolicReference.from_primitive(obj["reference"]),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "WorkSymbolicInput":
        return cls.from_primitive(parse_json_object(data))


WorkInput: TypeAlias = WorkLiteralInput | WorkSymbolicInput


def _work_input_from_primitive(value: object, *, field: str) -> WorkInput:
    obj = _expect_object(value, field=field)
    schema = obj.get("schema")
    if schema == WorkLiteralInput.SCHEMA:
        return WorkLiteralInput.from_primitive(obj, field=field)
    if schema == WorkSymbolicInput.SCHEMA:
        return WorkSymbolicInput.from_primitive(obj, field=field)
    raise SerializationError(f"unsupported {field} schema: {schema!r}")


@dataclass(frozen=True, slots=True)
class WorkOutput(_CanonicalWorkRecord):
    SCHEMA: ClassVar[str] = "irr.work_output.v1"

    name: str
    reference: SymbolicReference

    def __post_init__(self) -> None:
        _require_token(self.name, field="WorkOutput.name")
        if type(self.reference) is not SymbolicReference:
            raise ValidationError("WorkOutput.reference must be a SymbolicReference")

    def to_primitive(self) -> dict[str, object]:
        return {
            "name": self.name,
            "reference": self.reference.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(cls, value: object, *, field: str = "WorkOutput") -> "WorkOutput":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"schema", "name", "reference"}, field=field)
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                name=obj["name"],
                reference=SymbolicReference.from_primitive(obj["reference"]),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "WorkOutput":
        return cls.from_primitive(parse_json_object(data))


def _normalize_inputs(value: object, *, field: str) -> tuple[WorkInput, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) in (WorkLiteralInput, WorkSymbolicInput) for item in value):
        raise ValidationError(
            f"{field} must contain WorkLiteralInput or WorkSymbolicInput values"
        )
    inputs = cast(tuple[WorkInput, ...], value)
    names = [item.name for item in inputs]
    if len(set(names)) != len(names):
        raise ValidationError(f"{field} must not contain duplicate names")
    return tuple(sorted(inputs, key=lambda item: item.name))


def _normalize_outputs(value: object, *, field: str) -> tuple[WorkOutput, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is WorkOutput for item in value):
        raise ValidationError(f"{field} must contain WorkOutput values")
    outputs = cast(tuple[WorkOutput, ...], value)
    names = [item.name for item in outputs]
    if len(set(names)) != len(names):
        raise ValidationError(f"{field} must not contain duplicate names")
    slot_refs = [item.reference.slot_ref for item in outputs]
    if len(set(slot_refs)) != len(slot_refs):
        raise ValidationError(f"{field} must not publish the same symbolic slot twice")
    return tuple(sorted(outputs, key=lambda item: item.name))


@dataclass(frozen=True, slots=True)
class WorkStep(_CanonicalWorkRecord):
    SCHEMA: ClassVar[str] = "irr.work_step.v1"

    resolved_intent_identity: RecordIdentity
    step_ref: StableRef
    operation: str
    scope: str
    inputs: tuple[WorkInput, ...]
    outputs: tuple[WorkOutput, ...]
    depends_on: tuple[StableRef, ...]
    continuation: WorkContinuationMode
    completion_contract: str
    description: str

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError("WorkStep.resolved_intent_identity must be a RecordIdentity")
        if type(self.step_ref) is not StableRef:
            raise ValidationError("WorkStep.step_ref must be a StableRef")
        _require_token(self.operation, field="WorkStep.operation")
        _require_text(self.scope, field="WorkStep.scope")
        object.__setattr__(
            self,
            "inputs",
            _normalize_inputs(self.inputs, field="WorkStep.inputs"),
        )
        object.__setattr__(
            self,
            "outputs",
            _normalize_outputs(self.outputs, field="WorkStep.outputs"),
        )
        object.__setattr__(
            self,
            "depends_on",
            _normalize_ref_tuple(self.depends_on, field="WorkStep.depends_on"),
        )
        if self.step_ref in self.depends_on:
            raise ValidationError("WorkStep cannot depend on itself")
        if type(self.continuation) is not WorkContinuationMode:
            raise ValidationError("WorkStep.continuation must be a WorkContinuationMode")
        _require_text(self.completion_contract, field="WorkStep.completion_contract")
        _require_text(self.description, field="WorkStep.description")

        for work_input in self.inputs:
            if type(work_input) is WorkSymbolicInput:
                if work_input.reference.resolved_intent_identity != self.resolved_intent_identity:
                    raise ValidationError(
                        "WorkStep symbolic inputs must belong to the same ResolvedIntent"
                    )
        for output in self.outputs:
            if output.reference.resolved_intent_identity != self.resolved_intent_identity:
                raise ValidationError(
                    "WorkStep outputs must belong to the same ResolvedIntent"
                )

    def to_primitive(self) -> dict[str, object]:
        return {
            "completion_contract": self.completion_contract,
            "continuation": self.continuation.value,
            "depends_on": [item.to_primitive() for item in self.depends_on],
            "description": self.description,
            "inputs": [item.to_primitive() for item in self.inputs],
            "operation": self.operation,
            "outputs": [item.to_primitive() for item in self.outputs],
            "resolved_intent_identity": self.resolved_intent_identity.to_primitive(),
            "schema": self.SCHEMA,
            "scope": self.scope,
            "step_ref": self.step_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(cls, value: object, *, field: str = "WorkStep") -> "WorkStep":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "resolved_intent_identity",
                "step_ref",
                "operation",
                "scope",
                "inputs",
                "outputs",
                "depends_on",
                "continuation",
                "completion_contract",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["continuation"]) is not str:
            raise SerializationError(f"{field}.continuation must be a string")
        try:
            continuation = WorkContinuationMode(obj["continuation"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.continuation") from exc

        inputs = _expect_array(obj["inputs"], field=f"{field}.inputs")
        outputs = _expect_array(obj["outputs"], field=f"{field}.outputs")
        dependencies = _expect_array(obj["depends_on"], field=f"{field}.depends_on")
        try:
            return cls(
                resolved_intent_identity=RecordIdentity.from_primitive(
                    obj["resolved_intent_identity"],
                    field=f"{field}.resolved_intent_identity",
                ),
                step_ref=StableRef.from_primitive(obj["step_ref"], field=f"{field}.step_ref"),
                operation=obj["operation"],
                scope=obj["scope"],
                inputs=tuple(
                    _work_input_from_primitive(item, field=f"{field}.inputs[{index}]")
                    for index, item in enumerate(inputs)
                ),
                outputs=tuple(
                    WorkOutput.from_primitive(item, field=f"{field}.outputs[{index}]")
                    for index, item in enumerate(outputs)
                ),
                depends_on=tuple(
                    StableRef.from_primitive(item, field=f"{field}.depends_on[{index}]")
                    for index, item in enumerate(dependencies)
                ),
                continuation=continuation,
                completion_contract=obj["completion_contract"],
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "WorkStep":
        return cls.from_primitive(parse_json_object(data))


def _ref_key(value: StableRef) -> tuple[str, str]:
    return value.namespace, value.value


@dataclass(frozen=True, slots=True)
class WorkPlan(_CanonicalWorkRecord):
    SCHEMA: ClassVar[str] = "irr.work_plan.v1"

    resolved_intent_identity: RecordIdentity
    plan_ref: StableRef
    steps: tuple[WorkStep, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError("WorkPlan.resolved_intent_identity must be a RecordIdentity")
        if type(self.plan_ref) is not StableRef:
            raise ValidationError("WorkPlan.plan_ref must be a StableRef")
        if type(self.steps) is not tuple:
            raise ValidationError("WorkPlan.steps must be a tuple")
        if not self.steps:
            raise ValidationError("WorkPlan.steps must not be empty")
        if not all(type(item) is WorkStep for item in self.steps):
            raise ValidationError("WorkPlan.steps must contain WorkStep values")

        steps = cast(tuple[WorkStep, ...], self.steps)
        if any(step.resolved_intent_identity != self.resolved_intent_identity for step in steps):
            raise ValidationError("WorkPlan steps must belong to the same ResolvedIntent")

        refs = [step.step_ref for step in steps]
        if len(set(refs)) != len(refs):
            raise ValidationError("WorkPlan.steps must not contain duplicate step_ref values")

        step_map = {step.step_ref: step for step in steps}
        for step in steps:
            missing = [dependency for dependency in step.depends_on if dependency not in step_map]
            if missing:
                raise ValidationError(
                    "WorkPlan dependency must reference another step in the same plan"
                )

        visiting: set[StableRef] = set()
        visited: set[StableRef] = set()

        def visit(step_ref: StableRef) -> None:
            if step_ref in visiting:
                raise ValidationError("WorkPlan dependency graph must be acyclic")
            if step_ref in visited:
                return
            visiting.add(step_ref)
            for dependency in step_map[step_ref].depends_on:
                visit(dependency)
            visiting.remove(step_ref)
            visited.add(step_ref)

        for step_ref in step_map:
            visit(step_ref)

        symbolic_definitions: dict[StableRef, RecordIdentity] = {}
        output_producers: dict[StableRef, StableRef] = {}

        def admit_symbolic(reference: SymbolicReference) -> None:
            previous = symbolic_definitions.get(reference.slot_ref)
            if previous is not None and previous != reference.identity:
                raise ValidationError(
                    "WorkPlan cannot assign conflicting semantics to the same symbolic slot"
                )
            symbolic_definitions[reference.slot_ref] = reference.identity

        for step in steps:
            for work_input in step.inputs:
                if type(work_input) is WorkSymbolicInput:
                    admit_symbolic(work_input.reference)
            for output in step.outputs:
                admit_symbolic(output.reference)
                if output.reference.slot_ref in output_producers:
                    raise ValidationError(
                        "WorkPlan cannot publish the same symbolic output slot from multiple steps"
                    )
                output_producers[output.reference.slot_ref] = step.step_ref

        ancestor_cache: dict[StableRef, set[StableRef]] = {}

        def ancestors(step_ref: StableRef) -> set[StableRef]:
            cached = ancestor_cache.get(step_ref)
            if cached is not None:
                return cached
            result: set[StableRef] = set()
            for dependency in step_map[step_ref].depends_on:
                result.add(dependency)
                result.update(ancestors(dependency))
            ancestor_cache[step_ref] = result
            return result

        for step in steps:
            valid_ancestors = ancestors(step.step_ref)
            for work_input in step.inputs:
                if type(work_input) is not WorkSymbolicInput:
                    continue
                producer = output_producers.get(work_input.reference.slot_ref)
                if producer is None:
                    continue
                if producer not in valid_ancestors:
                    raise ValidationError(
                        "WorkStep internal symbolic input must depend on its producing step"
                    )

        object.__setattr__(
            self,
            "steps",
            tuple(sorted(steps, key=lambda item: _ref_key(item.step_ref))),
        )
        _require_text(self.description, field="WorkPlan.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "plan_ref": self.plan_ref.to_primitive(),
            "resolved_intent_identity": self.resolved_intent_identity.to_primitive(),
            "schema": self.SCHEMA,
            "steps": [step.to_primitive() for step in self.steps],
        }

    @classmethod
    def from_primitive(cls, value: object) -> "WorkPlan":
        obj = _expect_object(value, field="WorkPlan")
        _expect_exact_keys(
            obj,
            {"schema", "resolved_intent_identity", "plan_ref", "steps", "description"},
            field="WorkPlan",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported WorkPlan schema: {obj['schema']!r}")
        steps = _expect_array(obj["steps"], field="WorkPlan.steps")
        try:
            return cls(
                resolved_intent_identity=RecordIdentity.from_primitive(
                    obj["resolved_intent_identity"],
                    field="WorkPlan.resolved_intent_identity",
                ),
                plan_ref=StableRef.from_primitive(obj["plan_ref"], field="WorkPlan.plan_ref"),
                steps=tuple(
                    WorkStep.from_primitive(item, field=f"WorkPlan.steps[{index}]")
                    for index, item in enumerate(steps)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid WorkPlan") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "WorkPlan":
        return cls.from_primitive(parse_json_object(data))
