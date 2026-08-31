from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    RecordIdentity,
    SerializationError,
    StableRef,
    SymbolicReference,
    ValidationError,
    WorkContinuationMode,
    WorkLiteralInput,
    WorkOutput,
    WorkPlan,
    WorkStep,
    WorkSymbolicInput,
)

RESOLVED = RecordIdentity("sha256", "1" * 64)
OTHER_RESOLVED = RecordIdentity("sha256", "2" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _symbolic(
    name: str,
    *,
    resolved: RecordIdentity = RESOLVED,
    semantic_type: str = "artifact.path",
    selection_scope: str = "workspace:backups",
) -> SymbolicReference:
    return SymbolicReference(
        resolved_intent_identity=resolved,
        slot_ref=_ref("irr.slot", name),
        semantic_type=semantic_type,
        selection_scope=selection_scope,
        description=f"Symbolic value for {name}.",
    )


def _step(
    name: str,
    *,
    inputs: tuple[WorkLiteralInput | WorkSymbolicInput, ...] = (),
    outputs: tuple[WorkOutput, ...] = (),
    depends_on: tuple[StableRef, ...] = (),
    continuation: WorkContinuationMode = WorkContinuationMode.NONE,
    resolved: RecordIdentity = RESOLVED,
    operation: str = "artifact.inspect",
) -> WorkStep:
    return WorkStep(
        resolved_intent_identity=resolved,
        step_ref=_ref("irr.work_step", name),
        operation=operation,
        scope=f"scope:{name}",
        inputs=inputs,
        outputs=outputs,
        depends_on=depends_on,
        continuation=continuation,
        completion_contract=f"{name} produces its declared bounded result.",
        description=f"Bounded work step {name}.",
    )


def test_work_plan_round_trip_and_step_order_are_canonical() -> None:
    candidate = _symbolic("candidate")
    inspected = _symbolic("inspected", semantic_type="artifact.metadata")

    search = _step(
        "search",
        inputs=(
            WorkLiteralInput(
                name="directory",
                semantic_type="filesystem.directory",
                value=r"D:\Backups",
            ),
        ),
        outputs=(WorkOutput(name="candidate", reference=candidate),),
        operation="filesystem.search",
    )
    inspect = _step(
        "inspect",
        inputs=(WorkSymbolicInput(name="artifact", reference=candidate),),
        outputs=(WorkOutput(name="metadata", reference=inspected),),
        depends_on=(search.step_ref,),
        continuation=WorkContinuationMode.RETURN_TO_IRR,
        operation="artifact.inspect",
    )

    first = WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=_ref("irr.work_plan", "backup-inspection"),
        steps=(inspect, search),
        description="Find one candidate and inspect it before returning to IRR.",
    )
    second = WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=first.plan_ref,
        steps=(search, inspect),
        description=first.description,
    )

    assert first == second
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.identity == second.identity
    assert WorkPlan.from_json_bytes(first.canonical_bytes()) == first


def test_dependency_graph_must_be_finite_and_acyclic() -> None:
    a_ref = _ref("irr.work_step", "a")
    b_ref = _ref("irr.work_step", "b")
    a = _step("a", depends_on=(b_ref,))
    b = _step("b", depends_on=(a_ref,))

    with pytest.raises(ValidationError, match="acyclic"):
        WorkPlan(
            resolved_intent_identity=RESOLVED,
            plan_ref=_ref("irr.work_plan", "cycle"),
            steps=(a, b),
            description="Invalid cyclic plan.",
        )


def test_dependency_must_reference_a_step_in_the_same_plan() -> None:
    step = _step("inspect", depends_on=(_ref("irr.work_step", "missing"),))
    with pytest.raises(ValidationError, match="same plan"):
        WorkPlan(
            resolved_intent_identity=RESOLVED,
            plan_ref=_ref("irr.work_plan", "missing-dependency"),
            steps=(step,),
            description="Invalid missing dependency.",
        )


def test_internal_symbolic_dataflow_requires_dependency_path() -> None:
    produced = _symbolic("produced")
    producer = _step(
        "producer",
        outputs=(WorkOutput(name="result", reference=produced),),
    )
    consumer = _step(
        "consumer",
        inputs=(WorkSymbolicInput(name="result", reference=produced),),
    )

    with pytest.raises(ValidationError, match="producing step"):
        WorkPlan(
            resolved_intent_identity=RESOLVED,
            plan_ref=_ref("irr.work_plan", "unordered-dataflow"),
            steps=(producer, consumer),
            description="Internal dataflow without ordering is invalid.",
        )


