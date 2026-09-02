# M3.0 — Host Integration Charter

Status: **proposed normative charter for M3**. It becomes the M3 baseline only when this PR merges.

M1 froze canonical attributable semantic records. M2 froze replayable orchestration over those records. M3 moves one layer outward: real Host integration without making integration machinery a new semantic or authority source.

The central decision is:

```text
Host integration != semantic authority
Host integration != Governance authority
Host integration != evidence truth
Host integration != canonical lifecycle state
```

M3.0 adds no production Host runtime and no new canonical semantic record.

---

## 1. Host boundary

A Host may own mechanisms for:

- receiving external intent occurrences;
- constructing already-permitted bounded Context;
- calling Cognitive Providers;
- transporting Governance review;
- invoking Executors when exact authority exists;
- dispatching bounded Worker delegation;
- acquiring explicitly required external material;
- persisting admitted records;
- reconstructing derived runtime views after restart.

Those are mechanism responsibilities.

```text
IRR core != HDE integration
M3 Host boundary != product-specific shell
Host can call mechanism X != IRR is authorized to use X
```

HDE is one Host integration rather than a privileged IRR mode.

M3.0 does not freeze a public `HostRuntime`, mutable `ResolutionSession`, universal tool interface, or global Host state object.

---

## 2. Canonical state and replay

M3 preserves the M2 source-of-truth rule:

```text
canonical semantic lifecycle history
=
exact admitted immutable IRR records

HostState != canonical semantic lifecycle history
```

A Host may keep caches, queues, indexes, connections, cursors, materialized frontiers, or session-shaped convenience views. Those are reconstructible operational state.

```text
cache != canonical history
record persistence != semantic mutation
storage insertion order != lifecycle order
record present != active lineage by default
```

A semantic claim that must survive restart must be recoverable from exact admitted records plus explicit versioned configuration where configuration materially affects semantic replay.

Replay and external execution are different operations:

```text
semantic replay = re-derive frontiers from admitted records
external re-execution = perform an effect again
```

Therefore:

```text
restart != automatic retry
Host crash after send != no external effect
missing Outcome != failed
```

Competing valid-looking material also remains fail-closed:

```text
valid records individually != one valid active lifecycle automatically
competing active lineage != latest-write-wins
competing active lineage != scheduler choice
```

The Host may expose or quarantine conflicts. It must not choose by insertion order, timestamp accident, or queue order.

---

## 3. Existing IntentRequest + ContextEnvelope remain the Host input boundary

M3.0 does not introduce a generic `HostInput`, prompt bundle, raw context blob, or product-specific IRR input record.

```text
external occurrence
+ Host-owned identity/principal mapping
+ Host-permitted bounded semantic material
        ↓
IntentRequest
+ ContextEnvelope
        ↓
IRR validation / resolution
```

### IntentRequest

The Host constructs the frozen `IntentRequest` while preserving:

```text
Origin != Principal
origin attribution != identity verification
principal identity != permission
```

`OriginAttribution.source_event_ref` identifies the concrete occurrence that produced the expression. Companion-, worker-, and system-originated text must not be relabeled as human-originated merely because a human is the principal.

### ContextEnvelope

The Host may construct `ContextEnvelope` only from material already admitted for this Host-to-IRR disclosure boundary under Host-owned trust/access rules.

```text
Host possesses data != admitted IRR Context
local readability != Host-to-IRR disclosure admission
Context boundary attribution != permission proof
```

IRR validates the frozen Context schemas and their links. IRR does not gain ambient Host data access merely because the Host possesses it.

---

## 4. Context mapping is semantic, not transport-shaped

ContextEnvelope remains typed semantic Context, not a text/blob transport.

The frozen meanings remain:

- `ClaimRecord` — attributable proposition presented for resolution;
- `EvidenceRecord` — attributable evidence for an exact target/scope;
- `TemporalBasisRecord` — explicit attributable temporal basis;
- `CompletenessRecord` — explicit attributable completeness assertion;
- `ContextReferenceRecord` — identification of possible source/material whose content is not present.

A Host must not choose a type simply because it has a string field.

```text
raw Host text != ClaimRecord by default
raw Host text != EvidenceRecord by default
Host provenance != EvidenceRecord automatically
Host timestamp != TemporalBasisRecord automatically
Host bounded collection != CompletenessRecord automatically
ContextReferenceRecord.description != hidden content transport
```

M1.2 already freezes:

```text
Context Reference != content
```

A Host must not smuggle raw material into `ContextReferenceRecord.description`.

A Host may construct a `ClaimRecord` only when it can state a proposition without strengthening or changing the source semantics. A product may, for example, form a proposition about its own confirmed state rather than silently treating the underlying state text as a factual world claim.

If no existing Context record kind honestly represents material:

```text
no honest Context mapping
→ omit it from this ContextEnvelope
   or expose an explicit future vocabulary need
→ do not invent semantics for transport convenience
```

M3.0 does not extend the frozen M1 Context wire vocabulary.

---

## 5. External integration mechanisms remain non-authoritative

### Cognitive Provider

The Host may disclose an explicit permitted provider projection and receive attributable `CandidateResolution` proposal material.

```text
provider receives only explicitly projected material
provider proposal != IRR admission
provider output != Context by default
provider output != Observation by default
provider output != Authorization
```

Provider invocation must not hide retrieval. Newly acquired external information must re-enter through an explicit attributable Host/acquisition boundary before semantic admission.

### Governance

Governance remains external.

```text
Host boolean != GovernanceDecision
provider confidence != GovernanceDecision
GovernanceDecision != Effect
GovernanceDecision(AUTHORIZE) != admitted Authorization history
```

### Executor

Executor availability and installation do not imply selection or authority.

