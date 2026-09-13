from __future__ import annotations

from dataclasses import replace
from inspect import signature

import pytest

from intent_resolution_runtime import (
    AdmittedCapabilityCatalogSnapshot,
    AdmittedCapabilityRequirement,
    CandidateCapabilityCatalogSnapshot,
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityCatalogSnapshotAdmissionAttribution,
    CapabilityCatalogSnapshotProposalAttribution,
    CapabilityDescriptor,
    CapabilityMatch,
    CapabilityRequirement,
    CapabilityRequirementAdmissionAttribution,
    CapabilityRequestedScope,
    CapabilityScopeRequirement,
    MechanicallyDerivedCapabilityMatchEvaluation,
    RecordIdentity,
    StableRef,
    ValidationError,
    WorkContinuationMode,
    WorkPlan,
    WorkStep,
    derive_mechanical_capability_match_evaluation,
    evaluate_capability_match_evaluation,
)
from intent_resolution_runtime.capability_match_engine import (
    mechanical_capability_evaluator_ref,
)

RESOLVED = RecordIdentity("sha256", "9" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace=namespace, value=value)


def _plan(label: str = "primary") -> WorkPlan:
    plan_ref = _ref("irr.work_plan", f"m3.0.7:{label}")
    step = WorkStep(
        resolved_intent_identity=RESOLVED,
        work_plan_ref=plan_ref,
        step_ref=_ref("irr.work_step", f"inspect:{label}"),
        operation="workspace.inspect",
        scope="workspace:project",
        inputs=(),
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract="Return the bounded workspace inspection result.",
        description=f"Inspect one bounded workspace for {label}.",
    )
    return WorkPlan(
        resolved_intent_identity=RESOLVED,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="Complete the bounded inspection plan.",
        description=f"M3.0.7 bounded inspection plan {label}.",
    )


def _requirement(label: str = "primary") -> CapabilityRequirement:
    plan = _plan(label)
    requested_scope = CapabilityRequestedScope(
        scope_ref=_ref("irr.capability_requested_scope", f"workspace:{label}"),
        semantic_type="filesystem.path_scope",
        value="workspace:project",
        description="Exact bounded workspace scope.",
    )
    return CapabilityRequirement(
        work_plan=plan,
        step_ref=plan.steps[0].step_ref,
        primary_scope_ref=requested_scope.scope_ref,
        requested_scopes=(requested_scope,),
        requested_effects=(),
        execution_boundary_requirements=(),
        description=f"Exact bounded inspection requirement {label}.",
    )


def _admitted_requirement(label: str = "primary") -> AdmittedCapabilityRequirement:
    return AdmittedCapabilityRequirement(
        admission_attribution=CapabilityRequirementAdmissionAttribution(
            resolver_ref=_ref("irr.capability_requirement_resolver", "test"),
            admission_event_ref=_ref(
                "irr.capability_requirement_admission", f"m3.0.7:{label}"
            ),
        ),
        requirement=_requirement(label),
    )


def _descriptor(label: str = "local") -> CapabilityDescriptor:
    return CapabilityDescriptor(
        capability_ref=_ref("irr.capability", f"workspace.inspect:{label}"),
        operation="workspace.inspect",
        input_contracts=(),
        output_contracts=(),
        scope_requirements=(
            CapabilityScopeRequirement(
                requirement_ref=_ref(
                    "irr.capability_scope_requirement", f"workspace:{label}"
                ),
                semantic_type="filesystem.path_scope",
                statement="Invocation must remain inside one bounded workspace.",
            ),
        ),
        effects=(),
        execution_boundaries=(),
        completion_contract="Return the bounded workspace inspection result.",
        description=f"Exact local workspace inspection capability {label}.",
    )


def _snapshot(label: str = "primary") -> CapabilityCatalogSnapshot:
    return CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", f"m3.0.7:{label}"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=_ref("irr.capability_catalog_supplier", "test-host"),
            snapshot_event_ref=_ref(
                "irr.capability_catalog_snapshot", f"m3.0.7:{label}"
            ),
        ),
        scope_statement="Exact bounded capability surface for M3.0.7.",
        descriptors=(_descriptor(label),),
        description=f"Exact M3.0.7 capability catalog {label}.",
    )


def _admitted_catalog(
    label: str = "primary",
) -> AdmittedCapabilityCatalogSnapshot:
    snapshot = _snapshot(label)
    candidate = CandidateCapabilityCatalogSnapshot(
        attribution=CapabilityCatalogSnapshotProposalAttribution(
            proposer_ref=_ref("irr.catalog_proposer", "test-host"),
            proposal_event_ref=_ref("irr.catalog_proposal", f"m3.0.7:{label}"),
        ),
        snapshot=snapshot,
        rationale="Use this exact bounded capability domain.",
    )
    return AdmittedCapabilityCatalogSnapshot(
        admission_attribution=CapabilityCatalogSnapshotAdmissionAttribution(
            resolver_ref=_ref("irr.catalog_resolver", "test"),
            admission_event_ref=_ref("irr.catalog_admission", f"m3.0.7:{label}"),
        ),
        snapshot=snapshot,
        candidate_inputs=(candidate,),
    )


def _derive(
    *,
    requirement_label: str = "primary",
    catalog_label: str = "primary",
    event: str = "evaluation:1",
) -> MechanicallyDerivedCapabilityMatchEvaluation:
    return derive_mechanical_capability_match_evaluation(
        _admitted_requirement(requirement_label),
        _admitted_catalog(catalog_label),
        evaluation_event_ref=_ref("irr.capability_evaluation", event),
    )


