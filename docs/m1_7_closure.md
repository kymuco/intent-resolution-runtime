# M1.7 — Attempt / Outcome / Continuation IR Closure

Status: **complete and frozen in `main`**.

M1.7 encodes the frozen M0.9 Failure / Retry / Unknown Outcome boundary and the continuation side of the M0.4/M0.6/M0.8 contracts as explicit immutable lifecycle IR. It preserves execution history, scoped outcome interpretation, typed re-entry, and successor semantic lineage without introducing hidden retry, fallback, authority inheritance, parent-completion inference, or mutable lifecycle state.

Final M1.7 merge lineage closes at:

```text
main = 600cf8fc27d7a6e2353b7524f682cb67c7fabb23
```

M1.7 is complete. The next implementation milestone is **M1.8 — Executable M0.10 Fixtures & M1 Closure**.

## 1. Closed semantic chain

```text
exact uniquely matched capability-backed WorkStep
        |
        v
CapabilityAttempt
        |
        v
CapabilityOutcome
        |
        v
ContinuationInput
        |
        v
SuccessorResolutionLineage
        |
        +--> ResolvedIntent
        +--> ClarificationNeed
        `--> InformationNeed
```

No arrow above means authority inheritance, automatic retry, causal proof, parent completion, or successor WorkPlan creation.

## 2. M1.7a1 — Capability Attempt IR

M1.7a1 freezes one concrete attributable effort to invoke one exact uniquely matched capability-backed WorkStep.

A `CapabilityAttempt` preserves:

- the exact unique `CapabilityMatchEvaluation`;
- the exact WorkStep lineage carried by that evaluation;
- every concrete `BoundValue` used for symbolic inputs;
- optional presented `Authorization` lineage;
- actual executor attribution;
- one exact attempt occurrence.

Core invariants remain:

```text
Attempt != Outcome
Attempt != Effect
Attempt != success
Attempt != failure
Attempt != Authorization
presented Authorization != proof all conditions were satisfied
absence of Authorization != proof no Attempt occurred
Attempt N != Attempt N+1
Retry != mutation of Attempt N
CapabilityMatch != Attempt
Binding success != Attempt
```

A retry or fallback execution, if ever admitted by later runtime policy, is a new Attempt. M1.7 does not mutate an old Attempt into a second invocation.

## 3. M1.7a2 — Capability Outcome / Effect Certainty IR

M1.7a2 freezes attributable scoped result interpretation for one exact Attempt without rewriting the Attempt itself.

It deliberately does **not** collapse M0.9 concepts into one status enum. The frozen Outcome has orthogonal dimensions:

```text
OutcomeLifecycleState
    normal_protocol_completed | interrupted

OutcomeCompletionState
    satisfied | not_satisfied | unknown

OutcomeEffectCertainty
    confirmed_not_occurred
    | confirmed_partial
    | confirmed_occurred
    | unknown
```

This preserves combinations that a single `succeeded/failed/unknown_outcome` field would erase, for example:

```text
interrupted + completion unknown + effect unknown
normal protocol completed + completion not_satisfied + partial effect confirmed
interrupted + completion satisfied + effect confirmed
normal protocol completed + completion unknown
```

Core distinctions remain:

```text
lifecycle state != completion state
completion state != effect certainty
transport state != semantic completion
interrupted != failed
not_satisfied != no effect
unknown != failed
Outcome != Authorization
Outcome != Observation
Outcome != parent completion
```

M1.7a2 intentionally does not freeze a separate `succeeded` or `failed` wire enum, and pre-attempt blockers do not require fake Attempt/Outcome records. Outcome material may preserve exact attributable evidence and certainty assessments under its frozen contract, but it does not create retry permission or erase partial/uncertain historical effects.

## 4. M1.7b1 — Continuation Input IR

M1.7b1 freezes exact downstream/blocking material re-entry into IRR as typed immutable `ContinuationInput` records.

Admitted continuation source kinds include the frozen exact source contracts rather than an untyped generic payload. The source record remains exact and attributable; Host re-entry adds a separate attributable submission occurrence.

Core invariants:

```text
ContinuationInput != Observation by default
ContinuationInput != new Context by default
ContinuationInput != Authorization
ContinuationInput != Retry
ContinuationInput != fallback
source production occurrence != Host re-entry occurrence
same source re-entered twice != two independent source facts
```

`ContinuationInput.source_identity`, `resolved_intent_identity`, and `source_event_ref` are mechanically derived projections over the exact nested source. `source_event_ref` is non-serialized and therefore does not alter the frozen B1 wire identity.

## 5. M1.7b2 — Successor Resolution Lineage IR

M1.7b2 freezes the exact relation between:

```text
one predecessor ResolvedIntent
+
one or more exact ContinuationInput records
+
one exact successor Resolution Output
```

The successor remains one of the already-frozen Resolution Outputs:

```text
ResolvedIntent
ClarificationNeed
InformationNeed
```

A successor `ResolvedIntent` may later enter the ordinary frozen Intent-to-Work pipeline. B2 itself does not construct successor work.

Core invariants:

```text
SuccessorResolutionLineage != Retry
SuccessorResolutionLineage != fallback
SuccessorResolutionLineage != WorkPlan
SuccessorResolutionLineage != WorkPlan mutation
SuccessorResolutionLineage != Authorization
SuccessorResolutionLineage != Evidence
SuccessorResolutionLineage != parent completion
successor ResolutionOutput != successor WorkPlan
lineage association != causal proof
one source re-submitted many times != many independent lineage inputs
```

## 6. Four occurrence roles are fail-closed

Final M1.7b2 hardening preserves four semantic occurrence roles:

```text
1. predecessor Resolution admission
2. continuation source production
3. Host re-entry submission
4. successor Resolution admission
```

These roles may not alias across categories.

```text
predecessor admission != source production
predecessor admission != Host re-entry
source production != Host re-entry
successor admission != predecessor/source/re-entry
```

Same-category sharing remains representable where one real source-production occurrence legitimately produces multiple exact records or one real Host submission occurrence submits multiple records. The prohibition is cross-category, not a demand for globally unique event refs.

This closure was hardened after automated review found a source-production/successor-admission alias path and later found that the normative B2 document still described only three roles while the runtime enforced four. Both gaps were closed before the final merge.

## 7. Duplicate-source amplification is forbidden

Different Host re-entry occurrences around the same exact source produce different `ContinuationInput` identities, because delivery history is real history. They do not become independent semantic grounds.

`SuccessorResolutionLineage` therefore rejects duplicate `source_identity` values even when the corresponding re-entry occurrences differ.

```text
same exact source + re-entry A
same exact source + re-entry B
    !=
