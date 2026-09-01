from __future__ import annotations

from intent_resolution_runtime import (
    BindingAttribution,
    BindingAttribute,
    BindingAttributeKind,
    BindingInput,
    BindingInputRole,
    BindingIssue,
    BindingIssueKind,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    BoundValue,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffect,
    CapabilityEffectMatch,
    CapabilityEffectRequirement,
    CapabilityIncompatibleDescriptorAssessment,
    CapabilityInputContract,
    CapabilityInputMatch,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityMatchIssue,
    CapabilityMatchIssueKind,
    CapabilityMismatchKind,
    CapabilityMismatchReason,
    CapabilityOutputContract,
    CapabilityOutputMatch,
    CapabilityRequestedEffect,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    SymbolicReference,
    WorkContinuationMode,
    WorkLiteralInput,
    WorkOutput,
    WorkPlan,
    WorkStep,
    WorkSymbolicInput,
    evaluate_binding,
    evaluate_capability_match_evaluation,
)

REQUEST_IDENTITY = RecordIdentity("sha256", "1" * 64)
CONTEXT_IDENTITY = RecordIdentity("sha256", "2" * 64)
SEARCH_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "3" * 64)
BACKUP_ROOT = r"D:\Backups"
DESTINATION = r"W:\organism_lab"

_EFFECTS = {
    "filesystem.search": ("filesystem.read",),
    "archive.inspect": ("filesystem.read",),
    "archive.extract": ("filesystem.read", "filesystem.write"),
    "workspace.inspect": ("filesystem.read",),
    "process.launch": ("process.launch",),
}


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _resolved() -> ResolvedIntent:
    return ResolvedIntent(
        REQUEST_IDENTITY,
        CONTEXT_IDENTITY,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-a"),
            _ref("irr.resolution_event", "scenario-a-resolved"),
        ),
        (
            r"Search D:\Backups for organism_lab backups, select the unique greatest "
            r"admitted modification time, restore to W:\organism_lab, inspect the "
            "restored workspace, and launch only an exact admitted target."
        ),
        (),
        (),
        (),
    )


def _search_plan(resolved: ResolvedIntent) -> tuple[WorkPlan, WorkStep]:
    plan_ref = _ref("irr.work_plan", "scenario-a-search")
    candidates = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "backup-candidates"),
        "artifact.path_set",
        BACKUP_ROOT,
        "Bounded organism_lab backup candidate set.",
    )
    step = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "search-backups"),
        "filesystem.search",
        BACKUP_ROOT,
        (
            WorkLiteralInput("root", "filesystem.directory", BACKUP_ROOT),
            WorkLiteralInput("family", "artifact.family", "organism_lab"),
        ),
        (WorkOutput("candidates", candidates),),
        (),
        WorkContinuationMode.RETURN_TO_IRR,
        "Return the complete bounded matching candidate set.",
        "Bounded Scenario A backup discovery.",
    )
    plan = WorkPlan(
        resolved.identity,
        plan_ref,
        (step,),
        "The bounded candidate set has returned to IRR.",
        "Scenario A search phase.",
    )
    return plan, step


def _latest_rule(resolved: ResolvedIntent) -> BindingRule:
    selected = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "selected-backup"),
        "artifact.path",
        BACKUP_ROOT,
        "Newest backup under the frozen latest-by-modification-time rule.",
    )
    return BindingRule(
        resolved.identity,
        _ref("irr.binding_rule", "latest-backup"),
        selected,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (_ref("executor.source", "filesystem-search"),),
        (SEARCH_SOURCE_CONTRACT_IDENTITY,),
        "artifact.path",
        BACKUP_ROOT,
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.MAX_ATTRIBUTE,
            ("modification_time",),
            (BindingAttributeKind.RFC3339_TIMESTAMP,),
        ),
        "Select one unique greatest admitted timestamp and invent no tie-breaker.",
        (),
        (),
        (),
    )


def _candidate(
    resolved: ResolvedIntent,
    *,
    name: str,
    value: str,
    mtime: str,
) -> BindingInput:
    return BindingInput(
        resolved.identity,
        _ref("irr.binding_input", name),
        SourceAttribution(
            _ref("executor.source", "filesystem-search"),
            _ref("executor.event", f"scenario-a-result-{name}"),
        ),
        BindingInputRole.PLAN_LOCAL_OUTPUT,
        SEARCH_SOURCE_CONTRACT_IDENTITY,
        "artifact.path",
        value,
        BACKUP_ROOT,
        value,
        (
            BindingAttribute("name", BindingAttributeKind.TEXT, name),
            BindingAttribute(
                "modification_time",
                BindingAttributeKind.RFC3339_TIMESTAMP,
                mtime,
            ),
        ),
        (),
        (),
        (),
    )


