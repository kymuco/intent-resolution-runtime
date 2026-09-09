from __future__ import annotations

import inspect

import pytest

import intent_resolution_runtime as irr


PUBLIC_NAMES = (
    "AdmittedCapabilityMatchEvaluation",
    "CandidateCapabilityMatchEvaluation",
    "CapabilityMatchEvaluationAdmissionAttribution",
    "CapabilityMatchEvaluationAdmissionFrontier",
    "CapabilityMatchEvaluationAdmissionFrontierKind",
    "orchestrate_capability_match_evaluation_admission",
)


def test_public_surface_exports_exact_m3_0_5_contract() -> None:
    for name in PUBLIC_NAMES:
        assert hasattr(irr, name)
        assert name in irr.__all__

    parameters = inspect.signature(
        irr.orchestrate_capability_match_evaluation_admission
    ).parameters
    assert tuple(parameters) == (
        "requirement",
        "catalog_snapshot",
        "candidate_inputs",
        "admitted_outputs",
        "admitter",
        "admission_attribution",
    )


def test_public_surface_does_not_export_admitter_typing_alias() -> None:
    assert "CapabilityMatchEvaluationAdmitter" not in irr.__all__


def test_new_canonical_records_are_closed() -> None:
    with pytest.raises(TypeError):
        class _BadCandidate(irr.CandidateCapabilityMatchEvaluation):
            pass

    with pytest.raises(TypeError):
        class _BadAttribution(irr.CapabilityMatchEvaluationAdmissionAttribution):
            pass

    with pytest.raises(TypeError):
        class _BadAdmitted(irr.AdmittedCapabilityMatchEvaluation):
            pass


def test_admission_surface_has_no_selection_or_authorization_outputs() -> None:
    annotations = irr.AdmittedCapabilityMatchEvaluation.__annotations__
    assert set(annotations) == {
        "SCHEMA",
        "admission_attribution",
        "evaluation",
        "candidate_inputs",
    }
    for forbidden in (
        "selected_capability",
        "availability",
        "work_proposal",
        "governance",
        "authorization",
        "attempt",
        "executor",
        "retry",
        "fallback",
    ):
        assert forbidden not in annotations
