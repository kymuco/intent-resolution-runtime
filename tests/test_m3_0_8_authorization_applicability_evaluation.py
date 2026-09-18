from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    Authorization,
    AuthorizationApplicabilityAttribution,
    AuthorizationApplicabilityEvaluation,
    AuthorizationApplicabilityResult,
    AuthorizationConditionAssessment,
    AuthorizationConditionDisposition,
    GovernanceDecision,
    GovernanceDecisionComponent,
    GovernanceDecisionKind,
    GovernanceDirective,
    RecordIdentity,
    StableRef,
    ValidationError,
    evaluate_authorization_applicability,
    orchestrate_capability_governance,
)
from tests.test_m2_3_capability_governance_orchestrator import (
    _governance_attr,
    _plan,
    _proposal,
    _ref,
    _unique_evaluation,
)


def _authorization(
    *,
    label: str,
    directives: tuple[GovernanceDirective, ...] = (),
) -> tuple[Authorization, object]:
    plan = _plan("inspect", label=f"plan-{label}")
    requirement, evaluation = _unique_evaluation(plan, "inspect", event=label)
    proposal = _proposal(plan, (evaluation,), event=f"proposal-{label}")
    component = GovernanceDecisionComponent(
        component_ref=_ref("irr.governance_component", f"authorize-{label}"),
        kind=GovernanceDecisionKind.AUTHORIZE,
        step_refs=(requirement.step_ref,),
        directives=directives,
        rationale=f"Authorize exact step for {label}.",
    )
    decision = GovernanceDecision(
        attribution=_governance_attr(f"decision-{label}"),
        proposal=proposal,
        components=(component,),
        description=f"Governance decision for {label}.",
    )
    authorization = Authorization(decision, component.component_ref)
    frontier = orchestrate_capability_governance(
        plan,
        capability_requirements=(requirement,),
        capability_evaluations=(evaluation,),
        work_proposals=(proposal,),
        governance_decisions=(decision,),
        authorizations=(authorization,),
    )
    assert frontier.authorizations == (authorization,)
    return authorization, evaluation


def _directive(label: str, *, semantic_type: str = "one_use") -> GovernanceDirective:
    return GovernanceDirective(
        directive_ref=_ref("irr.governance_directive", label),
        semantic_type=semantic_type,
        scope=f"exact-use:{label}",
        statement=f"Condition {label} must be evaluated against exact use context.",
    )


def _attribution(label: str, *, context_digest: str = "a" * 64):
    return AuthorizationApplicabilityAttribution(
        evaluator_ref=_ref("irr.authorization_applicability_evaluator", "test"),
        evaluation_event_ref=_ref("irr.event", f"applicability-{label}"),
        use_context_ref=_ref("irr.authorization_use_context", label),
        use_context_identity=RecordIdentity("sha256", context_digest),
    )


def _assessment(
    directive: GovernanceDirective,
    disposition: AuthorizationConditionDisposition,
    *,
    evidence: str,
) -> AuthorizationConditionAssessment:
    return AuthorizationConditionAssessment(
        directive_ref=directive.directive_ref,
        disposition=disposition,
        evidence_refs=(_ref("irr.evidence", evidence),),
        rationale=f"Exact assessment for {directive.directive_ref.value}.",
    )


def test_unconditional_authorization_is_mechanically_applicable() -> None:
    authorization, _evaluation = _authorization(label="unconditional")

    applicability = AuthorizationApplicabilityEvaluation(
        attribution=_attribution("unconditional"),
        authorization=authorization,
        step_ref=authorization.authorized_step_refs[0],
        condition_assessments=(),
        description="No Governance conditions require assessment.",
    )

    assert (
        evaluate_authorization_applicability(applicability)
        is AuthorizationApplicabilityResult.APPLICABLE
    )


def test_all_conditions_satisfied_is_applicable() -> None:
    first = _directive("one-use")
    second = _directive("scope", semantic_type="scope_at_use")
    authorization, _evaluation = _authorization(
        label="all-satisfied",
        directives=(first, second),
    )

    applicability = AuthorizationApplicabilityEvaluation(
        attribution=_attribution("all-satisfied"),
        authorization=authorization,
        step_ref=authorization.authorized_step_refs[0],
        condition_assessments=(
            _assessment(
                second,
                AuthorizationConditionDisposition.SATISFIED,
                evidence="scope-current",
            ),
            _assessment(
                first,
                AuthorizationConditionDisposition.SATISFIED,
                evidence="unused",
            ),
        ),
        description="All exact conditions were assessed satisfied.",
    )

    assert tuple(
        item.directive_ref for item in applicability.condition_assessments
    ) == tuple(sorted((first.directive_ref, second.directive_ref), key=lambda item: (item.namespace, item.value)))
    assert (
        evaluate_authorization_applicability(applicability)
        is AuthorizationApplicabilityResult.APPLICABLE
    )


def test_unsatisfied_condition_dominates_unknown() -> None:
    expiry = _directive("expiry", semantic_type="expiry")
    scope = _directive("scope", semantic_type="scope_at_use")
    authorization, _evaluation = _authorization(
        label="not-applicable",
        directives=(expiry, scope),
    )

    applicability = AuthorizationApplicabilityEvaluation(
        attribution=_attribution("not-applicable"),
        authorization=authorization,
        step_ref=authorization.authorized_step_refs[0],
        condition_assessments=(
            _assessment(
                expiry,
                AuthorizationConditionDisposition.UNSATISFIED,
                evidence="expired",
            ),
            _assessment(
                scope,
                AuthorizationConditionDisposition.UNKNOWN,
                evidence="scope-unknown",
            ),
        ),
        description="One exact condition failed and another remained unresolved.",
    )

    assert (
        evaluate_authorization_applicability(applicability)
        is AuthorizationApplicabilityResult.NOT_APPLICABLE
    )


