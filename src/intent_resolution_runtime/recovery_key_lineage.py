"""Canonical recovery-key lineage for persistent deduplicated invocation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from .attempt import CapabilityAttempt
from .canonical import canonical_json_bytes, parse_json_object
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef
from .persistent_deduplicated_reinvocation import (
    AdmittedPersistentDeduplicationContract,
    CapabilityIdempotencyKey,
    DeduplicatedCapabilityInvocationRequest,
    derive_capability_idempotency_key,
)


class RecoveryKeyLineageError(ValidationError):
    """Raised when recovery cannot inherit one exact original deduplication key."""


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
        raise SerializationError(f"{field} has invalid fields ({', '.join(detail)})")


def _attempt_prerequisite_occurrences(attempt: CapabilityAttempt) -> set[StableRef]:
    """Return every canonical occurrence embedded in one exact CapabilityAttempt."""

    occurrences = {
        attempt.attribution.attempt_event_ref,
        attempt.capability_evaluation.attribution.evaluation_event_ref,
        attempt.capability_match.attribution.match_event_ref,
        attempt.capability_evaluation.catalog_snapshot.attribution.snapshot_event_ref,
        *(
            item.bound_value.binding_attribution.binding_event_ref
            for item in attempt.bound_inputs
        ),
    }
    for authorization in attempt.presented_authorizations:
        occurrences.add(
            authorization.decision.proposal.attribution.proposal_event_ref
        )
        occurrences.add(authorization.decision.attribution.decision_event_ref)
    return occurrences


class _CanonicalRecoveryKeyRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class OriginalDeduplicatedDispatchBindingAttribution(_CanonicalRecoveryKeyRecord):
    """Attribution for canonicalizing one exact M3.0.10 first-dispatch request."""

    SCHEMA: ClassVar[str] = "irr.original_deduplicated_dispatch_binding_attribution.v1"

    binder_ref: StableRef
    binding_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.binder_ref) is not StableRef:
            raise ValidationError(
                "OriginalDeduplicatedDispatchBindingAttribution.binder_ref "
                "must be a StableRef"
            )
        if type(self.binding_event_ref) is not StableRef:
            raise ValidationError(
                "OriginalDeduplicatedDispatchBindingAttribution.binding_event_ref "
                "must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "binder_ref": self.binder_ref.to_primitive(),
            "binding_event_ref": self.binding_event_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "OriginalDeduplicatedDispatchBindingAttribution",
    ) -> OriginalDeduplicatedDispatchBindingAttribution:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "binder_ref", "binding_event_ref"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                binder_ref=StableRef.from_primitive(
                    obj["binder_ref"],
                    field=f"{field}.binder_ref",
                ),
                binding_event_ref=StableRef.from_primitive(
                    obj["binding_event_ref"],
                    field=f"{field}.binding_event_ref",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> OriginalDeduplicatedDispatchBindingAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class OriginalDeduplicatedDispatchBinding(_CanonicalRecoveryKeyRecord):
    """Canonical anchor for the exact first-dispatch Attempt/contract/key binding."""

    SCHEMA: ClassVar[str] = "irr.original_deduplicated_dispatch_binding.v1"

    attribution: OriginalDeduplicatedDispatchBindingAttribution
    original_attempt: CapabilityAttempt
    admitted_contract: AdmittedPersistentDeduplicationContract
    idempotency_key: CapabilityIdempotencyKey

    def __post_init__(self) -> None:
        if type(self.attribution) is not OriginalDeduplicatedDispatchBindingAttribution:
            raise ValidationError(
                "OriginalDeduplicatedDispatchBinding.attribution must be "
                "OriginalDeduplicatedDispatchBindingAttribution"
            )
        if type(self.original_attempt) is not CapabilityAttempt:
            raise ValidationError(
                "OriginalDeduplicatedDispatchBinding.original_attempt "
                "must be a CapabilityAttempt"
            )
        if type(self.admitted_contract) is not AdmittedPersistentDeduplicationContract:
            raise ValidationError(
                "OriginalDeduplicatedDispatchBinding.admitted_contract must be "
                "an AdmittedPersistentDeduplicationContract"
            )
        if type(self.idempotency_key) is not CapabilityIdempotencyKey:
            raise ValidationError(
                "OriginalDeduplicatedDispatchBinding.idempotency_key "
                "must be a CapabilityIdempotencyKey"
            )

        expected = derive_capability_idempotency_key(
            self.admitted_contract,
            self.original_attempt,
        )
        if self.idempotency_key != expected:
            raise RecoveryKeyLineageError(
                "original dispatch binding must preserve the exact M3.0.10 "
                "Attempt/contract/key relation"
            )

        protected_events = {
            *_attempt_prerequisite_occurrences(self.original_attempt),
            self.admitted_contract.admission_attribution.admission_event_ref,
            self.admitted_contract.contract.attribution.contract_event_ref,
            *(
                candidate.attribution.proposal_event_ref
                for candidate in self.admitted_contract.candidate_inputs
            ),
            *(
                candidate.contract.attribution.contract_event_ref
                for candidate in self.admitted_contract.candidate_inputs
            ),
        }
        if self.attribution.binding_event_ref in protected_events:
            raise ValidationError(
                "original dispatch binding occurrence must differ from Attempt, "
                "contract proposal, contract, and admission occurrences"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "admitted_contract": self.admitted_contract.to_primitive(),
            "attribution": self.attribution.to_primitive(),
            "idempotency_key": self.idempotency_key.to_primitive(),
            "original_attempt": self.original_attempt.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "OriginalDeduplicatedDispatchBinding",
    ) -> OriginalDeduplicatedDispatchBinding:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "attribution",
                "original_attempt",
                "admitted_contract",
                "idempotency_key",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                attribution=(
                    OriginalDeduplicatedDispatchBindingAttribution.from_primitive(
                        obj["attribution"],
                        field=f"{field}.attribution",
                    )
                ),
                original_attempt=CapabilityAttempt.from_primitive(
                    obj["original_attempt"],
                    field=f"{field}.original_attempt",
                ),
                admitted_contract=(
                    AdmittedPersistentDeduplicationContract.from_primitive(
                        obj["admitted_contract"],
                        field=f"{field}.admitted_contract",
                    )
                ),
                idempotency_key=CapabilityIdempotencyKey.from_primitive(
                    obj["idempotency_key"],
                    field=f"{field}.idempotency_key",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> OriginalDeduplicatedDispatchBinding:
        return cls.from_primitive(parse_json_object(data))


def build_original_deduplicated_dispatch_binding(
    attribution: OriginalDeduplicatedDispatchBindingAttribution,
    request: DeduplicatedCapabilityInvocationRequest,
) -> OriginalDeduplicatedDispatchBinding:
    """Canonicalize one exact M3.0.10 first-dispatch mechanism request."""

    if type(attribution) is not OriginalDeduplicatedDispatchBindingAttribution:
        raise ValidationError(
            "attribution must be an OriginalDeduplicatedDispatchBindingAttribution"
        )
    if type(request) is not DeduplicatedCapabilityInvocationRequest:
        raise ValidationError(
            "request must be a DeduplicatedCapabilityInvocationRequest"
        )
    return OriginalDeduplicatedDispatchBinding(
        attribution=attribution,
        original_attempt=request.attempt,
        admitted_contract=request.admitted_contract,
        idempotency_key=request.idempotency_key,
    )


@dataclass(frozen=True, slots=True)
class RecoveryKeyLineageAttribution(_CanonicalRecoveryKeyRecord):
    """Attribution for linking one new recovery Attempt to one original key."""

    SCHEMA: ClassVar[str] = "irr.recovery_key_lineage_attribution.v1"

    linker_ref: StableRef
    lineage_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.linker_ref) is not StableRef:
            raise ValidationError(
                "RecoveryKeyLineageAttribution.linker_ref must be a StableRef"
            )
        if type(self.lineage_event_ref) is not StableRef:
            raise ValidationError(
                "RecoveryKeyLineageAttribution.lineage_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "lineage_event_ref": self.lineage_event_ref.to_primitive(),
            "linker_ref": self.linker_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "RecoveryKeyLineageAttribution",
    ) -> RecoveryKeyLineageAttribution:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "linker_ref", "lineage_event_ref"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                linker_ref=StableRef.from_primitive(
                    obj["linker_ref"],
                    field=f"{field}.linker_ref",
                ),
                lineage_event_ref=StableRef.from_primitive(
                    obj["lineage_event_ref"],
                    field=f"{field}.lineage_event_ref",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> RecoveryKeyLineageAttribution:
        return cls.from_primitive(parse_json_object(data))


def _without_descriptions(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _without_descriptions(item)
            for key, item in value.items()
            if key != "description"
        }
    if isinstance(value, list):
        return [_without_descriptions(item) for item in value]
    return value


def _validate_same_concrete_use(
    original: CapabilityAttempt,
    recovery: CapabilityAttempt,
) -> None:
    if original.identity == recovery.identity:
        raise RecoveryKeyLineageError(
            "recovery Attempt must be a new CapabilityAttempt identity"
        )
    if original.attribution.attempt_event_ref == recovery.attribution.attempt_event_ref:
        raise RecoveryKeyLineageError(
            "recovery Attempt must use a distinct attempt occurrence"
        )
    original_requirement = _without_descriptions(
        original.capability_evaluation.requirement.to_primitive()
    )
    recovery_requirement = _without_descriptions(
        recovery.capability_evaluation.requirement.to_primitive()
    )
    if original_requirement != recovery_requirement:
        raise RecoveryKeyLineageError(
            "recovery Attempt must preserve the exact semantic CapabilityRequirement"
        )
    if original.step_ref != recovery.step_ref:
        raise RecoveryKeyLineageError(
            "recovery Attempt must preserve the exact WorkStep ref"
        )
    if original.bound_inputs != recovery.bound_inputs:
        raise RecoveryKeyLineageError(
            "recovery Attempt must preserve the exact bound inputs"
        )

    original_match = original.capability_match
    recovery_match = recovery.capability_match
    if original_match.capability_ref != recovery_match.capability_ref:
        raise RecoveryKeyLineageError(
            "recovery Attempt must preserve the exact capability_ref"
        )
    if (
        original_match.capability_contract_identity
        != recovery_match.capability_contract_identity
    ):
        raise RecoveryKeyLineageError(
            "recovery Attempt must preserve the exact capability contract identity"
        )
    if original.attribution.executor_ref != recovery.attribution.executor_ref:
        raise RecoveryKeyLineageError(
            "recovery Attempt must preserve the exact executor_ref"
        )


@dataclass(frozen=True, slots=True)
class RecoveryKeyLineage(_CanonicalRecoveryKeyRecord):
    """Canonical inheritance of one original dedup key by one new recovery Attempt."""

    SCHEMA: ClassVar[str] = "irr.recovery_key_lineage.v1"

    attribution: RecoveryKeyLineageAttribution
    original_dispatch_binding: OriginalDeduplicatedDispatchBinding
    recovery_attempt: CapabilityAttempt
    inherited_idempotency_key: CapabilityIdempotencyKey

    def __post_init__(self) -> None:
        if type(self.attribution) is not RecoveryKeyLineageAttribution:
            raise ValidationError(
                "RecoveryKeyLineage.attribution must be a RecoveryKeyLineageAttribution"
            )
        if (
            type(self.original_dispatch_binding)
            is not OriginalDeduplicatedDispatchBinding
        ):
            raise ValidationError(
                "RecoveryKeyLineage.original_dispatch_binding must be "
                "OriginalDeduplicatedDispatchBinding"
            )
        if type(self.recovery_attempt) is not CapabilityAttempt:
            raise ValidationError(
                "RecoveryKeyLineage.recovery_attempt must be a CapabilityAttempt"
            )
        if type(self.inherited_idempotency_key) is not CapabilityIdempotencyKey:
            raise ValidationError(
                "RecoveryKeyLineage.inherited_idempotency_key must be "
                "a CapabilityIdempotencyKey"
            )
        if (
            self.inherited_idempotency_key
            != self.original_dispatch_binding.idempotency_key
        ):
            raise RecoveryKeyLineageError(
                "recovery lineage must inherit the exact original idempotency key"
            )

        original = self.original_dispatch_binding.original_attempt
        _validate_same_concrete_use(original, self.recovery_attempt)

        admitted = self.original_dispatch_binding.admitted_contract
        protected_events = {
            self.original_dispatch_binding.attribution.binding_event_ref,
            *_attempt_prerequisite_occurrences(original),
            *_attempt_prerequisite_occurrences(self.recovery_attempt),
            admitted.admission_attribution.admission_event_ref,
            admitted.contract.attribution.contract_event_ref,
            *(
                candidate.attribution.proposal_event_ref
                for candidate in admitted.candidate_inputs
            ),
            *(
                candidate.contract.attribution.contract_event_ref
                for candidate in admitted.candidate_inputs
            ),
        }
        if self.attribution.lineage_event_ref in protected_events:
            raise ValidationError(
                "recovery key lineage occurrence must differ from binding and "
                "Attempt occurrences"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "inherited_idempotency_key": (
                self.inherited_idempotency_key.to_primitive()
            ),
            "original_dispatch_binding": (
                self.original_dispatch_binding.to_primitive()
            ),
            "recovery_attempt": self.recovery_attempt.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "RecoveryKeyLineage",
    ) -> RecoveryKeyLineage:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "attribution",
                "original_dispatch_binding",
                "recovery_attempt",
                "inherited_idempotency_key",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                attribution=RecoveryKeyLineageAttribution.from_primitive(
                    obj["attribution"],
                    field=f"{field}.attribution",
                ),
                original_dispatch_binding=(
                    OriginalDeduplicatedDispatchBinding.from_primitive(
                        obj["original_dispatch_binding"],
                        field=f"{field}.original_dispatch_binding",
                    )
                ),
                recovery_attempt=CapabilityAttempt.from_primitive(
                    obj["recovery_attempt"],
                    field=f"{field}.recovery_attempt",
                ),
                inherited_idempotency_key=CapabilityIdempotencyKey.from_primitive(
                    obj["inherited_idempotency_key"],
                    field=f"{field}.inherited_idempotency_key",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> RecoveryKeyLineage:
        return cls.from_primitive(parse_json_object(data))


def build_recovery_key_lineage(
    attribution: RecoveryKeyLineageAttribution,
    original_dispatch_binding: OriginalDeduplicatedDispatchBinding,
    recovery_attempt: CapabilityAttempt,
) -> RecoveryKeyLineage:
    """Build exact inherited-key lineage for one new recovery Attempt."""

    if type(attribution) is not RecoveryKeyLineageAttribution:
        raise ValidationError("attribution must be a RecoveryKeyLineageAttribution")
    if type(original_dispatch_binding) is not OriginalDeduplicatedDispatchBinding:
        raise ValidationError(
            "original_dispatch_binding must be an OriginalDeduplicatedDispatchBinding"
        )
    if type(recovery_attempt) is not CapabilityAttempt:
        raise ValidationError("recovery_attempt must be a CapabilityAttempt")

    return RecoveryKeyLineage(
        attribution=attribution,
        original_dispatch_binding=original_dispatch_binding,
        recovery_attempt=recovery_attempt,
        inherited_idempotency_key=original_dispatch_binding.idempotency_key,
    )


@dataclass(frozen=True, slots=True)
class DeduplicatedRecoveryInvocationRequest:
    """Non-canonical mechanism state carrying a recovery Attempt and original key."""

    recovery_attempt: CapabilityAttempt
    recovery_key_lineage: RecoveryKeyLineage
    idempotency_key: CapabilityIdempotencyKey

    def __post_init__(self) -> None:
        if type(self.recovery_attempt) is not CapabilityAttempt:
            raise ValidationError(
                "DeduplicatedRecoveryInvocationRequest.recovery_attempt "
                "must be a CapabilityAttempt"
            )
        if type(self.recovery_key_lineage) is not RecoveryKeyLineage:
            raise ValidationError(
                "DeduplicatedRecoveryInvocationRequest.recovery_key_lineage "
                "must be a RecoveryKeyLineage"
            )
        if type(self.idempotency_key) is not CapabilityIdempotencyKey:
            raise ValidationError(
                "DeduplicatedRecoveryInvocationRequest.idempotency_key "
                "must be a CapabilityIdempotencyKey"
            )
        if self.recovery_attempt != self.recovery_key_lineage.recovery_attempt:
            raise RecoveryKeyLineageError(
                "recovery invocation request must carry the exact lineage "
                "recovery Attempt"
            )
        if self.idempotency_key != self.recovery_key_lineage.inherited_idempotency_key:
            raise RecoveryKeyLineageError(
                "recovery invocation request must carry the exact inherited "
                "original key"
            )


def build_deduplicated_recovery_invocation_request(
    lineage: RecoveryKeyLineage,
) -> DeduplicatedRecoveryInvocationRequest:
    """Build recovery mechanism state without invoking an Executor."""

    if type(lineage) is not RecoveryKeyLineage:
        raise ValidationError("lineage must be a RecoveryKeyLineage")
    return DeduplicatedRecoveryInvocationRequest(
        recovery_attempt=lineage.recovery_attempt,
        recovery_key_lineage=lineage,
        idempotency_key=lineage.inherited_idempotency_key,
    )


__all__ = (
    "DeduplicatedRecoveryInvocationRequest",
    "OriginalDeduplicatedDispatchBinding",
    "OriginalDeduplicatedDispatchBindingAttribution",
    "RecoveryKeyLineage",
    "RecoveryKeyLineageAttribution",
    "RecoveryKeyLineageError",
    "build_deduplicated_recovery_invocation_request",
    "build_original_deduplicated_dispatch_binding",
    "build_recovery_key_lineage",
)
