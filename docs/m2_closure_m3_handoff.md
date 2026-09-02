# M2 Closure & M3 Handoff

Status: **closure / handoff — M2 becomes complete and frozen when this PR merges**.

M2 began with one architectural question:

> How can IRR derive the next legal semantic transition from immutable M1 lifecycle history without turning orchestration into authority, execution, ambient retrieval, or one mutable session state machine?

That question is now answered and exercised end to end.

M2 closes as a runtime-orchestration layer over the frozen M1 record graph. It does not close as a complete product runtime, autonomous agent, executor, policy system, persistence engine, or Host implementation.

The M3 handoff therefore moves outward one layer:

```text
M1 = canonical semantic records
M2 = replayable orchestration over those records
M3 = Host integration boundary around those records and orchestrators
```

The intended M3 direction is **Host Integration Boundary**: define how an embedding Host acquires explicit inputs, retains admitted history, invokes replaceable external components, and feeds their exact attributable outputs back through the already-frozen IRR boundaries without gaining hidden semantic or authority privileges.

---

## 1. Exact M2 closure baseline

M2 closes from the merged M2.6 baseline:

```text
main = d99303103fc306dc8d6ec7e09a397d98b486c205
```

M2.6 merged as PR #99 and proved one complete Scenario A runtime composition through the already-implemented M2.1–M2.5 surfaces.

This closure PR introduces no new semantic runtime type, no new canonical record, and no new effectful integration implementation.

```text
closure != new runtime authority
handoff != implementation shortcut
```

---

## 2. M2 slices now closed

M2 is complete through:

```text
M2.0  Runtime Orchestration Charter
M2.1  Initial Resolution Orchestrator
M2.2  Work / Binding Orchestrator
M2.3  Capability / Governance Orchestrator
M2.4  Attempt / Outcome / Continuation Orchestrator
M2.5  Worker Lifecycle Orchestrator
M2.6  End-to-End Host Fixture
```

The slices are deliberately narrow. M2 never introduced one universal `LifecycleGraph`, `ResolutionSession`, `HostRuntime`, `orchestrate_end_to_end`, or global lifecycle enum as the canonical state surface.

---

## 3. Final M2 source-of-truth model

The central M2 result is:

```text
canonical lifecycle state
=
immutable attributable M1 record graph
```

and not:

```text
canonical lifecycle state
!= mutable ResolutionSession
!= Host object memory
!= scheduler queue
!= provider state
!= executor state
!= Worker state
!= one global status enum
```

M2 frontiers are derived runtime views. They expose the active semantic transition surface for one bounded slice, but they are not admitted semantic history themselves.

```text
M2 frontier != canonical record
frontier availability != transition occurrence
transition eligibility != permission
```

A Host may cache or materialize convenient views later, but those views must remain reconstructible from exact admitted history and explicit configuration.

---

## 4. Final M2 orchestration model

The completed architecture can be summarized as:

```text
exact admitted M1 lifecycle graph
+ explicit new Host input, when any
+ explicit orchestration policy/configuration
        |
        v
narrow M2 orchestrator
        |
        v
complete semantic transition frontier
        |
        +--> Host / external component may produce a new exact M1 record
        |
        `--> no new record means no historical transition occurred
```

This preserves the original M2.0 separation:

```text
orchestration != execution
orchestration != Governance
orchestration != authority
orchestration != ambient retrieval
next legal transition != permission
```

It also preserves scheduler separation:

```text
semantic frontier != scheduler queue
scheduler selection != semantic precedence
resource pressure != semantic truncation
material semantic choice != scheduler discretion
```

---

## 5. M2.1 closure — Initial Resolution

M2.1 proved that initial Resolution admission is independent from Cognitive Provider proposal.

```text
IntentRequest
+ ContextEnvelope
+ CandidateResolution[]
        |
        v
