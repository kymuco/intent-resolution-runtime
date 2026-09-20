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
    ValidationError,
)
from intent_resolution_runtime.persistent_deduplicated_reinvocation import (
    AdmittedPersistentDeduplicationContract,
    CandidatePersistentDeduplicationContract,
    CapabilityIdempotencyKey,
    DeduplicatedCapabilityInvocationRequest,
    DeduplicatedReinvocationContractError,
    PersistentDeduplicatedReinvocationContract,
    PersistentDeduplicationContractAdmissionAttribution,
    PersistentDeduplicationContractAttribution,
    PersistentDeduplicationContractProposalAttribution,
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
            "The external target persistently deduplicates all submissions carrying "
            "one exact idempotency key inside this domain to at most one protected "
            "target effect."
        ),
    )


def _candidate(
    contract: PersistentDeduplicatedReinvocationContract,
    *,
    label: str,
) -> CandidatePersistentDeduplicationContract:
    return CandidatePersistentDeduplicationContract(
        attribution=PersistentDeduplicationContractProposalAttribution(
            proposer_ref=_ref("irr.deduplication_contract_proposer", "test-host"),
            proposal_event_ref=_ref("irr.event", f"proposal-{label}"),
        ),
        contract=contract,
        rationale="Propose the exact downstream deduplication guarantee for admission.",
    )


def _admit_contract(
    contract: PersistentDeduplicatedReinvocationContract,
    *,
    label: str,
) -> AdmittedPersistentDeduplicationContract:
    candidate = _candidate(contract, label=label)
    return AdmittedPersistentDeduplicationContract(
        admission_attribution=PersistentDeduplicationContractAdmissionAttribution(
            resolver_ref=_ref("irr.deduplication_contract_admitter", "test-host"),
            admission_event_ref=_ref("irr.event", f"admission-{label}"),
        ),
        contract=contract,
        candidate_inputs=(candidate,),
    )


def _admitted(
    attempt,
    *,
    label: str = "dedup",
) -> AdmittedPersistentDeduplicationContract:
    return _admit_contract(
        _contract(attempt, event=f"contract-{label}"),
        label=label,
    )


def test_exact_admitted_contract_and_attempt_derive_stable_key() -> None:
    attempt = _exact_attempt()
    admitted = _admitted(attempt)

    first = derive_capability_idempotency_key(admitted, attempt)
    second = derive_capability_idempotency_key(admitted, attempt)

    assert first.__class__ is CapabilityIdempotencyKey
    assert first == second
    assert first.identity == second.identity
    assert first.admitted_contract_identity == admitted.identity
    assert first.original_attempt_identity == attempt.identity
    assert (
        first.deduplication_domain_ref
        == admitted.contract.deduplication_domain_ref
    )
    assert first.external_token == first.identity.digest
    assert len(first.external_token) == 64


def test_raw_downstream_contract_cannot_derive_key_without_admission() -> None:
    attempt = _exact_attempt()
    raw = _contract(attempt)

    with pytest.raises(
        ValidationError,
        match="admitted_contract must be an AdmittedPersistentDeduplicationContract",
    ):
        derive_capability_idempotency_key(raw, attempt)  # type: ignore[arg-type]


def test_admission_requires_explicit_candidate_provenance() -> None:
    attempt = _exact_attempt()
    contract = _contract(attempt)

    with pytest.raises(
        ValidationError,
        match="requires explicit candidate provenance",
    ):
        AdmittedPersistentDeduplicationContract(
            admission_attribution=(
                PersistentDeduplicationContractAdmissionAttribution(
                    resolver_ref=_ref(
                        "irr.deduplication_contract_admitter",
                        "test-host",
                    ),
                    admission_event_ref=_ref("irr.event", "admission-empty"),
                )
            ),
            contract=contract,
            candidate_inputs=(),
        )


