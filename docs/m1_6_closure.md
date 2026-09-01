# M1.6 — Capability / Governance IR Closure

Status: **complete and frozen in `main`**.

M1.6 encodes the frozen M0.5 Capability boundary and M0.6 Governance / Authority boundary as explicit immutable IR without collapsing capability existence, semantic compatibility, availability, review, permission, execution, or lifecycle state.

Final M1.6 merge lineage closes at:

```text
main = 80e2e68019a3db49bf1b634d80a1a4731645ec7a
```

M1.6 is complete. The next implementation milestone is **M1.7 — Attempt / Outcome / Continuation IR**.

## 1. Closed semantic chain

```text
WorkPlan / WorkStep
        |
        v
CapabilityRequirement
        +
exact CapabilityCatalogSnapshot
        |
        v
CapabilityMatch
        |
        v
CapabilityMatchEvaluation
    0 / 1 / >1
        |
        v
WorkProposal
        |
        v
external Governance
        |
        v
GovernanceDecision
  authorize | deny | constrain | require_review
        |
        +-- authorize only --> Authorization
```

No arrow above means semantic equivalence or authority inheritance.

## 2. M1.6a — Capability Descriptor / Catalog Snapshot

M1.6a freezes exact capability contract semantics independently from one WorkStep match.

Representative top-level frozen identities:

```text
CapabilityDescriptor
65e8db5cfdcc8475f8765023e8fda873cc763d5d3c86db18862c266bac4b2e74

CapabilityCatalogSnapshot
7c0e6629db0588c1d65d0c07b653f14b232d84f0cd29bd0ca974df753b132468
```

The Descriptor preserves semantic operation, input/output contracts, scope requirements, possible/unavoidable effect envelope, role-aware execution boundaries, completion semantics, and exact content identity.

Core invariants:

```text
same capability_ref != same capability semantics
Catalog membership != Capability Match
Catalog membership != Availability
Capability effect metadata != permission
execution boundary identity != authority
```

## 3. M1.6b1 — Capability Requirement / exact Match

M1.6b1 freezes the exact relation between admitted work and one exact Descriptor in one exact Catalog Snapshot.

Representative frozen identities:

```text
CapabilityRequirement
18371a898016175121bf14ba625a8c7dc74d5e0605e7d373cd692adc78baef9f

CapabilityMatch
e9bb4ae9ca89df181c165881ca65d6acc9adc8cd75a91145992b54fd9ae7179c
```

A v1 Match is conservative and fail-closed: exact operation and completion semantics, explicit scope/input/output/effect mappings, exact Descriptor identity, and coverage of all unavoidable Descriptor effects.

```text
CapabilityMatch != selection preference
CapabilityMatch != Availability
CapabilityMatch != Authorization
CapabilityMatch != invocation
CapabilityMatch != success
```

A `CapabilityRequirement` structures already-admitted capability-facing work semantics; it is not authority to invent new scope, effects, recipient/provider meaning, or other material work semantics.

## 4. M1.6b2 — exhaustive bounded Match Evaluation

M1.6b2 freezes exhaustive evaluation relative to one exact bounded Catalog Snapshot.

Representative frozen identities:

```text
CapabilityMatchEvaluation
618042cfc221eabcef59a2f997955358111c07ea2f389b3675e35ac22d7a465b

CapabilityMatchIssue
70254c8fbdff288ca9c5a124e666bf374dac0289b1dc8d64cb0da66e0412994f
```

Every Descriptor in the exact Snapshot must be classified exactly once as compatible or incompatible. Therefore:

```text
0 compatible relations -> no compatible capability in this exact planning surface
1 compatible relation  -> exact unique match relation
>1 relations            -> material multiple-match surface
```

But:

```text
no match != impossible everywhere
no match != Governance Denial
multiple matches != permission to choose first
Catalog order != provider preference
```

Distinct occurrence wrappers of the same semantic match relation cannot fabricate multiple-match ambiguity.

## 5. M1.6c1 — authority-neutral WorkProposal

M1.6c1 freezes the exact immutable work surface that may be presented to external Governance.

