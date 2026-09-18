# M3.0.9 — Atomic CapabilityAttempt Use Admission Prerequisite

## Goal

Freeze the missing pre-effect authority boundary between an exact Authorization-backed
CapabilityAttempt and Executor invocation.

M3.4 already persists an exact CapabilityAttempt before invoking Executor and blocks
automatic replay of that same Attempt. That does **not** prevent two distinct Attempts
from consuming the same one-use Authorization condition.

M3.0.9 closes only that gap.

~~~text
exact APPLICABLE Authorization evidence
        +
exact CapabilityAttempt
        +
explicit condition use-mode evaluation
        ↓
resolved use policy
        ↓
atomic CapabilityAttempt use admission
        ├── reusable conditions: no exclusive claim
        └── exclusive_once conditions: exact canonical claim
        ↓
STOP before Executor
~~~

## Falsification target

Two distinct CapabilityAttempts may carry the same Authorization and differ only in their
attempt occurrence. M3.4 history persistence accepts both because their identities differ.

M3.0.9 must make this impossible when an exact Authorization condition has been explicitly
classified EXCLUSIVE_ONCE.

## No directive-text interpretation

IRR does not infer use mode from GovernanceDirective.semantic_type, scope, statement,
time, Host history, or arbitrary string conventions.

Every Authorization condition receives one explicit
AuthorizationConditionUseAssessment with one mode:

- REUSABLE
- EXCLUSIVE_ONCE
- UNKNOWN

The assessment set must exactly cover the Authorization conditions.

~~~text
semantic_type == "one_use"
!= automatic EXCLUSIVE_ONCE

directive text
!= use-policy fact

Host preference
!= use-policy authority
~~~

UNKNOWN makes the use policy UNRESOLVED and therefore cannot produce a
CapabilityAttemptUseAdmission.

## Exact exclusive claim

For every EXCLUSIVE_ONCE assessment, IRR derives the claim key mechanically from:

~~~text
Authorization.identity
+
GovernanceDirective.directive_ref
~~~

The caller does not supply or override the claim key.

This prevents two different Attempts from avoiding exclusion by choosing different
Host-generated reservation identifiers.

The same directive_ref on two different Authorization identities does not alias.

## Admission material

CapabilityAttemptUseAdmission binds:

- one exact CapabilityAttempt;
- one exact APPLICABLE AuthorizationApplicabilityEvaluation;
- one exact RESOLVED AuthorizationUsePolicyEvaluation;
- the exact shared use-context ref and identity;
- one distinct admission occurrence;
- the exact derived EXCLUSIVE_ONCE claims.

The Attempt must present exactly the Authorization evaluated by both evaluations.

Construction is not durable activation:

~~~text
CapabilityAttemptUseAdmission construction
!= repository admission
!= Executor invocation
!= effect
~~~

## Atomic repository contract

CapabilityAttemptUseAdmissionRepository admits one complete use atomically.

Possible results:

- ADMITTED
- ATTEMPT_ALREADY_ADMITTED
- EXCLUSIVE_CLAIM_CONFLICT

For a fresh Attempt the repository must either:

1. commit the Attempt admission and every derived exclusive claim together; or
2. commit nothing.

A conflict on any one claim must not leak the remaining claims.

The reference in-memory repository serializes admission with a lock so concurrent
competing Attempts demonstrate exactly-one admission behavior. Production Hosts may use
a durable transactional store, but must preserve the same atomic contract.

## Relationship to M3.4

M3.0.9 does not invoke Executor and does not modify M3.4.

M3.4 currently protects:

~~~text
same exact CapabilityAttempt
→ no automatic reinvocation
~~~

M3.0.9 adds:

~~~text
different CapabilityAttempts
+ same EXCLUSIVE_ONCE Authorization condition
→ at most one admitted use
~~~

A later Host integration boundary must require exact durable use admission before
crossing ExecutorPort.

## Frozen invariants

~~~text
Authorization admission != applicability
applicability != use-mode classification
SATISFIED != reusable
SATISFIED != exclusive_once
directive text != use-mode fact
use-policy evaluation != use admission
use-admission construction != durable activation
Attempt identity != exclusive-use identity
same Attempt replay != distinct competing Attempt
exclusive claim conflict != retry authority
atomic use admission != Executor invocation
CapabilityAttempt != effect
~~~

## PASS

1. use-policy assessment exactly covers Authorization conditions;
2. UNKNOWN policy classification fails closed;
3. IRR never parses GovernanceDirective text into a use mode;
4. exclusive claims are derived only from Authorization identity + directive ref;
5. caller cannot omit a derived exclusive claim;
6. exact Attempt replay is not a second admission;
7. distinct Attempts with reusable conditions can both admit;
8. distinct Attempts sharing one exclusive claim cannot both admit;
9. multi-claim conflict is all-or-nothing;
10. concurrent competing Attempts produce exactly one ADMITTED result;
11. same directive ref under different Authorization identities does not alias;
12. exact canonical roundtrip preserves derived claims;
13. no ExecutorPort call, CapabilityOutcome, retry, fallback, or effect occurs.

## FAIL

- semantic_type/scope/statement is parsed to infer EXCLUSIVE_ONCE;
- Host supplies an arbitrary exclusivity key;
- partial condition use-policy coverage is accepted;
- UNKNOWN is treated as reusable;
- a caller can construct an admission while omitting an exclusive claim;
- a conflict leaves another claim reserved;
- two competing Attempts can both admit the same exclusive claim;
- repository admission invokes Executor;
- M3.0.9 claims exactly-once external effects.

## EXIT

M3.0.9 is complete when exact Authorization-backed CapabilityAttempt use admission can
atomically exclude competing uses across distinct Attempts without interpreting directive
text or crossing the Executor boundary.

The next HDE milestone may integrate this canonical prerequisite into a durable Host-side
store and replay boundary before Executor.
