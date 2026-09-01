from __future__ import annotations

from intent_resolution_runtime import (
    AttemptBoundInput,
    BindingAttribution,
    BindingAttribute,
    BindingAttributeKind,
    BindingInput,
    BindingInputRole,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    BoundValue,
    CapabilityAttempt,
    CapabilityAttemptAttribution,
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
    InterchangeableChoicePolicy,
    RecordIdentity,
    SourceAttribution,
    StableRef,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
    evaluate_binding,
)


RESOLVED = RecordIdentity("sha256", "3" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _evaluation_fixture() -> CapabilityMatchEvaluation:
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
    return CapabilityMatchEvaluation(
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


def _bound_value_fixture() -> BoundValue:
    resolved = RecordIdentity("sha256", "1" * 64)
    source = RecordIdentity("sha256", "2" * 64)
    temporal = RecordIdentity("sha256", "3" * 64)
    complete = RecordIdentity("sha256", "4" * 64)
    evidence = RecordIdentity("sha256", "5" * 64)
    selection_scope = r"D:\Backups"
    source_ref = _ref("host.source", "filesystem-search")

    from intent_resolution_runtime import SymbolicReference

    symbolic = SymbolicReference(
        resolved,
        _ref("irr.slot", "selected-backup"),
        "artifact.path",
        selection_scope,
        "Newest organism_lab backup selected by admitted modification time.",
    )

    def binding_input(name: str, timestamp: str) -> BindingInput:
        value = rf"D:\Backups\{name}"
        return BindingInput(
            resolved,
            _ref("irr.binding_input", name),
            SourceAttribution(
                source_ref,
                _ref("host.event", f"search-{name}"),
            ),
            BindingInputRole.PLAN_LOCAL_OUTPUT,
            source,
            "artifact.path",
            value,
            selection_scope,
            value,
            (
                BindingAttribute(
                    "modification_time",
                    BindingAttributeKind.RFC3339_TIMESTAMP,
                    timestamp,
                ),
                BindingAttribute("name", BindingAttributeKind.TEXT, name),
            ),
            (temporal,),
            (complete,),
            (evidence,),
        )

    older = binding_input("backup-a.zip", "2026-08-30T10:00:00+06:00")
    newer = binding_input("backup-b.zip", "2026-08-30T12:00:00+06:00")
    rule = BindingRule(
        resolved,
        _ref("irr.binding_rule", "latest-backup"),
        symbolic,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (source_ref,),
        (source,),
        "artifact.path",
        selection_scope,
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.MAX_ATTRIBUTE,
            ("modification_time",),
            (BindingAttributeKind.RFC3339_TIMESTAMP,),
            InterchangeableChoicePolicy.NONE,
        ),
        "Select the unique newest compatible backup by modification_time.",
        (temporal,),
        (complete,),
        (evidence,),
    )
    result = evaluate_binding(
        rule,
        (newer, older),
        attribution=BindingAttribution(
            _ref("irr.evaluator", "mechanical-binding-v1"),
            _ref("irr.event", "bind-001"),
        ),
    )
    assert type(result) is BoundValue
    return result


def test_m17a1_capability_attempt_golden_digests_are_frozen() -> None:
    evaluation = _evaluation_fixture()
    assert evaluation.identity.digest == (
        "6f4f32354356086edfb180b1df7b4953be3d2b1b5dd4628e7db61fd191bcda8c"
    )

    attribution = CapabilityAttemptAttribution(
        _ref("irr.executor", "workspace-local"),
        _ref("irr.event", "attempt-golden-001"),
    )
    attempt = CapabilityAttempt(
        attribution,
        evaluation,
        evaluation.requirement.step_ref,
        (),
        (),
        "One attributable authority-neutral workspace inspection attempt.",
    )
    bound_input = AttemptBoundInput("backup", _bound_value_fixture())

    assert attribution.identity.digest == (
        "2121fb4d58c87d7ce26be69754834d5e680944262203d25f6f2148a15b4845f7"
    )
    assert bound_input.identity.digest == (
        "b9870c90c3720c8ccd8ef8b0c1801be1d53ee5d31fa779e19791b3d811b8da1b"
    )
    assert attempt.identity.digest == (
        "4a17dde3375b8ea4facc90a011bb161f0033e4245c28632a6fa5128eb3e54f4c"
    )


def test_m17a1_capability_attempt_goldens_round_trip() -> None:
    evaluation = _evaluation_fixture()
    attribution = CapabilityAttemptAttribution(
        _ref("irr.executor", "workspace-local"),
        _ref("irr.event", "attempt-golden-001"),
    )
    attempt = CapabilityAttempt(
        attribution,
        evaluation,
        evaluation.requirement.step_ref,
        (),
        (),
        "One attributable authority-neutral workspace inspection attempt.",
    )
    bound_input = AttemptBoundInput("backup", _bound_value_fixture())

    decoded_attribution = CapabilityAttemptAttribution.from_json_bytes(
        attribution.canonical_bytes()
    )
    decoded_bound = AttemptBoundInput.from_json_bytes(bound_input.canonical_bytes())
    decoded_attempt = CapabilityAttempt.from_json_bytes(attempt.canonical_bytes())

    assert decoded_attribution == attribution
    assert decoded_attribution.identity == attribution.identity
    assert decoded_bound == bound_input
    assert decoded_bound.identity == bound_input.identity
    assert decoded_attempt == attempt
    assert decoded_attempt.identity == attempt.identity
