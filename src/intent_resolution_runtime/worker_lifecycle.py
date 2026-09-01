from __future__ import annotations

from dataclasses import dataclass

from .delegation import DelegatedWork, DelegatedWorkHandoff
from .errors import ValidationError
from .identity import RecordIdentity
from .intent import StableRef
from .resolution import ResolvedIntent
from .work import WorkPlan
from .worker_result import (
    WorkerResult,
    WorkerResultMaterialRole,
)


def _identity_key(value: object) -> str:
    identity = getattr(value, "identity", None)
    if type(identity) is not RecordIdentity:
        raise ValidationError("M2.5 worker lifecycle material must expose an exact RecordIdentity")
    return str(identity)


def _normalize_parent_work_plans(value: object) -> tuple[WorkPlan, ...]:
    if type(value) is not tuple:
        raise ValidationError("WorkerLifecycleFrontier.parent_work_plans must be a tuple")
    if not all(type(item) is WorkPlan for item in value):
        raise ValidationError(
            "WorkerLifecycleFrontier.parent_work_plans must contain WorkPlan values"
        )
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError("WorkerLifecycleFrontier.parent_work_plans contains duplicate identities")
    return tuple(sorted(items, key=_identity_key))


def _normalize_delegations(value: object) -> tuple[DelegatedWork, ...]:
    if type(value) is not tuple:
        raise ValidationError("WorkerLifecycleFrontier.delegated_work must be a tuple")
    if not all(type(item) is DelegatedWork for item in value):
        raise ValidationError(
            "WorkerLifecycleFrontier.delegated_work must contain DelegatedWork values"
        )
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError("WorkerLifecycleFrontier.delegated_work contains duplicate identities")

    by_ref: dict[StableRef, RecordIdentity] = {}
    for item in items:
        previous = by_ref.get(item.delegation_ref)
        if previous is not None and previous != item.identity:
            raise ValidationError(
                "M2.5 does not select among competing active DelegatedWork records for one delegation_ref"
            )
        by_ref[item.delegation_ref] = item.identity
    return tuple(sorted(items, key=_identity_key))


def _normalize_handoffs(value: object) -> tuple[DelegatedWorkHandoff, ...]:
    if type(value) is not tuple:
        raise ValidationError("WorkerLifecycleFrontier.handoffs must be a tuple")
    if not all(type(item) is DelegatedWorkHandoff for item in value):
        raise ValidationError(
            "WorkerLifecycleFrontier.handoffs must contain DelegatedWorkHandoff values"
        )
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError("WorkerLifecycleFrontier.handoffs contains duplicate identities")

    occurrences: dict[StableRef, RecordIdentity] = {}
    for item in items:
        event_ref = item.attribution.handoff_event_ref
        previous = occurrences.get(event_ref)
        if previous is not None and previous != item.identity:
            raise ValidationError(
                "one Worker handoff occurrence cannot identify competing DelegatedWorkHandoff records"
            )
        occurrences[event_ref] = item.identity
    return tuple(sorted(items, key=_identity_key))


def _normalize_results(value: object) -> tuple[WorkerResult, ...]:
    if type(value) is not tuple:
        raise ValidationError("WorkerLifecycleFrontier.worker_results must be a tuple")
    if not all(type(item) is WorkerResult for item in value):
        raise ValidationError(
            "WorkerLifecycleFrontier.worker_results must contain WorkerResult values"
        )
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError("WorkerLifecycleFrontier.worker_results contains duplicate identities")

    occurrences: dict[StableRef, RecordIdentity] = {}
    for item in items:
        event_ref = item.attribution.result_event_ref
        previous = occurrences.get(event_ref)
        if previous is not None and previous != item.identity:
            raise ValidationError(
                "one Worker result occurrence cannot identify competing WorkerResult records"
            )
        occurrences[event_ref] = item.identity
    return tuple(sorted(items, key=_identity_key))