def test_transitive_dependency_path_can_carry_internal_symbolic_dataflow() -> None:
    produced = _symbolic("produced")
    producer = _step(
        "producer",
        outputs=(WorkOutput(name="result", reference=produced),),
    )
    bridge = _step("bridge", depends_on=(producer.step_ref,))
    consumer = _step(
        "consumer",
        inputs=(WorkSymbolicInput(name="result", reference=produced),),
        depends_on=(bridge.step_ref,),
    )

    plan = WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=_ref("irr.work_plan", "transitive-dataflow"),
        steps=(consumer, producer, bridge),
        description="Transitive dependency preserves required ordering.",
    )
    assert len(plan.steps) == 3


def test_external_symbolic_input_does_not_require_an_internal_producer() -> None:
    external = _symbolic("externally-bound")
    step = _step(
        "consume",
        inputs=(WorkSymbolicInput(name="value", reference=external),),
    )
    plan = WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=_ref("irr.work_plan", "external-symbolic"),
        steps=(step,),
        description="The symbolic input may be bound outside this plan.",
    )
    assert plan.steps[0].inputs[0].reference == external


def test_same_symbolic_slot_cannot_have_conflicting_semantics() -> None:
    first = _symbolic("shared", semantic_type="artifact.path")
    conflicting = _symbolic("shared", semantic_type="artifact.metadata")
    a = _step(
        "a",
        inputs=(WorkSymbolicInput(name="one", reference=first),),
    )
    b = _step(
        "b",
        inputs=(WorkSymbolicInput(name="two", reference=conflicting),),
    )
    with pytest.raises(ValidationError, match="conflicting semantics"):
        WorkPlan(
            resolved_intent_identity=RESOLVED,
            plan_ref=_ref("irr.work_plan", "conflicting-symbol"),
            steps=(a, b),
            description="Conflicting symbolic meaning is invalid.",
        )


def test_same_symbolic_output_slot_cannot_have_multiple_producers() -> None:
    output = _symbolic("shared-output")
    a = _step("a", outputs=(WorkOutput(name="result-a", reference=output),))
    b = _step("b", outputs=(WorkOutput(name="result-b", reference=output),))
    with pytest.raises(ValidationError, match="multiple steps"):
        WorkPlan(
            resolved_intent_identity=RESOLVED,
            plan_ref=_ref("irr.work_plan", "duplicate-producer"),
            steps=(a, b),
            description="A symbolic output has one producer in a plan.",
        )


def test_work_step_rejects_foreign_symbolic_lineage() -> None:
    foreign = _symbolic("foreign", resolved=OTHER_RESOLVED)
    with pytest.raises(ValidationError, match="same ResolvedIntent"):
        _step(
            "foreign-input",
            inputs=(WorkSymbolicInput(name="foreign", reference=foreign),),
        )


def test_literal_executable_looking_text_remains_data() -> None:
    literal = WorkLiteralInput(
        name="user_text",
        semantic_type="text.literal",
        value="rm -rf / && curl https://example.invalid",
    )
    step = _step("preserve-text", inputs=(literal,), operation="text.inspect")
    plan = WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=_ref("irr.work_plan", "literal-data"),
        steps=(step,),
        description="Executable-looking text is represented only as literal input data.",
    )
    assert plan.steps[0].inputs[0].value == literal.value
    assert b"rm -rf /" in plan.canonical_bytes()


def test_work_plan_unknown_fields_fail_closed() -> None:
    plan = WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=_ref("irr.work_plan", "unknown-field"),
        steps=(_step("one"),),
        description="Unknown fields are rejected.",
    )
    primitive = plan.to_primitive()
    primitive["approved"] = "true"
    with pytest.raises(SerializationError, match="invalid fields"):
        WorkPlan.from_primitive(primitive)


def test_work_ir_has_no_authority_surface() -> None:
    plan = WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=_ref("irr.work_plan", "no-authority"),
        steps=(_step("one"),),
        description="Work semantics remain separate from authority.",
    )

    def walk(value: object) -> list[str]:
        if isinstance(value, dict):
            return list(value) + [
                key
                for child in value.values()
                for key in walk(child)
            ]
        if isinstance(value, list):
            return [key for child in value for key in walk(child)]
        return []

    keys = set(walk(plan.to_primitive()))
    assert not {"authorized", "authorization", "approved", "permission", "safe"} & keys


def test_public_work_records_are_closed_ir_types() -> None:
    with pytest.raises(TypeError, match="closed IR type"):
        class InvalidPlan(WorkPlan):
            pass

    with pytest.raises(TypeError, match="closed IR type"):
        class InvalidStep(WorkStep):
            pass
