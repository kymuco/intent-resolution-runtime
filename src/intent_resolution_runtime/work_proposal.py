from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, cast

from .canonical import canonical_json_bytes, parse_json_object
from .capability_match import CapabilityMatch
from .capability_match_evaluation import (
    CapabilityMatchEvaluation,
    evaluate_capability_match_evaluation,
)
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef
from .work import WorkPlan


def _reject_surrogates(value: str, *, field: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValidationError(f"{field} must contain only Unicode scalar values")


def _require_text(value: object, *, field: str) -> str:
    if type(value) is not str:
        raise ValidationError(f"{field} must be a string")
    _reject_surrogates(value, field=field)
    if not value.strip():
        raise ValidationError(f"{field} must contain non-whitespace text")
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


def _ref_key(value: StableRef) -> tuple[str, str]:
    return value.namespace, value.value


class _CanonicalWorkProposalRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class WorkProposalMaterialKind(str, Enum):
    AFFECTED_RESOURCE = "affected_resource"
    DATA_FLOW = "data_flow"
    DISCLOSURE = "disclosure"
    RECIPIENT = "recipient"
    UNCERTAINTY = "uncertainty"
    OTHER_EXPLICIT = "other_explicit"


@dataclass(frozen=True, slots=True)
class WorkProposalAttribution(_CanonicalWorkProposalRecord):
    SCHEMA: ClassVar[str] = "irr.work_proposal_attribution.v1"

    proposer_ref: StableRef
    proposal_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.proposer_ref) is not StableRef:
            raise ValidationError("WorkProposalAttribution.proposer_ref must be a StableRef")
        if type(self.proposal_event_ref) is not StableRef:
            raise ValidationError(
                "WorkProposalAttribution.proposal_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "proposal_event_ref": self.proposal_event_ref.to_primitive(),
            "proposer_ref": self.proposer_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "WorkProposalAttribution"
    ) -> "WorkProposalAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "proposer_ref", "proposal_event_ref"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                proposer_ref=StableRef.from_primitive(
                    obj["proposer_ref"], field=f"{field}.proposer_ref"
                ),
                proposal_event_ref=StableRef.from_primitive(
                    obj["proposal_event_ref"], field=f"{field}.proposal_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "WorkProposalAttribution":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class ProposedWorkStep(_CanonicalWorkProposalRecord):
    SCHEMA: ClassVar[str] = "irr.proposed_work_step.v1"

    step_ref: StableRef
    capability_evaluation: CapabilityMatchEvaluation

    def __post_init__(self) -> None:
        if type(self.step_ref) is not StableRef:
            raise ValidationError("ProposedWorkStep.step_ref must be a StableRef")
        if type(self.capability_evaluation) is not CapabilityMatchEvaluation:
            raise ValidationError(
                "ProposedWorkStep.capability_evaluation must be a CapabilityMatchEvaluation"
            )
        result = evaluate_capability_match_evaluation(self.capability_evaluation)
        if type(result) is not CapabilityMatch:
            raise ValidationError(
                "ProposedWorkStep requires exactly one admitted CapabilityMatch"
            )
        if result.requirement.step_ref != self.step_ref:
            raise ValidationError(
                "ProposedWorkStep capability evaluation must belong to the selected WorkStep"
            )

    @property
    def capability_match(self) -> CapabilityMatch:
        result = evaluate_capability_match_evaluation(self.capability_evaluation)
        if type(result) is not CapabilityMatch:
            raise AssertionError("validated ProposedWorkStep lost its exact CapabilityMatch")
        return result

    def to_primitive(self) -> dict[str, object]:
        return {
            "capability_evaluation": self.capability_evaluation.to_primitive(),
            "schema": self.SCHEMA,
            "step_ref": self.step_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "ProposedWorkStep"
    ) -> "ProposedWorkStep":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "step_ref", "capability_evaluation"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                step_ref=StableRef.from_primitive(
                    obj["step_ref"], field=f"{field}.step_ref"
                ),
                capability_evaluation=CapabilityMatchEvaluation.from_primitive(
                    obj["capability_evaluation"],
                    field=f"{field}.capability_evaluation",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "ProposedWorkStep":
        return cls.from_primitive(parse_json_object(data))


def _normalize_step_refs(value: object, *, field: str) -> tuple[StableRef, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if not all(type(item) is StableRef for item in value):
        raise ValidationError(f"{field} must contain StableRef values")
    items = cast(tuple[StableRef, ...], value)
    if len(set(items)) != len(items):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(items, key=_ref_key))


@dataclass(frozen=True, slots=True)
class WorkProposalMaterial(_CanonicalWorkProposalRecord):
    SCHEMA: ClassVar[str] = "irr.work_proposal_material.v1"

    material_ref: StableRef
    kind: WorkProposalMaterialKind
    step_refs: tuple[StableRef, ...]
    source_ref: StableRef
    source_identity: RecordIdentity
    scope: str
    statement: str

    def __post_init__(self) -> None:
        if type(self.material_ref) is not StableRef:
            raise ValidationError("WorkProposalMaterial.material_ref must be a StableRef")
        if type(self.kind) is not WorkProposalMaterialKind:
            raise ValidationError(
                "WorkProposalMaterial.kind must be a WorkProposalMaterialKind"
            )
        object.__setattr__(
            self,
            "step_refs",
            _normalize_step_refs(
                self.step_refs, field="WorkProposalMaterial.step_refs"
            ),
        )
        if type(self.source_ref) is not StableRef:
            raise ValidationError("WorkProposalMaterial.source_ref must be a StableRef")
        if type(self.source_identity) is not RecordIdentity:
            raise ValidationError(
                "WorkProposalMaterial.source_identity must be a RecordIdentity"
            )
        _require_text(self.scope, field="WorkProposalMaterial.scope")
        _require_text(self.statement, field="WorkProposalMaterial.statement")

    def to_primitive(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "material_ref": self.material_ref.to_primitive(),
            "schema": self.SCHEMA,
            "scope": self.scope,
            "source_identity": self.source_identity.to_primitive(),
            "source_ref": self.source_ref.to_primitive(),
            "statement": self.statement,
            "step_refs": [item.to_primitive() for item in self.step_refs],
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "WorkProposalMaterial"
    ) -> "WorkProposalMaterial":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "material_ref",
                "kind",
                "step_refs",
                "source_ref",
                "source_identity",
                "scope",
                "statement",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["kind"]) is not str:
            raise SerializationError(f"{field}.kind must be a string")
        try:
            kind = WorkProposalMaterialKind(obj["kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.kind") from exc
        refs = _expect_array(obj["step_refs"], field=f"{field}.step_refs")
        try:
            return cls(
                material_ref=StableRef.from_primitive(
                    obj["material_ref"], field=f"{field}.material_ref"
                ),
                kind=kind,
                step_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.step_refs[{index}]"
                    )
                    for index, item in enumerate(refs)
                ),
                source_ref=StableRef.from_primitive(
                    obj["source_ref"], field=f"{field}.source_ref"
                ),
                source_identity=RecordIdentity.from_primitive(
                    obj["source_identity"], field=f"{field}.source_identity"
                ),
                scope=obj["scope"],
                statement=obj["statement"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "WorkProposalMaterial":
        return cls.from_primitive(parse_json_object(data))


def _normalize_proposed_steps(
    value: object, *, field: str
) -> tuple[ProposedWorkStep, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if not all(type(item) is ProposedWorkStep for item in value):
        raise ValidationError(f"{field} must contain ProposedWorkStep values")
    items = cast(tuple[ProposedWorkStep, ...], value)
    refs = [item.step_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(
            f"{field} must not contain more than one capability relation per WorkStep"
        )
    return tuple(sorted(items, key=lambda item: _ref_key(item.step_ref)))


def _normalize_material(
    value: object, *, field: str
) -> tuple[WorkProposalMaterial, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is WorkProposalMaterial for item in value):
        raise ValidationError(f"{field} must contain WorkProposalMaterial values")
    items = cast(tuple[WorkProposalMaterial, ...], value)
    refs = [item.material_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate material_ref values")
    return tuple(sorted(items, key=lambda item: _ref_key(item.material_ref)))


@dataclass(frozen=True, slots=True)
class WorkProposal(_CanonicalWorkProposalRecord):
    SCHEMA: ClassVar[str] = "irr.work_proposal.v1"

    attribution: WorkProposalAttribution
    work_plan: WorkPlan
    proposed_steps: tuple[ProposedWorkStep, ...]
    authority_material: tuple[WorkProposalMaterial, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not WorkProposalAttribution:
            raise ValidationError(
                "WorkProposal.attribution must be a WorkProposalAttribution"
            )
        if type(self.work_plan) is not WorkPlan:
            raise ValidationError("WorkProposal.work_plan must be a WorkPlan")

        proposed_steps = _normalize_proposed_steps(
            self.proposed_steps, field="WorkProposal.proposed_steps"
        )
        plan_refs = {step.step_ref for step in self.work_plan.steps}
        proposed_refs = {item.step_ref for item in proposed_steps}
        if not proposed_refs.issubset(plan_refs):
            raise ValidationError(
                "WorkProposal proposed steps must belong to the exact WorkPlan"
            )
        catalog_snapshots = []
        for proposed in proposed_steps:
            if proposed.capability_evaluation.requirement.work_plan != self.work_plan:
                raise ValidationError(
                    "WorkProposal capability evaluations must preserve the exact WorkPlan"
                )
            if proposed.capability_evaluation.requirement.step_ref != proposed.step_ref:
                raise ValidationError(
                    "WorkProposal capability evaluation must belong to its proposed WorkStep"
                )
            catalog_snapshots.append(proposed.capability_evaluation.catalog_snapshot)
        if any(snapshot != catalog_snapshots[0] for snapshot in catalog_snapshots[1:]):
            raise ValidationError(
                "WorkProposal proposed steps must use one exact Capability Catalog Snapshot"
            )
        object.__setattr__(self, "proposed_steps", proposed_steps)

        material = _normalize_material(
            self.authority_material, field="WorkProposal.authority_material"
        )
        for item in material:
            if not set(item.step_refs).issubset(proposed_refs):
                raise ValidationError(
                    "WorkProposal authority material may reference only proposed WorkSteps"
                )
        object.__setattr__(self, "authority_material", material)
        _require_text(self.description, field="WorkProposal.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "authority_material": [
                item.to_primitive() for item in self.authority_material
            ],
            "description": self.description,
            "proposed_steps": [item.to_primitive() for item in self.proposed_steps],
            "schema": self.SCHEMA,
            "work_plan": self.work_plan.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "WorkProposal"
    ) -> "WorkProposal":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "attribution",
                "work_plan",
                "proposed_steps",
                "authority_material",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        steps = _expect_array(obj["proposed_steps"], field=f"{field}.proposed_steps")
        material = _expect_array(
            obj["authority_material"], field=f"{field}.authority_material"
        )
        try:
            return cls(
                attribution=WorkProposalAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                work_plan=WorkPlan.from_primitive(obj["work_plan"]),
                proposed_steps=tuple(
                    ProposedWorkStep.from_primitive(
                        item, field=f"{field}.proposed_steps[{index}]"
                    )
                    for index, item in enumerate(steps)
                ),
                authority_material=tuple(
                    WorkProposalMaterial.from_primitive(
                        item, field=f"{field}.authority_material[{index}]"
                    )
                    for index, item in enumerate(material)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "WorkProposal":
        return cls.from_primitive(parse_json_object(data))
