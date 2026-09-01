from __future__ import annotations

from intent_resolution_runtime import (
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
    WorkerResult,
    WorkerResultAttribution,
    WorkerResultMaterial,
    WorkerResultMaterialRole,
)


REQUEST_IDENTITY = RecordIdentity("sha256", "1" * 64)
CONTEXT_IDENTITY = RecordIdentity("sha256", "2" * 64)
CG242_EVIDENCE_IDENTITY = RecordIdentity("sha256", "3" * 64)
ANALYSIS_CAPABILITY_CONTRACT = RecordIdentity("sha256", "4" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> dict[str, object]:
    resolved = ResolvedIntent(
        REQUEST_IDENTITY,
        CONTEXT_IDENTITY,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-c"),
            _ref("irr.resolution_event", "scenario-c-delegation-resolved"),
        ),
        (
            "Analyze the explicitly supplied CG2.42 result surface and propose bounded "
            "next-experiment candidates without repository mutation or external publication."
        ),
        (),
        (),
        (),
    )

    evidence_scope = DelegatedScope(
        scope_ref=_ref("irr.delegated_scope", "cg2.42-evidence"),
        semantic_type="experiment.evidence_surface",
        value="organism_lab:CG2.42:results",
        description="Exact bounded CG2.42 evidence surface delegated to the Worker.",
    )
    context = DelegatedContextReference(
        context_ref=_ref("irr.delegated_context", "cg2.42-results"),
        semantic_type="experiment.result_bundle",
        scope_ref=evidence_scope.scope_ref,
        source_identity_refs=(CG242_EVIDENCE_IDENTITY,),
        description="Explicit attributable CG2.42 result material supplied by IRR/Host.",
    )
    allowance = DelegatedCapabilityAllowance(
        allowance_ref=_ref("irr.delegated_capability_allowance", "analysis-read"),
        capability_ref=_ref("irr.capability", "analysis.inspect"),
        capability_contract_identity=ANALYSIS_CAPABILITY_CONTRACT,
        scope_refs=(evidence_scope.scope_ref,),
        description=(
            "Exact admitted subordinate analysis/read capability contract over only the "
            "delegated CG2.42 evidence scope."
        ),
    )

    constraints = tuple(
        DelegationConstraint(
            constraint_ref=_ref("irr.delegation_constraint", name),
            kind=DelegationConstraintKind.FORBIDDEN_EFFECT,
            statement=statement,
        )
        for name, statement in (
            ("no-repository-mutation", "Repository mutation is outside this delegation."),
            ("no-commit", "Creating commits is outside this delegation."),
            ("no-push", "Pushing repository state is outside this delegation."),
            ("no-external-publication", "External publication is outside this delegation."),
        )
    )

    candidates = ExpectedDeliverable(
        deliverable_ref=_ref("irr.expected_deliverable", "experiment-candidates"),
        semantic_type="experiment.candidate_set",
        scope_ref=evidence_scope.scope_ref,
        description="Bounded next-experiment candidate set.",
    )
    rationale = ExpectedDeliverable(
        deliverable_ref=_ref("irr.expected_deliverable", "candidate-rationale"),
        semantic_type="analysis.rationale",
        scope_ref=evidence_scope.scope_ref,
        description="Rationale grounded in the delegated CG2.42 evidence surface.",
    )
    evidence_refs = ExpectedDeliverable(
        deliverable_ref=_ref("irr.expected_deliverable", "evidence-references"),
        semantic_type="evidence.reference_set",
        scope_ref=evidence_scope.scope_ref,
        description="References back to supplied evidence supporting the proposal.",
    )

    delegated = DelegatedWork(
        resolved_intent_identity=resolved.identity,
        delegation_ref=_ref("irr.delegated_work", "scenario-c-cg2.42-analysis"),
        parent_work_plan_identity_refs=(),
        objective=(
            "Analyze only the supplied CG2.42 results and propose one or more bounded "
            "next experiment candidates with rationale and evidence references."
        ),
        scopes=(evidence_scope,),
        context_surface=(context,),
        allowed_capabilities=(allowance,),
        constraints=constraints,
        expected_deliverables=(candidates, rationale, evidence_refs),
        completion_contract=(
            "Return attributable experiment candidate material, rationale, and evidence "
            "references, or explicit WorkerNeed material without widening the delegation."
        ),
        description="Scenario C explicit Worker delegation envelope.",
    )

    worker_ref = _ref("irr.worker", "codexia")
    handoff = DelegatedWorkHandoff(
        attribution=DelegationHandoffAttribution(
            dispatcher_ref=_ref("irr.dispatcher", "worker-boundary"),
            worker_ref=worker_ref,
            handoff_event_ref=_ref("irr.event", "scenario-c-codexia-handoff"),
        ),
        delegated_work=delegated,
    )

    result = WorkerResult(
        attribution=WorkerResultAttribution(
            worker_ref=worker_ref,
            result_event_ref=_ref("irr.event", "scenario-c-codexia-result"),
        ),
        handoff=handoff,
        materials=(
            WorkerResultMaterial(
                material_ref=_ref("irr.worker_result_material", "experiment-candidates"),
                role=WorkerResultMaterialRole.DELIVERABLE,
                semantic_type="experiment.candidate_set",
                scope_refs=(evidence_scope.scope_ref,),
                expected_deliverable_refs=(candidates.deliverable_ref,),
                source_refs=(_ref("source", "cg2.42-results"),),
                source_identity_refs=(CG242_EVIDENCE_IDENTITY,),
                content=(
                    "Candidate A: isolate the strongest CG2.42 uncertainty with one bounded "
                    "follow-up experiment; Candidate B: replicate the observed boundary on a "
                    "fresh seed family."
                ),
                description="Worker-proposed next-experiment candidates.",
            ),
            WorkerResultMaterial(
                material_ref=_ref("irr.worker_result_material", "candidate-rationale"),
                role=WorkerResultMaterialRole.DELIVERABLE,
                semantic_type="analysis.rationale",
                scope_refs=(evidence_scope.scope_ref,),
                expected_deliverable_refs=(rationale.deliverable_ref,),
                source_refs=(_ref("source", "cg2.42-results"),),
                source_identity_refs=(CG242_EVIDENCE_IDENTITY,),
                content=(
                    "The candidates target uncertainty visible in the supplied CG2.42 result "
                    "surface without assuming new repository or external evidence."
                ),
                description="Bounded rationale for the proposed candidates.",
            ),
            WorkerResultMaterial(
                material_ref=_ref("irr.worker_result_material", "evidence-references"),
                role=WorkerResultMaterialRole.DELIVERABLE,
                semantic_type="evidence.reference_set",
                scope_refs=(evidence_scope.scope_ref,),
                expected_deliverable_refs=(evidence_refs.deliverable_ref,),
                source_refs=(_ref("source", "cg2.42-results"),),
                source_identity_refs=(CG242_EVIDENCE_IDENTITY,),
                content="CG2.42 supplied result bundle / exact delegated evidence surface.",
                description="Evidence references supporting the returned proposal.",
            ),
            WorkerResultMaterial(
                material_ref=_ref("irr.worker_result_material", "uncertainty"),
                role=WorkerResultMaterialRole.UNCERTAINTY,
                semantic_type="analysis.uncertainty",
                scope_refs=(evidence_scope.scope_ref,),
                expected_deliverable_refs=(),
                source_refs=(_ref("source", "cg2.42-results"),),
                source_identity_refs=(CG242_EVIDENCE_IDENTITY,),
                content="No claim is made about evidence outside the explicitly delegated surface.",
                description="Explicit Worker uncertainty/omission boundary.",
            ),
            WorkerResultMaterial(
                material_ref=_ref("irr.worker_result_material", "completion-claim"),
                role=WorkerResultMaterialRole.COMPLETION_CLAIM,
                semantic_type="delegation.completion_claim",
                scope_refs=(evidence_scope.scope_ref,),
                expected_deliverable_refs=(),
                source_refs=(_ref("irr.worker", "codexia"),),
                source_identity_refs=(),
                content="Worker claims the bounded delegated analysis is complete.",
                description="Worker completion claim only; not parent completion proof.",
            ),
        ),
        needs=(),
        description="Attributable Scenario C Worker result within the original envelope.",
    )

    return {
        "resolved": resolved,
        "scope": evidence_scope,
        "context": context,
        "allowance": allowance,
        "constraints": constraints,
        "deliverables": (candidates, rationale, evidence_refs),
        "delegated": delegated,
        "handoff": handoff,
        "result": result,
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


def test_scenario_c_uses_explicit_delegated_work_not_hidden_ordinary_workstep() -> None:
    fixture = _fixture()
    delegated = fixture["delegated"]
    handoff = fixture["handoff"]
    result = fixture["result"]

    assert isinstance(delegated, DelegatedWork)
    assert isinstance(handoff, DelegatedWorkHandoff)
    assert isinstance(result, WorkerResult)
    assert handoff.delegated_work == delegated
    assert result.handoff == handoff
    assert delegated.resolved_intent_identity == fixture["resolved"].identity

    primitive = delegated.to_primitive()
    assert primitive["schema"] == "irr.delegated_work.v1"
    assert "operation" not in _all_keys(primitive)
    assert "command" not in _all_keys(primitive)
    assert "work_step" not in _all_keys(primitive)


def test_scenario_c_capability_ceiling_and_forbidden_effect_bounds_remain_explicit() -> None:
    fixture = _fixture()
    delegated = fixture["delegated"]
    allowance = fixture["allowance"]
    constraints = fixture["constraints"]

    assert isinstance(delegated, DelegatedWork)
    assert isinstance(allowance, DelegatedCapabilityAllowance)
    assert allowance.capability_contract_identity == ANALYSIS_CAPABILITY_CONTRACT
    assert allowance.scope_refs == (fixture["scope"].scope_ref,)
    assert delegated.allowed_capabilities == (allowance,)
    assert all(item.kind is DelegationConstraintKind.FORBIDDEN_EFFECT for item in constraints)

    statements = {item.statement for item in constraints}
    assert "Repository mutation is outside this delegation." in statements
    assert "Creating commits is outside this delegation." in statements
    assert "Pushing repository state is outside this delegation." in statements
    assert "External publication is outside this delegation." in statements


def test_scenario_c_worker_result_preserves_deliverables_uncertainty_and_claim_boundaries() -> None:
    fixture = _fixture()
    result = fixture["result"]
    assert isinstance(result, WorkerResult)

    roles = {item.role for item in result.materials}
    assert WorkerResultMaterialRole.DELIVERABLE in roles
    assert WorkerResultMaterialRole.UNCERTAINTY in roles
    assert WorkerResultMaterialRole.COMPLETION_CLAIM in roles
    assert result.needs == ()

    deliverable_refs = {
        ref
        for item in result.materials
        if item.role is WorkerResultMaterialRole.DELIVERABLE
        for ref in item.expected_deliverable_refs
    }
    assert deliverable_refs == {
        item.deliverable_ref for item in fixture["deliverables"]
    }

    primitive = result.to_primitive()
    keys = _all_keys(primitive)
    assert "authorization" not in keys
    assert "authorized" not in keys
    assert "parent_complete" not in keys
    assert "candidate_resolution" not in keys
    assert "successor" not in keys


def test_scenario_c_worker_result_round_trip_preserves_exact_lineage() -> None:
    fixture = _fixture()
    result = fixture["result"]
    assert isinstance(result, WorkerResult)

    decoded = WorkerResult.from_json_bytes(result.canonical_bytes())
    assert decoded == result
    assert decoded.identity == result.identity
    assert decoded.handoff.delegated_work.identity == fixture["delegated"].identity
