from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, cast

from .canonical import canonical_json_bytes, parse_json_object
from .errors import SerializationError, ValidationError
from .governance import Authorization
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


def _expect_exact_keys(
    value: dict[str, Any], expected: set[str], *, field: str
) -> None:
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


class _CanonicalApplicabilityRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class AuthorizationConditionDisposition(str, Enum):
    SATISFIED = "satisfied"
    UNSATISFIED = "unsatisfied"
    UNKNOWN = "unknown"


class AuthorizationApplicabilityResult(str, Enum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class AuthorizationApplicabilityAttribution(_CanonicalApplicabilityRecord):
    """Exact evaluator occurrence and exact current-use context snapshot."""

    SCHEMA: ClassVar[str] = "irr.authorization_applicability_attribution.v1"

    evaluator_ref: StableRef
    evaluation_event_ref: StableRef
    use_context_ref: StableRef
    use_context_identity: RecordIdentity

    def __post_init__(self) -> None:
        if type(self.evaluator_ref) is not StableRef:
            raise ValidationError(
                "AuthorizationApplicabilityAttribution.evaluator_ref must be a StableRef"
            )
        if type(self.evaluation_event_ref) is not StableRef:
            raise ValidationError(
                "AuthorizationApplicabilityAttribution.evaluation_event_ref must be a StableRef"
            )
        if type(self.use_context_ref) is not StableRef:
            raise ValidationError(
                "AuthorizationApplicabilityAttribution.use_context_ref must be a StableRef"
            )
        if type(self.use_context_identity) is not RecordIdentity:
            raise ValidationError(
                "AuthorizationApplicabilityAttribution.use_context_identity must be a RecordIdentity"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "evaluation_event_ref": self.evaluation_event_ref.to_primitive(),
            "evaluator_ref": self.evaluator_ref.to_primitive(),
            "schema": self.SCHEMA,
            "use_context_identity": self.use_context_identity.to_primitive(),
            "use_context_ref": self.use_context_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "AuthorizationApplicabilityAttribution",
    ) -> AuthorizationApplicabilityAttribution:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "evaluator_ref",
                "evaluation_event_ref",
                "use_context_ref",
                "use_context_identity",
            },
            field=field,
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
                use_context_ref=StableRef.from_primitive(
                    obj["use_context_ref"], field=f"{field}.use_context_ref"
                ),
                use_context_identity=RecordIdentity.from_primitive(
                    obj["use_context_identity"],
                    field=f"{field}.use_context_identity",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> AuthorizationApplicabilityAttribution:
        return cls.from_primitive(parse_json_object(data))


def _normalize_evidence_refs(
    value: object, *, field: str
) -> tuple[StableRef, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is StableRef for item in value):
        raise ValidationError(f"{field} must contain StableRef values")
    items = cast(tuple[StableRef, ...], value)
    if len(set(items)) != len(items):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(items, key=_ref_key))


