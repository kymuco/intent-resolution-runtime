from __future__ import annotations

import pytest

import intent_resolution_runtime as irr


def test_binding_rule_admission_types_are_public() -> None:
    expected = {
        "AdmittedBindingRule",
        "BindingRuleAdmissionAttribution",
        "BindingRuleAdmissionFrontier",
        "BindingRuleAdmissionFrontierKind",
        "BindingRuleProposalAttribution",
        "CandidateBindingRule",
        "orchestrate_binding_rule_admission",
    }
    assert expected.issubset(set(irr.__all__))
    for name in expected:
        assert getattr(irr, name) is not None


def test_new_canonical_binding_rule_records_are_closed_types() -> None:
    for base in (
        irr.BindingRuleProposalAttribution,
        irr.BindingRuleAdmissionAttribution,
        irr.CandidateBindingRule,
        irr.AdmittedBindingRule,
    ):
        with pytest.raises(TypeError, match="closed IR type"):
            type(f"Forged{base.__name__}", (base,), {})


def test_frontier_is_derived_not_canonical_record() -> None:
    assert "canonical_bytes" not in irr.BindingRuleAdmissionFrontier.__dict__
    assert "identity" not in irr.BindingRuleAdmissionFrontier.__dict__
