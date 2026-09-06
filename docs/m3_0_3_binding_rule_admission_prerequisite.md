# M3.0.3 — Binding Rule Admission Prerequisite

## Purpose

M3.0.3 closes the semantic gap between an unresolved external symbolic reference and an
active IRR `BindingRule`.

Before M3.0.3, M1.4 described `evaluate_binding(...)` as applying an already-admitted
bounded `BindingRule`, and M2.2 accepted a supplied `BindingRule` as active binding state,
but IRR had no explicit proposal/admission lifecycle for that rule.

That left integration hosts with a dangerous ambiguity: constructing a valid `BindingRule`
could silently become equivalent to deciding which sources are admissible and how a value
must be selected.

M3.0.3 adds the missing IRR-owned semantic transition:

```text
exact SymbolicReference
        ↓
CandidateBindingRule[]
        ↓
BindingRuleAdmissionFrontier
        ↓
explicit BindingRuleAdmitter
        ↓
AdmittedBindingRule
        ↓
exact embedded BindingRule may enter M2.2
```

## Why BindingRule needs admission

`BindingRule` is not merely a mechanical filter. It freezes material binding semantics,
including:

```text
allowed_input_roles
allowed_source_refs
allowed_source_identities
input_semantic_type
required_selection_scope
constraints
selection_policy
required temporal/completeness/evidence provenance
```

Therefore:

```text
valid BindingRule != active BindingRule
rule construction != rule admission
rule proposal != selection authority
```

A host must not gain semantic authority merely because it can instantiate a valid IR
record.

## Canonical records

M3.0.3 introduces canonical, content-addressed records:

```text
BindingRuleProposalAttribution
CandidateBindingRule
BindingRuleAdmissionAttribution
AdmittedBindingRule
```

`BindingRuleAdmissionFrontier` remains derived and non-canonical.

### CandidateBindingRule

`CandidateBindingRule` contains:

```text
proposal attribution
exact proposed BindingRule
rationale
```

It is proposal material only.

```text
CandidateBindingRule != active BindingRule
```

Proposal attribution and rationale are provenance/explanation, not voting weight or
semantic precedence.

Semantic candidate equivalence is based on the exact proposed `BindingRule`.

Therefore:

```text
same exact BindingRule + different proposer/rationale
→ ADMISSION_REQUIRED

materially distinct BindingRule values
→ ADJUDICATION_REQUIRED
```

Candidate order and count do not create precedence.

### AdmittedBindingRule

`AdmittedBindingRule` contains:

```text
exact admission attribution
exact admitted BindingRule
complete exact candidate provenance
```

It means only that one exact bounded rule has been admitted for one exact symbolic
reference.

It does not mean:

```text
BindingInput exists
input acquisition is authorized
binding evaluation succeeded
BoundValue exists
Governance approved
execution is authorized
```

## Frontier semantics

The derived frontier has four states:

```text
PROPOSAL_INPUT_REQUIRED
ADMISSION_REQUIRED
ADJUDICATION_REQUIRED
RULE_OUTPUT_AVAILABLE
```

No candidate is automatically admitted.

A unique candidate still requires explicit admission.

Semantically equivalent candidates still require explicit admission.

Divergent candidates require adjudication rather than hidden ranking, majority voting,
first-item selection, provider confidence, or presentation-order precedence.

## Explicit admission

A new `AdmittedBindingRule` may be created only through an explicit
`BindingRuleAdmitter` supplied together with exact
`BindingRuleAdmissionAttribution`.

The orchestrator validates that the output:

- targets the exact supplied `SymbolicReference`;
- belongs to the same `ResolvedIntent` lineage;
- preserves exact admission attribution;
- preserves complete exact candidate provenance.

Admitter abstention returns the same unresolved frontier.

```text
abstention != retry
```

## Historical semantic replay

Existing `AdmittedBindingRule` records may be supplied through `admitted_outputs` to
reconstruct `RULE_OUTPUT_AVAILABLE` without invoking a new admitter.

```text
historical replay != new admission transition
```

Competing admitted rules for the same symbolic-reference slice fail closed.

M3.0.3 does not define a durable repository or filesystem persistence protocol for these
records.

## Relationship to M1.4 evaluation

M1.4 remains unchanged:

```text
BindingRule
+ explicit BindingInput[]
+ BindingAttribution
        ↓
evaluate_binding(...)
        ↓
BoundValue | BindingIssue
```

`evaluate_binding(...)` remains purely mechanical over its supplied complete input set.
It performs no retrieval, ambient lookup, fallback, external effect, semantic-rule
mutation, or hidden selection policy.

M3.0.3 does not call `evaluate_binding(...)`.

## Relationship to M2.2 WorkBindingFrontier

Once one exact `AdmittedBindingRule` exists, its embedded exact rule may be projected into
the existing M2.2 orchestrator:

```text
AdmittedBindingRule.rule
        ↓
orchestrate_work_binding(... binding_rules=(rule,))
        ↓
pending_rules = (rule,)
```

No `BindingInput` or `BindingEvaluation` is synthesized.

Therefore:

```text
admitted rule != completed binding
pending rule != input acquisition permission
```

## BindingInput remains a separate authority boundary

`BindingInput` is attributable data with:

```text
source_ref
source_identity
role
semantic_type
value
selection_scope
value_scope
attributes
provenance references
```

M3.0.3 deliberately does not answer how those records are acquired or who may disclose
or construct them.

That is a later integration boundary.

This preserves:

```text
rule says HOW supplied data may be selected
!=
input says WHAT attributable data is available
!=
evaluation mechanically applies the rule
```

## Frozen invariants

```text
valid BindingRule != admitted BindingRule
CandidateBindingRule != admitted BindingRule
proposal attribution != admission authority
candidate count != voting authority
candidate order != precedence
rationale != semantic precedence

BindingRule != BindingInput
rule admission != input acquisition
rule admission != binding evaluation
AdmittedBindingRule != BoundValue
BindingIssue != retry authority

BindingAttribution != Authorization
BoundValue != Authorization
binding completion != execution permission

semantic replay != new admission
Host mechanism != binding semantic authority
```

## Non-goals

M3.0.3 does not implement:

- BindingInput acquisition or disclosure;
- source discovery or retrieval;
- binding evaluation orchestration;
- capability requirements or matching;
- Governance or Authorization;
- Runplane/Executor handoff;
- retry or fallback;
- persistence for admitted binding-rule history;
- Worker creation or delegation.

## HDE integration consequence

HDE M32.4 can now safely treat an M32.3 `missing_rule_reference` as a request for an IRR
rule-admission slice instead of constructing an active bare `BindingRule` itself.

The next HDE boundary should stop after projecting exact admitted rules into M2.2 as
`pending_rules`.

BindingInput acquisition and `evaluate_binding(...)` should remain later, separate
boundaries.
