# M0.9 — Failure, Retry & Unknown Outcome Boundary

Status: **normative for M0.9**.

This document freezes how Intent Resolution Runtime (IRR) and its downstream boundaries reason about success, failure, blocking, interruption, uncertain effects, retry, fallback, cancellation, and compensation without turning transport ambiguity into duplicated external effects or allowing recovery logic to widen semantics, capabilities, disclosure, or authority.

It extends M0.1 Product Charter & Vocabulary, M0.2 Trust/Context/Resolution Semantics, M0.3 Intent → Work Boundary, M0.4 Late Binding & Observation Boundary, M0.5 Capability Boundary, M0.6 Governance & Authority Boundary, M0.7 Cognitive Provider Boundary, and M0.8 Worker Delegation Boundary without introducing runtime code, exact Python enums, persistence schemas, retry schedulers, timeout constants, executor adapters, Worker orchestration, or M1 data models.

M0.9 answers one question:

> How may IRR continue after downstream work does not produce clean confirmed success without confusing failure with uncertainty or repeating an effect whose first attempt may already have happened?

The answer is:

> **Material downstream attempts and results remain attributable. Success, failure, blocking, interruption, and unknown outcome are distinct semantic conditions. A retry or executed fallback is a new Attempt, not harmless continuation. Unknown effectful outcome never implies automatic retry, and recovery never grants semantic, capability, disclosure, or authority expansion.**

Conceptually:

```text
admitted work / delegated work
          |
          v
pre-attempt boundaries
(capability / binding / authority / information)
          |
      +---+-----------------------------+
      |                                 |
      v                                 v
   blocked                         Attempt N
(no effect-attempt                   |
 required to exist)                  +----------------+----------------+----------------+
                                     |                |                |                |
                                     v                v                v                v
                                 succeeded         failed         interrupted    unknown_outcome
                                     |                |                |                |
                                     +----------------+----------------+----------------+
                                                      |
                                                      v
                                             recovery assessment
                                                      |
                                  +-------------------+-------------------+
                                  |                                       |
                                  v                                       v
                           no new Attempt                     Retry / executed fallback
                                                                      |
                                                                      v
                                                                 Attempt N+1
```

The diagram is conceptual, not a required flat state machine. `blocked` may exist before any effect-attempt begins or inside a larger lifecycle after earlier effects. `interrupted` describes lifecycle discontinuity, while effect/completion certainty is a separate semantic question; an interrupted lifecycle can have known effect state or materially unknown outcome. Exact runtime representation is deferred.

Central invariants:

```text
unknown_outcome != failed
failed != no effect
blocked != proof that an Attempt started
blocked != Denial
interrupted != no effect
transport timeout != proof of failure
lost acknowledgement != proof of no effect
retry != continuation of the same Attempt
retry != harmless repetition
executed fallback != continuation of the same Attempt
retry eligibility != Authorization
retry authorization != capability availability
retry authorization != retry safety
idempotency claim != duplicate-suppression guarantee
unknown effectful outcome != automatic retry
fallback != capability synthesis
fallback != semantic substitution authority
fallback != authority inheritance
worker failure != parent intent failure by definition
executor failure != intent invalidity
success != parent intent satisfaction by default
```

## 1. Outcome and recovery classification are scoped

An `Outcome` is an attributable downstream operational or lifecycle result for a specific bounded semantic scope.

That scope may conceptually be:

```text
one capability Attempt
one WorkStep execution Attempt
one delegated subordinate operation
one Worker subordinate lifecycle result
one bounded handoff lifecycle
```

A result for one scope MUST NOT silently become the result for a larger parent scope.

```text
Attempt success != WorkPlan success
WorkPlan success != parent intent satisfaction by default
Worker subtask success != parent intent satisfaction
```

Exact Outcome identifiers, wire schemas, digests, persistence, and state-machine layout are deferred.

## 2. Attempt

An `Attempt` is one attributable effort to perform one already admitted bounded downstream operation or delegated lifecycle transition.

An Attempt matters when a repeated effort could have a materially distinct result or effect history.

```text
Attempt N != Attempt N+1
```

A Retry is a new Attempt.

An executed fallback is also a new Attempt when it actually pursues the work through an alternate downstream path.

```text
retry Attempt N+1 != continuation of Attempt N
executed fallback != continuation of prior Attempt
```

A future representation must preserve enough lineage to distinguish attempts aimed at the same admitted semantic work.

Exact Attempt IDs, sequencing, digests, and persistence are deferred.

## 3. Blocking can exist before an Attempt

A required path may be unable to begin because a known prerequisite or boundary condition is unsatisfied.

Illustrative blockers include:

- `missing_capability`;
- known Capability unavailability;
- invocation unreadiness;
- missing required Context/Observation;
- unresolved Material Ambiguity;
- insufficient Authorization;
- explicit Denial for the relevant authority context;
- Worker escalation requiring information, scope, capability, or authority.

Such a path may be described as `blocked` without inventing a fake execution Attempt.

```text
blocked != proof that an Attempt started
blocked != failed Attempt by definition
```

A larger Worker/handoff lifecycle may also become blocked after earlier subordinate Attempts or effects already occurred. The blocker and prior effect history remain separate facts.

## 4. Blocking cause remains separately classified

