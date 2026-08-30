from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from intent_resolution_runtime import (
    ClaimRecord,
    CompletenessRecord,
    ContextEnvelope,
    ContextReferenceRecord,
    EvidenceRecord,
    EvidenceRelation,
    EvidenceTargetKind,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    RecordIdentity,
    SerializationError,
    SourceAttribution,
    StableRef,
    TemporalBasisKind,
    TemporalBasisRecord,
    ValidationError,
)


def make_request() -> IntentRequest:
    return IntentRequest(
        origin=OriginAttribution(
            kind=OriginKind.HUMAN,
            actor_ref=StableRef("host.actor", "user"),
            source_event_ref=StableRef("host.event", "intent-001"),
        ),
        principal_ref=StableRef("host.principal", "user"),
        expression=IntentExpression("Send my latest report."),
    )


def host_attr(event: str) -> SourceAttribution:
    return SourceAttribution(
        source_ref=StableRef("host.source", "workspace-index"),
        source_event_ref=StableRef("host.event", event),
    )


def boundary_attr(event: str) -> SourceAttribution:
    return SourceAttribution(
        source_ref=StableRef("host.boundary", "context-admission"),
        source_event_ref=StableRef("host.context_boundary", event),
    )


def make_context() -> ContextEnvelope:
    request = make_request()
    temporal = TemporalBasisRecord(
        attribution=host_attr("time-001"),
        kind=TemporalBasisKind.RESOLUTION_TIME,
        value="2026-08-31T00:08:00+06:00",
        scope="interpret latest within the admitted report listing",
    )
    claim = ClaimRecord(
        attribution=host_attr("claim-001"),
        statement="report-042 is the newest admitted report by modification time",
    )
    completeness = CompletenessRecord(
        attribution=host_attr("listing-001"),
        bounded_domain="reports visible in workspace index /reports",
        purpose="select the newest admitted report",
        temporal_basis_refs=(temporal.identity,),
    )
    evidence_claim = EvidenceRecord(
        attribution=host_attr("evidence-001"),
        relation=EvidenceRelation.SUPPORTS,
        target_kind=EvidenceTargetKind.CLAIM,
        target_identity=claim.identity,
        scope="newest-by-modification-time within the admitted /reports listing",
        description="bounded workspace index entry ordering supports the report recency claim",
    )
    evidence_attr = EvidenceRecord(
        attribution=host_attr("evidence-002"),
        relation=EvidenceRelation.SUPPORTS,
        target_kind=EvidenceTargetKind.ATTRIBUTION,
        target_identity=claim.identity,
        scope="source attribution of claim-001 to workspace-index",
        description="host receipt links claim-001 to workspace-index",
    )
    reference = ContextReferenceRecord(
        attribution=host_attr("ref-001"),
        reference=StableRef("repo.path", "reports/report-042.md"),
        description="possible report content; content is not present in this context envelope",
    )
    return ContextEnvelope(
        intent_request_identity=request.identity,
        boundary_attribution=boundary_attr("ctx-001"),
        records=(
            reference,
            evidence_attr,
            completeness,
            claim,
            temporal,
            evidence_claim,
        ),
    )


def test_records_are_immutable() -> None:
    claim = ClaimRecord(attribution=host_attr("claim"), statement="x is current")
    with pytest.raises(FrozenInstanceError):
        claim.statement = "changed"  # type: ignore[misc]


def test_context_envelope_is_explicit_and_occurrence_attributable() -> None:
    first = make_context()
    second = ContextEnvelope(
        intent_request_identity=first.intent_request_identity,
        boundary_attribution=boundary_attr("ctx-002"),
        records=first.records,
    )
    assert first.identity != second.identity


def test_boundary_source_is_identity_material_not_inferred_from_event_namespace() -> None:
    first = make_context()
    second = ContextEnvelope(
        intent_request_identity=first.intent_request_identity,
        boundary_attribution=SourceAttribution(
            source_ref=StableRef("host.boundary", "alternate-admission"),
            source_event_ref=first.boundary_attribution.source_event_ref,
        ),
        records=first.records,
    )
    assert first.identity != second.identity


def test_record_order_is_not_implicit_precedence() -> None:
    first = make_context()
    second = ContextEnvelope(
        intent_request_identity=first.intent_request_identity,
        boundary_attribution=first.boundary_attribution,
        records=tuple(reversed(first.records)),
    )
    assert second.records == first.records
    assert second.canonical_bytes() == first.canonical_bytes()
    assert second.identity == first.identity


def test_claim_evidence_and_attribution_evidence_remain_distinct() -> None:
    envelope = make_context()
    claim = next(record for record in envelope.records if isinstance(record, ClaimRecord))
    evidence = [
        record for record in envelope.records if isinstance(record, EvidenceRecord)
        and record.target_identity == claim.identity
    ]
    assert {record.target_kind for record in evidence} == {
        EvidenceTargetKind.CLAIM,
        EvidenceTargetKind.ATTRIBUTION,
    }
    assert evidence[0].identity != evidence[1].identity


