# Intent Resolution Runtime

Intent Resolution Runtime (IRR) interprets and resolves human-, companion-, worker-, or system-originated intent through bounded, inspectable resolution paths. When operational work is required, IRR may produce bounded semantic work representations suitable for downstream handoff.

> **Intent != Permission != Effect**

IRR resolves what an intent means and what, if anything, should happen next operationally. It does not grant authority and it does not perform effects.

## Status

Current milestone: **M0.4 — Late Binding & Observation Boundary**.

M0.1 Product Charter & Vocabulary, M0.2 Trust, Context & Resolution Semantics, and M0.3 Intent → Work Boundary are frozen in `main`. M0.4 freezes how future values may be bound without deferring semantic decisions: symbolic references use explicit bounded binding rules, compatible attributable observations may supply values, and new material choices return to IRR continuation rather than executor discretion.

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
                  (answer / no work)                  v
                                                  WorkStep[]
                                           semantic, finite,
                                           bounded, inspectable
                                                      |
                                      symbolic data / binding rules
                                                      |
                                         +------------+------------+
                                         |                         |
                                         v                         v
                                  unique bound value        new material choice
                                         |                         |
                                         v                         v
                               bounded downstream work      IRR Continuation
                                         |
                                         v
                              governance / authorization
                                         |
                                         v
                                  bounded executor
                                         |
                                         v
                                       effect
```

Clarification pauses resolution before a successor ResolvedIntent exists; it does not by itself complete the parent intent lifecycle. A ResolvedIntent may then complete without operational work or, when bounded operational work is required, produce a WorkPlan.

IRR has no ambient semantic context. Material used for resolution must enter through an explicit Host boundary and remain attributable. A context reference is not retrieval authority, evidence is not authority, and context available to IRR is not automatically authorized for disclosure to a Cognitive Provider.

When operational work is required, IRR represents **semantic operations**, not platform-specific command sequences. A WorkPlan is finite and inspectable; it may express dependencies, symbolic inputs/outputs, bounded ordering, and explicit continuation points, but it is not a scripting language and does not own arbitrary loops, hidden retries, embedded code, or silent observation-dependent branching.

Late Binding may fill a future value only under an already admitted bounded Binding Rule. Applying that unchanged rule to compatible attributable data is value binding, not a new semantic decision. A tie, missing rule input, incompatible observation, new effect, or other material choice stops mechanical binding and returns to IRR Continuation.

Plan-local symbolic dataflow may proceed without a new IRR resolution cycle only while all material semantics remain fixed. Returned data is not automatically an Observation, an Observation is not an Outcome, and a Bound Value is not authorization or permanent proof that the world has not changed.

An ordinary WorkStep must itself have bounded, inspectable semantics. IRR cannot hide an open-ended autonomous agent loop inside one apparently finite step. Long-form delegated cognition belongs to a separate Worker handoff boundary and is deliberately not depicted as ordinary WorkStep execution here.

Platform neutrality also does not permit effect-changing substitution: an implementation cannot silently introduce a material effect such as external disclosure merely because it is one way to perform an operation.

A semantically valid WorkPlan is still only proposed work. It does not imply current executability, authorization, execution, or successful effect. Whether a required semantic operation may be planned when no matching capability exists is intentionally deferred to the M0.5 Capability boundary.

## What IRR is not

IRR is not a shell-command generator, general-purpose workflow scripting language, desktop automation engine, policy or permission system, companion/personality runtime, memory system, general chat assistant, Runplane replacement, Codexia replacement, HDE-specific subsystem, or Organism runtime.

These systems may later integrate with IRR through explicit boundaries, but they are not dependencies of the IRR core.

## Normative documents

- [M0 runtime charter](docs/m0_runtime_charter.md)
- [M0.2 trust, context & resolution semantics](docs/m0_trust_context_resolution.md)
- [M0.3 intent → work boundary](docs/m0_intent_work_boundary.md)
- [M0.4 late binding & observation boundary](docs/m0_late_binding_observation_boundary.md)
- [Terminology](docs/terminology.md)

## Planning record

- [Roadmap](ROADMAP.md)

`ROADMAP.md` is the preserved planning record and may contain superseded planning guidance. Normative runtime contracts are frozen incrementally by M0.1 through M0.10.
