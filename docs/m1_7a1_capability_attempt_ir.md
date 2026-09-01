# M1.7a1 — Capability Attempt IR

Status: **candidate normative M1.7a1 contract**.

M1.6 froze exact Capability, WorkProposal, Governance Decision, and Authorization semantics. M1.7 begins the downstream lifecycle without reopening any of those boundaries.

M1.7a1 freezes only one thing: an immutable attributable record that **one concrete effort to invoke one exact uniquely matched capability-backed WorkStep occurred**.

It does **not** freeze Outcome, success/failure, blocking, interruption, unknown-outcome classification, retry/fallback eligibility, Continuation, execution scheduling, or persistence.

```text
exact WorkStep
    +
exact unique CapabilityMatchEvaluation
    +
exact concrete late-bound symbolic inputs
    +
optional presented Authorization lineage
    +
attempt occurrence / executor attribution
    |
    v
CapabilityAttempt
```

Core invariants:

```text
Attempt != Outcome
Attempt != Effect
Attempt != success
Attempt != failure
Attempt != Authorization
presented Authorization != proof conditions were satisfied
absence of Authorization != proof no Attempt occurred
Attempt N != Attempt N+1
Retry != mutation of Attempt N
attempt order != attempt number field
WorkProposal != universal prerequisite for capability execution
CapabilityMatch != Attempt
Binding success != Attempt
```

## 1. Why Attempt is separate from Outcome

An Attempt is historical lifecycle provenance: one bounded effort occurred.

Outcome is later attributable interpretation/evidence about what that effort achieved or may have affected.

M0.9 explicitly permits later evidence to refine an earlier unknown result while preserving what was knowable at the earlier time. Therefore M1.7 must not model execution as one mutable record whose `status` is rewritten in place.

```text
Attempt occurrence = immutable history
Outcome evidence/classification = separate later record
```

A retry or executed fallback will later create another Attempt. It never edits this Attempt into a second execution.

## 2. CapabilityAttemptAttribution

```text
CapabilityAttemptAttribution
├─ schema = irr.capability_attempt_attribution.v1
├─ executor_ref
└─ attempt_event_ref
```

`executor_ref` is attribution for the actual downstream executor/component associated with this occurrence. It does not prove identity, trust, capability compatibility, authority, or correct routing.

`attempt_event_ref` distinguishes two separate efforts over otherwise identical work.

```text
same work + different attempt_event_ref -> different Attempt identity
executor attribution != authorization
executor attribution != success
```

M1.7a1 does not introduce `attempt_number`. Global or per-work ordinal numbering requires persistence/concurrency semantics that are not frozen here.

## 3. Exact capability relation, without universal Governance

A `CapabilityAttempt` embeds one exact `CapabilityMatchEvaluation` and requires that the effect-free M1.6b2 classifier return exactly one `CapabilityMatch`.

This preserves:

- exact WorkPlan / WorkStep lineage;
- exact CapabilityRequirement;
- exact Catalog Snapshot occurrence;
- exact Descriptor contract identity;
- exact scope/input/output/effect mapping.

The Attempt does **not** embed `WorkProposal` as a universal prerequisite.

That is deliberate. M0.6 does not require every authority-neutral operation to pass through Governance. Requiring `WorkProposal` for every capability invocation would silently turn M1.6c into a mandatory global sequence.

```text
unique Capability Match -> may be attemptable subject to later/runtime boundaries
unique Capability Match != WorkProposal required by definition
unique Capability Match != Authorization
```

When Authorization is actually presented, that Authorization embeds its exact WorkProposal/Governance lineage and M1.7a1 verifies that it refers to this exact capability evaluation and WorkStep.

## 4. Capability cardinality remains closed

A no-match or multiple-match evaluation cannot become a CapabilityAttempt by choosing a candidate locally.

```text
0 matches -> no CapabilityAttempt from that evaluation
>1 match relations -> no CapabilityAttempt from that evaluation
1 exact match -> eligible for Attempt representation
```

This preserves M1.6b2 and prevents execution from becoming a hidden provider-selection layer.

## 5. AttemptBoundInput

```text
AttemptBoundInput
├─ schema = irr.attempt_bound_input.v1
├─ input_name
└─ bound_value
```

This record freezes the exact `BoundValue` actually used for one named symbolic WorkStep input at this Attempt.

