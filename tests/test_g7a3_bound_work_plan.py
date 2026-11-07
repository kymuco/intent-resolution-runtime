"""G7A.3 explicit dynamic WorkPlan materialization with zero authority."""

from __future__ import annotations

from dataclasses import replace

import pytest

from intent_resolution_runtime import (
    RecordIdentity,
    WorkContinuationMode,
    WorkPlan,
    WorkSymbolicInput,
)
from intent_resolution_runtime.binding import SymbolicReference
from intent_resolution_runtime.bound_work_plan import (
    BoundWorkPlanError,
    HostBoundStep,
    HostBoundWorkPlanMaterial,
    HostContractFieldName,
    HostExternalSymbolicBinding,
    HostLiteralBinding,
    HostPriorOutputBinding,
    assert_current_unadmitted_work_plan,
    materialize_unadmitted_work_plan,
)
from intent_resolution_runtime.candidate_planning_surface import (
    HostPlanningVisibility,
    build_candidate_planning_surface,
    find_structural_plan_candidates,
)
from tests.test_g7a1_dynamic_candidate_planning import (
    candidate,
    descriptor,
    ref,
    visibility,
)

RESOLVED = RecordIdentity("sha256", "1" * 64)


def _named(contract, name: str) -> HostContractFieldName:
    return HostContractFieldName(contract_ref=contract, name=name)


def _material(
    first,
    second,
    *,
    second_scope: str = "workspace:document",
) -> HostBoundWorkPlanMaterial:
    first_ref = ref("irr.work_step", "collect")
    second_ref = ref("irr.work_step", "summarize")
    first_input = first.input_contracts[0].input_ref
    first_output = first.output_contracts[0].output_ref
    second_input = second.input_contracts[0].input_ref
    second_output = second.output_contracts[0].output_ref
    return HostBoundWorkPlanMaterial(
        resolved_intent_identity=RESOLVED,
        plan_ref=ref("irr.work_plan", "from-human-goal"),
        steps=(
            HostBoundStep(
                capability_ref=first.capability_ref,
                step_ref=first_ref,
                scope="workspace:document",
                scope_requirement_refs=tuple(
                    item.requirement_ref for item in first.scope_requirements
                ),
                input_fields=(_named(first_input, "source"),),
                output_fields=(_named(first_output, "metadata"),),
                input_bindings=(HostLiteralBinding(first_input, "docs/research.txt"),),
            ),
            HostBoundStep(
                capability_ref=second.capability_ref,
                step_ref=second_ref,
                scope=second_scope,
                scope_requirement_refs=tuple(
                    item.requirement_ref for item in second.scope_requirements
                ),
                input_fields=(_named(second_input, "metadata"),),
                output_fields=(_named(second_output, "summary"),),
                input_bindings=(
                    HostPriorOutputBinding(
                        contract_ref=second_input,
                        producer_step_ref=first_ref,
                        producer_output_ref=first_output,
                    ),
                ),
            ),
        ),
        completion_contract="A verified summary is ready for HUMAN review.",
        description="Proposed collection and summarization, not admitted.",
    )


def _setup():
    first = descriptor("dynamic.collect", "workspace.path", "artifact.metadata")
    second = descriptor("dynamic.summarize", "artifact.metadata", "artifact.summary")
    catalog = candidate(first, second)
    surface = build_candidate_planning_surface(
        candidate=catalog,
        visibility=visibility(
            catalog,
            first.capability_ref,
            second.capability_ref,
        ),
    )
    sketch = find_structural_plan_candidates(
        surface,
        desired_output_semantic_type="artifact.summary",
        available_input_semantic_types=("workspace.path",),
    )[0]
    return first, second, surface, sketch


def test_host_bound_two_step_plan_has_exact_symbolic_dataflow() -> None:
    first, second, surface, sketch = _setup()
    result = materialize_unadmitted_work_plan(
        surface=surface,
        sketch=sketch,
        material=_material(first, second),
    )
    assert type(result.work_plan) is WorkPlan
    assert not result.admitted and not result.execution_authorized
    assert result.candidate_identity == surface.candidate_identity
    assert result.policy_revision_identity == surface.policy_revision_identity
    assert result.actor_ref == surface.actor_ref
    assert (
        WorkPlan.from_json_bytes(result.work_plan.canonical_bytes()) == result.work_plan
    )
    steps = {step.operation: step for step in result.work_plan.steps}
    collect = steps["dynamic.collect"]
    summarize = steps["dynamic.summarize"]
    assert summarize.depends_on == (collect.step_ref,)
    assert summarize.continuation is WorkContinuationMode.RETURN_TO_IRR
    assert collect.continuation is WorkContinuationMode.NONE
    assert summarize.inputs[0].name == "metadata"
    assert type(summarize.inputs[0]) is WorkSymbolicInput
    assert summarize.inputs[0].reference == collect.outputs[0].reference
    assert collect.inputs[0].value == "docs/research.txt"
    assert_current_unadmitted_work_plan(result, surface)


def test_reusing_unchanged_algorithm_for_new_plugin_capability() -> None:
    first, _, _, _ = _setup()
    sign = descriptor("plugin.sign", "artifact.metadata", "artifact.signature")
    catalog = candidate(first, sign, event="new-review")
    surface = build_candidate_planning_surface(
        candidate=catalog,
        visibility=visibility(catalog, first.capability_ref, sign.capability_ref),
    )
    sketch = find_structural_plan_candidates(
        surface,
        desired_output_semantic_type="artifact.signature",
        available_input_semantic_types=("workspace.path",),
    )[0]
    material = _material(first, sign)
    result = materialize_unadmitted_work_plan(
        surface=surface, sketch=sketch, material=material
    )
    assert {step.operation for step in result.work_plan.steps} == {
        "dynamic.collect",
        "plugin.sign",
    }
    assert not result.execution_authorized


