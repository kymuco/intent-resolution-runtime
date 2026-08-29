# M0 Closure — Runtime Charter & Boundary Freeze

Status: **normative M0 closure record for M0.10**.

This document records the closure proof for M0 after M0.1–M0.9 have frozen IRR's semantic boundaries and M0.10 has exercised them through reference architecture fixtures.

M0 closes the product/boundary question:

> What is Intent Resolution Runtime, what may it know and decide, what may it produce, where do capability, authority, cognition, Worker delegation, execution, and recovery responsibilities live, and which distinctions must survive into implementation?

After M0, those questions are treated as frozen architecture unless a later explicit architectural revision changes them. M1 begins from these semantics rather than reopening them implicitly through Python types.

---

# 1. Closure conditions

M0 is semantically complete when all of the following hold:

1. product scope/non-goals are explicit;
2. Context/trust semantics are bounded and attributable;
3. semantic work remains bounded and platform-neutral;
4. Late Binding cannot hide future semantic discretion;
5. capabilities are externally supplied and cannot be invented;
6. Governance/Authorization remains external to IRR;
7. Cognitive Providers propose but do not own admitted IRR state;
8. Workers own only bounded subordinate lifecycles;
9. failure/retry/unknown-outcome semantics preserve effect uncertainty/history;
10. canonical scenarios compose without violating those contracts;
11. IRR core remains independent of Character_OS, organism_lab, HDE, Codexia, Runplane, and a specific model/provider.

M0.1–M0.9 establish items 1–9 and 11. M0.10 reference fixtures establish item 10.

The final repository/process closure still depends on the exact reviewed M0.10 candidate being merged with correct provenance.

---

# 2. Roadmap Definition of Done — sixteen answers

The preserved roadmap requires sixteen questions to have unambiguous answers.

## 2.1 What does IRR receive?

IRR receives explicit attributable material through bounded external interfaces rather than ambient discovery.

Conceptually this may include:

```text
IntentRequest
Context
Temporal Basis when material
Capability Catalog Snapshot
CandidateResolution
Governance material
Observation / returned data under explicit role
WorkerResult
Outcome / recovery evidence
Continuation inputs
```

Their presence does not collapse their meanings.

```text
Context != authority
Observation != truth by default
Catalog != permission
CandidateResolution != admitted state
Authorization != Outcome
WorkerResult != parent completion
```

Owners: M0.1, M0.2, M0.4–M0.9.

## 2.2 Who is Origin and who is Principal?

`Origin` is the actor attributed as producing an IntentRequest. `Principal` is the entity whose goals/interests the request purports to serve.

```text
origin != principal
origin != authority
principal != permission
```

A companion initiative may be:

```text
Origin = companion
Principal = user
```

without being relabeled human.

Owner: M0.1. Fixture: E.

## 2.3 What Context is allowed?

IRR has no ambient semantic Context. Context is caller/Host supplied, explicit, bounded, and attributable.

```text
need for information != authority to acquire it
Context Reference != retrieval authority
Context availability != Provider Disclosure authority
Context availability != Worker Disclosure authority
```

Owners: M0.2, extended by M0.7/M0.8.

## 2.4 When must IRR clarify?

When unresolved Material Ambiguity or material Conflict could change a material choice and no already-admitted bounded rule resolves it.

Material dimensions include resource, recipient, scope, disclosure, mutation, executable target, external commitment/cost, external effect, and authority-relevant identity/trust interpretation.

Provider confidence, Worker judgment, Governance approval, ambient ordering, and convenience cannot substitute for clarification.

Owners: M0.2/M0.4/M0.6/M0.7. Fixtures: D/H.

## 2.5 What is ResolvedIntent?

`ResolvedIntent` is admitted intent semantics after blocking material ambiguity/conflict for the next bounded path has been addressed.

It may support non-operational completion, ordinary bounded operational work, explicit Worker delegation semantics, or later Continuation.

```text
ResolvedIntent != WorkPlan requirement
ResolvedIntent != Authorization
Clarification != ResolvedIntent
```

Owners: M0.2/M0.3/M0.8.

## 2.6 How does intent become semantic work?

M0.3 freezes ordinary bounded operational work as semantic `WorkPlan` / `WorkStep` semantics rather than commands or arbitrary scripting.

