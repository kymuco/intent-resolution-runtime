# M0.4 — Late Binding & Observation Boundary

Status: **normative for M0.4**.

This document freezes how Intent Resolution Runtime (IRR) may defer concrete values without deferring semantic decisions, how symbolic work data becomes bound, and when new downstream information must return to IRR for continuation.

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
attributable Binding Input
      |
      v
binding rule
      |
      +---------------------------+
      |                           |
      v                           v
admissible bound value       new material choice
      |                           |
      v                           v
bounded dataflow           IRR Continuation
                                  |
                         clarification / successor
```

The central invariant is:

```text
late binding != deferred discretion
```

## 1. Late Binding defers a value, not a meaning

Late Binding is allowed only when the semantic rule for obtaining or selecting a future value is already explicit and bounded before that value becomes available.

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
- ambient lookup state;
- a permission grant;
- a general-purpose scripting variable.

Conceptually:

```text
$step1.backup_candidates
$step2.selected_backup
```

The notation is illustrative only. Exact syntax is deferred to M1.

A Symbolic Reference MUST preserve enough semantic lineage for later contracts to identify the planned result or attributable future input it refers to.

```text
symbolic reference != observed value
symbolic reference != authority
```

## 3. Binding Input

A `Binding Input` is attributable data supplied to a Binding Rule for the purpose of concretizing a Symbolic Reference.

Binding Input is a semantic role, not a universal data class.

Depending on the surrounding contract, Binding Input may be:

- a plan-local output from a prior bounded WorkStep;
- an Observation explicitly returned to IRR and later used during Continuation;
- attributable Context supplied through the Host boundary;
- another future input explicitly permitted by later contracts.

Therefore:

```text
Binding Input != Observation by default
Binding Input != Context by default
Binding Input != Outcome by default
```

M0.4 MUST NOT reclassify all WorkStep outputs as Observations merely because they contain information.

This preserves the M0.2 Observation boundary while allowing M0.3 symbolic dataflow to operate without forcing every intermediate value through a new IRR resolution cycle.

## 4. Binding Rule

A `Binding Rule` is the explicit bounded semantic rule that determines how compatible Binding Input may satisfy a Symbolic Reference.

A Binding Rule MAY express bounded semantics such as:

- select the unique artifact with an exact declared name;
- choose the newest candidate by an explicit timestamp field;
- bind the process identifier returned by a specific prior launch step;
- bind the exact destination resolved from a previously explicit identifier;
- require exactly one candidate satisfying explicit constraints.

A Binding Rule MUST NOT mean:

- choose whichever candidate looks best;
- infer the most likely resource without an explicit rule;
- ask an Executor to improvise;
- choose according to ambient UI order;
- choose the first returned result unless that ordering is itself admitted semantics;
- silently invent a tie-breaker.

```text
binding rule != hidden heuristic
binding rule != executor discretion
```

The exact rule representation is deferred.

### 4.1 Binding Rule evaluation is effect-free

A Binding Rule consumes already supplied Binding Input. Evaluating the rule MUST NOT itself acquire new external information or perform a new external effect.

A Binding Rule MUST NOT silently:

- read additional files;
- query a repository, browser, account, network, or service;
- inspect ambient machine state;
- consult an ambient wall clock when time is material;
- widen a search scope;
- execute a process;
- mutate external state.

If required Binding Input is missing, the binding remains unresolved. A later lifecycle may represent an Information Need or Observation Need, but the rule itself does not satisfy that need.

```text
binding evaluation != observation
binding evaluation != retrieval
binding evaluation != external effect
```

This preserves the M0.2 no-ambient-context boundary and prevents a Binding Rule from becoming a hidden execution language.

## 5. Binding

`Binding` is the act of associating a concrete `Bound Value` with a Symbolic Reference by applying an unchanged admitted Binding Rule to compatible attributable Binding Input.

If the semantic rule was already admitted, concretizing the value does not by itself change WorkPlan meaning.

Example:

```text
rule:
    newest by modification time

input:
    backup-A.zip mtime=10:00
    backup-B.zip mtime=12:00

binding:
    selected_backup = backup-B.zip
