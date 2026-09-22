from __future__ import annotations

import inspect
from dataclasses import replace

import pytest

import intent_resolution_runtime.recovery_key_lineage as recovery_module
from intent_resolution_runtime import (
    CapabilityIdempotencyKey,
    DeduplicatedRecoveryInvocationRequest,
    OriginalDeduplicatedDispatchBinding,
    OriginalDeduplicatedDispatchBindingAttribution,
    RecordIdentity,
    RecoveryKeyLineage,
    RecoveryKeyLineageAttribution,
    RecoveryKeyLineageError,
    ValidationError,
    build_capability_invocation_request,
    build_deduplicated_capability_invocation_request,
    build_deduplicated_recovery_invocation_request,
    build_original_deduplicated_dispatch_binding,
    build_recovery_key_lineage,
)
from tests.test_m3_0_10_persistent_deduplicated_reinvocation_contract import (
    _admitted,
    _exact_attempt,
    _ref,
)
from tests.test_m3_4_executor_capability_invocation_port import (
    _attempt as _m34_attempt,
)
from tests.test_m3_4_executor_capability_invocation_port import (
    _executor_boundary,
)


def _fresh_recovery_attempt(original, *, event: str = "recovery-attempt"):
    return replace(
        original,
        attribution=replace(
            original.attribution,
            attempt_event_ref=_ref("irr.event", event),
        ),
        description="A new recovery Attempt for the exact same concrete use.",
    )


def _description_only_recovery(original):
    requirement = original.capability_evaluation.requirement
    plan = requirement.work_plan
    step = requirement.work_step

    changed_step = replace(
        step,
        description="Narrative-only recovery WorkStep description.",
    )
    changed_plan = replace(
        plan,
        steps=(changed_step,),
        description="Narrative-only recovery WorkPlan description.",
    )
    changed_scopes = tuple(
        replace(item, description="Narrative-only scope description.")
        for item in requirement.requested_scopes
    )
    changed_effects = tuple(
        replace(item, description="Narrative-only effect description.")
        for item in requirement.requested_effects
    )
    changed_boundaries = tuple(
        replace(item, description="Narrative-only boundary description.")
        for item in requirement.execution_boundary_requirements
    )
    changed_requirement = replace(
        requirement,
        work_plan=changed_plan,
        requested_scopes=changed_scopes,
        requested_effects=changed_effects,
        execution_boundary_requirements=changed_boundaries,
        description="Narrative-only requirement description.",
    )

    original_match = original.capability_match
    changed_match = replace(
        original_match,
        requirement=changed_requirement,
        description="Narrative-only capability match description.",
    )
    changed_evaluation = replace(
        original.capability_evaluation,
        attribution=replace(
            original.capability_evaluation.attribution,
            evaluation_event_ref=_ref(
                "irr.event",
                "recovery-description-evaluation",
            ),
        ),
        requirement=changed_requirement,
        compatible_matches=(changed_match,),
        description="Narrative-only evaluation description.",
    )
    return replace(
        original,
        attribution=replace(
            original.attribution,
            attempt_event_ref=_ref(
                "irr.event",
                "recovery-description-attempt",
            ),
        ),
        capability_evaluation=changed_evaluation,
        description="Narrative-only recovery Attempt description.",
    )


def _scope_drift_recovery(original):
    requirement = original.capability_evaluation.requirement
    plan = requirement.work_plan
    step = requirement.work_step
    changed_scope_value = "workspace:artifact/other-report.txt"

    changed_step = replace(step, scope=changed_scope_value)
    changed_plan = replace(plan, steps=(changed_step,))
    changed_scopes = tuple(
        replace(item, value=changed_scope_value)
        if item.scope_ref == requirement.primary_scope_ref
        else item
        for item in requirement.requested_scopes
    )
    changed_requirement = replace(
        requirement,
        work_plan=changed_plan,
        requested_scopes=changed_scopes,
    )
    original_match = original.capability_match
    changed_match = replace(
        original_match,
        requirement=changed_requirement,
    )
    changed_evaluation = replace(
        original.capability_evaluation,
        attribution=replace(
            original.capability_evaluation.attribution,
            evaluation_event_ref=_ref(
                "irr.event",
                "recovery-scope-evaluation",
            ),
        ),
        requirement=changed_requirement,
        compatible_matches=(changed_match,),
    )
    return replace(
        original,
        attribution=replace(
            original.attribution,
            attempt_event_ref=_ref("irr.event", "recovery-scope-attempt"),
        ),
        capability_evaluation=changed_evaluation,
    )


