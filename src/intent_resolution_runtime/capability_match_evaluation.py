from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, TypeAlias, cast

from .canonical import canonical_json_bytes, parse_json_object
from .capability import CapabilityCatalogSnapshot
from .capability_match import CapabilityMatch, CapabilityRequirement
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef


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


def _stable_ref_key(value: StableRef) -> tuple[str, str]:
    return value.namespace, value.value


class _CanonicalCapabilityEvaluationRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class CapabilityMismatchKind(str, Enum):
    OPERATION_MISMATCH = "operation_mismatch"
    SCOPE_MISMATCH = "scope_mismatch"
    INPUT_MISMATCH = "input_mismatch"
    OUTPUT_MISMATCH = "output_mismatch"
    UNAVOIDABLE_EFFECT_MISMATCH = "unavoidable_effect_mismatch"
    COMPLETION_MISMATCH = "completion_mismatch"
    EXECUTION_BOUNDARY_MISMATCH = "execution_boundary_mismatch"
    INSUFFICIENT_SEMANTICS = "insufficient_semantics"
    MAPPING_AMBIGUITY = "mapping_ambiguity"


class CapabilityMatchIssueKind(str, Enum):
    NO_COMPATIBLE_CAPABILITY = "no_compatible_capability"
    MULTIPLE_COMPATIBLE_MATCHES = "multiple_compatible_matches"


