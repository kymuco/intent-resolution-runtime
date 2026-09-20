# M3.0.10 — Persistent Deduplicated First-Dispatch Prerequisite

## Goal

Freeze the smallest IRR prerequisite required before any later capability-specific
deduplicated recovery can be modeled safely.

Exact base:

~~~text
intent-resolution-runtime/main
b07017feeed597b641138116428034c40cd1a660
~~~

M3.0.10 does **not** add retry execution.

It freezes:

1. one explicit downstream persistent deduplication contract;
2. explicit candidate/admission lineage for that contract;
3. one stable idempotency key derived from the exact admitted contract and the exact
   original CapabilityAttempt;
4. one non-canonical first-dispatch mechanism request that carries that exact key.

The purpose is to ensure that a future recovery path can prove which external key
protected the original dispatch.

## Frozen recovery constraints

M0.9 remains authoritative:

~~~text
retry = new attributable CapabilityAttempt
retry != same Attempt resuming
unknown outcome != automatic retry
Authorization != retry safety
~~~

Therefore M3.0.10 does not permit replay of the same exact CapabilityAttempt and does
not
reinterpret M3.4 ALREADY_PRESENT as permission to reinvoke.

A future recovery Attempt will be a new Attempt.

However, a new recovery Attempt must **not independently derive a new idempotency
key** if
it is intended to deduplicate against the original ambiguous dispatch.

Future recovery semantics must explicitly reference the original key created and
transported by M3.0.10.

~~~text
original Attempt
→ original admitted dedup contract
→ original idempotency key
→ first external dispatch

future recovery Attempt
→ new Attempt identity
→ explicit recovery lineage
→ reuse original key
~~~

The recovery-lineage relation itself is deliberately out of scope for M3.0.10.

## Why the key must exist on the first dispatch

M3.4's frozen ordinary request contains only:

~~~text
CapabilityInvocationRequest
└── attempt
~~~

It deliberately has no idempotency-key protocol.

Therefore creating an idempotency key only after an ambiguous Outcome would be
insufficient:

~~~text
first dispatch without key
→ ambiguous effect
→ derive key after crash
→ resend with key

!= proof that the second send deduplicates against the first send
~~~

M3.0.10 introduces a separate mechanism request:

~~~text
DeduplicatedCapabilityInvocationRequest
├── attempt
├── admitted_contract
└── idempotency_key
~~~

The request has no SCHEMA, canonical identity, or canonical bytes. It is Host mechanism
state, not a second lifecycle record.

M3.0.10 does not invoke an Executor. A later Host integration boundary must transport
this request on the first external dispatch for capabilities that want persistent
deduplication
recovery semantics.

## Persistent guarantee only

M3.0.10 intentionally supports only a strong persistent exact-key guarantee.

It does not model:

- TTL;
- deduplication window;
- expiry;
- clocks;
- timestamps;
- retry counts;
- provider-specific temporal heuristics.

Finite windows would reopen clock authority, expiry interpretation, restart timing, and
race semantics before there is concrete product evidence that they are needed.

The admitted downstream contract states that submissions inside one exact deduplication
domain carrying one exact idempotency key are suppressed to at most one protected target
effect.

Incompatible reuse of that exact key must not create a second protected target effect.

This is a declared downstream contract, not empirical verification of the external
system.

## Explicit downstream contract

Frozen M0.9 says idempotency must not be inferred from:

- identical request bytes;
- deterministic names;
- HTTP verbs;
- an `idempotent=true` flag;
- a final state that merely looks idempotent.

M3.0.10 therefore introduces:

~~~text
PersistentDeduplicatedReinvocationContract
~~~

bound to the exact:

- Capability Catalog Snapshot identity;
- capability_ref;
- capability contract identity;
- executor_ref;
- deduplication_domain_ref;
- downstream supplier attribution.

The supplier attribution is provenance, not source verification.

~~~text
supplier_ref != proof the supplier is truthful
declared contract != observed external guarantee
~~~

## Explicit admission

A raw downstream contract is insufficient.

The contract must flow through:

~~~text
PersistentDeduplicatedReinvocationContract
        ↓
CandidatePersistentDeduplicationContract
        ↓
AdmittedPersistentDeduplicationContract
~~~

Admission has its own resolver and occurrence.

The admitted contract must equal one exact candidate contract.

Contract occurrence, proposal occurrence, and admission occurrence remain distinct.

Only `AdmittedPersistentDeduplicationContract` may derive an idempotency key.

~~~text
raw contract != admitted contract
attributed contract != retry permission
admitted contract != Authorization
~~~

## Exact capability lineage

Before deriving a key, IRR requires the admitted contract to match the exact
CapabilityAttempt lineage:

~~~text
contract.catalog_snapshot_identity
==
attempt.capability_match.catalog_snapshot.identity

contract.supplier_ref
==
attempt.capability_match.catalog_snapshot.attribution.supplier_ref

