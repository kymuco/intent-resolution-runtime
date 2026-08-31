from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    ClaimRecord,
    ContextEnvelope,
    RecordIdentity,
    SourceAttribution,
    StableRef,
    ValidationError,
)


class TextSubclass(str):
    pass


class TupleSubclass(tuple):
    pass


def attr() -> SourceAttribution:
    return SourceAttribution(
        source_ref=StableRef("host.source", "index"),
        source_event_ref=StableRef("host.event", "event-1"),
    )


def test_scalar_subclasses_are_not_admitted_as_wire_values() -> None:
    with pytest.raises(ValidationError, match="must be a string"):
        StableRef(TextSubclass("host.source"), "index")

    with pytest.raises(ValidationError, match="only sha256"):
        RecordIdentity(TextSubclass("sha256"), "0" * 64)


def test_tuple_subclasses_are_not_admitted_as_record_collections() -> None:
    claim = ClaimRecord(attribution=attr(), statement="x")
    with pytest.raises(ValidationError, match="records must be a tuple"):
        ContextEnvelope(
            intent_request_identity=RecordIdentity("sha256", "0" * 64),
            boundary_attribution=attr(),
            records=TupleSubclass((claim,)),
        )
