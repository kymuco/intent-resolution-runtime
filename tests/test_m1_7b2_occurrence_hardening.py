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


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def test_reentry_occurrence_cannot_reuse_predecessor_admission_occurrence() -> None:
    predecessor = ResolvedIntent(
        intent_request_identity=RecordIdentity("sha256", "1" * 64),
        context_envelope_identity=RecordIdentity("sha256", "2" * 64),
        admission_attribution=ResolutionAttribution(
            _ref("irr.resolver", "semantic-v1"),
            _ref("irr.event", "resolve-predecessor-001"),
        ),
        semantics="Inspect bounded workspace.",
        assumptions=(),
        unresolved_issues=(),
        candidate_inputs=(),
    )
    symbolic = SymbolicReference(
        predecessor.identity,
        _ref("irr.slot", "selected-path"),
        "artifact.path",
        "workspace:project",
        "Select one exact path.",
    )
    rule = BindingRule(
        predecessor.identity,
        _ref("irr.binding_rule", "select-path"),
        symbolic,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (_ref("host.source", "filesystem"),),
        (RecordIdentity("sha256", "3" * 64),),
        "artifact.path",
        "workspace:project",
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.REQUIRE_UNIQUE,
            (),
            (),
            InterchangeableChoicePolicy.NONE,
        ),
        "Require one exact admitted path.",
        (),
        (),
        (),
    )
    source = evaluate_binding(
        rule,
        (),
        attribution=BindingAttribution(
            _ref("irr.evaluator", "mechanical-binding-v1"),
            _ref("irr.event", "binding-001"),
        ),
    )
    assert type(source) is BindingIssue
    continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "continuation-test"),
            predecessor.admission_attribution.admission_event_ref,
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        source,
    )
    successor = ResolvedIntent(
        predecessor.intent_request_identity,
        RecordIdentity("sha256", "4" * 64),
        ResolutionAttribution(
            _ref("irr.resolver", "semantic-v1"),
            _ref("irr.event", "resolve-successor-001"),
        ),
        "Successor semantics.",
        (),
        (),
        (),
    )

    with pytest.raises(ValidationError, match="re-entry occurrence must differ"):
        SuccessorResolutionLineage(
            predecessor,
            (continuation,),
            SuccessorResolutionKind.RESOLVED_INTENT,
            successor,
        )
