from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    BindingAttribution,
    BindingInput,
    BindingInputRole,
    BindingIssue,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    BoundValue,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
    SymbolicReference,
    ValidationError,
    WorkContinuationMode,
    WorkLiteralInput,
    WorkOutput,
    WorkPlan,
    WorkStep,
    WorkSymbolicInput,
    evaluate_binding,
)
from intent_resolution_runtime.work_binding import WorkBindingFrontier, orchestrate_work_binding


def _rid(ch: str) -> RecordIdentity:
    return RecordIdentity("sha256", ch * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _resolved(label: str = "main") -> ResolvedIntent:
    return ResolvedIntent(
        intent_request_identity=_rid("1"),
        context_envelope_identity=_rid("2"),
        admission_attribution=ResolutionAttribution(
            _ref("irr.resolver", "m2.2-test"),
            _ref("irr.resolution_event", f"resolved-{label}"),
        ),
        semantics=f"Admitted operational semantics for {label}.",
    )


def _symbol(
    resolved: ResolvedIntent,
    name: str,
    *,
    semantic_type: str = "artifact.path",
    selection_scope: str = "admitted workspace backups",
) -> SymbolicReference:
    return SymbolicReference(
        resolved_intent_identity=resolved.identity,
        slot_ref=_ref("irr.symbol", name),
        semantic_type=semantic_type,
        selection_scope=selection_scope,
        description=f"symbolic {name}",
    )


def _plan_with_external_symbols(
    resolved: ResolvedIntent,
    symbols: tuple[SymbolicReference, ...],
    *,
    label: str = "external",
) -> WorkPlan:
    plan_ref = _ref("irr.work_plan", label)
    step = WorkStep(
        resolved_intent_identity=resolved.identity,
        work_plan_ref=plan_ref,
        step_ref=_ref("irr.work_step", f"{label}-step"),
        operation="artifact.inspect",
        scope="bounded admitted artifact inputs",
        inputs=tuple(
            WorkSymbolicInput(name=f"input_{index}", reference=symbol)
            for index, symbol in enumerate(symbols)
        ),
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract="The bounded artifact inspection result is produced.",
        description="Inspect explicitly bound artifacts.",
    )
    return WorkPlan(
        resolved_intent_identity=resolved.identity,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="The bounded inspection plan completes.",
        description="External symbolic input plan.",
    )


def _literal_only_plan(resolved: ResolvedIntent, *, label: str = "literal") -> WorkPlan:
    plan_ref = _ref("irr.work_plan", label)
    step = WorkStep(
        resolved_intent_identity=resolved.identity,
        work_plan_ref=plan_ref,
        step_ref=_ref("irr.work_step", f"{label}-step"),
        operation="artifact.inspect",
        scope="bounded literal artifact descriptor",
        inputs=(WorkLiteralInput("descriptor", "artifact.label", "report"),),
        outputs=(),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract="The literal artifact descriptor is inspected.",
        description="Inspect a literal descriptor.",
    )
    return WorkPlan(
        resolved_intent_identity=resolved.identity,
        plan_ref=plan_ref,
        steps=(step,),
        completion_contract="The literal-only plan completes.",
        description="Literal-only plan.",
    )


def _internal_symbol_plan(
    resolved: ResolvedIntent,
    symbol: SymbolicReference,
    *,
    label: str = "internal",
) -> WorkPlan:
    plan_ref = _ref("irr.work_plan", label)
    producer_ref = _ref("irr.work_step", f"{label}-producer")
    producer = WorkStep(
        resolved_intent_identity=resolved.identity,
        work_plan_ref=plan_ref,
        step_ref=producer_ref,
        operation="filesystem.search",
        scope="bounded admitted directory",
        inputs=(),
        outputs=(WorkOutput("result", symbol),),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract="One bounded search result set is produced.",
        description="Produce a plan-local symbolic value.",
    )
    consumer = WorkStep(
        resolved_intent_identity=resolved.identity,
        work_plan_ref=plan_ref,
        step_ref=_ref("irr.work_step", f"{label}-consumer"),
        operation="artifact.inspect",
        scope="the plan-local search result",
        inputs=(WorkSymbolicInput("result", symbol),),
        outputs=(),
        depends_on=(producer_ref,),
        continuation=WorkContinuationMode.NONE,
        completion_contract="The produced plan-local result is inspected.",
        description="Consume the plan-local symbolic value.",
    )
    return WorkPlan(
        resolved_intent_identity=resolved.identity,
        plan_ref=plan_ref,
        steps=(producer, consumer),
        completion_contract="Search and bounded inspection complete.",
        description="Internal symbolic dataflow plan.",
    )


def _rule(
    resolved: ResolvedIntent,
    symbol: SymbolicReference,
    *,
    label: str,
    source_identity: RecordIdentity | None = None,
) -> BindingRule:
    source_identity = source_identity or _rid("a")
    return BindingRule(
        resolved_intent_identity=resolved.identity,
        rule_ref=_ref("irr.binding_rule", label),
        symbolic_reference=symbol,
        allowed_input_roles=(BindingInputRole.CONTEXT,),
        allowed_source_refs=(_ref("host.source", "binding-index"),),
        allowed_source_identities=(source_identity,),
        input_semantic_type=symbol.semantic_type,
        required_selection_scope=symbol.selection_scope,
        constraints=(),
        selection_policy=BindingSelectionPolicy(BindingSelectionMode.REQUIRE_UNIQUE),
        description=f"Require one exact admitted value for {label}.",
    )


def _binding_input(
    resolved: ResolvedIntent,
    symbol: SymbolicReference,
    *,
    label: str,
    value: str,
    source_identity: RecordIdentity | None = None,
) -> BindingInput:
    source_identity = source_identity or _rid("a")
    return BindingInput(
        resolved_intent_identity=resolved.identity,
        input_ref=_ref("irr.binding_input", label),
        attribution=SourceAttribution(
            _ref("host.source", "binding-index"),
            _ref("host.event", f"binding-{label}"),
        ),
        role=BindingInputRole.CONTEXT,
        source_identity=source_identity,
        semantic_type=symbol.semantic_type,
        value=value,
        selection_scope=symbol.selection_scope,
        value_scope=value,
    )


def _evaluation(
    rule: BindingRule,
    inputs: tuple[BindingInput, ...],
    *,
    label: str,
):
    return evaluate_binding(
        rule,
        inputs,
        attribution=BindingAttribution(
            _ref("irr.binding_evaluator", "m2.2-test"),
            _ref("irr.binding_event", label),
        ),
    )


def test_no_work_plan_requires_explicit_work_disposition_without_claiming_no_work() -> None:
    resolved = _resolved()

    frontier = orchestrate_work_binding(resolved)

    assert isinstance(frontier, WorkBindingFrontier)
    assert frontier.work_plan is None
    assert frontier.work_disposition_required is True
    assert frontier.external_symbolic_references == ()
    assert frontier.external_binding_complete is False


def test_frontier_is_derived_runtime_view_not_canonical_ir() -> None:
    frontier = orchestrate_work_binding(_resolved())

    assert not hasattr(frontier, "canonical_bytes")
    assert not hasattr(frontier, "identity")


def test_binding_material_without_work_plan_is_orphaned() -> None:
    resolved = _resolved()
    symbol = _symbol(resolved, "archive")
    rule = _rule(resolved, symbol, label="archive")

    with pytest.raises(ValidationError, match="orphaned when no active WorkPlan"):
        orchestrate_work_binding(resolved, binding_rules=(rule,))


def test_foreign_work_plan_lineage_fails_closed() -> None:
    resolved = _resolved("main")
    foreign = _resolved("foreign")
    plan = _literal_only_plan(foreign)

    with pytest.raises(ValidationError, match="foreign ResolvedIntent lineage"):
        orchestrate_work_binding(resolved, work_plans=(plan,))


def test_competing_active_work_plans_fail_closed_without_precedence() -> None:
    resolved = _resolved()
    first = _literal_only_plan(resolved, label="first")
    second = _literal_only_plan(resolved, label="second")

    with pytest.raises(ValidationError, match="competing active WorkPlan"):
        orchestrate_work_binding(resolved, work_plans=(first, second))


def test_literal_only_plan_has_no_external_binding_requirement() -> None:
    resolved = _resolved()
    plan = _literal_only_plan(resolved)

    frontier = orchestrate_work_binding(resolved, work_plans=(plan,))

    assert frontier.work_disposition_required is False
    assert frontier.external_symbolic_references == ()
    assert frontier.missing_rule_references == ()
    assert frontier.pending_rules == ()
    assert frontier.bound_values == ()
    assert frontier.binding_issues == ()
    assert frontier.external_binding_complete is True


def test_plan_local_symbolic_output_is_not_misclassified_as_external_binding() -> None:
    resolved = _resolved()
    symbol = _symbol(resolved, "search-result")
    plan = _internal_symbol_plan(resolved, symbol)

    frontier = orchestrate_work_binding(resolved, work_plans=(plan,))

    assert frontier.external_symbolic_references == ()
    assert frontier.external_binding_complete is True


def test_external_symbol_without_rule_is_exposed_not_guessed() -> None:
    resolved = _resolved()
    symbol = _symbol(resolved, "archive")
    plan = _plan_with_external_symbols(resolved, (symbol,))

    frontier = orchestrate_work_binding(resolved, work_plans=(plan,))

    assert frontier.external_symbolic_references == (symbol,)
    assert frontier.missing_rule_references == (symbol,)
    assert frontier.pending_rules == ()
    assert frontier.external_binding_complete is False


def test_rule_without_evaluation_is_pending_not_implicitly_evaluated() -> None:
    resolved = _resolved()
    symbol = _symbol(resolved, "archive")
    plan = _plan_with_external_symbols(resolved, (symbol,))
    rule = _rule(resolved, symbol, label="archive")

    frontier = orchestrate_work_binding(
        resolved,
        work_plans=(plan,),
        binding_rules=(rule,),
    )

    assert frontier.missing_rule_references == ()
    assert frontier.pending_rules == (rule,)
    assert frontier.bound_values == ()
    assert frontier.external_binding_complete is False


def test_bound_value_completes_one_external_symbol_without_mutating_work_plan() -> None:
    resolved = _resolved()
    symbol = _symbol(resolved, "archive")
    plan = _plan_with_external_symbols(resolved, (symbol,))
    rule = _rule(resolved, symbol, label="archive")
    binding_input = _binding_input(
        resolved,
        symbol,
        label="archive-a",
        value="W:/backups/archive-a.zip",
    )
    evaluation = _evaluation(rule, (binding_input,), label="archive-eval")
    assert isinstance(evaluation, BoundValue)

    frontier = orchestrate_work_binding(
        resolved,
        work_plans=(plan,),
        binding_rules=(rule,),
        binding_evaluations=(evaluation,),
    )

    assert frontier.work_plan is plan
    assert frontier.bound_values == (evaluation,)
    assert frontier.binding_issues == ()
    assert frontier.external_binding_complete is True
    assert plan.steps[0].inputs[0].reference == symbol


def test_binding_issue_is_preserved_as_canonical_result_not_hidden_fallback() -> None:
    resolved = _resolved()
    symbol = _symbol(resolved, "archive")
    plan = _plan_with_external_symbols(resolved, (symbol,))
    rule = _rule(resolved, symbol, label="archive")
    evaluation = _evaluation(rule, (), label="zero-matches")
    assert isinstance(evaluation, BindingIssue)

    frontier = orchestrate_work_binding(
        resolved,
        work_plans=(plan,),
        binding_rules=(rule,),
        binding_evaluations=(evaluation,),
    )

    assert frontier.binding_issues == (evaluation,)
    assert frontier.bound_values == ()
    assert frontier.external_binding_complete is False


def test_complete_semantic_frontier_exposes_bound_pending_and_missing_slots_together() -> None:
    resolved = _resolved()
    alpha = _symbol(resolved, "alpha")
    beta = _symbol(resolved, "beta")
    gamma = _symbol(resolved, "gamma")
    plan = _plan_with_external_symbols(resolved, (alpha, beta, gamma), label="three")

    alpha_rule = _rule(resolved, alpha, label="alpha")
    beta_rule = _rule(resolved, beta, label="beta")
    alpha_input = _binding_input(
        resolved,
        alpha,
        label="alpha-input",
        value="W:/alpha.zip",
    )
    alpha_bound = _evaluation(alpha_rule, (alpha_input,), label="alpha-bound")
    assert isinstance(alpha_bound, BoundValue)

    frontier = orchestrate_work_binding(
        resolved,
        work_plans=(plan,),
        binding_rules=(beta_rule, alpha_rule),
        binding_evaluations=(alpha_bound,),
    )

    assert frontier.bound_values == (alpha_bound,)
    assert frontier.pending_rules == (beta_rule,)
    assert frontier.missing_rule_references == (gamma,)
    assert frontier.external_binding_complete is False


def test_frontier_preserves_binding_issue_and_independent_missing_rule_simultaneously() -> None:
    resolved = _resolved()
    alpha = _symbol(resolved, "alpha")
    beta = _symbol(resolved, "beta")
    plan = _plan_with_external_symbols(resolved, (alpha, beta), label="mixed")
    alpha_rule = _rule(resolved, alpha, label="alpha")
    alpha_issue = _evaluation(alpha_rule, (), label="alpha-issue")
    assert isinstance(alpha_issue, BindingIssue)

    frontier = orchestrate_work_binding(
        resolved,
        work_plans=(plan,),
        binding_rules=(alpha_rule,),
        binding_evaluations=(alpha_issue,),
    )

    assert frontier.binding_issues == (alpha_issue,)
    assert frontier.missing_rule_references == (beta,)
    assert frontier.external_binding_complete is False


def test_rule_targeting_internal_or_absent_symbol_is_orphaned() -> None:
    resolved = _resolved()
    internal = _symbol(resolved, "internal")
    plan = _internal_symbol_plan(resolved, internal)
    rule = _rule(resolved, internal, label="internal")

    with pytest.raises(ValidationError, match="exact external symbolic reference"):
        orchestrate_work_binding(
            resolved,
            work_plans=(plan,),
            binding_rules=(rule,),
        )


def test_foreign_rule_lineage_fails_closed() -> None:
    resolved = _resolved("main")
    foreign = _resolved("foreign")
    symbol = _symbol(resolved, "archive")
    foreign_symbol = SymbolicReference(
        foreign.identity,
        symbol.slot_ref,
        symbol.semantic_type,
        symbol.selection_scope,
        symbol.description,
    )
    plan = _plan_with_external_symbols(resolved, (symbol,))
    rule = _rule(foreign, foreign_symbol, label="foreign")

    with pytest.raises(ValidationError, match="foreign ResolvedIntent lineage"):
        orchestrate_work_binding(
            resolved,
            work_plans=(plan,),
            binding_rules=(rule,),
        )


def test_competing_rules_for_one_external_slot_fail_closed() -> None:
    resolved = _resolved()
    symbol = _symbol(resolved, "archive")
    plan = _plan_with_external_symbols(resolved, (symbol,))
    first = _rule(resolved, symbol, label="first", source_identity=_rid("a"))
    second = _rule(resolved, symbol, label="second", source_identity=_rid("b"))

    with pytest.raises(ValidationError, match="competing BindingRule"):
        orchestrate_work_binding(
            resolved,
            work_plans=(plan,),
            binding_rules=(first, second),
        )


def test_evaluation_without_exact_supplied_rule_is_orphaned() -> None:
    resolved = _resolved()
    symbol = _symbol(resolved, "archive")
    plan = _plan_with_external_symbols(resolved, (symbol,))
    rule = _rule(resolved, symbol, label="archive")
    binding_input = _binding_input(
        resolved,
        symbol,
        label="archive",
        value="W:/archive.zip",
    )
    evaluation = _evaluation(rule, (binding_input,), label="archive")

    with pytest.raises(ValidationError, match="orphaned from the supplied active BindingRule set"):
        orchestrate_work_binding(
            resolved,
            work_plans=(plan,),
            binding_evaluations=(evaluation,),
        )


def test_competing_active_evaluations_for_one_rule_fail_closed() -> None:
    resolved = _resolved()
    symbol = _symbol(resolved, "archive")
    plan = _plan_with_external_symbols(resolved, (symbol,))
    rule = _rule(resolved, symbol, label="archive")
    first = _evaluation(rule, (), label="first")
    second = _evaluation(rule, (), label="second")
    assert first.identity != second.identity

    with pytest.raises(ValidationError, match="competing active BindingEvaluation"):
        orchestrate_work_binding(
            resolved,
            work_plans=(plan,),
            binding_rules=(rule,),
            binding_evaluations=(first, second),
        )


def test_rule_and_evaluation_input_order_do_not_create_precedence() -> None:
    resolved = _resolved()
    alpha = _symbol(resolved, "alpha")
    beta = _symbol(resolved, "beta")
    plan = _plan_with_external_symbols(resolved, (alpha, beta), label="order")
    alpha_rule = _rule(resolved, alpha, label="alpha")
    beta_rule = _rule(resolved, beta, label="beta")
    alpha_input = _binding_input(resolved, alpha, label="alpha", value="W:/alpha")
    beta_input = _binding_input(resolved, beta, label="beta", value="W:/beta")
    alpha_bound = _evaluation(alpha_rule, (alpha_input,), label="alpha")
    beta_bound = _evaluation(beta_rule, (beta_input,), label="beta")

    first = orchestrate_work_binding(
        resolved,
        work_plans=(plan,),
        binding_rules=(alpha_rule, beta_rule),
        binding_evaluations=(alpha_bound, beta_bound),
    )
    second = orchestrate_work_binding(
        resolved,
        work_plans=(plan,),
        binding_rules=(beta_rule, alpha_rule),
        binding_evaluations=(beta_bound, alpha_bound),
    )

    assert first == second
    assert first.external_binding_complete is True


def test_frontier_contains_no_authority_or_execution_claim() -> None:
    resolved = _resolved()
    plan = _literal_only_plan(resolved)
    frontier = orchestrate_work_binding(resolved, work_plans=(plan,))

    text = repr(frontier).lower()
    assert "authorization" not in text
    assert "approved" not in text
    assert "executed" not in text
