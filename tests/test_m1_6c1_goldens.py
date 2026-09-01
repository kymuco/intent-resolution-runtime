from __future__ import annotations

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    ProposedWorkStep,
    RecordIdentity,
    StableRef,
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


def _fixture() -> tuple[
    CapabilityMatchEvaluation,
    WorkProposalAttribution,
    ProposedWorkStep,
    WorkProposalMaterial,
    WorkProposal,
]:
    plan_ref = _ref("irr.work_plan", "inspect-001")
    step_ref = _ref("irr.work_step", "inspect")
    completion = "Return the bounded workspace inspection result."
    step = WorkStep(
        RESOLVED,
        plan_ref,
        step_ref,
        "workspace.inspect",
        "workspace:project",
        (),
        (),
        (),
        WorkContinuationMode.NONE,
        completion,
        "Inspect one bounded workspace.",
    )
    plan = WorkPlan(
        RESOLVED,
        plan_ref,
        (step,),
        "Complete the bounded inspection plan.",
        "Inspection plan.",
    )
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "workspace"),
        "filesystem.path_scope",
        "workspace:project",
        "Bounded workspace scope.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        requested_scope.scope_ref,
        (requested_scope,),
        (),
        (),
        "Exact inspection capability requirement.",
    )
    descriptor_scope = CapabilityScopeRequirement(
        _ref(
            "irr.capability_scope_requirement",
            "workspace-workspace.inspect.local",
        ),
        "filesystem.path_scope",
        "Invocation must remain inside one bounded workspace.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "workspace.inspect.local"),
        "workspace.inspect",
        (),
        (),
        (descriptor_scope,),
        (),
        (),
        completion,
        "Bounded workspace inspection capability workspace.inspect.local.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "proposal-test"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", "catalog-proposal-001"),
        ),
        "Exact bounded proposal planning surface.",
        (descriptor,),
        "Capability proposal test snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "exact-v1"),
            _ref("irr.event", "match-proposal-001"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityScopeMatch(
                requested_scope.scope_ref,
                descriptor_scope.requirement_ref,
            ),
        ),
        (),
        (),
        (),
        "Exact match for workspace.inspect.local.",
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", "evaluation-proposal-001"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for Governance proposal materialization.",
    )
    proposal_attribution = WorkProposalAttribution(
        _ref("irr.proposer", "irr-core"),
        _ref("irr.event", "proposal-001"),
    )
    proposed_step = ProposedWorkStep(step_ref, evaluation)
    material = WorkProposalMaterial(
        _ref("irr.work_proposal_material", "resource"),
        WorkProposalMaterialKind.AFFECTED_RESOURCE,
        (step_ref,),
        _ref("irr.source", "proposal-admission"),
        SOURCE_ID,
        "workspace:project",
        "The bounded workspace is authority-relevant affected-resource material.",
    )
    proposal = WorkProposal(
        proposal_attribution,
        plan,
        (proposed_step,),
        (material,),
        "Bounded inspection work proposed to external Governance.",
    )
    return evaluation, proposal_attribution, proposed_step, material, proposal


def test_m16c1_work_proposal_golden_digests_are_frozen() -> None:
    evaluation, attribution, proposed_step, material, proposal = _fixture()
    expected = {
        "evaluation": "6f4f32354356086edfb180b1df7b4953be3d2b1b5dd4628e7db61fd191bcda8c",
        "attribution": "cdcb65f9c3f12c3bf22726167c6874b7a90dad0d7de1463bc2d7bdc60dfcd1c0",
        "proposed_step": "8d4bdb1087bf4264c0690a4a5642df15d817ed53ff7fab1d645e2e74e070439e",
        "material": "33aa2f789fe55a19fbc4fded1a217927430e04b071517ab27b6852d9acb76ff1",
        "proposal": "6681affd3bd666e63d34a609f4750755232167f5e5a8f1d724cffaeafb4a395a",
    }
    actual = {
        "evaluation": evaluation.identity.digest,
        "attribution": attribution.identity.digest,
        "proposed_step": proposed_step.identity.digest,
        "material": material.identity.digest,
        "proposal": proposal.identity.digest,
    }
    assert actual == expected


def test_m16c1_work_proposal_golden_round_trip_preserves_identity() -> None:
    _, attribution, proposed_step, material, proposal = _fixture()
    decoded_attribution = WorkProposalAttribution.from_json_bytes(
        attribution.canonical_bytes()
    )
    decoded_step = ProposedWorkStep.from_json_bytes(proposed_step.canonical_bytes())
    decoded_material = WorkProposalMaterial.from_json_bytes(material.canonical_bytes())
    decoded_proposal = WorkProposal.from_json_bytes(proposal.canonical_bytes())

    assert decoded_attribution == attribution
    assert decoded_attribution.identity == attribution.identity
    assert decoded_step == proposed_step
    assert decoded_step.identity == proposed_step.identity
    assert decoded_material == material
    assert decoded_material.identity == material.identity
    assert decoded_proposal == proposal
    assert decoded_proposal.identity == proposal.identity
