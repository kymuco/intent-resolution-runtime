from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, TypeAlias, cast

from .canonical import canonical_json_bytes, parse_json_object
from .context import ContextEnvelope
from .continuation import ContinuationInput
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .resolution import (
    CandidateResolution,
    ClarificationNeed,
    InformationNeed,
    ResolutionAttribution,
    ResolutionOutput,
    ResolvedIntent,
)
from .successor_resolution import (
    SuccessorResolutionKind,
    SuccessorResolutionLineage,
)


def _expect_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SerializationError(f"{field} must be a JSON object")
    return value


def _expect_array(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise SerializationError(f"{field} must be a JSON array")
    return value


def _expect_exact_keys(
    value: dict[str, Any],
    expected: set[str],
    *,
    field: str,
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
        raise SerializationError(
            f"{field} has invalid fields ({', '.join(details)})"
        )


def _identity_key(value: RecordIdentity) -> tuple[str, str]:
    return value.algorithm, value.digest


class _CanonicalSuccessorSemanticRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


def _normalize_continuation_inputs(
    value: object,
    *,
    field: str,
) -> tuple[ContinuationInput, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if not all(type(item) is ContinuationInput for item in value):
        raise ValidationError(f"{field} must contain ContinuationInput values")

    inputs = cast(tuple[ContinuationInput, ...], value)
    identities = [item.identity for item in inputs]
    if len(set(identities)) != len(identities):
        raise ValidationError(
            f"{field} must not contain duplicate ContinuationInput identities"
        )

    source_identities = [item.source_identity for item in inputs]
    if len(set(source_identities)) != len(source_identities):
        raise ValidationError(
            f"{field} must not amplify one source through repeated re-entry occurrences"
        )

    return tuple(sorted(inputs, key=lambda item: _identity_key(item.source_identity)))


@dataclass(frozen=True, slots=True)
class SuccessorCandidateResolution(_CanonicalSuccessorSemanticRecord):
    """Provider proposal provenance bound to exact successor re-entry material."""

    SCHEMA: ClassVar[str] = "irr.successor_candidate_resolution.v1"

    predecessor: ResolvedIntent
    continuation_inputs: tuple[ContinuationInput, ...]
    candidate: CandidateResolution

    def __post_init__(self) -> None:
        if type(self.predecessor) is not ResolvedIntent:
            raise ValidationError(
                "SuccessorCandidateResolution.predecessor must be a ResolvedIntent"
            )
        inputs = _normalize_continuation_inputs(
            self.continuation_inputs,
            field="SuccessorCandidateResolution.continuation_inputs",
        )
        if any(
            item.resolved_intent_identity != self.predecessor.identity
            for item in inputs
        ):
            raise ValidationError(
                "SuccessorCandidateResolution continuation inputs must descend "
                "from the exact predecessor ResolvedIntent"
            )
        object.__setattr__(self, "continuation_inputs", inputs)

        if type(self.candidate) is not CandidateResolution:
            raise ValidationError(
                "SuccessorCandidateResolution.candidate must be a CandidateResolution"
            )
        if (
            self.candidate.intent_request_identity
            != self.predecessor.intent_request_identity
        ):
            raise ValidationError(
                "SuccessorCandidateResolution candidate must preserve the "
                "predecessor IntentRequest identity"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "candidate": self.candidate.to_primitive(),
            "continuation_inputs": [
                item.to_primitive() for item in self.continuation_inputs
            ],
            "predecessor": self.predecessor.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "SuccessorCandidateResolution",
    ) -> SuccessorCandidateResolution:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "predecessor",
                "continuation_inputs",
                "candidate",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported {field} schema: {obj['schema']!r}"
            )
        inputs = _expect_array(
            obj["continuation_inputs"],
            field=f"{field}.continuation_inputs",
        )
        try:
            return cls(
                predecessor=ResolvedIntent.from_primitive(obj["predecessor"]),
                continuation_inputs=tuple(
                    ContinuationInput.from_primitive(
                        item,
                        field=f"{field}.continuation_inputs[{index}]",
                    )
                    for index, item in enumerate(inputs)
                ),
                candidate=CandidateResolution.from_primitive(obj["candidate"]),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> SuccessorCandidateResolution:
        return cls.from_primitive(parse_json_object(data))


def _normalize_successor_candidates(
    value: object,
    *,
    field: str,
) -> tuple[SuccessorCandidateResolution, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is SuccessorCandidateResolution for item in value):
        raise ValidationError(
            f"{field} must contain SuccessorCandidateResolution values"
        )
    candidates = cast(tuple[SuccessorCandidateResolution, ...], value)
    identities = [item.identity for item in candidates]
    if len(set(identities)) != len(identities):
        raise ValidationError(
            f"{field} must not contain duplicate successor candidate identities"
        )
    return tuple(sorted(candidates, key=lambda item: _identity_key(item.identity)))


def _normalize_lineages(
    value: object,
    *,
    field: str,
) -> tuple[SuccessorResolutionLineage, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is SuccessorResolutionLineage for item in value):
        raise ValidationError(
            f"{field} must contain SuccessorResolutionLineage values"
        )
    lineages = cast(tuple[SuccessorResolutionLineage, ...], value)
    identities = [item.identity for item in lineages]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate lineage identities")
    return tuple(sorted(lineages, key=lambda item: _identity_key(item.identity)))


def _nested_candidates(
    candidates: tuple[SuccessorCandidateResolution, ...],
) -> tuple[CandidateResolution, ...]:
    nested = tuple(item.candidate for item in candidates)
    return tuple(sorted(nested, key=lambda item: _identity_key(item.identity)))


def _semantic_signature(
    candidate: SuccessorCandidateResolution,
) -> tuple[object, ...]:
    nested = candidate.candidate
    return (
        nested.proposed_semantics,
        nested.assumptions,
        nested.issues,
        nested.clarification_proposals,
        nested.information_need_proposals,
    )


def _candidates_are_semantically_equivalent(
    candidates: tuple[SuccessorCandidateResolution, ...],
) -> bool:
    if not candidates:
        return True
    signature = _semantic_signature(candidates[0])
    return all(_semantic_signature(item) == signature for item in candidates[1:])


class SuccessorResolutionFrontierKind(str, Enum):
    """Narrow M4.0 successor-resolution frontier classification."""

    RESOLUTION_INPUT_REQUIRED = "resolution_input_required"
    ADMISSION_REQUIRED = "admission_required"
    ADJUDICATION_REQUIRED = "adjudication_required"
    RESOLUTION_OUTPUT_AVAILABLE = "resolution_output_available"


@dataclass(frozen=True, slots=True)
class SuccessorResolutionFrontier:
    """Derived non-canonical view over one exact successor semantic branch."""

    predecessor: ResolvedIntent
    continuation_inputs: tuple[ContinuationInput, ...]
    context_envelope_identity: RecordIdentity
    kind: SuccessorResolutionFrontierKind
    candidate_inputs: tuple[SuccessorCandidateResolution, ...] = ()
    successor_lineage: SuccessorResolutionLineage | None = None

    def __post_init__(self) -> None:
        if type(self.predecessor) is not ResolvedIntent:
            raise ValidationError(
                "SuccessorResolutionFrontier.predecessor must be a ResolvedIntent"
            )

        inputs = _normalize_continuation_inputs(
            self.continuation_inputs,
            field="SuccessorResolutionFrontier.continuation_inputs",
        )
        if any(
            item.resolved_intent_identity != self.predecessor.identity
            for item in inputs
        ):
            raise ValidationError(
                "SuccessorResolutionFrontier continuation inputs must descend "
                "from the exact predecessor ResolvedIntent"
            )
        object.__setattr__(self, "continuation_inputs", inputs)

        if type(self.context_envelope_identity) is not RecordIdentity:
            raise ValidationError(
                "SuccessorResolutionFrontier.context_envelope_identity must be "
                "a RecordIdentity"
            )
        if type(self.kind) is not SuccessorResolutionFrontierKind:
            raise ValidationError(
                "SuccessorResolutionFrontier.kind must be a "
                "SuccessorResolutionFrontierKind"
            )

        candidates = _normalize_successor_candidates(
            self.candidate_inputs,
            field="SuccessorResolutionFrontier.candidate_inputs",
        )
        for candidate in candidates:
            _validate_successor_candidate(
                candidate,
                predecessor=self.predecessor,
                continuation_inputs=inputs,
                context_envelope_identity=self.context_envelope_identity,
                field="SuccessorResolutionFrontier.candidate_inputs",
            )
        object.__setattr__(self, "candidate_inputs", candidates)

        lineage = self.successor_lineage
        if lineage is not None:
            _validate_existing_lineage(
                lineage,
                predecessor=self.predecessor,
                continuation_inputs=inputs,
                context_envelope_identity=self.context_envelope_identity,
                candidates=candidates,
            )

        if self.kind is SuccessorResolutionFrontierKind.RESOLUTION_INPUT_REQUIRED:
            if candidates or lineage is not None:
                raise ValidationError(
                    "resolution_input_required frontier cannot contain candidate "
                    "or successor lineage"
                )
        elif self.kind in (
            SuccessorResolutionFrontierKind.ADMISSION_REQUIRED,
            SuccessorResolutionFrontierKind.ADJUDICATION_REQUIRED,
        ):
            if not candidates:
                raise ValidationError(
                    f"{self.kind.value} frontier requires explicit candidate material"
                )
            if lineage is not None:
                raise ValidationError(
                    f"{self.kind.value} frontier cannot contain admitted lineage"
                )
        elif self.kind is SuccessorResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE:
            if lineage is None:
                raise ValidationError(
                    "resolution_output_available frontier requires successor lineage"
                )
        else:  # pragma: no cover
            raise AssertionError("unsupported SuccessorResolutionFrontierKind")

    @property
    def resolution_output(self) -> ResolutionOutput | None:
        if self.successor_lineage is None:
            return None
        return self.successor_lineage.successor


SuccessorResolutionAdmitter: TypeAlias = Callable[
    [
        ResolvedIntent,
        ContextEnvelope,
        tuple[ContinuationInput, ...],
        tuple[SuccessorCandidateResolution, ...],
        ResolutionAttribution,
    ],
    ResolutionOutput | None,
]


def _validate_successor_candidate(
    candidate: SuccessorCandidateResolution,
    *,
    predecessor: ResolvedIntent,
    continuation_inputs: tuple[ContinuationInput, ...],
    context_envelope_identity: RecordIdentity,
    field: str,
) -> None:
    if candidate.predecessor != predecessor:
        raise ValidationError(f"{field} contains a foreign predecessor lineage")
    if candidate.continuation_inputs != continuation_inputs:
        raise ValidationError(f"{field} contains foreign continuation material")
    if candidate.candidate.context_envelope_identity != context_envelope_identity:
        raise ValidationError(f"{field} contains a foreign ContextEnvelope lineage")


def _validate_existing_lineage(
    lineage: SuccessorResolutionLineage,
    *,
    predecessor: ResolvedIntent,
    continuation_inputs: tuple[ContinuationInput, ...],
    context_envelope_identity: RecordIdentity,
    candidates: tuple[SuccessorCandidateResolution, ...],
) -> None:
    if lineage.predecessor != predecessor:
        raise ValidationError(
            "existing SuccessorResolutionLineage must preserve exact predecessor"
        )
    if lineage.continuation_inputs != continuation_inputs:
        raise ValidationError(
            "existing SuccessorResolutionLineage must preserve exact continuation inputs"
        )
    if lineage.successor.context_envelope_identity != context_envelope_identity:
        raise ValidationError(
            "existing SuccessorResolutionLineage successor must preserve exact "
            "ContextEnvelope identity"
        )
    if lineage.successor.candidate_inputs != _nested_candidates(candidates):
        raise ValidationError(
            "existing SuccessorResolutionLineage successor must preserve complete "
            "exact successor candidate provenance"
        )


def _unresolved_kind(
    candidates: tuple[SuccessorCandidateResolution, ...],
) -> SuccessorResolutionFrontierKind:
    if not candidates:
        return SuccessorResolutionFrontierKind.RESOLUTION_INPUT_REQUIRED
    if _candidates_are_semantically_equivalent(candidates):
        return SuccessorResolutionFrontierKind.ADMISSION_REQUIRED
    return SuccessorResolutionFrontierKind.ADJUDICATION_REQUIRED


def _frontier_without_output(
    predecessor: ResolvedIntent,
    continuation_inputs: tuple[ContinuationInput, ...],
    context_envelope: ContextEnvelope,
    candidates: tuple[SuccessorCandidateResolution, ...],
) -> SuccessorResolutionFrontier:
    return SuccessorResolutionFrontier(
        predecessor=predecessor,
        continuation_inputs=continuation_inputs,
        context_envelope_identity=context_envelope.identity,
        kind=_unresolved_kind(candidates),
        candidate_inputs=candidates,
    )


def _validate_output(
    output: object,
    *,
    predecessor: ResolvedIntent,
    context_envelope: ContextEnvelope,
    candidates: tuple[SuccessorCandidateResolution, ...],
    admission_attribution: ResolutionAttribution,
) -> ResolutionOutput:
    if type(output) not in (ResolvedIntent, ClarificationNeed, InformationNeed):
        raise ValidationError(
            "successor-resolution admitter output must be an exact ResolutionOutput"
        )
    admitted = cast(ResolutionOutput, output)
    if admitted.intent_request_identity != predecessor.intent_request_identity:
        raise ValidationError(
            "successor-resolution output must preserve predecessor IntentRequest identity"
        )
    if admitted.context_envelope_identity != context_envelope.identity:
        raise ValidationError(
            "successor-resolution output must preserve exact ContextEnvelope identity"
        )
    if admitted.admission_attribution != admission_attribution:
        raise ValidationError(
            "successor-resolution output must preserve exact supplied "
            "ResolutionAttribution"
        )
    if admitted.candidate_inputs != _nested_candidates(candidates):
        raise ValidationError(
            "successor-resolution output must preserve complete exact supplied "
            "candidate provenance"
        )
    return admitted


def _successor_kind(output: ResolutionOutput) -> SuccessorResolutionKind:
    if type(output) is ResolvedIntent:
        return SuccessorResolutionKind.RESOLVED_INTENT
    if type(output) is ClarificationNeed:
        return SuccessorResolutionKind.CLARIFICATION_NEED
    if type(output) is InformationNeed:
        return SuccessorResolutionKind.INFORMATION_NEED
    raise AssertionError("validated ResolutionOutput lost exact type")


def orchestrate_successor_resolution(
    predecessor: ResolvedIntent,
    context_envelope: ContextEnvelope,
    continuation_inputs: tuple[ContinuationInput, ...],
    *,
    candidate_inputs: tuple[SuccessorCandidateResolution, ...] = (),
    admitted_lineages: tuple[SuccessorResolutionLineage, ...] = (),
    admitter: SuccessorResolutionAdmitter | None = None,
    admission_attribution: ResolutionAttribution | None = None,
) -> SuccessorResolutionFrontier:
    """Derive or explicitly admit one exact successor semantic branch."""

    if type(predecessor) is not ResolvedIntent:
        raise ValidationError(
            "orchestrate_successor_resolution.predecessor must be a ResolvedIntent"
        )
    if type(context_envelope) is not ContextEnvelope:
        raise ValidationError(
            "orchestrate_successor_resolution.context_envelope must be a ContextEnvelope"
        )
    if context_envelope.intent_request_identity != predecessor.intent_request_identity:
        raise ValidationError(
            "successor ContextEnvelope must belong to predecessor IntentRequest"
        )

    inputs = _normalize_continuation_inputs(
        continuation_inputs,
        field="orchestrate_successor_resolution.continuation_inputs",
    )
    if any(item.resolved_intent_identity != predecessor.identity for item in inputs):
        raise ValidationError(
            "successor continuation inputs must descend from exact predecessor"
        )

    candidates = _normalize_successor_candidates(
        candidate_inputs,
        field="orchestrate_successor_resolution.candidate_inputs",
    )
    for candidate in candidates:
        _validate_successor_candidate(
            candidate,
            predecessor=predecessor,
            continuation_inputs=inputs,
            context_envelope_identity=context_envelope.identity,
            field="orchestrate_successor_resolution.candidate_inputs",
        )

    lineages = _normalize_lineages(
        admitted_lineages,
        field="orchestrate_successor_resolution.admitted_lineages",
    )
    if len(lineages) > 1:
        raise ValidationError(
            "successor lifecycle graph must not contain competing admitted lineages"
        )

    if lineages:
        if admitter is not None or admission_attribution is not None:
            raise ValidationError(
                "existing SuccessorResolutionLineage cannot be combined with a new "
                "admission transition"
            )
        lineage = lineages[0]
        _validate_existing_lineage(
            lineage,
            predecessor=predecessor,
            continuation_inputs=inputs,
            context_envelope_identity=context_envelope.identity,
            candidates=candidates,
        )
        return SuccessorResolutionFrontier(
            predecessor=predecessor,
            continuation_inputs=inputs,
            context_envelope_identity=context_envelope.identity,
            kind=SuccessorResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE,
            candidate_inputs=candidates,
            successor_lineage=lineage,
        )

    if admitter is None:
        if admission_attribution is not None:
            raise ValidationError(
                "ResolutionAttribution cannot be supplied without an explicit "
                "successor-resolution admitter"
            )
        return _frontier_without_output(
            predecessor,
            inputs,
            context_envelope,
            candidates,
        )

    if not callable(admitter):
        raise ValidationError(
            "orchestrate_successor_resolution.admitter must be callable"
        )
    if admission_attribution is None:
        raise ValidationError(
            "successor-resolution admitter requires explicit ResolutionAttribution"
        )
    if type(admission_attribution) is not ResolutionAttribution:
        raise ValidationError(
            "orchestrate_successor_resolution.admission_attribution must be a "
            "ResolutionAttribution"
        )

    proposed_output = admitter(
        predecessor,
        context_envelope,
        inputs,
        candidates,
        admission_attribution,
    )
    if proposed_output is None:
        return _frontier_without_output(
            predecessor,
            inputs,
            context_envelope,
            candidates,
        )

    output = _validate_output(
        proposed_output,
        predecessor=predecessor,
        context_envelope=context_envelope,
        candidates=candidates,
        admission_attribution=admission_attribution,
    )
    lineage = SuccessorResolutionLineage(
        predecessor=predecessor,
        continuation_inputs=inputs,
        successor_kind=_successor_kind(output),
        successor=output,
    )

    return SuccessorResolutionFrontier(
        predecessor=predecessor,
        continuation_inputs=inputs,
        context_envelope_identity=context_envelope.identity,
        kind=SuccessorResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE,
        candidate_inputs=candidates,
        successor_lineage=lineage,
    )


__all__ = (
    "SuccessorCandidateResolution",
    "SuccessorResolutionAdmitter",
    "SuccessorResolutionFrontier",
    "SuccessorResolutionFrontierKind",
    "orchestrate_successor_resolution",
)
