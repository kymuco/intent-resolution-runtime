"""Persistent exact-key deduplication contract for one capability invocation lineage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from .attempt import CapabilityAttempt
from .canonical import canonical_json_bytes, parse_json_object
from .capability import CapabilityExecutionBoundaryKind
from .capability_match import CapabilityMatch
from .capability_match_evaluation import evaluate_capability_match_evaluation
from .errors import IntentIRError, SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef


class DeduplicatedReinvocationContractError(IntentIRError):
    """Raised when a persistent deduplication contract does not match an Attempt."""


def _expect_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SerializationError(f"{field} must be a JSON object")
    return value


def _expect_exact_keys(
    value: dict[str, Any],
    expected: set[str],
    *,
    field: str,
) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        detail: list[str] = []
        if missing:
            detail.append(f"missing={missing}")
        if extra:
            detail.append(f"extra={extra}")
        raise SerializationError(
            f"{field} has invalid fields ({', '.join(detail)})"
        )


def _require_text(value: object, *, field: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValidationError(f"{field} must contain non-whitespace text")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValidationError(f"{field} must contain only Unicode scalar values")
    return value


class _CanonicalDeduplicationRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class PersistentDeduplicationContractAttribution(_CanonicalDeduplicationRecord):
    """Supplier attribution for one declared persistent external deduplication contract."""

    SCHEMA: ClassVar[str] = (
        "irr.persistent_deduplication_contract_attribution.v1"
    )

    supplier_ref: StableRef
    contract_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.supplier_ref) is not StableRef:
            raise ValidationError(
                "PersistentDeduplicationContractAttribution.supplier_ref "
                "must be a StableRef"
            )
        if type(self.contract_event_ref) is not StableRef:
            raise ValidationError(
                "PersistentDeduplicationContractAttribution.contract_event_ref "
                "must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "contract_event_ref": self.contract_event_ref.to_primitive(),
            "schema": self.SCHEMA,
            "supplier_ref": self.supplier_ref.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "PersistentDeduplicationContractAttribution",
    ) -> PersistentDeduplicationContractAttribution:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "supplier_ref", "contract_event_ref"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported {field} schema: {obj['schema']!r}"
            )
        try:
            return cls(
                supplier_ref=StableRef.from_primitive(
                    obj["supplier_ref"],
                    field=f"{field}.supplier_ref",
                ),
                contract_event_ref=StableRef.from_primitive(
                    obj["contract_event_ref"],
                    field=f"{field}.contract_event_ref",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> PersistentDeduplicationContractAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class PersistentDeduplicatedReinvocationContract(_CanonicalDeduplicationRecord):
    """Declared persistent exact-key deduplication guarantee for one capability contract.

    This record is not retry authority and does not verify the external system. It states
    that the same exact invocation, submitted repeatedly to the same deduplication domain
    with the same derived key, is externally deduplicated to at most one target effect.
    """

    SCHEMA: ClassVar[str] = (
        "irr.persistent_deduplicated_reinvocation_contract.v1"
    )

    attribution: PersistentDeduplicationContractAttribution
    catalog_snapshot_identity: RecordIdentity
    capability_ref: StableRef
    capability_contract_identity: RecordIdentity
    executor_ref: StableRef
    deduplication_domain_ref: StableRef
    statement: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not PersistentDeduplicationContractAttribution:
            raise ValidationError(
                "PersistentDeduplicatedReinvocationContract.attribution must be "
                "PersistentDeduplicationContractAttribution"
            )
        if type(self.catalog_snapshot_identity) is not RecordIdentity:
            raise ValidationError(
                "PersistentDeduplicatedReinvocationContract."
                "catalog_snapshot_identity must be a RecordIdentity"
            )
        if type(self.capability_ref) is not StableRef:
            raise ValidationError(
                "PersistentDeduplicatedReinvocationContract.capability_ref "
                "must be a StableRef"
            )
        if type(self.capability_contract_identity) is not RecordIdentity:
            raise ValidationError(
                "PersistentDeduplicatedReinvocationContract."
                "capability_contract_identity must be a RecordIdentity"
            )
        if type(self.executor_ref) is not StableRef:
            raise ValidationError(
                "PersistentDeduplicatedReinvocationContract.executor_ref "
                "must be a StableRef"
            )
        if type(self.deduplication_domain_ref) is not StableRef:
            raise ValidationError(
                "PersistentDeduplicatedReinvocationContract."
                "deduplication_domain_ref must be a StableRef"
            )
        _require_text(
            self.statement,
            field="PersistentDeduplicatedReinvocationContract.statement",
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "capability_contract_identity": (
                self.capability_contract_identity.to_primitive()
            ),
            "capability_ref": self.capability_ref.to_primitive(),
            "catalog_snapshot_identity": self.catalog_snapshot_identity.to_primitive(),
            "deduplication_domain_ref": self.deduplication_domain_ref.to_primitive(),
            "executor_ref": self.executor_ref.to_primitive(),
            "schema": self.SCHEMA,
            "statement": self.statement,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "PersistentDeduplicatedReinvocationContract",
    ) -> PersistentDeduplicatedReinvocationContract:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "attribution",
                "catalog_snapshot_identity",
                "capability_ref",
                "capability_contract_identity",
                "executor_ref",
                "deduplication_domain_ref",
                "statement",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported {field} schema: {obj['schema']!r}"
            )
        try:
            return cls(
                attribution=PersistentDeduplicationContractAttribution.from_primitive(
                    obj["attribution"],
                    field=f"{field}.attribution",
                ),
                catalog_snapshot_identity=RecordIdentity.from_primitive(
                    obj["catalog_snapshot_identity"],
                    field=f"{field}.catalog_snapshot_identity",
                ),
                capability_ref=StableRef.from_primitive(
                    obj["capability_ref"],
                    field=f"{field}.capability_ref",
                ),
                capability_contract_identity=RecordIdentity.from_primitive(
                    obj["capability_contract_identity"],
                    field=f"{field}.capability_contract_identity",
                ),
                executor_ref=StableRef.from_primitive(
                    obj["executor_ref"],
                    field=f"{field}.executor_ref",
                ),
                deduplication_domain_ref=StableRef.from_primitive(
                    obj["deduplication_domain_ref"],
                    field=f"{field}.deduplication_domain_ref",
                ),
                statement=obj["statement"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> PersistentDeduplicatedReinvocationContract:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityIdempotencyKey(_CanonicalDeduplicationRecord):
    """Stable exact-key material for one Attempt under one persistent contract."""

    SCHEMA: ClassVar[str] = "irr.capability_idempotency_key.v1"

    contract_identity: RecordIdentity
    attempt_identity: RecordIdentity
    deduplication_domain_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.contract_identity) is not RecordIdentity:
            raise ValidationError(
                "CapabilityIdempotencyKey.contract_identity must be a RecordIdentity"
            )
        if type(self.attempt_identity) is not RecordIdentity:
            raise ValidationError(
                "CapabilityIdempotencyKey.attempt_identity must be a RecordIdentity"
            )
        if type(self.deduplication_domain_ref) is not StableRef:
            raise ValidationError(
                "CapabilityIdempotencyKey.deduplication_domain_ref must be a StableRef"
            )

    @property
    def external_token(self) -> str:
        """Opaque stable token to transport to the declared deduplication domain."""

        return self.identity.digest

    def to_primitive(self) -> dict[str, object]:
        return {
            "attempt_identity": self.attempt_identity.to_primitive(),
            "contract_identity": self.contract_identity.to_primitive(),
            "deduplication_domain_ref": self.deduplication_domain_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "CapabilityIdempotencyKey",
    ) -> CapabilityIdempotencyKey:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "contract_identity",
                "attempt_identity",
                "deduplication_domain_ref",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported {field} schema: {obj['schema']!r}"
            )
        try:
            return cls(
                contract_identity=RecordIdentity.from_primitive(
                    obj["contract_identity"],
                    field=f"{field}.contract_identity",
                ),
                attempt_identity=RecordIdentity.from_primitive(
                    obj["attempt_identity"],
                    field=f"{field}.attempt_identity",
                ),
                deduplication_domain_ref=StableRef.from_primitive(
                    obj["deduplication_domain_ref"],
                    field=f"{field}.deduplication_domain_ref",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> CapabilityIdempotencyKey:
        return cls.from_primitive(parse_json_object(data))


def derive_capability_idempotency_key(
    contract: PersistentDeduplicatedReinvocationContract,
    attempt: CapabilityAttempt,
) -> CapabilityIdempotencyKey:
    """Derive stable key material only for an exact contract/Attempt lineage match."""

    if type(contract) is not PersistentDeduplicatedReinvocationContract:
        raise ValidationError(
            "contract must be a PersistentDeduplicatedReinvocationContract"
        )
    if type(attempt) is not CapabilityAttempt:
        raise ValidationError("attempt must be a CapabilityAttempt")

    match = evaluate_capability_match_evaluation(attempt.capability_evaluation)
    if type(match) is not CapabilityMatch:
        raise AssertionError("validated CapabilityAttempt lost its exact CapabilityMatch")

    if contract.catalog_snapshot_identity != match.catalog_snapshot.identity:
        raise DeduplicatedReinvocationContractError(
            "persistent deduplication contract catalog snapshot does not match "
            "the exact CapabilityAttempt"
        )
    if contract.attribution.supplier_ref != match.catalog_snapshot.attribution.supplier_ref:
        raise DeduplicatedReinvocationContractError(
            "persistent deduplication contract supplier does not match "
            "the exact Capability Catalog supplier"
        )
    if contract.capability_ref != match.capability_ref:
        raise DeduplicatedReinvocationContractError(
            "persistent deduplication contract capability_ref does not match "
            "the exact CapabilityAttempt"
        )
    if contract.capability_contract_identity != match.capability_contract_identity:
        raise DeduplicatedReinvocationContractError(
            "persistent deduplication contract capability identity does not match "
            "the exact CapabilityAttempt"
        )

    descriptors = {
        descriptor.capability_ref: descriptor
        for descriptor in match.catalog_snapshot.descriptors
    }
    descriptor = descriptors[match.capability_ref]
    executor_boundaries = tuple(
        boundary
        for boundary in descriptor.execution_boundaries
        if boundary.kind is CapabilityExecutionBoundaryKind.EXECUTOR
    )
    if len(executor_boundaries) != 1:
        raise DeduplicatedReinvocationContractError(
            "persistent deduplication requires exactly one explicit Executor boundary"
        )
    if contract.executor_ref != executor_boundaries[0].boundary_ref:
        raise DeduplicatedReinvocationContractError(
            "persistent deduplication contract executor_ref does not match "
            "the exact descriptor Executor boundary"
        )
    if attempt.attribution.executor_ref != contract.executor_ref:
        raise DeduplicatedReinvocationContractError(
            "persistent deduplication contract executor_ref does not match "
            "the exact CapabilityAttempt executor"
        )

    return CapabilityIdempotencyKey(
        contract_identity=contract.identity,
        attempt_identity=attempt.identity,
        deduplication_domain_ref=contract.deduplication_domain_ref,
    )


__all__ = (
    "CapabilityIdempotencyKey",
    "DeduplicatedReinvocationContractError",
    "PersistentDeduplicatedReinvocationContract",
    "PersistentDeduplicationContractAttribution",
    "derive_capability_idempotency_key",
)
