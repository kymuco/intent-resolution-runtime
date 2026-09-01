# M2.4 — Attempt / Outcome / Continuation Orchestrator

Status: **implementation slice**.

M2.4 extends the replayable M2 runtime over the frozen M1.7 Attempt / Outcome / Continuation / Successor Resolution contracts without introducing recovery policy, automatic retry, Outcome collapse, hidden branch choice, executor scheduling, or mutable canonical lifecycle state.

The central boundary is:

```text
lifecycle history != recovery decision
```

M2.4 derives what exact M1.7 lifecycle material is present, selected for semantic re-entry, re-entered by the Host, and consumed by an admitted successor lineage. It does not decide that a retry, fallback, new successor, or parent completion should happen.

## 1. Implemented boundary

```text
exact predecessor ResolvedIntent
+ CapabilityAttempt[]
+ CapabilityOutcome[]
+ explicit ContinuationSource[]
+ ContinuationInput[]
+ zero/one active SuccessorResolutionLineage
        |
        v
orchestrate_attempt_outcome_continuation(...)
        |
        v
AttemptOutcomeContinuationFrontier
```

The frontier is a derived runtime view over exact immutable M1 records.

```text
frontier != canonical record
frontier != recovery policy
frontier != scheduler state
frontier != authority
```

It has no canonical identity or wire surface. Exact M1 records remain lifecycle history.

## 2. Exact predecessor lineage

Every supplied CapabilityAttempt must descend from the exact supplied predecessor `ResolvedIntent.identity` through its exact `CapabilityRequirement.work_plan.resolved_intent_identity`.

Sharing an original IntentRequest is insufficient.

```text
same IntentRequest != same active ResolvedIntent branch
```

Foreign Attempt material fails closed instead of being attached by step name, plan reference, executor, or request text.

## 3. Attempt history remains append-only semantic history

M1.7 freezes one `CapabilityAttempt` as one attributable invocation effort.

M2.4 therefore permits several exact Attempts to refer to the same WorkStep and same CapabilityMatchEvaluation when they are genuinely distinct attempt occurrences.

```text
multiple Attempts for one WorkStep != one mutable Attempt
Retry != mutation of an Attempt
Attempt N != Attempt N+1
```

M2.4 does not label a later Attempt as a retry automatically. Whether a new attempt was semantically an admitted retry, compensation, fallback, or unrelated repeated invocation belongs to separately admitted semantics/policy outside this slice.

One attempt occurrence cannot identify competing distinct Attempt records. Duplicate exact Attempt identities are rejected.

## 4. Attempt without Outcome remains neutral

`outcome_pending_attempts` contains supplied Attempts for which no exact active CapabilityOutcome is supplied.

This is a graph/history projection only.

```text
Attempt without Outcome != failed
Attempt without Outcome != interrupted
Attempt without Outcome != safe to retry
Attempt without Outcome != retry required
```

M2.4 does not synthesize fake Outcome records for pre-outcome absence.

## 5. Exact Outcome graph admission

Every CapabilityOutcome must preserve an exact CapabilityAttempt present in the supplied Attempt history.

```text
Outcome attempt identity
must equal
one exact supplied Attempt identity
```

An orphan Outcome fails closed.

M2.4 admits at most one active exact Outcome per exact Attempt because frozen M1.7 defines immutable Outcome records but does not define an Outcome revision/supersession relation.

Two distinct Outcome records for one Attempt therefore fail closed.

```text
competing Outcomes != latest wins
competing Outcomes != successful-looking wins
competing Outcomes != canonical-identity wins
```

A future explicit revision/supersession contract may extend this boundary; M2.4 does not invent one.

## 6. Outcome dimensions remain orthogonal

M2.4 preserves the M1.7 frozen dimensions exactly:

```text
OutcomeLifecycleState
OutcomeCompletionState
OutcomeEffectCertainty
```

It does not collapse them into a synthetic `success`, `failure`, or `retryable` status.

```text
Outcome lifecycle != Outcome completion
Outcome completion != effect certainty
interrupted != failed
not_satisfied != no effect
material unknown != failed
material unknown != retry permission
```

`material_unknown_outcomes` merely projects exact Outcomes whose frozen completion/effect dimensions contain material unknowns.

`interrupted_outcomes` merely projects exact Outcomes whose frozen lifecycle state is interrupted.

Neither projection is recovery policy.

## 7. Outcome history is not automatic semantic re-entry

A CapabilityOutcome may be relevant only to completion/accounting, or the Host may decide that it must re-enter IRR for a new semantic decision.

M2.4 keeps those cases separate.

```text
Outcome history != selected Continuation source
Outcome != automatic ContinuationInput
```

The caller supplies an explicit `continuation_sources` tuple containing exact frozen M1.7 continuation-source records selected for this re-entry surface.

For CapabilityOutcome sources, the exact Outcome must already be present in the supplied Outcome history.

`outcomes_not_selected_for_continuation` is neutral: it identifies Outcome history not currently selected as semantic re-entry material. It does not assert that those Outcomes should or should not ever be re-entered.

## 8. Other exact M1.7 continuation sources remain supported

The explicit selected source surface accepts the exact frozen source types:

```text
CapabilityOutcome
WorkerResult
BindingIssue
CapabilityMatchIssue
GovernanceContinuationMaterial
```

Every selected source must descend from the exact predecessor ResolvedIntent branch.

M2.4 does not manufacture these source records or decide which source class should be selected.

## 9. Selected source is not Host re-entry occurrence

A selected exact source may still lack a Host-side `ContinuationInput` submission occurrence.

Such sources appear in:

```text
reentry_pending_sources
```

This property means only:

