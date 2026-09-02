# M3.0 — Host Integration Charter

Status: **proposed normative charter for M3**. It becomes the M3 baseline only when this PR merges.

M1 froze canonical attributable semantic records. M2 froze replayable orchestration over those records. M3 moves one layer outward: integrating real Host mechanisms without making integration machinery a new source of semantic truth or authority.

The central decision is:

```text
Host integration
=
explicit mechanism around frozen IRR records and orchestrators

Host integration
!= semantic authority
!= Governance authority
!= evidence truth
!= canonical lifecycle state
```

M3.0 adds no production Host runtime and no new canonical semantic record.

---

## 1. M3 purpose

M3 defines the boundary through which an embedding Host may connect:

- external intent occurrences;
- already-permitted bounded Context;
- Cognitive Providers;
- Governance;
- Executors;
- Workers;
- acquisition mechanisms;
- persistent admitted history;
- process restart and replay.

The Host may own those mechanisms. IRR still owns the semantics of its admitted records and derived frontiers.

```text
IRR core != HDE integration
M3 Host boundary != product-specific shell
Host can call mechanism X != IRR is authorized to use X
```

HDE may use this boundary later, but HDE is one Host integration rather than a privileged IRR mode.

---

## 2. Canonical state remains the admitted record graph

M3 does not reopen the central M2 decision.

```text
canonical semantic lifecycle history
=
exact admitted immutable IRR records

HostState != canonical semantic lifecycle history
```

A Host may retain caches, queues, indexes, connection pools, cursors, materialized frontiers, UI state, or session-shaped convenience objects. They are reconstructible mechanism state, not semantic truth.

A semantic claim that must survive restart must be recoverable from exact admitted records plus explicit versioned configuration where that configuration materially affects replay.

```text
cache loss != semantic history loss
storage insertion order != lifecycle order
latest row != active branch by default
```

M3.0 therefore does not freeze a public `HostRuntime`, mutable `ResolutionSession`, or universal Host-state object.

---

## 3. Host input construction uses existing IRR input records

A Host may receive an external occurrence and construct the already-frozen input boundary:

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

M3.0 does not introduce a generic `HostInput`, raw context blob, prompt bundle, or product-specific input record.

### IntentRequest

The Host constructs `IntentRequest` while preserving:

```text
Origin != Principal
origin attribution != identity verification
principal identity != permission
```

`OriginAttribution.source_event_ref` identifies the concrete occurrence that produced the intent expression. The Host must not relabel companion-, worker-, or system-originated text as human-originated merely because a human is the principal.

### ContextEnvelope

The Host constructs `ContextEnvelope` only from material already admitted for this Host-to-IRR disclosure boundary under the Host's own trust/access rules.

```text
Host possesses data != admitted IRR Context
local readability != Host-to-IRR disclosure admission
Context boundary attribution != permission proof
```

IRR validates the frozen Context schemas and cross-record links. M3 does not reinterpret `ContextEnvelope` construction as an IRR permission system for the Host's ambient data.

---

## 4. Host context mapping is semantic, not transport-shaped

`ContextEnvelope` remains typed semantic Context, not an arbitrary text container.

The existing record meanings remain:

- `ClaimRecord`: an attributable proposition presented for resolution;
- `EvidenceRecord`: attributable evidence with an exact target and scope;
- `TemporalBasisRecord`: an explicit attributable temporal basis;
- `CompletenessRecord`: an explicit attributable completeness assertion over a bounded domain;
- `ContextReferenceRecord`: identification of possible source/material whose content is **not** present.

A Host adapter must not choose a record type merely because it has a string field.

```text
raw Host text != ClaimRecord by default
raw Host text != EvidenceRecord by default
Host provenance != EvidenceRecord automatically
Host timestamp != TemporalBasisRecord automatically
Host bounded collection != CompletenessRecord automatically
ContextReferenceRecord.description != hidden content transport
```

In particular, M1.2 already freezes:

```text
Context Reference != content
```

A Host must not smuggle material text into `ContextReferenceRecord.description` to bypass that boundary.

A Host may construct a `ClaimRecord` when it can state a proposition without strengthening or changing the source semantics. For example, a product may represent an exact proposition about its own confirmed state rather than silently treating the underlying text as a factual world claim.

If no existing Context record kind truthfully represents the material:

```text
no honest Context mapping
→ omit the material from this ContextEnvelope
   or expose an explicit future vocabulary need
→ do not invent semantics to make transport convenient
```

M3.0 does not extend the frozen M1 Context wire vocabulary.

---

## 5. Provider integration boundary

A Cognitive Provider is a replaceable proposal mechanism.

The Host may:

1. build an explicitly permitted provider disclosure projection;
2. invoke the configured provider transport;
3. receive attributable `CandidateResolution` proposal material;
4. pass that exact material to the existing IRR admission boundary.

