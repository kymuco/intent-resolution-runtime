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
REPORT_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "3" * 64)
RECIPIENT_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "4" * 64)
AUTHORITY_CONTEXT_IDENTITY = RecordIdentity("sha256", "5" * 64)
OUTCOME_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "6" * 64)
TEMPORAL_BASIS_IDENTITY = RecordIdentity("sha256", "7" * 64)

REPORT_ROOT = r"W:\voice_engine\reports"
SELECTED_REPORT = r"W:\voice_engine\reports\voice-engine-2026-08-31.pdf"
TELEGRAM_DESTINATION_SCOPE = "telegram:user-destinations"
TELEGRAM_DESTINATION = "telegram:chat:primary-user"


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _predecessor() -> ResolvedIntent:
    return ResolvedIntent(
        REQUEST_IDENTITY,
        CONTEXT_IDENTITY,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-b"),
            _ref("irr.resolution_event", "scenario-b-send-resolved"),
        ),
        (
            "Send the exact already-selected Voice Engine report to the exact already-bound "
            "Telegram destination and require recipient-visible completion evidence."
        ),
        (),
        (),
        (),
    )


def _exact_bound_value(
    predecessor: ResolvedIntent,
    *,
    name: str,
    semantic_type: str,
    selection_scope: str,
    value: str,
    input_role: BindingInputRole,
    source_ref: StableRef,
    source_contract_identity: RecordIdentity,
    source_event: str,
    binding_event: str,
) -> BoundValue:
    symbolic = SymbolicReference(
        predecessor.identity,
        _ref("irr.slot", name),
        semantic_type,
        selection_scope,
        f"Exact bound value for Scenario B {name}.",
    )
    binding_input = BindingInput(
        predecessor.identity,
        _ref("irr.binding_input", name),
        SourceAttribution(source_ref, _ref("irr.source_event", source_event)),
        input_role,
        source_contract_identity,
        semantic_type,
        value,
        selection_scope,
        value,
        (),
        (),
        (),
        (),
    )
    rule = BindingRule(
        predecessor.identity,
        _ref("irr.binding_rule", name),
        symbolic,
        (input_role,),
        (source_ref,),
        (source_contract_identity,),
        semantic_type,
        selection_scope,
        (),
        BindingSelectionPolicy(BindingSelectionMode.REQUIRE_UNIQUE),
        f"Require one exact already-admitted Scenario B {name} value.",
        (),
        (),
        (),
    )
    result = evaluate_binding(
        rule,
        (binding_input,),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-b"),
            _ref("irr.event", binding_event),
        ),
    )
    assert type(result) is BoundValue
    return result


def _bindings(predecessor: ResolvedIntent) -> tuple[BoundValue, BoundValue]:
    report = _exact_bound_value(
        predecessor,
        name="selected-report",
        semantic_type="artifact.path",
        selection_scope=REPORT_ROOT,
        value=SELECTED_REPORT,
        input_role=BindingInputRole.PLAN_LOCAL_OUTPUT,
        source_ref=_ref("executor.source", "artifact-search"),
        source_contract_identity=REPORT_SOURCE_CONTRACT_IDENTITY,
        source_event="scenario-b-selected-report",
        binding_event="scenario-b-bind-selected-report",
    )
    recipient = _exact_bound_value(
        predecessor,
        name="telegram-recipient",
        semantic_type="telegram.destination",
        selection_scope=TELEGRAM_DESTINATION_SCOPE,
        value=TELEGRAM_DESTINATION,
        input_role=BindingInputRole.CONTEXT,
        source_ref=_ref("host.context", "telegram-destination"),
        source_contract_identity=RECIPIENT_SOURCE_CONTRACT_IDENTITY,
        source_event="scenario-b-recipient-context",
        binding_event="scenario-b-bind-recipient",
    )
    return report, recipient