`blocked` describes inability to proceed; it does not replace the semantic cause.

```text
blocked != Denial
blocked != missing_capability
blocked != Material Ambiguity
blocked != Capability unavailability
```

A Denial remains Governance material. `missing_capability` remains a capability-admission condition. Material Ambiguity remains a resolution condition.

Recovery MUST NOT collapse those distinctions merely to obtain one generic terminal label.

## 5. Transport activity is not semantic completion

A downstream system may expose states such as:

```text
request serialized
socket opened
request sent
server accepted connection
HTTP response received
ACK received
```

Those states do not automatically equal the Completion Semantics required by admitted work.

```text
transport success != semantic success
request accepted != requested effect completed by default
```

Capability/Worker contracts may later define stronger evidence, but transport convenience MUST NOT silently strengthen completion meaning.

## 6. `succeeded`

Conceptually, `succeeded` means sufficient attributable evidence establishes that a bounded Attempt satisfied the applicable Completion Semantics for its own Outcome scope.

```text
succeeded
    -> sufficient completion evidence for this scoped Attempt
```

This does not automatically prove:

- parent WorkPlan completion;
- parent intent satisfaction;
- factual truth of every returned Claim;
- continuing current-world state;
- Authorization correctness;
- future replay safety.

```text
succeeded != parent intent satisfied by default
succeeded != Authorization proof
historical success != current state guarantee
```

## 7. `failed`

Conceptually, `failed` means sufficient attributable evidence establishes that the bounded Attempt did not satisfy its required Completion Semantics.

Failure MUST NOT be interpreted as proof that no external effect occurred.

An operation can fail after producing partial or otherwise material effects.

Examples include conceptually:

```text
file write partially completed, then validation failed
remote operation created resource, then postcondition check failed
Worker produced some artifacts, then completion contract failed
process launched, then readiness check failed
```

Therefore:

```text
failed != no effect
failed != safe to retry
failed != automatic retry
```

Known partial effects remain attributable historical facts and are not erased by failure classification.

## 8. `interrupted`

Conceptually, `interrupted` means an in-progress Attempt or lifecycle stopped before its normal completion protocol finished.

Possible causes include:

```text
process termination
Worker cancellation
Host shutdown
network disconnection
session loss
operator stop
runtime crash
```

Interruption describes lifecycle discontinuity. It does not by itself establish whether the intended effect occurred.

```text
interrupted != no effect
interrupted != failed by definition
interrupted != unknown_outcome by definition
```

An interrupted local pure computation may have a known no-effect incomplete result. An interrupted remote send may have uncertain external effect status. Exact representation may later preserve both lifecycle interruption and effect certainty without forcing them into one mutually exclusive enum.

## 9. `unknown_outcome`

Conceptually, `unknown_outcome` means material attributable evidence is insufficient to establish whether the bounded effect or required Completion Semantics occurred.

```text
unknown_outcome != failed
```

Typical causes include:

```text
request may have reached remote service but acknowledgement was lost
process may have committed mutation before crash
Worker may have produced external side effect before transport failure
status source is unavailable and no independent evidence exists
```

Unknown outcome MUST preserve what is known and what remains unknown instead of collapsing uncertainty into a convenient failure label.

## 10. Unknown outcome is scoped to material uncertainty

Not every missing detail makes an entire lifecycle unknown.

The uncertainty must be material to the represented effect or Completion Semantics.

For example, if a capability independently proves that a file was atomically published at digest D but non-material telemetry acknowledgement was lost, the file-write Outcome need not become unknown merely because telemetry disappeared.

Conversely, if a missing acknowledgement is the only evidence that an external message became recipient-visible, effect status may remain unknown.

```text
missing telemetry != unknown semantic outcome by default
missing material effect evidence -> may require unknown_outcome
```

## 11. Timeout is not an Outcome by itself

A timeout is an attributable temporal/transport observation that an expected signal was not received within a bounded period.

```text
timeout != failed
timeout != unknown_outcome by definition
timeout != no effect
```

Correct classification depends on the remaining effect/completion evidence.

A timeout before an effect request was emitted may support a known blocked/failed condition under an explicit contract. A timeout after an external request may leave effect status unknown.

Exact timeout constants and mechanisms are deferred.

## 12. Lost acknowledgement is not proof of no effect

If an executor sends an effectful request and loses the acknowledgement, IRR MUST NOT infer:

```text
no ACK -> failed -> send again
```

unless an explicit downstream contract supplies stronger evidence.

```text
lost acknowledgement != proof of no effect
```

This is the canonical M0.9 duplicate-effect hazard.

## 13. Outcome evidence is attributable

Every material Outcome claim must be supported by attributable result/effect evidence appropriate to the claimed Completion Semantics.

A future record may conceptually preserve:

```text
Attempt lineage
reported condition/status
completion evidence
effect evidence
known partial effects
material uncertainty
source/provider/executor/Worker provenance
Temporal Basis when material
```

Exact fields are deferred.

A fluent Worker/Executor assertion does not amplify evidence beyond its admitted contract and provenance.

## 14. Executor assertion cannot strengthen its contract

An Executor may report `success` or `failure`.

IRR/Host may rely on that report according to the admitted downstream contract, but the semantic meaning remains bounded by that contract.

```text
executor says success != stronger completion than executor contract supports
executor says failure != proof of no effect
```

