# M3.4 — Executor / Capability Invocation Port

Status: **proposed Host integration boundary for external capability invocation**.

Exact base:

```text
intent-resolution-runtime/main@cca5d99f06fe85428f1d3ea7e0f1eef632989fcd
```

M1.7 froze `CapabilityAttempt` and `CapabilityOutcome` as separate canonical records.
M2.4 froze replayable orchestration over exact Attempt / Outcome history. M3.1 added
exact durable history with idempotent persistence. M3.4 moves one layer outward and
answers one Host-integration question:

> How may a real Host cross an external Executor boundary exactly once for one exact
> `CapabilityAttempt`, while preserving admitted capability routing and preventing a
> restart or replay from becoming an implicit retry?

The answer is deliberately narrow.

## 1. Boundary

```text
exact fully-bound CapabilityAttempt
        ↓
M3.4 pre-dispatch validation
        ├── exact source Attempt
        └── explicit Executor-boundary routing
        ↓
persist exact Attempt in AdmittedHistoryRepository
        ├── INSERTED
        │      ↓
        │  ExecutorPort.invoke(...)
        │      ↓
        │  exact CapabilityOutcome
        │      ↓
        │  validate Outcome ↔ exact Attempt
        │
        └── ALREADY_PRESENT
               ↓
             STOP
      no automatic reinvocation
```

`CapabilityInvocationRequest` is Host mechanism state. It is not a new canonical
semantic record. The embedded `CapabilityAttempt` remains the canonical Attempt history.

## 2. Why Attempt persistence is part of the invocation boundary

M0.9 and M3.0 freeze:

```text
Host crash after send != no external effect
missing Outcome != failed
restart != automatic retry
retry != continuation of the same Attempt
```

A naive adapter API can violate all four invariants:

```text
call external executor
→ process crashes after request transmission
→ Attempt was never durably recorded
→ restart sees no Attempt
→ same operation is sent again
```

For an effectful capability this can duplicate an external effect.

M3.4 therefore uses the exact M3.1 repository before crossing the external Executor
boundary.

The persistence point is the Host's durable commitment that the concrete invocation
effort has begun. `CapabilityAttempt` does not claim that the requested effect occurred;
it records one bounded effort to invoke the exact capability-backed WorkStep.

```text
Attempt persisted != effect occurred
Attempt persisted != Outcome known
Attempt persisted != success
```

Once this commitment exists, the exact same Attempt is never automatically dispatched
again.

## 3. INSERTED versus ALREADY_PRESENT

M3.1 already freezes idempotent persistence:

```text
HistoryPersistResult.INSERTED
HistoryPersistResult.ALREADY_PRESENT
```

M3.4 gives that distinction an execution-safety consequence.

For a fresh exact Attempt:

```text
persist -> INSERTED
→ this invocation boundary may call ExecutorPort once
```

For an already-recorded exact Attempt:

```text
persist -> ALREADY_PRESENT
→ fail closed
→ do not call ExecutorPort
```

This is not a claim that the older Attempt definitely reached the external system. It is
a refusal to infer retry safety from missing local knowledge.

```text
already recorded Attempt != safe to resend
```

If recovery later establishes that another effort is appropriate, the retry is a new
canonical `CapabilityAttempt` with a distinct `attempt_event_ref`.

```text
Attempt N != Attempt N+1
```

M3.4 contains no retry scheduler and creates no retry automatically.

## 4. CapabilityInvocationRequest

The public mechanism request contains exactly:

```text
CapabilityInvocationRequest
└── attempt: CapabilityAttempt
```

It deliberately does not duplicate:

- capability identity;
- WorkStep semantics;
- bound values;
- requested effects;
- Authorization lineage;
- execution-boundary semantics.

Those are already identity-covered by the exact embedded Attempt and its exact
`CapabilityMatchEvaluation` / Catalog lineage.

The request has no `SCHEMA`, canonical identity, or canonical bytes. It is mechanism
state, not a second lifecycle record.

## 5. Exact source Attempt is rebound before invocation

`invoke_executor(...)` receives the exact source `CapabilityAttempt` separately and
requires:

```text
request.attempt == exact source attempt
```

This check occurs before persistence and before the external Executor call.

A manually constructed request cannot substitute another valid-looking Attempt while
retaining the Host's invocation path.

## 6. Runtime routing is stricter than historical Attempt representation

M1.7a1 deliberately permits a historical `CapabilityAttempt.executor_ref` to disagree
with the Descriptor's expected execution boundary. That keeps a misrouted historical
Attempt representable.

