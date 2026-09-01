# M1.6b1 — Capability Requirement / Exact Match IR

Status: **implementation slice — successful exact match core**.

M1.6a froze exact `CapabilityDescriptor` and `CapabilityCatalogSnapshot` semantics. M1.6b1 adds the explicit immutable relation between one exact admitted WorkStep and one exact Descriptor in one exact Catalog Snapshot.

This slice does not introduce Availability, invocation readiness, Governance, Authorization, execution, Outcome, or retry state.

```text
exact WorkPlan
    └─ selected WorkStep
          ↓
CapabilityRequirement
          ↓
exact CapabilityCatalogSnapshot
          ↓
exact CapabilityDescriptor
          ↓
CapabilityMatch
```

Core invariants:

```text
CapabilityRequirement != WorkPlan mutation
CapabilityRequirement != Authorization
catalog membership != Capability Match
Capability Match != Availability
Capability Match != invocation readiness
Capability Match != Authorization
Capability Match != execution
Capability Match != success
same capability_ref != same capability semantics
same WorkStep in another exact WorkPlan != same requirement lineage
same Descriptor in another Catalog occurrence != same match lineage
name similarity != compatibility
unavoidable descriptor effect != permission to omit the effect
possible descriptor effect != requested effect by default
```

M1.6b1 represents successful admitted matches only. Missing capability and multiple-compatible-candidate semantics remain M1.6b2.

## CapabilityRequirement

```text
CapabilityRequirement
├─ schema = irr.capability_requirement.v1
├─ work_plan
├─ step_ref
├─ primary_scope_ref
├─ requested_scopes[]
├─ requested_effects[]
├─ execution_boundary_requirements[]
└─ description
```

The complete immutable WorkPlan is embedded rather than referring only to a stable plan/step label. Changing any identity-covered part of that exact WorkPlan changes the requirement identity, even when the selected WorkStep itself is unchanged.

```text
same plan_ref != same exact WorkPlan
same step_ref != same exact work lineage
```

This preserves planning provenance; it does not create authority.

## Requested scopes

```text
CapabilityRequestedScope
├─ schema = irr.capability_requested_scope.v1
├─ scope_ref
├─ semantic_type
├─ value
└─ description
```

Every requirement has one `primary_scope_ref`. The referenced scope value must equal the selected `WorkStep.scope`, giving the frozen M1.5 generic scope a stable M1.6 matching anchor without changing `WorkStep.v1`.

Additional requested scopes may represent already-admitted destinations, repositories, recipients, accounts, output surfaces, or other bounded semantic domains.

```text
requested scope != verified resource
requested scope != reachable resource
requested scope != authorized scope
```

## Requested effects

```text
CapabilityRequestedEffect
├─ schema = irr.capability_requested_effect.v1
├─ effect_ref
├─ semantic_type
├─ requested_scope_refs[]
└─ description
```

Every referenced scope must belong to the parent requirement. Effect semantics remain open tokens rather than a universal risk taxonomy.

```text
requested effect != Authorization
effect description != safety verdict
```

The separate requirement surface is deliberate: M1.6 materializes capability-facing effect semantics beside the already-frozen M1.5 WorkStep rather than retroactively adding effect or authority fields to WorkStep wire.

## Execution-boundary requirements

```text
CapabilityExecutionBoundaryRequirement
├─ schema = irr.capability_execution_boundary_requirement.v1
├─ kind
├─ boundary_ref
└─ description
```

`kind` reuses the M1.6a roles `provider`, `executor`, `adapter`, `service`, and `other_explicit`.

A successful match must contain each explicit `(kind, boundary_ref)` requirement. An empty tuple means no boundary constraint is represented by this requirement; it does not declare all providers interchangeable.

```text
boundary requirement != Availability
boundary requirement != trust proof
boundary requirement != Authorization
```

## CapabilityMatch lineage

```text
CapabilityMatch
├─ schema = irr.capability_match.v1
├─ attribution
├─ requirement
├─ catalog_snapshot
├─ capability_ref
├─ capability_contract_identity
├─ scope_matches[]
├─ input_matches[]
├─ output_matches[]
├─ effect_matches[]
└─ description
```

The selected `capability_ref` must belong to the embedded exact Catalog Snapshot. `capability_contract_identity` must equal the canonical identity of that exact embedded Descriptor.

```text
capability_ref alone != exact contract
descriptor outside exact snapshot != valid match
later Catalog snapshot != retroactive reinterpretation
```

A changed Catalog occurrence changes Match identity even when Descriptor bytes remain unchanged.

## Match attribution

```text
CapabilityMatchAttribution
├─ schema = irr.capability_match_attribution.v1
├─ matcher_ref
└─ match_event_ref
```

Attribution records which matching boundary produced one admitted match occurrence. It is not authentication, authority, Availability, or proof that the matcher implementation was correct.

## Scope mapping

```text
CapabilityScopeMatch
├─ schema = irr.capability_scope_match.v1
├─ requested_scope_ref
└─ descriptor_scope_requirement_ref
```

M1.6b1 requires a bijection: every requested scope maps exactly once, every Descriptor `CapabilityScopeRequirement` is satisfied exactly once, and mapped semantic types are lexically equal in v1.

The Descriptor scope `statement` remains semantic text, not executable policy. Domain-specific matching logic may exist later, but the admitted relation must preserve explicit scope mapping rather than hiding the decision behind `compatible=true`.

## Input mapping

