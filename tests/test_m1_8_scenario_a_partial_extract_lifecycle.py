from __future__ import annotations

from intent_resolution_runtime import (
    AttemptBoundInput,
    Authorization,
    BindingAttribution,
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
    CapabilityRequestedEffect,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    EvidenceRelation,
    GovernanceDecision,
    GovernanceDecisionAttribution,
    GovernanceDecisionComponent,
    GovernanceDecisionKind,
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
    WorkPlan,
    WorkProposal,
    WorkProposalAttribution,
    WorkProposalMaterial,
    WorkProposalMaterialKind,
    WorkStep,
    WorkSymbolicInput,
    evaluate_binding,
    evaluate_capability_match_evaluation,
)

REQUEST_IDENTITY = RecordIdentity("sha256", "1" * 64)
CONTEXT_IDENTITY = RecordIdentity("sha256", "2" * 64)
SEARCH_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "3" * 64)
OUTCOME_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "4" * 64)
AUTHORITY_CONTEXT_IDENTITY = RecordIdentity("sha256", "5" * 64)
TEMPORAL_BASIS_IDENTITY = RecordIdentity("sha256", "6" * 64)
BACKUP_ROOT = r"D:\Backups"
DESTINATION = r"W:\organism_lab"
SELECTED_BACKUP = r"D:\Backups\organism_lab-2026-08-31.zip"


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _predecessor() -> ResolvedIntent:
    return ResolvedIntent(
        REQUEST_IDENTITY,
        CONTEXT_IDENTITY,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-a"),
            _ref("irr.resolution_event", "scenario-a-before-extract"),
        ),
        (
            "Extract the exact already-selected organism_lab backup into the exact "
            "admitted destination and preserve scoped outcome evidence."
        ),
        (),
        (),
        (),
    )


def _binding(predecessor: ResolvedIntent) -> BoundValue:
    symbolic = SymbolicReference(
        predecessor.identity,
        _ref("irr.slot", "selected-backup"),
        "artifact.path",
        BACKUP_ROOT,
        "Exact backup selected by the already-admitted latest rule.",
    )
    source_ref = _ref("executor.source", "filesystem-search")
    binding_input = BindingInput(
        predecessor.identity,
        _ref("irr.binding_input", "selected-backup"),
        SourceAttribution(
            source_ref,
            _ref("executor.event", "scenario-a-selected-backup-result"),
        ),
        BindingInputRole.PLAN_LOCAL_OUTPUT,
        SEARCH_SOURCE_CONTRACT_IDENTITY,
        "artifact.path",
        SELECTED_BACKUP,
        BACKUP_ROOT,
        SELECTED_BACKUP,
        (),
        (),
        (),
        (),
    )
    rule = BindingRule(
        predecessor.identity,
        _ref("irr.binding_rule", "selected-backup-exact"),
        symbolic,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (source_ref,),
        (SEARCH_SOURCE_CONTRACT_IDENTITY,),
        "artifact.path",
        BACKUP_ROOT,
        (),
        BindingSelectionPolicy(BindingSelectionMode.REQUIRE_UNIQUE),
        "Require the one exact already-selected backup value for this Attempt.",
        (),
        (),
        (),
    )
    result = evaluate_binding(
        rule,
        (binding_input,),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-a"),
            _ref("irr.event", "scenario-a-bind-selected-backup"),
        ),
    )
    assert type(result) is BoundValue
    return result


def _evaluation(predecessor: ResolvedIntent, bound: BoundValue) -> CapabilityMatchEvaluation:
    plan_ref = _ref("irr.work_plan", "scenario-a-extract")
    step_ref = _ref("irr.work_step", "extract-archive")
    step = WorkStep(
        predecessor.identity,
        plan_ref,
        step_ref,
        "archive.extract",
        DESTINATION,
        (
            WorkSymbolicInput("archive", bound.rule.symbolic_reference),
            WorkLiteralInput("destination", "filesystem.path", DESTINATION),
        ),
        (),
        (),
        WorkContinuationMode.NONE,
        "Return a scoped extraction result for the exact destination.",
        "Extract only the exact selected backup into the exact admitted destination.",
    )
    plan = WorkPlan(
        predecessor.identity,
        plan_ref,
        (step,),
        "The bounded archive.extract step reaches its own completion contract.",
        "Scenario A extract lifecycle fixture.",
    )
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "extract-destination"),
        "filesystem.path_scope",
        DESTINATION,
        "Exact restore destination for archive.extract.",
    )
    read_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "extract-read"),
        "filesystem.read",
        (requested_scope.scope_ref,),
        "Read the selected archive as required by extraction.",
    )
    write_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "extract-write"),
        "filesystem.write",
        (requested_scope.scope_ref,),
        "Write extracted material only inside the exact destination.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        requested_scope.scope_ref,
        (requested_scope,),
        (read_effect, write_effect),
        (),
        "Exact Scenario A archive.extract capability requirement.",
    )

    scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "extract-destination"),
        "filesystem.path_scope",
        "Invocation must remain inside the exact restore destination.",
    )
    archive_input = CapabilityInputContract(
        _ref("irr.capability_input", "extract-archive"),
        "artifact.path",
        (),
        "Exact selected archive path.",
    )
    destination_input = CapabilityInputContract(
        _ref("irr.capability_input", "extract-destination"),
        "filesystem.path",
        (),
        "Exact restore destination.",
    )
    descriptor_read = CapabilityEffect(
        _ref("irr.capability_effect", "extract-read"),
        "filesystem.read",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (scope.requirement_ref,),
        "Extraction necessarily reads the selected archive.",
    )
    descriptor_write = CapabilityEffect(
        _ref("irr.capability_effect", "extract-write"),
        "filesystem.write",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (scope.requirement_ref,),
        "Extraction may materialize files inside the exact destination.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "archive.extract.local"),
        "archive.extract",
        (archive_input, destination_input),
        (),
        (scope,),
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
        "Only the exact archive.extract capability admitted for this lifecycle fixture.",
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
        (CapabilityScopeMatch(requested_scope.scope_ref, scope.requirement_ref),),
        (
            CapabilityInputMatch("archive", archive_input.input_ref, ()),
            CapabilityInputMatch("destination", destination_input.input_ref, ()),
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
    return evaluation


def _authorization(evaluation: CapabilityMatchEvaluation) -> Authorization:
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
                _ref("irr.work_proposal_material", "extract-destination"),
                WorkProposalMaterialKind.AFFECTED_RESOURCE,
                (step_ref,),
                _ref("irr.source", "scenario-a-context"),
                CONTEXT_IDENTITY,
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
    return Authorization(decision, component.component_ref)


def _attempt(predecessor: ResolvedIntent) -> tuple[CapabilityAttempt, Authorization]:
    bound = _binding(predecessor)
    evaluation = _evaluation(predecessor, bound)
    authorization = _authorization(evaluation)
    attempt = CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", "archive-extract-local"),
            _ref("irr.event", "scenario-a-extract-attempt"),
        ),
        evaluation,
        evaluation.requirement.step_ref,
        (AttemptBoundInput("archive", bound),),
        (authorization,),
        "One attributable authorized archive.extract Attempt.",
    )
    return attempt, authorization


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


