# IRR Terminology

Status: **normative vocabulary through M0.3**.

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

Origin is provenance metadata, not authority. Evidence supporting an Origin attribution is governed by M0.2 trust semantics.

IRR MUST NOT silently strengthen an Origin attribution into verified identity, authority, permission, or approval.

### Host

The embedding system that invokes IRR and supplies bounded inputs such as context, capability catalogs, temporal basis, or continuation observations.

### Cognitive Provider

A component that proposes an interpretation or candidate resolution. Examples may include an LLM, deterministic resolver, Organism-derived provider, or hybrid provider.

A Cognitive Provider does not own final IRR state.

### CandidateResolution

Provider-produced candidate semantic material offered to IRR for validation and possible admission.

Admission means contract-valid, not factually true, safe, approved, or permitted.

### Resolution

The IRR process or bounded semantic result of interpreting an IntentRequest under admitted context, trust, ambiguity, and continuation constraints.

Resolution does not imply approval, authorization, WorkPlan creation, or effect.

### ResolvedIntent

A future IRR representation of admitted intent semantics after Material Ambiguity and material Conflict blocking the next bounded path have been addressed.

A ResolvedIntent may support planning, answer-only completion, no-operational-work completion, or a downstream proposal. It does not necessarily produce a WorkPlan.

A Clarification request is not itself a ResolvedIntent. If a later Observation introduces new blocking Material Ambiguity or Conflict, Continuation returns to clarification or another explicit resolution path before a successor ResolvedIntent is admitted.

The exact schema and terminal states are not frozen in M0.3.

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

Observation is data, not authority and not automatically truth beyond its stated provenance, completeness, temporal basis, and evidence.

Ordinary Cognitive Provider output remains CandidateResolution material and is not silently reclassified as Observation.

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

An unverified Origin attribution may remain semantically usable when verification is not material, provided its evidentiary status is preserved.

### Epistemic Trust

A bounded assessment of what available Evidence justifies believing about a Claim, Attribution, Observation, or source.

Epistemic Trust is separate from Governance authority.

### Trust Amplification

An invalid strengthening of evidentiary status beyond what underlying Evidence supports, including silent propagation from one Claim, identity, source, or item to another.

IRR MUST NOT perform Trust Amplification.

### Conflict

A condition where attributable semantic inputs make incompatible Claims relevant to the same resolution.

A Conflict that can materially change the next bounded path blocks ResolvedIntent admission until an explicit bounded precedence rule, clarification, or further attributable information resolves it. A non-blocking Conflict may remain explicit in a ResolvedIntent.

### Completeness

An attributable assertion that an Observation or Context Item exhaustively covers a stated bounded domain for a stated purpose or time.

Completeness MUST NOT be inferred merely because a result appears exhaustive.

Absence within explicitly complete bounded evidence may support a negative conclusion only within the scope and time that the Completeness assertion covers.

### Freshness

The temporal relevance of a Claim, Context Item, or Observation to the semantics being resolved.

Freshness MUST NOT be inferred when time materially changes meaning and the available material does not support that inference.

### Temporal Basis

Attributable temporal context used to interpret relative or time-sensitive semantics such as `today`, `latest`, `current`, or `just downloaded`.

A Temporal Basis may later be represented by a resolution time, timezone, timestamp, sequence marker, or another bounded temporal reference. M0.2 freezes the semantics, not the wire format.

IRR MUST NOT silently substitute an ambient machine clock or timezone when the Temporal Basis is material.

## Context terms

### Context

Caller-supplied material admitted to resolution through an explicit Host boundary.

Context does not grant authority merely by being present.

### Context Item

An attributable unit of Context whose semantic content and source distinctions can be preserved when material to trust, ambiguity, Conflict, Freshness, Completeness, or resolution.

Exact representation is deferred.

### Context Boundary

The explicit Host-controlled boundary defining what semantic material is available to IRR for a resolution or Continuation.

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

### Semantic Operation

A platform-neutral description of requested operational meaning, such as `filesystem.search`, `archive.extract`, or `process.launch`.

A Semantic Operation describes what work is requested, not the command, API call, script, library, or adapter used to implement it.

Platform neutrality does not permit an implementation to introduce material effects absent from the represented work semantics.

