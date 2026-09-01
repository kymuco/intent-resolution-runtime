from __future__ import annotations

from dataclasses import dataclass

from .binding import BindingEvaluation, BindingIssue, BindingRule, BoundValue, SymbolicReference
from .errors import ValidationError
from .identity import RecordIdentity
from .resolution import ResolvedIntent
from .work import WorkPlan, WorkSymbolicInput


def _normalize_work_plans(value: object, *, field: str) -> tuple[WorkPlan, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is WorkPlan for item in value):
        raise ValidationError(f"{field} must contain WorkPlan values")
    plans = tuple(value)
    identities = [plan.identity for plan in plans]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate WorkPlan identities")
    return tuple(sorted(plans, key=lambda plan: str(plan.identity)))


def _normalize_rules(value: object, *, field: str) -> tuple[BindingRule, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is BindingRule for item in value):
        raise ValidationError(f"{field} must contain BindingRule values")
    rules = tuple(value)
    identities = [rule.identity for rule in rules]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate BindingRule identities")
    return tuple(sorted(rules, key=lambda rule: str(rule.identity)))


def _normalize_evaluations(
    value: object, *, field: str
) -> tuple[BindingEvaluation, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) in (BoundValue, BindingIssue) for item in value):
        raise ValidationError(f"{field} must contain BoundValue or BindingIssue values")
    evaluations = tuple(value)
    identities = [evaluation.identity for evaluation in evaluations]
    if len(set(identities)) != len(identities):
        raise ValidationError(f"{field} must not contain duplicate BindingEvaluation identities")
    return tuple(sorted(evaluations, key=lambda evaluation: str(evaluation.identity)))


def _normalize_symbolic_references(
    value: object, *, field: str
) -> tuple[SymbolicReference, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is SymbolicReference for item in value):
        raise ValidationError(f"{field} must contain SymbolicReference values")
    references = tuple(value)
    slots = [reference.slot_ref for reference in references]
    if len(set(slots)) != len(slots):
        raise ValidationError(f"{field} must not contain duplicate symbolic slots")
    return tuple(
        sorted(
            references,
            key=lambda reference: (
                reference.slot_ref.namespace,
                reference.slot_ref.value,
            ),
        )
    )


def _external_symbolic_references(work_plan: WorkPlan) -> tuple[SymbolicReference, ...]:
    produced_slots = {
        output.reference.slot_ref
        for step in work_plan.steps
        for output in step.outputs
    }
    external_by_slot: dict[object, SymbolicReference] = {}
    for step in work_plan.steps:
        for work_input in step.inputs:
            if type(work_input) is not WorkSymbolicInput:
                continue
            reference = work_input.reference
            if reference.slot_ref in produced_slots:
                continue
            previous = external_by_slot.get(reference.slot_ref)
            if previous is not None and previous.identity != reference.identity:
                raise ValidationError(
                    "WorkPlan external symbolic slot has conflicting SymbolicReference semantics"
                )
            external_by_slot[reference.slot_ref] = reference
    return _normalize_symbolic_references(
        tuple(external_by_slot.values()),
        field="WorkBindingFrontier.external_symbolic_references",
    )


