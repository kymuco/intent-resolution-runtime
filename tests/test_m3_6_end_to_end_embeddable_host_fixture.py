from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    AdmittedCapabilityCatalogSnapshot,
    AdmittedCapabilityRequirement,
    AdmittedWorkPlan,
    Authorization,
    CandidateAttribution,
    CandidateCapabilityCatalogSnapshot,
    CandidateCapabilityRequirement,
    CandidateResolution,
    CandidateWorkDisposition,
    CapabilityAttempt,
    CapabilityAttemptAttribution,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityCatalogSnapshotAdmissionAttribution,
    CapabilityCatalogSnapshotAdmissionFrontierKind,
    CapabilityCatalogSnapshotProposalAttribution,
    CapabilityDescriptor,
    CapabilityEffect,
    CapabilityEffectRequirement,
    CapabilityExecutionBoundary,
    CapabilityExecutionBoundaryKind,
    CapabilityExecutionBoundaryRequirement,
    CapabilityInvocationRequest,
    CapabilityMatchEvaluation,
    CapabilityOutcome,
    CapabilityOutcomeAttribution,
    CapabilityRequestedEffect,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityRequirementAdmissionAttribution,
    CapabilityRequirementAdmissionFrontierKind,
    CapabilityRequirementProposalAttribution,
    CapabilityScopeRequirement,
    ClaimRecord,
    CognitiveProviderRequest,
    ContextEnvelope,
    DelegatedScope,
    DelegatedWork,
    DelegatedWorkHandoff,
    DelegationHandoffAttribution,
    EvidenceRelation,
    ExecutorReplayBlockedError,
    ExpectedDeliverable,
    GovernanceDecision,
    GovernanceDecisionAttribution,
    GovernanceDecisionComponent,
    GovernanceDecisionKind,
    GovernanceReviewRequest,
    HistoryPersistResult,
    HistoryRecord,
    InMemoryAdmittedHistoryRepository,
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
    WorkContinuationMode,
    WorkDispositionAdmissionAttribution,
    WorkDispositionFrontierKind,
    WorkDispositionKind,
    WorkDispositionProposalAttribution,
    WorkPlan,
    WorkProposal,
    WorkProposalAttribution,
    WorkStep,
    WorkerHandoffRequest,
    WorkerNeed,
    WorkerNeedKind,
    WorkerReplayBlockedError,
    WorkerResult,
    WorkerResultAttribution,
    build_capability_invocation_request,
    build_cognitive_provider_request,
    build_governance_review_request,
    build_worker_handoff_request,
    derive_mechanical_capability_match_evaluation,
    invoke_cognitive_provider,
    invoke_executor,
    invoke_governance,
    invoke_worker,
    orchestrate_attempt_outcome_continuation,
    orchestrate_capability_catalog_snapshot_admission,
    orchestrate_capability_governance,
    orchestrate_capability_requirement_admission,
    orchestrate_initial_resolution,
    orchestrate_work_disposition,
    orchestrate_worker_lifecycle,
)


