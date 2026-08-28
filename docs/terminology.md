# IRR Terminology

Status: **normative vocabulary through M0.2**.

This document defines terms that later M0 contracts must use consistently. Exact data schemas are intentionally deferred.

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

Origin is provenance metadata, not authority. The evidence supporting an Origin attribution is governed by the M0.2 trust semantics.

IRR MUST NOT silently strengthen an Origin attribution into verified identity, authority, permission, or approval.

### Host

The embedding system that invokes IRR and supplies bounded inputs such as context, capability catalogs, or continuation observations.

### Cognitive Provider

A component that proposes an interpretation or candidate resolution. Examples may include an LLM, deterministic resolver, Organism-derived provider, or hybrid provider.

A Cognitive Provider does not own final IRR state.

### CandidateResolution

Provider-produced candidate semantic material offered to IRR for validation and possible admission.

Admission means contract-valid, not factually true, safe, approved, or permitted.

### ResolvedIntent

A future IRR representation of admitted intent semantics after Material Ambiguity that blocks the next bounded path has been addressed.

A ResolvedIntent may support planning, answer-only completion, no-operational-work completion, or a downstream proposal. It does not necessarily produce a WorkPlan.

A Clarification request is not itself a ResolvedIntent. If a later Observation introduces new Material Ambiguity, continuation returns to clarification or another explicit resolution path before a successor ResolvedIntent is admitted.

The exact schema and terminal states are not frozen in M0.2.

### Material Ambiguity

An ambiguity where competing interpretations could materially change a resource, recipient, scope, disclosure, mutation, executable target, cost or external commitment, external effect, or authority-relevant identity/trust interpretation.

Material Ambiguity blocks admission of a ResolvedIntent until resolved by clarification or an explicit bounded rule. It must not be hidden by Late Binding or an Assumption.

### Clarification

An explicit request for information needed to resolve Material Ambiguity or another unresolved semantic requirement.

### Assumption

An explicit premise used to continue resolution without claiming that the premise is established fact.

An Assumption is admissible only when getting it wrong cannot silently choose between materially different meanings. Material identity, recipient, disclosure, mutation, executable, authority, trust, cost, or external-effect choices MUST NOT be filled by Assumption.

### Information Need

A bounded description of information required to continue resolution.

An Information Need is not authority to acquire, observe, retrieve, or disclose that information. Exact schemas are deferred.

### Observation Need

An Information Need whose missing information would be supplied by a future attributable Observation.

An Observation Need is not execution authority.

### Observation

Attributable information returned from an external boundary or prior bounded step and supplied back to IRR for continuation.

Observation is data, not authority and not automatically truth beyond its stated provenance and evidence.

### Late Binding

Deferred resolution of a value when the semantic selection rule is already explicit and bounded and a future Observation supplies the value needed to apply that rule.

Late Binding is not permission to defer a discretionary semantic decision.

### Continuation

A successor resolution step that consumes attributable prior state plus new clarification, Observation, or Outcome while preserving parent intent lineage.

## Trust and knowledge terms

### Claim

Semantic content presented as describing some fact, state, identity, relation, preference, constraint, or other proposition relevant to resolution.

A Claim is not automatically factual truth.

### Attribution

The asserted source identity attached to an IntentRequest, Claim, Context Item, Observation, or other attributable material.

Attribution does not itself prove that the asserted source identity is verified.

### Evidence

Attributable material that supports or weakens a Claim or Attribution.

Evidence MUST be interpreted only within the scope it actually supports. Evidence does not grant authority.

### Evidentiary Status

The explicit characterization of what attributable Evidence establishes, if anything, about a Claim or Attribution.

M0.2 freezes the semantics but not a concrete enum, score, cryptographic mechanism, or trust algorithm.

### Origin Verification

Evidence-backed verification of an Origin attribution under a stated mechanism and scope.

Origin Verification does not grant permission and does not automatically establish truth of every Claim within the IntentRequest.

### Epistemic Trust

A bounded assessment of what available Evidence justifies believing about a Claim, Attribution, Observation, or source.

Epistemic Trust is separate from Governance authority.

### Trust Amplification

An invalid strengthening of evidentiary status beyond what the underlying Evidence supports, including silent propagation from one Claim, identity, source, or item to another.

IRR MUST NOT perform Trust Amplification.

### Conflict

A condition where attributable semantic inputs make materially incompatible Claims relevant to the same resolution.

A material Conflict must be preserved until an explicit bounded precedence rule, clarification, or further attributable information resolves it.

### Freshness

The temporal relevance of a Claim, Context Item, or Observation to the semantics being resolved.

Freshness MUST NOT be inferred when time materially changes meaning and the available material does not support that inference.

## Context terms

### Context

Caller-supplied material admitted to resolution through an explicit Host boundary.

Context does not grant authority merely by being present.

### Context Item

An attributable unit of Context whose semantic content and source distinctions can be preserved when material to trust, ambiguity, Conflict, or resolution.

Exact representation is deferred.

### Context Boundary

The explicit Host-controlled boundary defining what semantic material is available to IRR for a resolution or continuation.

IRR MUST NOT silently widen the Context Boundary.

### Ambient Context

Information IRR could potentially discover from a machine, repository, browser, memory store, account, network, device, or other environment but which has not been explicitly admitted through the Context Boundary.

IRR has no authority to acquire Ambient Context merely because it would help resolution.

### Context Reference

An explicit reference identifying possible Context material without necessarily providing the referenced content.

A Context Reference is not retrieval authority or disclosure authority.

### Provider Disclosure

The act of making Context or other semantic material available to a Cognitive Provider.

Context availability to IRR does not imply permission for Provider Disclosure. Exact disclosure policy and APIs are deferred.

## Work terms

### WorkPlan

A future bounded semantic representation of operational work derived from a ResolvedIntent when operational work is actually required.

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

A future attributable transfer of bounded proposed work from IRR to an external downstream boundary.

A receiving boundary may later represent governance review, capability execution, or delegated work, but the Handoff itself grants no authority and does not prove that required Governance conditions are satisfied.

Exact handoff types and routing are deferred.

## Authority and execution terms

### Governance

The external authority boundary that decides whether proposed work may proceed, must be constrained, requires review, or must be denied.

### Authorization

An external Governance decision permitting some bounded work under stated conditions.

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

An attributable result reported by an Executor or Worker. Exact outcome states, including unknown-outcome handling, are deferred to M0.9.

## Required distinctions

Later contracts MUST preserve these distinctions:

```text
origin != principal
origin != authority
origin attribution != origin verification
verified origin != permission
claim != factual truth
attribution != verification
evidence != authority
epistemic trust != authorization
context != authority
context availability != provider disclosure
context reference != retrieval authority
absence != negation
intent != permission
clarification != resolved intent
assumption != hidden default
assumption != established fact
information need != observation authority
resolution != approval
resolved intent != work plan requirement
handoff != authorization
candidate validity != factual truth
candidate validity != safety
candidate validity != permission
authorization != effect evidence
```

## External-neighbor names

`HDE`, `Character_OS`, `Organism`, `Codexia`, and `Runplane` are examples of possible external integrations. Their names in documentation do not create package, runtime, or architectural dependencies from the IRR core.
