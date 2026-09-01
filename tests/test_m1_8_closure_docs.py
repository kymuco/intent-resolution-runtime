from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CLOSURE = ROOT / "docs" / "m1_8_closure.md"


def test_readme_declares_completed_m1_and_removes_stale_next_m1_6_status() -> None:
    text = README.read_text(encoding="utf-8")

    assert "**M1 — Intent Resolution IR is complete and frozen through M1.8.**" in text
    assert "The next implementation slice is **M1.6" not in text
    assert "No M2 semantic milestone is declared yet" in text


def test_readme_normative_index_reaches_m1_8_closure() -> None:
    text = README.read_text(encoding="utf-8")

    assert "[M1.6 Capability / Governance / Authorization IR closure](docs/m1_6_closure.md)" in text
    assert "[M1.7 Attempt / Outcome / Continuation IR closure](docs/m1_7_closure.md)" in text
    assert "[M1.8 Executable M0.10 fixtures & M1 closure](docs/m1_8_closure.md)" in text


def test_m1_8_closure_record_freezes_eight_scenarios_without_declaring_m2() -> None:
    text = CLOSURE.read_text(encoding="utf-8")

    for scenario in "ABCDEFGH":
        assert f"Scenario {scenario}" in text
    assert "M1 — Intent Resolution IR is complete and frozen" in text
    assert "No M2 semantic milestone is declared here" in text