@dataclass(frozen=True, slots=True)
class CapabilityMatchEvaluationAttribution(_CanonicalCapabilityEvaluationRecord):
    SCHEMA: ClassVar[str] = "irr.capability_match_evaluation_attribution.v1"

    evaluator_ref: StableRef
    evaluation_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.evaluator_ref) is not StableRef:
            raise ValidationError(
                "CapabilityMatchEvaluationAttribution.evaluator_ref must be a StableRef"
            )
        if type(self.evaluation_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityMatchEvaluationAttribution.evaluation_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "evaluation_event_ref": self.evaluation_event_ref.to_primitive(),
            "evaluator_ref": self.evaluator_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityMatchEvaluationAttribution"
    ) -> "CapabilityMatchEvaluationAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "evaluator_ref", "evaluation_event_ref"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                evaluator_ref=StableRef.from_primitive(
                    obj["evaluator_ref"], field=f"{field}.evaluator_ref"
                ),
                evaluation_event_ref=StableRef.from_primitive(
                    obj["evaluation_event_ref"],
                    field=f"{field}.evaluation_event_ref",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityMatchEvaluationAttribution":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityMismatchReason(_CanonicalCapabilityEvaluationRecord):
    SCHEMA: ClassVar[str] = "irr.capability_mismatch_reason.v1"

    kind: CapabilityMismatchKind
    scope: str
    description: str

    def __post_init__(self) -> None:
        if type(self.kind) is not CapabilityMismatchKind:
            raise ValidationError(
                "CapabilityMismatchReason.kind must be a CapabilityMismatchKind"
            )
        _require_text(self.scope, field="CapabilityMismatchReason.scope")
        _require_text(self.description, field="CapabilityMismatchReason.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "kind": self.kind.value,
            "schema": self.SCHEMA,
            "scope": self.scope,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityMismatchReason"
    ) -> "CapabilityMismatchReason":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"schema", "kind", "scope", "description"}, field=field)
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["kind"]) is not str:
            raise SerializationError(f"{field}.kind must be a string")
        try:
            kind = CapabilityMismatchKind(obj["kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.kind") from exc
        try:
            return cls(
                kind=kind,
                scope=obj["scope"],
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityMismatchReason":
        return cls.from_primitive(parse_json_object(data))


def _normalize_mismatch_reasons(
    value: object, *, field: str
) -> tuple[CapabilityMismatchReason, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if not all(type(item) is CapabilityMismatchReason for item in value):
        raise ValidationError(f"{field} must contain CapabilityMismatchReason values")
    items = cast(tuple[CapabilityMismatchReason, ...], value)
    keys = [(item.kind.value, item.scope, item.description) for item in items]
    if len(set(keys)) != len(keys):
        raise ValidationError(f"{field} must not contain duplicate reasons")
    return tuple(sorted(items, key=lambda item: (item.kind.value, item.scope, item.description)))


@dataclass(frozen=True, slots=True)
class CapabilityIncompatibleDescriptorAssessment(_CanonicalCapabilityEvaluationRecord):
    SCHEMA: ClassVar[str] = "irr.capability_incompatible_descriptor_assessment.v1"

    capability_ref: StableRef
    capability_contract_identity: RecordIdentity
    reasons: tuple[CapabilityMismatchReason, ...]

    def __post_init__(self) -> None:
        if type(self.capability_ref) is not StableRef:
            raise ValidationError(
                "CapabilityIncompatibleDescriptorAssessment.capability_ref must be a StableRef"
            )
        if type(self.capability_contract_identity) is not RecordIdentity:
            raise ValidationError(
                "CapabilityIncompatibleDescriptorAssessment.capability_contract_identity "
                "must be a RecordIdentity"
            )
        object.__setattr__(
            self,
            "reasons",
            _normalize_mismatch_reasons(
                self.reasons,
                field="CapabilityIncompatibleDescriptorAssessment.reasons",
            ),
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "capability_contract_identity": (
                self.capability_contract_identity.to_primitive()
            ),
            "capability_ref": self.capability_ref.to_primitive(),
            "reasons": [item.to_primitive() for item in self.reasons],
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "CapabilityIncompatibleDescriptorAssessment",
    ) -> "CapabilityIncompatibleDescriptorAssessment":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "capability_ref",
                "capability_contract_identity",
                "reasons",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        reasons = _expect_array(obj["reasons"], field=f"{field}.reasons")
        try:
            return cls(
                capability_ref=StableRef.from_primitive(
                    obj["capability_ref"], field=f"{field}.capability_ref"
                ),
                capability_contract_identity=RecordIdentity.from_primitive(
                    obj["capability_contract_identity"],
                    field=f"{field}.capability_contract_identity",
                ),
                reasons=tuple(
                    CapabilityMismatchReason.from_primitive(
                        item, field=f"{field}.reasons[{index}]"
                    )
                    for index, item in enumerate(reasons)
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityIncompatibleDescriptorAssessment":
        return cls.from_primitive(parse_json_object(data))


def _normalize_matches(
    value: object, *, field: str
) -> tuple[CapabilityMatch, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CapabilityMatch for item in value):
        raise ValidationError(f"{field} must contain CapabilityMatch values")
    items = cast(tuple[CapabilityMatch, ...], value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate matches")
    relation_keys = [
        (
            item.capability_ref,
            item.capability_contract_identity,
            item.scope_matches,
            item.input_matches,
            item.output_matches,
            item.effect_matches,
        )
        for item in items
    ]
    if len(set(relation_keys)) != len(relation_keys):
        raise ValidationError(
            f"{field} must not repeat the same semantic match relation under "
            "different occurrence attribution or description"
        )
    return tuple(sorted(items, key=lambda item: item.identity.digest))


def _normalize_incompatible_assessments(
    value: object, *, field: str
) -> tuple[CapabilityIncompatibleDescriptorAssessment, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(
        type(item) is CapabilityIncompatibleDescriptorAssessment for item in value
    ):
        raise ValidationError(
            f"{field} must contain CapabilityIncompatibleDescriptorAssessment values"
        )
    items = cast(tuple[CapabilityIncompatibleDescriptorAssessment, ...], value)
    refs = [item.capability_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(
            f"{field} must not assess one capability_ref as incompatible more than once"
        )
    return tuple(sorted(items, key=lambda item: _stable_ref_key(item.capability_ref)))


@dataclass(frozen=True, slots=True)
class CapabilityMatchEvaluation(_CanonicalCapabilityEvaluationRecord):
    SCHEMA: ClassVar[str] = "irr.capability_match_evaluation.v1"

    attribution: CapabilityMatchEvaluationAttribution
    requirement: CapabilityRequirement
    catalog_snapshot: CapabilityCatalogSnapshot
    compatible_matches: tuple[CapabilityMatch, ...]
    incompatible_assessments: tuple[CapabilityIncompatibleDescriptorAssessment, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not CapabilityMatchEvaluationAttribution:
            raise ValidationError(
                "CapabilityMatchEvaluation.attribution must be a "
                "CapabilityMatchEvaluationAttribution"
            )
        if type(self.requirement) is not CapabilityRequirement:
            raise ValidationError(
                "CapabilityMatchEvaluation.requirement must be a CapabilityRequirement"
            )
        if type(self.catalog_snapshot) is not CapabilityCatalogSnapshot:
            raise ValidationError(
                "CapabilityMatchEvaluation.catalog_snapshot must be a CapabilityCatalogSnapshot"
            )

        matches = _normalize_matches(
            self.compatible_matches,
            field="CapabilityMatchEvaluation.compatible_matches",
        )
        for match in matches:
            if match.requirement != self.requirement:
                raise ValidationError(
                    "CapabilityMatchEvaluation matches must use the exact evaluation requirement"
                )
            if match.catalog_snapshot != self.catalog_snapshot:
                raise ValidationError(
                    "CapabilityMatchEvaluation matches must use the exact evaluation Catalog Snapshot"
                )
        object.__setattr__(self, "compatible_matches", matches)

        incompatible = _normalize_incompatible_assessments(
            self.incompatible_assessments,
            field="CapabilityMatchEvaluation.incompatible_assessments",
        )
        object.__setattr__(self, "incompatible_assessments", incompatible)

        descriptors = {
            item.capability_ref: item for item in self.catalog_snapshot.descriptors
        }
        compatible_refs = {item.capability_ref for item in matches}
        incompatible_refs = {item.capability_ref for item in incompatible}
        if compatible_refs & incompatible_refs:
            raise ValidationError(
                "CapabilityMatchEvaluation cannot classify one descriptor as both "
                "compatible and incompatible"
            )
        if compatible_refs | incompatible_refs != set(descriptors):
            raise ValidationError(
                "CapabilityMatchEvaluation must assess every descriptor in the exact "
                "Catalog Snapshot"
            )
        for assessment in incompatible:
            descriptor = descriptors[assessment.capability_ref]
            if descriptor.identity != assessment.capability_contract_identity:
                raise ValidationError(
                    "CapabilityMatchEvaluation incompatible assessment must pin the "
                    "exact Catalog descriptor identity"
                )

        _require_text(self.description, field="CapabilityMatchEvaluation.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "catalog_snapshot": self.catalog_snapshot.to_primitive(),
            "compatible_matches": [
                item.to_primitive() for item in self.compatible_matches
            ],
            "description": self.description,
            "incompatible_assessments": [
                item.to_primitive() for item in self.incompatible_assessments
            ],
            "requirement": self.requirement.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityMatchEvaluation"
    ) -> "CapabilityMatchEvaluation":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "attribution",
                "requirement",
                "catalog_snapshot",
                "compatible_matches",
                "incompatible_assessments",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        matches = _expect_array(
            obj["compatible_matches"], field=f"{field}.compatible_matches"
        )
        incompatible = _expect_array(
            obj["incompatible_assessments"],
            field=f"{field}.incompatible_assessments",
        )
        try:
            return cls(
                attribution=CapabilityMatchEvaluationAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                requirement=CapabilityRequirement.from_primitive(
                    obj["requirement"], field=f"{field}.requirement"
                ),
                catalog_snapshot=CapabilityCatalogSnapshot.from_primitive(
                    obj["catalog_snapshot"], field=f"{field}.catalog_snapshot"
                ),
                compatible_matches=tuple(
                    CapabilityMatch.from_primitive(
                        item, field=f"{field}.compatible_matches[{index}]"
                    )
                    for index, item in enumerate(matches)
                ),
                incompatible_assessments=tuple(
                    CapabilityIncompatibleDescriptorAssessment.from_primitive(
                        item,
                        field=f"{field}.incompatible_assessments[{index}]",
                    )
                    for index, item in enumerate(incompatible)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityMatchEvaluation":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityMatchIssue(_CanonicalCapabilityEvaluationRecord):
    SCHEMA: ClassVar[str] = "irr.capability_match_issue.v1"

    evaluation: CapabilityMatchEvaluation
    kind: CapabilityMatchIssueKind

    def __post_init__(self) -> None:
        if type(self.evaluation) is not CapabilityMatchEvaluation:
            raise ValidationError(
                "CapabilityMatchIssue.evaluation must be a CapabilityMatchEvaluation"
            )
        if type(self.kind) is not CapabilityMatchIssueKind:
            raise ValidationError(
                "CapabilityMatchIssue.kind must be a CapabilityMatchIssueKind"
            )
        count = len(self.evaluation.compatible_matches)
        if self.kind is CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY:
            if count != 0:
                raise ValidationError(
                    "no_compatible_capability issue requires zero compatible matches"
                )
        elif count < 2:
            raise ValidationError(
                "multiple_compatible_matches issue requires at least two compatible matches"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "evaluation": self.evaluation.to_primitive(),
            "kind": self.kind.value,
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityMatchIssue"
    ) -> "CapabilityMatchIssue":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"schema", "evaluation", "kind"}, field=field)
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["kind"]) is not str:
            raise SerializationError(f"{field}.kind must be a string")
        try:
            kind = CapabilityMatchIssueKind(obj["kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.kind") from exc
        try:
            return cls(
                evaluation=CapabilityMatchEvaluation.from_primitive(
                    obj["evaluation"], field=f"{field}.evaluation"
                ),
                kind=kind,
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityMatchIssue":
        return cls.from_primitive(parse_json_object(data))


CapabilityMatchEvaluationResult: TypeAlias = CapabilityMatch | CapabilityMatchIssue


def evaluate_capability_match_evaluation(
    evaluation: CapabilityMatchEvaluation,
) -> CapabilityMatchEvaluationResult:
    if type(evaluation) is not CapabilityMatchEvaluation:
        raise ValidationError(
            "evaluate_capability_match_evaluation requires a CapabilityMatchEvaluation"
        )
    count = len(evaluation.compatible_matches)
    if count == 1:
        return evaluation.compatible_matches[0]
    if count == 0:
        return CapabilityMatchIssue(
            evaluation=evaluation,
            kind=CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY,
        )
    return CapabilityMatchIssue(
        evaluation=evaluation,
        kind=CapabilityMatchIssueKind.MULTIPLE_COMPATIBLE_MATCHES,
    )