```

Therefore:

```text
binding != semantic plan mutation
```

M0.3's successor-plan rule still applies when new information changes material work semantics. M0.4 distinguishes that case from filling a previously declared symbolic slot according to an unchanged rule.

Later identity/digest contracts may represent plans and bindings separately. M0.4 freezes the semantic distinction, not the wire representation.

## 6. Binding MUST NOT rewrite the rule

A binding operation MUST NOT modify, broaden, weaken, or replace the Binding Rule in order to obtain a value.

If the admitted rule is:

```text
newest backup by modification time
```

and the Binding Input lacks modification times, IRR or downstream orchestration MUST NOT silently reinterpret the rule as:

```text
first backup returned
largest backup
lexicographically last filename
```

The binding remains unresolved until compatible attributable input is available or the lifecycle returns to IRR.

```text
missing rule inputs != permission to substitute a rule
```

## 7. Binding lineage

A material binding MUST remain attributable.

Later representations must preserve enough semantic relationship to identify:

- the Symbolic Reference being satisfied;
- the Binding Rule applied;
- the attributable Binding Input;
- the resulting Bound Value;
- material provenance, scope, freshness, and completeness limitations used by the rule.

Exact receipt, ID, digest, and lineage formats are deferred.

```text
bound value != provenance-free value
```

## 8. Binding eligibility is semantic

Not every value is eligible to satisfy every Symbolic Reference.

Binding Input is usable only when its declared semantics are compatible with what the Symbolic Reference and Binding Rule require.

A rule requiring:

```text
newest by modification time
```

cannot be satisfied by filenames that lack attributable modification-time data.

Likewise, a process identifier produced by one launch step MUST NOT silently satisfy a symbolic slot expecting the result of another launch step merely because both are integers.

```text
same shape != same meaning
structural compatibility != semantic substitutability
```

Exact type contracts are deferred to M1 and capability I/O contracts to M0.5.

## 9. Trust semantics survive binding

Binding does not erase M0.2 trust semantics.

A Binding Rule may require properties such as:

- bounded scope;
- declared completeness;
- temporal basis;
- freshness;
- source identity;
- specific evidence fields.

If those properties are material and unsupported, binding MUST remain unresolved.

Example:

```text
rule:
    latest backup in D:\Backups
```

A partial listing covering only one subdirectory cannot silently establish the latest backup across all of `D:\Backups`.

An old cached listing cannot silently satisfy `latest now` when freshness is material.

```text
binding does not amplify evidence
binding does not imply completeness
binding does not imply freshness
```

## 10. Zero matches

A bounded rule may produce no admissible value.

Example:

```text
rule:
    exactly one artifact named release.zip

input:
    no matching artifact
```

Zero matches MUST NOT cause IRR or an Executor to invent a fallback artifact.

Depending on later contracts, zero matches may represent:

- a bounded negative result supported by complete evidence;
- an unresolved Information Need;
- a missing resource condition;
- a reason for IRR Continuation;
- a downstream blocked or failed state.

M0.4 does not freeze terminal state enums.

```text
zero matches != permission to guess
```

## 11. Multiple matches

Multiple candidates do not automatically imply Material Ambiguity.

If an admitted Binding Rule deterministically produces an admissible result, Binding may proceed.

Example:

```text
rule:
    newest by modification time

