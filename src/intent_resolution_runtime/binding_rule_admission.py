from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, TypeAlias

from .binding import BindingRule, SymbolicReference
from .canonical import canonical_json_bytes, parse_json_object
from .errors import SerializationError, ValidationError
from .intent import StableRef


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


class _CanonicalBindingRuleAdmissionRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self):
        from .identity import identity_for_bytes

        return identity_for_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class BindingRuleProposalAttribution(_CanonicalBindingRuleAdmissionRecord):
    SCHEMA: ClassVar[str] = "irr.binding_rule_proposal_attribution.v1"

    proposer_ref: StableRef
    proposal_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.proposer_ref) is not StableRef:
            raise ValidationError(
                "BindingRuleProposalAttribution.proposer_ref must be a StableRef"
            )
        if type(self.proposal_event_ref) is not StableRef:
            raise ValidationError(
                "BindingRuleProposalAttribution.proposal_event_ref must be a StableRef"
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
        field: str = "BindingRuleProposalAttribution",
    ) -> BindingRuleProposalAttribution:
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
    ) -> BindingRuleProposalAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class BindingRuleAdmissionAttribution(_CanonicalBindingRuleAdmissionRecord):
    SCHEMA: ClassVar[str] = "irr.binding_rule_admission_attribution.v1"

    resolver_ref: StableRef
    admission_event_ref: StableRef

    def __post_init__(self) -> None:
        if type(self.resolver_ref) is not StableRef:
            raise ValidationError(
                "BindingRuleAdmissionAttribution.resolver_ref must be a StableRef"
            )
        if type(self.admission_event_ref) is not StableRef:
            raise ValidationError(
                "BindingRuleAdmissionAttribution.admission_event_ref must be a StableRef"
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
        field: str = "BindingRuleAdmissionAttribution",
    ) -> BindingRuleAdmissionAttribution:
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
    ) -> BindingRuleAdmissionAttribution:
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class CandidateBindingRule(_CanonicalBindingRuleAdmissionRecord):
    """Proposed rule semantics for one exact symbolic slot; not an active rule."""

    SCHEMA: ClassVar[str] = "irr.candidate_binding_rule.v1"

    attribution: BindingRuleProposalAttribution
    rule: BindingRule
    rationale: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not BindingRuleProposalAttribution:
            raise ValidationError(
                "CandidateBindingRule.attribution must be a BindingRuleProposalAttribution"
            )
        if type(self.rule) is not BindingRule:
            raise ValidationError("CandidateBindingRule.rule must be an exact BindingRule")
        _require_text(self.rationale, field="CandidateBindingRule.rationale")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "rationale": self.rationale,
            "rule": self.rule.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(cls, value: object) -> CandidateBindingRule:
        obj = _expect_object(value, field="CandidateBindingRule")
        _expect_exact_keys(
            obj,
            {"schema", "attribution", "rule", "rationale"},
            field="CandidateBindingRule",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported CandidateBindingRule schema: {obj['schema']!r}"
            )
        try:
            return cls(
                attribution=BindingRuleProposalAttribution.from_primitive(
                    obj["attribution"], field="CandidateBindingRule.attribution"
                ),
                rule=BindingRule.from_primitive(obj["rule"]),
                rationale=obj["rationale"],
            )
        except ValidationError as exc:
            raise SerializationError("invalid CandidateBindingRule") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> CandidateBindingRule:
        return cls.from_primitive(parse_json_object(data))


def _normalize_candidates(
    value: object, *, field: str
) -> tuple[CandidateBindingRule, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is CandidateBindingRule for item in value):
        raise ValidationError(f"{field} must contain CandidateBindingRule values")
    candidates = tuple(value)
    identities = [candidate.identity for candidate in candidates]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate candidate identities")
    return tuple(sorted(candidates, key=lambda candidate: str(candidate.identity)))


def _validate_candidates_target(
    candidates: tuple[CandidateBindingRule, ...],
    *,
    symbolic_reference: SymbolicReference,
    field: str,
) -> None:
    for candidate in candidates:
        if candidate.rule.symbolic_reference != symbolic_reference:
            raise ValidationError(f"{field} contains a foreign symbolic-reference target")
        if (
            candidate.rule.resolved_intent_identity
            != symbolic_reference.resolved_intent_identity
        ):
            raise ValidationError(f"{field} contains a foreign ResolvedIntent lineage")