Where work requires stronger confirmation, a weaker result cannot silently satisfy it.

## 15. WorkerResult and Outcome remain distinct

M0.8 remains normative.

A `WorkerResult` is a broad delegated-result envelope. It may contain/reference zero, one, or many subordinate Outcomes.

```text
WorkerResult != Outcome by default
```

A Worker may complete an analysis deliverable while one subordinate effect remains unknown, or fail its delegated completion contract despite several successful subordinate operations.

Those semantics MUST NOT be collapsed.

## 16. Parent failure is not implied by child failure

Failure of one Attempt, WorkStep, Executor, Capability instance, or Worker does not automatically prove that the parent intent is invalid or globally impossible.

```text
executor failure != intent invalidity
Worker failure != parent intent failure by definition
Attempt failure != global impossibility
```

IRR Continuation may later determine whether another admitted path exists, clarification is needed, the parent is blocked, or a future lifecycle policy should terminate the parent.

## 17. Parent success is not implied by child success

Likewise:

```text
Attempt success != parent completion
Worker subtask success != parent completion
```

IRR retains parent Completion Semantics and evaluates them explicitly.

## 18. Retry

A `Retry` is a new attributable Attempt against the **same admitted semantic operation or delegated objective and the same material effect/completion semantics** as an earlier Attempt.

Non-material runtime details may differ only where their variation was already admitted and does not change resource, recipient, provider/service semantics, disclosure, effect surface, scope, cost/commitment, completion meaning, or authority requirements.

```text
Retry = new Attempt over unchanged admitted material semantics
retry != hidden loop
retry != same Attempt resuming
```

If material semantics change, the next path is not merely a Retry; it requires the applicable Continuation, fallback, successor, capability, and Governance handling.

## 19. Retry requires an explicit basis

IRR/downstream lifecycle logic MUST NOT retry merely because the prior Attempt did not report success.

A retry requires an explicit admitted basis appropriate to the effect surface.

Conceptually, recovery must determine at least:

```text
what is known about prior effect/completion
whether the same semantic work is still desired
whether duplicate/repeated effects are acceptable or prevented
whether Capability semantics remain valid
whether Bound Values/resources remain valid
whether applicable Authorization covers the new Attempt/effect
whether any runtime variation changes provider/service/scope/cost/disclosure
```

Exact algorithms are deferred.

## 20. Unknown effectful outcome never implies automatic retry

This rule is absolute at the M0.9 semantic boundary:

> **An effectful `unknown_outcome` MUST NOT be converted into automatic Retry merely because success was not confirmed.**

```text
unknown effectful outcome != automatic retry
```

A new Attempt may duplicate the first effect.

Examples include:

- duplicate Telegram messages;
- duplicate purchases;
- duplicate issue/comment creation;
- repeated external disclosure;
- duplicate process/job launch;
- repeated mutation;
- duplicate commit/push-like effects.

Recovery must first establish an explicit safe basis or remain unresolved/blocked.

## 21. Confirmed failure also does not imply Retry

Even confirmed `failed` classification does not itself establish replay safety.

The failed Attempt may have produced partial effects or changed preconditions.

```text
failed != automatic retry
```

Retry assessment uses effect history and current semantics, not the status label alone.

## 22. Retry Eligibility

`Retry Eligibility` is a bounded recovery determination that a new Attempt over unchanged admitted material semantics may be semantically admissible given the known prior effect state, replay/duplication properties, current binding/capability state, and recovery contract.

Retry Eligibility does not create permission.

```text
retry eligibility != Authorization
```

If the new Attempt performs authority-requiring work, applicable external Authorization coverage must exist under M0.6.

Prior Authorization does not automatically cover every Retry unless its external scope explicitly covers repeated Attempts.

```text
Authorization for Attempt N != Authorization for Attempt N+1 by default
```

## 23. Authorization is not Retry safety

Governance may authorize another Attempt, but that does not prove it is safe from duplicate effects or semantically valid.

```text
retry authorization != retry safety
Authorization != effect-state knowledge
```

Authority and recovery correctness remain separate.

## 24. Capability Availability is not Retry safety

A capability being online/callable does not prove replay safety.

```text
available capability != safe retry
```

Capability existence, Match, Availability, invocation readiness, Retry Eligibility, and Authorization remain distinct.

## 25. Idempotency

`Idempotency` is a semantic property under an explicit downstream contract that repeating an operation does not create an additional material effect beyond the intended stable result at the stated effect scope.

M0.9 does not infer idempotency merely because an API uses PUT/UPSERT, a deterministic function name, identical request bytes, or stable input.

```text
same request bytes != idempotent effect
same operation name != idempotent effect
```

Idempotency must be explicitly supported by the applicable capability/execution contract at the relevant material effect scope.

Exact representation is deferred.

## 26. Idempotency scope matters

An operation can be idempotent for one effect while repeating other material side effects.

For example, setting exact file contents may be idempotent with respect to final bytes while still creating repeated audit events, billing, notifications, timestamps, network calls, or disclosures.

```text
idempotent final state != no repeated side effects by default
```

A Retry policy must reason about the material effects actually relevant to the intent/Governance boundary.

## 27. Idempotency claim is not proof

A provider, Worker, Executor, or metadata field saying `idempotent=true` does not establish the property by itself.

