from __future__ import annotations

from hashlib import sha256
from typing import Literal

from .capability import (
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffectRequirement,
)
from .capability_match import (
    CapabilityEffectMatch,
    CapabilityInputMatch,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityOutputMatch,
    CapabilityRequirement,
    CapabilityScopeMatch,
)
from .capability_match_evaluation import (
    CapabilityIncompatibleDescriptorAssessment,
    CapabilityMatchEvaluation,
    CapabilityMatchEvaluationAttribution,
    CapabilityMismatchKind,
    CapabilityMismatchReason,
)
from .errors import ValidationError
from .intent import StableRef
from .work import WorkLiteralInput, WorkSymbolicInput

IRR_CAPABILITY_MATCH_ENGINE_CONTRACT_VERSION = "1"
IRR_MECHANICAL_CAPABILITY_MATCHER_NAMESPACE = "irr.matcher"
IRR_MECHANICAL_CAPABILITY_MATCHER_VALUE = "exact-structural-v1"
IRR_MECHANICAL_CAPABILITY_EVALUATOR_NAMESPACE = "irr.evaluator"
IRR_MECHANICAL_CAPABILITY_EVALUATOR_VALUE = "capability-match-evaluation-v1"
IRR_CAPABILITY_MATCH_EVENT_NAMESPACE = "irr.capability_match"

_AssignmentStatus = Literal["none", "unique", "ambiguous"]


def mechanical_capability_matcher_ref() -> StableRef:
    """Return the fixed matcher attribution for exact structural v1 matching."""

    return StableRef(
        namespace=IRR_MECHANICAL_CAPABILITY_MATCHER_NAMESPACE,
        value=IRR_MECHANICAL_CAPABILITY_MATCHER_VALUE,
    )


def mechanical_capability_evaluator_ref() -> StableRef:
    """Return the fixed evaluator attribution for exhaustive snapshot evaluation."""

    return StableRef(
        namespace=IRR_MECHANICAL_CAPABILITY_EVALUATOR_NAMESPACE,
        value=IRR_MECHANICAL_CAPABILITY_EVALUATOR_VALUE,
    )


def _match_event_ref(
    evaluation_event_ref: StableRef,
    descriptor: CapabilityDescriptor,
) -> StableRef:
    payload = (
        f"{evaluation_event_ref.namespace}\0{evaluation_event_ref.value}\0"
        f"{descriptor.capability_ref.namespace}\0{descriptor.capability_ref.value}\0"
        f"{descriptor.identity.algorithm}\0{descriptor.identity.digest}"
    ).encode()
    return StableRef(
        namespace=IRR_CAPABILITY_MATCH_EVENT_NAMESPACE,
        value=sha256(payload).hexdigest(),
    )


def _unique_assignment(
    candidates: tuple[tuple[int, ...], ...],
    right_count: int,
    *,
    require_all_right: bool,
    required_right_indices: frozenset[int] = frozenset(),
) -> tuple[_AssignmentStatus, tuple[int, ...]]:
    if any(not options for options in candidates):
        return "none", ()
    if require_all_right and len(candidates) != right_count:
        return "none", ()
    if len(candidates) < len(required_right_indices):
        return "none", ()

    solutions: list[tuple[int, ...]] = []

    def walk(index: int, used: set[int], mapping: list[int]) -> None:
        if len(solutions) >= 2:
            return
        if index == len(candidates):
            if require_all_right and len(used) != right_count:
                return
            if not required_right_indices.issubset(used):
                return
            solutions.append(tuple(mapping))
            return
        for candidate in candidates[index]:
            if candidate in used:
                continue
            used.add(candidate)
            mapping.append(candidate)
            walk(index + 1, used, mapping)
            mapping.pop()
            used.remove(candidate)
            if len(solutions) >= 2:
                return

    walk(0, set(), [])
    if not solutions:
        return "none", ()
    if len(solutions) > 1:
        return "ambiguous", ()
    return "unique", solutions[0]


def _scope_label(descriptor: CapabilityDescriptor) -> str:
    return (
        f"capability:{descriptor.capability_ref.namespace}:"
        f"{descriptor.capability_ref.value}"
    )


