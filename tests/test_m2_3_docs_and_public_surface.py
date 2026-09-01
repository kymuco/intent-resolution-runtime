from __future__ import annotations

from pathlib import Path

import intent_resolution_runtime as irr


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOC = ROOT / "docs" / "m2_3_capability_governance_orchestrator.md"


def test_m2_3_runtime_surface_is_public_without_becoming_canonical_ir() -> None:
    assert irr.CapabilityGovernanceFrontier is not None
    assert callable(irr.orchestrate_capability_governance)

    assert not hasattr(irr.CapabilityGovernanceFrontier, "canonical_bytes")
    assert not hasattr(irr.CapabilityGovernanceFrontier, "identity")


def test_readme_declares_m2_3_and_preserves_frozen_m2_2_history() -> None:
    text = README.read_text(encoding="utf-8")

    assert "**M1 — Intent Resolution IR is complete and frozen through M1.8.**" in text
    assert "**M2.0 — Runtime Orchestration Charter is complete and frozen in `main`.**" in text
    assert "**M2.1 — Initial Resolution Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.2 — Work / Binding Orchestrator is complete and frozen in `main`.**" in text
    assert "**M2.3 — Capability / Governance Orchestrator** is the current milestone." in text
    assert "[M2.2 Work / Binding Orchestrator](docs/m2_2_work_binding_orchestrator.md)" in text
    assert "[M2.3 Capability / Governance Orchestrator](docs/m2_3_capability_governance_orchestrator.md)" in text


def test_m2_3_doc_freezes_capability_governance_and_authorization_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")

    for invariant in (
        "frontier != canonical record",
        "secondary projection != source of truth",
        "CapabilityRequirement absence != missing capability",
        "capability disposition required != capability required",
        "pending evaluation != capability unavailable",
        "Capability Match != Availability",
        "multiple matches != hidden selection",
        "unique Capability Match != Governance requirement",
        "proposal disposition required != Governance required",
        "no GovernanceDecision != Denial",
        "unmentioned step != denied step",
        "unmentioned step != authorized step",
        "GovernanceDecision != Authorization history",
        "Authorization transition candidate != admitted Authorization history",
        "Authorization projection != fresh grant",
        "same component_ref across decisions != same Authorization",
        "Authorization != Attempt",
        "Authorization != Effect",
        "Authorization != Outcome",
    ):
        assert invariant in text
