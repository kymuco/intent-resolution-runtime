# Intent Resolution Runtime

Intent Resolution Runtime (IRR) interprets and resolves human-, companion-, worker-, or system-originated intent through bounded, inspectable resolution paths. When operational work is required, IRR may produce bounded semantic work representations suitable for downstream handoff.

> **Intent != Permission != Effect**

IRR resolves what an intent means and what, if anything, should happen next operationally. It does not grant authority and it does not perform effects.

## Status

Current milestone: **M0.2 — Trust, Context & Resolution Semantics**.

M0.1 Product Charter & Vocabulary is frozen in `main`. M0.2 freezes how IRR may know and resolve intent: context is explicit and bounded, evidence remains scoped, material ambiguity blocks resolution, and missing semantics are clarified rather than invented.

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
 non-operational              bounded operational
 resolution path               representation
(answer / no work /                  |
 clarification)                     v
                         governance / authorization
                                   |
                                   v
                         executor or delegated worker
                                   |
                                   v
                                 effect
```

Not every intent produces operational work. IRR may resolve an inquiry, request clarification, or determine that no operational work is required without manufacturing a WorkPlan.

IRR has no ambient semantic context. Material used for resolution must enter through an explicit Host boundary and remain attributable. A context reference is not retrieval authority, evidence is not authority, and context available to IRR is not automatically authorized for disclosure to a Cognitive Provider.

When operational work is required, IRR may describe requested scope, effects, dependencies, uncertainty, and required capabilities. It must not claim that a request is safe, approved, authorized, or true merely because it is structurally resolvable.

## What IRR is not

IRR is not a shell-command generator, desktop automation engine, policy or permission system, companion/personality runtime, memory system, general chat assistant, Runplane replacement, Codexia replacement, HDE-specific subsystem, or Organism runtime.

These systems may later integrate with IRR through explicit boundaries, but they are not dependencies of the IRR core.

## Normative documents

- [M0 runtime charter](docs/m0_runtime_charter.md)
- [M0.2 trust, context & resolution semantics](docs/m0_trust_context_resolution.md)
- [Terminology](docs/terminology.md)

## Planning record

- [Roadmap](ROADMAP.md)

`ROADMAP.md` is the preserved planning record and may contain superseded planning guidance. Normative runtime contracts are frozen incrementally by M0.1 through M0.10.