Frozen:

```text
provider receives only explicitly projected material
provider proposal != IRR admission
provider output != Context by default
provider output != Observation by default
provider output != Authorization
provider output != final IRR state
```

Provider invocation must not hide retrieval. If the provider or provider-side agent acquires new external information, that material must return through an explicit attributable Host/acquisition boundary before it can become admitted semantic input.

Remote provider transport may itself create a network/disclosure effect. Local placement does not grant blanket access to Host data.

M3.0 does not freeze a public `CognitiveProviderPort` Python protocol.

---

## 6. Governance integration boundary

Governance remains external to IRR.

A Host mechanism may transport an exact `WorkProposal` to Governance and receive an attributable `GovernanceDecision`. The existing IRR boundary then determines whether exact Authorization material may be admitted.

```text
Host boolean != GovernanceDecision
provider confidence != GovernanceDecision
GovernanceDecision != Effect
GovernanceDecision(AUTHORIZE) != admitted Authorization history
```

A Host cannot replace Governance with `approved=True`, executor self-approval, or inferred user intent.

M3.0 does not freeze a public `GovernancePort` Python protocol.

---

## 7. Executor integration boundary

Executor integration is effect-adjacent and therefore stricter.

The Host may hand already-selected, sufficiently-authorized exact invocation material to an Executor mechanism. Executor availability or installation is not semantic selection or authority.

```text
WorkStep != invocation
Capability Match != invocation
Authorization != invocation
Executor != resolver
Executor != Governance
Executor failure != fallback authority
```

`CapabilityAttempt` and `CapabilityOutcome` remain separate attributable semantic records.

The exact crash/commit protocol around effectful invocation is deferred to the Executor integration slice. Until then M3 freezes only:

```text
Host crash after send != no external effect
missing Outcome != failed
restart != automatic retry
retry != same Attempt
```

M3.0 does not freeze a public `ExecutorPort` Python protocol.

---

## 8. Worker integration boundary

A Worker receives exact bounded delegation material through the existing delegation boundary.

```text
Worker receives DelegatedWork, not ambient parent state
Worker capability ceiling != authority grant
WorkerNeed != scope/capability/authority widening
WorkerResult != parent completion
```

A Host may implement Worker transport/dispatch. It may not convert Worker availability into semantic delegation or allow Worker output to silently expand the parent lifecycle.

M3.0 does not freeze a public `WorkerPort` Python protocol.

---

## 9. Acquisition boundary

Acquisition mechanisms may read filesystem, browser, repository, network, account, device, or other external state only when the Host has an explicit admitted reason and applicable Host-side authority to perform that acquisition.

```text
HostAcquisitionPort installed != retrieval authority
mechanism can read X != X is IRR Context
acquired bytes != factual truth
acquisition result != Observation by default
```

Acquisition must preserve source and occurrence attribution. If acquired material is later used semantically, it must enter through an appropriate frozen IRR record boundary rather than being injected through hidden provider state or Host memory.

M3.0 does not freeze a universal acquisition protocol.

---

## 10. Record producers remain explicit

M3 separates who may mechanically construct a record from what that record means.

Conceptually:

| Boundary | Attributed producer / mechanism | Result remains subject to |
| --- | --- | --- |
| external intent occurrence | Host boundary | `IntentRequest` validation and Origin/Principal separation |
| Host Context admission | Host boundary | typed `ContextEnvelope` semantics |
| interpretation proposal | Cognitive Provider | IRR Candidate admission |
| Governance review | Governance | Authorization materialization boundary |
| capability invocation/result | Executor boundary | Attempt/Outcome semantics |
| delegated work result | Worker boundary | WorkerResult / Continuation semantics |
| external acquisition | Host acquisition mechanism | explicit later semantic admission |

Construction capability never implies authority to invent a different producer or semantic meaning.

```text
record constructor access != semantic authority
attribution != verification
```

---

## 11. Persistence and replay requirements

A real Host must retain enough exact admitted history to reconstruct M2 frontiers after process restart.

M3.0 freezes the semantic requirements, not a storage API:

- preserve canonical record bytes or an exactly equivalent lossless representation;
- preserve record identity and record type;
- retrieve bounded admitted history without using insertion order as semantic precedence;
- surface identity/content conflicts instead of resolving them by latest-write-wins;
- distinguish canonical admitted records from caches/materialized views;
- reconstruct derived frontiers from exact history and explicit orchestration configuration;
- never infer external effect certainty from local persistence state.

```text
record persistence != semantic mutation
cache != canonical history
record present != active lineage by default
restart replay != external re-execution
```

Replay has two different meanings that must not be collapsed:

```text
semantic replay = re-derive frontiers from admitted records
external re-execution = perform an effect again
```

The first may be deterministic. The second requires its own semantic and authority basis.

