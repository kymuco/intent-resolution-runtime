# M2.2 — Work / Binding Orchestrator

Status: **implementation slice**.

M2.2 is the second runtime implementation built on the M2.0 Runtime Orchestration Charter. It derives the active work/binding frontier over an exact admitted `ResolvedIntent`, an optional active `WorkPlan`, and explicit M1.4 Binding records without collapsing independent symbolic slots into one mutable session status.

The central M2.2 choice is:

```text
complete work/binding frontier
!= one global binding status
```

A single WorkPlan may simultaneously contain:

```text
slot A -> BoundValue
slot B -> BindingRule present, evaluation pending
slot C -> BindingRule missing
slot D -> BindingIssue
```

The runtime must preserve all four facts at once.

## 1. Implemented boundary

```text
exact ResolvedIntent
+ zero or one active WorkPlan
+ explicit active BindingRule[]
+ explicit active BoundValue | BindingIssue[]
        |
        v
orchestrate_work_binding(...)
        |
        v
WorkBindingFrontier
```

`WorkBindingFrontier` is a derived runtime view, not a new canonical IR record.

```text
frontier != canonical lifecycle history
frontier != WorkPlan
frontier != Authorization
frontier != execution state
```

The canonical semantic history remains the exact M1 records supplied to and referenced by the frontier.

## 2. No global enum

M2.1 could use one narrow initial-resolution frontier kind because that slice has one active initial resolution branch.

M2.2 cannot safely do the same for a WorkPlan containing independent symbolic slots. A priority enum such as:

```text
MISSING_RULE
PENDING
BOUND
ISSUE
```

would hide information whenever different slots occupy different states.

M2.2 therefore exposes orthogonal collections:

```text
external_symbolic_references[]
missing_rule_references[]
pending_rules[]
bound_values[]
binding_issues[]
```

This implements the M2.0 rule:

```text
semantic frontier = complete eligible semantic surface
scheduler / presentation policy != semantic frontier
```

Array ordering is canonical presentation normalization only; it does not create semantic precedence.

## 3. Work disposition remains explicit

M1.5 froze:

```text
ResolvedIntent != WorkPlan requirement
```

A valid `ResolvedIntent` may be non-operational and require no WorkPlan at all.

M2.2 therefore does not interpret absence of a supplied WorkPlan as either:

```text
NO_OPERATIONAL_WORK
```

or:

```text
WORK_PLAN_REQUIRED
```

Instead the derived frontier exposes:

```text
work_disposition_required = true
```

meaning only that this Work/Binding slice does not have explicit active work disposition material from which to derive a WorkPlan binding surface.

```text
work_disposition_required
!= proof that work is required
!= proof that no work is required
!= permission to synthesize a WorkPlan
```

M2.2 does not add a canonical `NoOperationalWork` record and does not parse free-form `ResolvedIntent.semantics` to invent an operational classification.

## 4. Active WorkPlan graph admission

When a WorkPlan is supplied, it must preserve:

```text
WorkPlan.resolved_intent_identity == ResolvedIntent.identity
```

More than one active WorkPlan fails closed.

```text
WorkPlan A + WorkPlan B
!= choose first
!= choose newest
!= scheduler choice
```

M2.2 consumes a bounded active graph slice, not an unordered persistence bag. A future explicit WorkPlan successor/supersession model may permit richer history, but M2.2 does not infer such lineage from insertion order, timestamps, or `plan_ref` values.

Binding material without an active WorkPlan is rejected as orphan material in this slice.

## 5. External versus plan-local symbolic inputs

M1.5 allows a symbolic WorkStep input to be either:

- produced by another WorkStep in the same WorkPlan; or
- supplied/bound outside the plan under M1.4 Binding semantics.

M2.2 computes the exact **external symbolic reference set** by comparing WorkSymbolicInput slots against WorkOutput slots in the same already-valid WorkPlan.

```text
symbolic input with in-plan producer
-> plan-local dataflow
-> not an external binding requirement

symbolic input with no in-plan producer
-> external symbolic reference
-> requires explicit BindingRule / BindingEvaluation surface
```

The WorkPlan constructor already proves that an internal symbolic consumer depends transitively on its producer and that one symbolic output slot has one producer. M2.2 does not duplicate or weaken those invariants.

```text
plan-local output != ambient BindingInput
plan-local symbolic dependency != externally bound value
```

