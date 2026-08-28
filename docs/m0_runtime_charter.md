# M0.1 — Runtime Charter

Status: **normative for M0.1**.

This document freezes the product identity, actor vocabulary, responsibility boundary, and architectural non-goals of Intent Resolution Runtime (IRR). Later M0 PRs may refine trust, resolution, work planning, late binding, capabilities, governance, cognitive providers, delegation, and failure semantics, but they must preserve the boundary frozen here unless an explicit superseding architecture decision is reviewed.

## 1. Product definition

IRR interprets and resolves human-, companion-, worker-, or system-originated intent through bounded, attributable resolution paths.

A resolution does not necessarily imply operational work. IRR may resolve an inquiry without producing a WorkPlan, request clarification when semantics are insufficient, or determine that no operational work is required. When operational work is required, IRR may produce bounded, attributable operational work representations suitable for inspection, governance, execution handoff, or delegated-work handoff.

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
- resolve without operational work when no WorkPlan is required;
- request clarification rather than invent missing semantics;
- represent requested work semantically rather than as arbitrary executable code when operational work is required;
- identify required capabilities from an externally supplied capability catalog;
- represent dependencies, requested effects, and continuation needs;
- produce bounded downstream proposals;
- consume attributable observations or outcomes to continue the same intent lineage.

IRR MUST NOT manufacture operational work merely because an intent is structurally resolvable.

IRR MUST preserve the distinction between describing requested work and authorizing that work.

## 4. Actor model

### Principal

The **Principal** is the entity whose goals or interests an intent request purports to serve. A principal declaration is contextual identity information, not proof of authority, consent, or permission.

### Origin

The **Origin** identifies the actor attributed as having produced the `IntentRequest` presented to IRR.

Conceptual origin classes are:

```text
human
companion
worker
system
```

Origin is provenance metadata, not authority. The evidence supporting an origin attribution is a separate trust concern: it may later be self-asserted, Host-attested, cryptographically verified, or otherwise evidenced. M0.2 freezes those trust semantics.

IRR MUST preserve the supplied origin attribution and MUST NOT silently strengthen its evidentiary status or rewrite it to imply stronger authority.

```text
origin != principal
origin != authority
origin != permission
origin != approval
origin attribution != origin verification
```

A companion may originate a request in support of a human principal. That does not make the request human-originated.

### Host

The **Host** is the embedding system that invokes IRR and supplies bounded inputs such as context, capability catalogs, or continuation observations.

IRR MUST NOT require HDE, Character_OS, Runplane, Codexia, Organism, or another named integration to exist.

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
origin attribution != origin verification
resolution != approval
candidate validity != factual truth
candidate validity != safety
candidate validity != permission
authorization != effect evidence
```

IRR MUST NOT manufacture conclusions whose semantics imply that IRR granted permission, approved an effect, proved an origin attribution, or proved that an effect occurred.

Conceptually:

```text
IntentRequest
     |
     v
    IRR
     |
     +----------------------+
     |                      |
     v                      v
non-operational       bounded work proposal
resolution path             |
                            v
                       Governance
                            |
                            v
             authorization / constraint / denial
                            |
                            v
                   Executor or Worker
```

Exact resolution and handoff schemas are deferred.

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
- exact answer-only, clarification, no-operational-work, or terminal outcome schemas;
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
2. Not every resolved intent requires operational work or a WorkPlan.
3. Intent, permission, and effect are distinct stages.
4. Principal and Origin are distinct concepts.
5. Origin is attributable provenance; its evidentiary status is not silently strengthened and it does not grant authority.
6. Context and resolution do not grant authority.
7. Cognitive-provider output is candidate material, not truth or permission.
8. Governance and execution are external boundaries.
9. Material ambiguity cannot be disguised as late binding.
10. Capability meaning cannot drift silently after resolution.
11. HDE, Character_OS, Organism, Codexia, and Runplane remain replaceable external neighbors rather than IRR-core dependencies.
12. No implementation code or premature runtime schema is introduced.
