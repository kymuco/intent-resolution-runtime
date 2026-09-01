from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CHARTER = ROOT / "docs" / "m2_0_runtime_orchestration_charter.md"


def test_m2_0_charter_freezes_record_graph_not_mutable_session_as_canonical_state() -> None:
    text = CHARTER.read_text(encoding="utf-8")

    assert "immutable attributable M1 record graph" in text
    assert "canonical lifecycle state" in text
    assert "!= mutable ResolutionSession object" in text
    assert "one global status != complete lifecycle state" in text


def test_m2_0_charter_requires_global_lifecycle_graph_admission_not_record_bag_validity() -> None:
    text = CHARTER.read_text(encoding="utf-8")

    assert "valid individual records != automatically valid lifecycle graph" in text
    assert "competing active lineage != scheduler choice" in text
    assert "storage ordering != lifecycle ordering" in text
    assert "no foreign/orphan material" in text


def test_m2_0_charter_preserves_orchestration_authority_and_effect_boundaries() -> None:
    text = CHARTER.read_text(encoding="utf-8")

    for invariant in (
        "orchestration != authority",
        "orchestration != effect execution",
        "orchestration != Governance",
        "orchestration != ambient retrieval",
        "next legal transition != permission",
        "unknown external outcome != automatic retry",
        "WorkerNeed != delegation widening",
    ):
        assert invariant in text


def test_m2_0_charter_separates_replay_semantic_frontier_and_scheduler_selection() -> None:
    text = CHARTER.read_text(encoding="utf-8")

    assert "M2 is **replayable by design**" in text
    assert "complete semantic transition frontier" in text
    assert "scheduler selection != semantic frontier" in text
    assert "material semantic choice != scheduler discretion" in text
    assert "M2.1 — Initial Resolution Orchestrator" in text
    assert "M2.6 — End-to-end Host fixture" in text


def test_readme_declares_m2_0_without_unfreezing_m1() -> None:
    text = README.read_text(encoding="utf-8")

    assert "**M1 — Intent Resolution IR is complete and frozen through M1.8.**" in text
    assert "**M2.0 — Runtime Orchestration Charter**" in text
    assert "[M2.0 Runtime Orchestration Charter](docs/m2_0_runtime_orchestration_charter.md)" in text
    assert "No M2 semantic milestone is declared yet" not in text
