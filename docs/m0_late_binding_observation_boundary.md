# M0.4 — Late Binding & Observation Boundary

Status: **normative for M0.4**.

This document freezes how Intent Resolution Runtime (IRR) may defer concrete values without deferring semantic decisions, how symbolic work data becomes bound, and when downstream information must return to IRR for continuation.

It extends M0.1 Product Charter & Vocabulary, M0.2 Trust/Context/Resolution Semantics, and M0.3 Intent → Work Boundary without introducing runtime code, exact Python schemas, execution adapters, or authority.

M0.4 answers one question:

> How may a bounded WorkPlan refer to values that are not known yet without allowing executors to make hidden semantic decisions?

The answer is **Late Binding under an explicit bounded Binding Rule**.

```text
resolved semantics
      |
      v
symbolic reference
      |
      v
bounded observation
      |
      v
binding rule
      |
      +---------------------------+
      |                           |
      v                           v
unique admissible value      new material choice
      |                           |
      v                           v
bound value                IRR Continuation
                                  |
                         clarification / successor
```

The central invariant is:

```text
late binding != deferred discretion
```

## 1. Late Binding defers a value, not a meaning

Late Binding is allowed only when the semantic rule for obtaining or selecting a future value is already explicit and bounded before that value is observed.

Example:

```text
"Use the newest backup by modification time."
```

The concrete backup path may be unknown when the plan is created, while the semantic rule is already known.

Conceptually:

```text
filesystem.search
    output -> backup_candidates

artifact.select
    input  <- $backup_candidates
    rule   <- newest by modification time
    output -> selected_backup
```

The future concrete path is late-bound.

The rule `newest by modification time` is not late-bound.

IRR MUST NOT use Late Binding to postpone a choice such as:

```text
"pick whichever backup seems best later"
```

or:

```text
"choose a launcher after looking at them"
```

when no bounded selection semantics have already been admitted.

```text
unknown value != unknown decision rule
```

## 2. Symbolic Reference

A `Symbolic Reference` denotes a future value needed by planned semantics but not yet concretely available.

A Symbolic Reference MUST remain distinguishable from:

- an observed value;
- a guessed value;
- an ambient lookup;
- a permission grant;
- an executable variable owned by a general-purpose scripting language.

Conceptually:

```text
$step1.backup_candidates
$step2.selected_backup
```

The notation above is illustrative only. Exact syntax is deferred to M1.

A Symbolic Reference MUST preserve enough semantic lineage for later contracts to determine what planned result or attributable future input it refers to.

M0.4 does not freeze exact IDs, path syntax, slot schemas, serialization, or digest representation.

```text
symbolic reference != observed value
symbolic reference != authority
```

## 3. Binding Rule

A `Binding Rule` is the explicit bounded semantic rule that determines how an admissible future value may satisfy a Symbolic Reference.

A Binding Rule MAY express bounded semantics such as:

- select the unique artifact with an exact declared name;
- choose the newest candidate by an explicit timestamp field;
- bind the process identifier returned by a specific prior launch step;
- bind the exact destination resolved from a previously explicit identifier;
- require exactly one candidate satisfying explicit constraints.

A Binding Rule MUST NOT mean:

- choose whichever candidate looks best;
- infer the most likely resource without an explicit rule;
- ask an executor to improvise;
- choose according to ambient UI order;
- choose the first returned result unless that ordering is itself an admitted semantic rule;
- silently invent a tie-breaker.

```text
binding rule != hidden heuristic
binding rule != executor discretion
```

The exact rule representation is deferred.

## 4. Binding is not semantic self-mutation

Applying an already admitted Binding Rule to compatible attributable data may concretize a Symbolic Reference without changing the semantic meaning of the WorkPlan.

Example:

```text
rule:
    newest by modification time

observation:
    backup-A.zip mtime=10:00
    backup-B.zip mtime=12:00

binding:
    selected_backup = backup-B.zip
```

If the rule was already part of the admitted work semantics, binding `backup-B.zip` is value instantiation, not a new semantic decision.

Therefore:

```text
binding != semantic plan mutation
```

M0.3's successor-plan rule still applies when new information changes material work semantics. M0.4 distinguishes that from merely filling a previously declared symbolic slot according to an unchanged rule.

Later identity/digest contracts may represent plans and binding environments separately. M0.4 freezes the semantic distinction, not that wire representation.

## 5. Binding MUST NOT rewrite the rule

