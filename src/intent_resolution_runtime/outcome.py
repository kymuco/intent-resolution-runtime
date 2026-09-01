from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, cast

from .attempt import CapabilityAttempt
from .canonical import canonical_json_bytes, parse_json_object
from .context import EvidenceRelation, SourceAttribution
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


def _normalize_refs(
    value: object, *, field: str, nonempty: bool = False
) -> tuple[StableRef, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is StableRef for item in value):
        raise ValidationError(f"{field} must contain StableRef values")
    items = cast(tuple[StableRef, ...], value)
    if nonempty and not items:
        raise ValidationError(f"{field} must not be empty")
    if len(set(items)) != len(items):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(items, key=_ref_key))


def _normalize_identities(
    value: object, *, field: str
) -> tuple[RecordIdentity, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is RecordIdentity for item in value):
        raise ValidationError(f"{field} must contain RecordIdentity values")
    items = cast(tuple[RecordIdentity, ...], value)
    if len(set(items)) != len(items):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(items, key=str))


class _CanonicalOutcomeRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class OutcomeEvidenceRole(str, Enum):
    LIFECYCLE = "lifecycle"
    COMPLETION = "completion"
    EFFECT = "effect"
    PARTIAL_EFFECT = "partial_effect"
    UNCERTAINTY = "uncertainty"
    TRANSPORT = "transport"
    OTHER_EXPLICIT = "other_explicit"


class OutcomeLifecycleState(str, Enum):
    NORMAL_PROTOCOL_COMPLETED = "normal_protocol_completed"
    INTERRUPTED = "interrupted"


class OutcomeCompletionState(str, Enum):
    SATISFIED = "satisfied"
    NOT_SATISFIED = "not_satisfied"
    UNKNOWN = "unknown"


