# M3.5 — Worker Integration Port

Status: **proposed Host integration boundary for bounded external Worker handoff**.

Exact base:

```text
intent-resolution-runtime/main@43a474723a3dcfc541b5653783b948a59f8b17be
```

M1.5 froze `DelegatedWork`, `DelegatedWorkHandoff`, and `WorkerResult` as separate
canonical records. M2.5 froze replayable Worker-lifecycle projections without selecting
an active Worker, treating missing results as failure, satisfying `WorkerNeed`, or
interpreting Worker output as parent completion. M3.5 moves one layer outward and asks:

> How may a real Host cross the external Worker boundary for one exact already-admitted
> handoff without turning transport, restart, Worker output, or adapter convenience into
> scope widening, authority, retry, factual admission, or parent completion?

The answer is deliberately narrow.

## 1. Boundary

```text
exact DelegatedWorkHandoff
        ↓
WorkerHandoffRequest
        ↓
pre-dispatch source validation
        ↓
persist exact DelegatedWorkHandoff
   ├── INSERTED
   │      ↓
   │   WorkerPort.perform(...)
   │      ↓
   │   exact WorkerResult
   │      ↓
   │   result/handoff lineage validation
   │
   └── ALREADY_PRESENT
          ↓
        STOP
   no automatic redispatch
```

`WorkerHandoffRequest` is Host mechanism state. It is not a new canonical semantic
record and it grants no scope, capability, disclosure, or authority.

## 2. Worker receives the exact admitted handoff envelope

The request contains exactly one field:

```text
handoff: DelegatedWorkHandoff
```

The embedded `DelegatedWork` already carries the frozen bounded semantics:

- parent lineage identities;
- delegated objective;
- delegated scopes;
- explicit context-reference surface;
- capability ceiling;
- material / forbidden-effect / authority-requirement constraints;
- expected deliverables;
- delegated completion contract.

M3.5 does not add ambient Host state around that envelope.

The Worker request has no:

- parent session object;
- history repository handle;
- Context store;
- memory store;
- filesystem/browser handle;
- capability registry;
- Governance engine;
- Authorization store;
- Executor port;
- recursive Worker-dispatch handle.

```text
Worker receives DelegatedWork
not ambient parent state
```

## 3. Context references do not become ambient retrieval authority

`DelegatedWork.context_surface` remains the exact M1.5 bounded reference surface.

M3.5 does not invent a generic blob transport or automatically dereference those
references through Host storage.

```text
context reference != content
context reference != retrieval authority
Host possesses referenced material != Worker may retrieve it ambiently
```

A concrete product adapter may transport material already admitted for the Worker
boundary under product-owned rules, but such transport must preserve the frozen
DelegatedWork disclosure semantics. M3.5 does not add a hidden acquisition port.

## 4. WorkerPort is bounded work only

The public protocol is conceptually:

```python
def perform(request: WorkerHandoffRequest) -> WorkerResult: ...
```

The protocol deliberately exposes no:

```text
retry(...)
fallback(...)
authorize(...)
govern(...)
widen_scope(...)
grant_capability(...)
retrieve(...)
search(...)
persist(...)
complete_parent(...)
delegate_worker(...)
```

An installed Worker adapter therefore does not become a general autonomous-agent API.

```text
WorkerPort installed != Worker dispatch authority
WorkerPort installed != scope authority
WorkerPort installed != capability authority
WorkerPort installed != Governance authority
```

## 5. Exact source binding is checked before disclosure

`invoke_worker(...)` receives the exact source `DelegatedWorkHandoff` separately and
requires the prepared `WorkerHandoffRequest` to contain that exact handoff before any
repository commit or external Worker call.

```text
exact source DelegatedWorkHandoff
→ validated WorkerHandoffRequest
→ durable handoff commitment
→ external Worker
```

A manually fabricated request containing a foreign handoff fails before transport.

## 6. Handoff persistence precedes external Worker transport

M3.5 persists the exact canonical `DelegatedWorkHandoff` through the M3.1
`AdmittedHistoryRepository` before calling the Worker.

This is a crash/replay boundary, not a claim that the Worker has accepted the work.

```text
handoff persisted != Worker received bytes
handoff persisted != Worker accepted work
handoff persisted != Worker started work
handoff persisted != delegated completion
```

The persisted record means that the Host committed this exact handoff occurrence as the
one being crossed at the external Worker boundary.

The distinction matters because M1.5 already freezes:

```text
DelegatedWorkHandoff != transport
DelegatedWorkHandoff != Worker acceptance
DelegatedWorkHandoff != execution
```