```text
idempotency claim != idempotency guarantee by default
```

The property must come from an admitted attributable downstream contract or stronger evidence appropriate to that boundary.

## 28. Duplicate suppression

A downstream capability may support a bounded duplicate-suppression mechanism such as server-enforced request identity, idempotency key, exact CAS precondition, transaction identity, or another deduplication contract.

M0.9 freezes only the semantic requirement:

```text
dedup mechanism must cover the material effect being protected
```

A client-generated key the downstream service does not enforce is not duplicate-effect protection.

```text
idempotency key present != duplicate suppression guaranteed
```

Exact keys/tokens/protocols are deferred.

## 29. Safe replay evidence must be explicit

If a downstream contract can establish that reissuing an Attempt cannot duplicate the protected material effect, that may support Retry Eligibility.

Conceptual examples include:

```text
server-enforced request identity
CAS with exact expected-old value
transaction identity with durable deduplication semantics
pure side-effect-free computation over admitted immutable inputs
```

M0.9 does not declare these universally safe; the concrete admitted contract must support the claim.

## 30. Pure computation differs from effectful Retry

Repeating a deterministic side-effect-free computation over already admitted immutable inputs can have different recovery semantics from repeating an external mutation.

IRR MUST NOT assume purity from a name or implementation convention.

```text
analysis-like label != proof of purity
```

Purity/effect-free behavior follows from the applicable semantic contract.

## 31. Read-only Retry can still be material

A read-only operation may avoid mutation but can still:

- disclose data to a remote provider;
- incur cost;
- observe a changed world state;
- reveal information that changes later decisions;
- trigger rate limits/audit effects.

```text
read-only != universally harmless retry
```

M0.2/M0.4/M0.6 boundaries remain applicable.

## 32. Retry preserves Attempt history

A successful later Retry MUST NOT rewrite the earlier Attempt as successful.

```text
Attempt N failed/unknown
Attempt N+1 succeeded
    !=
Attempt N succeeded historically
```

Historical Outcome/effect evidence remains attributable.

## 33. Retry inputs must be revalidated when material

A Retry cannot blindly reuse stale Binding/capability assumptions.

Before a new Attempt, material conditions may require revalidation of:

```text
Bound Value Freshness
resource existence
Capability Match
Capability Availability
invocation readiness
provider/Worker identity
scope/disclosure semantics
Authorization applicability
```

Exact revalidation algorithms are deferred.

## 34. Retry cannot silently change semantics

If a next Attempt requires a materially different:

- resource;
- recipient;
- provider/service;
- capability;
- scope;
- disclosure;
- mutation surface;
- cost/commitment;
- completion meaning;
- authority basis;

then it is not merely Retry of the same admitted material semantics.

It returns through applicable IRR Continuation/successor/fallback/review boundaries.

```text
retry != permission for semantic mutation
```

## 35. Fallback

A `Fallback` is a proposed alternate downstream path after an earlier path is unavailable, blocked, failed, interrupted, or otherwise unsuitable.

Fallback is not capability synthesis and not semantic-substitution authority.

```text
fallback != capability synthesis
fallback != semantic substitution authority
```

M0.5/M0.8 remain normative.

## 36. Fallback selection requires explicit semantic basis

A fallback capability/provider/Worker may be selected without new parent semantics only when all material admitted dimensions remain equivalent or when an explicit previously admitted fallback/selection rule already governs the choice.

Material dimensions include at least:

```text
input/output semantics
effect surface
scope
disclosure
provider/service boundary
cost/commitment
completion semantics
trust/provenance handling
authority applicability
```

Otherwise fallback requires IRR Continuation/successor semantics.

## 37. Executed fallback is a new Attempt

Once an alternate fallback path is actually invoked, it becomes a new attributable Attempt with its own Outcome/effect history.

```text
fallback selection != effect
executed fallback -> new Attempt
```

The new Attempt does not merge with the failed/unknown/interrupted predecessor.

## 38. Fallback does not inherit authority

```text
Authorization for provider A != provider B by default
Authorization for Worker A != Worker B by default
```

A fallback path must independently remain inside applicable Authorization coverage.

```text
fallback != authority inheritance
```

## 39. Fallback does not erase prior unknown effects

If Attempt A has `unknown_outcome`, switching to fallback path B does not make A's possible effect disappear.

If B is executed, the parent history must preserve the possibility that both A and B effects may exist unless stronger evidence/deduplication guarantees establish otherwise.

```text
fallback after unknown != prior effect absent
```

This is especially important for sends, purchases, mutations, publication, process launches, and other non-idempotent operations.

## 40. Recovery is not goal improvisation

Recovery logic may not invent a smaller/different objective merely to achieve a terminal state.

```text
recovery convenience != intent reinterpretation
```

If attainable objective semantics change, IRR Continuation/successor resolution must make that change explicit.

## 41. Recovery does not bypass Material Ambiguity

Failure does not authorize guessing a new resource, recipient, executable, provider, or scope.

```text
failure != permission to guess
```

M0.2 remains normative.

## 42. Recovery does not bypass capability admission

Failure/uncertainty does not authorize shell/browser/arbitrary-code fallback when a required capability is missing or incompatible.

```text
failure != capability fallback authority
unknown_outcome != capability widening authority
```

