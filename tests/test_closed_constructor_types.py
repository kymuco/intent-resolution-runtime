from __future__ import annotations

from dataclasses import dataclass

import pytest

from intent_resolution_runtime import (
    ClaimRecord,
    ContextEnvelope,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    RecordIdentity,
    SourceAttribution,
    StableRef,
    ValidationError,
)


class TextSubclass(str):
    pass


@dataclass(frozen=True, slots=True)
class StableRefSubclass(StableRef):
    hidden: str = "hidden"


@dataclass(frozen=True, slots=True)
class SourceAttributionSubclass(SourceAttribution):
    hidden: str = "hidden"


@dataclass(frozen=True, slots=True)
class ClaimSubclass(ClaimRecord):
    hidden: str = "hidden"


@dataclass(frozen=True, slots=True)
class RecordIdentitySubclass(RecordIdentity):
    hidden: str = "hidden"


def attr() -> SourceAttribution:
    return SourceAttribution(
        source_ref=StableRef("host.source", "index"),
        source_event_ref=StableRef("host.event", "event-1"),
    )


def test_scalar_subclasses_are_not_admitted_as_wire_values() -> None:
    with pytest.raises(ValidationError, match="must be a string"):
        StableRef(TextSubclass("host.source"), "index")


def test_m11_nested_record_subclasses_are_rejected() -> None:
    evil_ref = StableRefSubclass("host.actor", "user", "hidden")
    with pytest.raises(ValidationError, match="actor_ref must be a StableRef"):
        OriginAttribution(OriginKind.HUMAN, evil_ref, StableRef("host.event", "intent"))

    origin = OriginAttribution(
        OriginKind.HUMAN,
        StableRef("host.actor", "user"),
        StableRef("host.event", "intent"),
    )

    @dataclass(frozen=True, slots=True)
    class ExpressionSubclass(IntentExpression):
        hidden: str = "hidden"

    with pytest.raises(ValidationError, match="expression must be an IntentExpression"):
        IntentRequest(
            origin=origin,
            principal_ref=StableRef("host.principal", "user"),
            expression=ExpressionSubclass("do x", "hidden"),
        )


def test_context_nested_attribution_subclass_is_rejected() -> None:
    evil_attr = SourceAttributionSubclass(
        StableRef("host.source", "index"),
        StableRef("host.event", "claim"),
        "hidden",
    )
    with pytest.raises(ValidationError, match="attribution must be a SourceAttribution"):
        ClaimRecord(attribution=evil_attr, statement="x")


def test_context_record_subclass_cannot_hide_state_outside_identity() -> None:
    evil_claim = ClaimSubclass(attribution=attr(), statement="x", hidden="secret")
    with pytest.raises(ValidationError, match="unsupported record type"):
        ContextEnvelope(
            intent_request_identity=RecordIdentity("sha256", "0" * 64),
            boundary_attribution=attr(),
            records=(evil_claim,),
        )


def test_record_identity_subclass_is_rejected_at_context_boundary() -> None:
    evil_identity = RecordIdentitySubclass("sha256", "0" * 64, "hidden")
    with pytest.raises(ValidationError, match="intent_request_identity must be a RecordIdentity"):
        ContextEnvelope(
            intent_request_identity=evil_identity,
            boundary_attribution=attr(),
            records=(),
        )
