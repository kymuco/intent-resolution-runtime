from __future__ import annotations

from pathlib import Path

import intent_resolution_runtime as irr


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOC = ROOT / "docs" / "m2_4_attempt_outcome_continuation_orchestrator.md"


def test_m2_4_runtime_surface_is_public_without_becoming_canonical_ir() -> None:
    assert irr.AttemptOutcomeContinuationFrontier is not None
    assert callable(irr.orchestrate_attempt_outcome_continuation)

    assert not hasattr(irr.AttemptOutcomeContinuationFrontier, "canonical_bytes")
    assert not hasattr(irr.AttemptOutcomeContinuationFrontier, "identity")


def test_readme_preserves_completed_m2_4_history_as_m2_advances() -> None:
    text = README.read_text(encoding="utf-8")

    assert "**M1 — Intent Resolution IR is complete and frozen through M1.8.**" in text
    assert "**M2.0 — Runtime Orchestration Charter is complete and frozen in `main`.**" in text
    assert "**M2.1 — Initial Resolution Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.2 — Work / Binding Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.3 — Capability / Governance Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.4 — Attempt / Outcome / Continuation Orchestrator is complete and frozen in `main`.**" in text
    assert "[M2.3 Capability / Governance Orchestrator](docs/m2_3_capability_governance_orchestrator.md)" in text
    assert "[M2.4 Attempt / Outcome / Continuation Orchestrator](docs/m2_4_attempt_outcome_continuation_orchestrator.md)" in text


def test_m2_4_doc_freezes_history_reentry_and_recovery_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")

    for invariant in (
        "frontier != canonical record",
        "frontier != recovery policy",
        "Attempt != Outcome",
        "Attempt without Outcome != failed",
        "Retry != mutation of an Attempt",
        "multiple Attempts for one WorkStep != one mutable Attempt",
        "Outcome lifecycle != Outcome completion",
        "Outcome completion != effect certainty",
        "material unknown != failed",
        "material unknown != retry permission",
        "competing Outcomes != latest wins",
        "Outcome history != selected Continuation source",
        "Outcome != automatic ContinuationInput",
        "reentry pending != reentry required",
        "same exact source re-entered twice != two independent semantic sources",
        "reentry ambiguity != first/latest precedence",
        "SuccessorResolutionLineage != retry",
        "SuccessorResolutionLineage != fallback",
        "competing successor lineages != hidden branch selection",
        "unconsumed ContinuationInput != automatic successor",
        "old Authorization != successor Authorization",
    ):
        assert invariant in text
