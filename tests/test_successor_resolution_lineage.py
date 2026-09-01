from __future__ import annotations

import copy

import pytest

from intent_resolution_runtime import (
    BindingAttribution,
    BindingInputRole,
    BindingIssue,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    ClarificationNeed,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    InformationNeed,
    InterchangeableChoicePolicy,
    RecordIdentity,
    ResolutionAttribution,
    ResolutionIssue,
    ResolutionIssueImpact,
    ResolutionIssueKind,
    ResolvedIntent,
    SerializationError,
    StableRef,
    SuccessorResolutionKind,
    SuccessorResolutionLineage,
    SymbolicReference,
    ValidationError,
    evaluate_binding,
)


REQUEST = RecordIdentity("sha256", "1" * 64)
CONTEXT_A = RecordIdentity("sha256", "2" * 64)
CONTEXT_B = RecordIdentity("sha256", "3" * 64)
SOURCE_ID = RecordIdentity("sha256", "4" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _predecessor(
    *, event: str = "resolve-predecessor-001", semantics: str = "Inspect bounded workspace."
) -> ResolvedIntent:
    return ResolvedIntent(
        intent_request_identity=REQUEST,
        context_envelope_identity=CONTEXT_A,
        admission_attribution=ResolutionAttribution(
            _ref("irr.resolver", "semantic-v1"), _ref("irr.event", event)
        ),
        semantics=semantics,
        assumptions=(),
        unresolved_issues=(),
        candidate_inputs=(),
    )


def _binding_issue(predecessor: ResolvedIntent, suffix: str) -> BindingIssue:
    scope = f"workspace:{suffix}"
    symbolic = SymbolicReference(
        predecessor.identity,
        _ref("irr.slot", f"selected-{suffix}"),
        "artifact.path",
        scope,
        f"Select one exact path for {suffix}.",
    )
    rule = BindingRule(
        predecessor.identity,
        _ref("irr.binding_rule", f"select-{suffix}"),
        symbolic,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (_ref("host.source", f"filesystem-{suffix}"),),
        (SOURCE_ID,),
        "artifact.path",
        scope,
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.REQUIRE_UNIQUE,
            (),
            (),
            InterchangeableChoicePolicy.NONE,
        ),
        f"Require one exact admitted path for {suffix}.",
        (),
        (),
        (),
    )
    issue = evaluate_binding(
        rule,
        (),
        attribution=BindingAttribution(
            _ref("irr.evaluator", "mechanical-binding-v1"),
            _ref("irr.event", f"binding-{suffix}-001"),
        ),
    )
    assert type(issue) is BindingIssue
    return issue


def _continuation(
    predecessor: ResolvedIntent, suffix: str, *, event: str | None = None
) -> ContinuationInput:
    return ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "continuation-test"),
            _ref("irr.event", event or f"reentry-{suffix}-001"),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        _binding_issue(predecessor, suffix),
    )


def _resolved_successor(
    predecessor: ResolvedIntent,
    *, event: str = "resolve-successor-001",
    request_identity: RecordIdentity | None = None,
) -> ResolvedIntent:
    return ResolvedIntent(
        intent_request_identity=request_identity or predecessor.intent_request_identity,
        context_envelope_identity=CONTEXT_B,
        admission_attribution=ResolutionAttribution(
            _ref("irr.resolver", "semantic-v1"), _ref("irr.event", event)
        ),
        semantics="Successor semantics after exact continuation material.",
        assumptions=(),
        unresolved_issues=(),
        candidate_inputs=(),
    )


def _clarification_successor(predecessor: ResolvedIntent) -> ClarificationNeed:
    issue = ResolutionIssue(
        ResolutionIssueKind.MATERIAL_AMBIGUITY,
        ResolutionIssueImpact.BLOCKING,
        "workspace:selection",
        "Two materially different successor scopes remain possible.",
        ("workspace:a", "workspace:b"),
    )
    return ClarificationNeed(
        predecessor.intent_request_identity,
        CONTEXT_B,
        ResolutionAttribution(
            _ref("irr.resolver", "semantic-v1"),
            _ref("irr.event", "clarification-successor-001"),
        ),
        "Which workspace should successor work target?",
        "workspace:selection",
        (issue,),
        (),
    )


