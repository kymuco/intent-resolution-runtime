from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeAlias, runtime_checkable

from .context import (
    ClaimRecord,
    CompletenessRecord,
    ContextEnvelope,
    ContextReferenceRecord,
    EvidenceRecord,
    EvidenceTargetKind,
    TemporalBasisRecord,
)
from .errors import IntentIRError, ValidationError
from .identity import RecordIdentity
from .intent import IntentExpression, IntentRequest, StableRef
from .resolution import CandidateResolution

ProviderContextRecord: TypeAlias = (
    ClaimRecord
    | EvidenceRecord
    | TemporalBasisRecord
    | CompletenessRecord
    | ContextReferenceRecord
)

_ALLOWED_CONTEXT_TYPES = (
    ClaimRecord,
    EvidenceRecord,
    TemporalBasisRecord,
    CompletenessRecord,
    ContextReferenceRecord,
)


class CognitiveProviderIntegrationError(IntentIRError):
    """Raised when a provider violates the frozen M3.2 integration contract."""


def _normalize_context_records(
    value: object,
) -> tuple[ProviderContextRecord, ...]:
    if type(value) is not tuple:
        raise ValidationError("CognitiveProviderRequest.context_records must be a tuple")
    if not all(type(item) in _ALLOWED_CONTEXT_TYPES for item in value):
        raise ValidationError(
            "CognitiveProviderRequest.context_records contains an unsupported record type"
        )
    records = tuple(value)
    identities = [record.identity for record in records]
    if len(set(identities)) != len(identities):
        raise ValidationError(
            "CognitiveProviderRequest.context_records must not contain duplicate identities"
        )
    return tuple(sorted(records, key=lambda record: str(record.identity)))  # type: ignore[return-value]


def _validate_projection_links(
    records: tuple[ProviderContextRecord, ...],
    *,
    intent_request_identity: RecordIdentity,
) -> None:
    disclosed = {record.identity: record for record in records}
    for record in records:
        if type(record) is EvidenceRecord:
            if record.target_kind is EvidenceTargetKind.ORIGIN_ATTRIBUTION:
                if record.target_identity != intent_request_identity:
                    raise ValidationError(
                        "provider projection origin-attribution evidence must target the exact IntentRequest"
                    )
                continue
            if record.target_identity not in disclosed:
                raise ValidationError(
                    "provider projection must disclose the target of every disclosed EvidenceRecord"
                )
        elif type(record) is CompletenessRecord:
            for temporal_ref in record.temporal_basis_refs:
                if type(disclosed.get(temporal_ref)) is not TemporalBasisRecord:
                    raise ValidationError(
                        "provider projection must disclose every TemporalBasisRecord referenced by a disclosed CompletenessRecord"
                    )


@dataclass(frozen=True, slots=True)
class CognitiveProviderRequest:
    """Explicit Host-permitted projection for one Cognitive Provider invocation.

    This is integration mechanism state, not canonical semantic history or permission.
    The provider receives only the intent expression and the explicitly disclosed Context
    records, never the complete Host state, principal mapping, repository, or acquisition
    surface through this contract.
    """

    provider_ref: StableRef
    invocation_ref: StableRef
    intent_request_identity: RecordIdentity
    context_envelope_identity: RecordIdentity
    intent_expression: IntentExpression
    context_records: tuple[ProviderContextRecord, ...] = ()

    def __post_init__(self) -> None:
        if type(self.provider_ref) is not StableRef:
            raise ValidationError("CognitiveProviderRequest.provider_ref must be a StableRef")
        if type(self.invocation_ref) is not StableRef:
            raise ValidationError(
                "CognitiveProviderRequest.invocation_ref must be a StableRef"
            )
        if type(self.intent_request_identity) is not RecordIdentity:
            raise ValidationError(
                "CognitiveProviderRequest.intent_request_identity must be a RecordIdentity"
            )
        if type(self.context_envelope_identity) is not RecordIdentity:
            raise ValidationError(
                "CognitiveProviderRequest.context_envelope_identity must be a RecordIdentity"
            )
        if type(self.intent_expression) is not IntentExpression:
            raise ValidationError(
                "CognitiveProviderRequest.intent_expression must be an IntentExpression"
            )
        records = _normalize_context_records(self.context_records)
        _validate_projection_links(
            records,
            intent_request_identity=self.intent_request_identity,
        )
        object.__setattr__(self, "context_records", records)


@runtime_checkable
class CognitiveProviderPort(Protocol):
    """Narrow proposal-only provider integration surface.

    Implementations may transport the explicit request to a local or remote provider, but
    must not treat provider output as admitted Resolution, Context, Governance, or
    Authorization. Retrieval/acquisition is intentionally absent from this protocol.
    """

    def propose(self, request: CognitiveProviderRequest) -> CandidateResolution: ...