def _evaluation(
    predecessor: ResolvedIntent,
    report: BoundValue,
    recipient: BoundValue,
) -> CapabilityMatchEvaluation:
    plan_ref = _ref("irr.work_plan", "scenario-b-send")
    step_ref = _ref("irr.work_step", "send-report")
    completion = (
        "Confirm recipient-visible delivery of the exact selected report to the exact "
        "admitted Telegram destination."
    )
    step = WorkStep(
        predecessor.identity,
        plan_ref,
        step_ref,
        "telegram.send_file",
        recipient.value,
        (
            WorkSymbolicInput("artifact", report.rule.symbolic_reference),
            WorkSymbolicInput("recipient", recipient.rule.symbolic_reference),
        ),
        (),
        (),
        WorkContinuationMode.NONE,
        completion,
        "Send the exact selected report only to the exact bound Telegram destination.",
    )
    plan = WorkPlan(
        predecessor.identity,
        plan_ref,
        (step,),
        "The bounded Telegram send step reaches its own completion contract.",
        "Scenario B lost-acknowledgement lifecycle fixture.",
    )

    report_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "send-report"),
        "artifact.path_scope",
        report.value,
        "Exact selected report scope.",
    )
    recipient_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "send-recipient"),
        "telegram.destination_scope",
        recipient.value,
        "Exact Telegram recipient scope.",
    )
    read_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "send-read"),
        "filesystem.read",
        (report_scope.scope_ref,),
        "Read only the exact selected report.",
    )
    network_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "send-network"),
        "network.use",
        (recipient_scope.scope_ref,),
        "Transmit only toward the exact Telegram destination.",
    )
    disclosure_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "send-disclosure"),
        "external.disclosure",
        (report_scope.scope_ref, recipient_scope.scope_ref),
        "Recipient-visible disclosure of the exact report to the exact destination.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        recipient_scope.scope_ref,
        (report_scope, recipient_scope),
        (read_effect, network_effect, disclosure_effect),
        (),
        "Exact Scenario B telegram.send_file capability requirement.",
    )

    report_requirement = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "send-report"),
        "artifact.path_scope",
        "Artifact reads remain inside one exact report resource.",
    )
    recipient_requirement = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "send-recipient"),
        "telegram.destination_scope",
        "Network/disclosure semantics remain bound to one exact Telegram destination.",
    )
    artifact_input = CapabilityInputContract(
        _ref("irr.capability_input", "send-artifact"),
        "artifact.path",
        (report_requirement.requirement_ref,),
        "Exact report artifact.",
    )
    recipient_input = CapabilityInputContract(
        _ref("irr.capability_input", "send-recipient"),
        "telegram.destination",
        (recipient_requirement.requirement_ref,),
        "Exact Telegram destination.",
    )
    descriptor_read = CapabilityEffect(
        _ref("irr.capability_effect", "send-read"),
        "filesystem.read",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (report_requirement.requirement_ref,),
        "A send invocation exposes report-read semantics.",
    )
    descriptor_network = CapabilityEffect(
        _ref("irr.capability_effect", "send-network"),
        "network.use",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (recipient_requirement.requirement_ref,),
        "A send invocation exposes network-use semantics.",
    )
    descriptor_disclosure = CapabilityEffect(
        _ref("irr.capability_effect", "send-disclosure"),
        "external.disclosure",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (report_requirement.requirement_ref, recipient_requirement.requirement_ref),
        "A completed send exposes recipient-visible external-disclosure semantics.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "telegram.send_file"),
        "telegram.send_file",
        (artifact_input, recipient_input),
        (),
        (report_requirement, recipient_requirement),
        (descriptor_read, descriptor_network, descriptor_disclosure),
        (),
        completion,
        "Exact bounded Telegram file-send capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "scenario-b-send"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "scenario-b-host"),
            _ref("irr.event", "scenario-b-send-catalog"),
        ),
        "Only the exact telegram.send_file capability is admitted for this Attempt fixture.",
        (descriptor,),
        "Scenario B send lifecycle Catalog snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "scenario-b-exact"),
            _ref("irr.event", "scenario-b-send-match"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityScopeMatch(report_scope.scope_ref, report_requirement.requirement_ref),
            CapabilityScopeMatch(
                recipient_scope.scope_ref,
                recipient_requirement.requirement_ref,
            ),
        ),
        (
            CapabilityInputMatch(
                "artifact",
                artifact_input.input_ref,
                (report_scope.scope_ref,),
            ),
            CapabilityInputMatch(
                "recipient",
                recipient_input.input_ref,
                (recipient_scope.scope_ref,),
            ),
        ),
        (),
        (
            CapabilityEffectMatch(read_effect.effect_ref, descriptor_read.effect_ref),
            CapabilityEffectMatch(network_effect.effect_ref, descriptor_network.effect_ref),
            CapabilityEffectMatch(
                disclosure_effect.effect_ref,
                descriptor_disclosure.effect_ref,
            ),
        ),
        "Exact Scenario B telegram.send_file match.",
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-b"),
            _ref("irr.event", "scenario-b-send-evaluation"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for Scenario B send Attempt.",
    )
    assert evaluate_capability_match_evaluation(evaluation) == match
    return evaluation