M1.7a1 also explicitly leaves a future runtime gate responsible for preventing invalid
substitution before execution.

M3.4 is that gate for the first Host invocation port.

For the exact matched `CapabilityDescriptor`:

```text
0 explicit EXECUTOR boundaries
    → M3.4 does not invent a material executor identity

1 explicit EXECUTOR boundary
    → attempt.executor_ref must equal that exact boundary_ref

>1 explicit EXECUTOR boundaries
    → fail closed
    → M3.4 does not choose by tuple/catalog/registration order
```

Several execution-boundary roles may coexist in one Descriptor. `PROVIDER`, `ADAPTER`,
`SERVICE`, and `OTHER_EXPLICIT` entries are not silently reinterpreted as alternative
Executor identities.

```text
execution-boundary list != routing priority list
multiple Executor refs != permission for scheduler choice
```

A future contract may add explicit routing semantics if real capabilities need multiple
interchangeable Executor choices. M3.4 does not invent them.

## 7. ExecutorPort is invocation-only

The public protocol is conceptually:

```python
def invoke(request: CapabilityInvocationRequest) -> CapabilityOutcome: ...
```

The port receives the exact Attempt after the Host has durably committed that Attempt.
It returns one exact `CapabilityOutcome`.

It has no protocol surface for:

```text
select_capability(...)
choose_executor(...)
authorize(...)
retry(...)
fallback(...)
continue_parent(...)
read_history(...)
```

The exact Attempt already fixes capability relation, WorkStep, concrete bound inputs, and
presented Authorization lineage.

```text
Executor != resolver
Executor != Governance
Executor failure != fallback authority
```

## 8. Executor object identity is not self-attestation

M3.4 validates the canonical Attempt's `executor_ref` against explicit Descriptor
`EXECUTOR` semantics where those semantics are singular and material.

It does **not** ask a Python adapter object to expose a second self-declared
`executor_ref` and then call that identity verification.

That would merely compare two Host-/adapter-supplied labels and create false trust.

```text
executor attribution != executor authentication
StableRef equality != cryptographic attestation
```

Concrete Hosts may authenticate adapter connections outside this protocol.

## 9. Authorization applicability is not reclassified by M3.4

M1.7a1 intentionally allows `CapabilityAttempt.presented_authorizations` to be empty.
Some bounded operations may be authority-neutral; historical unauthorized Attempts must
also remain representable.

Therefore M3.4 does not introduce a Host boolean such as:

```text
requires_authorization = true/false
approved = true
safe = true
```

and does not infer:

```text
no presented Authorization -> authority not required
presented Authorization -> all conditions are currently satisfied
```

If Authorization is present, existing `CapabilityAttempt` validation preserves its exact
proposal / decision / step / capability-evaluation lineage.

Whether external authority is required and whether its dynamic conditions remain
applicable belong to the embedding Governance/authority mechanism. A Host must call the
Executor only when applicable authority requirements are satisfied.

```text
M3.4 invocation mechanism != Governance authority
```

## 10. Outcome is exact canonical material, not transport success

A successful `ExecutorPort.invoke(...)` return must be an exact `CapabilityOutcome` whose
embedded `attempt` equals the exact persisted Attempt.

A foreign Outcome fails closed.

The return type does not mean that an HTTP response, ACK, callback, or arbitrary executor
message automatically constitutes semantic completion. A concrete Executor adapter is
responsible for returning a `CapabilityOutcome` only when it can construct the already-
frozen Outcome dimensions and evidence honestly.

```text
transport return != CapabilityOutcome automatically
transport success != completion satisfied
executor assertion != truth by definition
```

M1.7a2 remains authoritative for lifecycle, completion, effect certainty, and evidence.

## 11. Transport / Executor exception leaves Attempt pending

If `ExecutorPort.invoke(...)` raises after the Attempt was inserted, M3.4 propagates the
mechanism failure. It does not synthesize:

```text
failed CapabilityOutcome
DENY
retry
fallback
no-effect claim
```

The durable history remains:

```text
CapabilityAttempt present
CapabilityOutcome absent
```

M2.4 already derives this mechanically as an outcome-pending Attempt.

This is the correct fail-closed state after an ambiguous transport failure.

```text
exception after dispatch != no effect
missing Outcome != failed
```

A later reconciliation mechanism may add attributable Outcome evidence. M3.4 does not
freeze that acquisition/reconciliation subsystem.

