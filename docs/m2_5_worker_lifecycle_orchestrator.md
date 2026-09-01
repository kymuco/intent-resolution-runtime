# M2.5 — Worker Lifecycle Orchestrator

Status: **implementation slice**.

M2.5 extends replayable M2 orchestration over the frozen M1.5 Worker Delegation / WorkerResult records without introducing Worker selection, transport, completion policy, scope/capability/authority widening, generic Continuation duplication, or mutable Worker state.

The central boundary is:

```text
Worker lifecycle history != Worker/parent completion policy
```

## 1. Implemented boundary

```text
exact predecessor ResolvedIntent
+ exact parent WorkPlan[] when referenced
+ DelegatedWork[]
+ DelegatedWorkHandoff[]
+ WorkerResult[]
        |
        v
orchestrate_worker_lifecycle(...)
        |
        v
WorkerLifecycleFrontier
```

The frontier is a derived runtime view over exact immutable M1 records.

```text
frontier != canonical record
frontier != Worker scheduler
frontier != completion policy
frontier != authority
```

It has no canonical identity or wire schema.

## 2. Exact predecessor and parent-plan graph

Every supplied parent WorkPlan must descend from the exact predecessor `ResolvedIntent.identity`.

Every DelegatedWork must also preserve that exact predecessor identity.

When a DelegatedWork carries one `parent_work_plan_identity_refs` entry, the exact WorkPlan record must be present in the supplied `parent_work_plans` history.

```text
parent WorkPlan identity ref != ambient parent-plan lookup
same IntentRequest != same active ResolvedIntent branch
```

M2.5 does not fetch a missing parent WorkPlan or infer one from a plan ref.

## 3. DelegatedWork semantic identity remains stable

A delegation is the admitted subordinate semantic envelope.

M2.5 rejects two materially distinct active DelegatedWork records that reuse one exact `delegation_ref`.

```text
same delegation_ref + competing DelegatedWork semantics
!= first wins
!= latest wins
!= Worker choice
```

This does not make `delegation_ref` authority or authentication; it only prevents one active logical delegation reference from carrying competing semantic envelopes in this runtime slice.

## 4. Delegation without handoff remains neutral

A DelegatedWork may exist without a supplied DelegatedWorkHandoff.

Such records appear in:

```text
handoff_disposition_required_delegations
```

This property means only that no handoff history is supplied for that delegation.

```text
handoff disposition required != Worker dispatch required
handoff disposition required != Worker unavailable
handoff disposition required != delegation failed
```

M2.5 does not synthesize a Worker handoff.

## 5. Multiple handoffs preserve real history

M1.5 freezes Worker substitution as a distinct `DelegatedWorkHandoff` occurrence without declaring Worker refs interchangeable or defining one terminal handoff.

M2.5 therefore permits multiple exact handoff records for one exact DelegatedWork.

```text
multiple handoffs != latest Worker wins
multiple handoffs != Worker equivalence
multiple handoffs != delegation mutation
```

`multi_handoff_delegation_refs` exposes the multiplicity without selecting an active Worker or handoff.

M2.5 intentionally has no `active_worker` or `selected_handoff` field.

## 6. Handoff occurrence graph admission

Every handoff must embed one exact DelegatedWork present in the supplied delegation history.

One `handoff_event_ref` cannot identify competing distinct handoff records.

Handoff occurrence must also differ from the predecessor Resolution admission occurrence.

```text
Worker handoff occurrence != predecessor Resolution admission occurrence
```

This preserves occurrence-role separation in the admitted lifecycle graph.

## 7. Handoff without WorkerResult is not failure

A handoff with no supplied WorkerResult appears in:

```text
result_pending_handoffs
```

This is a neutral history projection only.

```text
handoff without WorkerResult != Worker failure
handoff without WorkerResult != timeout
handoff without WorkerResult != retry permission
handoff without WorkerResult != cancellation
```

M1.5 WorkerResult has no frozen success/failure lifecycle enum, and M2.5 does not invent one.

## 8. Exact WorkerResult lineage

Every WorkerResult must embed one exact DelegatedWorkHandoff present in supplied handoff history.

An orphan WorkerResult fails closed.

The frozen WorkerResult constructor already preserves exact Worker identity and requires its result occurrence to differ from its own handoff occurrence. M2.5 additionally validates the larger graph.

## 9. Multiple WorkerResult records are return history, not hidden revisions

M1.5b deliberately does not freeze WorkerResult as a terminal lifecycle Outcome, a progress event stream, or a single final record.

Therefore M2.5 does **not** reject multiple distinct WorkerResult records from the same handoff merely because they share the handoff.

```text
multiple WorkerResult records != latest result wins
multiple WorkerResult records != final result selection
multiple WorkerResult records != delegated completion
```

`multi_result_handoff_identities` exposes exact handoffs with more than one WorkerResult occurrence.

M2.5 intentionally has no `latest_result` or `final_result` field.

## 10. Worker result occurrence roles remain distinct

One Worker result occurrence cannot identify competing distinct WorkerResult records.

Every WorkerResult occurrence must differ from:

- the predecessor Resolution admission occurrence;
- every supplied Worker handoff occurrence.

```text
Worker result occurrence != predecessor Resolution admission occurrence
Worker result occurrence != Worker handoff occurrence
```

The second rule is global across the supplied Worker lifecycle graph rather than checking only the result's own handoff. One occurrence cannot be a handoff on one branch and a result on another.

## 11. WorkerNeed remains a need, not widening

