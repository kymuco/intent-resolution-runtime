# Intent Resolution Runtime

Intent Resolution Runtime (IRR) interprets and resolves human-, companion-, worker-, or system-originated intent through bounded, inspectable resolution paths. When operational work is required, IRR may produce bounded semantic work representations suitable for downstream handoff.

> **Intent != Permission != Effect**

IRR resolves what an intent means and what, if anything, should happen next operationally. It does not grant authority and it does not perform effects.

## Status

Current milestone: **M0.7 — Cognitive Provider Boundary**.

M0.1 Product Charter & Vocabulary, M0.2 Trust, Context & Resolution Semantics, M0.3 Intent → Work Boundary, M0.4 Late Binding & Observation Boundary, M0.5 Capability Boundary, and M0.6 Governance & Authority Boundary are frozen in `main`. M0.7 freezes the stable cognitive seam through which replaceable LLM, deterministic, hybrid, or future Organism-derived providers may propose `CandidateResolution` semantics without owning final IRR state, factual truth, capability admission, authority, or effects.

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
               IRR <---------------- CandidateResolution
     interpret / clarify / resolve                 ^
                |                                  |
                |                         Cognitive Provider
                |                      LLM / deterministic /
                |                       hybrid / Organism-derived
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
                                                                 WorkStep[]
                                                         semantic, finite,
                                                         bounded, inspectable,
                                                     capability-matched where required
                                                                     |
                                                                     v
                                                                WorkProposal
                                                          exact proposed semantics
                                                                     |
                                                                     v
                                                                  Governance
                                                      /-----------+-----------+-----------\
                                                     v            v           v            v
                                                Authorization   Denial    Constraint   require_review
                                                     |                        |            |
                                                     |                        v            v
                                                     |                 IRR Continuation   no execution
                                                     |                        |          authority yet
                                                     |                        v
                                                     |               Successor semantics
                                                     v
                                                   Handoff
                                                     |
                                                     v
                                              bounded Executor
                                              /              \
                                             v                v
                                          Effect      attributable Outcome /
                                                       optional returned data
                                                              |
                                          +-------------------+-------------------+
                                          |                   |                   |
                                          v                   v                   v
                                  no further semantic   fixed Binding Rule   new material choice
                                         use /                  |                   |
                                      completion                v                   v
                                                           Bound Value        IRR Continuation
                                                                |
                                                                v
                                                        next bounded work
                                              (again subject to applicable authority)
