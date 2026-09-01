from __future__ import annotations

from intent_resolution_runtime import (
    BindingAttribution,
    BindingAttributeKind,
    BindingInputRole,
    BindingIssue,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
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
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    GovernanceContinuationMaterial,
    GovernanceDecision,
    GovernanceDecisionAttribution,
    GovernanceDecisionComponent,
    GovernanceDecisionKind,
    GovernanceDirective,
    InterchangeableChoicePolicy,
    ProposedWorkStep,
    RecordIdentity,
    StableRef,
    SymbolicReference,
    WorkContinuationMode,
    WorkPlan,
    WorkProposal,
    WorkProposalAttribution,
    WorkProposalMaterial,
    WorkProposalMaterialKind,
    WorkStep,
    evaluate_binding,
)


BINDING_RESOLVED = RecordIdentity("sha256", "1" * 64)
BINDING_SOURCE = RecordIdentity("sha256", "2" * 64)
BINDING_TEMPORAL = RecordIdentity("sha256", "3" * 64)
BINDING_COMPLETE = RecordIdentity("sha256", "4" * 64)
BINDING_EVIDENCE = RecordIdentity("sha256", "5" * 64)
BINDING_SCOPE = r"D:\Backups"

GOV_RESOLVED = RecordIdentity("sha256", "3" * 64)
GOV_SOURCE = RecordIdentity("sha256", "4" * 64)
GOV_AUTHORITY = RecordIdentity("sha256", "5" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _binding_issue_fixture() -> BindingIssue:
    symbolic = SymbolicReference(
        BINDING_RESOLVED,
        _ref("irr.slot", "selected-backup"),
        "artifact.path",
        BINDING_SCOPE,
        "Newest organism_lab backup selected by admitted modification time.",
    )
    rule = BindingRule(
        BINDING_RESOLVED,
        _ref("irr.binding_rule", "latest-backup"),
        symbolic,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (_ref("host.source", "filesystem-search"),),
        (BINDING_SOURCE,),
        "artifact.path",
        BINDING_SCOPE,
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.MAX_ATTRIBUTE,
            ("modification_time",),
            (BindingAttributeKind.RFC3339_TIMESTAMP,),
            InterchangeableChoicePolicy.NONE,
        ),
        "Select the unique newest compatible backup by modification_time.",
        (BINDING_TEMPORAL,),
        (BINDING_COMPLETE,),
        (BINDING_EVIDENCE,),
    )
    issue = evaluate_binding(
        rule,
        (),
        attribution=BindingAttribution(
            _ref("irr.evaluator", "mechanical-binding-v1"),
            _ref("irr.event", "bind-001"),
        ),
    )
    assert type(issue) is BindingIssue
    assert issue.identity.digest == (
        "ba6fe8fb6071a8eec52e5893a37faf6967d2f00df894ac1d2a55471180e76b5e"
    )
    return issue


