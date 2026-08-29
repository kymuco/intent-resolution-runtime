# M0 Closure — Runtime Charter & Boundary Freeze

Status: **normative M0 closure record for M0.10**.

This document records the closure proof for M0 after M0.1–M0.9 have frozen the IRR semantic boundaries and M0.10 has exercised them through reference architecture fixtures.

M0 closes the question:

> What is Intent Resolution Runtime, what may it know and decide, what may it produce, where do capability, authority, cognition, Worker delegation, execution, and recovery begin and end, and which semantic distinctions must survive into implementation?

After M0, those product/boundary questions are treated as frozen architecture unless a later explicit architectural revision changes them.

M1 begins from these semantics rather than reopening them implicitly through Python types.

---

## 1. M0 closure statement

M0 is complete when all of the following are true:

1. the product boundary is explicit;
2. trust/context semantics are attributable and fail closed;
3. intent-to-work semantics are bounded and platform-neutral;
4. Late Binding cannot hide future semantic discretion;
5. capabilities are externally supplied and cannot be invented;
6. Governance/Authorization remains external to IRR;
7. Cognitive Providers propose but do not own admitted IRR state;
8. Workers receive bounded DelegatedWork and do not own the parent intent;
9. failure/retry/unknown-outcome semantics preserve effect uncertainty and history;
10. the architecture explains the canonical reference scenarios without violating those boundaries;
11. core IRR remains independently implementable without HDE, Character_OS, organism_lab, Codexia, Runplane, or a specific LLM/provider.

The M0.10 reference fixtures satisfy item 10. The M0.1–M0.9 normative documents satisfy items 1–9 and 11.

Therefore the M0 architecture is closed for transition into M1, subject to the exact merge/review state of the M0.10 pull request.

---

# 2. Definition-of-Done questions

The preserved roadmap defines sixteen questions that M0 must answer unambiguously. This section records the answers and the owning contract.

## 2.1 What does IRR receive?

IRR receives explicit attributable inputs through bounded external interfaces rather than ambiently discovering semantic state.

Conceptually these inputs may include:

```text
IntentRequest
explicit Context
Temporal Basis when material
Capability Catalog Snapshot
Governance material
Continuation inputs
selected Provider material
WorkerResult / downstream results
```

Their presence does not collapse their semantic roles.

```text
Context != authority
Observation != truth by default
Catalog != permission
Authorization != Outcome
WorkerResult != Context by default
```

Owners: M0.1, M0.2, M0.4–M0.9.

## 2.2 Who is Origin and who is Principal?

`Origin` is the actor attributed as producing an IntentRequest.

`Principal` is the entity whose goals/interests the request purports to serve.

They are distinct.

```text
origin != principal
origin != authority
principal != permission
```

A companion-originated initiative serving the user remains:

```text
Origin = companion
Principal = user
```

Owner: M0.1. Exercised by Reference Scenario E.

## 2.3 What Context is allowed?

IRR has no ambient semantic Context.

Context must be explicitly supplied through a bounded Host boundary and remain attributable.

```text
need for information != authority to acquire it
Context Reference != retrieval authority
Context availability != Provider Disclosure authority
Context availability != Worker Disclosure authority
```

Owner: M0.2, extended by M0.7/M0.8. Exercised by Scenarios A, B, C, D, E, G.

## 2.4 When must IRR ask for clarification?

Clarification is required when unresolved Material Ambiguity or material Conflict would change a material semantic choice and no already-admitted bounded rule resolves it.

Material dimensions include conceptually:

```text
resource
recipient
scope
disclosure
mutation
executable target
cost / external commitment
external effect
authority-relevant identity/trust choice
```

Provider confidence, Worker judgment, Governance approval, ambient ordering, or convenience cannot replace clarification.

Owner: M0.2, reinforced by M0.4/M0.6/M0.7. Exercised by Scenarios D and H.

## 2.5 What is a ResolvedIntent?

A `ResolvedIntent` is admitted intent semantics after material ambiguity/conflict blocking the next bounded path has been addressed.

It may lead to:

```text
non-operational resolution
WorkPlan
DelegatedWork / downstream proposal path
later continuation
```

It is not automatically a WorkPlan or Authorization.