def test_admission_must_equal_one_exact_proposed_contract() -> None:
    attempt = _exact_attempt()
    admitted_contract = _contract(attempt, event="contract-admitted")
    foreign_candidate = _candidate(
        _contract(
            attempt,
            event="contract-foreign",
            domain="foreign-domain",
        ),
        label="foreign-candidate",
    )

    with pytest.raises(
        ValidationError,
        match="must equal one exact proposed downstream contract",
    ):
        AdmittedPersistentDeduplicationContract(
            admission_attribution=(
                PersistentDeduplicationContractAdmissionAttribution(
                    resolver_ref=_ref(
                        "irr.deduplication_contract_admitter",
                        "test-host",
                    ),
                    admission_event_ref=_ref("irr.event", "admission-foreign"),
                )
            ),
            contract=admitted_contract,
            candidate_inputs=(foreign_candidate,),
        )


def test_contract_proposal_and_admission_occurrences_cannot_alias() -> None:
    attempt = _exact_attempt()
    contract = _contract(attempt, event="contract-occurrence")

    with pytest.raises(
        ValidationError,
        match="proposal occurrence must differ",
    ):
        CandidatePersistentDeduplicationContract(
            attribution=PersistentDeduplicationContractProposalAttribution(
                proposer_ref=_ref(
                    "irr.deduplication_contract_proposer",
                    "test-host",
                ),
                proposal_event_ref=contract.attribution.contract_event_ref,
            ),
            contract=contract,
            rationale="Aliased occurrence must fail closed.",
        )

    candidate = _candidate(contract, label="occurrence")
    with pytest.raises(
        ValidationError,
        match="admission occurrence must differ",
    ):
        AdmittedPersistentDeduplicationContract(
            admission_attribution=(
                PersistentDeduplicationContractAdmissionAttribution(
                    resolver_ref=_ref(
                        "irr.deduplication_contract_admitter",
                        "test-host",
                    ),
                    admission_event_ref=candidate.attribution.proposal_event_ref,
                )
            ),
            contract=contract,
            candidate_inputs=(candidate,),
        )


def test_distinct_fresh_attempt_occurrence_derives_distinct_original_key() -> None:
    first_attempt = _exact_attempt(event="attempt-dedup-first")
    second_attempt = _exact_attempt(event="attempt-dedup-second")
    admitted = _admitted(first_attempt, label="fresh-attempts")

    assert first_attempt.capability_match == second_attempt.capability_match
    assert first_attempt.identity != second_attempt.identity

    first_key = derive_capability_idempotency_key(admitted, first_attempt)
    second_key = derive_capability_idempotency_key(admitted, second_attempt)

    assert first_key != second_key
    assert first_key.external_token != second_key.external_token


def test_first_dispatch_request_carries_exact_original_key() -> None:
    attempt = _exact_attempt()
    admitted = _admitted(attempt, label="first-dispatch")

    request = build_deduplicated_capability_invocation_request(
        admitted,
        attempt,
    )

    assert request.__class__ is DeduplicatedCapabilityInvocationRequest
    assert request.attempt == attempt
    assert request.admitted_contract == admitted
    assert request.idempotency_key == derive_capability_idempotency_key(
        admitted,
        attempt,
    )
    assert request.idempotency_key.original_attempt_identity == attempt.identity


def test_first_dispatch_request_rejects_forged_key() -> None:
    attempt = _exact_attempt()
    admitted = _admitted(attempt, label="forged-key")
    forged = CapabilityIdempotencyKey(
        admitted_contract_identity=admitted.identity,
        original_attempt_identity=RecordIdentity("sha256", "d" * 64),
        deduplication_domain_ref=admitted.contract.deduplication_domain_ref,
    )

    with pytest.raises(
        DeduplicatedReinvocationContractError,
        match="must carry the exact key derived",
    ):
        DeduplicatedCapabilityInvocationRequest(
            attempt=attempt,
            admitted_contract=admitted,
            idempotency_key=forged,
        )


def test_deduplicated_invocation_request_is_mechanism_state_not_canonical_ir() -> None:
    attempt = _exact_attempt()
    request = build_deduplicated_capability_invocation_request(
        _admitted(attempt, label="mechanism-state"),
        attempt,
    )

    assert not hasattr(request, "SCHEMA")
    assert not hasattr(request, "identity")
    assert not hasattr(request, "canonical_bytes")


