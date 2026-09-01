# M1.6b2 — Capability Match Evaluation / Cardinality IR

Status: **implementation slice — exhaustive bounded match evaluation**.

M1.6b1 froze one successful exact `CapabilityMatch`. M1.6b2 freezes the bounded evaluation surface required to state, without hidden Catalog widening or provider preference, whether the exact applicable Catalog Snapshot contains zero, one, or multiple admitted match relations for one exact `CapabilityRequirement`.

This slice deliberately does **not** add Availability, invocation readiness, Governance, Authorization, execution, Outcome, retry, fallback, or generic Continuation state.

```text
CapabilityRequirement
        +
exact CapabilityCatalogSnapshot
        |
        v
CapabilityMatchEvaluation
  ├─ compatible_matches[]
  └─ incompatible_assessments[]
        |
        +--> exactly 1 -> exact CapabilityMatch
        +--> 0         -> CapabilityMatchIssue(no_compatible_capability)
        `--> >1        -> CapabilityMatchIssue(multiple_compatible_matches)
```

Core invariants:

```text
empty compatible set != global impossibility
Catalog omission != Governance denial
incompatible assessment != proof of impossibility everywhere
evaluation attribution != truth amplification
every exact Catalog Descriptor -> classified on exactly one side
same semantic match relation under another occurrence != new alternative
multiple distinct match relations != permission for hidden selection
Catalog order != precedence
provider preference != admitted selection rule
CapabilityMatchIssue != Continuation
CapabilityMatchIssue != Authorization
```

## 1. Structural completeness relative to one exact Catalog

A plain empty tuple of matches does not establish that no compatible Capability exists; a matcher may simply have stopped early.

M1.6b2 therefore requires every Descriptor in the embedded exact `CapabilityCatalogSnapshot` to be classified on exactly one side:

- at least one exact B1 `CapabilityMatch`; or
- one explicit `CapabilityIncompatibleDescriptorAssessment`.

The compatible and incompatible Descriptor-ref sets must be disjoint and their union must equal the exact Descriptor set of the Catalog Snapshot.

This is structural completeness **relative to that exact supplied planning surface**. It is not a claim that the Catalog is a global inventory of every technically possible capability.

```text
complete evaluation of exact Catalog Snapshot
    !=
complete inventory of all possible capabilities
```

An empty Catalog is valid and admits an evaluation with both collections empty.

## 2. Evaluation attribution

```text
CapabilityMatchEvaluationAttribution
├─ schema = irr.capability_match_evaluation_attribution.v1
├─ evaluator_ref
└─ evaluation_event_ref
```

Attribution preserves which evaluation boundary produced one occurrence. It does not authenticate the evaluator, amplify truth, prove external completeness, or grant authority.

```text
evaluation attribution != proof
evaluation attribution != Authorization
```

## 3. Incompatible Descriptor assessment

```text
CapabilityMismatchReason
├─ schema = irr.capability_mismatch_reason.v1
├─ kind
│  ├─ operation_mismatch
│  ├─ scope_mismatch
│  ├─ input_mismatch
│  ├─ output_mismatch
│  ├─ unavoidable_effect_mismatch
│  ├─ completion_mismatch
│  ├─ execution_boundary_mismatch
│  ├─ insufficient_semantics
│  └─ mapping_ambiguity
├─ scope
└─ description

