from __future__ import annotations

from dataclasses import replace

import pytest

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityIncompatibleDescriptorAssessment,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityMatchIssue,
    CapabilityMatchIssueKind,
    CapabilityMismatchKind,
    CapabilityMismatchReason,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    RecordIdentity,
    SerializationError,
    StableRef,
    ValidationError,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
    evaluate_capability_match_evaluation,
)


RESOLVED = RecordIdentity("sha256", "2" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _requirement() -> CapabilityRequirement:
    plan_ref = _ref("irr.work_plan", "inspect-001")
    step_ref = _ref("irr.work_step", "inspect")
    completion = "Return the bounded workspace inspection result."
    step = WorkStep(
        resolved_intent_identity=RESOLVED,
        work_plan_ref=plan_ref,
        step_ref=step_ref,
        operation="workspace.inspect",
        scope="workspace:project",
        inputs=(),
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract=completion,
        description="Inspect one bounded workspace.",
    )
    plan = WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="Complete the bounded inspection plan.",
        description="One-step inspection plan.",
    )
    scope = CapabilityRequestedScope(
        scope_ref=_ref("irr.capability_requested_scope", "workspace"),
        semantic_type="filesystem.path_scope",
        value="workspace:project",
        description="Bounded workspace scope.",
    )
    return CapabilityRequirement(
        work_plan=plan,
        step_ref=step_ref,
        primary_scope_ref=scope.scope_ref,
        requested_scopes=(scope,),
        requested_effects=(),
        execution_boundary_requirements=(),
        description="Exact inspection capability requirement.",
    )


def _descriptor(name: str) -> CapabilityDescriptor:
    scope = CapabilityScopeRequirement(
        requirement_ref=_ref("irr.capability_scope_requirement", f"workspace-{name}"),
        semantic_type="filesystem.path_scope",
        statement="Invocation must remain inside one bounded workspace.",
    )
    return CapabilityDescriptor(
        capability_ref=_ref("irr.capability", name),
        operation="workspace.inspect",
        input_contracts=(),
        output_contracts=(),
        scope_requirements=(scope,),
        effects=(),
        execution_boundaries=(),
        completion_contract="Return the bounded workspace inspection result.",
        description=f"Bounded workspace inspection capability {name}.",
    )


def _snapshot(*descriptors: CapabilityDescriptor) -> CapabilityCatalogSnapshot:
    return CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", "evaluation-test"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=_ref("irr.host", "test-host"),
            snapshot_event_ref=_ref("irr.event", "catalog-evaluation-001"),
        ),
        scope_statement="Exact bounded test planning surface.",
        descriptors=tuple(descriptors),
        description="Capability evaluation test snapshot.",
    )


def _match(
    requirement: CapabilityRequirement,
    snapshot: CapabilityCatalogSnapshot,
    descriptor: CapabilityDescriptor,
    event: str,
) -> CapabilityMatch:
    requested_scope = requirement.requested_scopes[0]
    descriptor_scope = descriptor.scope_requirements[0]
    return CapabilityMatch(
        attribution=CapabilityMatchAttribution(
            matcher_ref=_ref("irr.matcher", "exact-v1"),
            match_event_ref=_ref("irr.event", event),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        scope_matches=(
            CapabilityScopeMatch(
                requested_scope_ref=requested_scope.scope_ref,
                descriptor_scope_requirement_ref=descriptor_scope.requirement_ref,
            ),
        ),
        input_matches=(),
        output_matches=(),
        effect_matches=(),
        description=f"Exact match for {descriptor.capability_ref.value}.",
    )


def _evaluation(
    *,
    matches: tuple[CapabilityMatch, ...],
    incompatible: tuple[CapabilityIncompatibleDescriptorAssessment, ...],
    requirement: CapabilityRequirement,
    snapshot: CapabilityCatalogSnapshot,
) -> CapabilityMatchEvaluation:
    return CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            evaluator_ref=_ref("irr.evaluator", "capability-evaluation-v1"),
            evaluation_event_ref=_ref("irr.event", "evaluation-001"),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        compatible_matches=matches,
        incompatible_assessments=incompatible,
        description="Exhaustive assessment of the exact supplied Catalog Snapshot.",
    )