Initial Resolution frontier
```

Frozen distinctions include:

```text
provider proposes != IRR admits
one provider candidate != admission
provider consensus != admission
provider count != voting authority
candidate order != precedence
ResolutionAttribution != Authorization
```

IRR may also resolve a deterministic path without any provider candidate material:

```text
candidate_inputs = ()
```

Therefore:

```text
IRR != LLM wrapper
```

An explicit IRR-owned admission strategy may produce a ResolutionOutput, but the result is independently checked against exact request/context/admission attribution and complete supplied candidate provenance.

---

## 6. M2.2 closure — Work / Binding

M2.2 proved that `ResolvedIntent` does not silently become a `WorkPlan`, and that external symbolic binding state can be derived without mutating the plan.

```text
ResolvedIntent
+ WorkPlan?
+ BindingRule[]
+ BindingEvaluation[]
        |
        v
WorkBindingFrontier
```

Frozen distinctions include:

```text
ResolvedIntent != WorkPlan
missing WorkPlan != fake no-op plan
WorkPlan != mutable workflow session
BindingRule != hidden program
BoundValue != WorkPlan mutation
BindingIssue != hidden fallback permission
```

Every external symbolic slot has one explicit active binding state. Multiple independent slots remain multiple independent states rather than being collapsed into one global plan status.

M2.6 additionally hardened Scenario A so a latest-selection rule requires exact attributable completeness provenance before extremum selection.

```text
binding does not imply completeness
missing completeness provenance != safe latest selection
Binding tie != hidden tie-break
```

---

## 7. M2.3 closure — Capability / Governance

M2.3 proved that capability matching, proposal construction, external Governance, and Authorization projection remain distinct lifecycle stages.

```text
WorkPlan
+ CapabilityRequirement[]
+ CapabilityMatchEvaluation[]
+ WorkProposal[]
+ GovernanceDecision[]
+ Authorization[]
        |
        v
CapabilityGovernanceFrontier
```

Frozen distinctions include:

```text
CapabilityRequirement != capability availability
Capability Match != Authorization
Catalog membership != invocation readiness
WorkProposal != permission
GovernanceDecision != Effect
GovernanceDecision(AUTHORIZE) != admitted Authorization history
Authorization transition candidate != admitted Authorization history
Authorization != Outcome
```

An exact authorize component can expose the exact canonical `Authorization` record that may be materialized next. The frontier itself does not silently add that record to history.

---

## 8. M2.4 closure — Attempt / Outcome / Continuation

M2.4 proved that downstream execution history and semantic re-entry can be represented without retry/fallback policy leaking into orchestration.

```text
CapabilityAttempt[]
+ CapabilityOutcome[]
+ selected continuation source[]
+ ContinuationInput[]
+ SuccessorResolutionLineage[]
        |
        v
AttemptOutcomeContinuationFrontier
```

Frozen distinctions include:

```text
Attempt != Outcome
Outcome lifecycle != completion
Outcome completion != effect certainty
unknown outcome != failed
not_satisfied != no effect
Outcome history != selected Continuation source
Outcome != automatic ContinuationInput
ContinuationInput != retry
SuccessorResolutionLineage != recovery policy
successor Resolution != successor WorkPlan
```

M2.6 exercised a partial extraction with:

```text
lifecycle = normal_protocol_completed
completion = not_satisfied
filesystem.read = confirmed_occurred
filesystem.write = confirmed_partial
```

and correctly stopped before launch or automatic retry.

---

## 9. M2.5 closure — Worker lifecycle

M2.5 proved that Worker delegation has a separate subordinate lifecycle without becoming universal execution machinery.

```text
ResolvedIntent
+ parent WorkPlan[]
+ DelegatedWork[]
+ DelegatedWorkHandoff[]
+ WorkerResult[]
        |
        v
