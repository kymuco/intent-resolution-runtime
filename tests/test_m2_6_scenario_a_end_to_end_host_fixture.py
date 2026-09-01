from __future__ import annotations

from intent_resolution_runtime import (
    AttemptBoundInput,
    Authorization,
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
    CandidateAttribution,
    CandidateResolution,
    CapabilityAttempt,
    CapabilityAttemptAttribution,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffect,
    CapabilityEffectMatch,
    CapabilityEffectRequirement,
    CapabilityInputContract,
    CapabilityInputMatch,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityOutcome,
    CapabilityOutcomeAttribution,
    CapabilityOutputContract,
    CapabilityOutputMatch,
    CapabilityRequestedEffect,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    ClaimRecord,
    ContextEnvelope,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    EvidenceRelation,
    GovernanceDecision,
    GovernanceDecisionAttribution,
    GovernanceDecisionComponent,
    GovernanceDecisionKind,
    InitialResolutionFrontierKind,
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
    ProposedWorkStep,
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
    WorkProposal,
    WorkProposalAttribution,
    WorkProposalMaterial,
    WorkProposalMaterialKind,
    WorkStep,
    WorkSymbolicInput,
    evaluate_binding,
    evaluate_capability_match_evaluation,
    orchestrate_attempt_outcome_continuation,
    orchestrate_capability_governance,
    orchestrate_initial_resolution,
    orchestrate_worker_lifecycle,
    orchestrate_work_binding,
)


BACKUP_ROOT = r"D:\Backups"
DESTINATION = r"W:\organism_lab"
SELECTED_BACKUP = r"D:\Backups\organism_lab-2026-08-31.zip"
SEARCH_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "3" * 64)
OUTCOME_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "4" * 64)
AUTHORITY_CONTEXT_IDENTITY = RecordIdentity("sha256", "5" * 64)
TEMPORAL_BASIS_IDENTITY = RecordIdentity("sha256", "6" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _request_and_context() -> tuple[IntentRequest, ContextEnvelope]:
    request = IntentRequest(
        origin=OriginAttribution(
            OriginKind.HUMAN,
            _ref("human", "user"),
            _ref("host.event", "scenario-a-request"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression(
            r"Найди последний backup organism_lab, распакуй в W:\organism_lab и запусти."
        ),
    )
    context_source = SourceAttribution(
        _ref("host.source", "scenario-a-context"),
        _ref("host.event", "scenario-a-context"),
    )
    context = ContextEnvelope(
        request.identity,
        context_source,
        (
            ClaimRecord(context_source, f"Backup search root is exactly {BACKUP_ROOT}."),
            ClaimRecord(context_source, "Backup family match is exactly organism_lab."),
            ClaimRecord(context_source, f"Restore destination is exactly {DESTINATION}."),
            ClaimRecord(
                context_source,
                "Latest means the unique greatest admitted modification timestamp within the bounded matching set.",
            ),
        ),
    )
    return request, context


def _candidate(request: IntentRequest, context: ContextEnvelope) -> CandidateResolution:
    return CandidateResolution(
        request.identity,
        context.identity,
        CandidateAttribution(
            _ref("irr.provider", "scenario-a-provider"),
            _ref("irr.provider_invocation", "scenario-a-provider-001"),
        ),
        (
            "Search the bounded backup root, choose the newest organism_lab backup, "
            "extract it to the admitted destination, inspect the restored workspace, and launch it."
        ),
        (),
        (),
        (),
        (),
    )


def _admit_scenario_a(
    request: IntentRequest,
    context: ContextEnvelope,
    candidates: tuple[CandidateResolution, ...],
    attribution: ResolutionAttribution,
) -> ResolvedIntent:
    return ResolvedIntent(
        request.identity,
        context.identity,
        attribution,
        (
            f"Search only {BACKUP_ROOT} for organism_lab backups; select only the unique greatest "
            f"admitted modification timestamp; restore only to {DESTINATION}; any later launch must "
            "use an exact admitted target and occurs only after the preceding restore semantics remain satisfied."
        ),
        candidate_inputs=candidates,
    )


def _selected_reference(resolved: ResolvedIntent) -> SymbolicReference:
    return SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "selected-backup"),
        "artifact.path",
        BACKUP_ROOT,
        "Unique newest backup under the already-admitted latest-by-modification-time rule.",
    )


def _search_plan(resolved: ResolvedIntent) -> tuple[WorkPlan, WorkStep]:
    plan_ref = _ref("irr.work_plan", "m2-6-scenario-a-search")
    candidates = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "backup-candidates"),
        "artifact.path_set",
        BACKUP_ROOT,
        "Complete bounded organism_lab backup candidate set.",
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
        "Bounded Scenario A backup discovery phase.",
    )
    return (
        WorkPlan(
            resolved.identity,
            plan_ref,
            (step,),
            "The bounded candidate set has returned to IRR.",
            "Scenario A search phase.",
        ),
        step,
    )


