from __future__ import annotations

from dataclasses import dataclass

from .attempt import CapabilityAttempt
from .binding import BindingIssue
from .capability_match_evaluation import CapabilityMatchIssue
from .continuation import (
    ContinuationInput,
    ContinuationSource,
    GovernanceContinuationMaterial,
)
from .errors import ValidationError
from .identity import RecordIdentity
from .intent import StableRef
from .outcome import CapabilityOutcome, OutcomeLifecycleState
from .resolution import ResolvedIntent
from .successor_resolution import SuccessorResolutionLineage
from .worker_result import WorkerResult


_CONTINUATION_SOURCE_TYPES = (
    CapabilityOutcome,
    WorkerResult,
    BindingIssue,
    CapabilityMatchIssue,
    GovernanceContinuationMaterial,
)


def _identity_key(value: object) -> str:
    identity = getattr(value, "identity", None)
    if type(identity) is not RecordIdentity:
        raise ValidationError("M2.4 lifecycle material must expose an exact RecordIdentity")
    return str(identity)


def _normalize_attempts(value: object) -> tuple[CapabilityAttempt, ...]:
    if type(value) is not tuple:
        raise ValidationError("AttemptOutcomeContinuationFrontier.attempts must be a tuple")
    if not all(type(item) is CapabilityAttempt for item in value):
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.attempts must contain CapabilityAttempt values"
        )
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError("AttemptOutcomeContinuationFrontier.attempts contains duplicate identities")

    occurrences: dict[object, RecordIdentity] = {}
    for item in items:
        event_ref = item.attribution.attempt_event_ref
        previous = occurrences.get(event_ref)
        if previous is not None and previous != item.identity:
            raise ValidationError(
                "one CapabilityAttempt occurrence cannot identify competing Attempt records"
            )
        occurrences[event_ref] = item.identity
    return tuple(sorted(items, key=_identity_key))


def _normalize_outcomes(value: object) -> tuple[CapabilityOutcome, ...]:
    if type(value) is not tuple:
        raise ValidationError("AttemptOutcomeContinuationFrontier.outcomes must be a tuple")
    if not all(type(item) is CapabilityOutcome for item in value):
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.outcomes must contain CapabilityOutcome values"
        )
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError("AttemptOutcomeContinuationFrontier.outcomes contains duplicate identities")

    occurrences: dict[object, RecordIdentity] = {}
    for item in items:
        event_ref = item.attribution.outcome_event_ref
        previous = occurrences.get(event_ref)
        if previous is not None and previous != item.identity:
            raise ValidationError(
                "one CapabilityOutcome occurrence cannot identify competing Outcome records"
            )
        occurrences[event_ref] = item.identity
    return tuple(sorted(items, key=_identity_key))


def _source_resolved_intent_identity(source: ContinuationSource) -> RecordIdentity:
    if type(source) is CapabilityOutcome:
        return source.attempt.capability_evaluation.requirement.work_plan.resolved_intent_identity
    if type(source) is WorkerResult:
        return source.handoff.delegated_work.resolved_intent_identity
    if type(source) is BindingIssue:
        return source.rule.resolved_intent_identity
    if type(source) is CapabilityMatchIssue:
        return source.evaluation.requirement.work_plan.resolved_intent_identity
    if type(source) is GovernanceContinuationMaterial:
        return source.decision.proposal.work_plan.resolved_intent_identity
    raise ValidationError("M2.4 continuation source has unsupported exact IR type")


def _source_event_ref(source: ContinuationSource) -> StableRef:
    if type(source) is CapabilityOutcome:
        return source.attribution.outcome_event_ref
    if type(source) is WorkerResult:
        return source.attribution.result_event_ref
    if type(source) is BindingIssue:
        return source.binding_attribution.binding_event_ref
    if type(source) is CapabilityMatchIssue:
        return source.evaluation.attribution.evaluation_event_ref
    if type(source) is GovernanceContinuationMaterial:
        return source.decision.attribution.decision_event_ref
    raise ValidationError("M2.4 continuation source has unsupported exact IR type")


