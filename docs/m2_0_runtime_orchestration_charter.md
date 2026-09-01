# M2.0 — Runtime Orchestration Charter

Status: **proposed normative charter for M2**. It becomes the M2 baseline only when this PR merges.

M1 froze the immutable Intent Resolution IR and proved it against the eight canonical M0.10 scenarios. M2 begins a different phase: using those records to drive a real intent lifecycle without collapsing the boundaries M0/M1 deliberately separated.

M2.0 therefore freezes the orchestration model before implementation code is added.

The central decision is:

```text
canonical lifecycle state
=
immutable attributable M1 record graph

canonical lifecycle state
!= mutable ResolutionSession object
!= one global status enum
!= hidden provider / executor state
```

An implementation may later expose a session-shaped convenience API, cache, cursor, or materialized view. Such a view is derived runtime state only. It is never the canonical semantic history and must be reconstructible from admitted records plus explicit orchestration configuration.

## 1. M2 purpose

M2 turns the frozen M1 language into a bounded orchestration runtime.

Conceptually:

```text
explicit admitted M1 history
        +
explicit new Host input, when any
        +
explicit orchestration policy/configuration
        |
        v
   IRR Orchestrator
        |
        v
bounded eligible transition frontier
        |
        +--> internal deterministic M1 transition
        |
        +--> explicit Host boundary requirement
        |
        `--> quiescent / terminal-for-now result
```

The Orchestrator determines what transitions are semantically legal next. It does not manufacture authority and it does not perform external effects.

```text
orchestration != execution
orchestration != Governance
orchestration != ambient retrieval
orchestration != authority
next legal transition != permission
```

## 2. Frozen architectural choice: record graph over mutable session state

M1 already contains immutable content-addressed records and explicit lineage. M2 MUST preserve that property rather than wrapping the lifecycle in a mutable object whose latest fields silently replace history.

The canonical lifecycle is a graph rooted in one attributable `IntentRequest` and composed from exact admitted M1 records such as:

```text
IntentRequest
Context / Claim / Evidence material
CandidateResolution
ResolvedIntent | ClarificationNeed | InformationNeed
BindingRule / BindingInput / BoundValue | BindingIssue
WorkPlan / WorkStep
DelegatedWork / DelegatedWorkHandoff
WorkerResult
CapabilityRequirement
CapabilityCatalogSnapshot
CapabilityMatchEvaluation
WorkProposal
GovernanceDecision / Authorization
CapabilityAttempt
CapabilityOutcome
ContinuationInput
SuccessorResolutionLineage
```

No later record rewrites an earlier record into a new meaning.

```text
new resolution != mutation of old resolution
new WorkPlan != mutation of old WorkPlan
retry Attempt != mutation of old Attempt
successor lineage != replacement of predecessor history
new Authorization != retroactive authorization
```

A derived runtime view MAY summarize this graph for efficient execution, but loss of the view must not destroy semantic history.

## 3. Why M2 does not freeze one global state enum

The completed M1 model is not intrinsically linear.

One intent may contain:

- multiple independent WorkSteps;
- symbolic values that become available at different times;
- an authorized subset and an unresolved subset;
- a delegated Worker branch while another ordinary work branch is already complete;
- an interrupted Attempt requiring continuation while unrelated work remains unaffected;
- a successor Resolution branch that preserves the original request but supersedes only specific prior semantics.

Therefore a single field such as:

```text
session.status = WAITING_FOR_AUTHORIZATION
```

cannot be the canonical lifecycle state. It would erase which exact proposal, step, branch, authorization scope, attempt, or continuation is waiting.

M2 instead derives a **transition frontier** over exact records. The frontier may contain zero, one, or multiple independently eligible next transitions.

The exact Python representation of that frontier is deferred beyond M2.0.

## 4. Host / Orchestrator boundary

The Host remains the embedding environment around IRR.

The Host may be responsible for concrete mechanisms such as:

- obtaining human clarification;
- invoking a Cognitive Provider;
- acquiring explicitly requested information through an admitted mechanism;
- supplying a Capability Catalog Snapshot;
- transporting a WorkProposal to Governance;
- transporting authorized capability work to an Executor;
- transporting DelegatedWork to a Worker;
- receiving external outcomes or Worker results;
- persistence, scheduling, process lifecycle, network transport, and UI.

The Orchestrator consumes only explicit admitted inputs and determines the next semantically legal boundary.

It MUST NOT treat Host reachability as semantic permission.

```text
Host can perform mechanism X
!= IRR has authority to request X

Host possesses data Y
!= Y is admitted IRR Context

