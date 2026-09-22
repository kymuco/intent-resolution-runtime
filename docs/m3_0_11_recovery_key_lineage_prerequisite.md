# M3.0.11 — Recovery Key Lineage Prerequisite

## Goal

Freeze the smallest canonical lineage required before any later Host can safely consider
reinvoking an ambiguous persistent-dedup capability Attempt.

Exact base:

~~~text
intent-resolution-runtime/main
0b3dca86041e4ef3ac96002c6acec131dc99066e
~~~

M3.0.11 does **not** retry, resend, or invoke an Executor.

It freezes:

1. a canonical binding of one exact M3.0.10 first-dispatch request;
2. a canonical lineage from one new recovery Attempt back to that binding;
3. exact inheritance of the original idempotency key;
4. non-canonical recovery invocation material carrying that inherited key.

## Frozen predecessor semantics

M3.0.10 established:

~~~text
admitted persistent dedup contract
+ original CapabilityAttempt
→ original CapabilityIdempotencyKey
→ DeduplicatedCapabilityInvocationRequest
→ STOP before Executor
~~~

M0.9 remains authoritative:

~~~text
retry = new attributable CapabilityAttempt
retry != same Attempt resuming
unknown outcome != automatic retry
~~~

Therefore M3.0.11 must satisfy both:

~~~text
recovery Attempt identity != original Attempt identity
recovery key == original key
~~~

A new recovery Attempt must never independently derive a new key when it is intended to
deduplicate against the original external effort.

## Why a canonical first-dispatch binding is required

The M3.0.10 `DeduplicatedCapabilityInvocationRequest` is deliberately mechanism state:

- no SCHEMA;
- no canonical identity;
- no canonical bytes.

If M3.0.11 merely re-derived the key from the original Attempt after a crash, it would
not establish which exact Attempt/contract/key tuple had been prepared for first
dispatch.

M3.0.11 therefore introduces:

~~~text
OriginalDeduplicatedDispatchBinding
~~~

built only from one exact M3.0.10 `DeduplicatedCapabilityInvocationRequest`.

The binding canonically contains:

- exact original CapabilityAttempt;
- exact admitted persistent deduplication contract;
- exact original CapabilityIdempotencyKey;
- explicit binding attribution and occurrence.

The binding validates the exact M3.0.10 relation again.

~~~text
ordinary CapabilityInvocationRequest
!= key-protected first-dispatch binding
~~~

Historical ordinary M3.4 requests cannot be retroactively promoted into deduplicated
first-dispatch state.

## Binding is not proof of external dispatch

The canonical binding proves only:

~~~text
this exact Attempt
+ this exact admitted dedup contract
+ this exact key
were bound together for deduplicated first-dispatch mechanism state
~~~

It does **not** prove:

- that ExecutorPort.invoke was called;
- that bytes crossed a transport;
- that the external provider received the key;
- that an external effect occurred;
- that an Outcome is missing;
- that a retry is permitted.

Those are Host/runtime evidence questions.

A later HDE integration boundary must bind this IRR record to durable dispatch evidence
before any recovery execution can become eligible.

## Recovery Attempt

A recovery Attempt must be a genuinely new CapabilityAttempt:

~~~text
recovery_attempt.identity != original_attempt.identity
recovery_attempt.attempt_event_ref != original_attempt.attempt_event_ref
~~~

M3.0.11 does not reuse the original Attempt occurrence.

## Same concrete-use semantics

The recovery Attempt may have new provenance/permission wrappers, but it may not change
the concrete target effect protected by the original idempotency key.

M3.0.11 requires:

- same semantic CapabilityRequirement;
- same WorkStep ref;
- same exact bound inputs;
- same capability_ref;
- same capability contract identity;
- same executor_ref.

The semantic CapabilityRequirement comparison ignores only fields named
`description`, recursively.

Everything else remains exact, including:

- WorkPlan/WorkStep refs and identities;
- operation;
- target scope values;
- requested scopes;
- requested effects;
- execution-boundary requirements;
- completion contracts;
- symbolic structure.

Therefore:

~~~text
description-only drift
→ permitted

target scope drift
→ rejected

requested effect drift
→ rejected

bound input drift
→ rejected

capability contract drift
→ rejected

executor drift
→ rejected
~~~

## Deliberately allowed provenance drift

M3.0.11 does not require the whole recovery CapabilityAttempt to be byte-identical to
the original.

A recovery path may legitimately obtain:

- a new Attempt occurrence;
- a new CapabilityMatchEvaluation occurrence;
- a new Catalog snapshot containing the same exact capability contract identity;
- new Authorization provenance;
- different narrative descriptions.

These do not themselves define a different protected target effect.

M3.0.11 does not decide whether any new Authorization is sufficient or whether recovery
permission exists. Permission remains a separate boundary.

## Recovery key lineage

