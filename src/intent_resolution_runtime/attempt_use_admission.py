from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from threading import Lock
from typing import Any, ClassVar, Protocol, cast, runtime_checkable

from .attempt import CapabilityAttempt
from .authorization_applicability import (
    AuthorizationApplicabilityEvaluation,
    AuthorizationApplicabilityResult,
    evaluate_authorization_applicability,
)
from .canonical import canonical_json_bytes, parse_json_object
from .errors import SerializationError, ValidationError
from .governance import Authorization
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


def _expect_exact_keys(
    value: dict[str, Any], expected: set[str], *, field: str
) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details: list[str] = []
        if missing:
            details.append(f"missing={missing}")
        if extra:
            details.append(f"extra={extra}")
        raise SerializationError(f"{field} has invalid fields ({', '.join(details)})")


def _ref_key(value: StableRef) -> tuple[str, str]:
    return value.namespace, value.value


class _CanonicalUseAdmissionRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class AuthorizationConditionUseMode(StrEnum):
    REUSABLE = "reusable"
    EXCLUSIVE_ONCE = "exclusive_once"
    UNKNOWN = "unknown"


class AuthorizationUsePolicyResult(StrEnum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class AuthorizationConditionUseAssessment(_CanonicalUseAdmissionRecord):
    """Explicit use-mode classification for one exact GovernanceDirective."""

    SCHEMA: ClassVar[str] = "irr.authorization_condition_use_assessment.v1"

    directive_ref: StableRef
    mode: AuthorizationConditionUseMode
    evidence_refs: tuple[StableRef, ...]
    rationale: str

    def __post_init__(self) -> None:
        if type(self.directive_ref) is not StableRef:
            raise ValidationError(
                "AuthorizationConditionUseAssessment.directive_ref must be a StableRef"
            )
        if type(self.mode) is not AuthorizationConditionUseMode:
            raise ValidationError(
                "AuthorizationConditionUseAssessment.mode must be an "
                "AuthorizationConditionUseMode"
            )
        if type(self.evidence_refs) is not tuple:
            raise ValidationError(
                "AuthorizationConditionUseAssessment.evidence_refs must be a tuple"
            )
        if not all(type(item) is StableRef for item in self.evidence_refs):
            raise ValidationError(
                "AuthorizationConditionUseAssessment.evidence_refs must contain "
                "StableRef values"
            )
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ValidationError(
                "AuthorizationConditionUseAssessment.evidence_refs must not "
                "contain duplicates"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(sorted(self.evidence_refs, key=_ref_key)),
        )
        _require_text(
            self.rationale,
            field="AuthorizationConditionUseAssessment.rationale",
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "directive_ref": self.directive_ref.to_primitive(),
            "evidence_refs": [item.to_primitive() for item in self.evidence_refs],
            "mode": self.mode.value,
            "rationale": self.rationale,
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "AuthorizationConditionUseAssessment",
    ) -> AuthorizationConditionUseAssessment:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "directive_ref", "mode", "evidence_refs", "rationale"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["mode"]) is not str:
            raise SerializationError(f"{field}.mode must be a string")
        try:
            mode = AuthorizationConditionUseMode(obj["mode"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.mode") from exc
        evidence_refs = _expect_array(
            obj["evidence_refs"],
            field=f"{field}.evidence_refs",
        )
        try:
            return cls(
                directive_ref=StableRef.from_primitive(
                    obj["directive_ref"],
                    field=f"{field}.directive_ref",
                ),
                mode=mode,
                evidence_refs=tuple(
                    StableRef.from_primitive(
                        item,
                        field=f"{field}.evidence_refs[{index}]",
                    )
                    for index, item in enumerate(evidence_refs)
                ),
                rationale=obj["rationale"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> AuthorizationConditionUseAssessment:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class AuthorizationUsePolicyAttribution(_CanonicalUseAdmissionRecord):
    """Attributed policy-classification occurrence for one exact use context."""

    SCHEMA: ClassVar[str] = "irr.authorization_use_policy_attribution.v1"

    evaluator_ref: StableRef
    evaluation_event_ref: StableRef
    use_context_ref: StableRef
    use_context_identity: RecordIdentity

    def __post_init__(self) -> None:
        if type(self.evaluator_ref) is not StableRef:
            raise ValidationError(
                "AuthorizationUsePolicyAttribution.evaluator_ref must be a StableRef"
            )
        if type(self.evaluation_event_ref) is not StableRef:
            raise ValidationError(
                "AuthorizationUsePolicyAttribution.evaluation_event_ref must be "
                "a StableRef"
            )
        if type(self.use_context_ref) is not StableRef:
            raise ValidationError(
                "AuthorizationUsePolicyAttribution.use_context_ref must be a StableRef"
            )
        if type(self.use_context_identity) is not RecordIdentity:
            raise ValidationError(
                "AuthorizationUsePolicyAttribution.use_context_identity must be "
                "a RecordIdentity"
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
        field: str = "AuthorizationUsePolicyAttribution",
    ) -> AuthorizationUsePolicyAttribution:
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
                    obj["evaluator_ref"],
                    field=f"{field}.evaluator_ref",
                ),
                evaluation_event_ref=StableRef.from_primitive(
                    obj["evaluation_event_ref"],
                    field=f"{field}.evaluation_event_ref",
                ),
                use_context_ref=StableRef.from_primitive(
                    obj["use_context_ref"],
                    field=f"{field}.use_context_ref",
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
        cls,
        data: bytes | bytearray | memoryview,
    ) -> AuthorizationUsePolicyAttribution:
        return cls.from_primitive(parse_json_object(data))


def _normalize_use_assessments(
    value: object,
    *,
    field: str,
) -> tuple[AuthorizationConditionUseAssessment, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is AuthorizationConditionUseAssessment for item in value):
        raise ValidationError(
            f"{field} must contain AuthorizationConditionUseAssessment values"
        )
    assessments = cast(tuple[AuthorizationConditionUseAssessment, ...], value)
    refs = [item.directive_ref for item in assessments]
    if len(set(refs)) != len(refs):
        raise ValidationError(
            f"{field} must not contain duplicate directive_ref values"
        )
    return tuple(sorted(assessments, key=lambda item: _ref_key(item.directive_ref)))


@dataclass(frozen=True, slots=True)
class AuthorizationUsePolicyEvaluation(_CanonicalUseAdmissionRecord):
    """Exact externally-supplied reusable/exclusive classification for all conditions."""

    SCHEMA: ClassVar[str] = "irr.authorization_use_policy_evaluation.v1"

    attribution: AuthorizationUsePolicyAttribution
    authorization: Authorization
    step_ref: StableRef
    condition_assessments: tuple[AuthorizationConditionUseAssessment, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not AuthorizationUsePolicyAttribution:
            raise ValidationError(
                "AuthorizationUsePolicyEvaluation.attribution must be an "
                "AuthorizationUsePolicyAttribution"
            )
        if type(self.authorization) is not Authorization:
            raise ValidationError(
                "AuthorizationUsePolicyEvaluation.authorization must be an Authorization"
            )
        if type(self.step_ref) is not StableRef:
            raise ValidationError(
                "AuthorizationUsePolicyEvaluation.step_ref must be a StableRef"
            )
        if self.step_ref not in self.authorization.authorized_step_refs:
            raise ValidationError(
                "AuthorizationUsePolicyEvaluation.step_ref must be covered by the "
                "exact Authorization"
            )
        if (
            self.attribution.evaluation_event_ref
            == self.authorization.decision.attribution.decision_event_ref
        ):
            raise ValidationError(
                "Authorization use-policy occurrence must differ from "
                "GovernanceDecision occurrence"
            )

        assessments = _normalize_use_assessments(
            self.condition_assessments,
            field="AuthorizationUsePolicyEvaluation.condition_assessments",
        )
        expected_refs = {item.directive_ref for item in self.authorization.conditions}
        actual_refs = {item.directive_ref for item in assessments}
        if actual_refs != expected_refs:
            raise ValidationError(
                "AuthorizationUsePolicyEvaluation.condition_assessments must exactly "
                "cover Authorization conditions"
            )
        object.__setattr__(self, "condition_assessments", assessments)
        _require_text(
            self.description,
            field="AuthorizationUsePolicyEvaluation.description",
        )

    @property
    def policy_identity(self) -> RecordIdentity:
        """Path-neutral identity of directive use modes, excluding occurrence evidence."""

        payload = {
            "authorization_identity": self.authorization.identity.to_primitive(),
            "condition_modes": [
                {
                    "directive_ref": item.directive_ref.to_primitive(),
                    "mode": item.mode.value,
                }
                for item in self.condition_assessments
            ],
            "schema": "irr.authorization_use_policy_semantics.v1",
        }
        return identity_for_bytes(canonical_json_bytes(payload))

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
        field: str = "AuthorizationUsePolicyEvaluation",
    ) -> AuthorizationUsePolicyEvaluation:
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
                attribution=AuthorizationUsePolicyAttribution.from_primitive(
                    obj["attribution"],
                    field=f"{field}.attribution",
                ),
                authorization=Authorization.from_primitive(
                    obj["authorization"],
                    field=f"{field}.authorization",
                ),
                step_ref=StableRef.from_primitive(
                    obj["step_ref"],
                    field=f"{field}.step_ref",
                ),
                condition_assessments=tuple(
                    AuthorizationConditionUseAssessment.from_primitive(
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
        cls,
        data: bytes | bytearray | memoryview,
    ) -> AuthorizationUsePolicyEvaluation:
        return cls.from_primitive(parse_json_object(data))


def evaluate_authorization_use_policy(
    evaluation: AuthorizationUsePolicyEvaluation,
) -> AuthorizationUsePolicyResult:
    """Resolve explicit use-mode assessments without interpreting directive text."""

    if type(evaluation) is not AuthorizationUsePolicyEvaluation:
        raise ValidationError(
            "evaluate_authorization_use_policy requires an "
            "AuthorizationUsePolicyEvaluation"
        )
    if any(
        item.mode is AuthorizationConditionUseMode.UNKNOWN
        for item in evaluation.condition_assessments
    ):
        return AuthorizationUsePolicyResult.UNRESOLVED
    return AuthorizationUsePolicyResult.RESOLVED


@dataclass(frozen=True, slots=True)
class ExclusiveAuthorizationUseClaim(_CanonicalUseAdmissionRecord):
    """Canonical exclusivity key for one exact Authorization condition."""

    SCHEMA: ClassVar[str] = "irr.exclusive_authorization_use_claim.v1"

    authorization_identity: RecordIdentity
    directive_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.authorization_identity) is not RecordIdentity:
            raise ValidationError(
                "ExclusiveAuthorizationUseClaim.authorization_identity must be a "
                "RecordIdentity"
            )
        if type(self.directive_ref) is not StableRef:
            raise ValidationError(
                "ExclusiveAuthorizationUseClaim.directive_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "authorization_identity": self.authorization_identity.to_primitive(),
            "directive_ref": self.directive_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "ExclusiveAuthorizationUseClaim",
    ) -> ExclusiveAuthorizationUseClaim:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "authorization_identity", "directive_ref"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                authorization_identity=RecordIdentity.from_primitive(
                    obj["authorization_identity"],
                    field=f"{field}.authorization_identity",
                ),
                directive_ref=StableRef.from_primitive(
                    obj["directive_ref"],
                    field=f"{field}.directive_ref",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


@dataclass(frozen=True, slots=True)
class CapabilityAttemptUseAdmissionAttribution(_CanonicalUseAdmissionRecord):
    """Exact admission occurrence for one current-use attempt."""

    SCHEMA: ClassVar[str] = "irr.capability_attempt_use_admission_attribution.v1"

    admitter_ref: StableRef
    admission_event_ref: StableRef
    use_context_ref: StableRef
    use_context_identity: RecordIdentity

    def __post_init__(self) -> None:
        if type(self.admitter_ref) is not StableRef:
            raise ValidationError(
                "CapabilityAttemptUseAdmissionAttribution.admitter_ref must be a StableRef"
            )
        if type(self.admission_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityAttemptUseAdmissionAttribution.admission_event_ref must "
                "be a StableRef"
            )
        if type(self.use_context_ref) is not StableRef:
            raise ValidationError(
                "CapabilityAttemptUseAdmissionAttribution.use_context_ref must be "
                "a StableRef"
            )
        if type(self.use_context_identity) is not RecordIdentity:
            raise ValidationError(
                "CapabilityAttemptUseAdmissionAttribution.use_context_identity must "
                "be a RecordIdentity"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_event_ref": self.admission_event_ref.to_primitive(),
            "admitter_ref": self.admitter_ref.to_primitive(),
            "schema": self.SCHEMA,
            "use_context_identity": self.use_context_identity.to_primitive(),
            "use_context_ref": self.use_context_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "CapabilityAttemptUseAdmissionAttribution",
    ) -> CapabilityAttemptUseAdmissionAttribution:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "admitter_ref",
                "admission_event_ref",
                "use_context_ref",
                "use_context_identity",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                admitter_ref=StableRef.from_primitive(
                    obj["admitter_ref"],
                    field=f"{field}.admitter_ref",
                ),
                admission_event_ref=StableRef.from_primitive(
                    obj["admission_event_ref"],
                    field=f"{field}.admission_event_ref",
                ),
                use_context_ref=StableRef.from_primitive(
                    obj["use_context_ref"],
                    field=f"{field}.use_context_ref",
                ),
                use_context_identity=RecordIdentity.from_primitive(
                    obj["use_context_identity"],
                    field=f"{field}.use_context_identity",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


def _derived_exclusive_claims(
    evaluation: AuthorizationUsePolicyEvaluation,
) -> tuple[ExclusiveAuthorizationUseClaim, ...]:
    claims = tuple(
        ExclusiveAuthorizationUseClaim(
            authorization_identity=evaluation.authorization.identity,
            directive_ref=assessment.directive_ref,
        )
        for assessment in evaluation.condition_assessments
        if assessment.mode is AuthorizationConditionUseMode.EXCLUSIVE_ONCE
    )
    return tuple(sorted(claims, key=lambda item: str(item.identity)))


@dataclass(frozen=True, slots=True)
class CapabilityAttemptUseAdmission(_CanonicalUseAdmissionRecord):
    """Exact pre-effect admission material for one Authorization-backed Attempt."""

    SCHEMA: ClassVar[str] = "irr.capability_attempt_use_admission.v1"

    attribution: CapabilityAttemptUseAdmissionAttribution
    attempt: CapabilityAttempt
    applicability_evaluation: AuthorizationApplicabilityEvaluation
    use_policy_evaluation: AuthorizationUsePolicyEvaluation
    description: str
    exclusive_claims: tuple[ExclusiveAuthorizationUseClaim, ...] = field(init=False)

    def __post_init__(self) -> None:
        if type(self.attribution) is not CapabilityAttemptUseAdmissionAttribution:
            raise ValidationError(
                "CapabilityAttemptUseAdmission.attribution must be a "
                "CapabilityAttemptUseAdmissionAttribution"
            )
        if type(self.attempt) is not CapabilityAttempt:
            raise ValidationError(
                "CapabilityAttemptUseAdmission.attempt must be a CapabilityAttempt"
            )
        if (
            type(self.applicability_evaluation)
            is not AuthorizationApplicabilityEvaluation
        ):
            raise ValidationError(
                "CapabilityAttemptUseAdmission.applicability_evaluation must be an "
                "AuthorizationApplicabilityEvaluation"
            )
        if type(self.use_policy_evaluation) is not AuthorizationUsePolicyEvaluation:
            raise ValidationError(
                "CapabilityAttemptUseAdmission.use_policy_evaluation must be an "
                "AuthorizationUsePolicyEvaluation"
            )
        if (
            evaluate_authorization_applicability(self.applicability_evaluation)
            is not AuthorizationApplicabilityResult.APPLICABLE
        ):
            raise ValidationError(
                "CapabilityAttemptUseAdmission requires APPLICABLE Authorization evidence"
            )
        if (
            evaluate_authorization_use_policy(self.use_policy_evaluation)
            is not AuthorizationUsePolicyResult.RESOLVED
        ):
            raise ValidationError(
                "CapabilityAttemptUseAdmission requires resolved Authorization use policy"
            )

        authorization = self.applicability_evaluation.authorization
        if self.use_policy_evaluation.authorization != authorization:
            raise ValidationError(
                "CapabilityAttemptUseAdmission evaluations must preserve the exact "
                "Authorization"
            )
        if self.attempt.presented_authorizations != (authorization,):
            raise ValidationError(
                "CapabilityAttemptUseAdmission Attempt must present exactly the "
                "evaluated Authorization"
            )
        if self.attempt.step_ref != self.applicability_evaluation.step_ref:
            raise ValidationError(
                "CapabilityAttemptUseAdmission Attempt must preserve the exact "
                "applicability WorkStep"
            )
        if self.use_policy_evaluation.step_ref != self.attempt.step_ref:
            raise ValidationError(
                "CapabilityAttemptUseAdmission use policy must preserve the exact "
                "Attempt WorkStep"
            )

        applicability_attr = self.applicability_evaluation.attribution
        policy_attr = self.use_policy_evaluation.attribution
        if applicability_attr.use_context_ref != self.attribution.use_context_ref:
            raise ValidationError(
                "CapabilityAttemptUseAdmission must preserve the exact applicability "
                "use-context ref"
            )
        if (
            applicability_attr.use_context_identity
            != self.attribution.use_context_identity
        ):
            raise ValidationError(
                "CapabilityAttemptUseAdmission must preserve the exact applicability "
                "use-context identity"
            )
        if policy_attr.use_context_ref != self.attribution.use_context_ref:
            raise ValidationError(
                "CapabilityAttemptUseAdmission must preserve the exact policy "
                "use-context ref"
            )
        if policy_attr.use_context_identity != self.attribution.use_context_identity:
            raise ValidationError(
                "CapabilityAttemptUseAdmission must preserve the exact policy "
                "use-context identity"
            )

        protected_occurrences = {
            self.attempt.attribution.attempt_event_ref,
            applicability_attr.evaluation_event_ref,
            policy_attr.evaluation_event_ref,
            authorization.decision.attribution.decision_event_ref,
        }
        if self.attribution.admission_event_ref in protected_occurrences:
            raise ValidationError(
                "CapabilityAttempt use-admission occurrence must differ from all "
                "prerequisite occurrences"
            )

        object.__setattr__(
            self,
            "exclusive_claims",
            _derived_exclusive_claims(self.use_policy_evaluation),
        )
        _require_text(
            self.description,
            field="CapabilityAttemptUseAdmission.description",
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "applicability_evaluation": self.applicability_evaluation.to_primitive(),
            "attempt": self.attempt.to_primitive(),
            "attribution": self.attribution.to_primitive(),
            "description": self.description,
            "exclusive_claims": [item.to_primitive() for item in self.exclusive_claims],
            "schema": self.SCHEMA,
            "use_policy_evaluation": self.use_policy_evaluation.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "CapabilityAttemptUseAdmission",
    ) -> CapabilityAttemptUseAdmission:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "attribution",
                "attempt",
                "applicability_evaluation",
                "use_policy_evaluation",
                "exclusive_claims",
                "description",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        serialized_claims = _expect_array(
            obj["exclusive_claims"],
            field=f"{field}.exclusive_claims",
        )
        try:
            restored = cls(
                attribution=CapabilityAttemptUseAdmissionAttribution.from_primitive(
                    obj["attribution"],
                    field=f"{field}.attribution",
                ),
                attempt=CapabilityAttempt.from_primitive(
                    obj["attempt"],
                    field=f"{field}.attempt",
                ),
                applicability_evaluation=AuthorizationApplicabilityEvaluation.from_primitive(
                    obj["applicability_evaluation"],
                    field=f"{field}.applicability_evaluation",
                ),
                use_policy_evaluation=AuthorizationUsePolicyEvaluation.from_primitive(
                    obj["use_policy_evaluation"],
                    field=f"{field}.use_policy_evaluation",
                ),
                description=obj["description"],
            )
            exact_claims = tuple(
                ExclusiveAuthorizationUseClaim.from_primitive(
                    item,
                    field=f"{field}.exclusive_claims[{index}]",
                )
                for index, item in enumerate(serialized_claims)
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc
        if exact_claims != restored.exclusive_claims:
            raise SerializationError(
                f"{field}.exclusive_claims must equal exact derived claims"
            )
        return restored

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> CapabilityAttemptUseAdmission:
        return cls.from_primitive(parse_json_object(data))


class CapabilityAttemptUseAdmissionResult(StrEnum):
    ADMITTED = "admitted"
    ATTEMPT_ALREADY_ADMITTED = "attempt_already_admitted"
    AUTHORIZATION_POLICY_CONFLICT = "authorization_policy_conflict"
    EXCLUSIVE_CLAIM_CONFLICT = "exclusive_claim_conflict"


@runtime_checkable
class CapabilityAttemptUseAdmissionRepository(Protocol):
    """Atomic store for exact pre-effect use admissions and exclusive claims."""

    def admit(
        self,
        admission: CapabilityAttemptUseAdmission,
    ) -> CapabilityAttemptUseAdmissionResult: ...

    def get(
        self,
        attempt_identity: RecordIdentity,
    ) -> CapabilityAttemptUseAdmission | None: ...

    def claim_owner(
        self,
        claim_identity: RecordIdentity,
    ) -> RecordIdentity | None: ...

    def authorization_policy_identity(
        self,
        authorization_identity: RecordIdentity,
    ) -> RecordIdentity | None: ...


class InMemoryCapabilityAttemptUseAdmissionRepository:
    """Reference atomic admission store; production Hosts may use durable storage."""

    __slots__ = (
        "_admissions",
        "_authorization_policy_identities",
        "_claim_owners",
        "_lock",
    )

    def __init__(self) -> None:
        self._admissions: dict[RecordIdentity, CapabilityAttemptUseAdmission] = {}
        self._authorization_policy_identities: dict[RecordIdentity, RecordIdentity] = {}
        self._claim_owners: dict[RecordIdentity, RecordIdentity] = {}
        self._lock = Lock()

    def admit(
        self,
        admission: CapabilityAttemptUseAdmission,
    ) -> CapabilityAttemptUseAdmissionResult:
        if type(admission) is not CapabilityAttemptUseAdmission:
            raise ValidationError(
                "InMemoryCapabilityAttemptUseAdmissionRepository.admit requires "
                "CapabilityAttemptUseAdmission"
            )
        attempt_identity = admission.attempt.identity
        with self._lock:
            if attempt_identity in self._admissions:
                return CapabilityAttemptUseAdmissionResult.ATTEMPT_ALREADY_ADMITTED

            authorization_identity = (
                admission.applicability_evaluation.authorization.identity
            )
            policy_identity = admission.use_policy_evaluation.policy_identity
            existing_policy_identity = self._authorization_policy_identities.get(
                authorization_identity
            )
            if (
                existing_policy_identity is not None
                and existing_policy_identity != policy_identity
            ):
                return CapabilityAttemptUseAdmissionResult.AUTHORIZATION_POLICY_CONFLICT

            if any(
                claim.identity in self._claim_owners
                and self._claim_owners[claim.identity] != attempt_identity
                for claim in admission.exclusive_claims
            ):
                return CapabilityAttemptUseAdmissionResult.EXCLUSIVE_CLAIM_CONFLICT

            self._admissions[attempt_identity] = admission
            self._authorization_policy_identities[authorization_identity] = (
                policy_identity
            )
            for claim in admission.exclusive_claims:
                self._claim_owners[claim.identity] = attempt_identity
            return CapabilityAttemptUseAdmissionResult.ADMITTED

    def get(
        self,
        attempt_identity: RecordIdentity,
    ) -> CapabilityAttemptUseAdmission | None:
        if type(attempt_identity) is not RecordIdentity:
            raise ValidationError(
                "CapabilityAttemptUseAdmissionRepository.get requires RecordIdentity"
            )
        with self._lock:
            return self._admissions.get(attempt_identity)

    def claim_owner(
        self,
        claim_identity: RecordIdentity,
    ) -> RecordIdentity | None:
        if type(claim_identity) is not RecordIdentity:
            raise ValidationError(
                "CapabilityAttemptUseAdmissionRepository.claim_owner requires "
                "RecordIdentity"
            )
        with self._lock:
            return self._claim_owners.get(claim_identity)

    def authorization_policy_identity(
        self,
        authorization_identity: RecordIdentity,
    ) -> RecordIdentity | None:
        if type(authorization_identity) is not RecordIdentity:
            raise ValidationError(
                "CapabilityAttemptUseAdmissionRepository.authorization_policy_identity "
                "requires RecordIdentity"
            )
        with self._lock:
            return self._authorization_policy_identities.get(authorization_identity)


__all__ = (
    "AuthorizationConditionUseAssessment",
    "AuthorizationConditionUseMode",
    "AuthorizationUsePolicyAttribution",
    "AuthorizationUsePolicyEvaluation",
    "AuthorizationUsePolicyResult",
    "CapabilityAttemptUseAdmission",
    "CapabilityAttemptUseAdmissionAttribution",
    "CapabilityAttemptUseAdmissionRepository",
    "CapabilityAttemptUseAdmissionResult",
    "ExclusiveAuthorizationUseClaim",
    "InMemoryCapabilityAttemptUseAdmissionRepository",
    "evaluate_authorization_use_policy",
)
