# M1.6a — Capability Catalog / Descriptor IR

Status: **implementation slice — Capability Catalog foundation**.

M1.6a encodes the first half of the frozen M0.5 Capability boundary as immutable IR. It defines the exact capability contracts and exact attributable Catalog Snapshot against which later M1.6b matching can operate.

This slice deliberately does **not** decide whether a capability matches a WorkStep, whether it is currently available, whether an invocation is ready, or whether any work is authorized.

```text
Semantic Operation
       |
       v
CapabilityCatalogSnapshot
       |
       v
CapabilityDescriptor
       |
       +---- exact input/output contract
       +---- exact scope requirements
       +---- exact effect envelope
       +---- execution-boundary attribution
       +---- completion contract
       |
       v
future M1.6b CapabilityMatch
```

Core invariants:

```text
semantic operation != capability
same capability_ref != same capability semantics
catalog membership != Capability Match
catalog membership != Availability
Availability != invocation readiness
Capability Match != Authorization
effect metadata != permission
scope requirement != authorized scope
execution boundary identity != authority
catalog attribution != authorization
empty applicable catalog != global impossibility
```

## 1. CapabilityDescriptor

```text
CapabilityDescriptor
├─ schema = irr.capability_descriptor.v1
├─ capability_ref
├─ operation
├─ input_contracts[]
├─ output_contracts[]
├─ scope_requirements[]
├─ effects[]
├─ execution_boundaries[]
├─ completion_contract
└─ description
```

A descriptor is an immutable semantic capability contract. It is not an implementation command, executable callback, tool object, or permission grant.

`capability_ref` is a stable logical reference only. Exact descriptor identity is the SHA-256 identity of the complete canonical record.

Therefore:

```text
same capability_ref + changed contract
    ->
different CapabilityDescriptor identity
```

This is required by M0.5 and is the exact contract identity consumed conceptually by the M1.5b `DelegatedCapabilityAllowance.capability_contract_identity` field.

## 2. Semantic operation

`operation` uses the same narrow lowercase dotted semantic-identifier form used by M1.5 Work IR, for example:

```text
archive.inspect
archive.extract
filesystem.search
```

The vocabulary itself remains open. The syntax prevents implementation text such as shell commands from being represented as a semantic operation identifier.

```text
semantic operation identifier != executable command
```

M1.6a does not claim that equal operation strings imply capability compatibility. Exact compatibility belongs to M1.6b.

## 3. CapabilityScopeRequirement

```text
CapabilityScopeRequirement
├─ schema = irr.capability_scope_requirement.v1
├─ requirement_ref
├─ semantic_type
└─ statement
```

A scope requirement describes a bounded semantic scope that an invocation must provide or remain within.

It is descriptive capability semantics, not authority:

```text
scope requirement != authorized scope
capability-supported scope != requested WorkStep scope
```

The statement is identity-covered semantic material. M1.6a does not parse it as a policy language or executable predicate.

## 4. CapabilityInputContract

```text
CapabilityInputContract
├─ schema = irr.capability_input_contract.v1
├─ input_ref
├─ semantic_type
├─ scope_requirement_refs[]
└─ description
```

Input compatibility is semantic rather than based on primitive shape.

Every referenced scope requirement must exist in the parent descriptor. This prevents an input contract from silently depending on an unrepresented ambient scope rule.

```text
same primitive representation != same semantic input
input scope link != authority
```

Zero inputs are valid for capability contracts that require no represented invocation input.

## 5. CapabilityOutputContract

```text
CapabilityOutputContract
├─ schema = irr.capability_output_contract.v1
├─ output_ref
├─ semantic_type
├─ scope_requirement_refs[]
└─ description
```

Outputs describe the semantic data/result surface a capability may return. Every output scope reference must belong to the parent descriptor's admitted scope requirements, so a returned path/artifact/result cannot silently lose the bounded scope semantics of the capability contract.

Returned values do not become factual truth, Observation, Outcome, or completion evidence merely because a descriptor declares an output type.

M1.6a also carries a descriptor-level `completion_contract`, because output shape alone is insufficient to distinguish, for example:

```text
request accepted
```

from:

```text
requested operation completed
```

M1.6b must preserve this distinction when matching a WorkStep whose completion semantics require a stronger result.

## 6. CapabilityEffect

```text
CapabilityEffect
├─ schema = irr.capability_effect.v1
├─ effect_ref
├─ semantic_type
├─ requirement
│  ├─ possible
│  └─ unavoidable
├─ scope_requirement_refs[]
└─ description
```

M0.5 distinguishes a descriptor's overall effect envelope from effects that are unavoidable for an invocation. M1.6a therefore preserves whether one represented effect is merely possible within the contract or unavoidable.

This is not a risk taxonomy. `semantic_type` remains an open semantic token.

```text
possible effect != requested effect
unavoidable effect != authorization
effect metadata != safety verdict
```

Every effect scope reference must belong to the descriptor's admitted scope requirements.

Future M1.6b matching must reject a proposed WorkStep when unavoidable descriptor effects exceed or contradict the represented WorkStep semantics.

