from __future__ import annotations

import json

import pytest

from intent_resolution_runtime import (
    BindingAttribution,
    BindingInputRole,
    BindingIssue,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    CapabilityAttempt,
    CapabilityAttemptAttribution,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityMatchIssue,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    CapabilityOutcome,
    CapabilityOutcomeAttribution,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    DelegatedScope,
    DelegatedWork,
    DelegatedWorkHandoff,
    DelegationHandoffAttribution,
    EvidenceRelation,
    ExpectedDeliverable,
    GovernanceContinuationMaterial,
    GovernanceDecision,
    GovernanceDecisionAttribution,
    GovernanceDecisionComponent,
    GovernanceDecisionKind,
    GovernanceDirective,
    InterchangeableChoicePolicy,
    OutcomeCompletionAssessment,
    OutcomeCompletionState,
    OutcomeEvidence,
    OutcomeEvidenceRole,
    OutcomeLifecycleAssessment,
    OutcomeLifecycleState,
    ProposedWorkStep,
    RecordIdentity,
    SerializationError,
    SourceAttribution,
    StableRef,
    SymbolicReference,
    ValidationError,
    WorkerResult,
    WorkerResultAttribution,
    WorkerResultMaterial,
    WorkerResultMaterialRole,
    WorkContinuationMode,
    WorkPlan,
    WorkProposal,
    WorkProposalAttribution,
    WorkStep,
    evaluate_binding,
    evaluate_capability_match_evaluation,
)


RESOLVED = RecordIdentity("sha256", "1" * 64)
SOURCE_IDENTITY = RecordIdentity("sha256", "2" * 64)
AUTHORITY_IDENTITY = RecordIdentity("sha256", "3" * 64)
TEMPORAL = RecordIdentity("sha256", "4" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _unique_evaluation() -> CapabilityMatchEvaluation:
    plan_ref = _ref("irr.work_plan", "inspect-001")
    step_ref = _ref("irr.work_step", "inspect")
    completion = "Return the bounded inspection result."
    step = WorkStep(
        RESOLVED,
        plan_ref,
        step_ref,
        "workspace.inspect",
        "workspace:project",
        (),
        (),
        (),
        WorkContinuationMode.RETURN_TO_IRR,
        completion,
        "Inspect one bounded workspace and return to IRR.",
    )
    plan = WorkPlan(
        RESOLVED,
        plan_ref,
        (step,),
        "Complete after the bounded inspection result is admitted.",
        "Continuation test plan.",
    )
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "workspace"),
        "filesystem.path_scope",
        "workspace:project",
        "Exact workspace scope.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        requested_scope.scope_ref,
        (requested_scope,),
        (),
        (),
        "Exact workspace inspection requirement.",
    )
    descriptor_scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "workspace"),
        "filesystem.path_scope",
        "Remain inside the exact workspace scope.",
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
        "Bounded local workspace inspection capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "continuation"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", "catalog-continuation-001"),
        ),
        "Continuation test capability surface.",
        (descriptor,),
        "Exact continuation test Catalog snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "exact-v1"),
            _ref("irr.event", "match-continuation-001"),
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
        "Exact continuation test capability match.",
    )
    return CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", "evaluation-continuation-001"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for continuation tests.",
    )