Host can invoke executor Z
!= Z is a matched Capability
```

M2 may later define typed Host requests/responses, but M2.0 does not freeze those wire schemas.

## 5. No hidden acquisition or hidden tool loop

The Orchestrator MUST NOT solve missing information by ambiently reading files, memory, browsers, repositories, accounts, network state, process state, or another external source.

If a semantic step requires new information, that requirement must cross an explicit M1-compatible boundary.

Likewise, a Cognitive Provider cannot be treated as an agent-shaped escape hatch around IRR provenance.

```text
provider needs data
→ explicit information / observation acquisition boundary
→ attributable returned material
→ IRR admission

provider hidden tool call
!= admitted Context
!= admitted Observation
!= authority
```

## 6. Transition frontier

The Orchestrator derives a bounded set of legal next transitions from the exact admitted graph.

Conceptual transition classes include, without freezing an enum or public API:

```text
resolution work
    candidate admission / clarification / information need

semantic work construction
    WorkPlan / DelegatedWork construction under already admitted semantics

binding work
    apply an already admitted BindingRule to explicit compatible BindingInput

capability work
    build/evaluate exact CapabilityRequirement against an exact Catalog Snapshot

governance boundary
    present exact WorkProposal material to external Governance

execution boundary
    hand exact uniquely matched and sufficiently authorized work toward an Executor

worker boundary
    hand exact DelegatedWork toward a Worker

continuation work
    admit exact Outcome / WorkerResult / BindingIssue / CapabilityMatchIssue /
    applicable Governance continuation material and produce successor Resolution

quiescent boundary
    no internal transition is currently legal without new explicit external input
```

These are conceptual categories only. M2.0 intentionally does not add a new universal `NextAction` schema.

## 7. Internal transition versus external boundary requirement

Some transitions may be wholly mechanical over already admitted records. Others require external material.

For example:

```text
compatible BindingInput + unchanged BindingRule
→ mechanical binding may be internal
```

while:

```text
material ambiguity
→ requires external clarification material
```

and:

```text
WorkProposal requiring authority
→ requires external Governance material
```

The Orchestrator MUST NOT collapse these categories merely to keep an execution loop moving.

```text
mechanically computable != externally authorized
externally available != semantically admitted
waiting for input != permission to invent input
```

## 8. Replayability and deterministic derivation

M2 is **replayable by design**.

Given:

1. the same exact admitted M1 record graph;
2. the same explicit orchestration policy/configuration version;
3. the same explicit external inputs already admitted into that graph;

IRR MUST derive the same semantic transition frontier.

The derivation MUST NOT depend on hidden mutable memory, ambient filesystem state, current browser state, implicit process discovery, random provider output, or wall-clock time that was never admitted as input.

If time, availability, quota, connectivity, or another changing fact materially affects the transition, that fact must enter through an explicit attributable boundary appropriate to its semantics.

Replayability does not mean every external effect is replayed. Replaying semantic history is different from invoking an Executor again.

```text
replay lifecycle derivation
!= retry capability Attempt
!= resend external message
!= repeat Worker effect
```

## 9. Determinism applies to the frontier, not hidden scheduling authority

Two independent transitions may both be legal.

M2 may expose both as an eligible frontier rather than fabricating one global ordering.

If ordering between two operations is semantically irrelevant under already admitted contracts, a Host scheduler may choose an execution order within those bounds. If the ordering or choice changes material semantics, scope, recipient, disclosure, cost, completion meaning, or authority, it is not a mere scheduler decision and must return through the appropriate IRR semantic boundary.

```text
independent scheduling choice
!= semantic choice

