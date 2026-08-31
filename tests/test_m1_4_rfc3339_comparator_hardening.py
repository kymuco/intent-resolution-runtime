from __future__ import annotations

import pytest

from intent_resolution_runtime import (
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
    RecordIdentity,
    SourceAttribution,
    StableRef,
    SymbolicReference,
    ValidationError,
    evaluate_binding,
)

RESOLVED = RecordIdentity("sha256", "1" * 64)
SOURCE = RecordIdentity("sha256", "2" * 64)
SELECTION_SCOPE = "scope:timestamps"
SOURCE_REF = StableRef("host.source", "rfc3339-hardening")


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _input(name: str, timestamp: str) -> BindingInput:
    return BindingInput(
        resolved_intent_identity=RESOLVED,
        input_ref=_ref("irr.binding_input", name),
        attribution=SourceAttribution(source_ref=SOURCE_REF, source_event_ref=_ref("host.event", name)),
        role=BindingInputRole.PLAN_LOCAL_OUTPUT,
        source_identity=SOURCE,
        semantic_type="test.value",
        value=name,
        selection_scope=SELECTION_SCOPE,
        value_scope=f"value:{name}",
        attributes=(BindingAttribute(name="timestamp", kind=BindingAttributeKind.RFC3339_TIMESTAMP, value=timestamp),),
    )


def _rule() -> BindingRule:
    symbolic = SymbolicReference(
        resolved_intent_identity=RESOLVED,
        slot_ref=_ref("irr.slot", "selected"),
        semantic_type="test.value",
        selection_scope=SELECTION_SCOPE,
        description="Select the exact latest timestamp.",
    )
    return BindingRule(
        resolved_intent_identity=RESOLVED,
        rule_ref=_ref("irr.binding_rule", "latest"),
        symbolic_reference=symbolic,
        allowed_input_roles=(BindingInputRole.PLAN_LOCAL_OUTPUT,),
        allowed_source_refs=(SOURCE_REF,),
        allowed_source_identities=(SOURCE,),
        input_semantic_type="test.value",
        required_selection_scope=SELECTION_SCOPE,
        constraints=(),
        selection_policy=BindingSelectionPolicy(
            mode=BindingSelectionMode.MAX_ATTRIBUTE,
            selector_attributes=("timestamp",),
            selector_kinds=(BindingAttributeKind.RFC3339_TIMESTAMP,),
        ),
        description="Choose the unique latest exact RFC3339 instant.",
    )


def _attribution() -> BindingAttribution:
    return BindingAttribution(evaluator_ref=_ref("irr.evaluator", "binding-v1"), binding_event_ref=_ref("irr.event", "r8"))


def test_arbitrary_fractional_precision_does_not_depend_on_decimal_to_int_conversion() -> None:
    prefix = "0" * 5000
    older = _input("older", f"2026-08-30T12:00:00.{prefix}1Z")
    newer = _input("newer", f"2026-08-30T12:00:00.{prefix}2Z")
    result = evaluate_binding(_rule(), (newer, older), attribution=_attribution())
    assert getattr(result, "value", None) == "newer"


def test_year_zero_and_lowercase_rfc3339_forms_compare_as_exact_instants() -> None:
    first = _input("first", "0000-01-01t00:00:00z")
    second = _input("second", "0000-01-01T01:00:00+01:00")
    result = evaluate_binding(_rule(), (first, second), attribution=_attribution())
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.TIE


@pytest.mark.parametrize("mode", [BindingSelectionMode.MAX_ATTRIBUTE, BindingSelectionMode.MIN_ATTRIBUTE])
def test_text_extrema_are_not_admitted_without_an_explicit_text_ordering_contract(mode: BindingSelectionMode) -> None:
    with pytest.raises(ValidationError, match="rfc3339_timestamp selector kind"):
        BindingSelectionPolicy(mode=mode, selector_attributes=("name",), selector_kinds=(BindingAttributeKind.TEXT,))


def test_fractional_trailing_zero_forms_compare_as_the_same_instant() -> None:
    first = _input("first", "2026-08-30T12:00:00.1Z")
    second = _input("second", "2026-08-30t12:00:00.1000z")
    result = evaluate_binding(_rule(), (first, second), attribution=_attribution())
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.TIE



def test_non_ascii_decimal_digits_are_not_rfc3339_digits() -> None:
    with pytest.raises(ValidationError, match="RFC3339 timestamp"):
        BindingAttribute(
            name="timestamp",
            kind=BindingAttributeKind.RFC3339_TIMESTAMP,
            value="2026-08-30T12:00:00.١Z",
        )


def test_fractional_comparison_preserves_numeric_order_across_lengths() -> None:
    earlier = _input("earlier", "2026-08-30T12:00:00.19Z")
    later = _input("later", "2026-08-30T12:00:00.2Z")
    result = evaluate_binding(_rule(), (later, earlier), attribution=_attribution())
    assert getattr(result, "value", None) == "later"

    earlier_prefix = _input("earlier-prefix", "2026-08-30T12:00:00.1Z")
    later_prefix = _input("later-prefix", "2026-08-30T12:00:00.11Z")
    result = evaluate_binding(
        _rule(),
        (earlier_prefix, later_prefix),
        attribution=_attribution(),
    )
    assert getattr(result, "value", None) == "later-prefix"


def test_proleptic_gregorian_validation_covers_century_rules_and_year_zero() -> None:
    BindingAttribute(
        name="timestamp",
        kind=BindingAttributeKind.RFC3339_TIMESTAMP,
        value="0000-02-29T00:00:00Z",
    )
    BindingAttribute(
        name="timestamp",
        kind=BindingAttributeKind.RFC3339_TIMESTAMP,
        value="2000-02-29T00:00:00Z",
    )
    with pytest.raises(ValidationError, match="invalid calendar date"):
        BindingAttribute(
            name="timestamp",
            kind=BindingAttributeKind.RFC3339_TIMESTAMP,
            value="1900-02-29T00:00:00Z",
        )
