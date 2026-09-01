from __future__ import annotations

from pathlib import Path


SCENARIO_FILES: dict[str, tuple[str, ...]] = {
    "A": (
        "test_m1_8_scenario_a_restore_backup.py",
        "test_m1_8_scenario_a_partial_extract_lifecycle.py",
    ),
    "B": (
        "test_m1_8_scenario_b_telegram_planning.py",
        "test_m1_8_scenario_b_telegram_unknown_outcome.py",
    ),
    "C": (
        "test_m1_8_scenario_c_codexia_delegation.py",
        "test_m1_8_scenario_c_codexia_escalation.py",
    ),
    "D": ("test_m1_8_scenario_d_ambiguous_referent.py",),
    "E": ("test_m1_8_scenario_e_companion_initiative.py",),
    "F": ("test_m1_8_scenario_f_missing_signal_capability.py",),
    "G": ("test_m1_8_scenario_g_no_operational_intent.py",),
    "H": ("test_m1_8_scenario_h_returned_search_material_choice.py",),
}


def test_m1_8_covers_all_eight_canonical_m0_10_scenarios() -> None:
    assert tuple(SCENARIO_FILES) == tuple("ABCDEFGH")

    tests_dir = Path(__file__).parent
    missing = [
        filename
        for filenames in SCENARIO_FILES.values()
        for filename in filenames
        if not (tests_dir / filename).is_file()
    ]
    assert missing == []


def test_scenario_splits_are_explicit_and_bounded() -> None:
    assert len(SCENARIO_FILES["A"]) == 2
    assert len(SCENARIO_FILES["B"]) == 2
    assert len(SCENARIO_FILES["C"]) == 2
    for scenario in "DEFGH":
        assert len(SCENARIO_FILES[scenario]) == 1


def test_m1_8_fixture_inventory_contains_no_generic_scenario_runtime_layer() -> None:
    filenames = {
        filename for scenario_files in SCENARIO_FILES.values() for filename in scenario_files
    }
    assert all(filename.startswith("test_m1_8_scenario_") for filename in filenames)
    assert "scenario_runtime.py" not in filenames
    assert "scenario_dto.py" not in filenames