M3.5 does not weaken those meanings.

## 7. Fresh persistence is the dispatch freshness gate

Only:

```text
HistoryPersistResult.INSERTED
```

may proceed to `WorkerPort.perform(...)`.

If persistence returns:

```text
HistoryPersistResult.ALREADY_PRESENT
```

M3.5 raises `WorkerReplayBlockedError` and does not call the Worker.

```text
same exact handoff already in history
!= safe to dispatch again
```

This implements the M3 invariant:

```text
semantic replay != external re-execution
restart != retry permission
```

## 8. Crash / transport ambiguity remains explicit

Consider:

```text
persist exact handoff
→ send to Worker
→ Worker may accept/start/produce effects
→ transport or Host process fails before WorkerResult is durably recorded
```

After restart, exact admitted history may honestly contain:

```text
DelegatedWorkHandoff present
WorkerResult absent
```

M2.5 already defines this as neutral `result_pending_handoffs` material.

It is not automatically:

```text
Worker failed
Worker timed out
Worker did nothing
safe to retry
safe to substitute
```

M3.5 therefore refuses to redispatch the same handoff automatically.

## 9. A real retry/substitution requires a new handoff occurrence

M2.5 intentionally permits multiple exact `DelegatedWorkHandoff` records for one exact
`DelegatedWork` without selecting a latest/active Worker.

M3.5 preserves that model.

A later explicit recovery decision may create another handoff with, for example:

- a new `handoff_event_ref` to the same Worker; or
- a new Worker target plus a new handoff occurrence.

That produces a different canonical handoff identity and can cross M3.5 as a fresh
occurrence.

```text
same handoff redispatch != retry policy
new handoff occurrence != mutation of prior handoff
Worker substitution != semantic equivalence proof
Worker substitution != authority inheritance
```

M3.5 does not choose or synthesize the new handoff.

## 10. Worker identity remains attribution, not attestation

The exact handoff already contains:

```text
dispatcher_ref
worker_ref
handoff_event_ref
```

M3.5 does not add a second `worker_ref` property to the Python adapter and pretend that
comparing two Host-supplied refs proves physical identity.

```text
worker_ref = attribution
worker_ref != authentication
worker_ref != trust proof
```

The returned `WorkerResult` constructor already requires its Worker attribution to match
the exact Worker targeted by the embedded handoff. M3.5 additionally requires the
returned result to embed the exact handoff that was dispatched.

## 11. Output binding is fail-closed

A successful return must be an exact `WorkerResult` and:

```text
result.handoff == exact dispatched handoff
```

A valid-looking result for another handoff does not cross the M3.5 boundary.

The existing frozen `WorkerResult` constructor continues to enforce:

- result Worker attribution matches handed-off Worker;
- result occurrence differs from handoff occurrence;
- material scopes remain within admitted DelegatedWork scopes;
- deliverable references/types/scopes remain exact;
- WorkerNeed related existing scopes remain admitted.

M3.5 does not duplicate those semantic validators.

## 12. WorkerResult remains returned material, not parent completion

Returning a `WorkerResult` through the port does not strengthen its semantics.

```text
WorkerResult != factual truth by default
WorkerResult != Observation by default
WorkerResult != Outcome by default
WorkerResult != GovernanceDecision
WorkerResult != Authorization
WorkerResult != parent completion
```

A `completion_claim` remains a Worker assertion.

A returned deliverable remains returned material structurally related to an
`ExpectedDeliverable`; it does not prove the Delegated Completion Contract or parent
intent satisfaction.

M2.5 and M2.4 remain responsible for derived Worker lifecycle and any explicitly selected
Continuation re-entry.

## 13. WorkerNeed remains a need

M3.5 transports all frozen `WorkerNeedKind` values without satisfying them:

```text
information
capability
authority
scope
clarification
objective_change
effect_boundary
other_explicit
```

The port does not react by acquiring data, discovering another capability, widening
scope, calling Governance, changing the objective, or authorizing effects.

```text
WorkerNeed != action
WorkerNeed != scope expansion
WorkerNeed != capability grant
WorkerNeed != Authorization
WorkerNeed != successor semantics
```

Any material response returns through existing explicit Host / IRR boundaries.

## 14. No automatic WorkerResult persistence

M3.5 deliberately does not persist the returned `WorkerResult` inside
`invoke_worker(...)`.

The pre-dispatch handoff commit and post-return result admission/persistence are distinct
Host transitions.

This preserves the crash window honestly:

```text
handoff committed
+ external Worker activity may have occurred
+ WorkerResult not yet durably admitted
```