material choice
!= scheduler discretion
```

M2.0 therefore does not freeze a universal FIFO, priority queue, topological scheduler, or concurrency model.

## 10. Orchestration policy is not semantic authority

Later M2 code may require explicit policy/configuration for mechanical questions such as:

- which deterministic resolver implementation to invoke first;
- bounded provider selection among semantically equivalent configured providers;
- whether independent eligible transitions are exposed together or processed serially;
- runtime resource limits;
- local scheduling details that do not alter admitted semantics.

Such policy MUST NOT:

- resolve Material Ambiguity by preference;
- widen a Capability requirement;
- substitute a missing provider/service/capability when that changes semantics;
- create Authorization;
- infer retry safety;
- relabel Worker-originated material as human-originated;
- change an admitted completion contract;
- erase an unknown or partial effect.

If changing the policy changes the material meaning of the work, that is no longer orchestration policy; it is a semantic decision requiring explicit IRR representation.

## 11. Cognitive Provider orchestration

M2 may coordinate invocation of a Cognitive Provider, but the M0.7/M1.3 boundary remains frozen.

```text
provider invocation
→ CandidateResolution material
→ IRR validation/admission
```

The provider does not own lifecycle state.

A provider may be local, remote, deterministic, model-based, Organism-derived, or hybrid. Provider identity and transport do not grant factual truth, authority, ambient Context, or effect permission.

Provider retry/fallback is not automatically harmless. If changing provider changes disclosure, cost, semantic behavior, authority surface, or another material dimension, the switch cannot be hidden in orchestration plumbing.

## 12. Governance orchestration

Governance remains external to IRR.

M2 may determine that exact `WorkProposal` material requires Governance review and may expose a Host boundary requirement for that review. It MUST NOT generate its own `Authorization` merely because work is valid, safe-looking, requested by a human, or executable.

```text
eligible Governance request != Authorization
Governance pending != Denial
authority for subset != authority for whole plan
old Authorization != successor Authorization
```

Authorization applicability must be evaluated against exact represented work and its conditions.

## 13. Executor orchestration

M2 may determine that one exact capability-backed WorkStep is eligible for Executor handoff only when the frozen M1 contracts permit that handoff.

This does not mean IRR performs the effect.

The external execution boundary must preserve:

- exact WorkStep lineage;
- exact admitted Capability Match;
- exact bound values required by the Attempt;
- applicable Authorization material where required;
- exact Attempt occurrence identity/provenance once attempted.

The Executor result must return as attributable M1 lifecycle material rather than mutating an in-memory status to `done`.

## 14. Worker orchestration

M2 may coordinate bounded Worker handoff, but `DelegatedWork` remains an immutable envelope.

Worker-local planning is allowed only within that envelope.

```text
WorkerNeed
!= envelope mutation
!= permission expansion
!= new capability grant
!= Authorization
```

A material Worker escalation returns through explicit `WorkerResult` / `ContinuationInput` / successor Resolution semantics.

M2 MUST NOT recursively create new delegated Workers merely because a Worker asks for one unless later explicit contracts permit that behavior.

## 15. Outcome, recovery, and retry

M2 orchestration must preserve the M0.9/M1.7 recovery model.

```text
Attempt != Outcome
interrupted != failed
completion not_satisfied != no effect
unknown completion/effect != failed
failed != automatic retry
unknown outcome != automatic retry
retry != mutation of old Attempt
```

A retry, fallback, compensation, or status query is new semantic work when it is required. M2 may orchestrate that work only after the relevant successor semantics are admitted.

No generic runtime loop may contain logic equivalent to:

```text
if attempt_failed_or_timed_out:
    retry()
