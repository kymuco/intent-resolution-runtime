from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    StableRef,
    ValidationError,
)
from intent_resolution_runtime.capability_catalog_admission import (
    AdmittedCapabilityCatalogSnapshot,
    CandidateCapabilityCatalogSnapshot,
    CapabilityCatalogSnapshotAdmissionAttribution,
    CapabilityCatalogSnapshotAdmissionFrontierKind,
    CapabilityCatalogSnapshotProposalAttribution,
    orchestrate_capability_catalog_snapshot_admission,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _snapshot(label: str) -> CapabilityCatalogSnapshot:
    return CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", f"catalog:{label}"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=_ref("irr.capability_catalog_supplier", f"supplier:{label}"),
            snapshot_event_ref=_ref("irr.capability_catalog_snapshot", label),
        ),
        scope_statement=f"Bounded capability domain {label}.",
        descriptors=(),
        description=f"Exact empty capability catalog snapshot {label}.",
    )


def _candidate(
    snapshot: CapabilityCatalogSnapshot,
    *,
    label: str,
) -> CandidateCapabilityCatalogSnapshot:
    return CandidateCapabilityCatalogSnapshot(
        attribution=CapabilityCatalogSnapshotProposalAttribution(
            proposer_ref=_ref("irr.catalog_proposer", label),
            proposal_event_ref=_ref("irr.catalog_proposal", label),
        ),
        snapshot=snapshot,
        rationale=f"Use exact bounded capability domain {label}.",
    )


def _admission(label: str) -> CapabilityCatalogSnapshotAdmissionAttribution:
    return CapabilityCatalogSnapshotAdmissionAttribution(
        resolver_ref=_ref("irr.catalog_resolver", "test"),
        admission_event_ref=_ref("irr.catalog_admission", label),
    )


def _admitter(
    candidates: tuple[CandidateCapabilityCatalogSnapshot, ...],
    attribution: CapabilityCatalogSnapshotAdmissionAttribution,
) -> AdmittedCapabilityCatalogSnapshot:
    return AdmittedCapabilityCatalogSnapshot(
        admission_attribution=attribution,
        snapshot=candidates[0].snapshot,
        candidate_inputs=candidates,
    )


def test_no_candidate_material_requires_explicit_proposal_input() -> None:
    frontier = orchestrate_capability_catalog_snapshot_admission()

    assert (
        frontier.kind
        is CapabilityCatalogSnapshotAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
    )
    assert frontier.candidate_inputs == ()
    assert frontier.admitted_catalog is None


def test_empty_candidate_domain_cannot_be_synthesized_by_admitter() -> None:
    with pytest.raises(ValidationError, match="requires explicit candidate snapshot"):
        orchestrate_capability_catalog_snapshot_admission(
            admitter=_admitter,
            admission_attribution=_admission("empty"),
        )


def test_admitted_catalog_must_equal_one_exact_proposed_snapshot() -> None:
    candidate = _candidate(_snapshot("proposed"), label="proposed")

    with pytest.raises(ValidationError, match="one exact proposed snapshot"):
        AdmittedCapabilityCatalogSnapshot(
            admission_attribution=_admission("synthesized"),
            snapshot=_snapshot("synthesized"),
            candidate_inputs=(candidate,),
        )


def test_one_exact_catalog_requires_admission_not_automatic_activation() -> None:
    candidate = _candidate(_snapshot("one"), label="one")

    frontier = orchestrate_capability_catalog_snapshot_admission(
        candidate_inputs=(candidate,),
    )

    assert (
        frontier.kind
        is CapabilityCatalogSnapshotAdmissionFrontierKind.ADMISSION_REQUIRED
    )
    assert frontier.candidate_inputs == (candidate,)
    assert frontier.admitted_catalog is None


def test_proposal_provenance_does_not_turn_one_snapshot_into_adjudication() -> None:
    snapshot = _snapshot("same")
    first = _candidate(snapshot, label="first")
    second = _candidate(snapshot, label="second")

    frontier = orchestrate_capability_catalog_snapshot_admission(
        candidate_inputs=(second, first),
    )

    assert (
        frontier.kind
        is CapabilityCatalogSnapshotAdmissionFrontierKind.ADMISSION_REQUIRED
    )
    assert {item.snapshot.identity for item in frontier.candidate_inputs} == {
        snapshot.identity
    }


