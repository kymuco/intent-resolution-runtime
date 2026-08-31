from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from intent_resolution_runtime import (
    BindingAttribution,
    BindingAttribute,
    BindingAttributeKind,
    BindingConstraint,
    BindingConstraintOperator,
    BindingInput,
    BindingInputRole,
    BindingIssue,
    BindingIssueKind,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    BoundValue,
    InterchangeableChoicePolicy,
    RecordIdentity,
    SerializationError,
    SourceAttribution,
    StableRef,
    SymbolicReference,
    ValidationError,
    evaluate_binding,
)


def _id(character: str) -> RecordIdentity:
    return RecordIdentity(algorithm="sha256", digest=character * 64)


RESOLVED = _id("1")
SOURCE = _id("2")
TEMPORAL = _id("3")
COMPLETE = _id("4")
EVIDENCE = _id("5")


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace=namespace, value=value)


def _attribution(event: str) -> SourceAttribution:
    return SourceAttribution(
        source_ref=_ref("host.source", "filesystem-search"),
        source_event_ref=_ref("host.event", event),
    )


def _binding_attribution(event: str = "bind-001") -> BindingAttribution:
    return BindingAttribution(
        evaluator_ref=_ref("irr.evaluator", "mechanical-binding-v1"),
        binding_event_ref=_ref("irr.event", event),
    )


def _symbolic() -> SymbolicReference:
    return SymbolicReference(
        resolved_intent_identity=RESOLVED,
        slot_ref=_ref("irr.slot", "selected-backup"),
        semantic_type="artifact.path",
        scope=r"D:\Backups",
        description="Newest organism_lab backup selected by admitted modification time.",
    )


def _input(
    *,
    input_name: str,
    value: str,
    mtime: str | None,
    source_identity: RecordIdentity = SOURCE,
    role: BindingInputRole = BindingInputRole.PLAN_LOCAL_OUTPUT,
    semantic_type: str = "artifact.path",
    scope: str = r"D:\Backups",
    completeness: tuple[RecordIdentity, ...] = (COMPLETE,),
) -> BindingInput:
    attributes = [
        BindingAttribute(
            name="name",
            kind=BindingAttributeKind.TEXT,
            value=input_name,
        )
    ]
    if mtime is not None:
        attributes.append(
            BindingAttribute(
                name="modification_time",
                kind=BindingAttributeKind.RFC3339_TIMESTAMP,
                value=mtime,
            )
        )
    return BindingInput(
        resolved_intent_identity=RESOLVED,
        input_ref=_ref("irr.binding_input", input_name),
        attribution=_attribution(f"search-{input_name}"),
        role=role,
        source_identity=source_identity,
        semantic_type=semantic_type,
        value=value,
        scope=scope,
        attributes=tuple(reversed(attributes)),
        temporal_basis_refs=(TEMPORAL,),
        completeness_refs=completeness,
        evidence_refs=(EVIDENCE,),
    )


def _rule(
    *,
    mode: BindingSelectionMode = BindingSelectionMode.MAX_ATTRIBUTE,
    constraints: tuple[BindingConstraint, ...] = (),
    allowed_sources: tuple[RecordIdentity, ...] = (SOURCE,),
    required_completeness: tuple[RecordIdentity, ...] = (COMPLETE,),
) -> BindingRule:
    if mode in (BindingSelectionMode.MAX_ATTRIBUTE, BindingSelectionMode.MIN_ATTRIBUTE):
        selection_policy = BindingSelectionPolicy(
            mode=mode,
            selector_attributes=("modification_time",),
            selector_kinds=(BindingAttributeKind.RFC3339_TIMESTAMP,),
        )
    elif mode is BindingSelectionMode.ANY_INTERCHANGEABLE:
        selection_policy = BindingSelectionPolicy(
            mode=mode,
            interchangeable_choice=InterchangeableChoicePolicy.CANONICAL_IDENTITY_MIN,
        )
    else:
        selection_policy = BindingSelectionPolicy(mode=mode)

    return BindingRule(
        resolved_intent_identity=RESOLVED,
        rule_ref=_ref("irr.binding_rule", "latest-backup"),
        symbolic_reference=_symbolic(),
        allowed_input_roles=(BindingInputRole.PLAN_LOCAL_OUTPUT,),
        allowed_source_identities=allowed_sources,
        input_semantic_type="artifact.path",
        required_scope=r"D:\Backups",
        constraints=constraints,
        selection_policy=selection_policy,
        description="Select the unique newest compatible backup by modification_time.",
        required_temporal_basis_refs=(TEMPORAL,),
        required_completeness_refs=required_completeness,
        required_evidence_refs=(EVIDENCE,),
    )


