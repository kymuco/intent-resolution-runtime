from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityIncompatibleDescriptorAssessment,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityMatchIssue,
    CapabilityMatchIssueKind,
    CapabilityMismatchKind,
    CapabilityMismatchReason,
    CapabilityRequestedEffect,
    CapabilityRequestedScope,
    CapabilityRequirement,
    ProposedWorkStep,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    StableRef,
    ValidationError,
    WorkContinuationMode,
    WorkLiteralInput,
    WorkPlan,
    WorkStep,
    evaluate_capability_match_evaluation,
)


REQUEST_IDENTITY = RecordIdentity("sha256", "1" * 64)
CONTEXT_IDENTITY = RecordIdentity("sha256", "2" * 64)
FILE_PATH = r"W:\reports\report.pdf"
RECIPIENT = "signal:alice"


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> tuple[WorkStep, CapabilityMatchEvaluation, CapabilityMatchIssue]:
    resolved = ResolvedIntent(
        REQUEST_IDENTITY,
        CONTEXT_IDENTITY,
        ResolutionAttribution(
            _ref("irr.resolver", "scenario-f"),
            _ref("irr.resolution_event", "scenario-f-resolved"),
        ),
        "Send the exact resolved file to the exact resolved Signal recipient.",
        (),
        (),
        (),
    )
    plan_ref = _ref("irr.work_plan", "scenario-f-signal-send")
    step_ref = _ref("irr.work_step", "send-signal-file")
    step = WorkStep(
        resolved.identity,
        plan_ref,
        step_ref,
        "signal.send_file",
        RECIPIENT,
        (
            WorkLiteralInput("artifact", "artifact.path", FILE_PATH),
            WorkLiteralInput("recipient", "messaging.destination", RECIPIENT),
        ),
        (),
        (),
        WorkContinuationMode.NONE,
        "Return attributable evidence under the exact Signal send completion contract.",
        "Send only the exact resolved file to the exact resolved Signal recipient.",
    )
    plan = WorkPlan(
        resolved.identity,
        plan_ref,
        (step,),
        "The exact Signal send step reaches its represented completion contract.",
        "Scenario F exact Signal-send semantic work.",
    )

    artifact_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "signal-artifact"),
        "artifact.path_scope",
        FILE_PATH,
        "Exact file that would be read/disclosed.",
    )
    recipient_scope = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "signal-recipient"),
        "messaging.destination_scope",
        RECIPIENT,
        "Exact resolved Signal destination.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        recipient_scope.scope_ref,
        (artifact_scope, recipient_scope),
        (
            CapabilityRequestedEffect(
                _ref("irr.capability_requested_effect", "signal-network"),
                "network.use",
                (recipient_scope.scope_ref,),
                "Signal send requires network use toward the exact destination.",
            ),
            CapabilityRequestedEffect(
                _ref("irr.capability_requested_effect", "signal-disclosure"),
                "external.disclosure",
                (artifact_scope.scope_ref, recipient_scope.scope_ref),
                "The exact file may be disclosed to the exact Signal recipient.",
            ),
        ),
        (),
        "Exact Signal send capability requirement.",
    )

    # A materially different channel exists in the exact Catalog, but it is not a Signal capability.
    telegram = CapabilityDescriptor(
        _ref("irr.capability", "telegram.send_file"),
        "telegram.send_file",
        (),
        (),
        (),
        (),
        (),
        "Return attributable Telegram send completion material.",
        "Telegram file-send capability; not semantically substitutable for Signal.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "scenario-f"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "scenario-f-host"),
            _ref("irr.event", "scenario-f-catalog"),
        ),
        "Applicable Catalog intentionally contains Telegram but no Signal send capability.",
        (telegram,),
        "Scenario F missing-Signal Catalog snapshot.",
    )
    incompatible = CapabilityIncompatibleDescriptorAssessment(
        telegram.capability_ref,
        telegram.identity,
        (
            CapabilityMismatchReason(
                CapabilityMismatchKind.OPERATION_MISMATCH,
                "semantic operation",
                "telegram.send_file does not satisfy the exact signal.send_file operation.",
            ),
        ),
    )
    evaluation = CapabilityMatchEvaluation(
        CapabilityMatchEvaluationAttribution(
            _ref("irr.evaluator", "scenario-f"),
            _ref("irr.event", "scenario-f-evaluation"),
        ),
        requirement,
        snapshot,
        (),
        (incompatible,),
        "Exhaustive exact Catalog evaluation with no compatible Signal capability.",
    )
    issue = evaluate_capability_match_evaluation(evaluation)
    assert isinstance(issue, CapabilityMatchIssue)
    return step, evaluation, issue


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


def test_scenario_f_missing_signal_capability_is_bounded_no_match_not_fallback() -> None:
    step, evaluation, issue = _fixture()

    assert step.operation == "signal.send_file"
    assert issue.kind is CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY
    assert evaluation.compatible_matches == ()
    assert len(evaluation.incompatible_assessments) == 1
    assessment = evaluation.incompatible_assessments[0]
    assert assessment.capability_ref == _ref("irr.capability", "telegram.send_file")
    assert assessment.reasons[0].kind is CapabilityMismatchKind.OPERATION_MISMATCH


def test_scenario_f_missing_capability_cannot_enter_governance_or_attempt_path() -> None:
    step, evaluation, issue = _fixture()

    with pytest.raises(ValidationError, match="exactly one admitted CapabilityMatch"):
        ProposedWorkStep(step.step_ref, evaluation)

    keys = _all_keys(issue.to_primitive())
    for forbidden in (
        "authorization",
        "authorized",
        "attempt",
        "fallback",
        "telegram_selected",
        "browser",
        "shell",
    ):
        assert forbidden not in keys


def test_scenario_f_other_channel_presence_does_not_mean_global_impossibility_or_precedence() -> None:
    _, evaluation, issue = _fixture()

    assert issue.kind is CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY
    assert "Telegram" in evaluation.catalog_snapshot.scope_statement
    assert evaluation.catalog_snapshot.descriptors[0].operation == "telegram.send_file"
    assert evaluation.requirement.work_step.operation == "signal.send_file"
    assert evaluation.catalog_snapshot.descriptors[0].operation != evaluation.requirement.work_step.operation


def test_scenario_f_issue_round_trip_preserves_exact_missing_capability_provenance() -> None:
    _, _, issue = _fixture()

    decoded = CapabilityMatchIssue.from_json_bytes(issue.canonical_bytes())
    assert decoded == issue
    assert decoded.identity == issue.identity
    assert decoded.kind is CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY
