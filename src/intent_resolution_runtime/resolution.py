from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, TypeAlias, cast

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


def _normalize_record_tuple(
    value: object, *, field: str, allowed: tuple[type, ...]
) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) in allowed for item in value):
        raise ValidationError(f"{field} contains an unsupported record type")
    identities = [item.identity for item in value]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate record identities")
    return tuple(sorted(value, key=lambda item: str(item.identity)))


class _CanonicalResolutionRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class AssumptionKind(str, Enum):
    PRESENTATION = "presentation"
    FORMATTING = "formatting"
    OTHER_NON_MATERIAL = "other_non_material"


class ResolutionIssueKind(str, Enum):
    MATERIAL_AMBIGUITY = "material_ambiguity"
    CONFLICT = "conflict"
    MISSING_INFORMATION = "missing_information"
    UNCERTAINTY = "uncertainty"


class ResolutionIssueImpact(str, Enum):
    BLOCKING = "blocking"
    NON_BLOCKING = "non_blocking"


@dataclass(frozen=True, slots=True)
class CandidateAttribution:
    """Attribution of candidate semantics to one provider invocation; not trust or authority."""

    provider_ref: StableRef
    invocation_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.provider_ref) is not StableRef:
            raise ValidationError("CandidateAttribution.provider_ref must be a StableRef")
        if type(self.invocation_ref) is not StableRef:
            raise ValidationError("CandidateAttribution.invocation_ref must be a StableRef")

    def to_primitive(self) -> dict[str, object]:
        return {
            "invocation_ref": self.invocation_ref.to_primitive(),
            "provider_ref": self.provider_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(cls, value: object, *, field: str = "attribution") -> "CandidateAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"provider_ref", "invocation_ref"}, field=field)
        try:
            return cls(
                provider_ref=StableRef.from_primitive(obj["provider_ref"], field=f"{field}.provider_ref"),
                invocation_ref=StableRef.from_primitive(obj["invocation_ref"], field=f"{field}.invocation_ref"),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


@dataclass(frozen=True, slots=True)
class ResolutionAttribution:
    """Attribution of an IRR-owned resolution admission event; not Governance authority."""

    resolver_ref: StableRef
    admission_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.resolver_ref) is not StableRef:
            raise ValidationError("ResolutionAttribution.resolver_ref must be a StableRef")
        if type(self.admission_event_ref) is not StableRef:
            raise ValidationError("ResolutionAttribution.admission_event_ref must be a StableRef")

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_event_ref": self.admission_event_ref.to_primitive(),
            "resolver_ref": self.resolver_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(cls, value: object, *, field: str = "admission_attribution") -> "ResolutionAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"resolver_ref", "admission_event_ref"}, field=field)
        try:
            return cls(
                resolver_ref=StableRef.from_primitive(obj["resolver_ref"], field=f"{field}.resolver_ref"),
                admission_event_ref=StableRef.from_primitive(
                    obj["admission_event_ref"], field=f"{field}.admission_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


@dataclass(frozen=True, slots=True)
class AssumptionRecord(_CanonicalResolutionRecord):
    SCHEMA: ClassVar[str] = "irr.assumption.v1"

    kind: AssumptionKind
    statement: str
    scope: str
    rationale: str

    def __post_init__(self) -> None:
        if type(self.kind) is not AssumptionKind:
            raise ValidationError("AssumptionRecord.kind must be an AssumptionKind")
        _require_text(self.statement, field="AssumptionRecord.statement")
        _require_text(self.scope, field="AssumptionRecord.scope")
        _require_text(self.rationale, field="AssumptionRecord.rationale")

    def to_primitive(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "rationale": self.rationale,
            "schema": self.SCHEMA,
            "scope": self.scope,
            "statement": self.statement,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "AssumptionRecord":
        obj = _expect_object(value, field="AssumptionRecord")
        _expect_exact_keys(obj, {"schema", "kind", "statement", "scope", "rationale"}, field="AssumptionRecord")
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported AssumptionRecord schema: {obj['schema']!r}")
        if type(obj["kind"]) is not str:
            raise SerializationError("AssumptionRecord.kind must be a string")
        try:
            kind = AssumptionKind(obj["kind"])
        except ValueError as exc:
            raise SerializationError("unsupported AssumptionRecord.kind") from exc
        try:
            return cls(kind=kind, statement=obj["statement"], scope=obj["scope"], rationale=obj["rationale"])
        except ValidationError as exc:
            raise SerializationError("invalid AssumptionRecord") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "AssumptionRecord":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class ResolutionIssue(_CanonicalResolutionRecord):
    SCHEMA: ClassVar[str] = "irr.resolution_issue.v1"

    kind: ResolutionIssueKind
    impact: ResolutionIssueImpact
    scope: str
    description: str
    alternatives: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.kind) is not ResolutionIssueKind:
            raise ValidationError("ResolutionIssue.kind must be a ResolutionIssueKind")
        if type(self.impact) is not ResolutionIssueImpact:
            raise ValidationError("ResolutionIssue.impact must be a ResolutionIssueImpact")
        _require_text(self.scope, field="ResolutionIssue.scope")
        _require_text(self.description, field="ResolutionIssue.description")
        if type(self.alternatives) is not tuple:
            raise ValidationError("ResolutionIssue.alternatives must be a tuple")
        if not all(type(item) is str for item in self.alternatives):
            raise ValidationError("ResolutionIssue.alternatives must contain strings")
        for index, item in enumerate(self.alternatives):
            _require_text(item, field=f"ResolutionIssue.alternatives[{index}]")
        if len(set(self.alternatives)) != len(self.alternatives):
            raise ValidationError("ResolutionIssue.alternatives must not contain duplicates")
        object.__setattr__(self, "alternatives", tuple(sorted(self.alternatives)))

        if self.kind is ResolutionIssueKind.MATERIAL_AMBIGUITY:
            if self.impact is not ResolutionIssueImpact.BLOCKING:
                raise ValidationError("Material Ambiguity must be blocking")
            if len(self.alternatives) < 2:
                raise ValidationError("Material Ambiguity must preserve at least two alternatives")
        elif self.kind is ResolutionIssueKind.CONFLICT:
            if len(self.alternatives) < 2:
                raise ValidationError("Conflict must preserve at least two alternatives")
        elif self.alternatives:
            raise ValidationError(
                "Missing Information or Uncertainty must not invent competing alternatives"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "alternatives": list(self.alternatives),
            "description": self.description,
            "impact": self.impact.value,
            "kind": self.kind.value,
            "schema": self.SCHEMA,
            "scope": self.scope,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "ResolutionIssue":
        obj = _expect_object(value, field="ResolutionIssue")
        _expect_exact_keys(obj, {"schema", "kind", "impact", "scope", "description", "alternatives"}, field="ResolutionIssue")
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported ResolutionIssue schema: {obj['schema']!r}")
        if type(obj["kind"]) is not str or type(obj["impact"]) is not str:
            raise SerializationError("ResolutionIssue kind and impact must be strings")
        try:
            kind = ResolutionIssueKind(obj["kind"])
            impact = ResolutionIssueImpact(obj["impact"])
        except ValueError as exc:
            raise SerializationError("unsupported ResolutionIssue kind or impact") from exc
        alternatives = _expect_array(obj["alternatives"], field="ResolutionIssue.alternatives")
        try:
            return cls(
                kind=kind,
                impact=impact,
                scope=obj["scope"],
                description=obj["description"],
                alternatives=tuple(alternatives),
            )
        except ValidationError as exc:
            raise SerializationError("invalid ResolutionIssue") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "ResolutionIssue":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class ClarificationProposal(_CanonicalResolutionRecord):
    SCHEMA: ClassVar[str] = "irr.clarification_proposal.v1"

    question: str
    scope: str
    reason: str

    def __post_init__(self) -> None:
        _require_text(self.question, field="ClarificationProposal.question")
        _require_text(self.scope, field="ClarificationProposal.scope")
        _require_text(self.reason, field="ClarificationProposal.reason")

    def to_primitive(self) -> dict[str, object]:
        return {"question": self.question, "reason": self.reason, "schema": self.SCHEMA, "scope": self.scope}

    @classmethod
    def from_primitive(cls, value: object) -> "ClarificationProposal":
        obj = _expect_object(value, field="ClarificationProposal")
        _expect_exact_keys(obj, {"schema", "question", "scope", "reason"}, field="ClarificationProposal")
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported ClarificationProposal schema: {obj['schema']!r}")
        try:
            return cls(question=obj["question"], scope=obj["scope"], reason=obj["reason"])
        except ValidationError as exc:
            raise SerializationError("invalid ClarificationProposal") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "ClarificationProposal":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class InformationNeedProposal(_CanonicalResolutionRecord):
    SCHEMA: ClassVar[str] = "irr.information_need_proposal.v1"

    description: str
    scope: str
    reason: str

    def __post_init__(self) -> None:
        _require_text(self.description, field="InformationNeedProposal.description")
        _require_text(self.scope, field="InformationNeedProposal.scope")
        _require_text(self.reason, field="InformationNeedProposal.reason")

    def to_primitive(self) -> dict[str, object]:
        return {"description": self.description, "reason": self.reason, "schema": self.SCHEMA, "scope": self.scope}

    @classmethod
    def from_primitive(cls, value: object) -> "InformationNeedProposal":
        obj = _expect_object(value, field="InformationNeedProposal")
        _expect_exact_keys(obj, {"schema", "description", "scope", "reason"}, field="InformationNeedProposal")
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported InformationNeedProposal schema: {obj['schema']!r}")
        try:
            return cls(description=obj["description"], scope=obj["scope"], reason=obj["reason"])
        except ValidationError as exc:
            raise SerializationError("invalid InformationNeedProposal") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "InformationNeedProposal":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CandidateResolution(_CanonicalResolutionRecord):
    """Provider-produced candidate semantics. This is not admitted IRR state."""

    SCHEMA: ClassVar[str] = "irr.candidate_resolution.v1"

    intent_request_identity: RecordIdentity
    context_envelope_identity: RecordIdentity
    attribution: CandidateAttribution
    proposed_semantics: str
    assumptions: tuple[AssumptionRecord, ...] = ()
    issues: tuple[ResolutionIssue, ...] = ()
    clarification_proposals: tuple[ClarificationProposal, ...] = ()
    information_need_proposals: tuple[InformationNeedProposal, ...] = ()

    def __post_init__(self) -> None:
        if type(self.intent_request_identity) is not RecordIdentity:
            raise ValidationError("CandidateResolution.intent_request_identity must be a RecordIdentity")
        if type(self.context_envelope_identity) is not RecordIdentity:
            raise ValidationError("CandidateResolution.context_envelope_identity must be a RecordIdentity")
        if type(self.attribution) is not CandidateAttribution:
            raise ValidationError("CandidateResolution.attribution must be a CandidateAttribution")
        _require_text(self.proposed_semantics, field="CandidateResolution.proposed_semantics")
        object.__setattr__(
            self,
            "assumptions",
            _normalize_record_tuple(self.assumptions, field="CandidateResolution.assumptions", allowed=(AssumptionRecord,)),
        )
        object.__setattr__(
            self,
            "issues",
            _normalize_record_tuple(self.issues, field="CandidateResolution.issues", allowed=(ResolutionIssue,)),
        )
        object.__setattr__(
            self,
            "clarification_proposals",
            _normalize_record_tuple(
                self.clarification_proposals,
                field="CandidateResolution.clarification_proposals",
                allowed=(ClarificationProposal,),
            ),
        )
        object.__setattr__(
            self,
            "information_need_proposals",
            _normalize_record_tuple(
                self.information_need_proposals,
                field="CandidateResolution.information_need_proposals",
                allowed=(InformationNeedProposal,),
            ),
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "assumptions": [item.to_primitive() for item in self.assumptions],
            "attribution": self.attribution.to_primitive(),
            "clarification_proposals": [item.to_primitive() for item in self.clarification_proposals],
            "context_envelope_identity": self.context_envelope_identity.to_primitive(),
            "information_need_proposals": [item.to_primitive() for item in self.information_need_proposals],
            "intent_request_identity": self.intent_request_identity.to_primitive(),
            "issues": [item.to_primitive() for item in self.issues],
            "proposed_semantics": self.proposed_semantics,
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "CandidateResolution":
        obj = _expect_object(value, field="CandidateResolution")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "intent_request_identity",
                "context_envelope_identity",
                "attribution",
                "proposed_semantics",
                "assumptions",
                "issues",
                "clarification_proposals",
                "information_need_proposals",
            },
            field="CandidateResolution",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported CandidateResolution schema: {obj['schema']!r}")
        assumptions = _expect_array(obj["assumptions"], field="CandidateResolution.assumptions")
        issues = _expect_array(obj["issues"], field="CandidateResolution.issues")
        clarifications = _expect_array(obj["clarification_proposals"], field="CandidateResolution.clarification_proposals")
        information_needs = _expect_array(obj["information_need_proposals"], field="CandidateResolution.information_need_proposals")
        try:
            return cls(
                intent_request_identity=RecordIdentity.from_primitive(
                    obj["intent_request_identity"], field="CandidateResolution.intent_request_identity"
                ),
                context_envelope_identity=RecordIdentity.from_primitive(
                    obj["context_envelope_identity"], field="CandidateResolution.context_envelope_identity"
                ),
                attribution=CandidateAttribution.from_primitive(obj["attribution"]),
                proposed_semantics=obj["proposed_semantics"],
                assumptions=tuple(AssumptionRecord.from_primitive(item) for item in assumptions),
                issues=tuple(ResolutionIssue.from_primitive(item) for item in issues),
                clarification_proposals=tuple(ClarificationProposal.from_primitive(item) for item in clarifications),
                information_need_proposals=tuple(InformationNeedProposal.from_primitive(item) for item in information_needs),
            )
        except ValidationError as exc:
            raise SerializationError("invalid CandidateResolution") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "CandidateResolution":
        return cls.from_primitive(parse_json_object(data))


def _validate_common_resolution_output(
    *,
    intent_request_identity: object,
    context_envelope_identity: object,
    admission_attribution: object,
    candidate_inputs: object,
    field_prefix: str,
) -> tuple[CandidateResolution, ...]:
    if type(intent_request_identity) is not RecordIdentity:
        raise ValidationError(f"{field_prefix}.intent_request_identity must be a RecordIdentity")
    if type(context_envelope_identity) is not RecordIdentity:
        raise ValidationError(f"{field_prefix}.context_envelope_identity must be a RecordIdentity")
    if type(admission_attribution) is not ResolutionAttribution:
        raise ValidationError(f"{field_prefix}.admission_attribution must be a ResolutionAttribution")

    candidates = cast(
        tuple[CandidateResolution, ...],
        _normalize_record_tuple(
            candidate_inputs,
            field=f"{field_prefix}.candidate_inputs",
            allowed=(CandidateResolution,),
        ),
    )
    for candidate in candidates:
        if candidate.intent_request_identity != intent_request_identity:
            raise ValidationError(
                f"{field_prefix}.candidate_inputs must belong to the same IntentRequest identity"
            )
        if candidate.context_envelope_identity != context_envelope_identity:
            raise ValidationError(
                f"{field_prefix}.candidate_inputs must belong to the same ContextEnvelope identity"
            )
    return candidates


@dataclass(frozen=True, slots=True)
class ResolvedIntent(_CanonicalResolutionRecord):
    """IRR-admitted intent semantics. This does not imply WorkPlan, approval, or effect."""

    SCHEMA: ClassVar[str] = "irr.resolved_intent.v1"

    intent_request_identity: RecordIdentity
    context_envelope_identity: RecordIdentity
    admission_attribution: ResolutionAttribution
    semantics: str
    assumptions: tuple[AssumptionRecord, ...] = ()
    unresolved_issues: tuple[ResolutionIssue, ...] = ()
    candidate_inputs: tuple[CandidateResolution, ...] = ()

    def __post_init__(self) -> None:
        refs = _validate_common_resolution_output(
            intent_request_identity=self.intent_request_identity,
            context_envelope_identity=self.context_envelope_identity,
            admission_attribution=self.admission_attribution,
            candidate_inputs=self.candidate_inputs,
            field_prefix="ResolvedIntent",
        )
        object.__setattr__(self, "candidate_inputs", refs)
        _require_text(self.semantics, field="ResolvedIntent.semantics")
        object.__setattr__(
            self,
            "assumptions",
            _normalize_record_tuple(self.assumptions, field="ResolvedIntent.assumptions", allowed=(AssumptionRecord,)),
        )
        issues = _normalize_record_tuple(
            self.unresolved_issues,
            field="ResolvedIntent.unresolved_issues",
            allowed=(ResolutionIssue,),
        )
        if any(issue.impact is ResolutionIssueImpact.BLOCKING for issue in issues):
            raise ValidationError("ResolvedIntent cannot contain unresolved blocking issues")
        if any(issue.kind is ResolutionIssueKind.MATERIAL_AMBIGUITY for issue in issues):
            raise ValidationError("ResolvedIntent cannot contain Material Ambiguity")
        object.__setattr__(self, "unresolved_issues", issues)

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_attribution": self.admission_attribution.to_primitive(),
            "assumptions": [item.to_primitive() for item in self.assumptions],
            "candidate_inputs": [item.to_primitive() for item in self.candidate_inputs],
            "context_envelope_identity": self.context_envelope_identity.to_primitive(),
            "intent_request_identity": self.intent_request_identity.to_primitive(),
            "schema": self.SCHEMA,
            "semantics": self.semantics,
            "unresolved_issues": [item.to_primitive() for item in self.unresolved_issues],
        }

    @classmethod
    def from_primitive(cls, value: object) -> "ResolvedIntent":
        obj = _expect_object(value, field="ResolvedIntent")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "intent_request_identity",
                "context_envelope_identity",
                "admission_attribution",
                "semantics",
                "assumptions",
                "unresolved_issues",
                "candidate_inputs",
            },
            field="ResolvedIntent",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported ResolvedIntent schema: {obj['schema']!r}")
        assumptions = _expect_array(obj["assumptions"], field="ResolvedIntent.assumptions")
        issues = _expect_array(obj["unresolved_issues"], field="ResolvedIntent.unresolved_issues")
        candidate_inputs = _expect_array(obj["candidate_inputs"], field="ResolvedIntent.candidate_inputs")
        try:
            return cls(
                intent_request_identity=RecordIdentity.from_primitive(obj["intent_request_identity"], field="ResolvedIntent.intent_request_identity"),
                context_envelope_identity=RecordIdentity.from_primitive(obj["context_envelope_identity"], field="ResolvedIntent.context_envelope_identity"),
                admission_attribution=ResolutionAttribution.from_primitive(obj["admission_attribution"]),
                semantics=obj["semantics"],
                assumptions=tuple(AssumptionRecord.from_primitive(item) for item in assumptions),
                unresolved_issues=tuple(ResolutionIssue.from_primitive(item) for item in issues),
                candidate_inputs=tuple(CandidateResolution.from_primitive(item) for item in candidate_inputs),
            )
        except ValidationError as exc:
            raise SerializationError("invalid ResolvedIntent") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "ResolvedIntent":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class ClarificationNeed(_CanonicalResolutionRecord):
    """IRR-owned pause requesting a semantic clarification. It is not a ResolvedIntent."""

    SCHEMA: ClassVar[str] = "irr.clarification_need.v1"

    intent_request_identity: RecordIdentity
    context_envelope_identity: RecordIdentity
    admission_attribution: ResolutionAttribution
    question: str
    scope: str
    blocking_issues: tuple[ResolutionIssue, ...]
    candidate_inputs: tuple[CandidateResolution, ...] = ()

    def __post_init__(self) -> None:
        refs = _validate_common_resolution_output(
            intent_request_identity=self.intent_request_identity,
            context_envelope_identity=self.context_envelope_identity,
            admission_attribution=self.admission_attribution,
            candidate_inputs=self.candidate_inputs,
            field_prefix="ClarificationNeed",
        )
        object.__setattr__(self, "candidate_inputs", refs)
        _require_text(self.question, field="ClarificationNeed.question")
        _require_text(self.scope, field="ClarificationNeed.scope")
        issues = _normalize_record_tuple(
            self.blocking_issues,
            field="ClarificationNeed.blocking_issues",
            allowed=(ResolutionIssue,),
        )
        if not issues:
            raise ValidationError("ClarificationNeed requires at least one blocking issue")
        if any(issue.impact is not ResolutionIssueImpact.BLOCKING for issue in issues):
            raise ValidationError("ClarificationNeed.blocking_issues must all be blocking")
        object.__setattr__(self, "blocking_issues", issues)

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_attribution": self.admission_attribution.to_primitive(),
            "blocking_issues": [item.to_primitive() for item in self.blocking_issues],
            "candidate_inputs": [item.to_primitive() for item in self.candidate_inputs],
            "context_envelope_identity": self.context_envelope_identity.to_primitive(),
            "intent_request_identity": self.intent_request_identity.to_primitive(),
            "question": self.question,
            "schema": self.SCHEMA,
            "scope": self.scope,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "ClarificationNeed":
        obj = _expect_object(value, field="ClarificationNeed")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "intent_request_identity",
                "context_envelope_identity",
                "admission_attribution",
                "question",
                "scope",
                "blocking_issues",
                "candidate_inputs",
            },
            field="ClarificationNeed",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported ClarificationNeed schema: {obj['schema']!r}")
        issues = _expect_array(obj["blocking_issues"], field="ClarificationNeed.blocking_issues")
        candidate_inputs = _expect_array(obj["candidate_inputs"], field="ClarificationNeed.candidate_inputs")
        try:
            return cls(
                intent_request_identity=RecordIdentity.from_primitive(obj["intent_request_identity"], field="ClarificationNeed.intent_request_identity"),
                context_envelope_identity=RecordIdentity.from_primitive(obj["context_envelope_identity"], field="ClarificationNeed.context_envelope_identity"),
                admission_attribution=ResolutionAttribution.from_primitive(obj["admission_attribution"]),
                question=obj["question"],
                scope=obj["scope"],
                blocking_issues=tuple(ResolutionIssue.from_primitive(item) for item in issues),
                candidate_inputs=tuple(CandidateResolution.from_primitive(item) for item in candidate_inputs),
            )
        except ValidationError as exc:
            raise SerializationError("invalid ClarificationNeed") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "ClarificationNeed":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class InformationNeed(_CanonicalResolutionRecord):
    """IRR-owned bounded information requirement. This grants no retrieval/observation authority."""

    SCHEMA: ClassVar[str] = "irr.information_need.v1"

    intent_request_identity: RecordIdentity
    context_envelope_identity: RecordIdentity
    admission_attribution: ResolutionAttribution
    description: str
    scope: str
    reason: str
    blocking_issues: tuple[ResolutionIssue, ...]
    candidate_inputs: tuple[CandidateResolution, ...] = ()

    def __post_init__(self) -> None:
        refs = _validate_common_resolution_output(
            intent_request_identity=self.intent_request_identity,
            context_envelope_identity=self.context_envelope_identity,
            admission_attribution=self.admission_attribution,
            candidate_inputs=self.candidate_inputs,
            field_prefix="InformationNeed",
        )
        object.__setattr__(self, "candidate_inputs", refs)
        _require_text(self.description, field="InformationNeed.description")
        _require_text(self.scope, field="InformationNeed.scope")
        _require_text(self.reason, field="InformationNeed.reason")
        issues = _normalize_record_tuple(
            self.blocking_issues,
            field="InformationNeed.blocking_issues",
            allowed=(ResolutionIssue,),
        )
        if not issues:
            raise ValidationError("InformationNeed requires at least one blocking issue")
        if any(issue.impact is not ResolutionIssueImpact.BLOCKING for issue in issues):
            raise ValidationError("InformationNeed.blocking_issues must all be blocking")
        object.__setattr__(self, "blocking_issues", issues)

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_attribution": self.admission_attribution.to_primitive(),
            "blocking_issues": [item.to_primitive() for item in self.blocking_issues],
            "candidate_inputs": [item.to_primitive() for item in self.candidate_inputs],
            "context_envelope_identity": self.context_envelope_identity.to_primitive(),
            "description": self.description,
            "intent_request_identity": self.intent_request_identity.to_primitive(),
            "reason": self.reason,
            "schema": self.SCHEMA,
            "scope": self.scope,
        }

    @classmethod
    def from_primitive(cls, value: object) -> "InformationNeed":
        obj = _expect_object(value, field="InformationNeed")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "intent_request_identity",
                "context_envelope_identity",
                "admission_attribution",
                "description",
                "scope",
                "reason",
                "blocking_issues",
                "candidate_inputs",
            },
            field="InformationNeed",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported InformationNeed schema: {obj['schema']!r}")
        issues = _expect_array(obj["blocking_issues"], field="InformationNeed.blocking_issues")
        candidate_inputs = _expect_array(obj["candidate_inputs"], field="InformationNeed.candidate_inputs")
        try:
            return cls(
                intent_request_identity=RecordIdentity.from_primitive(obj["intent_request_identity"], field="InformationNeed.intent_request_identity"),
                context_envelope_identity=RecordIdentity.from_primitive(obj["context_envelope_identity"], field="InformationNeed.context_envelope_identity"),
                admission_attribution=ResolutionAttribution.from_primitive(obj["admission_attribution"]),
                description=obj["description"],
                scope=obj["scope"],
                reason=obj["reason"],
                blocking_issues=tuple(ResolutionIssue.from_primitive(item) for item in issues),
                candidate_inputs=tuple(CandidateResolution.from_primitive(item) for item in candidate_inputs),
            )
        except ValidationError as exc:
            raise SerializationError("invalid InformationNeed") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> "InformationNeed":
        return cls.from_primitive(parse_json_object(data))


ResolutionOutput: TypeAlias = ResolvedIntent | ClarificationNeed | InformationNeed