A binding operation MUST NOT modify, broaden, weaken, or replace the Binding Rule in order to obtain a value.

If the admitted rule is:

```text
newest backup by modification time
```

and the available data lacks modification times, IRR or downstream orchestration MUST NOT silently reinterpret the rule as:

```text
first backup returned
```

or:

```text
largest backup
```

or:

```text
lexicographically last filename
```

The correct result is unresolved binding, additional attributable information if allowed, or IRR Continuation.

```text
missing rule inputs != permission to substitute a rule
```

## 6. Observation lineage

An Observation used for binding MUST remain attributable to the external boundary, prior bounded step, or other explicit source that produced it.

Material provenance MUST NOT be erased merely because the Observation is consumed by a deterministic Binding Rule.

At minimum, later representations must be able to preserve the semantic relationship between:

- the Observation;
- the step or external boundary that produced it;
- the symbolic value being bound;
- the Binding Rule applied;
- the resulting Bound Value.

Exact receipt, ID, digest, and lineage formats are deferred.

```text
bound value != provenance-free value
```

## 7. Observation eligibility

Not every Observation is eligible to satisfy every Symbolic Reference.

An Observation is usable for a binding only when its declared semantics are compatible with what the Symbolic Reference and Binding Rule require.

For example, a rule requiring:

```text
newest by modification time
```

cannot be satisfied by an Observation that contains only filenames with no attributable modification-time data.

Similarly, a process identifier produced by one launch operation MUST NOT silently satisfy a symbolic reference expecting the result of a different launch operation merely because both values are integers.

Compatibility is semantic, not merely structural.

```text
same shape != same meaning
```

Exact type contracts are deferred to M1 and capability-output contracts to M0.5.

## 8. Observation scope, completeness, and freshness remain material

Binding does not erase M0.2 trust semantics.

A Binding Rule may require Observation properties such as:

- bounded scope;
- declared completeness;
- temporal basis;
- freshness;
- source identity;
- specific evidence fields.

If those properties are material and unsupported, the binding MUST remain unresolved.

Example:

```text
rule:
    latest backup in D:\Backups
```

A partial listing that explicitly covers only one subdirectory cannot silently prove the latest backup across all of `D:\Backups`.

Likewise, an undated cached listing cannot silently satisfy a rule whose meaning depends on `latest now` when freshness is material.

```text
binding does not amplify evidence
binding does not imply completeness
binding does not imply freshness
```

## 9. Zero matches

A bounded rule may produce no admissible value.

Example:

```text
rule:
    exactly one artifact named release.zip

observation:
    no matching artifact
```

Zero matches MUST NOT cause IRR or an executor to invent a fallback artifact.

Zero matches may represent:

- a valid bounded negative observation when completeness supports it;
- an unresolved information need;
- a missing resource condition;
- a reason for IRR Continuation;
- a downstream failure or blocked state under later contracts.

M0.4 does not freeze the terminal state enum.

```text
zero matches != permission to guess
```

## 10. Multiple matches and deterministic selection

Multiple observed candidates do not automatically imply Material Ambiguity.

If an explicit Binding Rule deterministically and uniquely selects one candidate, binding may proceed.

Example:

```text
rule:
    newest by modification time

candidates:
    A at 10:00
    B at 12:00
```

selects `B` without a new semantic decision.

However, if the rule does not determine a unique result, the binding MUST NOT proceed.

Example:

```text
A at 12:00
B at 12:00
```

with no admitted tie-breaker.

That produces a new material choice if the selected artifact affects downstream work.

```text
tie under material selection rule -> IRR Continuation
```

IRR MUST NOT use result order, filename order, provider ranking, UI ordering, or another hidden preference as an implicit tie-breaker.

## 11. Selection order is semantic only when admitted

A result sequence may have presentation order without carrying semantic ranking.

Therefore:

```text
first result != preferred result by default
presentation order != binding precedence
```

A Binding Rule MAY intentionally use an ordering only when that ordering itself is semantically defined and attributable.

For example:

```text
source contract:
    results sorted descending by signed monotonic sequence

binding rule:
    choose highest sequence
```

may be valid if the ordering semantics are part of the admitted evidence.

M0.4 does not invent universal ordering semantics.

## 12. Plan-local dataflow versus IRR Continuation

Not every intermediate WorkStep result requires a new IRR resolution cycle.

If all material semantics are already fixed, a bounded downstream path MAY carry an attributable value through symbolic dataflow and apply a pre-admitted Binding Rule without asking IRR to make a new semantic decision.