M0.5 remains normative.

## 43. Recovery does not bypass Governance

Retry/fallback/recovery work does not become authorized merely because it attempts to repair an earlier problem.

```text
recovery objective != authority exemption
```

M0.6 remains normative.

## 44. Recovery does not bypass Worker boundaries

A Worker cannot self-retry an authority/effect Attempt beyond the DelegatedWork envelope merely because a previous Attempt failed.

Worker-local material Retry is permitted only where delegation, capability, effect, recovery, and authority contracts admit it.

```text
Worker retry != scope widening authority
```

M0.8 remains normative.

## 45. Worker internal pure iteration and external Retry are distinct

A Worker may internally repeat a pure computation as an implementation detail when it remains inside the bounded subordinate lifecycle and creates no new material effect.

That is distinct from reissuing a material downstream external Attempt.

```text
internal computation retry != external effect retry
```

M0.9 does not require every internal pure iteration to become an IRR Attempt record; it freezes that material external Attempts/effects cannot be hidden as internal retry behavior.

## 46. Cancellation

Cancellation is an attributable request/transition to stop further work.

Cancellation does not erase already produced effects and does not prove that an in-flight effect was prevented.

```text
cancel requested != effect prevented
cancel acknowledged != prior effects erased
```

Depending on evidence, cancellation may lead to known interruption/no-further-effect semantics or leave an in-flight effect materially unknown.

Exact cancellation protocol is deferred.

## 47. Revocation and Cancellation are distinct

Authorization revocation changes authority applicability.

Cancellation asks a lifecycle to stop.

```text
Authorization revoked != Cancellation delivered
Cancellation delivered != Authorization history erased
```

One MUST NOT be inferred from the other unless an explicit external contract establishes the relationship.

## 48. Unknown authority state is not unknown Outcome

M0.6 authority uncertainty and M0.9 effect uncertainty are separate semantic dimensions.

```text
unknown Authorization state != unknown_outcome
```

A system may know exactly that no effect Attempt occurred while authority is unresolved, or have unknown effect Outcome even though the Attempt was clearly authorized.

## 49. Capability unavailability is not failed Attempt by itself

A Capability being unavailable before an Attempt starts is normally a readiness/blocking condition, not evidence that an effectful Attempt failed.

```text
Capability unavailable != failed Attempt by default
```

If an Attempt began and provider availability disappeared mid-flight, evidence may instead support failed, interrupted, or unknown-outcome semantics.

## 50. `missing_capability` is not an Outcome

`missing_capability` is a planning/admission condition under M0.5.

```text
missing_capability != Outcome
```

It may cause a work path to be blocked without creating a fake downstream Attempt/Outcome.

## 51. Denial and `require_review` are not Outcomes

A Governance Denial or `require_review` decision concerns authority, not execution result.

```text
Denial != Outcome
require_review != Outcome
```

A denied/unreviewed operation may remain unattempted.

## 52. Clarification and candidate rejection are not failure Outcomes

```text
clarification_required != failure
Candidate rejection != Outcome
```

These belong to resolution/provider-admission boundaries, not downstream execution recovery.

## 53. Worker escalation is not Worker failure by definition

A Worker may correctly discover a need outside its DelegatedWork envelope and escalate.

```text
Worker escalation != Worker failure by definition
```

Escalation can be the correct bounded result of delegated work.

## 54. Partial effects remain explicit

If an Attempt is known to have produced some but not all intended effects, partial effect history remains explicit.

A future lifecycle representation may classify scoped completion as failed while separately preserving known partial effects.

```text
failed completion != erased partial effects
```

Recovery accounts for those effects before repeated or compensating work.

## 55. Compensation is not Retry

A compensating operation attempts to counteract/mitigate an earlier effect.

It is a distinct new semantic operation, not Retry of the original Attempt.

```text
compensation != retry
```

Compensation requires its own Capability Match, effect representation, and applicable Authorization.

M0.9 does not freeze automatic compensation algorithms.

## 56. Rollback is not historical erasure

Even when later work restores external state, the earlier effect and rollback remain historical facts.

```text
rollback success != original effect never happened
```

This preserves audit/provenance semantics.

## 57. Unknown Outcome may require new Observation

Resolving `unknown_outcome` may require a bounded attributable Observation, status query, receipt lookup, or other evidence-gathering operation.

The evidence need does not grant authority to acquire it.

```text
unknown outcome evidence need != observation authority
```

Any acquisition path remains subject to Context/Capability/Governance boundaries.

## 58. Recovery status query is a separate operation

Examples include:

```text
query message by request identity
read transaction receipt
inspect remote resource state
check process existence
```

Such a status check is a separate semantic operation with its own capability/effect/disclosure semantics.

```text
recovery status need != ambient query authority
```

## 59. New evidence may refine Outcome classification

An earlier `unknown_outcome` may later become known when new attributable evidence arrives.

Conceptually:

```text
unknown_outcome at T1
        |
new attributable evidence at T2
        |
IRR / lifecycle continuation
        |
refined known effect/completion state
```

Historical lineage preserves that T1 decisions were made under uncertainty.

Later evidence does not rewrite what was knowable at T1.

## 60. Later evidence does not retroactively justify unsafe Retry

