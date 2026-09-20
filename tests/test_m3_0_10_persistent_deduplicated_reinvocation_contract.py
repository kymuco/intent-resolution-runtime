from __future__ import annotations

import inspect
from dataclasses import replace

import pytest

import intent_resolution_runtime.persistent_deduplicated_reinvocation as dedup_module
from intent_resolution_runtime import (
    CapabilityExecutionBoundary,
    CapabilityExecutionBoundaryKind,
    RecordIdentity,
    SerializationError,
    StableRef,
)
from intent_resolution_runtime.persistent_deduplicated_reinvocation import (
    CapabilityIdempotencyKey,
    DeduplicatedCapabilityInvocationRequest,
    DeduplicatedReinvocationContractError,
    PersistentDeduplicatedReinvocationContract,
    PersistentDeduplicationContractAttribution,
    build_deduplicated_capability_invocation_request,
    derive_capability_idempotency_key,
)
from tests.test_m3_4_executor_capability_invocation_port import (
    _attempt,
    _executor_boundary,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _exact_attempt(*, event: str = "attempt-dedup"):
    return _attempt(
        event=event,
        executor="artifact-executor",
        executor_boundaries=(_executor_boundary("artifact-executor"),),
    )


def _contract(
    attempt,
    *,
    event: str = "contract-dedup",
    domain: str = "artifact-publish-persistent",
) -> PersistentDeduplicatedReinvocationContract:
    match = attempt.capability_match
    return PersistentDeduplicatedReinvocationContract(
        attribution=PersistentDeduplicationContractAttribution(
            supplier_ref=match.catalog_snapshot.attribution.supplier_ref,
            contract_event_ref=_ref("irr.event", event),
        ),
        catalog_snapshot_identity=match.catalog_snapshot.identity,
        capability_ref=match.capability_ref,
        capability_contract_identity=match.capability_contract_identity,
        executor_ref=attempt.attribution.executor_ref,
        deduplication_domain_ref=_ref("irr.deduplication_domain", domain),
        statement=(
            "The external target persistently deduplicates repeated exact invocation "
            "submissions carrying the same derived idempotency key to at most one "
            "target effect."
        ),
    )


def test_exact_contract_and_attempt_derive_stable_key() -> None:
    attempt = _exact_attempt()
    contract = _contract(attempt)

    first = derive_capability_idempotency_key(contract, attempt)
    second = derive_capability_idempotency_key(contract, attempt)

    assert first.__class__ is CapabilityIdempotencyKey
    assert first == second
    assert first.identity == second.identity
    assert first.contract_identity == contract.identity
    assert first.attempt_identity == attempt.identity
    assert first.deduplication_domain_ref == contract.deduplication_domain_ref
    assert first.external_token == first.identity.digest
    assert len(first.external_token) == 64


def test_distinct_fresh_attempt_occurrence_derives_distinct_key() -> None:
    first_attempt = _exact_attempt(event="attempt-dedup-first")
    second_attempt = _exact_attempt(event="attempt-dedup-second")
    contract = _contract(first_attempt)

    assert first_attempt.capability_match == second_attempt.capability_match
    assert first_attempt.identity != second_attempt.identity

    first_key = derive_capability_idempotency_key(contract, first_attempt)
    second_key = derive_capability_idempotency_key(contract, second_attempt)

    assert first_key != second_key
    assert first_key.external_token != second_key.external_token


def test_first_dispatch_request_carries_exact_original_key() -> None:
    attempt = _exact_attempt()
    contract = _contract(attempt)

    request = build_deduplicated_capability_invocation_request(contract, attempt)

    assert request.__class__ is DeduplicatedCapabilityInvocationRequest
    assert request.attempt == attempt
    assert request.contract == contract
    assert request.idempotency_key == derive_capability_idempotency_key(
        contract,
        attempt,
    )
    assert request.idempotency_key.attempt_identity == attempt.identity


def test_first_dispatch_request_rejects_forged_key() -> None:
    attempt = _exact_attempt()
    contract = _contract(attempt)
    forged = CapabilityIdempotencyKey(
        contract_identity=contract.identity,
        attempt_identity=RecordIdentity("sha256", "d" * 64),
        deduplication_domain_ref=contract.deduplication_domain_ref,
    )

    with pytest.raises(
        DeduplicatedReinvocationContractError,
        match="must carry the exact key derived",
    ):
        DeduplicatedCapabilityInvocationRequest(
            attempt=attempt,
            contract=contract,
            idempotency_key=forged,
        )


def test_deduplicated_invocation_request_is_mechanism_state_not_canonical_ir() -> None:
    attempt = _exact_attempt()
    request = build_deduplicated_capability_invocation_request(
        _contract(attempt),
        attempt,
    )

    assert not hasattr(request, "SCHEMA")
    assert not hasattr(request, "identity")
    assert not hasattr(request, "canonical_bytes")


def test_contract_identity_change_changes_key() -> None:
    attempt = _exact_attempt()
    first_contract = _contract(attempt, event="contract-first")
    second_contract = _contract(attempt, event="contract-second")

    assert first_contract.identity != second_contract.identity

    first_key = derive_capability_idempotency_key(first_contract, attempt)
    second_key = derive_capability_idempotency_key(second_contract, attempt)

    assert first_key != second_key
    assert first_key.external_token != second_key.external_token


@pytest.mark.parametrize(
    ("field", "value"),
    (
        (
            "catalog_snapshot_identity",
            RecordIdentity("sha256", "f" * 64),
        ),
        (
            "capability_ref",
            _ref("irr.capability", "foreign"),
        ),
        (
            "capability_contract_identity",
            RecordIdentity("sha256", "e" * 64),
        ),
        (
            "executor_ref",
            _ref("irr.executor", "foreign"),
        ),
    ),
)
def test_contract_lineage_mismatch_fails_closed(field: str, value: object) -> None:
    attempt = _exact_attempt()
    contract = replace(_contract(attempt), **{field: value})

    with pytest.raises(DeduplicatedReinvocationContractError):
        derive_capability_idempotency_key(contract, attempt)


def test_contract_supplier_must_match_exact_catalog_supplier() -> None:
    attempt = _exact_attempt()
    contract = _contract(attempt)
    foreign = replace(
        contract,
        attribution=replace(
            contract.attribution,
            supplier_ref=_ref("irr.host", "foreign-supplier"),
        ),
    )

    with pytest.raises(
        DeduplicatedReinvocationContractError,
        match="supplier does not match",
    ):
        derive_capability_idempotency_key(foreign, attempt)


def test_contract_requires_exactly_one_explicit_executor_boundary() -> None:
    no_executor = _attempt(
        executor="artifact-executor",
        executor_boundaries=(),
    )
    no_executor_contract = _contract(no_executor)

    with pytest.raises(
        DeduplicatedReinvocationContractError,
        match="exactly one explicit Executor boundary",
    ):
        derive_capability_idempotency_key(no_executor_contract, no_executor)

    multiple = _attempt(
        executor="artifact-executor",
        executor_boundaries=(
            _executor_boundary("artifact-executor"),
            _executor_boundary("secondary-executor"),
        ),
    )
    multiple_contract = _contract(multiple)

    with pytest.raises(
        DeduplicatedReinvocationContractError,
        match="exactly one explicit Executor boundary",
    ):
        derive_capability_idempotency_key(multiple_contract, multiple)


def test_non_executor_boundary_cannot_substitute_for_executor_contract() -> None:
    service = CapabilityExecutionBoundary(
        _ref("irr.service", "artifact-service"),
        CapabilityExecutionBoundaryKind.SERVICE,
        "Service boundary is not a persistent-dedup Executor boundary.",
    )
    attempt = _attempt(
        executor="artifact-executor",
        executor_boundaries=(service,),
    )
    contract = _contract(attempt)

    with pytest.raises(
        DeduplicatedReinvocationContractError,
        match="exactly one explicit Executor boundary",
    ):
        derive_capability_idempotency_key(contract, attempt)


def test_contract_and_key_roundtrip_preserve_exact_identity() -> None:
    attempt = _exact_attempt()
    contract = _contract(attempt)
    key = derive_capability_idempotency_key(contract, attempt)

    restored_contract = PersistentDeduplicatedReinvocationContract.from_json_bytes(
        contract.canonical_bytes()
    )
    restored_key = CapabilityIdempotencyKey.from_json_bytes(key.canonical_bytes())

    assert restored_contract == contract
    assert restored_contract.identity == contract.identity
    assert restored_key == key
    assert restored_key.identity == key.identity
    assert restored_key.external_token == key.external_token


def test_serialized_contract_cannot_change_schema_or_lineage_shape() -> None:
    attempt = _exact_attempt()
    primitive = _contract(attempt).to_primitive()
    primitive["schema"] = "irr.unknown.v1"

    with pytest.raises(SerializationError, match="unsupported"):
        PersistentDeduplicatedReinvocationContract.from_primitive(primitive)


def test_public_surface_exposes_first_dispatch_material_not_retry_execution() -> None:
    derive_parameters = inspect.signature(
        derive_capability_idempotency_key
    ).parameters
    build_parameters = inspect.signature(
        build_deduplicated_capability_invocation_request
    ).parameters
    assert set(derive_parameters) == {"contract", "attempt"}
    assert set(build_parameters) == {"contract", "attempt"}

    for parameters in (derive_parameters, build_parameters):
        for forbidden in (
            "retry",
            "recovery_attempt",
            "reinvoke",
            "resend",
            "executor",
            "outcome",
            "authorization",
            "governance",
            "continuation",
        ):
            assert forbidden not in parameters

    assert not hasattr(dedup_module, "retry_capability")
    assert not hasattr(dedup_module, "reinvoke_capability")
    assert not hasattr(dedup_module, "invoke_executor")


def test_v1_contract_has_no_finite_window_or_clock_surface() -> None:
    fields = set(PersistentDeduplicatedReinvocationContract.__dataclass_fields__)

    for forbidden in (
        "expires_at",
        "ttl",
        "window",
        "duration",
        "clock",
        "timestamp",
        "retry_count",
    ):
        assert forbidden not in fields


def test_raw_key_construction_is_not_contract_validation() -> None:
    attempt = _exact_attempt()
    forged = CapabilityIdempotencyKey(
        contract_identity=RecordIdentity("sha256", "d" * 64),
        attempt_identity=attempt.identity,
        deduplication_domain_ref=_ref("irr.deduplication_domain", "forged"),
    )

    assert forged.contract_identity != _contract(attempt).identity
    assert forged.external_token != derive_capability_idempotency_key(
        _contract(attempt),
        attempt,
    ).external_token