AUTHORITY_CONTEXT_IDENTITY = RecordIdentity("sha256", "a" * 64)
OUTCOME_SOURCE_IDENTITY = RecordIdentity("sha256", "b" * 64)
OUTCOME_TEMPORAL_IDENTITY = RecordIdentity("sha256", "c" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _persist(repository: InMemoryAdmittedHistoryRepository, record: object) -> None:
    canonical_bytes = record.canonical_bytes()
    result = repository.persist(HistoryRecord.from_canonical_bytes(canonical_bytes))
    assert result is HistoryPersistResult.INSERTED


def _stored_bytes(
    repository: InMemoryAdmittedHistoryRepository, identity: RecordIdentity
) -> bytes:
    stored = repository.get(identity)
    assert stored is not None
    return stored.canonical_record_bytes


def _request_and_context() -> tuple[IntentRequest, ContextEnvelope]:
    request = IntentRequest(
        origin=OriginAttribution(
            kind=OriginKind.HUMAN,
            actor_ref=_ref("irr.actor", "m3-6-human"),
            source_event_ref=_ref("irr.event", "m3-6-user-intent"),
        ),
        principal_ref=_ref("irr.principal", "m3-6-principal"),
        expression=IntentExpression(
            "Publish the exact report artifact to the admitted external target."
        ),
    )
    claim = ClaimRecord(
        attribution=SourceAttribution(
            source_ref=_ref("irr.source", "m3-6-host-input"),
            source_event_ref=_ref("irr.event", "m3-6-context-claim"),
        ),
        statement="The requested artifact is workspace:artifact/report.txt.",
    )
    context = ContextEnvelope(
        intent_request_identity=request.identity,
        boundary_attribution=SourceAttribution(
            source_ref=_ref("irr.host", "m3-6-host"),
            source_event_ref=_ref("irr.event", "m3-6-context-envelope"),
        ),
        records=(claim,),
    )
    return request, context


class RecordingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def propose(self, request: CognitiveProviderRequest) -> CandidateResolution:
        self.calls += 1
        return CandidateResolution(
            intent_request_identity=request.intent_request_identity,
            context_envelope_identity=request.context_envelope_identity,
            attribution=CandidateAttribution(
                provider_ref=request.provider_ref,
                invocation_ref=request.invocation_ref,
            ),
            proposed_semantics=(
                "Publish workspace:artifact/report.txt to the exact admitted external target."
            ),
            assumptions=(),
            issues=(),
            clarification_proposals=(),
            information_need_proposals=(),
        )


def _admit_resolution(
    request: IntentRequest,
    context: ContextEnvelope,
    candidates: tuple[CandidateResolution, ...],
    attribution: ResolutionAttribution,
) -> ResolvedIntent:
    return ResolvedIntent(
        intent_request_identity=request.identity,
        context_envelope_identity=context.identity,
        admission_attribution=attribution,
        semantics=candidates[0].proposed_semantics,
        assumptions=(),
        unresolved_issues=(),
        candidate_inputs=candidates,
    )


def _work_plan(resolved: ResolvedIntent) -> WorkPlan:
    plan_ref = _ref("irr.work_plan", "m3-6-publish")
    step_ref = _ref("irr.work_step", "m3-6-publish")
    completion = "Confirm publication of the exact bounded report artifact."
    step = WorkStep(
        resolved_intent_identity=resolved.identity,
        work_plan_ref=plan_ref,
        step_ref=step_ref,
        operation="artifact.publish",
        scope="workspace:artifact/report.txt",
        inputs=(),
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract=completion,
        description="Publish the exact bounded report artifact.",
    )
    return WorkPlan(
        resolved_intent_identity=resolved.identity,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="Complete the exact bounded publication request.",
        description="M3.6 executable capability-path WorkPlan.",
    )


def _admit_work_plan(resolved: ResolvedIntent, plan: WorkPlan) -> AdmittedWorkPlan:
    candidate = CandidateWorkDisposition(
        resolved_intent_identity=resolved.identity,
        attribution=WorkDispositionProposalAttribution(
            proposer_ref=_ref("irr.proposer", "m3-6-host-planner"),
            proposal_event_ref=_ref("irr.event", "m3-6-work-plan-proposal"),
        ),
        kind=WorkDispositionKind.WORK_PLAN,
        work_plan=plan,
        rationale="The resolved intent requires one bounded operational publication step.",
    )
    unresolved = orchestrate_work_disposition(resolved, candidate_inputs=(candidate,))
    assert unresolved.kind is WorkDispositionFrontierKind.ADMISSION_REQUIRED

    attribution = WorkDispositionAdmissionAttribution(
        resolver_ref=_ref("irr.resolver", "m3-6-work-disposition"),
        admission_event_ref=_ref("irr.event", "m3-6-work-plan-admission"),
    )

    def admitter(
        _: ResolvedIntent,
        candidates: tuple[CandidateWorkDisposition, ...],
        exact_attribution: WorkDispositionAdmissionAttribution,
    ) -> AdmittedWorkPlan:
        return AdmittedWorkPlan(
            resolved_intent_identity=resolved.identity,
            admission_attribution=exact_attribution,
            work_plan=plan,
            candidate_inputs=candidates,
        )

    admitted = orchestrate_work_disposition(
        resolved,
        candidate_inputs=(candidate,),
        admitter=admitter,
        admission_attribution=attribution,
    )
    assert admitted.kind is WorkDispositionFrontierKind.DISPOSITION_OUTPUT_AVAILABLE
    assert type(admitted.disposition_output) is AdmittedWorkPlan
    return admitted.disposition_output


def _admit_requirement(work_plan: WorkPlan) -> AdmittedCapabilityRequirement:
    step = work_plan.steps[0]
    scope = CapabilityRequestedScope(
        scope_ref=_ref("irr.capability_requested_scope", "m3-6-artifact"),
        semantic_type="artifact.path_scope",
        value=step.scope,
        description="The exact report artifact path.",
    )
    effect = CapabilityRequestedEffect(
        effect_ref=_ref("irr.capability_requested_effect", "m3-6-publish"),
        semantic_type="external.publish",
        requested_scope_refs=(scope.scope_ref,),
        description="Publish the exact report artifact to the admitted external target.",
    )
    boundary = CapabilityExecutionBoundaryRequirement(
        kind=CapabilityExecutionBoundaryKind.EXECUTOR,
        boundary_ref=_ref("irr.executor", "m3-6-artifact-executor"),
        description="This exact publication must cross the admitted M3.6 Executor.",
    )
    requirement = CapabilityRequirement(
        work_plan=work_plan,
        step_ref=step.step_ref,
        primary_scope_ref=scope.scope_ref,
        requested_scopes=(scope,),
        requested_effects=(effect,),
        execution_boundary_requirements=(boundary,),
        description="Exact M3.6 publication CapabilityRequirement.",
    )
    candidate = CandidateCapabilityRequirement(
        attribution=CapabilityRequirementProposalAttribution(
            proposer_ref=_ref("irr.proposer", "m3-6-capability-planner"),
            proposal_event_ref=_ref("irr.event", "m3-6-requirement-proposal"),
        ),
        requirement=requirement,
        rationale="The publication step requires the bounded publication capability.",
    )
    unresolved = orchestrate_capability_requirement_admission(
        work_plan,
        step.step_ref,
        candidate_inputs=(candidate,),
    )
    assert (
        unresolved.kind is CapabilityRequirementAdmissionFrontierKind.ADMISSION_REQUIRED
    )

    attribution = CapabilityRequirementAdmissionAttribution(
        resolver_ref=_ref("irr.resolver", "m3-6-capability-requirement"),
        admission_event_ref=_ref("irr.event", "m3-6-requirement-admission"),
    )

    def admitter(
        _: WorkPlan,
        __: WorkStep,
        candidates: tuple[CandidateCapabilityRequirement, ...],
        exact_attribution: CapabilityRequirementAdmissionAttribution,
    ) -> AdmittedCapabilityRequirement:
        return AdmittedCapabilityRequirement(
            admission_attribution=exact_attribution,
            requirement=requirement,
            candidate_inputs=candidates,
        )

    frontier = orchestrate_capability_requirement_admission(
        work_plan,
        step.step_ref,
        candidate_inputs=(candidate,),
        admitter=admitter,
        admission_attribution=attribution,
    )
    assert (
        frontier.kind
        is CapabilityRequirementAdmissionFrontierKind.REQUIREMENT_OUTPUT_AVAILABLE
    )
    assert frontier.admitted_requirement is not None
    return frontier.admitted_requirement


def _admit_catalog(
    admitted_requirement: AdmittedCapabilityRequirement,
) -> AdmittedCapabilityCatalogSnapshot:
    requirement = admitted_requirement.requirement
    requested_scope = requirement.requested_scopes[0]
    requested_effect = requirement.requested_effects[0]
    boundary_requirement = requirement.execution_boundary_requirements[0]
    descriptor_scope = CapabilityScopeRequirement(
        requirement_ref=_ref("irr.capability_scope_requirement", "m3-6-artifact"),
        semantic_type=requested_scope.semantic_type,
        statement="Invocation must remain inside the exact admitted artifact scope.",
    )
    descriptor_effect = CapabilityEffect(
        effect_ref=_ref("irr.capability_effect", "m3-6-external-publish"),
        semantic_type=requested_effect.semantic_type,
        requirement=CapabilityEffectRequirement.UNAVOIDABLE,
        scope_requirement_refs=(descriptor_scope.requirement_ref,),
        description="Publication necessarily creates the requested external effect.",
    )
    descriptor = CapabilityDescriptor(
        capability_ref=_ref("irr.capability", "m3-6-artifact-publish"),
        operation=requirement.work_step.operation,
        input_contracts=(),
        output_contracts=(),
        scope_requirements=(descriptor_scope,),
        effects=(descriptor_effect,),
        execution_boundaries=(
            CapabilityExecutionBoundary(
                boundary_ref=boundary_requirement.boundary_ref,
                kind=CapabilityExecutionBoundaryKind.EXECUTOR,
                description="Exact M3.6 artifact publication Executor boundary.",
            ),
        ),
        completion_contract=requirement.work_step.completion_contract,
        description="Exact bounded M3.6 artifact publication capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", "m3-6"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=_ref("irr.host", "m3-6-capability-catalog"),
            snapshot_event_ref=_ref("irr.event", "m3-6-catalog-snapshot"),
        ),
        scope_statement="M3.6 exact bounded publication fixture catalog.",
        descriptors=(descriptor,),
        description="One exact publication capability for the M3.6 fixture.",
    )
    candidate = CandidateCapabilityCatalogSnapshot(
        attribution=CapabilityCatalogSnapshotProposalAttribution(
            proposer_ref=_ref("irr.proposer", "m3-6-catalog-source"),
            proposal_event_ref=_ref("irr.event", "m3-6-catalog-proposal"),
        ),
        snapshot=snapshot,
        rationale="The embedding Host supplied one bounded catalog candidate.",
    )
    unresolved = orchestrate_capability_catalog_snapshot_admission(
        candidate_inputs=(candidate,)
    )
    assert (
        unresolved.kind
        is CapabilityCatalogSnapshotAdmissionFrontierKind.ADMISSION_REQUIRED
    )
    attribution = CapabilityCatalogSnapshotAdmissionAttribution(
        resolver_ref=_ref("irr.resolver", "m3-6-catalog-admission"),
        admission_event_ref=_ref("irr.event", "m3-6-catalog-admission"),
    )

    def admitter(
        candidates: tuple[CandidateCapabilityCatalogSnapshot, ...],
        exact_attribution: CapabilityCatalogSnapshotAdmissionAttribution,
    ) -> AdmittedCapabilityCatalogSnapshot:
        return AdmittedCapabilityCatalogSnapshot(
            admission_attribution=exact_attribution,
            snapshot=snapshot,
            candidate_inputs=candidates,
        )

    frontier = orchestrate_capability_catalog_snapshot_admission(
        candidate_inputs=(candidate,),
        admitter=admitter,
        admission_attribution=attribution,
    )
    assert (
        frontier.kind
        is CapabilityCatalogSnapshotAdmissionFrontierKind.CATALOG_OUTPUT_AVAILABLE
    )
    assert frontier.admitted_catalog is not None
    return frontier.admitted_catalog