def _inputs() -> tuple[BindingInput, BindingInput]:
    return (
        _input(
            input_name="backup-a.zip",
            value=r"D:\Backups\backup-a.zip",
            mtime="2026-08-30T10:00:00+06:00",
        ),
        _input(
            input_name="backup-b.zip",
            value=r"D:\Backups\backup-b.zip",
            mtime="2026-08-30T12:00:00+06:00",
        ),
    )


def test_symbolic_reference_round_trip_and_immutability() -> None:
    reference = _symbolic()
    assert SymbolicReference.from_json_bytes(reference.canonical_bytes()) == reference
    with pytest.raises(FrozenInstanceError):
        reference.scope = "elsewhere"  # type: ignore[misc]


def test_binding_input_normalizes_attribute_and_reference_order() -> None:
    first = _input(
        input_name="backup-a.zip",
        value=r"D:\Backups\backup-a.zip",
        mtime="2026-08-30T10:00:00+06:00",
    )
    second = BindingInput(
        resolved_intent_identity=first.resolved_intent_identity,
        input_ref=first.input_ref,
        attribution=first.attribution,
        role=first.role,
        source_identity=first.source_identity,
        semantic_type=first.semantic_type,
        value=first.value,
        scope=first.scope,
        attributes=tuple(reversed(first.attributes)),
        temporal_basis_refs=tuple(reversed(first.temporal_basis_refs)),
        completeness_refs=tuple(reversed(first.completeness_refs)),
        evidence_refs=tuple(reversed(first.evidence_refs)),
    )
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.identity == second.identity


def test_binding_rule_rejects_foreign_symbolic_lineage() -> None:
    foreign = SymbolicReference(
        resolved_intent_identity=_id("a"),
        slot_ref=_ref("irr.slot", "selected-backup"),
        semantic_type="artifact.path",
        scope=r"D:\Backups",
        description="Foreign slot.",
    )
    with pytest.raises(ValidationError, match="same ResolvedIntent"):
        BindingRule(
            resolved_intent_identity=RESOLVED,
            rule_ref=_ref("irr.binding_rule", "foreign"),
            symbolic_reference=foreign,
            allowed_input_roles=(BindingInputRole.PLAN_LOCAL_OUTPUT,),
            allowed_source_identities=(SOURCE,),
            input_semantic_type="artifact.path",
            required_scope=r"D:\Backups",
            constraints=(),
            selection_policy=BindingSelectionPolicy(
                mode=BindingSelectionMode.REQUIRE_UNIQUE
            ),
            description="Invalid foreign lineage rule.",
        )


def test_extremum_policy_freezes_selector_kind_before_input_arrives() -> None:
    with pytest.raises(ValidationError, match="selector attribute and kind"):
        BindingSelectionPolicy(
            mode=BindingSelectionMode.MAX_ATTRIBUTE,
            selector_attributes=("modification_time",),
        )


def test_newest_timestamp_binds_unique_winner_and_retains_full_input_set() -> None:
    inputs = _inputs()
    result = evaluate_binding(_rule(), tuple(reversed(inputs)), attribution=_binding_attribution())
    assert type(result) is BoundValue
    assert result.value == r"D:\Backups\backup-b.zip"
    assert result.selected_input_identity == inputs[1].identity
    assert set(item.identity for item in result.binding_inputs) == set(
        item.identity for item in inputs
    )
    assert BoundValue.from_json_bytes(result.canonical_bytes()) == result


