from __future__ import annotations

from dataclasses import replace

import pytest

from intent_resolution_runtime.capability import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityScopeRequirement,
)
from intent_resolution_runtime.capability_match import (
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
)
from intent_resolution_runtime.capability_match_evaluation import (
    CapabilityIncompatibleDescriptorAssessment,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityMismatchKind,
    CapabilityMismatchReason,
)
from intent_resolution_runtime.capability_match_evaluation_admission import (
    AdmittedCapabilityMatchEvaluation,
    CandidateCapabilityMatchEvaluation,
    CapabilityMatchEvaluationAdmissionAttribution,
    CapabilityMatchEvaluationAdmissionFrontier,
    CapabilityMatchEvaluationAdmissionFrontierKind,
    orchestrate_capability_match_evaluation_admission,
)
from intent_resolution_runtime.errors import SerializationError, ValidationError
from intent_resolution_runtime.identity import RecordIdentity
from intent_resolution_runtime.intent import StableRef
from intent_resolution_runtime.work import (
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
)


RESOLVED = RecordIdentity("sha256", "2" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _requirement(*, label: str = "main") -> CapabilityRequirement:
    plan_ref = _ref("irr.work_plan", f"inspect-{label}")
    step_ref = _ref("irr.work_step", f"inspect-{label}")
    completion = "Return the bounded workspace inspection result."
    step = WorkStep(
        resolved_intent_identity=RESOLVED,
        work_plan_ref=plan_ref,
        step_ref=step_ref,
        operation="workspace.inspect",
        scope=f"workspace:{label}",
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
        scope_ref=_ref("irr.capability_requested_scope", f"workspace-{label}"),
        semantic_type="filesystem.path_scope",
        value=f"workspace:{label}",
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
        requirement_ref=_ref("irr.capability_scope_requirement", f"scope-{name}"),
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


def _snapshot(
    requirement: CapabilityRequirement,
    *descriptors: CapabilityDescriptor,
    label: str = "main",
) -> CapabilityCatalogSnapshot:
    return CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", f"catalog-{label}"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=_ref("irr.catalog_supplier", f"supplier-{label}"),
            snapshot_event_ref=_ref("irr.catalog_snapshot_event", f"event-{label}"),
        ),
        scope_statement=(
            f"Explicit catalog snapshot for {requirement.work_step.scope}."
        ),
        descriptors=tuple(descriptors),
        description="Exact capability catalog snapshot for admission tests.",
    )


def _match(
    requirement: CapabilityRequirement,
    snapshot: CapabilityCatalogSnapshot,
    descriptor: CapabilityDescriptor,
    *,
    label: str,
) -> CapabilityMatch:
    requested_scope = requirement.requested_scopes[0]
    descriptor_scope = descriptor.scope_requirements[0]
    return CapabilityMatch(
        attribution=CapabilityMatchAttribution(
            matcher_ref=_ref("irr.matcher", f"matcher-{label}"),
            match_event_ref=_ref("irr.match_event", f"match-{label}"),
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
        description=f"Exact compatible relation from matcher {label}.",
    )


def _compatible_evaluation(
    requirement: CapabilityRequirement,
    snapshot: CapabilityCatalogSnapshot,
    descriptor: CapabilityDescriptor,
    *,
    label: str,
) -> CapabilityMatchEvaluation:
    return CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            evaluator_ref=_ref("irr.evaluator", f"evaluator-{label}"),
            evaluation_event_ref=_ref(
                "irr.capability_evaluation_event",
                f"evaluation-{label}",
            ),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        compatible_matches=(
            _match(requirement, snapshot, descriptor, label=label),
        ),
        incompatible_assessments=(),
        description=f"Compatible exhaustive evaluation from {label}.",
    )


