from __future__ import annotations

from intent_resolution_runtime import (
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
    CapabilityRequestedEffect,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    GovernanceDecision,
    GovernanceDecisionAttribution,
    GovernanceDecisionComponent,
    GovernanceDecisionKind,
    ProposedWorkStep,
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
REPORT_SEARCH_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "3" * 64)
TELEGRAM_DESTINATION_SOURCE_CONTRACT_IDENTITY = RecordIdentity("sha256", "4" * 64)
AUTHORITY_CONTEXT_IDENTITY = RecordIdentity("sha256", "5" * 64)

REPORT_ROOT = r"W:\voice_engine\reports"
REPORT_FAMILY = "Voice Engine report"
REPORT_SELECTION_SCOPE = REPORT_ROOT
TELEGRAM_DESTINATION_SCOPE = "telegram:user-destinations"
TELEGRAM_DESTINATION = "telegram:chat:primary-user"
SELECTED_REPORT = r"W:\voice_engine\reports\voice-engine-2026-08-31.pdf"


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _resolved() -> ResolvedIntent:
    return ResolvedIntent(
        REQUEST_IDENTITY,
        CONTEXT_IDENTITY,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-b"),
            _ref("irr.resolution_event", "scenario-b-resolved"),
        ),
        (
            "Select the latest Voice Engine report under the admitted bounded ordering "
            "rule and send that exact report only to an explicit attributable Telegram "
            "destination; principal identity alone does not bind the recipient."
        ),
        (),
        (),
        (),
    )


def _search_plan(resolved: ResolvedIntent) -> tuple[WorkPlan, WorkStep]:
    plan_ref = _ref("irr.work_plan", "scenario-b-search")
    candidates = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "report-candidates"),
        "artifact.path_set",
        REPORT_SELECTION_SCOPE,
        "Bounded Voice Engine report candidate set.",
    )
    step = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "search-reports"),
        "artifact.search",
        REPORT_ROOT,
        (
            WorkLiteralInput("root", "filesystem.directory", REPORT_ROOT),
            WorkLiteralInput("family", "artifact.family", REPORT_FAMILY),
        ),
        (WorkOutput("candidates", candidates),),
        (),
        WorkContinuationMode.RETURN_TO_IRR,
        "Return the complete bounded matching report candidate set.",
        "Bounded Scenario B report discovery.",
    )
    return (
        WorkPlan(
            resolved.identity,
            plan_ref,
            (step,),
            "The bounded report candidate set has returned to IRR.",
            "Scenario B report search phase.",
        ),
        step,
    )


def _report_rule(resolved: ResolvedIntent) -> BindingRule:
    selected = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "selected-report"),
        "artifact.path",
        REPORT_SELECTION_SCOPE,
        "Latest Voice Engine report under the frozen timestamp rule.",
    )
    return BindingRule(
        resolved.identity,
        _ref("irr.binding_rule", "latest-report"),
        selected,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (_ref("executor.source", "artifact-search"),),
        (REPORT_SEARCH_SOURCE_CONTRACT_IDENTITY,),
        "artifact.path",
        REPORT_SELECTION_SCOPE,
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.MAX_ATTRIBUTE,
            ("modification_time",),
            (BindingAttributeKind.RFC3339_TIMESTAMP,),
        ),
        "Select one unique greatest admitted report timestamp.",
        (),
        (),
        (),
    )


def _report_candidate(
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
            _ref("executor.source", "artifact-search"),
            _ref("executor.event", f"scenario-b-report-{name}"),
        ),
        BindingInputRole.PLAN_LOCAL_OUTPUT,
        REPORT_SEARCH_SOURCE_CONTRACT_IDENTITY,
        "artifact.path",
        value,
        REPORT_SELECTION_SCOPE,
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


def _recipient_rule(resolved: ResolvedIntent) -> BindingRule:
    recipient = SymbolicReference(
        resolved.identity,
        _ref("irr.slot", "telegram-recipient"),
        "telegram.destination",
        TELEGRAM_DESTINATION_SCOPE,
        "Explicit attributable Telegram destination for this send.",
    )
    return BindingRule(
        resolved.identity,
        _ref("irr.binding_rule", "telegram-recipient"),
        recipient,
        (BindingInputRole.CONTEXT,),
        (_ref("host.context", "telegram-destination"),),
        (TELEGRAM_DESTINATION_SOURCE_CONTRACT_IDENTITY,),
        "telegram.destination",
        TELEGRAM_DESTINATION_SCOPE,
        (),
        BindingSelectionPolicy(BindingSelectionMode.REQUIRE_UNIQUE),
        "Require exactly one explicit attributable Telegram destination.",
        (),
        (),
        (),
    )


