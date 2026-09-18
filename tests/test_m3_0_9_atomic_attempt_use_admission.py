from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256

import pytest

from intent_resolution_runtime import (
    AuthorizationApplicabilityAttribution,
    AuthorizationApplicabilityEvaluation,
    AuthorizationConditionAssessment,
    AuthorizationConditionDisposition,
    AuthorizationConditionUseAssessment,
    AuthorizationConditionUseMode,
    AuthorizationUsePolicyAttribution,
    AuthorizationUsePolicyEvaluation,
    AuthorizationUsePolicyResult,
    CapabilityAttempt,
    CapabilityAttemptAttribution,
    CapabilityAttemptUseAdmission,
    CapabilityAttemptUseAdmissionAttribution,
    CapabilityAttemptUseAdmissionResult,
    InMemoryCapabilityAttemptUseAdmissionRepository,
    RecordIdentity,
    StableRef,
    ValidationError,
    evaluate_authorization_use_policy,
)
from tests.test_m3_0_8_authorization_applicability_evaluation import (
    _authorization,
    _directive,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _context(label: str) -> tuple[StableRef, RecordIdentity]:
    return (
        _ref("irr.authorization_use_context", label),
        RecordIdentity("sha256", sha256(label.encode("utf-8")).hexdigest()),
    )


def _applicability(
    *,
    label: str,
    directives=(),
):
    authorization, evaluation = _authorization(
        label=label,
        directives=tuple(directives),
    )
    context_ref, context_identity = _context(label)
    assessments = tuple(
        AuthorizationConditionAssessment(
            directive_ref=directive.directive_ref,
            disposition=AuthorizationConditionDisposition.SATISFIED,
            evidence_refs=(
                _ref(
                    "irr.authorization_use_evidence",
                    f"{label}-{directive.directive_ref.value}",
                ),
            ),
            rationale="Exact current-use evidence reports this condition satisfied.",
        )
        for directive in directives
    )
    applicability = AuthorizationApplicabilityEvaluation(
        attribution=AuthorizationApplicabilityAttribution(
            evaluator_ref=_ref(
                "irr.authorization_applicability_evaluator",
                "m3-0-9-test",
            ),
            evaluation_event_ref=_ref("irr.event", f"applicability-{label}"),
            use_context_ref=context_ref,
            use_context_identity=context_identity,
        ),
        authorization=authorization,
        step_ref=authorization.authorized_step_refs[0],
        condition_assessments=assessments,
        description="Exact M3.0.9 prerequisite applicability evidence.",
    )
    return authorization, evaluation, applicability


def _use_policy(
    applicability: AuthorizationApplicabilityEvaluation,
    *,
    label: str,
    modes: dict[StableRef, AuthorizationConditionUseMode],
) -> AuthorizationUsePolicyEvaluation:
    return AuthorizationUsePolicyEvaluation(
        attribution=AuthorizationUsePolicyAttribution(
            evaluator_ref=_ref("irr.authorization_use_policy_evaluator", "test"),
            evaluation_event_ref=_ref("irr.event", f"use-policy-{label}"),
            use_context_ref=applicability.attribution.use_context_ref,
            use_context_identity=applicability.attribution.use_context_identity,
        ),
        authorization=applicability.authorization,
        step_ref=applicability.step_ref,
        condition_assessments=tuple(
            AuthorizationConditionUseAssessment(
                directive_ref=directive.directive_ref,
                mode=modes[directive.directive_ref],
                evidence_refs=(
                    _ref(
                        "irr.authorization_use_policy_evidence",
                        f"{label}-{directive.directive_ref.value}",
                    ),
                ),
                rationale="Explicit externally supplied use-mode classification.",
            )
            for directive in applicability.authorization.conditions
        ),
        description="Exact M3.0.9 Authorization use-policy evaluation.",
    )


def _attempt(
    applicability: AuthorizationApplicabilityEvaluation,
    evaluation,
    *,
    event: str,
) -> CapabilityAttempt:
    return CapabilityAttempt(
        attribution=CapabilityAttemptAttribution(
            executor_ref=_ref("irr.executor", "m3-0-9-test"),
            attempt_event_ref=_ref("irr.event", event),
        ),
        capability_evaluation=evaluation,
        step_ref=applicability.step_ref,
        bound_inputs=(),
        presented_authorizations=(applicability.authorization,),
        description="Exact M3.0.9 Authorization-backed CapabilityAttempt.",
    )


def _admission(
    attempt: CapabilityAttempt,
    applicability: AuthorizationApplicabilityEvaluation,
    policy: AuthorizationUsePolicyEvaluation,
    *,
    event: str,
) -> CapabilityAttemptUseAdmission:
    return CapabilityAttemptUseAdmission(
        attribution=CapabilityAttemptUseAdmissionAttribution(
            admitter_ref=_ref("irr.attempt_use_admitter", "m3-0-9-test"),
            admission_event_ref=_ref("irr.event", event),
            use_context_ref=applicability.attribution.use_context_ref,
            use_context_identity=applicability.attribution.use_context_identity,
        ),
        attempt=attempt,
        applicability_evaluation=applicability,
        use_policy_evaluation=policy,
        description="Exact pre-effect CapabilityAttempt use admission.",
    )


def test_directive_text_is_not_silently_classified_as_exclusive() -> None:
    one_use = _directive("opaque-one-use", semantic_type="one_use")
    _authorization_record, _evaluation, applicability = _applicability(
        label="opaque",
        directives=(one_use,),
    )
    policy = _use_policy(
        applicability,
        label="opaque",
        modes={one_use.directive_ref: AuthorizationConditionUseMode.UNKNOWN},
    )

    assert (
        evaluate_authorization_use_policy(policy)
        is AuthorizationUsePolicyResult.UNRESOLVED
    )
    assert policy.condition_assessments[0].mode is AuthorizationConditionUseMode.UNKNOWN


def test_use_policy_must_exactly_cover_authorization_conditions() -> None:
    first = _directive("first")
    second = _directive("second", semantic_type="scope_at_use")
    authorization, _evaluation, applicability = _applicability(
        label="coverage",
        directives=(first, second),
    )

    with pytest.raises(ValidationError, match="exactly cover Authorization conditions"):
        AuthorizationUsePolicyEvaluation(
            attribution=AuthorizationUsePolicyAttribution(
                evaluator_ref=_ref("irr.authorization_use_policy_evaluator", "test"),
                evaluation_event_ref=_ref("irr.event", "use-policy-coverage"),
                use_context_ref=applicability.attribution.use_context_ref,
                use_context_identity=applicability.attribution.use_context_identity,
            ),
            authorization=authorization,
            step_ref=applicability.step_ref,
            condition_assessments=(
                AuthorizationConditionUseAssessment(
                    directive_ref=first.directive_ref,
                    mode=AuthorizationConditionUseMode.REUSABLE,
                    evidence_refs=(),
                    rationale="Only one condition was classified.",
                ),
            ),
            description="Incomplete classification must fail closed.",
        )


def test_exclusive_claim_is_derived_from_exact_authorization_and_directive() -> None:
    one_use = _directive("exclusive")
    _authorization_record, evaluation, applicability = _applicability(
        label="claim",
        directives=(one_use,),
    )
    policy = _use_policy(
        applicability,
        label="claim",
        modes={one_use.directive_ref: AuthorizationConditionUseMode.EXCLUSIVE_ONCE},
    )
    attempt = _attempt(applicability, evaluation, event="attempt-claim")
    admission = _admission(
        attempt,
        applicability,
        policy,
        event="admission-claim",
    )

    assert len(admission.exclusive_claims) == 1
    claim = admission.exclusive_claims[0]
    assert claim.authorization_identity == applicability.authorization.identity
    assert claim.directive_ref == one_use.directive_ref


def test_unresolved_use_policy_cannot_construct_admission() -> None:
    directive = _directive("unknown")
    _authorization_record, evaluation, applicability = _applicability(
        label="unknown",
        directives=(directive,),
    )
    policy = _use_policy(
        applicability,
        label="unknown",
        modes={directive.directive_ref: AuthorizationConditionUseMode.UNKNOWN},
    )
    attempt = _attempt(applicability, evaluation, event="attempt-unknown")

    with pytest.raises(ValidationError, match="resolved Authorization use policy"):
        _admission(
            attempt,
            applicability,
            policy,
            event="admission-unknown",
        )


def test_reusable_authorization_allows_distinct_attempts() -> None:
    directive = _directive("scope", semantic_type="scope_at_use")
    _authorization_record, evaluation, applicability = _applicability(
        label="reusable",
        directives=(directive,),
    )
    policy = _use_policy(
        applicability,
        label="reusable",
        modes={directive.directive_ref: AuthorizationConditionUseMode.REUSABLE},
    )
    first = _admission(
        _attempt(applicability, evaluation, event="attempt-reusable-first"),
        applicability,
        policy,
        event="admission-reusable-first",
    )
    second = _admission(
        _attempt(applicability, evaluation, event="attempt-reusable-second"),
        applicability,
        policy,
        event="admission-reusable-second",
    )
    repository = InMemoryCapabilityAttemptUseAdmissionRepository()

    assert repository.admit(first) is CapabilityAttemptUseAdmissionResult.ADMITTED
    assert repository.admit(second) is CapabilityAttemptUseAdmissionResult.ADMITTED
    assert first.exclusive_claims == ()
    assert second.exclusive_claims == ()


def test_exclusive_condition_blocks_distinct_competing_attempt() -> None:
    directive = _directive("one-use")
    _authorization_record, evaluation, applicability = _applicability(
        label="exclusive",
        directives=(directive,),
    )
    policy = _use_policy(
        applicability,
        label="exclusive",
        modes={directive.directive_ref: AuthorizationConditionUseMode.EXCLUSIVE_ONCE},
    )
    first = _admission(
        _attempt(applicability, evaluation, event="attempt-exclusive-first"),
        applicability,
        policy,
        event="admission-exclusive-first",
    )
    second = _admission(
        _attempt(applicability, evaluation, event="attempt-exclusive-second"),
        applicability,
        policy,
        event="admission-exclusive-second",
    )
    repository = InMemoryCapabilityAttemptUseAdmissionRepository()

    assert repository.admit(first) is CapabilityAttemptUseAdmissionResult.ADMITTED
    assert (
        repository.admit(second)
        is CapabilityAttemptUseAdmissionResult.EXCLUSIVE_CLAIM_CONFLICT
    )
    assert repository.get(first.attempt.identity) == first
    assert repository.get(second.attempt.identity) is None
    assert (
        repository.claim_owner(first.exclusive_claims[0].identity)
        == first.attempt.identity
    )


def test_same_attempt_replay_is_not_a_second_admission() -> None:
    directive = _directive("replay")
    _authorization_record, evaluation, applicability = _applicability(
        label="replay",
        directives=(directive,),
    )
    policy = _use_policy(
        applicability,
        label="replay",
        modes={directive.directive_ref: AuthorizationConditionUseMode.EXCLUSIVE_ONCE},
    )
    admission = _admission(
        _attempt(applicability, evaluation, event="attempt-replay"),
        applicability,
        policy,
        event="admission-replay",
    )
    repository = InMemoryCapabilityAttemptUseAdmissionRepository()

    assert repository.admit(admission) is CapabilityAttemptUseAdmissionResult.ADMITTED
    assert (
        repository.admit(admission)
        is CapabilityAttemptUseAdmissionResult.ATTEMPT_ALREADY_ADMITTED
    )


def test_authorization_use_policy_cannot_drift_after_first_admitted_use() -> None:
    directive = _directive("policy-drift")
    _authorization_record, evaluation, applicability = _applicability(
        label="policy-drift",
        directives=(directive,),
    )
    reusable_policy = _use_policy(
        applicability,
        label="policy-drift-reusable",
        modes={directive.directive_ref: AuthorizationConditionUseMode.REUSABLE},
    )
    exclusive_policy = _use_policy(
        applicability,
        label="policy-drift-exclusive",
        modes={directive.directive_ref: AuthorizationConditionUseMode.EXCLUSIVE_ONCE},
    )
    first = _admission(
        _attempt(applicability, evaluation, event="attempt-policy-drift-first"),
        applicability,
        reusable_policy,
        event="admission-policy-drift-first",
    )
    second = _admission(
        _attempt(applicability, evaluation, event="attempt-policy-drift-second"),
        applicability,
        exclusive_policy,
        event="admission-policy-drift-second",
    )
    repository = InMemoryCapabilityAttemptUseAdmissionRepository()

    assert repository.admit(first) is CapabilityAttemptUseAdmissionResult.ADMITTED
    assert (
        repository.admit(second)
        is CapabilityAttemptUseAdmissionResult.AUTHORIZATION_POLICY_CONFLICT
    )
    assert repository.get(second.attempt.identity) is None
    assert (
        repository.authorization_policy_identity(applicability.authorization.identity)
        == reusable_policy.policy_identity
    )


def test_same_directive_ref_in_different_authorization_does_not_alias_claim() -> None:
    directive = _directive("shared-ref")
    _auth_a, evaluation_a, applicability_a = _applicability(
        label="auth-a",
        directives=(directive,),
    )
    _auth_b, evaluation_b, applicability_b = _applicability(
        label="auth-b",
        directives=(directive,),
    )
    assert (
        applicability_a.authorization.identity != applicability_b.authorization.identity
    )

    policy_a = _use_policy(
        applicability_a,
        label="auth-a",
        modes={directive.directive_ref: AuthorizationConditionUseMode.EXCLUSIVE_ONCE},
    )
    policy_b = _use_policy(
        applicability_b,
        label="auth-b",
        modes={directive.directive_ref: AuthorizationConditionUseMode.EXCLUSIVE_ONCE},
    )
    first = _admission(
        _attempt(applicability_a, evaluation_a, event="attempt-auth-a"),
        applicability_a,
        policy_a,
        event="admission-auth-a",
    )
    second = _admission(
        _attempt(applicability_b, evaluation_b, event="attempt-auth-b"),
        applicability_b,
        policy_b,
        event="admission-auth-b",
    )
    repository = InMemoryCapabilityAttemptUseAdmissionRepository()

    assert repository.admit(first) is CapabilityAttemptUseAdmissionResult.ADMITTED
    assert repository.admit(second) is CapabilityAttemptUseAdmissionResult.ADMITTED
    assert first.exclusive_claims[0].identity != second.exclusive_claims[0].identity


def test_concurrent_competing_attempts_admit_exactly_one_exclusive_use() -> None:
    directive = _directive("race")
    _authorization_record, evaluation, applicability = _applicability(
        label="race",
        directives=(directive,),
    )
    policy = _use_policy(
        applicability,
        label="race",
        modes={directive.directive_ref: AuthorizationConditionUseMode.EXCLUSIVE_ONCE},
    )
    first = _admission(
        _attempt(applicability, evaluation, event="attempt-race-first"),
        applicability,
        policy,
        event="admission-race-first",
    )
    second = _admission(
        _attempt(applicability, evaluation, event="attempt-race-second"),
        applicability,
        policy,
        event="admission-race-second",
    )
    repository = InMemoryCapabilityAttemptUseAdmissionRepository()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(repository.admit, (first, second)))

    assert results.count(CapabilityAttemptUseAdmissionResult.ADMITTED) == 1
    assert (
        results.count(CapabilityAttemptUseAdmissionResult.EXCLUSIVE_CLAIM_CONFLICT) == 1
    )


def test_roundtrip_preserves_derived_claims_and_exact_admission_identity() -> None:
    directive = _directive("roundtrip")
    _authorization_record, evaluation, applicability = _applicability(
        label="roundtrip-use",
        directives=(directive,),
    )
    policy = _use_policy(
        applicability,
        label="roundtrip-use",
        modes={directive.directive_ref: AuthorizationConditionUseMode.EXCLUSIVE_ONCE},
    )
    original = _admission(
        _attempt(applicability, evaluation, event="attempt-roundtrip-use"),
        applicability,
        policy,
        event="admission-roundtrip-use",
    )

    restored = CapabilityAttemptUseAdmission.from_json_bytes(original.canonical_bytes())

    assert restored == original
    assert restored.identity == original.identity
    assert restored.exclusive_claims == original.exclusive_claims
