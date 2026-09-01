from __future__ import annotations

import pytest

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
    SerializationError,
    StableRef,
    ValidationError,
)


RESOLVED = RecordIdentity("sha256", "1" * 64)
WORK_PLAN = RecordIdentity("sha256", "2" * 64)
OTHER_WORK_PLAN = RecordIdentity("sha256", "3" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _scope(name: str) -> DelegatedScope:
    return DelegatedScope(
        scope_ref=_ref("irr.delegated_scope", name),
        semantic_type="workspace.surface",
        value=f"workspace:{name}",
        description=f"Delegated scope {name}.",
    )


def _context(name: str, scope_ref: StableRef) -> DelegatedContextReference:
    return DelegatedContextReference(
        context_ref=_ref("irr.delegated_context", name),
        semantic_type="artifact.reference",
        scope_ref=scope_ref,
        source_identity_refs=(RecordIdentity("sha256", name[0] * 64),)
        if name[0] in "abcdef"
        else (),
        description=f"Delegated context {name}.",
    )


def _constraint(name: str, kind: DelegationConstraintKind) -> DelegationConstraint:
    return DelegationConstraint(
        constraint_ref=_ref("irr.delegation_constraint", name),
        kind=kind,
        statement=f"Constraint {name}.",
    )


def _deliverable(name: str, scope_ref: StableRef) -> ExpectedDeliverable:
    return ExpectedDeliverable(
        deliverable_ref=_ref("irr.expected_deliverable", name),
        semantic_type="artifact.report",
        scope_ref=scope_ref,
        description=f"Expected deliverable {name}.",
    )


def _capability(
    name: str,
    scope_ref: StableRef,
    *,
    digest_char: str = "4",
) -> DelegatedCapabilityAllowance:
    return DelegatedCapabilityAllowance(
        allowance_ref=_ref("irr.delegated_capability_allowance", name),
        capability_ref=_ref("irr.capability", name),
        capability_contract_identity=RecordIdentity("sha256", digest_char * 64),
        scope_refs=(scope_ref,),
        description=f"Exact capability allowance {name}.",
    )


def _delegated_work(
    *,
    scopes: tuple[DelegatedScope, ...] | None = None,
    context_surface: tuple[DelegatedContextReference, ...] | None = None,
    allowed_capabilities: tuple[DelegatedCapabilityAllowance, ...] | None = None,
    constraints: tuple[DelegationConstraint, ...] | None = None,
    expected_deliverables: tuple[ExpectedDeliverable, ...] | None = None,
    parent_work_plan_identity_refs: tuple[RecordIdentity, ...] = (WORK_PLAN,),
) -> DelegatedWork:
    primary = _scope("project")
    scopes = (primary,) if scopes is None else scopes
    scope_ref = scopes[0].scope_ref
    context_surface = (
        (_context("artifact", scope_ref),)
        if context_surface is None
        else context_surface
    )
    allowed_capabilities = (
        (_capability("artifact.read", scope_ref),)
        if allowed_capabilities is None
        else allowed_capabilities
    )
    constraints = (
        (
            _constraint("no-external-disclosure", DelegationConstraintKind.FORBIDDEN_EFFECT),
            _constraint("review-required-before-mutation", DelegationConstraintKind.AUTHORITY_REQUIREMENT),
        )
        if constraints is None
        else constraints
    )
    expected_deliverables = (
        (_deliverable("analysis-report", scope_ref),)
        if expected_deliverables is None
        else expected_deliverables
    )
    return DelegatedWork(
        resolved_intent_identity=RESOLVED,
        delegation_ref=_ref("irr.delegated_work", "research-001"),
        parent_work_plan_identity_refs=parent_work_plan_identity_refs,
        objective="Analyze the supplied project evidence and produce an inspectable report.",
        scopes=scopes,
        context_surface=context_surface,
        allowed_capabilities=allowed_capabilities,
        constraints=constraints,
        expected_deliverables=expected_deliverables,
        completion_contract="Return the expected analysis report or later attributable blocked-result material.",
        description="Bounded research delegation.",
    )


def _handoff(
    delegated_work: DelegatedWork | None = None,
    *,
    worker: str = "research-worker-v1",
) -> DelegatedWorkHandoff:
    return DelegatedWorkHandoff(
        attribution=DelegationHandoffAttribution(
            dispatcher_ref=_ref("irr.dispatcher", "worker-boundary-v1"),
            worker_ref=_ref("irr.worker", worker),
            handoff_event_ref=_ref("irr.event", f"handoff-{worker}"),
        ),
        delegated_work=_delegated_work() if delegated_work is None else delegated_work,
    )


def test_delegated_work_round_trip_and_set_like_order_are_canonical() -> None:
    project = _scope("project")
    reports = _scope("reports")
    c1 = _context("artifact", project.scope_ref)
    c2 = _context("report-template", reports.scope_ref)
    k1 = _constraint("no-network", DelegationConstraintKind.FORBIDDEN_EFFECT)
    k2 = _constraint("preserve-lineage", DelegationConstraintKind.MATERIAL)
    d1 = _deliverable("analysis", reports.scope_ref)
    d2 = _deliverable("evidence-index", reports.scope_ref)
    cap1 = _capability("artifact.read", project.scope_ref, digest_char="4")
    cap2 = _capability("artifact.write_report", reports.scope_ref, digest_char="5")

    first = _delegated_work(
        scopes=(reports, project),
        context_surface=(c2, c1),
        allowed_capabilities=(cap2, cap1),
        constraints=(k2, k1),
        expected_deliverables=(d2, d1),
    )
    second = _delegated_work(
        scopes=(project, reports),
        context_surface=(c1, c2),
        allowed_capabilities=(cap1, cap2),
        constraints=(k1, k2),
        expected_deliverables=(d1, d2),
    )

    assert first == second
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.identity == second.identity
    assert DelegatedWork.from_json_bytes(first.canonical_bytes()) == first


def test_delegated_work_can_derive_directly_from_resolved_intent() -> None:
    delegated = _delegated_work(parent_work_plan_identity_refs=())
    assert delegated.parent_work_plan_identity_refs == ()


def test_delegated_work_allows_at_most_one_parent_work_plan_identity() -> None:
    with pytest.raises(ValidationError, match="at most 1"):
        _delegated_work(parent_work_plan_identity_refs=(WORK_PLAN, OTHER_WORK_PLAN))


def test_context_surface_must_reference_an_admitted_delegated_scope() -> None:
    admitted = _scope("project")
    foreign = _scope("foreign")
    context = _context("artifact", foreign.scope_ref)
    with pytest.raises(ValidationError, match="context entries"):
        _delegated_work(scopes=(admitted,), context_surface=(context,))


def test_expected_deliverable_must_reference_an_admitted_scope() -> None:
    admitted = _scope("project")
    foreign = _scope("foreign")
    deliverable = _deliverable("report", foreign.scope_ref)
    with pytest.raises(ValidationError, match="deliverables"):
        _delegated_work(scopes=(admitted,), expected_deliverables=(deliverable,))


def test_delegated_work_requires_at_least_one_scope_and_deliverable() -> None:
    with pytest.raises(ValidationError, match="scopes must not be empty"):
        DelegatedWork(
            resolved_intent_identity=RESOLVED,
            delegation_ref=_ref("irr.delegated_work", "empty-scope"),
            parent_work_plan_identity_refs=(WORK_PLAN,),
            objective="Bounded delegation with an invalid empty scope surface.",
            scopes=(),
            context_surface=(),
            allowed_capabilities=(),
            constraints=(),
            expected_deliverables=(),
            completion_contract="This constructor must fail before completion is admitted.",
            description="Invalid empty-scope delegation.",
        )

    project = _scope("project")
    with pytest.raises(ValidationError, match="expected_deliverables must not be empty"):
        _delegated_work(scopes=(project,), expected_deliverables=())


def test_allowed_capabilities_are_exact_contract_ceiling_not_unrestricted_default() -> None:
    delegated = _delegated_work(allowed_capabilities=())
    assert delegated.allowed_capabilities == ()
    assert "allowed_capabilities" in delegated.to_primitive()


def test_capability_allowance_identity_and_scope_are_material() -> None:
    project = _scope("project")
    first = _capability("artifact.read", project.scope_ref, digest_char="4")
    changed_contract = _capability("artifact.read", project.scope_ref, digest_char="5")
    assert first.identity != changed_contract.identity

    delegated_first = _delegated_work(scopes=(project,), allowed_capabilities=(first,))
    delegated_changed = _delegated_work(scopes=(project,), allowed_capabilities=(changed_contract,))
    assert delegated_first.identity != delegated_changed.identity


def test_capability_allowance_must_reference_admitted_scope() -> None:
    project = _scope("project")
    foreign = _scope("foreign")
    allowance = _capability("artifact.read", foreign.scope_ref)
    with pytest.raises(ValidationError, match="capability allowances"):
        _delegated_work(scopes=(project,), allowed_capabilities=(allowance,))


def test_duplicate_scope_context_capability_constraint_and_deliverable_refs_fail_closed() -> None:
    project = _scope("project")
    duplicate_scope = DelegatedScope(
        scope_ref=project.scope_ref,
        semantic_type="other.scope",
        value="workspace:other",
        description="Conflicting duplicate scope.",
    )
    with pytest.raises(ValidationError, match="duplicate scope_ref"):
        _delegated_work(scopes=(project, duplicate_scope))

    context = _context("artifact", project.scope_ref)
    duplicate_context = DelegatedContextReference(
        context_ref=context.context_ref,
        semantic_type="other.material",
        scope_ref=project.scope_ref,
        source_identity_refs=(),
        description="Duplicate context reference.",
    )
    with pytest.raises(ValidationError, match="duplicate context_ref"):
        _delegated_work(scopes=(project,), context_surface=(context, duplicate_context))

    capability = _capability("artifact.read", project.scope_ref)
    duplicate_allowance = DelegatedCapabilityAllowance(
        allowance_ref=capability.allowance_ref,
        capability_ref=_ref("irr.capability", "artifact.other"),
        capability_contract_identity=RecordIdentity("sha256", "5" * 64),
        scope_refs=(project.scope_ref,),
        description="Duplicate allowance ref.",
    )
    with pytest.raises(ValidationError, match="duplicate allowance_ref"):
        _delegated_work(scopes=(project,), allowed_capabilities=(capability, duplicate_allowance))

    same_capability_other_allowance = DelegatedCapabilityAllowance(
        allowance_ref=_ref("irr.delegated_capability_allowance", "second"),
        capability_ref=capability.capability_ref,
        capability_contract_identity=RecordIdentity("sha256", "5" * 64),
        scope_refs=(project.scope_ref,),
        description="Same logical capability with conflicting contract identity.",
    )
    with pytest.raises(ValidationError, match="duplicate capability_ref"):
        _delegated_work(scopes=(project,), allowed_capabilities=(capability, same_capability_other_allowance))

    constraint = _constraint("no-network", DelegationConstraintKind.FORBIDDEN_EFFECT)
    duplicate_constraint = DelegationConstraint(
        constraint_ref=constraint.constraint_ref,
        kind=DelegationConstraintKind.MATERIAL,
        statement="Different statement under the same ref.",
    )
    with pytest.raises(ValidationError, match="duplicate constraint_ref"):
        _delegated_work(scopes=(project,), constraints=(constraint, duplicate_constraint))

    deliverable = _deliverable("report", project.scope_ref)
    duplicate_deliverable = ExpectedDeliverable(
        deliverable_ref=deliverable.deliverable_ref,
        semantic_type="artifact.other",
        scope_ref=project.scope_ref,
        description="Duplicate deliverable ref.",
    )
    with pytest.raises(ValidationError, match="duplicate deliverable_ref"):
        _delegated_work(scopes=(project,), expected_deliverables=(deliverable, duplicate_deliverable))


def test_constraint_kinds_keep_forbidden_effect_and_authority_requirement_distinct() -> None:
    project = _scope("project")
    forbidden = _constraint("no-mutation", DelegationConstraintKind.FORBIDDEN_EFFECT)
    authority = _constraint("mutation-needs-review", DelegationConstraintKind.AUTHORITY_REQUIREMENT)
    delegated = _delegated_work(scopes=(project,), constraints=(authority, forbidden))
    kinds = {item.kind for item in delegated.constraints}
    assert kinds == {
        DelegationConstraintKind.FORBIDDEN_EFFECT,
        DelegationConstraintKind.AUTHORITY_REQUIREMENT,
    }


def test_context_reference_preserves_source_identity_lineage() -> None:
    project = _scope("project")
    source_a = RecordIdentity("sha256", "a" * 64)
    source_b = RecordIdentity("sha256", "b" * 64)
    context = DelegatedContextReference(
        context_ref=_ref("irr.delegated_context", "evidence"),
        semantic_type="evidence.bundle",
        scope_ref=project.scope_ref,
        source_identity_refs=(source_b, source_a),
        description="Selected evidence with preserved source identities.",
    )
    assert context.source_identity_refs == (source_a, source_b)
    assert DelegatedContextReference.from_json_bytes(context.canonical_bytes()) == context


def test_handoff_is_attributable_and_embeds_exact_delegated_work() -> None:
    delegated = _delegated_work()
    handoff = _handoff(delegated)
    assert handoff.delegated_work == delegated
    assert handoff.delegated_work.identity == delegated.identity
    assert handoff.attribution.worker_ref == _ref("irr.worker", "research-worker-v1")
    assert DelegatedWorkHandoff.from_json_bytes(handoff.canonical_bytes()) == handoff


def test_worker_substitution_changes_handoff_identity_without_rewriting_delegated_work() -> None:
    delegated = _delegated_work()
    first = _handoff(delegated, worker="research-worker-v1")
    second = _handoff(delegated, worker="research-worker-v2")
    assert first.delegated_work.identity == second.delegated_work.identity
    assert first.identity != second.identity


def test_delegated_work_handoff_has_no_authorization_surface() -> None:
    primitive = _handoff().to_primitive()

    def walk_keys(value: object) -> list[str]:
        if isinstance(value, dict):
            return list(value) + [key for child in value.values() for key in walk_keys(child)]
        if isinstance(value, list):
            return [key for child in value for key in walk_keys(child)]
        return []

    keys = set(walk_keys(primitive))
    assert not {"authorized", "authorization", "approved", "permission", "permission_granted", "safe"} & keys


def test_unknown_wire_fields_fail_closed() -> None:
    delegated = _delegated_work()
    primitive = delegated.to_primitive()
    primitive["authorized"] = "true"
    with pytest.raises(SerializationError, match="invalid fields"):
        DelegatedWork.from_primitive(primitive)

    handoff = _handoff()
    handoff_primitive = handoff.to_primitive()
    handoff_primitive["execute"] = "true"
    with pytest.raises(SerializationError, match="invalid fields"):
        DelegatedWorkHandoff.from_primitive(handoff_primitive)


def test_public_delegation_records_are_closed_ir_types() -> None:
    with pytest.raises(TypeError, match="closed IR type"):
        class InvalidDelegatedWork(DelegatedWork):
            pass

    with pytest.raises(TypeError, match="closed IR type"):
        class InvalidHandoff(DelegatedWorkHandoff):
            pass
