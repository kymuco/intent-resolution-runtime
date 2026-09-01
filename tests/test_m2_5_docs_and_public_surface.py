from __future__ import annotations

from pathlib import Path

import intent_resolution_runtime as irr


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOC = ROOT / "docs" / "m2_5_worker_lifecycle_orchestrator.md"


def test_m2_5_runtime_surface_is_public_without_becoming_canonical_ir() -> None:
    assert irr.WorkerLifecycleFrontier is not None
    assert callable(irr.orchestrate_worker_lifecycle)

    assert not hasattr(irr.WorkerLifecycleFrontier, "canonical_bytes")
    assert not hasattr(irr.WorkerLifecycleFrontier, "identity")


def test_readme_preserves_m2_5_as_frozen_history() -> None:
    text = README.read_text(encoding="utf-8")

    assert "**M1 — Intent Resolution IR is complete and frozen through M1.8.**" in text
    assert "**M2.0 — Runtime Orchestration Charter is complete and frozen in `main`.**" in text
    assert "**M2.1 — Initial Resolution Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.2 — Work / Binding Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.3 — Capability / Governance Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.4 — Attempt / Outcome / Continuation Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.5 — Worker Lifecycle Orchestrator is complete and frozen in `main`.**" in text
    assert "[M2.4 Attempt / Outcome / Continuation Orchestrator](docs/m2_4_attempt_outcome_continuation_orchestrator.md)" in text
    assert "[M2.5 Worker Lifecycle Orchestrator](docs/m2_5_worker_lifecycle_orchestrator.md)" in text


def test_m2_5_doc_freezes_worker_history_and_completion_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")

    for invariant in (
        "frontier != canonical record",
        "frontier != Worker scheduler",
        "frontier != completion policy",
        "DelegatedWork != DelegatedWorkHandoff",
        "DelegatedWorkHandoff != Worker acceptance",
        "handoff disposition required != Worker dispatch required",
        "multiple handoffs != latest Worker wins",
        "handoff without WorkerResult != Worker failure",
        "WorkerResult != Worker lifecycle success",
        "multiple WorkerResult records != latest result wins",
        "multiple WorkerResult records != final result selection",
        "WorkerNeed != scope expansion",
        "WorkerNeed != capability grant",
        "WorkerNeed != Authorization",
        "completion claim != delegated completion proof",
        "deliverable material != parent completion",
        "WorkerResult history != automatic Continuation",
        "WorkerResult availability != continuation-source selection",
    ):
        assert invariant in text