def _binding(original, *, label: str):
    admitted = _admitted(original, label=f"{label}-contract")
    request = build_deduplicated_capability_invocation_request(
        admitted,
        original,
    )
    attribution = OriginalDeduplicatedDispatchBindingAttribution(
        binder_ref=_ref("irr.dispatch_binder", "test-host"),
        binding_event_ref=_ref("irr.event", f"binding-{label}"),
    )
    binding = build_original_deduplicated_dispatch_binding(
        attribution,
        request,
    )
    return admitted, request, binding


def _lineage(original, recovery, *, label: str):
    _admitted_contract, _request, binding = _binding(original, label=label)
    attribution = RecoveryKeyLineageAttribution(
        linker_ref=_ref("irr.recovery_key_linker", "test-host"),
        lineage_event_ref=_ref("irr.event", f"lineage-{label}"),
    )
    lineage = build_recovery_key_lineage(
        attribution,
        binding,
        recovery,
    )
    return binding, lineage


def test_original_binding_requires_exact_m3_0_10_first_dispatch_request() -> None:
    original = _exact_attempt()
    ordinary_request = build_capability_invocation_request(original)
    attribution = OriginalDeduplicatedDispatchBindingAttribution(
        binder_ref=_ref("irr.dispatch_binder", "test-host"),
        binding_event_ref=_ref("irr.event", "binding-ordinary-request"),
    )

    with pytest.raises(
        ValidationError,
        match="DeduplicatedCapabilityInvocationRequest",
    ):
        build_original_deduplicated_dispatch_binding(
            attribution,
            ordinary_request,  # type: ignore[arg-type]
        )


def test_original_binding_canonicalizes_exact_first_dispatch_material() -> None:
    original = _exact_attempt()
    admitted, request, binding = _binding(original, label="exact-binding")

    assert binding.__class__ is OriginalDeduplicatedDispatchBinding
    assert binding.original_attempt == original
    assert binding.admitted_contract == admitted
    assert binding.idempotency_key == request.idempotency_key

    restored = OriginalDeduplicatedDispatchBinding.from_json_bytes(
        binding.canonical_bytes()
    )
    assert restored == binding
    assert restored.identity == binding.identity


@pytest.mark.parametrize(
    "event_source",
    ("attempt", "admission", "contract", "proposal"),
)
def test_original_binding_occurrence_cannot_alias_protected_lineage(
    event_source: str,
) -> None:
    original = _exact_attempt()
    admitted = _admitted(original, label=f"binding-alias-{event_source}")
    request = build_deduplicated_capability_invocation_request(
        admitted,
        original,
    )
    events = {
        "attempt": original.attribution.attempt_event_ref,
        "admission": admitted.admission_attribution.admission_event_ref,
        "contract": admitted.contract.attribution.contract_event_ref,
        "proposal": admitted.candidate_inputs[0].attribution.proposal_event_ref,
    }

    with pytest.raises(
        ValidationError,
        match="binding occurrence must differ",
    ):
        build_original_deduplicated_dispatch_binding(
            OriginalDeduplicatedDispatchBindingAttribution(
                binder_ref=_ref("irr.dispatch_binder", "test-host"),
                binding_event_ref=events[event_source],
            ),
            request,
        )


def test_recovery_lineage_inherits_exact_original_key_for_new_attempt() -> None:
    original = _exact_attempt()
    recovery = _fresh_recovery_attempt(original)
    binding, lineage = _lineage(original, recovery, label="inherit")

    assert lineage.__class__ is RecoveryKeyLineage
    assert lineage.recovery_attempt == recovery
    assert recovery.identity != original.identity
    assert lineage.inherited_idempotency_key == binding.idempotency_key
    assert (
        lineage.inherited_idempotency_key.external_token
        == binding.idempotency_key.external_token
    )
    assert lineage.inherited_idempotency_key.original_attempt_identity == original.identity


def test_same_exact_attempt_cannot_be_used_as_recovery_attempt() -> None:
    original = _exact_attempt()
    _admitted_contract, _request, binding = _binding(
        original,
        label="same-attempt",
    )

    with pytest.raises(
        RecoveryKeyLineageError,
        match="new CapabilityAttempt identity",
    ):
        build_recovery_key_lineage(
            RecoveryKeyLineageAttribution(
                linker_ref=_ref("irr.recovery_key_linker", "test-host"),
                lineage_event_ref=_ref("irr.event", "lineage-same-attempt"),
            ),
            binding,
            original,
        )


def test_recovery_attempt_must_have_new_attempt_occurrence() -> None:
    original = _exact_attempt()
    recovery = replace(
        original,
        description="Different identity but deliberately reused occurrence.",
    )
    assert recovery.identity != original.identity
    assert recovery.attribution.attempt_event_ref == original.attribution.attempt_event_ref

    _admitted_contract, _request, binding = _binding(
        original,
        label="same-occurrence",
    )
    with pytest.raises(
        RecoveryKeyLineageError,
        match="distinct attempt occurrence",
    ):
        build_recovery_key_lineage(
            RecoveryKeyLineageAttribution(
                linker_ref=_ref("irr.recovery_key_linker", "test-host"),
                lineage_event_ref=_ref("irr.event", "lineage-same-occurrence"),
            ),
            binding,
            recovery,
        )