```text
WorkStep != invocation
Capability Match != invocation
Authorization != invocation
Executor != resolver
Executor != Governance
Executor failure != fallback authority
```

`CapabilityAttempt` and `CapabilityOutcome` remain separate attributable records.

### Worker

```text
Worker receives DelegatedWork, not ambient parent state
Worker capability ceiling != authority grant
WorkerNeed != scope/capability/authority widening
WorkerResult != parent completion
```

### Acquisition

```text
HostAcquisitionPort installed != retrieval authority
mechanism can read X != X is IRR Context
acquired bytes != factual truth
acquisition result != Observation by default
```

Acquired material that matters semantically must enter through an appropriate explicit IRR boundary.

M3.0 does not freeze public Provider, Governance, Executor, Worker, or acquisition Python protocols.

---

## 6. Attribution and record production

M3 separates mechanical record construction from semantic authority.

Conceptually:

| Boundary | Attributed producer / mechanism | Result still requires |
| --- | --- | --- |
| external intent occurrence | Host boundary | IntentRequest validation + Origin/Principal separation |
| Host Context admission | Host boundary | truthful typed Context semantics |
| interpretation proposal | Cognitive Provider | IRR Candidate admission |
| Governance review | Governance | Authorization materialization boundary |
| capability invocation/result | Executor boundary | Attempt / Outcome semantics |
| delegated work result | Worker boundary | WorkerResult / Continuation semantics |
| external acquisition | Host acquisition mechanism | explicit later semantic admission |

```text
record constructor access != semantic authority
attribution != verification
```

Adapter occurrence identities must identify the concrete occurrence that produced attributable material rather than a timeless adapter installation or product account.

---

## 7. Persistence contract — semantic requirements only

A real Host needs durable admitted history, but M3.0 does not freeze `HistoryRepository` as a public Python protocol.

The later repository boundary must at least preserve:

- exact canonical record bytes or a losslessly equivalent representation;
- record identity and type;
- bounded retrieval of admitted history;
- no insertion-order semantic precedence;
- fail-closed identity/content collisions;
- separation of canonical records from caches/materialized views;
- replay from exact history plus explicit relevant configuration.

Configuration materially affecting semantic derivation, admission, or mapping must be identifiable/versioned for corresponding replay claims.

Examples may include admission-strategy or semantic-mapping policy versions. Tokens, sockets, process handles, and connection pools remain mechanism state.

```text
configuration identity != authority
secret availability != semantic permission
```

---

## 8. Automatic Host sequencing

The Host may automatically sequence only materially neutral transitions under already-admitted semantics and applicable authority.

It must stop or expose choice when alternatives can materially change resource, recipient, disclosure, effect, provider/service, capability semantics, cost, completion meaning, authority scope, retry/fallback consequences, or successor branch.

```text
mechanically runnable != semantically self-selecting
scheduler choice != semantic choice
```

No storage order, adapter registration order, provider count, capability count, or queue priority becomes a semantic tie-break.

---

## 9. Product boundary and HDE compatibility

M3 does not absorb product-owned trust, identity, memory, UI, account, or policy systems.

```text
IRR Host boundary != product trust core
IRR core != HDE core
```

One valid product flow is:

```text
product-owned explicit intent occurrence
+ product-owned target-safe material
        ↓
product-owned truthful semantic mapping
        ↓
IRR IntentRequest
+ typed ContextEnvelope
        ↓
IRR resolution
```

Host permission answers:

> may IRR receive this material?

IRR Context typing answers:

> what semantic role does this admitted material have?

Those remain separate.

A target-safe text view is not automatically a Claim, Evidence, Completeness, or Temporal Basis record merely because disclosure was authorized.

M3.0 gives product integrations enough normative guidance to construct the existing IRR input records without waiting for a new universal Host-input API.

---

## 10. M3.1 selected next slice

The next IRR implementation slice is:

# **M3.1 — Admitted History Repository / Replay Boundary**

It asks:

> What minimum repository boundary lets a Host retain and replay exact admitted IRR records without turning persistence order, mutable snapshots, or caches into canonical semantic state?

Likely acceptance shape:

```text
exact record identity + canonical bytes
→ admitted persistence
→ bounded exact-history retrieval
→ replay input
```

with fail-closed identity/content conflicts and no latest-write-wins semantics.

Exact repository class/protocol names are not frozen by M3.0.

M3.1 must not introduce a universal `HostRuntime`.

A product-owned input adapter may be implemented after M3.0 using the already-frozen `IntentRequest` and `ContextEnvelope`; it need not wait for M3.1 unless durable IRR history is required in the same product slice.

---

## 11. M3.0 non-goals

M3.0 adds no:

- production `HostRuntime`;
- mutable canonical session object;
- new Context record schema;
- generic text/blob Context record;
- public external-component Python ports;
- acquisition implementation;
- persistence implementation;
- scheduler;
- retry/fallback/recovery engine;
- execution capability;
- embedded Governance engine;
- HDE-specific dependency.

---

## 12. M3.0 acceptance

M3.0 freezes:

```text
Host mechanism != semantic authority
HostState != canonical semantic lifecycle history
Host possession != admitted Context
existing IntentRequest + ContextEnvelope remain the Host input boundary
ContextEnvelope remains typed semantic Context, not a text/blob transport
ContextReferenceRecord.description != hidden content transport
provider proposal != IRR admission
Governance remains external
Authorization != invocation
Attempt != Outcome
WorkerResult != parent completion
acquisition availability != retrieval authority
semantic replay != external re-execution
scheduler choice != semantic choice
restart != retry permission
IRR core != HDE integration
no public HostRuntime frozen
M3.1 = Admitted History Repository / Replay Boundary
```

The charter changes integration rules, not frozen M1/M2 runtime semantics.