M0.8 adds a distinct `DelegatedWork` semantic boundary for long-form Worker-owned subordinate lifecycles.

```text
semantic operation != implementation command
WorkPlan != scripting language
DelegatedWork != ordinary WorkStep
```

M0 deliberately does **not** freeze the exact M1 structural relation between `ResolvedIntent`, `WorkPlan`, and `DelegatedWork`. A future representation may reference DelegatedWork from a WorkPlan or represent a delegation path alongside ordinary work, provided it preserves M0.3/M0.8 and does not hide Worker autonomy inside an opaque ordinary WorkStep.

```text
exact WorkPlan <-> DelegatedWork schema relation = deferred
Worker lifecycle hidden in WorkStep = forbidden
```

Owners: M0.3/M0.8. Fixtures: A/B/C/F/G.

## 2.7 How is an unknown future result represented?

For a future value whose semantic rule is already fixed:

```text
Symbolic Reference
    + Binding Rule / Selection Policy
    + attributable Binding Input
    -> Bound Value
```

Returned/lifecycle material may later occupy distinct roles such as:

```text
Binding Input
Observation
WorkerResult
Attempt
Outcome
```

These roles are not interchangeable by default. Exact schemas remain M1+ work.

Owners: M0.4/M0.8/M0.9. Fixtures: A/B/H.

## 2.8 Where do capabilities come from?

Only from an explicit attributable Capability Catalog Snapshot supplied by an external Host/execution boundary.

```text
capability catalog != ambient capability discovery
same textual label != Capability Match
```

Effect-free Binding/Selection semantics do not automatically become external capabilities merely because they choose a value.

Owner: M0.5, with M0.4 distinction. Fixtures: A/B/F.

## 2.9 What happens when a capability is missing?

IRR records `missing_capability` for the exact applicable planning surface and fails closed for that required executable operation.

```text
missing_capability != Denial
missing_capability != global impossibility
missing_capability != fallback authority
```

It does not invent shell/browser/plugin/Worker/other-service fallback.

Owner: M0.5, reinforced by M0.8/M0.9. Fixture: F.

## 2.10 Where does IRR end and Governance begin?

This question is an **ownership boundary**, not a statement that the entire IRR lifecycle permanently ends at one point.

IRR owns semantic resolution/work representation. Governance owns authority decisions over applicable bounded work.

Conceptually:

```text
IRR semantic work / WorkProposal / DelegatedWork
        |
        v
external Governance authority decision
```

IRR may later consume Governance material through Continuation/coordination, but receiving a decision does not make IRR the authority source.

```text
intent != authorization
WorkPlan != authorization
WorkProposal != authorization
DelegatedWork != authorization
Governance Decision remains externally attributable
```

Owner: M0.6.

## 2.11 Where does Governance end and execution begin?

M0 does not freeze one universal sequence in which every provider invocation, Worker handoff, or non-effectful analysis must first pass through Governance.

The stronger frozen invariant is:

> Before any operation performs an effect/disclosure/mutation/invocation that requires authority, applicable external Authorization coverage must exist for that authority-requiring semantics.

Downstream work may then occur through the appropriate Executor/Capability or Worker boundary.

```text
Handoff != Authorization
Authorization != Effect
Effect != proof of Authorization
```

A Worker handoff itself does not manufacture authority, and a Worker may not exceed applicable authority merely because it already received DelegatedWork.

Owners: M0.6/M0.8.

## 2.12 How does Worker delegation differ from capability execution?

Capability/Executor work is a bounded operational invocation. Worker delegation hands explicit bounded `DelegatedWork` to a Worker that may own an internal subordinate lifecycle.

```text
CapabilityHandoff != DelegatedWorkHandoff
Worker != Executor by default
worker subplan != parent WorkPlan
WorkerResult != parent intent completion
```

IRR retains parent intent/continuation ownership.

Owner: M0.8. Fixture: C.

## 2.13 Where does the LLM connect?

An LLM may implement a replaceable Cognitive Provider.

```text
Provider Input Envelope
    -> LLM/provider
    -> CandidateResolution
    -> Candidate Admission
```

The provider does not own truth, final IRR state, capability admission, authority, or effects.

Owner: M0.7.

## 2.14 Where does Organism connect later?