two independent continuation sources
```

This prevents one Outcome, WorkerResult, BindingIssue, CapabilityMatchIssue, or Governance component from being amplified by repeated submission.

## 8. Original intent and branch lineage remain exact

Every continuation input in one B2 lineage must mechanically descend from the exact predecessor `ResolvedIntent.identity`.

```text
same IntentRequest != same ResolvedIntent branch
```

The successor must preserve the predecessor's exact original `IntentRequest.identity`. Its ContextEnvelope may remain the same or change only through separately admitted context semantics; B2 does not create or mutate Context itself.

## 9. Canonical identity and frozen representative chain

M1.7 continues the M1 canonical JSON SHA-256 identity model and preserves all earlier frozen golden identities.

The representative independently reconstructed B2 chain freezes:

```text
predecessor ResolvedIntent
6b6dc4d65e6954657b13d0fc93038baa2a83399ae81dc48f5e34019e6612919b

BindingIssue
4ecaa5cae8cac4b13c6546ec5dd8bcf0306be479627ca62a879881991b77ba8f

ContinuationInput
99a3efdccfe00a721db11d24b01d37c898c17ce984ed27ade2e735e717ac4046

successor ResolvedIntent
ae49c4e3c6f58186cf8c77a6b9bcf497a01cb24828e76260764077bf345aa83f

SuccessorResolutionLineage
d747c722833e1ef1a19af5dc4a30ac5d6b9dddca710ea2aa98ae3ca1d44196a9
```

Those literal sentinels were independently calculated before final merge and then checked against the project encoder on Python 3.11–3.14.

## 10. What M1.7 deliberately does not add

M1.7 closes representational lifecycle semantics, not autonomous recovery policy.

It does not add:

- automatic retry eligibility;
- retry scheduling or loops;
- fallback selection;
- capability/provider/executor substitution policy;
- Authorization renewal or inheritance;
- idempotency inference;
- cancellation or compensation policy;
- parent intent completion evaluator;
- successor WorkPlan construction;
- ambient Observation/retrieval;
- persistence/event sourcing;
- transport orchestration.

Therefore:

```text
Outcome != retry decision
Continuation != retry
lineage != recovery policy
new semantic information != automatic fallback authority
old Authorization != successor Authorization
```

## 11. Verification

All completed M1.7 slices and hardening passed the repository CI matrix on:

```text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

The final exact M1.7b2 head was reviewed after all hardening and frozen goldens; the current-head automated review reported no major issues before merge.

The full suite continued executing earlier M1 frozen goldens, so M1.7 did not silently redefine M1.1–M1.6 canonical bytes.

## 12. M1.7 closure invariants

```text
Attempt != Outcome
Outcome lifecycle != Outcome completion
Outcome completion != effect certainty
interrupted != failed
unknown completion/effect != failed
not_satisfied != no effect
Retry != mutation of an Attempt
ContinuationInput != Retry
source production != Host re-entry
one source re-submitted many times != many independent lineage inputs
predecessor Resolution admission != source / re-entry / successor admission
successor Resolution lineage != causal proof
successor Resolution lineage != Authorization
successor Resolution lineage != WorkPlan
successor ResolvedIntent != successor WorkPlan
old Authorization != successor Authorization
```

With these boundaries frozen, **M1.7 is closed** and implementation proceeds to **M1.8 — Executable M0.10 Fixtures & M1 Closure**.