Conceptually:

```text
filesystem.search
      |
      v
backup_candidates
      |
      v
artifact.select(rule=newest_by_mtime)
      |
      v
selected_backup
      |
      v
archive.inspect
```

This plan-local dataflow does not grant IRR ambient context and does not imply that every intermediate Observation becomes newly admitted Context for unrelated resolution purposes.

If the intermediate result creates a new material decision, the downstream path MUST stop at the applicable continuation boundary and return attributable information to IRR.

```text
fixed semantics -> bounded dataflow MAY continue
new material semantics -> IRR Continuation REQUIRED
```

## 13. Downstream binding does not create authority

A downstream executor or bounded capability may apply an explicit Binding Rule as part of an already represented operation when later capability contracts permit it.

That does not make the executor an intent resolver or Governance authority.

The executor MUST NOT:

- invent a missing Binding Rule;
- broaden the selection scope;
- choose between materially different meanings;
- add new effects to make the binding succeed;
- interpret a failed binding as permission to try another semantic operation.

```text
deterministic binding != semantic discretion
deterministic binding != authorization
```

M0.4 does not freeze where a specific implementation performs the mechanical rule application. It freezes that no component may convert mechanical binding into hidden semantic choice.

## 14. Authorization and binding remain separate

Late Binding does not decide when Governance must inspect or authorize concrete values.

A future Governance contract may require:

- authorization before binding;
- authorization after concrete binding;
- re-review when a bound resource becomes known;
- constraints on which values a symbolic slot may accept.

M0.4 does not choose that policy.

It freezes only:

```text
bound value != authorization
binding success != permission
```

M0.6 freezes the Governance boundary in detail.

## 15. Bound Value

A `Bound Value` is the concrete value associated with a Symbolic Reference after an admissible Binding Rule has been applied to compatible attributable input.

A Bound Value MUST preserve semantic relationship to:

- the symbolic slot it satisfies;
- the Binding Rule;
- the attributable input or Observation used;
- material scope/freshness/completeness limitations relevant to downstream interpretation.

A Bound Value is not automatically:

- true beyond its evidence;
- authorized;
- immutable world state;
- valid forever;
- transferable to unrelated symbolic slots.

```text
bound value != timeless fact
bound value != permission
```

Exact binding-record schemas are deferred.

## 16. Stale bindings and world drift

The external world may change after a value is bound.

For example:

```text
selected_backup = D:\Backups\backup-42.zip
```

may later refer to a file that was deleted, replaced, or changed.

M0.4 MUST NOT treat successful binding as permanent proof that the world still matches the Observation.

If freshness or identity is material at execution time, later capability or Governance contracts may require revalidation.

Revalidation MUST NOT silently change the bound value to another resource unless an already admitted Binding Rule explicitly permits a new binding under the applicable lifecycle.

```text
stale binding != permission to reselect silently
```

Exact revalidation and drift handling are deferred to later milestones.

## 17. Rebinding

A Symbolic Reference MUST NOT silently rebind from one concrete value to another after downstream inspection, authorization, or execution semantics depend on the original binding.

If later attributable information requires a materially different bound value, IRR MUST preserve that change through an explicit lifecycle path rather than pretending the original binding never existed.

Depending on later lifecycle contracts, that may require:

- a new binding instance;
- IRR Continuation;
- a Successor WorkPlan;
- Governance re-review;
- rejection of the stale work path.

M0.4 freezes the non-silent-rebinding invariant, not exact state transitions.

```text
rebind != overwrite history
```

## 18. Binding failure does not authorize fallback

If a Binding Rule cannot be satisfied, IRR or downstream execution MUST NOT silently substitute:

- another rule;
- another resource class;
- another scope;
- another service;
- arbitrary shell logic;
- a broader search;
- a user-like discretionary guess.

The failure remains explicit and returns through the applicable bounded lifecycle.

```text
binding failure != fallback authority
```

This preserves M0.3's no-hidden-fallback boundary.

## 19. Observation may reveal new semantics

An Observation can do more than supply a value.

It may reveal:

- a previously unknown resource class;
- a conflict;
- a tie;
- an additional recipient;
- a new disclosure requirement;
- a different executable target;
- a new mutation surface;
- missing prerequisites;
- changed cost or commitment;
- evidence that invalidates an earlier assumption.

When such information can materially change the next bounded path, it MUST NOT be consumed as mere binding data.

It becomes continuation-relevant semantic input.