def _restore_plan(
    resolved: ResolvedIntent,
    selected: SymbolicReference,
) -> tuple[WorkPlan, dict[str, WorkStep]]:
    plan_ref = _ref("irr.work_plan", "scenario-a-restore")
    metadata = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "archive-metadata"),
        "archive.metadata",
        BACKUP_ROOT,
        "Metadata for the exact selected backup.",
    )
    extracted = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "extracted-paths"),
        "filesystem.path_set",
        DESTINATION,
        "Bounded extracted path set.",
    )
    launch_target = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "launch-target"),
        "process.target",
        DESTINATION,
        "Exact launch target discovered in the restored workspace.",
    )
    inspect_archive = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "inspect-archive"),
        "archive.inspect",
        BACKUP_ROOT,
        (WorkSymbolicInput("archive", selected),),
        (WorkOutput("metadata", metadata),),
        (),
        WorkContinuationMode.NONE,
        "Return inspectable metadata for the exact selected archive.",
        "Inspect the selected backup.",
    )
    extract = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "extract-archive"),
        "archive.extract",
        DESTINATION,
        (
            WorkSymbolicInput("archive", selected),
            WorkLiteralInput("destination", "filesystem.path", DESTINATION),
        ),
        (WorkOutput("files", extracted),),
        (inspect_archive.step_ref,),
        WorkContinuationMode.NONE,
        "Return the bounded extracted path set.",
        "Extract only the selected backup into the admitted destination.",
    )
    inspect_workspace = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "inspect-workspace"),
        "workspace.inspect",
        DESTINATION,
        (WorkLiteralInput("workspace", "filesystem.path", DESTINATION),),
        (WorkOutput("launch_target", launch_target),),
        (extract.step_ref,),
        WorkContinuationMode.NONE,
        "Return one exact launch target.",
        "Inspect only the restored workspace.",
    )
    launch = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "launch"),
        "process.launch",
        DESTINATION,
        (WorkSymbolicInput("target", launch_target),),
        (),
        (inspect_workspace.step_ref,),
        WorkContinuationMode.NONE,
        "Record the bounded process-launch result.",
        "Launch only the exact admitted target.",
    )
    steps = {
        "archive.inspect": inspect_archive,
        "archive.extract": extract,
        "workspace.inspect": inspect_workspace,
        "process.launch": launch,
    }
    plan = WorkPlan(
        resolved.identity,
        plan_ref,
        tuple(reversed(tuple(steps.values()))),
        "Every admitted restore step reaches its own completion contract.",
        "Scenario A restore phase.",
    )
    return plan, steps


def _requirement(plan: WorkPlan, step: WorkStep) -> CapabilityRequirement:
    scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", step.step_ref.value),
        "bounded.operation.scope",
        step.scope,
        f"Exact bounded scope for {step.operation}.",
    )
    effects = tuple(
        CapabilityRequestedEffect(
            _ref("irr.capability_requested_effect", f"{step.step_ref.value}-{index}"),
            effect,
            (scope.scope_ref,),
            f"Requested {effect} effect.",
        )
        for index, effect in enumerate(_EFFECTS[step.operation])
    )
    return CapabilityRequirement(
        plan,
        step.step_ref,
        scope.scope_ref,
        (scope,),
        effects,
        (),
        f"Exact capability requirement for {step.operation}.",
    )


def _descriptor(step: WorkStep) -> CapabilityDescriptor:
    scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", step.step_ref.value),
        "bounded.operation.scope",
        f"Invocation stays inside the exact {step.operation} scope.",
    )
    inputs = tuple(
        CapabilityInputContract(
            _ref("irr.capability_input", f"{step.step_ref.value}-{item.name}"),
            item.semantic_type
            if isinstance(item, WorkLiteralInput)
            else item.reference.semantic_type,
            (),
            f"Exact {item.name} input.",
        )
        for item in step.inputs
    )
    outputs = tuple(
        CapabilityOutputContract(
            _ref("irr.capability_output", f"{step.step_ref.value}-{item.name}"),
            item.reference.semantic_type,
            (),
            f"Exact {item.name} output.",
        )
        for item in step.outputs
    )
    effects = tuple(
        CapabilityEffect(
            _ref("irr.capability_effect", f"{step.step_ref.value}-{index}"),
            effect,
            CapabilityEffectRequirement.UNAVOIDABLE,
            (scope.requirement_ref,),
            f"Unavoidable {effect} effect.",
        )
        for index, effect in enumerate(_EFFECTS[step.operation])
    )
    return CapabilityDescriptor(
        _ref("irr.capability", step.operation),
        step.operation,
        inputs,
        outputs,
        (scope,),
        effects,
        (),
        step.completion_contract,
        f"Exact Scenario A descriptor for {step.operation}.",
    )


