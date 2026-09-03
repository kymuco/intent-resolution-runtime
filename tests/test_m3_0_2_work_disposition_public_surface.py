from __future__ import annotations

import intent_resolution_runtime as irr


EXPECTED_PUBLIC_NAMES = (
    "AdmittedWorkPlan",
    "CandidateWorkDisposition",
    "NoOperationalWork",
    "WorkDispositionAdmissionAttribution",
    "WorkDispositionFrontier",
    "WorkDispositionFrontierKind",
    "WorkDispositionKind",
    "WorkDispositionOutput",
    "WorkDispositionProposalAttribution",
    "orchestrate_work_disposition",
)

CANONICAL_CLOSED_TYPES = (
    irr.AdmittedWorkPlan,
    irr.CandidateWorkDisposition,
    irr.NoOperationalWork,
    irr.WorkDispositionAdmissionAttribution,
    irr.WorkDispositionProposalAttribution,
)


def test_m3_0_2_public_surface_is_exported_from_package_root() -> None:
    for name in EXPECTED_PUBLIC_NAMES:
        assert name in irr.__all__
        assert hasattr(irr, name)


def test_new_canonical_work_disposition_records_are_closed_ir_types() -> None:
    for record_type in CANONICAL_CLOSED_TYPES:
        try:
            type(f"Illegal{record_type.__name__}Subclass", (record_type,), {})
        except TypeError as exc:
            assert "closed IR type" in str(exc)
        else:  # pragma: no cover - explicit regression failure branch
            raise AssertionError(f"{record_type.__name__} unexpectedly allowed subclassing")


def test_derived_work_disposition_frontier_is_not_sealed_as_canonical_ir() -> None:
    class DerivedFrontier(irr.WorkDispositionFrontier):
        pass

    assert issubclass(DerivedFrontier, irr.WorkDispositionFrontier)
