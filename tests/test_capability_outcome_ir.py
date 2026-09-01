from __future__ import annotations

import json

import pytest

from intent_resolution_runtime import (
    CapabilityAttempt,
    CapabilityAttemptAttribution,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffect,
    CapabilityEffectMatch,
    CapabilityEffectRequirement,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityOutcome,
    CapabilityOutcomeAttribution,
    CapabilityRequestedEffect,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    EvidenceRelation,
    OutcomeCompletionAssessment,
    OutcomeCompletionState,
    OutcomeEffectAssessment,
    OutcomeEffectCertainty,
    OutcomeEvidence,
    OutcomeEvidenceRole,
    OutcomeLifecycleAssessment,
    OutcomeLifecycleState,
    RecordIdentity,
    SerializationError,
    SourceAttribution,
    StableRef,
    ValidationError,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
)


RESOLVED = RecordIdentity("sha256", "7" * 64)
SOURCE_IDENTITY = RecordIdentity("sha256", "8" * 64)
TEMPORAL = RecordIdentity("sha256", "9" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _effectful_evaluation() -> CapabilityMatchEvaluation:
    plan_ref = _ref("irr.work_plan", "publish-001")
    step_ref = _ref("irr.work_step", "publish")
    completion = "Confirm the bounded artifact publication for the requested target."
    step = WorkStep(
        RESOLVED,
        plan_ref,
        step_ref,
        "artifact.publish",
        "workspace:artifact/report.txt",
        (),
        (),
        (),
        WorkContinuationMode.NONE,
        completion,
        "Publish one bounded artifact.",
    )
    plan = WorkPlan(
        RESOLVED,
        plan_ref,
        (step,),
        "Complete the bounded artifact publication plan.",
        "Publication plan.",
    )
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "artifact"),
        "artifact.path_scope",
        "workspace:artifact/report.txt",
        "Exact artifact target.",
    )
    requested_effect = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "publish"),
        "external.publish",
        (requested_scope.scope_ref,),
        "Publish the bounded artifact to the admitted target.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        requested_scope.scope_ref,
        (requested_scope,),
        (requested_effect,),
        (),
        "Exact effectful publication capability requirement.",
    )
    descriptor_scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "artifact-publish"),
        "artifact.path_scope",
        "Invocation must remain inside the exact artifact target.",
    )
    descriptor_effect = CapabilityEffect(
        _ref("irr.capability_effect", "external-publish"),
        "external.publish",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (descriptor_scope.requirement_ref,),
        "Publishing necessarily creates the requested external effect.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "artifact.publish.local"),
        "artifact.publish",
        (),
        (),
        (descriptor_scope,),
        (descriptor_effect,),
        (),
        completion,
        "Bounded artifact publication capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "outcome-test"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", "catalog-outcome-001"),
        ),
        "Exact bounded outcome test planning surface.",
        (descriptor,),
        "Outcome test Catalog snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "exact-v1"),
            _ref("irr.event", "match-outcome-001"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityScopeMatch(
                requested_scope.scope_ref,
                descriptor_scope.requirement_ref,
            ),
        ),
        (),
        (),
        (
            CapabilityEffectMatch(
                requested_effect.effect_ref,
                descriptor_effect.effect_ref,
            ),
        ),
        "Exact effectful publication capability match.",
    )
    return CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", "evaluation-outcome-001"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive exact Catalog evaluation for Outcome tests.",
    )


def _effectful_attempt() -> CapabilityAttempt:
    evaluation = _effectful_evaluation()
    return CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", "artifact-local"),
            _ref("irr.event", "attempt-outcome-001"),
        ),
        evaluation,
        evaluation.requirement.step_ref,
        (),
        (),
        "One attributable artifact publication attempt.",
    )