```text
selected source + no supplied ContinuationInput occurrence
```

It deliberately does not mean:

```text
reentry pending != reentry required by policy
reentry pending != automatic Host submission
```

The Host must supply an exact canonical ContinuationInput when a real re-entry occurrence exists.

## 10. ContinuationInput graph admission

Every supplied ContinuationInput must:

- descend from the exact predecessor ResolvedIntent;
- wrap an exact source present in the selected `continuation_sources` set;
- preserve the exact frozen source identity and Host re-entry attribution.

An unselected-source ContinuationInput fails closed rather than promoting its source implicitly.

```text
ContinuationInput availability != source-selection authority
```

## 11. Repeated Host delivery preserves delivery history

M1.7 deliberately allows the same exact source to be submitted through distinct Host re-entry occurrences. Those ContinuationInput records have distinct identities because delivery history is real history.

M2.4 preserves them rather than deduplicating the canonical history.

At the same time:

```text
same exact source re-entered twice != two independent semantic sources
```

`reentry_ambiguity_source_identities` exposes any exact source identity represented by more than one active re-entry occurrence.

This does not choose one occurrence.

```text
reentry ambiguity != first/latest precedence
reentry ambiguity != duplicate semantic evidence
```

Frozen `SuccessorResolutionLineage` continues to reject amplification of one exact source through multiple re-entry wrappers inside one lineage.

## 12. Successor lineage remains explicit history

M2.4 accepts zero or one active exact `SuccessorResolutionLineage` in this narrow slice.

Every lineage must:

- preserve the exact predecessor ResolvedIntent;
- reference only exact ContinuationInput records present in supplied re-entry history;
- continue to satisfy all frozen M1.7 occurrence and duplicate-source rules.

```text
SuccessorResolutionLineage != retry
SuccessorResolutionLineage != fallback
SuccessorResolutionLineage != Authorization
SuccessorResolutionLineage != WorkPlan
```

M2.4 does not synthesize a successor ResolutionOutput or successor lineage.

## 13. Competing successor branches fail closed

M1.7 contains no active-branch precedence rule for two distinct SuccessorResolutionLineage records over the same predecessor lifecycle surface.

M2.4 therefore rejects more than one active distinct lineage.

```text
competing successor lineages != hidden branch selection
input order != successor precedence
canonical identity order != successor precedence
```

A future explicit branch/supersession lifecycle may extend this boundary. It is not inferred here.

## 14. Unconsumed re-entry remains explicit

`unconsumed_continuation_inputs` contains exact supplied ContinuationInput records not referenced by the active successor lineage.

This is again neutral lifecycle state.

```text
unconsumed ContinuationInput != automatic successor
unconsumed ContinuationInput != retry request
unconsumed ContinuationInput != error by definition
```

The runtime does not silently create a second successor branch.

## 15. Input ordering creates no semantic precedence

Attempts, Outcomes, selected continuation sources, ContinuationInputs, and successor lineage material are normalized independently of caller presentation order.

```text
input order != attempt precedence
input order != outcome precedence
input order != re-entry precedence
input order != successor precedence
```

Normalization exists for deterministic derived representation, not as a hidden policy selector.

## 16. What M2.4 does not add

M2.4 does not add:

- CapabilityAttempt synthesis;
- executor scheduling or handoff;
- Capability Availability/readiness checking;
- CapabilityOutcome synthesis;
- `failed` / `succeeded` synthetic lifecycle status;
- retry eligibility;
- retry safety inference;
- retry scheduling or loops;
- fallback selection;
- compensation/cancellation policy;
- automatic Outcome → Continuation promotion;
- Host re-entry synthesis;
- source-selection policy;
- successor Resolution synthesis;
- successor WorkPlan construction;
- parent WorkPlan completion inference;
- parent intent completion inference;
- Authorization renewal/inheritance;
- persistence/event sourcing;
- mutable global lifecycle status.

## 17. Frozen M2.4 invariants

```text
frontier != canonical record
frontier != recovery policy

Attempt != Outcome
Attempt without Outcome != failed
Retry != mutation of an Attempt
multiple Attempts for one WorkStep != one mutable Attempt

Outcome lifecycle != Outcome completion
Outcome completion != effect certainty
material unknown != failed
material unknown != retry permission
competing Outcomes != latest wins

Outcome history != selected Continuation source
Outcome != automatic ContinuationInput
reentry pending != reentry required
same exact source re-entered twice != two independent semantic sources
reentry ambiguity != first/latest precedence

SuccessorResolutionLineage != retry
SuccessorResolutionLineage != fallback
competing successor lineages != hidden branch selection
unconsumed ContinuationInput != automatic successor
old Authorization != successor Authorization
```

## 18. Acceptance

M2.4 is complete when executable tests prove at least:

```text
empty lifecycle history derives a non-canonical frontier
foreign Attempt lineage fails closed
multiple Attempts for one WorkStep remain distinct exact history
Attempt without Outcome remains neutral
orphan Outcome fails closed
competing Outcomes for one Attempt fail closed
Outcome does not automatically become selected Continuation source
selected source does not automatically become ContinuationInput
ContinuationInput outside selected source set fails closed
material unknown/interrupted Outcome stays multidimensional and non-retry-policy
same source re-entered twice preserves delivery history without semantic amplification
SuccessorResolutionLineage cannot consume unsupplied re-entry history
one active successor lineage consumes only its exact inputs
competing successor lineages fail closed
input ordering does not create precedence
all frozen M0/M1/M2.0–M2.3 tests remain green
Python 3.11–3.14 CI passes
```

After M2.4 closes, the next planned slice is **M2.5 — Worker Lifecycle Orchestrator**.
