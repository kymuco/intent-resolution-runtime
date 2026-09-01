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
    CapabilityAttempt,
    CapabilityAttemptAttribution,
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
    ClaimRecord,
    ContextEnvelope,
    ContextReferenceRecord,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    EvidenceRelation,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    OutcomeCompletionAssessment,
    OutcomeCompletionState,
    OutcomeEffectAssessment,
    OutcomeEffectCertainty,
    OutcomeEvidence,
    OutcomeEvidenceRole,
    OutcomeLifecycleAssessment,
    OutcomeLifecycleState,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    SuccessorResolutionKind,
    SuccessorResolutionLineage,
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

BACKUP_ROOT = r"D:\Backups"
DESTINATION = r"W:\organism_lab"
FAMILY = "organism_lab"
SOURCE_ID = RecordIdentity("sha256", "8" * 64)
TEMPORAL_ID = RecordIdentity("sha256", "9" * 64)

_EFFECTS = {
    "filesystem.search": ("filesystem.read",),
    "archive.inspect": ("filesystem.read",),
    "archive.extract": ("filesystem.read", "filesystem.write"),
    "workspace.inspect": ("filesystem.read",),
    "process.launch": ("process.launch",),
}


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _request() -> IntentRequest:
    return IntentRequest(
        OriginAttribution(
            OriginKind.HUMAN,
            _ref("host.actor", "user"),
            _ref("host.event", "scenario-a-intent-001"),
        ),
        _ref("host.principal", "user"),
        IntentExpression(
            r"Найди последний backup organism_lab, распакуй в W:\organism_lab и запусти."
        ),
    )


def _context(request: IntentRequest) -> ContextEnvelope:
    source = SourceAttribution(
        _ref("host.source", "scenario-a-explicit-inputs"),
        _ref("host.event", "scenario-a-context-source-001"),
    )
    return ContextEnvelope(
        request.identity,
        SourceAttribution(
            _ref("host.boundary", "context-admission"),
            _ref("host.context_boundary", "scenario-a-context-001"),
        ),
        (
            ContextReferenceRecord(
                source,
                _ref("filesystem.path", BACKUP_ROOT),
                "Exact bounded backup search root supplied by the Host.",
            ),
            ContextReferenceRecord(
                source,
                _ref("filesystem.path", DESTINATION),
                "Exact restore destination supplied by the Host.",
            ),
            ClaimRecord(source, f"Backup family constraint is exactly {FAMILY}."),
            ClaimRecord(
                source,
                "latest means greatest admitted modification timestamp inside the bounded matching candidate set",
            ),
        ),
    )


def _resolved(
    request: IntentRequest,
    context: ContextEnvelope,
    event: str,
    semantics: str,
) -> ResolvedIntent:
    return ResolvedIntent(
        request.identity,
        context.identity,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-a"),
            _ref("irr.resolution_event", event),
        ),
        semantics,
        (),
        (),
        (),
    )


def _search_plan(resolved: ResolvedIntent) -> tuple[WorkPlan, WorkStep]:
    plan_ref = _ref("irr.work_plan", "scenario-a-search")
    candidates = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "scenario-a-backup-candidates"),
        "artifact.path_set",
        BACKUP_ROOT,
        "Bounded organism_lab backup candidates returned by filesystem.search.",
    )
    step = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "search-backups"),
        "filesystem.search",
        BACKUP_ROOT,
        (
            WorkLiteralInput("root", "filesystem.directory", BACKUP_ROOT),
            WorkLiteralInput("family", "artifact.family", FAMILY),
        ),
        (WorkOutput("candidates", candidates),),
        (),
        WorkContinuationMode.RETURN_TO_IRR,
        "Return the complete bounded matching candidate set to IRR.",
        "Search only the exact admitted backup root and family.",
    )
    return (
        WorkPlan(
            resolved.identity,
            plan_ref,
            (step,),
            "The bounded matching candidate set has returned to IRR.",
            "Scenario A bounded backup discovery phase.",
        ),
        step,
    )