def _normalize_sources(value: object) -> tuple[ContinuationSource, ...]:
    if type(value) is not tuple:
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.continuation_sources must be a tuple"
        )
    if not all(type(item) in _CONTINUATION_SOURCE_TYPES for item in value):
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.continuation_sources contains unsupported IR material"
        )
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.continuation_sources contains duplicate source identities"
        )
    return tuple(sorted(items, key=_identity_key))


def _normalize_continuation_inputs(value: object) -> tuple[ContinuationInput, ...]:
    if type(value) is not tuple:
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.continuation_inputs must be a tuple"
        )
    if not all(type(item) is ContinuationInput for item in value):
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.continuation_inputs must contain ContinuationInput values"
        )
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.continuation_inputs contains duplicate identities"
        )
    return tuple(sorted(items, key=_identity_key))


def _normalize_lineages(value: object) -> tuple[SuccessorResolutionLineage, ...]:
    if type(value) is not tuple:
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.successor_lineages must be a tuple"
        )
    if not all(type(item) is SuccessorResolutionLineage for item in value):
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.successor_lineages must contain SuccessorResolutionLineage values"
        )
    items = tuple(value)
    identities = [item.identity for item in items]
    if len(set(identities)) != len(identities):
        raise ValidationError(
            "AttemptOutcomeContinuationFrontier.successor_lineages contains duplicate identities"
        )
    if len(items) > 1:
        raise ValidationError(
            "M2.4 does not select among competing active SuccessorResolutionLineage records"
        )
    return tuple(sorted(items, key=_identity_key))


