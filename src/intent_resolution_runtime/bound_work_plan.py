"""G7A.3: exact named bindings for a G7A.1 sketch -> unadmitted IRR WorkPlan.

No plugin imports, provider dispatch, catalog/requirement admission, approval,
or authority. The Host MUST independently authenticate the HUMAN ResolvedIntent,
policy, scope review and input provenance. Constructing these Python records
is not evidence of that authentication. No opaque capability ref is parsed
to invent a technical argument name.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .binding import SymbolicReference
from .candidate_planning_surface import CandidatePlanningSurface, CandidatePlanSketch
from .identity import RecordIdentity
from .intent import StableRef
from .work import (
    WorkContinuationMode,
    WorkLiteralInput,
    WorkOutput,
    WorkPlan,
    WorkStep,
    WorkSymbolicInput,
)

G7A3_BOUND_WORKPLAN_CANDIDATE_VERSION = "1"


class BoundWorkPlanError(ValueError):
    """Missing Host bindings, unsupported dataflow or stale catalog provenance."""


def _ref(value: object, label: str) -> StableRef:
    if type(value) is not StableRef:
        raise BoundWorkPlanError(f"{label} requires exact StableRef")
    return value


def _text(value: object, label: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value.strip()):
        raise BoundWorkPlanError(f"invalid {label}")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise BoundWorkPlanError(f"surrogate in {label}")
    return value


@dataclass(frozen=True, slots=True)
class HostContractFieldName:
    """Independently reviewed technical argument/result name, NOT inferred."""

    contract_ref: StableRef
    name: str

    def __post_init__(self) -> None:
        _ref(self.contract_ref, "contract_ref")
        _text(self.name, "field name")
        if not self.name.replace("_", "a").isalnum() or not self.name[0].isalpha():
            raise BoundWorkPlanError("field name must be an identifier")


@dataclass(frozen=True, slots=True)
class HostLiteralBinding:
    contract_ref: StableRef
    value: str

    def __post_init__(self) -> None:
        _ref(self.contract_ref, "literal contract")
        _text(self.value, "literal", allow_empty=True)
        if len(self.value.encode("utf-8")) > 4096:
            raise BoundWorkPlanError("literal exceeds planning bound")


@dataclass(frozen=True, slots=True)
class HostPriorOutputBinding:
    contract_ref: StableRef
    producer_step_ref: StableRef
    producer_output_ref: StableRef

    def __post_init__(self) -> None:
        for field in ("contract_ref", "producer_step_ref", "producer_output_ref"):
            _ref(getattr(self, field), field)


@dataclass(frozen=True, slots=True)
class HostExternalSymbolicBinding:
    """Host-provided reference; downstream binding admission still required."""

    contract_ref: StableRef
    reference: SymbolicReference

    def __post_init__(self) -> None:
        _ref(self.contract_ref, "external symbolic contract")
        if type(self.reference) is not SymbolicReference:
            raise BoundWorkPlanError("external reference must be SymbolicReference")


PlanBinding = HostLiteralBinding | HostPriorOutputBinding | HostExternalSymbolicBinding


@dataclass(frozen=True, slots=True)
class HostBoundStep:
    capability_ref: StableRef
    step_ref: StableRef
    scope: str
    scope_requirement_refs: tuple[StableRef, ...]
    input_fields: tuple[HostContractFieldName, ...]
    output_fields: tuple[HostContractFieldName, ...]
    input_bindings: tuple[PlanBinding, ...]

    def __post_init__(self) -> None:
        _ref(self.capability_ref, "step capability")
        _ref(self.step_ref, "step ref")
        _text(self.scope, "step scope")
        if type(self.scope_requirement_refs) is not tuple or not all(
            type(x) is StableRef for x in self.scope_requirement_refs
        ):
            raise BoundWorkPlanError("scope requirements must be exact tuple")
        if len(set(self.scope_requirement_refs)) != len(self.scope_requirement_refs):
            raise BoundWorkPlanError("duplicate scope requirement")
        for name in ("input_fields", "output_fields"):
            fields = getattr(self, name)
            if type(fields) is not tuple or not all(
                type(x) is HostContractFieldName for x in fields
            ):
                raise BoundWorkPlanError(f"invalid {name}")
            if len({x.contract_ref for x in fields}) != len(fields):
                raise BoundWorkPlanError(f"duplicate {name} contract")
            if len({x.name for x in fields}) != len(fields):
                raise BoundWorkPlanError(f"duplicate {name} technical name")
        if type(self.input_bindings) is not tuple or not all(
            type(x)
            in (HostLiteralBinding, HostPriorOutputBinding, HostExternalSymbolicBinding)
            for x in self.input_bindings
        ):
            raise BoundWorkPlanError("invalid input bindings")
        if len({x.contract_ref for x in self.input_bindings}) != len(
            self.input_bindings
        ):
            raise BoundWorkPlanError("duplicate input binding")


@dataclass(frozen=True, slots=True)
class HostBoundWorkPlanMaterial:
    """Explicit Host/HUMAN-context material, not proof of original HUMAN origin."""

    resolved_intent_identity: RecordIdentity
    plan_ref: StableRef
    steps: tuple[HostBoundStep, ...]
    completion_contract: str
    description: str

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise BoundWorkPlanError("exact ResolvedIntent identity required")
        _ref(self.plan_ref, "plan ref")
        _text(self.completion_contract, "completion contract")
        _text(self.description, "plan description")
        if type(self.steps) is not tuple or not 1 <= len(self.steps) <= 3:
            raise BoundWorkPlanError("bounded one-to-three-step material required")
        if any(type(x) is not HostBoundStep for x in self.steps):
            raise BoundWorkPlanError("foreign Host step material")
        if len({x.step_ref for x in self.steps}) != len(self.steps):
            raise BoundWorkPlanError("duplicate step ref")


@dataclass(frozen=True, slots=True)
class UnadmittedBoundWorkPlan:
    """Real WorkPlan in a non-authoritative, version-bound review envelope."""

    work_plan: WorkPlan
    candidate_identity: RecordIdentity
    catalog_identity: RecordIdentity
    policy_revision_identity: RecordIdentity
    actor_ref: StableRef
    sketch: CandidatePlanSketch
    capability_descriptor_identities: tuple[RecordIdentity, ...]

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def admitted(self) -> bool:
        return False


def _exact_route(
    surface: CandidatePlanningSurface, sketch: CandidatePlanSketch
) -> tuple:
    if type(surface) is not CandidatePlanningSurface:
        raise BoundWorkPlanError("exact planning surface required")
    if type(sketch) is not CandidatePlanSketch:
        raise BoundWorkPlanError("exact G7A.1 sketch required")
    if (
        sketch.candidate_identity != surface.candidate_identity
        or sketch.policy_revision_identity != surface.policy_revision_identity
        or sketch.actor_ref != surface.actor_ref
    ):
        raise BoundWorkPlanError("stale candidate, policy or actor")
    if not 1 <= len(sketch.capability_refs) <= 3:
        raise BoundWorkPlanError("invalid sketch length")
    if len(sketch.capability_refs) != len(sketch.operations):
        raise BoundWorkPlanError("sketch operation count mismatch")
    if len(set(sketch.capability_refs)) != len(sketch.capability_refs):
        raise BoundWorkPlanError("repeated capability in sketch")
    options = {option.capability_ref: option for option in surface.options}
    route = []
    for ref, operation in zip(sketch.capability_refs, sketch.operations, strict=True):
        option = options.get(ref)
        if option is None or option.operation != operation:
            raise BoundWorkPlanError("sketch operation absent from current catalog")
        route.append(option)
    return tuple(route)


def _field_map(
    names: tuple[HostContractFieldName, ...], actual: set[StableRef], label: str
) -> dict[StableRef, str]:
    mapped = {field.contract_ref: field.name for field in names}
    if set(mapped) != actual:
        raise BoundWorkPlanError(f"{label} mapping differs from exact descriptor")
    return mapped


def _slot_ref(
    plan_ref: StableRef, step_ref: StableRef, output_ref: StableRef
) -> StableRef:
    raw = "|".join(
        f"{len(value)}:{value}"
        for value in (
            plan_ref.namespace,
            plan_ref.value,
            step_ref.namespace,
            step_ref.value,
            output_ref.namespace,
            output_ref.value,
        )
    )
    return StableRef("irr.g7a3.slot", hashlib.sha256(raw.encode()).hexdigest())


def materialize_unadmitted_work_plan(
    *,
    surface: CandidatePlanningSurface,
    sketch: CandidatePlanSketch,
    material: HostBoundWorkPlanMaterial,
) -> UnadmittedBoundWorkPlan:
    """Build exact WorkPlan IR with explicit Host fields and symbolic lineage.

    Caller is responsible for authenticating the user/Host context and
    providing trustworthy sources. No capability match/admission is inferred.
    """
    route = _exact_route(surface, sketch)
    if type(material) is not HostBoundWorkPlanMaterial:
        raise BoundWorkPlanError("explicit Host material required")
    if len(material.steps) != len(route):
        raise BoundWorkPlanError("material must bind every suggested step")

    produced: dict[tuple[StableRef, StableRef], SymbolicReference] = {}
    steps: list[WorkStep] = []
    descriptor_ids: list[RecordIdentity] = []
    for index, (option, spec) in enumerate(zip(route, material.steps, strict=True)):
        descriptor = option.descriptor
        if spec.capability_ref != option.capability_ref:
            raise BoundWorkPlanError("step capability differs from sketch")
        exact_scopes = {x.requirement_ref for x in descriptor.scope_requirements}
        if set(spec.scope_requirement_refs) != exact_scopes:
            raise BoundWorkPlanError("step lacks exact reviewed scope requirements")
        inputs = {x.input_ref: x for x in descriptor.input_contracts}
        outputs = {x.output_ref: x for x in descriptor.output_contracts}
        input_names = _field_map(spec.input_fields, set(inputs), "input")
        output_field_names = _field_map(spec.output_fields, set(outputs), "output")
        bindings = {x.contract_ref: x for x in spec.input_bindings}
        if set(bindings) != set(inputs):
            raise BoundWorkPlanError("missing or extra input binding")
        work_inputs: list[WorkLiteralInput | WorkSymbolicInput] = []
        dependencies: set[StableRef] = set()
        for input_ref, contract in inputs.items():
            binding = bindings[input_ref]
            name = input_names[input_ref]
            if type(binding) is HostLiteralBinding:
                work_inputs.append(
                    WorkLiteralInput(
                        name=name,
                        semantic_type=contract.semantic_type,
                        value=binding.value,
                    )
                )
            elif type(binding) is HostExternalSymbolicBinding:
                ref = binding.reference
                if (
                    ref.semantic_type != contract.semantic_type
                    or ref.resolved_intent_identity != material.resolved_intent_identity
                    or ref.selection_scope != spec.scope
                ):
                    raise BoundWorkPlanError(
                        "foreign external symbolic type, intent or scope"
                    )
                work_inputs.append(WorkSymbolicInput(name=name, reference=ref))
            else:
                assert type(binding) is HostPriorOutputBinding
                key = (binding.producer_step_ref, binding.producer_output_ref)
                if key not in produced:
                    raise BoundWorkPlanError("missing earlier producer output")
                ref = produced[key]
                if ref.semantic_type != contract.semantic_type:
                    raise BoundWorkPlanError("producer output/input type mismatch")
                if ref.selection_scope != spec.scope:
                    raise BoundWorkPlanError(
                        "cross-scope symbolic binding requires separate review"
                    )
                dependencies.add(binding.producer_step_ref)
                work_inputs.append(WorkSymbolicInput(name=name, reference=ref))
        work_outputs: list[WorkOutput] = []
        for output_ref, contract in outputs.items():
            symbolic = SymbolicReference(
                resolved_intent_identity=material.resolved_intent_identity,
                slot_ref=_slot_ref(material.plan_ref, spec.step_ref, output_ref),
                semantic_type=contract.semantic_type,
                selection_scope=spec.scope,
                description=f"Unadmitted output of {descriptor.operation}.",
            )
            key = (spec.step_ref, output_ref)
            produced[key] = symbolic
            work_outputs.append(
                WorkOutput(name=output_field_names[output_ref], reference=symbolic)
            )
        steps.append(
            WorkStep(
                resolved_intent_identity=material.resolved_intent_identity,
                work_plan_ref=material.plan_ref,
                step_ref=spec.step_ref,
                operation=descriptor.operation,
                scope=spec.scope,
                inputs=tuple(work_inputs),
                outputs=tuple(work_outputs),
                depends_on=tuple(dependencies),
                continuation=(
                    WorkContinuationMode.RETURN_TO_IRR
                    if index == len(route) - 1
                    else WorkContinuationMode.NONE
                ),
                completion_contract=descriptor.completion_contract,
                description=descriptor.description,
            )
        )
        descriptor_ids.append(descriptor.identity)
    required = {steps[-1].step_ref}
    step_by_ref = {step.step_ref: step for step in steps}
    pending = [steps[-1].step_ref]
    while pending:
        for dependency in step_by_ref[pending.pop()].depends_on:
            if dependency not in required:
                required.add(dependency)
                pending.append(dependency)
    if required != set(step_by_ref):
        raise BoundWorkPlanError("unrelated step is not required by final goal")
    if sketch.desired_output_semantic_type not in {
        x.reference.semantic_type for x in steps[-1].outputs
    }:
        raise BoundWorkPlanError("final step does not produce requested type")
    plan = WorkPlan(
        resolved_intent_identity=material.resolved_intent_identity,
        plan_ref=material.plan_ref,
        steps=tuple(steps),
        completion_contract=material.completion_contract,
        description=material.description,
    )
    return UnadmittedBoundWorkPlan(
        work_plan=plan,
        candidate_identity=surface.candidate_identity,
        catalog_identity=surface.catalog_identity,
        policy_revision_identity=surface.policy_revision_identity,
        actor_ref=surface.actor_ref,
        sketch=sketch,
        capability_descriptor_identities=tuple(descriptor_ids),
    )


def assert_current_unadmitted_work_plan(
    result: UnadmittedBoundWorkPlan, current_surface: CandidatePlanningSurface
) -> None:
    """Reject stale advice; Host must separately authenticate current surface."""
    if type(result) is not UnadmittedBoundWorkPlan:
        raise BoundWorkPlanError("exact unadmitted plan envelope required")
    route = _exact_route(current_surface, result.sketch)
    if (
        result.candidate_identity != current_surface.candidate_identity
        or result.catalog_identity != current_surface.catalog_identity
        or result.policy_revision_identity != current_surface.policy_revision_identity
        or result.actor_ref != current_surface.actor_ref
        or result.capability_descriptor_identities
        != tuple(x.descriptor.identity for x in route)
    ):
        raise BoundWorkPlanError("WorkPlan candidate stale against current catalog")
