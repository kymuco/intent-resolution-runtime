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
PLAN_REF = StableRef("irr.work_plan", "test-plan")
OTHER_PLAN_REF = StableRef("irr.work_plan", "other-plan")


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
    plan_ref: StableRef = PLAN_REF,
    operation: str = "artifact.inspect",
) -> WorkStep:
    return WorkStep(
        resolved_intent_identity=resolved,
        work_plan_ref=plan_ref,
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


def _plan(
    *steps: WorkStep,
    completion_contract: str = "All declared bounded work reaches the plan's admitted completion condition.",
    description: str = "Bounded test plan.",
) -> WorkPlan:
    return WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=PLAN_REF,
        steps=steps,
        completion_contract=completion_contract,
        description=description,
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

    first = _plan(
        inspect,
        search,
        completion_contract="A candidate has been inspected and its metadata is ready for IRR.",
        description="Find one candidate and inspect it before returning to IRR.",
    )
    second = _plan(
        search,
        inspect,
        completion_contract=first.completion_contract,
        description=first.description,
    )

    assert first == second
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.identity == second.identity
    assert WorkPlan.from_json_bytes(first.canonical_bytes()) == first


def test_work_plan_completion_contract_is_distinct_identity_covered_semantics() -> None:
    step = _step("one")
    first = _plan(step, completion_contract="The bounded inspection result exists.")
    second = _plan(step, completion_contract="The bounded inspection result has been reviewed by IRR.")

    assert first != second
    assert first.identity != second.identity


def test_work_step_is_bound_to_parent_work_plan_ref() -> None:
    foreign_step = _step("foreign-plan", plan_ref=OTHER_PLAN_REF)
    with pytest.raises(ValidationError, match="same WorkPlan ref"):
        _plan(foreign_step)


def test_dependency_graph_must_be_finite_and_acyclic() -> None:
    a_ref = _ref("irr.work_step", "a")
    b_ref = _ref("irr.work_step", "b")
    a = _step("a", depends_on=(b_ref,))
    b = _step("b", depends_on=(a_ref,))

    with pytest.raises(ValidationError, match="acyclic"):
        _plan(a, b, description="Invalid cyclic plan.")


def test_large_finite_dependency_chain_does_not_depend_on_python_recursion_limit() -> None:
    steps: list[WorkStep] = []
    previous: StableRef | None = None
    for index in range(1500):
        name = f"step-{index:04d}"
        step = _step(
            name,
            depends_on=() if previous is None else (previous,),
            operation="test.step",
        )
        steps.append(step)
        previous = step.step_ref

    plan = _plan(*reversed(steps), description="Large but finite acyclic plan.")
    assert len(plan.steps) == 1500


def test_dependency_must_reference_a_step_in_the_same_plan() -> None:
    step = _step("inspect", depends_on=(_ref("irr.work_step", "missing"),))
    with pytest.raises(ValidationError, match="same plan"):
        _plan(step, description="Invalid missing dependency.")


def test_return_to_irr_is_terminal_with_respect_to_plan_dependencies() -> None:
    pause = _step("pause", continuation=WorkContinuationMode.RETURN_TO_IRR)
    hidden_successor = _step("hidden-successor", depends_on=(pause.step_ref,))

    with pytest.raises(ValidationError, match="terminal"):
        _plan(
            pause,
            hidden_successor,
            description="A successor cannot be pre-admitted beyond return_to_irr.",
        )


def test_independent_work_may_coexist_with_terminal_return_to_irr_step() -> None:
    pause = _step("pause", continuation=WorkContinuationMode.RETURN_TO_IRR)
    independent = _step("independent", operation="artifact.inspect")
    plan = _plan(pause, independent)
    assert len(plan.steps) == 2


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
        _plan(
            producer,
            consumer,
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

    plan = _plan(
        consumer,
        producer,
        bridge,
        description="Transitive dependency preserves required ordering.",
    )
    assert len(plan.steps) == 3


def test_external_symbolic_input_does_not_require_an_internal_producer() -> None:
    external = _symbolic("externally-bound")
    step = _step(
        "consume",
        inputs=(WorkSymbolicInput(name="value", reference=external),),
    )
    plan = _plan(
        step,
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
        _plan(a, b, description="Conflicting symbolic meaning is invalid.")


def test_same_symbolic_output_slot_cannot_have_multiple_producers() -> None:
    output = _symbolic("shared-output")
    a = _step("a", outputs=(WorkOutput(name="result-a", reference=output),))
    b = _step("b", outputs=(WorkOutput(name="result-b", reference=output),))
    with pytest.raises(ValidationError, match="multiple steps"):
        _plan(a, b, description="A symbolic output has one producer in a plan.")


def test_work_step_rejects_foreign_symbolic_lineage() -> None:
    foreign = _symbolic("foreign", resolved=OTHER_RESOLVED)
    with pytest.raises(ValidationError, match="same ResolvedIntent"):
        _step(
            "foreign-input",
            inputs=(WorkSymbolicInput(name="foreign", reference=foreign),),
        )


def test_operation_is_a_dotted_semantic_identifier_not_executable_text() -> None:
    assert _step("valid-operation", operation="filesystem.search").operation == "filesystem.search"
    with pytest.raises(ValidationError, match="semantic operation identifier"):
        _step("command-shaped-operation", operation="rm -rf /")
    with pytest.raises(ValidationError, match="semantic operation identifier"):
        _step("single-token-operation", operation="search")


def test_literal_executable_looking_text_remains_data() -> None:
    literal = WorkLiteralInput(
        name="user_text",
        semantic_type="text.literal",
        value="rm -rf / && curl https://example.invalid",
    )
    step = _step("preserve-text", inputs=(literal,), operation="text.inspect")
    plan = _plan(
        step,
        description="Executable-looking text is represented only as literal input data.",
    )
    assert plan.steps[0].inputs[0].value == literal.value
    assert b"rm -rf /" in plan.canonical_bytes()


def test_literal_string_value_may_be_empty_or_whitespace_when_semantically_meaningful() -> None:
    empty = WorkLiteralInput(name="empty", semantic_type="text.literal", value="")
    whitespace = WorkLiteralInput(name="whitespace", semantic_type="text.literal", value="   ")
    step = _step("literal-edge-values", inputs=(whitespace, empty), operation="text.inspect")
    plan = _plan(step)
    values = {item.name: item.value for item in plan.steps[0].inputs}
    assert values == {"empty": "", "whitespace": "   "}


def test_work_plan_unknown_fields_fail_closed() -> None:
    plan = _plan(_step("one"), description="Unknown fields are rejected.")
    primitive = plan.to_primitive()
    primitive["approved"] = "true"
    with pytest.raises(SerializationError, match="invalid fields"):
        WorkPlan.from_primitive(primitive)


def test_work_ir_has_no_authority_surface() -> None:
    plan = _plan(
        _step("one"),
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