def _reason(
    descriptor: CapabilityDescriptor,
    kind: CapabilityMismatchKind,
    description: str,
) -> CapabilityMismatchReason:
    return CapabilityMismatchReason(
        kind=kind,
        scope=_scope_label(descriptor),
        description=description,
    )


def _assessment(
    descriptor: CapabilityDescriptor,
    reasons: tuple[CapabilityMismatchReason, ...],
) -> CapabilityIncompatibleDescriptorAssessment:
    return CapabilityIncompatibleDescriptorAssessment(
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        reasons=reasons,
    )


def _work_input_semantic_type(value: object) -> str:
    if type(value) is WorkLiteralInput:
        return value.semantic_type
    if type(value) is WorkSymbolicInput:
        return value.reference.semantic_type
    raise ValidationError("WorkStep contains an unsupported exact input type")


def _evaluate_descriptor(
    requirement: CapabilityRequirement,
    snapshot: CapabilityCatalogSnapshot,
    descriptor: CapabilityDescriptor,
    *,
    evaluation_event_ref: StableRef,
) -> CapabilityMatch | CapabilityIncompatibleDescriptorAssessment:
    step = requirement.work_step
    immediate_reasons: list[CapabilityMismatchReason] = []
    if descriptor.operation != step.operation:
        immediate_reasons.append(
            _reason(
                descriptor,
                CapabilityMismatchKind.OPERATION_MISMATCH,
                "Descriptor operation does not exactly equal the WorkStep operation.",
            )
        )
    if descriptor.completion_contract != step.completion_contract:
        immediate_reasons.append(
            _reason(
                descriptor,
                CapabilityMismatchKind.COMPLETION_MISMATCH,
                "Descriptor completion contract is not lexically exact for the WorkStep.",
            )
        )
    descriptor_boundaries = {
        (item.kind, item.boundary_ref) for item in descriptor.execution_boundaries
    }
    if any(
        (item.kind, item.boundary_ref) not in descriptor_boundaries
        for item in requirement.execution_boundary_requirements
    ):
        immediate_reasons.append(
            _reason(
                descriptor,
                CapabilityMismatchKind.EXECUTION_BOUNDARY_MISMATCH,
                "Descriptor does not satisfy every explicit execution-boundary requirement.",
            )
        )
    if immediate_reasons:
        return _assessment(descriptor, tuple(immediate_reasons))

    requested_scopes = requirement.requested_scopes
    descriptor_scopes = descriptor.scope_requirements
    scope_candidates = tuple(
        tuple(
            index
            for index, candidate in enumerate(descriptor_scopes)
            if candidate.semantic_type == requested.semantic_type
        )
        for requested in requested_scopes
    )
    scope_status, scope_mapping = _unique_assignment(
        scope_candidates,
        len(descriptor_scopes),
        require_all_right=True,
    )
    if scope_status == "none":
        return _assessment(
            descriptor,
            (
                _reason(
                    descriptor,
                    CapabilityMismatchKind.SCOPE_MISMATCH,
                    "Requested and descriptor scope semantics do not form an exact bijection.",
                ),
            ),
        )
    if scope_status == "ambiguous":
        return _assessment(
            descriptor,
            (
                _reason(
                    descriptor,
                    CapabilityMismatchKind.INSUFFICIENT_SEMANTICS,
                    "Scope semantics admit more than one exact structural mapping.",
                ),
            ),
        )

    scope_matches = tuple(
        CapabilityScopeMatch(
            requested_scope_ref=requested.scope_ref,
            descriptor_scope_requirement_ref=descriptor_scopes[
                descriptor_index
            ].requirement_ref,
        )
        for requested, descriptor_index in zip(
            requested_scopes, scope_mapping, strict=True
        )
    )
    requested_to_descriptor_scope = {
        requested.scope_ref: descriptor_scopes[descriptor_index].requirement_ref
        for requested, descriptor_index in zip(
            requested_scopes, scope_mapping, strict=True
        )
    }
    descriptor_to_requested_scope = {
        descriptor_ref: requested_ref
        for requested_ref, descriptor_ref in requested_to_descriptor_scope.items()
    }

    work_inputs = tuple(sorted(step.inputs, key=lambda item: item.name))
    descriptor_inputs = descriptor.input_contracts
    input_candidates = tuple(
        tuple(
            index
            for index, candidate in enumerate(descriptor_inputs)
            if candidate.semantic_type == _work_input_semantic_type(work_input)
        )
        for work_input in work_inputs
    )
    input_status, input_mapping = _unique_assignment(
        input_candidates,
        len(descriptor_inputs),
        require_all_right=True,
    )
    if input_status == "none":
        return _assessment(
            descriptor,
            (
                _reason(
                    descriptor,
                    CapabilityMismatchKind.INPUT_MISMATCH,
                    "WorkStep inputs and descriptor input contracts do not match exactly.",
                ),
            ),
        )
    if input_status == "ambiguous":
        return _assessment(
            descriptor,
            (
                _reason(
                    descriptor,
                    CapabilityMismatchKind.INSUFFICIENT_SEMANTICS,
                    "Input semantics admit more than one exact structural mapping.",
                ),
            ),
        )
    input_matches = tuple(
        CapabilityInputMatch(
            work_input_name=work_input.name,
            descriptor_input_ref=descriptor_inputs[descriptor_index].input_ref,
            requested_scope_refs=tuple(
                descriptor_to_requested_scope[scope_ref]
                for scope_ref in descriptor_inputs[
                    descriptor_index
                ].scope_requirement_refs
            ),
        )
        for work_input, descriptor_index in zip(work_inputs, input_mapping, strict=True)
    )

    work_outputs = tuple(sorted(step.outputs, key=lambda item: item.name))
    descriptor_outputs = descriptor.output_contracts
    output_candidates = tuple(
        tuple(
            index
            for index, candidate in enumerate(descriptor_outputs)
            if candidate.semantic_type == work_output.reference.semantic_type
        )
        for work_output in work_outputs
    )
    output_status, output_mapping = _unique_assignment(
        output_candidates,
        len(descriptor_outputs),
        require_all_right=False,
    )
    if output_status == "none":
        return _assessment(
            descriptor,
            (
                _reason(
                    descriptor,
                    CapabilityMismatchKind.OUTPUT_MISMATCH,
                    "WorkStep outputs cannot be mapped to distinct descriptor outputs.",
                ),
            ),
        )
    if output_status == "ambiguous":
        return _assessment(
            descriptor,
            (
                _reason(
                    descriptor,
                    CapabilityMismatchKind.INSUFFICIENT_SEMANTICS,
                    "Output semantics admit more than one exact structural mapping.",
                ),
            ),
        )
    output_matches = tuple(
        CapabilityOutputMatch(
            work_output_name=work_output.name,
            descriptor_output_ref=descriptor_outputs[descriptor_index].output_ref,
            requested_scope_refs=tuple(
                descriptor_to_requested_scope[scope_ref]
                for scope_ref in descriptor_outputs[
                    descriptor_index
                ].scope_requirement_refs
            ),
        )
        for work_output, descriptor_index in zip(
            work_outputs, output_mapping, strict=True
        )
    )

    requested_effects = requirement.requested_effects
    descriptor_effects = descriptor.effects
    effect_candidates = tuple(
        tuple(
            index
            for index, candidate in enumerate(descriptor_effects)
            if candidate.semantic_type == requested_effect.semantic_type
            and set(candidate.scope_requirement_refs)
            == {
                requested_to_descriptor_scope[scope_ref]
                for scope_ref in requested_effect.requested_scope_refs
            }
        )
        for requested_effect in requested_effects
    )
    unavoidable_indices = frozenset(
        index
        for index, effect in enumerate(descriptor_effects)
        if effect.requirement is CapabilityEffectRequirement.UNAVOIDABLE
    )
    effect_status, effect_mapping = _unique_assignment(
        effect_candidates,
        len(descriptor_effects),
        require_all_right=False,
        required_right_indices=unavoidable_indices,
    )
    if effect_status == "none":
        return _assessment(
            descriptor,
            (
                _reason(
                    descriptor,
                    CapabilityMismatchKind.UNAVOIDABLE_EFFECT_MISMATCH,
                    "Requested effects and unavoidable descriptor effects cannot be matched exactly.",
                ),
            ),
        )
    if effect_status == "ambiguous":
        return _assessment(
            descriptor,
            (
                _reason(
                    descriptor,
                    CapabilityMismatchKind.INSUFFICIENT_SEMANTICS,
                    "Effect semantics admit more than one exact structural mapping.",
                ),
            ),
        )
    effect_matches = tuple(
        CapabilityEffectMatch(
            requested_effect_ref=requested_effect.effect_ref,
            descriptor_effect_ref=descriptor_effects[descriptor_index].effect_ref,
        )
        for requested_effect, descriptor_index in zip(
            requested_effects, effect_mapping, strict=True
        )
    )

    return CapabilityMatch(
        attribution=CapabilityMatchAttribution(
            matcher_ref=mechanical_capability_matcher_ref(),
            match_event_ref=_match_event_ref(evaluation_event_ref, descriptor),
        ),
        requirement=requirement,
        catalog_snapshot=snapshot,
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
        scope_matches=scope_matches,
        input_matches=input_matches,
        output_matches=output_matches,
        effect_matches=effect_matches,
        description="Unique exact structural v1 match in the supplied Catalog Snapshot.",
    )


