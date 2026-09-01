from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .context import ContextEnvelope
from .errors import ValidationError
from .identity import RecordIdentity
from .intent import IntentRequest
from .resolution import (
    CandidateResolution,
    ClarificationNeed,
    InformationNeed,
    ResolutionAttribution,
    ResolutionIssueImpact,
    ResolvedIntent,
)


ResolutionOutput: TypeAlias = ResolvedIntent | ClarificationNeed | InformationNeed


class InitialResolutionFrontierKind(str, Enum):
    """Narrow M2.1 frontier classification; not a global lifecycle state."""

    CANDIDATE_INPUT_REQUIRED = "candidate_input_required"
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

        if self.kind is InitialResolutionFrontierKind.CANDIDATE_INPUT_REQUIRED:
            if candidates or self.resolution_output is not None:
                raise ValidationError(
                    "candidate_input_required frontier cannot contain candidate or resolution output"
                )
        elif self.kind is InitialResolutionFrontierKind.ADJUDICATION_REQUIRED:
            if not candidates:
                raise ValidationError(
                    "adjudication_required frontier requires candidate material"
                )
            if self.resolution_output is not None:
                raise ValidationError(
                    "adjudication_required frontier cannot contain an admitted resolution output"
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
    output: ResolutionOutput,
    *,
    intent_request_identity: RecordIdentity,
    context_envelope_identity: RecordIdentity,
    field: str,
) -> None:
    if type(output) not in (ResolvedIntent, ClarificationNeed, InformationNeed):
        raise ValidationError(f"{field} must be an exact ResolutionOutput type")
    if output.intent_request_identity != intent_request_identity:
        raise ValidationError(f"{field} belongs to a foreign IntentRequest lineage")
    if output.context_envelope_identity != context_envelope_identity:
        raise ValidationError(f"{field} belongs to a foreign ContextEnvelope lineage")


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


def _derive_resolution_output(
    candidates: tuple[CandidateResolution, ...],
    *,
    admission_attribution: ResolutionAttribution,
) -> ResolutionOutput | None:
    candidate = candidates[0]
    blocking_issues = tuple(
        issue
        for issue in candidate.issues
        if issue.impact is ResolutionIssueImpact.BLOCKING
    )

    if not blocking_issues:
        return ResolvedIntent(
            intent_request_identity=candidate.intent_request_identity,
            context_envelope_identity=candidate.context_envelope_identity,
            admission_attribution=admission_attribution,
            semantics=candidate.proposed_semantics,
            assumptions=candidate.assumptions,
            unresolved_issues=candidate.issues,
            candidate_inputs=candidates,
        )

    if len(blocking_issues) != 1:
        return None

    if (
        len(candidate.clarification_proposals) == 1
        and not candidate.information_need_proposals
    ):
        proposal = candidate.clarification_proposals[0]
        return ClarificationNeed(
            intent_request_identity=candidate.intent_request_identity,
            context_envelope_identity=candidate.context_envelope_identity,
            admission_attribution=admission_attribution,
            question=proposal.question,
            scope=proposal.scope,
            blocking_issues=blocking_issues,
            candidate_inputs=candidates,
        )

    if (
        len(candidate.information_need_proposals) == 1
        and not candidate.clarification_proposals
    ):
        proposal = candidate.information_need_proposals[0]
        return InformationNeed(
            intent_request_identity=candidate.intent_request_identity,
            context_envelope_identity=candidate.context_envelope_identity,
            admission_attribution=admission_attribution,
            description=proposal.description,
            scope=proposal.scope,
            reason=proposal.reason,
            blocking_issues=blocking_issues,
            candidate_inputs=candidates,
        )

    return None


def orchestrate_initial_resolution(
    intent_request: IntentRequest,
    context_envelope: ContextEnvelope,
    *,
    candidate_inputs: tuple[CandidateResolution, ...] = (),
    admitted_outputs: tuple[ResolutionOutput, ...] = (),
    admission_attribution: ResolutionAttribution | None = None,
) -> InitialResolutionFrontier:
    """Derive the M2.1 initial-resolution frontier from explicit admitted material.

    This function performs no provider invocation, retrieval, Governance, execution,
    retry, fallback, or hidden candidate ranking. It may admit a new M1 ResolutionOutput
    only when the supplied candidate semantics make that transition deterministic under
    the deliberately narrow M2.1 admission rules.
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

    if not candidates:
        return InitialResolutionFrontier(
            intent_request_identity=intent_request.identity,
            context_envelope_identity=context_envelope.identity,
            kind=InitialResolutionFrontierKind.CANDIDATE_INPUT_REQUIRED,
        )

    if not _candidates_are_semantically_equivalent(candidates):
        return InitialResolutionFrontier(
            intent_request_identity=intent_request.identity,
            context_envelope_identity=context_envelope.identity,
            kind=InitialResolutionFrontierKind.ADJUDICATION_REQUIRED,
            candidate_inputs=candidates,
        )

    if admission_attribution is None:
        raise ValidationError(
            "deterministic initial resolution admission requires explicit ResolutionAttribution"
        )
    if type(admission_attribution) is not ResolutionAttribution:
        raise ValidationError(
            "orchestrate_initial_resolution.admission_attribution must be a ResolutionAttribution"
        )

    output = _derive_resolution_output(
        candidates,
        admission_attribution=admission_attribution,
    )
    if output is None:
        return InitialResolutionFrontier(
            intent_request_identity=intent_request.identity,
            context_envelope_identity=context_envelope.identity,
            kind=InitialResolutionFrontierKind.ADJUDICATION_REQUIRED,
            candidate_inputs=candidates,
        )

    return InitialResolutionFrontier(
        intent_request_identity=intent_request.identity,
        context_envelope_identity=context_envelope.identity,
        kind=InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE,
        candidate_inputs=output.candidate_inputs,
        resolution_output=output,
    )