def test_stale_policy_and_catalog_reject_existing_plan() -> None:
    first, second, surface, sketch = _setup()
    old = materialize_unadmitted_work_plan(
        surface=surface, sketch=sketch, material=_material(first, second)
    )
    new_policy = HostPlanningVisibility(
        actor_ref=surface.actor_ref,
        policy_ref=surface.policy_ref,
        policy_revision_identity=RecordIdentity("sha256", "f" * 64),
        candidate_identity=surface.candidate_identity,
        visible_capability_refs=(first.capability_ref, second.capability_ref),
    )
    catalog = candidate(first, second)
    changed = build_candidate_planning_surface(candidate=catalog, visibility=new_policy)
    with pytest.raises(BoundWorkPlanError, match="stale"):
        assert_current_unadmitted_work_plan(old, changed)
    updated_catalog = candidate(first, second, event="updated-source")
    updated_surface = build_candidate_planning_surface(
        candidate=updated_catalog,
        visibility=visibility(
            updated_catalog, first.capability_ref, second.capability_ref
        ),
    )
    with pytest.raises(BoundWorkPlanError, match="stale"):
        assert_current_unadmitted_work_plan(old, updated_surface)


def test_missing_extra_or_foreign_host_field_mapping_fails_closed() -> None:
    first, second, surface, sketch = _setup()
    baseline = _material(first, second)
    one, two = baseline.steps
    with pytest.raises(BoundWorkPlanError, match="mapping differs"):
        materialize_unadmitted_work_plan(
            surface=surface,
            sketch=sketch,
            material=replace(baseline, steps=(replace(one, input_fields=()), two)),
        )
    with pytest.raises(BoundWorkPlanError, match="mapping differs"):
        materialize_unadmitted_work_plan(
            surface=surface,
            sketch=sketch,
            material=replace(
                baseline,
                steps=(
                    replace(
                        one,
                        output_fields=(
                            _named(ref("foreign.contract", "result"), "metadata"),
                        ),
                    ),
                    two,
                ),
            ),
        )
    with pytest.raises(BoundWorkPlanError, match="missing or extra"):
        materialize_unadmitted_work_plan(
            surface=surface,
            sketch=sketch,
            material=replace(baseline, steps=(replace(one, input_bindings=()), two)),
        )


def test_wrong_producer_type_foreign_scope_and_future_binding_fail_closed() -> None:
    first, second, surface, sketch = _setup()
    baseline = _material(first, second)
    one, two = baseline.steps
    with pytest.raises(BoundWorkPlanError, match="cross-scope"):
        materialize_unadmitted_work_plan(
            surface=surface,
            sketch=sketch,
            material=_material(first, second, second_scope="workspace:other"),
        )
    with pytest.raises(BoundWorkPlanError, match="missing earlier"):
        materialize_unadmitted_work_plan(
            surface=surface,
            sketch=sketch,
            material=replace(
                baseline,
                steps=(
                    one,
                    replace(
                        two,
                        input_bindings=(
                            HostPriorOutputBinding(
                                contract_ref=second.input_contracts[0].input_ref,
                                producer_step_ref=two.step_ref,
                                producer_output_ref=second.output_contracts[
                                    0
                                ].output_ref,
                            ),
                        ),
                    ),
                ),
            ),
        )
    with pytest.raises(BoundWorkPlanError, match="scope requirements"):
        materialize_unadmitted_work_plan(
            surface=surface,
            sketch=sketch,
            material=replace(
                baseline, steps=(replace(one, scope_requirement_refs=()), two)
            ),
        )


def test_external_symbolic_input_requires_same_intent_type_and_scope() -> None:
    first, second, surface, sketch = _setup()
    baseline = _material(first, second)
    one, two = baseline.steps
    source = SymbolicReference(
        resolved_intent_identity=RESOLVED,
        slot_ref=ref("irr.external", "human-document"),
        semantic_type="workspace.path",
        selection_scope=one.scope,
        description="Bounded original-human document reference.",
    )
    bind = HostExternalSymbolicBinding(
        contract_ref=first.input_contracts[0].input_ref,
        reference=source,
    )
    result = materialize_unadmitted_work_plan(
        surface=surface,
        sketch=sketch,
        material=replace(baseline, steps=(replace(one, input_bindings=(bind,)), two)),
    )
    assert isinstance(result.work_plan.steps[0].inputs[0], WorkSymbolicInput)
    with pytest.raises(BoundWorkPlanError, match="foreign external"):
        materialize_unadmitted_work_plan(
            surface=surface,
            sketch=sketch,
            material=replace(
                baseline,
                steps=(
                    replace(
                        one,
                        input_bindings=(
                            HostExternalSymbolicBinding(
                                contract_ref=first.input_contracts[0].input_ref,
                                reference=replace(
                                    source, semantic_type="workspace.paths"
                                ),
                            ),
                        ),
                    ),
                    two,
                ),
            ),
        )


def test_no_raw_sketch_or_foreign_actor_can_mint_authority() -> None:
    first, second, surface, sketch = _setup()
    material = _material(first, second)
    with pytest.raises(BoundWorkPlanError, match="exact G7A.1"):
        materialize_unadmitted_work_plan(
            surface=surface, sketch=None, material=material
        )
    with pytest.raises(BoundWorkPlanError, match="stale"):
        materialize_unadmitted_work_plan(
            surface=surface,
            sketch=replace(sketch, actor_ref=ref("hde.actor", "foreign")),
            material=material,
        )
    result = materialize_unadmitted_work_plan(
        surface=surface, sketch=sketch, material=material
    )
    for forbidden in ("execute", "governance", "authorization", "attempt", "admitter"):
        assert not hasattr(result, forbidden)
