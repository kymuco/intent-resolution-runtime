from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, TypeAlias, cast

from .canonical import canonical_json_bytes, parse_json_object
from .capability_match import CapabilityRequirement
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef
from .work import WorkPlan, WorkStep


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


def _step_for(work_plan: WorkPlan, step_ref: StableRef) -> WorkStep:
    if type(work_plan) is not WorkPlan:
        raise ValidationError("work_plan must be an exact WorkPlan")
    if type(step_ref) is not StableRef:
        raise ValidationError("step_ref must be an exact StableRef")
    for step in work_plan.steps:
        if step.step_ref == step_ref:
            return step
    raise ValidationError("step_ref must identify a step in the exact WorkPlan")


class _CanonicalCapabilityRequirementAdmissionRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class CapabilityRequirementProposalAttribution(
    _CanonicalCapabilityRequirementAdmissionRecord
):
    SCHEMA: ClassVar[str] = "irr.capability_requirement_proposal_attribution.v1"

    proposer_ref: StableRef
    proposal_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.proposer_ref) is not StableRef:
            raise ValidationError(
                "CapabilityRequirementProposalAttribution.proposer_ref must be a StableRef"
            )
        if type(self.proposal_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityRequirementProposalAttribution.proposal_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "proposal_event_ref": self.proposal_event_ref.to_primitive(),
            "proposer_ref": self.proposer_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "CapabilityRequirementProposalAttribution",
    ) -> CapabilityRequirementProposalAttribution:
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
    ) -> CapabilityRequirementProposalAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityRequirementAdmissionAttribution(
    _CanonicalCapabilityRequirementAdmissionRecord
):
    SCHEMA: ClassVar[str] = "irr.capability_requirement_admission_attribution.v1"

    resolver_ref: StableRef
    admission_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.resolver_ref) is not StableRef:
            raise ValidationError(
                "CapabilityRequirementAdmissionAttribution.resolver_ref must be a StableRef"
            )
        if type(self.admission_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityRequirementAdmissionAttribution.admission_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_event_ref": self.admission_event_ref.to_primitive(),
            "resolver_ref": self.resolver_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "CapabilityRequirementAdmissionAttribution",
    ) -> CapabilityRequirementAdmissionAttribution:
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
    ) -> CapabilityRequirementAdmissionAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CandidateCapabilityRequirement(_CanonicalCapabilityRequirementAdmissionRecord):
    """Proposed capability-facing semantics for one WorkStep; not active state."""

    SCHEMA: ClassVar[str] = "irr.candidate_capability_requirement.v1"

    attribution: CapabilityRequirementProposalAttribution
    requirement: CapabilityRequirement
    rationale: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not CapabilityRequirementProposalAttribution:
            raise ValidationError(
                "CandidateCapabilityRequirement.attribution must be a "
                "CapabilityRequirementProposalAttribution"
            )
        if type(self.requirement) is not CapabilityRequirement:
            raise ValidationError(
                "CandidateCapabilityRequirement.requirement must be a CapabilityRequirement"
            )
        _require_text(self.rationale, field="CandidateCapabilityRequirement.rationale")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "rationale": self.rationale,
            "requirement": self.requirement.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CandidateCapabilityRequirement"
    ) -> CandidateCapabilityRequirement:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "attribution", "requirement", "rationale"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                attribution=CapabilityRequirementProposalAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                requirement=CapabilityRequirement.from_primitive(
                    obj["requirement"], field=f"{field}.requirement"
                ),
                rationale=obj["rationale"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> CandidateCapabilityRequirement:
        return cls.from_primitive(parse_json_object(data))


def _normalize_candidates(
    value: object, *, field: str
) -> tuple[CandidateCapabilityRequirement, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CandidateCapabilityRequirement for item in value):
        raise ValidationError(f"{field} must contain CandidateCapabilityRequirement values")
    candidates = cast(tuple[CandidateCapabilityRequirement, ...], value)
    identities = [candidate.identity for candidate in candidates]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate candidate identities")
    return tuple(sorted(candidates, key=lambda candidate: str(candidate.identity)))


def _validate_candidate_targets(
    candidates: tuple[CandidateCapabilityRequirement, ...],
    *,
    work_plan: WorkPlan,
    step_ref: StableRef,
    field: str,
) -> None:
    for candidate in candidates:
        if candidate.requirement.work_plan != work_plan:
            raise ValidationError(f"{field} contains a foreign WorkPlan")
        if candidate.requirement.step_ref != step_ref:
            raise ValidationError(f"{field} contains a foreign WorkStep target")


@dataclass(frozen=True, slots=True)
class AdmittedCapabilityRequirement(_CanonicalCapabilityRequirementAdmissionRecord):
    """IRR admission of one exact CapabilityRequirement; never Authorization."""

    SCHEMA: ClassVar[str] = "irr.admitted_capability_requirement.v1"

    admission_attribution: CapabilityRequirementAdmissionAttribution
    requirement: CapabilityRequirement
    candidate_inputs: tuple[CandidateCapabilityRequirement, ...] = ()

    def __post_init__(self) -> None:
        if type(self.admission_attribution) is not CapabilityRequirementAdmissionAttribution:
            raise ValidationError(
                "AdmittedCapabilityRequirement.admission_attribution must be a "
                "CapabilityRequirementAdmissionAttribution"
            )
        if type(self.requirement) is not CapabilityRequirement:
            raise ValidationError(
                "AdmittedCapabilityRequirement.requirement must be a CapabilityRequirement"
            )
        candidates = _normalize_candidates(
            self.candidate_inputs, field="AdmittedCapabilityRequirement.candidate_inputs"
        )
        _validate_candidate_targets(
            candidates,
            work_plan=self.requirement.work_plan,
            step_ref=self.requirement.step_ref,
            field="AdmittedCapabilityRequirement.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_attribution": self.admission_attribution.to_primitive(),
            "candidate_inputs": [item.to_primitive() for item in self.candidate_inputs],
            "requirement": self.requirement.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "AdmittedCapabilityRequirement"
    ) -> AdmittedCapabilityRequirement:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "admission_attribution", "requirement", "candidate_inputs"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        candidates = _expect_array(
            obj["candidate_inputs"], field=f"{field}.candidate_inputs"
        )
        try:
            return cls(
                admission_attribution=CapabilityRequirementAdmissionAttribution.from_primitive(
                    obj["admission_attribution"],
                    field=f"{field}.admission_attribution",
                ),
                requirement=CapabilityRequirement.from_primitive(
                    obj["requirement"], field=f"{field}.requirement"
                ),
                candidate_inputs=tuple(
                    CandidateCapabilityRequirement.from_primitive(
                        item, field=f"{field}.candidate_inputs[{index}]"
                    )
                    for index, item in enumerate(candidates)
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> AdmittedCapabilityRequirement:
        return cls.from_primitive(parse_json_object(data))


class CapabilityRequirementAdmissionFrontierKind(StrEnum):
    PROPOSAL_INPUT_REQUIRED = "proposal_input_required"
    ADMISSION_REQUIRED = "admission_required"
    ADJUDICATION_REQUIRED = "adjudication_required"
    REQUIREMENT_OUTPUT_AVAILABLE = "requirement_output_available"


@dataclass(frozen=True, slots=True)
class CapabilityRequirementAdmissionFrontier:
    """Derived admission state for one exact WorkStep capability requirement."""

    work_plan: WorkPlan
    step_ref: StableRef
    candidate_inputs: tuple[CandidateCapabilityRequirement, ...]
    kind: CapabilityRequirementAdmissionFrontierKind
    admitted_requirement: AdmittedCapabilityRequirement | None = None

    def __post_init__(self) -> None:
        _step_for(self.work_plan, self.step_ref)
        candidates = _normalize_candidates(
            self.candidate_inputs,
            field="CapabilityRequirementAdmissionFrontier.candidate_inputs",
        )
        _validate_candidate_targets(
            candidates,
            work_plan=self.work_plan,
            step_ref=self.step_ref,
            field="CapabilityRequirementAdmissionFrontier.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)
        if type(self.kind) is not CapabilityRequirementAdmissionFrontierKind:
            raise ValidationError(
                "CapabilityRequirementAdmissionFrontier.kind must be a "
                "CapabilityRequirementAdmissionFrontierKind"
            )

        output = self.admitted_requirement
        if self.kind is CapabilityRequirementAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED:
            if candidates or output is not None:
                raise ValidationError(
                    "proposal_input_required frontier cannot contain candidates or output"
                )
            return

        if self.kind in (
            CapabilityRequirementAdmissionFrontierKind.ADMISSION_REQUIRED,
            CapabilityRequirementAdmissionFrontierKind.ADJUDICATION_REQUIRED,
        ):
            if not candidates:
                raise ValidationError(
                    f"{self.kind.value} frontier requires explicit candidate material"
                )
            if output is not None:
                raise ValidationError(
                    f"{self.kind.value} frontier cannot contain admitted output"
                )
            return

        if self.kind is CapabilityRequirementAdmissionFrontierKind.REQUIREMENT_OUTPUT_AVAILABLE:
            if type(output) is not AdmittedCapabilityRequirement:
                raise ValidationError(
                    "requirement_output_available requires AdmittedCapabilityRequirement"
                )
            if output.requirement.work_plan != self.work_plan:
                raise ValidationError("admitted requirement changed the exact WorkPlan")
            if output.requirement.step_ref != self.step_ref:
                raise ValidationError("admitted requirement changed the exact WorkStep")
            if output.candidate_inputs != candidates:
                raise ValidationError(
                    "requirement_output_available candidate_inputs must equal exact "
                    "output provenance"
                )
            return

        raise AssertionError("unsupported CapabilityRequirementAdmissionFrontierKind")


CapabilityRequirementAdmitter: TypeAlias = Callable[
    [
        WorkPlan,
        WorkStep,
        tuple[CandidateCapabilityRequirement, ...],
        CapabilityRequirementAdmissionAttribution,
    ],
    AdmittedCapabilityRequirement | None,
]


def _unresolved_kind(
    candidates: tuple[CandidateCapabilityRequirement, ...],
) -> CapabilityRequirementAdmissionFrontierKind:
    if not candidates:
        return CapabilityRequirementAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
    semantic_identities = {candidate.requirement.identity for candidate in candidates}
    if len(semantic_identities) == 1:
        return CapabilityRequirementAdmissionFrontierKind.ADMISSION_REQUIRED
    return CapabilityRequirementAdmissionFrontierKind.ADJUDICATION_REQUIRED


def orchestrate_capability_requirement_admission(
    work_plan: WorkPlan,
    step_ref: StableRef,
    *,
    candidate_inputs: tuple[CandidateCapabilityRequirement, ...] = (),
    admitted_outputs: tuple[AdmittedCapabilityRequirement, ...] = (),
    admitter: CapabilityRequirementAdmitter | None = None,
    admission_attribution: CapabilityRequirementAdmissionAttribution | None = None,
) -> CapabilityRequirementAdmissionFrontier:
    """Derive or explicitly advance one WorkStep capability-requirement admission.

    Proposal provenance never votes. Requirement construction is not admission. The
    explicit admitter may adjudicate or synthesize semantics, but the resulting record
    preserves the complete supplied candidate set. This function performs no catalog
    discovery, capability matching, Governance, Authorization, Attempt, or execution.
    """

    step = _step_for(work_plan, step_ref)
    candidates = _normalize_candidates(candidate_inputs, field="candidate_inputs")
    _validate_candidate_targets(
        candidates,
        work_plan=work_plan,
        step_ref=step_ref,
        field="candidate_inputs",
    )

    if type(admitted_outputs) is not tuple:
        raise ValidationError("admitted_outputs must be a tuple")
    if not all(type(item) is AdmittedCapabilityRequirement for item in admitted_outputs):
        raise ValidationError(
            "admitted_outputs must contain AdmittedCapabilityRequirement values"
        )
    outputs = cast(tuple[AdmittedCapabilityRequirement, ...], admitted_outputs)
    if len(outputs) > 1:
        raise ValidationError("competing admitted capability requirements fail closed")

    if outputs:
        output = outputs[0]
        if output.requirement.work_plan != work_plan:
            raise ValidationError("admitted output belongs to a foreign WorkPlan")
        if output.requirement.step_ref != step_ref:
            raise ValidationError("admitted output belongs to a foreign WorkStep")
        if admitter is not None or admission_attribution is not None:
            raise ValidationError(
                "admitted-output replay cannot also invoke a new admitter"
            )
        admitted_candidate_identities = {
            candidate.identity for candidate in output.candidate_inputs
        }
        supplied_candidate_identities = {candidate.identity for candidate in candidates}
        if not supplied_candidate_identities.issubset(admitted_candidate_identities):
            raise ValidationError(
                "candidate material outside admitted requirement provenance is orphaned"
            )
        return CapabilityRequirementAdmissionFrontier(
            work_plan=work_plan,
            step_ref=step_ref,
            candidate_inputs=output.candidate_inputs,
            kind=CapabilityRequirementAdmissionFrontierKind.REQUIREMENT_OUTPUT_AVAILABLE,
            admitted_requirement=output,
        )

    unresolved = CapabilityRequirementAdmissionFrontier(
        work_plan=work_plan,
        step_ref=step_ref,
        candidate_inputs=candidates,
        kind=_unresolved_kind(candidates),
    )
    if admitter is None:
        if admission_attribution is not None:
            raise ValidationError(
                "admission_attribution requires an explicit capability requirement admitter"
            )
        return unresolved
    if not callable(admitter):
        raise ValidationError("admitter must be callable")
    if type(admission_attribution) is not CapabilityRequirementAdmissionAttribution:
        raise ValidationError(
            "explicit admission requires CapabilityRequirementAdmissionAttribution"
        )

    admitted = admitter(work_plan, step, candidates, admission_attribution)
    if admitted is None:
        return unresolved
    if type(admitted) is not AdmittedCapabilityRequirement:
        raise ValidationError(
            "capability requirement admitter must return "
            "AdmittedCapabilityRequirement or None"
        )
    if admitted.admission_attribution != admission_attribution:
        raise ValidationError("admitter changed the exact admission attribution")
    if admitted.requirement.work_plan != work_plan:
        raise ValidationError("admitter returned a foreign WorkPlan requirement")
    if admitted.requirement.step_ref != step_ref:
        raise ValidationError("admitter returned a foreign WorkStep requirement")
    if admitted.candidate_inputs != candidates:
        raise ValidationError("admitter must preserve the exact candidate set")

    return CapabilityRequirementAdmissionFrontier(
        work_plan=work_plan,
        step_ref=step_ref,
        candidate_inputs=candidates,
        kind=CapabilityRequirementAdmissionFrontierKind.REQUIREMENT_OUTPUT_AVAILABLE,
        admitted_requirement=admitted,
    )


__all__ = (
    "AdmittedCapabilityRequirement",
    "CandidateCapabilityRequirement",
    "CapabilityRequirementAdmissionAttribution",
    "CapabilityRequirementAdmissionFrontier",
    "CapabilityRequirementAdmissionFrontierKind",
    "CapabilityRequirementProposalAttribution",
    "orchestrate_capability_requirement_admission",
)
