# IRR Terminology

Status: **normative vocabulary through M0.5**.

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

The exact schema and terminal states are not frozen in M0.5.

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

Attributable information explicitly supplied back to IRR from an external boundary or prior bounded step for continuation or resolution use.

Observation is data, not authority and not automatically truth beyond its stated provenance, completeness, temporal basis, and evidence.

Ordinary Cognitive Provider output remains CandidateResolution material and is not silently reclassified as Observation. Returned data and plan-local WorkStep output are not automatically Observations merely because they contain information.

### Late Binding

Deferred concretization of a value when the semantic Binding Rule is already explicit and bounded before the value becomes available.

Late Binding defers a value, not an unadmitted semantic decision.

```text
late binding != unadmitted semantic discretion
unknown value != unknown decision rule
```

### Binding Input

Attributable data supplied to a Binding Rule for the purpose of concretizing a Symbolic Reference.

Binding Input is a semantic role, not a universal data class. Depending on the surrounding contract, it may be plan-local WorkStep output, an Observation, admitted Context, or another explicitly permitted attributable input.

Binding Input is not Observation, Context, Outcome, or authority by default. Availability of Binding Input at one boundary does not authorize disclosure to another evaluator boundary.

### Binding Rule

An explicit bounded semantic rule that determines how compatible Binding Input may satisfy a Symbolic Reference.

A Binding Rule consumes supplied input; its evaluation does not itself observe, retrieve, query ambient state, or perform external effects.

A Binding Rule must not be a hidden heuristic, ambient ordering preference, free-form model judgment, or invitation for an Executor to improvise beyond admitted semantics.

### Selection Policy

A bounded part of Binding semantics describing how a concrete value may be selected when admitted intent already treats multiple values as interchangeable.

A Selection Policy may permit a bounded non-unique choice only when the admissible set and choice semantics were established before the Binding Input arrived. It is not permission to invent a tie-breaker after seeing the candidates.

A Selection Policy is semantic selection metadata, not a Governance policy. It does not authorize a resource, effect, disclosure, scope, cost, or execution merely because that value is selectable.

```text
Selection Policy != Governance policy
Selection Policy != authorization
```

Exact representation is deferred.

### Binding

The act of associating a concrete Bound Value with a Symbolic Reference by applying unchanged admitted Binding Rule and Selection Policy semantics to compatible attributable Binding Input.

Binding is value instantiation, not semantic WorkPlan self-mutation, authorization, or permission.

### Bound Value

A concrete value associated with a Symbolic Reference after admissible Binding.

A Bound Value retains material semantic lineage and evidentiary limitations. It is not automatically a timeless fact, authorization, or permission grant.

### Rebinding

A later association of a Symbolic Reference or successor symbolic slot with a materially different concrete value after an earlier Binding exists.

Rebinding must not silently overwrite prior binding history. Exact lifecycle and identity representation are deferred.

### Continuation

A successor resolution step that consumes attributable prior state plus new clarification, Observation, Outcome, or another explicitly admitted continuation input while preserving parent intent lineage.

Continuation is required when new information introduces a material semantic decision not already determined by admitted semantics. Continuation is not retrieval or observation authority.

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

An attributable assertion that an Observation, Context Item, or other attributable Binding Input exhaustively covers a stated bounded domain for a stated purpose or time.

Completeness MUST NOT be inferred merely because a result appears exhaustive.

Absence within explicitly complete bounded evidence may support a negative conclusion only within the scope and time that the Completeness assertion covers.

### Freshness

The temporal relevance of a Claim, Context Item, Observation, Binding Input, or Bound Value to the semantics being resolved or executed.

Freshness MUST NOT be inferred when time materially changes meaning and the available material does not support that inference.

Successful Binding does not prove that the external world still matches the Binding Input indefinitely.

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

A WorkPlan may represent WorkSteps, explicit dependencies, symbolic inputs/outputs, bounded ordering, Binding Rules, Selection Policies, and explicit Continuation Points.

A WorkPlan is not executable authority, a general-purpose script, or an autonomous planner loop.

Every operational WorkPlan is attributable to the exact applicable Capability Catalog Snapshot and admitted Capability contracts used to validate its WorkSteps.

### WorkStep

A bounded semantic unit of requested operational work inside a WorkPlan.

A WorkStep must remain attributable to its parent ResolvedIntent/WorkPlan semantics, an admitted constraint, or a necessary explicit prerequisite. Exact structure is deferred.

An ordinary WorkStep's semantic contract must itself be inspectably bounded. A broad or opaque step must not hide an open-ended observe/decide/act loop merely to make the containing WorkPlan look finite; long-form delegated cognition belongs to the separate Worker boundary.

A valid WorkStep is not an authorized WorkStep.