@dataclass(frozen=True, slots=True)
class AuthorizationConditionAssessment(_CanonicalApplicabilityRecord):
    """Attributed result for one exact GovernanceDirective on one use snapshot."""

    SCHEMA: ClassVar[str] = "irr.authorization_condition_assessment.v1"

    directive_ref: StableRef
    disposition: AuthorizationConditionDisposition
    evidence_refs: tuple[StableRef, ...]
    rationale: str

    def __post_init__(self) -> None:
        if type(self.directive_ref) is not StableRef:
            raise ValidationError(
                "AuthorizationConditionAssessment.directive_ref must be a StableRef"
            )
        if type(self.disposition) is not AuthorizationConditionDisposition:
            raise ValidationError(
                "AuthorizationConditionAssessment.disposition must be an AuthorizationConditionDisposition"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_evidence_refs(
                self.evidence_refs,
                field="AuthorizationConditionAssessment.evidence_refs",
            ),
        )
        _require_text(
            self.rationale,
            field="AuthorizationConditionAssessment.rationale",
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "directive_ref": self.directive_ref.to_primitive(),
            "disposition": self.disposition.value,
            "evidence_refs": [item.to_primitive() for item in self.evidence_refs],
            "rationale": self.rationale,
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "AuthorizationConditionAssessment",
    ) -> AuthorizationConditionAssessment:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "directive_ref",
                "disposition",
                "evidence_refs",
                "rationale",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["disposition"]) is not str:
            raise SerializationError(f"{field}.disposition must be a string")
        try:
            disposition = AuthorizationConditionDisposition(obj["disposition"])
        except ValueError as exc:
            raise SerializationError(
                f"unsupported {field}.disposition"
            ) from exc
        evidence_refs = _expect_array(
            obj["evidence_refs"], field=f"{field}.evidence_refs"
        )
        try:
            return cls(
                directive_ref=StableRef.from_primitive(
                    obj["directive_ref"], field=f"{field}.directive_ref"
                ),
                disposition=disposition,
                evidence_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.evidence_refs[{index}]"
                    )
                    for index, item in enumerate(evidence_refs)
                ),
                rationale=obj["rationale"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> AuthorizationConditionAssessment:
        return cls.from_primitive(parse_json_object(data))


def _normalize_assessments(
    value: object, *, field: str
) -> tuple[AuthorizationConditionAssessment, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is AuthorizationConditionAssessment for item in value):
        raise ValidationError(
            f"{field} must contain AuthorizationConditionAssessment values"
        )
    items = cast(tuple[AuthorizationConditionAssessment, ...], value)
    refs = [item.directive_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate directive_ref values")
    return tuple(sorted(items, key=lambda item: _ref_key(item.directive_ref)))


@dataclass(frozen=True, slots=True)
class AuthorizationApplicabilityEvaluation(_CanonicalApplicabilityRecord):
    """Exact applicability evidence for one admitted Authorization and concrete use."""

    SCHEMA: ClassVar[str] = "irr.authorization_applicability_evaluation.v1"

    attribution: AuthorizationApplicabilityAttribution
    authorization: Authorization
    step_ref: StableRef
    condition_assessments: tuple[AuthorizationConditionAssessment, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not AuthorizationApplicabilityAttribution:
            raise ValidationError(
                "AuthorizationApplicabilityEvaluation.attribution must be an AuthorizationApplicabilityAttribution"
            )
        if type(self.authorization) is not Authorization:
            raise ValidationError(
                "AuthorizationApplicabilityEvaluation.authorization must be an Authorization"
            )
        if type(self.step_ref) is not StableRef:
            raise ValidationError(
                "AuthorizationApplicabilityEvaluation.step_ref must be a StableRef"
            )
        if self.step_ref not in self.authorization.authorized_step_refs:
            raise ValidationError(
                "AuthorizationApplicabilityEvaluation.step_ref must be covered by the exact Authorization"
            )
        if (
            self.attribution.evaluation_event_ref
            == self.authorization.decision.attribution.decision_event_ref
        ):
            raise ValidationError(
                "Authorization applicability occurrence must differ from GovernanceDecision occurrence"
            )

        assessments = _normalize_assessments(
            self.condition_assessments,
            field="AuthorizationApplicabilityEvaluation.condition_assessments",
        )
        expected_refs = {item.directive_ref for item in self.authorization.conditions}
        actual_refs = {item.directive_ref for item in assessments}
        if actual_refs != expected_refs:
            raise ValidationError(
                "AuthorizationApplicabilityEvaluation.condition_assessments must exactly cover Authorization conditions"
            )
        object.__setattr__(self, "condition_assessments", assessments)
        _require_text(
            self.description,
            field="AuthorizationApplicabilityEvaluation.description",
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "authorization": self.authorization.to_primitive(),
            "condition_assessments": [
                item.to_primitive() for item in self.condition_assessments
            ],
            "description": self.description,
            "schema": self.SCHEMA,
            "step_ref": self.step_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "AuthorizationApplicabilityEvaluation",
    ) -> AuthorizationApplicabilityEvaluation:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "attribution",
                "authorization",
                "step_ref",
                "condition_assessments",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        assessments = _expect_array(
            obj["condition_assessments"],
            field=f"{field}.condition_assessments",
        )
        try:
            return cls(
                attribution=AuthorizationApplicabilityAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                authorization=Authorization.from_primitive(
                    obj["authorization"], field=f"{field}.authorization"
                ),
                step_ref=StableRef.from_primitive(
                    obj["step_ref"], field=f"{field}.step_ref"
                ),
                condition_assessments=tuple(
                    AuthorizationConditionAssessment.from_primitive(
                        item,
                        field=f"{field}.condition_assessments[{index}]",
                    )
                    for index, item in enumerate(assessments)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> AuthorizationApplicabilityEvaluation:
        return cls.from_primitive(parse_json_object(data))


def evaluate_authorization_applicability(
    evaluation: AuthorizationApplicabilityEvaluation,
) -> AuthorizationApplicabilityResult:
    """Mechanically aggregate exact per-directive assessments.

    IRR does not infer directive meaning from semantic_type, scope, statement, time,
    consumption history, or Host state. Those facts must already be represented by the
    exact attributed assessments bound to one use-context snapshot.
    """

    if type(evaluation) is not AuthorizationApplicabilityEvaluation:
        raise ValidationError(
            "evaluate_authorization_applicability requires an AuthorizationApplicabilityEvaluation"
        )
    dispositions = {
        item.disposition for item in evaluation.condition_assessments
    }
    if AuthorizationConditionDisposition.UNSATISFIED in dispositions:
        return AuthorizationApplicabilityResult.NOT_APPLICABLE
    if AuthorizationConditionDisposition.UNKNOWN in dispositions:
        return AuthorizationApplicabilityResult.UNRESOLVED
    return AuthorizationApplicabilityResult.APPLICABLE


__all__ = (
    "AuthorizationApplicabilityAttribution",
    "AuthorizationApplicabilityEvaluation",
    "AuthorizationApplicabilityResult",
    "AuthorizationConditionAssessment",
    "AuthorizationConditionDisposition",
    "evaluate_authorization_applicability",
)