A at 10:00
B at 12:00
```

selects `B` without a new semantic decision.

However, if the rule cannot determine the required result, Binding MUST stop.

Example:

```text
A at 12:00
B at 12:00
```

with no admitted tie-breaker.

If choosing between them can materially change downstream work:

```text
tie under material rule -> IRR Continuation
```

IRR and Executors MUST NOT use result order, filename order, provider ranking, UI ordering, or another hidden preference as an implicit tie-breaker.

## 12. Presentation order is not binding precedence

A result sequence may have presentation order without semantic ranking.

```text
first result != preferred result by default
presentation order != binding precedence
```

A Binding Rule MAY use an ordering only when that ordering itself is semantically defined and attributable.

M0.4 defines no universal ordering precedence.

## 13. Plan-local symbolic dataflow

Not every intermediate WorkStep result requires a new IRR Continuation.

If all material semantics are already fixed, bounded downstream work MAY carry attributable Binding Input through symbolic dataflow and apply a pre-admitted Binding Rule without asking IRR to make a new semantic decision.

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

The intermediate `backup_candidates` may be plan-local output rather than an Observation returned to IRR.

Plan-local dataflow does not grant IRR ambient context and does not automatically admit intermediate values as Context for unrelated resolution purposes.

If an intermediate result creates a new material semantic decision, the bounded path MUST stop and return the applicable attributable information through IRR Continuation.

```text
fixed semantics -> bounded dataflow MAY continue
new material semantics -> IRR Continuation REQUIRED
```

## 14. Binding does not determine authority timing

M0.4 does **not** establish that Binding happens before or after Governance.

A WorkStep that produces Binding Input may itself require authorization before it can execute. A future Governance contract may also require review after a concrete resource becomes bound.

Depending on later contracts, authority may be required:

- before an observation-oriented WorkStep executes;
- before a mutating WorkStep executes;
- after a symbolic resource becomes concrete;
- again when a Bound Value materially changes the authority-relevant scope.

M0.4 freezes no universal ordering such as:

```text
binding -> authorization
```

or:

```text
authorization -> all future binding
```

It freezes only:

```text
bound value != authorization
binding success != permission
```

M0.6 freezes Governance semantics.

## 15. Mechanical Binding does not create semantic authority

A downstream Executor or bounded capability may later be permitted to apply an explicit Binding Rule mechanically.

That does not make the Executor an intent resolver or Governance authority.

The Executor MUST NOT:

- invent a missing Binding Rule;
- broaden the selection scope;
- choose between materially different meanings;
- add new effects to make Binding succeed;
- interpret unresolved Binding as permission to try a different semantic operation.

```text
deterministic binding != semantic discretion
deterministic binding != authorization
```

M0.4 does not freeze where mechanical rule evaluation runs. It freezes that mechanical evaluation cannot become hidden semantic choice.

## 16. Bound Value

A `Bound Value` is the concrete value associated with a Symbolic Reference after admissible Binding.

A Bound Value MUST retain material semantic relationship to:

- the symbolic slot it satisfies;
- the Binding Rule;
- the attributable Binding Input;
- material scope/freshness/completeness limitations relevant downstream.

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

## 17. World drift and stale bindings

The external world may change after a value is bound.

For example:

```text
selected_backup = D:\Backups\backup-42.zip
```

may later refer to a file that was deleted, replaced, or changed.

Successful Binding MUST NOT be treated as permanent proof that the world still matches the original input.

If freshness or identity is material at execution time, later Capability or Governance contracts may require revalidation.

Revalidation MUST NOT silently change the Bound Value to another resource unless an admitted lifecycle explicitly permits a new Binding under the same rule.

```text
stale binding != permission to reselect silently
```

Exact revalidation and drift handling are deferred.

## 18. Rebinding

A material Bound Value MUST NOT silently change from one concrete resource to another while pretending the earlier Binding never existed.

If later attributable input requires a materially different value, the change must remain explicit and attributable.

Depending on later lifecycle contracts, this may require:

- a new binding instance;
- IRR Continuation;
- a Successor WorkPlan;
- Governance re-review;
- rejection of the stale work path.

```text
rebind != overwrite history
```

M0.4 freezes the non-silent-rebinding invariant, not exact state transitions.

## 19. Binding failure does not authorize fallback

If a Binding Rule cannot be satisfied, IRR or downstream execution MUST NOT silently substitute:

- another rule;
- another resource class;
- another scope;
- another service;
- arbitrary shell logic;
- a broader search;
- discretionary guessing.

```text
binding failure != fallback authority
```

This preserves M0.3's no-hidden-fallback boundary.

## 20. Material new information is not mechanical Binding Input

Downstream information may reveal more than a concrete value.

It may reveal:

- a new resource class;
- a Conflict;
- a tie;
- an additional recipient;
- a new disclosure requirement;
- a different executable target;
- a new mutation surface;
- missing prerequisites;
- changed cost or commitment;
- evidence that invalidates an earlier Assumption.

When such information can materially change the next bounded path, it MUST NOT be consumed merely as mechanical Binding Input.

It becomes continuation-relevant semantic input.

```text
material new information != mechanical binding input
```

## 21. IRR Continuation

An `IRR Continuation` consumes attributable prior IRR state plus new clarification, Observation, Outcome, or other explicitly admitted continuation input while preserving parent intent lineage.

For M0.4, Continuation is REQUIRED when new information introduces or exposes a material semantic decision not already determined by admitted semantics.

Examples:

- two tied latest backups with no tie-breaker;
- two plausible launchers after archive inspection;
- a selected resource introduces external disclosure not represented in the current work semantics;
- an expected operation now requires a materially different target or scope;
- a prior Assumption is contradicted in a way that changes downstream work.

Continuation MAY produce:

```text
clarification
successor ResolvedIntent
successor WorkPlan
no-work completion
explicit inability to continue
```

Exact lifecycle/state-machine representation remains deferred.

## 22. Continuation is not observation authority

Returning to IRR does not grant authority to collect more data.

If Continuation identifies another Information Need or Observation Need, M0.2 still applies:

```text
information need != observation authority
continuation != retrieval authority
```

Any new observation effect remains external to IRR and subject to later Capability/Governance contracts.

## 23. Returned-data classification

A returned value is not an Observation merely because it came from execution.

The surrounding contract must preserve whether returned material is:

- plan-local output;
- an Observation intended for IRR Continuation;
- Context supplied through the Host boundary;
- an Outcome from an Executor or Worker;
- Binding Input used by a bounded rule;
- another explicitly classified attributable input.

These roles may overlap only when explicitly represented; they MUST NOT be silently collapsed because the same bytes participate in more than one role.

```text
returned data != Observation by default
retrieval != Observation by default
```

## 24. Observation boundary

An `Observation` retains the M0.2 meaning: attributable information explicitly supplied back to IRR from an external boundary or prior bounded step for continuation/resolution use.

Observation is not automatic truth or authority.

M0.4 adds one clarification: plan-local output used only for fixed symbolic dataflow does not have to become an Observation merely to be used as Binding Input.

If the data must influence a new IRR semantic decision, it must re-enter through an attributable continuation boundary under its explicit classification.

This preserves both:

```text
plan-local dataflow != ambient IRR context
```

and:

```text
new semantic decision -> attributable IRR input
```

## 25. Observation versus Outcome

An Observation describes attributable information relevant to IRR resolution or continuation.

An Outcome is an attributable reported result of Executor or Worker activity.

One downstream event may later supply both meanings, but they MUST remain distinguishable.

Example:

```text
archive.inspect succeeded
```

may be an Outcome about the inspect operation, while:

```text
two launchers found: A.exe, B.exe
```

may be Observation material relevant to Continuation.

M0.9 freezes exact Outcome states.

```text
observation != outcome
```

## 26. Authorized observation does not authorize observed resources

An Observation produced by an authorized operation does not inherit or propagate that operation's authority.

Authorization to list a directory does not mean that every returned file is authorized for deletion, execution, disclosure, or mutation.

```text
authorized observation effect != authority over observed resources
```

Observed or Bound resources may require separate Governance decisions under later contracts.

## 27. Chained symbolic dataflow

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
```

