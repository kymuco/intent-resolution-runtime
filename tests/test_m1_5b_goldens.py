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
    StableRef,
    WorkerNeed,
    WorkerNeedKind,
    WorkerResult,
    WorkerResultAttribution,
    WorkerResultMaterial,
    WorkerResultMaterialRole,
)


RESOLVED = RecordIdentity("sha256", "1" * 64)
WORK_PLAN = RecordIdentity("sha256", "2" * 64)
SOURCE_RECORD = RecordIdentity("sha256", "3" * 64)
CAPABILITY_CONTRACT = RecordIdentity("sha256", "4" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> tuple[
    DelegatedScope,
    DelegatedContextReference,
    DelegatedCapabilityAllowance,
    DelegationConstraint,
    ExpectedDeliverable,
    DelegatedWork,
    DelegationHandoffAttribution,
    DelegatedWorkHandoff,
    WorkerResultAttribution,
    WorkerResultMaterial,
    WorkerNeed,
    WorkerResult,
]:
    scope = DelegatedScope(
        scope_ref=_ref("irr.delegated_scope", "project"),
        semantic_type="workspace.surface",
        value="workspace:project",
        description="Delegated project workspace.",
    )
    context = DelegatedContextReference(
        context_ref=_ref("irr.delegated_context", "evidence"),
        semantic_type="artifact.reference",
        scope_ref=scope.scope_ref,
        source_identity_refs=(SOURCE_RECORD,),
        description="Supplied project evidence.",
    )
    allowance = DelegatedCapabilityAllowance(
        allowance_ref=_ref(
            "irr.delegated_capability_allowance", "artifact.read"
        ),
        capability_ref=_ref("irr.capability", "artifact.read"),
        capability_contract_identity=CAPABILITY_CONTRACT,
        scope_refs=(scope.scope_ref,),
        description="Exact admitted read capability contract.",
    )
    constraint = DelegationConstraint(
        constraint_ref=_ref(
            "irr.delegation_constraint", "no-external-disclosure"
        ),
        kind=DelegationConstraintKind.FORBIDDEN_EFFECT,
        statement="No external disclosure.",
    )
    deliverable = ExpectedDeliverable(
        deliverable_ref=_ref("irr.expected_deliverable", "analysis-report"),
        semantic_type="artifact.report",
        scope_ref=scope.scope_ref,
        description="Expected analysis report.",
    )
    delegated = DelegatedWork(
        resolved_intent_identity=RESOLVED,
        delegation_ref=_ref("irr.delegated_work", "research-001"),
        parent_work_plan_identity_refs=(WORK_PLAN,),
        objective=(
            "Analyze the supplied project evidence and produce an inspectable report."
        ),
        scopes=(scope,),
        context_surface=(context,),
        allowed_capabilities=(allowance,),
        constraints=(constraint,),
        expected_deliverables=(deliverable,),
        completion_contract=(
            "Return the expected analysis report or explicit attributable need material."
        ),
        description="Bounded research delegation.",
    )
    handoff_attribution = DelegationHandoffAttribution(
        dispatcher_ref=_ref("irr.dispatcher", "worker-boundary-v1"),
        worker_ref=_ref("irr.worker", "research-worker-v1"),
        handoff_event_ref=_ref("irr.event", "handoff-research-worker-v1"),
    )
    handoff = DelegatedWorkHandoff(
        attribution=handoff_attribution,
        delegated_work=delegated,
    )
    result_attribution = WorkerResultAttribution(
        worker_ref=handoff_attribution.worker_ref,
        result_event_ref=_ref("irr.event", "result-research-worker-v1"),
    )
    material = WorkerResultMaterial(
        material_ref=_ref("irr.worker_result_material", "analysis-report"),
        role=WorkerResultMaterialRole.DELIVERABLE,
        semantic_type="artifact.report",
        scope_refs=(scope.scope_ref,),
        expected_deliverable_refs=(deliverable.deliverable_ref,),
        source_refs=(_ref("source", "supplied-evidence"),),
        source_identity_refs=(SOURCE_RECORD,),
        content="Inspectable analysis report.",
        description="Returned required analysis report.",
    )
    need = WorkerNeed(
        need_ref=_ref("irr.worker_need", "mutation-review"),
        kind=WorkerNeedKind.AUTHORITY,
        related_scope_refs=(scope.scope_ref,),
        statement=(
            "Repository mutation would require an external authority decision."
        ),
    )
    result = WorkerResult(
        attribution=result_attribution,
        handoff=handoff,
        materials=(material,),
        needs=(need,),
        description=(
            "Attributable Worker result with deliverable and explicit authority need."
        ),
    )
    return (
        scope,
        context,
        allowance,
        constraint,
        deliverable,
        delegated,
        handoff_attribution,
        handoff,
        result_attribution,
        material,
        need,
        result,
    )


def test_m15b_delegation_result_golden_digests_are_frozen() -> None:
    (
        scope,
        context,
        allowance,
        constraint,
        deliverable,
        delegated,
        handoff_attribution,
        handoff,
        result_attribution,
        material,
        need,
        result,
    ) = _fixture()

    expected = {
        "scope": "a0136fddf1dd1ac3b73559bc4384ca49e847cf775fcca55933c5445deeb271fa",
        "context": "b1c5665db6b14c074c9cb3ad0362b3d13c352c1ea595f9f4b6047d07ff8c9265",
        "allowance": "a86bc0327512c3b9fa12fd55222cbd6641e7fbee9a3ab9527595f03d4c1c4286",
        "constraint": "cf0e40b6bcb8fd2872a3673c42ba1929a22ed47190e0c6cdfda138a1de40c927",
        "deliverable": "1428d294757c7f35b4f3096bae412e455e2ba31e2ce112f5dbd44d1815cb3e38",
        "delegated": "660a82e4badfa4bfc9a90a9ed36e1e1b5cafc1c172c79fd0252a3a590292c64b",
        "handoff_attribution": "37c69543778417e1307e08b9da2c64bc24f179eb28ee7318aa1cda8ccf2dc286",
        "handoff": "a0375ee355da896938abd2cd862d4ffe8b07c4b2896d1ce7de0c415c83469a1f",
        "result_attribution": "06283881d8c6aaff3c377da1e068f0c8d7837797572204cefd7704f08ec0da48",
        "material": "7999e83bba8f0fd0fa25e6f2f176e412e96c78b342f4632bc388821c299f052c",
        "need": "02456a287ea45b9c5f7797a4eba4073427a98ab0a528e7ec06471eb9ca022d9b",
        "result": "6369f754f3c56c1ccbf175bc3193ce19582ef4c46aa62b238a47562316bc2b79",
    }
    actual = {
        "scope": scope.identity.digest,
        "context": context.identity.digest,
        "allowance": allowance.identity.digest,
        "constraint": constraint.identity.digest,
        "deliverable": deliverable.identity.digest,
        "delegated": delegated.identity.digest,
        "handoff_attribution": handoff_attribution.identity.digest,
        "handoff": handoff.identity.digest,
        "result_attribution": result_attribution.identity.digest,
        "material": material.identity.digest,
        "need": need.identity.digest,
        "result": result.identity.digest,
    }

    assert actual == expected


def test_m15b_golden_handoff_and_result_round_trip_preserve_identity() -> None:
    *_, delegated, handoff_attribution, handoff, result_attribution, material, need, result = (
        _fixture()
    )

    decoded_delegated = DelegatedWork.from_json_bytes(delegated.canonical_bytes())
    decoded_handoff = DelegatedWorkHandoff.from_json_bytes(handoff.canonical_bytes())
    decoded_result = WorkerResult.from_json_bytes(result.canonical_bytes())

    assert decoded_delegated == delegated
    assert decoded_delegated.identity == delegated.identity
    assert decoded_handoff == handoff
    assert decoded_handoff.identity == handoff.identity
    assert decoded_result == result
    assert decoded_result.identity == result.identity