def _search_capability_evaluation(
    plan: WorkPlan,
    step: WorkStep,
) -> tuple[CapabilityRequirement, CapabilityMatchEvaluation]:
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "search-root"),
        "filesystem.directory_scope",
        BACKUP_ROOT,
        "Exact bounded backup search root.",
    )
    requested_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "search-read"),
        "filesystem.read",
        (requested_scope.scope_ref,),
        "Read directory metadata only inside the exact bounded search root.",
    )
    requirement = CapabilityRequirement(
        plan,
        step.step_ref,
        requested_scope.scope_ref,
        (requested_scope,),
        (requested_effect,),
        (),
        "Exact filesystem.search capability requirement.",
    )

    offered_scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "search-root"),
        "filesystem.directory_scope",
        "Search stays inside the exact supplied directory scope.",
    )
    root_input = CapabilityInputContract(
        _ref("irr.capability_input", "search-root"),
        "filesystem.directory",
        (offered_scope.requirement_ref,),
        "Exact search root.",
    )
    family_input = CapabilityInputContract(
        _ref("irr.capability_input", "search-family"),
        "artifact.family",
        (),
        "Exact backup family filter.",
    )
    candidates_output = CapabilityOutputContract(
        _ref("irr.capability_output", "search-candidates"),
        "artifact.path_set",
        (),
        "Bounded candidate set.",
    )
    offered_effect = CapabilityEffect(
        _ref("irr.capability_effect", "search-read"),
        "filesystem.read",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (offered_scope.requirement_ref,),
        "Search necessarily reads directory metadata inside the admitted root.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "filesystem.search.local"),
        "filesystem.search",
        (root_input, family_input),
        (candidates_output,),
        (offered_scope,),
        (offered_effect,),
        (),
        step.completion_contract,
        "Bounded local filesystem search capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "scenario-a-search"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "scenario-a-host"),
            _ref("irr.event", "scenario-a-search-catalog"),
        ),
        "Only the exact bounded search capability is admitted for this phase.",
        (descriptor,),
        "Scenario A bounded search Catalog snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "scenario-a-exact"),
            _ref("irr.event", "scenario-a-search-match"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (CapabilityScopeMatch(requested_scope.scope_ref, offered_scope.requirement_ref),),
        (
            CapabilityInputMatch("root", root_input.input_ref, (requested_scope.scope_ref,)),
            CapabilityInputMatch("family", family_input.input_ref, ()),
        ),
        (CapabilityOutputMatch("candidates", candidates_output.output_ref, ()),),
        (CapabilityEffectMatch(requested_effect.effect_ref, offered_effect.effect_ref),),
        "Exact bounded filesystem.search match.",
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-a"),
            _ref("irr.event", "scenario-a-search-evaluation"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for bounded backup search.",
    )
    assert evaluate_capability_match_evaluation(evaluation) == match
    return requirement, evaluation


def _latest_rule(resolved: ResolvedIntent) -> BindingRule:
    return BindingRule(
        resolved.identity,
        _ref("irr.binding_rule", "latest-backup"),
        _selected_reference(resolved),
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


def _candidate_path(
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
            _ref("executor.event", f"scenario-a-search-result-{name}"),
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


def _extract_plan(
    resolved: ResolvedIntent,
    selected: SymbolicReference,
) -> tuple[WorkPlan, WorkStep]:
    plan_ref = _ref("irr.work_plan", "m2-6-scenario-a-extract")
    step = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "extract-archive"),
        "archive.extract",
        DESTINATION,
        (
            WorkSymbolicInput("archive", selected),
            WorkLiteralInput("destination", "filesystem.path", DESTINATION),
        ),
        (),
        (),
        WorkContinuationMode.NONE,
        "Return a scoped extraction result for the exact destination.",
        "Extract only the exact selected backup into the exact admitted destination.",
    )
    return (
        WorkPlan(
            resolved.identity,
            plan_ref,
            (step,),
            "The bounded archive.extract step reaches its own completion contract.",
            "Scenario A extract phase.",
        ),
        step,
    )


def _extract_capability_evaluation(
    plan: WorkPlan,
    step: WorkStep,
) -> tuple[CapabilityRequirement, CapabilityMatchEvaluation]:
    source_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "extract-source"),
        "filesystem.path_scope",
        SELECTED_BACKUP,
        "Exact selected backup read scope.",
    )
    destination_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "extract-destination"),
        "filesystem.path_scope",
        DESTINATION,
        "Exact restore destination write scope.",
    )
    read_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "extract-read"),
        "filesystem.read",
        (source_scope.scope_ref,),
        "Read only the exact selected backup.",
    )
    write_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "extract-write"),
        "filesystem.write",
        (destination_scope.scope_ref,),
        "Write extracted material only inside the exact destination.",
    )
    requirement = CapabilityRequirement(
        plan,
        step.step_ref,
        destination_scope.scope_ref,
        (source_scope, destination_scope),
        (read_effect, write_effect),
        (),
        "Exact Scenario A archive.extract capability requirement.",
    )

    source_requirement = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "extract-source"),
        "filesystem.path_scope",
        "Archive reads remain inside the exact selected backup scope.",
    )
    destination_requirement = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "extract-destination"),
        "filesystem.path_scope",
        "Writes remain inside the exact restore destination scope.",
    )
    archive_input = CapabilityInputContract(
        _ref("irr.capability_input", "extract-archive"),
        "artifact.path",
        (source_requirement.requirement_ref,),
        "Exact selected archive path.",
    )
    destination_input = CapabilityInputContract(
        _ref("irr.capability_input", "extract-destination"),
        "filesystem.path",
        (destination_requirement.requirement_ref,),
        "Exact restore destination.",
    )
    descriptor_read = CapabilityEffect(
        _ref("irr.capability_effect", "extract-read"),
        "filesystem.read",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (source_requirement.requirement_ref,),
        "Extraction necessarily reads the selected archive.",
    )
    descriptor_write = CapabilityEffect(
        _ref("irr.capability_effect", "extract-write"),
        "filesystem.write",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (destination_requirement.requirement_ref,),
        "Extraction may materialize files inside the exact destination.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "archive.extract.local"),
        "archive.extract",
        (archive_input, destination_input),
        (),
        (source_requirement, destination_requirement),
        (descriptor_read, descriptor_write),
        (),
        step.completion_contract,
        "Bounded local archive extraction capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "scenario-a-extract"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "scenario-a-host"),
            _ref("irr.event", "scenario-a-extract-catalog"),
        ),
        "Only the exact archive.extract capability is admitted for this phase.",
        (descriptor,),
        "Scenario A extract Catalog snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "scenario-a-exact"),
            _ref("irr.event", "scenario-a-extract-match"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityScopeMatch(source_scope.scope_ref, source_requirement.requirement_ref),
            CapabilityScopeMatch(
                destination_scope.scope_ref,
                destination_requirement.requirement_ref,
            ),
        ),
        (
            CapabilityInputMatch("archive", archive_input.input_ref, (source_scope.scope_ref,)),
            CapabilityInputMatch(
                "destination",
                destination_input.input_ref,
                (destination_scope.scope_ref,),
            ),
        ),
        (),
        (
            CapabilityEffectMatch(read_effect.effect_ref, descriptor_read.effect_ref),
            CapabilityEffectMatch(write_effect.effect_ref, descriptor_write.effect_ref),
        ),
        "Exact Scenario A archive.extract capability match.",
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-a"),
            _ref("irr.event", "scenario-a-extract-evaluation"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for Scenario A archive.extract.",
    )
    assert evaluate_capability_match_evaluation(evaluation) == match
    return requirement, evaluation


