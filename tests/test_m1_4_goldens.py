from __future__ import annotations

from intent_resolution_runtime import (
    BindingAttribution,
    BindingAttribute,
    BindingAttributeKind,
    BindingInput,
    BindingInputRole,
    BindingIssue,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    BoundValue,
    InterchangeableChoicePolicy,
    RecordIdentity,
    SourceAttribution,
    StableRef,
    SymbolicReference,
    evaluate_binding,
)


RESOLVED = RecordIdentity("sha256", "1" * 64)
SOURCE = RecordIdentity("sha256", "2" * 64)
TEMPORAL = RecordIdentity("sha256", "3" * 64)
COMPLETE = RecordIdentity("sha256", "4" * 64)
EVIDENCE = RecordIdentity("sha256", "5" * 64)
SELECTION_SCOPE = r"D:\Backups"
SOURCE_REF = StableRef("host.source", "filesystem-search")


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _source_attribution(event: str) -> SourceAttribution:
    return SourceAttribution(
        source_ref=SOURCE_REF,
        source_event_ref=_ref("host.event", event),
    )


def _binding_attribution() -> BindingAttribution:
    return BindingAttribution(
        evaluator_ref=_ref("irr.evaluator", "mechanical-binding-v1"),
        binding_event_ref=_ref("irr.event", "bind-001"),
    )


def _symbolic() -> SymbolicReference:
    return SymbolicReference(
        resolved_intent_identity=RESOLVED,
        slot_ref=_ref("irr.slot", "selected-backup"),
        semantic_type="artifact.path",
        selection_scope=SELECTION_SCOPE,
        description="Newest organism_lab backup selected by admitted modification time.",
    )


def _input(name: str, timestamp: str) -> BindingInput:
    value = rf"D:\Backups\{name}"
    return BindingInput(
        resolved_intent_identity=RESOLVED,
        input_ref=_ref("irr.binding_input", name),
        attribution=_source_attribution(f"search-{name}"),
        role=BindingInputRole.PLAN_LOCAL_OUTPUT,
        source_identity=SOURCE,
        semantic_type="artifact.path",
        value=value,
        selection_scope=SELECTION_SCOPE,
        value_scope=value,
        attributes=(
            BindingAttribute(
                name="modification_time",
                kind=BindingAttributeKind.RFC3339_TIMESTAMP,
                value=timestamp,
            ),
            BindingAttribute(name="name", kind=BindingAttributeKind.TEXT, value=name),
        ),
        temporal_basis_refs=(TEMPORAL,),
        completeness_refs=(COMPLETE,),
        evidence_refs=(EVIDENCE,),
    )


def _rule() -> BindingRule:
    return BindingRule(
        resolved_intent_identity=RESOLVED,
        rule_ref=_ref("irr.binding_rule", "latest-backup"),
        symbolic_reference=_symbolic(),
        allowed_input_roles=(BindingInputRole.PLAN_LOCAL_OUTPUT,),
        allowed_source_refs=(SOURCE_REF,),
        allowed_source_identities=(SOURCE,),
        input_semantic_type="artifact.path",
        required_selection_scope=SELECTION_SCOPE,
        constraints=(),
        selection_policy=BindingSelectionPolicy(
            mode=BindingSelectionMode.MAX_ATTRIBUTE,
            selector_attributes=("modification_time",),
            selector_kinds=(BindingAttributeKind.RFC3339_TIMESTAMP,),
            interchangeable_choice=InterchangeableChoicePolicy.NONE,
        ),
        description="Select the unique newest compatible backup by modification_time.",
        required_temporal_basis_refs=(TEMPORAL,),
        required_completeness_refs=(COMPLETE,),
        required_evidence_refs=(EVIDENCE,),
    )


def test_m14_binding_golden_digests_are_frozen() -> None:
    symbolic = _symbolic()
    older = _input("backup-a.zip", "2026-08-30T10:00:00+06:00")
    newer = _input("backup-b.zip", "2026-08-30T12:00:00+06:00")
    rule = _rule()
    bound = evaluate_binding(
        rule,
        (newer, older),
        attribution=_binding_attribution(),
    )
    issue = evaluate_binding(
        rule,
        (),
        attribution=_binding_attribution(),
    )

    assert type(bound) is BoundValue
    assert type(issue) is BindingIssue

    assert symbolic.identity.digest == (
        "ec1a9dc741af9bded6fbcfcf39e09b8772ca866ea77314b7e5553ebfca451a69"
    )
    assert older.identity.digest == (
        "80d924d187cb42fd2385d258294e6069d7fc601d127f3788dd8c609ebcb0e8c8"
    )
    assert newer.identity.digest == (
        "d87a892f54532f4acb6367fc0a62195001e9bdcfa509ac2cbaccf1e02b21c5e8"
    )
    assert rule.identity.digest == (
        "cdf10037dbeeae766b5eb7aaba51702d2828a7e11b4888f2db4b85ffbc32db03"
    )
    assert bound.identity.digest == (
        "c42a00e3a5632831215e56a2739d0b6671454d575b81d69bcbb3bc2cc2c9bd68"
    )
    assert issue.identity.digest == (
        "ba6fe8fb6071a8eec52e5893a37faf6967d2f00df894ac1d2a55471180e76b5e"
    )


def test_m14_golden_bound_value_retains_selected_scope_and_full_input_set() -> None:
    older = _input("backup-a.zip", "2026-08-30T10:00:00+06:00")
    newer = _input("backup-b.zip", "2026-08-30T12:00:00+06:00")
    result = evaluate_binding(
        _rule(),
        (older, newer),
        attribution=_binding_attribution(),
    )

    assert type(result) is BoundValue
    assert result.selected_input_identity == newer.identity
    assert result.selection_scope == SELECTION_SCOPE
    assert result.value_scope == r"D:\Backups\backup-b.zip"
    assert {item.identity for item in result.binding_inputs} == {older.identity, newer.identity}
