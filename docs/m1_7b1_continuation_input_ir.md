# M1.7b1 — Continuation Input / Re-entry IR

Status: **candidate normative M1.7b1 contract**.

M1.7a1 froze immutable `CapabilityAttempt`; M1.7a2 froze immutable `CapabilityOutcome`.
M1.7b1 freezes the next boundary only: how exact downstream or blocking material may be
submitted back into IRR as an attributable semantic re-entry input.

It does **not** decide what IRR should do next.

```text
exact downstream/blocking record
            +
exact re-entry occurrence
            |
            v
    ContinuationInput
            |
            v
   later IRR resolution
```

Core invariants:

```text
ContinuationInput != Retry
ContinuationInput != fallback
ContinuationInput != successor WorkPlan
ContinuationInput != WorkPlan mutation
ContinuationInput != Authorization
ContinuationInput != Observation
ContinuationInput != parent completion
re-entry occurrence != source occurrence
re-entry submission != source truth amplification
same source re-submitted != new source semantics
```

## 1. Why this boundary exists

M0.3 and M0.4 freeze an explicit return-to-IRR model rather than hidden loops inside
`WorkPlan`.

A terminal WorkStep may say `return_to_irr`, a Worker may return material or a need,
binding may remain unresolved, capability matching may fail or remain ambiguous, and
Governance may constrain work or require review.

Those facts need a typed way to cross back into IRR without giving the downstream
component permission to mint a successor plan, retry policy, or new interpretation.

M1.7b1 therefore represents only:

> this exact already-typed material was submitted back into IRR at this exact
> attributable re-entry occurrence.

## 2. ContinuationInputAttribution

```text
ContinuationInputAttribution
├─ schema = irr.continuation_input_attribution.v1
├─ submitter_ref
└─ reentry_event_ref
```

`submitter_ref` attributes the component/Host boundary that submitted the source back to
IRR. It is not authentication, authority, or proof that the source is true.

`reentry_event_ref` is the occurrence of re-entry itself.

The re-entry occurrence must differ from the source occurrence.

```text
source occurrence != re-entry occurrence
```

This preserves the distinction between:

```text
executor produced Outcome
Host submitted Outcome back to IRR
```

or:

```text
Governance produced constraint
Host submitted that exact constraint back to IRR
```

## 3. Closed source set

M1.7b1 admits exactly these source kinds:

```text
capability_outcome
worker_result
binding_issue
capability_match_issue
governance_constraint
governance_require_review
```

The source itself is embedded as the exact frozen IR record.

There is no generic:

```text
record_identity
json_blob
message
text
reason
status
```

escape hatch.

An arbitrary record cannot be relabeled as continuation material.

## 4. CapabilityOutcome re-entry

A `CapabilityOutcome` may re-enter IRR regardless of whether its completion/effect
assessment is known, unknown, satisfied, not satisfied, normal, or interrupted.

M1.7b1 does not infer next action from those dimensions.

```text
Outcome satisfied -> ContinuationInput, not automatic parent completion
Outcome unknown   -> ContinuationInput, not automatic retry
Outcome interrupted -> ContinuationInput, not automatic failure
```

The exact Attempt, Capability Match, concrete bindings, Authorization lineage if any,
Outcome evidence, and effect certainty remain transitively embedded.

## 5. WorkerResult re-entry

`WorkerResult` is admitted directly as exact Worker lifecycle material.

This preserves:

- exact `DelegatedWorkHandoff`;
- worker attribution;
- returned materials;
- explicit `WorkerNeed` values;
- delegated scopes;
- expected deliverables;
- original ResolvedIntent lineage.

M1.7b1 does not interpret:

```text
WorkerResult has deliverable -> parent complete
WorkerResult has WorkerNeed  -> automatically satisfy need
WorkerResult has no need     -> success
```

Those are later IRR decisions.

## 6. BindingIssue re-entry

An unresolved `BindingIssue` can re-enter IRR exactly as produced by mechanical binding
evaluation.

