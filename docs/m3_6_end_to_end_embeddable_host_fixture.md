# M3.6 — End-to-End Embeddable Host Fixture

Status: **M3 closure candidate — executable integration proof, not a new Host runtime**.

Exact base:

```text
intent-resolution-runtime/main@21accb2bed0a5c8d650a590166090c4ea329826f
```

M3.1–M3.5 froze the minimum real Host integration seams around the already-frozen M1/M2 core:

```text
M3.1  exact admitted history / replay
M3.2  Cognitive Provider proposal transport
M3.3  external Governance review transport
M3.4  Executor invocation with durable pre-dispatch Attempt commitment
M3.5  Worker handoff with durable pre-dispatch handoff commitment
```

M3.6 asks one final question:

> Can a real embedding Host compose those seams end to end, survive Host-side reconstruction, and replay semantic state without creating a universal mutable `HostRuntime` or turning replay into external re-execution?

The answer is proven by executable fixtures rather than by adding another production abstraction.

```text
fixture composition != production HostRuntime
Host sequencing != semantic authority
Host mechanism state != canonical semantic history
```

## 1. Why M3.6 is a fixture, not another runtime layer

M2.6 proved the frozen M2 orchestrators compose when a test plays the Host role manually. M3 then added the missing external integration mechanisms. The architectural risk at M3.6 is therefore not lack of another object. The risk is that the individual seams only look correct in isolation but cannot be assembled without hidden mutable state, implicit authority, or replaying external calls.

M3.6 deliberately adds no production Python module.

The fixture itself owns ordinary local variables and call ordering, exactly as an embedding product can. Semantic state still comes from exact canonical records and derived M2 frontiers.

```text
Python variable != canonical lifecycle state
fixture call order != semantic precedence
adapter object != authority
```

## 2. Two independent downstream lanes

One artificial mega-flow that forces every intent through both Executor and Worker would create semantics merely to exercise APIs. M3.6 instead uses two bounded lanes sharing the same integration principles.

### Capability / Executor lane

```text
IntentRequest + ContextEnvelope
        ↓
explicit provider projection
        ↓
CognitiveProviderPort
        ↓
CandidateResolution
        ↓
explicit M2.1 Resolution admission
        ↓
ResolvedIntent
        ↓
explicit WorkPlan disposition admission
        ↓
exact CapabilityRequirement admission
+ exact CapabilityCatalogSnapshot admission
        ↓
IRR deterministic mechanical evaluation
        ↓
WorkProposal
        ↓
GovernancePort
        ↓
GovernanceDecision(AUTHORIZE)
        ↓
M2.3 Authorization materialization frontier
        ↓
explicit Authorization history admission
        ↓
CapabilityAttempt
        ↓
persist Attempt before effect boundary
        ↓
ExecutorPort
        ↓
CapabilityOutcome
        ↓
explicit post-return Outcome persistence
```

### Worker lane

```text
ResolvedIntent + exact parent WorkPlan
        ↓
exact DelegatedWork
        ↓
exact DelegatedWorkHandoff
        ↓
persist handoff before external boundary
        ↓
WorkerPort
        ↓
WorkerResult
        ↓
explicit post-return WorkerResult persistence
        ↓
M2.5 replay
```

The lanes are independent because ordinary capability invocation does not imply Worker delegation and Worker delegation does not imply ordinary Executor invocation.

```text
ordinary capability path != implicit Worker path
Worker handoff != CapabilityAttempt
```

## 3. Provider transport does not become admission

The capability fixture constructs one explicit provider projection from one exact `IntentRequest` and its exact bounded `ContextEnvelope`.

`invoke_cognitive_provider(...)` returns only attributable `CandidateResolution` proposal material.

The fixture must then separately invoke the frozen M2.1 admission boundary.

```text
provider call succeeded != ResolvedIntent admitted
provider proposal != IRR admission
```

No provider receives the repository, principal object, Governance port, Executor port, Worker port, or ambient Host data through the M3.2 contract.

## 4. Work and capability semantics remain explicit admissions

M3.6 does not jump from `ResolvedIntent` directly to invocation.

The fixture explicitly crosses the already-frozen semantic boundaries for:

- Work disposition / exact `WorkPlan` admission;
- exact `CapabilityRequirement` admission;
- exact bounded `CapabilityCatalogSnapshot` admission;
- deterministic mechanical match evaluation.

This keeps the M3 integration proof honest:

```text
ResolvedIntent != WorkPlan
WorkPlan != CapabilityRequirement
Catalog membership != capability selection authority
mechanical match != Governance
```

## 5. Governance remains external and Authorization remains separate

The fixture sends one exact `WorkProposal` through `GovernancePort.review(...)` and receives an exact attributable `GovernanceDecision`.

Even when the decision contains `AUTHORIZE`, no Authorization exists yet.

M2.3 must first expose the exact eligible `Authorization` on its materialization frontier, and the fixture must explicitly supply that exact record back as admitted history.

```text
GovernanceDecision(AUTHORIZE) != admitted Authorization
Authorization materialization candidate != admitted Authorization
```

Only that exact admitted Authorization is presented on the later `CapabilityAttempt`.

## 6. Executor crossing uses the M3.4 crash boundary

The exact `CapabilityAttempt` is persisted before `ExecutorPort.invoke(...)` is crossed.

Only a fresh `HistoryPersistResult.INSERTED` occurrence may execute. The returned `CapabilityOutcome` is separately validated and is not automatically persisted by M3.4.

The fixture therefore performs an explicit post-return Outcome persistence step.

```text
Attempt persisted != effect success
Outcome returned != Outcome durably persisted
Outcome persisted != parent completion
```