Organism-derived cognition can implement the same provider seam when used for intent interpretation/resolution proposals.

```text
Organism internal cognition
    -> provider adapter
    -> CandidateResolution
    -> Candidate Admission
```

```text
Organism integration != organism_lab dependency in IRR core
```

Owner: M0.7.

## 2.15 What happens at unknown outcome?

`unknown_outcome` means material evidence is insufficient to establish whether the bounded effect/completion occurred.

```text
unknown_outcome != failed
failed != no effect
lost acknowledgement != proof of no effect
```

Lifecycle interruption and effect certainty remain separate semantic questions; M0 does not require one flat enum.

An effectful unknown outcome never implies automatic Retry. Any actual Retry is a new attributable Attempt and requires a valid safe-replay basis plus applicable capability/authority conditions.

Owner: M0.9. Fixture: B.

## 2.16 Why can IRR not perform actions itself?

IRR's product boundary is semantic resolution and bounded work/delegation representation, not effect execution.

This separation keeps:

- capability existence externally supplied;
- authority externally governed;
- effects attributable to downstream components;
- providers/Workers/Executors replaceable;
- core IRR platform-neutral and independently implementable.

```text
resolution != execution
Intent != Permission != Effect
```

Owner: M0.1, reinforced by M0.3/M0.5/M0.6.

---

# 3. Neighbor-independence proof

The roadmap requires these systems to remain replaceable external neighbors:

```text
Character_OS
Organism / organism_lab
HDE
Codexia
Runplane / execution runtime
```

## 3.1 Character_OS

A companion may be an Origin and communicate through the Host boundary. IRR does not depend on personality, memory, UI, or companion implementation details.

## 3.2 Organism / organism_lab

Organism-derived cognition may connect through a Cognitive Provider adapter. IRR consumes candidate semantics, not organism internal representation/runtime details.

## 3.3 HDE

HDE may embed IRR and supply Context, Catalogs, Governance material, providers, Workers, and downstream integrations. IRR core does not encode HDE-specific memory, UI, project, consent, or lifecycle APIs.

## 3.4 Codexia

Codexia may implement a Worker adapter. IRR depends on the DelegatedWork/WorkerResult semantic boundary, not Codexia internals.

## 3.5 Runplane / execution runtime

Runplane or another runtime may supply Capability/Executor behavior and effect evidence. IRR plans against explicit capability semantics rather than importing one execution implementation as semantic truth.

## 3.6 Replacement test

The architecture remains coherent under substitutions such as:

```text
Character_OS -> another companion / no companion
LLM A -> LLM B -> deterministic resolver -> Organism resolver
Codexia -> another Worker
Runplane -> another governed executor runtime
HDE -> another Host embedding
```

Material provider/Worker/executor substitutions may still require revalidation/authority review when identity changes semantics, but the IRR core contract itself does not need redesign.

---

# 4. Reference-fixture closure

Canonical M0.10 fixtures:

```text
A  Restore latest organism_lab backup
B  Send latest Voice Engine report via Telegram + unknown outcome branch
C  Delegate CG2.42 analysis to Codexia
D  Ambiguous referent: "Launch it"
E  Companion initiative
F  Missing Signal capability
G  No operational intent
H  Returned search data / Binding tie requires Continuation
```

The historical roadmap name for H is “Observation changes plan”; the normative fixture preserves the later M0.4 distinction that returned search data / Binding Input is not Observation by default.

Together the fixtures exercise:

```text
Origin / Principal
explicit Context
Material Ambiguity
non-operational resolution
bounded ordinary work
Late Binding / Selection
Capability Catalog / missing capability
Governance / Authorization
external disclosure
Cognitive Provider admission
Worker delegation
forbidden-effect scope
WorkerResult continuation
Attempt / Outcome / interruption / unknown outcome
Retry / fallback
```

No fixture requires IRR to violate its non-goals.

---

# 5. What M0 freezes

