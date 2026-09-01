from __future__ import annotations

from dataclasses import replace
import json

import pytest

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityIncompatibleDescriptorAssessment,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityMismatchKind,
    CapabilityMismatchReason,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    ProposedWorkStep,
    RecordIdentity,
    SerializationError,
    StableRef,
    ValidationError,
    WorkContinuationMode,
    WorkPlan,
    WorkProposal,
    WorkProposalAttribution,
    WorkProposalMaterial,
    WorkProposalMaterialKind,
    WorkStep,
)


RESOLVED = RecordIdentity("sha256", "3" * 64)
SOURCE_ID = RecordIdentity("sha256", "4" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _plan(*, suffix: str = "001", description: str = "Inspection plan.") -> WorkPlan:
    plan_ref = _ref("irr.work_plan", f"inspect-{suffix}")
    step = WorkStep(
        resolved_intent_identity=RESOLVED,
        work_plan_ref=plan_ref,
        step_ref=_ref("irr.work_step", "inspect"),
        operation="workspace.inspect",
        scope="workspace:project",
        inputs=(),
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
        description=description,
    )


def _requirement(plan: WorkPlan) -> CapabilityRequirement:
    scope = CapabilityRequestedScope(
        scope_ref=_ref("irr.capability_requested_scope", "workspace"),
        semantic_type="filesystem.path_scope",
        value="workspace:project",
        description="Bounded workspace scope.",
    )
    return CapabilityRequirement(
        work_plan=plan,
        step_ref=_ref("irr.work_step", "inspect"),
        primary_scope_ref=scope.scope_ref,
        requested_scopes=(scope,),
        requested_effects=(),
        execution_boundary_requirements=(),
        description="Exact inspection capability requirement.",
    )


def _descriptor(name: str, *, operation: str = "workspace.inspect") -> CapabilityDescriptor:
    scope = CapabilityScopeRequirement(
        requirement_ref=_ref("irr.capability_scope_requirement", f"workspace-{name}"),
        semantic_type="filesystem.path_scope",
        statement="Invocation must remain inside one bounded workspace.",
    )
    return CapabilityDescriptor(
        capability_ref=_ref("irr.capability", name),
        operation=operation,
        input_contracts=(),
        output_contracts=(),
        scope_requirements=(scope,),
        effects=(),
        execution_boundaries=(),
        completion_contract="Return the bounded workspace inspection result.",
        description=f"Bounded workspace inspection capability {name}.",
    )


def _snapshot(
    *descriptors: CapabilityDescriptor,
    event: str = "catalog-proposal-001",
) -> CapabilityCatalogSnapshot:
    return CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", "proposal-test"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=_ref("irr.host", "test-host"),
            snapshot_event_ref=_ref("irr.event", event),
        ),
        scope_statement="Exact bounded proposal planning surface.",
        descriptors=tuple(descriptors),
        description="Capability proposal test snapshot.",
    )


def _match(
    requirement: CapabilityRequirement,
    snapshot: CapabilityCatalogSnapshot,
    descriptor: CapabilityDescriptor,
    event: str,
) -> CapabilityMatch:
    return CapabilityMatch(
        attribution=CapabilityMatchAttribution(
            matcher_ref=_ref("irr.matcher", "exact-v1"),
            match_event_ref=_ref("irr.event", event),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        scope_matches=(
            CapabilityScopeMatch(
                requested_scope_ref=requirement.requested_scopes[0].scope_ref,
                descriptor_scope_requirement_ref=descriptor.scope_requirements[0].requirement_ref,
            ),
        ),
        input_matches=(),
        output_matches=(),
        effect_matches=(),
        description=f"Exact match for {descriptor.capability_ref.value}.",
    )


def _incompatible(descriptor: CapabilityDescriptor) -> CapabilityIncompatibleDescriptorAssessment:
    return CapabilityIncompatibleDescriptorAssessment(
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        reasons=(
            CapabilityMismatchReason(
                kind=CapabilityMismatchKind.OPERATION_MISMATCH,
                scope=f"descriptor:{descriptor.capability_ref.value}",
                description="Descriptor operation differs from selected WorkStep operation.",
            ),
        ),
    )


def _evaluation(
    requirement: CapabilityRequirement,
    snapshot: CapabilityCatalogSnapshot,
    *,
    matches: tuple[CapabilityMatch, ...],
    incompatible: tuple[CapabilityIncompatibleDescriptorAssessment, ...] = (),
    event: str = "evaluation-proposal-001",
) -> CapabilityMatchEvaluation:
    return CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            evaluator_ref=_ref("irr.evaluator", "capability-evaluation-v1"),
            evaluation_event_ref=_ref("irr.event", event),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        compatible_matches=matches,
        incompatible_assessments=incompatible,
        description="Exhaustive exact Catalog evaluation for Governance proposal materialization.",
    )