def _proposal(
    work_plan: WorkPlan, evaluation: CapabilityMatchEvaluation
) -> WorkProposal:
    return WorkProposal(
        attribution=WorkProposalAttribution(
            proposer_ref=_ref("irr.proposer", "m3-6-irr"),
            proposal_event_ref=_ref("irr.event", "m3-6-work-proposal"),
        ),
        work_plan=work_plan,
        proposed_steps=(ProposedWorkStep(work_plan.steps[0].step_ref, evaluation),),
        authority_material=(),
        description="Exact M3.6 work proposal for external Governance review.",
    )


class RecordingGovernance:
    def __init__(self) -> None:
        self.calls = 0

    def review(self, request: GovernanceReviewRequest) -> GovernanceDecision:
        self.calls += 1
        proposal = request.proposal
        return GovernanceDecision(
            attribution=GovernanceDecisionAttribution(
                governance_ref=request.governance_ref,
                decision_event_ref=request.decision_event_ref,
                authority_context_ref=request.authority_context_ref,
                authority_context_identity=request.authority_context_identity,
            ),
            proposal=proposal,
            components=(
                GovernanceDecisionComponent(
                    component_ref=_ref("irr.governance_component", "m3-6-authorize"),
                    kind=GovernanceDecisionKind.AUTHORIZE,
                    step_refs=(proposal.proposed_steps[0].step_ref,),
                    directives=(),
                    rationale="The exact bounded publication is authorized.",
                ),
            ),
            description="External Governance reviewed the exact M3.6 WorkProposal.",
        )


class RecordingExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, request: CapabilityInvocationRequest) -> CapabilityOutcome:
        self.calls += 1
        attempt = request.attempt
        lifecycle = OutcomeEvidence(
            evidence_ref=_ref("irr.outcome_evidence", "m3-6-lifecycle"),
            attribution=SourceAttribution(
                source_ref=_ref("executor.source", "m3-6-artifact-executor"),
                source_event_ref=_ref("executor.event", "m3-6-lifecycle"),
            ),
            source_identity=OUTCOME_SOURCE_IDENTITY,
            relation=EvidenceRelation.SUPPORTS,
            roles=(OutcomeEvidenceRole.LIFECYCLE,),
            temporal_basis_refs=(OUTCOME_TEMPORAL_IDENTITY,),
            scope="artifact.publish attempt",
            statement="The exact executor protocol completed normally.",
        )
        receipt = OutcomeEvidence(
            evidence_ref=_ref("irr.outcome_evidence", "m3-6-receipt"),
            attribution=SourceAttribution(
                source_ref=_ref("executor.source", "m3-6-artifact-executor"),
                source_event_ref=_ref("executor.event", "m3-6-receipt"),
            ),
            source_identity=OUTCOME_SOURCE_IDENTITY,
            relation=EvidenceRelation.SUPPORTS,
            roles=(OutcomeEvidenceRole.COMPLETION, OutcomeEvidenceRole.EFFECT),
            temporal_basis_refs=(OUTCOME_TEMPORAL_IDENTITY,),
            scope="artifact.publish attempt",
            statement="Attributable evidence confirms the exact publication.",
        )
        effect_ref = attempt.capability_evaluation.requirement.requested_effects[
            0
        ].effect_ref
        return CapabilityOutcome(
            attribution=CapabilityOutcomeAttribution(
                evaluator_ref=_ref("irr.outcome_evaluator", "m3-6-executor-result"),
                outcome_event_ref=_ref("irr.event", "m3-6-outcome"),
            ),
            attempt=attempt,
            evidence=(lifecycle, receipt),
            lifecycle=OutcomeLifecycleAssessment(
                state=OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
                evidence_refs=(lifecycle.evidence_ref,),
                description="The executor result protocol completed.",
            ),
            completion=OutcomeCompletionAssessment(
                state=OutcomeCompletionState.SATISFIED,
                evidence_refs=(receipt.evidence_ref,),
                description="The exact WorkStep completion contract is satisfied.",
            ),
            effect_assessments=(
                OutcomeEffectAssessment(
                    requested_effect_ref=effect_ref,
                    certainty=OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                    evidence_refs=(receipt.evidence_ref,),
                    description="The requested publication effect is confirmed.",
                ),
            ),
            description="Exact M3.6 publication Outcome.",
        )


