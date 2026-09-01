from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, cast

from .binding import BoundValue
from .canonical import canonical_json_bytes, parse_json_object
from .capability_match import CapabilityMatch
from .capability_match_evaluation import (
    CapabilityMatchEvaluation,
    evaluate_capability_match_evaluation,
)
from .errors import SerializationError, ValidationError
from .governance import Authorization
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef
from .work import WorkStep, WorkSymbolicInput


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


class _CanonicalAttemptRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class CapabilityAttemptAttribution(_CanonicalAttemptRecord):
    """Attributed executor and unique occurrence for one capability-backed attempt."""

    SCHEMA: ClassVar[str] = "irr.capability_attempt_attribution.v1"

    executor_ref: StableRef
    attempt_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.executor_ref) is not StableRef:
            raise ValidationError(
                "CapabilityAttemptAttribution.executor_ref must be a StableRef"
            )
        if type(self.attempt_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityAttemptAttribution.attempt_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "attempt_event_ref": self.attempt_event_ref.to_primitive(),
            "executor_ref": self.executor_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityAttemptAttribution"
    ) -> "CapabilityAttemptAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "executor_ref", "attempt_event_ref"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                executor_ref=StableRef.from_primitive(
                    obj["executor_ref"], field=f"{field}.executor_ref"
                ),
                attempt_event_ref=StableRef.from_primitive(
                    obj["attempt_event_ref"], field=f"{field}.attempt_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityAttemptAttribution":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class AttemptBoundInput(_CanonicalAttemptRecord):
    """Exact late-bound value supplied to one named symbolic WorkStep input."""

    SCHEMA: ClassVar[str] = "irr.attempt_bound_input.v1"

    input_name: str
    bound_value: BoundValue

    def __post_init__(self) -> None:
        _require_token(self.input_name, field="AttemptBoundInput.input_name")
        if type(self.bound_value) is not BoundValue:
            raise ValidationError("AttemptBoundInput.bound_value must be a BoundValue")

    def to_primitive(self) -> dict[str, object]:
        return {
            "bound_value": self.bound_value.to_primitive(),
            "input_name": self.input_name,
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "AttemptBoundInput"
    ) -> "AttemptBoundInput":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"schema", "input_name", "bound_value"}, field=field)
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                input_name=obj["input_name"],
                bound_value=BoundValue.from_primitive(obj["bound_value"]),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "AttemptBoundInput":
        return cls.from_primitive(parse_json_object(data))


def _normalize_bound_inputs(
    value: object, *, field: str
) -> tuple[AttemptBoundInput, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is AttemptBoundInput for item in value):
        raise ValidationError(f"{field} must contain AttemptBoundInput values")
    items = cast(tuple[AttemptBoundInput, ...], value)
    names = [item.input_name for item in items]
    if len(set(names)) != len(names):
        raise ValidationError(f"{field} must not contain duplicate input_name values")
    return tuple(sorted(items, key=lambda item: item.input_name))


def _normalize_authorizations(
    value: object, *, field: str
) -> tuple[Authorization, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is Authorization for item in value):
        raise ValidationError(f"{field} must contain Authorization values")
    items = cast(tuple[Authorization, ...], value)
    if len(items) > 1:
        raise ValidationError(
            f"{field} supports at most one Authorization in v1; "
            "multi-authority composition is not frozen"
        )
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(items, key=lambda item: item.identity.digest))