@dataclass(frozen=True, slots=True)
class WorkBindingFrontier:
    """Derived non-canonical M2.2 view over one bounded WorkPlan binding surface."""

    resolved_intent_identity: RecordIdentity
    work_plan: WorkPlan | None
    work_disposition_required: bool
    external_symbolic_references: tuple[SymbolicReference, ...] = ()
    missing_rule_references: tuple[SymbolicReference, ...] = ()
    pending_rules: tuple[BindingRule, ...] = ()
    bound_values: tuple[BoundValue, ...] = ()
    binding_issues: tuple[BindingIssue, ...] = ()
    external_binding_complete: bool = False

    def __post_init__(self) -> None:
        if type(self.resolved_intent_identity) is not RecordIdentity:
            raise ValidationError(
                "WorkBindingFrontier.resolved_intent_identity must be a RecordIdentity"
            )
        if type(self.work_disposition_required) is not bool:
            raise ValidationError(
                "WorkBindingFrontier.work_disposition_required must be a bool"
            )
        if type(self.external_binding_complete) is not bool:
            raise ValidationError(
                "WorkBindingFrontier.external_binding_complete must be a bool"
            )

        external = _normalize_symbolic_references(
            self.external_symbolic_references,
            field="WorkBindingFrontier.external_symbolic_references",
        )
        missing = _normalize_symbolic_references(
            self.missing_rule_references,
            field="WorkBindingFrontier.missing_rule_references",
        )
        pending = _normalize_rules(
            self.pending_rules,
            field="WorkBindingFrontier.pending_rules",
        )
        bound = _normalize_evaluations(
            self.bound_values,
            field="WorkBindingFrontier.bound_values",
        )
        issues = _normalize_evaluations(
            self.binding_issues,
            field="WorkBindingFrontier.binding_issues",
        )
        if not all(type(item) is BoundValue for item in bound):
            raise ValidationError("WorkBindingFrontier.bound_values must contain BoundValue values")
        if not all(type(item) is BindingIssue for item in issues):
            raise ValidationError("WorkBindingFrontier.binding_issues must contain BindingIssue values")

        object.__setattr__(self, "external_symbolic_references", external)
        object.__setattr__(self, "missing_rule_references", missing)
        object.__setattr__(self, "pending_rules", pending)
        object.__setattr__(self, "bound_values", tuple(bound))
        object.__setattr__(self, "binding_issues", tuple(issues))

        if self.work_plan is None:
            if not self.work_disposition_required:
                raise ValidationError(
                    "WorkBindingFrontier without WorkPlan must require explicit work disposition"
                )
            if external or missing or pending or bound or issues:
                raise ValidationError(
                    "WorkBindingFrontier without WorkPlan cannot contain binding surface material"
                )
            if self.external_binding_complete:
                raise ValidationError(
                    "WorkBindingFrontier without WorkPlan cannot claim external binding complete"
                )
            return

        if type(self.work_plan) is not WorkPlan:
            raise ValidationError("WorkBindingFrontier.work_plan must be a WorkPlan or None")
        if self.work_plan.resolved_intent_identity != self.resolved_intent_identity:
            raise ValidationError(
                "WorkBindingFrontier WorkPlan must belong to the exact ResolvedIntent"
            )
        if self.work_disposition_required:
            raise ValidationError(
                "WorkBindingFrontier with WorkPlan cannot require work disposition"
            )

        expected_external = _external_symbolic_references(self.work_plan)
        if external != expected_external:
            raise ValidationError(
                "WorkBindingFrontier external symbolic references must match the exact WorkPlan"
            )

        external_by_slot = {reference.slot_ref: reference for reference in external}
        state_slots: list[object] = []

        for reference in missing:
            expected = external_by_slot.get(reference.slot_ref)
            if expected is None or expected.identity != reference.identity:
                raise ValidationError(
                    "WorkBindingFrontier missing rule reference must be an exact external WorkPlan symbol"
                )
            state_slots.append(reference.slot_ref)

        for rule in pending:
            expected = external_by_slot.get(rule.symbolic_reference.slot_ref)
            if expected is None or expected.identity != rule.symbolic_reference.identity:
                raise ValidationError(
                    "WorkBindingFrontier pending rule must target an exact external WorkPlan symbol"
                )
            state_slots.append(rule.symbolic_reference.slot_ref)

        for evaluation in (*bound, *issues):
            expected = external_by_slot.get(evaluation.rule.symbolic_reference.slot_ref)
            if expected is None or expected.identity != evaluation.rule.symbolic_reference.identity:
                raise ValidationError(
                    "WorkBindingFrontier evaluation must target an exact external WorkPlan symbol"
                )
            state_slots.append(evaluation.rule.symbolic_reference.slot_ref)

        if len(set(state_slots)) != len(state_slots):
            raise ValidationError(
                "WorkBindingFrontier cannot assign multiple active binding states to one symbolic slot"
            )
        if set(state_slots) != set(external_by_slot):
            raise ValidationError(
                "WorkBindingFrontier must expose one active binding state for every external symbolic slot"
            )

        expected_complete = bool(self.work_plan) and not missing and not pending and not issues
        if not external:
            expected_complete = True
        if self.external_binding_complete != expected_complete:
            raise ValidationError(
                "WorkBindingFrontier.external_binding_complete does not match the active binding surface"
            )