The canonical `RecoveryKeyLineage` contains:

~~~text
RecoveryKeyLineageAttribution
OriginalDeduplicatedDispatchBinding
new recovery CapabilityAttempt
inherited original CapabilityIdempotencyKey
~~~

The inherited key must be byte-for-byte the exact key stored in the original dispatch
binding.

~~~text
recovery key != newly derived key
recovery key == original key
~~~

The lineage occurrence must differ from:

- original binding occurrence;
- original Attempt occurrence;
- recovery Attempt occurrence;
- admitted dedup-contract admission occurrence;
- selected and candidate downstream-contract occurrences;
- candidate proposal occurrences.

## Recovery invocation mechanism state

M3.0.11 also introduces:

~~~text
DeduplicatedRecoveryInvocationRequest
~~~

containing:

- exact recovery Attempt;
- exact RecoveryKeyLineage;
- exact inherited original idempotency key.

Like the M3.0.10 first-dispatch request, this is mechanism state:

- immutable;
- no SCHEMA;
- no canonical identity;
- no canonical bytes.

It does not invoke an Executor.

## Ambiguity is intentionally outside M3.0.11

Pure IRR has no canonical record for:

~~~text
dispatch committed
+ no durable Outcome
~~~

M3.4 intentionally treats missing Outcome after dispatch as a mechanism/runtime
ambiguity,
not as a synthetic CapabilityOutcome.

Therefore M3.0.11 does not accept or manufacture:

- CapabilityOutcome;
- `OUTCOME_UNKNOWN` boolean;
- retry eligibility;
- transport-failure claims;
- dispatch-history claims.

~~~text
RecoveryKeyLineage != proof of ambiguity
RecoveryKeyLineage != retry permission
RecoveryKeyLineage != Authorization
RecoveryKeyLineage != dispatch commitment
~~~

A Host/HDE boundary must prove those facts separately.

## Occurrence separation

`OriginalDeduplicatedDispatchBinding.binding_event_ref` must differ from:

- original Attempt occurrence;
- selected admitted-contract admission occurrence;
- every candidate proposal occurrence;
- every candidate downstream-contract occurrence.

`RecoveryKeyLineage.lineage_event_ref` must differ from:

- original dispatch binding occurrence;
- original Attempt occurrence;
- recovery Attempt occurrence.

This prevents one occurrence from silently playing multiple semantic roles.

## Canonical vs mechanism state

Canonical IR:

- OriginalDeduplicatedDispatchBindingAttribution;
- OriginalDeduplicatedDispatchBinding;
- RecoveryKeyLineageAttribution;
- RecoveryKeyLineage.

These are closed canonical IR types with stable identities.

Mechanism state:

- DeduplicatedRecoveryInvocationRequest.

The mechanism request is deliberately not canonical lifecycle IR.

## PASS

1. ordinary M3.4 CapabilityInvocationRequest cannot create a first-dispatch binding;
2. exact M3.0.10 deduplicated request creates one canonical binding;
3. binding preserves exact original Attempt/admitted contract/key;
4. binding occurrence cannot alias protected predecessor occurrences;
5. recovery Attempt must have a new identity;
6. recovery Attempt must have a new attempt occurrence;
7. description-only drift does not create false incompatibility;
8. semantic CapabilityRequirement drift fails closed;
9. WorkStep ref drift fails closed;
10. bound-input drift fails closed;
11. capability_ref drift fails closed;
12. capability contract identity drift fails closed;
13. executor_ref drift fails closed;
14. recovery lineage inherits the exact original key;
15. forged inherited key fails closed;
16. lineage occurrence is distinct from binding/original/recovery occurrences;
17. canonical binding/lineage roundtrip preserves exact identity;
18. recovery invocation mechanism state preserves exact lineage/Attempt/key;
19. recovery invocation request is non-canonical;
20. no ambiguity/retry/resend/Executor/Authorization surface is introduced.

## FAIL

- historical ordinary M3.4 dispatch is treated as key-protected;
- original key is re-derived after the fact without a first-dispatch binding;
- same CapabilityAttempt occurrence is reused as recovery;
- recovery changes target scope or requested effect;
- recovery changes concrete bound inputs;
- recovery changes capability contract or executor;
- recovery derives a fresh idempotency key;
- lineage itself claims Outcome ambiguity;
- lineage itself grants retry permission;
- M3.0.11 invokes an Executor;
- M3.0.11 reuses Authorization by implication.

## EXIT

M3.0.11 is complete when IRR can canonically anchor one exact M3.0.10 key-protected
first-dispatch request and link one new same-concrete-use recovery Attempt to the
original
idempotency key, while stopping before any external reinvocation.

The next Host/HDE milestone may combine this lineage with durable dispatch ambiguity,
fresh recovery permission, and a real Executor boundary. It must not infer those from
M3.0.11 itself.
