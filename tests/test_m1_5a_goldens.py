from __future__ import annotations

from intent_resolution_runtime import (
    RecordIdentity,
    StableRef,
    SymbolicReference,
    WorkContinuationMode,
    WorkLiteralInput,
    WorkOutput,
    WorkPlan,
    WorkStep,
    WorkSymbolicInput,
)


RESOLVED = RecordIdentity("sha256", "1" * 64)
PLAN_REF = StableRef("irr.work_plan", "backup-inspection")


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _candidate() -> SymbolicReference:
    return SymbolicReference(
        resolved_intent_identity=RESOLVED,
        slot_ref=_ref("irr.slot", "candidate"),
        semantic_type="artifact.path",
        selection_scope="workspace:backups",
        description="Candidate backup artifact.",
    )


def _metadata() -> SymbolicReference:
    return SymbolicReference(
        resolved_intent_identity=RESOLVED,
        slot_ref=_ref("irr.slot", "metadata"),
        semantic_type="artifact.metadata",
        selection_scope="workspace:backups",
        description="Inspected backup metadata.",
    )


def _search() -> WorkStep:
    return WorkStep(
        resolved_intent_identity=RESOLVED,
        work_plan_ref=PLAN_REF,
        step_ref=_ref("irr.work_step", "search"),
        operation="filesystem.search",
        scope="workspace:backups",
        inputs=(
            WorkLiteralInput(
                name="directory",
                semantic_type="filesystem.directory",
                value=r"D:\Backups",
            ),
        ),
        outputs=(WorkOutput(name="candidate", reference=_candidate()),),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract="The bounded search yields its declared candidate slot.",
        description="Search the admitted backup workspace.",
    )


def _inspect() -> WorkStep:
    return WorkStep(
        resolved_intent_identity=RESOLVED,
        work_plan_ref=PLAN_REF,
        step_ref=_ref("irr.work_step", "inspect"),
        operation="artifact.inspect",
        scope="workspace:backups",
        inputs=(WorkSymbolicInput(name="artifact", reference=_candidate()),),
        outputs=(WorkOutput(name="metadata", reference=_metadata()),),
        depends_on=(_ref("irr.work_step", "search"),),
        continuation=WorkContinuationMode.RETURN_TO_IRR,
        completion_contract="The selected candidate is inspected and metadata is produced.",
        description="Inspect the selected backup candidate.",
    )


def _plan() -> WorkPlan:
    return WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=PLAN_REF,
        steps=(_search(), _inspect()),
        description="Find one backup candidate, inspect it, then return to IRR.",
    )


def test_m15a_work_golden_digests_are_frozen() -> None:
    search = _search()
    inspect = _inspect()
    plan = _plan()

    literal = search.inputs[0]
    candidate_output = search.outputs[0]
    symbolic_input = inspect.inputs[0]
    metadata_output = inspect.outputs[0]

    assert literal.identity.digest == (
        "0006690b5ef614b59caa64444bc883e7a39660a5c97f6e68f61dc7ccb709b5c9"
    )
    assert candidate_output.identity.digest == (
        "0e20a9dbb971f19dfbbc1a72d0edfd273b50dc287b8df761e19cb9dfd8b294e7"
    )
    assert symbolic_input.identity.digest == (
        "6be2466d24a2576327555fc24eb8b0176297156d162e00596f7f940180db5920"
    )
    assert metadata_output.identity.digest == (
        "ce2472248f089675a722e372846d3a36c5b4b539ce73ac72c78abd5132f06422"
    )
    assert search.identity.digest == (
        "82b6b696929c1a3296b7e46c89d4262083389aad010591b6afcea0f451f40ef5"
    )
    assert inspect.identity.digest == (
        "081e8171b393bd4584456d216d42412371dbf76e1f85db4279a57304eca46870"
    )
    assert plan.identity.digest == (
        "2a222b931575813823cf1cab13518239d46adc65100d54e3cbc3c109fd05968f"
    )


def test_m15a_golden_plan_round_trip_preserves_frozen_identity() -> None:
    plan = _plan()
    decoded = WorkPlan.from_json_bytes(plan.canonical_bytes())
    assert decoded == plan
    assert decoded.identity == plan.identity