def _capability_outcome() -> CapabilityOutcome:
    evaluation = _unique_evaluation()
    attempt = CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", "workspace-local"),
            _ref("irr.event", "attempt-continuation-001"),
        ),
        evaluation,
        evaluation.requirement.step_ref,
        (),
        (),
        "One bounded workspace inspection attempt.",
    )
    lifecycle = OutcomeEvidence(
        _ref("irr.outcome_evidence", "lifecycle"),
        SourceAttribution(
            _ref("executor.source", "workspace-local"),
            _ref("executor.event", "protocol-complete"),
        ),
        SOURCE_IDENTITY,
        EvidenceRelation.SUPPORTS,
        (OutcomeEvidenceRole.LIFECYCLE,),
        (TEMPORAL,),
        "workspace.inspect attempt",
        "The bounded result protocol completed normally.",
    )
    completion = OutcomeEvidence(
        _ref("irr.outcome_evidence", "completion"),
        SourceAttribution(
            _ref("executor.source", "workspace-local"),
            _ref("executor.event", "completion-receipt"),
        ),
        SOURCE_IDENTITY,
        EvidenceRelation.SUPPORTS,
        (OutcomeEvidenceRole.COMPLETION,),
        (TEMPORAL,),
        "workspace.inspect completion",
        "The exact completion contract is satisfied.",
    )
    return CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "bounded-v1"),
            _ref("irr.event", "outcome-continuation-001"),
        ),
        attempt,
        (completion, lifecycle),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
            (lifecycle.evidence_ref,),
            "The normal result protocol completed.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.SATISFIED,
            (completion.evidence_ref,),
            "The WorkStep completion contract is satisfied.",
        ),
        (),
        "Bounded effect-free inspection Outcome.",
    )


def _worker_result() -> WorkerResult:
    scope = DelegatedScope(
        _ref("irr.delegated_scope", "research"),
        "project.scope",
        "project:continuation",
        "Exact delegated project scope.",
    )
    deliverable = ExpectedDeliverable(
        _ref("irr.expected_deliverable", "finding"),
        "research.finding",
        scope.scope_ref,
        "Return one bounded finding.",
    )
    delegated = DelegatedWork(
        RESOLVED,
        _ref("irr.delegated_work", "research-001"),
        (),
        "Inspect the bounded project material and return one finding.",
        (scope,),
        (),
        (),
        (),
        (deliverable,),
        "Return the exact requested finding or an explicit WorkerNeed.",
        "Bounded delegated continuation fixture.",
    )
    worker_ref = _ref("irr.worker", "research-worker")
    handoff = DelegatedWorkHandoff(
        DelegationHandoffAttribution(
            _ref("irr.dispatcher", "test-host"),
            worker_ref,
            _ref("irr.event", "handoff-continuation-001"),
        ),
        delegated,
    )
    material = WorkerResultMaterial(
        _ref("irr.worker_material", "finding"),
        WorkerResultMaterialRole.DELIVERABLE,
        "research.finding",
        (scope.scope_ref,),
        (deliverable.deliverable_ref,),
        (),
        (),
        "The bounded inspection found one exact candidate.",
        "Requested research finding.",
    )
    return WorkerResult(
        WorkerResultAttribution(
            worker_ref,
            _ref("irr.event", "worker-result-continuation-001"),
        ),
        handoff,
        (material,),
        (),
        "Worker returned the requested bounded finding.",
    )


def _binding_issue() -> BindingIssue:
    selection_scope = "workspace:backups"
    symbolic = SymbolicReference(
        RESOLVED,
        _ref("irr.slot", "selected-backup"),
        "artifact.path",
        selection_scope,
        "Exact backup artifact selected by admitted binding semantics.",
    )
    source_ref = _ref("host.source", "filesystem-search")
    rule = BindingRule(
        RESOLVED,
        _ref("irr.binding_rule", "unique-backup"),
        symbolic,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (source_ref,),
        (SOURCE_IDENTITY,),
        "artifact.path",
        selection_scope,
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.REQUIRE_UNIQUE,
            (),
            (),
            InterchangeableChoicePolicy.NONE,
        ),
        "Require one exact compatible backup candidate.",
        (),
        (),
        (),
    )
    result = evaluate_binding(
        rule,
        (),
        attribution=BindingAttribution(
            _ref("irr.evaluator", "mechanical-binding-v1"),
            _ref("irr.event", "binding-continuation-001"),
        ),
    )
    assert type(result) is BindingIssue
    return result