def _latest_rule(resolved: ResolvedIntent) -> BindingRule:
    selected = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "scenario-a-selected-backup"),
        "artifact.path",
        BACKUP_ROOT,
        "Newest organism_lab backup selected only by admitted modification_time.",
    )
    return BindingRule(
        resolved.identity,
        _ref("irr.binding_rule", "scenario-a-latest-backup"),
        selected,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (_ref("executor.source", "filesystem-search"),),
        (),
        "artifact.path",
        BACKUP_ROOT,
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.MAX_ATTRIBUTE,
            ("modification_time",),
            (BindingAttributeKind.RFC3339_TIMESTAMP,),
        ),
        "Select the unique greatest admitted modification_time; invent no tie-breaker.",
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
        _ref("irr.slot", "scenario-a-archive-metadata"),
        "archive.metadata",
        BACKUP_ROOT,
        "Metadata for the exact selected archive.",
    )
    extracted = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "scenario-a-extracted-paths"),
        "filesystem.path_set",
        DESTINATION,
        "Bounded path set produced by extraction.",
    )
    launcher = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "scenario-a-launch-target"),
        "process.target",
        DESTINATION,
        "Exact launch target produced by bounded workspace inspection.",
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
        "Inspect the selected backup without changing the admitted selection rule.",
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
        "Return the bounded extracted path set after extraction completes.",
        "Extract the exact selected backup into the exact admitted destination.",
    )
    inspect_workspace = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "inspect-workspace"),
        "workspace.inspect",
        DESTINATION,
        (WorkLiteralInput("workspace", "filesystem.path", DESTINATION),),
        (WorkOutput("launch_target", launcher),),
        (extract.step_ref,),
        WorkContinuationMode.NONE,
        "Return one exact launch target or later require semantic continuation.",
        "Inspect only the restored workspace for an admitted launch target.",
    )
    launch = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "launch"),
        "process.launch",
        DESTINATION,
        (WorkSymbolicInput("target", launcher),),
        (),
        (inspect_workspace.step_ref,),
        WorkContinuationMode.NONE,
        "Record the bounded process-launch result for the exact admitted target.",
        "Launch only the exact target produced by bounded workspace inspection.",
    )
    steps = {
        "archive.inspect": inspect_archive,
        "archive.extract": extract,
        "workspace.inspect": inspect_workspace,
        "process.launch": launch,
    }
    return (
        WorkPlan(
            resolved.identity,
            plan_ref,
            tuple(reversed(tuple(steps.values()))),
            "Each admitted restore/inspection/launch step reaches its own completion contract.",
            "Scenario A restore phase after exact latest-backup binding.",
        ),
        steps,
    )


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
            semantic_type,
            (scope.scope_ref,),
            f"Requested {semantic_type} effect for {step.operation}.",
        )
        for index, semantic_type in enumerate(_EFFECTS[step.operation])
    )
    return CapabilityRequirement(
        plan,
        step.step_ref,
        scope.scope_ref,
        (scope,),
        effects,
        (),
        f"Exact Scenario A capability requirement for {step.operation}.",
    )


def _descriptor(step: WorkStep) -> CapabilityDescriptor:
    scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", step.step_ref.value),
        "bounded.operation.scope",
        f"Invocation must remain inside the exact Scenario A scope for {step.operation}.",
    )
    inputs = tuple(
        CapabilityInputContract(
            _ref("irr.capability_input", f"{step.step_ref.value}-{item.name}"),
            item.semantic_type
            if isinstance(item, WorkLiteralInput)
            else item.reference.semantic_type,
            (),
            f"Exact {item.name} input for {step.operation}.",
        )
        for item in step.inputs
    )
    outputs = tuple(
        CapabilityOutputContract(
            _ref("irr.capability_output", f"{step.step_ref.value}-{item.name}"),
            item.reference.semantic_type,
            (),
            f"Exact {item.name} output for {step.operation}.",
        )
        for item in step.outputs
    )
    effects = tuple(
        CapabilityEffect(
            _ref("irr.capability_effect", f"{step.step_ref.value}-{index}"),
            semantic_type,
            CapabilityEffectRequirement.UNAVOIDABLE,
            (scope.requirement_ref,),
            f"Unavoidable {semantic_type} effect for {step.operation}.",
        )
        for index, semantic_type in enumerate(_EFFECTS[step.operation])
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


def _catalog(*descriptors: CapabilityDescriptor, event: str) -> CapabilityCatalogSnapshot:
    return CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "scenario-a"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "scenario-a-host"),
            _ref("irr.event", event),
        ),
        "Capabilities explicitly supplied for frozen M0.10 Scenario A only.",
        descriptors,
        "Scenario A exact bounded capability catalog snapshot.",
    )


def _incompatible(
    descriptor: CapabilityDescriptor,
    required_operation: str,
) -> CapabilityIncompatibleDescriptorAssessment:
    return CapabilityIncompatibleDescriptorAssessment(
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityMismatchReason(
                CapabilityMismatchKind.OPERATION_MISMATCH,
                f"descriptor:{descriptor.capability_ref.value}",
                f"{descriptor.operation} differs from required {required_operation}.",
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
    descriptor_scope = descriptor.scope_requirements[0]
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "scenario-a-exact"),
            _ref("irr.event", f"scenario-a-match-{event}"),
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
        f"Exact Scenario A match for {step.operation}.",
    )
    return CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-a-capability-evaluation"),
            _ref("irr.event", f"scenario-a-evaluation-{event}"),
        ),
        requirement,
        snapshot,
        (match,),
        tuple(
            _incompatible(other, step.operation)
            for other in snapshot.descriptors
            if other.identity != descriptor.identity
        ),
        f"Exhaustive exact Scenario A Catalog evaluation for {step.operation}.",
    )