If an unsafe Retry occurred while the first Attempt was unknown, later evidence showing the first Attempt actually failed does not make the earlier Retry decision historically well-founded.

```text
later knowledge != retroactive recovery justification
```

Recovery-decision provenance must preserve evidence available at decision time.

## 61. Outcome Freshness matters

An Outcome may establish that an effect occurred at a time; it is not permanent proof of current external state.

```text
historical success != current state guarantee
```

Later continuation may require fresh Observation when current state is material.

## 62. Outcome remains distinct from Observation

M0.2/M0.4 remain normative.

```text
Outcome != Observation
```

One downstream event may support an Outcome and separately classified returned information, but the semantic roles remain distinct.

## 63. Outcome remains distinct from Authorization

M0.6 remains normative.

```text
Outcome != Authorization
Effect != proof of Authorization
```

Successful effect does not legitimize itself after the fact.

## 64. Outcome remains distinct from Capability Match

Historical successful execution does not prove an incompatible Capability should have been admitted or that the same capability remains compatible now.

```text
historical success != Capability Match proof
```

M0.5 remains normative.

## 65. Successful Outcome is not arbitrary factual truth

A successful operation can coexist with incorrect/uncertain Claims elsewhere in a WorkerResult/provider response.

```text
successful Outcome != every associated Claim true
```

M0.2 evidence semantics remain in force.

## 66. Conflicting Outcome sources have no implicit precedence

Executor status, remote receipt, Worker report, local Observation, and other sources may disagree.

IRR/Host MUST preserve material provenance/Conflict rather than silently assuming:

```text
newest wins
Executor wins
Worker wins
remote service wins
majority wins
```

An explicit bounded evidence/precedence rule is required when disagreement changes material recovery behavior.

## 67. Recovery Policy is not Governance policy

A future Retry/fallback algorithm may determine what recovery action is semantically admissible to propose.

Governance decides permission.

```text
Recovery Policy != Governance policy
Retry policy != Authorization
```

Exact policy interfaces are deferred.

## 68. Recovery Policy cannot create capabilities

```text
Recovery Policy != capability factory
```

M0.5 remains normative.

## 69. Recovery Policy cannot erase uncertainty

A preference such as `retry_on_timeout=true` cannot convert an effectful ambiguous Attempt into known failure.

```text
Retry preference != Outcome evidence
```

Policy acts only within evidence/contracts actually available.

## 70. Bounded automatic Retry may exist later

M0.9 does not ban all automatic Retry.

A future system may automatically Retry when an explicit admitted contract establishes that replay cannot create a material duplicated/forbidden effect and all required capability, authority, binding, and revalidation conditions remain satisfied.

Some pure computations or server-enforced deduplicated operations may support such behavior.

```text
automatic retry requires explicit safe-replay basis
```

Exact Retry count, backoff, jitter, scheduler, and timeout policy are deferred.

## 71. Retry budgets are runtime policy

M0.9 does not define:

```text
max_attempts
backoff schedule
retry delay
jitter
timeout constants
circuit-breaker thresholds
```

M0.9 freezes semantic safety/lineage, not numeric policy.

## 72. Infinite Retry is forbidden

No recovery policy may smuggle an unbounded Retry loop into an ordinary WorkStep or DelegatedWork boundary.

```text
retry-until-success != bounded recovery
```

Any future automatic Retry mechanism must be explicitly bounded.

## 73. Retry cost is material

Repeated Attempts may create additional cost, quota use, rate-limit consumption, compute use, or external commitment.

If Retry materially widens cost/commitment beyond admitted semantics, it cannot remain hidden recovery behavior.

```text
retry cost widening -> explicit Continuation/review as applicable
```

## 74. Retry disclosure is material

A repeated remote Attempt may disclose the same data again or use a different provider.

```text
retry != disclosure exemption
```

M0.5/M0.6 remain applicable.

## 75. Retry target remains bounded

Recovery MUST NOT choose another recipient/resource merely because the original target failed or is unavailable.

```text
retry target change != same Retry by default
```

Material target change returns to IRR Continuation.

## 76. Worker fallback remains explicit

If Worker A is unavailable/fails, Worker B is not automatically equivalent.

M0.8 remains normative:

```text
Worker substitution != semantic equivalence by default
Worker fallback != scope/disclosure expansion authority
```

M0.9 adds that fallback lineage preserves the earlier Worker Outcomes/effects.

## 77. Executor/provider fallback remains explicit

Switching Executor/provider may change disclosure, account boundary, cost, effects, provenance, or authority requirements.

```text
Executor fallback != semantic equivalence by default
provider fallback != authority inheritance
```

M0.5/M0.6 remain normative.

## 78. Material unknown Outcome may block parent completion

If unresolved unknown effect is material to the parent intent or makes further work unsafe/duplicative, parent completion MUST NOT be asserted for convenience.

```text
material unknown outcome != parent completion proof
```

The parent may remain unresolved/blocked pending evidence or later explicit policy/decision.

## 79. Unknown branch does not erase known progress

An unknown subordinate effect does not imply every other branch/result is invalid.

IRR may preserve known successful progress while keeping the unknown branch explicit.

```text
one unknown outcome != erase known progress
```

## 80. Failure may coexist with useful result material

A failed Worker subtask/capability Attempt may still return useful attributable data or artifacts.