def test_binding_result_is_independent_of_input_presentation_order() -> None:
    inputs = _inputs()
    first = evaluate_binding(_rule(), inputs, attribution=_binding_attribution())
    second = evaluate_binding(
        _rule(), tuple(reversed(inputs)), attribution=_binding_attribution()
    )
    assert type(first) is BoundValue
    assert type(second) is BoundValue
    assert first.canonical_bytes() == second.canonical_bytes()


def test_tied_extremum_stops_without_hidden_tie_breaker() -> None:
    inputs = (
        _input(
            input_name="backup-a.zip",
            value=r"D:\Backups\backup-a.zip",
            mtime="2026-08-30T12:00:00+06:00",
        ),
        _input(
            input_name="backup-b.zip",
            value=r"D:\Backups\backup-b.zip",
            mtime="2026-08-30T12:00:00+06:00",
        ),
    )
    result = evaluate_binding(_rule(), inputs, attribution=_binding_attribution())
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.TIE


def test_equivalent_timestamp_offsets_are_a_tie() -> None:
    inputs = (
        _input(
            input_name="backup-a.zip",
            value=r"D:\Backups\backup-a.zip",
            mtime="2026-08-30T12:00:00+06:00",
        ),
        _input(
            input_name="backup-b.zip",
            value=r"D:\Backups\backup-b.zip",
            mtime="2026-08-30T06:00:00Z",
        ),
    )
    result = evaluate_binding(_rule(), inputs, attribution=_binding_attribution())
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.TIE


def test_zero_matches_does_not_guess() -> None:
    constraint = BindingConstraint(
        attribute_name="name",
        operator=BindingConstraintOperator.EQUALS,
        expected_kind=BindingAttributeKind.TEXT,
        expected_value="release.zip",
    )
    result = evaluate_binding(
        _rule(constraints=(constraint,)),
        _inputs(),
        attribution=_binding_attribution(),
    )
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.ZERO_MATCHES


def test_missing_selector_data_is_not_replaced_with_another_rule() -> None:
    missing = _input(
        input_name="backup-a.zip",
        value=r"D:\Backups\backup-a.zip",
        mtime=None,
    )
    result = evaluate_binding(_rule(), (missing,), attribution=_binding_attribution())
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.MISSING_REQUIRED_DATA


def test_missing_material_completeness_provenance_blocks_binding() -> None:
    incomplete = _input(
        input_name="backup-a.zip",
        value=r"D:\Backups\backup-a.zip",
        mtime="2026-08-30T10:00:00+06:00",
        completeness=(),
    )
    result = evaluate_binding(_rule(), (incomplete,), attribution=_binding_attribution())
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.MISSING_REQUIRED_DATA


@pytest.mark.parametrize(
    "input_value",
    [
        _input(
            input_name="backup-a.zip",
            value=r"D:\Backups\backup-a.zip",
            mtime="2026-08-30T10:00:00+06:00",
            source_identity=_id("9"),
        ),
        _input(
            input_name="backup-a.zip",
            value=r"D:\Backups\backup-a.zip",
            mtime="2026-08-30T10:00:00+06:00",
            role=BindingInputRole.OBSERVATION,
        ),
        _input(
            input_name="backup-a.zip",
            value="1234",
            mtime="2026-08-30T10:00:00+06:00",
            semantic_type="process.id",
        ),
        _input(
            input_name="backup-a.zip",
            value=r"W:\Elsewhere\backup-a.zip",
            mtime="2026-08-30T10:00:00+06:00",
            scope=r"W:\Elsewhere",
        ),
    ],
)
def test_structurally_plausible_but_semantically_incompatible_input_is_rejected(
    input_value: BindingInput,
) -> None:
    result = evaluate_binding(_rule(), (input_value,), attribution=_binding_attribution())
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.INCOMPATIBLE_INPUT


