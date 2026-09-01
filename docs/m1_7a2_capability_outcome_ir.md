# M1.7a2 — Capability Outcome / Effect Certainty IR

Status: **candidate normative M1.7a2 contract**.

This document freezes the first immutable Outcome representation for an exact `CapabilityAttempt` while preserving the M0.9 separation between lifecycle interruption, Completion Semantics, effect certainty, transport observations, authority, and later recovery policy.

M1.7a2 extends M1.7a1. It does **not** introduce Retry, fallback, retry eligibility, blocked-without-attempt state, generic Continuation, Worker lifecycle Outcome, persistence, scheduling, or executor transport.

## 1. Boundary

```text
exact CapabilityAttempt
        |
        v
attributable result/evidence
        |
        v
CapabilityOutcome
  ├─ lifecycle assessment
  ├─ completion assessment
  ├─ requested-effect certainty[]
  └─ attributable evidence[]
```

There is deliberately no single `status` field.

```text
lifecycle state != completion state
completion state != effect certainty
transport state != semantic completion
Outcome != Attempt
Outcome != Authorization
Outcome != Observation
Outcome != parent completion
```

This permits states that M0.9 requires to remain representable:

```text
interrupted + completion unknown + effect unknown
normal protocol complete + completion not satisfied + partial effect confirmed
interrupted + completion satisfied + effect confirmed
normal protocol complete + completion unknown
```

No enum value silently erases another semantic dimension.

## 2. CapabilityOutcomeAttribution

`CapabilityOutcomeAttribution` preserves:

```text
evaluator_ref
outcome_event_ref
```

`evaluator_ref` identifies the component admitting/classifying the Outcome. It is attribution, not proof of correctness.

The Outcome occurrence must differ from the exact `CapabilityAttempt.attempt_event_ref`.

```text
Attempt occurrence != Outcome occurrence
```

M1.7a2 does not require the evaluator to differ from the executor. Such equality is provenance, not verification or authority.

## 3. OutcomeEvidence

`OutcomeEvidence` is attributable material considered when admitting one Outcome:

```text
evidence_ref
attribution
source_identity
relation
roles[]
temporal_basis_refs[]
scope
statement
```

`SourceAttribution` preserves source actor/component and source occurrence. `source_identity` independently preserves the exact source record/contract identity admitted for that item.

```text
source attribution != source verification
source identity != truth
executor assertion != stronger completion than its contract supports
```

Evidence relation reuses the existing `supports | weakens` vocabulary. M1.7a2 does not define implicit precedence between conflicting evidence.

```text
newest wins        -> forbidden by default
Executor wins      -> forbidden by default
remote source wins -> forbidden by default
majority wins      -> forbidden by default
```

Conflicting evidence may be embedded together and may support an `unknown` assessment.

## 4. OutcomeEvidenceRole

M1.7a2 freezes these evidence roles:

```text
lifecycle
completion
effect
partial_effect
uncertainty
transport
other_explicit
```

Roles are semantic classifications, not trust levels.

An evidence item may carry multiple roles when one exact source item is materially relevant to multiple dimensions.

The separate `transport` role exists specifically so transport convenience cannot become semantic completion automatically.

```text
request sent != completion evidence by default
HTTP response != completion evidence by default
ACK received != required completion by default
```

A producer that wants a transport receipt to support Completion Semantics must explicitly admit it with the `completion` role under the applicable downstream contract.

## 5. Temporal basis

`OutcomeEvidence.temporal_basis_refs` may reference exact admitted temporal-basis identities when freshness/time is material.

M1.7a2 does not read an ambient wall clock.

```text
historical success != current-state guarantee
Outcome evidence timestamp != permanent freshness
```

Fresh Observation or status acquisition may be required later when current state matters.

## 6. OutcomeLifecycleState

M1.7a2 freezes:

```text
normal_protocol_completed
interrupted
```

This dimension says whether the bounded Attempt's normal result/lifecycle protocol completed.

It does **not** say whether the semantic Completion Contract was satisfied and does not determine effect certainty.

```text
interrupted != failed
interrupted != no effect
interrupted != unknown effect by definition
normal protocol completed != semantic success
```

`OutcomeLifecycleAssessment` must reference embedded evidence carrying the `lifecycle` role.

## 7. OutcomeCompletionState

M1.7a2 freezes:

```text
satisfied
not_satisfied
unknown
```

This dimension is scoped to the exact WorkStep Completion Semantics already embedded through the exact `CapabilityAttempt`.

Conceptually:

```text
satisfied
    -> sufficient admitted evidence for this Attempt's Completion Semantics

not_satisfied
    -> sufficient admitted evidence that those Completion Semantics were not satisfied

unknown
    -> evidence is materially insufficient/conflicting for that completion judgment
```

For `satisfied` and `not_satisfied`, the assessment must reference embedded evidence carrying the `completion` role.

