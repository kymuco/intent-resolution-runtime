from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    ClaimRecord,
    ContextEnvelope,
    RecordIdentity,
    SourceAttribution,
    StableRef,
)


def _attribution() -> SourceAttribution:
    return SourceAttribution(
        source_ref=StableRef("host.source", "immutability-test"),
        source_event_ref=StableRef("host.event", "immutability-001"),
    )


def test_canonical_context_records_have_no_instance_dict_escape() -> None:
    claim = ClaimRecord(attribution=_attribution(), statement="immutable claim")
    envelope = ContextEnvelope(
        intent_request_identity=RecordIdentity("sha256", "0" * 64),
        boundary_attribution=_attribution(),
        records=(claim,),
    )

    for record in (claim, envelope):
        assert not hasattr(record, "__dict__")
        with pytest.raises(AttributeError):
            _ = record.__dict__  # type: ignore[attr-defined]