def _unique_evaluation(plan: WorkPlan | None = None) -> CapabilityMatchEvaluation:
    plan = _plan() if plan is None else plan
    requirement = _requirement(plan)
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(descriptor)
    match = _match(requirement, snapshot, descriptor, "match-proposal-001")
    return _evaluation(requirement, snapshot, matches=(match,))


def _material(
    *,
    ref: str = "resource",
    kind: WorkProposalMaterialKind = WorkProposalMaterialKind.AFFECTED_RESOURCE,
    step_ref: StableRef | None = None,
    source_identity: RecordIdentity = SOURCE_ID,
) -> WorkProposalMaterial:
    return WorkProposalMaterial(
        material_ref=_ref("irr.work_proposal_material", ref),
        kind=kind,
        step_refs=((_ref("irr.work_step", "inspect") if step_ref is None else step_ref),),
        source_ref=_ref("irr.source", "proposal-admission"),
        source_identity=source_identity,
        scope="workspace:project",
        statement="The bounded workspace is authority-relevant affected-resource material.",
    )


def _proposal(
    *,
    plan: WorkPlan | None = None,
    evaluation: CapabilityMatchEvaluation | None = None,
    material: tuple[WorkProposalMaterial, ...] = (),
    event: str = "proposal-001",
) -> WorkProposal:
    plan = _plan() if plan is None else plan
    evaluation = _unique_evaluation(plan) if evaluation is None else evaluation
    return WorkProposal(
        attribution=WorkProposalAttribution(
            proposer_ref=_ref("irr.proposer", "irr-core"),
            proposal_event_ref=_ref("irr.event", event),
        ),
        work_plan=plan,
        proposed_steps=(
            ProposedWorkStep(
                step_ref=_ref("irr.work_step", "inspect"),
                capability_evaluation=evaluation,
            ),
        ),
        authority_material=material,
        description="Bounded inspection work proposed to external Governance.",
    )


def test_work_proposal_round_trip_preserves_exact_identity() -> None:
    proposal = _proposal(material=(_material(),))
    decoded = WorkProposal.from_json_bytes(proposal.canonical_bytes())
    assert decoded == proposal
    assert decoded.identity == proposal.identity
    assert decoded.proposed_steps[0].capability_match == (
        decoded.proposed_steps[0].capability_evaluation.compatible_matches[0]
    )


def test_proposed_work_step_requires_exactly_one_admitted_match() -> None:
    plan = _plan()
    requirement = _requirement(plan)

    empty_snapshot = _snapshot()
    no_match = _evaluation(requirement, empty_snapshot, matches=())
    with pytest.raises(ValidationError):
        ProposedWorkStep(_ref("irr.work_step", "inspect"), no_match)

    first = _descriptor("workspace.inspect.a")
    second = _descriptor("workspace.inspect.b")
    snapshot = _snapshot(first, second)
    multiple = _evaluation(
        requirement,
        snapshot,
        matches=(
            _match(requirement, snapshot, first, "match-a"),
            _match(requirement, snapshot, second, "match-b"),
        ),
    )
    with pytest.raises(ValidationError):
        ProposedWorkStep(_ref("irr.work_step", "inspect"), multiple)


def test_work_proposal_cannot_bypass_b2_with_wrong_exact_work_plan() -> None:
    admitted = _plan(description="Admitted plan.")
    other = _plan(description="Materially different exact plan bytes.")
    evaluation = _unique_evaluation(other)
    with pytest.raises(ValidationError):
        _proposal(plan=admitted, evaluation=evaluation)


def test_proposed_work_step_must_match_selected_step_ref() -> None:
    evaluation = _unique_evaluation()
    with pytest.raises(ValidationError):
        ProposedWorkStep(_ref("irr.work_step", "other"), evaluation)