def _delegation(resolved: ResolvedIntent, parent: WorkPlan) -> DelegatedWork:
    scope = DelegatedScope(
        scope_ref=_ref("irr.delegated_scope", "m3-6-audit"),
        semantic_type="artifact.path_scope",
        value="workspace:artifact/report.txt",
        description="Exact report artifact scope for the delegated audit.",
    )
    deliverable = ExpectedDeliverable(
        deliverable_ref=_ref("irr.expected_deliverable", "m3-6-audit-note"),
        semantic_type="artifact.audit_note",
        scope_ref=scope.scope_ref,
        description="A bounded audit note for the exact artifact.",
    )
    return DelegatedWork(
        resolved_intent_identity=resolved.identity,
        delegation_ref=_ref("irr.delegated_work", "m3-6-audit"),
        parent_work_plan_identity_refs=(parent.identity,),
        objective=(
            "Inspect the bounded publication context and return an explicit need if "
            "evidence is insufficient."
        ),
        scopes=(scope,),
        context_surface=(),
        allowed_capabilities=(),
        constraints=(),
        expected_deliverables=(deliverable,),
        completion_contract=(
            "Return the exact audit note or an explicit bounded WorkerNeed."
        ),
        description="M3.6 bounded Worker lane.",
    )


class RecordingWorker:
    def __init__(self) -> None:
        self.calls = 0

    def perform(self, request: WorkerHandoffRequest) -> WorkerResult:
        self.calls += 1
        handoff = request.handoff
        return WorkerResult(
            attribution=WorkerResultAttribution(
                worker_ref=handoff.attribution.worker_ref,
                result_event_ref=_ref("irr.event", "m3-6-worker-result"),
            ),
            handoff=handoff,
            materials=(),
            needs=(
                WorkerNeed(
                    need_ref=_ref("irr.worker_need", "m3-6-evidence"),
                    kind=WorkerNeedKind.INFORMATION,
                    related_scope_refs=(handoff.delegated_work.scopes[0].scope_ref,),
                    statement="Additional attributable publication evidence is required.",
                ),
            ),
            description="Worker returned an explicit bounded information need.",
        )