Those materials remain available under their provenance, uncertainty, partial-completion, and effect history.

```text
failed Attempt != returned data nonexistent
```

## 81. Outcome refinement preserves history

For example:

```text
Attempt 1: unknown_outcome at T1
new receipt at T2
Attempt 1: effect confirmed at T2
```

The record preserves both later confirmation and the earlier uncertainty relevant to decisions made at T1.

Exact event-sourcing/persistence is deferred.

## 82. Reference scenario — Telegram acknowledgement loss

Intent:

```text
"Send report R to recipient A in Telegram."
```

Executor transmits a request. Connection drops before material acknowledgement.

Correct semantics:

```text
Attempt 1
known: transmission began
unknown: whether recipient-visible send occurred
Outcome/effect certainty: unknown_outcome
```

Incorrect:

```text
no ACK -> failed -> automatically send Attempt 2
```

Retry requires explicit safe basis, such as downstream duplicate suppression or attributable status evidence, plus applicable Authorization for the new Attempt where required.

## 83. Reference scenario — pre-attempt missing capability

Work requires `telegram.send_file`, but the exact applicable Catalog contains no compatible Capability.

Correct semantics:

```text
missing_capability
work path: blocked
execution Attempt: none
Outcome: none for the unattempted send
```

Incorrect:

```text
Attempt 1 = failed
```

or shell/browser fallback invented by recovery.

## 84. Reference scenario — local CAS failure

A bounded local mutation uses exact compare-and-swap and the admitted contract proves CAS failed before mutation.

Possible semantics:

```text
Attempt 1: failed
known effect: target mutation did not occur under the CAS contract
```

A later Retry may become eligible after revalidation, but `failed != automatic retry` because resource/current state/Authorization can change.

## 85. Reference scenario — process launch response lost

Executor requests process launch and loses the response after launch may have succeeded.

Correct semantics may be:

```text
Attempt 1: unknown_outcome
```

not:

```text
failed -> launch again
```

Recovery may require a separately admitted process-status Observation/query if a compatible capability exists and authority permits it where required.

## 86. Reference scenario — Worker partial patch then failure

Delegated coding Worker creates a patch artifact but cannot satisfy the full delegated completion contract.

Correct semantics:

```text
WorkerResult:
  patch artifact: attributable
  delegated completion: not satisfied
  subordinate Outcome(s): preserved according to evidence
```

The patch does not disappear because the Worker failed, and it does not become applied mutation automatically.

## 87. Reference scenario — fallback Worker after unknown external effect

Worker A may have published an artifact externally but loses confirmation.

IRR MUST NOT silently delegate the same publication to Worker B.

```text
Worker B available != Worker A effect absent
```

If Worker B is eventually used under a safe explicit recovery basis, its invocation is a new Attempt with separate lineage.

## 88. Relationship to M0.2 Trust/Context

M0.2 owns Claims, Evidence, provenance, Conflict, Completeness, Freshness, and Material Ambiguity.

M0.9 uses these semantics to determine what Outcome/recovery claims evidence supports.

```text
recovery preference != evidence
```

## 89. Relationship to M0.3 Work Boundary

M0.3 forbids hidden retries/unbounded plan control flow.

M0.9 defines semantic principles under which later bounded Retry may create new Attempts.

```text
retry != hidden WorkPlan loop
```

## 90. Relationship to M0.4 Binding/Observation

M0.4 owns returned-data classification, Observation, Binding Input, Bound Value, and Continuation.

M0.9 may require fresh evidence/status Observation to resolve uncertainty, but recovery gains no ambient observation authority.

## 91. Relationship to M0.5 Capability Boundary

M0.5 owns Capability Match, Catalog Membership, Availability, invocation readiness, effect/scope metadata, and drift.

M0.9 cannot create capabilities and must revalidate material capability/resource conditions before a new Attempt when necessary.

## 92. Relationship to M0.6 Governance

M0.6 owns Authorization, Denial, Governance Constraint, and `require_review`.

M0.9 owns recovery semantics, not permission.

```text
retry eligibility != Authorization
Denial != Outcome
```

## 93. Relationship to M0.7 Cognitive Provider

M0.7 owns CandidateResolution/Candidate Admission.

Provider recommendations about failure/Retry are candidate material, not Outcome evidence or Governance authority by themselves.

```text
provider recommends retry != retry authority
provider says failed != failed Outcome by default
```

Candidate Admission must apply all later applicable frozen constraints when candidate material proposes Worker or recovery semantics; provider admission never bypasses M0.8/M0.9.

## 94. Relationship to M0.8 Worker Delegation

M0.8 owns DelegatedWork/WorkerResult/Worker subordinate lifecycle boundaries.

M0.9 owns general failure/Retry/unknown-outcome principles applicable to material Worker Attempts and subordinate Outcomes.

Worker internal pure iteration may remain implementation detail; material external Attempts/effects preserve M0.9 lineage/safety semantics.

## 95. Acceptance criteria

M0.9 is complete when the repository states unambiguously that:

1. Outcome/recovery classification is scoped to bounded downstream work/lifecycle semantics.
2. `blocked` may exist before any effect Attempt and does not prove an Attempt started.
3. Retry is a new attributable Attempt over unchanged admitted material semantics.
4. Executed fallback is a new attributable Attempt.
5. Transport success does not automatically satisfy Completion Semantics.
6. `succeeded` is scoped completion evidence, not parent intent satisfaction by default.
7. `failed` means scoped Completion Semantics were not satisfied and does not imply no effect.
8. `blocked` is distinct from Denial, `missing_capability`, failure, and Attempt existence.
9. `interrupted` is distinct from no-effect, failure, and `unknown_outcome` by definition.
10. Lifecycle interruption and effect certainty may be represented separately later.
11. `unknown_outcome` is distinct from failure.
12. Timeout is not failure or no-effect proof by itself.
13. Lost acknowledgement is not proof that an external effect did not occur.
14. Outcome evidence remains attributable.
15. WorkerResult remains broader than Outcome.
16. Child failure does not automatically imply parent intent failure.
17. Child success does not automatically imply parent intent completion.
18. Retry never occurs merely because success was not confirmed.
19. Effectful unknown outcome never implies automatic Retry.
20. Confirmed failure does not automatically imply Retry safety.
21. Retry Eligibility is distinct from Authorization.
22. Authorization is distinct from Retry safety/effect-state knowledge.
23. Capability Availability is distinct from Retry safety.
24. Idempotency comes from explicit admitted contract at material effect scope.
25. Same request bytes/name do not prove Idempotency.
26. Idempotency scope cannot ignore repeated material side effects.
27. `idempotent=true` metadata alone does not establish guarantee.
28. Duplicate-suppression mechanism must cover protected material effect.
29. Read-only Retry is not universally harmless.
30. Retry preserves prior Attempt history.
31. Material binding/capability/authority conditions are revalidated when required.
32. Retry cannot silently mutate semantics.
33. Fallback is distinct from capability synthesis and semantic-substitution authority.
34. Fallback equivalence requires explicit semantic basis.
35. Executed fallback creates separate Attempt lineage.
36. Fallback does not inherit Authorization by default.
37. Fallback after unknown Outcome does not erase possible earlier effect.
38. Recovery cannot improvise a new goal.
39. Recovery cannot bypass ambiguity, Capability Match, Governance, or Worker boundaries.
40. Cancellation does not prove in-flight effect prevention.
41. Revocation and Cancellation remain distinct.
42. Unknown authority state is distinct from unknown effect Outcome.
43. Capability unavailability before Attempt is not failed execution by default.
44. `missing_capability`, Denial, `require_review`, clarification, and candidate rejection are not fake execution Outcomes.
45. Worker escalation is not Worker failure by definition.
46. Partial effects remain explicit under failure.
47. Compensation is a new semantic operation, not Retry.
48. Rollback does not erase historical effects.
49. Resolving unknown Outcome may require separately admitted/authorized evidence acquisition.
50. Recovery status queries are separate semantic operations.
51. New evidence may refine earlier unknown Outcome without rewriting earlier knowledge state.
52. Later evidence does not retroactively justify unsafe Retry.
53. Outcome Freshness is bounded; historical success is not permanent current-state proof.
54. Outcome remains distinct from Observation, Authorization, Capability Match, and arbitrary factual truth.
55. Conflicting Outcome sources preserve provenance and require explicit resolution basis.
56. Recovery Policy is distinct from Governance policy.
57. Recovery Policy cannot create capabilities or erase uncertainty.
58. Bounded automatic Retry may exist only under explicit safe-replay basis.
59. Retry budgets/backoff/timeouts remain deferred runtime policy.
60. Infinite Retry is forbidden.
61. Retry cost/disclosure/target changes remain material semantic dimensions.
62. Worker/Executor/provider fallback remains explicit and attributable.
63. Material unknown Outcome may block parent completion.
64. One unknown branch does not erase known successful progress.
65. Failed Attempts may still return useful attributable data/artifacts.
66. Later Outcome refinement preserves Attempt/evidence lineage.
67. Candidate Admission remains subject to applicable M0.8/M0.9 boundaries.
68. M0.1–M0.8 ownership remains preserved.
69. Exact runtime state machines/schemas remain deferred to M1/later milestones.
70. No runtime code or `src/` tree is introduced.

## 96. M0.9 exclusions

M0.9 intentionally does NOT freeze:

- Python `Outcome` / `Attempt` classes or enums;
- exact `succeeded` / `failed` / `blocked` / `interrupted` / `unknown_outcome` wire values;
- whether lifecycle interruption/effect certainty are separate fields or another future representation;
- terminal/non-terminal runtime state-machine layout;
- exact Attempt IDs, digests, or lineage serialization;
- persistence/event-sourcing schemas;
- timeout values;
- Retry counts;
- exponential-backoff algorithms;
- jitter;
- circuit breakers;
- Retry queues/schedulers;
- executor transport adapters;
- Worker orchestration/recovery implementation;
- exact idempotency-key format;
- exact duplicate-suppression protocol;
- exact status-query capabilities;
- automatic compensation algorithms;
- rollback implementation;
- concrete Governance Retry policy;
- concrete CapabilityHandoff/DelegatedWorkHandoff runtime protocol;
- M1 immutable Python schemas;
- M5 concrete governed handoff/recovery implementation;
- M7 concrete Worker recovery integration.

M0.9 freezes the failure/recovery semantic boundary, not a recovery orchestration engine.