Representative frozen identity:

```text
WorkProposal
6681affd3bd666e63d34a609f4750755232167f5e5a8f1d724cffaeafb4a395a
```

A proposed WorkStep embeds exact B2 evaluation and is admissible only when that evaluation has exactly one match. This prevents Governance presentation from bypassing the multiple-match boundary by manually choosing a B1 candidate.

All proposed steps in one `WorkProposal.v1` use one exact Catalog Snapshot occurrence. The proposal may cover an explicit WorkStep subset without mutating or deleting the historical WorkPlan.

Authority-relevant material may preserve affected resource, data flow, disclosure, recipient, uncertainty, or other explicit review material with provenance, but:

```text
WorkProposal != Authorization
proposal attribution != authority
authority material != permission
authority material != semantic-widening authority
material provenance != factual truth
```

## 6. M1.6c2 — Governance Decision / Authorization

M1.6c2 freezes an external Governance decision over one exact WorkProposal and the separate canonical Authorization projection.

Representative frozen identities:

```text
GovernanceDecision
40d754c9f2e1282b42659a3570fdf043098571f606de74f9cebd0bcc07edd63f

Authorization
fb2a8fd3ba1bc790a1a3e879a2e96d594430a3f31ecf07658888fc938d19d935
```

Governance components are explicit:

```text
authorize
deny
constrain
require_review
```

A decision may cover only a subset of proposal steps. Omission remains absence of an authority result:

```text
unmentioned step != denied step
unmentioned step != authorized step
absence of Authorization != Denial
```

One WorkStep may appear in at most one decision component in `GovernanceDecision.v1`. Authority-separable portions must already be explicit WorkSteps; Governance cannot silently split one WorkStep and rewrite its semantics.

Only an `authorize` component can materialize `Authorization`.

```text
Denial != Authorization
Governance Constraint != Authorization
require_review != Authorization
```

## 7. Authorization idempotence hardening

First-party review found and fixed an authority-amplification defect before wire freeze.

An early local shape gave `Authorization` an independently supplied local ID/description. That could wrap the same authorize component multiple times into distinct identities, which is unsafe for bounded conditions such as `one_use`.

The final frozen v1 shape is only:

```text
Authorization = (exact GovernanceDecision, authorize component_ref)
```

Therefore:

```text
same decision + same authorize component -> same canonical bytes
same decision + same authorize component -> same Authorization identity
re-materialization != fresh grant
re-materialization != renewed one-use authority
representation duplication != authority amplification
```

Reusable grants, leases, revocation, usage counters, separately minted authority tokens, and quorum/multi-party authority remain later explicit contracts rather than being simulated through duplicate `Authorization.v1` wrappers.

## 8. Boundary preserved for M1.7

M1.6 deliberately does not encode execution lifecycle.

```text
Authorization != Handoff
Authorization != Attempt
Authorization != Effect
Authorization != Outcome
Authorization != completion
```

Likewise:

```text
Capability Match != Availability
Authorization != Capability Availability
Governance Decision != Effect
```

M1.7 begins only after these semantics are frozen and owns attributable Attempt, scoped Outcome/evidence, recovery classification, and explicit Continuation lineage.

## 9. Verification

All completed M1.6 slices and hardening PRs passed the repository CI matrix on:

```text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

Representative wire identities were independently calculated and then checked against the project canonical encoder before merge. The full suite continued executing earlier M1 frozen goldens, so M1.6 did not silently redefine M1.1–M1.5 canonical bytes.

## 10. M1.6 closure invariants

```text
semantic operation != capability
same capability_ref != same capability semantics
Catalog membership != Match
Match != Availability
Availability != Authorization
Match != Authorization
multiple matches != hidden selection authority
WorkProposal != Authorization
Governance Constraint != Authorization
absence of Authorization != Denial
Authorization Condition != semantic work mutation
Authorization rematerialization != fresh authority
Authorization != Attempt / Effect / Outcome
```

With these boundaries frozen, **M1.6 is closed** and implementation proceeds to **M1.7 — Attempt / Outcome / Continuation IR**.