A later runtime slice may turn an actual plan-local returned value into an explicit attributable BindingInput when the frozen M1.4/M0.4 conditions are satisfied. M2.2 does not pretend that value exists before execution.

## 6. BindingRule admission against the WorkPlan

Every active BindingRule supplied to M2.2 must:

- belong to the exact ResolvedIntent lineage;
- target an exact external SymbolicReference appearing in the active WorkPlan;
- be the only active BindingRule for that symbolic slot.

A BindingRule targeting an internal symbolic output or a symbol absent from the WorkPlan is rejected as orphan material.

```text
nearby SymbolicReference != exact WorkPlan symbol
same slot name with different semantics != same symbol
```

Two different active rules for one external symbolic slot fail closed.

```text
rule A + rule B for one slot
!= choose canonical identity min
!= choose newest
!= evaluate both and pick success
```

Binding semantics were required to be fixed before runtime input arrived; M2.2 does not create a hidden rule-selection policy.

## 7. Why raw BindingInput[] is not a plan-level M2.2 input

M2.2 deliberately does **not** accept one undifferentiated bag of raw `BindingInput[]` and distribute those inputs among WorkPlan BindingRules.

That distribution can itself be material. One BindingInput may structurally resemble more than one rule surface, and assigning it to one rule rather than another could change binding outcomes.

```text
raw BindingInput availability
!= permission for orchestrator to invent rule association
```

The frozen M1.4 boundary already provides the exact explicit operation:

```text
evaluate_binding(
    exact BindingRule,
    exact complete BindingInput[],
    exact BindingAttribution,
)
-> BoundValue | BindingIssue
```

M2.2 consumes those canonical `BoundValue | BindingIssue` results.

This preserves:

```text
BindingInput-to-rule association
!= hidden orchestration discretion
```

If a Host wants M2.2 to drive acquisition/evaluation automatically later, that association and acquisition boundary must first become explicit and attributable rather than inferred from a global input pool.

## 8. BindingEvaluation graph admission

Each supplied active BindingEvaluation is an exact M1.4:

```text
BoundValue | BindingIssue
```

and embeds the BindingRule and complete BindingInput set that produced it.

M2.2 requires the embedded rule to match one exact active BindingRule supplied for the WorkPlan.

An evaluation whose rule is absent from the active rule set is rejected as orphan material.

More than one active BindingEvaluation for the same exact rule fails closed.

```text
evaluation A + evaluation B
!= choose latest
!= prefer BoundValue over BindingIssue
!= prefer successful-looking result
```

This is an active-slice rule, not a claim that historical re-evaluation can never exist. M2.2 simply has no admitted supersession lineage that would permit it to decide which of several records is active.

## 9. Missing rule state

For every external symbolic reference with no supplied active BindingRule, the frontier preserves that exact SymbolicReference in:

```text
missing_rule_references[]
```

This does not invent a rule and does not mean any available input can be used.

```text
missing BindingRule
!= missing value only
!= provider discretion
!= fallback rule authority
```

The semantic rule must remain explicit before mechanical binding can proceed.

## 10. Pending evaluation state

An exact active BindingRule with no supplied `BoundValue | BindingIssue` appears in:

```text
pending_rules[]
```

This means only that the active lifecycle graph does not yet contain a canonical evaluation result for that rule.

```text
pending rule
!= permission to retrieve inputs
!= permission to choose BindingInputs
!= proof inputs are unavailable
!= implicit evaluate_binding call
```

M2.2 does not acquire BindingInput or manufacture BindingAttribution.

## 11. BoundValue state

A supplied exact BoundValue is preserved in:

```text
bound_values[]
```

M2.2 does not copy the selected string into the WorkPlan or replace WorkSymbolicInput with a literal input.

```text
BoundValue != WorkPlan mutation
BoundValue != new WorkPlan identity
```

The immutable WorkPlan remains the admitted semantic plan and the BoundValue remains the canonical binding result that concretizes one external symbol.

This separation preserves provenance and avoids rewriting historical work semantics after a future value becomes known.

## 12. BindingIssue state

A supplied exact BindingIssue is preserved in:

```text
binding_issues[]
```

M2.2 does not interpret every BindingIssue as the same next action.

M1.4 explicitly froze:

```text
BindingIssue != generic IRR Continuation
BindingIssue != fallback permission
```

A later orchestration/continuation slice may decide whether a particular issue can be addressed by more attributable BindingInput under the unchanged rule or requires semantic re-entry through M1.7 ContinuationInput.