The exact `BindingRule`, candidate input set, issue kind, source/provenance constraints,
and selection scope remain embedded.

M1.7b1 does not turn:

```text
zero_matches
multiple_matches
tie
missing_required_data
incompatible_input
```

into hidden fallback rules.

A successor resolution may later request information, clarification, new binding input,
or different admitted semantics, but B1 does not choose among them.

## 7. CapabilityMatchIssue re-entry

`CapabilityMatchIssue` may re-enter IRR for:

```text
no_compatible_capability
multiple_compatible_matches
```

The exact Capability requirement and exact Catalog evaluation remain embedded.

M1.7b1 does not choose a provider, synthesize a capability, call a shell fallback, or
modify the requirement.

```text
missing capability != retry
multiple matches != choose first
Catalog order != precedence
```

## 8. GovernanceContinuationMaterial

Governance needs one additional selector because a single `GovernanceDecision` may
contain multiple non-overlapping decision components.

```text
GovernanceContinuationMaterial
├─ schema = irr.governance_continuation_material.v1
├─ exact GovernanceDecision
└─ exact component_ref
```

The selected component must exist in that exact decision and must be one of:

```text
constrain
require_review
```

`authorize` and `deny` are deliberately not admitted as B1 Governance continuation
material.

### Why `authorize` is excluded

Authorization already has its own M1.6 projection. Re-entry must not create a second
permission path or treat permission as a request to reinterpret work.

```text
Authorization != ContinuationInput trigger
```

### Why `deny` is excluded

A Denial may block work, but M1.7b1 does not freeze the broader blocked-without-attempt
or user-renegotiation lifecycle. Automatically turning every Denial into semantic
re-planning would make Governance a hidden planner.

A later explicit blocked/continuation contract may add such semantics if needed.

## 9. Governance constraint

A `constrain` component is valid re-entry material because M0.6 explicitly forbids
silently editing the old WorkPlan when Governance changes permitted semantics.

```text
old WorkPlan
   +
Governance constraint
   |
   v
ContinuationInput
```

Only a later successor-resolution boundary may produce changed work.

```text
constraint != mutated old WorkPlan
constraint != successor WorkPlan by itself
```

## 10. Governance require-review

A `require_review` component is also valid re-entry material.

It preserves exact directives and proposal lineage but grants no review result and no
authority.

```text
require_review != approval
require_review != denial
require_review != clarification answer
```

M1.7b1 does not open a UI, ask a person, or acquire approval. It records only that this
exact Governance requirement returned to IRR.

## 11. source_kind is mechanical

`ContinuationInput.source_kind` is not a free label.

It must agree exactly with the runtime source type.

For Governance material it is additionally derived from the selected decision component:

```text
constrain       -> governance_constraint
require_review  -> governance_require_review
```

Therefore:

```text
BindingIssue + source_kind=worker_result -> invalid
constraint component + governance_require_review -> invalid
```

This prevents semantic relabeling at re-entry.

## 12. No free lineage identifiers

`ContinuationInput` contains no independently supplied:

```text
resolved_intent_identity
work_plan_identity
attempt_identity
outcome_identity
worker_handoff_identity
governance_identity
```

The source record already carries its exact lineage transitively.

The original ResolvedIntent identity is exposed only as a derived property.

This prevents callers from taking source material from Intent A and independently
claiming it belongs to Intent B.

## 13. source_identity is derived

`ContinuationInput.source_identity` is derived from the embedded exact source.

It is not a caller-supplied field.

For Governance continuation, the source identity is the
`GovernanceContinuationMaterial` identity, which itself closes over the exact decision
and selected component.

```text
same source bytes -> same source identity
different Governance component -> different source identity
```

## 14. Re-submission is not semantic amplification

The same exact source may be submitted more than once under different re-entry events.

That produces distinct `ContinuationInput` occurrence identities while preserving one
source identity.

```text
source S + re-entry event A -> ContinuationInput A
source S + re-entry event B -> ContinuationInput B

A.identity != B.identity
A.source_identity == B.source_identity
```