def orchestrate_work_binding(
    resolved_intent: ResolvedIntent,
    *,
    work_plans: tuple[WorkPlan, ...] = (),
    binding_rules: tuple[BindingRule, ...] = (),
    binding_evaluations: tuple[BindingEvaluation, ...] = (),
) -> WorkBindingFrontier:
    """Derive the complete active M2.2 work/binding frontier from explicit M1 records.

    M2.2 does not synthesize a WorkPlan, infer a non-operational terminal state,
    acquire BindingInput, choose which BindingInput belongs to which rule, or perform
    binding evaluation implicitly. Mechanical evaluation remains the explicit M1.4
    ``evaluate_binding`` boundary; this orchestrator consumes its canonical results.
    """

    if type(resolved_intent) is not ResolvedIntent:
        raise ValidationError(
            "orchestrate_work_binding.resolved_intent must be a ResolvedIntent"
        )

    plans = _normalize_work_plans(
        work_plans,
        field="orchestrate_work_binding.work_plans",
    )
    if any(plan.resolved_intent_identity != resolved_intent.identity for plan in plans):
        raise ValidationError(
            "orchestrate_work_binding WorkPlan belongs to a foreign ResolvedIntent lineage"
        )
    if len(plans) > 1:
        raise ValidationError(
            "work/binding graph must not contain competing active WorkPlan records"
        )

    rules = _normalize_rules(
        binding_rules,
        field="orchestrate_work_binding.binding_rules",
    )
    evaluations = _normalize_evaluations(
        binding_evaluations,
        field="orchestrate_work_binding.binding_evaluations",
    )

    if not plans:
        if rules or evaluations:
            raise ValidationError(
                "binding material is orphaned when no active WorkPlan is supplied"
            )
        return WorkBindingFrontier(
            resolved_intent_identity=resolved_intent.identity,
            work_plan=None,
            work_disposition_required=True,
        )

    work_plan = plans[0]
    external = _external_symbolic_references(work_plan)
    external_by_slot = {reference.slot_ref: reference for reference in external}

    rules_by_slot: dict[object, BindingRule] = {}
    rules_by_identity: dict[RecordIdentity, BindingRule] = {}
    for rule in rules:
        if rule.resolved_intent_identity != resolved_intent.identity:
            raise ValidationError(
                "BindingRule belongs to a foreign ResolvedIntent lineage"
            )
        expected = external_by_slot.get(rule.symbolic_reference.slot_ref)
        if expected is None or expected.identity != rule.symbolic_reference.identity:
            raise ValidationError(
                "BindingRule must target an exact external symbolic reference from the WorkPlan"
            )
        if rule.symbolic_reference.slot_ref in rules_by_slot:
            raise ValidationError(
                "work/binding graph must not contain competing BindingRule records for one symbolic slot"
            )
        rules_by_slot[rule.symbolic_reference.slot_ref] = rule
        rules_by_identity[rule.identity] = rule

    evaluations_by_rule: dict[RecordIdentity, BindingEvaluation] = {}
    for evaluation in evaluations:
        supplied_rule = rules_by_identity.get(evaluation.rule.identity)
        if supplied_rule is None:
            raise ValidationError(
                "BindingEvaluation is orphaned from the supplied active BindingRule set"
            )
        if evaluation.rule != supplied_rule:
            raise ValidationError(
                "BindingEvaluation must embed the exact supplied BindingRule"
            )
        if evaluation.rule.identity in evaluations_by_rule:
            raise ValidationError(
                "work/binding graph must not contain competing active BindingEvaluation records for one rule"
            )
        evaluations_by_rule[evaluation.rule.identity] = evaluation

    missing = tuple(
        reference
        for reference in external
        if reference.slot_ref not in rules_by_slot
    )
    pending = tuple(
        rule
        for rule in rules
        if rule.identity not in evaluations_by_rule
    )
    bound = tuple(
        evaluation
        for evaluation in evaluations
        if type(evaluation) is BoundValue
    )
    issues = tuple(
        evaluation
        for evaluation in evaluations
        if type(evaluation) is BindingIssue
    )
    complete = not missing and not pending and not issues
    if not external:
        complete = True

    return WorkBindingFrontier(
        resolved_intent_identity=resolved_intent.identity,
        work_plan=work_plan,
        work_disposition_required=False,
        external_symbolic_references=external,
        missing_rule_references=missing,
        pending_rules=pending,
        bound_values=bound,
        binding_issues=issues,
        external_binding_complete=complete,
    )