def _successor_lineage(
    predecessor: ResolvedIntent,
    outcome: CapabilityOutcome,
) -> tuple[ContinuationInput, ResolvedIntent, SuccessorResolutionLineage]:
    continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "scenario-a-host"),
            _ref("irr.event", "scenario-a-reentry-after-partial-extract"),
        ),
        ContinuationSourceKind.CAPABILITY_OUTCOME,
        outcome,
    )
    successor = ResolvedIntent(
        predecessor.intent_request_identity,
        predecessor.context_envelope_identity,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-a"),
            _ref("irr.resolution_event", "scenario-a-after-partial-extract"),
        ),
        (
            "Inspect the exact destination state after the partial extraction before any "
            "further recovery action; the prior failed Attempt is not retried implicitly."
        ),
        (),
        (),
        (),
    )
    lineage = SuccessorResolutionLineage(
        predecessor,
        (continuation,),
        SuccessorResolutionKind.RESOLVED_INTENT,
        successor,
    )
    return continuation, successor, lineage


def _fixture() -> dict[str, object]:
    predecessor = _predecessor()
    attempt, authorization = _attempt(predecessor)
    outcome = _partial_outcome(attempt)
    continuation, successor, lineage = _successor_lineage(predecessor, outcome)
    return {
        "predecessor": predecessor,
        "attempt": attempt,
        "authorization": authorization,
        "outcome": outcome,
        "continuation": continuation,
        "successor": successor,
        "lineage": lineage,
    }


def _all_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys.update(_all_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_all_keys(item))
    return keys


def test_scenario_a_partial_extract_preserves_scoped_effects_and_returns_to_irr() -> None:
    fixture = _fixture()
    attempt = fixture["attempt"]
    authorization = fixture["authorization"]
    outcome = fixture["outcome"]
    continuation = fixture["continuation"]
    successor = fixture["successor"]
    lineage = fixture["lineage"]

    assert isinstance(attempt, CapabilityAttempt)
    assert isinstance(authorization, Authorization)
    assert isinstance(outcome, CapabilityOutcome)
    assert isinstance(continuation, ContinuationInput)
    assert isinstance(successor, ResolvedIntent)
    assert isinstance(lineage, SuccessorResolutionLineage)

    assert attempt.presented_authorizations == (authorization,)
    assert authorization.decision.components[0].kind is GovernanceDecisionKind.AUTHORIZE
    assert outcome.lifecycle.state is OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED
    assert outcome.completion.state is OutcomeCompletionState.NOT_SATISFIED

    certainties = {
        assessment.requested_effect_ref: assessment.certainty
        for assessment in outcome.effect_assessments
    }
    requested = {
        item.semantic_type: item.effect_ref
        for item in attempt.capability_evaluation.requirement.requested_effects
    }
    assert certainties[requested["filesystem.read"]] is OutcomeEffectCertainty.CONFIRMED_OCCURRED
    assert certainties[requested["filesystem.write"]] is OutcomeEffectCertainty.CONFIRMED_PARTIAL

    assert continuation.source == outcome
    assert continuation.source_identity == outcome.identity
    assert lineage.predecessor == fixture["predecessor"]
    assert lineage.continuation_inputs == (continuation,)
    assert lineage.successor == successor
    assert successor.identity != fixture["predecessor"].identity


def test_scenario_a_failed_completion_does_not_become_no_effect_or_parent_success() -> None:
    outcome = _fixture()["outcome"]
    assert isinstance(outcome, CapabilityOutcome)
    assert outcome.completion.state is OutcomeCompletionState.NOT_SATISFIED
    assert any(
        assessment.certainty is OutcomeEffectCertainty.CONFIRMED_PARTIAL
        for assessment in outcome.effect_assessments
    )
    assert outcome.has_material_unknown is False


def test_scenario_a_partial_extract_recovery_surface_has_no_hidden_retry_or_fallback_fields() -> None:
    fixture = _fixture()
    for record_name in ("outcome", "continuation", "lineage"):
        record = fixture[record_name]
        keys = _all_keys(record.to_primitive())  # type: ignore[attr-defined]
        assert "retry" not in keys
        assert "retry_attempt" not in keys
        assert "fallback" not in keys
        assert "parent_complete" not in keys
