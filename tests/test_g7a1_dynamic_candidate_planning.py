"""G7A.1: arbitrary new capabilities enter IRR planning through typed catalogs."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffect,
    CapabilityEffectRequirement,
    CapabilityExecutionBoundary,
    CapabilityExecutionBoundaryKind,
    CapabilityInputContract,
    CapabilityOutputContract,
    CapabilityScopeRequirement,
    StableRef,
)
from intent_resolution_runtime.capability_catalog_admission import (
    CandidateCapabilityCatalogSnapshot,
    CapabilityCatalogSnapshotProposalAttribution,
)
from intent_resolution_runtime.candidate_planning_surface import (
    CapabilityPlanningSurfaceError,
    HostPlanningVisibility,
    build_candidate_planning_surface,
    find_structural_plan_candidates,
)
from intent_resolution_runtime.identity import RecordIdentity


def ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def descriptor(
    operation: str, input_type: str, output_type: str
) -> CapabilityDescriptor:
    scope_ref = ref("host.test.scope", operation)
    return CapabilityDescriptor(
        capability_ref=ref("host.dynamic.capability", operation),
        operation=operation,
        input_contracts=(
            CapabilityInputContract(
                input_ref=ref("host.input", operation),
                semantic_type=input_type,
                scope_requirement_refs=(scope_ref,),
                description="Host-mapped exact input type.",
            ),
        ),
        output_contracts=(
            CapabilityOutputContract(
                output_ref=ref("host.output", operation),
                semantic_type=output_type,
                scope_requirement_refs=(scope_ref,),
                description="Host-mapped exact output type.",
            ),
        ),
        scope_requirements=(
            CapabilityScopeRequirement(
                requirement_ref=scope_ref,
                semantic_type="workspace.bounded_scope",
                statement="Host-selected bounded scope, still requires approval.",
            ),
        ),
        effects=(
            CapabilityEffect(
                effect_ref=ref("host.effect", operation),
                semantic_type="workspace.read",
                requirement=CapabilityEffectRequirement.POSSIBLE,
                scope_requirement_refs=(scope_ref,),
                description="Effect is possible, not authorized.",
            ),
        ),
        execution_boundaries=(
            CapabilityExecutionBoundary(
                boundary_ref=ref("host.executor", "runplane"),
                kind=CapabilityExecutionBoundaryKind.EXECUTOR,
                description="Technical provider boundary, not a grant.",
            ),
        ),
        completion_contract="Return output only after a governed completion.",
        description="Host-verified semantic description of plugin operation.",
    )


def candidate(*descriptors: CapabilityDescriptor, event: str = "v1"):
    snapshot = CapabilityCatalogSnapshot(
        catalog_ref=ref("host.catalog", "catalog"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=ref("host.supplier", "trusted-shell"),
            snapshot_event_ref=ref("host.snapshot", event),
        ),
        scope_statement="Host-curated, not admitted or authorized catalog.",
        descriptors=descriptors,
        description="Exact snapshot from trusted Runplane inventory projection.",
    )
    return CandidateCapabilityCatalogSnapshot(
        attribution=CapabilityCatalogSnapshotProposalAttribution(
            proposer_ref=ref("host.proposer", "trusted-shell"),
            proposal_event_ref=ref("host.proposal", event),
        ),
        snapshot=snapshot,
        rationale="Candidate before any WorkPlan, not a capability admission.",
    )


def visibility(catalog, *permitted: StableRef):
    return HostPlanningVisibility(
        actor_ref=ref("host.actor", "human"),
        policy_ref=ref("host.policy", "restricted-planning"),
        policy_revision_identity=RecordIdentity("sha256", "a" * 64),
        candidate_identity=catalog.identity,
        visible_capability_refs=tuple(permitted),
    )


def test_new_plugin_changes_planning_without_changing_planner_code() -> None:
    collect = descriptor("dynamic.collect", "workspace.path", "artifact.metadata")
    summarize = descriptor("dynamic.summarize", "artifact.metadata", "artifact.summary")
    sign = descriptor("dynamic.sign", "artifact.metadata", "artifact.signature")

    first = candidate(collect, summarize, event="initial")
    view = build_candidate_planning_surface(
        candidate=first,
        visibility=visibility(first, collect.capability_ref, summarize.capability_ref),
    )
    suggestions = find_structural_plan_candidates(
        view,
        desired_output_semantic_type="artifact.summary",
        available_input_semantic_types=("workspace.path",),
    )
    assert [path.operations for path in suggestions] == [
        ("dynamic.collect", "dynamic.summarize")
    ]
    assert all(not path.execution_authorized for path in suggestions)
    assert not view.execution_authorized
    assert view.admitted_catalog is None

    updated = candidate(collect, summarize, sign, event="plugin-installed")
    updated_view = build_candidate_planning_surface(
        candidate=updated,
        visibility=visibility(
            updated,
            collect.capability_ref,
            summarize.capability_ref,
            sign.capability_ref,
        ),
    )
    assert [hint.semantic_type for hint in updated_view.dependency_hints] == [
        "artifact.metadata", "artifact.metadata"
    ]
    new_suggestions = find_structural_plan_candidates(
        updated_view,
        desired_output_semantic_type="artifact.signature",
        available_input_semantic_types=("workspace.path",),
    )
    assert [path.operations for path in new_suggestions] == [
        ("dynamic.collect", "dynamic.sign")
    ]


def test_plugin_is_invisible_until_host_policy_explicitly_includes_it() -> None:
    collect = descriptor("plugin.collect", "workspace.path", "artifact.metadata")
    sign = descriptor("plugin.sign", "artifact.metadata", "artifact.signature")
    catalog = candidate(collect, sign)
    allowed = build_candidate_planning_surface(
        candidate=catalog,
        visibility=visibility(catalog, collect.capability_ref),
    )
    assert {option.operation for option in allowed.options} == {"plugin.collect"}
    assert not find_structural_plan_candidates(
        allowed,
        desired_output_semantic_type="artifact.signature",
        available_input_semantic_types=("workspace.path",),
    )
    denied = build_candidate_planning_surface(
        candidate=catalog, visibility=visibility(catalog)
    )
    assert denied.options == ()
    assert denied.dependency_hints == ()


def test_catalog_change_invalidates_previous_host_policy_evidence() -> None:
    first_operation = descriptor("plugin.first", "workspace.path", "artifact.metadata")
    later_operation = descriptor("plugin.later", "artifact.metadata", "artifact.report")
    first = candidate(first_operation)
    evidence = visibility(first, first_operation.capability_ref)
    upgraded = candidate(first_operation, later_operation)
    with pytest.raises(CapabilityPlanningSurfaceError, match="stale or foreign"):
        build_candidate_planning_surface(
            candidate=upgraded, visibility=evidence
        )
    with pytest.raises(CapabilityPlanningSurfaceError, match="foreign capability"):
        build_candidate_planning_surface(
            candidate=first,
            visibility=visibility(first, later_operation.capability_ref),
        )


def test_exact_semantics_and_all_inputs_are_required() -> None:
    first = descriptor("plugin.read", "workspace.path", "artifact.metadata")
    second = descriptor("plugin.report", "artifact.metadata", "artifact.report")
    catalog = candidate(first, second)
    view = build_candidate_planning_surface(
        candidate=catalog,
        visibility=visibility(
            catalog, first.capability_ref, second.capability_ref
        ),
    )
    assert not find_structural_plan_candidates(
        view, desired_output_semantic_type="artifact.report",
        available_input_semantic_types=("workspace.paths",),
    )
    assert not find_structural_plan_candidates(
        view, desired_output_semantic_type="artifact.report",
        available_input_semantic_types=(),
    )
    assert not find_structural_plan_candidates(
        view, desired_output_semantic_type="artifact.report",
        available_input_semantic_types=("workspace.path",), max_steps=1,
    )


def test_candidate_result_is_not_workplan_or_authorization() -> None:
    first = descriptor("plugin.read", "workspace.path", "artifact.metadata")
    catalog = candidate(first)
    view = build_candidate_planning_surface(
        candidate=catalog,
        visibility=visibility(catalog, first.capability_ref),
    )
    sketch = find_structural_plan_candidates(
        view, desired_output_semantic_type="artifact.metadata",
        available_input_semantic_types=("workspace.path",),
    )[0]
    assert sketch.operations == ("plugin.read",)
    assert sketch.capability_refs == (first.capability_ref,)
    assert not hasattr(sketch, "execute")
    assert not hasattr(sketch, "work_plan")
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        sketch.execution_authorized = True  # type: ignore[misc]
    with pytest.raises(TypeError):
        replace(sketch, execution_authorized=True)


def test_no_forged_or_unbounded_visibility() -> None:
    first = descriptor("plugin.read", "workspace.path", "artifact.metadata")
    catalog = candidate(first)
    with pytest.raises(CapabilityPlanningSurfaceError, match="duplicate"):
        visibility(catalog, first.capability_ref, first.capability_ref)
    with pytest.raises(CapabilityPlanningSurfaceError, match="exact Host visibility"):
        build_candidate_planning_surface(
            candidate=catalog, visibility=None  # type: ignore[arg-type]
        )
    with pytest.raises(CapabilityPlanningSurfaceError, match="invalid bounded"):
        view = build_candidate_planning_surface(
            candidate=catalog,
            visibility=visibility(catalog, first.capability_ref),
        )
        find_structural_plan_candidates(
            view,
            desired_output_semantic_type="artifact.metadata",
            available_input_semantic_types=("workspace.path",),
            max_steps=4,
        )
