from __future__ import annotations

from intent_resolution_runtime import (
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    DelegatedCapabilityAllowance,
    DelegatedContextReference,
    DelegatedScope,
    DelegatedWork,
    DelegatedWorkHandoff,
    DelegationConstraint,
    DelegationConstraintKind,
    DelegationHandoffAttribution,
    ExpectedDeliverable,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    StableRef,
    SuccessorResolutionKind,
    SuccessorResolutionLineage,
    WorkerNeed,
    WorkerNeedKind,
    WorkerResult,
    WorkerResultAttribution,
)


REQUEST_IDENTITY = RecordIdentity("sha256", "1" * 64)
CONTEXT_IDENTITY = RecordIdentity("sha256", "2" * 64)
CG242_EVIDENCE_IDENTITY = RecordIdentity("sha256", "3" * 64)
ANALYSIS_CAPABILITY_CONTRACT = RecordIdentity("sha256", "4" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _predecessor() -> ResolvedIntent:
    return ResolvedIntent(
        REQUEST_IDENTITY,
        CONTEXT_IDENTITY,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-c"),
            _ref("irr.resolution_event", "scenario-c-before-worker-escalation"),
        ),
        (
            "Analyze only the supplied CG2.42 evidence and return any material need that "
            "would require new scope or a forbidden effect back to IRR."
        ),
        (),
        (),
        (),
    )


def _delegated(predecessor: ResolvedIntent) -> DelegatedWork:
    scope = DelegatedScope(
        scope_ref=_ref("irr.delegated_scope", "cg2.42-evidence"),
        semantic_type="experiment.evidence_surface",
        value="organism_lab:CG2.42:results",
        description="Exact bounded CG2.42 evidence surface.",
    )
    context = DelegatedContextReference(
        context_ref=_ref("irr.delegated_context", "cg2.42-results"),
        semantic_type="experiment.result_bundle",
        scope_ref=scope.scope_ref,
        source_identity_refs=(CG242_EVIDENCE_IDENTITY,),
        description="Only the explicitly supplied CG2.42 result bundle.",
    )
    allowance = DelegatedCapabilityAllowance(
        allowance_ref=_ref("irr.delegated_capability_allowance", "analysis-read"),
        capability_ref=_ref("irr.capability", "analysis.inspect"),
        capability_contract_identity=ANALYSIS_CAPABILITY_CONTRACT,
        scope_refs=(scope.scope_ref,),
        description="Exact subordinate analysis/read ceiling over the delegated evidence.",
    )
    deliverable = ExpectedDeliverable(
        deliverable_ref=_ref("irr.expected_deliverable", "experiment-proposal"),
        semantic_type="experiment.proposal",
        scope_ref=scope.scope_ref,
        description="Bounded next-experiment proposal if current evidence is sufficient.",
    )
    return DelegatedWork(
        resolved_intent_identity=predecessor.identity,
        delegation_ref=_ref("irr.delegated_work", "scenario-c-escalation"),
        parent_work_plan_identity_refs=(),
        objective=(
            "Analyze the supplied CG2.42 evidence and propose a next experiment only if the "
            "current envelope is sufficient; otherwise return explicit need material."
        ),
        scopes=(scope,),
        context_surface=(context,),
        allowed_capabilities=(allowance,),
        constraints=(
            DelegationConstraint(
                constraint_ref=_ref("irr.delegation_constraint", "no-external-search"),
                kind=DelegationConstraintKind.FORBIDDEN_EFFECT,
                statement="External evidence acquisition is outside this delegation.",
            ),
            DelegationConstraint(
                constraint_ref=_ref("irr.delegation_constraint", "no-repository-mutation"),
                kind=DelegationConstraintKind.FORBIDDEN_EFFECT,
                statement="Repository mutation is outside this delegation.",
            ),
            DelegationConstraint(
                constraint_ref=_ref("irr.delegation_constraint", "no-push"),
                kind=DelegationConstraintKind.FORBIDDEN_EFFECT,
                statement="Repository push/publication is outside this delegation.",
            ),
        ),
        expected_deliverables=(deliverable,),
        completion_contract=(
            "Return the bounded proposal or attributable WorkerNeed material; do not widen "
            "scope or effects inside the existing delegation."
        ),
        description="Scenario C escalation envelope.",
    )


