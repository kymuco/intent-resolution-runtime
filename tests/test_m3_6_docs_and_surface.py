from __future__ import annotations

from pathlib import Path

import intent_resolution_runtime as irr

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "m3_6_end_to_end_embeddable_host_fixture.md"
README = ROOT / "README.md"


def test_m3_6_adds_no_central_host_runtime_surface() -> None:
    for name in (
        "HostRuntime",
        "HostSession",
        "orchestrate_host",
        "orchestrate_end_to_end",
    ):
        assert not hasattr(irr, name)


def test_m3_6_doc_freezes_restart_replay_and_authority_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")

    for invariant in (
        "fixture composition != production HostRuntime",
        "semantic replay != adapter recall",
        "restart != retry permission",
        "provider proposal != IRR admission",
        "GovernanceDecision(AUTHORIZE) != admitted Authorization",
        "Attempt persisted != effect success",
        "WorkerResult returned != parent completion",
        "semantic replay != external re-execution",
        "M1 = canonical semantic records",
        "M2 = replayable semantic orchestration",
        "M3 = narrow embeddable Host integration mechanisms around those records/orchestrators",
    ):
        assert invariant in text


def test_readme_closes_m3_without_inventing_next_milestone() -> None:
    text = README.read_text(encoding="utf-8")

    assert "**M3 — Host Integration is complete and frozen through M3.6.**" in text
    assert "M3.6 — End-to-End Embeddable Host Fixture" in text
    assert "M3.0 — Host Integration Charter** is the next milestone" not in text
    assert (
        "the next milestone should be selected from concrete embedding-product evidence"
        in text
    )