```text
Intent != Permission != Effect
Origin != Principal != authority
Context is explicit, bounded, attributable
Material Ambiguity cannot be guessed away
ResolvedIntent does not imply WorkPlan
ordinary semantic work is bounded and non-command-oriented
WorkPlan is not arbitrary scripting
Worker autonomy is explicit DelegatedWork, not hidden WorkStep behavior
Late Binding defers values, not semantic decisions
Binding/Selection != external Capability by default
Capability Catalog is externally supplied
missing capability fails closed for that planning surface
Capability Match != Availability != Authorization
Governance is external authority ownership
Authorization remains separate from work/delegation semantics
Authorization cannot rewrite semantic forbidden-effect bounds
Cognitive Provider proposes; IRR admits
provider prior/confidence != admitted Evidence/authority
WorkerResult != parent completion
failed != no effect
unknown_outcome != failed
interrupted != unknown_outcome by definition
Retry is a new Attempt
unknown effectful outcome != automatic Retry
fallback preserves prior effect uncertainty and cannot silently widen semantics/capability/authority
```

These are semantic constraints M1 must encode faithfully.

---

# 6. What M0 deliberately does not freeze

M0 is not a finished runtime design.

Deferred to M1+:

- exact Python classes/protocols/enums/module layout;
- exact WorkPlan ↔ DelegatedWork structural relation;
- immutable record schemas;
- canonical serialization;
- stable IDs/digests;
- exact Candidate Admission result types;
- exact Binding representation;
- exact CapabilityDescriptor/Catalog schema;
- exact Governance/Authorization wire schema;
- exact Provider/Worker/Executor transport;
- exact lifecycle/interruption/effect-certainty state layout;
- persistence/event sourcing;
- retry/backoff/scheduler algorithms;
- concrete idempotency protocols;
- concrete Governance implementation;
- filesystem/process/network adapters;
- Codexia integration;
- organism_lab integration;
- HDE integration;
- Runplane/execution integration.

---

# 7. M1 handoff

M1 should now primarily encode/validate frozen semantics:

```text
M0 semantics
    -> immutable Python contracts
    -> validation
    -> canonical serialization
    -> stable identity/digests
    -> lineage/equality rules
    -> executable architecture-fixture encoding
```

A proposed M1 representation is invalid if it cannot preserve a material M0 distinction required by the fixtures.

Examples:

```text
Origin and Principal collapse -> invalid
commands are the only WorkPlan representation -> invalid
Binding Input and Observation collapse universally -> invalid
Binding/Selection automatically requires external Capability -> invalid
missing_capability and Denial collapse -> invalid
CandidateResolution and ResolvedIntent collapse -> invalid
Worker lifecycle hidden in ordinary WorkStep -> invalid
Authorization can erase DelegatedWork forbidden effects -> invalid
WorkerResult and parent completion collapse -> invalid
failed and unknown_outcome collapse -> invalid
interrupted forced to equal unknown_outcome -> invalid
Retry lacks separate Attempt lineage -> invalid
```

Exact type count is not frozen. Semantic fidelity is.

---

# 8. Process acceptance criteria

After the M0.10 PR is reviewed and merged, M0 may be marked complete if:

```text
[ ] M0.1–M0.9 normative contracts remain in main
[ ] reference_scenarios.md is merged
[ ] m0_closure.md is merged
[ ] README points to both documents and identifies M0.10
[ ] no runtime src/ implementation was introduced by M0.10
[ ] final first-party review finds no blocking cross-contract contradiction
[ ] exact merge provenance is verified
```

The pull-request/merge record establishes whether these process criteria were satisfied; the checkboxes are not mutable runtime state.

---

# 9. Closure verdict

At the semantic level, M0.1–M0.10 define a coherent IRR boundary:

```text
attributable intent
    -> explicit bounded context
    -> interpretation / clarification
    -> admitted intent semantics
    -> optional ordinary work and/or explicit Worker delegation semantics
    -> external capability + authority boundaries
    -> downstream Executor / Worker lifecycle
    -> attributable returned material / effect / outcome
    -> explicit Continuation when semantics materially change
```

At no point does IRR gain implicit permission to turn intent into effect.

```text
Intent != Permission != Effect
```

M0.10 introduces no new core runtime vocabulary beyond the M0.1–M0.9 semantic set; it proves that the frozen set composes across realistic scenarios and records the transition into M1.

Once the exact M0.10 candidate passes final review and is merged, **M0 — Runtime Charter & Boundary Freeze is complete** and implementation may proceed to M1 Intent IR without reopening the product boundary by default.