def build_capability_match_evaluation(
    requirement: CapabilityRequirement,
    catalog_snapshot: CapabilityCatalogSnapshot,
    *,
    evaluation_event_ref: StableRef,
) -> CapabilityMatchEvaluation:
    """Exhaustively evaluate one exact requirement against one exact Catalog Snapshot.

    This function performs no catalog discovery, capability invocation, provider call,
    Governance decision, authorization, retry, fallback, or execution. Ambiguous
    structural mappings fail closed as INSUFFICIENT_SEMANTICS rather than selecting by
    descriptor or tuple order.
    """

    if type(requirement) is not CapabilityRequirement:
        raise ValidationError(
            "build_capability_match_evaluation.requirement must be a CapabilityRequirement"
        )
    if type(catalog_snapshot) is not CapabilityCatalogSnapshot:
        raise ValidationError(
            "build_capability_match_evaluation.catalog_snapshot must be a CapabilityCatalogSnapshot"
        )
    if type(evaluation_event_ref) is not StableRef:
        raise ValidationError(
            "build_capability_match_evaluation.evaluation_event_ref must be a StableRef"
        )

    matches: list[CapabilityMatch] = []
    incompatible: list[CapabilityIncompatibleDescriptorAssessment] = []
    for descriptor in catalog_snapshot.descriptors:
        result = _evaluate_descriptor(
            requirement,
            catalog_snapshot,
            descriptor,
            evaluation_event_ref=evaluation_event_ref,
        )
        if isinstance(result, CapabilityMatch):
            matches.append(result)
        elif isinstance(result, CapabilityIncompatibleDescriptorAssessment):
            incompatible.append(result)
        else:  # pragma: no cover - closed internal union guard
            raise TypeError(
                "Capability match engine returned an unsupported result type."
            )

    return CapabilityMatchEvaluation(
        attribution=CapabilityMatchEvaluationAttribution(
            evaluator_ref=mechanical_capability_evaluator_ref(),
            evaluation_event_ref=evaluation_event_ref,
        ),
        requirement=requirement,
        catalog_snapshot=catalog_snapshot,
        compatible_matches=tuple(matches),
        incompatible_assessments=tuple(incompatible),
        description=(
            "Exhaustive deterministic exact-structural-v1 assessment of the supplied "
            "Capability Catalog Snapshot."
        ),
    )


__all__ = (
    "IRR_CAPABILITY_MATCH_ENGINE_CONTRACT_VERSION",
    "IRR_CAPABILITY_MATCH_EVENT_NAMESPACE",
    "IRR_MECHANICAL_CAPABILITY_EVALUATOR_NAMESPACE",
    "IRR_MECHANICAL_CAPABILITY_EVALUATOR_VALUE",
    "IRR_MECHANICAL_CAPABILITY_MATCHER_NAMESPACE",
    "IRR_MECHANICAL_CAPABILITY_MATCHER_VALUE",
    "build_capability_match_evaluation",
    "mechanical_capability_evaluator_ref",
    "mechanical_capability_matcher_ref",
)