```text
material new information != mechanical binding input
```

## 20. Continuation boundary

An `IRR Continuation` consumes attributable prior IRR state plus new clarification, Observation, or Outcome while preserving parent intent lineage.

M0.4 freezes when continuation is required for late-binding scenarios:

Continuation is REQUIRED when new information introduces or exposes a material semantic decision not already determined by admitted semantics.

Examples:

- two tied latest backups with no tie-breaker;
- two plausible launchers after archive inspection;
- a selected resource requires external disclosure not represented in the plan;
- an expected local operation now requires privilege escalation;
- a prior assumption is contradicted in a way that changes downstream work.

Continuation MAY produce:

```text
clarification
successor ResolvedIntent
successor WorkPlan
no-work completion
explicit inability to continue
```

Exact lifecycle/state-machine representation remains deferred.

## 21. Continuation is not automatic permission to observe more

Returning to IRR does not grant authority to collect additional data.

If Continuation identifies another Information Need or Observation Need, M0.2 still applies:

```text
information need != observation authority
continuation != retrieval authority
```

Any new observation effect remains external to IRR and subject to later capability/Governance contracts.

## 22. Observation classification remains semantic

A returned value is not an Observation merely because it came from execution.

Likewise, retrieval does not automatically make data observational.

The Host or downstream contract must preserve whether returned material is:

- plan-local output;
- an Observation intended for IRR Continuation;
- Context supplied through the Host boundary;
- an Outcome from an Executor or Worker;
- another explicitly classified attributable input.

M0.4 MUST NOT collapse these categories merely because they all contain data.

```text
returned data != Observation by default
```

## 23. Observation versus Outcome

An Observation describes attributable information relevant to resolution or binding.

An Outcome is an attributable reported result of Executor or Worker activity.

One downstream event may later produce both observational information and an Outcome, but those meanings MUST remain distinguishable.

For example:

```text
archive.inspect succeeded
```

may be an Outcome about the inspect operation, while:

```text
two launchers found: A.exe, B.exe
```

is Observation material relevant to continuation.

M0.9 freezes exact Outcome states.

```text
observation != outcome
```

## 24. Observation does not inherit execution authority

An Observation created by an authorized operation does not inherit that operation's authority.

For example, authorization to list a directory does not mean that every returned file is authorized for deletion, execution, disclosure, or future mutation.

```text
authorized observation effect != authority over observed resources
```

Observed resources may require separate Governance decisions under later contracts.

## 25. Chained symbolic dataflow

A bounded WorkPlan MAY contain finite chains of symbolic dependencies.

Example:

```text
filesystem.search
    -> backup_candidates

artifact.select
    <- backup_candidates
    -> selected_backup

archive.inspect
    <- selected_backup
    -> archive_manifest

workspace.select_launcher
    <- archive_manifest
    -> launcher
```

Each symbolic dependency MUST remain semantically attributable and must respect the finite acyclic Work Dependency graph frozen by M0.3.

A chain MUST stop for IRR Continuation when a new material semantic decision appears.

Symbolic chaining MUST NOT become an autonomous planner loop.

## 26. No implicit cross-slot substitution

A value bound to one Symbolic Reference MUST NOT silently satisfy another merely because the values have compatible primitive types or similar names.

For example:

```text
$selected_backup
```

must not automatically satisfy:

```text
$launch_target
```

because both happen to be paths.

```text
structural compatibility != semantic substitutability
```

Exact typing rules are deferred.

## 27. No hidden widening during observation

A bounded observation or binding step MUST NOT silently widen its scope merely because the initial scope did not produce a value.

Example:

```text
search D:\Backups
```

must not become:

```text
search all drives
```

without an explicit new semantic decision and applicable downstream authority.

```text
empty bounded result != permission to widen scope
```

This preserves M0.2 Context Boundary and M0.3 Plan Derivation semantics.

## 28. Relationship to the backup scenario

Intent:

```text
"Find the newest organism_lab backup in D:\Backups,
extract it to W:\organism_lab,
and launch the project."
```

A valid conceptual path may be:

```text
Step 1
filesystem.search(scope=D:\Backups, constraint=organism_lab backup)
output -> $backup_candidates

Step 2
artifact.select(
    input=$backup_candidates,
    rule=newest by modification time
)
output -> $selected_backup

Step 3
archive.inspect(input=$selected_backup)
output -> $archive_manifest

Step 4
archive.extract(
    input=$selected_backup,
    destination=W:\organism_lab
)

Step 5
workspace.inspect(input=W:\organism_lab)
output -> $launcher_candidates
```