def _worker_result(predecessor: ResolvedIntent) -> WorkerResult:
    delegated = _delegated(predecessor)
    worker_ref = _ref("irr.worker", "codexia")
    handoff = DelegatedWorkHandoff(
        attribution=DelegationHandoffAttribution(
            dispatcher_ref=_ref("irr.dispatcher", "worker-boundary"),
            worker_ref=worker_ref,
            handoff_event_ref=_ref("irr.event", "scenario-c-escalation-handoff"),
        ),
        delegated_work=delegated,
    )
    return WorkerResult(
        attribution=WorkerResultAttribution(
            worker_ref=worker_ref,
            result_event_ref=_ref("irr.event", "scenario-c-escalation-result"),
        ),
        handoff=handoff,
        materials=(),
        needs=(
            WorkerNeed(
                need_ref=_ref("irr.worker_need", "external-evidence-scope"),
                kind=WorkerNeedKind.SCOPE,
                related_scope_refs=(),
                statement=(
                    "A material decision would require an external evidence surface outside "
                    "the current delegated CG2.42 scope."
                ),
            ),
            WorkerNeed(
                need_ref=_ref("irr.worker_need", "repository-mutation-boundary"),
                kind=WorkerNeedKind.EFFECT_BOUNDARY,
                related_scope_refs=(delegated.scopes[0].scope_ref,),
                statement=(
                    "Implementing a candidate would require repository mutation that crosses "
                    "the current delegation's forbidden-effect boundary."
                ),
            ),
        ),
        description=(
            "Codexia returns explicit escalation needs instead of widening the delegation."
        ),
    )


def _lineage() -> tuple[
    ResolvedIntent,
    WorkerResult,
    ContinuationInput,
    ResolvedIntent,
    SuccessorResolutionLineage,
]:
    predecessor = _predecessor()
    result = _worker_result(predecessor)
    continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "scenario-c-host"),
            _ref("irr.event", "scenario-c-worker-result-reentry"),
        ),
        ContinuationSourceKind.WORKER_RESULT,
        result,
    )
    successor = ResolvedIntent(
        predecessor.intent_request_identity,
        predecessor.context_envelope_identity,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-c"),
            _ref("irr.resolution_event", "scenario-c-after-worker-escalation"),
        ),
        (
            "Represent any external evidence acquisition or repository mutation as new "
            "successor semantics with its own scope, capability, and authority boundaries; "
            "do not alter the completed historical DelegatedWork envelope."
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
    return predecessor, result, continuation, successor, lineage


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


def test_scenario_c_worker_escalation_returns_need_without_widening_old_delegation() -> None:
    predecessor, result, continuation, _, lineage = _lineage()
    delegated = result.handoff.delegated_work
    original_identity = delegated.identity

    assert result.materials == ()
    assert {need.kind for need in result.needs} == {
        WorkerNeedKind.SCOPE,
        WorkerNeedKind.EFFECT_BOUNDARY,
    }
    assert continuation.source_kind is ContinuationSourceKind.WORKER_RESULT
    assert continuation.source == result
    assert continuation.resolved_intent_identity == predecessor.identity
    assert lineage.continuation_inputs == (continuation,)

    # Re-entry cannot mutate the historical delegation envelope.
    assert result.handoff.delegated_work.identity == original_identity
    statements = {item.statement for item in delegated.constraints}
    assert "External evidence acquisition is outside this delegation." in statements
    assert "Repository mutation is outside this delegation." in statements


def test_scenario_c_authorization_cannot_be_smuggled_in_as_worker_need_or_continuation() -> None:
    _, result, continuation, successor, lineage = _lineage()

    for record in (result, continuation, successor, lineage):
        keys = _all_keys(record.to_primitive())
        assert "authorization" not in keys
        assert "authorized" not in keys
        assert "retry" not in keys
        assert "fallback" not in keys
        assert "parent_complete" not in keys


def test_scenario_c_successor_resolution_is_new_semantics_not_old_envelope_mutation() -> None:
    predecessor, result, continuation, successor, lineage = _lineage()
    delegated = result.handoff.delegated_work

    assert lineage.predecessor == predecessor
    assert lineage.successor == successor
    assert successor.attribution.admission_event_ref != predecessor.attribution.admission_event_ref
    assert successor.identity != predecessor.identity
    assert successor.intent_request_identity == predecessor.intent_request_identity
    assert successor.context_envelope_identity == predecessor.context_envelope_identity

    primitive = delegated.to_primitive()
    assert "successor" not in _all_keys(primitive)
    assert "external evidence acquisition" in " ".join(
        item.statement.lower() for item in delegated.constraints
    )
    assert continuation.source_identity == result.identity


def test_scenario_c_worker_result_and_continuation_round_trip_preserve_lineage() -> None:
    _, result, continuation, _, _ = _lineage()

    decoded_result = WorkerResult.from_json_bytes(result.canonical_bytes())
    decoded_continuation = ContinuationInput.from_json_bytes(
        continuation.canonical_bytes()
    )

    assert decoded_result == result
    assert decoded_result.identity == result.identity
    assert decoded_continuation == continuation
    assert decoded_continuation.identity == continuation.identity
    assert decoded_continuation.source_identity == result.identity
