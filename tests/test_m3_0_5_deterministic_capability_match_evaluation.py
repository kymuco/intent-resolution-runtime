from __future__ import annotations

from dataclasses import replace

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffect,
    CapabilityEffectRequirement,
    CapabilityInputContract,
    CapabilityMatch,
    CapabilityMatchIssue,
    CapabilityMatchIssueKind,
    CapabilityMismatchKind,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeRequirement,
    RecordIdentity,
    StableRef,
    WorkContinuationMode,
    WorkLiteralInput,
    WorkPlan,
    WorkStep,
    evaluate_capability_match_evaluation,
)
from intent_resolution_runtime.capability_match_engine import (
    IRR_CAPABILITY_MATCH_ENGINE_CONTRACT_VERSION,
    IRR_CAPABILITY_MATCH_EVENT_NAMESPACE,
    IRR_MECHANICAL_CAPABILITY_EVALUATOR_NAMESPACE,
    IRR_MECHANICAL_CAPABILITY_EVALUATOR_VALUE,
    IRR_MECHANICAL_CAPABILITY_MATCHER_NAMESPACE,
    IRR_MECHANICAL_CAPABILITY_MATCHER_VALUE,
    build_capability_match_evaluation,
    mechanical_capability_evaluator_ref,
    mechanical_capability_matcher_ref,
)


RESOLVED = RecordIdentity("sha256", "7" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace=namespace, value=value)


def _plan(*, inputs=()) -> WorkPlan:
    plan_ref = _ref("irr.work_plan", "m3.0.5")
    step = WorkStep(
        resolved_intent_identity=RESOLVED,
        work_plan_ref=plan_ref,
        step_ref=_ref("irr.work_step", "inspect"),
        operation="workspace.inspect",
        scope="workspace:project",
        inputs=inputs,
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract="Return the bounded workspace inspection result.",
        description="Inspect one bounded workspace.",
    )
    return WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="Complete the bounded inspection plan.",
        description="One-step bounded inspection plan.",
    )


def _requirement(*, inputs=(), duplicate_scope: bool = False) -> CapabilityRequirement:
    plan = _plan(inputs=inputs)
    primary = CapabilityRequestedScope(
        scope_ref=_ref("irr.capability_requested_scope", "workspace-primary"),
        semantic_type="filesystem.path_scope",
        value="workspace:project",
        description="Primary bounded workspace scope.",
    )
    scopes = [primary]
    if duplicate_scope:
        scopes.append(
            CapabilityRequestedScope(
                scope_ref=_ref("irr.capability_requested_scope", "workspace-secondary"),
                semantic_type="filesystem.path_scope",
                value="workspace:secondary",
                description="Secondary bounded workspace scope.",
            )
        )
    return CapabilityRequirement(
        work_plan=plan,
        step_ref=plan.steps[0].step_ref,
        primary_scope_ref=primary.scope_ref,
        requested_scopes=tuple(scopes),
        requested_effects=(),
        execution_boundary_requirements=(),
        description="Exact bounded inspection capability requirement.",
    )


def _descriptor(
    name: str,
    *,
    operation: str = "workspace.inspect",
    duplicate_scope: bool = False,
    inputs=(),
    effects=(),
) -> CapabilityDescriptor:
    scopes = [
        CapabilityScopeRequirement(
            requirement_ref=_ref("irr.capability_scope_requirement", f"{name}:primary"),
            semantic_type="filesystem.path_scope",
            statement="Invocation must remain inside one bounded workspace.",
        )
    ]
    if duplicate_scope:
        scopes.append(
            CapabilityScopeRequirement(
                requirement_ref=_ref(
                    "irr.capability_scope_requirement", f"{name}:secondary"
                ),
                semantic_type="filesystem.path_scope",
                statement="Invocation must remain inside a second bounded workspace.",
            )
        )
    return CapabilityDescriptor(
        capability_ref=_ref("irr.capability", name),
        operation=operation,
        input_contracts=inputs,
        output_contracts=(),
        scope_requirements=tuple(scopes),
        effects=effects,
        execution_boundaries=(),
        completion_contract="Return the bounded workspace inspection result.",
        description=f"Bounded workspace inspection capability {name}.",
    )


def _snapshot(*descriptors: CapabilityDescriptor) -> CapabilityCatalogSnapshot:
    return CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", "m3.0.5"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=_ref("irr.host", "test-host"),
            snapshot_event_ref=_ref("irr.catalog_event", "m3.0.5:1"),
        ),
        scope_statement="Exact bounded capability surface supplied for this test.",
        descriptors=tuple(descriptors),
        description="M3.0.5 deterministic matcher test catalog.",
    )


def _evaluate(requirement, snapshot, *, event: str = "evaluation:1"):
    return build_capability_match_evaluation(
        requirement,
        snapshot,
        evaluation_event_ref=_ref("irr.capability_evaluation", event),
    )


def test_fixed_public_mechanical_identities() -> None:
    assert IRR_CAPABILITY_MATCH_ENGINE_CONTRACT_VERSION == "1"
    matcher = mechanical_capability_matcher_ref()
    evaluator = mechanical_capability_evaluator_ref()

    assert matcher.namespace == IRR_MECHANICAL_CAPABILITY_MATCHER_NAMESPACE
    assert matcher.value == IRR_MECHANICAL_CAPABILITY_MATCHER_VALUE
    assert evaluator.namespace == IRR_MECHANICAL_CAPABILITY_EVALUATOR_NAMESPACE
    assert evaluator.value == IRR_MECHANICAL_CAPABILITY_EVALUATOR_VALUE