This preserves the real crash window instead of hiding it inside an all-in-one Host transaction.

## 7. Worker crossing uses the M3.5 crash boundary

The exact `DelegatedWorkHandoff` is persisted before the external Worker call.

The Worker receives only that bounded handoff envelope. A returned `WorkerResult` is exact result material, not parent completion, and is explicitly persisted only after return.

```text
handoff persisted != Worker acceptance
WorkerResult returned != parent completion
WorkerResult persistence != completion proof
```

The fixture does not auto-satisfy `WorkerNeed`, widen scope, or recursively delegate.

## 8. Restart/reconstruction proof

The strongest M3.6 property is not the first successful call sequence. It is what happens after Host-side integration objects are discarded and recreated.

The retained repository contains exact canonical bytes. M3.6 retrieves those bytes, re-parses them through the existing schema-specific `from_json_bytes(...)` constructors, and re-derives the relevant M2 frontiers from the reconstructed records.

For the capability lane, replay reconstructs at least:

```text
ResolvedIntent
WorkPlan
CapabilityRequirement
CapabilityMatchEvaluation
WorkProposal
GovernanceDecision
Authorization
CapabilityAttempt
CapabilityOutcome
```

and M2.3 / M2.4-derived state can be recomputed without calling Provider, Governance, or Executor again.

For the Worker lane, replay reconstructs:

```text
ResolvedIntent
parent WorkPlan
DelegatedWork
DelegatedWorkHandoff
WorkerResult
```

and M2.5 can be recomputed without redispatching the Worker.

```text
semantic replay = exact record reconstruction + frontier derivation
semantic replay != adapter recall
```

## 9. Replay-block proof

M3.6 also deliberately attempts the dangerous operations after history reconstruction:

```text
same exact CapabilityAttempt -> invoke Executor again
same exact DelegatedWorkHandoff -> dispatch Worker again
```

Both must fail before the external adapter receives a second call.

This is the integration-level proof of the M3 rule:

```text
restart != retry permission
semantic replay != external re-execution
```

M3.6 does not claim distributed exactly-once delivery. It proves that IRR itself will not transform semantic replay into a duplicate external dispatch for an exact already-committed occurrence.

## 10. Repository remains storage, not active-state selection

The fixture never asks the repository for `latest`, `current`, or `active` state. It retrieves exact identities known from the semantic graph and passes exact reconstructed records to existing orchestrators.

```text
record present != active by storage
identity lookup != lifecycle selection
repository order != semantic precedence
```

Any competing active graph material must still be handled by the frozen semantic/orchestration boundaries rather than by storage ordering.

## 11. No central Host object is required

M3.6 intentionally proves composition with ordinary fixture-local wiring.

The public package must still expose no:

```text
HostRuntime
HostSession
orchestrate_host
orchestrate_end_to_end
```

The absence is a positive result, not missing implementation.

A product such as HDE may later own a convenience composition object, dependency-injection container, service graph, queues, or UI-facing session view. Such a product object is reconstructible mechanism state and is not part of IRR canonical semantics.

## 12. What M3.6 deliberately does not add

M3.6 adds no:

- universal Host runtime;
- mutable canonical session;
- scheduler;
- adapter registry;
- provider ranking;
- capability discovery;
- capability availability probe;
- hidden WorkPlan generator;
- hidden CapabilityRequirement generator;
- embedded Governance engine;
- automatic Authorization admission;
- retry/fallback/recovery engine;
- automatic Outcome persistence;
- automatic WorkerResult persistence;
- WorkerNeed satisfaction;
- parent completion evaluator;
- acquisition port implementation;
- SQLite/filesystem/network persistence backend;
- HDE-specific dependency.

M3.6 also does not force Executor and Worker into one universal downstream abstraction.

## 13. M3.6 acceptance

M3.6 is complete when executable tests prove at least:

```text
M3.2 provider projection -> CandidateResolution without admission
explicit M2.1 admission -> ResolvedIntent
explicit work disposition admission -> exact WorkPlan
explicit capability requirement/catalog admission -> deterministic evaluation
M3.3 Governance -> GovernanceDecision without automatic Authorization
M2.3 explicitly materializes and then admits exact Authorization
M3.4 persists exact Attempt before Executor call
Executor returns exact Outcome and Host persists it separately
M3.5 persists exact handoff before Worker call
Worker returns exact WorkerResult and Host persists it separately
exact stored bytes can be reparsed after Host-side reconstruction
M2.3/M2.5 replay derives the same semantic frontier from reconstructed records
replay performs zero Provider/Governance/Executor/Worker calls
same exact Attempt cannot be reinvoked
same exact handoff cannot be redispatched
no public HostRuntime/HostSession/end-to-end super-orchestrator is introduced
all earlier frozen tests remain green
Python 3.11–3.14 CI passes
```

## 14. M3 closure

If the executable fixture passes without a new production Host abstraction, M3 has answered its original integration question.

```text
M1 = canonical semantic records
M2 = replayable semantic orchestration
M3 = narrow embeddable Host integration mechanisms around those records/orchestrators
```

M3 completion therefore does **not** mean IRR became an autonomous agent runtime. It means an embedding product can now connect exact storage, proposal cognition, external Governance, effect execution, and delegated work without collapsing their authority boundaries.

Frozen M3 closure invariants:

```text
Host integration != semantic authority
HostState != canonical semantic history
provider proposal != IRR admission
GovernanceDecision != Authorization
Authorization != invocation
Attempt != Outcome
WorkerResult != parent completion
semantic replay != external re-execution
restart != retry permission
fixture composition != production HostRuntime
IRR core != HDE integration
```

After M3.6, a next milestone must be selected from concrete product-integration evidence rather than extending M3 with speculative glue.