def test_unknown_condition_is_unresolved_not_implicitly_applicable() -> None:
    one_use = _directive("one-use")
    authorization, _evaluation = _authorization(
        label="unknown-one-use",
        directives=(one_use,),
    )

    applicability = AuthorizationApplicabilityEvaluation(
        attribution=_attribution("unknown-one-use"),
        authorization=authorization,
        step_ref=authorization.authorized_step_refs[0],
        condition_assessments=(
            _assessment(
                one_use,
                AuthorizationConditionDisposition.UNKNOWN,
                evidence="consumption-history-missing",
            ),
        ),
        description="One-use state is not established by exact current evidence.",
    )

    assert (
        evaluate_authorization_applicability(applicability)
        is AuthorizationApplicabilityResult.UNRESOLVED
    )


def test_directive_semantic_type_is_not_silently_interpreted() -> None:
    one_use = _directive("opaque-one-use", semantic_type="one_use")
    authorization, _evaluation = _authorization(
        label="opaque-semantics",
        directives=(one_use,),
    )

    unresolved = AuthorizationApplicabilityEvaluation(
        attribution=_attribution("opaque-semantics"),
        authorization=authorization,
        step_ref=authorization.authorized_step_refs[0],
        condition_assessments=(
            _assessment(
                one_use,
                AuthorizationConditionDisposition.UNKNOWN,
                evidence="opaque-policy",
            ),
        ),
        description="IRR preserves evaluator evidence instead of parsing directive text.",
    )

    assert (
        evaluate_authorization_applicability(unresolved)
        is AuthorizationApplicabilityResult.UNRESOLVED
    )


def test_assessments_must_exactly_cover_authorization_conditions() -> None:
    first = _directive("first")
    second = _directive("second")
    authorization, _evaluation = _authorization(
        label="exact-coverage",
        directives=(first, second),
    )

    with pytest.raises(ValidationError, match="exactly cover Authorization conditions"):
        AuthorizationApplicabilityEvaluation(
            attribution=_attribution("exact-coverage"),
            authorization=authorization,
            step_ref=authorization.authorized_step_refs[0],
            condition_assessments=(
                _assessment(
                    first,
                    AuthorizationConditionDisposition.SATISFIED,
                    evidence="first-only",
                ),
            ),
            description="Incomplete assessments must fail closed.",
        )


def test_duplicate_condition_assessment_fails_closed() -> None:
    directive = _directive("duplicate")
    authorization, _evaluation = _authorization(
        label="duplicate",
        directives=(directive,),
    )
    assessment = _assessment(
        directive,
        AuthorizationConditionDisposition.SATISFIED,
        evidence="duplicate",
    )

    with pytest.raises(ValidationError, match="duplicate directive_ref"):
        AuthorizationApplicabilityEvaluation(
            attribution=_attribution("duplicate"),
            authorization=authorization,
            step_ref=authorization.authorized_step_refs[0],
            condition_assessments=(assessment, assessment),
            description="Duplicate assessments must fail closed.",
        )


def test_evaluation_must_target_exact_authorized_step() -> None:
    authorization, _evaluation = _authorization(label="foreign-step")

    with pytest.raises(ValidationError, match="covered by the exact Authorization"):
        AuthorizationApplicabilityEvaluation(
            attribution=_attribution("foreign-step"),
            authorization=authorization,
            step_ref=StableRef("irr.work_step", "other"),
            condition_assessments=(),
            description="Foreign step must fail closed.",
        )


def test_use_context_identity_is_part_of_evaluation_identity() -> None:
    authorization, _evaluation = _authorization(label="context-binding")

    first = AuthorizationApplicabilityEvaluation(
        attribution=_attribution("context-binding", context_digest="a" * 64),
        authorization=authorization,
        step_ref=authorization.authorized_step_refs[0],
        condition_assessments=(),
        description="Exact use context A.",
    )
    second = AuthorizationApplicabilityEvaluation(
        attribution=_attribution("context-binding", context_digest="b" * 64),
        authorization=authorization,
        step_ref=authorization.authorized_step_refs[0],
        condition_assessments=(),
        description="Exact use context A.",
    )

    assert first.identity != second.identity


def test_roundtrip_preserves_exact_applicability_evidence() -> None:
    directive = _directive("roundtrip", semantic_type="expiry")
    authorization, _evaluation = _authorization(
        label="roundtrip",
        directives=(directive,),
    )
    original = AuthorizationApplicabilityEvaluation(
        attribution=_attribution("roundtrip"),
        authorization=authorization,
        step_ref=authorization.authorized_step_refs[0],
        condition_assessments=(
            _assessment(
                directive,
                AuthorizationConditionDisposition.SATISFIED,
                evidence="time-evidence",
            ),
        ),
        description="Exact replayable applicability evidence.",
    )

    restored = AuthorizationApplicabilityEvaluation.from_json_bytes(
        original.canonical_bytes()
    )

    assert restored == original
    assert restored.identity == original.identity