def test_authority_material_may_reference_only_proposed_steps() -> None:
    with pytest.raises(ValidationError):
        _proposal(material=(_material(step_ref=_ref("irr.work_step", "other")),))


def test_authority_material_has_stable_set_order_and_unique_refs() -> None:
    first = _material(ref="a")
    second = _material(ref="b", kind=WorkProposalMaterialKind.UNCERTAINTY)
    left = _proposal(material=(second, first))
    right = _proposal(material=(first, second))
    assert left.identity == right.identity
    assert [item.material_ref.value for item in left.authority_material] == ["a", "b"]

    with pytest.raises(ValidationError):
        _proposal(material=(first, replace(first, statement="Different statement.")))


def test_material_source_identity_is_identity_covered_not_truth_amplification() -> None:
    first = _proposal(material=(_material(),))
    second = _proposal(
        material=(_material(source_identity=RecordIdentity("sha256", "5" * 64)),)
    )
    assert first.identity != second.identity


def test_empty_extra_authority_material_is_valid_for_exact_semantics_already_in_ir() -> None:
    proposal = _proposal(material=())
    assert proposal.authority_material == ()
    assert proposal.proposed_steps[0].capability_match.capability_ref.value == (
        "workspace.inspect.local"
    )


def test_proposal_occurrence_is_identity_covered_without_changing_work_plan() -> None:
    plan = _plan()
    evaluation = _unique_evaluation(plan)
    first = _proposal(plan=plan, evaluation=evaluation, event="proposal-a")
    second = _proposal(plan=plan, evaluation=evaluation, event="proposal-b")
    assert first.work_plan == second.work_plan == plan
    assert first.identity != second.identity


def test_unknown_authority_like_fields_fail_closed() -> None:
    proposal = _proposal()
    primitive = proposal.to_primitive()
    primitive["approved"] = "true"
    with pytest.raises(SerializationError):
        WorkProposal.from_json_bytes(
            json.dumps(primitive, separators=(",", ":"), sort_keys=True).encode()
        )


def test_unknown_material_kind_fails_closed() -> None:
    primitive = _material().to_primitive()
    primitive["kind"] = "authorization"
    with pytest.raises(SerializationError):
        WorkProposalMaterial.from_json_bytes(
            json.dumps(primitive, separators=(",", ":"), sort_keys=True).encode()
        )


def test_material_step_refs_are_canonical_and_nonempty() -> None:
    inspect = _ref("irr.work_step", "inspect")
    other = _ref("irr.work_step", "other")
    item = WorkProposalMaterial(
        material_ref=_ref("irr.work_proposal_material", "flow"),
        kind=WorkProposalMaterialKind.DATA_FLOW,
        step_refs=(other, inspect),
        source_ref=_ref("irr.source", "proposal-admission"),
        source_identity=SOURCE_ID,
        scope="workspace:project",
        statement="Bounded data flow material.",
    )
    assert item.step_refs == (inspect, other)
    with pytest.raises(ValidationError):
        replace(item, step_refs=())


def test_proposal_rejects_multiple_capability_relations_for_same_step() -> None:
    evaluation = _unique_evaluation()
    proposed = ProposedWorkStep(_ref("irr.work_step", "inspect"), evaluation)
    with pytest.raises(ValidationError):
        WorkProposal(
            attribution=WorkProposalAttribution(
                _ref("irr.proposer", "irr-core"), _ref("irr.event", "proposal-dup")
            ),
            work_plan=evaluation.requirement.work_plan,
            proposed_steps=(proposed, proposed),
            authority_material=(),
            description="Duplicate proposal relation should fail.",
        )