M2.5 exposes exact WorkerResult records containing WorkerNeed through:

```text
results_with_needs
```

No WorkerNeed is applied to DelegatedWork.

```text
WorkerNeed != scope expansion
WorkerNeed != capability grant
WorkerNeed != Authorization
WorkerNeed != objective change
WorkerNeed != effect authority
```

The original immutable DelegatedWork envelope remains unchanged.

A requested new scope may continue to be represented with an empty `related_scope_refs` tuple exactly as frozen by M1.5b; this does not pretend the new scope is admitted.

## 12. Completion claims remain Worker assertions

WorkerResult material with role `completion_claim` appears through:

```text
results_with_completion_claims
```

This is only a structural projection of exact returned material.

```text
completion claim != delegated completion proof
completion claim != parent WorkPlan completion
completion claim != parent intent satisfaction
```

M2.5 adds no `delegated_complete`, `parent_complete`, or `intent_satisfied` status.

## 13. Deliverables remain returned material, not parent completion

WorkerResult records containing material with role `deliverable` appear through:

```text
results_with_deliverables
```

The frozen M1.5 constructor already checks exact ExpectedDeliverable relation, semantic type, and scope coverage.

M2.5 does not strengthen that structural relation into completion.

```text
deliverable material != delegated completion proof
deliverable material != parent WorkPlan completion
deliverable material != parent intent satisfaction
```

## 14. WorkerResult remains non-factual by default

M2.5 does not promote WorkerResultMaterial roles such as finding, uncertainty, artifact reference, omission, or deliverable into Context, Claim, Evidence, Observation, Outcome, or authority-bearing records.

```text
WorkerResult != factual truth by default
WorkerResult != Observation by default
WorkerResult != Outcome by default
```

Epistemic admission remains outside this slice.

## 15. M2.4 owns generic Continuation re-entry

WorkerResult is already one of the exact frozen M1.7 `ContinuationSource` types.

M2.5 deliberately does not add another source-selection / ContinuationInput / SuccessorResolutionLineage engine.

```text
WorkerResult history != automatic Continuation
WorkerResult availability != continuation-source selection
```

When the Host explicitly selects an exact WorkerResult for semantic re-entry, M2.4 owns:

```text
selected ContinuationSource
→ Host ContinuationInput
→ SuccessorResolutionLineage
```

This keeps Worker-specific lifecycle orchestration and generic IRR continuation orchestration compositional rather than duplicated.

## 16. Input ordering creates no Worker/result precedence

Parent WorkPlans, DelegatedWork records, handoffs, and WorkerResult records are normalized by exact identity independently of caller presentation order.

```text
input order != delegation precedence
input order != Worker precedence
input order != result precedence
canonical identity order != final-result policy
```

Normalization provides deterministic derived representation only.

## 17. What M2.5 does not add

M2.5 does not add:

- Worker registry or discovery;
- Worker selection/ranking;
- Worker transport/protocol;
- dispatch scheduling;
- Worker acceptance/rejection state;
- progress or streaming;
- cancellation or timeout;
- retry/fallback policy;
- nested Worker orchestration;
- recursive delegation policy;
- WorkerResult factual admission;
- WorkerResult → Outcome conversion;
- delegated completion evaluation;
- parent WorkPlan completion evaluation;
- parent intent satisfaction evaluation;
- scope/context/capability widening;
- Authorization creation/inheritance;
- WorkerNeed satisfaction policy;
- generic Continuation source selection;
- ContinuationInput synthesis;
- successor Resolution synthesis;
- persistence/event sourcing;
- mutable Worker status.

## 18. Frozen M2.5 invariants

```text
frontier != canonical record
frontier != Worker scheduler
frontier != completion policy

DelegatedWork != DelegatedWorkHandoff
DelegatedWorkHandoff != Worker acceptance
handoff disposition required != Worker dispatch required
multiple handoffs != latest Worker wins

handoff without WorkerResult != Worker failure
WorkerResult != Worker lifecycle success
multiple WorkerResult records != latest result wins
multiple WorkerResult records != final result selection

WorkerNeed != scope expansion
WorkerNeed != capability grant
WorkerNeed != Authorization
completion claim != delegated completion proof
deliverable material != parent completion

WorkerResult history != automatic Continuation
WorkerResult availability != continuation-source selection
```

## 19. Acceptance

M2.5 is complete when executable tests prove at least:

```text
empty Worker lifecycle derives a non-canonical frontier
foreign parent WorkPlan fails closed
foreign DelegatedWork fails closed
parented DelegatedWork requires exact supplied parent WorkPlan
competing DelegatedWork semantics for one delegation_ref fail closed
DelegatedWork without handoff remains neutral
orphan handoff fails closed
multiple handoffs for one delegation preserve history without Worker selection
handoff/predecessor occurrence collision fails closed
handoff without WorkerResult remains neutral
orphan WorkerResult fails closed
multiple WorkerResult records for one handoff preserve history without latest/final selection
competing records cannot reuse one result occurrence
result/predecessor and result/handoff occurrence collisions fail closed
WorkerNeed does not widen DelegatedWork
completion claim remains an assertion
returned deliverable does not imply parent completion
M2.5 does not duplicate generic Continuation
input order creates no Worker/result precedence
all frozen M0/M1/M2.0–M2.4 tests remain green
Python 3.11–3.14 CI passes
```

After M2.5 closes, the next planned slice is **M2.6 — End-to-End Host Fixture**.
