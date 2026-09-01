from __future__ import annotations

from dataclasses import replace

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityIncompatibleDescriptorAssessment,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityMatchIssue,
    CapabilityMatchIssueKind,
    CapabilityMismatchKind,
    CapabilityMismatchReason,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeRequirement,
    RecordIdentity,
    StableRef,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
)


RESOLVED = RecordIdentity("sha256", "2" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> tuple[
    CapabilityRequirement,
    CapabilityDescriptor,
    CapabilityCatalogSnapshot,
    CapabilityMatchEvaluationAttribution,
    CapabilityMismatchReason,
    CapabilityIncompatibleDescriptorAssessment,
    CapabilityMatchEvaluation,
    CapabilityMatchIssue,
]:
    plan_ref = _ref("irr.work_plan", "inspect-001")
    step_ref = _ref("irr.work_step", "inspect")
    completion = "Return the bounded workspace inspection result."
    step = WorkStep(
        resolved_intent_identity=RESOLVED,
        work_plan_ref=plan_ref,
        step_ref=step_ref,
        operation="workspace.inspect",
        scope="workspace:project",
        inputs=(),
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract=completion,
        description="Inspect one bounded workspace.",
    )
    plan = WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="Complete the bounded inspection plan.",
        description="One-step inspection plan.",
    )
    requested_scope = CapabilityRequestedScope(
        scope_ref=_ref("irr.capability_requested_scope", "workspace"),
        semantic_type="filesystem.path_scope",
        value="workspace:project",
        description="Bounded workspace scope.",
    )
    requirement = CapabilityRequirement(
        work_plan=plan,
        step_ref=step_ref,
        primary_scope_ref=requested_scope.scope_ref,
        requested_scopes=(requested_scope,),
        requested_effects=(),
        execution_boundary_requirements=(),
        description="Exact inspection capability requirement.",
    )

    descriptor_scope = CapabilityScopeRequirement(
        requirement_ref=_ref(
            "irr.capability_scope_requirement",
            "workspace-workspace.inspect.remote",
        ),
        semantic_type="filesystem.path_scope",
        statement="Invocation must remain inside one bounded workspace.",
    )
    descriptor = CapabilityDescriptor(
        capability_ref=_ref("irr.capability", "workspace.inspect.remote"),
        operation="workspace.inspect",
        input_contracts=(),
        output_contracts=(),
        scope_requirements=(descriptor_scope,),
        effects=(),
        execution_boundaries=(),
        completion_contract=completion,
        description=(
            "Bounded workspace inspection capability workspace.inspect.remote."
        ),
    )
    descriptor = replace(descriptor, operation="workspace.scan")
    snapshot = CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", "evaluation-test"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=_ref("irr.host", "test-host"),
            snapshot_event_ref=_ref("irr.event", "catalog-evaluation-001"),
        ),
        scope_statement="Exact bounded test planning surface.",
        descriptors=(descriptor,),
        description="Capability evaluation test snapshot.",
    )

    attribution = CapabilityMatchEvaluationAttribution(
        evaluator_ref=_ref("irr.evaluator", "capability-evaluation-v1"),
        evaluation_event_ref=_ref("irr.event", "evaluation-001"),
    )
    reason = CapabilityMismatchReason(
        kind=CapabilityMismatchKind.OPERATION_MISMATCH,
        scope="descriptor:workspace.inspect.remote",
        description=(
            "Descriptor operation differs from the selected WorkStep operation."
        ),
    )
    assessment = CapabilityIncompatibleDescriptorAssessment(
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        reasons=(reason,),
    )
    evaluation = CapabilityMatchEvaluation(
        attribution=attribution,
        requirement=requirement,
        catalog_snapshot=snapshot,
        compatible_matches=(),
        incompatible_assessments=(assessment,),
        description="Exhaustive assessment of the exact supplied Catalog Snapshot.",
    )
    issue = CapabilityMatchIssue(
        evaluation=evaluation,
        kind=CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY,
    )
    return (
        requirement,
        descriptor,
        snapshot,
        attribution,
        reason,
        assessment,
        evaluation,
        issue,
    )


def test_m16b2_capability_evaluation_golden_digests_are_frozen() -> None:
    (
        requirement,
        descriptor,
        snapshot,
        attribution,
        reason,
        assessment,
        evaluation,
        issue,
    ) = _fixture()

    expected = {
        "requirement": "382b30cd9e79e0edbb6025bd942407d14256f96af5debfd83bef4483d5769847",
        "descriptor": "468be096ac462b65668fbb276a1d9b86c1ac5c3ca79b8aca3e3c609d447b788f",
        "snapshot": "17a200e9757367126ce5125ea0a1f21659385031b9d13ba4eaebbd959d3e3b00",
        "attribution": "fb00afff42f07711f5574868e59f069485051c9662ccce1e964f0ec6187e9628",
        "reason": "74c1ee7b9f4e3f406841dd41c90a4ad287e6e95a17cac5c3b2432bee33977902",
        "assessment": "6556dd3eda622d811f22a28ded1c6f533816ae845c8b7b52e2a6aa642fd62efe",
        "evaluation": "618042cfc221eabcef59a2f997955358111c07ea2f389b3675e35ac22d7a465b",
        "issue": "70254c8fbdff288ca9c5a124e666bf374dac0289b1dc8d64cb0da66e0412994f",
    }
    actual = {
        "requirement": requirement.identity.digest,
        "descriptor": descriptor.identity.digest,
        "snapshot": snapshot.identity.digest,
        "attribution": attribution.identity.digest,
        "reason": reason.identity.digest,
        "assessment": assessment.identity.digest,
        "evaluation": evaluation.identity.digest,
        "issue": issue.identity.digest,
    }
    assert actual == expected


def test_m16b2_golden_evaluation_and_issue_round_trip_preserve_identity() -> None:
    *_, evaluation, issue = _fixture()

    decoded_evaluation = CapabilityMatchEvaluation.from_json_bytes(
        evaluation.canonical_bytes()
    )
    decoded_issue = CapabilityMatchIssue.from_json_bytes(issue.canonical_bytes())

    assert decoded_evaluation == evaluation
    assert decoded_evaluation.identity == evaluation.identity
    assert decoded_issue == issue
    assert decoded_issue.identity == issue.identity
