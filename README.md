# Intent Resolution Runtime

Intent Resolution Runtime (IRR) interprets and resolves human-, companion-, worker-, or system-originated intent through bounded, inspectable resolution paths. When operational work is required, IRR may produce bounded semantic work representations suitable for downstream handoff.

> **Intent != Permission != Effect**

IRR resolves what an intent means and what, if anything, should happen next operationally. It does not grant authority and it does not perform effects.

## Status

Current milestone: **M0.5 — Capability Boundary**.

M0.1 Product Charter & Vocabulary, M0.2 Trust, Context & Resolution Semantics, M0.3 Intent → Work Boundary, and M0.4 Late Binding & Observation Boundary are frozen in `main`. M0.5 freezes how WorkSteps are admitted only against an explicit attributable Capability Catalog snapshot, how missing capabilities fail closed, and how capability membership, availability, effects, scope, authorization, and drift remain distinct.

This repository is currently charter-first. There is intentionally no runtime implementation or `src/` tree yet. Python schemas and executable APIs begin only after the M0 boundary freeze is complete.

## Product identity

- Repository: `intent-resolution-runtime`
- Planned distribution: `intent-resolution-runtime`
- Planned Python namespace: `intent_resolution_runtime`
- Short name: `IRR`
- License: Apache-2.0

## Boundary

```text
human / companion / worker / system
                |
                v
           IntentRequest
                |
                v
      explicit bounded context
                |
                v
               IRR
     interpret / clarify / resolve
                |
        +-------+------------------+
        |                          |
        v                          v
 clarification                ResolvedIntent
(pre-resolution pause)             |
                            +-------+------------------+
                            |                          |
                            v                          v
                    non-operational                WorkPlan
                      resolution                      |
                  (answer / no work)                  |
                                                      |       explicit attributable
                                                      |       Capability Catalog Snapshot
                                                      |                  |
                                                      +------------------+
                                                                     |
                                                                     v
                                                        capability-bound WorkStep[]
                                                         semantic, finite,
                                                         bounded, inspectable
                                                                     |
                                                        applicable downstream
                                                     governance / authorization
                                                                     |
                                                                     v
                                                              bounded executor
                                                            /                 \
                                                           v                   v
                                                        effect      optional attributable
                                                                      returned data
                                                                           |
                                                     +---------------------+---------------------+
                                                     |                     |                     |
                                                     v                     v                     v
                                             no further semantic     fixed Binding Rule    new material choice
                                                    use /                    |                     |
                                                 completion                  v                     v
                                                                       Bound Value          IRR Continuation
                                                                            |
                                                                            v
                                                                    next bounded work
                                                        (again subject to applicable authority)
```

Clarification pauses resolution before a successor ResolvedIntent exists; it does not by itself complete the parent intent lifecycle. A ResolvedIntent may then complete without operational work or, when bounded operational work is required, produce a WorkPlan.

IRR has no ambient semantic context. Material used for resolution must enter through an explicit Host boundary and remain attributable. A context reference is not retrieval authority, evidence is not authority, and context available to IRR is not automatically authorized for disclosure to a Cognitive Provider.

When operational work is required, IRR represents **semantic operations**, not platform-specific command sequences. A WorkPlan is finite and inspectable; it may express dependencies, symbolic inputs/outputs, bounded ordering, and explicit continuation points, but it is not a scripting language and does not own arbitrary loops, hidden retries, embedded code, or silent observation-dependent branching.

Late Binding may fill a future value only under an already admitted bounded Binding Rule. Applying that unchanged rule to compatible attributable Binding Input is value binding, not a new semantic decision. A tie, missing rule input, incompatible input, new effect, or other material choice stops mechanical Binding and returns to IRR Continuation.

Binding Input is a semantic role, not another name for Observation. A plan-local WorkStep output may feed a Binding Rule without becoming IRR Context or an Observation. When new data must influence a new semantic decision, it returns to IRR through an attributable Continuation boundary under an explicit classification. Returned data that requires no further semantic use may simply contribute to completion; M0.4 does not require every returned value to become Binding Input or Continuation input.