## 12. Outcome persistence is not hidden inside ExecutorPort

M3.4 validates and returns the exact `CapabilityOutcome`, but does not automatically
persist it.

That is deliberate.

The safety-critical persistence is the pre-dispatch Attempt commitment. If the process
crashes after an external effect but before the returned Outcome is persisted, the exact
Attempt still exists and blocks automatic reinvocation.

The Host may subsequently persist the validated Outcome as an exact M3.1 history record.

```text
Outcome returned != Outcome durably persisted
Outcome not persisted != safe retry
```

This also keeps the Executor protocol independent from repository mutation authority.

## 13. Wrong return type or foreign Outcome

If the Executor returns anything other than exact `CapabilityOutcome`, or returns an
Outcome for another Attempt:

```text
Attempt remains persisted
→ integration error propagates
→ no automatic second invocation
```

The invalid result does not erase the historical dispatch commitment.

This matters because adapter-contract failure may occur after an external effect.

## 14. Repository failure does not become execution

M3.4 never invokes the Executor unless exact Attempt persistence returns `INSERTED`.

If persistence raises, returns an unsupported result, or cannot establish a fresh exact
Attempt commitment:

```text
no Executor call
```

The Host must resolve the persistence state explicitly rather than assuming the external
operation was not attempted and retrying optimistically.

## 15. No automatic capability selection

The request carries one exact `CapabilityAttempt`, which in turn requires one exact
uniquely classified `CapabilityMatch`.

M3.4 has no access to a catalog-wide selection callback and does not compare alternative
capabilities.

```text
Executor installed != Capability selected
multiple compatible capabilities != Executor choice
Capability Match != invocation
```

Capability ambiguity must be resolved before an Attempt can reach this boundary.

## 16. No automatic retry or fallback

The public invocation helper has no retry/fallback argument or callback.

Executor failure, transport failure, missing Outcome, and `ALREADY_PRESENT` do not grant
authority to select another capability or resend the same Attempt.

```text
Executor failure != fallback authority
ALREADY_PRESENT != retry permission
```

Any later recovery decision remains explicit successor/recovery work under the frozen
M0.9 rules.

## 17. Replay semantics

Semantic replay may reconstruct that an Attempt exists and has no Outcome.

Replay must not call `ExecutorPort.invoke(...)` merely because that state is pending.

The exact same Attempt sent back through `invoke_executor(...)` encounters
`ALREADY_PRESENT` and fails closed.

```text
semantic replay != external re-execution
restart != retry permission
```

This gives M3.1 persistence a concrete execution-safety role without turning repository
order into lifecycle semantics.

## 18. Deliberate non-goals

M3.4 adds no:

- capability discovery;
- capability ranking or selection;
- availability probe;
- embedded Governance engine;
- Authorization-condition evaluator;
- generic policy boolean;
- retry scheduler;
- fallback selector;
- idempotency-key protocol;
- distributed transaction with external services;
- automatic Outcome persistence;
- Outcome reconciliation/acquisition mechanism;
- central `HostRuntime`;
- HDE-specific executor implementation.

The boundary does not claim to solve arbitrary distributed exactly-once effects. It
prevents IRR replay/restart from **automatically** issuing the same exact Attempt again.
External systems may still require their own idempotency or transactional mechanisms.

## 19. Acceptance invariants

M3.4 is accepted when tests prove:

```text
exact Attempt source is checked before dispatch
explicit singular EXECUTOR boundary is enforced
multiple explicit EXECUTOR boundaries fail closed
no explicit EXECUTOR boundary does not invent routing semantics
Attempt persistence happens before Executor invocation
INSERTED permits one invocation
ALREADY_PRESENT blocks automatic reinvocation
Executor exception leaves exact Attempt durable
retry requires a different Attempt identity / occurrence
wrong return type leaves Attempt durable
foreign Outcome is rejected
Outcome is not auto-persisted
Authorization applicability is not invented by M3.4
CapabilityInvocationRequest is mechanism state, not canonical IR
ExecutorPort exposes no retry/fallback/Governance/selection authority
```

and repository CI passes on all supported Python versions.

## 20. Next slice

If M3.4 merges without revealing another prerequisite, the next planned Host integration
slice is:

# **M3.5 — Worker Integration Port**

M3.5 should apply the same discipline to exact `DelegatedWork` / `DelegatedWorkHandoff`
without giving a Worker ambient parent state, scope widening, authority inheritance, or
parent-completion authority.