@dataclass(frozen=True, slots=True)
class WorkerLifecycleFrontier:
    """Derived M2.5 view over exact Worker delegation/handoff/result history."""

    predecessor: ResolvedIntent
    parent_work_plans: tuple[WorkPlan, ...] = ()
    delegated_work: tuple[DelegatedWork, ...] = ()
    handoffs: tuple[DelegatedWorkHandoff, ...] = ()
    worker_results: tuple[WorkerResult, ...] = ()

    def __post_init__(self) -> None:
        if type(self.predecessor) is not ResolvedIntent:
            raise ValidationError("WorkerLifecycleFrontier.predecessor must be a ResolvedIntent")

        predecessor_identity = self.predecessor.identity
        predecessor_event = self.predecessor.admission_attribution.admission_event_ref

        parent_plans = _normalize_parent_work_plans(self.parent_work_plans)
        for plan in parent_plans:
            if plan.resolved_intent_identity != predecessor_identity:
                raise ValidationError(
                    "parent WorkPlan must descend from the exact predecessor ResolvedIntent"
                )
        object.__setattr__(self, "parent_work_plans", parent_plans)
        parent_plan_map = {item.identity: item for item in parent_plans}

        delegations = _normalize_delegations(self.delegated_work)
        for delegated in delegations:
            if delegated.resolved_intent_identity != predecessor_identity:
                raise ValidationError(
                    "DelegatedWork must descend from the exact predecessor ResolvedIntent"
                )
            for parent_identity in delegated.parent_work_plan_identity_refs:
                if parent_identity not in parent_plan_map:
                    raise ValidationError(
                        "DelegatedWork parent WorkPlan identity is orphaned from exact supplied parent_work_plans"
                    )
        object.__setattr__(self, "delegated_work", delegations)
        delegation_map = {item.identity: item for item in delegations}

        handoffs = _normalize_handoffs(self.handoffs)
        handoff_events: set[StableRef] = set()
        for handoff in handoffs:
            delegated = delegation_map.get(handoff.delegated_work.identity)
            if delegated is None or delegated != handoff.delegated_work:
                raise ValidationError(
                    "DelegatedWorkHandoff is orphaned from the exact supplied DelegatedWork history"
                )
            event_ref = handoff.attribution.handoff_event_ref
            if event_ref == predecessor_event:
                raise ValidationError(
                    "Worker handoff occurrence must differ from the predecessor admission occurrence"
                )
            handoff_events.add(event_ref)
        object.__setattr__(self, "handoffs", handoffs)
        handoff_map = {item.identity: item for item in handoffs}

        results = _normalize_results(self.worker_results)
        for result in results:
            handoff = handoff_map.get(result.handoff.identity)
            if handoff is None or handoff != result.handoff:
                raise ValidationError(
                    "WorkerResult is orphaned from the exact supplied DelegatedWorkHandoff history"
                )
            event_ref = result.attribution.result_event_ref
            if event_ref == predecessor_event:
                raise ValidationError(
                    "Worker result occurrence must differ from the predecessor admission occurrence"
                )
            if event_ref in handoff_events:
                raise ValidationError(
                    "Worker result occurrence must remain distinct from every Worker handoff occurrence"
                )
        object.__setattr__(self, "worker_results", results)

    @property
    def handoff_disposition_required_delegations(self) -> tuple[DelegatedWork, ...]:
        handed_off = {item.delegated_work.identity for item in self.handoffs}
        return tuple(item for item in self.delegated_work if item.identity not in handed_off)

    @property
    def result_pending_handoffs(self) -> tuple[DelegatedWorkHandoff, ...]:
        returned = {item.handoff.identity for item in self.worker_results}
        return tuple(item for item in self.handoffs if item.identity not in returned)

    @property
    def multi_handoff_delegation_refs(self) -> tuple[StableRef, ...]:
        counts: dict[RecordIdentity, int] = {}
        refs: dict[RecordIdentity, StableRef] = {}
        for handoff in self.handoffs:
            identity = handoff.delegated_work.identity
            counts[identity] = counts.get(identity, 0) + 1
            refs[identity] = handoff.delegated_work.delegation_ref
        return tuple(
            sorted(
                (refs[identity] for identity, count in counts.items() if count > 1),
                key=lambda item: (item.namespace, item.value),
            )
        )

    @property
    def multi_result_handoff_identities(self) -> tuple[RecordIdentity, ...]:
        counts: dict[RecordIdentity, int] = {}
        for result in self.worker_results:
            identity = result.handoff.identity
            counts[identity] = counts.get(identity, 0) + 1
        return tuple(sorted((identity for identity, count in counts.items() if count > 1), key=str))

    @property
    def results_with_needs(self) -> tuple[WorkerResult, ...]:
        return tuple(item for item in self.worker_results if item.needs)

    @property
    def results_with_completion_claims(self) -> tuple[WorkerResult, ...]:
        return tuple(
            result
            for result in self.worker_results
            if any(
                material.role is WorkerResultMaterialRole.COMPLETION_CLAIM
                for material in result.materials
            )
        )

    @property
    def results_with_deliverables(self) -> tuple[WorkerResult, ...]:
        return tuple(
            result
            for result in self.worker_results
            if any(
                material.role is WorkerResultMaterialRole.DELIVERABLE
                for material in result.materials
            )
        )


def orchestrate_worker_lifecycle(
    predecessor: ResolvedIntent,
    *,
    parent_work_plans: tuple[WorkPlan, ...] = (),
    delegated_work: tuple[DelegatedWork, ...] = (),
    handoffs: tuple[DelegatedWorkHandoff, ...] = (),
    worker_results: tuple[WorkerResult, ...] = (),
) -> WorkerLifecycleFrontier:
    """Derive exact Worker lifecycle history without Worker or parent-completion policy."""

    return WorkerLifecycleFrontier(
        predecessor=predecessor,
        parent_work_plans=parent_work_plans,
        delegated_work=delegated_work,
        handoffs=handoffs,
        worker_results=worker_results,
    )