def _incompatible_evaluation(
    requirement: CapabilityRequirement,
    snapshot: CapabilityCatalogSnapshot,
    descriptor: CapabilityDescriptor,
    *,
    label: str,
) -> CapabilityMatchEvaluation:
    reason = CapabilityMismatchReason(
        kind=CapabilityMismatchKind.INSUFFICIENT_SEMANTICS,
        scope=f"descriptor:{descriptor.capability_ref.value}",
        description=(
            "The evaluator reports insufficient semantics for compatibility."
        ),
    )
    assessment = CapabilityIncompatibleDescriptorAssessment(
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        reasons=(reason,),
    )
    return CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            evaluator_ref=_ref("irr.evaluator", f"evaluator-{label}"),
            evaluation_event_ref=_ref(
                "irr.capability_evaluation_event",
                f"evaluation-{label}",
            ),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        compatible_matches=(),
        incompatible_assessments=(assessment,),
        description=f"Incompatible exhaustive evaluation from {label}.",
    )


def _candidate(
    evaluation: CapabilityMatchEvaluation,
    *,
    label: str,
) -> CandidateCapabilityMatchEvaluation:
    return CandidateCapabilityMatchEvaluation(
        evaluation=evaluation,
        rationale=f"Explicit evaluator evidence {label} for admission.",
    )


def _admission_attribution(
    label: str = "main",
) -> CapabilityMatchEvaluationAdmissionAttribution:
    return CapabilityMatchEvaluationAdmissionAttribution(
        resolver_ref=_ref("irr.capability_evaluation_resolver", f"resolver-{label}"),
        admission_event_ref=_ref(
            "irr.capability_evaluation_admission",
            f"admission-{label}",
        ),
    )


def test_zero_candidates_require_explicit_proposal_input() -> None:
    requirement = _requirement()
    snapshot = _snapshot(requirement)

    frontier = orchestrate_capability_match_evaluation_admission(
        requirement,
        snapshot,
    )

    assert frontier.kind is (
        CapabilityMatchEvaluationAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
    )
    assert frontier.candidate_inputs == ()
    assert frontier.admitted_evaluation is None


def test_same_semantics_from_distinct_evaluators_do_not_vote() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(requirement, descriptor)
    first = _candidate(
        _compatible_evaluation(requirement, snapshot, descriptor, label="first"),
        label="first",
    )
    second = _candidate(
        _compatible_evaluation(requirement, snapshot, descriptor, label="second"),
        label="second",
    )
    assert first.identity != second.identity

    frontier = orchestrate_capability_match_evaluation_admission(
        requirement,
        snapshot,
        candidate_inputs=(second, first),
    )

    assert frontier.kind is (
        CapabilityMatchEvaluationAdmissionFrontierKind.ADMISSION_REQUIRED
    )
    assert set(frontier.candidate_inputs) == {first, second}
    assert frontier.admitted_evaluation is None


def test_disagreeing_evaluation_semantics_require_adjudication() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(requirement, descriptor)
    compatible = _candidate(
        _compatible_evaluation(requirement, snapshot, descriptor, label="yes"),
        label="yes",
    )
    incompatible = _candidate(
        _incompatible_evaluation(requirement, snapshot, descriptor, label="no"),
        label="no",
    )

    frontier = orchestrate_capability_match_evaluation_admission(
        requirement,
        snapshot,
        candidate_inputs=(compatible, incompatible),
    )

    assert frontier.kind is (
        CapabilityMatchEvaluationAdmissionFrontierKind.ADJUDICATION_REQUIRED
    )
    assert frontier.admitted_evaluation is None


def test_explicit_admitter_can_adjudicate_but_must_preserve_provenance() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(requirement, descriptor)
    compatible = _candidate(
        _compatible_evaluation(requirement, snapshot, descriptor, label="yes"),
        label="yes",
    )
    incompatible = _candidate(
        _incompatible_evaluation(requirement, snapshot, descriptor, label="no"),
        label="no",
    )
    attribution = _admission_attribution()

    def admitter(requirement_, snapshot_, candidates, attribution_):
        assert requirement_ == requirement
        assert snapshot_ == snapshot
        chosen = next(
            candidate.evaluation
            for candidate in candidates
            if candidate.evaluation.compatible_matches
        )
        return AdmittedCapabilityMatchEvaluation(
            admission_attribution=attribution_,
            evaluation=chosen,
            candidate_inputs=candidates,
        )

    frontier = orchestrate_capability_match_evaluation_admission(
        requirement,
        snapshot,
        candidate_inputs=(incompatible, compatible),
        admitter=admitter,
        admission_attribution=attribution,
    )

    assert frontier.kind is (
        CapabilityMatchEvaluationAdmissionFrontierKind.EVALUATION_OUTPUT_AVAILABLE
    )
    assert frontier.admitted_evaluation is not None
    assert frontier.admitted_evaluation.evaluation.compatible_matches
    assert frontier.admitted_evaluation.candidate_inputs == frontier.candidate_inputs
    assert frontier.admitted_evaluation.admission_attribution == attribution