WorkerLifecycleFrontier
```

Frozen distinctions include:

```text
DelegatedWork != WorkPlan
DelegatedWork != Authorization
DelegatedWorkHandoff != Worker acceptance
WorkerResult != parent completion
WorkerNeed != scope expansion
WorkerNeed != capability grant
WorkerNeed != Authorization
completion claim != completion proof
WorkerResult history != automatic Continuation
```

M2.6 also proved the negative case:

```text
ordinary capability path != implicit Worker path
```

Scenario A can carry a normal WorkPlan while the Worker lifecycle surface remains empty.

---

## 10. M2.6 closure — composition proof

M2.6 was the first executable composition of all implemented M2 boundaries around one realistic Scenario A lifecycle.

The final path was:

```text
IntentRequest + bounded ContextEnvelope + CandidateResolution
→ M2.1 explicit IRR admission
→ ResolvedIntent
→ M2.2 bounded search WorkPlan
→ M2.3 exact search Capability Match
→ attributable search material + exact completeness provenance
→ M1.4 latest Binding
→ M2.2 extract WorkPlan binding frontier
→ M2.3 extract Capability / Governance / Authorization materialization
→ CapabilityAttempt
→ partial CapabilityOutcome
→ M2.4 explicit continuation selection / Host re-entry / successor lineage
→ M2.5 empty Worker surface for ordinary capability path
→ successor ResolvedIntent
→ M2.2 work disposition required
```

No production `HostRuntime` or super-orchestrator was required.

---

## 11. Interpreting the original M2.6 plan correctly

The M2.0 charter said that at least one canonical scenario should be driven through the implemented Orchestrator rather than manually composing every record in a test.

By the time M2.1–M2.5 existed, the architecture had intentionally converged on **multiple narrow orchestrators**, each deriving one complete semantic frontier over exact M1 records.

M2.6 therefore satisfies the intent of that criterion by driving one scenario through those implemented orchestrators in sequence while explicit external boundaries still produce their own M1 records.

It does **not** satisfy the old wording by inventing a single central `orchestrate_end_to_end()` function.

That distinction is now frozen:

```text
implemented orchestration != one super-orchestrator
Host composition != new semantic authority
repeated Host sequencing != proof that a mutable HostRuntime should become canonical
```

Creating a central orchestration object solely to mirror the old singular noun would reduce the separation that M2 proved.

---

## 12. What M2 proved beyond green unit tests

M2.6 found a real integration defect that isolated slice tests had not exposed: Scenario A could select the maximum timestamp from a supplied subset without requiring completeness provenance.

The fix did not add an ad-hoc Host check. It strengthened the existing M1.4 provenance path used by the composed runtime:

```text
BindingRule.required_completeness_refs
<->
BindingInput.completeness_refs
```

The incomplete-search adversarial path now yields:

```text
BindingIssueKind.MISSING_REQUIRED_DATA
external_binding_complete = false
```

This matters to M2 closure because it demonstrates that the M2 end-to-end fixture is an architectural regression test, not documentation theatre.

---

## 13. Replayability closure

M2 remains replay-oriented.

For a given narrow orchestrator:

```text
same exact admitted graph slice
+ same explicit orchestration policy/configuration
+ same admitted external inputs
→ same semantic frontier
```

Replay must not depend on:

- storage insertion order;
- ambient filesystem state;
- ambient browser/UI state;
- hidden provider memory;
- executor-local transient state unless represented through explicit records;
- unadmitted wall-clock reads;
- scheduler order;
- process restart assumptions.

```text
replay derivation != retry Attempt
process restart != proof of external failure
unknown external outcome != automatic retry
```

---

## 14. Complete M2 cross-slice invariants

M2 closes with the following cross-slice boundaries intact:

```text
Intent != Permission != Effect
Origin != Principal
Context != authority
Evidence != authority
provider proposal != IRR admission
ResolvedIntent != WorkPlan
WorkPlan != Authorization
Binding tie != hidden tie-break
binding does not imply completeness
Capability Match != Authorization
Catalog membership != availability
GovernanceDecision != Effect
Authorization != Outcome
Attempt != Outcome
Outcome completion != effect certainty
unknown outcome != failed
failed/not_satisfied != no effect
Retry != mutation of old Attempt
ContinuationInput != retry
ContinuationInput != Observation by default
successor Resolution != successor WorkPlan
DelegatedWork != Authorization
WorkerNeed != scope/capability/authority grant
WorkerResult != parent completion
M2 frontier != canonical semantic history
Host sequencing != canonical lifecycle state
scheduler selection != semantic authority
```

These are M3 constraints, not M2 implementation details that may be casually discarded.

---

## 15. What M2 deliberately does not provide

M2 completion does **not** provide:

- a complete embeddable Host runtime;
- provider transport or provider SDK integration;
- filesystem/browser/network acquisition adapters;
- persistent record storage;
- an event store;
- crash/restart persistence semantics;
- automatic context acquisition;
- automatic WorkPlan generation policy;
- automatic CapabilityRequirement generation policy;
- capability invocation;
- Executor implementation;
- Governance implementation;
- Worker implementation;
- scheduler implementation;
- automatic retry, fallback, compensation, or recovery;
- parent-intent completion policy;
- background monitoring;
- one universal lifecycle/session state object;
- HDE-, Companion-, Codexia-, Organism-, shell-, browser-, Telegram-, Signal-, or filesystem-specific authority shortcuts.

Those omissions are intentional. They define the boundary between orchestration semantics and integration/runtime mechanisms.

---

# M3 Handoff

## 16. M3 identity

The next phase is:

# **M3 — Host Integration Boundary**

M3 asks:

> How can a real embedding Host connect storage, Cognitive Providers, Governance, Executors, Workers, and acquisition mechanisms to the frozen M1/M2 core without making Host convenience state a new semantic or authority source?

The goal is not to build HDE integration directly. The goal is an **embeddable, replaceable, testable Host boundary** that HDE or another Host can later use.

```text
IRR core != HDE integration
M3 Host boundary != product-specific shell
```

---

## 17. Why Host integration is the next layer

M1 already defines what exact semantic history looks like.

M2 already derives what the active semantic frontier looks like.

The missing practical layer is the one that performs explicit integration work around those boundaries:

```text
receive external occurrence
→ construct/admit exact attributable input
→ replay relevant M2 frontier
→ select only materially-neutral runnable work automatically
   or expose material choice to the appropriate external actor