An operational WorkStep requiring a Capability is admissible only when a compatible Capability exists in the exact applicable Catalog Snapshot.

### Work Dependency

A finite ordering or data requirement between WorkSteps.

A Work Dependency may express that one step requires another step's result or must occur after another step for semantic validity.

A Work Dependency is not arbitrary program control flow. V1 WorkPlan dependencies form a finite acyclic graph.

### Symbolic Reference

A semantically attributable reference from planned work to a value expected from another planned result or future attributable input but not yet known at planning time.

A Symbolic Reference does not assert that the referenced value has already been observed or established as true. Primitive type similarity does not allow one symbolic slot to satisfy another unrelated slot.

```text
symbolic reference != observed value
structural compatibility != semantic substitutability
```

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

A bounded operation contract that an external execution environment can potentially provide, such as `filesystem.search` or `archive.extract`.

A Capability is distinct from both the Semantic Operation it can represent and the implementation command or adapter that may execute it, even when the human-readable labels are identical.

A Capability does not grant permission, prove availability, or prove successful effect.

```text
semantic operation != capability
same textual label != same semantic object
capability != implementation command
```

### Capability Descriptor

The attributable semantic definition of a Capability within a Capability Catalog Snapshot.

A future Descriptor must preserve enough semantics to identify conceptually the capability identity, purpose, input contract, output contract, material effect metadata, scope requirements, and executor/provider identity when material.

Exact fields are deferred to M1.

### Capability Identity

The semantic identity of a declared Capability contract.

A stable human-readable capability identifier alone does not prove unchanged semantics across Catalog Snapshots.

```text
same capability_id != same capability semantics
```

### Capability Catalog

The externally supplied bounded set of Capability definitions admitted for a resolution.

The Catalog is the capability planning surface IRR may use. It is not necessarily a global inventory of every operation technically possible elsewhere.

IRR does not ambiently discover or widen the Catalog. Catalog omission does not by itself mean Governance denial.

### Catalog Snapshot

The exact attributable version of the Capability Catalog used for a resolution or planning decision.

Every operational WorkPlan remains attributable to the exact applicable Catalog Snapshot and admitted Capability contracts used to validate its WorkSteps.

Exact snapshot identity, digest, serialization, matched-descriptor references, and persistence are deferred.

### Catalog Membership

The condition that a Capability Descriptor is present in the exact applicable Catalog Snapshot and is eligible for matching under that snapshot's scope.

Catalog Membership means capability-known-for-planning. It does not establish current Availability, Authorization, Governance approval, or successful effect.

### Capability Match

The bounded determination that a Capability Descriptor can represent a planned Semantic Operation under the required semantic input, output, effect, scope, and provider/executor constraints.

Capability Match is semantic compatibility, not name similarity, primitive type compatibility, implementation coercion, or provider preference.

Descriptor presence alone does not establish a Capability Match.

### Input Contract

The semantic input shape and constraints a Capability may consume.

Input compatibility is semantic rather than merely structural or primitive-type compatibility. Exact type representation is deferred.

### Output Contract

The semantic attributable result/data contract a Capability may produce.

Capability outputs may later serve as Binding Input, Observation, Outcome evidence, completion evidence, or another explicitly classified value; output status alone does not determine that classification.

### Effect Metadata

Descriptive metadata representing the material externally observable effect surface or bounded effect envelope of a Capability contract.

Effect Metadata is inspectable semantic information, not Authorization, safety approval, or a Governance decision.

The Descriptor effect envelope remains distinct from the concrete requested effect semantics of a particular WorkStep. A match is invalid when unavoidable capability effects exceed or contradict the represented WorkStep semantics.

Exact per-invocation effect projection and effect taxonomies remain deferred.

### Scope Requirements

The bounded resource, destination, account, recipient, path, repository, network domain, or other semantic scope a Capability invocation requires.

Scope Requirements are descriptive constraints, not authorized scope. A capability's maximum supported scope is not automatically the requested WorkStep scope.

### Capability Availability

The attributable, time-bounded condition describing whether a catalog-known Capability can currently be offered by the applicable downstream environment under stated runtime conditions.

Availability is distinct from Catalog Membership and Authorization.

A known but unavailable Capability is not `missing_capability`.

An availability statement is not automatically an M0.4 Observation; classification depends on how the attributable state enters IRR.

### missing_capability

The conceptual condition where a required Semantic Operation has no compatible Capability admitted in the exact applicable Catalog Snapshot.

`missing_capability` does not claim global impossibility or Governance denial and does not authorize fallback, Catalog widening, arbitrary command execution, browser automation, Worker substitution, or silent omission of required work.

A same-named but semantically incompatible Descriptor does not satisfy the requirement.

### Capability Drift