def _evidence(
    name: str,
    roles: tuple[OutcomeEvidenceRole, ...],
    statement: str,
    *,
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS,
) -> OutcomeEvidence:
    return OutcomeEvidence(
        _ref("irr.outcome_evidence", name),
        SourceAttribution(
            _ref("executor.source", "artifact-local"),
            _ref("executor.event", name),
        ),
        SOURCE_IDENTITY,
        relation,
        roles,
        (TEMPORAL,),
        "artifact.publish attempt",
        statement,
    )


def _success_outcome() -> CapabilityOutcome:
    attempt = _effectful_attempt()
    lifecycle = _evidence(
        "protocol-complete",
        (OutcomeEvidenceRole.LIFECYCLE,),
        "The executor completion protocol finished normally.",
    )
    receipt = _evidence(
        "publication-receipt",
        (OutcomeEvidenceRole.COMPLETION, OutcomeEvidenceRole.EFFECT),
        "The authoritative publication receipt confirms the requested artifact became published.",
    )
    effect_ref = attempt.capability_evaluation.requirement.requested_effects[0].effect_ref
    return CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "bounded-v1"),
            _ref("irr.event", "outcome-001"),
        ),
        attempt,
        (receipt, lifecycle),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
            (lifecycle.evidence_ref,),
            "The normal result protocol completed.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.SATISFIED,
            (receipt.evidence_ref,),
            "The WorkStep completion contract is satisfied for this Attempt.",
        ),
        (
            OutcomeEffectAssessment(
                effect_ref,
                OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                (receipt.evidence_ref,),
                "The requested external publication effect is confirmed.",
            ),
        ),
        "Confirmed successful bounded publication Outcome.",
    )


def test_capability_outcome_round_trip_and_independent_dimensions() -> None:
    outcome = _success_outcome()
    decoded = CapabilityOutcome.from_json_bytes(outcome.canonical_bytes())
    assert decoded == outcome
    assert decoded.identity == outcome.identity
    assert decoded.lifecycle.state is OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED
    assert decoded.completion.state is OutcomeCompletionState.SATISFIED
    assert decoded.effect_assessments[0].certainty is OutcomeEffectCertainty.CONFIRMED_OCCURRED
    assert outcome.has_material_unknown is False


def test_interrupted_unknown_outcome_is_representable_without_calling_it_failure() -> None:
    attempt = _effectful_attempt()
    disconnect = _evidence(
        "connection-loss",
        (
            OutcomeEvidenceRole.LIFECYCLE,
            OutcomeEvidenceRole.UNCERTAINTY,
            OutcomeEvidenceRole.TRANSPORT,
        ),
        "Connection was lost after request transmission; no material acknowledgement is available.",
    )
    effect_ref = attempt.capability_evaluation.requirement.requested_effects[0].effect_ref
    outcome = CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "bounded-v1"),
            _ref("irr.event", "outcome-unknown-001"),
        ),
        attempt,
        (disconnect,),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.INTERRUPTED,
            (disconnect.evidence_ref,),
            "The normal lifecycle was interrupted by connection loss.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.UNKNOWN,
            (disconnect.evidence_ref,),
            "Available evidence cannot establish whether completion semantics were satisfied.",
        ),
        (
            OutcomeEffectAssessment(
                effect_ref,
                OutcomeEffectCertainty.UNKNOWN,
                (disconnect.evidence_ref,),
                "Available evidence cannot establish whether the external effect occurred.",
            ),
        ),
        "Interrupted attempt with material unknown outcome.",
    )
    assert outcome.lifecycle.state is OutcomeLifecycleState.INTERRUPTED
    assert outcome.completion.state is OutcomeCompletionState.UNKNOWN
    assert outcome.effect_assessments[0].certainty is OutcomeEffectCertainty.UNKNOWN
    assert outcome.has_material_unknown is True