def _governance(
    evaluation: CapabilityMatchEvaluation,
    bound: BoundValue,
) -> tuple[WorkProposal, GovernanceDecision, Authorization]:
    step_ref = evaluation.requirement.step_ref
    proposal = WorkProposal(
        WorkProposalAttribution(
            _ref("irr.proposer", "irr-core"),
            _ref("irr.event", "scenario-a-extract-proposal"),
        ),
        evaluation.requirement.work_plan,
        (ProposedWorkStep(step_ref, evaluation),),
        (
            WorkProposalMaterial(
                _ref("irr.work_proposal_material", "selected-backup"),
                WorkProposalMaterialKind.AFFECTED_RESOURCE,
                (step_ref,),
                _ref("irr.source", "scenario-a-binding"),
                bound.identity,
                SELECTED_BACKUP,
                "archive.extract reads the exact selected backup resource.",
            ),
            WorkProposalMaterial(
                _ref("irr.work_proposal_material", "extract-destination"),
                WorkProposalMaterialKind.AFFECTED_RESOURCE,
                (step_ref,),
                _ref("irr.source", "scenario-a-context"),
                evaluation.requirement.work_plan.resolved_intent_identity,
                DESTINATION,
                "archive.extract may write or replace material inside the exact destination.",
            ),
        ),
        "Present the exact effectful extraction step to external Governance.",
    )
    component = GovernanceDecisionComponent(
        _ref("irr.governance_component", "authorize-extract"),
        GovernanceDecisionKind.AUTHORIZE,
        (step_ref,),
        (),
        "Authorize only the exact represented archive.extract step.",
    )
    decision = GovernanceDecision(
        GovernanceDecisionAttribution(
            _ref("irr.governance", "scenario-a-governance"),
            _ref("irr.event", "scenario-a-extract-decision"),
            _ref("irr.authority_context", "scenario-a"),
            AUTHORITY_CONTEXT_IDENTITY,
        ),
        proposal,
        (component,),
        "Exact Governance decision for Scenario A archive extraction.",
    )
    return proposal, decision, Authorization(decision, component.component_ref)


