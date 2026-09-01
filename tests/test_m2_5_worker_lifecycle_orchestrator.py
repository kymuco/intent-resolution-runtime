from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    ContextEnvelope,
    DelegatedScope,
    DelegatedWork,
    DelegatedWorkHandoff,
    DelegationHandoffAttribution,
    ExpectedDeliverable,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    ResolutionAttribution,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    ValidationError,
    WorkerNeed,
    WorkerNeedKind,
    WorkerResult,
    WorkerResultAttribution,
    WorkerResultMaterial,
    WorkerResultMaterialRole,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
)
from intent_resolution_runtime.worker_lifecycle import (
    WorkerLifecycleFrontier,
    orchestrate_worker_lifecycle,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _predecessor(label: str = "main") -> ResolvedIntent:
    request = IntentRequest(
        origin=OriginAttribution(
            OriginKind.HUMAN,
            _ref("human", "user"),
            _ref("host.event", f"request-{label}"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression("Analyze the bounded project and return a report."),
    )
    context = ContextEnvelope(
        request.identity,
        SourceAttribution(
            _ref("host.source", "context"),
            _ref("host.event", f"context-{label}"),
        ),
        (),
    )
    return ResolvedIntent(
        request.identity,
        context.identity,
        ResolutionAttribution(
            _ref("irr.resolver", "m2.5-test"),
            _ref("irr.resolution_event", f"predecessor-{label}"),
        ),
        "Delegate one bounded long-form analysis task.",
    )


def _parent_plan(predecessor: ResolvedIntent, label: str = "main") -> WorkPlan:
    plan_ref = _ref("irr.work_plan", f"analysis-{label}")
    step = WorkStep(
        predecessor.identity,
        plan_ref,
        _ref("irr.work_step", "prepare-delegation"),
        "analysis.prepare",
        "workspace:project",
        (),
        (),
        (),
        WorkContinuationMode.NONE,
        "Prepare the bounded delegated-analysis envelope.",
        "Prepare bounded work for Worker delegation.",
    )
    return WorkPlan(
        predecessor.identity,
        plan_ref,
        (step,),
        "Prepare the bounded Worker delegation.",
        "Parent preparation plan.",
    )


def _delegation(
    predecessor: ResolvedIntent,
    *,
    label: str = "main",
    parent_plan: WorkPlan | None = None,
    delegation_ref: StableRef | None = None,
    objective: str = "Analyze the bounded project and return the admitted report.",
) -> DelegatedWork:
    scope = DelegatedScope(
        _ref("irr.delegated_scope", f"project-{label}"),
        "workspace.scope",
        "workspace:project",
        "Exact bounded project scope.",
    )
    deliverable = ExpectedDeliverable(
        _ref("irr.expected_deliverable", f"report-{label}"),
        "analysis.report",
        scope.scope_ref,
        "One bounded analysis report.",
    )
    return DelegatedWork(
        predecessor.identity,
        _ref("irr.delegation", label) if delegation_ref is None else delegation_ref,
        () if parent_plan is None else (parent_plan.identity,),
        objective,
        (scope,),
        (),
        (),
        (),
        (deliverable,),
        "Return the admitted report for the bounded project scope.",
        "Bounded long-form Worker analysis delegation.",
    )


def _handoff(
    delegated: DelegatedWork,
    *,
    worker: str = "worker-a",
    event: str = "handoff-a",
) -> DelegatedWorkHandoff:
    return DelegatedWorkHandoff(
        DelegationHandoffAttribution(
            _ref("irr.dispatcher", "m2.5-test"),
            _ref("irr.worker", worker),
            _ref("irr.handoff_event", event),
        ),
        delegated,
    )


def _deliverable_result(
    handoff: DelegatedWorkHandoff,
    *,
    event: str = "result-a",
    content: str = "Bounded report content.",
) -> WorkerResult:
    delegated = handoff.delegated_work
    expected = delegated.expected_deliverables[0]
    material = WorkerResultMaterial(
        material_ref=_ref("irr.worker_material", event),
        role=WorkerResultMaterialRole.DELIVERABLE,
        semantic_type=expected.semantic_type,
        scope_refs=(expected.scope_ref,),
        expected_deliverable_refs=(expected.deliverable_ref,),
        source_refs=(),
        source_identity_refs=(),
        content=content,
        description="Worker-returned deliverable material.",
    )
    return WorkerResult(
        WorkerResultAttribution(
            handoff.attribution.worker_ref,
            _ref("irr.worker_result_event", event),
        ),
        handoff,
        (material,),
        (),
        "Attributable Worker deliverable return.",
    )


def _need_result(
    handoff: DelegatedWorkHandoff,
    *,
    event: str = "result-need",
    need_kind: WorkerNeedKind = WorkerNeedKind.SCOPE,
) -> WorkerResult:
    need = WorkerNeed(
        _ref("irr.worker_need", event),
        need_kind,
        (),
        "The Worker reports a material need outside the currently admitted envelope.",
    )
    return WorkerResult(
        WorkerResultAttribution(
            handoff.attribution.worker_ref,
            _ref("irr.worker_result_event", event),
        ),
        handoff,
        (),
        (need,),
        "Attributable Worker need return.",
    )


def _completion_claim_result(
    handoff: DelegatedWorkHandoff,
    *,
    event: str = "result-completion-claim",
) -> WorkerResult:
    delegated = handoff.delegated_work
    material = WorkerResultMaterial(
        material_ref=_ref("irr.worker_material", event),
        role=WorkerResultMaterialRole.COMPLETION_CLAIM,
        semantic_type="worker.claim",
        scope_refs=(delegated.scopes[0].scope_ref,),
        expected_deliverable_refs=(),
        source_refs=(),
        source_identity_refs=(),
        content="done",
        description="Worker assertion that the delegated work is complete.",
    )
    return WorkerResult(
        WorkerResultAttribution(
            handoff.attribution.worker_ref,
            _ref("irr.worker_result_event", event),
        ),
        handoff,
        (material,),
        (),
        "Attributable completion claim only.",
    )


def test_empty_worker_frontier_is_noncanonical_derived_view() -> None:
    predecessor = _predecessor()
    frontier = orchestrate_worker_lifecycle(predecessor)

    assert isinstance(frontier, WorkerLifecycleFrontier)
    assert frontier.parent_work_plans == ()
    assert frontier.delegated_work == ()
    assert frontier.handoffs == ()
    assert frontier.worker_results == ()
    assert not hasattr(frontier, "identity")
    assert not hasattr(frontier, "canonical_bytes")


def test_parent_work_plan_must_descend_from_exact_predecessor() -> None:
    predecessor = _predecessor("active")
    foreign = _predecessor("foreign")
    plan = _parent_plan(foreign)

    with pytest.raises(ValidationError, match="parent WorkPlan must descend"):
        orchestrate_worker_lifecycle(predecessor, parent_work_plans=(plan,))


def test_delegation_must_descend_from_exact_predecessor() -> None:
    predecessor = _predecessor("active")
    foreign = _predecessor("foreign")
    delegated = _delegation(foreign)

    with pytest.raises(ValidationError, match="DelegatedWork must descend"):
        orchestrate_worker_lifecycle(predecessor, delegated_work=(delegated,))


def test_parented_delegation_requires_exact_supplied_parent_plan() -> None:
    predecessor = _predecessor()
    plan = _parent_plan(predecessor)
    delegated = _delegation(predecessor, parent_plan=plan)

    with pytest.raises(ValidationError, match="parent WorkPlan identity is orphaned"):
        orchestrate_worker_lifecycle(predecessor, delegated_work=(delegated,))

    frontier = orchestrate_worker_lifecycle(
        predecessor,
        parent_work_plans=(plan,),
        delegated_work=(delegated,),
    )
    assert frontier.parent_work_plans == (plan,)
    assert frontier.delegated_work == (delegated,)


def test_competing_delegated_work_for_one_delegation_ref_fails_closed() -> None:
    predecessor = _predecessor()
    shared_ref = _ref("irr.delegation", "shared")
    first = _delegation(predecessor, label="a", delegation_ref=shared_ref)
    second = _delegation(
        predecessor,
        label="b",
        delegation_ref=shared_ref,
        objective="A materially different active delegation objective.",
    )
    assert first.identity != second.identity

    with pytest.raises(ValidationError, match="competing active DelegatedWork"):
        orchestrate_worker_lifecycle(
            predecessor,
            delegated_work=(first, second),
        )


def test_delegation_without_handoff_is_neutral_disposition_not_failure() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)

    frontier = orchestrate_worker_lifecycle(
        predecessor,
        delegated_work=(delegated,),
    )

    assert frontier.handoff_disposition_required_delegations == (delegated,)
    assert frontier.result_pending_handoffs == ()
    assert not hasattr(frontier, "failed_delegations")
    assert not hasattr(frontier, "worker_required")


def test_handoff_requires_exact_supplied_delegation() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    handoff = _handoff(delegated)

    with pytest.raises(ValidationError, match="orphaned from the exact supplied DelegatedWork"):
        orchestrate_worker_lifecycle(predecessor, handoffs=(handoff,))


def test_multiple_handoffs_for_one_delegation_preserve_history_without_worker_precedence() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    first = _handoff(delegated, worker="worker-a", event="handoff-a")
    second = _handoff(delegated, worker="worker-b", event="handoff-b")

    frontier = orchestrate_worker_lifecycle(
        predecessor,
        delegated_work=(delegated,),
        handoffs=(second, first),
    )

    assert set(frontier.handoffs) == {first, second}
    assert frontier.multi_handoff_delegation_refs == (delegated.delegation_ref,)
    assert set(frontier.result_pending_handoffs) == {first, second}
    assert not hasattr(frontier, "active_worker")
    assert not hasattr(frontier, "selected_handoff")


def test_handoff_occurrence_cannot_alias_predecessor_admission() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    handoff = DelegatedWorkHandoff(
        DelegationHandoffAttribution(
            _ref("irr.dispatcher", "m2.5-test"),
            _ref("irr.worker", "worker-a"),
            predecessor.admission_attribution.admission_event_ref,
        ),
        delegated,
    )

    with pytest.raises(ValidationError, match="handoff occurrence must differ"):
        orchestrate_worker_lifecycle(
            predecessor,
            delegated_work=(delegated,),
            handoffs=(handoff,),
        )


def test_worker_result_requires_exact_supplied_handoff() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    handoff = _handoff(delegated)
    result = _deliverable_result(handoff)

    with pytest.raises(ValidationError, match="orphaned from the exact supplied DelegatedWorkHandoff"):
        orchestrate_worker_lifecycle(
            predecessor,
            delegated_work=(delegated,),
            worker_results=(result,),
        )


def test_handoff_without_result_is_pending_not_worker_failure() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    handoff = _handoff(delegated)

    frontier = orchestrate_worker_lifecycle(
        predecessor,
        delegated_work=(delegated,),
        handoffs=(handoff,),
    )

    assert frontier.result_pending_handoffs == (handoff,)
    assert frontier.worker_results == ()
    assert not hasattr(frontier, "worker_failed")


def test_multiple_worker_results_for_one_handoff_remain_distinct_return_history() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    handoff = _handoff(delegated)
    first = _deliverable_result(handoff, event="result-first", content="First returned material.")
    second = _need_result(handoff, event="result-second")

    frontier = orchestrate_worker_lifecycle(
        predecessor,
        delegated_work=(delegated,),
        handoffs=(handoff,),
        worker_results=(second, first),
    )

    assert set(frontier.worker_results) == {first, second}
    assert frontier.multi_result_handoff_identities == (handoff.identity,)
    assert frontier.result_pending_handoffs == ()
    assert frontier.results_with_needs == (second,)
    assert frontier.results_with_deliverables == (first,)
    assert not hasattr(frontier, "latest_result")
    assert not hasattr(frontier, "final_result")


def test_competing_records_cannot_share_one_worker_result_occurrence() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    handoff = _handoff(delegated)
    event_ref = _ref("irr.worker_result_event", "shared-result-event")

    expected = delegated.expected_deliverables[0]
    first_material = WorkerResultMaterial(
        _ref("irr.worker_material", "first"),
        WorkerResultMaterialRole.DELIVERABLE,
        expected.semantic_type,
        (expected.scope_ref,),
        (expected.deliverable_ref,),
        (),
        (),
        "First content.",
        "First return.",
    )
    second_material = WorkerResultMaterial(
        _ref("irr.worker_material", "second"),
        WorkerResultMaterialRole.DELIVERABLE,
        expected.semantic_type,
        (expected.scope_ref,),
        (expected.deliverable_ref,),
        (),
        (),
        "Second content.",
        "Second return.",
    )
    first = WorkerResult(
        WorkerResultAttribution(handoff.attribution.worker_ref, event_ref),
        handoff,
        (first_material,),
        (),
        "First record for one occurrence.",
    )
    second = WorkerResult(
        WorkerResultAttribution(handoff.attribution.worker_ref, event_ref),
        handoff,
        (second_material,),
        (),
        "Competing record for the same occurrence.",
    )

    with pytest.raises(ValidationError, match="one Worker result occurrence cannot identify competing"):
        orchestrate_worker_lifecycle(
            predecessor,
            delegated_work=(delegated,),
            handoffs=(handoff,),
            worker_results=(first, second),
        )


def test_worker_result_occurrence_cannot_alias_predecessor_admission() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    handoff = _handoff(delegated)
    result = _need_result(handoff, event="temporary")
    collided = WorkerResult(
        WorkerResultAttribution(
            handoff.attribution.worker_ref,
            predecessor.admission_attribution.admission_event_ref,
        ),
        handoff,
        result.materials,
        result.needs,
        result.description,
    )

    with pytest.raises(ValidationError, match="result occurrence must differ from the predecessor"):
        orchestrate_worker_lifecycle(
            predecessor,
            delegated_work=(delegated,),
            handoffs=(handoff,),
            worker_results=(collided,),
        )


def test_worker_result_occurrence_cannot_alias_another_handoff_occurrence() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    first_handoff = _handoff(delegated, worker="worker-a", event="handoff-a")
    second_handoff = _handoff(delegated, worker="worker-b", event="handoff-b")
    result = _need_result(first_handoff, event="temporary")
    collided = WorkerResult(
        WorkerResultAttribution(
            first_handoff.attribution.worker_ref,
            second_handoff.attribution.handoff_event_ref,
        ),
        first_handoff,
        result.materials,
        result.needs,
        result.description,
    )

    with pytest.raises(ValidationError, match="distinct from every Worker handoff occurrence"):
        orchestrate_worker_lifecycle(
            predecessor,
            delegated_work=(delegated,),
            handoffs=(first_handoff, second_handoff),
            worker_results=(collided,),
        )


def test_worker_need_is_visible_without_widening_delegated_envelope() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    handoff = _handoff(delegated)
    result = _need_result(handoff, need_kind=WorkerNeedKind.SCOPE)

    frontier = orchestrate_worker_lifecycle(
        predecessor,
        delegated_work=(delegated,),
        handoffs=(handoff,),
        worker_results=(result,),
    )

    assert frontier.results_with_needs == (result,)
    assert frontier.delegated_work == (delegated,)
    assert result.needs[0].kind is WorkerNeedKind.SCOPE
    assert result.needs[0].related_scope_refs == ()
    assert not hasattr(frontier, "expanded_scopes")
    assert not hasattr(frontier, "authorization")


def test_completion_claim_is_visible_but_not_delegated_or_parent_completion() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    handoff = _handoff(delegated)
    claim = _completion_claim_result(handoff)

    frontier = orchestrate_worker_lifecycle(
        predecessor,
        delegated_work=(delegated,),
        handoffs=(handoff,),
        worker_results=(claim,),
    )

    assert frontier.results_with_completion_claims == (claim,)
    assert frontier.results_with_deliverables == ()
    assert not hasattr(frontier, "delegated_complete")
    assert not hasattr(frontier, "parent_complete")
    assert not hasattr(frontier, "intent_satisfied")


def test_deliverable_return_is_not_parent_completion_or_automatic_continuation() -> None:
    predecessor = _predecessor()
    delegated = _delegation(predecessor)
    handoff = _handoff(delegated)
    result = _deliverable_result(handoff)

    frontier = orchestrate_worker_lifecycle(
        predecessor,
        delegated_work=(delegated,),
        handoffs=(handoff,),
        worker_results=(result,),
    )

    assert frontier.results_with_deliverables == (result,)
    assert not hasattr(frontier, "continuation_inputs")
    assert not hasattr(frontier, "successor_lineage")
    assert not hasattr(frontier, "parent_complete")


def test_input_order_does_not_create_worker_handoff_or_result_precedence() -> None:
    predecessor = _predecessor()
    first_delegation = _delegation(predecessor, label="alpha")
    second_delegation = _delegation(predecessor, label="beta")
    first_handoff = _handoff(first_delegation, worker="worker-a", event="handoff-alpha")
    second_handoff = _handoff(second_delegation, worker="worker-b", event="handoff-beta")
    first_result = _deliverable_result(first_handoff, event="result-alpha")
    second_result = _need_result(second_handoff, event="result-beta")

    first = orchestrate_worker_lifecycle(
        predecessor,
        delegated_work=(first_delegation, second_delegation),
        handoffs=(first_handoff, second_handoff),
        worker_results=(first_result, second_result),
    )
    second = orchestrate_worker_lifecycle(
        predecessor,
        delegated_work=(second_delegation, first_delegation),
        handoffs=(second_handoff, first_handoff),
        worker_results=(second_result, first_result),
    )

    assert first == second
    assert first.multi_handoff_delegation_refs == ()
    assert first.multi_result_handoff_identities == ()
    assert first.results_with_deliverables == (first_result,)
    assert first.results_with_needs == (second_result,)