def _information_successor(predecessor: ResolvedIntent) -> InformationNeed:
    issue = ResolutionIssue(
        ResolutionIssueKind.MISSING_INFORMATION,
        ResolutionIssueImpact.BLOCKING,
        "workspace:selection",
        "The exact successor workspace path is not available.",
        (),
    )
    return InformationNeed(
        predecessor.intent_request_identity,
        CONTEXT_B,
        ResolutionAttribution(
            _ref("irr.resolver", "semantic-v1"),
            _ref("irr.event", "information-successor-001"),
        ),
        "Obtain the exact successor workspace path.",
        "workspace:selection",
        "Successor semantics cannot bind the workspace without this material.",
        (issue,),
        (),
    )


@pytest.mark.parametrize(
    ("kind", "factory"),
    [
        (SuccessorResolutionKind.RESOLVED_INTENT, _resolved_successor),
        (SuccessorResolutionKind.CLARIFICATION_NEED, _clarification_successor),
        (SuccessorResolutionKind.INFORMATION_NEED, _information_successor),
    ],
)
def test_all_frozen_resolution_outputs_round_trip(kind, factory) -> None:
    predecessor = _predecessor()
    continuation = _continuation(predecessor, "primary")
    lineage = SuccessorResolutionLineage(
        predecessor, (continuation,), kind, factory(predecessor)
    )
    decoded = SuccessorResolutionLineage.from_json_bytes(lineage.canonical_bytes())
    assert decoded == lineage
    assert decoded.identity == lineage.identity


def test_input_order_is_canonical_by_source_identity() -> None:
    predecessor = _predecessor()
    first = _continuation(predecessor, "a")
    second = _continuation(predecessor, "b")
    successor = _resolved_successor(predecessor)
    left = SuccessorResolutionLineage(
        predecessor,
        (first, second),
        SuccessorResolutionKind.RESOLVED_INTENT,
        successor,
    )
    right = SuccessorResolutionLineage(
        predecessor,
        (second, first),
        SuccessorResolutionKind.RESOLVED_INTENT,
        successor,
    )
    assert left == right
    assert left.canonical_bytes() == right.canonical_bytes()
    assert left.identity == right.identity


def test_repeated_reentry_of_same_source_cannot_amplify_lineage() -> None:
    predecessor = _predecessor()
    source = _binding_issue(predecessor, "same-source")
    first = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "continuation-test"),
            _ref("irr.event", "reentry-same-a"),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        source,
    )
    second = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "continuation-test"),
            _ref("irr.event", "reentry-same-b"),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        source,
    )
    assert first.identity != second.identity
    assert first.source_identity == second.source_identity
    with pytest.raises(ValidationError, match="must not amplify one source"):
        SuccessorResolutionLineage(
            predecessor,
            (first, second),
            SuccessorResolutionKind.RESOLVED_INTENT,
            _resolved_successor(predecessor),
        )


def test_continuation_must_descend_from_exact_predecessor() -> None:
    predecessor = _predecessor()
    foreign = _predecessor(event="resolve-foreign-001", semantics="Foreign semantics.")
    with pytest.raises(ValidationError, match="exact predecessor ResolvedIntent"):
        SuccessorResolutionLineage(
            predecessor,
            (_continuation(foreign, "foreign"),),
            SuccessorResolutionKind.RESOLVED_INTENT,
            _resolved_successor(predecessor),
        )