def test_single_match_round_trip_and_classification_returns_exact_match() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(descriptor)
    match = _match(requirement, snapshot, descriptor, "match-local")
    evaluation = _evaluation(
        matches=(match,),
        incompatible=(),
        requirement=requirement,
        snapshot=snapshot,
    )

    decoded = CapabilityMatchEvaluation.from_json_bytes(evaluation.canonical_bytes())
    assert decoded == evaluation
    assert decoded.identity == evaluation.identity
    assert evaluate_capability_match_evaluation(evaluation) == match


def test_empty_catalog_classifies_as_bounded_no_match_not_global_impossibility() -> None:
    requirement = _requirement()
    snapshot = _snapshot()
    evaluation = _evaluation(
        matches=(),
        incompatible=(),
        requirement=requirement,
        snapshot=snapshot,
    )
    result = evaluate_capability_match_evaluation(evaluation)

    assert type(result) is CapabilityMatchIssue
    assert result.kind is CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY
    assert result.evaluation.catalog_snapshot == snapshot


def test_incompatible_assessment_pins_exact_descriptor_and_covers_catalog() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.remote")
    snapshot = _snapshot(descriptor)
    reason = CapabilityMismatchReason(
        kind=CapabilityMismatchKind.INSUFFICIENT_SEMANTICS,
        scope="descriptor:workspace.inspect.remote",
        description="The supplied descriptor semantics are insufficient for admission.",
    )
    assessment = CapabilityIncompatibleDescriptorAssessment(
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        reasons=(reason,),
    )
    evaluation = _evaluation(
        matches=(),
        incompatible=(assessment,),
        requirement=requirement,
        snapshot=snapshot,
    )

    assert evaluate_capability_match_evaluation(evaluation).kind is (
        CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY
    )
    wrong = replace(
        assessment,
        capability_contract_identity=RecordIdentity("sha256", "f" * 64),
    )
    with pytest.raises(ValidationError):
        _evaluation(
            matches=(),
            incompatible=(wrong,),
            requirement=requirement,
            snapshot=snapshot,
        )


def test_evaluation_must_cover_every_exact_catalog_descriptor_once() -> None:
    requirement = _requirement()
    first = _descriptor("workspace.inspect.a")
    second = _descriptor("workspace.inspect.b")
    snapshot = _snapshot(first, second)
    first_match = _match(requirement, snapshot, first, "match-a")

    with pytest.raises(ValidationError):
        _evaluation(
            matches=(first_match,),
            incompatible=(),
            requirement=requirement,
            snapshot=snapshot,
        )

    reason = CapabilityMismatchReason(
        CapabilityMismatchKind.MAPPING_AMBIGUITY,
        "descriptor:workspace.inspect.b",
        "No single mapping was admitted for this descriptor.",
    )
    second_assessment = CapabilityIncompatibleDescriptorAssessment(
        second.capability_ref,
        second.identity,
        (reason,),
    )
    evaluation = _evaluation(
        matches=(first_match,),
        incompatible=(second_assessment,),
        requirement=requirement,
        snapshot=snapshot,
    )
    assert evaluate_capability_match_evaluation(evaluation) == first_match

    with pytest.raises(ValidationError):
        _evaluation(
            matches=(first_match,),
            incompatible=(
                CapabilityIncompatibleDescriptorAssessment(
                    first.capability_ref,
                    first.identity,
                    (reason,),
                ),
                second_assessment,
            ),
            requirement=requirement,
            snapshot=snapshot,
        )


