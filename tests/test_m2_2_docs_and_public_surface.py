from __future__ import annotations

from pathlib import Path

import intent_resolution_runtime as irr


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOC = ROOT / "docs" / "m2_2_work_binding_orchestrator.md"


def test_m2_2_runtime_surface_is_public_without_becoming_canonical_ir() -> None:
    assert irr.WorkBindingFrontier is not None
    assert callable(irr.orchestrate_work_binding)

    assert not hasattr(irr.WorkBindingFrontier, "canonical_bytes")
    assert not hasattr(irr.WorkBindingFrontier, "identity")


def test_readme_preserves_completed_m2_2_history_as_m2_advances() -> None:
    text = README.read_text(encoding="utf-8")

    assert "**M1 — Intent Resolution IR is complete and frozen through M1.8.**" in text
    assert "**M2.0 — Runtime Orchestration Charter is complete and frozen in `main`.**" in text
    assert "**M2.1 — Initial Resolution Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.2 — Work / Binding Orchestrator is complete and frozen in `main`.**" in text
    assert "[M2.1 Initial Resolution Orchestrator](docs/m2_1_initial_resolution_orchestrator.md)" in text
    assert "[M2.2 Work / Binding Orchestrator](docs/m2_2_work_binding_orchestrator.md)" in text


def test_m2_2_doc_freezes_complete_frontier_and_binding_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")

    for invariant in (
        "complete work/binding frontier != one global status",
        "frontier != canonical record",
        "ResolvedIntent != WorkPlan requirement",
        "work_disposition_required != WorkPlan required",
        "work_disposition_required != no operational work",
        "plan-local symbolic output != external binding requirement",
        "competing BindingRules != hidden rule choice",
        "raw BindingInput pool != implicit rule association",
        "competing active BindingEvaluations != latest-wins",
        "BoundValue != WorkPlan mutation",
        "BindingIssue != generic Continuation",
        "external_binding_complete != executability",
        "external_binding_complete != Authorization",
    ):
        assert invariant in text
