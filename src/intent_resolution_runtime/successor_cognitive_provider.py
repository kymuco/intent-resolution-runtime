from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast, runtime_checkable

from .cognitive_provider import (
    CognitiveProviderRequest,
    ProviderContextRecord,
    build_cognitive_provider_request,
)
from .context import ContextEnvelope
from .continuation import ContinuationInput
from .errors import IntentIRError, ValidationError
from .identity import RecordIdentity
from .intent import IntentExpression, IntentRequest, StableRef
from .resolution import (
    AssumptionRecord,
    CandidateResolution,
    ResolutionIssue,
    ResolvedIntent,
)
from .successor_semantic_resolution import SuccessorCandidateResolution


class SuccessorCognitiveProviderIntegrationError(IntentIRError):
    """Raised when a provider violates the M4.1 successor integration contract."""


def _normalize_continuation_inputs(
    value: object,
) -> tuple[ContinuationInput, ...]:
    if type(value) is not tuple:
        raise ValidationError(
            "SuccessorCognitiveProviderRequest.continuation_inputs must be a tuple"
        )
    if not value:
        raise ValidationError(
            "SuccessorCognitiveProviderRequest.continuation_inputs must not be empty"
        )
    if not all(type(item) is ContinuationInput for item in value):
        raise ValidationError(
            "SuccessorCognitiveProviderRequest.continuation_inputs must contain "
            "ContinuationInput values"
        )

    inputs = cast(tuple[ContinuationInput, ...], value)
    identities = [item.identity for item in inputs]
    if len(set(identities)) != len(identities):
        raise ValidationError(
            "SuccessorCognitiveProviderRequest.continuation_inputs must not contain "
            "duplicate identities"
        )

    source_identities = [item.source_identity for item in inputs]
    if len(set(source_identities)) != len(source_identities):
        raise ValidationError(
            "SuccessorCognitiveProviderRequest.continuation_inputs must not amplify "
            "one source through repeated re-entry occurrences"
        )

    return tuple(sorted(inputs, key=lambda item: str(item.source_identity)))


def _normalize_assumptions(
    value: object,
) -> tuple[AssumptionRecord, ...]:
    if type(value) is not tuple:
        raise ValidationError(
            "SuccessorCognitiveProviderRequest.predecessor_assumptions must be a tuple"
        )
    if not all(type(item) is AssumptionRecord for item in value):
        raise ValidationError(
            "SuccessorCognitiveProviderRequest.predecessor_assumptions must contain "
            "AssumptionRecord values"
        )
    return cast(tuple[AssumptionRecord, ...], value)


def _normalize_issues(
    value: object,
) -> tuple[ResolutionIssue, ...]:
    if type(value) is not tuple:
        raise ValidationError(
            "SuccessorCognitiveProviderRequest.predecessor_unresolved_issues "
            "must be a tuple"
        )
    if not all(type(item) is ResolutionIssue for item in value):
        raise ValidationError(
            "SuccessorCognitiveProviderRequest.predecessor_unresolved_issues must "
            "contain ResolutionIssue values"
        )
    return cast(tuple[ResolutionIssue, ...], value)


