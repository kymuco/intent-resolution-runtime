from __future__ import annotations

from dataclasses import FrozenInstanceError

import json
import pytest

from intent_resolution_runtime import (
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    SerializationError,
    StableRef,
    ValidationError,
)


def make_request(*, source_event: str = "evt-001", text: str = "Стоит проверить последние логи.") -> IntentRequest:
    return IntentRequest(
        origin=OriginAttribution(
            kind=OriginKind.COMPANION,
            actor_ref=StableRef(namespace="character_os.actor", value="kaguya"),
            source_event_ref=StableRef(namespace="hde.event", value=source_event),
        ),
        principal_ref=StableRef(namespace="hde.principal", value="user:self"),
        expression=IntentExpression(text=text),
    )


def test_companion_origin_and_user_principal_remain_distinct() -> None:
    request = make_request()

    assert request.origin.kind is OriginKind.COMPANION
    assert request.origin.actor_ref == StableRef("character_os.actor", "kaguya")
    assert request.principal_ref == StableRef("hde.principal", "user:self")
    assert request.origin.actor_ref != request.principal_ref


def test_records_are_deeply_immutable() -> None:
    request = make_request()

    with pytest.raises(FrozenInstanceError):
        request.expression = IntentExpression("different")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        request.origin.kind = OriginKind.HUMAN  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        request.principal_ref.value = "someone-else"  # type: ignore[misc]


def test_canonical_bytes_are_deterministic_and_round_trip() -> None:
    request = make_request()

    encoded = request.canonical_bytes()
    decoded = IntentRequest.from_json_bytes(encoded)

    assert decoded == request
    assert decoded.canonical_bytes() == encoded
    assert decoded.identity == request.identity
    assert str(request.identity).startswith("sha256:")
    assert len(request.identity.digest) == 64


def test_source_event_is_part_of_occurrence_identity() -> None:
    first = make_request(source_event="evt-001")
    second = make_request(source_event="evt-002")

    assert first.expression == second.expression
    assert first.origin.actor_ref == second.origin.actor_ref
    assert first.identity != second.identity


@pytest.mark.parametrize(
    "mutator",
    [
        lambda primitive: primitive["origin"].update({"kind": "human"}),
        lambda primitive: primitive["origin"]["actor_ref"].update({"value": "ren"}),
        lambda primitive: primitive["principal_ref"].update({"value": "user:other"}),
        lambda primitive: primitive["expression"].update({"text": "Другой запрос"}),
    ],
)
def test_material_input_changes_change_identity(mutator) -> None:
    request = make_request()
    primitive = request.to_primitive()
    mutator(primitive)

    changed = IntentRequest.from_json_bytes(
        json.dumps(primitive, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    assert changed.identity != request.identity


def test_text_is_preserved_exactly_without_silent_normalization() -> None:
    request = make_request(text="  Запусти backup — именно этот.  ")

    decoded = IntentRequest.from_json_bytes(request.canonical_bytes())

    assert decoded.expression.text == "  Запусти backup — именно этот.  "


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: StableRef("", "x"), "namespace"),
        (lambda: StableRef("x", " "), "value"),
        (lambda: IntentExpression("   "), "text"),
    ],
)
def test_blank_required_values_are_rejected(factory, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        factory()


def test_parser_rejects_authority_smuggling_via_unknown_top_level_field() -> None:
    encoded = make_request().canonical_bytes()
    text = encoded.decode("utf-8")[:-1] + ',"approved":true}'

    with pytest.raises(SerializationError, match="extra=.*approved"):
        IntentRequest.from_json_bytes(text.encode("utf-8"))


def test_parser_rejects_verification_smuggling_into_origin() -> None:
    encoded = make_request().canonical_bytes().decode("utf-8")
    text = encoded.replace(
        '"origin":{"actor_ref"',
        '"origin":{"verified":true,"actor_ref"',
        1,
    )

    with pytest.raises(SerializationError, match="origin has invalid fields"):
        IntentRequest.from_json_bytes(text.encode("utf-8"))


def test_parser_rejects_duplicate_json_keys() -> None:
    payload = (
        '{"schema":"irr.intent_request.v1","schema":"irr.intent_request.v1",'
        '"origin":{"kind":"human","actor_ref":{"namespace":"host.actor","value":"user"},'
        '"source_event_ref":{"namespace":"host.event","value":"evt"}},'
        '"principal_ref":{"namespace":"host.principal","value":"user"},'
        '"expression":{"text":"hello"}}'
    )

    with pytest.raises(SerializationError, match="duplicate JSON object key"):
        IntentRequest.from_json_bytes(payload.encode("utf-8"))


def test_parser_rejects_unknown_schema() -> None:
    encoded = make_request().canonical_bytes().decode("utf-8")
    encoded = encoded.replace("irr.intent_request.v1", "irr.intent_request.v2", 1)

    with pytest.raises(SerializationError, match="unsupported IntentRequest schema"):
        IntentRequest.from_json_bytes(encoded.encode("utf-8"))


def test_origin_attribution_is_not_identity_verification() -> None:
    primitive = make_request().to_primitive()

    assert set(primitive["origin"]) == {"kind", "actor_ref", "source_event_ref"}
    assert "verified" not in primitive["origin"]
    assert "approved" not in primitive
    assert "permission" not in primitive


def test_origin_kind_is_closed_for_v1() -> None:
    encoded = make_request().canonical_bytes().decode("utf-8")
    encoded = encoded.replace('"kind":"companion"', '"kind":"admin"', 1)

    with pytest.raises(SerializationError, match="unsupported origin.kind"):
        IntentRequest.from_json_bytes(encoded.encode("utf-8"))
