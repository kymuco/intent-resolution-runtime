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
    BoundValue,
    ClarificationNeed,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    IntentExpression,
    IntentRequest,
    InterchangeableChoicePolicy,
    OriginAttribution,
    OriginKind,
    RecordIdentity,
    ResolutionAttribution,
    ResolutionIssue,
    ResolutionIssueImpact,
    ResolutionIssueKind,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    SuccessorResolutionKind,
    SuccessorResolutionLineage,
    SymbolicReference,
    ValidationError,
    evaluate_binding,
)


CONTEXT_IDENTITY = RecordIdentity("sha256", "2" * 64)
SEARCH_RESULT_IDENTITY = RecordIdentity("sha256", "3" * 64)
SELECTION_SCOPE = r"W:\backups\organism_lab"
BACKUP_A = r"W:\backups\organism_lab\organism_lab-a.zip"
BACKUP_B = r"W:\backups\organism_lab\organism_lab-b.zip"
LATEST_TIME = "2026-09-01T20:00:00+06:00"
SEARCH_SOURCE_REF = StableRef("host.source", "scenario-h-backup-search")


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> dict[str, object]:
    request = IntentRequest(
        origin=OriginAttribution(
            OriginKind.HUMAN,
            _ref("human", "user"),
            _ref("host.event", "scenario-h-request"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression(
            "Найди последний backup organism_lab, распакуй в W:\\organism_lab и запусти."
        ),
    )
    predecessor = ResolvedIntent(
        request.identity,
        CONTEXT_IDENTITY,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-h"),
            _ref("irr.resolution_event", "scenario-h-predecessor"),
        ),
        (
            "Find the unique newest organism_lab backup inside the admitted backup scope before "
            "any extraction or launch work continues."
        ),
        (),
        (),
        (),
    )

    symbolic = SymbolicReference(
        predecessor.identity,
        _ref("irr.slot", "scenario-h-selected-backup"),
        "artifact.path",
        SELECTION_SCOPE,
        "Unique newest organism_lab backup selected by admitted modification time.",
    )
    rule = BindingRule(
        predecessor.identity,
        _ref("irr.binding_rule", "scenario-h-newest-backup"),
        symbolic,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (SEARCH_SOURCE_REF,),
        (SEARCH_RESULT_IDENTITY,),
        "artifact.path",
        SELECTION_SCOPE,
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.MAX_ATTRIBUTE,
            ("modification_time",),
            (BindingAttributeKind.RFC3339_TIMESTAMP,),
        ),
        "Select only a unique newest returned backup; a tied newest value is unresolved.",
    )

    def candidate(name: str, path: str, event: str) -> BindingInput:
        return BindingInput(
            predecessor.identity,
            _ref("irr.binding_input", name),
            SourceAttribution(SEARCH_SOURCE_REF, _ref("host.event", event)),
            BindingInputRole.PLAN_LOCAL_OUTPUT,
            SEARCH_RESULT_IDENTITY,
            "artifact.path",
            path,
            SELECTION_SCOPE,
            path,
            (
                BindingAttribute(
                    "modification_time",
                    BindingAttributeKind.RFC3339_TIMESTAMP,
                    LATEST_TIME,
                ),
            ),
            (),
            (),
            (),
        )

    inputs = (
        candidate("organism_lab-a", BACKUP_A, "scenario-h-search-result-a"),
        candidate("organism_lab-b", BACKUP_B, "scenario-h-search-result-b"),
    )
    binding_attribution = BindingAttribution(
        _ref("irr.evaluator", "scenario-h-binding"),
        _ref("irr.event", "scenario-h-binding-tie"),
    )
    binding = evaluate_binding(rule, inputs, attribution=binding_attribution)
    assert isinstance(binding, BindingIssue)

    continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "scenario-h-host"),
            _ref("host.event", "scenario-h-reentry"),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        binding,
    )

    ambiguity = ResolutionIssue(
        ResolutionIssueKind.MATERIAL_AMBIGUITY,
        ResolutionIssueImpact.BLOCKING,
        "backup candidate selection",
        (
            "Returned search data contains two equally newest backups. Choosing either changes "
            "the concrete artifact that later mutation and launch semantics would target."
        ),
        (BACKUP_A, BACKUP_B),
    )
    clarification = ClarificationNeed(
        request.identity,
        CONTEXT_IDENTITY,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-h"),
            _ref("irr.resolution_event", "scenario-h-clarification"),
        ),
        "Найдено два одинаково новых backup. Какой использовать: organism_lab-a.zip или organism_lab-b.zip?",
        "backup candidate selection",
        (ambiguity,),
        (),
    )
    lineage = SuccessorResolutionLineage(
        predecessor,
        (continuation,),
        SuccessorResolutionKind.CLARIFICATION_NEED,
        clarification,
    )
    return {
        "request": request,
        "predecessor": predecessor,
        "rule": rule,
        "inputs": inputs,
        "binding": binding,
        "continuation": continuation,
        "clarification": clarification,
        "lineage": lineage,
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


def test_scenario_h_equal_newest_search_results_stop_mechanical_binding() -> None:
    fixture = _fixture()
    rule = fixture["rule"]
    inputs = fixture["inputs"]
    binding = fixture["binding"]
    assert isinstance(rule, BindingRule)
    assert isinstance(inputs, tuple)
    assert isinstance(binding, BindingIssue)

    assert rule.selection_policy.mode is BindingSelectionMode.MAX_ATTRIBUTE
    assert rule.selection_policy.interchangeable_choice is InterchangeableChoicePolicy.NONE
    assert binding.kind is BindingIssueKind.TIE
    assert {item.value for item in binding.binding_inputs} == {BACKUP_A, BACKUP_B}

    reversed_result = evaluate_binding(
        rule,
        tuple(reversed(inputs)),
        attribution=binding.binding_attribution,
    )
    assert isinstance(reversed_result, BindingIssue)
    assert reversed_result.canonical_bytes() == binding.canonical_bytes()


def test_scenario_h_tie_cannot_be_laundered_into_a_hidden_bound_value() -> None:
    fixture = _fixture()
    rule = fixture["rule"]
    inputs = fixture["inputs"]
    binding = fixture["binding"]
    assert isinstance(rule, BindingRule)
    assert isinstance(inputs, tuple)
    assert isinstance(binding, BindingIssue)

    first = inputs[0]
    with pytest.raises(ValidationError, match="BindingRule is unresolved"):
        BoundValue(
            binding.binding_attribution,
            rule,
            inputs,
            first.identity,
            first.semantic_type,
            first.value,
            first.selection_scope,
            first.value_scope,
        )

    primitive = binding.to_primitive()
    assert "selected_input_identity" not in _all_keys(primitive)
    assert "canonical_identity_min" not in repr(primitive)


def test_scenario_h_material_choice_reenters_irr_and_yields_successor_clarification() -> None:
    fixture = _fixture()
    predecessor = fixture["predecessor"]
    binding = fixture["binding"]
    continuation = fixture["continuation"]
    clarification = fixture["clarification"]
    lineage = fixture["lineage"]
    assert isinstance(predecessor, ResolvedIntent)
    assert isinstance(binding, BindingIssue)
    assert isinstance(continuation, ContinuationInput)
    assert isinstance(clarification, ClarificationNeed)
    assert isinstance(lineage, SuccessorResolutionLineage)

    assert continuation.source_kind is ContinuationSourceKind.BINDING_ISSUE
    assert continuation.source_identity == binding.identity
    assert continuation.resolved_intent_identity == predecessor.identity
    assert continuation.source_event_ref != continuation.attribution.reentry_event_ref

    assert lineage.predecessor == predecessor
    assert lineage.continuation_inputs == (continuation,)
    assert lineage.successor_kind is SuccessorResolutionKind.CLARIFICATION_NEED
    assert lineage.successor == clarification
    assert clarification.blocking_issues[0].kind is ResolutionIssueKind.MATERIAL_AMBIGUITY
    assert clarification.blocking_issues[0].alternatives == tuple(sorted((BACKUP_A, BACKUP_B)))


def test_scenario_h_returned_data_does_not_create_authority_or_silent_next_plan() -> None:
    fixture = _fixture()
    continuation = fixture["continuation"]
    clarification = fixture["clarification"]
    assert isinstance(continuation, ContinuationInput)
    assert isinstance(clarification, ClarificationNeed)

    keys = _all_keys(clarification.to_primitive()) | _all_keys(continuation.to_primitive())
    for forbidden in (
        "authorization",
        "authorized",
        "work_proposal",
        "capability_attempt",
        "selected_input_identity",
        "fallback",
    ):
        assert forbidden not in keys

    assert "artifact.path" in repr(continuation.to_primitive())
    assert "observation" not in keys


def test_scenario_h_successor_lineage_round_trip_preserves_exact_material_choice() -> None:
    fixture = _fixture()
    lineage = fixture["lineage"]
    assert isinstance(lineage, SuccessorResolutionLineage)

    decoded = SuccessorResolutionLineage.from_json_bytes(lineage.canonical_bytes())
    assert decoded == lineage
    assert decoded.identity == lineage.identity
    assert decoded.successor_kind is SuccessorResolutionKind.CLARIFICATION_NEED
    assert isinstance(decoded.successor, ClarificationNeed)
    assert decoded.successor.blocking_issues[0].alternatives == tuple(sorted((BACKUP_A, BACKUP_B)))
