# M3.0.5 — Capability Match Evaluation Admission Prerequisite

Status: proposed additive IRR prerequisite for HDE M33.2.

Exact base:

```text
intent-resolution-runtime/main@0abb4f35d8b4424a2256bf21bbe279a1720430f9
```

## 1. Why this prerequisite exists

IRR already has canonical records for:

```text
CapabilityCatalogSnapshot
CapabilityDescriptor
CapabilityRequirement
CapabilityMatch
CapabilityMatchEvaluation
CapabilityMatchIssue
```

and already exposes:

```text
evaluate_capability_match_evaluation(evaluation)
    -> CapabilityMatch | CapabilityMatchIssue
```

But that evaluator only classifies the cardinality of an already-constructed exhaustive
`CapabilityMatchEvaluation`:

```text
1 compatible match  -> CapabilityMatch
0 compatible matches -> NO_COMPATIBLE_CAPABILITY
2+ compatible matches -> MULTIPLE_COMPATIBLE_MATCHES
```

It does not itself prove how each descriptor became compatible or incompatible.

`CapabilityMatchEvaluation` validates important structural invariants:

- every exact Catalog Snapshot descriptor is assessed once;
- a descriptor cannot be both compatible and incompatible;
- compatible `CapabilityMatch` records preserve exact requirement/catalog lineage;
- incompatible assessments pin exact descriptor identity;
- compatible match mappings must satisfy the canonical match contracts.

However, construction of the evaluation is still not semantic admission. In particular,
an incompatible assessment contains an explicit evaluator-authored mismatch reason.

Therefore the unsafe shortcut would be:

```text
provider / Host constructs CapabilityMatchEvaluation
        ↓
M2.3 treats it as active evaluation
```

That would make construction equivalent to semantic authority.

M3.0.5 inserts an explicit admission boundary.

## 2. Boundary

```text
exact CapabilityRequirement
+ exact CapabilityCatalogSnapshot
+ CandidateCapabilityMatchEvaluation[]
        ↓
CapabilityMatchEvaluationAdmissionFrontier
        ↓
explicit CapabilityMatchEvaluationAdmitter
        ↓
AdmittedCapabilityMatchEvaluation
        ↓
STOP
```

Public records:

```text
CandidateCapabilityMatchEvaluation
CapabilityMatchEvaluationAdmissionAttribution
AdmittedCapabilityMatchEvaluation
CapabilityMatchEvaluationAdmissionFrontier
CapabilityMatchEvaluationAdmissionFrontierKind
```

Public orchestrator:

```text
orchestrate_capability_match_evaluation_admission(...)
```

## 3. Evaluation occurrence is evidence, not authority

`CapabilityMatchEvaluation` already contains:

```text
CapabilityMatchEvaluationAttribution(
    evaluator_ref,
    evaluation_event_ref,
)
```

Therefore M3.0.5 does not add a second redundant proposal-attribution record.

`CandidateCapabilityMatchEvaluation` wraps the exact evaluation plus rationale and marks it
as proposal/evidence material only.

Frozen:

```text
CapabilityMatchEvaluation construction != admission
Evaluator attribution != admission authority
CandidateCapabilityMatchEvaluation != active evaluation
provider count != semantic authority
```

## 4. Semantic agreement ignores occurrence metadata

Two evaluator occurrences may produce the same semantic assessment while carrying
different:

- evaluator refs;
- evaluation event refs;
- match occurrence attribution;
- human-readable evaluation/match descriptions.

Those differences must not manufacture adjudication or votes.

M3.0.5 compares candidate evaluation semantics using:

- exact requirement identity;
- exact catalog snapshot identity;
- compatible capability refs and exact descriptor identities;
- exact scope/input/output/effect match mappings;
- exact incompatible descriptor identities and mismatch reasons.

It excludes occurrence attribution and presentation description from the semantic key.

Thus:

```text
same semantic assessment from many evaluators
!= majority vote
!= multiple independent decisions
```

and remains:

```text
ADMISSION_REQUIRED
```

Materially different compatible/incompatible assessments become:

```text
ADJUDICATION_REQUIRED
```

## 5. Explicit admission

Only an explicit admitter plus exact
`CapabilityMatchEvaluationAdmissionAttribution` may produce:

```text
AdmittedCapabilityMatchEvaluation
```

The admitter may:

- admit one candidate evaluation;
- adjudicate among conflicting candidate evaluations;
- synthesize an evaluation even when no provider candidate exists.

But the admitted record must preserve the complete supplied candidate set exactly.

Frozen:

```text
admitter may adjudicate semantics
!= candidate selection by ordering
!= provider voting
```

## 6. Replay

A canonical admitted output may be replayed without invoking a new admitter.

Replay may supply no candidate material or a subset of the admitted provenance. The
frontier restores the complete exact candidate provenance from the admitted output.

Candidate material not present in admitted provenance is rejected as orphaned.

Frozen:

```text
semantic replay != new admission
replay != new evaluator invocation
restart != permission to reconsider match semantics
```

## 7. What admission does not mean

An admitted exhaustive evaluation is active semantic match evidence. It is not capability
selection and it does not establish runtime availability/readiness.

```text
AdmittedCapabilityMatchEvaluation != selected capability
CapabilityMatch != selected capability
CapabilityCatalogSnapshot != live availability
CapabilityDescriptor presence != readiness
CapabilityMatch != Authorization
CapabilityMatchIssue != recovery authority
```

`NO_COMPATIBLE_CAPABILITY` remains bounded to the exact supplied Catalog Snapshot. It does
not establish global impossibility.

`MULTIPLE_COMPATIBLE_MATCHES` remains explicit ambiguity. It does not grant permission to
choose by catalog order, tuple order, provider preference, or hidden ranking.

## 8. Non-goals

M3.0.5 performs no:

- capability catalog discovery;
- plugin registration;
- live availability/readiness probing;
- automatic generation of `CapabilityMatchEvaluation` from descriptors;
- hidden capability selection;
- `WorkProposal` synthesis;
- Governance;
- Authorization;
- worker delegation;
- Attempt or executor invocation;
- external effect;
- retry, fallback, or recovery.

## 9. HDE M33.2 after this prerequisite

After M3.0.5 closes, HDE may safely bridge:

```text
M33.1 exact active CapabilityRequirement
+ explicit CapabilityCatalogSnapshot
+ explicit CandidateCapabilityMatchEvaluation[]
        ↓
IRR M3.0.5 admission
        ↓
AdmittedCapabilityMatchEvaluation
        ↓
IRR M2.3 evaluation projection
        ↓
CapabilityMatch | CapabilityMatchIssue
        ↓
STOP before WorkProposal
```

This keeps the capability pipeline separated as:

```text
requirement
!= evaluation proposal
!= admitted evaluation
!= match result
!= capability selection
!= WorkProposal
!= Authorization
!= execution
```