def _catalog(
    *descriptors: CapabilityDescriptor,
    event: str = "catalog-001",
) -> CapabilityCatalogSnapshot:
    return CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "scenario-a"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "scenario-a-host"),
            _ref("irr.event", event),
        ),
        "Only capabilities explicitly supplied for Scenario A.",
        descriptors,
        "Bounded Scenario A capability snapshot.",
    )


def _incompatible(
    descriptor: CapabilityDescriptor,
    operation: str,
) -> CapabilityIncompatibleDescriptorAssessment:
    return CapabilityIncompatibleDescriptorAssessment(
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityMismatchReason(
                CapabilityMismatchKind.OPERATION_MISMATCH,
                f"descriptor:{descriptor.capability_ref.value}",
                f"{descriptor.operation} differs from required {operation}.",
            ),
        ),
    )


def _evaluation(
    requirement: CapabilityRequirement,
    descriptor: CapabilityDescriptor,
    snapshot: CapabilityCatalogSnapshot,
    event: str,
) -> CapabilityMatchEvaluation:
    step = requirement.work_step
    requested_scope = requirement.requested_scopes[0]
    offered_scope = descriptor.scope_requirements[0]
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "scenario-a-exact"),
            _ref("irr.event", f"match-{event}"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (CapabilityScopeMatch(requested_scope.scope_ref, offered_scope.requirement_ref),),
        tuple(
            CapabilityInputMatch(
                item.name,
                next(
                    contract.input_ref
                    for contract in descriptor.input_contracts
                    if contract.input_ref.value.endswith(f"-{item.name}")
                ),
                (),
            )
            for item in step.inputs
        ),
        tuple(
            CapabilityOutputMatch(
                item.name,
                next(
                    contract.output_ref
                    for contract in descriptor.output_contracts
                    if contract.output_ref.value.endswith(f"-{item.name}")
                ),
                (),
            )
            for item in step.outputs
        ),
        tuple(
            CapabilityEffectMatch(
                requested.effect_ref,
                next(
                    offered.effect_ref
                    for offered in descriptor.effects
                    if offered.semantic_type == requested.semantic_type
                ),
            )
            for requested in requirement.requested_effects
        ),
        f"Exact match for {step.operation}.",
    )
    return CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-a"),
            _ref("irr.event", f"evaluation-{event}"),
        ),
        requirement,
        snapshot,
        (match,),
        tuple(
            _incompatible(other, step.operation)
            for other in snapshot.descriptors
            if other.identity != descriptor.identity
        ),
        f"Exhaustive bounded Catalog evaluation for {step.operation}.",
    )


def _fixture() -> dict[str, object]:
    resolved = _resolved()
    search_plan, search_step = _search_plan(resolved)
    search_descriptor = _descriptor(search_step)
    rule = _latest_rule(resolved)
    restore_plan, restore_steps = _restore_plan(resolved, rule.symbolic_reference)
    descriptors = (search_descriptor,) + tuple(
        _descriptor(step) for step in restore_steps.values()
    )
    snapshot = _catalog(*descriptors)
    by_operation = {descriptor.operation: descriptor for descriptor in snapshot.descriptors}
    candidates = (
        _candidate(
            resolved,
            name="organism_lab-2026-08-30.zip",
            value=r"D:\Backups\organism_lab-2026-08-30.zip",
            mtime="2026-08-30T20:00:00+06:00",
        ),
        _candidate(
            resolved,
            name="organism_lab-2026-08-31.zip",
            value=r"D:\Backups\organism_lab-2026-08-31.zip",
            mtime="2026-08-31T22:30:00+06:00",
        ),
    )
    bound = evaluate_binding(
        rule,
        tuple(reversed(candidates)),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-a"),
            _ref("irr.event", "bind-latest"),
        ),
    )
    assert type(bound) is BoundValue
    evaluations = {
        operation: _evaluation(
            _requirement(restore_plan, step),
            by_operation[operation],
            snapshot,
            operation.replace(".", "-"),
        )
        for operation, step in restore_steps.items()
    }
    return {
        "resolved": resolved,
        "search_plan": search_plan,
        "search_descriptor": search_descriptor,
        "rule": rule,
        "restore_plan": restore_plan,
        "restore_steps": restore_steps,
        "snapshot": snapshot,
        "candidates": candidates,
        "bound": bound,
        "evaluations": evaluations,
    }