If `$launcher_candidates` contains exactly one admissible launcher under an explicit rule, downstream binding may continue.

If it contains two materially different launchers and no admitted selection rule:

```text
$launcher_candidates
        |
        v
new material choice
        |
        v
IRR Continuation
        |
        v
Clarification
```

IRR MUST NOT choose one silently.

## 29. Relationship to authority

M0.4 freezes no permission policy.

A plan may have symbolic resources, bound resources, observations, and continuation points without any of those granting authority.

The following distinctions are mandatory:

```text
symbolic reference != authority
binding rule != authorization
observation != permission
bound value != permission
continuation != authority
```

M0.6 freezes Governance semantics.

## 30. Relationship to later milestones

M0.4 intentionally leaves these details to later contracts:

- M0.5 — Capability Catalog, capability I/O contracts, effect metadata, scope requirements, availability, and drift;
- M0.6 — Governance and authorization around symbolic or concrete resources;
- M0.7 — Cognitive Provider behavior when proposing symbolic/binding semantics;
- M0.8 — Worker observations and delegated-work continuation;
- M0.9 — failure, interruption, retry, unknown outcome, and recovery;
- M1 — exact immutable schemas, symbolic-reference identifiers, binding records, validation, serialization, identities, and digests.

Later milestones may refine representation but MUST preserve the Late Binding and Observation boundary frozen here.

## 31. M0.4 exclusions

M0.4 intentionally does NOT freeze:

- Python classes, enums, protocols, or serialization;
- exact `SymbolicReference` fields or syntax;
- exact `BindingRule` representation;
- exact `BoundValue` or binding-record schema;
- exact Observation or ObservationNeed schema;
- exact capability input/output contracts;
- execution scheduling;
- where mechanical Binding Rule evaluation runs in a concrete architecture;
- concrete trust/evidence enums;
- Governance policy or consent rules;
- plan/step/binding IDs, digests, persistence, or receipt format;
- exact revalidation or stale-binding algorithms;
- exact Continuation state-machine transitions;
- retry/recovery behavior;
- terminal Outcome schemas.

M0.4 freezes semantic constraints, not implementation types.

## 32. Acceptance criteria

M0.4 is complete when the repository states unambiguously that:

1. Late Binding defers concrete values, not semantic decisions.
2. A Symbolic Reference is not an observed value, authority, or scripting variable.
3. Every material late-bound value is governed by an explicit bounded Binding Rule.
4. Binding Rule semantics cannot be silently rewritten to make a binding succeed.
5. Applying an unchanged Binding Rule to compatible attributable data is binding, not semantic WorkPlan self-mutation.
6. Bound Values retain material provenance and semantic lineage.
7. Observation compatibility is semantic rather than merely structural.
8. Binding preserves M0.2 scope, completeness, freshness, and evidentiary limitations.
9. Zero matches do not authorize guessing or scope widening.
10. Multiple candidates may bind only when the admitted rule uniquely determines the result.
11. Ties or unresolved material choices return to IRR Continuation.
12. Presentation order or first-result order is not implicit binding precedence.
13. Bounded plan-local symbolic dataflow may continue without a new IRR semantic decision when all material semantics are already fixed.
14. Downstream mechanical binding does not grant semantic discretion or authority.
15. Binding and Governance authorization remain separate.
16. A Bound Value is not a timeless fact or permission grant.
17. Stale bindings do not authorize silent reselection.
18. Rebinding cannot overwrite prior binding history silently.
19. Binding failure does not authorize fallback semantics.
20. Material new information is continuation input, not mechanical binding data.
21. Continuation is required when new information creates a material semantic decision not already determined by admitted semantics.
22. Continuation does not grant observation or retrieval authority.
23. Returned data is not automatically classified as Observation.
24. Observation and Outcome semantics remain distinguishable.
25. Authorized observation does not grant authority over observed resources.
26. Chained symbolic dataflow remains finite, acyclic, and stops at new semantic decisions.
27. Primitive type similarity does not permit cross-slot substitution.
28. Empty observation results do not permit hidden scope widening.
29. The backup scenario can proceed through symbolic dataflow but stops for clarification when launcher selection becomes materially ambiguous.
30. M0.5+, M0.6+, M0.7+, M0.8+, M0.9+, and M1 implementation details remain explicitly deferred.
31. No runtime code or `src/` tree is introduced.