def test_description_only_drift_does_not_change_concrete_use() -> None:
    original = _exact_attempt()
    recovery = _description_only_recovery(original)

    binding, lineage = _lineage(
        original,
        recovery,
        label="description-only",
    )

    assert recovery.capability_evaluation.requirement != (
        original.capability_evaluation.requirement
    )
    assert lineage.original_dispatch_binding == binding
    assert lineage.recovery_attempt == recovery
    assert lineage.inherited_idempotency_key == binding.idempotency_key


def test_target_scope_drift_cannot_inherit_original_key() -> None:
    original = _exact_attempt()
    recovery = _scope_drift_recovery(original)
    _admitted_contract, _request, binding = _binding(
        original,
        label="scope-drift",
    )

    with pytest.raises(
        RecoveryKeyLineageError,
        match="semantic CapabilityRequirement",
    ):
        build_recovery_key_lineage(
            RecoveryKeyLineageAttribution(
                linker_ref=_ref("irr.recovery_key_linker", "test-host"),
                lineage_event_ref=_ref("irr.event", "lineage-scope-drift"),
            ),
            binding,
            recovery,
        )


def test_executor_drift_cannot_inherit_original_key() -> None:
    original = _exact_attempt()
    recovery = _fresh_recovery_attempt(original, event="recovery-executor-drift")
    recovery = replace(
        recovery,
        attribution=replace(
            recovery.attribution,
            executor_ref=_ref("irr.executor", "foreign-executor"),
        ),
    )
    _admitted_contract, _request, binding = _binding(
        original,
        label="executor-drift",
    )

    with pytest.raises(
        RecoveryKeyLineageError,
        match="exact executor_ref",
    ):
        build_recovery_key_lineage(
            RecoveryKeyLineageAttribution(
                linker_ref=_ref("irr.recovery_key_linker", "test-host"),
                lineage_event_ref=_ref("irr.event", "lineage-executor-drift"),
            ),
            binding,
            recovery,
        )


def test_capability_contract_drift_cannot_inherit_original_key() -> None:
    original = _exact_attempt()
    recovery = _m34_attempt(
        event="recovery-contract-drift",
        executor="artifact-executor-v2",
        executor_boundaries=(_executor_boundary("artifact-executor-v2"),),
    )
    assert (
        recovery.capability_evaluation.requirement
        == original.capability_evaluation.requirement
    )
    assert recovery.capability_match.capability_ref == (
        original.capability_match.capability_ref
    )
    assert recovery.capability_match.capability_contract_identity != (
        original.capability_match.capability_contract_identity
    )

    _admitted_contract, _request, binding = _binding(
        original,
        label="contract-drift",
    )
    with pytest.raises(
        RecoveryKeyLineageError,
        match="capability contract identity",
    ):
        build_recovery_key_lineage(
            RecoveryKeyLineageAttribution(
                linker_ref=_ref("irr.recovery_key_linker", "test-host"),
                lineage_event_ref=_ref("irr.event", "lineage-contract-drift"),
            ),
            binding,
            recovery,
        )


def test_forged_inherited_key_is_rejected() -> None:
    original = _exact_attempt()
    recovery = _fresh_recovery_attempt(original, event="recovery-forged-key")
    _admitted_contract, _request, binding = _binding(
        original,
        label="forged-key",
    )
    forged = CapabilityIdempotencyKey(
        admitted_contract_identity=binding.idempotency_key.admitted_contract_identity,
        original_attempt_identity=RecordIdentity("sha256", "d" * 64),
        deduplication_domain_ref=binding.idempotency_key.deduplication_domain_ref,
    )

    with pytest.raises(
        RecoveryKeyLineageError,
        match="inherit the exact original idempotency key",
    ):
        RecoveryKeyLineage(
            attribution=RecoveryKeyLineageAttribution(
                linker_ref=_ref("irr.recovery_key_linker", "test-host"),
                lineage_event_ref=_ref("irr.event", "lineage-forged-key"),
            ),
            original_dispatch_binding=binding,
            recovery_attempt=recovery,
            inherited_idempotency_key=forged,
        )


