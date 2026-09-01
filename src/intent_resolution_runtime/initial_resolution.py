from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeAlias

from .context import ContextEnvelope
from .errors import ValidationError
from .identity import RecordIdentity
from .intent import IntentRequest
from .resolution import (
    CandidateResolution,
    ClarificationNeed,
    InformationNeed,
    ResolutionAttribution,
    ResolvedIntent,
)


ResolutionOutput: TypeAlias = ResolvedIntent | ClarificationNeed | InformationNeed
InitialResolutionAdmitter: TypeAlias = Callable[
    [
        IntentRequest,
        ContextEnvelope,
        tuple[CandidateResolution, ...],
        ResolutionAttribution,
    ],
    ResolutionOutput | None,
]


class InitialResolutionFrontierKind(str, Enum):
    """Narrow M2.1 frontier classification; not a global lifecycle state."""

    RESOLUTION_INPUT_REQUIRED = "resolution_input_required"
    ADMISSION_REQUIRED = "admission_required"
    ADJUDICATION_REQUIRED = "adjudication_required"
    RESOLUTION_OUTPUT_AVAILABLE = "resolution_output_available"


@dataclass(frozen=True, slots=True)
class InitialResolutionFrontier:
    """Derived non-canonical view over the admitted initial-resolution graph slice."""

    intent_request_identity: RecordIdentity
    context_envelope_identity: RecordIdentity
    kind: InitialResolutionFrontierKind
    candidate_inputs: tuple[CandidateResolution, ...] = ()
    resolution_output: ResolutionOutput | None = None

    def __post_init__(self) -> None:
        if type(self.intent_request_identity) is not RecordIdentity:
            raise ValidationError(
                "InitialResolutionFrontier.intent_request_identity must be a RecordIdentity"
            )
        if type(self.context_envelope_identity) is not RecordIdentity:
            raise ValidationError(
                "InitialResolutionFrontier.context_envelope_identity must be a RecordIdentity"
            )
        if type(self.kind) is not InitialResolutionFrontierKind:
            raise ValidationError(
                "InitialResolutionFrontier.kind must be an InitialResolutionFrontierKind"
            )
        candidates = _normalize_candidates(
            self.candidate_inputs,
            field="InitialResolutionFrontier.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)

        for candidate in candidates:
            _validate_candidate_lineage(
                candidate,
                intent_request_identity=self.intent_request_identity,
                context_envelope_identity=self.context_envelope_identity,
                field="InitialResolutionFrontier.candidate_inputs",
            )

        if self.resolution_output is not None:
            _validate_resolution_output_lineage(
                self.resolution_output,
                intent_request_identity=self.intent_request_identity,
                context_envelope_identity=self.context_envelope_identity,
                field="InitialResolutionFrontier.resolution_output",
            )

        if self.kind is InitialResolutionFrontierKind.RESOLUTION_INPUT_REQUIRED:
            if candidates or self.resolution_output is not None:
                raise ValidationError(
                    "resolution_input_required frontier cannot contain candidate or resolution output"
                )
        elif self.kind in (
            InitialResolutionFrontierKind.ADMISSION_REQUIRED,
            InitialResolutionFrontierKind.ADJUDICATION_REQUIRED,
        ):
            if not candidates:
                raise ValidationError(
                    f"{self.kind.value} frontier requires explicit candidate material"
                )
            if self.resolution_output is not None:
                raise ValidationError(
                    f"{self.kind.value} frontier cannot contain an admitted resolution output"
                )
        elif self.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE:
            if self.resolution_output is None:
                raise ValidationError(
                    "resolution_output_available frontier requires a ResolutionOutput"
                )
            if candidates != self.resolution_output.candidate_inputs:
                raise ValidationError(
                    "resolution_output_available candidate_inputs must equal exact output provenance"
                )
        else:  # pragma: no cover - exhaustive enum guard
            raise AssertionError("unsupported InitialResolutionFrontierKind")


def _normalize_candidates(
    value: object, *, field: str
) -> tuple[CandidateResolution, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CandidateResolution for item in value):
        raise ValidationError(f"{field} must contain CandidateResolution values")
    candidates = tuple(value)
    identities = [candidate.identity for candidate in candidates]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate candidate identities")
    return tuple(sorted(candidates, key=lambda candidate: str(candidate.identity)))


def _normalize_outputs(
    value: object, *, field: str
) -> tuple[ResolutionOutput, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    allowed = (ResolvedIntent, ClarificationNeed, InformationNeed)
    if not all(type(item) in allowed for item in value):
        raise ValidationError(f"{field} must contain ResolutionOutput values")
    outputs = tuple(value)
    identities = [output.identity for output in outputs]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate output identities")
    return tuple(sorted(outputs, key=lambda output: str(output.identity)))


def _validate_candidate_lineage(
    candidate: CandidateResolution,
    *,
    intent_request_identity: RecordIdentity,
    context_envelope_identity: RecordIdentity,
    field: str,
) -> None:
    if candidate.intent_request_identity != intent_request_identity:
        raise ValidationError(f"{field} contains a foreign IntentRequest lineage")
    if candidate.context_envelope_identity != context_envelope_identity:
        raise ValidationError(f"{field} contains a foreign ContextEnvelope lineage")


def _validate_resolution_output_lineage(
    output: object,
    *,
    intent_request_identity: RecordIdentity,
    context_envelope_identity: RecordIdentity,
    field: str,
) -> ResolutionOutput:
    if type(output) not in (ResolvedIntent, ClarificationNeed, InformationNeed):
        raise ValidationError(f"{field} must be an exact ResolutionOutput type")
    admitted = output
    if admitted.intent_request_identity != intent_request_identity:
        raise ValidationError(f"{field} belongs to a foreign IntentRequest lineage")
    if admitted.context_envelope_identity != context_envelope_identity:
        raise ValidationError(f"{field} belongs to a foreign ContextEnvelope lineage")
    return admitted


def _candidate_semantic_signature(candidate: CandidateResolution) -> tuple[object, ...]:
    """Provider attribution is provenance, not semantic precedence or voting weight."""

    return (
        candidate.proposed_semantics,
        candidate.assumptions,
        candidate.issues,
        candidate.clarification_proposals,
        candidate.information_need_proposals,
    )


def _candidates_are_semantically_equivalent(
    candidates: tuple[CandidateResolution, ...],
) -> bool:
    if not candidates:
        return True
    signature = _candidate_semantic_signature(candidates[0])
    return all(
        _candidate_semantic_signature(candidate) == signature
        for candidate in candidates[1:]
    )


def _unresolved_frontier_kind(
    candidates: tuple[CandidateResolution, ...],
) -> InitialResolutionFrontierKind:
    if not candidates:
        return InitialResolutionFrontierKind.RESOLUTION_INPUT_REQUIRED
    if _candidates_are_semantically_equivalent(candidates):
        return InitialResolutionFrontierKind.ADMISSION_REQUIRED
    return InitialResolutionFrontierKind.ADJUDICATION_REQUIRED


def _frontier_without_output(
    intent_request: IntentRequest,
    context_envelope: ContextEnvelope,
    candidates: tuple[CandidateResolution, ...],
) -> InitialResolutionFrontier:
    return InitialResolutionFrontier(
        intent_request_identity=intent_request.identity,
        context_envelope_identity=context_envelope.identity,
        kind=_unresolved_frontier_kind(candidates),
        candidate_inputs=candidates,
    )


def orchestrate_initial_resolution(
    intent_request: IntentRequest,
    context_envelope: ContextEnvelope,
    *,
    candidate_inputs: tuple[CandidateResolution, ...] = (),
    admitted_outputs: tuple[ResolutionOutput, ...] = (),
    admitter: InitialResolutionAdmitter | None = None,
    admission_attribution: ResolutionAttribution | None = None,
) -> InitialResolutionFrontier:
    """Derive and, when explicitly delegated, advance the M2.1 initial frontier.

    The orchestrator never treats CandidateResolution as admitted merely because it is
    unique, fluent, or provider-consensual. A new M1 ResolutionOutput may be produced
    only by an explicit IRR-owned ``admitter`` boundary. The returned output is then
    validated against exact request/context lineage, admission occurrence, and complete
    supplied candidate provenance.

    This function performs no provider invocation, retrieval, Governance, execution,
    retry, fallback, or hidden candidate ranking.
    """

    if type(intent_request) is not IntentRequest:
        raise ValidationError(
            "orchestrate_initial_resolution.intent_request must be an IntentRequest"
        )
    if type(context_envelope) is not ContextEnvelope:
        raise ValidationError(
            "orchestrate_initial_resolution.context_envelope must be a ContextEnvelope"
        )
    if context_envelope.intent_request_identity != intent_request.identity:
        raise ValidationError(
            "ContextEnvelope must belong to the exact supplied IntentRequest"
        )

    candidates = _normalize_candidates(
        candidate_inputs,
        field="orchestrate_initial_resolution.candidate_inputs",
    )
    for candidate in candidates:
        _validate_candidate_lineage(
            candidate,
            intent_request_identity=intent_request.identity,
            context_envelope_identity=context_envelope.identity,
            field="orchestrate_initial_resolution.candidate_inputs",
        )

    outputs = _normalize_outputs(
        admitted_outputs,
        field="orchestrate_initial_resolution.admitted_outputs",
    )
    for output in outputs:
        _validate_resolution_output_lineage(
            output,
            intent_request_identity=intent_request.identity,
            context_envelope_identity=context_envelope.identity,
            field="orchestrate_initial_resolution.admitted_outputs",
        )

    if len(outputs) > 1:
        raise ValidationError(
            "initial lifecycle graph must not contain competing admitted ResolutionOutput records"
        )

    if outputs:
        if admitter is not None or admission_attribution is not None:
            raise ValidationError(
                "existing admitted ResolutionOutput cannot be combined with a new admission transition"
            )
        output = outputs[0]
        admitted_candidate_identities = {
            candidate.identity for candidate in output.candidate_inputs
        }
        supplied_candidate_identities = {candidate.identity for candidate in candidates}
        if not supplied_candidate_identities.issubset(admitted_candidate_identities):
            raise ValidationError(
                "candidate material outside the admitted ResolutionOutput provenance is orphaned"
            )
        return InitialResolutionFrontier(
            intent_request_identity=intent_request.identity,
            context_envelope_identity=context_envelope.identity,
            kind=InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE,
            candidate_inputs=output.candidate_inputs,
            resolution_output=output,
        )

    if admitter is None:
        if admission_attribution is not None:
            raise ValidationError(
                "ResolutionAttribution cannot be supplied without an explicit initial-resolution admitter"
            )
        return _frontier_without_output(intent_request, context_envelope, candidates)

    if not callable(admitter):
        raise ValidationError(
            "orchestrate_initial_resolution.admitter must be callable"
        )
    if admission_attribution is None:
        raise ValidationError(
            "initial-resolution admitter requires explicit ResolutionAttribution"
        )
    if type(admission_attribution) is not ResolutionAttribution:
        raise ValidationError(
            "orchestrate_initial_resolution.admission_attribution must be a ResolutionAttribution"
        )

    proposed_output = admitter(
        intent_request,
        context_envelope,
        candidates,
        admission_attribution,
    )
    if proposed_output is None:
        return _frontier_without_output(intent_request, context_envelope, candidates)

    output = _validate_resolution_output_lineage(
        proposed_output,
        intent_request_identity=intent_request.identity,
        context_envelope_identity=context_envelope.identity,
        field="orchestrate_initial_resolution.admitter output",
    )
    if output.admission_attribution != admission_attribution:
        raise ValidationError(
            "admitter output must preserve the exact supplied ResolutionAttribution"
        )
    if output.candidate_inputs != candidates:
        raise ValidationError(
            "admitter output must preserve the complete exact supplied candidate provenance"
        )

    return InitialResolutionFrontier(
        intent_request_identity=intent_request.identity,
        context_envelope_identity=context_envelope.identity,
        kind=InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE,
        candidate_inputs=output.candidate_inputs,
        resolution_output=output,
    )