def _evidence(
    name: str,
    roles: tuple[OutcomeEvidenceRole, ...],
    statement: str,
) -> OutcomeEvidence:
    return OutcomeEvidence(
        _ref("irr.outcome_evidence", name),
        SourceAttribution(
            _ref("executor.source", "archive-extract-local"),
            _ref("executor.event", name),
        ),
        OUTCOME_SOURCE_CONTRACT_IDENTITY,
        EvidenceRelation.SUPPORTS,
        roles,
        (TEMPORAL_BASIS_IDENTITY,),
        "Scenario A archive.extract Attempt",
        statement,
    )


def _partial_outcome(attempt: CapabilityAttempt) -> CapabilityOutcome:
    lifecycle = _evidence(
        "scenario-a-extract-failure-protocol",
        (OutcomeEvidenceRole.LIFECYCLE,),
        "The executor returned through its normal failure result protocol.",
    )
    read = _evidence(
        "scenario-a-extract-read-confirmed",
        (OutcomeEvidenceRole.EFFECT,),
        "The selected archive was read before extraction stopped.",
    )
    partial_write = _evidence(
        "scenario-a-extract-partial-write",
        (
            OutcomeEvidenceRole.COMPLETION,
            OutcomeEvidenceRole.EFFECT,
            OutcomeEvidenceRole.PARTIAL_EFFECT,
        ),
        "Some destination files were materialized, but the extraction completion contract was not satisfied.",
    )
    effects = {
        item.semantic_type: item
        for item in attempt.capability_evaluation.requirement.requested_effects
    }
    return CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "scenario-a"),
            _ref("irr.event", "scenario-a-extract-outcome"),
        ),
        attempt,
        (partial_write, lifecycle, read),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
            (lifecycle.evidence_ref,),
            "The failure result protocol completed normally.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.NOT_SATISFIED,
            (partial_write.evidence_ref,),
            "The exact archive.extract completion contract was not satisfied.",
        ),
        (
            OutcomeEffectAssessment(
                effects["filesystem.read"].effect_ref,
                OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                (read.evidence_ref,),
                "The archive read effect is confirmed.",
            ),
            OutcomeEffectAssessment(
                effects["filesystem.write"].effect_ref,
                OutcomeEffectCertainty.CONFIRMED_PARTIAL,
                (partial_write.evidence_ref,),
                "Known partial filesystem writes remain explicit after failed completion.",
            ),
        ),
        "Scenario A archive.extract failed completion with known partial destination effects.",
    )


