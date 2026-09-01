from __future__ import annotations

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
    SourceAttribution,
    StableRef,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
)


RESOLVED = RecordIdentity("sha256", "7" * 64)
SOURCE_IDENTITY = RecordIdentity("sha256", "8" * 64)
TEMPORAL = RecordIdentity("sha256", "9" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _attempt_fixture() -> CapabilityAttempt:
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
    evaluation = CapabilityMatchEvaluation(
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
    return CapabilityAttempt(
        CapabilityAttemptAttribution(
            _ref("irr.executor", "artifact-local"),
            _ref("irr.event", "attempt-outcome-001"),
        ),
        evaluation,
        step_ref,
        (),
        (),
        "One attributable artifact publication attempt.",
    )


def _evidence(
    name: str,
    roles: tuple[OutcomeEvidenceRole, ...],
    statement: str,
) -> OutcomeEvidence:
    return OutcomeEvidence(
        _ref("irr.outcome_evidence", name),
        SourceAttribution(
            _ref("executor.source", "artifact-local"),
            _ref("executor.event", name),
        ),
        SOURCE_IDENTITY,
        EvidenceRelation.SUPPORTS,
        roles,
        (TEMPORAL,),
        "artifact.publish attempt",
        statement,
    )


def _outcome_fixture() -> tuple[
    CapabilityOutcome,
    CapabilityOutcomeAttribution,
    OutcomeEvidence,
    OutcomeEvidence,
    OutcomeLifecycleAssessment,
    OutcomeCompletionAssessment,
    OutcomeEffectAssessment,
]:
    attempt = _attempt_fixture()
    lifecycle_evidence = _evidence(
        "protocol-complete",
        (OutcomeEvidenceRole.LIFECYCLE,),
        "The executor completion protocol finished normally.",
    )
    receipt_evidence = _evidence(
        "publication-receipt",
        (OutcomeEvidenceRole.COMPLETION, OutcomeEvidenceRole.EFFECT),
        "The authoritative publication receipt confirms the requested artifact became published.",
    )
    attribution = CapabilityOutcomeAttribution(
        _ref("irr.outcome_evaluator", "bounded-v1"),
        _ref("irr.event", "outcome-001"),
    )
    lifecycle = OutcomeLifecycleAssessment(
        OutcomeLifecycleState.NORMAL_PROTOCOL_COMPLETED,
        (lifecycle_evidence.evidence_ref,),
        "The normal result protocol completed.",
    )
    completion = OutcomeCompletionAssessment(
        OutcomeCompletionState.SATISFIED,
        (receipt_evidence.evidence_ref,),
        "The WorkStep completion contract is satisfied for this Attempt.",
    )
    effect = OutcomeEffectAssessment(
        attempt.capability_evaluation.requirement.requested_effects[0].effect_ref,
        OutcomeEffectCertainty.CONFIRMED_OCCURRED,
        (receipt_evidence.evidence_ref,),
        "The requested external publication effect is confirmed.",
    )
    outcome = CapabilityOutcome(
        attribution,
        attempt,
        (receipt_evidence, lifecycle_evidence),
        lifecycle,
        completion,
        (effect,),
        "Confirmed successful bounded publication Outcome.",
    )
    return (
        outcome,
        attribution,
        lifecycle_evidence,
        receipt_evidence,
        lifecycle,
        completion,
        effect,
    )


def test_m17a2_capability_outcome_golden_digests_are_frozen() -> None:
    (
        outcome,
        attribution,
        lifecycle_evidence,
        receipt_evidence,
        lifecycle,
        completion,
        effect,
    ) = _outcome_fixture()

    # Independent encoder control for the exact nested Attempt fixture.
    assert outcome.attempt.identity.digest == (
        "1e2daa7292151f06310099316649ee752fc86ebb454e72d629069f8554401912"
    )

    assert attribution.identity.digest == (
        "9a951c880ab3858fd19fbc5f98dd9631970eb16c0c44664d46f52e6b043fd3af"
    )
    assert lifecycle_evidence.identity.digest == (
        "915503b1d31d77cba664a5ee7f581cf7c1fe4e9fa19c2667cd81f79fd881e5a8"
    )
    assert receipt_evidence.identity.digest == (
        "89821a2ccdc41d078bdf52e1d0314177b496a7932ee333ea47cae6d388829a62"
    )
    assert lifecycle.identity.digest == (
        "344322154d3d2b7229df71a0b6b1fa885d2574c73dea8e356835ac4d1bee7b6e"
    )
    assert completion.identity.digest == (
        "552a12b6c153f33eaf18e3a090b2f3271e7b97bf938413f07d772981e73f369a"
    )
    assert effect.identity.digest == (
        "60e9f1eefa2929a1d7566c7db10df0015c314e5dfb88f96a6eaacfd8130af98f"
    )
    assert outcome.identity.digest == (
        "2205f35eceeaac1d5abe3b495a280737e404830eb2648cabe6d7a06a752c660e"
    )


def test_m17a2_capability_outcome_goldens_round_trip() -> None:
    outcome, attribution, lifecycle_evidence, receipt_evidence, lifecycle, completion, effect = (
        _outcome_fixture()
    )

    records = (
        (CapabilityOutcomeAttribution, attribution),
        (OutcomeEvidence, lifecycle_evidence),
        (OutcomeEvidence, receipt_evidence),
        (OutcomeLifecycleAssessment, lifecycle),
        (OutcomeCompletionAssessment, completion),
        (OutcomeEffectAssessment, effect),
        (CapabilityOutcome, outcome),
    )
    for record_type, record in records:
        decoded = record_type.from_json_bytes(record.canonical_bytes())
        assert decoded == record
        assert decoded.identity == record.identity