def test_capability_lane_composes_and_replays_without_external_reexecution() -> None:
    repository = InMemoryAdmittedHistoryRepository()
    request, context = _request_and_context()
    provider = RecordingProvider()
    provider_request = build_cognitive_provider_request(
        provider_ref=_ref("irr.provider", "m3-6-provider"),
        invocation_ref=_ref("irr.event", "m3-6-provider-invocation"),
        intent_request=request,
        context_envelope=context,
        disclosed_context_identities=(context.records[0].identity,),
    )
    candidate = invoke_cognitive_provider(
        provider,
        provider_request,
        intent_request=request,
        context_envelope=context,
    )
    assert provider.calls == 1

    unresolved_resolution = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
    )
    assert (
        unresolved_resolution.kind is InitialResolutionFrontierKind.ADMISSION_REQUIRED
    )
    resolution_frontier = orchestrate_initial_resolution(
        request,
        context,
        candidate_inputs=(candidate,),
        admitter=_admit_resolution,
        admission_attribution=ResolutionAttribution(
            resolver_ref=_ref("irr.resolver", "m3-6-resolution"),
            admission_event_ref=_ref("irr.event", "m3-6-resolution-admission"),
        ),
    )
    assert (
        resolution_frontier.kind
        is InitialResolutionFrontierKind.RESOLUTION_OUTPUT_AVAILABLE
    )
    assert type(resolution_frontier.resolution_output) is ResolvedIntent
    resolved = resolution_frontier.resolution_output

    plan = _work_plan(resolved)
    admitted_plan = _admit_work_plan(resolved, plan)
    admitted_requirement = _admit_requirement(admitted_plan.work_plan)
    admitted_catalog = _admit_catalog(admitted_requirement)
    evaluation = derive_mechanical_capability_match_evaluation(
        admitted_requirement,
        admitted_catalog,
        evaluation_event_ref=_ref("irr.event", "m3-6-capability-evaluation"),
    ).evaluation
    proposal = _proposal(admitted_plan.work_plan, evaluation)

    governance = RecordingGovernance()
    governance_request = build_governance_review_request(
        governance_ref=_ref("irr.governance", "m3-6-governance"),
        decision_event_ref=_ref("irr.event", "m3-6-governance-decision"),
        authority_context_ref=_ref("irr.authority_context", "m3-6-authority"),
        authority_context_identity=AUTHORITY_CONTEXT_IDENTITY,
        proposal=proposal,
    )
    decision = invoke_governance(governance, governance_request, proposal=proposal)
    assert governance.calls == 1

    before_authorization = orchestrate_capability_governance(
        admitted_plan.work_plan,
        capability_requirements=(admitted_requirement.requirement,),
        capability_evaluations=(evaluation,),
        work_proposals=(proposal,),
        governance_decisions=(decision,),
    )
    assert before_authorization.authorizations == ()
    assert len(before_authorization.authorization_materialization_frontier) == 1
    authorization = before_authorization.authorization_materialization_frontier[0]

    after_authorization = orchestrate_capability_governance(
        admitted_plan.work_plan,
        capability_requirements=(admitted_requirement.requirement,),
        capability_evaluations=(evaluation,),
        work_proposals=(proposal,),
        governance_decisions=(decision,),
        authorizations=(authorization,),
    )
    assert after_authorization.authorizations == (authorization,)
    assert after_authorization.authorization_materialization_frontier == ()

    attempt = CapabilityAttempt(
        attribution=CapabilityAttemptAttribution(
            executor_ref=admitted_requirement.requirement.execution_boundary_requirements[
                0
            ].boundary_ref,
            attempt_event_ref=_ref("irr.event", "m3-6-attempt"),
        ),
        capability_evaluation=evaluation,
        step_ref=admitted_plan.work_plan.steps[0].step_ref,
        bound_inputs=(),
        presented_authorizations=(authorization,),
        description="One exact authorized M3.6 publication Attempt.",
    )
    executor = RecordingExecutor()
    outcome = invoke_executor(
        executor,
        repository,
        build_capability_invocation_request(attempt),
        attempt=attempt,
    )
    assert executor.calls == 1
    assert repository.get(attempt.identity) is not None
    assert repository.get(outcome.identity) is None

    for record in (
        request,
        context,
        candidate,
        resolved,
        admitted_plan.work_plan,
        admitted_requirement.requirement,
        evaluation,
        proposal,
        decision,
        authorization,
        outcome,
    ):
        if repository.get(record.identity) is None:
            _persist(repository, record)

    replayed_resolved = ResolvedIntent.from_json_bytes(
        _stored_bytes(repository, resolved.identity)
    )
    replayed_plan = WorkPlan.from_json_bytes(_stored_bytes(repository, plan.identity))
    replayed_requirement = CapabilityRequirement.from_json_bytes(
        _stored_bytes(repository, admitted_requirement.requirement.identity)
    )
    replayed_evaluation = CapabilityMatchEvaluation.from_json_bytes(
        _stored_bytes(repository, evaluation.identity)
    )
    replayed_proposal = WorkProposal.from_json_bytes(
        _stored_bytes(repository, proposal.identity)
    )
    replayed_decision = GovernanceDecision.from_json_bytes(
        _stored_bytes(repository, decision.identity)
    )
    replayed_authorization = Authorization.from_json_bytes(
        _stored_bytes(repository, authorization.identity)
    )
    replayed_attempt = CapabilityAttempt.from_json_bytes(
        _stored_bytes(repository, attempt.identity)
    )
    replayed_outcome = CapabilityOutcome.from_json_bytes(
        _stored_bytes(repository, outcome.identity)
    )

    replayed_governance = orchestrate_capability_governance(
        replayed_plan,
        capability_requirements=(replayed_requirement,),
        capability_evaluations=(replayed_evaluation,),
        work_proposals=(replayed_proposal,),
        governance_decisions=(replayed_decision,),
        authorizations=(replayed_authorization,),
    )
    assert replayed_governance.materialized_authorized_step_refs == (
        replayed_plan.steps[0].step_ref,
    )
    assert replayed_governance.authorization_materialization_frontier == ()

    replayed_attempts = orchestrate_attempt_outcome_continuation(
        replayed_resolved,
        attempts=(replayed_attempt,),
        outcomes=(replayed_outcome,),
    )
    assert replayed_attempts.outcome_pending_attempts == ()
    assert replayed_attempts.outcomes_not_selected_for_continuation == (
        replayed_outcome,
    )

    assert provider.calls == 1
    assert governance.calls == 1
    assert executor.calls == 1

    fresh_executor_after_restart = RecordingExecutor()
    with pytest.raises(ExecutorReplayBlockedError, match="automatic reinvocation"):
        invoke_executor(
            fresh_executor_after_restart,
            repository,
            build_capability_invocation_request(replayed_attempt),
            attempt=replayed_attempt,
        )
    assert fresh_executor_after_restart.calls == 0