def test_failed_completion_can_preserve_known_partial_effect() -> None:
    attempt = _effectful_attempt()
    lifecycle = _evidence(
        "failure-protocol",
        (OutcomeEvidenceRole.LIFECYCLE,),
        "The executor returned through its normal failure protocol.",
    )
    partial = _evidence(
        "partial-effect",
        (
            OutcomeEvidenceRole.COMPLETION,
            OutcomeEvidenceRole.EFFECT,
            OutcomeEvidenceRole.PARTIAL_EFFECT,
        ),
        "A partial external publication exists, but the required completion contract was not satisfied.",
    )
    effect_ref = attempt.capability_evaluation.requirement.requested_effects[0].effect_ref
    outcome = CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "bounded-v1"),
            _ref("irr.event", "outcome-partial-001"),
        ),
        attempt,
        (lifecycle, partial),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
            (lifecycle.evidence_ref,),
            "The failure protocol completed normally.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.NOT_SATISFIED,
            (partial.evidence_ref,),
            "The required completion contract is known not to be satisfied.",
        ),
        (
            OutcomeEffectAssessment(
                effect_ref,
                OutcomeEffectCertainty.CONFIRMED_PARTIAL,
                (partial.evidence_ref,),
                "Known partial effect remains explicit despite failed completion.",
            ),
        ),
        "Failed completion with known partial effect history.",
    )
    assert outcome.completion.state is OutcomeCompletionState.NOT_SATISFIED
    assert outcome.effect_assessments[0].certainty is OutcomeEffectCertainty.CONFIRMED_PARTIAL


def test_transport_only_evidence_cannot_be_silently_strengthened_into_completion_evidence() -> None:
    attempt = _effectful_attempt()
    transport = _evidence(
        "http-response",
        (OutcomeEvidenceRole.LIFECYCLE, OutcomeEvidenceRole.TRANSPORT),
        "A transport response was received.",
    )
    effect_ref = attempt.capability_evaluation.requirement.requested_effects[0].effect_ref
    with pytest.raises(ValidationError, match="completion.evidence_refs requires evidence"):
        CapabilityOutcome(
            CapabilityOutcomeAttribution(
                _ref("irr.outcome_evaluator", "bounded-v1"),
                _ref("irr.event", "outcome-transport-only"),
            ),
            attempt,
            (transport,),
            OutcomeLifecycleAssessment(
                OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
                (transport.evidence_ref,),
                "Transport protocol completed.",
            ),
            OutcomeCompletionAssessment(
                OutcomeCompletionState.SATISFIED,
                (transport.evidence_ref,),
                "Invalid attempt to treat transport as semantic completion.",
            ),
            (
                OutcomeEffectAssessment(
                    effect_ref,
                    OutcomeEffectCertainty.UNKNOWN,
                    (transport.evidence_ref,),
                    "Effect remains unknown.",
                ),
            ),
            "Invalid transport-strengthened Outcome.",
        )


def test_effect_assessments_must_exactly_cover_requested_effects() -> None:
    outcome = _success_outcome()
    with pytest.raises(ValidationError, match="exactly cover all requested effects"):
        CapabilityOutcome(
            outcome.attribution,
            outcome.attempt,
            outcome.evidence,
            outcome.lifecycle,
            outcome.completion,
            (),
            outcome.description,
        )


def test_effect_assessment_cannot_reference_foreign_effect() -> None:
    outcome = _success_outcome()
    with pytest.raises(ValidationError, match="exactly cover all requested effects"):
        CapabilityOutcome(
            outcome.attribution,
            outcome.attempt,
            outcome.evidence,
            outcome.lifecycle,
            outcome.completion,
            (
                OutcomeEffectAssessment(
                    _ref("irr.capability_requested_effect", "foreign"),
                    OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                    outcome.effect_assessments[0].evidence_refs,
                    "Foreign effect assessment.",
                ),
            ),
            outcome.description,
        )


def test_assessments_may_reference_only_embedded_evidence() -> None:
    outcome = _success_outcome()
    missing = _ref("irr.outcome_evidence", "missing")
    with pytest.raises(ValidationError, match="reference embedded OutcomeEvidence"):
        CapabilityOutcome(
            outcome.attribution,
            outcome.attempt,
            outcome.evidence,
            OutcomeLifecycleAssessment(
                outcome.lifecycle.state,
                (missing,),
                outcome.lifecycle.description,
            ),
            outcome.completion,
            outcome.effect_assessments,
            outcome.description,
        )