For `unknown`, referenced evidence must contain at least `completion` or `uncertainty`.

```text
not_satisfied != no effect
not_satisfied != safe retry
satisfied != parent WorkPlan completion
satisfied != parent intent satisfaction
unknown != failed
```

M1.7a2 intentionally does not freeze a separate `succeeded` or `failed` wire enum. Those conceptual M0.9 labels can be reasoned from the orthogonal recorded dimensions without collapsing them.

## 8. Requested-effect certainty

Each exact `CapabilityRequirement.requested_effects` entry must receive exactly one `OutcomeEffectAssessment`.

This provides a bounded effect-certainty surface over the same exact admitted effect semantics used for Capability Match and Attempt.

`OutcomeEffectCertainty` freezes:

```text
confirmed_not_occurred
confirmed_partial
confirmed_occurred
unknown
```

Meaning:

- `confirmed_not_occurred`: admitted evidence establishes that this requested effect did not occur at the represented scope;
- `confirmed_partial`: admitted evidence establishes a material partial occurrence;
- `confirmed_occurred`: admitted evidence establishes that the requested effect occurred;
- `unknown`: evidence cannot materially establish whether/how the requested effect occurred.

```text
confirmed_partial != erased effect
confirmed_occurred != Completion Semantics satisfied
confirmed_not_occurred != safe retry by itself
unknown != failed
```

For known effect classifications, referenced evidence must carry `effect` and, for partial effects, may carry `partial_effect`.

For `unknown`, evidence may carry `effect` or `uncertainty`.

## 9. Exact effect coverage

A `CapabilityOutcome.v1` must assess **every and only** requested effect of the exact Attempt's `CapabilityRequirement`.

```text
requested effect omitted from Outcome -> invalid v1 Outcome
foreign requested effect inserted      -> invalid v1 Outcome
same requested effect assessed twice   -> invalid v1 Outcome
```

This prevents an Outcome from presenting a complete-looking certainty surface while silently dropping one admitted material effect.

For an admitted requirement with zero requested effects, `effect_assessments` is exactly empty. That is natural for a pure/effect-free operation and does not synthesize fake effects.

Descriptor `possible` effects that were not requested do not become requested effects after execution. If an unexpected or unadmitted effect is reported, its attributable source material may still be preserved in `OutcomeEvidence`; M1.7a2 does not yet freeze a standalone unadmitted-effect occurrence schema.

## 10. Evidence references are closed

Every lifecycle/completion/effect assessment references `OutcomeEvidence.evidence_ref` values embedded in the same exact `CapabilityOutcome`.

Unknown or foreign evidence refs are fail-closed.

Evidence order is canonical presentation order only and never source precedence.

## 11. Transport does not strengthen completion

M1.7a2 structurally rejects using evidence classified only as `transport` to support a known `satisfied` or `not_satisfied` completion assessment.

This preserves the M0.9 rule:

```text
transport success != semantic success
request accepted != requested effect completed by default
```

The correct downstream contract may admit a specific receipt as both `transport` and `completion`; the role must be explicit.

## 12. Failure may coexist with effects

A completion assessment of `not_satisfied` may coexist with:

```text
confirmed_partial
confirmed_occurred
unknown
```

effect certainty.

This is essential for operations that mutate state before later validation fails.

```text
failed completion != no effect
failed completion != history erasure
```

M1.7a2 does not infer Retry Eligibility from any such combination.

## 13. Interruption and effect certainty are independent

An interrupted Attempt may have:

```text
confirmed_not_occurred
confirmed_partial
confirmed_occurred
unknown
```

depending on attributable evidence.

This directly encodes the M0.9 requirement that lifecycle interruption and effect certainty not be forced into one mutually exclusive status enum.

## 14. Material unknown helper

`CapabilityOutcome.has_material_unknown` is a derived convenience property.

It is true when:

```text
completion == unknown
OR
any requested effect certainty == unknown
```

It has no independent wire field and therefore cannot drift from the canonical assessments.

It does not decide Retry, fallback, parent blocking, or parent completion.

## 15. Outcome is not Observation

`OutcomeEvidence` and `CapabilityOutcome` do not become Context/Observation automatically.

```text
Outcome != Observation
OutcomeEvidence != Context EvidenceRecord by default
returned result != ambient reusable fact
```

If returned data must become new decision evidence or current-world Observation, that classification occurs through the applicable later Continuation/Host boundary.

## 16. Outcome is not Authorization or compliance proof

A successful/effect-confirmed Outcome does not prove the Attempt was authorized.

Likewise, an unauthorized historical Attempt may have a perfectly knowable Outcome.

```text
Outcome != Authorization
Effect != proof of Authorization
later approval != retroactive Authorization
```

M1.7a2 does not validate authorization-condition consumption/revocation or convert historical execution into permission.

## 17. Outcome is scoped to one exact Attempt

