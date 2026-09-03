from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "m3_0_2_work_disposition_admission_prerequisite.md"
)


def test_work_disposition_doc_matches_runtime_equivalence_contract() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "Candidate proposal attribution and `rationale` are excluded" in text
    assert "`kind` and the exact proposed `WorkPlan`" in text
    assert "same exact WorkPlan + different proposer attribution/rationale" in text
    assert "→ still ADMISSION_REQUIRED" in text

    assert "`rationale` all participate in the equivalence signature" not in text
    assert "same exact WorkPlan + different rationale\n→ ADJUDICATION_REQUIRED" not in text