M3.5 must not turn that into a fabricated result or an automatic second Worker run.

A Host may mechanically persist the exact returned WorkerResult after validation under
the M3.1 repository contract. That remains separate from the external Worker call.

## 15. Multiple WorkerResult occurrences remain possible

M1.5/M2.5 intentionally permit multiple WorkerResult records for one handoff and do not
define `latest_result` or `final_result`.

M3.5 `perform(...) -> WorkerResult` represents one bounded request/return exchange only.
It does not redefine the overall Worker lifecycle as single-result.

Future product-specific streaming, callbacks, progress, reconciliation, or additional
result delivery may create additional exact WorkerResult occurrences while preserving the
same handoff lineage.

```text
one M3.5 return != only possible WorkerResult
multiple WorkerResults != latest wins
multiple WorkerResults != delegated completion
```

## 16. No Worker-local expansion

M3.5 passes the exact immutable delegation envelope and exposes no mutation surface.

The Worker cannot use this protocol to rewrite:

- objective;
- scopes;
- context surface;
- allowed capabilities;
- constraints;
- expected deliverables;
- completion contract;
- parent lineage.

A material need for expansion can only be returned as Worker result/need material.

## 17. No recursive delegation authority

`WorkerPort` has no Worker-dispatch handle.

Internal helper agents or model components remain Worker implementation detail unless a
future explicit IRR nested-delegation contract is admitted.

```text
Worker handoff != recursive delegation authority
```

## 18. No generic autonomous-agent loop

M3.5 does not add a scheduler or loop such as:

```text
while not done:
    let Worker inspect ambient state
    let Worker pick tools
    auto-satisfy needs
    retry failures
    widen scope if useful
```

That would violate the existing Worker boundary.

The integration seam is one already-admitted bounded handoff occurrence only.

## 19. Explicit non-goals

M3.5 does not add:

- Worker discovery or registry;
- Worker ranking/selection;
- proof that two Workers are interchangeable;
- ambient context retrieval;
- generic artifact transport;
- Worker progress/streaming schema;
- Worker acceptance/rejection state;
- cancellation/timeout model;
- automatic retry or fallback;
- recovery/substitution policy;
- nested Worker delegation;
- recursive Worker scheduling;
- WorkerResult factual admission;
- WorkerResult → Outcome conversion;
- delegated completion evaluation;
- parent WorkPlan completion evaluation;
- parent intent satisfaction evaluation;
- WorkerNeed satisfaction;
- scope/context/capability widening;
- Authorization creation/inheritance;
- generic Continuation source selection;
- automatic WorkerResult persistence;
- a public HostRuntime;
- Codexia-specific dependency.

## 20. Frozen M3.5 invariants

```text
Worker receives exact DelegatedWorkHandoff, not ambient parent state
WorkerHandoffRequest != canonical semantic record
WorkerPort installed != dispatch authority

handoff persisted != Worker acceptance
handoff persisted != Worker execution
handoff persisted != completion
same exact handoff persisted -> no automatic redispatch
restart != retry permission
new retry/substitution -> new handoff occurrence

WorkerResult.handoff must equal exact dispatched handoff
WorkerResult != factual truth by default
WorkerResult != Outcome by default
WorkerResult != parent completion
completion claim != delegated completion proof

WorkerNeed != scope expansion
WorkerNeed != capability grant
WorkerNeed != Authorization
WorkerNeed != successor semantics

WorkerResult validation != automatic persistence
multiple WorkerResults != latest/final result policy
```

## 21. Acceptance

M3.5 is complete when executable tests prove at least:

```text
request contains exactly one exact DelegatedWorkHandoff
prepared request is rebound to exact source handoff before dispatch
forged foreign handoff fails before persistence/Worker call
fresh handoff is durably persisted before Worker call
already-persisted exact handoff blocks Worker redispatch
Worker/transport failure leaves exact handoff durable
same handoff cannot become an implicit retry after transport failure
new handoff occurrence remains separately dispatchable
Worker must return exact WorkerResult type
foreign WorkerResult handoff fails closed
WorkerNeed returns as data without widening DelegatedWork
completion claim remains Worker material, not parent completion
successful result is not automatically persisted
request/port expose no ambient retrieval, retry, authority, or recursive-delegation surface
all frozen M0/M1/M2/M3.1–M3.4 tests remain green
Python 3.11–3.14 CI passes
```

After M3.5 closes, the direct next slice is **M3.6 — End-to-End Embeddable Host
Fixture**. M3.6 should compose the already-frozen M3 ports rather than invent a universal
mutable Host runtime.
