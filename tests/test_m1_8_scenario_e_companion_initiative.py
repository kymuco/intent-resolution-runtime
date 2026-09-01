from __future__ import annotations

from intent_resolution_runtime import (
    CapabilityAttempt,
    CapabilityAttemptAttribution,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityInputContract,
    CapabilityInputMatch,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    CapabilityOutcome,
    CapabilityOutcomeAttribution,
    EvidenceRelation,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    OutcomeCompletionAssessment,
    OutcomeCompletionState,
    OutcomeEvidence,
    OutcomeEvidenceRole,
    OutcomeLifecycleAssessment,
    OutcomeLifecycleState,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    WorkContinuationMode,
    WorkLiteralInput,
    WorkPlan,
    WorkStep,
    evaluate_capability_match_evaluation,
)


CONTEXT_IDENTITY = RecordIdentity("sha256", "2" * 64)
OUTCOME_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "3" * 64)
TEMPORAL_BASIS_IDENTITY = RecordIdentity("sha256", "4" * 64)
LOG_SCOPE = r"W:\logs\organism_lab"


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> dict[str, object]:
    request = IntentRequest(
        origin=OriginAttribution(
            OriginKind.COMPANION,
            _ref("companion", "kaguya"),
            _ref("companion.event", "scenario-e-initiative"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression("Стоит проверить последние логи."),
    )
    resolved = ResolvedIntent(
        request.identity,
        CONTEXT_IDENTITY,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-e"),
            _ref("irr.resolution_event", "scenario-e-resolved"),
        ),
        (
            "Inspect only the explicitly admitted organism_lab log scope; companion initiative "
            "does not grant authority or ambient filesystem access."
        ),
        (),
        (),
        (),
    )

    plan_ref = _ref("irr.work_plan", "scenario-e-log-inspection")
    step_ref = _ref("irr.work_step", "inspect-logs")
    step = WorkStep(
        resolved.identity,
        plan_ref,
        step_ref,
        "logs.inspect",
        LOG_SCOPE,
        (WorkLiteralInput("scope", "filesystem.path_scope", LOG_SCOPE),),
        (),
        (),
        WorkContinuationMode.NONE,
        "Return attributable bounded log-inspection material.",
        "Inspect only the exact admitted log scope.",
    )
    plan = WorkPlan(
        resolved.identity,
        plan_ref,
        (step,),
        "The bounded log inspection returns attributable completion material.",
        "Scenario E bounded companion-initiated log inspection.",
    )

    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "logs"),
        "filesystem.path_scope",
        LOG_SCOPE,
        "Exact admitted log scope.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        requested_scope.scope_ref,
        (requested_scope,),
        (),
        (),
        "Exact authority-neutral log inspection requirement.",
    )
    descriptor_scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "logs"),
        "filesystem.path_scope",
        "Inspection remains inside the exact supplied log scope.",
    )
    descriptor_input = CapabilityInputContract(
        _ref("irr.capability_input", "scope"),
        "filesystem.path_scope",
        (descriptor_scope.requirement_ref,),
        "Exact bounded log scope input.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "logs.inspect.local"),
        "logs.inspect",
        (descriptor_input,),
        (),
        (descriptor_scope,),
        (),
        (),
        step.completion_contract,
        "Read-only bounded local log inspection capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "scenario-e"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "scenario-e-host"),
            _ref("irr.event", "scenario-e-catalog"),
        ),
        "Only the exact bounded log-inspection capability applicable here.",
        (descriptor,),
        "Scenario E capability snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "scenario-e"),
            _ref("irr.event", "scenario-e-match"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (CapabilityScopeMatch(requested_scope.scope_ref, descriptor_scope.requirement_ref),),
        (
            CapabilityInputMatch(
                "scope",
                descriptor_input.input_ref,
                (requested_scope.scope_ref,),
            ),
        ),
        (),
        (),
        "Exact Scenario E log-inspection match.",
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-e"),
            _ref("irr.event", "scenario-e-evaluation"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for the bounded inspection.",
    )
    assert evaluate_capability_match_evaluation(evaluation) == match

    attempt = CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", "local-log-inspector"),
            _ref("irr.event", "scenario-e-attempt"),
        ),
        evaluation,
        step_ref,
        (),
        (),
        "One attributable authority-neutral read-only log inspection Attempt.",
    )
    completion_evidence = OutcomeEvidence(
        _ref("irr.outcome_evidence", "scenario-e-inspection-complete"),
        SourceAttribution(
            _ref("executor.source", "local-log-inspector"),
            _ref("executor.event", "scenario-e-inspection-result"),
        ),
        OUTCOME_SOURCE_CONTRACT_IDENTITY,
        EvidenceRelation.SUPPORTS,
        (OutcomeEvidenceRole.LIFECYCLE, OutcomeEvidenceRole.COMPLETION),
        (TEMPORAL_BASIS_IDENTITY,),
        LOG_SCOPE,
        "The bounded local log inspection returned its admitted completion material.",
    )
    outcome = CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "scenario-e"),
            _ref("irr.event", "scenario-e-outcome"),
        ),
        attempt,
        (completion_evidence,),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
            (completion_evidence.evidence_ref,),
            "The bounded inspection result protocol completed normally.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.SATISFIED,
            (completion_evidence.evidence_ref,),
            "The exact inspection completion contract is satisfied.",
        ),
        (),
        "Scoped Scenario E log-inspection outcome.",
    )
    return {
        "request": request,
        "resolved": resolved,
        "plan": plan,
        "evaluation": evaluation,
        "attempt": attempt,
        "outcome": outcome,
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


def test_scenario_e_companion_origin_remains_distinct_from_user_principal() -> None:
    fixture = _fixture()
    request = fixture["request"]
    assert isinstance(request, IntentRequest)

    assert request.origin.kind is OriginKind.COMPANION
    assert request.origin.actor_ref == _ref("companion", "kaguya")
    assert request.principal_ref == _ref("principal", "user")
    assert request.origin.actor_ref != request.principal_ref


def test_scenario_e_companion_initiative_does_not_create_authority_or_ambient_scope() -> None:
    fixture = _fixture()
    plan = fixture["plan"]
    attempt = fixture["attempt"]
    assert isinstance(plan, WorkPlan)
    assert isinstance(attempt, CapabilityAttempt)

    assert plan.steps[0].scope == LOG_SCOPE
    assert attempt.presented_authorizations == ()

    keys = set()
    for name in ("request", "resolved", "plan", "evaluation", "attempt"):
        record = fixture[name]
        keys.update(_all_keys(record.to_primitive()))  # type: ignore[attr-defined]
    for forbidden in (
        "standing_grant",
        "relationship_authority",
        "ambient_filesystem",
        "ambient_memory",
        "authorized",
    ):
        assert forbidden not in keys


def test_scenario_e_result_provenance_remains_with_actual_executor_not_companion_or_human() -> None:
    fixture = _fixture()
    request = fixture["request"]
    attempt = fixture["attempt"]
    outcome = fixture["outcome"]
    assert isinstance(request, IntentRequest)
    assert isinstance(attempt, CapabilityAttempt)
    assert isinstance(outcome, CapabilityOutcome)

    assert attempt.attribution.executor_ref == _ref("irr.executor", "local-log-inspector")
    assert attempt.attribution.executor_ref != request.origin.actor_ref
    assert outcome.evidence[0].attribution.source_ref == _ref(
        "executor.source", "local-log-inspector"
    )
    assert outcome.completion.state is OutcomeCompletionState.SATISFIED


def test_scenario_e_outcome_round_trip_preserves_nonhuman_origin_lineage() -> None:
    fixture = _fixture()
    request = fixture["request"]
    outcome = fixture["outcome"]
    assert isinstance(request, IntentRequest)
    assert isinstance(outcome, CapabilityOutcome)

    decoded = CapabilityOutcome.from_json_bytes(outcome.canonical_bytes())
    assert decoded == outcome
    assert decoded.identity == outcome.identity
    assert request.origin.kind is OriginKind.COMPANION