Each symbolic dependency MUST remain semantically attributable and respect the finite acyclic Work Dependency graph frozen by M0.3.

The chain MUST stop for IRR Continuation when a new material semantic decision appears.

Symbolic chaining MUST NOT become an autonomous planner loop.

## 28. No implicit cross-slot substitution

A value bound to one Symbolic Reference MUST NOT silently satisfy another merely because primitive types or names look compatible.

```text
$selected_backup
```

must not automatically satisfy:

```text
$launch_target
```

merely because both are paths.

```text
structural compatibility != semantic substitutability
```

Exact typing rules are deferred.

## 29. No hidden scope widening

A bounded observation-oriented or binding step MUST NOT silently widen its scope because the initial scope failed to produce a value.

Example:

```text
search D:\Backups
```

must not become:

```text
search all drives
```

without a new explicit semantic decision and applicable downstream authority.

```text
empty bounded result != permission to widen scope
```

This preserves M0.2 Context Boundary and M0.3 Plan Derivation semantics.

## 30. Backup scenario

Intent:

```text
"Find the newest organism_lab backup in D:\Backups,
extract it to W:\organism_lab,
and launch the project."
```

A conceptual bounded work path may contain:

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

Each WorkStep remains subject to whatever Capability and Governance conditions later contracts require. The example does not imply one authorization covers the whole chain.

`$backup_candidates` and `$selected_backup` may flow plan-locally while the admitted selection rule remains sufficient.

If launcher selection is governed by an admitted rule such as `require exactly one admissible launcher`, one unique launcher may bind mechanically.

If two materially different launcher candidates remain and no admitted rule chooses between them:

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

IRR and Executors MUST NOT choose one silently.

## 31. Authority distinctions

M0.4 freezes no permission policy.

The following distinctions are mandatory:

```text
symbolic reference != authority
Binding Input != authority
binding rule != authorization
binding != authorization
Observation != permission
Bound Value != permission
Continuation != authority
```

M0.6 freezes Governance semantics.

## 32. Relationship to later milestones

M0.4 intentionally leaves these details to later contracts:

- M0.5 — Capability Catalog, capability I/O contracts, effect metadata, scope requirements, availability, and drift;
- M0.6 — Governance and authorization around symbolic or concrete resources;
- M0.7 — Cognitive Provider behavior when proposing symbolic/binding semantics;
- M0.8 — Worker observations and delegated-work continuation;
- M0.9 — failure, interruption, retry, unknown outcome, and recovery;
- M1 — exact immutable schemas, symbolic-reference identifiers, binding records, validation, serialization, identities, and digests.

Later milestones may refine representation but MUST preserve the Late Binding and Observation boundary frozen here.

## 33. M0.4 exclusions

M0.4 intentionally does NOT freeze:

- Python classes, enums, protocols, or serialization;
- exact `SymbolicReference` fields or syntax;
- exact `BindingInput` representation;
- exact `BindingRule` representation;
- exact `BoundValue` or binding-record schema;
- exact Observation or ObservationNeed schema;
- exact Capability input/output contracts;
- execution scheduling;
- where mechanical Binding Rule evaluation runs;
- concrete trust/evidence enums;
- Governance policy or consent rules;
- whether a particular authority decision occurs before or after a particular Binding;
- plan/step/binding IDs, digests, persistence, or receipt format;
- exact revalidation or stale-binding algorithms;
- exact Continuation state-machine transitions;
- retry/recovery behavior;
- terminal Outcome schemas.

M0.4 freezes semantic constraints, not implementation types.

## 34. Acceptance criteria

M0.4 is complete when the repository states unambiguously that:

1. Late Binding defers concrete values, not semantic decisions.
2. A Symbolic Reference is not an observed value, authority, or scripting variable.
3. Binding Input is an attributable semantic role and is not Observation, Context, or Outcome by default.
4. Every material late-bound value is governed by an explicit bounded Binding Rule.
5. Binding Rule evaluation consumes supplied Binding Input and does not itself observe, retrieve, query ambient state, or perform external effects.
6. Binding Rule semantics cannot be silently rewritten to make Binding succeed.
7. Applying an unchanged Binding Rule to compatible attributable input is Binding, not semantic WorkPlan self-mutation.
8. Bound Values retain material provenance and semantic lineage.
9. Binding compatibility is semantic rather than merely structural.
10. Binding preserves M0.2 scope, completeness, freshness, and evidentiary limitations.
11. Zero matches do not authorize guessing or scope widening.
12. Multiple candidates may bind only when the admitted rule determines the required result.
13. Ties or unresolved material choices return to IRR Continuation.
14. Presentation order is not implicit Binding precedence.
15. Bounded plan-local symbolic dataflow may continue without a new IRR semantic decision while all material semantics remain fixed.
16. Plan-local output does not become Observation or ambient IRR Context automatically.
17. M0.4 does not fix Binding before or after Governance; observation-producing WorkSteps may themselves require authority.
18. Mechanical downstream Binding does not grant semantic discretion or authority.
19. Binding and authorization remain distinct.
20. A Bound Value is not a timeless fact or permission grant.
21. Stale bindings do not authorize silent reselection.
22. Rebinding cannot overwrite prior binding history silently.
23. Binding failure does not authorize fallback semantics.
24. Material new information is continuation input, not mechanical Binding Input.
25. Continuation is required when new information creates a material semantic decision not already determined by admitted semantics.
26. Continuation does not grant observation or retrieval authority.
27. Returned data is not automatically classified as Observation.
28. Observation retains the M0.2 explicit return-to-IRR meaning.
29. Observation and Outcome remain distinguishable.
30. Authorized observation does not grant authority over observed resources.
31. Chained symbolic dataflow remains finite, acyclic, and stops at new semantic decisions.
32. Primitive type similarity does not permit cross-slot substitution.
33. Empty bounded results do not permit hidden scope widening.
34. The backup scenario can proceed through symbolic dataflow but stops for clarification when launcher selection becomes materially ambiguous.
35. M0.5+, M0.6+, M0.7+, M0.8+, M0.9+, and M1 implementation details remain explicitly deferred.
36. No runtime code or `src/` tree is introduced.