def test_scenario_a_separates_source_contract_capability_and_occurrence() -> None:
    fixture = _fixture()
    search_plan = fixture["search_plan"]
    search_descriptor = fixture["search_descriptor"]
    rule = fixture["rule"]
    bound = fixture["bound"]
    restore_plan = fixture["restore_plan"]
    snapshot = fixture["snapshot"]
    assert isinstance(search_plan, WorkPlan)
    assert isinstance(search_descriptor, CapabilityDescriptor)
    assert isinstance(rule, BindingRule)
    assert isinstance(bound, BoundValue)
    assert isinstance(restore_plan, WorkPlan)
    assert isinstance(snapshot, CapabilityCatalogSnapshot)

    assert search_plan.steps[0].continuation is WorkContinuationMode.RETURN_TO_IRR
    assert SEARCH_SOURCE_CONTRACT_IDENTITY != search_descriptor.identity
    assert rule.allowed_source_identities == (SEARCH_SOURCE_CONTRACT_IDENTITY,)
    assert all(
        candidate.source_identity == SEARCH_SOURCE_CONTRACT_IDENTITY
        for candidate in bound.binding_inputs
    )
    assert len(
        {candidate.attribution.source_event_ref for candidate in bound.binding_inputs}
    ) == len(bound.binding_inputs)
    assert all(
        candidate.attribution.source_ref == _ref("executor.source", "filesystem-search")
        for candidate in bound.binding_inputs
    )

    assert bound.value == r"D:\Backups\organism_lab-2026-08-31.zip"
    assert bound.selection_scope == BACKUP_ROOT
    assert {step.operation for step in restore_plan.steps} == {
        "archive.inspect",
        "archive.extract",
        "workspace.inspect",
        "process.launch",
    }
    assert {descriptor.operation for descriptor in snapshot.descriptors} == set(_EFFECTS)
    for evaluation in fixture["evaluations"].values():
        assert evaluate_capability_match_evaluation(evaluation) == (
            evaluation.compatible_matches[0]
        )


def test_scenario_a_equal_latest_timestamps_fail_closed() -> None:
    fixture = _fixture()
    resolved = fixture["resolved"]
    assert isinstance(resolved, ResolvedIntent)
    candidates = tuple(
        _candidate(
            resolved,
            name=name,
            value=rf"D:\Backups\{name}",
            mtime="2026-08-31T22:30:00+06:00",
        )
        for name in ("organism_lab-a.zip", "organism_lab-b.zip")
    )
    result = evaluate_binding(
        fixture["rule"],
        tuple(reversed(candidates)),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-a"),
            _ref("irr.event", "bind-tie"),
        ),
    )
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.TIE


def test_scenario_a_missing_extract_is_no_match_not_hidden_fallback() -> None:
    fixture = _fixture()
    snapshot = fixture["snapshot"]
    restore_plan = fixture["restore_plan"]
    restore_steps = fixture["restore_steps"]
    assert isinstance(snapshot, CapabilityCatalogSnapshot)
    assert isinstance(restore_plan, WorkPlan)
    assert isinstance(restore_steps, dict)
    missing = _catalog(
        *(
            descriptor
            for descriptor in snapshot.descriptors
            if descriptor.operation != "archive.extract"
        ),
        event="catalog-without-extract",
    )
    requirement = _requirement(restore_plan, restore_steps["archive.extract"])
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-a"),
            _ref("irr.event", "evaluation-missing-extract"),
        ),
        requirement,
        missing,
        (),
        tuple(
            _incompatible(descriptor, "archive.extract")
            for descriptor in missing.descriptors
        ),
        "Exhaustive bounded evaluation with archive.extract absent.",
    )
    result = evaluate_capability_match_evaluation(evaluation)
    assert type(result) is CapabilityMatchIssue
    assert result.kind is CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY
    rendered = str(result.to_primitive()).lower()
    assert "fallback" not in rendered
    assert "powershell" not in rendered
    assert "7-zip" not in rendered
    assert "python" not in rendered