def _recipient_input(
    resolved: ResolvedIntent,
    *,
    name: str,
    destination: str,
) -> BindingInput:
    return BindingInput(
        resolved.identity,
        _ref("irr.binding_input", name),
        SourceAttribution(
            _ref("host.context", "telegram-destination"),
            _ref("host.context_event", f"scenario-b-{name}"),
        ),
        BindingInputRole.CONTEXT,
        TELEGRAM_DESTINATION_SOURCE_CONTRACT_IDENTITY,
        "telegram.destination",
        destination,
        TELEGRAM_DESTINATION_SCOPE,
        destination,
        (),
        (),
        (),
        (),
    )


def _bound_report(resolved: ResolvedIntent) -> BoundValue:
    candidates = (
        _report_candidate(
            resolved,
            name="voice-engine-2026-08-30.pdf",
            value=r"W:\voice_engine\reports\voice-engine-2026-08-30.pdf",
            mtime="2026-08-30T21:00:00+06:00",
        ),
        _report_candidate(
            resolved,
            name="voice-engine-2026-08-31.pdf",
            value=SELECTED_REPORT,
            mtime="2026-08-31T23:10:00+06:00",
        ),
    )
    result = evaluate_binding(
        _report_rule(resolved),
        tuple(reversed(candidates)),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-b"),
            _ref("irr.event", "scenario-b-bind-latest-report"),
        ),
    )
    assert type(result) is BoundValue
    return result


def _bound_recipient(resolved: ResolvedIntent) -> BoundValue:
    result = evaluate_binding(
        _recipient_rule(resolved),
        (
            _recipient_input(
                resolved,
                name="telegram-primary",
                destination=TELEGRAM_DESTINATION,
            ),
        ),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-b"),
            _ref("irr.event", "scenario-b-bind-recipient"),
        ),
    )
    assert type(result) is BoundValue
    return result


def _send_plan(
    resolved: ResolvedIntent,
    report: BoundValue,
    recipient: BoundValue,
) -> tuple[WorkPlan, WorkStep]:
    plan_ref = _ref("irr.work_plan", "scenario-b-send")
    step = WorkStep(
        resolved.identity,
        plan_ref,
        _ref("irr.work_step", "send-report"),
        "telegram.send_file",
        recipient.value,
        (
            WorkSymbolicInput("artifact", report.rule.symbolic_reference),
            WorkSymbolicInput("recipient", recipient.rule.symbolic_reference),
        ),
        (),
        (),
        WorkContinuationMode.NONE,
        (
            "Confirm recipient-visible delivery of the exact selected report to the "
            "exact admitted Telegram destination."
        ),
        "Send only the selected Voice Engine report to the explicit bound recipient.",
    )
    return (
        WorkPlan(
            resolved.identity,
            plan_ref,
            (step,),
            "The bounded Telegram send step reaches its own completion contract.",
            "Scenario B send phase.",
        ),
        step,
    )


def _search_descriptor(search_step: WorkStep) -> CapabilityDescriptor:
    scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "report-search-root"),
        "filesystem.directory_scope",
        "Search remains inside the exact bounded report root.",
    )
    inputs = tuple(
        CapabilityInputContract(
            _ref("irr.capability_input", f"search-{item.name}"),
            item.semantic_type,
            (scope.requirement_ref,),
            f"Exact artifact.search {item.name} input.",
        )
        for item in search_step.inputs
    )
    output = CapabilityOutputContract(
        _ref("irr.capability_output", "report-candidates"),
        "artifact.path_set",
        (scope.requirement_ref,),
        "Bounded report candidate set.",
    )
    effect = CapabilityEffect(
        _ref("irr.capability_effect", "report-search-read"),
        "filesystem.read",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (scope.requirement_ref,),
        "Bounded report discovery exposes filesystem.read semantics.",
    )
    return CapabilityDescriptor(
        _ref("irr.capability", "artifact.search.local"),
        "artifact.search",
        inputs,
        (output,),
        (scope,),
        (effect,),
        (),
        search_step.completion_contract,
        "Bounded local artifact.search capability.",
    )


