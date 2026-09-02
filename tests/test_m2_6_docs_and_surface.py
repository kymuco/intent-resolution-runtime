from __future__ import annotations

from pathlib import Path

import intent_resolution_runtime as irr


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOC = ROOT / "docs" / "m2_6_end_to_end_host_fixture.md"


def test_m2_6_adds_no_premature_public_host_runtime() -> None:
    assert not hasattr(irr, "HostRuntime")
    assert not hasattr(irr, "HostSession")
    assert not hasattr(irr, "orchestrate_host")
    assert not hasattr(irr, "orchestrate_end_to_end")


def test_readme_declares_m2_6_and_preserves_frozen_m2_5_history() -> None:
    text = README.read_text(encoding="utf-8")

    assert "**M1 — Intent Resolution IR is complete and frozen through M1.8.**" in text
    assert "**M2.0 — Runtime Orchestration Charter is complete and frozen in `main`.**" in text
    assert "**M2.1 — Initial Resolution Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.2 — Work / Binding Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.3 — Capability / Governance Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.4 — Attempt / Outcome / Continuation Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.5 — Worker Lifecycle Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.6 — End-to-End Host Fixture is complete and frozen in `main`.**" in text
    assert "**M3.0 — Host Integration Charter** is the next milestone." in text
    assert "[M2.5 Worker Lifecycle Orchestrator](docs/m2_5_worker_lifecycle_orchestrator.md)" in text
    assert "[M2.6 End-to-End Host Fixture](docs/m2_6_end_to_end_host_fixture.md)" in text


def test_m2_6_doc_freezes_composition_without_new_authority() -> None:
    text = DOC.read_text(encoding="utf-8")

    for invariant in (
        "fixture composition != new orchestration authority",
        "Host sequencing != canonical lifecycle state",
        "M2 frontier != canonical record",
        "partial extract != restore success",
        "partial extract != launch readiness",
        "provider proposes != IRR admits",
        "one provider candidate != admission",
        "binding does not imply completeness",
        "missing completeness provenance != safe latest selection",
        "unknown future value != unknown decision rule",
        "Binding tie != hidden selection",
        "Capability Match != Authorization",
        "GovernanceDecision != admitted Authorization history",
        "Authorization transition candidate != admitted Authorization history",
        "not_satisfied != no effect",
        "partial effect != retry permission",
        "Outcome history != selected Continuation source",
        "Outcome != automatic ContinuationInput",
        "ContinuationInput != retry",
        "successor ResolvedIntent != successor WorkPlan",
        "ordinary capability path != implicit Worker path",
        "Host composition != new semantic authority",
    ):
        assert invariant in text