@pytest.mark.parametrize(
    "alias",
    (
        "binding",
        "original",
        "recovery",
        "admission",
        "contract",
        "proposal",
    ),
)
def test_recovery_lineage_occurrence_cannot_alias_related_occurrences(
    alias: str,
) -> None:
    original = _exact_attempt()
    recovery = _fresh_recovery_attempt(original, event="recovery-alias")
    _admitted_contract, _request, binding = _binding(
        original,
        label=f"lineage-alias-{alias}",
    )
    admitted = binding.admitted_contract
    events = {
        "binding": binding.attribution.binding_event_ref,
        "original": original.attribution.attempt_event_ref,
        "recovery": recovery.attribution.attempt_event_ref,
        "admission": admitted.admission_attribution.admission_event_ref,
        "contract": admitted.contract.attribution.contract_event_ref,
        "proposal": admitted.candidate_inputs[0].attribution.proposal_event_ref,
    }

    with pytest.raises(
        ValidationError,
        match="lineage occurrence must differ",
    ):
        build_recovery_key_lineage(
            RecoveryKeyLineageAttribution(
                linker_ref=_ref("irr.recovery_key_linker", "test-host"),
                lineage_event_ref=events[alias],
            ),
            binding,
            recovery,
        )


def test_recovery_lineage_roundtrip_preserves_exact_identity() -> None:
    original = _exact_attempt()
    recovery = _fresh_recovery_attempt(original, event="recovery-roundtrip")
    _binding_record, lineage = _lineage(
        original,
        recovery,
        label="roundtrip",
    )

    restored = RecoveryKeyLineage.from_json_bytes(lineage.canonical_bytes())

    assert restored == lineage
    assert restored.identity == lineage.identity
    assert (
        restored.inherited_idempotency_key.external_token
        == lineage.inherited_idempotency_key.external_token
    )


def test_recovery_invocation_request_carries_exact_lineage_attempt_and_key() -> None:
    original = _exact_attempt()
    recovery = _fresh_recovery_attempt(original, event="recovery-request")
    _binding_record, lineage = _lineage(
        original,
        recovery,
        label="recovery-request",
    )

    request = build_deduplicated_recovery_invocation_request(lineage)

    assert request.__class__ is DeduplicatedRecoveryInvocationRequest
    assert request.recovery_attempt == recovery
    assert request.recovery_key_lineage == lineage
    assert request.idempotency_key == lineage.inherited_idempotency_key
    assert not hasattr(request, "SCHEMA")
    assert not hasattr(request, "identity")
    assert not hasattr(request, "canonical_bytes")


def test_recovery_invocation_request_rejects_foreign_attempt_and_key() -> None:
    original = _exact_attempt()
    recovery = _fresh_recovery_attempt(original, event="recovery-request-base")
    _binding_record, lineage = _lineage(
        original,
        recovery,
        label="request-foreign",
    )
    foreign_attempt = _fresh_recovery_attempt(
        original,
        event="recovery-request-foreign",
    )
    forged_key = CapabilityIdempotencyKey(
        admitted_contract_identity=(
            lineage.inherited_idempotency_key.admitted_contract_identity
        ),
        original_attempt_identity=RecordIdentity("sha256", "e" * 64),
        deduplication_domain_ref=(
            lineage.inherited_idempotency_key.deduplication_domain_ref
        ),
    )

    with pytest.raises(
        RecoveryKeyLineageError,
        match="exact lineage recovery Attempt",
    ):
        DeduplicatedRecoveryInvocationRequest(
            recovery_attempt=foreign_attempt,
            recovery_key_lineage=lineage,
            idempotency_key=lineage.inherited_idempotency_key,
        )

    with pytest.raises(
        RecoveryKeyLineageError,
        match="exact inherited original key",
    ):
        DeduplicatedRecoveryInvocationRequest(
            recovery_attempt=recovery,
            recovery_key_lineage=lineage,
            idempotency_key=forged_key,
        )


def test_public_surface_has_no_ambiguity_retry_or_executor_authority() -> None:
    binding_parameters = inspect.signature(
        build_original_deduplicated_dispatch_binding
    ).parameters
    lineage_parameters = inspect.signature(build_recovery_key_lineage).parameters
    request_parameters = inspect.signature(
        build_deduplicated_recovery_invocation_request
    ).parameters

    assert set(binding_parameters) == {"attribution", "request"}
    assert set(lineage_parameters) == {
        "attribution",
        "original_dispatch_binding",
        "recovery_attempt",
    }
    assert set(request_parameters) == {"lineage"}

    for parameters in (
        binding_parameters,
        lineage_parameters,
        request_parameters,
    ):
        for forbidden in (
            "outcome",
            "ambiguity",
            "retry",
            "resend",
            "executor",
            "authorization",
            "governance",
            "continuation",
        ):
            assert forbidden not in parameters

    assert "outcome" not in RecoveryKeyLineage.__dataclass_fields__
    assert "ambiguity" not in RecoveryKeyLineage.__dataclass_fields__
    assert not hasattr(recovery_module, "retry_capability")
    assert not hasattr(recovery_module, "reinvoke_capability")
    assert not hasattr(recovery_module, "invoke_executor")