def _send_requirement(
    plan: WorkPlan,
    step: WorkStep,
    report: BoundValue,
    recipient: BoundValue,
) -> CapabilityRequirement:
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
        "Use the network only for the exact Telegram destination.",
    )
    disclosure_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "send-disclosure"),
        "external.disclosure",
        (report_scope.scope_ref, recipient_scope.scope_ref),
        "Disclose the exact selected report only to the exact admitted destination.",
    )
    return CapabilityRequirement(
        plan,
        step.step_ref,
        recipient_scope.scope_ref,
        (report_scope, recipient_scope),
        (read_effect, network_effect, disclosure_effect),
        (),
        "Exact Scenario B telegram.send_file capability requirement.",
    )


def _send_descriptor(step: WorkStep) -> CapabilityDescriptor:
    report_scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "send-report"),
        "artifact.path_scope",
        "Artifact reads remain inside one exact report resource.",
    )
    recipient_scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "send-recipient"),
        "telegram.destination_scope",
        "Network/disclosure effects remain bound to one exact Telegram destination.",
    )
    artifact_input = CapabilityInputContract(
        _ref("irr.capability_input", "send-artifact"),
        "artifact.path",
        (report_scope.requirement_ref,),
        "Exact report artifact.",
    )
    recipient_input = CapabilityInputContract(
        _ref("irr.capability_input", "send-recipient"),
        "telegram.destination",
        (recipient_scope.requirement_ref,),
        "Exact Telegram destination.",
    )
    read_effect = CapabilityEffect(
        _ref("irr.capability_effect", "send-read"),
        "filesystem.read",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (report_scope.requirement_ref,),
        "Sending the file necessarily exposes report-read semantics.",
    )
    network_effect = CapabilityEffect(
        _ref("irr.capability_effect", "send-network"),
        "network.use",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (recipient_scope.requirement_ref,),
        "Sending the file necessarily exposes network-use semantics.",
    )
    disclosure_effect = CapabilityEffect(
        _ref("irr.capability_effect", "send-disclosure"),
        "external.disclosure",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (report_scope.requirement_ref, recipient_scope.requirement_ref),
        "Sending the file necessarily exposes external disclosure semantics.",
    )
    return CapabilityDescriptor(
        _ref("irr.capability", "telegram.send_file"),
        "telegram.send_file",
        (artifact_input, recipient_input),
        (),
        (report_scope, recipient_scope),
        (read_effect, network_effect, disclosure_effect),
        (),
        step.completion_contract,
        "Exact bounded Telegram file-send capability.",
    )


def _incompatible_search(
    descriptor: CapabilityDescriptor,
) -> CapabilityIncompatibleDescriptorAssessment:
    return CapabilityIncompatibleDescriptorAssessment(
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityMismatchReason(
                CapabilityMismatchKind.OPERATION_MISMATCH,
                f"descriptor:{descriptor.capability_ref.value}",
                "artifact.search does not satisfy telegram.send_file.",
            ),
        ),
    )