def test_admission_identity_change_changes_original_key() -> None:
    attempt = _exact_attempt()
    contract = _contract(attempt, event="contract-shared")
    first = _admit_contract(contract, label="admission-first")
    second = _admit_contract(contract, label="admission-second")

    assert first.contract == second.contract
    assert first.identity != second.identity

    first_key = derive_capability_idempotency_key(first, attempt)
    second_key = derive_capability_idempotency_key(second, attempt)

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
def test_admitted_contract_lineage_mismatch_fails_closed(
    field: str,
    value: object,
) -> None:
    attempt = _exact_attempt()
    foreign_contract = replace(_contract(attempt), **{field: value})
    admitted = _admit_contract(foreign_contract, label=f"foreign-{field}")

    with pytest.raises(DeduplicatedReinvocationContractError):
        derive_capability_idempotency_key(admitted, attempt)


def test_admitted_contract_supplier_must_match_exact_catalog_supplier() -> None:
    attempt = _exact_attempt()
    contract = _contract(attempt)
    foreign = replace(
        contract,
        attribution=replace(
            contract.attribution,
            supplier_ref=_ref("irr.host", "foreign-supplier"),
        ),
    )
    admitted = _admit_contract(foreign, label="foreign-supplier")

    with pytest.raises(
        DeduplicatedReinvocationContractError,
        match="supplier does not match",
    ):
        derive_capability_idempotency_key(admitted, attempt)


def test_contract_requires_exactly_one_explicit_executor_boundary() -> None:
    no_executor = _attempt(
        executor="artifact-executor",
        executor_boundaries=(),
    )
    no_executor_admitted = _admitted(no_executor, label="no-executor")

    with pytest.raises(
        DeduplicatedReinvocationContractError,
        match="exactly one explicit Executor boundary",
    ):
        derive_capability_idempotency_key(no_executor_admitted, no_executor)

    multiple = _attempt(
        executor="artifact-executor",
        executor_boundaries=(
            _executor_boundary("artifact-executor"),
            _executor_boundary("secondary-executor"),
        ),
    )
    multiple_admitted = _admitted(multiple, label="multiple-executors")

    with pytest.raises(
        DeduplicatedReinvocationContractError,
        match="exactly one explicit Executor boundary",
    ):
        derive_capability_idempotency_key(multiple_admitted, multiple)


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
    admitted = _admitted(attempt, label="service-only")

    with pytest.raises(
        DeduplicatedReinvocationContractError,
        match="exactly one explicit Executor boundary",
    ):
        derive_capability_idempotency_key(admitted, attempt)


def test_contract_admission_and_key_roundtrip_preserve_exact_identity() -> None:
    attempt = _exact_attempt()
    admitted = _admitted(attempt, label="roundtrip")
    key = derive_capability_idempotency_key(admitted, attempt)

    restored_contract = PersistentDeduplicatedReinvocationContract.from_json_bytes(
        admitted.contract.canonical_bytes()
    )
    restored_admitted = AdmittedPersistentDeduplicationContract.from_json_bytes(
        admitted.canonical_bytes()
    )
    restored_key = CapabilityIdempotencyKey.from_json_bytes(key.canonical_bytes())

    assert restored_contract == admitted.contract
    assert restored_contract.identity == admitted.contract.identity
    assert restored_admitted == admitted
    assert restored_admitted.identity == admitted.identity
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
    assert set(derive_parameters) == {"admitted_contract", "attempt"}
    assert set(build_parameters) == {"admitted_contract", "attempt"}

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


def test_raw_key_construction_is_not_admission_validation() -> None:
    attempt = _exact_attempt()
    admitted = _admitted(attempt, label="raw-key")
    forged = CapabilityIdempotencyKey(
        admitted_contract_identity=RecordIdentity("sha256", "d" * 64),
        original_attempt_identity=attempt.identity,
        deduplication_domain_ref=_ref(
            "irr.deduplication_domain",
            "forged",
        ),
    )

    assert forged.admitted_contract_identity != admitted.identity
    assert forged.external_token != derive_capability_idempotency_key(
        admitted,
        attempt,
    ).external_token