def test_origin_attribution_can_be_targeted_without_becoming_authority() -> None:
    request = make_request()
    evidence = EvidenceRecord(
        attribution=host_attr("origin-proof"),
        relation=EvidenceRelation.SUPPORTS,
        target_kind=EvidenceTargetKind.ORIGIN_ATTRIBUTION,
        target_identity=request.identity,
        scope="attribution of this IntentRequest occurrence to host.actor:user",
        description="host-authenticated session evidence supports the attributed request origin",
    )
    envelope = ContextEnvelope(
        intent_request_identity=request.identity,
        boundary_attribution=boundary_attr("ctx-origin"),
        records=(evidence,),
    )
    primitive = envelope.to_primitive()
    assert "authorized" not in str(primitive)
    assert "permission" not in str(primitive)


def test_evidence_target_must_be_inside_bounded_context() -> None:
    missing = RecordIdentity("sha256", "0" * 64)
    evidence = EvidenceRecord(
        attribution=host_attr("evidence"),
        relation=EvidenceRelation.SUPPORTS,
        target_kind=EvidenceTargetKind.CLAIM,
        target_identity=missing,
        scope="missing claim target",
        description="claimed support",
    )
    with pytest.raises(ValidationError, match="target must be present"):
        ContextEnvelope(
            intent_request_identity=make_request().identity,
            boundary_attribution=boundary_attr("ctx"),
            records=(evidence,),
        )


def test_completeness_requires_explicit_temporal_link_when_one_is_named() -> None:
    missing = RecordIdentity("sha256", "1" * 64)
    completeness = CompletenessRecord(
        attribution=host_attr("listing"),
        bounded_domain="D:/Backups listing",
        purpose="absence check",
        temporal_basis_refs=(missing,),
    )
    with pytest.raises(ValidationError, match="temporal basis must resolve"):
        ContextEnvelope(
            intent_request_identity=make_request().identity,
            boundary_attribution=boundary_attr("ctx"),
            records=(completeness,),
        )


def test_absence_does_not_create_completeness_or_temporal_basis() -> None:
    envelope = ContextEnvelope(
        intent_request_identity=make_request().identity,
        boundary_attribution=boundary_attr("empty"),
        records=(),
    )
    assert envelope.records == ()
    assert "completeness" not in envelope.canonical_bytes().decode()
    assert "temporal_basis" not in envelope.canonical_bytes().decode()


def test_context_reference_has_no_retrieval_or_disclosure_authority_fields() -> None:
    reference = ContextReferenceRecord(
        attribution=host_attr("ref"),
        reference=StableRef("repo.path", "private/report.md"),
        description="reference only",
    )
    text = reference.canonical_bytes().decode("utf-8")
    assert "retrieval" not in text
    assert "disclosure" not in text
    tampered = text[:-1] + ',"retrieval_authorized":"yes"}'
    with pytest.raises(SerializationError, match="invalid fields"):
        ContextReferenceRecord.from_json_bytes(tampered.encode())


def test_provider_disclosure_smuggling_is_rejected() -> None:
    envelope = make_context()
    text = envelope.canonical_bytes().decode("utf-8")
    tampered = text[:-1] + ',"provider_disclosure_allowed":"yes"}'
    with pytest.raises(SerializationError, match="invalid fields"):
        ContextEnvelope.from_json_bytes(tampered.encode())


def test_boundary_attribution_preserves_host_source_and_event() -> None:
    envelope = make_context()
    assert envelope.boundary_attribution.source_ref == StableRef(
        "host.boundary", "context-admission"
    )
    assert envelope.boundary_attribution.source_event_ref == StableRef(
        "host.context_boundary", "ctx-001"
    )


def test_evidence_scope_is_mandatory_and_identity_material() -> None:
    claim = ClaimRecord(attribution=host_attr("scope-claim"), statement="A and B")
    broad = EvidenceRecord(
        attribution=host_attr("scope-evidence"),
        relation=EvidenceRelation.SUPPORTS,
        target_kind=EvidenceTargetKind.CLAIM,
        target_identity=claim.identity,
        scope="A only",
        description="evidence only covers proposition A",
    )
    other = EvidenceRecord(
        attribution=broad.attribution,
        relation=broad.relation,
        target_kind=broad.target_kind,
        target_identity=broad.target_identity,
        scope="A and B",
        description=broad.description,
    )
    assert broad.identity != other.identity
    text = broad.canonical_bytes().decode("utf-8")
    assert '"scope":"A only"' in text


def test_round_trip_and_cross_links_are_preserved() -> None:
    envelope = make_context()
    decoded = ContextEnvelope.from_json_bytes(envelope.canonical_bytes())
    assert decoded == envelope
    assert decoded.canonical_bytes() == envelope.canonical_bytes()
    assert decoded.identity == envelope.identity


def test_m12_context_golden_digest_is_frozen() -> None:
    assert make_context().identity.digest == (
        "de7e426fec93946c94f90d769e0517fb70e7ba3684a1153a350aef977340fcf0"
    )