@dataclass(frozen=True, slots=True)
class AttemptOutcomeContinuationFrontier:
    """Derived M2.4 lifecycle view over exact immutable M1 records."""

    predecessor: ResolvedIntent
    attempts: tuple[CapabilityAttempt, ...] = ()
    outcomes: tuple[CapabilityOutcome, ...] = ()
    continuation_sources: tuple[ContinuationSource, ...] = ()
    continuation_inputs: tuple[ContinuationInput, ...] = ()
    successor_lineages: tuple[SuccessorResolutionLineage, ...] = ()

    def __post_init__(self) -> None:
        if type(self.predecessor) is not ResolvedIntent:
            raise ValidationError(
                "AttemptOutcomeContinuationFrontier.predecessor must be a ResolvedIntent"
            )

        attempts = _normalize_attempts(self.attempts)
        predecessor_identity = self.predecessor.identity
        predecessor_event = self.predecessor.admission_attribution.admission_event_ref
        for attempt in attempts:
            if (
                attempt.capability_evaluation.requirement.work_plan.resolved_intent_identity
                != predecessor_identity
            ):
                raise ValidationError(
                    "CapabilityAttempt must descend from the exact predecessor ResolvedIntent"
                )
        object.__setattr__(self, "attempts", attempts)

        outcomes = _normalize_outcomes(self.outcomes)
        attempt_map = {item.identity: item for item in attempts}
        outcome_attempts: dict[RecordIdentity, CapabilityOutcome] = {}
        for outcome in outcomes:
            attempt_identity = outcome.attempt.identity
            if attempt_identity not in attempt_map or attempt_map[attempt_identity] != outcome.attempt:
                raise ValidationError(
                    "CapabilityOutcome is orphaned from the exact supplied CapabilityAttempt history"
                )
            previous = outcome_attempts.get(attempt_identity)
            if previous is not None and previous.identity != outcome.identity:
                raise ValidationError(
                    "M2.4 does not select among competing active CapabilityOutcome records for one Attempt"
                )
            outcome_attempts[attempt_identity] = outcome
        object.__setattr__(self, "outcomes", outcomes)

        sources = _normalize_sources(self.continuation_sources)
        outcome_map = {item.identity: item for item in outcomes}
        for source in sources:
            if _source_resolved_intent_identity(source) != predecessor_identity:
                raise ValidationError(
                    "Continuation source must descend from the exact predecessor ResolvedIntent"
                )
            if _source_event_ref(source) == predecessor_event:
                raise ValidationError(
                    "Continuation source occurrence must differ from the predecessor admission occurrence"
                )
            if type(source) is CapabilityOutcome:
                admitted = outcome_map.get(source.identity)
                if admitted is None or admitted != source:
                    raise ValidationError(
                        "CapabilityOutcome continuation source must be present in exact supplied Outcome history"
                    )
        object.__setattr__(self, "continuation_sources", sources)

        inputs = _normalize_continuation_inputs(self.continuation_inputs)
        source_map = {item.identity: item for item in sources}
        for item in inputs:
            if item.resolved_intent_identity != predecessor_identity:
                raise ValidationError(
                    "ContinuationInput must descend from the exact predecessor ResolvedIntent"
                )
            if item.attribution.reentry_event_ref == predecessor_event:
                raise ValidationError(
                    "ContinuationInput re-entry occurrence must differ from the predecessor admission occurrence"
                )
            selected_source = source_map.get(item.source_identity)
            if selected_source is None or selected_source != item.source:
                raise ValidationError(
                    "ContinuationInput is orphaned from the exact selected continuation source"
                )
        object.__setattr__(self, "continuation_inputs", inputs)

        lineages = _normalize_lineages(self.successor_lineages)
        input_map = {item.identity: item for item in inputs}
        for lineage in lineages:
            if lineage.predecessor != self.predecessor:
                raise ValidationError(
                    "SuccessorResolutionLineage must preserve the exact supplied predecessor"
                )
            for item in lineage.continuation_inputs:
                admitted = input_map.get(item.identity)
                if admitted is None or admitted != item:
                    raise ValidationError(
                        "SuccessorResolutionLineage uses ContinuationInput outside the exact supplied re-entry history"
                    )
        object.__setattr__(self, "successor_lineages", lineages)

    @property
    def outcome_pending_attempts(self) -> tuple[CapabilityAttempt, ...]:
        covered = {item.attempt.identity for item in self.outcomes}
        return tuple(item for item in self.attempts if item.identity not in covered)

    @property
    def material_unknown_outcomes(self) -> tuple[CapabilityOutcome, ...]:
        return tuple(item for item in self.outcomes if item.has_material_unknown)

    @property
    def interrupted_outcomes(self) -> tuple[CapabilityOutcome, ...]:
        return tuple(
            item
            for item in self.outcomes
            if item.lifecycle.state is OutcomeLifecycleState.INTERRUPTED
        )

    @property
    def outcomes_not_selected_for_continuation(self) -> tuple[CapabilityOutcome, ...]:
        selected = {item.identity for item in self.continuation_sources if type(item) is CapabilityOutcome}
        return tuple(item for item in self.outcomes if item.identity not in selected)

    @property
    def reentry_pending_sources(self) -> tuple[ContinuationSource, ...]:
        reentered = {item.source_identity for item in self.continuation_inputs}
        return tuple(item for item in self.continuation_sources if item.identity not in reentered)

    @property
    def reentry_ambiguity_source_identities(self) -> tuple[RecordIdentity, ...]:
        counts: dict[RecordIdentity, int] = {}
        for item in self.continuation_inputs:
            counts[item.source_identity] = counts.get(item.source_identity, 0) + 1
        return tuple(sorted((identity for identity, count in counts.items() if count > 1), key=str))

    @property
    def unconsumed_continuation_inputs(self) -> tuple[ContinuationInput, ...]:
        consumed = {
            item.identity
            for lineage in self.successor_lineages
            for item in lineage.continuation_inputs
        }
        return tuple(item for item in self.continuation_inputs if item.identity not in consumed)

    @property
    def successor_lineage(self) -> SuccessorResolutionLineage | None:
        return self.successor_lineages[0] if self.successor_lineages else None


def orchestrate_attempt_outcome_continuation(
    predecessor: ResolvedIntent,
    *,
    attempts: tuple[CapabilityAttempt, ...] = (),
    outcomes: tuple[CapabilityOutcome, ...] = (),
    continuation_sources: tuple[ContinuationSource, ...] = (),
    continuation_inputs: tuple[ContinuationInput, ...] = (),
    successor_lineages: tuple[SuccessorResolutionLineage, ...] = (),
) -> AttemptOutcomeContinuationFrontier:
    """Derive the exact M2.4 lifecycle frontier without recovery or scheduling policy."""

    return AttemptOutcomeContinuationFrontier(
        predecessor=predecessor,
        attempts=attempts,
        outcomes=outcomes,
        continuation_sources=continuation_sources,
        continuation_inputs=continuation_inputs,
        successor_lineages=successor_lineages,
    )