def test_selector_kind_is_rule_semantics_not_input_discretion() -> None:
    wrong_kind = BindingInput(
        resolved_intent_identity=RESOLVED,
        input_ref=_ref("irr.binding_input", "wrong-kind"),
        attribution=_attribution("wrong-kind"),
        role=BindingInputRole.PLAN_LOCAL_OUTPUT,
        source_identity=SOURCE,
        semantic_type="artifact.path",
        value=r"D:\Backups\backup-a.zip",
        scope=r"D:\Backups",
        attributes=(
            BindingAttribute(
                name="modification_time",
                kind=BindingAttributeKind.TEXT,
                value="2026-08-30T10:00:00+06:00",
            ),
        ),
        temporal_basis_refs=(TEMPORAL,),
        completeness_refs=(COMPLETE,),
        evidence_refs=(EVIDENCE,),
    )
    result = evaluate_binding(_rule(), (wrong_kind,), attribution=_binding_attribution())
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.INCOMPATIBLE_INPUT


def test_require_unique_refuses_multiple_matches() -> None:
    result = evaluate_binding(
        _rule(mode=BindingSelectionMode.REQUIRE_UNIQUE),
        _inputs(),
        attribution=_binding_attribution(),
    )
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.MULTIPLE_MATCHES


def test_any_interchangeable_has_explicit_deterministic_mechanical_policy() -> None:
    inputs = _inputs()
    result = evaluate_binding(
        _rule(mode=BindingSelectionMode.ANY_INTERCHANGEABLE),
        tuple(reversed(inputs)),
        attribution=_binding_attribution(),
    )
    assert type(result) is BoundValue
    assert result.selected_input_identity == min(
        (item.identity for item in inputs), key=str
    )


def test_any_interchangeable_requires_explicit_choice_policy() -> None:
    with pytest.raises(ValidationError, match="canonical_identity_min"):
        BindingSelectionPolicy(mode=BindingSelectionMode.ANY_INTERCHANGEABLE)


def test_binding_issue_cannot_lie_about_mechanical_result() -> None:
    with pytest.raises(ValidationError, match="does not match"):
        BindingIssue(
            binding_attribution=_binding_attribution(),
            rule=_rule(),
            binding_inputs=_inputs(),
            kind=BindingIssueKind.ZERO_MATCHES,
            scope=r"D:\Backups",
            description="False issue assertion.",
        )


def test_bound_value_cannot_override_selected_concrete_value() -> None:
    inputs = _inputs()
    valid = evaluate_binding(_rule(), inputs, attribution=_binding_attribution())
    assert type(valid) is BoundValue
    with pytest.raises(ValidationError, match="value must equal"):
        BoundValue(
            binding_attribution=valid.binding_attribution,
            rule=valid.rule,
            binding_inputs=valid.binding_inputs,
            selected_input_identity=valid.selected_input_identity,
            semantic_type=valid.semantic_type,
            value=r"D:\Backups\invented.zip",
            scope=valid.scope,
        )


def test_unknown_wire_fields_are_rejected() -> None:
    primitive = _symbolic().to_primitive()
    primitive["authorized"] = "true"
    import json

    data = json.dumps(primitive, ensure_ascii=False).encode("utf-8")
    with pytest.raises(SerializationError):
        SymbolicReference.from_json_bytes(data)


@pytest.mark.parametrize(
    "record_type",
    [
        SymbolicReference,
        BindingInput,
        BindingRule,
        BoundValue,
        BindingIssue,
        BindingAttribute,
        BindingConstraint,
        BindingSelectionPolicy,
        BindingAttribution,
    ],
)
def test_binding_public_record_types_are_closed(record_type: type) -> None:
    with pytest.raises(TypeError, match="closed IR type"):
        type(f"Evil{record_type.__name__}", (record_type,), {})


def test_binding_records_do_not_expose_authority_fields() -> None:
    result = evaluate_binding(_rule(), _inputs(), attribution=_binding_attribution())
    assert type(result) is BoundValue
    serialized = result.to_primitive()
    forbidden = {"authorized", "permission", "approved", "trusted", "safe", "verified"}
    assert forbidden.isdisjoint(serialized)
    assert forbidden.isdisjoint(result.rule.to_primitive())
    assert forbidden.isdisjoint(result.rule.symbolic_reference.to_primitive())