def test_successor_preserves_request_and_has_distinct_admission_event() -> None:
    predecessor = _predecessor()
    continuation = _continuation(predecessor, "primary")
    with pytest.raises(ValidationError, match="preserve the predecessor IntentRequest"):
        SuccessorResolutionLineage(
            predecessor,
            (continuation,),
            SuccessorResolutionKind.RESOLVED_INTENT,
            _resolved_successor(
                predecessor, request_identity=RecordIdentity("sha256", "9" * 64)
            ),
        )
    with pytest.raises(ValidationError, match="predecessor admission occurrence"):
        SuccessorResolutionLineage(
            predecessor,
            (continuation,),
            SuccessorResolutionKind.RESOLVED_INTENT,
            _resolved_successor(
                predecessor,
                event=predecessor.admission_attribution.admission_event_ref.value,
            ),
        )
    with pytest.raises(ValidationError, match="every re-entry occurrence"):
        SuccessorResolutionLineage(
            predecessor,
            (continuation,),
            SuccessorResolutionKind.RESOLVED_INTENT,
            _resolved_successor(
                predecessor, event=continuation.attribution.reentry_event_ref.value
            ),
        )


def test_successor_kind_is_mechanical() -> None:
    predecessor = _predecessor()
    with pytest.raises(ValidationError, match="must match the exact successor type"):
        SuccessorResolutionLineage(
            predecessor,
            (_continuation(predecessor, "primary"),),
            SuccessorResolutionKind.CLARIFICATION_NEED,
            _resolved_successor(predecessor),
        )


def test_requires_nonempty_tuple_of_continuation_inputs() -> None:
    predecessor = _predecessor()
    successor = _resolved_successor(predecessor)
    with pytest.raises(ValidationError, match="must be a tuple"):
        SuccessorResolutionLineage(
            predecessor,
            [],  # type: ignore[arg-type]
            SuccessorResolutionKind.RESOLVED_INTENT,
            successor,
        )
    with pytest.raises(ValidationError, match="must not be empty"):
        SuccessorResolutionLineage(
            predecessor, (), SuccessorResolutionKind.RESOLVED_INTENT, successor
        )


def test_wire_rejects_hidden_policy_fields_and_bad_discriminator() -> None:
    predecessor = _predecessor()
    lineage = SuccessorResolutionLineage(
        predecessor,
        (_continuation(predecessor, "primary"),),
        SuccessorResolutionKind.RESOLVED_INTENT,
        _resolved_successor(predecessor),
    )
    primitive = lineage.to_primitive()
    assert set(primitive) == {
        "schema",
        "predecessor",
        "continuation_inputs",
        "successor_kind",
        "successor",
    }
    for forbidden in (
        "retry",
        "fallback",
        "authorized",
        "successor_work_plan",
        "parent_complete",
        "lineage_event_ref",
        "description",
    ):
        mutated = copy.deepcopy(primitive)
        mutated[forbidden] = "forbidden"
        with pytest.raises(SerializationError, match="invalid fields"):
            SuccessorResolutionLineage.from_primitive(mutated)

    unknown = copy.deepcopy(primitive)
    unknown["successor_kind"] = "retry"
    with pytest.raises(SerializationError, match="unsupported .*successor_kind"):
        SuccessorResolutionLineage.from_primitive(unknown)


def test_same_exact_relation_is_idempotent_and_type_is_closed() -> None:
    predecessor = _predecessor()
    continuation = _continuation(predecessor, "primary")
    successor = _resolved_successor(predecessor)
    first = SuccessorResolutionLineage(
        predecessor,
        (continuation,),
        SuccessorResolutionKind.RESOLVED_INTENT,
        successor,
    )
    second = SuccessorResolutionLineage(
        predecessor,
        (continuation,),
        SuccessorResolutionKind.RESOLVED_INTENT,
        successor,
    )
    assert first == second
    assert first.identity == second.identity

    with pytest.raises(TypeError, match="closed IR type"):
        class InvalidSuccessorResolutionLineage(SuccessorResolutionLineage):
            pass
