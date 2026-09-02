from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHARTER = ROOT / "docs" / "m3_0_host_integration_charter.md"


def charter_text() -> str:
    return CHARTER.read_text(encoding="utf-8")


def test_m3_0_keeps_host_mechanism_and_host_state_non_authoritative() -> None:
    text = charter_text()

    for invariant in (
        "Host integration != semantic authority",
        "Host integration != Governance authority",
        "Host integration != evidence truth",
        "HostState != canonical semantic lifecycle history",
        "no public HostRuntime frozen",
    ):
        assert invariant in text


def test_m3_0_uses_existing_typed_irr_input_boundary_without_blob_escape() -> None:
    text = charter_text()

    assert "IntentRequest\n+ ContextEnvelope" in text
    assert "Host possesses data != admitted IRR Context" in text
    assert "ContextEnvelope remains typed semantic Context, not a text/blob transport" in text
    assert "ContextReferenceRecord.description != hidden content transport" in text
    assert "raw Host text != ClaimRecord by default" in text
    assert "Context Reference != content" in text


def test_m3_0_preserves_external_component_boundaries() -> None:
    text = charter_text()

    for invariant in (
        "provider proposal != IRR admission",
        "GovernanceDecision != Effect",
        "Authorization != invocation",
        "Executor != resolver",
        "WorkerResult != parent completion",
        "HostAcquisitionPort installed != retrieval authority",
    ):
        assert invariant in text


def test_m3_0_separates_persistence_replay_and_external_reexecution() -> None:
    text = charter_text()

    assert "record persistence != semantic mutation" in text
    assert "storage insertion order != lifecycle order" in text
    assert "semantic replay = re-derive frontiers from admitted records" in text
    assert "external re-execution = perform an effect again" in text
    assert "restart != automatic retry" in text
    assert "competing active lineage != latest-write-wins" in text


def test_m3_0_remains_product_neutral_and_selects_only_m3_1() -> None:
    text = charter_text()

    assert "IRR core != HDE integration" in text
    assert "HDE is one Host integration rather than a privileged IRR mode" in text
    assert "M3.1 — Admitted History Repository / Replay Boundary" in text
    assert "Exact repository class/protocol names are not frozen by M3.0" in text
    assert "A product-owned input adapter may be implemented after M3.0" in text