def _no_match_evaluation(
    requirement: CapabilityRequirement,
    snapshot: CapabilityCatalogSnapshot,
) -> CapabilityMatchEvaluation:
    return CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-a-capability-evaluation"),
            _ref("irr.event", "scenario-a-evaluation-missing-extract"),
        ),
        requirement,
        snapshot,
        (),
        tuple(
            _incompatible(descriptor, requirement.work_step.operation)
            for descriptor in snapshot.descriptors
        ),
        "Exhaustive Scenario A Catalog evaluation with archive.extract absent.",
    )


def _evidence(
    name: str,
    roles: tuple[OutcomeEvidenceRole, ...],
    statement: str,
) -> OutcomeEvidence:
    return OutcomeEvidence(
        _ref("irr.outcome_evidence", name),
        SourceAttribution(
            _ref("executor.source", "filesystem-search"),
            _ref("executor.event", name),
        ),
        SOURCE_ID,
        EvidenceRelation.SUPPORTS,
        roles,
        (TEMPORAL_ID,),
        "Scenario A bounded filesystem.search",
        statement,
    )


def _search_outcome(
    evaluation: CapabilityMatchEvaluation,
):
    attempt = CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", "filesystem-search"),
            _ref("irr.event", "scenario-a-attempt-search"),
        ),
        evaluation,
        evaluation.requirement.step_ref,
        (),
        (),
        "One attributable bounded filesystem.search attempt.",
    )
    lifecycle = _evidence(
        "scenario-a-search-lifecycle",
        (OutcomeEvidenceRole.LIFECYCLE,),
        "The bounded filesystem.search result protocol completed normally.",
    )
    result = _evidence(
        "scenario-a-search-result",
        (OutcomeEvidenceRole.COMPLETION, OutcomeEvidenceRole.EFFECT),
        "The exact bounded matching candidate set was returned.",
    )
    from intent_resolution_runtime import CapabilityOutcome, CapabilityOutcomeAttribution

    return CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "scenario-a"),
            _ref("irr.event", "scenario-a-outcome-search"),
        ),
        attempt,
        (lifecycle, result),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
            (lifecycle.evidence_ref,),
            "The bounded search result protocol completed.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.SATISFIED,
            (result.evidence_ref,),
            "The search WorkStep completion contract is satisfied.",
        ),
        (
            OutcomeEffectAssessment(
                evaluation.requirement.requested_effects[0].effect_ref,
                OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                (result.evidence_ref,),
                "The bounded filesystem.read effect is confirmed.",
            ),
        ),
        "Scenario A bounded search Outcome.",
    )


def _binding_input(
    resolved: ResolvedIntent,
    outcome,
    name: str,
    value: str,
    mtime: str,
) -> BindingInput:
    return BindingInput(
        resolved.identity,
        _ref("irr.binding_input", name),
        SourceAttribution(
            _ref("executor.source", "filesystem-search"),
            _ref("executor.event", "scenario-a-search-result-001"),
        ),
        BindingInputRole.PLAN_LOCAL_OUTPUT,
        outcome.identity,
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


def _scenario():
    request = _request()
    context = _context(request)
    initial = _resolved(
        request,
        context,
        "scenario-a-resolve-initial",
        (
            "Search only D:\\Backups for organism_lab candidates. latest means greatest "
            "admitted modification timestamp. Restore only to W:\\organism_lab and launch "
            "only an exact target later admitted by bounded workspace inspection."
        ),
    )
    search_plan, search_step = _search_plan(initial)

    after_search = _resolved(
        request,
        context,
        "scenario-a-resolve-after-search",
        (
            "Use the exact bounded search result as BindingInput material and apply the "
            "already-admitted latest-by-modification-time rule before restore work."
        ),
    )
    rule = _latest_rule(after_search)
    restore_plan, restore_steps = _restore_plan(after_search, rule.symbolic_reference)

    all_steps = (search_step,) + tuple(restore_steps.values())
    descriptors = tuple(_descriptor(step) for step in all_steps)
    snapshot = _catalog(*descriptors, event="scenario-a-catalog-001")
    descriptor_by_operation = {item.operation: item for item in snapshot.descriptors}

    search_requirement = _requirement(search_plan, search_step)
    search_evaluation = _evaluation(
        search_requirement,
        descriptor_by_operation["filesystem.search"],
        snapshot,
        "search",
    )
    search_outcome = _search_outcome(search_evaluation)
    continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "scenario-a-host"),
            _ref("irr.event", "scenario-a-reentry-search"),
        ),
        ContinuationSourceKind.CAPABILITY_OUTCOME,
        search_outcome,
    )
    lineage = SuccessorResolutionLineage(
        initial,
        (continuation,),
        SuccessorResolutionKind.RESOLVED_INTENT,
        after_search,
    )

    candidates = (
        _binding_input(
            after_search,
            search_outcome,
            "organism_lab-2026-08-30.zip",
            r"D:\Backups\organism_lab-2026-08-30.zip",
            "2026-08-30T20:00:00+06:00",
        ),
        _binding_input(
            after_search,
            search_outcome,
            "organism_lab-2026-08-31.zip",
            r"D:\Backups\organism_lab-2026-08-31.zip",
            "2026-08-31T22:30:00+06:00",
        ),
    )
    bound = evaluate_binding(
        rule,
        tuple(reversed(candidates)),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-a"),
            _ref("irr.event", "scenario-a-binding-latest"),
        ),
    )
    assert type(bound) is BoundValue

    evaluations = {
        operation: _evaluation(
            _requirement(restore_plan, step),
            descriptor_by_operation[operation],
            snapshot,
            operation.replace(".", "-"),
        )
        for operation, step in restore_steps.items()
    }

    return {
        "request": request,
        "context": context,
        "initial": initial,
        "search_plan": search_plan,
        "search_outcome": search_outcome,
        "lineage": lineage,
        "after_search": after_search,
        "rule": rule,
        "candidates": candidates,
        "bound": bound,
        "restore_plan": restore_plan,
        "restore_steps": restore_steps,
        "snapshot": snapshot,
        "evaluations": evaluations,
    }


