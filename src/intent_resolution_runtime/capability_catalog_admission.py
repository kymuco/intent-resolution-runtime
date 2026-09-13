from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, TypeAlias, cast

from .canonical import canonical_json_bytes, parse_json_object
from .capability import CapabilityCatalogSnapshot
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef


def _expect_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SerializationError(f"{field} must be a JSON object")
    return value


def _expect_array(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise SerializationError(f"{field} must be a JSON array")
    return value


def _expect_exact_keys(
    value: dict[str, Any], expected: set[str], *, field: str
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


def _reject_surrogates(value: str, *, field: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValidationError(f"{field} must contain only Unicode scalar values")


def _require_text(value: object, *, field: str) -> str:
    if type(value) is not str:
        raise ValidationError(f"{field} must be a string")
    _reject_surrogates(value, field=field)
    if not value.strip():
        raise ValidationError(f"{field} must contain non-whitespace text")
    return value


class _CanonicalCapabilityCatalogAdmissionRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class CapabilityCatalogSnapshotProposalAttribution(
    _CanonicalCapabilityCatalogAdmissionRecord
):
    SCHEMA: ClassVar[str] = "irr.capability_catalog_snapshot_proposal_attribution.v1"

    proposer_ref: StableRef
    proposal_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.proposer_ref) is not StableRef:
            raise ValidationError(
                "CapabilityCatalogSnapshotProposalAttribution.proposer_ref must be a "
                "StableRef"
            )
        if type(self.proposal_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityCatalogSnapshotProposalAttribution.proposal_event_ref "
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
        field: str = "CapabilityCatalogSnapshotProposalAttribution",
    ) -> CapabilityCatalogSnapshotProposalAttribution:
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
                    obj["proposer_ref"], field=f"{field}.proposer_ref"
                ),
                proposal_event_ref=StableRef.from_primitive(
                    obj["proposal_event_ref"], field=f"{field}.proposal_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> CapabilityCatalogSnapshotProposalAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CapabilityCatalogSnapshotAdmissionAttribution(
    _CanonicalCapabilityCatalogAdmissionRecord
):
    SCHEMA: ClassVar[str] = "irr.capability_catalog_snapshot_admission_attribution.v1"

    resolver_ref: StableRef
    admission_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.resolver_ref) is not StableRef:
            raise ValidationError(
                "CapabilityCatalogSnapshotAdmissionAttribution.resolver_ref must be a "
                "StableRef"
            )
        if type(self.admission_event_ref) is not StableRef:
            raise ValidationError(
                "CapabilityCatalogSnapshotAdmissionAttribution.admission_event_ref "
                "must be a StableRef"
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
        field: str = "CapabilityCatalogSnapshotAdmissionAttribution",
    ) -> CapabilityCatalogSnapshotAdmissionAttribution:
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
                    obj["resolver_ref"], field=f"{field}.resolver_ref"
                ),
                admission_event_ref=StableRef.from_primitive(
                    obj["admission_event_ref"], field=f"{field}.admission_event_ref"
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> CapabilityCatalogSnapshotAdmissionAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CandidateCapabilityCatalogSnapshot(_CanonicalCapabilityCatalogAdmissionRecord):
    """Proposed bounded capability candidate domain; never active matching state."""

    SCHEMA: ClassVar[str] = "irr.candidate_capability_catalog_snapshot.v1"

    attribution: CapabilityCatalogSnapshotProposalAttribution
    snapshot: CapabilityCatalogSnapshot
    rationale: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not CapabilityCatalogSnapshotProposalAttribution:
            raise ValidationError(
                "CandidateCapabilityCatalogSnapshot.attribution must be a "
                "CapabilityCatalogSnapshotProposalAttribution"
            )
        if type(self.snapshot) is not CapabilityCatalogSnapshot:
            raise ValidationError(
                "CandidateCapabilityCatalogSnapshot.snapshot must be a "
                "CapabilityCatalogSnapshot"
            )
        _require_text(
            self.rationale, field="CandidateCapabilityCatalogSnapshot.rationale"
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "rationale": self.rationale,
            "schema": self.SCHEMA,
            "snapshot": self.snapshot.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "CandidateCapabilityCatalogSnapshot"
    ) -> CandidateCapabilityCatalogSnapshot:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "attribution", "snapshot", "rationale"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                attribution=CapabilityCatalogSnapshotProposalAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                snapshot=CapabilityCatalogSnapshot.from_primitive(
                    obj["snapshot"], field=f"{field}.snapshot"
                ),
                rationale=obj["rationale"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> CandidateCapabilityCatalogSnapshot:
        return cls.from_primitive(parse_json_object(data))


def _normalize_candidates(
    value: object, *, field: str
) -> tuple[CandidateCapabilityCatalogSnapshot, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CandidateCapabilityCatalogSnapshot for item in value):
        raise ValidationError(
            f"{field} must contain CandidateCapabilityCatalogSnapshot values"
        )
    candidates = cast(tuple[CandidateCapabilityCatalogSnapshot, ...], value)
    identities = [candidate.identity for candidate in candidates]
    if len(set(identities)) != len(identities):
        raise ValidationError(
            f"{field} must not contain duplicate candidate identities"
        )
    return tuple(sorted(candidates, key=lambda candidate: str(candidate.identity)))


@dataclass(frozen=True, slots=True)
class AdmittedCapabilityCatalogSnapshot(_CanonicalCapabilityCatalogAdmissionRecord):
    """Explicit admission of one exact bounded catalog; never capability selection."""

    SCHEMA: ClassVar[str] = "irr.admitted_capability_catalog_snapshot.v1"

    admission_attribution: CapabilityCatalogSnapshotAdmissionAttribution
    snapshot: CapabilityCatalogSnapshot
    candidate_inputs: tuple[CandidateCapabilityCatalogSnapshot, ...] = ()

    def __post_init__(self) -> None:
        if (
            type(self.admission_attribution)
            is not CapabilityCatalogSnapshotAdmissionAttribution
        ):
            raise ValidationError(
                "AdmittedCapabilityCatalogSnapshot.admission_attribution must be a "
                "CapabilityCatalogSnapshotAdmissionAttribution"
            )
        if type(self.snapshot) is not CapabilityCatalogSnapshot:
            raise ValidationError(
                "AdmittedCapabilityCatalogSnapshot.snapshot must be a "
                "CapabilityCatalogSnapshot"
            )
        object.__setattr__(
            self,
            "candidate_inputs",
            _normalize_candidates(
                self.candidate_inputs,
                field="AdmittedCapabilityCatalogSnapshot.candidate_inputs",
            ),
        )

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_attribution": self.admission_attribution.to_primitive(),
            "candidate_inputs": [item.to_primitive() for item in self.candidate_inputs],
            "schema": self.SCHEMA,
            "snapshot": self.snapshot.to_primitive(),
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "AdmittedCapabilityCatalogSnapshot"
    ) -> AdmittedCapabilityCatalogSnapshot:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "admission_attribution", "snapshot", "candidate_inputs"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        candidates = _expect_array(
            obj["candidate_inputs"], field=f"{field}.candidate_inputs"
        )
        try:
            return cls(
                admission_attribution=(
                    CapabilityCatalogSnapshotAdmissionAttribution.from_primitive(
                        obj["admission_attribution"],
                        field=f"{field}.admission_attribution",
                    )
                ),
                snapshot=CapabilityCatalogSnapshot.from_primitive(
                    obj["snapshot"], field=f"{field}.snapshot"
                ),
                candidate_inputs=tuple(
                    CandidateCapabilityCatalogSnapshot.from_primitive(
                        item, field=f"{field}.candidate_inputs[{index}]"
                    )
                    for index, item in enumerate(candidates)
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> AdmittedCapabilityCatalogSnapshot:
        return cls.from_primitive(parse_json_object(data))


class CapabilityCatalogSnapshotAdmissionFrontierKind(StrEnum):
    PROPOSAL_INPUT_REQUIRED = "proposal_input_required"
    ADMISSION_REQUIRED = "admission_required"
    ADJUDICATION_REQUIRED = "adjudication_required"
    CATALOG_OUTPUT_AVAILABLE = "catalog_output_available"


@dataclass(frozen=True, slots=True)
class CapabilityCatalogSnapshotAdmissionFrontier:
    """Derived admission state for one exact bounded capability catalog snapshot."""

    candidate_inputs: tuple[CandidateCapabilityCatalogSnapshot, ...]
    kind: CapabilityCatalogSnapshotAdmissionFrontierKind
    admitted_catalog: AdmittedCapabilityCatalogSnapshot | None = None

    def __post_init__(self) -> None:
        candidates = _normalize_candidates(
            self.candidate_inputs,
            field="CapabilityCatalogSnapshotAdmissionFrontier.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)
        if type(self.kind) is not CapabilityCatalogSnapshotAdmissionFrontierKind:
            raise ValidationError(
                "CapabilityCatalogSnapshotAdmissionFrontier.kind must be a "
                "CapabilityCatalogSnapshotAdmissionFrontierKind"
            )

        output = self.admitted_catalog
        if (
            self.kind
            is CapabilityCatalogSnapshotAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
        ):
            if candidates or output is not None:
                raise ValidationError(
                    "proposal_input_required frontier cannot contain candidates or "
                    "output"
                )
            return

        if self.kind in (
            CapabilityCatalogSnapshotAdmissionFrontierKind.ADMISSION_REQUIRED,
            CapabilityCatalogSnapshotAdmissionFrontierKind.ADJUDICATION_REQUIRED,
        ):
            if not candidates:
                raise ValidationError(
                    f"{self.kind.value} frontier requires explicit candidate material"
                )
            if output is not None:
                raise ValidationError(
                    f"{self.kind.value} frontier cannot contain admitted output"
                )
            expected_kind = _unresolved_kind(candidates)
            if self.kind is not expected_kind:
                raise ValidationError(
                    "unresolved catalog frontier kind must match exact candidate "
                    "semantics"
                )
            return

        if (
            self.kind
            is CapabilityCatalogSnapshotAdmissionFrontierKind.CATALOG_OUTPUT_AVAILABLE
        ):
            if type(output) is not AdmittedCapabilityCatalogSnapshot:
                raise ValidationError(
                    "catalog_output_available requires "
                    "AdmittedCapabilityCatalogSnapshot"
                )
            if output.candidate_inputs != candidates:
                raise ValidationError(
                    "catalog_output_available candidate_inputs must equal exact "
                    "output provenance"
                )
            return

        raise AssertionError(
            "unsupported CapabilityCatalogSnapshotAdmissionFrontierKind"
        )


CapabilityCatalogSnapshotAdmitter: TypeAlias = Callable[
    [
        tuple[CandidateCapabilityCatalogSnapshot, ...],
        CapabilityCatalogSnapshotAdmissionAttribution,
    ],
    AdmittedCapabilityCatalogSnapshot | None,
]


def _unresolved_kind(
    candidates: tuple[CandidateCapabilityCatalogSnapshot, ...],
) -> CapabilityCatalogSnapshotAdmissionFrontierKind:
    if not candidates:
        return CapabilityCatalogSnapshotAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
    semantic_identities = {candidate.snapshot.identity for candidate in candidates}
    if len(semantic_identities) == 1:
        return CapabilityCatalogSnapshotAdmissionFrontierKind.ADMISSION_REQUIRED
    return CapabilityCatalogSnapshotAdmissionFrontierKind.ADJUDICATION_REQUIRED


def orchestrate_capability_catalog_snapshot_admission(
    *,
    candidate_inputs: tuple[CandidateCapabilityCatalogSnapshot, ...] = (),
    admitted_outputs: tuple[AdmittedCapabilityCatalogSnapshot, ...] = (),
    admitter: CapabilityCatalogSnapshotAdmitter | None = None,
    admission_attribution: CapabilityCatalogSnapshotAdmissionAttribution | None = None,
) -> CapabilityCatalogSnapshotAdmissionFrontier:
    """Derive or explicitly advance one bounded catalog-snapshot admission frontier.

    Proposal provenance never votes. Catalog construction is not admission. The explicit
    admitter may adjudicate or synthesize one exact snapshot, but the resulting record
    preserves the complete supplied candidate set. Admission does not imply live
    availability, global completeness, capability selection, Governance, Authorization,
    Attempt, or execution.
    """

    candidates = _normalize_candidates(candidate_inputs, field="candidate_inputs")

    if type(admitted_outputs) is not tuple:
        raise ValidationError("admitted_outputs must be a tuple")
    if not all(
        type(item) is AdmittedCapabilityCatalogSnapshot for item in admitted_outputs
    ):
        raise ValidationError(
            "admitted_outputs must contain AdmittedCapabilityCatalogSnapshot values"
        )
    outputs = cast(tuple[AdmittedCapabilityCatalogSnapshot, ...], admitted_outputs)
    if len(outputs) > 1:
        raise ValidationError(
            "competing admitted capability catalog snapshots fail closed"
        )

    if outputs:
        output = outputs[0]
        if admitter is not None or admission_attribution is not None:
            raise ValidationError(
                "admitted-output replay cannot also invoke a new catalog admitter"
            )
        admitted_candidate_identities = {
            candidate.identity for candidate in output.candidate_inputs
        }
        supplied_candidate_identities = {candidate.identity for candidate in candidates}
        if not supplied_candidate_identities.issubset(admitted_candidate_identities):
            raise ValidationError(
                "candidate material outside admitted catalog provenance is orphaned"
            )
        return CapabilityCatalogSnapshotAdmissionFrontier(
            candidate_inputs=output.candidate_inputs,
            kind=(
                CapabilityCatalogSnapshotAdmissionFrontierKind.CATALOG_OUTPUT_AVAILABLE
            ),
            admitted_catalog=output,
        )

    unresolved = CapabilityCatalogSnapshotAdmissionFrontier(
        candidate_inputs=candidates,
        kind=_unresolved_kind(candidates),
    )
    if admitter is None:
        if admission_attribution is not None:
            raise ValidationError(
                "admission_attribution requires an explicit catalog admitter"
            )
        return unresolved
    if not callable(admitter):
        raise ValidationError("admitter must be callable")
    if type(admission_attribution) is not CapabilityCatalogSnapshotAdmissionAttribution:
        raise ValidationError(
            "explicit admission requires CapabilityCatalogSnapshotAdmissionAttribution"
        )

    admitted = admitter(candidates, admission_attribution)
    if admitted is None:
        return unresolved
    if type(admitted) is not AdmittedCapabilityCatalogSnapshot:
        raise ValidationError(
            "catalog admitter must return AdmittedCapabilityCatalogSnapshot or None"
        )
    if admitted.admission_attribution != admission_attribution:
        raise ValidationError(
            "catalog admitter changed the exact admission attribution"
        )
    if admitted.candidate_inputs != candidates:
        raise ValidationError("catalog admitter must preserve the exact candidate set")

    return CapabilityCatalogSnapshotAdmissionFrontier(
        candidate_inputs=candidates,
        kind=CapabilityCatalogSnapshotAdmissionFrontierKind.CATALOG_OUTPUT_AVAILABLE,
        admitted_catalog=admitted,
    )


__all__ = (
    "AdmittedCapabilityCatalogSnapshot",
    "CandidateCapabilityCatalogSnapshot",
    "CapabilityCatalogSnapshotAdmissionAttribution",
    "CapabilityCatalogSnapshotAdmissionFrontier",
    "CapabilityCatalogSnapshotAdmissionFrontierKind",
    "CapabilityCatalogSnapshotProposalAttribution",
    "orchestrate_capability_catalog_snapshot_admission",
)
