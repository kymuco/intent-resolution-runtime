from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    BindingAttribution,
    BindingInputRole,
    BindingIssue,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    InterchangeableChoicePolicy,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    StableRef,
    SuccessorResolutionKind,
    SuccessorResolutionLineage,
    SymbolicReference,
    ValidationError,
    evaluate_binding,
)


REQUEST = RecordIdentity("sha256", "1" * 64)
CONTEXT = RecordIdentity("sha256", "2" * 64)
SOURCE_ID = RecordIdentity("sha256", "3" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _predecessor() -> ResolvedIntent:
    return ResolvedIntent(
        REQUEST,
        CONTEXT,
        ResolutionAttribution(
            _ref("irr.resolver", "semantic-v1"),
            _ref("irr.event", "resolve-predecessor-001"),
        ),
        "Inspect bounded workspace.",
        (),
        (),
        (),
    )


def _source(predecessor: ResolvedIntent, suffix: str, *, event: str) -> BindingIssue:
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
    result = evaluate_binding(
        rule,
        (),
        attribution=BindingAttribution(
            _ref("irr.evaluator", "mechanical-binding-v1"),
            _ref("irr.event", event),
        ),
    )
    assert type(result) is BindingIssue
    return result


def _continuation(
    predecessor: ResolvedIntent,
    suffix: str,
    *,
    source_event: str,
    reentry_event: str,
) -> ContinuationInput:
    return ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "continuation-test"),
            _ref("irr.event", reentry_event),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        _source(predecessor, suffix, event=source_event),
    )


def _successor(predecessor: ResolvedIntent, *, event: str) -> ResolvedIntent:
    return ResolvedIntent(
        predecessor.intent_request_identity,
        RecordIdentity("sha256", "4" * 64),
        ResolutionAttribution(
            _ref("irr.resolver", "semantic-v1"),
            _ref("irr.event", event),
        ),
        "Successor semantics after exact continuation material.",
        (),
        (),
        (),
    )


def test_continuation_exposes_mechanical_source_occurrence_without_wire_change() -> None:
    predecessor = _predecessor()
    continuation = _continuation(
        predecessor,
        "primary",
        source_event="binding-primary-001",
        reentry_event="reentry-primary-001",
    )
    assert continuation.source_event_ref == _ref("irr.event", "binding-primary-001")
    assert "source_event_ref" not in continuation.to_primitive()


def test_successor_admission_cannot_reuse_source_occurrence() -> None:
    predecessor = _predecessor()
    continuation = _continuation(
        predecessor,
        "primary",
        source_event="binding-primary-001",
        reentry_event="reentry-primary-001",
    )
    with pytest.raises(ValidationError, match="every source occurrence"):
        SuccessorResolutionLineage(
            predecessor,
            (continuation,),
            SuccessorResolutionKind.RESOLVED_INTENT,
            _successor(predecessor, event="binding-primary-001"),
        )


def test_source_occurrence_cannot_reuse_predecessor_admission_occurrence() -> None:
    predecessor = _predecessor()
    continuation = _continuation(
        predecessor,
        "primary",
        source_event="resolve-predecessor-001",
        reentry_event="reentry-primary-001",
    )
    with pytest.raises(ValidationError, match="source occurrence must differ"):
        SuccessorResolutionLineage(
            predecessor,
            (continuation,),
            SuccessorResolutionKind.RESOLVED_INTENT,
            _successor(predecessor, event="resolve-successor-001"),
        )


def test_source_and_reentry_occurrence_roles_cannot_overlap_across_inputs() -> None:
    predecessor = _predecessor()
    first = _continuation(
        predecessor,
        "a",
        source_event="binding-a-001",
        reentry_event="reentry-a-001",
    )
    second = _continuation(
        predecessor,
        "b",
        source_event="binding-b-001",
        reentry_event="binding-a-001",
    )
    with pytest.raises(ValidationError, match="source occurrences must remain distinct"):
        SuccessorResolutionLineage(
            predecessor,
            (first, second),
            SuccessorResolutionKind.RESOLVED_INTENT,
            _successor(predecessor, event="resolve-successor-001"),
        )