def _resolved_fixture() -> tuple[IntentRequest, ContextEnvelope, CandidateResolution, ResolvedIntent]:
    request, context = _request_and_context()
    candidate = _candidate(request, context)

    proposal_frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
    )
    assert proposal_frontier.kind is InitialResolutionFrontierKind.ADMISSION_REQUIRED
    assert proposal_frontier.resolution_output is None

    admitted_frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admitter=_admit_scenario_a,
        admission_attribution=ResolutionAttribution(
            _ref("irr.resolver", "scenario-a"),
            _ref("irr.resolution_event", "scenario-a-resolved"),
        ),
    )
    assert admitted_frontier.kind is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    resolved = admitted_frontier.resolution_output
    assert type(resolved) is ResolvedIntent
    assert resolved.candidate_inputs == (candidate,)
    assert resolved.semantics != candidate.proposed_semantics
    return request, context, candidate, resolved


def test_m2_6_scenario_a_threads_m2_1_through_m2_5_without_hidden_policy() -> None:
    request, context, candidate, resolved = _resolved_fixture()

    search_plan, search_step = _search_plan(resolved)
    search_binding = orchestrate_work_binding(resolved, work_plans=(search_plan,))
    assert search_binding.external_binding_complete is True
    assert search_binding.external_symbolic_references == ()

    search_requirement, search_evaluation = _search_capability_evaluation(
        search_plan,
        search_step,
    )
    search_capability = orchestrate_capability_governance(
        search_plan,
        capability_requirements=(search_requirement,),
        capability_evaluations=(search_evaluation,),
    )
    assert len(search_capability.capability_matches) == 1
    assert search_capability.capability_issues == ()
    assert search_capability.proposal_disposition_required_step_refs == (search_step.step_ref,)
    assert search_capability.materialized_authorized_step_refs == ()

    rule = _latest_rule(resolved)
    candidates = (
        _candidate_path(
            resolved,
            name="organism_lab-2026-08-30.zip",
            value=r"D:\Backups\organism_lab-2026-08-30.zip",
            mtime="2026-08-30T20:00:00+06:00",
        ),
        _candidate_path(
            resolved,
            name="organism_lab-2026-08-31.zip",
            value=SELECTED_BACKUP,
            mtime="2026-08-31T22:30:00+06:00",
        ),
    )
    bound = evaluate_binding(
        rule,
        tuple(reversed(candidates)),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-a"),
            _ref("irr.event", "scenario-a-bind-latest"),
        ),
    )
    assert type(bound) is BoundValue
    assert bound.value == SELECTED_BACKUP

    extract_plan, extract_step = _extract_plan(resolved, rule.symbolic_reference)
    before_binding = orchestrate_work_binding(
        resolved,
        work_plans=(extract_plan,),
        binding_rules=(rule,),
    )
    assert before_binding.pending_rules == (rule,)
    assert before_binding.external_binding_complete is False

    after_binding = orchestrate_work_binding(
        resolved,
        work_plans=(extract_plan,),
        binding_rules=(rule,),
        binding_evaluations=(bound,),
    )
    assert after_binding.bound_values == (bound,)
    assert after_binding.binding_issues == ()
    assert after_binding.external_binding_complete is True

    extract_requirement, extract_evaluation = _extract_capability_evaluation(
        extract_plan,
        extract_step,
    )
    proposal, decision, authorization = _governance(extract_evaluation, bound)

    before_authorization = orchestrate_capability_governance(
        extract_plan,
        capability_requirements=(extract_requirement,),
        capability_evaluations=(extract_evaluation,),
        work_proposals=(proposal,),
        governance_decisions=(decision,),
    )
    assert before_authorization.authorization_materialization_frontier == (authorization,)
    assert before_authorization.materialized_authorized_step_refs == ()

    authorized = orchestrate_capability_governance(
        extract_plan,
        capability_requirements=(extract_requirement,),
        capability_evaluations=(extract_evaluation,),
        work_proposals=(proposal,),
        governance_decisions=(decision,),
        authorizations=(authorization,),
    )
    assert authorized.authorization_materialization_frontier == ()
    assert authorized.materialized_authorized_step_refs == (extract_step.step_ref,)

    attempt = CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", "archive-extract-local"),
            _ref("irr.event", "scenario-a-extract-attempt"),
        ),
        extract_evaluation,
        extract_step.step_ref,
        (AttemptBoundInput("archive", bound),),
        (authorization,),
        "One attributable authorized archive.extract Attempt.",
    )
    outcome = _partial_outcome(attempt)

    history_only = orchestrate_attempt_outcome_continuation(
        resolved,
        attempts=(attempt,),
        outcomes=(outcome,),
    )
    assert history_only.outcome_pending_attempts == ()
    assert history_only.outcomes_not_selected_for_continuation == (outcome,)
    assert history_only.successor_lineage is None

    continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "scenario-a-host"),
            _ref("irr.event", "scenario-a-reentry-after-partial-extract"),
        ),
        ContinuationSourceKind.CAPABILITY_OUTCOME,
        outcome,
    )
    successor = ResolvedIntent(
        request.identity,
        context.identity,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-a"),
            _ref("irr.resolution_event", "scenario-a-after-partial-extract"),
        ),
        (
            "Inspect the exact destination state after the partial extraction before any further "
            "recovery action; do not retry the prior Attempt implicitly and do not launch yet."
        ),
    )
    lineage = SuccessorResolutionLineage(
        resolved,
        (continuation,),
        SuccessorResolutionKind.RESOLVED_INTENT,
        successor,
    )

    continued = orchestrate_attempt_outcome_continuation(
        resolved,
        attempts=(attempt,),
        outcomes=(outcome,),
        continuation_sources=(outcome,),
        continuation_inputs=(continuation,),
        successor_lineages=(lineage,),
    )
    assert continued.reentry_pending_sources == ()
    assert continued.reentry_ambiguity_source_identities == ()
    assert continued.unconsumed_continuation_inputs == ()
    assert continued.successor_lineage == lineage
    assert outcome.completion.state is OutcomeCompletionState.NOT_SATISFIED
    assert any(
        item.certainty is OutcomeEffectCertainty.CONFIRMED_PARTIAL
        for item in outcome.effect_assessments
    )

    worker = orchestrate_worker_lifecycle(
        resolved,
        parent_work_plans=(extract_plan,),
    )
    assert worker.delegated_work == ()
    assert worker.handoffs == ()
    assert worker.worker_results == ()
    assert worker.handoff_disposition_required_delegations == ()
    assert worker.result_pending_handoffs == ()

    successor_work = orchestrate_work_binding(successor)
    assert successor_work.work_plan is None
    assert successor_work.work_disposition_required is True
    assert successor_work.external_binding_complete is False

    assert candidate.intent_request_identity == request.identity
    assert resolved.context_envelope_identity == context.identity
    assert attempt.presented_authorizations == (authorization,)
    assert lineage.successor == successor


def test_m2_6_equal_latest_timestamp_stops_before_extract_binding_completion() -> None:
    _, _, _, resolved = _resolved_fixture()
    rule = _latest_rule(resolved)
    candidates = tuple(
        _candidate_path(
            resolved,
            name=name,
            value=rf"D:\Backups\{name}",
            mtime="2026-08-31T22:30:00+06:00",
        )
        for name in ("organism_lab-a.zip", "organism_lab-b.zip")
    )
    issue = evaluate_binding(
        rule,
        tuple(reversed(candidates)),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-a"),
            _ref("irr.event", "scenario-a-bind-tie"),
        ),
    )
    assert type(issue) is BindingIssue
    assert issue.kind is BindingIssueKind.TIE

    extract_plan, _ = _extract_plan(resolved, rule.symbolic_reference)
    frontier = orchestrate_work_binding(
        resolved,
        work_plans=(extract_plan,),
        binding_rules=(rule,),
        binding_evaluations=(issue,),
    )
    assert frontier.binding_issues == (issue,)
    assert frontier.bound_values == ()
    assert frontier.external_binding_complete is False