def test_scenario_a_planning_binding_and_capability_surface_are_executable() -> None:
    fixture = _scenario()

    request = fixture["request"]
    context = fixture["context"]
    assert request.origin.kind is OriginKind.HUMAN
    assert request.expression.text.startswith("Найди последний backup organism_lab")
    assert BACKUP_ROOT.encode() in context.canonical_bytes()
    assert DESTINATION.encode() in context.canonical_bytes()

    search_plan = fixture["search_plan"]
    assert search_plan.steps[0].operation == "filesystem.search"
    assert search_plan.steps[0].continuation is WorkContinuationMode.RETURN_TO_IRR
    assert fixture["lineage"].predecessor == fixture["initial"]
    assert fixture["lineage"].successor == fixture["after_search"]

    bound = fixture["bound"]
    assert bound.value == r"D:\Backups\organism_lab-2026-08-31.zip"
    assert bound.selection_scope == BACKUP_ROOT
    assert bound.selected_input_identity == fixture["candidates"][1].identity
    assert bound.rule.selection_policy.mode is BindingSelectionMode.MAX_ATTRIBUTE

    restore_plan = fixture["restore_plan"]
    assert {step.operation for step in restore_plan.steps} == {
        "archive.inspect",
        "archive.extract",
        "workspace.inspect",
        "process.launch",
    }
    assert {item.operation for item in fixture["snapshot"].descriptors} == {
        "filesystem.search",
        "archive.inspect",
        "archive.extract",
        "workspace.inspect",
        "process.launch",
    }
    for evaluation in fixture["evaluations"].values():
        assert evaluate_capability_match_evaluation(evaluation) == (
            evaluation.compatible_matches[0]
        )


def test_scenario_a_equal_latest_timestamps_fail_closed_without_tie_breaker() -> None:
    fixture = _scenario()
    first = _binding_input(
        fixture["after_search"],
        fixture["search_outcome"],
        "organism_lab-a.zip",
        r"D:\Backups\organism_lab-a.zip",
        "2026-08-31T22:30:00+06:00",
    )
    second = _binding_input(
        fixture["after_search"],
        fixture["search_outcome"],
        "organism_lab-b.zip",
        r"D:\Backups\organism_lab-b.zip",
        "2026-08-31T22:30:00+06:00",
    )
    result = evaluate_binding(
        fixture["rule"],
        (second, first),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-a"),
            _ref("irr.event", "scenario-a-binding-tie"),
        ),
    )
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.TIE


def test_scenario_a_missing_extract_capability_is_bounded_no_match_not_fallback() -> None:
    fixture = _scenario()
    missing_snapshot = _catalog(
        *(
            descriptor
            for descriptor in fixture["snapshot"].descriptors
            if descriptor.operation != "archive.extract"
        ),
        event="scenario-a-catalog-without-extract",
    )
    requirement = _requirement(
        fixture["restore_plan"],
        fixture["restore_steps"]["archive.extract"],
    )
    evaluation = _no_match_evaluation(requirement, missing_snapshot)
    result = evaluate_capability_match_evaluation(evaluation)

    assert type(result) is CapabilityMatchIssue
    assert result.kind is CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY
    rendered = str(result.to_primitive()).lower()
    assert "fallback" not in rendered
    assert "powershell" not in rendered
    assert "7-zip" not in rendered
    assert "python" not in rendered