A later layer must not interpret repeated submission as:

```text
two Outcomes
two grants
two effects
two retries
```

B1 records occurrence provenance only.

## 15. Continuation is not Observation

M1.7b1 does not admit generic Observation records and does not automatically convert
Outcome/Worker material into reusable ambient context.

```text
ContinuationInput != Observation
WorkerResult material != Context EvidenceRecord by default
CapabilityOutcome evidence != ambient current-world truth
```

If new world-state evidence is required, the applicable Host/Context boundary must
classify and admit it explicitly.

## 16. Continuation is not Retry

There is no:

```text
retry
retryable
safe_to_retry
attempt_number
fallback
fallback_provider
idempotency_key
replay
```

field in B1.

M0.9 remains intact:

```text
unknown effectful Outcome != automatic retry
failed completion != automatic retry
missing capability != automatic fallback
```

Retry policy and execution recovery remain later runtime work.

## 17. Continuation is not successor work

There is no embedded:

```text
ResolvedIntent
WorkPlan
WorkStep
WorkProposal
CandidateResolution
successor_plan_ref
```

created by `ContinuationInput`.

The old source history is immutable.

M1.7b2 may later freeze an explicit successor semantic lineage that consumes one or more
B1 inputs without mutating the predecessor records.

## 18. Continuation is not parent completion

A child WorkStep or delegated Worker result cannot mark the parent Intent complete
through this schema.

There is no:

```text
parent_complete
intent_satisfied
plan_complete
```

field.

Parent aggregation remains a later explicit boundary.

## 19. No hidden acquisition or effects

Constructing or decoding B1 records performs no:

- retrieval;
- capability invocation;
- status query;
- user prompt;
- Governance call;
- worker call;
- network access;
- filesystem access;
- scheduling;
- persistence;
- external effect.

All input records must already exist.

## 20. Canonical identity

All new records are immutable and exact-key decoded.

`ContinuationInput` identity closes over:

- exact submitter attribution;
- exact re-entry occurrence;
- exact mechanical source kind;
- complete exact source record.

It contains no descriptive free text.

Therefore one exact source submitted at one exact re-entry occurrence has one canonical
semantic representation in B1.

## 21. Explicit deferrals

M1.7b1 intentionally does not freeze:

- successor `ResolvedIntent` lineage;
- successor `WorkPlan` lineage;
- combination of multiple continuation inputs into one successor decision;
- blocked-without-attempt state;
- Denial re-planning semantics;
- Retry Eligibility;
- retry/fallback algorithms;
- idempotency / duplicate suppression;
- cancellation;
- compensation;
- Observation admission;
- parent WorkPlan completion;
- parent Intent satisfaction;
- worker-specific Outcome beyond existing `WorkerResult`;
- capability Availability/readiness;
- persistence/event sourcing;
- scheduling;
- transport.

## 22. Acceptance criteria

M1.7b1 is acceptable only if tests prove at least:

1. all six admitted source kinds round-trip canonically;
2. source kind is mechanically tied to exact source type;
3. arbitrary records cannot be smuggled through a generic continuation envelope;
4. re-entry occurrence differs from source occurrence;
5. original ResolvedIntent lineage is derived from the exact source;
6. source identity is derived rather than caller supplied;
7. Governance selector refers to an exact component in the exact decision;
8. only Governance `constrain` and `require_review` are admitted;
9. `authorize` cannot become a continuation permission path;
10. `deny` is not silently converted into automatic re-planning;
11. constraint cannot masquerade as require-review;
12. no retry/fallback/successor/authority/parent-completion fields exist;
13. same source under a new re-entry event preserves source identity while changing
    continuation occurrence identity;
14. unknown fields fail closed;
15. new public record types are closed against subclassing;
16. all earlier M1 goldens remain unchanged;
17. Python 3.11–3.14 CI passes;
18. representative canonical identities are independently calculated and frozen before
    merge.