M3.0 does not freeze `HistoryRepository` as a public Python protocol yet.

---

## 12. Host configuration and replay claims

A replay claim may depend on explicit configuration when configuration affects semantic derivation, admission, or adapter interpretation.

Configuration that materially affects such behavior must be identifiable/versioned rather than read as hidden mutable process state.

Examples may include:

- IRR admission strategy identity/version;
- deterministic orchestration policy version;
- Host semantic mapping policy version;
- adapter contract/version when it changes how external results are interpreted.

Operational secrets, tokens, sockets, process handles, and connection pools are mechanism state and must not become semantic provenance merely because they are required to call a service.

```text
configuration identity != authority
secret availability != semantic permission
```

---

## 13. Automatic Host sequencing

The Host may automatically sequence only transitions whose choice is materially neutral under already-admitted semantics and applicable authority.

It must stop or expose the choice when different options can materially change:

- resource or target;
- recipient;
- disclosure;
- mutation/effect class;
- provider/service;
- capability semantics;
- cost or commitment;
- completion meaning;
- authority scope;
- retry/fallback consequences;
- active successor branch.

```text
mechanically runnable != semantically self-selecting
scheduler choice != semantic choice
```

No storage order, adapter registration order, provider count, capability count, or queue priority may become a hidden semantic tie-break.

---

## 14. Failure and competing-history behavior

The Host must fail closed when the admitted record set does not support one coherent active graph for the requested M2 frontier.

```text
valid records individually != one valid active lifecycle automatically
competing active lineage != latest-write-wins
competing active lineage != scheduler choice
```

The Host may quarantine, expose, or require explicit resolution of incompatible graph material. It must not silently delete history or choose a branch because it was inserted later.

Likewise:

```text
process crash != semantic failure
transport timeout != failed effect
unknown effectful outcome != retry permission
```

---

## 15. Product-specific responsibilities remain outside IRR core

M3 does not absorb product-owned trust, identity, UI, storage, or policy systems.

Examples of product-specific responsibilities include:

- HDE memory and Workstation state;
- HDE consent/access evaluation before Host-to-IRR disclosure;
- Companion presentation/personality;
- product UI and notifications;
- product-specific account/session management;
- product-specific semantic mapping from already-safe source records into truthful IRR Context records.

```text
IRR Host boundary != product trust core
IRR core != HDE core
```

A product adapter may depend on IRR. IRR core must not depend on the product.

---

## 16. HDE compatibility without HDE privilege

M3.0 is compatible with the HDE M31 integration sequence but does not encode HDE types.

One valid future Host flow is conceptually:

```text
product-owned explicit intent occurrence
+ product-owned target-safe selected material
        ↓
product-owned semantic mapping
        ↓
IRR IntentRequest
+ typed ContextEnvelope
        ↓
IRR resolution
```

The product mapping must obey Section 4. A target-safe text view is not automatically a `ClaimRecord`, `EvidenceRecord`, `CompletenessRecord`, or `TemporalBasisRecord` merely because the product has already authorized disclosure.

Host permission answers **may IRR receive this material?**
IRR Context typing answers **what semantic role does this admitted material have?**

Those questions remain separate.

M3.0 therefore gives product integrations enough normative guidance to construct the existing IRR input records without waiting for a new universal Host-input API.

---

## 17. M3.1 selected next slice

The next IRR implementation slice is:

# **M3.1 — Admitted History Repository / Replay Boundary**

M3.1 should answer the narrow mechanism question:

> What minimum repository boundary lets a Host retain and replay exact admitted IRR records without turning persistence order, mutable snapshots, or caches into canonical semantic state?

M3.1 should not introduce a universal `HostRuntime`.

The likely acceptance surface is:

```text
exact record identity + canonical bytes
→ admitted persistence
→ bounded exact-history retrieval
→ replay input
```

with fail-closed identity/content conflicts and no latest-write-wins semantics.

Exact repository class/protocol names are not frozen by M3.0.

A product-owned input adapter may be implemented after M3.0 using the already-frozen `IntentRequest` and `ContextEnvelope`; it does not need to wait for M3.1 unless that product specifically requires durable IRR history in the same slice.

---

## 18. M3.0 non-goals

M3.0 adds no:

- production `HostRuntime`;
- mutable canonical session object;
- new Context record schema;
- generic text/blob Context record;
- Provider/Governance/Executor/Worker public Python port;
- acquisition implementation;
- persistence implementation;
- scheduler;
- retry/fallback/recovery engine;
- execution capability;
- embedded Governance engine;
- HDE-specific dependency;
- Companion/Codexia/Organism-specific runtime path.

---

## 19. M3.0 acceptance

M3.0 is correct when the repository freezes all of the following:

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

The charter changes integration rules, not the frozen M1/M2 runtime semantics.