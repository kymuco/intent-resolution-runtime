# IRR Terminology

Status: **normative vocabulary for M0.1**.

This document defines the terms that later M0 contracts must use consistently. Exact data schemas are intentionally deferred.

## Normative words

`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` express contract strength in normative IRR documentation.

## Core terms

### Intent

A semantic expression of desired result, work, inquiry, or change. Intent alone grants no authority.

### IntentRequest

The attributable request presented to IRR for interpretation or resolution. The exact schema is deferred to M1.

### Principal

The entity whose goals or interests an IntentRequest purports to serve.

Principal identity does not prove authority, consent, or permission.

### Origin

The actor attributed as having produced the IntentRequest presented to IRR.

Conceptual origin classes are `human`, `companion`, `worker`, and `system`.

Origin is provenance metadata, not authority. The evidence supporting an Origin attribution is a separate trust concern and is frozen later by M0.2.

IRR MUST NOT silently strengthen an Origin attribution into verified identity, authority, permission, or approval.

### Host

The embedding system that invokes IRR and supplies bounded inputs such as context, capability catalogs, or continuation observations.

### Context

Caller-supplied material available to resolution through an explicit Host boundary.

Context does not grant authority merely by being present.

### Cognitive Provider

A component that proposes an interpretation or candidate resolution. Examples may include an LLM, deterministic resolver, Organism-derived provider, or hybrid provider.

A Cognitive Provider does not own final IRR state.

### CandidateResolution

Provider-produced candidate semantic material offered to IRR for validation and possible admission.

Admission means contract-valid, not factually true, safe, approved, or permitted.

### ResolvedIntent

A future IRR representation of admitted intent semantics after material ambiguity that blocks resolution has been addressed.

A ResolvedIntent may support planning, answer-only completion, no-operational-work completion, or a downstream proposal. It does not necessarily produce a WorkPlan.

A Clarification request is not itself a ResolvedIntent. If a later Observation introduces new Material Ambiguity, continuation returns to clarification or another explicit resolution path before a successor ResolvedIntent is admitted.

The exact schema and terminal states are not frozen in M0.1.

### Material Ambiguity

An ambiguity where competing interpretations could materially change a resource, recipient, scope, disclosure, mutation, executable target, cost, or external effect.

Material Ambiguity requires clarification or another explicit resolution path. It must not be hidden by late binding.

### Clarification

An explicit request for information needed to resolve Material Ambiguity or another unresolved semantic requirement.

### Assumption

An explicit non-hidden premise used during resolution. Later milestones define when assumptions are admissible.

### Observation

Attributable information returned from an external boundary or prior bounded step and supplied back to IRR for continuation.

Observation is data, not authority and not automatically truth beyond its stated provenance.

### Late Binding

Deferred resolution of a value when the semantic selection rule is already explicit and bounded and a future Observation supplies the value needed to apply that rule.

Late Binding is not permission to defer a discretionary semantic decision.

### Continuation

A successor resolution step that consumes attributable prior state plus new clarification, observation, or outcome while preserving parent intent lineage.

## Work terms

### WorkPlan

A future bounded semantic representation of operational work derived from a resolved intent when operational work is actually required.

Not every ResolvedIntent yields a WorkPlan.

A WorkPlan is not executable authority and is not a general-purpose script.

### WorkStep

A future bounded unit inside a WorkPlan. Exact structure is deferred.

### Capability

A named operation class that an external execution environment can potentially provide, such as `filesystem.search` or `archive.extract`.

A Capability describes what may be requested; it does not itself grant permission to perform it.

### Capability Catalog

The externally supplied set of Capability definitions available to a resolution.

A resolved plan must later bind to the exact catalog snapshot used to interpret those capabilities.

### Capability Drift

A change in Capability Catalog identity or semantics after a resolution was produced.

Capability Drift must not silently reinterpret an existing WorkPlan.

### Handoff

A future attributable transfer of bounded proposed work from IRR to another boundary, such as Governance, an Executor, or a Worker.

Exact handoff types are deferred.

## Authority and execution terms

### Governance

The external authority boundary that decides whether proposed work may proceed, must be constrained, requires review, or must be denied.

### Authorization

An external Governance outcome permitting some bounded work under stated conditions.

Authorization is not proof that an effect occurred.

### Permission

A generic authority concept. IRR does not grant Permission.

### Effect

A change or externally observable operation produced by an Executor or Worker outside the IRR core.

### Executor

A downstream component that performs bounded Capabilities under the applicable authority conditions.

IRR is not an Executor.

### Worker

A downstream component that performs delegated bounded work with its own subordinate lifecycle.

A Worker may return a result to IRR while IRR retains the parent intent lifecycle.

### Outcome

An attributable result reported by an Executor or Worker. Exact outcome states, including unknown outcome handling, are deferred to M0.9.

## Required distinctions

Later contracts MUST preserve these distinctions:

```text
origin != principal
origin != authority
origin attribution != origin verification
context != authority
intent != permission
clarification != resolved intent
resolution != approval
resolved intent != work plan requirement
candidate validity != factual truth
candidate validity != safety
candidate validity != permission
authorization != effect evidence
```

## External-neighbor names

`HDE`, `Character_OS`, `Organism`, `Codexia`, and `Runplane` are examples of possible external integrations. Their names in documentation do not create package, runtime, or architectural dependencies from the IRR core.