@dataclass(frozen=True, slots=True)
class AdmittedBindingRule(_CanonicalBindingRuleAdmissionRecord):
    """IRR admission of one exact BindingRule; not input acquisition or Authorization."""

    SCHEMA: ClassVar[str] = "irr.admitted_binding_rule.v1"

    admission_attribution: BindingRuleAdmissionAttribution
    rule: BindingRule
    candidate_inputs: tuple[CandidateBindingRule, ...] = ()

    def __post_init__(self) -> None:
        if type(self.admission_attribution) is not BindingRuleAdmissionAttribution:
            raise ValidationError(
                "AdmittedBindingRule.admission_attribution must be a "
                "BindingRuleAdmissionAttribution"
            )
        if type(self.rule) is not BindingRule:
            raise ValidationError("AdmittedBindingRule.rule must be an exact BindingRule")
        candidates = _normalize_candidates(
            self.candidate_inputs, field="AdmittedBindingRule.candidate_inputs"
        )
        _validate_candidates_target(
            candidates,
            symbolic_reference=self.rule.symbolic_reference,
            field="AdmittedBindingRule.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)

    def to_primitive(self) -> dict[str, object]:
        return {
            "admission_attribution": self.admission_attribution.to_primitive(),
            "candidate_inputs": [item.to_primitive() for item in self.candidate_inputs],
            "rule": self.rule.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(cls, value: object) -> AdmittedBindingRule:
        obj = _expect_object(value, field="AdmittedBindingRule")
        _expect_exact_keys(
            obj,
            {"schema", "admission_attribution", "rule", "candidate_inputs"},
            field="AdmittedBindingRule",
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(
                f"unsupported AdmittedBindingRule schema: {obj['schema']!r}"
            )
        candidates = _expect_array(
            obj["candidate_inputs"], field="AdmittedBindingRule.candidate_inputs"
        )
        try:
            return cls(
                admission_attribution=BindingRuleAdmissionAttribution.from_primitive(
                    obj["admission_attribution"],
                    field="AdmittedBindingRule.admission_attribution",
                ),
                rule=BindingRule.from_primitive(obj["rule"]),
                candidate_inputs=tuple(
                    CandidateBindingRule.from_primitive(item) for item in candidates
                ),
            )
        except ValidationError as exc:
            raise SerializationError("invalid AdmittedBindingRule") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> AdmittedBindingRule:
        return cls.from_primitive(parse_json_object(data))


BindingRuleAdmitter: TypeAlias = Callable[
    [
        SymbolicReference,
        tuple[CandidateBindingRule, ...],
        BindingRuleAdmissionAttribution,
    ],
    AdmittedBindingRule | None,
]


def _normalize_outputs(
    value: object, *, field: str
) -> tuple[AdmittedBindingRule, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is AdmittedBindingRule for item in value):
        raise ValidationError(f"{field} must contain AdmittedBindingRule values")
    outputs = tuple(value)
    identities = [output.identity for output in outputs]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate output identities")
    return tuple(sorted(outputs, key=lambda output: str(output.identity)))


def _validate_output_target(
    output: object,
    *,
    symbolic_reference: SymbolicReference,
    field: str,
) -> AdmittedBindingRule:
    if type(output) is not AdmittedBindingRule:
        raise ValidationError(f"{field} must be an exact AdmittedBindingRule")
    admitted = output
    if admitted.rule.symbolic_reference != symbolic_reference:
        raise ValidationError(f"{field} belongs to a foreign symbolic-reference target")
    if (
        admitted.rule.resolved_intent_identity
        != symbolic_reference.resolved_intent_identity
    ):
        raise ValidationError(f"{field} belongs to a foreign ResolvedIntent lineage")
    return admitted


def _candidate_semantic_signature(candidate: CandidateBindingRule) -> BindingRule:
    """Proposal attribution and rationale are provenance/explanation, not precedence."""

    return candidate.rule


def _candidates_are_semantically_equivalent(
    candidates: tuple[CandidateBindingRule, ...],
) -> bool:
    if not candidates:
        return True
    signature = _candidate_semantic_signature(candidates[0])
    return all(
        _candidate_semantic_signature(candidate) == signature
        for candidate in candidates[1:]
    )


class BindingRuleAdmissionFrontierKind(str, Enum):
    PROPOSAL_INPUT_REQUIRED = "proposal_input_required"
    ADMISSION_REQUIRED = "admission_required"
    ADJUDICATION_REQUIRED = "adjudication_required"
    RULE_OUTPUT_AVAILABLE = "rule_output_available"


@dataclass(frozen=True, slots=True)
class BindingRuleAdmissionFrontier:
    """Derived non-canonical view over one symbolic-reference rule-admission slice."""

    symbolic_reference: SymbolicReference
    kind: BindingRuleAdmissionFrontierKind
    candidate_inputs: tuple[CandidateBindingRule, ...] = ()
    admitted_rule: AdmittedBindingRule | None = None

    def __post_init__(self) -> None:
        if type(self.symbolic_reference) is not SymbolicReference:
            raise ValidationError(
                "BindingRuleAdmissionFrontier.symbolic_reference must be a SymbolicReference"
            )
        if type(self.kind) is not BindingRuleAdmissionFrontierKind:
            raise ValidationError(
                "BindingRuleAdmissionFrontier.kind must be a BindingRuleAdmissionFrontierKind"
            )
        candidates = _normalize_candidates(
            self.candidate_inputs,
            field="BindingRuleAdmissionFrontier.candidate_inputs",
        )
        _validate_candidates_target(
            candidates,
            symbolic_reference=self.symbolic_reference,
            field="BindingRuleAdmissionFrontier.candidate_inputs",
        )
        object.__setattr__(self, "candidate_inputs", candidates)

        output = None
        if self.admitted_rule is not None:
            output = _validate_output_target(
                self.admitted_rule,
                symbolic_reference=self.symbolic_reference,
                field="BindingRuleAdmissionFrontier.admitted_rule",
            )

        if self.kind is BindingRuleAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED:
            if candidates or output is not None:
                raise ValidationError(
                    "proposal_input_required frontier cannot contain candidates or output"
                )
        elif self.kind in (
            BindingRuleAdmissionFrontierKind.ADMISSION_REQUIRED,
            BindingRuleAdmissionFrontierKind.ADJUDICATION_REQUIRED,
        ):
            if not candidates:
                raise ValidationError(
                    f"{self.kind.value} frontier requires explicit candidate material"
                )
            if output is not None:
                raise ValidationError(
                    f"{self.kind.value} frontier cannot contain admitted output"
                )
        elif self.kind is BindingRuleAdmissionFrontierKind.RULE_OUTPUT_AVAILABLE:
            if output is None:
                raise ValidationError(
                    "rule_output_available frontier requires an AdmittedBindingRule"
                )
            if candidates != output.candidate_inputs:
                raise ValidationError(
                    "rule_output_available candidate_inputs must equal exact output provenance"
                )
        else:  # pragma: no cover
            raise AssertionError("unsupported BindingRuleAdmissionFrontierKind")


def _frontier_without_output(
    symbolic_reference: SymbolicReference,
    candidates: tuple[CandidateBindingRule, ...],
) -> BindingRuleAdmissionFrontier:
    if not candidates:
        kind = BindingRuleAdmissionFrontierKind.PROPOSAL_INPUT_REQUIRED
    elif _candidates_are_semantically_equivalent(candidates):
        kind = BindingRuleAdmissionFrontierKind.ADMISSION_REQUIRED
    else:
        kind = BindingRuleAdmissionFrontierKind.ADJUDICATION_REQUIRED
    return BindingRuleAdmissionFrontier(
        symbolic_reference=symbolic_reference,
        kind=kind,
        candidate_inputs=candidates,
    )


def orchestrate_binding_rule_admission(
    symbolic_reference: SymbolicReference,
    *,
    candidate_inputs: tuple[CandidateBindingRule, ...] = (),
    admitted_outputs: tuple[AdmittedBindingRule, ...] = (),
    admitter: BindingRuleAdmitter | None = None,
    admission_attribution: BindingRuleAdmissionAttribution | None = None,
) -> BindingRuleAdmissionFrontier:
    """Derive and, when explicitly delegated, advance one binding-rule admission.

    A CandidateBindingRule never becomes active merely because it is unique, carries
    a valid BindingRule, or was proposed by a trusted source. This function performs
    no BindingInput acquisition, binding evaluation, capability matching, Governance,
    Authorization, execution, retry, fallback, or persistence.
    """

    if type(symbolic_reference) is not SymbolicReference:
        raise ValidationError(
            "orchestrate_binding_rule_admission.symbolic_reference must be a "
            "SymbolicReference"
        )

    candidates = _normalize_candidates(
        candidate_inputs,
        field="orchestrate_binding_rule_admission.candidate_inputs",
    )
    _validate_candidates_target(
        candidates,
        symbolic_reference=symbolic_reference,
        field="orchestrate_binding_rule_admission.candidate_inputs",
    )

    outputs = _normalize_outputs(
        admitted_outputs,
        field="orchestrate_binding_rule_admission.admitted_outputs",
    )
    for output in outputs:
        _validate_output_target(
            output,
            symbolic_reference=symbolic_reference,
            field="orchestrate_binding_rule_admission.admitted_outputs",
        )

    if len(outputs) > 1:
        raise ValidationError(
            "binding-rule graph must not contain competing admitted outputs"
        )

    if outputs:
        if admitter is not None or admission_attribution is not None:
            raise ValidationError(
                "existing admitted BindingRule cannot be combined with a new "
                "admission transition"
            )
        output = outputs[0]
        admitted_candidate_identities = {
            candidate.identity for candidate in output.candidate_inputs
        }
        supplied_candidate_identities = {candidate.identity for candidate in candidates}
        if not supplied_candidate_identities.issubset(admitted_candidate_identities):
            raise ValidationError(
                "candidate material outside admitted BindingRule provenance is orphaned"
            )
        return BindingRuleAdmissionFrontier(
            symbolic_reference=symbolic_reference,
            kind=BindingRuleAdmissionFrontierKind.RULE_OUTPUT_AVAILABLE,
            candidate_inputs=output.candidate_inputs,
            admitted_rule=output,
        )

    if admitter is None:
        if admission_attribution is not None:
            raise ValidationError(
                "BindingRuleAdmissionAttribution cannot be supplied without an "
                "explicit admitter"
            )
        return _frontier_without_output(symbolic_reference, candidates)

    if not callable(admitter):
        raise ValidationError(
            "orchestrate_binding_rule_admission.admitter must be callable"
        )
    if admission_attribution is None:
        raise ValidationError(
            "binding-rule admitter requires explicit BindingRuleAdmissionAttribution"
        )
    if type(admission_attribution) is not BindingRuleAdmissionAttribution:
        raise ValidationError(
            "orchestrate_binding_rule_admission.admission_attribution must be a "
            "BindingRuleAdmissionAttribution"
        )

    proposed_output = admitter(symbolic_reference, candidates, admission_attribution)
    if proposed_output is None:
        return _frontier_without_output(symbolic_reference, candidates)

    output = _validate_output_target(
        proposed_output,
        symbolic_reference=symbolic_reference,
        field="orchestrate_binding_rule_admission.admitter output",
    )
    if output.admission_attribution != admission_attribution:
        raise ValidationError(
            "admitter output must preserve exact BindingRuleAdmissionAttribution"
        )
    if output.candidate_inputs != candidates:
        raise ValidationError(
            "admitter output must preserve complete exact candidate provenance"
        )

    return BindingRuleAdmissionFrontier(
        symbolic_reference=symbolic_reference,
        kind=BindingRuleAdmissionFrontierKind.RULE_OUTPUT_AVAILABLE,
        candidate_inputs=output.candidate_inputs,
        admitted_rule=output,
    )


__all__ = (
    "AdmittedBindingRule",
    "BindingRuleAdmissionAttribution",
    "BindingRuleAdmissionFrontier",
    "BindingRuleAdmissionFrontierKind",
    "BindingRuleProposalAttribution",
    "CandidateBindingRule",
    "orchestrate_binding_rule_admission",
)
