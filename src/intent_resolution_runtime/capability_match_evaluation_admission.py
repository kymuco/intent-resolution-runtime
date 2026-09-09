from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, TypeAlias, cast

from .canonical import canonical_json_bytes, parse_json_object
from .capability import CapabilityCatalogSnapshot
from .capability_match import CapabilityRequirement
from .capability_match_evaluation import CapabilityMatchEvaluation
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef


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


class _CanonicalCapabilityMatchEvaluationAdmissionRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class CapabilityMatchEvaluationAdmissionAttribution(
    _CanonicalCapabilityMatchEvaluationAdmissionRecord
):
    SCHEMA: ClassVar[str] = "irr.capability_match_evaluation_admission_attribution.v1"

    resolver_ref: StableRef
    admission_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.resolver_ref) is not StableRef:
            raise ValidationError(
                "CapabilityMatchEvaluationAdmissionAttribution.resolver_ref "
                "must be a StableRef"
            )
        if type(self.admission_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityMatchEvaluationAdmissionAttribution.admission_event_ref "
                "must be a StableRef"
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
        field: str = "CapabilityMatchEvaluationAdmissionAttribution",
    ) -> CapabilityMatchEvaluationAdmissionAttribution:
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
    ) -> CapabilityMatchEvaluationAdmissionAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CandidateCapabilityMatchEvaluation(
    _CanonicalCapabilityMatchEvaluationAdmissionRecord
):
    """Proposed exhaustive catalog assessment; not active M2.3 evaluation state."""

    SCHEMA: ClassVar[str] = "irr.candidate_capability_match_evaluation.v1"

    evaluation: CapabilityMatchEvaluation
    rationale: str

    def __post_init__(self) -> None:
        if type(self.evaluation) is not CapabilityMatchEvaluation:
            raise ValidationError(
                "CandidateCapabilityMatchEvaluation.evaluation must be a "
                "CapabilityMatchEvaluation"
            )
        _require_text(self.rationale, field="CandidateCapabilityMatchEvaluation.rationale")

    def to_primitive(self) -> dict[str, object]:
        return {
            "evaluation": self.evaluation.to_primitive(),
            "rationale": self.rationale,
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CandidateCapabilityMatchEvaluation"
    ) -> CandidateCapabilityMatchEvaluation:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(obj, {"schema", "evaluation", "rationale"}, field=field)
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                evaluation=CapabilityMatchEvaluation.from_primitive(
                    obj["evaluation"], field=f"{field}.evaluation"
                ),
                rationale=obj["rationale"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> CandidateCapabilityMatchEvaluation:
        return cls.from_primitive(parse_json_object(data))


def _normalize_candidates(
    value: object, *, field: str
) -> tuple[CandidateCapabilityMatchEvaluation, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CandidateCapabilityMatchEvaluation for item in value):
        raise ValidationError(
            f"{field} must contain CandidateCapabilityMatchEvaluation values"
        )
    candidates = cast(tuple[CandidateCapabilityMatchEvaluation, ...], value)
    identities = [candidate.identity for candidate in candidates]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate candidate identities")
    return tuple(sorted(candidates, key=lambda candidate: str(candidate.identity)))


def _validate_candidate_targets(
    candidates: tuple[CandidateCapabilityMatchEvaluation, ...],
    *,
    requirement: CapabilityRequirement,
    catalog_snapshot: CapabilityCatalogSnapshot,
    field: str,
) -> None:
    for candidate in candidates:
        if candidate.evaluation.requirement != requirement:
            raise ValidationError(f"{field} contains a foreign CapabilityRequirement")
        if candidate.evaluation.catalog_snapshot != catalog_snapshot:
            raise ValidationError(f"{field} contains a foreign CapabilityCatalogSnapshot")


def _evaluation_semantic_key(evaluation: CapabilityMatchEvaluation) -> tuple[object, ...]:
    compatible = tuple(
        sorted(
            (
                match.capability_ref,
                match.capability_contract_identity,
                match.scope_matches,
                match.input_matches,
                match.output_matches,
                match.effect_matches,
            )
            for match in evaluation.compatible_matches
        , key=lambda item: (item[0].namespace, item[0].value, str(item[1])))
    )
    incompatible = tuple(
        (
            assessment.capability_ref,
            assessment.capability_contract_identity,
            assessment.reasons,
        )
        for assessment in evaluation.incompatible_assessments
    )
    return (
        evaluation.requirement.identity,
        evaluation.catalog_snapshot.identity,
        compatible,
        incompatible,
    )


@dataclass(frozen=True, slots=True)
class AdmittedCapabilityMatchEvaluation(
    _CanonicalCapabilityMatchEvaluationAdmissionRecord
):
    """Explicit IRR admission of one exhaustive match evaluation; never selection."""

    SCHEMA: ClassVar[str] = "irr.admitted_capability_match_evaluation.v1"

    admission_attribution: CapabilityMatchEvaluationAdmissionAttribution
    evaluation: CapabilityMatchEvaluation
    candidate_inputs: tuple[CandidateCapabilityMatchEvaluation, ...] = ()

    def __post_init__(self) -> None:
        if type(self.admission_attribution) is not (
            CapabilityMatchEvaluationAdmissionAttribution
        ):
            raise ValidationError(
                "AdmittedCapabilityMatchEvaluation.admission_attribution must be a "
                "CapabilityMatchEvaluationAdmissionAttribution"
            )
        if type(self.evaluation) is not CapabilityMatchEvaluation:
            raise ValidationError(
                "AdmittedCapabilityMatchEvaluation.evaluation must be a "
                "CapabilityMatchEvaluation"
            )
        candidates = _normalize_candidates(
            self.candidate_inputs,
            field="AdmittedCapabilityMatchEvaluation.candidate_inputs",
        )
        _validate_candidate_targets(
            candidates,
            requirement=self.evaluation.requirement,
            catalog_snapshot=self.evaluation.catalog_snapshot,
            field="AdmittedCapabilityMatchEvaluation.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_attribution": self.admission_attribution.to_primitive(),
            "candidate_inputs": [item.to_primitive() for item in self.candidate_inputs],
            "evaluation": self.evaluation.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "AdmittedCapabilityMatchEvaluation"
    ) -> AdmittedCapabilityMatchEvaluation:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "admission_attribution", "evaluation", "candidate_inputs"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        candidates = _expect_array(
            obj["candidate_inputs"], field=f"{field}.candidate_inputs"
        )
        try:
            return cls(
                admission_attribution=(
                    CapabilityMatchEvaluationAdmissionAttribution.from_primitive(
                        obj["admission_attribution"],
                        field=f"{field}.admission_attribution",
                    )
                ),
                evaluation=CapabilityMatchEvaluation.from_primitive(
                    obj["evaluation"], field=f"{field}.evaluation"
                ),
                candidate_inputs=tuple(
                    CandidateCapabilityMatchEvaluation.from_primitive(
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
    ) -> AdmittedCapabilityMatchEvaluation:
        return cls.from_primitive(parse_json_object(data))


class CapabilityMatchEvaluationAdmissionFrontierKind(StrEnum):
    PROPOSAL_INPUT_REQUIRED = "proposal_input_required"
    ADMISSION_REQUIRED = "admission_required"
    ADJUDICATION_REQUIRED = "adjudication_required"
    EVALUATION_OUTPUT_AVAILABLE = "evaluation_output_available"


@dataclass(frozen=True, slots=True)
class CapabilityMatchEvaluationAdmissionFrontier:
    """Derived admission state for one requirement/catalog evaluation surface."""

    requirement: CapabilityRequirement
    catalog_snapshot: CapabilityCatalogSnapshot
    candidate_inputs: tuple[CandidateCapabilityMatchEvaluation, ...]
    kind: CapabilityMatchEvaluationAdmissionFrontierKind
    admitted_evaluation: AdmittedCapabilityMatchEvaluation | None = None

    def __post_init__(self) -> None:
        if type(self.requirement) is not CapabilityRequirement:
            raise ValidationError(
                "CapabilityMatchEvaluationAdmissionFrontier.requirement must be a "
                "CapabilityRequirement"
            )
        if type(self.catalog_snapshot) is not CapabilityCatalogSnapshot:
            raise ValidationError(
                "CapabilityMatchEvaluationAdmissionFrontier.catalog_snapshot must be a "
                "CapabilityCatalogSnapshot"
            )
        candidates = _normalize_candidates(
            self.candidate_inputs,
            field="CapabilityMatchEvaluationAdmissionFrontier.candidate_inputs",
        )
        _validate_candidate_targets(
            candidates,
            requirement=self.requirement,
            catalog_snapshot=self.catalog_snapshot,
            field="CapabilityMatchEvaluationAdmissionFrontier.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)
        if type(self.kind) is not CapabilityMatchEvaluationAdmissionFrontierKind:
            raise ValidationError(
                "CapabilityMatchEvaluationAdmissionFrontier.kind must be a "
                "CapabilityMatchEvaluationAdmissionFrontierKind"
            )

        output = self.admitted_evaluation
        if (
            self.kind
            is CapabilityMatchEvaluationAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
        ):
            if candidates or output is not None:
                raise ValidationError(
                    "proposal_input_required frontier cannot contain candidates or output"
                )
            return

        if self.kind in (
            CapabilityMatchEvaluationAdmissionFrontierKind.ADMISSION_REQUIRED,
            CapabilityMatchEvaluationAdmissionFrontierKind.ADJUDICATION_REQUIRED,
        ):
            if not candidates:
                raise ValidationError(
                    f"{self.kind.value} frontier requires explicit candidate material"
                )
            if output is not None:
                raise ValidationError(
                    f"{self.kind.value} frontier cannot contain admitted output"
                )
            expected_kind = _unresolved_kind(candidates)
            if self.kind is not expected_kind:
                raise ValidationError(
                    "unresolved capability match evaluation frontier kind must match "
                    "exact candidate semantics"
                )
            return

        if (
            self.kind
            is CapabilityMatchEvaluationAdmissionFrontierKind.EVALUATION_OUTPUT_AVAILABLE
        ):
            if type(output) is not AdmittedCapabilityMatchEvaluation:
                raise ValidationError(
                    "evaluation_output_available requires "
                    "AdmittedCapabilityMatchEvaluation"
                )
            if output.evaluation.requirement != self.requirement:
                raise ValidationError("admitted evaluation changed the exact requirement")
            if output.evaluation.catalog_snapshot != self.catalog_snapshot:
                raise ValidationError("admitted evaluation changed the exact catalog snapshot")
            if output.candidate_inputs != candidates:
                raise ValidationError(
                    "evaluation_output_available candidate_inputs must equal exact "
                    "output provenance"
                )
            return

        raise AssertionError("unsupported CapabilityMatchEvaluationAdmissionFrontierKind")


CapabilityMatchEvaluationAdmitter: TypeAlias = Callable[
    [
        CapabilityRequirement,
        CapabilityCatalogSnapshot,
        tuple[CandidateCapabilityMatchEvaluation, ...],
        CapabilityMatchEvaluationAdmissionAttribution,
    ],
    AdmittedCapabilityMatchEvaluation | None,
]


def _unresolved_kind(
    candidates: tuple[CandidateCapabilityMatchEvaluation, ...],
) -> CapabilityMatchEvaluationAdmissionFrontierKind:
    if not candidates:
        return CapabilityMatchEvaluationAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
    semantic_keys = {
        _evaluation_semantic_key(candidate.evaluation) for candidate in candidates
    }
    if len(semantic_keys) == 1:
        return CapabilityMatchEvaluationAdmissionFrontierKind.ADMISSION_REQUIRED
    return CapabilityMatchEvaluationAdmissionFrontierKind.ADJUDICATION_REQUIRED


def orchestrate_capability_match_evaluation_admission(
    requirement: CapabilityRequirement,
    catalog_snapshot: CapabilityCatalogSnapshot,
    *,
    candidate_inputs: tuple[CandidateCapabilityMatchEvaluation, ...] = (),
    admitted_outputs: tuple[AdmittedCapabilityMatchEvaluation, ...] = (),
    admitter: CapabilityMatchEvaluationAdmitter | None = None,
    admission_attribution: CapabilityMatchEvaluationAdmissionAttribution | None = None,
) -> CapabilityMatchEvaluationAdmissionFrontier:
    """Derive or explicitly advance one capability match evaluation admission.

    Evaluation construction is not admission. Evaluator provenance never votes. The
    explicit admitter may adjudicate or synthesize one exhaustive evaluation while
    preserving the complete supplied candidate set. This function performs no catalog
    discovery, capability selection, WorkProposal synthesis, Governance, Authorization,
    Attempt, external effect, retry, fallback, or recovery.
    """

    if type(requirement) is not CapabilityRequirement:
        raise ValidationError("requirement must be an exact CapabilityRequirement")
    if type(catalog_snapshot) is not CapabilityCatalogSnapshot:
        raise ValidationError("catalog_snapshot must be an exact CapabilityCatalogSnapshot")

    candidates = _normalize_candidates(candidate_inputs, field="candidate_inputs")
    _validate_candidate_targets(
        candidates,
        requirement=requirement,
        catalog_snapshot=catalog_snapshot,
        field="candidate_inputs",
    )

    if type(admitted_outputs) is not tuple:
        raise ValidationError("admitted_outputs must be a tuple")
    if not all(type(item) is AdmittedCapabilityMatchEvaluation for item in admitted_outputs):
        raise ValidationError(
            "admitted_outputs must contain AdmittedCapabilityMatchEvaluation values"
        )
    outputs = cast(tuple[AdmittedCapabilityMatchEvaluation, ...], admitted_outputs)
    if len(outputs) > 1:
        raise ValidationError("competing admitted capability match evaluations fail closed")

    if outputs:
        output = outputs[0]
        if output.evaluation.requirement != requirement:
            raise ValidationError("admitted output belongs to a foreign requirement")
        if output.evaluation.catalog_snapshot != catalog_snapshot:
            raise ValidationError("admitted output belongs to a foreign catalog snapshot")
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
                "candidate material outside admitted evaluation provenance is orphaned"
            )
        return CapabilityMatchEvaluationAdmissionFrontier(
            requirement=requirement,
            catalog_snapshot=catalog_snapshot,
            candidate_inputs=output.candidate_inputs,
            kind=(
                CapabilityMatchEvaluationAdmissionFrontierKind.EVALUATION_OUTPUT_AVAILABLE
            ),
            admitted_evaluation=output,
        )

    unresolved = CapabilityMatchEvaluationAdmissionFrontier(
        requirement=requirement,
        catalog_snapshot=catalog_snapshot,
        candidate_inputs=candidates,
        kind=_unresolved_kind(candidates),
    )
    if admitter is None:
        if admission_attribution is not None:
            raise ValidationError(
                "admission_attribution requires an explicit capability match "
                "evaluation admitter"
            )
        return unresolved
    if not callable(admitter):
        raise ValidationError("admitter must be callable")
    if type(admission_attribution) is not CapabilityMatchEvaluationAdmissionAttribution:
        raise ValidationError(
            "explicit admission requires "
            "CapabilityMatchEvaluationAdmissionAttribution"
        )

    admitted = admitter(requirement, catalog_snapshot, candidates, admission_attribution)
    if admitted is None:
        return unresolved
    if type(admitted) is not AdmittedCapabilityMatchEvaluation:
        raise ValidationError(
            "capability match evaluation admitter must return "
            "AdmittedCapabilityMatchEvaluation or None"
        )
    if admitted.admission_attribution != admission_attribution:
        raise ValidationError("admitter changed the exact admission attribution")
    if admitted.evaluation.requirement != requirement:
        raise ValidationError("admitter returned a foreign requirement evaluation")
    if admitted.evaluation.catalog_snapshot != catalog_snapshot:
        raise ValidationError("admitter returned a foreign catalog snapshot evaluation")
    if admitted.candidate_inputs != candidates:
        raise ValidationError("admitter must preserve the exact candidate set")

    return CapabilityMatchEvaluationAdmissionFrontier(
        requirement=requirement,
        catalog_snapshot=catalog_snapshot,
        candidate_inputs=candidates,
        kind=CapabilityMatchEvaluationAdmissionFrontierKind.EVALUATION_OUTPUT_AVAILABLE,
        admitted_evaluation=admitted,
    )


__all__ = (
    "AdmittedCapabilityMatchEvaluation",
    "CandidateCapabilityMatchEvaluation",
    "CapabilityMatchEvaluationAdmissionAttribution",
    "CapabilityMatchEvaluationAdmissionFrontier",
    "CapabilityMatchEvaluationAdmissionFrontierKind",
    "orchestrate_capability_match_evaluation_admission",
)