CapabilityIncompatibleDescriptorAssessment
├─ schema = irr.capability_incompatible_descriptor_assessment.v1
├─ capability_ref
├─ capability_contract_identity
└─ reasons[]
```

The parent evaluation verifies that the logical ref belongs to the exact Catalog Snapshot and that `capability_contract_identity` equals the exact embedded Descriptor identity.

Mismatch reasons are attributable assessment material, not global impossibility proofs, Availability observations, or Governance decisions.

```text
Descriptor mismatch in exact evaluation != impossible everywhere
mismatch reason != Governance Decision
mismatch reason != Availability
```

There are intentionally no `unavailable`, `unauthorized`, `unsafe`, or `denied` mismatch kinds.

## 4. CapabilityMatchEvaluation

```text
CapabilityMatchEvaluation
├─ schema = irr.capability_match_evaluation.v1
├─ attribution
├─ requirement
├─ catalog_snapshot
├─ compatible_matches[]
├─ incompatible_assessments[]
└─ description
```

Every compatible B1 match must embed the exact same Requirement and exact same Catalog Snapshot as the evaluation.

Every Descriptor must be represented on the compatible side or incompatible side, never both.

A `no_compatible_capability` result therefore means:

```text
no admitted compatible relation exists in this exact bounded evaluation
```

not:

```text
nothing can perform this work anywhere
```

IRR MUST NOT widen the Catalog to PATH, shell commands, browser surfaces, internet services, plugins, or another runtime merely because this exact evaluation has no match.

## 5. Match occurrence is not a semantic alternative

A B1 `CapabilityMatch` carries occurrence attribution and human description. Two records can therefore differ in record identity while expressing the same semantic relation.

M1.6b2 rejects duplicate semantic relations under different occurrence attribution or description instead of counting them as multiple alternatives.

The semantic relation key is formed by:

- exact capability ref;
- exact capability contract identity;
- scope mappings;
- input mappings;
- output mappings;
- effect mappings.

Requirement and Catalog are already fixed by the parent evaluation.

```text
same semantic relation + another match event != second alternative
```

Genuinely different Descriptor contracts or genuinely different mappings remain distinct relations.

## 6. CapabilityMatchIssue

```text
CapabilityMatchIssue
├─ schema = irr.capability_match_issue.v1
├─ evaluation
└─ kind
   ├─ no_compatible_capability
   └─ multiple_compatible_matches
```

The issue wire contains no preferred candidate, fallback command, authority decision, or human prose field.

Cardinality is closed:

```text
no_compatible_capability <=> zero compatible match relations
multiple_compatible_matches <=> at least two distinct match relations
```

A `CapabilityMatchIssue` is not generic Continuation and does not mutate the WorkPlan.

```text
CapabilityMatchIssue != Continuation
CapabilityMatchIssue != WorkPlan mutation
CapabilityMatchIssue != Authorization
```

## 7. Effect-free cardinality classification

`evaluate_capability_match_evaluation()` is purely mechanical:

```text
0 matches  -> CapabilityMatchIssue(no_compatible_capability)
1 match    -> that exact CapabilityMatch
>1 matches -> CapabilityMatchIssue(multiple_compatible_matches)
```

It does not search outside the Catalog, discover capabilities, inspect Availability, prefer a provider, invoke Governance, execute anything, retry, or mutate work semantics.

## 8. Multiple matches fail closed in v1

M0.5 permits a future bounded selection rule if multiple candidates are already proven semantically interchangeable under admitted semantics.

M1.6b2 v1 intentionally freezes no such rule.

Therefore every set with more than one distinct admitted match relation produces `multiple_compatible_matches`.

```text
apparent interchangeability != frozen proof of interchangeability
multiple matches != choose first
Catalog order != precedence
registration order != precedence
canonical identity order != precedence
```

A future named deterministic interchangeability/selection rule may broaden this boundary separately.

## 9. No Availability or authority leakage

M1.6b2 adds no fields for online state, health, reachability, credentials, availability, readiness, approval, authorization, denial, or safety.

```text
compatible != available
available != authorized
```

No-match is not denial. Multiple-match is not approval to choose.

## 10. Canonical ordering

Set-like surfaces are canonicalized:

- compatible matches by exact match identity after duplicate semantic-relation rejection;
- incompatible assessments by `capability_ref`;
- mismatch reasons by `(kind, scope, description)`.

Presentation order cannot become precedence.

## 11. Explicit deferrals

M1.6b2 deliberately does not introduce automatic Descriptor-to-Requirement mapping generation, semantic-interchangeability declarations, automatic candidate selection, provider preference, Catalog widening/discovery, Capability Availability/health, invocation readiness, WorkProposal, Governance Decision, Authorization/Denial/require-review, executable Capability handoff, Attempt/Outcome/generic Continuation, retry/fallback/compensation, or persistence.

M1.6c owns WorkProposal / Governance / Authorization. M1.7 owns lifecycle state.

## Acceptance

M1.6b2 is correct when tests prove at least:

```text
every exact Catalog Descriptor is classified compatible or incompatible, never both
incompatible assessment pins exact Descriptor identity
empty exact Catalog -> bounded no-compatible-capability issue
one compatible relation -> exact CapabilityMatch
multiple distinct relations -> multiple-compatible-matches issue
Catalog order and tuple order do not choose a winner
duplicate occurrence of same semantic match relation fails closed
foreign Requirement/Catalog match cannot enter evaluation
issue cardinality is structurally closed
unknown authority/availability fields fail closed
canonical round-trip preserves identity
records are immutable/slotted/sealed
all earlier M1 goldens remain unchanged
```
