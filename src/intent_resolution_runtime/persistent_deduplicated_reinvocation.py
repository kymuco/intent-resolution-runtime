"""Persistent exact-key deduplication prerequisite for one capability lineage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, cast

from .attempt import CapabilityAttempt
from .canonical import canonical_json_bytes, parse_json_object
from .capability import CapabilityExecutionBoundaryKind
from .capability_match import CapabilityMatch
from .capability_match_evaluation import evaluate_capability_match_evaluation
from .errors import IntentIRError, SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef


class DeduplicatedReinvocationContractError(IntentIRError):
    """Raised when admitted persistent deduplication lineage does not match."""


def _expect_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SerializationError(f"{field} must be a JSON object")
    return value


def _expect_array(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise SerializationError(f"{field} must be a JSON array")
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
    """Supplier attribution for one declared persistent external deduplication
    contract."""

    SCHEMA: ClassVar[str] = "irr.persistent_deduplication_contract_attribution.v1"

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
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
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
    """Declared persistent exact-key suppression guarantee for one capability contract.

    This record is not retry authority and does not verify the external system.
    It states
    that submissions inside the same deduplication domain carrying one exact idempotency
    key are externally deduplicated to at most one protected target effect. Incompatible
    reuse of that key must not create a second protected target effect.
    """

    SCHEMA: ClassVar[str] = "irr.persistent_deduplicated_reinvocation_contract.v1"

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
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
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
class PersistentDeduplicationContractProposalAttribution(_CanonicalDeduplicationRecord):
    SCHEMA: ClassVar[str] = (
        "irr.persistent_deduplication_contract_proposal_attribution.v1"
    )

    proposer_ref: StableRef
    proposal_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.proposer_ref) is not StableRef:
            raise ValidationError(
                "PersistentDeduplicationContractProposalAttribution.proposer_ref "
                "must be a StableRef"
            )
        if type(self.proposal_event_ref) is not StableRef:
            raise ValidationError(
                "PersistentDeduplicationContractProposalAttribution.proposal_event_ref "
                "must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "proposal_event_ref": self.proposal_event_ref.to_primitive(),
            "proposer_ref": self.proposer_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "PersistentDeduplicationContractProposalAttribution",
    ) -> PersistentDeduplicationContractProposalAttribution:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "proposer_ref", "proposal_event_ref"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                proposer_ref=StableRef.from_primitive(
                    obj["proposer_ref"],
                    field=f"{field}.proposer_ref",
                ),
                proposal_event_ref=StableRef.from_primitive(
                    obj["proposal_event_ref"],
                    field=f"{field}.proposal_event_ref",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> PersistentDeduplicationContractProposalAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CandidatePersistentDeduplicationContract(_CanonicalDeduplicationRecord):
    """Proposed persistent deduplication contract; never active retry-safety state."""

    SCHEMA: ClassVar[str] = "irr.candidate_persistent_deduplication_contract.v1"

    attribution: PersistentDeduplicationContractProposalAttribution
    contract: PersistentDeduplicatedReinvocationContract
    rationale: str

    def __post_init__(self) -> None:
        if (
            type(self.attribution)
            is not PersistentDeduplicationContractProposalAttribution
        ):
            raise ValidationError(
                "CandidatePersistentDeduplicationContract.attribution must be "
                "PersistentDeduplicationContractProposalAttribution"
            )
        if type(self.contract) is not PersistentDeduplicatedReinvocationContract:
            raise ValidationError(
                "CandidatePersistentDeduplicationContract.contract must be "
                "PersistentDeduplicatedReinvocationContract"
            )
        if (
            self.attribution.proposal_event_ref
            == self.contract.attribution.contract_event_ref
        ):
            raise ValidationError(
                "persistent deduplication proposal occurrence must differ from "
                "the downstream contract occurrence"
            )
        _require_text(
            self.rationale,
            field="CandidatePersistentDeduplicationContract.rationale",
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "contract": self.contract.to_primitive(),
            "rationale": self.rationale,
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "CandidatePersistentDeduplicationContract",
    ) -> CandidatePersistentDeduplicationContract:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "attribution", "contract", "rationale"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                attribution=(
                    PersistentDeduplicationContractProposalAttribution.from_primitive(
                        obj["attribution"],
                        field=f"{field}.attribution",
                    )
                ),
                contract=PersistentDeduplicatedReinvocationContract.from_primitive(
                    obj["contract"],
                    field=f"{field}.contract",
                ),
                rationale=obj["rationale"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> CandidatePersistentDeduplicationContract:
        return cls.from_primitive(parse_json_object(data))


def _normalize_candidates(
    value: object,
    *,
    field: str,
) -> tuple[CandidatePersistentDeduplicationContract, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(
        type(item) is CandidatePersistentDeduplicationContract for item in value
    ):
        raise ValidationError(
            f"{field} must contain CandidatePersistentDeduplicationContract values"
        )
    items = cast(tuple[CandidatePersistentDeduplicationContract, ...], value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate candidates")

    contract_event_identities: dict[StableRef, RecordIdentity] = {}
    for item in items:
        event_ref = item.contract.attribution.contract_event_ref
        prior_identity = contract_event_identities.get(event_ref)
        if prior_identity is not None and prior_identity != item.contract.identity:
            raise ValidationError(
                f"{field} assigns one downstream contract occurrence to "
                "multiple contract identities"
            )
        contract_event_identities[event_ref] = item.contract.identity

    return tuple(sorted(items, key=lambda item: str(item.identity)))


def _contract_target(
    contract: PersistentDeduplicatedReinvocationContract,
) -> tuple[RecordIdentity, StableRef, RecordIdentity, StableRef]:
    return (
        contract.catalog_snapshot_identity,
        contract.capability_ref,
        contract.capability_contract_identity,
        contract.executor_ref,
    )


def _validate_candidate_targets(
    candidates: tuple[CandidatePersistentDeduplicationContract, ...],
    *,
    selected_contract: PersistentDeduplicatedReinvocationContract,
    field: str,
) -> None:
    selected_target = _contract_target(selected_contract)
    for candidate in candidates:
        if _contract_target(candidate.contract) != selected_target:
            raise ValidationError(
                f"{field} contains a contract for a foreign capability target"
            )


@dataclass(frozen=True, slots=True)
class PersistentDeduplicationContractAdmissionAttribution(
    _CanonicalDeduplicationRecord
):
    SCHEMA: ClassVar[str] = (
        "irr.persistent_deduplication_contract_admission_attribution.v1"
    )

    resolver_ref: StableRef
    admission_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.resolver_ref) is not StableRef:
            raise ValidationError(
                "PersistentDeduplicationContractAdmissionAttribution.resolver_ref "
                "must be a StableRef"
            )
        if type(self.admission_event_ref) is not StableRef:
            raise ValidationError(
                "PersistentDeduplicationContractAdmissionAttribution."
                "admission_event_ref must be a StableRef"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_event_ref": self.admission_event_ref.to_primitive(),
            "resolver_ref": self.resolver_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "PersistentDeduplicationContractAdmissionAttribution",
    ) -> PersistentDeduplicationContractAdmissionAttribution:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "resolver_ref", "admission_event_ref"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                resolver_ref=StableRef.from_primitive(
                    obj["resolver_ref"],
                    field=f"{field}.resolver_ref",
                ),
                admission_event_ref=StableRef.from_primitive(
                    obj["admission_event_ref"],
                    field=f"{field}.admission_event_ref",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> PersistentDeduplicationContractAdmissionAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class AdmittedPersistentDeduplicationContract(_CanonicalDeduplicationRecord):
    """Explicit admission of one exact downstream persistent deduplication contract."""

    SCHEMA: ClassVar[str] = "irr.admitted_persistent_deduplication_contract.v1"

    admission_attribution: PersistentDeduplicationContractAdmissionAttribution
    contract: PersistentDeduplicatedReinvocationContract
    candidate_inputs: tuple[CandidatePersistentDeduplicationContract, ...]

    def __post_init__(self) -> None:
        if (
            type(self.admission_attribution)
            is not PersistentDeduplicationContractAdmissionAttribution
        ):
            raise ValidationError(
                "AdmittedPersistentDeduplicationContract.admission_attribution "
                "must be PersistentDeduplicationContractAdmissionAttribution"
            )
        if type(self.contract) is not PersistentDeduplicatedReinvocationContract:
            raise ValidationError(
                "AdmittedPersistentDeduplicationContract.contract must be "
                "PersistentDeduplicatedReinvocationContract"
            )
        candidates = _normalize_candidates(
            self.candidate_inputs,
            field="AdmittedPersistentDeduplicationContract.candidate_inputs",
        )
        if not candidates:
            raise ValidationError(
                "AdmittedPersistentDeduplicationContract requires explicit "
                "candidate provenance"
            )
        _validate_candidate_targets(
            candidates,
            selected_contract=self.contract,
            field="AdmittedPersistentDeduplicationContract.candidate_inputs",
        )
        if self.contract.identity not in {
            candidate.contract.identity for candidate in candidates
        }:
            raise ValidationError(
                "admitted persistent deduplication contract must equal one exact "
                "proposed downstream contract"
            )
        protected_events = {
            *(
                candidate.contract.attribution.contract_event_ref
                for candidate in candidates
            ),
            *(candidate.attribution.proposal_event_ref for candidate in candidates),
        }
        if self.admission_attribution.admission_event_ref in protected_events:
            raise ValidationError(
                "persistent deduplication admission occurrence must differ from "
                "contract and proposal occurrences"
            )
        object.__setattr__(self, "candidate_inputs", candidates)

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_attribution": self.admission_attribution.to_primitive(),
            "candidate_inputs": [item.to_primitive() for item in self.candidate_inputs],
            "contract": self.contract.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "AdmittedPersistentDeduplicationContract",
    ) -> AdmittedPersistentDeduplicationContract:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "admission_attribution", "contract", "candidate_inputs"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        candidates = _expect_array(
            obj["candidate_inputs"],
            field=f"{field}.candidate_inputs",
        )
        try:
            return cls(
                admission_attribution=(
                    PersistentDeduplicationContractAdmissionAttribution.from_primitive(
                        obj["admission_attribution"],
                        field=f"{field}.admission_attribution",
                    )
                ),
                contract=PersistentDeduplicatedReinvocationContract.from_primitive(
                    obj["contract"],
                    field=f"{field}.contract",
                ),
                candidate_inputs=tuple(
                    CandidatePersistentDeduplicationContract.from_primitive(
                        item,
                        field=f"{field}.candidate_inputs[{index}]",
                    )
                    for index, item in enumerate(candidates)
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls,
        data: bytes | bytearray | memoryview,
    ) -> AdmittedPersistentDeduplicationContract:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityIdempotencyKey(_CanonicalDeduplicationRecord):
    """Stable key for one original Attempt under one admitted persistent contract."""

    SCHEMA: ClassVar[str] = "irr.capability_idempotency_key.v1"

    admitted_contract_identity: RecordIdentity
    original_attempt_identity: RecordIdentity
    deduplication_domain_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.admitted_contract_identity) is not RecordIdentity:
            raise ValidationError(
                "CapabilityIdempotencyKey.admitted_contract_identity "
                "must be a RecordIdentity"
            )
        if type(self.original_attempt_identity) is not RecordIdentity:
            raise ValidationError(
                "CapabilityIdempotencyKey.original_attempt_identity "
                "must be a RecordIdentity"
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
            "admitted_contract_identity": (
                self.admitted_contract_identity.to_primitive()
            ),
            "deduplication_domain_ref": self.deduplication_domain_ref.to_primitive(),
            "original_attempt_identity": self.original_attempt_identity.to_primitive(),
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
                "admitted_contract_identity",
                "original_attempt_identity",
                "deduplication_domain_ref",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                admitted_contract_identity=RecordIdentity.from_primitive(
                    obj["admitted_contract_identity"],
                    field=f"{field}.admitted_contract_identity",
                ),
                original_attempt_identity=RecordIdentity.from_primitive(
                    obj["original_attempt_identity"],
                    field=f"{field}.original_attempt_identity",
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


def _validate_admitted_contract_for_attempt(
    admitted_contract: AdmittedPersistentDeduplicationContract,
    attempt: CapabilityAttempt,
) -> None:
    contract = admitted_contract.contract
    match = evaluate_capability_match_evaluation(attempt.capability_evaluation)
    if type(match) is not CapabilityMatch:
        raise AssertionError(
            "validated CapabilityAttempt lost its exact CapabilityMatch"
        )

    if contract.catalog_snapshot_identity != match.catalog_snapshot.identity:
        raise DeduplicatedReinvocationContractError(
            "persistent deduplication contract catalog snapshot does not match "
            "the exact CapabilityAttempt"
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


def derive_capability_idempotency_key(
    admitted_contract: AdmittedPersistentDeduplicationContract,
    attempt: CapabilityAttempt,
) -> CapabilityIdempotencyKey:
    """Derive original-dispatch key only from exact admitted contract lineage."""

    if type(admitted_contract) is not AdmittedPersistentDeduplicationContract:
        raise ValidationError(
            "admitted_contract must be an AdmittedPersistentDeduplicationContract"
        )
    if type(attempt) is not CapabilityAttempt:
        raise ValidationError("attempt must be a CapabilityAttempt")

    _validate_admitted_contract_for_attempt(admitted_contract, attempt)
    return CapabilityIdempotencyKey(
        admitted_contract_identity=admitted_contract.identity,
        original_attempt_identity=attempt.identity,
        deduplication_domain_ref=admitted_contract.contract.deduplication_domain_ref,
    )


@dataclass(frozen=True, slots=True)
class DeduplicatedCapabilityInvocationRequest:
    """First-dispatch mechanism state carrying one exact persistent key.

    This request is not canonical IR and grants no retry authority. A later recovery
    Attempt must not independently derive a replacement key; future recovery semantics
    must explicitly reference the original key transported by this first dispatch.
    """

    attempt: CapabilityAttempt
    admitted_contract: AdmittedPersistentDeduplicationContract
    idempotency_key: CapabilityIdempotencyKey

    def __post_init__(self) -> None:
        if type(self.attempt) is not CapabilityAttempt:
            raise ValidationError(
                "DeduplicatedCapabilityInvocationRequest.attempt "
                "must be a CapabilityAttempt"
            )
        if type(self.admitted_contract) is not AdmittedPersistentDeduplicationContract:
            raise ValidationError(
                "DeduplicatedCapabilityInvocationRequest.admitted_contract must be "
                "an AdmittedPersistentDeduplicationContract"
            )
        if type(self.idempotency_key) is not CapabilityIdempotencyKey:
            raise ValidationError(
                "DeduplicatedCapabilityInvocationRequest.idempotency_key "
                "must be a CapabilityIdempotencyKey"
            )
        expected = derive_capability_idempotency_key(
            self.admitted_contract,
            self.attempt,
        )
        if self.idempotency_key != expected:
            raise DeduplicatedReinvocationContractError(
                "deduplicated invocation request must carry the exact key derived "
                "from its original Attempt and admitted persistent contract"
            )


def build_deduplicated_capability_invocation_request(
    admitted_contract: AdmittedPersistentDeduplicationContract,
    attempt: CapabilityAttempt,
) -> DeduplicatedCapabilityInvocationRequest:
    """Build first-dispatch mechanism state carrying the admitted persistent key."""

    key = derive_capability_idempotency_key(admitted_contract, attempt)
    return DeduplicatedCapabilityInvocationRequest(
        attempt=attempt,
        admitted_contract=admitted_contract,
        idempotency_key=key,
    )


__all__ = (
    "AdmittedPersistentDeduplicationContract",
    "CandidatePersistentDeduplicationContract",
    "CapabilityIdempotencyKey",
    "DeduplicatedCapabilityInvocationRequest",
    "DeduplicatedReinvocationContractError",
    "PersistentDeduplicatedReinvocationContract",
    "PersistentDeduplicationContractAdmissionAttribution",
    "PersistentDeduplicationContractAttribution",
    "PersistentDeduplicationContractProposalAttribution",
    "build_deduplicated_capability_invocation_request",
    "derive_capability_idempotency_key",
)