def _governance_proposal() -> WorkProposal:
    plan_ref = _ref("irr.work_plan", "inspect-001")
    step_ref = _ref("irr.work_step", "inspect")
    completion = "Return the bounded workspace inspection result."
    step = WorkStep(
        GOV_RESOLVED,
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
        GOV_RESOLVED,
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
        _ref("irr.capability_scope_requirement", "workspace-workspace.inspect.local"),
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
    material = WorkProposalMaterial(
        _ref("irr.work_proposal_material", "resource"),
        WorkProposalMaterialKind.AFFECTED_RESOURCE,
        (step_ref,),
        _ref("irr.source", "proposal-admission"),
        GOV_SOURCE,
        "workspace:project",
        "The bounded workspace is authority-relevant affected-resource material.",
    )
    proposal = WorkProposal(
        WorkProposalAttribution(
            _ref("irr.proposer", "irr-core"),
            _ref("irr.event", "proposal-001"),
        ),
        plan,
        (ProposedWorkStep(step_ref, evaluation),),
        (material,),
        "Bounded inspection work proposed to external Governance.",
    )
    assert proposal.identity.digest == (
        "6681affd3bd666e63d34a609f4750755232167f5e5a8f1d724cffaeafb4a395a"
    )
    return proposal


def _governance_material() -> GovernanceContinuationMaterial:
    proposal = _governance_proposal()
    directive = GovernanceDirective(
        _ref("irr.governance_directive", "read-only"),
        "governance.constraint",
        "workspace:project",
        "Preserve the exact workspace operation as read-only successor semantics.",
    )
    component = GovernanceDecisionComponent(
        _ref("irr.governance_component", "constrain-inspect"),
        GovernanceDecisionKind.CONSTRAIN,
        (proposal.proposed_steps[0].step_ref,),
        (directive,),
        "Governance requires constrained successor semantics for the exact proposed inspection step.",
    )
    decision = GovernanceDecision(
        GovernanceDecisionAttribution(
            _ref("irr.governance", "host-policy"),
            _ref("irr.event", "decision-continuation-golden-001"),
            _ref("irr.authority_context", "session-001"),
            GOV_AUTHORITY,
        ),
        proposal,
        (component,),
        "External Governance constrained the exact proposed step.",
    )
    return GovernanceContinuationMaterial(decision, component.component_ref)


def test_m17b1_continuation_input_golden_digests_are_frozen() -> None:
    issue = _binding_issue_fixture()
    attribution = ContinuationInputAttribution(
        _ref("irr.host", "continuation-test"),
        _ref("irr.event", "reentry-binding_issue-001"),
    )
    continuation = ContinuationInput(
        attribution,
        ContinuationSourceKind.BINDING_ISSUE,
        issue,
    )

    governance_material = _governance_material()
    governance_attribution = ContinuationInputAttribution(
        _ref("irr.host", "continuation-test"),
        _ref("irr.event", "reentry-governance_constraint-001"),
    )
    governance_continuation = ContinuationInput(
        governance_attribution,
        ContinuationSourceKind.GOVERNANCE_CONSTRAINT,
        governance_material,
    )

    assert attribution.identity.digest == (
        "8289bbeca3f1c51d5342816e59ac90c79855495c0d037705b2c4d8cda9d54d42"
    )
    assert continuation.identity.digest == (
        "d0de995d43773d95801f591054edc5e28c4296d081251fd3e676dbbfc8a8f734"
    )
    assert governance_material.identity.digest == (
        "4f013a879a41d88144852b72f69751f57d5f3a56f390262173ea35cba85079a3"
    )
    assert governance_attribution.identity.digest == (
        "cfce8e348abf6369701be31e228b51983008f1add4606160865ca1786dbdfc16"
    )
    assert governance_continuation.identity.digest == (
        "2d2647a6adc15c22cdccd6f6d4428378b4a20569f6d7f4e65f6844e6afd7c598"
    )


def test_m17b1_continuation_goldens_round_trip_and_preserve_source_identity() -> None:
    issue = _binding_issue_fixture()
    continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "continuation-test"),
            _ref("irr.event", "reentry-binding_issue-001"),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        issue,
    )
    governance_material = _governance_material()
    governance_continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "continuation-test"),
            _ref("irr.event", "reentry-governance_constraint-001"),
        ),
        ContinuationSourceKind.GOVERNANCE_CONSTRAINT,
        governance_material,
    )

    decoded = ContinuationInput.from_json_bytes(continuation.canonical_bytes())
    decoded_governance_material = GovernanceContinuationMaterial.from_json_bytes(
        governance_material.canonical_bytes()
    )
    decoded_governance = ContinuationInput.from_json_bytes(
        governance_continuation.canonical_bytes()
    )

    assert decoded == continuation
    assert decoded.identity == continuation.identity
    assert decoded.source_identity == issue.identity
    assert decoded_governance_material == governance_material
    assert decoded_governance_material.identity == governance_material.identity
    assert decoded_governance == governance_continuation
    assert decoded_governance.identity == governance_continuation.identity
    assert decoded_governance.source_identity == governance_material.identity