def test_lifecycle_assessment_requires_lifecycle_role() -> None:
    attempt = _effectful_attempt()
    completion = _evidence(
        "completion-only",
        (OutcomeEvidenceRole.COMPLETION, OutcomeEvidenceRole.EFFECT),
        "Completion and effect evidence without lifecycle role.",
    )
    effect_ref = attempt.capability_evaluation.requirement.requested_effects[0].effect_ref
    with pytest.raises(ValidationError, match="lifecycle.evidence_refs requires evidence"):
        CapabilityOutcome(
            CapabilityOutcomeAttribution(
                _ref("irr.outcome_evaluator", "bounded-v1"),
                _ref("irr.event", "outcome-no-lifecycle-role"),
            ),
            attempt,
            (completion,),
            OutcomeLifecycleAssessment(
                OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
                (completion.evidence_ref,),
                "Invalid lifecycle assessment.",
            ),
            OutcomeCompletionAssessment(
                OutcomeCompletionState.SATISFIED,
                (completion.evidence_ref,),
                "Completion is supported.",
            ),
            (
                OutcomeEffectAssessment(
                    effect_ref,
                    OutcomeEffectCertainty.CONFIRMED_OCCURRED,
                    (completion.evidence_ref,),
                    "Effect is supported.",
                ),
            ),
            "Invalid lifecycle evidence role.",
        )


def test_outcome_occurrence_must_differ_from_attempt_occurrence() -> None:
    outcome = _success_outcome()
    with pytest.raises(ValidationError, match="must differ from CapabilityAttempt occurrence"):
        CapabilityOutcome(
            CapabilityOutcomeAttribution(
                _ref("irr.outcome_evaluator", "bounded-v1"),
                outcome.attempt.attribution.attempt_event_ref,
            ),
            outcome.attempt,
            outcome.evidence,
            outcome.lifecycle,
            outcome.completion,
            outcome.effect_assessments,
            outcome.description,
        )


def test_conflicting_outcome_evidence_has_no_implicit_precedence() -> None:
    attempt = _effectful_attempt()
    lifecycle = _evidence(
        "conflict-lifecycle",
        (OutcomeEvidenceRole.LIFECYCLE,),
        "The reporting protocol terminated normally.",
    )
    supports = _evidence(
        "receipt-supports",
        (OutcomeEvidenceRole.COMPLETION, OutcomeEvidenceRole.EFFECT),
        "One source reports publication completion.",
        relation=EvidenceRelation.SUPPORTS,
    )
    weakens = _evidence(
        "status-weakens",
        (
            OutcomeEvidenceRole.COMPLETION,
            OutcomeEvidenceRole.EFFECT,
            OutcomeEvidenceRole.UNCERTAINTY,
        ),
        "Another source cannot confirm the publication.",
        relation=EvidenceRelation.WEAKENS,
    )
    effect_ref = attempt.capability_evaluation.requirement.requested_effects[0].effect_ref
    outcome = CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "bounded-v1"),
            _ref("irr.event", "outcome-conflict-001"),
        ),
        attempt,
        (weakens, supports, lifecycle),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
            (lifecycle.evidence_ref,),
            "The reporting protocol completed.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.UNKNOWN,
            (supports.evidence_ref, weakens.evidence_ref),
            "Conflicting evidence leaves material completion unresolved.",
        ),
        (
            OutcomeEffectAssessment(
                effect_ref,
                OutcomeEffectCertainty.UNKNOWN,
                (supports.evidence_ref, weakens.evidence_ref),
                "Conflicting effect evidence has no implicit source precedence.",
            ),
        ),
        "Outcome with preserved conflicting evidence.",
    )
    assert {item.relation for item in outcome.evidence} == {
        EvidenceRelation.SUPPORTS,
        EvidenceRelation.WEAKENS,
    }
    assert outcome.has_material_unknown is True