@dataclass(frozen=True, slots=True)
class SuccessorCognitiveProviderRequest:
    """Explicit Host-permitted provider projection for one successor invocation.

    This is integration mechanism state, not canonical semantic history or permission.
    Exact continuation inputs cross this boundary because M4.0 proposal provenance
    claims that the provider candidate is based on those exact re-entry inputs.
    """

    provider_ref: StableRef
    invocation_ref: StableRef
    intent_request_identity: RecordIdentity
    context_envelope_identity: RecordIdentity
    intent_expression: IntentExpression
    predecessor_identity: RecordIdentity
    predecessor_semantics: str
    predecessor_assumptions: tuple[AssumptionRecord, ...]
    predecessor_unresolved_issues: tuple[ResolutionIssue, ...]
    continuation_inputs: tuple[ContinuationInput, ...]
    context_records: tuple[ProviderContextRecord, ...] = ()

    def __post_init__(self) -> None:
        if type(self.provider_ref) is not StableRef:
            raise ValidationError(
                "SuccessorCognitiveProviderRequest.provider_ref must be a StableRef"
            )
        if type(self.invocation_ref) is not StableRef:
            raise ValidationError(
                "SuccessorCognitiveProviderRequest.invocation_ref must be a StableRef"
            )
        if type(self.intent_request_identity) is not RecordIdentity:
            raise ValidationError(
                "SuccessorCognitiveProviderRequest.intent_request_identity must be "
                "a RecordIdentity"
            )
        if type(self.context_envelope_identity) is not RecordIdentity:
            raise ValidationError(
                "SuccessorCognitiveProviderRequest.context_envelope_identity must be "
                "a RecordIdentity"
            )
        if type(self.intent_expression) is not IntentExpression:
            raise ValidationError(
                "SuccessorCognitiveProviderRequest.intent_expression must be an "
                "IntentExpression"
            )
        if type(self.predecessor_identity) is not RecordIdentity:
            raise ValidationError(
                "SuccessorCognitiveProviderRequest.predecessor_identity must be "
                "a RecordIdentity"
            )
        if (
            type(self.predecessor_semantics) is not str
            or not self.predecessor_semantics
            or self.predecessor_semantics != self.predecessor_semantics.strip()
        ):
            raise ValidationError(
                "SuccessorCognitiveProviderRequest.predecessor_semantics must be "
                "non-empty trimmed text"
            )

        object.__setattr__(
            self,
            "predecessor_assumptions",
            _normalize_assumptions(self.predecessor_assumptions),
        )
        object.__setattr__(
            self,
            "predecessor_unresolved_issues",
            _normalize_issues(self.predecessor_unresolved_issues),
        )
        object.__setattr__(
            self,
            "continuation_inputs",
            _normalize_continuation_inputs(self.continuation_inputs),
        )

        initial_projection = CognitiveProviderRequest(
            provider_ref=self.provider_ref,
            invocation_ref=self.invocation_ref,
            intent_request_identity=self.intent_request_identity,
            context_envelope_identity=self.context_envelope_identity,
            intent_expression=self.intent_expression,
            context_records=self.context_records,
        )
        object.__setattr__(
            self,
            "context_records",
            initial_projection.context_records,
        )


@runtime_checkable
class SuccessorCognitiveProviderPort(Protocol):
    """Proposal-only provider mechanism for explicit successor semantic input."""

    def propose_successor(
        self,
        request: SuccessorCognitiveProviderRequest,
    ) -> CandidateResolution: ...


def _validate_source_material(
    request: SuccessorCognitiveProviderRequest,
    *,
    intent_request: IntentRequest,
    predecessor: ResolvedIntent,
    context_envelope: ContextEnvelope,
    continuation_inputs: tuple[ContinuationInput, ...],
) -> None:
    if type(intent_request) is not IntentRequest:
        raise ValidationError("intent_request must be an IntentRequest")
    if type(predecessor) is not ResolvedIntent:
        raise ValidationError("predecessor must be a ResolvedIntent")
    if type(context_envelope) is not ContextEnvelope:
        raise ValidationError("context_envelope must be a ContextEnvelope")

    if predecessor.intent_request_identity != intent_request.identity:
        raise ValidationError(
            "predecessor must belong to the exact IntentRequest being projected"
        )
    if context_envelope.intent_request_identity != intent_request.identity:
        raise ValidationError(
            "context_envelope must belong to the exact IntentRequest being projected"
        )

    inputs = _normalize_continuation_inputs(continuation_inputs)
    if any(item.resolved_intent_identity != predecessor.identity for item in inputs):
        raise ValidationError(
            "successor continuation inputs must descend from the exact predecessor"
        )

    if request.intent_request_identity != intent_request.identity:
        raise ValidationError(
            "successor provider request must preserve the exact IntentRequest identity"
        )
    if request.context_envelope_identity != context_envelope.identity:
        raise ValidationError(
            "successor provider request must preserve the exact ContextEnvelope identity"
        )
    if request.intent_expression != intent_request.expression:
        raise ValidationError(
            "successor provider request must preserve the exact IntentExpression"
        )
    if request.predecessor_identity != predecessor.identity:
        raise ValidationError(
            "successor provider request must preserve the exact predecessor identity"
        )
    if request.predecessor_semantics != predecessor.semantics:
        raise ValidationError(
            "successor provider request must preserve exact predecessor semantics"
        )
    if request.predecessor_assumptions != predecessor.assumptions:
        raise ValidationError(
            "successor provider request must preserve exact predecessor assumptions"
        )
    if request.predecessor_unresolved_issues != predecessor.unresolved_issues:
        raise ValidationError(
            "successor provider request must preserve exact predecessor unresolved issues"
        )
    if request.continuation_inputs != inputs:
        raise ValidationError(
            "successor provider request must preserve exact continuation inputs"
        )

    expected_projection = build_cognitive_provider_request(
        provider_ref=request.provider_ref,
        invocation_ref=request.invocation_ref,
        intent_request=intent_request,
        context_envelope=context_envelope,
        disclosed_context_identities=tuple(
            record.identity for record in request.context_records
        ),
    )
    if expected_projection.context_records != request.context_records:
        raise ValidationError(
            "successor provider request context_records must come from the exact "
            "ContextEnvelope"
        )