def _authorization(
    evaluation: CapabilityMatchEvaluation,
    report: BoundValue,
    recipient: BoundValue,
) -> Authorization:
    step_ref = evaluation.requirement.step_ref
    proposal = WorkProposal(
        WorkProposalAttribution(
            _ref("irr.proposer", "irr-core"),
            _ref("irr.event", "scenario-b-send-proposal"),
        ),
        evaluation.requirement.work_plan,
        (ProposedWorkStep(step_ref, evaluation),),
        (
            WorkProposalMaterial(
                _ref("irr.work_proposal_material", "report"),
                WorkProposalMaterialKind.AFFECTED_RESOURCE,
                (step_ref,),
                _ref("irr.source", "scenario-b-report-binding"),
                report.identity,
                report.value,
                "The exact selected report may be read and externally disclosed.",
            ),
            WorkProposalMaterial(
                _ref("irr.work_proposal_material", "recipient"),
                WorkProposalMaterialKind.RECIPIENT,
                (step_ref,),
                _ref("irr.source", "scenario-b-recipient-binding"),
                recipient.identity,
                recipient.value,
                "The exact attributable Telegram destination is the recipient.",
            ),
            WorkProposalMaterial(
                _ref("irr.work_proposal_material", "disclosure"),
                WorkProposalMaterialKind.DISCLOSURE,
                (step_ref,),
                _ref("irr.source", "scenario-b-send-semantics"),
                evaluation.requirement.identity,
                f"{report.value} -> {recipient.value}",
                "The exact report may leave the local boundary for the exact recipient.",
            ),
            WorkProposalMaterial(
                _ref("irr.work_proposal_material", "data-flow"),
                WorkProposalMaterialKind.DATA_FLOW,
                (step_ref,),
                _ref("irr.source", "scenario-b-send-semantics"),
                evaluation.requirement.identity,
                f"local-report -> {recipient.value}",
                "Network transfer carries the exact report toward Telegram.",
            ),
        ),
        "Present exact recipient/disclosure semantics to external Governance.",
    )
    component = GovernanceDecisionComponent(
        _ref("irr.governance_component", "authorize-send"),
        GovernanceDecisionKind.AUTHORIZE,
        (step_ref,),
        (),
        "Authorize only the exact represented Telegram send Attempt semantics.",
    )
    decision = GovernanceDecision(
        GovernanceDecisionAttribution(
            _ref("irr.governance", "scenario-b-governance"),
            _ref("irr.event", "scenario-b-send-decision"),
            _ref("irr.authority_context", "scenario-b"),
            AUTHORITY_CONTEXT_IDENTITY,
        ),
        proposal,
        (component,),
        "Exact Governance decision for Scenario B Telegram disclosure.",
    )
    return Authorization(decision, component.component_ref)


def _attempt(predecessor: ResolvedIntent) -> tuple[CapabilityAttempt, Authorization]:
    report, recipient = _bindings(predecessor)
    evaluation = _evaluation(predecessor, report, recipient)
    authorization = _authorization(evaluation, report, recipient)
    attempt = CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", "telegram-send"),
            _ref("irr.event", "scenario-b-send-attempt"),
        ),
        evaluation,
        evaluation.requirement.step_ref,
        (
            AttemptBoundInput("artifact", report),
            AttemptBoundInput("recipient", recipient),
        ),
        (authorization,),
        "One attributable authorized Telegram send Attempt.",
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
            _ref("executor.source", "telegram-send"),
            _ref("executor.event", name),
        ),
        OUTCOME_SOURCE_CONTRACT_IDENTITY,
        EvidenceRelation.SUPPORTS,
        roles,
        (TEMPORAL_BASIS_IDENTITY,),
        "Scenario B telegram.send_file Attempt",
        statement,
    )


def _unknown_outcome(attempt: CapabilityAttempt) -> CapabilityOutcome:
    local_read = _evidence(
        "scenario-b-report-read",
        (OutcomeEvidenceRole.EFFECT,),
        "The exact selected report was read locally for transmission.",
    )
    transmitted = _evidence(
        "scenario-b-request-transmitted",
        (OutcomeEvidenceRole.TRANSPORT, OutcomeEvidenceRole.EFFECT),
        "The send request bytes were transmitted toward Telegram transport.",
    )
    lost_ack = _evidence(
        "scenario-b-ack-lost",
        (
            OutcomeEvidenceRole.LIFECYCLE,
            OutcomeEvidenceRole.UNCERTAINTY,
            OutcomeEvidenceRole.TRANSPORT,
        ),
        "The connection/lifecycle was interrupted before material recipient-visible acknowledgement.",
    )
    effects = {
        item.semantic_type: item
        for item in attempt.capability_evaluation.requirement.requested_effects
    }
    return CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "scenario-b"),
            _ref("irr.event", "scenario-b-send-outcome-unknown"),
        ),
        attempt,
        (lost_ack, transmitted, local_read),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.INTERRUPTED,
            (lost_ack.evidence_ref,),
            "The normal result lifecycle was interrupted before a material acknowledgement.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.UNKNOWN,
            (lost_ack.evidence_ref,),
            "Available evidence cannot establish recipient-visible delivery completion.",
        ),
        (
            OutcomeEffectAssessment(
                effects["filesystem.read"].effect_ref,
                OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                (local_read.evidence_ref,),
                "The local report-read effect is confirmed.",
            ),
            OutcomeEffectAssessment(
                effects["network.use"].effect_ref,
                OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                (transmitted.evidence_ref,),
                "Network transmission toward Telegram is confirmed.",
            ),
            OutcomeEffectAssessment(
                effects["external.disclosure"].effect_ref,
                OutcomeEffectCertainty.UNKNOWN,
                (lost_ack.evidence_ref,),
                "Recipient-visible external disclosure cannot be established from transport evidence.",
            ),
        ),
        "Interrupted Telegram send with material unknown recipient-visible outcome.",
    )


