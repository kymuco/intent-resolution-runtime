from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    ClaimRecord,
    CompletenessRecord,
    ContextEnvelope,
    ContextReferenceRecord,
    EvidenceRecord,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    RecordIdentity,
    SourceAttribution,
    StableRef,
    TemporalBasisRecord,
)
from intent_resolution_runtime.intent import IntentRequest as DirectIntentRequest


_CLOSED_IR_TYPES = (
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
)


@pytest.mark.parametrize("base_type", _CLOSED_IR_TYPES)
def test_public_m1_ir_record_types_cannot_be_subclassed(base_type: type) -> None:
    with pytest.raises(TypeError, match=rf"{base_type.__name__} is a closed IR type"):
        type(
            f"Hidden{base_type.__name__}",
            (base_type,),
            {"__slots__": ("hidden",)},
        )


def test_direct_submodule_import_sees_the_same_sealed_type() -> None:
    assert DirectIntentRequest is IntentRequest
    with pytest.raises(TypeError, match="IntentRequest is a closed IR type"):
        type("HiddenDirectIntentRequest", (DirectIntentRequest,), {})