def test_distinct_catalog_domains_require_explicit_adjudication() -> None:
    first = _candidate(_snapshot("first"), label="first")
    second = _candidate(_snapshot("second"), label="second")

    frontier = orchestrate_capability_catalog_snapshot_admission(
        candidate_inputs=(first, second),
    )

    assert (
        frontier.kind
        is CapabilityCatalogSnapshotAdmissionFrontierKind.ADJUDICATION_REQUIRED
    )
    assert frontier.admitted_catalog is None


def test_explicit_admission_preserves_complete_candidate_provenance() -> None:
    first = _candidate(_snapshot("first"), label="first")
    second = _candidate(_snapshot("second"), label="second")
    attribution = _admission("choose-first")

    frontier = orchestrate_capability_catalog_snapshot_admission(
        candidate_inputs=(second, first),
        admitter=_admitter,
        admission_attribution=attribution,
    )

    assert (
        frontier.kind
        is CapabilityCatalogSnapshotAdmissionFrontierKind.CATALOG_OUTPUT_AVAILABLE
    )
    output = frontier.admitted_catalog
    assert output is not None
    assert output.admission_attribution == attribution
    assert output.snapshot == frontier.candidate_inputs[0].snapshot
    assert output.candidate_inputs == frontier.candidate_inputs
    for forbidden in (
        "capability_match",
        "selected_capability",
        "available",
        "work_proposal",
        "governance",
        "authorization",
        "attempt",
        "executor",
    ):
        assert not hasattr(output, forbidden)


def test_admitted_output_replay_preserves_exact_full_provenance() -> None:
    candidate = _candidate(_snapshot("replay"), label="replay")
    admitted = _admitter((candidate,), _admission("replay"))

    frontier = orchestrate_capability_catalog_snapshot_admission(
        admitted_outputs=(admitted,),
    )

    assert (
        frontier.kind
        is CapabilityCatalogSnapshotAdmissionFrontierKind.CATALOG_OUTPUT_AVAILABLE
    )
    assert frontier.candidate_inputs == (candidate,)
    assert frontier.admitted_catalog == admitted


def test_candidate_outside_admitted_provenance_is_rejected_on_replay() -> None:
    admitted_candidate = _candidate(_snapshot("admitted"), label="admitted")
    foreign_candidate = _candidate(_snapshot("foreign"), label="foreign")
    admitted = _admitter((admitted_candidate,), _admission("admitted"))

    with pytest.raises(ValidationError, match="outside admitted catalog provenance"):
        orchestrate_capability_catalog_snapshot_admission(
            candidate_inputs=(foreign_candidate,),
            admitted_outputs=(admitted,),
        )


def test_competing_admitted_catalogs_fail_closed() -> None:
    first = _candidate(_snapshot("first"), label="first")
    second = _candidate(_snapshot("second"), label="second")
    first_output = _admitter((first,), _admission("first"))
    second_output = _admitter((second,), _admission("second"))

    with pytest.raises(ValidationError, match="competing admitted"):
        orchestrate_capability_catalog_snapshot_admission(
            admitted_outputs=(first_output, second_output),
        )


def test_candidate_and_admitted_records_round_trip_canonically() -> None:
    candidate = _candidate(_snapshot("round-trip"), label="round-trip")
    admitted = _admitter((candidate,), _admission("round-trip"))

    restored_candidate = CandidateCapabilityCatalogSnapshot.from_json_bytes(
        candidate.canonical_bytes()
    )
    restored_admitted = AdmittedCapabilityCatalogSnapshot.from_json_bytes(
        admitted.canonical_bytes()
    )

    assert restored_candidate == candidate
    assert restored_candidate.identity == candidate.identity
    assert restored_admitted == admitted
    assert restored_admitted.identity == admitted.identity