def _successor_lineage(
    predecessor: ResolvedIntent,
    outcome: CapabilityOutcome,
) -> tuple[ContinuationInput, ResolvedIntent, SuccessorResolutionLineage]:
    continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "scenario-b-host"),
            _ref("irr.event", "scenario-b-reentry-unknown-send"),
        ),
        ContinuationSourceKind.CAPABILITY_OUTCOME,
        outcome,
    )
    successor = ResolvedIntent(
        predecessor.intent_request_identity,
        predecessor.context_envelope_identity,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-b"),
            _ref("irr.resolution_event", "scenario-b-after-unknown-send"),
        ),
        (
            "Acquire attributable bounded send-status or completion evidence before any "
            "new Telegram send Attempt; do not resend from transport uncertainty alone."
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
    outcome = _unknown_outcome(attempt)
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


def test_scenario_b_lost_ack_preserves_known_transport_and_unknown_delivery() -> None:
    fixture = _fixture()
    attempt = fixture["attempt"]
    authorization = fixture["authorization"]
    outcome = fixture["outcome"]
    continuation = fixture["continuation"]
    lineage = fixture["lineage"]

    assert isinstance(attempt, CapabilityAttempt)
    assert isinstance(authorization, Authorization)
    assert isinstance(outcome, CapabilityOutcome)
    assert isinstance(continuation, ContinuationInput)
    assert isinstance(lineage, SuccessorResolutionLineage)

    assert attempt.presented_authorizations == (authorization,)
    assert outcome.lifecycle.state is OutcomeLifecycleState.INTERRUPTED
    assert outcome.completion.state is OutcomeCompletionState.UNKNOWN
    assert outcome.has_material_unknown is True

    requested = {
        item.semantic_type: item.effect_ref
        for item in attempt.capability_evaluation.requirement.requested_effects
    }
    certainties = {
        item.requested_effect_ref: item.certainty
        for item in outcome.effect_assessments
    }
    assert certainties[requested["filesystem.read"]] is OutcomeEffectCertainty.CONFIRMED_OCCURRED
    assert certainties[requested["network.use"]] is OutcomeEffectCertainty.CONFIRMED_OCCURRED
    assert certainties[requested["external.disclosure"]] is OutcomeEffectCertainty.UNKNOWN

    assert continuation.source == outcome
    assert continuation.source_identity == outcome.identity
    assert lineage.predecessor == fixture["predecessor"]
    assert lineage.continuation_inputs == (continuation,)
    assert lineage.successor == fixture["successor"]


def test_scenario_b_transport_evidence_is_not_completion_evidence() -> None:
    outcome = _fixture()["outcome"]
    assert isinstance(outcome, CapabilityOutcome)
    by_ref = {item.evidence_ref: item for item in outcome.evidence}
    completion_evidence = [by_ref[ref] for ref in outcome.completion.evidence_refs]
    assert all(OutcomeEvidenceRole.COMPLETION not in item.roles for item in completion_evidence)
    assert all(OutcomeEvidenceRole.UNCERTAINTY in item.roles for item in completion_evidence)
    transport_items = [
        item for item in outcome.evidence if OutcomeEvidenceRole.TRANSPORT in item.roles
    ]
    assert transport_items
    assert all(OutcomeEvidenceRole.COMPLETION not in item.roles for item in transport_items)


def test_scenario_b_unknown_send_surface_has_no_hidden_resend_or_retry_fields() -> None:
    fixture = _fixture()
    for record_name in ("outcome", "continuation", "lineage"):
        record = fixture[record_name]
        keys = _all_keys(record.to_primitive())  # type: ignore[attr-defined]
        assert "retry" not in keys
        assert "resend" not in keys
        assert "fallback" not in keys
        assert "safe_to_retry" not in keys
        assert "parent_complete" not in keys