→ invoke the correct external adapter when explicitly allowed
→ receive exact attributable result
→ add exact M1 history
→ replay
```

Without M3, applications must manually wire these steps themselves, as M2.6 intentionally did in the integration fixture.

---

## 18. M3 Host responsibilities

A future Host integration layer may own mechanisms such as:

- receiving a user/companion/system occurrence and constructing an `IntentRequest`;
- constructing explicit bounded `ContextEnvelope` material from already-permitted Host inputs;
- invoking a configured Cognitive Provider with an explicitly projected disclosure surface;
- receiving provider `CandidateResolution` material;
- invoking an IRR-owned admission policy implementation;
- retaining exact admitted M1 records;
- replaying M2 frontiers from those exact records;
- presenting semantic choices/needs to the appropriate external actor;
- invoking Governance through an adapter when Governance review is actually required;
- materializing exact Authorization only from explicit Governance output;
- handing an authorized exact capability invocation to an Executor adapter;
- receiving attributable Attempt/Outcome material;
- handing explicit `DelegatedWork` to a Worker adapter;
- receiving attributable WorkerResult material;
- constructing explicit Host re-entry / Continuation records when the external boundary actually selects them;
- reconstructing derived runtime views after process restart from admitted history.

These are **mechanism responsibilities**, not automatic semantic discretion.

---

## 19. M3 Host non-authority rule

The most important M3 invariant is:

```text
Host mechanism != semantic authority
Host mechanism != Governance authority
Host mechanism != evidence truth
Host mechanism != completion proof
```

The Host may know how to call an adapter. That does not mean the corresponding operation is semantically selected or authorized.

```text
adapter installed != Capability admitted
Capability admitted != currently available
currently available != authorized
authorized != executed
executed != successful
successful child operation != parent completion
```

A Host registry, dependency injection container, Python object reference, executable path, connected account, API token, or local filesystem permission must never become an implicit IRR authority grant.

---

## 20. M3 canonical-state rule

M3 must not reverse the central M2 decision.

A Host may maintain operational bookkeeping, caches, indexes, queues, connection pools, or reconstructed convenience state, but:

```text
HostState != canonical semantic lifecycle history
```

Any semantic lifecycle claim that must survive replay must resolve to exact admitted M1 records and explicit M3 configuration/versioning where applicable.

A future persistent store therefore stores or indexes canonical records; it does not replace them with one mutable row such as:

```text
status = running
```

as the only source of truth.

---

## 21. M3 adapter principle

M3 should prefer narrow typed ports over one omnipotent tool interface.

Conceptually:

```text
CognitiveProviderPort
GovernancePort
ExecutorPort
WorkerPort
HistoryRepository
HostAcquisitionPort(s)
```

These names are **handoff concepts, not frozen Python APIs**.

The charter phase must determine whether each deserves a public protocol/type and what exact data may cross each boundary.

```text
one generic tool() interface != automatic architectural simplification
adapter convenience != semantic interchangeability
```

For example, an Executor port must not silently accept arbitrary shell text just because shell execution is technically available.

---

## 22. Provider integration requirements for M3

A provider adapter must preserve the frozen M0/M1/M2 provider boundary:

```text
provider receives only explicitly projected material
provider output = CandidateResolution proposal material
provider output != admitted Context by default
provider output != Observation by default
provider output != Authorization
provider output != final IRR state
```

Remote provider transport may itself create disclosure/network effects. Local placement does not grant blanket access to Host data.

An adapter must not hide retrieval inside provider invocation and then present retrieved facts as if they were already admitted Context.

---

## 23. Governance integration requirements for M3

Governance remains external.

A Governance adapter may transport an exact `WorkProposal` and return an exact attributable `GovernanceDecision` according to the future M3 contract.

It must not be replaced with:

- `approved=True` on WorkPlan;
- a Host boolean;
- provider confidence;
- user-origin text interpreted directly as Authorization;
- Executor self-approval.

M2.3 already defines the semantic distinction. M3 may implement the transport/integration boundary without collapsing it.

---

## 24. Executor integration requirements for M3

An Executor adapter is where M3 first approaches actual effects, so this boundary must remain strict.

M3 must preserve:

```text
WorkStep != invocation
Capability Match != invocation
Authorization != invocation
CapabilityAttempt = attributable invocation occurrence representation
CapabilityOutcome = separately attributable evaluated result
```

The exact design question for M3 is how the Host passes the already-selected, already-bounded, sufficiently-authorized invocation material to an Executor without giving the Executor permission to reinterpret intent or invent fallback.

```text
Executor != resolver
Executor != Governance
Executor failure != fallback authority
```

---

## 25. Worker integration requirements for M3

A Worker adapter must receive exact bounded delegation material, not a vague parent goal plus ambient Host access.

```text
Worker receives DelegatedWork through explicit handoff
Worker capability ceiling != authority grant
WorkerNeed != automatic widening
WorkerResult != parent completion
```

M3 may implement Worker dispatch/transport mechanisms, but parent semantic continuation remains governed by the existing WorkerResult + Continuation boundaries.

---

## 26. Persistence / replay handoff

Persistence becomes materially relevant in M3 because a real Host must survive process lifetime and reconstruct frontiers.

However M3 must distinguish:

```text
record persistence != semantic mutation
storage order != lifecycle order
record present in database != active lineage by default
cache != canonical history
```

A future history repository should support replay from exact records and reject or surface invalid competing graph material rather than using insertion order as conflict resolution.

M3 must also distinguish internal persistence from external effect certainty:

```text
Host crashed after sending != no external effect
record not yet persisted != proof executor did nothing
restart != automatic retry
```

The exact crash/commit protocol belongs to M3 design and must be chartered before effectful implementation is frozen.

---

## 27. Material choice versus automatic Host sequencing

M3 may automate only transitions whose execution choice is materially neutral under already-admitted semantics and applicable authority.

The Host must not use scheduler convenience to resolve semantic choice.

Examples that must remain explicit:

- two materially different provider interpretations;
- Binding tie;
- two non-interchangeable capabilities;
- Governance constraint that changes work semantics;
- WorkerNeed that widens scope/effect/disclosure;
- unknown effectful outcome followed by a proposed retry;
- multiple successor branches requiring semantic selection.

```text
mechanically runnable != semantically self-selecting
```

---

## 28. M3.0 must be charter-first

The first M3 slice should be:

# **M3.0 — Host Integration Charter**

M3.0 should add documentation/tests only unless a tiny supporting type is strictly necessary to make a boundary precise.

Before freezing public Host interfaces, M3.0 must answer at least:

1. What exact state does the Host retain versus derive?
2. What is the minimum history-repository contract?
3. Which actors are allowed to create which M1 record types?
4. What exact material crosses Provider, Governance, Executor, Worker, and acquisition boundaries?
5. Which adapter calls may themselves constitute external effects?
6. How are adapter occurrence identities attributed?
7. How does process restart reconstruct active frontiers?
8. How does the Host fail closed on competing/invalid active graph material?
9. Which transitions may the Host sequence automatically because they are materially neutral?
10. How are crash windows around effectful invocation represented without inventing retry safety?
11. What configuration/version material is required for replay claims?
12. What must remain product-specific and outside IRR core?

No public `HostRuntime` should be frozen before those questions are answered.

---

## 29. Proposed M3 sequence — planning only

A plausible sequence after M3.0 is:

```text
M3.0  Host Integration Charter
M3.1  Admitted History Repository / Replay Boundary
M3.2  Cognitive Provider Integration Port
M3.3  Governance Integration Port
M3.4  Executor / Capability Invocation Port
M3.5  Worker Integration Port
M3.6  End-to-End Embeddable Host Fixture
```

This sequence is **not yet normative** beyond selecting M3.0 as the next milestone.

M3.0 may reorder, split, combine, or reject M3.1–M3.6 after the integration boundaries are examined adversarially.

In particular, M3 must not create a persistence abstraction, generic adapter API, or central Host object merely because this list names one.

---

## 30. M3 non-goals carried forward

M3 is not permission to turn IRR into:

- a shell-command generator;
- a universal desktop automation engine;
- an embedded policy/Governance engine;
- a permission database;
- a general workflow scripting language;
- a generic autonomous agent loop;
- a hidden retry engine;
- an ambient memory/filesystem/browser scanner;
- an HDE-only subsystem;
- a Companion runtime;
- a Codexia runtime;
- an Organism runtime;
- a universal tool router that treats every installed mechanism as semantically interchangeable.

M3 may provide integration ports that those systems use, but it must preserve their role separation.

---

## 31. M3 entry invariants

M3 begins under these already-frozen constraints:

```text
M1 records remain canonical semantic history
M2 frontiers remain derived non-canonical views
Host state != canonical semantic history
Host mechanism != authority
provider proposal != IRR admission
Context != ambient Host data
Capability Match != Authorization
Authorization != invocation
Attempt != Outcome
Outcome != automatic Continuation
WorkerResult != parent completion
scheduler choice != semantic choice
restart != retry permission
```

Any M3 design that requires weakening one of these must explicitly reopen the relevant earlier architecture rather than silently bypassing it.

---

## 32. M2 Definition of Done

M2 closes when the exact closure candidate demonstrates:

```text
M2.0–M2.6 are merged and documented
M1 canonical/wire semantics remain frozen
all M2 public frontiers remain derived non-canonical runtime views
M2.6 composes M2.1–M2.5 over one canonical scenario
no central HostRuntime is required for semantic correctness
completeness/tie failure paths remain fail-closed
Capability/Governance/Authorization separation remains intact
Attempt/Outcome/Continuation dimensions remain intact
ordinary WorkPlan does not imply Worker delegation
successor Resolution does not imply successor WorkPlan
closure delta adds no hidden runtime/API/wire expansion
repository CI passes on Python 3.11–3.14
```

Once this closure PR merges:

# **M2 — Runtime Orchestration is complete and frozen through M2.6.**

The next implementation milestone is not M2.7.

It is:

# **M3.0 — Host Integration Charter**

with the explicit rule:

```text
integrate the runtime
without turning integration machinery into semantic authority
```
