from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    BindingAttribution,
    BindingInputRole,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    ContextEnvelope,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    SymbolicReference,
    ValidationError,
    evaluate_binding,
)
from intent_resolution_runtime.attempt_outcome_continuation import (
    orchestrate_attempt_outcome_continuation,
)


SOURCE_IDENTITY = RecordIdentity("sha256", "a" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _predecessor() -> ResolvedIntent:
    request = IntentRequest(
        origin=OriginAttribution(
            OriginKind.HUMAN,
            _ref("human", "user"),
            _ref("host.event", "request-occurrence-collision"),
        ),
        principal_ref=_ref("principal", "user"),
        expression=IntentExpression("Resolve one bounded symbolic target."),
    )
    context = ContextEnvelope(
        request.identity,
        SourceAttribution(
            _ref("host.source", "context"),
            _ref("host.event", "context-occurrence-collision"),
        ),
        (),
    )
    return ResolvedIntent(
        request.identity,
        context.identity,
        ResolutionAttribution(
            _ref("irr.resolver", "m2.4-occurrence-test"),
            _ref("irr.resolution_event", "predecessor-occurrence"),
        ),
        "Resolve the bounded target using an already admitted mechanical binding rule.",
    )


def _binding_issue(
    predecessor: ResolvedIntent,
    *,
    binding_event_ref: StableRef,
):
    symbolic = SymbolicReference(
        predecessor.identity,
        _ref("irr.symbol", "target"),
        "artifact.path",
        "workspace:artifacts",
        "One future bounded artifact path.",
    )
    rule = BindingRule(
        predecessor.identity,
        _ref("irr.binding_rule", "target-unique"),
        symbolic,
        (BindingInputRole.OTHER_EXPLICIT,),
        (_ref("irr.source", "explicit-binding-input"),),
        (SOURCE_IDENTITY,),
        "artifact.path",
        "workspace:artifacts",
        (),
        BindingSelectionPolicy(BindingSelectionMode.REQUIRE_UNIQUE),
        "Require exactly one attributable bounded artifact path.",
    )
    return evaluate_binding(
        rule,
        (),
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "m2.4-test"),
            binding_event_ref,
        ),
    )


def test_selected_source_occurrence_cannot_alias_predecessor_admission() -> None:
    predecessor = _predecessor()
    source = _binding_issue(
        predecessor,
        binding_event_ref=predecessor.admission_attribution.admission_event_ref,
    )

    with pytest.raises(
        ValidationError,
        match="Continuation source occurrence must differ from the predecessor admission occurrence",
    ):
        orchestrate_attempt_outcome_continuation(
            predecessor,
            continuation_sources=(source,),
        )


def test_host_reentry_occurrence_cannot_alias_predecessor_admission() -> None:
    predecessor = _predecessor()
    source = _binding_issue(
        predecessor,
        binding_event_ref=_ref("irr.binding_event", "source-occurrence"),
    )
    continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "m2.4-test"),
            predecessor.admission_attribution.admission_event_ref,
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        source,
    )

    with pytest.raises(
        ValidationError,
        match="ContinuationInput re-entry occurrence must differ from the predecessor admission occurrence",
    ):
        orchestrate_attempt_outcome_continuation(
            predecessor,
            continuation_sources=(source,),
            continuation_inputs=(continuation,),
        )