def build_successor_cognitive_provider_request(
    *,
    provider_ref: StableRef,
    invocation_ref: StableRef,
    intent_request: IntentRequest,
    predecessor: ResolvedIntent,
    context_envelope: ContextEnvelope,
    continuation_inputs: tuple[ContinuationInput, ...],
    disclosed_context_identities: tuple[RecordIdentity, ...] = (),
) -> SuccessorCognitiveProviderRequest:
    """Build one explicit successor provider projection from admitted source material."""

    if type(predecessor) is not ResolvedIntent:
        raise ValidationError("predecessor must be a ResolvedIntent")
    if predecessor.intent_request_identity != intent_request.identity:
        raise ValidationError(
            "predecessor must belong to the exact IntentRequest being projected"
        )

    inputs = _normalize_continuation_inputs(continuation_inputs)
    if any(item.resolved_intent_identity != predecessor.identity for item in inputs):
        raise ValidationError(
            "successor continuation inputs must descend from the exact predecessor"
        )

    initial_projection = build_cognitive_provider_request(
        provider_ref=provider_ref,
        invocation_ref=invocation_ref,
        intent_request=intent_request,
        context_envelope=context_envelope,
        disclosed_context_identities=disclosed_context_identities,
    )

    return SuccessorCognitiveProviderRequest(
        provider_ref=initial_projection.provider_ref,
        invocation_ref=initial_projection.invocation_ref,
        intent_request_identity=initial_projection.intent_request_identity,
        context_envelope_identity=initial_projection.context_envelope_identity,
        intent_expression=initial_projection.intent_expression,
        predecessor_identity=predecessor.identity,
        predecessor_semantics=predecessor.semantics,
        predecessor_assumptions=predecessor.assumptions,
        predecessor_unresolved_issues=predecessor.unresolved_issues,
        continuation_inputs=inputs,
        context_records=initial_projection.context_records,
    )


def invoke_successor_cognitive_provider(
    provider: SuccessorCognitiveProviderPort,
    request: SuccessorCognitiveProviderRequest,
    *,
    intent_request: IntentRequest,
    predecessor: ResolvedIntent,
    context_envelope: ContextEnvelope,
    continuation_inputs: tuple[ContinuationInput, ...],
) -> SuccessorCandidateResolution:
    """Invoke a successor provider and bind exact proposal provenance mechanically."""

    if not isinstance(provider, SuccessorCognitiveProviderPort):
        raise ValidationError(
            "provider must satisfy SuccessorCognitiveProviderPort"
        )
    if type(request) is not SuccessorCognitiveProviderRequest:
        raise ValidationError(
            "request must be a SuccessorCognitiveProviderRequest"
        )

    _validate_source_material(
        request,
        intent_request=intent_request,
        predecessor=predecessor,
        context_envelope=context_envelope,
        continuation_inputs=continuation_inputs,
    )

    candidate = provider.propose_successor(request)
    if type(candidate) is not CandidateResolution:
        raise SuccessorCognitiveProviderIntegrationError(
            "successor provider must return an exact CandidateResolution"
        )
    if candidate.intent_request_identity != request.intent_request_identity:
        raise SuccessorCognitiveProviderIntegrationError(
            "successor provider CandidateResolution belongs to a foreign IntentRequest"
        )
    if candidate.context_envelope_identity != request.context_envelope_identity:
        raise SuccessorCognitiveProviderIntegrationError(
            "successor provider CandidateResolution belongs to a foreign ContextEnvelope"
        )
    if candidate.attribution.provider_ref != request.provider_ref:
        raise SuccessorCognitiveProviderIntegrationError(
            "successor provider CandidateResolution attribution has the wrong provider_ref"
        )
    if candidate.attribution.invocation_ref != request.invocation_ref:
        raise SuccessorCognitiveProviderIntegrationError(
            "successor provider CandidateResolution attribution has the wrong "
            "invocation_ref"
        )

    return SuccessorCandidateResolution(
        predecessor=predecessor,
        continuation_inputs=request.continuation_inputs,
        candidate=candidate,
    )


__all__ = (
    "SuccessorCognitiveProviderIntegrationError",
    "SuccessorCognitiveProviderPort",
    "SuccessorCognitiveProviderRequest",
    "build_successor_cognitive_provider_request",
    "invoke_successor_cognitive_provider",
)
