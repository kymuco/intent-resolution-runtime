# Intent Resolution Runtime

Intent Resolution Runtime (IRR) resolves human-, companion-, worker-, or system-originated intent into bounded, inspectable resolution outcomes. When operational work is required, IRR produces bounded semantic work representations and downstream handoffs.

> **Intent != Permission != Effect**

IRR resolves what an intent means and what, if anything, should happen next operationally. It does not grant authority and it does not perform effects.

## Status

M0.1 — Product Charter & Vocabulary.

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
               IRR
     interpret / clarify / resolve
                |
        +-------+------------------+
        |                          |
        v                          v
 non-operational              bounded operational
resolution outcome             representation
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

When operational work is required, IRR may describe requested scope, effects, dependencies, uncertainty, and required capabilities. It must not claim that a request is safe, approved, authorized, or true merely because it is structurally resolvable.

## What IRR is not

IRR is not a shell-command generator, desktop automation engine, policy or permission system, companion/personality runtime, memory system, general chat assistant, Runplane replacement, Codexia replacement, HDE-specific subsystem, or Organism runtime.

These systems may later integrate with IRR through explicit boundaries, but they are not dependencies of the IRR core.

## Normative documents

- [M0 runtime charter](docs/m0_runtime_charter.md)
- [Terminology](docs/terminology.md)

## Planning record

- [Roadmap](ROADMAP.md)

`ROADMAP.md` is the preserved planning record and may contain superseded planning guidance. Normative runtime contracts are frozen incrementally by M0.1 through M0.10.
