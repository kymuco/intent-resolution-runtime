"""Intent Resolution Runtime public M1 Intent IR surface."""

from .context import (
    ClaimRecord,
    CompletenessRecord,
    ContextEnvelope,
    ContextReferenceRecord,
    EvidenceRecord,
    EvidenceRelation,
    EvidenceTargetKind,
    SourceAttribution,
    TemporalBasisKind,
    TemporalBasisRecord,
)
from .errors import IntentIRError, SerializationError, ValidationError
from .identity import RecordIdentity
from .intent import IntentExpression, IntentRequest, OriginAttribution, OriginKind, StableRef


def _seal_ir_type(base_type: type) -> None:
    base_name = base_type.__name__

    def _reject_subclassing(cls: type, **kwargs: object) -> None:
        raise TypeError(f"{base_name} is a closed IR type and cannot be subclassed")

    base_type.__init_subclass__ = classmethod(_reject_subclassing)


for _ir_type in (
    StableRef,
    OriginAttribution,
    IntentExpression,
    IntentRequest,
    RecordIdentity,
    SourceAttribution,
    ClaimRecord,
    EvidenceRecord,
    TemporalBasisRecord,
    CompletenessRecord,
    ContextReferenceRecord,
    ContextEnvelope,
):
    _seal_ir_type(_ir_type)

del _ir_type, _seal_ir_type


__all__ = [
    "ClaimRecord",
    "CompletenessRecord",
    "ContextEnvelope",
    "ContextReferenceRecord",
    "EvidenceRecord",
    "EvidenceRelation",
    "EvidenceTargetKind",
    "IntentExpression",
    "IntentIRError",
    "IntentRequest",
    "OriginAttribution",
    "OriginKind",
    "RecordIdentity",
    "SerializationError",
    "SourceAttribution",
    "StableRef",
    "TemporalBasisKind",
    "TemporalBasisRecord",
    "ValidationError",
]