```

A Cognitive Provider is a replaceable proposal source, not the owner of IRR state. IRR discloses only an explicitly permitted bounded input surface to a provider; the provider returns attributable `CandidateResolution` material; IRR independently validates and admits or rejects those semantics under the same M0.1–M0.6 contracts used without a provider.

```text
provider proposes != IRR admits
CandidateResolution != ResolvedIntent
provider output != Context by default
provider output != Observation by default
provider recommendation != Governance Decision
```

Provider confidence, fluent rationale, model identity, local placement, deterministic behavior, or an Organism-derived internal representation do not establish factual truth, Capability Match, Authorization, or final IRR state. IRR admission must depend on inspectable candidate semantics and attributable admitted inputs, not private chain-of-thought.

Context or Capability Catalog material available inside IRR is not automatically provider-disclosable. A provider receives only the explicitly permitted projection for that provider boundary. Remote provider transport may itself create network/external-disclosure effects, while a local provider still does not gain blanket entitlement to all Context, memory, account data, Catalog entries, or authority material.

The Cognitive Provider boundary does not grant ambient retrieval or tool authority. If a provider needs files, repository state, browser data, current world state, or other new information, it may propose a bounded Information Need or Observation Need; hidden model-side tools/retrieval cannot be used to launder new facts into IRR Context or Observation. A tool-using/provider-agent implementation that acquires external information must return that information through an explicit attributable Host/acquisition boundary before IRR can use it as evidence.

A provider may propose semantic interpretation, clarification, candidate inferences, bounded work semantics, or capability usage based on disclosed material. IRR still validates material references, ambiguity, assumptions, WorkPlan boundedness, capability requirements, exact Catalog membership, and Governance separation. Provider-generated shell/code/tool-call syntax remains candidate data rather than execution authority.

Provider output is not canonical memory and cannot self-expand future privileges. Candidate rejection also does not reject the parent intent by definition: another provider, deterministic path, clarification, or later attributable information may still resolve it. IRR may resolve simple paths without invoking any Cognitive Provider at all, so IRR is not an LLM wrapper.

Clarification pauses resolution before a successor ResolvedIntent exists; it does not by itself complete the parent intent lifecycle. A ResolvedIntent may then complete without operational work or, when bounded operational work is required, produce a WorkPlan.

IRR has no ambient semantic context. Material used for resolution must enter through an explicit Host boundary and remain attributable. A context reference is not retrieval authority, evidence is not authority, and context available to IRR is not automatically authorized for disclosure to a Cognitive Provider.

When operational work is required, IRR represents **semantic operations**, not platform-specific command sequences. A WorkPlan is finite and inspectable; it may express dependencies, symbolic inputs/outputs, bounded ordering, and explicit continuation points, but it is not a scripting language and does not own arbitrary loops, hidden retries, embedded code, or silent observation-dependent branching.

Late Binding may fill a future value only under an already admitted bounded Binding Rule. Applying that unchanged rule to compatible attributable Binding Input is value binding, not a new semantic decision. A tie, missing rule input, incompatible input, new effect, or other material choice stops mechanical Binding and returns to IRR Continuation.

Binding Input is a semantic role, not another name for Observation. A plan-local WorkStep output may feed a Binding Rule without becoming IRR Context or an Observation. When new data must influence a new semantic decision, it returns to IRR through an attributable Continuation boundary under an explicit classification. Returned data that requires no further semantic use may simply contribute to completion; M0.4 does not require every returned value to become Binding Input or Continuation input.

A WorkStep requiring operational capability may be admitted only when a compatible Capability exists in the exact applicable Capability Catalog Snapshot. The WorkPlan remains attributable to that snapshot and, where a WorkStep is capability-bound, to the admitted capability contract that justified the match. A same-named Descriptor, or one missing material input/effect/scope/result semantics needed to establish compatibility, is not automatically a valid Capability Match.

Capability Match must also preserve material Completion Semantics. A capability result that proves only acceptance, scheduling, or another weaker state cannot silently satisfy a WorkStep whose admitted completion meaning requires a stronger downstream result.

If no compatible Capability is admitted in that snapshot, IRR reports the conceptual `missing_capability` condition rather than inventing shell commands, browser automation, Worker fallback, another service, or arbitrary executable code.

`missing_capability` means **missing from the exact applicable planning surface**, not “impossible everywhere” and not “Governance denied this.” IRR does not widen or ambiently rediscover the Catalog just because a required operation is absent.

A generic `shell.execute`, process-execution, or browser capability is not a universal adapter for unrelated Semantic Operations. Such a capability can match only when the admitted work genuinely requests that bounded operation; IRR does not silently lower `archive.extract`, `telegram.send_file`, or another semantic operation into generic command execution.

The Catalog itself is structured IRR input, not automatically Provider-disclosable context. If a Cognitive Provider needs capability information, only the explicitly permitted Catalog material crosses that boundary.

Capability Catalog Membership, current Capability Availability, invocation readiness, and Governance Authorization are distinct:

```text
known capability != currently available capability
Capability Availability != invocation readiness
available capability != authorized capability
catalog membership != successful effect
```

A known Capability may be temporarily unavailable while the capability-bound WorkPlan remains semantically valid. A Capability may also remain available even when one otherwise semantically compatible bound resource or invocation input is stale, missing, unreachable, or temporarily unusable. Semantic input/scope incompatibility is instead a Capability Match or revalidation failure, not a transient readiness state. Conversely, an executable mechanism that exists on the machine does not become an admitted Capability unless it is explicitly represented in the applicable Catalog.

Capability effect and scope metadata are descriptive, not authority. A Descriptor may define a broader bounded effect envelope than one particular invocation requests; the concrete WorkStep must still expose its actual requested effects and scope. Unavoidable capability effects that exceed the represented WorkStep semantics invalidate the match rather than becoming hidden side effects.

A WorkProposal is the bounded operational work surface presented to Governance. It remains attributable to the exact reviewed work semantics; a convenient human-readable summary cannot silently replace material scope, effect, recipient, disclosure, provider, uncertainty, or lineage that the authority decision actually depends on.

Governance is external to IRR. Conceptually it may authorize, deny, constrain, or require additional review. These are conceptual decision components, not a requirement that every Governance response contain exactly one mutually exclusive state: one response may, for example, authorize an already represented read-only subset while constraining the mutation remainder. A Governance Constraint is not Authorization by default and cannot be interpreted by an Executor as permission to rewrite the proposal and continue.

A WorkPlan or WorkProposal does not become permission merely because it is valid or inspectable, and IRR never writes authority semantics such as `approved=true`, `safe=true`, or `permission_granted=true` into its own plan state.

Authorization is a separate attributable authority decision over explicitly bounded work. Authorization for one resource, recipient, effect, provider, prerequisite, or WorkStep subset does not transitively authorize related work. Human-originated intent — including conversational text such as “yes” or “do it” — is not Authorization by default; an external Governance mechanism must establish what proposal the act refers to and what authority it carries.

An Authorization Condition may limit authority applicability without changing work semantics, for example a time/session or one-use condition. A Governance Constraint that materially changes resource, recipient, scope, effect, disclosure, provider semantics, or completion meaning does **not** edit the old WorkPlan in place. It returns through IRR Continuation and produces explicit successor semantics with lineage.

Governance may authorize an already represented bounded subset of a WorkProposal without authorizing the whole plan. But if that subset becomes the new objective — for example “inspect only, do not extract” — the objective change must be explicit through successor resolution; completing the subset does not silently satisfy the original full intent.

Absence of sufficient Authorization remains fail-closed for authority-requiring execution, but it is not the same semantic state as an explicit Denial. `require_review` is also not Authorization and does not predict eventual approval.

M0.6 does not force one universal ordering between Binding and Governance. Governance may authorize bounded symbolic work when its scope explicitly covers the symbolic rule/class; a later Bound Value must still remain within that authority. A concrete binding can therefore remain semantically valid yet require Governance re-review without requiring a successor WorkPlan when no semantic meaning changed.

Capability Drift, rebinding, provider substitution, new recipients, new disclosure, or other material changes do not silently inherit prior Authorization. Pure availability drift is different: an executor going offline does not by itself rewrite what Governance authorized.

Authorization does not prove execution, Outcome, completion, or Effect. Conversely, an observed Effect does not prove that prior Authorization existed, and later approval cannot rewrite history to make an earlier unauthorized effect retroactively authorized.

```text
Authorization != Effect
Authorization != Outcome
Authorization != effect evidence
Effect != proof of Authorization
```

Authorized observation/read also does not grant authority over discovered resources, and read authority does not automatically become disclosure authority.

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
- [M0.6 governance & authority boundary](docs/m0_governance_authority_boundary.md)
- [M0.7 cognitive provider boundary](docs/m0_cognitive_provider_boundary.md)
- [Terminology](docs/terminology.md)

## Planning record

- [Roadmap](ROADMAP.md)

`ROADMAP.md` is the preserved planning record and may contain superseded planning guidance. Normative runtime contracts are frozen incrementally by M0.1 through M0.10.