Literal WorkStep inputs are already concrete and identity-covered in the exact WorkStep; they are not redundantly copied into `bound_inputs`.

Every `WorkSymbolicInput` must be covered exactly once before `CapabilityAttempt` can be constructed.

```text
symbolic input without BoundValue -> no CapabilityAttempt
extra bound input name -> invalid
BoundValue for another SymbolicReference -> invalid
```

This matters for recovery. Two Attempts over the same WorkStep can use materially different concrete resources after rebinding. M1.7 must preserve that difference rather than pretending both attempts were identical because their symbolic WorkPlan was unchanged.

## 6. Exact BoundValue lineage

For every symbolic input:

```text
BoundValue.rule.symbolic_reference
    ==
WorkSymbolicInput.reference
```

and semantic type must remain equal.

The entire exact BoundValue is embedded, including BindingRule, candidate BindingInputs, selected input identity, selection scope, concrete value, and concrete value scope.

Therefore:

```text
same symbolic WorkStep + different BoundValue -> different Attempt identity
rebound resource != same concrete Attempt semantics
```

M1.7a1 does not claim the BoundValue is still fresh/current. Freshness or revalidation before another Attempt remains a later runtime/recovery responsibility.

## 7. Attempt and Binding occurrences are distinct

The Attempt event cannot equal the Binding event used to produce one of its BoundValues.

```text
Binding occurrence != Attempt occurrence
```

Binding determines an admitted value. Attempt is a later downstream effort using that value.

Likewise, the Attempt occurrence must differ from the exact CapabilityMatchEvaluation occurrence.

## 8. Authorization is optional in the historical record

`presented_authorizations` may be empty.

This is required for two reasons:

1. some bounded operations may not require external authority under their applicable boundary;
2. IRR must be able to represent an observed historical Attempt that occurred without sufficient Authorization rather than making unauthorized execution literally unrepresentable.

```text
CapabilityAttempt existence != proof of Authorization
no presented Authorization != proof Attempt did not occur
```

M1.7a1 is an immutable lifecycle record, not a constructor that certifies normative execution correctness.

## 9. Presented Authorization lineage

M1.7a1 supports at most one `Authorization.v1` record per CapabilityAttempt.

This follows M1.6c2, which explicitly deferred quorum, multi-party authority composition, leases, reusable grants, revocation, and independently minted authority tokens.

If Authorization is presented:

- its exact WorkProposal must include the attempted WorkStep;
- that `ProposedWorkStep.capability_evaluation` must exactly equal the Attempt's `CapabilityMatchEvaluation`;
- the authorize component must cover this exact WorkStep;
- Attempt, WorkProposal, and GovernanceDecision occurrences must remain distinct.

This prevents authority approved for another proposal/evaluation from being attached to a materially different invocation lineage.

## 10. Presented Authorization is not applicability proof

M1.7a1 deliberately names the field `presented_authorizations`, not `valid_authorizations` or `applicable_authorizations`.

Construction proves only exact structural lineage and authorize-component coverage.

It does **not** prove:

- a time/session condition is currently satisfied;
- a one-use condition has not already been consumed;
- revocation did not occur in some later authority-state model;
- identity authentication succeeded;
- an external policy engine was correct;
- the attempt was otherwise permitted to proceed.

```text
Authorization attached != all Authorization Conditions satisfied
Authorization attached != compliant execution proof
```

Condition evaluation / authority-consumption state is not smuggled into the Attempt schema.

## 11. Actual executor attribution may disagree with expected boundaries

`executor_ref` records actual attempt attribution. M1.7a1 does not mechanically reject it merely because it differs from a Descriptor execution-boundary ref.

That is intentional for historical representability: an incorrectly routed or substituted execution attempt must still be recordable.

The exact CapabilityMatch still preserves the expected/admitted Descriptor execution-boundary semantics. A mismatch can therefore remain inspectable instead of making the historical event impossible to encode.

```text
actual executor attribution != automatic Capability Match rewrite
unexpected executor != hidden fallback admission
```

A future runtime gate should prevent invalid substitution before execution; M1.7a1 records what occurred.

## 12. No Outcome fields

The following are intentionally absent from `CapabilityAttempt.v1`:

```text
status
succeeded
failed
blocked
interrupted
unknown_outcome
completion_satisfied
effect_occurred
partial_effects
outcome_ref
```