def _send_evaluation(
    requirement: CapabilityRequirement,
    search_descriptor: CapabilityDescriptor,
    send_descriptor: CapabilityDescriptor,
    *,
    catalog_event: str = "scenario-b-catalog",
) -> CapabilityMatchEvaluation:
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "scenario-b"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "scenario-b-host"),
            _ref("irr.event", catalog_event),
        ),
        "Only artifact.search and telegram.send_file are admitted for Scenario B.",
        (search_descriptor, send_descriptor),
        "Bounded Scenario B capability snapshot.",
    )
    requested = {
        item.semantic_type: item
        for item in requirement.requested_effects
    }
    offered_effects = {
        item.semantic_type: item
        for item in send_descriptor.effects
    }
    requested_scopes = {
        item.value: item
        for item in requirement.requested_scopes
    }
    offered_scopes = {
        item.semantic_type: item
        for item in send_descriptor.scope_requirements
    }
    report_scope = requested_scopes[SELECTED_REPORT]
    recipient_scope = requested_scopes[TELEGRAM_DESTINATION]
    report_requirement = offered_scopes["artifact.path_scope"]
    recipient_requirement = offered_scopes["telegram.destination_scope"]
    inputs = {
        item.semantic_type: item
        for item in send_descriptor.input_contracts
    }
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "scenario-b-exact"),
            _ref("irr.event", "scenario-b-send-match"),
        ),
        requirement,
        snapshot,
        send_descriptor.capability_ref,
        send_descriptor.identity,
        (
            CapabilityScopeMatch(
                report_scope.scope_ref,
                report_requirement.requirement_ref,
            ),
            CapabilityScopeMatch(
                recipient_scope.scope_ref,
                recipient_requirement.requirement_ref,
            ),
        ),
        (
            CapabilityInputMatch(
                "artifact",
                inputs["artifact.path"].input_ref,
                (report_scope.scope_ref,),
            ),
            CapabilityInputMatch(
                "recipient",
                inputs["telegram.destination"].input_ref,
                (recipient_scope.scope_ref,),
            ),
        ),
        (),
        (
            CapabilityEffectMatch(
                requested["filesystem.read"].effect_ref,
                offered_effects["filesystem.read"].effect_ref,
            ),
            CapabilityEffectMatch(
                requested["network.use"].effect_ref,
                offered_effects["network.use"].effect_ref,
            ),
            CapabilityEffectMatch(
                requested["external.disclosure"].effect_ref,
                offered_effects["external.disclosure"].effect_ref,
            ),
        ),
        "Exact Scenario B telegram.send_file capability match.",
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-b"),
            _ref("irr.event", "scenario-b-send-evaluation"),
        ),
        requirement,
        snapshot,
        (match,),
        (_incompatible_search(search_descriptor),),
        "Exhaustive exact Catalog evaluation for Scenario B send.",
    )
    assert evaluate_capability_match_evaluation(evaluation) == match
    return evaluation


def _proposal_and_authorization(
    evaluation: CapabilityMatchEvaluation,
    report: BoundValue,
    recipient: BoundValue,
) -> tuple[WorkProposal, Authorization]:
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
                "The exact selected report is read and externally disclosed.",
            ),
            WorkProposalMaterial(
                _ref("irr.work_proposal_material", "recipient"),
                WorkProposalMaterialKind.RECIPIENT,
                (step_ref,),
                _ref("irr.source", "scenario-b-recipient-binding"),
                recipient.identity,
                recipient.value,
                "The exact attributable Telegram destination receives the report.",
            ),
            WorkProposalMaterial(
                _ref("irr.work_proposal_material", "disclosure"),
                WorkProposalMaterialKind.DISCLOSURE,
                (step_ref,),
                _ref("irr.source", "scenario-b-send-semantics"),
                evaluation.requirement.identity,
                f"{report.value} -> {recipient.value}",
                "The exact report leaves the local boundary for the exact recipient.",
            ),
            WorkProposalMaterial(
                _ref("irr.work_proposal_material", "data-flow"),
                WorkProposalMaterialKind.DATA_FLOW,
                (step_ref,),
                _ref("irr.source", "scenario-b-send-semantics"),
                evaluation.requirement.identity,
                f"local-report -> {recipient.value}",
                "Network transfer carries the exact selected report to Telegram.",
            ),
        ),
        "Present the exact recipient/disclosure send semantics to external Governance.",
    )
    component = GovernanceDecisionComponent(
        _ref("irr.governance_component", "authorize-send"),
        GovernanceDecisionKind.AUTHORIZE,
        (step_ref,),
        (),
        "Authorize only the exact represented Telegram send step.",
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
        "Exact Governance decision for the bounded Telegram disclosure.",
    )
    return proposal, Authorization(decision, component.component_ref)


def _fixture() -> dict[str, object]:
    resolved = _resolved()
    search_plan, search_step = _search_plan(resolved)
    report = _bound_report(resolved)
    recipient = _bound_recipient(resolved)
    send_plan, send_step = _send_plan(resolved, report, recipient)
    search_descriptor = _search_descriptor(search_step)
    send_descriptor = _send_descriptor(send_step)
    requirement = _send_requirement(send_plan, send_step, report, recipient)
    evaluation = _send_evaluation(requirement, search_descriptor, send_descriptor)
    proposal, authorization = _proposal_and_authorization(
        evaluation,
        report,
        recipient,
    )
    return {
        "resolved": resolved,
        "search_plan": search_plan,
        "report": report,
        "recipient": recipient,
        "send_plan": send_plan,
        "search_descriptor": search_descriptor,
        "send_descriptor": send_descriptor,
        "evaluation": evaluation,
        "proposal": proposal,
        "authorization": authorization,
    }


