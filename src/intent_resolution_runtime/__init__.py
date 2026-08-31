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
from .resolution import (
    AssumptionKind,
    AssumptionRecord,
    CandidateAttribution,
    CandidateResolution,
    ClarificationNeed,
    ClarificationProposal,
    InformationNeed,
    InformationNeedProposal,
    ResolutionAttribution,
    ResolutionIssue,
    ResolutionIssueImpact,
    ResolutionIssueKind,
    ResolvedIntent,
)


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
    CandidateAttribution,
    ResolutionAttribution,
    AssumptionRecord,
    ResolutionIssue,
    ClarificationProposal,
    InformationNeedProposal,
    CandidateResolution,
    ResolvedIntent,
    ClarificationNeed,
    InformationNeed,
):
    _seal_ir_type(_ir_type)

del _ir_type, _seal_ir_type


__all__ = [
    "AssumptionKind",
    "AssumptionRecord",
    "CandidateAttribution",
    "CandidateResolution",
    "ClaimRecord",
    "ClarificationNeed",
    "ClarificationProposal",
    "CompletenessRecord",
    "ContextEnvelope",
    "ContextReferenceRecord",
    "EvidenceRecord",
    "EvidenceRelation",
    "EvidenceTargetKind",
    "InformationNeed",
    "InformationNeedProposal",
    "IntentExpression",
    "IntentIRError",
    "IntentRequest",
    "OriginAttribution",
    "OriginKind",
    "RecordIdentity",
    "ResolutionAttribution",
    "ResolutionIssue",
    "ResolutionIssueImpact",
    "ResolutionIssueKind",
    "ResolvedIntent",
    "SerializationError",
    "SourceAttribution",
    "StableRef",
    "TemporalBasisKind",
    "TemporalBasisRecord",
    "ValidationError",
]