```text
ResolvedIntent != WorkPlan requirement
ResolvedIntent != Authorization
Clarification != ResolvedIntent
```

Owners: M0.2/M0.3.

## 2.6 How does intent become semantic work?

When operational work is actually required, IRR produces a bounded semantic `WorkPlan` rather than executable implementation commands.

```text
IntentRequest
    -> ResolvedIntent
    -> WorkPlan
    -> bounded WorkStep[]
```

Long-form subordinate autonomy is represented separately as `DelegatedWork` rather than hidden inside an ordinary WorkStep.

```text
semantic operation != implementation command
WorkPlan != scripting language
DelegatedWork != ordinary WorkStep
```

Owners: M0.3/M0.8. Exercised by Scenarios A, B, C, F, G.

## 2.7 How is an unknown future result represented?

M0 freezes the semantic need for symbolic future values and attributable downstream results without freezing exact M1 schemas.

For future values inside already-fixed semantics:

```text
Symbolic Reference
    + Binding Rule
    + attributable Binding Input
    -> Bound Value
```

For downstream lifecycle results:

```text
Attempt / Outcome / WorkerResult / Observation
```

remain distinct semantic roles.

Owner: M0.4/M0.8/M0.9. Exercised by Scenarios A, B, H.

## 2.8 Where do capabilities come from?

Capabilities come only from an explicit attributable Capability Catalog Snapshot supplied by an external Host/execution boundary.

IRR does not discover its own execution powers.

```text
capability catalog != ambient capability discovery
same textual label != Capability Match
```

Owner: M0.5.

## 2.9 What happens when a capability is missing?

IRR records the conceptual `missing_capability` condition for the exact applicable Catalog Snapshot and fails closed for planning that required executable operation.

It does not silently fall back to shell/browser/plugins/Workers/another service.

```text
missing_capability != Denial
missing_capability != global impossibility
missing_capability != fallback authority
```

Owner: M0.5, reinforced by M0.8/M0.9. Exercised by Scenario F.

## 2.10 Where does IRR end and Governance begin?

IRR ends at attributable bounded work/proposal semantics.

Governance owns authority decisions.

```text
IRR
    -> WorkProposal / bounded delegated semantics
Governance
    -> Authorization / Denial / Constraint / require_review
```

IRR does not mint fields whose semantics mean permission.

```text
intent != authorization
WorkPlan != authorization
WorkProposal != authorization
DelegatedWork != authorization
```

Owner: M0.6.

## 2.11 Where does Governance end and execution begin?

Governance establishes applicable authority; downstream handoff/execution performs bounded operational effects under the appropriate capability/executor or Worker boundary.

```text
Authorization != Effect
Handoff != Authorization
Effect != proof of Authorization
```

Exact transport and executor APIs remain deferred.

Owners: M0.6, M0.8, M0.9.

## 2.12 How does Worker delegation differ from capability execution?

A Capability/Executor path performs bounded operational work.

A Worker receives explicit `DelegatedWork` and may own a bounded subordinate lifecycle involving internal planning/analysis/iteration.

```text
CapabilityHandoff != DelegatedWorkHandoff
Worker != Executor by default
worker subplan != parent WorkPlan
WorkerResult != parent intent completion
```

IRR retains parent intent ownership.

Owner: M0.8. Exercised by Scenario C.

## 2.13 Where does the LLM connect?

An LLM may implement a replaceable `Cognitive Provider` behind the M0.7 provider seam.

It receives an explicitly permitted `Provider Input Envelope` and returns attributable `CandidateResolution` material.

```text
LLM/provider proposes
    -> CandidateResolution
    -> IRR Candidate Admission
```

The model does not own final IRR state, truth, capability admission, authority, or effects.

Owner: M0.7.

## 2.14 Where does Organism connect later?

Organism-derived cognition connects through the same stable Cognitive Provider semantic seam when used for intent interpretation/resolution proposals.

```text
Organism internal cognition
    -> OrganismResolver/provider adapter
    -> CandidateResolution
    -> Candidate Admission
```

IRR core does not depend on organism_lab internal representations.

```text
Organism integration != organism_lab dependency in IRR core
```

Owner: M0.7.

## 2.15 What happens at unknown outcome?

`unknown_outcome` means material evidence is insufficient to establish whether the bounded effect/completion occurred.