def test_explicit_admitter_may_synthesize_with_zero_provider_candidates() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(requirement, descriptor)
    attribution = _admission_attribution("synthesized")
    synthesized = _compatible_evaluation(
        requirement,
        snapshot,
        descriptor,
        label="resolver",
    )

    def admitter(requirement_, snapshot_, candidates, attribution_):
        assert candidates == ()
        return AdmittedCapabilityMatchEvaluation(
            admission_attribution=attribution_,
            evaluation=synthesized,
            candidate_inputs=(),
        )

    frontier = orchestrate_capability_match_evaluation_admission(
        requirement,
        snapshot,
        admitter=admitter,
        admission_attribution=attribution,
    )

    assert frontier.kind is (
        CapabilityMatchEvaluationAdmissionFrontierKind.EVALUATION_OUTPUT_AVAILABLE
    )
    assert frontier.admitted_evaluation is not None
    assert frontier.admitted_evaluation.evaluation == synthesized


def test_replay_restores_complete_admitted_candidate_provenance() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(requirement, descriptor)
    first = _candidate(
        _compatible_evaluation(requirement, snapshot, descriptor, label="first"),
        label="first",
    )
    second = _candidate(
        _compatible_evaluation(requirement, snapshot, descriptor, label="second"),
        label="second",
    )
    attribution = _admission_attribution("replay")

    def admitter(_requirement, _snapshot, candidates, attribution_):
        return AdmittedCapabilityMatchEvaluation(
            admission_attribution=attribution_,
            evaluation=candidates[0].evaluation,
            candidate_inputs=candidates,
        )

    admitted = orchestrate_capability_match_evaluation_admission(
        requirement,
        snapshot,
        candidate_inputs=(first, second),
        admitter=admitter,
        admission_attribution=attribution,
    )
    output = admitted.admitted_evaluation
    assert output is not None

    replayed = orchestrate_capability_match_evaluation_admission(
        requirement,
        snapshot,
        candidate_inputs=(first,),
        admitted_outputs=(output,),
    )

    assert replayed == admitted
    assert replayed.candidate_inputs == output.candidate_inputs


def test_replay_rejects_orphan_candidate_and_new_admission() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(requirement, descriptor)
    candidate = _candidate(
        _compatible_evaluation(requirement, snapshot, descriptor, label="base"),
        label="base",
    )
    attribution = _admission_attribution("base")
    output = AdmittedCapabilityMatchEvaluation(
        admission_attribution=attribution,
        evaluation=candidate.evaluation,
        candidate_inputs=(candidate,),
    )
    orphan = _candidate(
        _compatible_evaluation(requirement, snapshot, descriptor, label="orphan"),
        label="orphan",
    )

    with pytest.raises(ValidationError, match="outside admitted evaluation provenance"):
        orchestrate_capability_match_evaluation_admission(
            requirement,
            snapshot,
            candidate_inputs=(orphan,),
            admitted_outputs=(output,),
        )

    with pytest.raises(ValidationError, match="cannot also invoke a new admitter"):
        orchestrate_capability_match_evaluation_admission(
            requirement,
            snapshot,
            admitted_outputs=(output,),
            admitter=lambda *_args: output,
            admission_attribution=attribution,
        )