```text
semantic operation != implementation command
platform neutrality != effect-changing substitution
```

### WorkPlan

A finite, bounded semantic representation of operational work derived from a ResolvedIntent when operational work is actually required.

Not every ResolvedIntent yields a WorkPlan.

A WorkPlan may represent WorkSteps, explicit dependencies, symbolic inputs/outputs, bounded ordering, and explicit Continuation Points.

A WorkPlan is not executable authority, a general-purpose script, or an autonomous planner loop.

### WorkStep

A bounded semantic unit of requested operational work inside a WorkPlan.

A WorkStep must remain attributable to its parent ResolvedIntent/WorkPlan semantics, an admitted constraint, or a necessary explicit prerequisite. Exact structure is deferred.

An ordinary WorkStep's semantic contract must itself be inspectably bounded. A broad or opaque step must not hide an open-ended observe/decide/act loop merely to make the containing WorkPlan look finite; long-form delegated cognition belongs to the separate Worker boundary.

A valid WorkStep is not an authorized WorkStep.

### Work Dependency

A finite ordering or data requirement between WorkSteps.

A Work Dependency may express that one step requires another step's result or must occur after another step for semantic validity.

A Work Dependency is not arbitrary program control flow. V1 WorkPlan dependencies form a finite acyclic graph.

### Symbolic Reference

A reference from planned work to a value that is expected to be supplied by another planned result or future attributable input but is not yet known at planning time.

A Symbolic Reference does not assert that the referenced value has already been observed or established as true.

### Continuation Point

An explicit boundary where additional attributable information must return to IRR before a new material semantic decision may be made.

A Continuation Point is not an embedded autonomous planner loop or hidden runtime branch.

### Successor WorkPlan

A later WorkPlan produced through IRR Continuation when new admitted information changes material operational semantics.

A Successor WorkPlan preserves lineage to the prior intent/work representation rather than silently mutating the prior plan in place. Exact identity and lineage representation are deferred.

### Plan Derivation

The attributable semantic relationship explaining why a material WorkStep exists in a WorkPlan.

A material WorkStep must derive from the parent ResolvedIntent, an explicit admitted constraint, or a necessary bounded prerequisite. Plan Derivation does not permit unrelated convenience work.

### Completion Semantics

The intended meaning of completion for a WorkStep, WorkPlan, or parent intent.

Step completion, plan completion, and intent satisfaction are distinct concepts. Exact completion-condition and Outcome schemas are deferred.

### Capability

A named operation class that an external execution environment can potentially provide, such as `filesystem.search` or `archive.extract`.

A Capability describes what may be requested; it does not itself grant permission to perform it.

M0.5 freezes the exact relationship between Semantic Operations, capabilities, catalog membership, availability, and the Capability Catalog.

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

Worker delegation is distinct from ordinary WorkStep execution; exact delegated-work handoff semantics are deferred to M0.8.

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
absence in incomplete context != negation
bounded completeness != global completeness
temporal basis != ambient wall clock
intent != permission
clarification != resolved intent
clarification != intent completion
assumption != hidden default
assumption != established fact
information need != observation authority
cognitive provider output != observation by default
resolution != approval
resolved intent != work plan requirement
semantic operation != implementation command
platform neutrality != effect-changing substitution
work plan != scripting language
bounded work plan != opaque autonomous work step
work dependency != arbitrary control flow
presentation order != execution dependency
symbolic reference != observed value
continuation point != autonomous planner loop
necessary prerequisite != hidden side task
executable-looking text != executable authority
executable-looking text != work plan control flow
valid plan != currently executable plan
valid plan != authorized plan
valid plan != successful effect
step completion != plan completion
plan completion != intent satisfaction by default
failure != automatic retry
unknown result != automatic retry
missing implementation != permission to invent a different operation
worker delegation != ordinary work step execution
inspectable != approved
handoff != authorization
candidate validity != factual truth
candidate validity != safety
candidate validity != permission
authorization != effect evidence
```

## External-neighbor names

`HDE`, `Character_OS`, `Organism`, `Codexia`, and `Runplane` are examples of possible external integrations. Their names in documentation do not create package, runtime, or architectural dependencies from the IRR core.
