from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, TypeAlias

from .canonical import canonical_json_bytes, parse_json_object
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef
from .resolution import ResolvedIntent
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


class _CanonicalWorkDispositionRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class WorkDispositionKind(str, Enum):
    NO_OPERATIONAL_WORK = "no_operational_work"
    WORK_PLAN = "work_plan"


@dataclass(frozen=True, slots=True)
class WorkDispositionProposalAttribution(_CanonicalWorkDispositionRecord):
    SCHEMA: ClassVar[str] = "irr.work_disposition_proposal_attribution.v1"

    proposer_ref: StableRef
    proposal_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.proposer_ref) is not StableRef:
            raise ValidationError(
                "WorkDispositionProposalAttribution.proposer_ref must be a StableRef"
            )
        if type(self.proposal_event_ref) is not StableRef:
            raise ValidationError(
                "WorkDispositionProposalAttribution.proposal_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "proposal_event_ref": self.proposal_event_ref.to_primitive(),
            "proposer_ref": self.proposer_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "WorkDispositionProposalAttribution"
    ) -> WorkDispositionProposalAttribution:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "proposer_ref", "proposal_event_ref"},
            field=field,
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
    ) -> WorkDispositionProposalAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class WorkDispositionAdmissionAttribution(_CanonicalWorkDispositionRecord):
    SCHEMA: ClassVar[str] = "irr.work_disposition_admission_attribution.v1"

    resolver_ref: StableRef
    admission_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.resolver_ref) is not StableRef:
            raise ValidationError(
                "WorkDispositionAdmissionAttribution.resolver_ref must be a StableRef"
            )
        if type(self.admission_event_ref) is not StableRef:
            raise ValidationError(
                "WorkDispositionAdmissionAttribution.admission_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_event_ref": self.admission_event_ref.to_primitive(),
            "resolver_ref": self.resolver_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "WorkDispositionAdmissionAttribution"
    ) -> WorkDispositionAdmissionAttribution:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "resolver_ref", "admission_event_ref"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                resolver_ref=StableRef.from_primitive(
                    obj["resolver_ref"], field=f"{field}.resolver_ref"
                ),
                admission_event_ref=StableRef.from_primitive(
                    obj["admission_event_ref"], field=f"{field}.admission_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> WorkDispositionAdmissionAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CandidateWorkDisposition(_CanonicalWorkDispositionRecord):
    """Proposed post-resolution work semantics; not admitted work state."""

    SCHEMA: ClassVar[str] = "irr.candidate_work_disposition.v1"

    resolved_intent_identity: RecordIdentity
    attribution: WorkDispositionProposalAttribution
    kind: WorkDispositionKind
    work_plan: WorkPlan | None
    rationale: str

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError(
                "CandidateWorkDisposition.resolved_intent_identity must be a RecordIdentity"
            )
        if type(self.attribution) is not WorkDispositionProposalAttribution:
            raise ValidationError(
                "CandidateWorkDisposition.attribution must be a WorkDispositionProposalAttribution"
            )
        if type(self.kind) is not WorkDispositionKind:
            raise ValidationError(
                "CandidateWorkDisposition.kind must be a WorkDispositionKind"
            )
        _require_text(self.rationale, field="CandidateWorkDisposition.rationale")

        if self.kind is WorkDispositionKind.NO_OPERATIONAL_WORK:
            if self.work_plan is not None:
                raise ValidationError(
                    "no_operational_work candidate cannot contain a WorkPlan"
                )
            return

        if self.kind is WorkDispositionKind.WORK_PLAN:
            if type(self.work_plan) is not WorkPlan:
                raise ValidationError("work_plan candidate requires an exact WorkPlan")
            if self.work_plan.resolved_intent_identity != self.resolved_intent_identity:
                raise ValidationError(
                    "candidate WorkPlan must belong to the exact ResolvedIntent"
                )
            return

        raise AssertionError("unsupported WorkDispositionKind")

    def to_primitive(self) -> dict[str, object]:
        primitive: dict[str, object] = {
            "attribution": self.attribution.to_primitive(),
            "kind": self.kind.value,
            "rationale": self.rationale,
            "resolved_intent_identity": self.resolved_intent_identity.to_primitive(),
            "schema": self.SCHEMA,
        }
        if self.work_plan is not None:
            primitive["work_plan"] = self.work_plan.to_primitive()
        return primitive

    @classmethod
    def from_primitive(cls, value: object) -> CandidateWorkDisposition:
        obj = _expect_object(value, field="CandidateWorkDisposition")

        schema = obj.get("schema")
        if schema != cls.SCHEMA:
            raise SerializationError(
                f"unsupported CandidateWorkDisposition schema: {schema!r}"
            )

        kind_value = obj.get("kind")
        if type(kind_value) is not str:
            raise SerializationError("CandidateWorkDisposition.kind must be a string")
        try:
            kind = WorkDispositionKind(kind_value)
        except ValueError as exc:
            raise SerializationError(
                "unsupported CandidateWorkDisposition.kind"
            ) from exc

        expected_keys = {
            "schema",
            "resolved_intent_identity",
            "attribution",
            "kind",
            "rationale",
        }
        if kind is WorkDispositionKind.WORK_PLAN:
            expected_keys.add("work_plan")

        _expect_exact_keys(
            obj,
            expected_keys,
            field="CandidateWorkDisposition",
        )

        try:
            work_plan = (
                WorkPlan.from_primitive(obj["work_plan"])
                if kind is WorkDispositionKind.WORK_PLAN
                else None
            )
            return cls(
                resolved_intent_identity=RecordIdentity.from_primitive(
                    obj["resolved_intent_identity"],
                    field="CandidateWorkDisposition.resolved_intent_identity",
                ),
                attribution=WorkDispositionProposalAttribution.from_primitive(
                    obj["attribution"],
                    field="CandidateWorkDisposition.attribution",
                ),
                kind=kind,
                work_plan=work_plan,
                rationale=obj["rationale"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid CandidateWorkDisposition") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> CandidateWorkDisposition:
        return cls.from_primitive(parse_json_object(data))


def _normalize_candidates(
    value: object, *, field: str
) -> tuple[CandidateWorkDisposition, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CandidateWorkDisposition for item in value):
        raise ValidationError(f"{field} must contain CandidateWorkDisposition values")
    candidates = tuple(value)
    identities = [candidate.identity for candidate in candidates]
    if len(set(identities)) != len(identities):
        raise ValidationError(
            f"{field} must not contain duplicate candidate identities"
        )
    return tuple(sorted(candidates, key=lambda candidate: str(candidate.identity)))


def _validate_candidates_lineage(
    candidates: tuple[CandidateWorkDisposition, ...],
    *,
    resolved_intent_identity: RecordIdentity,
    field: str,
) -> None:
    if any(
        candidate.resolved_intent_identity != resolved_intent_identity
        for candidate in candidates
    ):
        raise ValidationError(f"{field} contains a foreign ResolvedIntent lineage")


@dataclass(frozen=True, slots=True)
class NoOperationalWork(_CanonicalWorkDispositionRecord):
    """IRR-admitted decision that the ResolvedIntent requires no operational work."""

    SCHEMA: ClassVar[str] = "irr.no_operational_work.v1"

    resolved_intent_identity: RecordIdentity
    admission_attribution: WorkDispositionAdmissionAttribution
    rationale: str
    candidate_inputs: tuple[CandidateWorkDisposition, ...] = ()

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError(
                "NoOperationalWork.resolved_intent_identity must be a RecordIdentity"
            )
        if type(self.admission_attribution) is not WorkDispositionAdmissionAttribution:
            raise ValidationError(
                "NoOperationalWork.admission_attribution must be a WorkDispositionAdmissionAttribution"
            )
        _require_text(self.rationale, field="NoOperationalWork.rationale")
        candidates = _normalize_candidates(
            self.candidate_inputs, field="NoOperationalWork.candidate_inputs"
        )
        _validate_candidates_lineage(
            candidates,
            resolved_intent_identity=self.resolved_intent_identity,
            field="NoOperationalWork.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_attribution": self.admission_attribution.to_primitive(),
            "candidate_inputs": [item.to_primitive() for item in self.candidate_inputs],
            "rationale": self.rationale,
            "resolved_intent_identity": self.resolved_intent_identity.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(cls, value: object) -> NoOperationalWork:
        obj = _expect_object(value, field="NoOperationalWork")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "resolved_intent_identity",
                "admission_attribution",
                "rationale",
                "candidate_inputs",
            },
            field="NoOperationalWork",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported NoOperationalWork schema: {obj['schema']!r}"
            )
        candidates = _expect_array(
            obj["candidate_inputs"], field="NoOperationalWork.candidate_inputs"
        )
        try:
            return cls(
                resolved_intent_identity=RecordIdentity.from_primitive(
                    obj["resolved_intent_identity"],
                    field="NoOperationalWork.resolved_intent_identity",
                ),
                admission_attribution=WorkDispositionAdmissionAttribution.from_primitive(
                    obj["admission_attribution"],
                    field="NoOperationalWork.admission_attribution",
                ),
                rationale=obj["rationale"],
                candidate_inputs=tuple(
                    CandidateWorkDisposition.from_primitive(item) for item in candidates
                ),
            )
        except ValidationError as exc:
            raise SerializationError("invalid NoOperationalWork") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> NoOperationalWork:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class AdmittedWorkPlan(_CanonicalWorkDispositionRecord):
    """IRR admission of one exact bounded WorkPlan; not Governance Authorization."""

    SCHEMA: ClassVar[str] = "irr.admitted_work_plan.v1"

    resolved_intent_identity: RecordIdentity
    admission_attribution: WorkDispositionAdmissionAttribution
    work_plan: WorkPlan
    candidate_inputs: tuple[CandidateWorkDisposition, ...] = ()

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError(
                "AdmittedWorkPlan.resolved_intent_identity must be a RecordIdentity"
            )
        if type(self.admission_attribution) is not WorkDispositionAdmissionAttribution:
            raise ValidationError(
                "AdmittedWorkPlan.admission_attribution must be a WorkDispositionAdmissionAttribution"
            )
        if type(self.work_plan) is not WorkPlan:
            raise ValidationError(
                "AdmittedWorkPlan.work_plan must be an exact WorkPlan"
            )
        if self.work_plan.resolved_intent_identity != self.resolved_intent_identity:
            raise ValidationError(
                "AdmittedWorkPlan WorkPlan must belong to the exact ResolvedIntent"
            )
        candidates = _normalize_candidates(
            self.candidate_inputs, field="AdmittedWorkPlan.candidate_inputs"
        )
        _validate_candidates_lineage(
            candidates,
            resolved_intent_identity=self.resolved_intent_identity,
            field="AdmittedWorkPlan.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_attribution": self.admission_attribution.to_primitive(),
            "candidate_inputs": [item.to_primitive() for item in self.candidate_inputs],
            "resolved_intent_identity": self.resolved_intent_identity.to_primitive(),
            "schema": self.SCHEMA,
            "work_plan": self.work_plan.to_primitive(),
        }

    @classmethod
    def from_primitive(cls, value: object) -> AdmittedWorkPlan:
        obj = _expect_object(value, field="AdmittedWorkPlan")
        _expect_exact_keys(
            obj,
            {
                "schema",
                "resolved_intent_identity",
                "admission_attribution",
                "work_plan",
                "candidate_inputs",
            },
            field="AdmittedWorkPlan",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported AdmittedWorkPlan schema: {obj['schema']!r}"
            )
        candidates = _expect_array(
            obj["candidate_inputs"], field="AdmittedWorkPlan.candidate_inputs"
        )
        try:
            return cls(
                resolved_intent_identity=RecordIdentity.from_primitive(
                    obj["resolved_intent_identity"],
                    field="AdmittedWorkPlan.resolved_intent_identity",
                ),
                admission_attribution=WorkDispositionAdmissionAttribution.from_primitive(
                    obj["admission_attribution"],
                    field="AdmittedWorkPlan.admission_attribution",
                ),
                work_plan=WorkPlan.from_primitive(obj["work_plan"]),
                candidate_inputs=tuple(
                    CandidateWorkDisposition.from_primitive(item) for item in candidates
                ),
            )
        except ValidationError as exc:
            raise SerializationError("invalid AdmittedWorkPlan") from exc

    @classmethod
    def from_json_bytes(cls, data: bytes | bytearray | memoryview) -> AdmittedWorkPlan:
        return cls.from_primitive(parse_json_object(data))


WorkDispositionOutput: TypeAlias = NoOperationalWork | AdmittedWorkPlan
WorkDispositionAdmitter: TypeAlias = Callable[
    [
        ResolvedIntent,
        tuple[CandidateWorkDisposition, ...],
        WorkDispositionAdmissionAttribution,
    ],
    WorkDispositionOutput | None,
]


def _normalize_outputs(
    value: object, *, field: str
) -> tuple[WorkDispositionOutput, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) in (NoOperationalWork, AdmittedWorkPlan) for item in value):
        raise ValidationError(f"{field} must contain WorkDispositionOutput values")
    outputs = tuple(value)
    identities = [output.identity for output in outputs]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate output identities")
    return tuple(sorted(outputs, key=lambda output: str(output.identity)))


def _validate_output_lineage(
    output: object,
    *,
    resolved_intent_identity: RecordIdentity,
    field: str,
) -> WorkDispositionOutput:
    if type(output) not in (NoOperationalWork, AdmittedWorkPlan):
        raise ValidationError(f"{field} must be an exact WorkDispositionOutput type")
    admitted = output
    if admitted.resolved_intent_identity != resolved_intent_identity:
        raise ValidationError(f"{field} belongs to a foreign ResolvedIntent lineage")
    return admitted


def _candidate_semantic_signature(
    candidate: CandidateWorkDisposition,
) -> tuple[object, ...]:
    """Proposal attribution is provenance, not precedence or voting weight."""

    return candidate.kind, candidate.work_plan


def _candidates_are_semantically_equivalent(
    candidates: tuple[CandidateWorkDisposition, ...],
) -> bool:
    if not candidates:
        return True
    signature = _candidate_semantic_signature(candidates[0])
    return all(
        _candidate_semantic_signature(candidate) == signature
        for candidate in candidates[1:]
    )


class WorkDispositionFrontierKind(str, Enum):
    """Narrow work-disposition frontier classification, not global lifecycle state."""

    PROPOSAL_INPUT_REQUIRED = "proposal_input_required"
    ADMISSION_REQUIRED = "admission_required"
    ADJUDICATION_REQUIRED = "adjudication_required"
    DISPOSITION_OUTPUT_AVAILABLE = "disposition_output_available"


@dataclass(frozen=True, slots=True)
class WorkDispositionFrontier:
    """Derived non-canonical view over one ResolvedIntent work-disposition slice."""

    resolved_intent_identity: RecordIdentity
    kind: WorkDispositionFrontierKind
    candidate_inputs: tuple[CandidateWorkDisposition, ...] = ()
    disposition_output: WorkDispositionOutput | None = None

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError(
                "WorkDispositionFrontier.resolved_intent_identity must be a RecordIdentity"
            )
        if type(self.kind) is not WorkDispositionFrontierKind:
            raise ValidationError(
                "WorkDispositionFrontier.kind must be a WorkDispositionFrontierKind"
            )
        candidates = _normalize_candidates(
            self.candidate_inputs, field="WorkDispositionFrontier.candidate_inputs"
        )
        _validate_candidates_lineage(
            candidates,
            resolved_intent_identity=self.resolved_intent_identity,
            field="WorkDispositionFrontier.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)

        if self.disposition_output is not None:
            output = _validate_output_lineage(
                self.disposition_output,
                resolved_intent_identity=self.resolved_intent_identity,
                field="WorkDispositionFrontier.disposition_output",
            )
        else:
            output = None

        if self.kind is WorkDispositionFrontierKind.PROPOSAL_INPUT_REQUIRED:
            if candidates or output is not None:
                raise ValidationError(
                    "proposal_input_required frontier cannot contain candidates or output"
                )
        elif self.kind in (
            WorkDispositionFrontierKind.ADMISSION_REQUIRED,
            WorkDispositionFrontierKind.ADJUDICATION_REQUIRED,
        ):
            if not candidates:
                raise ValidationError(
                    f"{self.kind.value} frontier requires explicit candidate material"
                )
            if output is not None:
                raise ValidationError(
                    f"{self.kind.value} frontier cannot contain admitted output"
                )
        elif self.kind is WorkDispositionFrontierKind.DISPOSITION_OUTPUT_AVAILABLE:
            if output is None:
                raise ValidationError(
                    "disposition_output_available frontier requires a WorkDispositionOutput"
                )
            if candidates != output.candidate_inputs:
                raise ValidationError(
                    "disposition_output_available candidate_inputs must equal exact output provenance"
                )
        else:  # pragma: no cover
            raise AssertionError("unsupported WorkDispositionFrontierKind")


def _frontier_without_output(
    resolved_intent: ResolvedIntent,
    candidates: tuple[CandidateWorkDisposition, ...],
) -> WorkDispositionFrontier:
    if not candidates:
        kind = WorkDispositionFrontierKind.PROPOSAL_INPUT_REQUIRED
    elif _candidates_are_semantically_equivalent(candidates):
        kind = WorkDispositionFrontierKind.ADMISSION_REQUIRED
    else:
        kind = WorkDispositionFrontierKind.ADJUDICATION_REQUIRED
    return WorkDispositionFrontier(
        resolved_intent_identity=resolved_intent.identity,
        kind=kind,
        candidate_inputs=candidates,
    )


def orchestrate_work_disposition(
    resolved_intent: ResolvedIntent,
    *,
    candidate_inputs: tuple[CandidateWorkDisposition, ...] = (),
    admitted_outputs: tuple[WorkDispositionOutput, ...] = (),
    admitter: WorkDispositionAdmitter | None = None,
    admission_attribution: WorkDispositionAdmissionAttribution | None = None,
) -> WorkDispositionFrontier:
    """Derive and, when explicitly delegated, advance work-disposition admission.

    CandidateWorkDisposition never becomes active merely because it is unique,
    provider-consensual, or contains a valid WorkPlan. A new NoOperationalWork or
    AdmittedWorkPlan may be created only through an explicit admission boundary.

    This function performs no planner/provider invocation, Binding, capability match,
    Governance, Authorization, execution, retry, fallback, or persistence.
    """

    if type(resolved_intent) is not ResolvedIntent:
        raise ValidationError(
            "orchestrate_work_disposition.resolved_intent must be a ResolvedIntent"
        )

    candidates = _normalize_candidates(
        candidate_inputs, field="orchestrate_work_disposition.candidate_inputs"
    )
    _validate_candidates_lineage(
        candidates,
        resolved_intent_identity=resolved_intent.identity,
        field="orchestrate_work_disposition.candidate_inputs",
    )

    outputs = _normalize_outputs(
        admitted_outputs, field="orchestrate_work_disposition.admitted_outputs"
    )
    for output in outputs:
        _validate_output_lineage(
            output,
            resolved_intent_identity=resolved_intent.identity,
            field="orchestrate_work_disposition.admitted_outputs",
        )

    if len(outputs) > 1:
        raise ValidationError(
            "work-disposition graph must not contain competing admitted outputs"
        )

    if outputs:
        if admitter is not None or admission_attribution is not None:
            raise ValidationError(
                "existing admitted work disposition cannot be combined with a new admission transition"
            )
        output = outputs[0]
        admitted_candidate_identities = {
            candidate.identity for candidate in output.candidate_inputs
        }
        supplied_candidate_identities = {candidate.identity for candidate in candidates}
        if not supplied_candidate_identities.issubset(admitted_candidate_identities):
            raise ValidationError(
                "candidate material outside admitted work-disposition provenance is orphaned"
            )
        return WorkDispositionFrontier(
            resolved_intent_identity=resolved_intent.identity,
            kind=WorkDispositionFrontierKind.DISPOSITION_OUTPUT_AVAILABLE,
            candidate_inputs=output.candidate_inputs,
            disposition_output=output,
        )

    if admitter is None:
        if admission_attribution is not None:
            raise ValidationError(
                "WorkDispositionAdmissionAttribution cannot be supplied without an explicit admitter"
            )
        return _frontier_without_output(resolved_intent, candidates)

    if not callable(admitter):
        raise ValidationError("orchestrate_work_disposition.admitter must be callable")
    if admission_attribution is None:
        raise ValidationError(
            "work-disposition admitter requires explicit WorkDispositionAdmissionAttribution"
        )
    if type(admission_attribution) is not WorkDispositionAdmissionAttribution:
        raise ValidationError(
            "orchestrate_work_disposition.admission_attribution must be a WorkDispositionAdmissionAttribution"
        )

    proposed_output = admitter(resolved_intent, candidates, admission_attribution)
    if proposed_output is None:
        return _frontier_without_output(resolved_intent, candidates)

    output = _validate_output_lineage(
        proposed_output,
        resolved_intent_identity=resolved_intent.identity,
        field="orchestrate_work_disposition.admitter output",
    )
    if output.admission_attribution != admission_attribution:
        raise ValidationError(
            "admitter output must preserve exact WorkDispositionAdmissionAttribution"
        )
    if output.candidate_inputs != candidates:
        raise ValidationError(
            "admitter output must preserve complete exact candidate provenance"
        )

    return WorkDispositionFrontier(
        resolved_intent_identity=resolved_intent.identity,
        kind=WorkDispositionFrontierKind.DISPOSITION_OUTPUT_AVAILABLE,
        candidate_inputs=output.candidate_inputs,
        disposition_output=output,
    )


__all__ = (
    "AdmittedWorkPlan",
    "CandidateWorkDisposition",
    "NoOperationalWork",
    "WorkDispositionAdmissionAttribution",
    "WorkDispositionFrontier",
    "WorkDispositionFrontierKind",
    "WorkDispositionKind",
    "WorkDispositionOutput",
    "WorkDispositionProposalAttribution",
    "orchestrate_work_disposition",
)