```

unless a later explicit recovery policy has first represented and validated all semantic, idempotency, authority, and effect-history requirements.

## 16. Quiescence and terminal-for-now states

The absence of an immediately executable transition is not necessarily lifecycle completion.

The derived frontier may be empty because the lifecycle is:

- waiting for human clarification;
- waiting for attributable information;
- waiting for Governance;
- waiting for an Executor/Worker result;
- blocked on missing capability;
- paused after an unknown outcome until recovery semantics are resolved;
- actually complete for the represented parent intent.

M2 MUST preserve these distinctions rather than compressing them into one `idle`, `blocked`, or `done` flag.

Parent-intent completion policy is not frozen by M2.0.

## 17. Persistence boundary

Replayable orchestration does not require M2.0 to choose a database, event store, append-only log format, or persistence backend.

The Host may persist canonical M1 records and any future M2 records using an implementation-specific store, provided storage does not silently alter semantic identities or lineage.

A cache, index, materialized view, or session snapshot may be discarded and rebuilt.

```text
persistence backend != semantic authority
cache != canonical history
materialized session view != source of truth
```

The exact durable storage model is deferred.

## 18. Crash / resume boundary

A runtime process crash must not require mutating historical M1 records to recover semantic state.

After restart, the Orchestrator should be able to reconstruct the eligible transition frontier from persisted admitted records and explicit runtime configuration.

However, process restart MUST NOT convert an in-flight external effect into a known failure or safe retry.

```text
runtime process died
!= external Attempt definitely failed
!= external effect definitely absent
```

If the external outcome is unknown, the ordinary M1 unknown-outcome/continuation boundary applies.

## 19. No hidden parent completion inference

M2 may derive local completion facts already encoded by M1 contracts, but it MUST NOT infer parent intent completion merely because:

- every currently known WorkStep has an Outcome;
- one Worker says `done`;
- one authorized subset completed;
- one successor branch completed;
- no transition is currently executable.

Parent completion may depend on the original intent semantics, explicit completion contracts, unresolved branches, and successor lineage.

A dedicated parent-completion policy/evaluator, if needed, is a later M2 design decision.

## 20. M2.0 deliberately does not freeze public runtime API

M2.0 freezes architecture, not Python class names.

It does not yet declare public types such as:

```text
ResolutionSession
OrchestratorState
NextAction
TransitionFrontier
HostRequest
RuntimeEvent
```

Those names are illustrative only and MUST NOT be treated as frozen API.

The first implementation slice should derive the smallest API from executable transition requirements instead of inventing a broad runtime framework up front.

## 21. Planned M2 implementation sequence

M2.0 declares the following implementation direction while allowing narrow PR-level refinement.

### M2.1 — Initial Resolution Orchestrator

Target:

```text
IntentRequest
+ explicit Context
+ explicit CandidateResolution material when used
→ ResolvedIntent | ClarificationNeed | InformationNeed
```

Focus: provider boundary, admission, non-operational resolution, and no hidden acquisition.

### M2.2 — Work / Binding Orchestrator

Target:

```text
ResolvedIntent
→ bounded work construction
→ mechanical Binding where rules are already admitted
→ BindingIssue re-entry when mechanical resolution stops
```

Focus: semantic work versus runtime scheduling.

### M2.3 — Capability / Governance Orchestrator

Target:

```text
WorkStep
→ CapabilityRequirement
→ exact Catalog evaluation
→ WorkProposal
→ external Governance boundary
→ Authorization applicability
```

Focus: capability validity remains distinct from authority.

### M2.4 — Attempt / Outcome / Continuation Orchestrator

Target:

```text
eligible authorized/matched work
→ external Executor handoff
→ Attempt / Outcome
→ ContinuationInput
→ SuccessorResolutionLineage
```

Focus: real multi-step lifecycle without hidden retry.

### M2.5 — Worker Lifecycle Orchestrator

Target:

```text
DelegatedWork
→ Worker handoff
→ WorkerResult / WorkerNeed
→ Continuation
→ successor Resolution
```

Focus: subordinate lifecycle without envelope mutation.

### M2.6 — End-to-end Host fixture

At least one canonical scenario should be driven through the implemented Orchestrator rather than manually composing every record in the test.

Scenario A or B is the preferred first end-to-end target because both exercise late binding, capability boundaries, authority, lifecycle outcome, and continuation.

M2.6 is not permission to add generic shell/browser fallback.

## 22. M2.0 non-goals

M2.0 does not add:

- effect execution;
- a universal mutable `ResolutionSession` source of truth;
- one global lifecycle state enum;
- persistence implementation;
- event-store implementation;
- transport implementation;
- provider SDK integration;
- Governance engine;
- Executor implementation;
- Worker implementation;
- automatic retries;
- automatic fallback;
- ambient retrieval;
- background monitoring;
- parent-intent completion evaluator;
- HDE-, Companion-, Codexia-, Organism-, Telegram-, Signal-, shell-, browser-, or filesystem-specific orchestration shortcuts.

## 23. M2.0 frozen invariants

The following statements are normative for later M2 slices:

```text
M1 record graph = canonical semantic lifecycle history
mutable session view != canonical semantic history
one global status != complete lifecycle state

orchestration != authority
orchestration != effect execution
orchestration != Governance
orchestration != ambient retrieval
next legal transition != permission

Host mechanism availability != admitted capability
Host-held data != admitted Context
provider output != admitted Resolution by default

transition frontier != hidden scheduler authority
independent scheduling choice != material semantic choice
material semantic choice != scheduler discretion

replay derivation != retry Attempt
process restart != proof of external failure
unknown external outcome != automatic retry

WorkerNeed != delegation widening
Capability Match != Authorization
Authorization != Effect
Outcome != parent completion
quiescent != parent completion
```

## 24. M2.0 Definition of Done

M2.0 is complete when:

```text
M1 remains frozen and unmodified semantically
runtime orchestration responsibility is explicit
Host / Orchestrator / Governance / Executor / Worker boundaries remain distinct
canonical lifecycle state is frozen as immutable record-graph semantics
mutable session state is explicitly non-canonical
one global status enum is explicitly rejected as canonical lifecycle state
replayability rules are explicit
transition-frontier semantics are explicit
material choice remains outside scheduler discretion
unknown-outcome/retry boundaries remain fail-closed
no public runtime API is prematurely frozen
planned M2.1–M2.6 implementation slices are recorded
repository CI passes without runtime/API/wire-schema changes
```

Once this charter merges, implementation may proceed to **M2.1 — Initial Resolution Orchestrator**.