def test_exact_admitted_inputs_produce_one_mechanically_bound_evaluation() -> None:
    output = _derive()

    assert output.evaluation.requirement == output.admitted_requirement.requirement
    assert output.evaluation.catalog_snapshot == output.admitted_catalog.snapshot
    assert (
        output.evaluation.attribution.evaluator_ref
        == mechanical_capability_evaluator_ref()
    )

    result = evaluate_capability_match_evaluation(output.evaluation)
    assert result.__class__ is CapabilityMatch
    assert result == output.evaluation.compatible_matches[0]


def test_boundary_has_no_semantic_admitter_or_candidate_evaluation_input() -> None:
    parameters = signature(derive_mechanical_capability_match_evaluation).parameters

    assert tuple(parameters) == (
        "admitted_requirement",
        "admitted_catalog",
        "evaluation_event_ref",
    )
    assert "admitter" not in parameters
    assert "candidate_inputs" not in parameters
    assert "provider" not in parameters


def test_raw_unadmitted_requirement_is_rejected() -> None:
    with pytest.raises(ValidationError, match="admitted_requirement"):
        derive_mechanical_capability_match_evaluation(  # type: ignore[arg-type]
            _requirement(),
            _admitted_catalog(),
            evaluation_event_ref=_ref("irr.capability_evaluation", "raw-requirement"),
        )


def test_raw_unadmitted_catalog_is_rejected() -> None:
    with pytest.raises(ValidationError, match="admitted_catalog"):
        derive_mechanical_capability_match_evaluation(  # type: ignore[arg-type]
            _admitted_requirement(),
            _snapshot(),
            evaluation_event_ref=_ref("irr.capability_evaluation", "raw-catalog"),
        )


def test_valid_but_tampered_evaluation_fails_mechanical_rederivation() -> None:
    output = _derive()
    tampered = replace(
        output.evaluation,
        description="A valid record shape with non-canonical evaluator-authored semantics.",
    )

    with pytest.raises(ValidationError, match="exactly equal the deterministic IRR"):
        MechanicallyDerivedCapabilityMatchEvaluation(
            admitted_requirement=output.admitted_requirement,
            admitted_catalog=output.admitted_catalog,
            evaluation=tampered,
        )


def test_foreign_admitted_requirement_cannot_be_attached_to_evaluation() -> None:
    output = _derive()

    with pytest.raises(ValidationError, match="exact admitted CapabilityRequirement"):
        MechanicallyDerivedCapabilityMatchEvaluation(
            admitted_requirement=_admitted_requirement("foreign"),
            admitted_catalog=output.admitted_catalog,
            evaluation=output.evaluation,
        )


def test_foreign_admitted_catalog_cannot_be_attached_to_evaluation() -> None:
    output = _derive()

    with pytest.raises(
        ValidationError, match="exact admitted CapabilityCatalogSnapshot"
    ):
        MechanicallyDerivedCapabilityMatchEvaluation(
            admitted_requirement=output.admitted_requirement,
            admitted_catalog=_admitted_catalog("foreign"),
            evaluation=output.evaluation,
        )


def test_same_exact_inputs_and_event_replay_to_same_identity() -> None:
    first = _derive(event="stable")
    second = _derive(event="stable")

    assert second == first
    assert second.identity == first.identity
    assert second.canonical_bytes() == first.canonical_bytes()


def test_distinct_admission_provenance_remains_distinct_with_same_evaluation() -> None:
    requirement = _requirement()
    first_admission = AdmittedCapabilityRequirement(
        admission_attribution=CapabilityRequirementAdmissionAttribution(
            resolver_ref=_ref("irr.capability_requirement_resolver", "test"),
            admission_event_ref=_ref("irr.capability_requirement_admission", "first"),
        ),
        requirement=requirement,
    )
    second_admission = AdmittedCapabilityRequirement(
        admission_attribution=CapabilityRequirementAdmissionAttribution(
            resolver_ref=_ref("irr.capability_requirement_resolver", "test"),
            admission_event_ref=_ref("irr.capability_requirement_admission", "second"),
        ),
        requirement=requirement,
    )
    catalog = _admitted_catalog()
    event_ref = _ref("irr.capability_evaluation", "same-semantics")

    first = derive_mechanical_capability_match_evaluation(
        first_admission,
        catalog,
        evaluation_event_ref=event_ref,
    )
    second = derive_mechanical_capability_match_evaluation(
        second_admission,
        catalog,
        evaluation_event_ref=event_ref,
    )

    assert second.evaluation == first.evaluation
    assert second.identity != first.identity
    assert second.canonical_bytes() != first.canonical_bytes()


def test_round_trip_revalidates_mechanical_derivation() -> None:
    output = _derive(event="round-trip")

    restored = MechanicallyDerivedCapabilityMatchEvaluation.from_json_bytes(
        output.canonical_bytes()
    )

    assert restored == output
    assert restored.identity == output.identity


def test_wrapper_adds_no_selection_governance_or_execution_authority() -> None:
    output = _derive()

    for forbidden in (
        "selected_capability",
        "available",
        "work_proposal",
        "governance",
        "authorization",
        "attempt",
        "executor",
        "permission",
        "approved",
    ):
        assert not hasattr(output, forbidden)
