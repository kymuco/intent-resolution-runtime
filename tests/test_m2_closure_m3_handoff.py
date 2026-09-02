from __future__ import annotations

from pathlib import Path

import intent_resolution_runtime as irr


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOC = ROOT / "docs" / "m2_closure_m3_handoff.md"


def test_m2_closure_adds_no_premature_m3_public_runtime_surface() -> None:
    for name in (
        "HostRuntime",
        "HostSession",
        "HistoryRepository",
        "CognitiveProviderPort",
        "GovernancePort",
        "ExecutorPort",
        "WorkerPort",
        "orchestrate_host",
        "orchestrate_end_to_end",
    ):
        assert not hasattr(irr, name)


def test_readme_closes_m2_and_selects_m3_0_charter() -> None:
    text = README.read_text(encoding="utf-8")

    assert "**M1 — Intent Resolution IR is complete and frozen through M1.8.**" in text
    assert "**M2 — Runtime Orchestration is complete and frozen through M2.6.**" in text
    assert "**M2.6 — End-to-End Host Fixture is complete and frozen in `main`.**" in text
    assert "**M3.0 — Host Integration Charter** is the next milestone." in text
    assert "[M2 closure & M3 handoff](docs/m2_closure_m3_handoff.md)" in text
    assert (
        "Normative M0 contracts, the M1 IR, and M2 Runtime Orchestration are frozen in `main`; "
        "M3 begins with a charter-first Host integration boundary"
    ) in text


def test_m2_closure_doc_freezes_source_of_truth_and_m3_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")

    for invariant in (
        "M1 = canonical semantic records",
        "M2 = replayable orchestration over those records",
        "M3 = Host integration boundary around those records and orchestrators",
        "M2 frontier != canonical record",
        "Host sequencing != canonical lifecycle state",
        "implemented orchestration != one super-orchestrator",
        "provider proposes != IRR admits",
        "ResolvedIntent != WorkPlan",
        "binding does not imply completeness",
        "Capability Match != Authorization",
        "GovernanceDecision(AUTHORIZE) != admitted Authorization history",
        "Attempt != Outcome",
        "Outcome != automatic ContinuationInput",
        "WorkerResult != parent completion",
        "ordinary capability path != implicit Worker path",
        "Host mechanism != semantic authority",
        "Host mechanism != Governance authority",
        "HostState != canonical semantic lifecycle history",
        "adapter installed != Capability admitted",
        "mechanically runnable != semantically self-selecting",
        "M3.0 — Host Integration Charter",
        "restart != retry permission",
        "integrate the runtime",
        "without turning integration machinery into semantic authority",
    ):
        assert invariant in text


def test_m3_follow_on_sequence_is_explicitly_non_normative() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "## 29. Proposed M3 sequence — planning only" in text
    assert "This sequence is **not yet normative** beyond selecting M3.0 as the next milestone." in text
    for proposed in (
        "M3.1  Admitted History Repository / Replay Boundary",
        "M3.2  Cognitive Provider Integration Port",
        "M3.3  Governance Integration Port",
        "M3.4  Executor / Capability Invocation Port",
        "M3.5  Worker Integration Port",
        "M3.6  End-to-End Embeddable Host Fixture",
    ):
        assert proposed in text