def _capability_match_issue() -> CapabilityMatchIssue:
    plan_ref = _ref("irr.work_plan", "missing-capability-001")
    step_ref = _ref("irr.work_step", "missing")
    step = WorkStep(
        RESOLVED,
        plan_ref,
        step_ref,
        "missing.operation",
        "workspace:project",
        (),
        (),
        (),
        WorkContinuationMode.RETURN_TO_IRR,
        "Return the bounded operation result.",
        "Work requiring a currently absent capability.",
    )
    plan = WorkPlan(
        RESOLVED,
        plan_ref,
        (step,),
        "Complete after the missing operation can be performed.",
        "Missing capability continuation fixture.",
    )
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "missing-workspace"),
        "filesystem.path_scope",
        "workspace:project",
        "Exact requested scope.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        requested_scope.scope_ref,
        (requested_scope,),
        (),
        (),
        "Requirement with no compatible Catalog descriptor.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "empty"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", "catalog-empty-001"),
        ),
        "Exact empty capability surface.",
        (),
        "Empty Catalog snapshot.",
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", "evaluation-missing-001"),
        ),
        requirement,
        snapshot,
        (),
        (),
        "Exhaustive evaluation over an empty exact Catalog.",
    )
    result = evaluate_capability_match_evaluation(evaluation)
    assert type(result) is CapabilityMatchIssue
    return result


def _governance_decision(kind: GovernanceDecisionKind) -> GovernanceDecision:
    evaluation = _unique_evaluation()
    step_ref = evaluation.requirement.step_ref
    proposal = WorkProposal(
        WorkProposalAttribution(
            _ref("irr.proposer", "test-host"),
            _ref("irr.event", f"proposal-{kind.value}-001"),
        ),
        evaluation.requirement.work_plan,
        (ProposedWorkStep(step_ref, evaluation),),
        (),
        "Exact proposal for Governance continuation testing.",
    )
    directives = (
        ()
        if kind is GovernanceDecisionKind.DENY
        else (
            GovernanceDirective(
                _ref("irr.governance_directive", kind.value),
                "governance.reentry_requirement",
                "workspace:project",
                (
                    "Preserve the exact constrained semantics."
                    if kind is GovernanceDecisionKind.CONSTRAIN
                    else "Obtain explicit external review before successor work."
                ),
            ),
        )
    )
    component = GovernanceDecisionComponent(
        _ref("irr.governance_component", kind.value),
        kind,
        (step_ref,),
        directives,
        f"Governance {kind.value} fixture.",
    )
    return GovernanceDecision(
        GovernanceDecisionAttribution(
            _ref("irr.governance", "test-policy"),
            _ref("irr.event", f"decision-{kind.value}-001"),
            _ref("irr.authority_context", "test"),
            AUTHORITY_IDENTITY,
        ),
        proposal,
        (component,),
        f"Exact Governance {kind.value} decision.",
    )


def _governance_material(kind: GovernanceDecisionKind) -> GovernanceContinuationMaterial:
    decision = _governance_decision(kind)
    return GovernanceContinuationMaterial(
        decision,
        decision.components[0].component_ref,
    )


def _continuation(source_kind: ContinuationSourceKind, source: object) -> ContinuationInput:
    return ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "continuation-test"),
            _ref("irr.event", f"reentry-{source_kind.value}-001"),
        ),
        source_kind,
        source,  # type: ignore[arg-type]
    )


def test_all_admitted_continuation_sources_round_trip_without_free_lineage() -> None:
    sources = (
        (ContinuationSourceKind.CAPABILITY_OUTCOME, _capability_outcome()),
        (ContinuationSourceKind.WORKER_RESULT, _worker_result()),
        (ContinuationSourceKind.BINDING_ISSUE, _binding_issue()),
        (ContinuationSourceKind.CAPABILITY_MATCH_ISSUE, _capability_match_issue()),
        (
            ContinuationSourceKind.GOVERNANCE_CONSTRAINT,
            _governance_material(GovernanceDecisionKind.CONSTRAIN),
        ),
        (
            ContinuationSourceKind.GOVERNANCE_REQUIRE_REVIEW,
            _governance_material(GovernanceDecisionKind.REQUIRE_REVIEW),
        ),
    )
    for kind, source in sources:
        continuation = _continuation(kind, source)
        decoded = ContinuationInput.from_json_bytes(continuation.canonical_bytes())
        assert decoded == continuation
        assert decoded.identity == continuation.identity
        assert decoded.source_identity == source.identity
        assert decoded.resolved_intent_identity == RESOLVED
        assert set(decoded.to_primitive()) == {
            "schema",
            "attribution",
            "source_kind",
            "source",
        }