def test_foreign_requirement_and_catalog_candidate_material_fail_closed() -> None:
    requirement = _requirement(label="main")
    foreign_requirement = _requirement(label="foreign")
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(requirement, descriptor, label="main")
    foreign_snapshot = _snapshot(
        foreign_requirement,
        descriptor,
        label="foreign",
    )
    foreign_requirement_candidate = _candidate(
        _compatible_evaluation(
            foreign_requirement,
            foreign_snapshot,
            descriptor,
            label="foreign-requirement",
        ),
        label="foreign-requirement",
    )

    with pytest.raises(ValidationError, match="foreign CapabilityRequirement"):
        orchestrate_capability_match_evaluation_admission(
            requirement,
            foreign_snapshot,
            candidate_inputs=(foreign_requirement_candidate,),
        )

    foreign_catalog_candidate = _candidate(
        _compatible_evaluation(
            requirement,
            snapshot,
            descriptor,
            label="main-catalog",
        ),
        label="main-catalog",
    )
    with pytest.raises(ValidationError, match="foreign CapabilityCatalogSnapshot"):
        orchestrate_capability_match_evaluation_admission(
            requirement,
            foreign_snapshot,
            candidate_inputs=(foreign_catalog_candidate,),
        )


def test_frontier_constructor_cannot_mislabel_unresolved_semantics() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(requirement, descriptor)
    one = _candidate(
        _compatible_evaluation(requirement, snapshot, descriptor, label="one"),
        label="one",
    )

    with pytest.raises(ValidationError, match="must match exact candidate semantics"):
        CapabilityMatchEvaluationAdmissionFrontier(
            requirement=requirement,
            catalog_snapshot=snapshot,
            candidate_inputs=(one,),
            kind=CapabilityMatchEvaluationAdmissionFrontierKind.ADJUDICATION_REQUIRED,
        )

    other = _candidate(
        _incompatible_evaluation(requirement, snapshot, descriptor, label="other"),
        label="other",
    )
    with pytest.raises(ValidationError, match="must match exact candidate semantics"):
        CapabilityMatchEvaluationAdmissionFrontier(
            requirement=requirement,
            catalog_snapshot=snapshot,
            candidate_inputs=(one, other),
            kind=CapabilityMatchEvaluationAdmissionFrontierKind.ADMISSION_REQUIRED,
        )


def test_admitted_evaluation_round_trip_has_no_authority_fields() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(requirement, descriptor)
    candidate = _candidate(
        _compatible_evaluation(requirement, snapshot, descriptor, label="round-trip"),
        label="round-trip",
    )
    admitted = AdmittedCapabilityMatchEvaluation(
        admission_attribution=_admission_attribution("round-trip"),
        evaluation=candidate.evaluation,
        candidate_inputs=(candidate,),
    )

    decoded = AdmittedCapabilityMatchEvaluation.from_json_bytes(
        admitted.canonical_bytes()
    )
    assert decoded == admitted
    assert decoded.identity == admitted.identity

    primitive = admitted.to_primitive()
    primitive["authorized"] = True
    with pytest.raises(SerializationError):
        AdmittedCapabilityMatchEvaluation.from_primitive(primitive)


def test_candidate_occurrence_metadata_does_not_change_semantic_frontier_kind() -> None:
    requirement = _requirement()
    descriptor = _descriptor("workspace.inspect.local")
    snapshot = _snapshot(requirement, descriptor)
    base = _compatible_evaluation(
        requirement,
        snapshot,
        descriptor,
        label="base",
    )
    changed = replace(
        base,
        attribution=CapabilityMatchEvaluationAttribution(
            evaluator_ref=_ref("irr.evaluator", "another-evaluator"),
            evaluation_event_ref=_ref(
                "irr.capability_evaluation_event",
                "another-event",
            ),
        ),
        description="Same semantic assessment from another occurrence.",
        compatible_matches=(
            replace(
                base.compatible_matches[0],
                attribution=CapabilityMatchAttribution(
                    matcher_ref=_ref("irr.matcher", "another-matcher"),
                    match_event_ref=_ref("irr.match_event", "another-match-event"),
                ),
                description="Same exact semantic relation from another occurrence.",
            ),
        ),
    )
    first = _candidate(base, label="base")
    second = _candidate(changed, label="changed")

    frontier = orchestrate_capability_match_evaluation_admission(
        requirement,
        snapshot,
        candidate_inputs=(first, second),
    )

    assert first.identity != second.identity
    assert frontier.kind is (
        CapabilityMatchEvaluationAdmissionFrontierKind.ADMISSION_REQUIRED
    )