def test_multiple_matches_never_choose_by_catalog_or_tuple_order() -> None:
    requirement = _requirement()
    first = _descriptor("workspace.inspect.a")
    second = _descriptor("workspace.inspect.b")
    snapshot = _snapshot(second, first)
    first_match = _match(requirement, snapshot, first, "match-a")
    second_match = _match(requirement, snapshot, second, "match-b")

    evaluation = _evaluation(
        matches=(second_match, first_match),
        incompatible=(),
        requirement=requirement,
        snapshot=snapshot,
    )
    reordered = replace(
        evaluation,
        compatible_matches=tuple(reversed(evaluation.compatible_matches)),
    )
    result = evaluate_capability_match_evaluation(evaluation)

    assert evaluation.identity == reordered.identity
    assert type(result) is CapabilityMatchIssue
    assert result.kind is CapabilityMatchIssueKind.MULTIPLE_COMPATIBLE_MATCHES
    assert len(result.evaluation.compatible_matches) == 2


def test_duplicate_semantic_match_occurrences_do_not_create_fake_ambiguity() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(descriptor)
    first = _match(requirement, snapshot, descriptor, "match-occurrence-a")
    second = _match(requirement, snapshot, descriptor, "match-occurrence-b")

    with pytest.raises(ValidationError):
        _evaluation(
            matches=(first, second),
            incompatible=(),
            requirement=requirement,
            snapshot=snapshot,
        )


def test_match_must_use_exact_evaluation_requirement_and_catalog() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(descriptor)
    match = _match(requirement, snapshot, descriptor, "match-local")

    changed_requirement = replace(requirement, description="Another exact requirement.")
    with pytest.raises(ValidationError):
        _evaluation(
            matches=(match,),
            incompatible=(),
            requirement=changed_requirement,
            snapshot=snapshot,
        )

    changed_snapshot = replace(
        snapshot,
        attribution=replace(
            snapshot.attribution,
            snapshot_event_ref=_ref("irr.event", "catalog-evaluation-002"),
        ),
    )
    with pytest.raises(ValidationError):
        _evaluation(
            matches=(match,),
            incompatible=(),
            requirement=requirement,
            snapshot=changed_snapshot,
        )


def test_issue_kind_is_cardinality_closed_and_has_no_authority_fields() -> None:
    requirement = _requirement()
    snapshot = _snapshot()
    evaluation = _evaluation(
        matches=(),
        incompatible=(),
        requirement=requirement,
        snapshot=snapshot,
    )
    issue = CapabilityMatchIssue(
        evaluation=evaluation,
        kind=CapabilityMatchIssueKind.NO_COMPATIBLE_CAPABILITY,
    )

    with pytest.raises(ValidationError):
        CapabilityMatchIssue(
            evaluation=evaluation,
            kind=CapabilityMatchIssueKind.MULTIPLE_COMPATIBLE_MATCHES,
        )

    primitive = issue.to_primitive()
    primitive["authorized"] = "true"
    with pytest.raises(SerializationError):
        CapabilityMatchIssue.from_primitive(primitive)


def test_mismatch_reason_and_assessment_round_trip_and_order_are_canonical() -> None:
    descriptor = _descriptor("workspace.inspect.remote")
    first = CapabilityMismatchReason(
        CapabilityMismatchKind.SCOPE_MISMATCH,
        "scope:workspace",
        "Requested scope could not be admitted against the descriptor scope contract.",
    )
    second = CapabilityMismatchReason(
        CapabilityMismatchKind.EXECUTION_BOUNDARY_MISMATCH,
        "boundary:provider",
        "Required provider boundary was not represented.",
    )
    assessment = CapabilityIncompatibleDescriptorAssessment(
        descriptor.capability_ref,
        descriptor.identity,
        (first, second),
    )
    reordered = replace(assessment, reasons=(second, first))

    assert assessment.identity == reordered.identity
    decoded = CapabilityIncompatibleDescriptorAssessment.from_json_bytes(
        assessment.canonical_bytes()
    )
    assert decoded == assessment
    assert decoded.identity == assessment.identity


def test_public_records_are_closed() -> None:
    with pytest.raises(TypeError):
        class _BadEvaluation(CapabilityMatchEvaluation):
            pass

    with pytest.raises(TypeError):
        class _BadIssue(CapabilityMatchIssue):
            pass
