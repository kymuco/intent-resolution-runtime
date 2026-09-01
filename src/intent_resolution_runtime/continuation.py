from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, TypeAlias

from .binding import BindingIssue
from .canonical import canonical_json_bytes, parse_json_object
from .capability_match_evaluation import CapabilityMatchIssue
from .errors import SerializationError, ValidationError
from .governance import (
    GovernanceDecision,
    GovernanceDecisionComponent,
    GovernanceDecisionKind,
)
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef
from .outcome import CapabilityOutcome
from .worker_result import WorkerResult


def _expect_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SerializationError(f"{field} must be a JSON object")
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


class _CanonicalContinuationRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class ContinuationSourceKind(str, Enum):
    CAPABILITY_OUTCOME = "capability_outcome"
    WORKER_RESULT = "worker_result"
    BINDING_ISSUE = "binding_issue"
    CAPABILITY_MATCH_ISSUE = "capability_match_issue"
    GOVERNANCE_CONSTRAINT = "governance_constraint"
    GOVERNANCE_REQUIRE_REVIEW = "governance_require_review"


@dataclass(frozen=True, slots=True)
class ContinuationInputAttribution(_CanonicalContinuationRecord):
    """Attribution for one exact Host-side re-entry occurrence into IRR."""

    SCHEMA: ClassVar[str] = "irr.continuation_input_attribution.v1"

    submitter_ref: StableRef
    reentry_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.submitter_ref) is not StableRef:
            raise ValidationError(
                "ContinuationInputAttribution.submitter_ref must be a StableRef"
            )
        if type(self.reentry_event_ref) is not StableRef:
            raise ValidationError(
                "ContinuationInputAttribution.reentry_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "reentry_event_ref": self.reentry_event_ref.to_primitive(),
            "schema": self.SCHEMA,
            "submitter_ref": self.submitter_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "ContinuationInputAttribution"
    ) -> "ContinuationInputAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "submitter_ref", "reentry_event_ref"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                submitter_ref=StableRef.from_primitive(
                    obj["submitter_ref"], field=f"{field}.submitter_ref"
                ),
                reentry_event_ref=StableRef.from_primitive(
                    obj["reentry_event_ref"], field=f"{field}.reentry_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "ContinuationInputAttribution":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class GovernanceContinuationMaterial(_CanonicalContinuationRecord):
    """Exact Governance constrain/review component selected for semantic re-entry."""

    SCHEMA: ClassVar[str] = "irr.governance_continuation_material.v1"

    decision: GovernanceDecision
    component_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.decision) is not GovernanceDecision:
            raise ValidationError(
                "GovernanceContinuationMaterial.decision must be a GovernanceDecision"
            )
        if type(self.component_ref) is not StableRef:
            raise ValidationError(
                "GovernanceContinuationMaterial.component_ref must be a StableRef"
            )
        component = self.component
        if component.kind not in (
            GovernanceDecisionKind.CONSTRAIN,
            GovernanceDecisionKind.REQUIRE_REVIEW,
        ):
            raise ValidationError(
                "GovernanceContinuationMaterial requires a constrain or require_review component"
            )

    @property
    def component(self) -> GovernanceDecisionComponent:
        for component in self.decision.components:
            if component.component_ref == self.component_ref:
                return component
        raise ValidationError(
            "GovernanceContinuationMaterial.component_ref must identify a component "
            "in the exact GovernanceDecision"
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "component_ref": self.component_ref.to_primitive(),
            "decision": self.decision.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "GovernanceContinuationMaterial"
    ) -> "GovernanceContinuationMaterial":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"schema", "decision", "component_ref"}, field=field)
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                decision=GovernanceDecision.from_primitive(
                    obj["decision"], field=f"{field}.decision"
                ),
                component_ref=StableRef.from_primitive(
                    obj["component_ref"], field=f"{field}.component_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "GovernanceContinuationMaterial":
        return cls.from_primitive(parse_json_object(data))


ContinuationSource: TypeAlias = (
    CapabilityOutcome
    | WorkerResult
    | BindingIssue
    | CapabilityMatchIssue
    | GovernanceContinuationMaterial
)


def _source_kind(source: ContinuationSource) -> ContinuationSourceKind:
    if type(source) is CapabilityOutcome:
        return ContinuationSourceKind.CAPABILITY_OUTCOME
    if type(source) is WorkerResult:
        return ContinuationSourceKind.WORKER_RESULT
    if type(source) is BindingIssue:
        return ContinuationSourceKind.BINDING_ISSUE
    if type(source) is CapabilityMatchIssue:
        return ContinuationSourceKind.CAPABILITY_MATCH_ISSUE
    if type(source) is GovernanceContinuationMaterial:
        if source.component.kind is GovernanceDecisionKind.CONSTRAIN:
            return ContinuationSourceKind.GOVERNANCE_CONSTRAINT
        if source.component.kind is GovernanceDecisionKind.REQUIRE_REVIEW:
            return ContinuationSourceKind.GOVERNANCE_REQUIRE_REVIEW
        raise AssertionError("validated GovernanceContinuationMaterial lost its admitted kind")
    raise ValidationError("ContinuationInput.source has unsupported IR type")


def _source_event_ref(source: ContinuationSource) -> StableRef:
    if type(source) is CapabilityOutcome:
        return source.attribution.outcome_event_ref
    if type(source) is WorkerResult:
        return source.attribution.result_event_ref
    if type(source) is BindingIssue:
        return source.binding_attribution.binding_event_ref
    if type(source) is CapabilityMatchIssue:
        return source.evaluation.attribution.evaluation_event_ref
    if type(source) is GovernanceContinuationMaterial:
        return source.decision.attribution.decision_event_ref
    raise AssertionError("validated ContinuationSource lost its occurrence")


def _resolved_intent_identity(source: ContinuationSource) -> RecordIdentity:
    if type(source) is CapabilityOutcome:
        return (
            source.attempt.capability_evaluation.requirement.work_plan.resolved_intent_identity
        )
    if type(source) is WorkerResult:
        return source.handoff.delegated_work.resolved_intent_identity
    if type(source) is BindingIssue:
        return source.rule.resolved_intent_identity
    if type(source) is CapabilityMatchIssue:
        return source.evaluation.requirement.work_plan.resolved_intent_identity
    if type(source) is GovernanceContinuationMaterial:
        return source.decision.proposal.work_plan.resolved_intent_identity
    raise AssertionError("validated ContinuationSource lost its ResolvedIntent lineage")


def _parse_source(
    kind: ContinuationSourceKind, value: object, *, field: str
) -> ContinuationSource:
    if kind is ContinuationSourceKind.CAPABILITY_OUTCOME:
        return CapabilityOutcome.from_primitive(value, field=field)
    if kind is ContinuationSourceKind.WORKER_RESULT:
        return WorkerResult.from_primitive(value)
    if kind is ContinuationSourceKind.BINDING_ISSUE:
        return BindingIssue.from_primitive(value)
    if kind is ContinuationSourceKind.CAPABILITY_MATCH_ISSUE:
        return CapabilityMatchIssue.from_primitive(value, field=field)
    if kind in (
        ContinuationSourceKind.GOVERNANCE_CONSTRAINT,
        ContinuationSourceKind.GOVERNANCE_REQUIRE_REVIEW,
    ):
        return GovernanceContinuationMaterial.from_primitive(value, field=field)
    raise AssertionError("unsupported ContinuationSourceKind")


@dataclass(frozen=True, slots=True)
class ContinuationInput(_CanonicalContinuationRecord):
    """One exact attributable semantic re-entry input; it does not choose what happens next."""

    SCHEMA: ClassVar[str] = "irr.continuation_input.v1"

    attribution: ContinuationInputAttribution
    source_kind: ContinuationSourceKind
    source: ContinuationSource

    def __post_init__(self) -> None:
        if type(self.attribution) is not ContinuationInputAttribution:
            raise ValidationError(
                "ContinuationInput.attribution must be a ContinuationInputAttribution"
            )
        if type(self.source_kind) is not ContinuationSourceKind:
            raise ValidationError(
                "ContinuationInput.source_kind must be a ContinuationSourceKind"
            )
        expected_kind = _source_kind(self.source)
        if self.source_kind is not expected_kind:
            raise ValidationError(
                "ContinuationInput.source_kind must match the exact source semantics"
            )
        if self.attribution.reentry_event_ref == _source_event_ref(self.source):
            raise ValidationError(
                "ContinuationInput re-entry occurrence must differ from the source occurrence"
            )

    @property
    def source_identity(self) -> RecordIdentity:
        return self.source.identity

    @property
    def source_event_ref(self) -> StableRef:
        return _source_event_ref(self.source)

    @property
    def resolved_intent_identity(self) -> RecordIdentity:
        return _resolved_intent_identity(self.source)

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "schema": self.SCHEMA,
            "source": self.source.to_primitive(),
            "source_kind": self.source_kind.value,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "ContinuationInput"
    ) -> "ContinuationInput":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj, {"schema", "attribution", "source_kind", "source"}, field=field
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["source_kind"]) is not str:
            raise SerializationError(f"{field}.source_kind must be a string")
        try:
            kind = ContinuationSourceKind(obj["source_kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.source_kind") from exc
        try:
            return cls(
                attribution=ContinuationInputAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                source_kind=kind,
                source=_parse_source(kind, obj["source"], field=f"{field}.source"),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "ContinuationInput":
        return cls.from_primitive(parse_json_object(data))