M2.2 therefore preserves the issue without silently:

- retrying evaluation;
- acquiring new input;
- changing the rule;
- choosing a tie-break;
- switching capability/provider;
- producing a successor Resolution.

## 13. Complete frontier, not priority state

For three external slots, M2.2 may legitimately return one frontier containing:

```text
bound_values = [slot A]
pending_rules = [slot B]
missing_rule_references = [slot C]
```

Likewise a BindingIssue for one slot and a missing rule for another remain simultaneously visible.

```text
one issue != hide independent missing rule
one missing rule != hide already-bound value
```

This is important for future Host orchestration because independent preparation work may remain visible without letting a scheduler redefine semantics.

## 14. external_binding_complete

The derived boolean:

```text
external_binding_complete
```

is true only when an active WorkPlan exists and every external symbolic slot has one exact BoundValue, with no missing rule, pending rule, or BindingIssue state.

A WorkPlan with no external symbolic references is externally binding-complete by definition.

The name is deliberately narrow.

```text
external_binding_complete
!= WorkPlan executable
!= Capability Match
!= capability availability
!= invocation readiness
!= Governance approval
!= Authorization
!= Attempt
!= Outcome
!= plan completion
!= parent intent satisfaction
```

M2.3 owns the next Capability/Governance orchestration boundary.

## 15. Derived frontier is non-canonical

`WorkBindingFrontier` is immutable and slotted for runtime hygiene but intentionally has no:

```text
canonical_bytes()
identity
wire schema
```

It is reconstructible from the explicit active M1 graph slice.

Persisting the frontier instead of the underlying WorkPlan / BindingRule / BoundValue / BindingIssue records would violate the M2.0 source-of-truth model.

## 16. What M2.2 does not add

M2.2 does not add:

- WorkPlan synthesis;
- a canonical operational/non-operational disposition record;
- provider planning transport;
- raw BindingInput acquisition;
- ambient Context or Observation retrieval;
- automatic BindingInput-to-rule association;
- automatic evaluate_binding invocation;
- BindingRule synthesis;
- hidden tie-breaking;
- WorkPlan mutation after Binding;
- capability requirement construction;
- Capability Catalog lookup;
- Governance;
- Authorization;
- executor/worker invocation;
- Attempt/Outcome lifecycle;
- automatic ContinuationInput construction from BindingIssue;
- retry/fallback;
- persistence;
- one mutable global work/binding status.

## 17. M2.2 invariants

```text
complete work/binding frontier != one global status
frontier != canonical record

ResolvedIntent != WorkPlan requirement
work_disposition_required != WorkPlan required
work_disposition_required != no operational work

competing active WorkPlans != precedence
plan-local symbolic output != external binding requirement

BindingRule must target exact external WorkPlan symbol
competing BindingRules != hidden rule choice
missing BindingRule != fallback authority

raw BindingInput pool != implicit rule association
pending BindingRule != retrieval authority

BindingEvaluation must embed exact active BindingRule
competing active BindingEvaluations != latest-wins

BoundValue != WorkPlan mutation
BindingIssue != generic Continuation
BindingIssue != automatic retry

external_binding_complete != executability
external_binding_complete != Capability Match
external_binding_complete != Authorization
```

## 18. Acceptance

M2.2 is complete when executable tests prove at least:

```text
no WorkPlan -> neutral work_disposition_required frontier
frontier has no canonical identity/wire surface
binding material without WorkPlan is orphaned
foreign WorkPlan lineage fails closed
competing active WorkPlans fail closed
literal-only WorkPlan requires no external binding
plan-local symbolic output is not treated as external binding
external symbolic input without rule remains explicitly missing
BindingRule without evaluation remains pending
exact BoundValue completes one external binding without WorkPlan mutation
BindingIssue remains explicit and blocks external_binding_complete
one frontier can simultaneously expose bound + pending + missing slots
one frontier can expose BindingIssue + independent missing rule
rule targeting internal/absent symbol fails closed
foreign BindingRule lineage fails closed
competing rules for one slot fail closed
BindingEvaluation without exact active rule is orphaned
competing active evaluations for one rule fail closed
rule/evaluation input order does not create precedence
frontier contains no authority/execution claim
all frozen M0/M1/M2.1 tests remain green
Python 3.11–3.14 CI passes
```

After M2.2 closes, the next planned slice is **M2.3 — Capability / Governance Orchestrator**.