def test_source_kind_is_mechanical_not_local_discretion() -> None:
    with pytest.raises(ValidationError, match="source_kind must match"):
        _continuation(ContinuationSourceKind.WORKER_RESULT, _binding_issue())


def test_reentry_occurrence_must_differ_from_source_occurrence() -> None:
    source = _binding_issue()
    with pytest.raises(ValidationError, match="must differ from the source occurrence"):
        ContinuationInput(
            ContinuationInputAttribution(
                _ref("irr.host", "continuation-test"),
                source.binding_attribution.binding_event_ref,
            ),
            ContinuationSourceKind.BINDING_ISSUE,
            source,
        )


def test_arbitrary_records_cannot_be_smuggled_as_continuation_sources() -> None:
    with pytest.raises(ValidationError, match="unsupported IR type"):
        _continuation(ContinuationSourceKind.BINDING_ISSUE, object())


def test_governance_continuation_accepts_only_constraint_or_review_components() -> None:
    for kind in (
        GovernanceDecisionKind.AUTHORIZE,
        GovernanceDecisionKind.DENY,
    ):
        decision = _governance_decision(kind)
        with pytest.raises(ValidationError, match="constrain or require_review"):
            GovernanceContinuationMaterial(
                decision,
                decision.components[0].component_ref,
            )


def test_governance_component_ref_must_exist_in_exact_decision() -> None:
    decision = _governance_decision(GovernanceDecisionKind.CONSTRAIN)
    with pytest.raises(ValidationError, match="identify a component"):
        GovernanceContinuationMaterial(
            decision,
            _ref("irr.governance_component", "foreign"),
        )


def test_governance_constraint_cannot_masquerade_as_require_review() -> None:
    material = _governance_material(GovernanceDecisionKind.CONSTRAIN)
    with pytest.raises(ValidationError, match="source_kind must match"):
        _continuation(
            ContinuationSourceKind.GOVERNANCE_REQUIRE_REVIEW,
            material,
        )


def test_continuation_has_no_retry_successor_or_authority_fields() -> None:
    continuation = _continuation(
        ContinuationSourceKind.BINDING_ISSUE,
        _binding_issue(),
    )
    payload = json.loads(continuation.canonical_bytes().decode("utf-8"))
    for field, value in (
        ("retry", "true"),
        ("fallback", "other-provider"),
        ("successor_work_plan", "locally-minted"),
        ("authorized", "true"),
        ("parent_complete", "true"),
    ):
        mutated = dict(payload)
        mutated[field] = value
        with pytest.raises(SerializationError):
            ContinuationInput.from_json_bytes(
                json.dumps(mutated, ensure_ascii=False).encode("utf-8")
            )


def test_same_source_new_reentry_event_is_new_occurrence_not_new_source_semantics() -> None:
    source = _binding_issue()
    first = _continuation(ContinuationSourceKind.BINDING_ISSUE, source)
    second = ContinuationInput(
        ContinuationInputAttribution(
            first.attribution.submitter_ref,
            _ref("irr.event", "reentry-binding_issue-002"),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        source,
    )
    assert first.identity != second.identity
    assert first.source_identity == second.source_identity == source.identity
    assert first.resolved_intent_identity == second.resolved_intent_identity == RESOLVED


def test_public_continuation_records_are_closed_against_subclassing() -> None:
    with pytest.raises(TypeError):
        class DerivedContinuation(ContinuationInput):
            pass

    with pytest.raises(TypeError):
        class DerivedGovernanceMaterial(GovernanceContinuationMaterial):
            pass