```text
CapabilityInputMatch
├─ schema = irr.capability_input_match.v1
├─ work_input_name
├─ descriptor_input_ref
└─ requested_scope_refs[]
```

Every selected WorkStep input and every Descriptor input contract must participate exactly once. Therefore a Descriptor requiring an additional input absent from the WorkStep fails closed.

Work-side semantic type is derived from `WorkLiteralInput.semantic_type` or `WorkSymbolicInput.reference.semantic_type` and must lexically equal the mapped Descriptor input semantic type in v1. Requested scope mappings must exactly cover the Descriptor input scope requirements.

```text
same primitive shape != input compatibility
unmapped required Descriptor input != compatible capability
```

## Output mapping

```text
CapabilityOutputMatch
├─ schema = irr.capability_output_match.v1
├─ work_output_name
├─ descriptor_output_ref
└─ requested_scope_refs[]
```

Every WorkStep output must map exactly once with exact v1 semantic type and scope coverage. Descriptor outputs not consumed by the WorkStep may remain unmapped.

This preserves the M0.4 distinction that returned data is not automatically plan-local semantics, Context, Observation, Outcome, Claim, Evidence, completion proof, or authority.

## Effect mapping

```text
CapabilityEffectMatch
├─ schema = irr.capability_effect_match.v1
├─ requested_effect_ref
└─ descriptor_effect_ref
```

Every requested effect must map exactly once with exact v1 semantic type and scope coverage.

Most importantly, every Descriptor effect marked `unavoidable` must be represented by a requested effect in a successful match:

```text
unavoidable descriptor effect absent from admitted work
    -> no CapabilityMatch
```

This closes effect smuggling. A locally described operation cannot silently match a Descriptor that necessarily adds an unrepresented network, disclosure, mutation, or other material effect.

A Descriptor effect marked `possible` may remain unmapped because M1.6a distinguishes the broader capability-family envelope from one requested invocation surface.

```text
possible effect != requested effect by default
unavoidable effect != optional work semantics
```

## Exact completion semantics in v1

M0.5 forbids a weaker capability result contract from silently satisfying stronger WorkStep completion semantics. M1.6b1 does not invent a hidden stronger/weaker/equivalence ontology for prose.

The v1 rule is deliberately narrow:

```text
CapabilityDescriptor.completion_contract
    ==
WorkStep.completion_contract
```

by exact lexical equality.

```text
accepted != delivered
scheduled != completed
similar wording != proven equivalent completion
```

A future named relation may broaden this only with explicit deterministic semantics.

## Exact operation semantics in v1

Descriptor and WorkStep semantic operation identifiers must be lexically equal.

```text
archive.extract == archive.extract
archive.extract != shell.execute
name similarity != compatibility
```

M1.6b1 does not lower semantic work into shell/browser commands or other implementation techniques.

## Successful Match is not candidate-selection authority

M1.6b1 represents one already admitted successful candidate relation. It does not choose among multiple compatible candidates.

```text
two compatible candidates != choose first Catalog entry
Catalog order != precedence
registration order != precedence
provider preference != admitted semantics
```

M1.6b2 owns no-match, multiple-match, material-interchangeability, and fail-closed selection/continuation semantics.

## Successful Match is not Availability

A Match does not establish provider online state, credentials, reachability, bound-resource freshness, or per-invocation readiness.

```text
CapabilityMatch != Availability
CapabilityMatch != invocation readiness
```

There is no availability boolean, health probe, lease, credential state, or retry behavior in this slice.

## Successful Match is not authority

No M1.6b1 record grants permission.

```text
CapabilityRequirement != Authorization
CapabilityMatch != Authorization
effect mapping != Authorization
scope mapping != authorized scope
provider match != authority
```

Unknown authority- or availability-like wire fields fail closed. WorkProposal / Governance / Authorization remain M1.6c.

## Canonical ordering

Set-like surfaces are canonicalized by explicit stable keys: requested scopes by `scope_ref`; requested effects by `effect_ref`; boundary requirements by `(kind, boundary_ref)`; scope matches by requested scope; input/output matches by WorkStep name; effect matches by requested effect.

Duplicate semantic keys fail closed instead of creating tuple-order precedence.

## Explicit deferrals

M1.6b1 deliberately does not introduce missing-capability results, candidate search algorithms, multiple-match selection, interchangeability rules, provider preference, Catalog widening/discovery, Capability Availability, health probes or leases, invocation readiness, concrete BoundValue revalidation algorithms, WorkProposal, Governance Decision, Authorization/Denial/require-review, CapabilityHandoff, execution, Attempt/Outcome/Continuation, retry/fallback/compensation, or persistence.

M1.6b2 owns missing/multiple capability evaluation. M1.6c owns Governance/Authorization. M1.7 owns lifecycle/recovery state.

## Acceptance

M1.6b1 is correct when tests prove at least:

```text
immutable closed records
exact WorkPlan + selected WorkStep lineage
primary requested scope == WorkStep scope
requested effect scopes -> admitted requested scopes only
exact Catalog Snapshot membership
exact Descriptor content identity
exact operation equality
scope mapping bijection
input mapping bijection + semantic/scope equality
every WorkStep output mapped
unused Descriptor output remains returned data only
all requested effects mapped
all unavoidable Descriptor effects represented
unrequested possible Descriptor effects remain possible-only
explicit execution-boundary requirements satisfied
exact lexical completion contract in v1
set-like order does not affect identity
Catalog occurrence changes Match identity
authority/availability-like unknown fields rejected
canonical round-trip preserves identity
all earlier M1 goldens remain unchanged
```