def test_array_extension_preserves_m11_golden_identity() -> None:
    request = IntentRequest(
        origin=OriginAttribution(
            kind=OriginKind.COMPANION,
            actor_ref=StableRef("character_os.actor", "kaguya"),
            source_event_ref=StableRef("hde.event", "evt-001"),
        ),
        principal_ref=StableRef("hde.principal", "user:self"),
        expression=IntentExpression("Стоит проверить последние логи."),
    )
    assert request.identity.digest == (
        "bedad2f962490352db8d156a3e39cbd40c2cbc6071a0bfc64899607fdd2967e8"
    )


def test_unknown_nested_attribution_field_is_rejected() -> None:
    claim = ClaimRecord(attribution=host_attr("claim"), statement="x")
    text = claim.canonical_bytes().decode()
    tampered = text.replace(
        '"attribution":{"source_event_ref"',
        '"attribution":{"verified":"yes","source_event_ref"',
        1,
    )
    with pytest.raises(SerializationError, match="invalid fields"):
        ClaimRecord.from_json_bytes(tampered.encode())


def test_evidence_scope_is_required_on_wire() -> None:
    claim = ClaimRecord(attribution=host_attr("scope-wire-claim"), statement="A and B")
    evidence = EvidenceRecord(
        attribution=host_attr("scope-wire-evidence"),
        relation=EvidenceRelation.SUPPORTS,
        target_kind=EvidenceTargetKind.CLAIM,
        target_identity=claim.identity,
        scope="A only",
        description="supports A",
    )
    text = evidence.canonical_bytes().decode("utf-8")
    text = text.replace('"scope":"A only",', "", 1)
    with pytest.raises(SerializationError, match="missing=.*scope"):
        EvidenceRecord.from_json_bytes(text.encode("utf-8"))


def test_invalid_enum_values_are_rejected() -> None:
    claim = ClaimRecord(attribution=host_attr("claim"), statement="x")
    evidence = EvidenceRecord(
        attribution=host_attr("evidence"),
        relation=EvidenceRelation.SUPPORTS,
        target_kind=EvidenceTargetKind.CLAIM,
        target_identity=claim.identity,
        scope="example claim support",
        description="support",
    )
    text = evidence.canonical_bytes().decode().replace('"supports"', '"proves"', 1)
    with pytest.raises(SerializationError, match="unsupported EvidenceRecord"):
        EvidenceRecord.from_json_bytes(text.encode())


def test_temporal_basis_is_explicit_and_attributable() -> None:
    basis = TemporalBasisRecord(
        attribution=host_attr("time"),
        kind=TemporalBasisKind.SEQUENCE,
        value="workspace-index-generation-42",
        scope="latest report selection",
    )
    primitive = basis.to_primitive()
    assert primitive["kind"] == "sequence"
    assert primitive["value"] == "workspace-index-generation-42"
    assert primitive["attribution"]["source_ref"]["value"] == "workspace-index"


def test_context_records_require_immutable_tuple_and_unique_identities() -> None:
    claim = ClaimRecord(attribution=host_attr("claim-dup"), statement="same")
    with pytest.raises(ValidationError, match="must be a tuple"):
        ContextEnvelope(  # type: ignore[arg-type]
            intent_request_identity=make_request().identity,
            boundary_attribution=boundary_attr("ctx-list"),
            records=[claim],
        )
    with pytest.raises(ValidationError, match="duplicate record identities"):
        ContextEnvelope(
            intent_request_identity=make_request().identity,
            boundary_attribution=boundary_attr("ctx-dup"),
            records=(claim, claim),
        )


def test_claim_evidence_cannot_target_non_claim_record() -> None:
    temporal = TemporalBasisRecord(
        attribution=host_attr("time-target"),
        kind=TemporalBasisKind.NAMED,
        value="release-window",
        scope="example",
    )
    evidence = EvidenceRecord(
        attribution=host_attr("evidence-target"),
        relation=EvidenceRelation.SUPPORTS,
        target_kind=EvidenceTargetKind.CLAIM,
        target_identity=temporal.identity,
        scope="wrong target class",
        description="wrong target class",
    )
    with pytest.raises(ValidationError, match="claim evidence must target"):
        ContextEnvelope(
            intent_request_identity=make_request().identity,
            boundary_attribution=boundary_attr("ctx-target"),
            records=(temporal, evidence),
        )


def test_origin_attribution_evidence_cannot_target_another_request() -> None:
    evidence = EvidenceRecord(
        attribution=host_attr("origin-wrong"),
        relation=EvidenceRelation.SUPPORTS,
        target_kind=EvidenceTargetKind.ORIGIN_ATTRIBUTION,
        target_identity=RecordIdentity("sha256", "2" * 64),
        scope="wrong request origin attribution",
        description="wrong request target",
    )
    with pytest.raises(ValidationError, match="must target this envelope"):
        ContextEnvelope(
            intent_request_identity=make_request().identity,
            boundary_attribution=boundary_attr("ctx-origin-wrong"),
            records=(evidence,),
        )