It is not failure.

```text
unknown_outcome != failed
lost acknowledgement != proof of no effect
```

An effectful unknown outcome never implies automatic Retry.

Any Retry is a new attributable Attempt and requires a valid safe-replay basis plus applicable capability/authority conditions.

Owner: M0.9. Exercised by Scenario B.

## 2.16 Why can IRR not perform actions itself?

Because IRR's product boundary is semantic resolution and bounded work representation, not effect execution.

Execution is intentionally downstream so that:

- capability existence is externally supplied;
- authority is externally governed;
- implementation effects remain attributable;
- Workers/Executors are replaceable;
- IRR can remain platform-neutral and independently implementable.

```text
resolution != execution
intent != permission != effect
```

Owner: M0.1, reinforced by M0.3/M0.5/M0.6.

---

# 3. Neighbor-independence proof

The roadmap requires these systems to remain replaceable external neighbors rather than dependencies of IRR core:

```text
Character_OS
Organism / organism_lab
HDE
Codexia
Runplane / execution runtime
```

M0 satisfies that requirement as follows.

## 3.1 Character_OS / companion

A companion may be an Origin and may supply requests through an external Host boundary.

IRR does not depend on companion personality, memory format, UI, or identity implementation.

```text
companion Origin != Character_OS dependency
```

## 3.2 Organism / organism_lab

Organism-derived cognition may later implement a Cognitive Provider adapter.

IRR consumes candidate semantics, not organism internal state machinery.

```text
OrganismResolver replaceable
organism_lab internals outside IRR core
```

## 3.3 HDE

HDE may be a Host/embedding environment that supplies Context, Capability Catalogs, Governance material, providers, Workers, and downstream integration.

IRR does not encode HDE-specific memory, UI, project, permission, or lifecycle APIs in its core semantic contracts.

```text
HDE may host IRR
IRR != HDE subsystem by definition
```

## 3.4 Codexia

Codexia may implement a Worker adapter for bounded delegated research/coding work.

IRR depends only on the stable DelegatedWork/WorkerResult semantic seam, not Codexia internals.

```text
Codexia != IRR dependency
Codexia adapter -> Worker boundary
```

## 3.5 Runplane / execution runtime

Runplane or another execution runtime may provide capabilities/executors and effect evidence.

IRR plans against externally supplied capability semantics and hands bounded work downstream; it does not import one execution runtime as its semantic truth.

```text
Executor implementation != IRR semantic contract
```

## 3.6 Replacement test

The core architecture still makes sense if any one of the following substitutions occurs:

```text
Character_OS -> another companion / no companion
LLM A -> LLM B -> deterministic resolver -> Organism resolver
Codexia -> another Worker / no Worker for ordinary work
Runplane -> another governed executor runtime
HDE -> another Host embedding
```

Material boundary semantics may require revalidation when provider/Worker/executor identity matters, but the IRR core model itself does not need redesign.

That is the required independence property.

---

# 4. M0 reference-fixture closure

The canonical eight scenarios are frozen in [`reference_scenarios.md`](reference_scenarios.md):

```text
A  Restore latest organism_lab backup
B  Send latest Voice Engine report through Telegram
C  Delegate CG2.42 analysis to Codexia
D  Ambiguous referent: "Launch it"
E  Companion initiative
F  Missing Signal capability
G  No operational intent
H  Observation / binding tie changes the path
```

Together they exercise:

```text
human and companion Origin
Principal distinction
explicit Context
Material Ambiguity
non-operational resolution
bounded WorkPlan
Late Binding
Selection Policy
Capability Catalog / missing capability
Governance / Authorization
external disclosure
Cognitive Provider admission
Worker delegation
WorkerResult continuation
Attempt / Outcome
unknown outcome / retry / fallback
```

No scenario requires IRR to violate its non-goals in order to produce a coherent architecture path.

---

# 5. What M0 freezes

The following semantic decisions are now architectural contracts for implementation:

```text
Intent != Permission != Effect
Origin != Principal != authority
Context is explicit, bounded, attributable
Material Ambiguity cannot be guessed away
ResolvedIntent does not imply WorkPlan
WorkPlan is semantic and bounded, not executable code
ordinary WorkStep cannot hide open-ended autonomy
Late Binding defers values, not semantic choices
Capability Catalog is externally supplied
missing capability fails closed for that planning surface
Capability Match != Availability != Authorization
Governance is external to IRR
Authorization remains separate from work representation
Cognitive Provider proposes; IRR admits
provider prior/confidence != admitted Evidence/authority
Worker delegation is distinct from ordinary capability execution
Worker autonomy is bounded by DelegatedWork
WorkerResult != parent completion
Outcome scope does not silently widen
failed != no effect
unknown_outcome != failed
Retry is a new Attempt
unknown effectful outcome != automatic Retry
fallback cannot silently change material semantics/capability/authority
```

These are the semantic foundations M1 must encode.

---

# 6. What M0 deliberately does not freeze

M0 closure must not be misread as a finished runtime design.

The following remain implementation work for M1 and later milestones:

- exact Python classes, protocols, enums, generics, and module layout;
- immutable record schemas;
- canonical serialization format;
- stable IDs and digest algorithms;
- exact normalization APIs;
- exact Candidate Admission result types;
- exact WorkPlan/WorkStep/Binding representations;
- exact CapabilityDescriptor/Catalog schemas;
- exact Governance/Authorization wire schemas;
- exact Provider/Worker/Executor transport APIs;
- persistence/event sourcing;
- concrete retry/backoff/scheduler algorithms;
- concrete idempotency-key protocols;
- concrete policy/Governance implementations;
- real filesystem/process/network adapters;
- Codexia integration;
- organism_lab integration;
- HDE integration;
- Runplane/execution integration.

M0 freezes semantic constraints on those later implementations, not their code shape.

---

# 7. M1 handoff

M1 should now be primarily a representation/validation milestone rather than another product-definition milestone.

Conceptually:

```text
M0 frozen semantics
      |
      v
M1 immutable Python contracts
      |
      +--> validation
      +--> canonical serialization
      +--> stable identity / digests
      +--> deterministic equality / lineage rules
      +--> architecture-fixture encoding
```

M1 should use the M0.10 reference scenarios as architecture constraints while defining the first executable Intent IR.

A proposed M1 representation is invalid if it cannot faithfully distinguish material M0 concepts that the scenarios require.

Examples:

```text
if one field collapses Origin and Principal -> invalid design
if WorkPlan can only store commands -> invalid design
if symbolic value and observed value are indistinguishable -> invalid design
if missing capability and Denial collapse -> invalid design
if CandidateResolution and ResolvedIntent collapse -> invalid design
if WorkerResult and parent completion collapse -> invalid design
if failed and unknown_outcome collapse -> invalid design
if Retry cannot preserve separate Attempt lineage -> invalid design
```

The exact class count is not frozen. Semantic fidelity is.

---

# 8. M0 closure acceptance criteria

After the M0.10 PR is reviewed and merged, M0 may be marked complete if:

```text
[ ] M0.1–M0.9 normative contracts remain in main
[ ] reference_scenarios.md is merged
[ ] this m0_closure.md is merged
[ ] README points to the reference/closure documents
[ ] no runtime src/ implementation was introduced by M0.10
[ ] final first-party review finds no blocking cross-contract contradiction
[ ] exact merge provenance is verified
```

The checkboxes are process criteria rather than mutable runtime state inside this document. The pull request/merge record establishes whether they were actually satisfied.

---

# 9. Closure verdict

At the semantic architecture level, M0.1–M0.10 define a coherent Intent Resolution Runtime boundary:

```text
attributable intent
    -> bounded explicit context
    -> interpretation / clarification
    -> admitted intent semantics
    -> optional bounded work / delegation
    -> external capability + authority boundaries
    -> downstream execution / Worker lifecycle
    -> attributable result / outcome
    -> explicit continuation when semantics change
```

At no point does IRR acquire implicit permission to turn intent into effect.

The defining invariant remains:

```text
Intent != Permission != Effect
```

M0.10 introduces no new core vocabulary beyond the M0.1–M0.9 semantic set; it proves that the frozen set composes across realistic scenarios and records the transition contract into M1.

Once this exact M0.10 candidate passes final review and is merged, **M0 — Runtime Charter & Boundary Freeze is complete** and implementation may proceed to M1 Intent IR without reopening the product boundary by default.
