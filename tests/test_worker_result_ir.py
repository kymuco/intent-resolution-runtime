from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from intent_resolution_runtime import (
    DelegatedCapabilityAllowance,
    DelegatedScope,
    DelegatedWork,
    DelegatedWorkHandoff,
    DelegationHandoffAttribution,
    ExpectedDeliverable,
    RecordIdentity,
    SerializationError,
    StableRef,
    ValidationError,
    WorkerNeed,
    WorkerNeedKind,
    WorkerResult,
    WorkerResultAttribution,
    WorkerResultMaterial,
    WorkerResultMaterialRole,
)


RESOLVED = RecordIdentity("sha256", "1" * 64)
WORK_PLAN = RecordIdentity("sha256", "2" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _scope(name: str = "project") -> DelegatedScope:
    return DelegatedScope(
        scope_ref=_ref("irr.delegated_scope", name),
        semantic_type="workspace.surface",
        value=f"workspace:{name}",
        description=f"Delegated scope {name}.",
    )


def _deliverable(scope_ref: StableRef, name: str = "analysis-report") -> ExpectedDeliverable:
    return ExpectedDeliverable(
        deliverable_ref=_ref("irr.expected_deliverable", name),
        semantic_type="artifact.report",
        scope_ref=scope_ref,
        description=f"Expected deliverable {name}.",
    )


def _handoff(*, worker: str = "research-worker-v1") -> DelegatedWorkHandoff:
    project = _scope()
    deliverable = _deliverable(project.scope_ref)
    delegated = DelegatedWork(
        resolved_intent_identity=RESOLVED,
        delegation_ref=_ref("irr.delegated_work", "research-001"),
        parent_work_plan_identity_refs=(WORK_PLAN,),
        objective="Analyze the supplied evidence and produce an inspectable report.",
        scopes=(project,),
        context_surface=(),
        allowed_capabilities=(
            DelegatedCapabilityAllowance(
                allowance_ref=_ref(
                    "irr.delegated_capability_allowance", "artifact.read"
                ),
                capability_ref=_ref("irr.capability", "artifact.read"),
                capability_contract_identity=RecordIdentity("sha256", "4" * 64),
                scope_refs=(project.scope_ref,),
                description="Exact admitted read capability contract.",
            ),
        ),
        constraints=(),
        expected_deliverables=(deliverable,),
        completion_contract=(
            "Return the expected report or explicit attributable need material."
        ),
        description="Bounded research delegation.",
    )
    return DelegatedWorkHandoff(
        attribution=DelegationHandoffAttribution(
            dispatcher_ref=_ref("irr.dispatcher", "worker-boundary-v1"),
            worker_ref=_ref("irr.worker", worker),
            handoff_event_ref=_ref("irr.event", f"handoff-{worker}"),
        ),
        delegated_work=delegated,
    )


def _material(
    handoff: DelegatedWorkHandoff,
    *,
    name: str = "report",
    role: WorkerResultMaterialRole = WorkerResultMaterialRole.DELIVERABLE,
    semantic_type: str = "artifact.report",
    expected: bool = True,
    scope_ref: StableRef | None = None,
) -> WorkerResultMaterial:
    delegated = handoff.delegated_work
    scope_ref = delegated.scopes[0].scope_ref if scope_ref is None else scope_ref
    expected_refs = (
        (delegated.expected_deliverables[0].deliverable_ref,)
        if expected
        else ()
    )
    return WorkerResultMaterial(
        material_ref=_ref("irr.worker_result_material", name),
        role=role,
        semantic_type=semantic_type,
        scope_refs=(scope_ref,),
        expected_deliverable_refs=expected_refs,
        source_refs=(_ref("source", "supplied-evidence"),),
        source_identity_refs=(RecordIdentity("sha256", "5" * 64),),
        content="Inspectable returned material.",
        description=f"Worker material {name}.",
    )


def _need(
    handoff: DelegatedWorkHandoff,
    *,
    name: str = "need-more-data",
    kind: WorkerNeedKind = WorkerNeedKind.INFORMATION,
    scope_ref: StableRef | None = None,
) -> WorkerNeed:
    refs = () if scope_ref is None else (scope_ref,)
    return WorkerNeed(
        need_ref=_ref("irr.worker_need", name),
        kind=kind,
        related_scope_refs=refs,
        statement="Additional attributable information is required.",
    )


def _result(
    *,
    worker: str = "research-worker-v1",
    materials: tuple[WorkerResultMaterial, ...] | None = None,
    needs: tuple[WorkerNeed, ...] = (),
) -> WorkerResult:
    handoff = _handoff(worker=worker)
    if materials is None:
        materials = (_material(handoff),)
    return WorkerResult(
        attribution=WorkerResultAttribution(
            worker_ref=handoff.attribution.worker_ref,
            result_event_ref=_ref("irr.event", f"result-{worker}"),
        ),
        handoff=handoff,
        materials=materials,
        needs=needs,
        description="Attributable Worker result envelope.",
    )


def test_worker_result_round_trip_and_set_like_order_are_canonical() -> None:
    handoff = _handoff()
    report = _material(handoff, name="report")
    finding = _material(
        handoff,
        name="finding",
        role=WorkerResultMaterialRole.FINDING,
        semantic_type="analysis.finding",
        expected=False,
    )
    need_a = _need(handoff, name="authority", kind=WorkerNeedKind.AUTHORITY)
    need_b = _need(handoff, name="clarify", kind=WorkerNeedKind.CLARIFICATION)
    attribution = WorkerResultAttribution(
        worker_ref=handoff.attribution.worker_ref,
        result_event_ref=_ref("irr.event", "result-canonical"),
    )

    first = WorkerResult(
        attribution=attribution,
        handoff=handoff,
        materials=(report, finding),
        needs=(need_a, need_b),
        description="Canonical result.",
    )
    second = WorkerResult(
        attribution=attribution,
        handoff=handoff,
        materials=(finding, report),
        needs=(need_b, need_a),
        description="Canonical result.",
    )

    assert first == second
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.identity == second.identity
    assert WorkerResult.from_json_bytes(first.canonical_bytes()) == first


def test_worker_result_is_bound_to_exact_handoff_and_worker() -> None:
    handoff = _handoff(worker="worker-a")
    material = _material(handoff)
    with pytest.raises(ValidationError, match="match the handed-off Worker"):
        WorkerResult(
            attribution=WorkerResultAttribution(
                worker_ref=_ref("irr.worker", "worker-b"),
                result_event_ref=_ref("irr.event", "result-wrong-worker"),
            ),
            handoff=handoff,
            materials=(material,),
            needs=(),
            description="Invalid substituted Worker result.",
        )

    other_handoff = _handoff(worker="worker-b")
    assert handoff.identity != other_handoff.identity


def test_worker_result_requires_material_or_need_without_status_enum() -> None:
    handoff = _handoff()
    with pytest.raises(ValidationError, match="at least one material or WorkerNeed"):
        WorkerResult(
            attribution=WorkerResultAttribution(
                worker_ref=handoff.attribution.worker_ref,
                result_event_ref=_ref("irr.event", "empty-result"),
            ),
            handoff=handoff,
            materials=(),
            needs=(),
            description="Invalid empty result.",
        )

    assert "status" not in WorkerResult.__dataclass_fields__


def test_completion_claim_is_material_not_completion_proof() -> None:
    handoff = _handoff()
    claim = _material(
        handoff,
        name="done-claim",
        role=WorkerResultMaterialRole.COMPLETION_CLAIM,
        semantic_type="worker.completion_claim",
        expected=False,
    )
    result = WorkerResult(
        attribution=WorkerResultAttribution(
            worker_ref=handoff.attribution.worker_ref,
            result_event_ref=_ref("irr.event", "done-claim-result"),
        ),
        handoff=handoff,
        materials=(claim,),
        needs=(),
        description="Worker asserted completion without required deliverable material.",
    )
    assert result.materials[0].role is WorkerResultMaterialRole.COMPLETION_CLAIM
    assert "parent_completed" not in WorkerResult.__dataclass_fields__
    assert "delegated_complete" not in WorkerResult.__dataclass_fields__


def test_deliverable_material_must_reference_expected_deliverable() -> None:
    handoff = _handoff()
    with pytest.raises(ValidationError, match="must reference at least one"):
        _material(handoff, expected=False)


def test_non_deliverable_material_cannot_claim_expected_deliverable() -> None:
    handoff = _handoff()
    with pytest.raises(ValidationError, match="only deliverable"):
        _material(
            handoff,
            role=WorkerResultMaterialRole.FINDING,
            semantic_type="artifact.report",
            expected=True,
        )


def test_expected_deliverable_semantic_type_and_scope_are_revalidated() -> None:
    handoff = _handoff()
    wrong_type = _material(
        handoff,
        semantic_type="artifact.patch",
    )
    with pytest.raises(ValidationError, match="semantic_type must match"):
        WorkerResult(
            attribution=WorkerResultAttribution(
                worker_ref=handoff.attribution.worker_ref,
                result_event_ref=_ref("irr.event", "wrong-type"),
            ),
            handoff=handoff,
            materials=(wrong_type,),
            needs=(),
            description="Invalid deliverable type.",
        )

    foreign_scope = _ref("irr.delegated_scope", "foreign")
    wrong_scope = _material(handoff, scope_ref=foreign_scope)
    with pytest.raises(ValidationError, match="admitted delegated scopes"):
        WorkerResult(
            attribution=WorkerResultAttribution(
                worker_ref=handoff.attribution.worker_ref,
                result_event_ref=_ref("irr.event", "wrong-scope"),
            ),
            handoff=handoff,
            materials=(wrong_scope,),
            needs=(),
            description="Invalid deliverable scope.",
        )


def test_worker_need_is_not_authority_or_scope_expansion() -> None:
    handoff = _handoff()
    need = _need(handoff, kind=WorkerNeedKind.AUTHORITY)
    result = WorkerResult(
        attribution=WorkerResultAttribution(
            worker_ref=handoff.attribution.worker_ref,
            result_event_ref=_ref("irr.event", "authority-need"),
        ),
        handoff=handoff,
        materials=(),
        needs=(need,),
        description="Worker requires an external authority decision.",
    )
    assert result.needs[0].kind is WorkerNeedKind.AUTHORITY
    primitive = result.to_primitive()
    assert "authorization" not in primitive
    assert "approved" not in primitive


def test_worker_need_related_scope_must_be_admitted_but_may_be_empty() -> None:
    handoff = _handoff()
    empty_related = _need(handoff, kind=WorkerNeedKind.SCOPE)
    result = WorkerResult(
        attribution=WorkerResultAttribution(
            worker_ref=handoff.attribution.worker_ref,
            result_event_ref=_ref("irr.event", "new-scope-need"),
        ),
        handoff=handoff,
        materials=(),
        needs=(empty_related,),
        description="Need may request a new scope without pretending it is admitted.",
    )
    assert result.needs[0].related_scope_refs == ()

    foreign = _need(
        handoff,
        name="foreign",
        kind=WorkerNeedKind.INFORMATION,
        scope_ref=_ref("irr.delegated_scope", "foreign"),
    )
    with pytest.raises(ValidationError, match="related scopes"):
        WorkerResult(
            attribution=result.attribution,
            handoff=handoff,
            materials=(),
            needs=(foreign,),
            description="Invalid foreign related scope.",
        )


def test_source_provenance_dimensions_are_preserved_without_truth_claim() -> None:
    handoff = _handoff()
    finding = _material(
        handoff,
        role=WorkerResultMaterialRole.FINDING,
        semantic_type="analysis.finding",
        expected=False,
    )
    result = WorkerResult(
        attribution=WorkerResultAttribution(
            worker_ref=handoff.attribution.worker_ref,
            result_event_ref=_ref("irr.event", "finding-result"),
        ),
        handoff=handoff,
        materials=(finding,),
        needs=(),
        description="Worker-mediated finding.",
    )
    material = result.materials[0]
    assert material.source_refs
    assert material.source_identity_refs
    assert "truth" not in material.to_primitive()
    assert "evidence" not in material.to_primitive()


def test_result_material_content_remains_inert_data() -> None:
    handoff = _handoff()
    material = WorkerResultMaterial(
        material_ref=_ref("irr.worker_result_material", "patch-text"),
        role=WorkerResultMaterialRole.ARTIFACT_REFERENCE,
        semantic_type="code.patch_text",
        scope_refs=(handoff.delegated_work.scopes[0].scope_ref,),
        expected_deliverable_refs=(),
        source_refs=(),
        source_identity_refs=(),
        content="rm -rf / && git push --force",
        description="Executable-looking result data remains inert.",
    )
    result = WorkerResult(
        attribution=WorkerResultAttribution(
            worker_ref=handoff.attribution.worker_ref,
            result_event_ref=_ref("irr.event", "patch-text-result"),
        ),
        handoff=handoff,
        materials=(material,),
        needs=(),
        description="Executable-looking text is result data.",
    )
    assert result.materials[0].content.startswith("rm -rf")


def test_duplicate_material_and_need_refs_fail_closed() -> None:
    handoff = _handoff()
    first = _material(handoff, name="dup")
    second = _material(handoff, name="dup")
    with pytest.raises(ValidationError, match="duplicate material_ref"):
        WorkerResult(
            attribution=WorkerResultAttribution(
                worker_ref=handoff.attribution.worker_ref,
                result_event_ref=_ref("irr.event", "dup-material"),
            ),
            handoff=handoff,
            materials=(first, second),
            needs=(),
            description="Duplicate material refs.",
        )

    need_a = _need(handoff, name="dup")
    need_b = _need(handoff, name="dup", kind=WorkerNeedKind.CLARIFICATION)
    with pytest.raises(ValidationError, match="duplicate need_ref"):
        WorkerResult(
            attribution=WorkerResultAttribution(
                worker_ref=handoff.attribution.worker_ref,
                result_event_ref=_ref("irr.event", "dup-need"),
            ),
            handoff=handoff,
            materials=(),
            needs=(need_a, need_b),
            description="Duplicate need refs.",
        )


def test_unknown_fields_fail_closed() -> None:
    result = _result()
    primitive = result.to_primitive()
    primitive["authorized"] = "true"
    import json

    with pytest.raises(SerializationError, match="invalid fields"):
        WorkerResult.from_json_bytes(
            json.dumps(primitive, separators=(",", ":"), sort_keys=True).encode()
        )


def test_worker_result_records_are_immutable() -> None:
    result = _result()
    with pytest.raises(FrozenInstanceError):
        result.description = "mutated"  # type: ignore[misc]