def test_unknown_fields_are_rejected() -> None:
    outcome = _success_outcome()
    payload = json.loads(outcome.canonical_bytes().decode("utf-8"))
    payload["status"] = "succeeded"
    with pytest.raises(SerializationError):
        CapabilityOutcome.from_json_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8")
        )


def _pure_attempt() -> CapabilityAttempt:
    plan_ref = _ref("irr.work_plan", "inspect-pure-001")
    step_ref = _ref("irr.work_step", "inspect-pure")
    completion = "Return the bounded pure inspection result."
    step = WorkStep(
        RESOLVED,
        plan_ref,
        step_ref,
        "workspace.inspect",
        "workspace:pure",
        (),
        (),
        (),
        WorkContinuationMode.NONE,
        completion,
        "Inspect without admitted material effects.",
    )
    plan = WorkPlan(
        RESOLVED,
        plan_ref,
        (step,),
        "Complete the pure inspection plan.",
        "Pure inspection plan.",
    )
    requested_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "pure-workspace"),
        "filesystem.path_scope",
        "workspace:pure",
        "Pure workspace scope.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        requested_scope.scope_ref,
        (requested_scope,),
        (),
        (),
        "Pure inspection capability requirement.",
    )
    descriptor_scope = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "pure-workspace"),
        "filesystem.path_scope",
        "Remain inside the pure workspace scope.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "workspace.inspect.pure"),
        "workspace.inspect",
        (),
        (),
        (descriptor_scope,),
        (),
        (),
        completion,
        "Pure bounded workspace inspection capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "pure-outcome-test"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "test-host"),
            _ref("irr.event", "catalog-pure-outcome-001"),
        ),
        "Pure outcome test surface.",
        (descriptor,),
        "Pure outcome Catalog snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "exact-v1"),
            _ref("irr.event", "match-pure-outcome-001"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityScopeMatch(
                requested_scope.scope_ref,
                descriptor_scope.requirement_ref,
            ),
        ),
        (),
        (),
        (),
        "Exact pure inspection match.",
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "capability-evaluation-v1"),
            _ref("irr.event", "evaluation-pure-outcome-001"),
        ),
        requirement,
        snapshot,
        (match,),
        (),
        "Exhaustive pure inspection evaluation.",
    )
    return CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", "workspace-pure"),
            _ref("irr.event", "attempt-pure-outcome-001"),
        ),
        evaluation,
        step_ref,
        (),
        (),
        "One effect-free inspection Attempt.",
    )


def test_effect_free_attempt_requires_no_fake_effect_assessment() -> None:
    attempt = _pure_attempt()
    lifecycle = _evidence(
        "pure-lifecycle",
        (OutcomeEvidenceRole.LIFECYCLE,),
        "The pure computation protocol completed.",
    )
    completion = _evidence(
        "pure-completion",
        (OutcomeEvidenceRole.COMPLETION,),
        "The pure computation returned the required inspection result.",
    )
    outcome = CapabilityOutcome(
        CapabilityOutcomeAttribution(
            _ref("irr.outcome_evaluator", "bounded-v1"),
            _ref("irr.event", "outcome-pure-001"),
        ),
        attempt,
        (lifecycle, completion),
        OutcomeLifecycleAssessment(
            OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
            (lifecycle.evidence_ref,),
            "The pure computation protocol completed normally.",
        ),
        OutcomeCompletionAssessment(
            OutcomeCompletionState.SATISFIED,
            (completion.evidence_ref,),
            "The pure computation completion contract is satisfied.",
        ),
        (),
        "Effect-free Outcome without fake effect records.",
    )
    assert outcome.effect_assessments == ()
    assert outcome.has_material_unknown is False


def test_public_outcome_records_are_closed_against_subclassing() -> None:
    with pytest.raises(TypeError):
        class DerivedOutcome(CapabilityOutcome):
            pass