def test_proposal_rejects_mixed_catalog_snapshot_occurrences_across_steps() -> None:
    plan_ref = _ref("irr.work_plan", "inspect-two-step")
    first_ref = _ref("irr.work_step", "inspect-a")
    second_ref = _ref("irr.work_step", "inspect-b")
    completion = "Return the bounded workspace inspection result."
    first_step = WorkStep(
        RESOLVED, plan_ref, first_ref, "workspace.inspect", "workspace:project",
        (), (), (), WorkContinuationMode.NONE, completion, "Inspect bounded workspace A."
    )
    second_step = WorkStep(
        RESOLVED, plan_ref, second_ref, "workspace.inspect", "workspace:project",
        (), (), (), WorkContinuationMode.NONE, completion, "Inspect bounded workspace B."
    )
    plan = WorkPlan(
        RESOLVED, plan_ref, (second_step, first_step),
        "Complete both bounded inspections.", "Two-step inspection plan."
    )
    scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "workspace"),
        "filesystem.path_scope", "workspace:project", "Bounded workspace scope."
    )
    first_requirement = CapabilityRequirement(
        plan, first_ref, scope.scope_ref, (scope,), (), (), "Requirement A."
    )
    second_requirement = CapabilityRequirement(
        plan, second_ref, scope.scope_ref, (scope,), (), (), "Requirement B."
    )
    descriptor = _descriptor("workspace.inspect.shared")
    first_snapshot = _snapshot(descriptor, event="catalog-proposal-a")
    second_snapshot = _snapshot(descriptor, event="catalog-proposal-b")
    first_eval = _evaluation(
        first_requirement, first_snapshot,
        matches=(_match(first_requirement, first_snapshot, descriptor, "match-a"),),
        event="eval-a",
    )
    second_eval = _evaluation(
        second_requirement, second_snapshot,
        matches=(_match(second_requirement, second_snapshot, descriptor, "match-b"),),
        event="eval-b",
    )
    with pytest.raises(ValidationError):
        WorkProposal(
            attribution=WorkProposalAttribution(
                _ref("irr.proposer", "irr-core"), _ref("irr.event", "proposal-mixed")
            ),
            work_plan=plan,
            proposed_steps=(
                ProposedWorkStep(first_ref, first_eval),
                ProposedWorkStep(second_ref, second_eval),
            ),
            authority_material=(),
            description="Mixed Catalog occurrences must fail closed.",
        )


def test_multiple_proposed_steps_share_one_exact_catalog_and_are_canonical() -> None:
    plan_ref = _ref("irr.work_plan", "inspect-two-step-valid")
    first_ref = _ref("irr.work_step", "inspect-a")
    second_ref = _ref("irr.work_step", "inspect-b")
    completion = "Return the bounded workspace inspection result."
    first_step = WorkStep(RESOLVED, plan_ref, first_ref, "workspace.inspect", "workspace:project", (), (), (), WorkContinuationMode.NONE, completion, "Inspect A.")
    second_step = WorkStep(RESOLVED, plan_ref, second_ref, "workspace.inspect", "workspace:project", (), (), (), WorkContinuationMode.NONE, completion, "Inspect B.")
    plan = WorkPlan(RESOLVED, plan_ref, (second_step, first_step), "Complete both inspections.", "Two-step plan.")
    scope = CapabilityRequestedScope(_ref("irr.capability_requested_scope", "workspace"), "filesystem.path_scope", "workspace:project", "Bounded workspace scope.")
    first_requirement = CapabilityRequirement(plan, first_ref, scope.scope_ref, (scope,), (), (), "Requirement A.")
    second_requirement = CapabilityRequirement(plan, second_ref, scope.scope_ref, (scope,), (), (), "Requirement B.")
    descriptor = _descriptor("workspace.inspect.shared-valid")
    snapshot = _snapshot(descriptor, event="catalog-proposal-shared")
    first_eval = _evaluation(first_requirement, snapshot, matches=(_match(first_requirement, snapshot, descriptor, "match-a-valid"),), event="eval-a-valid")
    second_eval = _evaluation(second_requirement, snapshot, matches=(_match(second_requirement, snapshot, descriptor, "match-b-valid"),), event="eval-b-valid")
    first = ProposedWorkStep(first_ref, first_eval)
    second = ProposedWorkStep(second_ref, second_eval)
    left = WorkProposal(WorkProposalAttribution(_ref("irr.proposer", "irr-core"), _ref("irr.event", "proposal-shared")), plan, (second, first), (), "Shared exact Catalog proposal.")
    right = WorkProposal(left.attribution, plan, (first, second), (), left.description)
    assert left.identity == right.identity
    assert [item.step_ref.value for item in left.proposed_steps] == ["inspect-a", "inspect-b"]


def test_closed_work_proposal_types_reject_subclassing() -> None:
    with pytest.raises(TypeError):
        class InvalidProposal(WorkProposal):
            pass