`CapabilityOutcome` embeds the complete exact `CapabilityAttempt`.

Changing any material Attempt dimension therefore changes Outcome identity, including:

- exact Capability Match evaluation;
- exact Catalog/Descriptor semantics;
- WorkStep;
- concrete BoundValue material;
- presented Authorization lineage;
- executor attribution;
- Attempt occurrence.

```text
Outcome for Attempt A != Outcome for Attempt B
Retry Attempt N+1 -> separate Outcome lineage
```

M1.7a2 does not mutate an earlier Attempt.

## 18. Multiple Outcomes for one Attempt

M1.7a2 does not impose a persistence/event-sourcing state machine.

Multiple attributable `CapabilityOutcome` records may exist for the same exact Attempt when later evidence changes what can be admitted.

For example:

```text
Outcome occurrence T1:
    completion = unknown
    effect = unknown

later attributable receipt

Outcome occurrence T2:
    completion = satisfied
    effect = confirmed_occurred
```

Both historical records may remain valid historical facts about what was admitted at their respective occurrences.

M1.7a2 does not freeze predecessor links, temporal ordering algorithms, or replacement semantics. Those belong to later Continuation/persistence work.

```text
later knowledge != rewrite earlier knowledge state
later evidence != retroactive recovery justification
```

## 19. No blocked-without-attempt record

`missing_capability`, Governance Denial, `require_review`, unresolved Material Ambiguity, known pre-attempt unavailability, and other pre-attempt blockers do not require a fake `CapabilityAttempt` or `CapabilityOutcome`.

```text
blocked before Attempt -> no fake Attempt
missing_capability != Outcome
Denial != Outcome
require_review != Outcome
clarification != Outcome
```

A dedicated blocked/Continuation representation remains later M1.7 work.

## 20. No Retry semantics

M1.7a2 records what is known about one Attempt. It does not decide what should happen next.

There is no:

```text
retry=true
retryable=true
safe_to_retry=true
fallback
attempt_number
predecessor_attempt
automatic retry policy
```

in this slice.

```text
failed != automatic retry
unknown effectful outcome != automatic retry
Authorization != retry safety
Capability availability != retry safety
```

Retry/recovery is successor semantics, not an Outcome field.

## 21. No hidden evidence precedence

A `CapabilityOutcome` may embed supporting and weakening evidence together.

Validation checks reference closure and role suitability, not substantive truth or source priority.

The evaluator/IRR admission boundary owns the explicit judgment.

```text
evidence presence != truth
fluent executor report != stronger contract
source count != majority policy
```

Future explicit evidence-resolution rules may be introduced without changing this frozen representational boundary.

## 22. Canonical behavior

All new records:

- are immutable;
- use exact-key deserialization;
- reject Unicode surrogate code points in text;
- canonicalize set-like tuples;
- reject duplicate stable references;
- are closed against subclassing through the package public surface;
- include all material semantics in canonical identity.

Presentation order never becomes evidence precedence or lifecycle ordering.

## 23. Explicit deferrals

M1.7a2 intentionally does **not** freeze:

- generic Worker Outcome schema;
- blocked-without-attempt record;
- Retry / fallback / Retry Eligibility;
- idempotency or duplicate-suppression contracts;
- cancellation;
- compensation / rollback;
- capability Availability / invocation readiness;
- status-query acquisition;
- generic Observation admission;
- generic Continuation;
- successor WorkPlan generation;
- parent WorkPlan completion aggregation;
- parent intent satisfaction;
- Outcome predecessor/refinement links;
- persistence/event sourcing;
- executor transport protocol;
- automatic Outcome evaluator algorithms;
- trust/source-precedence policy;
- cryptographic source verification.

## 24. Acceptance criteria

M1.7a2 is acceptable only if executable tests prove at least:

1. Outcome occurrence differs from Attempt occurrence.
2. Lifecycle, completion, and effect certainty are independently representable.
3. `interrupted + unknown` is representable without calling it failed.
4. `not_satisfied + confirmed_partial` preserves partial effect history.
5. transport-only evidence cannot silently satisfy Completion Semantics.
6. every requested effect is assessed exactly once.
7. foreign requested effect assessments are rejected.
8. pure/effect-free Attempt may have zero effect assessments.
9. assessments may reference only embedded Outcome evidence.
10. lifecycle assessment requires lifecycle-role evidence.
11. known completion assessment requires completion-role evidence.
12. unknown completion/effect may be supported by uncertainty-role evidence.
13. conflicting supporting/weakening evidence is representable without precedence.
14. source attribution/source identity remain separate from truth.
15. Outcome remains distinct from Authorization, Observation, Capability Match, Retry, and parent completion.
16. round-trip preserves canonical identity.
17. unknown fields are rejected.
18. new IR records are closed against subclassing.
19. full Python 3.11–3.14 CI passes.
20. representative canonical identities are independently calculated and frozen before merge.