Adding any unknown field during deserialization fails closed.

A downstream response, timeout, ACK loss, process exit, Worker message, receipt, or Observation must enter through later Outcome/evidence semantics rather than mutating Attempt.

## 13. No Retry / fallback fields

The following are also absent:

```text
retry
attempt_number
predecessor_attempt
fallback_from
retry_eligible
idempotent
safe_to_replay
```

M0.9 defines Retry as a **new Attempt over unchanged admitted material semantics** under an explicit safe basis. The relation between Attempt N and Attempt N+1 belongs to later recovery/Continuation IR.

```text
new attempt occurrence != implicit retry
same WorkStep attempted twice != retry eligibility proof
```

## 14. Pre-attempt blockers do not create fake Attempts

`missing_capability`, Capability unavailability, invocation unreadiness, insufficient authority, Denial, `require_review`, unresolved ambiguity, or missing information may block work before an execution attempt begins.

M1.7a1 does not manufacture a `CapabilityAttempt` merely to attach `blocked` to it.

```text
blocked before execution -> no fake CapabilityAttempt required
missing_capability != failed Attempt
Denial != Outcome
require_review != Outcome
```

A later M1.7 slice may represent blocked lifecycle/recovery state separately.

## 15. Canonical ordering and identity

Set-like surfaces are canonicalized:

```text
bound_inputs -> input_name
presented_authorizations -> Authorization identity
```

`presented_authorizations` is currently cardinality 0..1, but canonical handling remains explicit.

`CapabilityAttempt` identity covers at least:

- executor attribution;
- exact attempt occurrence;
- exact unique CapabilityMatchEvaluation;
- exact WorkStep lineage through that evaluation;
- all concrete BoundValues used for symbolic inputs;
- presented Authorization lineage when present;
- description.

Therefore:

```text
new attempt event -> new identity
changed BoundValue -> new identity
changed Catalog/Descriptor/Match relation -> new identity
changed presented Authorization -> new identity
```

## 16. Attempt description is not execution evidence

`description` is identity-covered inspectable text only.

It is not:

- Outcome evidence;
- success assertion;
- authority;
- capability compatibility proof;
- retry basis.

## 17. Relationship to Worker attempts

M1.7a1 intentionally names the record `CapabilityAttempt`, not generic `Attempt`.

Worker/DelegatedWork lifecycle attempts have different lineage and may need a separate representation. M1.7 should not force a Worker subordinate lifecycle into a capability invocation schema just to obtain one universal DTO.

Later M1.7 slices may introduce additional attempt scopes while preserving the shared M0.9 invariants.

## 18. Explicit deferrals

M1.7a1 does not freeze:

- Outcome records/evidence/classification;
- lifecycle interruption representation;
- effect certainty;
- partial-effect records;
- blocked-state record;
- Timeout/ACK schemas;
- Attempt ordering/sequence numbers;
- Retry Eligibility;
- retry/fallback relationship records;
- idempotency / duplicate-suppression contracts;
- cancellation;
- compensation;
- generic Continuation;
- Capability Availability or invocation-readiness schema;
- Authorization condition evaluation/consumption/revocation;
- quorum/multi-party authority;
- Worker-attempt schema;
- executor transport;
- scheduling;
- persistence/event sourcing.

M1.7a2 owns scoped Outcome/evidence. Later M1.7 recovery/Continuation slices own retry/fallback/successor semantics.

## 19. Acceptance criteria

M1.7a1 is acceptable only if tests prove at least:

```text
CapabilityAttempt is immutable and closed
exactly one CapabilityMatch relation is required
WorkProposal is not a universal Attempt prerequisite
step_ref equals the exact evaluated WorkStep
all symbolic WorkStep inputs are bound exactly once
extra/missing bound input names fail closed
BoundValue belongs to exact symbolic reference
binding and attempt occurrences remain distinct
evaluation and attempt occurrences remain distinct
empty presented_authorizations is representable
presented Authorization must include exact step + exact evaluation
at most one Authorization.v1 is supported
presented Authorization does not create an authorized=true field
no status/outcome/retry/attempt_number fields exist
unknown lifecycle/authority-like fields fail closed
new attempt occurrence changes identity
round-trip preserves canonical identity
all earlier M1 goldens remain unchanged
full Python 3.11–3.14 CI passes
representative canonical identities are frozen before merge
```