def test_scenario_b_binds_report_and_recipient_before_disclosure_authority() -> None:
    fixture = _fixture()
    report = fixture["report"]
    recipient = fixture["recipient"]
    search_descriptor = fixture["search_descriptor"]
    send_descriptor = fixture["send_descriptor"]
    evaluation = fixture["evaluation"]
    proposal = fixture["proposal"]
    authorization = fixture["authorization"]

    assert isinstance(report, BoundValue)
    assert isinstance(recipient, BoundValue)
    assert isinstance(search_descriptor, CapabilityDescriptor)
    assert isinstance(send_descriptor, CapabilityDescriptor)
    assert isinstance(evaluation, CapabilityMatchEvaluation)
    assert isinstance(proposal, WorkProposal)
    assert isinstance(authorization, Authorization)

    assert report.value == SELECTED_REPORT
    assert recipient.value == TELEGRAM_DESTINATION
    assert report.rule.allowed_source_identities == (
        REPORT_SEARCH_SOURCE_CONTRACT_IDENTITY,
    )
    assert recipient.rule.allowed_source_identities == (
        TELEGRAM_DESTINATION_SOURCE_CONTRACT_IDENTITY,
    )
    assert REPORT_SEARCH_SOURCE_CONTRACT_IDENTITY != search_descriptor.identity
    assert TELEGRAM_DESTINATION_SOURCE_CONTRACT_IDENTITY != send_descriptor.identity

    match = evaluate_capability_match_evaluation(evaluation)
    assert type(match) is CapabilityMatch
    assert match.capability_ref == send_descriptor.capability_ref

    kinds = {item.kind for item in proposal.authority_material}
    assert kinds == {
        WorkProposalMaterialKind.AFFECTED_RESOURCE,
        WorkProposalMaterialKind.RECIPIENT,
        WorkProposalMaterialKind.DISCLOSURE,
        WorkProposalMaterialKind.DATA_FLOW,
    }
    assert authorization.decision.proposal == proposal
    assert authorization.decision.components[0].kind is GovernanceDecisionKind.AUTHORIZE


def test_scenario_b_principal_alone_does_not_bind_telegram_destination() -> None:
    resolved = _resolved()
    result = evaluate_binding(
        _recipient_rule(resolved),
        (),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-b"),
            _ref("irr.event", "scenario-b-recipient-missing"),
        ),
    )
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.ZERO_MATCHES


def test_scenario_b_multiple_destinations_fail_closed_instead_of_guessing() -> None:
    resolved = _resolved()
    result = evaluate_binding(
        _recipient_rule(resolved),
        (
            _recipient_input(
                resolved,
                name="telegram-primary",
                destination=TELEGRAM_DESTINATION,
            ),
            _recipient_input(
                resolved,
                name="telegram-secondary",
                destination="telegram:chat:secondary-user",
            ),
        ),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "scenario-b"),
            _ref("irr.event", "scenario-b-recipient-ambiguous"),
        ),
    )
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.MULTIPLE_MATCHES


def test_scenario_b_missing_send_capability_is_no_match_not_hidden_fallback() -> None:
    fixture = _fixture()
    evaluation = fixture["evaluation"]
    search_descriptor = fixture["search_descriptor"]
    assert isinstance(evaluation, CapabilityMatchEvaluation)
    assert isinstance(search_descriptor, CapabilityDescriptor)

    missing = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "scenario-b-missing-send"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "scenario-b-host"),
            _ref("irr.event", "scenario-b-catalog-without-send"),
        ),
        "Only artifact.search remains in the bounded Scenario B planning surface.",
        (search_descriptor,),
        "Scenario B Catalog without telegram.send_file.",
    )
    no_match = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-b"),
            _ref("irr.event", "scenario-b-send-no-match"),
        ),
        evaluation.requirement,
        missing,
        (),
        (_incompatible_search(search_descriptor),),
        "Exhaustive bounded evaluation with telegram.send_file absent.",
    )
    result = evaluate_capability_match_evaluation(no_match)
    assert type(result) is CapabilityMatchIssue
    assert result.kind is CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY
    rendered = str(result.to_primitive()).lower()
    assert "fallback" not in rendered
    assert "browser" not in rendered
    assert "http" not in rendered
