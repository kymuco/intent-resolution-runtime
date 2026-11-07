"""G7A.1: bounded planning hypotheses from exact, Host-projected IRR catalogs.

The Host is responsible for Runplane discovery, semantics, provider provenance,
policy evaluation and attribution of the visibility input. This module is pure
IRR: it imports no plugin, runs no effects, never creates WorkPlan, Catalog
Admission, Governance, Authorization or Attempt. A candidate chain is only
a structural suggestion; data values, scope feasibility, binding and authority
MUST be checked independently before real plan admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .capability import CapabilityDescriptor
from .capability_catalog_admission import CandidateCapabilityCatalogSnapshot
from .identity import RecordIdentity
from .intent import StableRef

IRR_DYNAMIC_PLANNING_SURFACE_CONTRACT_VERSION = "1"
_MAX_OPTIONS = 64
_MAX_STATES = 4096


class CapabilityPlanningSurfaceError(ValueError):
    """Invalid source, forged visibility claim or unbounded search request."""


def _exact_ref(value: object, name: str) -> StableRef:
    if type(value) is not StableRef:
        raise CapabilityPlanningSurfaceError(f"{name} must be an exact StableRef")
    return value


def _exact_identity(value: object, name: str) -> RecordIdentity:
    if type(value) is not RecordIdentity:
        raise CapabilityPlanningSurfaceError(f"{name} must be exact RecordIdentity")
    return value


def _semantic_type(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise CapabilityPlanningSurfaceError(f"invalid {name}")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise CapabilityPlanningSurfaceError(f"invalid Unicode in {name}")
    return value


def _ref_key(value: StableRef) -> tuple[str, str]:
    return value.namespace, value.value


@dataclass(frozen=True, slots=True)
class HostPlanningVisibility:
    """Host-owned planning visibility, NOT capability admission or permission.

    The caller MUST authenticate this record through its own trusted policy
    path; an untrusted plugin/model can construct a Python dataclass, which
    is not proof of Host identity. Every visible ref is tied to the exact
    candidate identity; a changed catalog requires new Host policy evidence.
    """

    actor_ref: StableRef
    policy_ref: StableRef
    policy_revision_identity: RecordIdentity
    candidate_identity: RecordIdentity
    visible_capability_refs: tuple[StableRef, ...]

    def __post_init__(self) -> None:
        for field in ("actor_ref", "policy_ref"):
            _exact_ref(getattr(self, field), field)
        for field in ("policy_revision_identity", "candidate_identity"):
            _exact_identity(getattr(self, field), field)
        refs = self.visible_capability_refs
        if type(refs) is not tuple or not all(type(item) is StableRef for item in refs):
            raise CapabilityPlanningSurfaceError(
                "visible_capability_refs must be exact tuple of StableRef"
            )
        if len(set(refs)) != len(refs):
            raise CapabilityPlanningSurfaceError("duplicate visible capability")
        if len(refs) > _MAX_OPTIONS:
            raise CapabilityPlanningSurfaceError("visibility exceeds bounded options")
        object.__setattr__(
            self, "visible_capability_refs", tuple(sorted(refs, key=_ref_key))
        )


@dataclass(frozen=True, slots=True)
class PlanningOption:
    """One exactly described candidate; provider activation is never implied."""

    descriptor: CapabilityDescriptor

    def __post_init__(self) -> None:
        if type(self.descriptor) is not CapabilityDescriptor:
            raise CapabilityPlanningSurfaceError("foreign descriptor")

    @property
    def capability_ref(self) -> StableRef:
        return self.descriptor.capability_ref

    @property
    def operation(self) -> str:
        return self.descriptor.operation

    @property
    def input_semantic_types(self) -> tuple[str, ...]:
        return tuple(item.semantic_type for item in self.descriptor.input_contracts)

    @property
    def output_semantic_types(self) -> tuple[str, ...]:
        return tuple(item.semantic_type for item in self.descriptor.output_contracts)


@dataclass(frozen=True, slots=True)
class PlanningDependencyHint:
    """Matching output/input TYPES only; never a proven data binding."""

    producer_ref: StableRef
    consumer_ref: StableRef
    semantic_type: str


@dataclass(frozen=True, slots=True)
class CandidatePlanningSurface:
    """Candidate-only planner input with immutable provenance and policy scope."""

    contract_version: ClassVar[str] = IRR_DYNAMIC_PLANNING_SURFACE_CONTRACT_VERSION
    candidate_identity: RecordIdentity
    catalog_identity: RecordIdentity
    actor_ref: StableRef
    policy_ref: StableRef
    policy_revision_identity: RecordIdentity
    options: tuple[PlanningOption, ...]
    dependency_hints: tuple[PlanningDependencyHint, ...]

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def admitted_catalog(self) -> None:
        return None


@dataclass(frozen=True, slots=True)
class CandidatePlanSketch:
    """Read-only structural route. NOT WorkPlan, Authorization or Attempt."""

    candidate_identity: RecordIdentity
    policy_revision_identity: RecordIdentity
    actor_ref: StableRef
    capability_refs: tuple[StableRef, ...]
    operations: tuple[str, ...]
    desired_output_semantic_type: str

    @property
    def execution_authorized(self) -> bool:
        return False


def build_candidate_planning_surface(
    *,
    candidate: CandidateCapabilityCatalogSnapshot,
    visibility: HostPlanningVisibility,
) -> CandidatePlanningSurface:
    """Filter exact Host-projected catalog refs, never mint admission.

    Must be called only with authenticated Host-owned visibility and an
    independently captured/provenanced Runplane G3 candidate. Constructing
    a matching in-memory pair does NOT authenticate their origin.
    """
    if type(candidate) is not CandidateCapabilityCatalogSnapshot:
        raise CapabilityPlanningSurfaceError("exact candidate input required")
    if type(visibility) is not HostPlanningVisibility:
        raise CapabilityPlanningSurfaceError("exact Host visibility required")
    if candidate.identity != visibility.candidate_identity:
        raise CapabilityPlanningSurfaceError("stale or foreign candidate identity")
    descriptors = {item.capability_ref: item for item in candidate.snapshot.descriptors}
    missing = set(visibility.visible_capability_refs) - descriptors.keys()
    if missing:
        raise CapabilityPlanningSurfaceError("visibility includes foreign capability")
    options = tuple(
        sorted(
            (
                PlanningOption(descriptors[ref])
                for ref in visibility.visible_capability_refs
            ),
            key=lambda option: (option.operation, *_ref_key(option.capability_ref)),
        )
    )
    hints: set[tuple[StableRef, StableRef, str]] = set()
    for producer in options:
        for consumer in options:
            if producer.capability_ref == consumer.capability_ref:
                continue
            shared = set(producer.output_semantic_types) & set(
                consumer.input_semantic_types
            )
            for semantic in shared:
                hints.add((producer.capability_ref, consumer.capability_ref, semantic))
    edges = tuple(
        PlanningDependencyHint(*edge)
        for edge in sorted(
            hints,
            key=lambda edge: (*_ref_key(edge[0]), *_ref_key(edge[1]), edge[2]),
        )
    )
    return CandidatePlanningSurface(
        candidate_identity=candidate.identity,
        catalog_identity=candidate.snapshot.identity,
        actor_ref=visibility.actor_ref,
        policy_ref=visibility.policy_ref,
        policy_revision_identity=visibility.policy_revision_identity,
        options=options,
        dependency_hints=edges,
    )


def _contributes_to_goal(route: tuple[PlanningOption, ...], goal: str) -> bool:
    """Every suggested step must contribute an exact type needed downstream."""
    required = {goal}
    for option in reversed(route):
        outputs = set(option.output_semantic_types)
        if not (outputs & required):
            return False
        required.difference_update(outputs)
        required.update(option.input_semantic_types)
    return True


def find_structural_plan_candidates(
    surface: CandidatePlanningSurface,
    *,
    desired_output_semantic_type: str,
    available_input_semantic_types: tuple[str, ...],
    max_steps: int = 3,
    max_candidates: int = 16,
) -> tuple[CandidatePlanSketch, ...]:
    """Explore exact-type reachability, never synthesize WorkPlan or values.

    Input semantic TYPES indicate possible data roles, NOT verified values,
    scopes or actual symbolic bindings. A candidate requires all declared
    input types to be available from the environment or prior suggested
    outputs; no implicit conversion or semantic similarity is accepted.
    """
    if type(surface) is not CandidatePlanningSurface:
        raise CapabilityPlanningSurfaceError("foreign planning surface")
    goal = _semantic_type(desired_output_semantic_type, "desired output")
    if type(available_input_semantic_types) is not tuple:
        raise CapabilityPlanningSurfaceError("available types must be tuple")
    known: set[str] = set()
    for semantic in available_input_semantic_types:
        known.add(_semantic_type(semantic, "available input"))
    if (
        type(max_steps) is not int
        or not 1 <= max_steps <= 3
        or type(max_candidates) is not int
        or not 1 <= max_candidates <= 32
    ):
        raise CapabilityPlanningSurfaceError("invalid bounded search limits")
    if len(surface.options) > _MAX_OPTIONS:
        raise CapabilityPlanningSurfaceError("oversized planning surface")
    finished: dict[tuple[StableRef, ...], CandidatePlanSketch] = {}
    frontier: list[tuple[tuple[PlanningOption, ...], frozenset[str]]] = [
        ((), frozenset(known))
    ]
    explored = 0
    for _ in range(max_steps):
        next_frontier: list[tuple[tuple[PlanningOption, ...], frozenset[str]]] = []
        for route, known_types in frontier:
            used = {item.capability_ref for item in route}
            for option in surface.options:
                if option.capability_ref in used:
                    continue
                if not set(option.input_semantic_types).issubset(known_types):
                    continue
                outputs = set(option.output_semantic_types)
                if not outputs:
                    continue
                next_route = (*route, option)
                next_types = known_types | outputs
                explored += 1
                if explored > _MAX_STATES:
                    raise CapabilityPlanningSurfaceError(
                        "bounded search exhausted; refine candidate catalog"
                    )
                if goal in outputs and _contributes_to_goal(next_route, goal):
                    refs = tuple(item.capability_ref for item in next_route)
                    finished[refs] = CandidatePlanSketch(
                        candidate_identity=surface.candidate_identity,
                        policy_revision_identity=surface.policy_revision_identity,
                        actor_ref=surface.actor_ref,
                        capability_refs=refs,
                        operations=tuple(item.operation for item in next_route),
                        desired_output_semantic_type=goal,
                    )
                if outputs - known_types:
                    next_frontier.append((next_route, frozenset(next_types)))
        frontier = next_frontier
    return tuple(
        sorted(
            finished.values(),
            key=lambda item: (
                len(item.capability_refs),
                item.operations,
                tuple(_ref_key(ref) for ref in item.capability_refs),
            ),
        )[:max_candidates]
    )