## 7. CapabilityExecutionBoundary

```text
CapabilityExecutionBoundary
├─ schema = irr.capability_execution_boundary.v1
├─ boundary_ref
├─ kind
│  ├─ provider
│  ├─ executor
│  ├─ adapter
│  ├─ service
│  └─ other_explicit
└─ description
```

Execution-boundary identity is identity-covered together with its semantic role. A bare set of refs is insufficient because the same external component can be material as a provider, executor, adapter, or service boundary and those roles must not be guessed later.

The same `boundary_ref` may appear under more than one explicit role when one component genuinely occupies multiple roles. Duplicate `(kind, boundary_ref)` pairs fail closed.

```text
execution boundary role != availability
execution boundary identity != trust proof
execution boundary identity != authorization
same operation != provider interchangeability
```

The tuple may be empty where execution-boundary identity is not material to the declared contract.

## 8. CapabilityCatalogAttribution

```text
CapabilityCatalogAttribution
├─ schema = irr.capability_catalog_attribution.v1
├─ supplier_ref
└─ snapshot_event_ref
```

This preserves who/what supplied the Catalog material and the exact supplied-snapshot occurrence.

Attribution is not authentication, completeness proof, or authority.

```text
catalog supplier != trusted supplier by definition
catalog attribution != authorization
snapshot occurrence != availability observation
```

## 9. CapabilityCatalogSnapshot

```text
CapabilityCatalogSnapshot
├─ schema = irr.capability_catalog_snapshot.v1
├─ catalog_ref
├─ attribution
├─ scope_statement
├─ descriptors[]
└─ description
```

The snapshot embeds the complete immutable descriptors rather than referring to mutable ambient registry state.

Therefore a material descriptor change changes:

```text
CapabilityDescriptor identity
CapabilityCatalogSnapshot identity
```

and cannot retroactively reinterpret older work.

`scope_statement` records the bounded planning surface represented by this snapshot. It is not global machine capability discovery.

The descriptor collection is set-like and canonicalized by `capability_ref`. Duplicate logical capability refs fail closed, so one snapshot cannot contain two competing semantic contracts under one logical ref.

An empty descriptor tuple is valid and means:

```text
no capabilities represented in this applicable snapshot
```

It does **not** mean:

```text
nothing is technically possible anywhere
```

## 10. No ambient discovery

M1.6a contains no API that scans:

- PATH;
- installed executables;
- browser automation surfaces;
- service registries;
- plugins;
- Runplane;
- Worker tools;
- operating-system conventions;
- network services.

The Host constructs or obtains the applicable Catalog outside IRR and supplies it explicitly.

```text
Catalog Snapshot != ambient discovery result owned by IRR
```

## 11. No Availability in Part A

M0.5 separates Catalog Membership, Availability, and per-invocation readiness.

M1.6a freezes only Catalog semantics.

There are intentionally no fields such as:

```text
available
online
healthy
ready
reachable
credentials_present
```

Availability may change without changing the immutable capability contract. Its later representation must therefore remain separate from `CapabilityDescriptor` identity.

## 12. No Governance or Authorization in Part A

M1.6a has no:

```text
approved
authorized
permission
safe
consented
denied
```

fields.

A valid descriptor or catalog snapshot remains proposed planning material only.

```text
known capability != authorized capability
inspectable effect metadata != permission
```

M1.6c owns WorkProposal / Governance / Authorization IR.

## 13. Canonical set-like surfaces

Where presentation order is not semantic, v1 canonicalizes by explicit stable key:

- scope requirements by `requirement_ref`;
- input contracts by `input_ref`;
- output contracts by `output_ref`;
- effects by `effect_ref`;
- execution boundaries by `(kind, namespace, value)`;
- Catalog descriptors by `capability_ref`.

Duplicate semantic keys fail closed rather than creating registration-order precedence.

```text
catalog order != capability precedence
tuple order != semantic difference
duplicate logical key != implicit override
```

## 14. Explicit deferrals

M1.6a deliberately does not introduce:

- `CapabilityMatch`;
- missing-capability evaluation;
- multiple-match selection rules;
- Capability Availability;
- invocation readiness;
- concrete WorkStep-to-Capability binding;
- WorkProposal;
- Governance Decision;
- Authorization / Denial / require-review records;
- CapabilityHandoff;
- executor invocation;
- Attempt / Outcome / Continuation;
- retry/fallback/recovery;
- runtime discovery/probing;
- persistence.

Those remain M1.6b, M1.6c, M1.7, or later runtime milestones.

## Acceptance

M1.6a is correct when executable tests prove at least:

```text
immutable closed IR records
strict wire fields
canonical round-trip determinism
set-like order independence
same capability_ref + changed semantics -> changed descriptor identity
changed descriptor -> changed catalog snapshot identity
duplicate capability_ref in one snapshot -> fail closed
input/output/effect scope links -> admitted descriptor scope requirements only
execution-boundary role is explicit and identity material
possible effect != unavoidable effect
semantic operation identifier != executable text
catalog attribution occurrence is identity material
empty applicable catalog is representable
no Availability fields
no authority fields
```
