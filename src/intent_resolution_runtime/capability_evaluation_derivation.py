from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from .canonical import canonical_json_bytes, parse_json_object
from .capability_catalog_admission import AdmittedCapabilityCatalogSnapshot
from .capability_match_engine import build_capability_match_evaluation
from .capability_match_evaluation import CapabilityMatchEvaluation
from .capability_requirement_admission import AdmittedCapabilityRequirement
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef


def _expect_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SerializationError(f"{field} must be a JSON object")
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


class _CanonicalCapabilityEvaluationDerivationRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class MechanicallyDerivedCapabilityMatchEvaluation(
    _CanonicalCapabilityEvaluationDerivationRecord
):
    """Exact deterministic match evaluation bound to exact admitted inputs.

    This record carries no semantic admission, capability-selection, Governance,
    Authorization, or execution authority. Its only claim is that ``evaluation`` is
    exactly reproducible by the frozen IRR mechanical match engine from the exact
    admitted requirement and catalog snapshot recorded here.
    """

    SCHEMA: ClassVar[str] = "irr.mechanically_derived_capability_match_evaluation.v1"

    admitted_requirement: AdmittedCapabilityRequirement
    admitted_catalog: AdmittedCapabilityCatalogSnapshot
    evaluation: CapabilityMatchEvaluation

    def __post_init__(self) -> None:
        if type(self.admitted_requirement) is not AdmittedCapabilityRequirement:
            raise ValidationError(
                "MechanicallyDerivedCapabilityMatchEvaluation.admitted_requirement "
                "must be an AdmittedCapabilityRequirement"
            )
        if type(self.admitted_catalog) is not AdmittedCapabilityCatalogSnapshot:
            raise ValidationError(
                "MechanicallyDerivedCapabilityMatchEvaluation.admitted_catalog must "
                "be an AdmittedCapabilityCatalogSnapshot"
            )
        if type(self.evaluation) is not CapabilityMatchEvaluation:
            raise ValidationError(
                "MechanicallyDerivedCapabilityMatchEvaluation.evaluation must be a "
                "CapabilityMatchEvaluation"
            )
        if self.evaluation.requirement != self.admitted_requirement.requirement:
            raise ValidationError(
                "mechanically derived evaluation must preserve the exact admitted "
                "CapabilityRequirement"
            )
        if self.evaluation.catalog_snapshot != self.admitted_catalog.snapshot:
            raise ValidationError(
                "mechanically derived evaluation must preserve the exact admitted "
                "CapabilityCatalogSnapshot"
            )

        expected = build_capability_match_evaluation(
            self.admitted_requirement.requirement,
            self.admitted_catalog.snapshot,
            evaluation_event_ref=self.evaluation.attribution.evaluation_event_ref,
        )
        if self.evaluation != expected:
            raise ValidationError(
                "mechanically derived evaluation must exactly equal the deterministic "
                "IRR capability match derivation"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "admitted_catalog": self.admitted_catalog.to_primitive(),
            "admitted_requirement": self.admitted_requirement.to_primitive(),
            "evaluation": self.evaluation.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls,
        value: object,
        *,
        field: str = "MechanicallyDerivedCapabilityMatchEvaluation",
    ) -> MechanicallyDerivedCapabilityMatchEvaluation:
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "admitted_requirement", "admitted_catalog", "evaluation"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                admitted_requirement=AdmittedCapabilityRequirement.from_primitive(
                    obj["admitted_requirement"],
                    field=f"{field}.admitted_requirement",
                ),
                admitted_catalog=AdmittedCapabilityCatalogSnapshot.from_primitive(
                    obj["admitted_catalog"],
                    field=f"{field}.admitted_catalog",
                ),
                evaluation=CapabilityMatchEvaluation.from_primitive(
                    obj["evaluation"],
                    field=f"{field}.evaluation",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> MechanicallyDerivedCapabilityMatchEvaluation:
        return cls.from_primitive(parse_json_object(data))


def derive_mechanical_capability_match_evaluation(
    admitted_requirement: AdmittedCapabilityRequirement,
    admitted_catalog: AdmittedCapabilityCatalogSnapshot,
    *,
    evaluation_event_ref: StableRef,
) -> MechanicallyDerivedCapabilityMatchEvaluation:
    """Derive one exhaustive evaluation from exact admitted semantic inputs.

    There is intentionally no admitter, provider proposal, ranking, adjudication, or
    selection callback here. Once the requirement and catalog domain are admitted,
    exact-structural-v1 evaluation is a deterministic IRR derivation.
    """

    if type(admitted_requirement) is not AdmittedCapabilityRequirement:
        raise ValidationError(
            "derive_mechanical_capability_match_evaluation.admitted_requirement must "
            "be an AdmittedCapabilityRequirement"
        )
    if type(admitted_catalog) is not AdmittedCapabilityCatalogSnapshot:
        raise ValidationError(
            "derive_mechanical_capability_match_evaluation.admitted_catalog must be "
            "an AdmittedCapabilityCatalogSnapshot"
        )
    if type(evaluation_event_ref) is not StableRef:
        raise ValidationError(
            "derive_mechanical_capability_match_evaluation.evaluation_event_ref must "
            "be a StableRef"
        )

    evaluation = build_capability_match_evaluation(
        admitted_requirement.requirement,
        admitted_catalog.snapshot,
        evaluation_event_ref=evaluation_event_ref,
    )
    return MechanicallyDerivedCapabilityMatchEvaluation(
        admitted_requirement=admitted_requirement,
        admitted_catalog=admitted_catalog,
        evaluation=evaluation,
    )


__all__ = (
    "MechanicallyDerivedCapabilityMatchEvaluation",
    "derive_mechanical_capability_match_evaluation",
)