def test_single_exact_descriptor_produces_one_exact_match() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(descriptor)

    evaluation = _evaluate(requirement, snapshot)
    result = evaluate_capability_match_evaluation(evaluation)

    assert evaluation.requirement == requirement
    assert evaluation.catalog_snapshot == snapshot
    assert evaluation.attribution.evaluator_ref == mechanical_capability_evaluator_ref()
    assert len(evaluation.compatible_matches) == 1
    assert evaluation.incompatible_assessments == ()
    assert result.__class__ is CapabilityMatch
    assert result == evaluation.compatible_matches[0]
    assert result.capability_ref == descriptor.capability_ref
    assert result.attribution.matcher_ref == mechanical_capability_matcher_ref()
    assert result.attribution.match_event_ref.namespace == IRR_CAPABILITY_MATCH_EVENT_NAMESPACE


def test_empty_catalog_is_bounded_no_match_not_global_impossibility() -> None:
    evaluation = _evaluate(_requirement(), _snapshot())
    result = evaluate_capability_match_evaluation(evaluation)

    assert evaluation.compatible_matches == ()
    assert evaluation.incompatible_assessments == ()
    assert result.__class__ is CapabilityMatchIssue
    assert result.kind is CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY


def test_operation_mismatch_is_explicit_descriptor_assessment() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.scan.local", operation="workspace.scan")
    evaluation = _evaluate(requirement, _snapshot(descriptor))

    assert evaluation.compatible_matches == ()
    assert len(evaluation.incompatible_assessments) == 1
    assessment = evaluation.incompatible_assessments[0]
    assert assessment.capability_ref == descriptor.capability_ref
    assert assessment.capability_contract_identity == descriptor.identity
    assert {reason.kind for reason in assessment.reasons} == {
        CapabilityMismatchKind.OPERATION_MISMATCH
    }


def test_duplicate_scope_semantics_fail_closed_as_insufficient_semantics() -> None:
    requirement = _requirement(duplicate_scope=True)
    descriptor = _descriptor(
        "workspace.inspect.ambiguous-scopes",
        duplicate_scope=True,
    )
    evaluation = _evaluate(requirement, _snapshot(descriptor))

    assert evaluation.compatible_matches == ()
    assert evaluation.incompatible_assessments[0].reasons[0].kind is (
        CapabilityMismatchKind.INSUFFICIENT_SEMANTICS
    )


def test_duplicate_same_type_input_pairing_never_uses_tuple_order() -> None:
    first_input = WorkLiteralInput(
        name="left",
        semantic_type="artifact_ref",
        value="artifact:left",
    )
    second_input = WorkLiteralInput(
        name="right",
        semantic_type="artifact_ref",
        value="artifact:right",
    )
    requirement = _requirement(inputs=(first_input, second_input))
    scope_ref = _ref(
        "irr.capability_scope_requirement",
        "workspace.inspect.ambiguous-inputs:primary",
    )
    descriptor = _descriptor(
        "workspace.inspect.ambiguous-inputs",
        inputs=(
            CapabilityInputContract(
                input_ref=_ref("irr.capability_input", "a"),
                semantic_type="artifact_ref",
                scope_requirement_refs=(scope_ref,),
                description="First artifact input.",
            ),
            CapabilityInputContract(
                input_ref=_ref("irr.capability_input", "b"),
                semantic_type="artifact_ref",
                scope_requirement_refs=(scope_ref,),
                description="Second artifact input.",
            ),
        ),
    )
    evaluation = _evaluate(requirement, _snapshot(descriptor))

    assert evaluation.compatible_matches == ()
    assert evaluation.incompatible_assessments[0].reasons[0].kind is (
        CapabilityMismatchKind.INSUFFICIENT_SEMANTICS
    )


def test_unavoidable_unrequested_effect_fails_closed() -> None:
    requirement = _requirement()
    scope_ref = _ref(
        "irr.capability_scope_requirement",
        "workspace.inspect.mutating:primary",
    )
    effect = CapabilityEffect(
        effect_ref=_ref("irr.capability_effect", "filesystem.write"),
        semantic_type="filesystem.write",
        requirement=CapabilityEffectRequirement.UNAVOIDABLE,
        scope_requirement_refs=(scope_ref,),
        description="Invocation necessarily writes inside the bounded scope.",
    )
    descriptor = _descriptor(
        "workspace.inspect.mutating",
        effects=(effect,),
    )
    evaluation = _evaluate(requirement, _snapshot(descriptor))

    assert evaluation.compatible_matches == ()
    assert evaluation.incompatible_assessments[0].reasons[0].kind is (
        CapabilityMismatchKind.UNAVOIDABLE_EFFECT_MISMATCH
    )


def test_multiple_compatible_descriptors_never_choose_a_winner() -> None:
    requirement = _requirement()
    first = _descriptor("workspace.inspect.a")
    second = _descriptor("workspace.inspect.b")
    evaluation = _evaluate(requirement, _snapshot(second, first))
    result = evaluate_capability_match_evaluation(evaluation)

    assert len(evaluation.compatible_matches) == 2
    assert result.__class__ is CapabilityMatchIssue
    assert result.kind is CapabilityMatchIssueKind.MULTIPLE_COMPATIBLE_MATCHES
    assert {match.capability_ref for match in evaluation.compatible_matches} == {
        first.capability_ref,
        second.capability_ref,
    }


def test_catalog_presentation_order_does_not_change_evaluation() -> None:
    requirement = _requirement()
    first = _descriptor("workspace.inspect.a")
    second = replace(
        _descriptor("workspace.inspect.b"),
        operation="workspace.scan",
    )

    forward = _evaluate(requirement, _snapshot(first, second), event="same")
    reverse = _evaluate(requirement, _snapshot(second, first), event="same")

    assert forward == reverse
    assert forward.identity == reverse.identity
