# M3.0.9 — Atomic CapabilityAttempt Use Admission Prerequisite

## Goal

Freeze the missing pre-effect authority boundary between an exact Authorization-backed
CapabilityAttempt and Executor invocation.

M3.4 already persists an exact CapabilityAttempt before invoking Executor and blocks
automatic replay of that same Attempt. That does **not** prevent two distinct Attempts
from targeting the same exact concrete use, nor does it prevent distinct concrete uses
from consuming the same one-use Authorization condition.

M3.0.9 closes exactly those two pre-effect admission gaps.

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
        ├── exact use-context claim: always
        ├── reusable conditions: no Authorization-level exclusive claim
        └── exclusive_once conditions: exact Authorization-level claim
        ↓
STOP before Executor
~~~

## Falsification target

Two distinct CapabilityAttempts may differ only in their attempt occurrence while still
targeting the same exact concrete use. M3.4 history persistence accepts both because their
Attempt identities differ.

M3.0.9 must ensure that one exact use-context can admit at most one Attempt regardless of
whether the Authorization is reusable.

Separately, two different use-contexts may still carry the same Authorization. When an
exact Authorization condition is explicitly classified EXCLUSIVE_ONCE, at most one of
those distinct uses may be admitted.

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

REUSABLE and EXCLUSIVE_ONCE are positive authority-relevant classifications and must
reference at least one evidence_ref. UNKNOWN may preserve an empty evidence set.

## Exact concrete-use claim

Every CapabilityAttemptUseAdmission mechanically derives one CapabilityUseContextClaim
from the exact content-bound:

~~~text
use_context_identity
~~~

The StableRef remains trace metadata in applicability/admission lineage, but it is not
part of the exclusivity key. Therefore aliasing the same exact use-context identity under
a different ref cannot create a second claim.

This claim exists for every admitted use, including unconditional and REUSABLE
Authorizations.

The caller cannot supply or override it.

Therefore:

~~~text
same exact use-context
+ different CapabilityAttempt occurrences
→ at most one admitted Attempt

REUSABLE Authorization
!= permission to duplicate one concrete use
!= retry authority
~~~

A new concrete use must have a distinct exact use-context. IRR does not decide whether two
real-world situations are the same concrete use; the Host integration must construct and
content-bind the use-context correctly.

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
- one exact derived concrete-use claim;
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
- ATTEMPT_ADMISSION_CONFLICT
- AUTHORIZATION_POLICY_CONFLICT
- USE_CONTEXT_CONFLICT
- EXCLUSIVE_CLAIM_CONFLICT

For a fresh Attempt the repository must commit the Attempt admission, the exact
use-context claim, and every derived Authorization-level exclusive claim in one atomic
critical section, or commit nothing.

The repository also freezes one normalized condition-mode mapping per Authorization on
the first successful use admission. A later Attempt that presents a different mapping
for the same Authorization fails closed with AUTHORIZATION_POLICY_CONFLICT. The
normalized policy identity excludes evaluator occurrence and evidence details and commits
only to Authorization identity plus exact directive_ref → mode semantics.

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
+ same exact use-context
→ at most one admitted Attempt

different exact use-contexts
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
Attempt identity != concrete-use identity
concrete-use claim != Authorization-level exclusive claim
same Attempt replay != distinct competing Attempt
REUSABLE != retry authority
use-context conflict != retry authority
exclusive claim conflict != retry authority
atomic use admission != Executor invocation
CapabilityAttempt != effect
~~~

## PASS

1. use-policy assessment exactly covers Authorization conditions;
2. UNKNOWN policy classification fails closed;
3. REUSABLE and EXCLUSIVE_ONCE require explicit evidence provenance;
4. IRR never parses GovernanceDirective text into a use mode;
5. one exact use-context claim is mechanically derived for every admission;
6. caller cannot omit or redirect the exact use-context claim;
7. ref aliases of one exact use-context identity resolve to the same claim;
8. two distinct Attempts for the same exact use-context cannot both admit, even when
   Authorization conditions are REUSABLE;
9. distinct exact use-contexts may both admit under stable REUSABLE policy;
10. Authorization-level exclusive claims are derived only from Authorization identity +
   directive ref;
11. caller cannot omit or redirect a derived Authorization-level exclusive claim;
12. distinct exact use-contexts sharing one EXCLUSIVE_ONCE claim cannot both admit;
13. only an exact same CapabilityAttemptUseAdmission is replay; the same Attempt with
    changed admission lineage fails closed;
14. applicability, use-policy, use-admission, and embedded Attempt prerequisite
    occurrences remain distinct;
15. Authorization use-policy semantics cannot drift after first admitted use;
16. concurrent same-use Attempts produce exactly one ADMITTED result;
17. concurrent distinct-use Attempts sharing one exclusive claim produce exactly one
    ADMITTED result;
18. same directive ref under different Authorization identities does not alias;
19. exact canonical roundtrip preserves the derived use-context and exclusive claims;
20. no ExecutorPort call, CapabilityOutcome, retry, fallback, or effect occurs.

## FAIL

- semantic_type/scope/statement is parsed to infer EXCLUSIVE_ONCE;
- Host supplies an arbitrary concrete-use or Authorization-level exclusivity key;
- partial condition use-policy coverage is accepted;
- REUSABLE or EXCLUSIVE_ONCE is accepted without evidence provenance;
- UNKNOWN is treated as reusable;
- a caller can construct an admission while omitting the exact use-context claim;
- a caller can construct an admission while omitting an Authorization-level exclusive claim;
- two different Attempts can both admit the same exact use-context;
- two different use-contexts can both admit the same EXCLUSIVE_ONCE claim;
- a failed admission leaks any claim or admission state;
- the same Attempt with changed admission lineage is treated as exact replay;
- repository admission invokes Executor;
- M3.0.9 claims exactly-once external effects.

## EXIT

M3.0.9 is complete when exact Authorization-backed CapabilityAttempt use admission can
atomically exclude duplicate Attempts for one exact concrete use and independently exclude
competing concrete uses for EXCLUSIVE_ONCE Authorization conditions, without interpreting
directive text or crossing the Executor boundary.

The next HDE milestone may integrate this canonical prerequisite into a durable Host-side
store and replay boundary before Executor.
