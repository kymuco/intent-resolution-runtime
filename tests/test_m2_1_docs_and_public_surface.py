from __future__ import annotations

from pathlib import Path

import intent_resolution_runtime as irr


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOC = ROOT / "docs" / "m2_1_initial_resolution_orchestrator.md"


def test_m2_1_runtime_surface_is_public_without_becoming_canonical_ir() -> None:
    assert irr.InitialResolutionFrontier is not None
    assert irr.InitialResolutionFrontierKind is not None
    assert callable(irr.orchestrate_initial_resolution)

    assert not hasattr(irr.InitialResolutionFrontier, "canonical_bytes")
    assert not hasattr(irr.InitialResolutionFrontier, "identity")


def test_readme_declares_m2_1_and_preserves_frozen_m1_m2_0_history() -> None:
    text = README.read_text(encoding="utf-8")

    assert "**M1 — Intent Resolution IR is complete and frozen through M1.8.**" in text
    assert "**M2.0 — Runtime Orchestration Charter is complete and frozen in `main`.**" in text
    assert "**M2.1 — Initial Resolution Orchestrator** is the current milestone." in text
    assert "[M2.0 Runtime Orchestration Charter](docs/m2_0_runtime_orchestration_charter.md)" in text
    assert "[M2.1 Initial Resolution Orchestrator](docs/m2_1_initial_resolution_orchestrator.md)" in text


def test_m2_1_doc_freezes_candidate_admission_and_noncanonical_frontier_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")

    for invariant in (
        "frontier != canonical record",
        "duplicate candidate delivery != extra semantic weight",
        "provider count != voting authority",
        "semantically distinct candidates -> ADJUDICATION_REQUIRED",
        "multiple blockers != guessed pause mapping",
        "competing pause modes != hidden choice",
        "ResolutionAttribution != Authorization",
    ):
        assert invariant in text