class OutcomeEffectCertainty(str, Enum):
    CONFIRMED_NOT_OCCURRED = "confirmed_not_occurred"
    CONFIRMED_PARTIAL = "confirmed_partial"
    CONFIRMED_OCCURRED = "confirmed_occurred"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CapabilityOutcomeAttribution(_CanonicalOutcomeRecord):
    SCHEMA: ClassVar[str] = "irr.capability_outcome_attribution.v1"

    evaluator_ref: StableRef
    outcome_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.evaluator_ref) is not StableRef:
            raise ValidationError(
                "CapabilityOutcomeAttribution.evaluator_ref must be a StableRef"
            )
        if type(self.outcome_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityOutcomeAttribution.outcome_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "evaluator_ref": self.evaluator_ref.to_primitive(),
            "outcome_event_ref": self.outcome_event_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityOutcomeAttribution"
    ) -> "CapabilityOutcomeAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "evaluator_ref", "outcome_event_ref"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                evaluator_ref=StableRef.from_primitive(
                    obj["evaluator_ref"], field=f"{field}.evaluator_ref"
                ),
                outcome_event_ref=StableRef.from_primitive(
                    obj["outcome_event_ref"], field=f"{field}.outcome_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityOutcomeAttribution":
        return cls.from_primitive(parse_json_object(data))


def _normalize_roles(
    value: object, *, field: str
) -> tuple[OutcomeEvidenceRole, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if not all(type(item) is OutcomeEvidenceRole for item in value):
        raise ValidationError(f"{field} must contain OutcomeEvidenceRole values")
    items = cast(tuple[OutcomeEvidenceRole, ...], value)
    if len(set(items)) != len(items):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(items, key=lambda item: item.value))


@dataclass(frozen=True, slots=True)
class OutcomeEvidence(_CanonicalOutcomeRecord):
    SCHEMA: ClassVar[str] = "irr.outcome_evidence.v1"

    evidence_ref: StableRef
    attribution: SourceAttribution
    source_identity: RecordIdentity
    relation: EvidenceRelation
    roles: tuple[OutcomeEvidenceRole, ...]
    temporal_basis_refs: tuple[RecordIdentity, ...]
    scope: str
    statement: str

    def __post_init__(self) -> None:
        if type(self.evidence_ref) is not StableRef:
            raise ValidationError("OutcomeEvidence.evidence_ref must be a StableRef")
        if type(self.attribution) is not SourceAttribution:
            raise ValidationError("OutcomeEvidence.attribution must be a SourceAttribution")
        if type(self.source_identity) is not RecordIdentity:
            raise ValidationError("OutcomeEvidence.source_identity must be a RecordIdentity")
        if type(self.relation) is not EvidenceRelation:
            raise ValidationError("OutcomeEvidence.relation must be an EvidenceRelation")
        object.__setattr__(
            self,
            "roles",
            _normalize_roles(self.roles, field="OutcomeEvidence.roles"),
        )
        object.__setattr__(
            self,
            "temporal_basis_refs",
            _normalize_identities(
                self.temporal_basis_refs,
                field="OutcomeEvidence.temporal_basis_refs",
            ),
        )
        _require_text(self.scope, field="OutcomeEvidence.scope")
        _require_text(self.statement, field="OutcomeEvidence.statement")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "evidence_ref": self.evidence_ref.to_primitive(),
            "relation": self.relation.value,
            "roles": [item.value for item in self.roles],
            "schema": self.SCHEMA,
            "scope": self.scope,
            "source_identity": self.source_identity.to_primitive(),
            "statement": self.statement,
            "temporal_basis_refs": [
                item.to_primitive() for item in self.temporal_basis_refs
            ],
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "OutcomeEvidence"
    ) -> "OutcomeEvidence":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "evidence_ref",
                "attribution",
                "source_identity",
                "relation",
                "roles",
                "temporal_basis_refs",
                "scope",
                "statement",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["relation"]) is not str:
            raise SerializationError(f"{field}.relation must be a string")
        try:
            relation = EvidenceRelation(obj["relation"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.relation") from exc
        roles = _expect_array(obj["roles"], field=f"{field}.roles")
        temporal = _expect_array(
            obj["temporal_basis_refs"], field=f"{field}.temporal_basis_refs"
        )
        try:
            parsed_roles = tuple(OutcomeEvidenceRole(item) for item in roles)
        except (ValueError, TypeError) as exc:
            raise SerializationError(f"unsupported {field}.roles") from exc
        try:
            return cls(
                evidence_ref=StableRef.from_primitive(
                    obj["evidence_ref"], field=f"{field}.evidence_ref"
                ),
                attribution=SourceAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                source_identity=RecordIdentity.from_primitive(
                    obj["source_identity"], field=f"{field}.source_identity"
                ),
                relation=relation,
                roles=parsed_roles,
                temporal_basis_refs=tuple(
                    RecordIdentity.from_primitive(
                        item, field=f"{field}.temporal_basis_refs[{index}]"
                    )
                    for index, item in enumerate(temporal)
                ),
                scope=obj["scope"],
                statement=obj["statement"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "OutcomeEvidence":
        return cls.from_primitive(parse_json_object(data))


def _normalize_evidence(
    value: object, *, field: str
) -> tuple[OutcomeEvidence, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if not all(type(item) is OutcomeEvidence for item in value):
        raise ValidationError(f"{field} must contain OutcomeEvidence values")
    items = cast(tuple[OutcomeEvidence, ...], value)
    refs = [item.evidence_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate evidence_ref values")
    return tuple(sorted(items, key=lambda item: _ref_key(item.evidence_ref)))


@dataclass(frozen=True, slots=True)
class OutcomeLifecycleAssessment(_CanonicalOutcomeRecord):
    SCHEMA: ClassVar[str] = "irr.outcome_lifecycle_assessment.v1"

    state: OutcomeLifecycleState
    evidence_refs: tuple[StableRef, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.state) is not OutcomeLifecycleState:
            raise ValidationError(
                "OutcomeLifecycleAssessment.state must be an OutcomeLifecycleState"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                self.evidence_refs,
                field="OutcomeLifecycleAssessment.evidence_refs",
                nonempty=True,
            ),
        )
        _require_text(self.description, field="OutcomeLifecycleAssessment.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "evidence_refs": [item.to_primitive() for item in self.evidence_refs],
            "schema": self.SCHEMA,
            "state": self.state.value,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "OutcomeLifecycleAssessment"
    ) -> "OutcomeLifecycleAssessment":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "state", "evidence_refs", "description"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["state"]) is not str:
            raise SerializationError(f"{field}.state must be a string")
        try:
            state = OutcomeLifecycleState(obj["state"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.state") from exc
        refs = _expect_array(obj["evidence_refs"], field=f"{field}.evidence_refs")
        try:
            return cls(
                state=state,
                evidence_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.evidence_refs[{index}]"
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
    ) -> "OutcomeLifecycleAssessment":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class OutcomeCompletionAssessment(_CanonicalOutcomeRecord):
    SCHEMA: ClassVar[str] = "irr.outcome_completion_assessment.v1"

    state: OutcomeCompletionState
    evidence_refs: tuple[StableRef, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.state) is not OutcomeCompletionState:
            raise ValidationError(
                "OutcomeCompletionAssessment.state must be an OutcomeCompletionState"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                self.evidence_refs,
                field="OutcomeCompletionAssessment.evidence_refs",
                nonempty=True,
            ),
        )
        _require_text(self.description, field="OutcomeCompletionAssessment.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "description": self.description,
            "evidence_refs": [item.to_primitive() for item in self.evidence_refs],
            "schema": self.SCHEMA,
            "state": self.state.value,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "OutcomeCompletionAssessment"
    ) -> "OutcomeCompletionAssessment":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "state", "evidence_refs", "description"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["state"]) is not str:
            raise SerializationError(f"{field}.state must be a string")
        try:
            state = OutcomeCompletionState(obj["state"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.state") from exc
        refs = _expect_array(obj["evidence_refs"], field=f"{field}.evidence_refs")
        try:
            return cls(
                state=state,
                evidence_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.evidence_refs[{index}]"
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
    ) -> "OutcomeCompletionAssessment":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class OutcomeEffectAssessment(_CanonicalOutcomeRecord):
    SCHEMA: ClassVar[str] = "irr.outcome_effect_assessment.v1"

    requested_effect_ref: StableRef
    certainty: OutcomeEffectCertainty
    evidence_refs: tuple[StableRef, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.requested_effect_ref) is not StableRef:
            raise ValidationError(
                "OutcomeEffectAssessment.requested_effect_ref must be a StableRef"
            )
        if type(self.certainty) is not OutcomeEffectCertainty:
            raise ValidationError(
                "OutcomeEffectAssessment.certainty must be an OutcomeEffectCertainty"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                self.evidence_refs,
                field="OutcomeEffectAssessment.evidence_refs",
                nonempty=True,
            ),
        )
        _require_text(self.description, field="OutcomeEffectAssessment.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "certainty": self.certainty.value,
            "description": self.description,
            "evidence_refs": [item.to_primitive() for item in self.evidence_refs],
            "requested_effect_ref": self.requested_effect_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "OutcomeEffectAssessment"
    ) -> "OutcomeEffectAssessment":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "requested_effect_ref",
                "certainty",
                "evidence_refs",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["certainty"]) is not str:
            raise SerializationError(f"{field}.certainty must be a string")
        try:
            certainty = OutcomeEffectCertainty(obj["certainty"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.certainty") from exc
        refs = _expect_array(obj["evidence_refs"], field=f"{field}.evidence_refs")
        try:
            return cls(
                requested_effect_ref=StableRef.from_primitive(
                    obj["requested_effect_ref"],
                    field=f"{field}.requested_effect_ref",
                ),
                certainty=certainty,
                evidence_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.evidence_refs[{index}]"
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
    ) -> "OutcomeEffectAssessment":
        return cls.from_primitive(parse_json_object(data))


def _normalize_effect_assessments(
    value: object, *, field: str
) -> tuple[OutcomeEffectAssessment, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is OutcomeEffectAssessment for item in value):
        raise ValidationError(f"{field} must contain OutcomeEffectAssessment values")
    items = cast(tuple[OutcomeEffectAssessment, ...], value)
    refs = [item.requested_effect_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(
            f"{field} must not assess one requested effect more than once"
        )
    return tuple(sorted(items, key=lambda item: _ref_key(item.requested_effect_ref)))


def _evidence_roles_for_refs(
    refs: tuple[StableRef, ...],
    evidence_map: dict[StableRef, OutcomeEvidence],
) -> set[OutcomeEvidenceRole]:
    return {
        role
        for ref in refs
        for role in evidence_map[ref].roles
    }


def _require_assessment_evidence(
    refs: tuple[StableRef, ...],
    *,
    evidence_map: dict[StableRef, OutcomeEvidence],
    field: str,
    required_any_role: tuple[OutcomeEvidenceRole, ...],
) -> None:
    missing = [ref for ref in refs if ref not in evidence_map]
    if missing:
        raise ValidationError(f"{field} must reference embedded OutcomeEvidence")
    roles = _evidence_roles_for_refs(refs, evidence_map)
    if not any(role in roles for role in required_any_role):
        allowed = ", ".join(role.value for role in required_any_role)
        raise ValidationError(
            f"{field} requires evidence with at least one admitted role: {allowed}"
        )


@dataclass(frozen=True, slots=True)
class CapabilityOutcome(_CanonicalOutcomeRecord):
    SCHEMA: ClassVar[str] = "irr.capability_outcome.v1"

    attribution: CapabilityOutcomeAttribution
    attempt: CapabilityAttempt
    evidence: tuple[OutcomeEvidence, ...]
    lifecycle: OutcomeLifecycleAssessment
    completion: OutcomeCompletionAssessment
    effect_assessments: tuple[OutcomeEffectAssessment, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not CapabilityOutcomeAttribution:
            raise ValidationError(
                "CapabilityOutcome.attribution must be a CapabilityOutcomeAttribution"
            )
        if type(self.attempt) is not CapabilityAttempt:
            raise ValidationError("CapabilityOutcome.attempt must be a CapabilityAttempt")
        if (
            self.attribution.outcome_event_ref
            == self.attempt.attribution.attempt_event_ref
        ):
            raise ValidationError(
                "CapabilityOutcome occurrence must differ from CapabilityAttempt occurrence"
            )

        evidence = _normalize_evidence(self.evidence, field="CapabilityOutcome.evidence")
        object.__setattr__(self, "evidence", evidence)
        evidence_map = {item.evidence_ref: item for item in evidence}

        if type(self.lifecycle) is not OutcomeLifecycleAssessment:
            raise ValidationError(
                "CapabilityOutcome.lifecycle must be an OutcomeLifecycleAssessment"
            )
        _require_assessment_evidence(
            self.lifecycle.evidence_refs,
            evidence_map=evidence_map,
            field="CapabilityOutcome.lifecycle.evidence_refs",
            required_any_role=(OutcomeEvidenceRole.LIFECYCLE,),
        )

        if type(self.completion) is not OutcomeCompletionAssessment:
            raise ValidationError(
                "CapabilityOutcome.completion must be an OutcomeCompletionAssessment"
            )
        completion_roles = (
            (OutcomeEvidenceRole.COMPLETION,)
            if self.completion.state
            in (OutcomeCompletionState.SATISFIED, OutcomeCompletionState.NOT_SATISFIED)
            else (OutcomeEvidenceRole.COMPLETION, OutcomeEvidenceRole.UNCERTAINTY)
        )
        _require_assessment_evidence(
            self.completion.evidence_refs,
            evidence_map=evidence_map,
            field="CapabilityOutcome.completion.evidence_refs",
            required_any_role=completion_roles,
        )

        effects = _normalize_effect_assessments(
            self.effect_assessments,
            field="CapabilityOutcome.effect_assessments",
        )
        requested_effects = {
            item.effect_ref: item
            for item in self.attempt.capability_evaluation.requirement.requested_effects
        }
        if {item.requested_effect_ref for item in effects} != set(requested_effects):
            raise ValidationError(
                "CapabilityOutcome.effect_assessments must exactly cover all requested effects"
            )
        for assessment in effects:
            required_roles = (
                (OutcomeEvidenceRole.PARTIAL_EFFECT, OutcomeEvidenceRole.EFFECT)
                if assessment.certainty is OutcomeEffectCertainty.CONFIRMED_PARTIAL
                else (
                    (OutcomeEvidenceRole.EFFECT,)
                    if assessment.certainty
                    in (
                        OutcomeEffectCertainty.CONFIRMED_NOT_OCCURRED,
                        OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                    )
                    else (
                        OutcomeEvidenceRole.EFFECT,
                        OutcomeEvidenceRole.UNCERTAINTY,
                    )
                )
            )
            _require_assessment_evidence(
                assessment.evidence_refs,
                evidence_map=evidence_map,
                field=(
                    "CapabilityOutcome.effect_assessments"
                    f"[{assessment.requested_effect_ref}]"
                ),
                required_any_role=required_roles,
            )
        object.__setattr__(self, "effect_assessments", effects)

        _require_text(self.description, field="CapabilityOutcome.description")

    @property
    def has_material_unknown(self) -> bool:
        return (
            self.completion.state is OutcomeCompletionState.UNKNOWN
            or any(
                item.certainty is OutcomeEffectCertainty.UNKNOWN
                for item in self.effect_assessments
            )
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "attempt": self.attempt.to_primitive(),
            "attribution": self.attribution.to_primitive(),
            "completion": self.completion.to_primitive(),
            "description": self.description,
            "effect_assessments": [
                item.to_primitive() for item in self.effect_assessments
            ],
            "evidence": [item.to_primitive() for item in self.evidence],
            "lifecycle": self.lifecycle.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CapabilityOutcome"
    ) -> "CapabilityOutcome":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "attribution",
                "attempt",
                "evidence",
                "lifecycle",
                "completion",
                "effect_assessments",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        evidence = _expect_array(obj["evidence"], field=f"{field}.evidence")
        effects = _expect_array(
            obj["effect_assessments"], field=f"{field}.effect_assessments"
        )
        try:
            return cls(
                attribution=CapabilityOutcomeAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                attempt=CapabilityAttempt.from_primitive(
                    obj["attempt"], field=f"{field}.attempt"
                ),
                evidence=tuple(
                    OutcomeEvidence.from_primitive(
                        item, field=f"{field}.evidence[{index}]"
                    )
                    for index, item in enumerate(evidence)
                ),
                lifecycle=OutcomeLifecycleAssessment.from_primitive(
                    obj["lifecycle"], field=f"{field}.lifecycle"
                ),
                completion=OutcomeCompletionAssessment.from_primitive(
                    obj["completion"], field=f"{field}.completion"
                ),
                effect_assessments=tuple(
                    OutcomeEffectAssessment.from_primitive(
                        item, field=f"{field}.effect_assessments[{index}]"
                    )
                    for index, item in enumerate(effects)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "CapabilityOutcome":
        return cls.from_primitive(parse_json_object(data))