A WorkStep requiring operational capability may be admitted only when a compatible Capability exists in the exact applicable Capability Catalog Snapshot. The WorkPlan remains attributable to that snapshot and to the admitted capability contracts that justified its WorkSteps.

If no compatible Capability is admitted in that snapshot, IRR reports the conceptual `missing_capability` condition rather than inventing shell commands, browser automation, Worker fallback, another service, or arbitrary executable code.

`missing_capability` means **missing from the exact applicable planning surface**, not “impossible everywhere” and not “Governance denied this.” IRR does not widen or ambiently rediscover the Catalog just because a required operation is absent.

A generic `shell.execute`, process-execution, or browser capability is not a universal adapter for unrelated Semantic Operations. Such a capability can match only when the admitted work genuinely requests that bounded operation; IRR does not silently lower `archive.extract`, `telegram.send_file`, or another semantic operation into generic command execution.

Capability Catalog Membership, current Capability Availability, and Governance Authorization are distinct:

```text
known capability != currently available capability
available capability != authorized capability
catalog membership != successful effect
```

A known Capability may be temporarily unavailable while the capability-bound WorkPlan remains semantically valid. Conversely, an executable mechanism that exists on the machine does not become an admitted Capability unless it is explicitly represented in the applicable Catalog.

Capability effect and scope metadata are descriptive, not authority. A Descriptor may define a broader bounded effect envelope than one particular invocation requests; the concrete WorkStep must still expose its actual requested effects and scope. Unavoidable capability effects that exceed the represented WorkStep semantics invalidate the match rather than becoming hidden side effects.

IRR may represent that a capability can mutate local state, launch a process, use a network, or disclose data externally, but it does not decide that those effects are safe or permitted. M0.6 owns Governance semantics.

Capability identity is more than a human-readable name. The same `capability_id` does not prove identical input/output contracts, effect surface, scope requirements, provider boundary, or semantics forever. Material Capability Drift must not silently reinterpret an already-resolved WorkPlan.

M0.4 does not freeze Binding before or after Governance. An observation-producing WorkStep may require authorization before it runs, and a newly concrete Bound Value may later require Governance review. Binding success itself grants no permission.

Plan-local symbolic dataflow may proceed without a new IRR resolution cycle only while all material semantics remain fixed. Returned data is not automatically an Observation, an Observation is not an Outcome, and a Bound Value is not authorization or permanent proof that the world has not changed.

An ordinary WorkStep must itself have bounded, inspectable semantics. IRR cannot hide an open-ended autonomous agent loop inside one apparently finite step. Long-form delegated cognition belongs to a separate Worker handoff boundary and is deliberately not depicted as ordinary WorkStep execution here.

Platform neutrality also does not permit effect-changing substitution: an implementation cannot silently introduce a material effect such as external disclosure merely because it is one way to perform an operation.

A semantically valid WorkPlan is still only proposed work. It does not imply current executability, authorization, execution, or successful effect.

## What IRR is not

IRR is not a shell-command generator, general-purpose workflow scripting language, desktop automation engine, policy or permission system, companion/personality runtime, memory system, general chat assistant, Runplane replacement, Codexia replacement, HDE-specific subsystem, or Organism runtime.

These systems may later integrate with IRR through explicit boundaries, but they are not dependencies of the IRR core.

## Normative documents

- [M0 runtime charter](docs/m0_runtime_charter.md)
- [M0.2 trust, context & resolution semantics](docs/m0_trust_context_resolution.md)
- [M0.3 intent → work boundary](docs/m0_intent_work_boundary.md)
- [M0.4 late binding & observation boundary](docs/m0_late_binding_observation_boundary.md)
- [M0.5 capability boundary](docs/m0_capability_boundary.md)
- [Terminology](docs/terminology.md)

## Planning record

- [Roadmap](ROADMAP.md)

`ROADMAP.md` is the preserved planning record and may contain superseded planning guidance. Normative runtime contracts are frozen incrementally by M0.1 through M0.10.