def test_worker_lane_replays_without_worker_redispatch_or_parent_completion() -> None:
    repository = InMemoryAdmittedHistoryRepository()
    request, context = _request_and_context()
    candidate = CandidateResolution(
        intent_request_identity=request.identity,
        context_envelope_identity=context.identity,
        attribution=CandidateAttribution(
            provider_ref=_ref("irr.provider", "m3-6-worker-fixture"),
            invocation_ref=_ref("irr.event", "m3-6-worker-resolution-proposal"),
        ),
        proposed_semantics="Produce a bounded audit of the exact report artifact.",
        assumptions=(),
        issues=(),
        clarification_proposals=(),
        information_need_proposals=(),
    )
    resolved = _admit_resolution(
        request,
        context,
        (candidate,),
        ResolutionAttribution(
            resolver_ref=_ref("irr.resolver", "m3-6-worker-resolution"),
            admission_event_ref=_ref("irr.event", "m3-6-worker-resolution-admission"),
        ),
    )
    parent = _work_plan(resolved)
    delegated = _delegation(resolved, parent)
    handoff = DelegatedWorkHandoff(
        attribution=DelegationHandoffAttribution(
            dispatcher_ref=_ref("irr.dispatcher", "m3-6-host"),
            worker_ref=_ref("irr.worker", "m3-6-worker"),
            handoff_event_ref=_ref("irr.event", "m3-6-worker-handoff"),
        ),
        delegated_work=delegated,
    )
    worker = RecordingWorker()
    result = invoke_worker(
        worker,
        repository,
        build_worker_handoff_request(handoff),
        handoff=handoff,
    )
    assert worker.calls == 1
    assert repository.get(handoff.identity) is not None
    assert repository.get(result.identity) is None
    assert result.needs[0].kind is WorkerNeedKind.INFORMATION

    for record in (resolved, parent, delegated, result):
        _persist(repository, record)

    replayed_resolved = ResolvedIntent.from_json_bytes(
        _stored_bytes(repository, resolved.identity)
    )
    replayed_parent = WorkPlan.from_json_bytes(
        _stored_bytes(repository, parent.identity)
    )
    replayed_delegated = DelegatedWork.from_json_bytes(
        _stored_bytes(repository, delegated.identity)
    )
    replayed_handoff = DelegatedWorkHandoff.from_json_bytes(
        _stored_bytes(repository, handoff.identity)
    )
    replayed_result = WorkerResult.from_json_bytes(
        _stored_bytes(repository, result.identity)
    )

    replayed_frontier = orchestrate_worker_lifecycle(
        replayed_resolved,
        parent_work_plans=(replayed_parent,),
        delegated_work=(replayed_delegated,),
        handoffs=(replayed_handoff,),
        worker_results=(replayed_result,),
    )
    assert replayed_frontier.result_pending_handoffs == ()
    assert replayed_frontier.results_with_needs == (replayed_result,)
    assert replayed_frontier.results_with_completion_claims == ()
    assert not hasattr(replayed_frontier, "parent_completed")

    assert worker.calls == 1
    fresh_worker_after_restart = RecordingWorker()
    with pytest.raises(WorkerReplayBlockedError, match="automatic redispatch"):
        invoke_worker(
            fresh_worker_after_restart,
            repository,
            build_worker_handoff_request(replayed_handoff),
            handoff=replayed_handoff,
        )
    assert fresh_worker_after_restart.calls == 0