contract.capability_ref
==
attempt.capability_match.capability_ref

contract.capability_contract_identity
==
attempt.capability_match.capability_contract_identity
~~~

M3.0.10 additionally requires exactly one explicit EXECUTOR boundary in the matched
CapabilityDescriptor.

~~~text
0 EXECUTOR boundaries
→ not eligible for persistent dedup key derivation

1 EXECUTOR boundary
→ contract.executor_ref
  == descriptor boundary_ref
  == attempt.executor_ref

>1 EXECUTOR boundaries
→ fail closed
~~~

SERVICE, ADAPTER, PROVIDER, and OTHER_EXPLICIT boundaries are not silently reinterpreted
as an Executor.

## Original idempotency key

The canonical `CapabilityIdempotencyKey` contains:

~~~text
admitted_contract_identity
original_attempt_identity
deduplication_domain_ref
~~~

Its external token is the key record's canonical identity digest.

Therefore:

~~~text
same admitted contract + same original Attempt
→ same key

different original Attempt
→ different independently-derived key

different contract admission
→ different key

different dedup domain
→ different key
~~~

The second statement does **not** define future recovery behavior.

A future recovery Attempt must not derive a fresh key merely because it is a new
Attempt.
It must explicitly inherit the original key through a future recovery-lineage contract.

## M3.4 remains frozen

M3.0.10 does not modify:

- CapabilityInvocationRequest;
- ExecutorPort;
- invoke_executor(...);
- M3.4 replay blocking;
- M3.4 pre-dispatch Attempt persistence.

Ordinary M3.4 dispatch remains valid but carries no persistent-dedup recovery guarantee.

~~~text
ordinary M3.4 invocation
!= deduplicated first dispatch

deduplicated first-dispatch request
!= retry authority
~~~

A later HDE/Host integration milestone may compose M33-style durable dispatch commitment
with the M3.0.10 request, but must not infer that historical ordinary M3.4/M33.11
dispatches were protected by a key they never carried.

## No retry surface

M3.0.10 adds no:

- retry function;
- reinvocation function;
- resend function;
- Executor call;
- Outcome construction;
- recovery scheduler;
- fallback selection;
- Authorization reuse;
- recovery Attempt construction;
- continuation selection.

Public derivation/build helpers accept only:

~~~text
admitted_contract
attempt
~~~

They produce key/request material only.

## Canonical vs mechanism state

Canonical IR:

- PersistentDeduplicationContractAttribution;
- PersistentDeduplicatedReinvocationContract;
- PersistentDeduplicationContractProposalAttribution;
- CandidatePersistentDeduplicationContract;
- PersistentDeduplicationContractAdmissionAttribution;
- AdmittedPersistentDeduplicationContract;
- CapabilityIdempotencyKey.

These are closed IR types with canonical serialization and stable identity.

Mechanism state:

- DeduplicatedCapabilityInvocationRequest.

The request is immutable but deliberately has no canonical identity.

## PASS

1. raw downstream contract cannot derive a key;
2. explicit candidate provenance is required;
3. admitted contract equals one exact candidate contract;
4. contract/proposal/admission occurrences are distinct;
5. catalog snapshot identity matches exact Attempt lineage;
6. supplier matches exact Catalog supplier;
7. capability_ref matches exact CapabilityMatch;
8. capability contract identity matches exact CapabilityMatch;
9. exactly one explicit EXECUTOR boundary is required;
10. contract executor_ref equals descriptor Executor boundary;
11. contract executor_ref equals Attempt executor_ref;
12. same admitted contract + same original Attempt derives one stable key;
13. different fresh Attempt derives a different independently-derived key;
14. different admission identity changes the key;
15. first-dispatch request carries the exact derived key;
16. forged key cannot be inserted into first-dispatch request;
17. request is mechanism state, not canonical IR;
18. canonical records roundtrip with exact identity;
19. no TTL/window/clock/retry-count surface exists;
20. no retry/reinvoke/resend/Executor API is introduced.

## FAIL

- raw contract is sufficient for key derivation;
- self-asserted idempotency flag is accepted;
- Catalog supplier lineage may drift;
- capability contract may drift;
- Executor may be selected from multiple explicit boundaries;
- non-Executor boundary substitutes for Executor identity;
- key is first created only after an ambiguous dispatch;
- first-dispatch request accepts a forged key;
- new recovery Attempt is told to derive a new key;
- M3.0.10 reinvokes an Executor;
- finite dedup window semantics are silently invented;
- admitted dedup contract is treated as Authorization.

## EXIT

M3.0.10 is complete when IRR can represent and admit one exact downstream persistent
deduplication guarantee, derive one stable key for one exact original CapabilityAttempt,
and build first-dispatch mechanism state carrying that key, while adding no retry
execution or recovery-attempt semantics.

Only after this prerequisite is closed should a later milestone define explicit recovery
lineage from a new retry Attempt back to the original key.