@dataclass(frozen=True, slots=True)
class CapabilityAttempt(_CanonicalAttemptRecord):
    """One attributable effort to invoke one exact uniquely matched WorkStep."""

    SCHEMA: ClassVar[str] = "irr.capability_attempt.v1"

    attribution: CapabilityAttemptAttribution
    capability_evaluation: CapabilityMatchEvaluation
    step_ref: StableRef
    bound_inputs: tuple[AttemptBoundInput, ...]
    presented_authorizations: tuple[Authorization, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not CapabilityAttemptAttribution:
            raise ValidationError(
                "CapabilityAttempt.attribution must be a CapabilityAttemptAttribution"
            )
        if type(self.capability_evaluation) is not CapabilityMatchEvaluation:
            raise ValidationError(
                "CapabilityAttempt.capability_evaluation must be a CapabilityMatchEvaluation"
            )
        if type(self.step_ref) is not StableRef:
            raise ValidationError("CapabilityAttempt.step_ref must be a StableRef")

        match = evaluate_capability_match_evaluation(self.capability_evaluation)
        if type(match) is not CapabilityMatch:
            raise ValidationError(
                "CapabilityAttempt requires exactly one admitted CapabilityMatch"
            )
        if self.capability_evaluation.requirement.step_ref != self.step_ref:
            raise ValidationError(
                "CapabilityAttempt.step_ref must equal the exact capability requirement WorkStep"
            )
        if (
            self.attribution.attempt_event_ref
            == self.capability_evaluation.attribution.evaluation_event_ref
        ):
            raise ValidationError(
                "CapabilityAttempt occurrence must differ from CapabilityMatchEvaluation occurrence"
            )

        work_step = self.work_step
        symbolic_inputs = {
            item.name: item
            for item in work_step.inputs
            if type(item) is WorkSymbolicInput
        }
        bound_inputs = _normalize_bound_inputs(
            self.bound_inputs, field="CapabilityAttempt.bound_inputs"
        )
        if {item.input_name for item in bound_inputs} != set(symbolic_inputs):
            raise ValidationError(
                "CapabilityAttempt.bound_inputs must exactly cover all symbolic WorkStep inputs"
            )
        for bound_input in bound_inputs:
            symbolic = symbolic_inputs[bound_input.input_name]
            bound = bound_input.bound_value
            if bound.rule.symbolic_reference != symbolic.reference:
                raise ValidationError(
                    "CapabilityAttempt BoundValue must belong to the exact WorkSymbolicInput reference"
                )
            if bound.semantic_type != symbolic.reference.semantic_type:
                raise ValidationError(
                    "CapabilityAttempt BoundValue semantic type must match the WorkSymbolicInput"
                )
            if (
                bound.binding_attribution.binding_event_ref
                == self.attribution.attempt_event_ref
            ):
                raise ValidationError(
                    "CapabilityAttempt occurrence must differ from Binding occurrence"
                )
        object.__setattr__(self, "bound_inputs", bound_inputs)

        authorizations = _normalize_authorizations(
            self.presented_authorizations,
            field="CapabilityAttempt.presented_authorizations",
        )
        for authorization in authorizations:
            proposal = authorization.decision.proposal
            proposed_map = {item.step_ref: item for item in proposal.proposed_steps}
            if self.step_ref not in proposed_map:
                raise ValidationError(
                    "CapabilityAttempt Authorization proposal must include the attempted WorkStep"
                )
            proposed = proposed_map[self.step_ref]
            if proposed.capability_evaluation != self.capability_evaluation:
                raise ValidationError(
                    "CapabilityAttempt Authorization must bind the exact capability evaluation"
                )
            if self.step_ref not in authorization.authorized_step_refs:
                raise ValidationError(
                    "CapabilityAttempt Authorization must cover the attempted WorkStep"
                )
            if (
                proposal.attribution.proposal_event_ref
                == self.attribution.attempt_event_ref
            ):
                raise ValidationError(
                    "CapabilityAttempt occurrence must differ from WorkProposal occurrence"
                )
            if (
                authorization.decision.attribution.decision_event_ref
                == self.attribution.attempt_event_ref
            ):
                raise ValidationError(
                    "CapabilityAttempt occurrence must differ from GovernanceDecision occurrence"
                )
        object.__setattr__(self, "presented_authorizations", authorizations)

        _require_text(self.description, field="CapabilityAttempt.description")

    @property
    def work_step(self) -> WorkStep:
        return self.capability_evaluation.requirement.work_step

    @property
    def capability_match(self) -> CapabilityMatch:
        result = evaluate_capability_match_evaluation(self.capability_evaluation)
        if type(result) is not CapabilityMatch:
            raise AssertionError("validated CapabilityAttempt lost its exact CapabilityMatch")
        return result

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "bound_inputs": [item.to_primitive() for item in self.bound_inputs],
            "capability_evaluation": self.capability_evaluation.to_primitive(),
            "description": self.description,
            "presented_authorizations": [
                item.to_primitive() for item in self.presented_authorizations
            ],
            "schema": self.SCHEMA,
            "step_ref": self.step_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityAttempt"
    ) -> "CapabilityAttempt":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "attribution",
                "capability_evaluation",
                "step_ref",
                "bound_inputs",
                "presented_authorizations",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        bound_inputs = _expect_array(
            obj["bound_inputs"], field=f"{field}.bound_inputs"
        )
        authorizations = _expect_array(
            obj["presented_authorizations"],
            field=f"{field}.presented_authorizations",
        )
        try:
            return cls(
                attribution=CapabilityAttemptAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                capability_evaluation=CapabilityMatchEvaluation.from_primitive(
                    obj["capability_evaluation"],
                    field=f"{field}.capability_evaluation",
                ),
                step_ref=StableRef.from_primitive(
                    obj["step_ref"], field=f"{field}.step_ref"
                ),
                bound_inputs=tuple(
                    AttemptBoundInput.from_primitive(
                        item, field=f"{field}.bound_inputs[{index}]"
                    )
                    for index, item in enumerate(bound_inputs)
                ),
                presented_authorizations=tuple(
                    Authorization.from_primitive(
                        item, field=f"{field}.presented_authorizations[{index}]"
                    )
                    for index, item in enumerate(authorizations)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityAttempt":
        return cls.from_primitive(parse_json_object(data))