A material membership or descriptor-semantic change between the capability surface against which work was resolved and a later capability surface presented for validation, handoff, or execution.

Capability Drift may include changed input/output contracts, effect metadata, scope requirements, or provider/executor identity when material.

Capability Drift must not silently reinterpret an existing WorkPlan. An unrelated Catalog change need not change WorkPlan meaning merely because overall snapshot identity differs, while historical snapshot attribution remains exact.

### Availability Drift

A change in whether a semantically known Capability is currently available without necessarily changing its Capability Descriptor semantics.

Availability Drift may affect executability without changing WorkPlan meaning and remains distinct from semantic or membership Capability Drift.

### Capability Revalidation

A later bounded check that an existing capability-bound WorkStep remains compatible with a current capability surface.

Revalidation is not Authorization and does not permit hidden capability substitution or semantic mutation.

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

An Executor may later perform mechanical Binding when an explicit contract permits it, but mechanical Binding does not grant semantic discretion beyond explicitly admitted Binding Rule and Selection Policy semantics.

IRR is not an Executor.

### Worker

A downstream component that performs delegated bounded work with its own subordinate lifecycle.

A Worker may return a result to IRR while IRR retains the parent intent lifecycle.

Worker delegation is distinct from ordinary WorkStep execution; exact delegated-work handoff semantics are deferred to M0.8.

### Outcome

An attributable result reported by an Executor or Worker. Exact outcome states, including unknown-outcome handling, are deferred to M0.9.

Outcome semantics remain distinct from Observation semantics even when one downstream event supplies both.

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
returned data != observation by default
Binding Input != Observation by default
Binding Input != Context by default
Binding Input != Outcome by default
Binding Input != authority
Binding Input availability != disclosure authority
observation != outcome
resolution != approval
resolved intent != work plan requirement
semantic operation != implementation command
semantic operation != capability
same textual label != same semantic object
capability != implementation command
capability != autonomous goal loop
platform neutrality != effect-changing substitution
work plan != scripting language
bounded work plan != opaque autonomous work step
work dependency != arbitrary control flow
presentation order != execution dependency
presentation order != binding precedence
symbolic reference != observed value
symbolic reference != authority
late binding != unadmitted semantic discretion
unknown value != unknown decision rule
binding rule != hidden heuristic
binding rule != unbounded executor discretion
binding evaluation != observation
binding evaluation != retrieval
binding evaluation != external effect
opaque cognitive judgment != mechanical binding
explicit bounded choice != hidden discretion
Selection Policy != Governance policy
Selection Policy != authorization
binding != semantic plan mutation
binding != authorization
bound value != timeless fact
bound value != permission
same shape != same meaning
structural compatibility != semantic substitutability
zero matches != permission to guess
stale binding != permission to reselect silently
rebind != overwrite history
binding failure != fallback authority
material new information != mechanical binding input
continuation != retrieval authority
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
empty bounded result != permission to widen scope
capability catalog != ambient capability discovery
catalog scope != global environment capability
catalog attribution != authorization
catalog omission != Governance denial
catalog membership != Governance approval
same capability_id != same capability semantics
same primitive shape != compatible capability input
name similarity != capability compatibility
implementation possibility != capability admission
descriptor present != compatible capability
multiple matches != permission for hidden provider preference
catalog order != capability precedence
catalog membership != current availability
catalog membership != authorization
catalog membership != successful effect
known capability + unavailable != missing capability
availability != timeless fact
availability claim != Observation by default
available != authorized
authorized != available
missing_capability != global impossibility
missing capability != fallback authority
partial capability coverage != full intent satisfaction
generic command execution != universal capability adapter
provider proposal != capability existence
capability prerequisite != implicit capability expansion
effect metadata != authorization
effect metadata != safety verdict
effect metadata != risk approval
descriptor effect envelope != requested invocation effect
scope requirement != authorized scope
capability-supported scope != requested scope
capability drift != silent plan reinterpretation
revalidation != authorization
revalidation != capability substitution
executor substitution != automatic semantic equivalence
capability descriptor != authorization record
risk/effect label != Governance decision
new catalog snapshot != rewritten planning history
later capability addition != retroactive capability existence
binding != capability admission
capability admission != bound-resource authorization
worker availability != capability fallback
missing capability != execution failure
unavailable capability != unknown outcome
worker delegation != ordinary work step execution
inspectable != approved
handoff != authorization
candidate validity != factual truth
candidate validity != safety
candidate validity != permission
authorization != effect evidence
authorized observation effect != authority over observed resources
```

## External-neighbor names

`HDE`, `Character_OS`, `Organism`, `Codexia`, and `Runplane` are examples of possible external integrations. Their names in documentation do not create package, runtime, or architectural dependencies from the IRR core.