def _validate_request_source(
    request: CognitiveProviderRequest,
    *,
    intent_request: IntentRequest,
    context_envelope: ContextEnvelope,
) -> None:
    if type(intent_request) is not IntentRequest:
        raise ValidationError("intent_request must be an IntentRequest")
    if type(context_envelope) is not ContextEnvelope:
        raise ValidationError("context_envelope must be a ContextEnvelope")
    if context_envelope.intent_request_identity != intent_request.identity:
        raise ValidationError(
            "context_envelope must belong to the exact IntentRequest being projected"
        )
    if request.intent_request_identity != intent_request.identity:
        raise ValidationError(
            "provider request must preserve the exact source IntentRequest identity"
        )
    if request.context_envelope_identity != context_envelope.identity:
        raise ValidationError(
            "provider request must preserve the exact source ContextEnvelope identity"
        )
    if request.intent_expression != intent_request.expression:
        raise ValidationError(
            "provider request must preserve the exact source IntentExpression"
        )

    available = {record.identity: record for record in context_envelope.records}
    for record in request.context_records:
        source = available.get(record.identity)
        if source is None or source != record:
            raise ValidationError(
                "provider request context_records must come from the exact source ContextEnvelope"
            )


def build_cognitive_provider_request(
    *,
    provider_ref: StableRef,
    invocation_ref: StableRef,
    intent_request: IntentRequest,
    context_envelope: ContextEnvelope,
    disclosed_context_identities: tuple[RecordIdentity, ...] = (),
) -> CognitiveProviderRequest:
    """Build one explicit provider projection from already-admitted Host inputs.

    Construction does not grant permission. The Host remains responsible for deciding
    that this exact projection may be disclosed to this provider before calling here.
    """

    if type(provider_ref) is not StableRef:
        raise ValidationError("provider_ref must be a StableRef")
    if type(invocation_ref) is not StableRef:
        raise ValidationError("invocation_ref must be a StableRef")
    if type(intent_request) is not IntentRequest:
        raise ValidationError("intent_request must be an IntentRequest")
    if type(context_envelope) is not ContextEnvelope:
        raise ValidationError("context_envelope must be a ContextEnvelope")
    if context_envelope.intent_request_identity != intent_request.identity:
        raise ValidationError(
            "context_envelope must belong to the exact IntentRequest being projected"
        )
    if type(disclosed_context_identities) is not tuple or not all(
        type(identity) is RecordIdentity for identity in disclosed_context_identities
    ):
        raise ValidationError(
            "disclosed_context_identities must be a tuple of RecordIdentity values"
        )
    if len(set(disclosed_context_identities)) != len(disclosed_context_identities):
        raise ValidationError("disclosed_context_identities must not contain duplicates")

    available = {record.identity: record for record in context_envelope.records}
    missing = [
        identity for identity in disclosed_context_identities if identity not in available
    ]
    if missing:
        raise ValidationError(
            "provider projection may include only records from the exact ContextEnvelope"
        )

    records = tuple(available[identity] for identity in disclosed_context_identities)
    return CognitiveProviderRequest(
        provider_ref=provider_ref,
        invocation_ref=invocation_ref,
        intent_request_identity=intent_request.identity,
        context_envelope_identity=context_envelope.identity,
        intent_expression=intent_request.expression,
        context_records=records,
    )


def invoke_cognitive_provider(
    provider: CognitiveProviderPort,
    request: CognitiveProviderRequest,
    *,
    intent_request: IntentRequest,
    context_envelope: ContextEnvelope,
) -> CandidateResolution:
    """Invoke a provider and validate exact input/output lineage and attribution.

    Transport/provider exceptions are deliberately not converted into semantic IR records.
    A successful return is still only CandidateResolution proposal material for M2.1.
    """

    if not isinstance(provider, CognitiveProviderPort):
        raise ValidationError("provider must satisfy CognitiveProviderPort")
    if type(request) is not CognitiveProviderRequest:
        raise ValidationError("request must be a CognitiveProviderRequest")
    _validate_request_source(
        request,
        intent_request=intent_request,
        context_envelope=context_envelope,
    )

    candidate = provider.propose(request)
    if type(candidate) is not CandidateResolution:
        raise CognitiveProviderIntegrationError(
            "provider must return an exact CandidateResolution"
        )
    if candidate.intent_request_identity != request.intent_request_identity:
        raise CognitiveProviderIntegrationError(
            "provider CandidateResolution belongs to a foreign IntentRequest"
        )
    if candidate.context_envelope_identity != request.context_envelope_identity:
        raise CognitiveProviderIntegrationError(
            "provider CandidateResolution belongs to a foreign ContextEnvelope"
        )
    if candidate.attribution.provider_ref != request.provider_ref:
        raise CognitiveProviderIntegrationError(
            "provider CandidateResolution attribution has the wrong provider_ref"
        )
    if candidate.attribution.invocation_ref != request.invocation_ref:
        raise CognitiveProviderIntegrationError(
            "provider CandidateResolution attribution has the wrong invocation_ref"
        )
    return candidate


__all__ = (
    "CognitiveProviderIntegrationError",
    "CognitiveProviderPort",
    "CognitiveProviderRequest",
    "ProviderContextRecord",
    "build_cognitive_provider_request",
    "invoke_cognitive_provider",
)
