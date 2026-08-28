# M0.1 — Runtime Charter

Status: **normative for M0.1**.

This document freezes the product identity, actor vocabulary, responsibility boundary, and architectural non-goals of Intent Resolution Runtime (IRR). Later M0 PRs may refine trust, resolution, work planning, late binding, capabilities, governance, cognitive providers, delegation, and failure semantics, but they must preserve the boundary frozen here unless an explicit superseding architecture decision is reviewed.

## 1. Product definition

IRR converts human-, companion-, worker-, or system-originated intent into bounded, attributable operational work representations suitable for inspection, clarification, governance, execution handoff, or delegated-work handoff.

IRR owns **intent resolution**. It does not own authority or effects.

```text
Intent != Permission != Effect
```

A resolved intention is not permission. Permission is not proof that an effect occurred.

## 2. Product identity

```text
Repository:        intent-resolution-runtime
Planned package:   intent-resolution-runtime
Planned namespace: intent_resolution_runtime
Short name:        IRR
License:           Apache-2.0
```

The package and namespace are reserved names only in M0.1. No implementation package or public Python API is created by this milestone.

## 3. Core responsibility

Subject to later M0 contracts, IRR may:

- receive an attributable intent request;
- interpret objective and requested deliverables;
- identify ambiguity, assumptions, missing information, and uncertainty;
- represent requested work semantically rather than as arbitrary executable code;
- identify required capabilities from an externally supplied capability catalog;
- represent dependencies, requested effects, and continuation needs;
- produce bounded downstream proposals;
- consume attributable observations or outcomes to continue the same intent lineage.

IRR MUST preserve the distinction between describing requested work and authorizing that work.

## 4. Actor model

### Principal

The **Principal** is the entity whose goals or interests an intent request purports to serve. A principal declaration is contextual identity information, not proof of authority, consent, or permission.

### Origin

The **Origin** is the actor that actually produced the `IntentRequest` presented to IRR.

Conceptual origin classes are:

```text
human
companion
worker
system
```

Origin is factual provenance and MUST NOT be rewritten to imply stronger authority.

```text
origin != principal
origin != authority
origin != permission
origin != approval
```

A companion may originate a request in support of a human principal. That does not make the request human-originated.

### Host

The **Host** is the embedding system that invokes IRR and supplies bounded inputs such as context, capability catalogs, or continuation observations.

IRR MUST NOT require HDE, Character_OS, Runplane, Codexia, Organism, or another named host to exist.

### Cognitive Provider

A **Cognitive Provider** proposes an interpretation or candidate resolution. It may later be implemented by an LLM, Organism-derived system, deterministic resolver, hybrid system, or another provider.

Provider output is candidate material until admitted by IRR contracts. Admission means only contract validity; it does NOT establish factual truth, safety, approval, permission, or authority.

### Governance

**Governance** is an external authority boundary that decides whether proposed work may proceed, must be constrained, requires review, or must be denied.

IRR may describe requested effects and scopes but MUST NOT impersonate Governance.

### Executor

An **Executor** performs bounded capabilities after required downstream authority conditions are satisfied. IRR is not an executor.

### Worker

A **Worker** performs delegated bounded work with its own subordinate lifecycle, for example a research or coding worker. IRR may later delegate to workers while retaining ownership of the parent intent lifecycle.

## 5. Authority invariants

The following distinctions are normative:

```text
intent != authority
context != authority
origin != authority
resolution != approval
candidate validity != factual truth
candidate validity != safety
candidate validity != permission
authorization != effect evidence
```

IRR MUST NOT manufacture conclusions whose semantics imply that IRR granted permission, approved an effect, or proved that an effect occurred.

Conceptually:

```text
IntentRequest
     |
     v
    IRR
     |
     v
bounded work proposal
     |
     v
Governance
     |
     v
authorization / constraint / denial
     |
     v
Executor or Worker
```

Exact handoff schemas are deferred.

## 6. Context boundary

IRR is not an ambient-observation system.

Semantic context must enter through an explicit Host boundary. IRR does not gain authority to scan a machine, project, memory store, browser, repository, account, or network merely because more data would help resolution.

If required information is absent, IRR MUST represent that need rather than silently acquire ambient context.

Exact context contracts belong to M0.2.

## 7. Ambiguity versus late binding

M0.1 freezes the distinction; exact mechanics belong to M0.2 and M0.4.

**Material semantic ambiguity** exists when multiple interpretations could materially change a resource, recipient, scope, disclosure, mutation, executable target, cost, or external effect.

Material semantic ambiguity MUST NOT be hidden behind late binding.

**Late binding** is reserved for cases where the semantic selection rule is already explicit and bounded and a future observation merely supplies a value required to apply that rule.

If a later observation exposes a new material choice that the existing rule cannot resolve, the intent MUST return to continuation or clarification rather than make a silent discretionary choice.

## 8. Capability boundary

IRR does not invent capabilities or arbitrary executable fallbacks.

A future WorkPlan MUST be attributable to the exact Capability Catalog snapshot used during resolution. Capability drift MUST NOT silently change the meaning or implementation surface of an already resolved plan; revalidation or successor resolution is required.

Exact work and catalog contracts belong to M0.3 and M0.5.

## 9. Explicit non-goals

IRR is not and MUST NOT become implicitly:

- a shell-command generator;
- a general-purpose scripting language;
- a desktop automation engine;
- a filesystem or process authority;
- a network client with ambient authority;
- a policy engine;
- a permission or consent system;
- a companion, personality, or relationship runtime;
- a canonical memory owner;
- a general chat assistant;
- a replacement for Runplane or another execution runtime;
- a replacement for Codexia or another delegated worker;
- an HDE-specific subsystem;
- an Organism runtime;
- a hidden source scanner, watcher, or ambient context collector.

## 10. External-neighbor independence

The IRR core MUST remain independently implementable and testable without importing or depending on:

```text
HDE
Character_OS
Organism
Codexia
Runplane
```

These are examples of possible external neighbors, not core dependencies.

This preserves a stable seam where HDE can host IRR, Character_OS can originate intent, Organism can later act as a cognitive provider, Codexia can act as a worker, and Runplane or another runtime can execute capabilities without any of them owning IRR core semantics.

## 11. M0.1 exclusions

M0.1 intentionally does NOT freeze:

- Python classes, enums, or serialization schemas;
- runtime state machines;
- exact `IntentRequest`, `ResolvedIntent`, `WorkPlan`, or handoff fields;
- persistence or storage formats;
- digest or identity algorithms;
- context-envelope schemas;
- capability-descriptor schemas;
- governance APIs;
- cognitive-provider APIs;
- worker-delegation APIs;
- retry or recovery algorithms;
- executable adapters.

Those belong to later milestones. M0.1 freezes the vocabulary and boundary they must obey.

## 12. Acceptance criteria

M0.1 is complete when the repository states unambiguously that:

1. IRR resolves intent rather than executing effects.
2. Intent, permission, and effect are distinct stages.
3. Principal and Origin are distinct concepts.
4. Origin retains truthful provenance and does not grant authority.
5. Context and resolution do not grant authority.
6. Cognitive-provider output is candidate material, not truth or permission.
7. Governance and execution are external boundaries.
8. Material ambiguity cannot be disguised as late binding.
9. Capability meaning cannot drift silently after resolution.
10. HDE, Character_OS, Organism, Codexia, and Runplane remain replaceable external neighbors rather than IRR-core dependencies.
11. No implementation code or premature runtime schema is introduced.
