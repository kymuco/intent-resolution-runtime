# M0.9 — Failure, Retry & Unknown Outcome Boundary

Status: **normative for M0.9**.

This document freezes how Intent Resolution Runtime (IRR) and its downstream boundaries must reason about success, failure, blocking, interruption, uncertain effects, retry, and fallback without turning transport ambiguity into duplicated external effects or allowing recovery logic to widen semantics, capabilities, disclosure, or authority.

It extends M0.1 Product Charter & Vocabulary, M0.2 Trust/Context/Resolution Semantics, M0.3 Intent → Work Boundary, M0.4 Late Binding & Observation Boundary, M0.5 Capability Boundary, M0.6 Governance & Authority Boundary, M0.7 Cognitive Provider Boundary, and M0.8 Worker Delegation Boundary without introducing runtime code, exact Python enums, persistence schemas, retry schedulers, timeout values, executor adapters, Worker orchestration, or M1 data models.

M0.9 answers one question:

> How may IRR continue after downstream work does not produce a clean confirmed success without confusing failure with uncertainty or repeating an effect whose first attempt may already have happened?

The answer is:

> **Every material downstream attempt and result remains attributable. Success, failure, blocking, interruption, and unknown outcome are distinct semantic conditions. A retry is a new attempt, not a harmless continuation. Unknown effectful outcome never implies automatic retry, and fallback never grants semantic, capability, disclosure, or authority expansion.**

```text
admitted work
    |
    v
 Attempt
    |
    +----------------+----------------+----------------+----------------+
    |                |                |                |                |
    v                v                v                v                v
succeeded         failed           blocked        interrupted    unknown_outcome
    |                |                |                |                |
    +----------------+----------------+----------------+----------------+
                                 |
                                 v
                        explicit continuation /
                         recovery assessment
                                 |
                   +-------------+-------------+
                   |                           |
                   v                           v
             no new attempt              Retry / fallback
                                              |
                                              v
                                      NEW attributable attempt
```

Central invariants:

```text
unknown_outcome != failed
failed != no effect
blocked != Denial
interrupted != no effect
transport timeout != proof of failure
lost acknowledgement != proof of no effect
retry != continuation of the same attempt
retry != harmless repetition
retry eligibility != Authorization
retry authorization != capability availability
retry authorization != retry safety
idempotency claim != duplicate-suppression proof by default
unknown effectful outcome != automatic retry
fallback != capability synthesis
fallback != semantic substitution authority
fallback != authority inheritance
worker failure != parent intent failure by definition
executor failure != intent invalidity
success != parent intent satisfaction by default
```

## 1. Outcome classification is scoped

An `Outcome` describes an attributable downstream operational or lifecycle result for a specific bounded semantic scope.

That scope may conceptually be:

```text
one capability attempt
one WorkStep execution attempt
one delegated subordinate operation
one Worker subordinate lifecycle result
one bounded handoff attempt
```

A result for one scope MUST NOT silently become the result for a larger parent scope.

```text
attempt success != WorkPlan success
WorkPlan success != parent intent satisfaction by default
worker subtask success != parent intent satisfaction
```

Exact Outcome identifiers, schemas, digests, and persistence are deferred to M1/later lifecycle milestones.

## 2. Attempt

An `Attempt` is one attributable effort to perform one already admitted bounded downstream operation or delegated lifecycle transition.

A retry is a **new Attempt**.

```text
retry attempt N+1 != continuation of attempt N
```

A future representation must preserve enough lineage to distinguish attempts that target the same semantic work.

Attempt identity is important because two attempts may each create external effects even when they originate from one WorkStep or one user intent.

Exact attempt IDs and sequencing are deferred.

## 3. Transport activity is not semantic completion

A downstream system may expose transport states such as:

```text
request serialized
socket opened
request sent
server accepted connection
HTTP response received
ACK received
```

Those states do not automatically equal the Completion Semantics required by the admitted work.

```text
transport success != semantic success
request accepted != requested effect completed by default
```

Capability/Worker contracts may later define stronger evidence, but transport convenience MUST NOT silently strengthen completion meaning.

## 4. `succeeded`

Conceptually, `succeeded` means there is sufficient attributable evidence that the bounded attempt satisfied the applicable Completion Semantics for its own scope.

```text
succeeded
    -> completion evidence sufficient for this outcome scope
```

This does not automatically prove:

- parent WorkPlan completion;
- parent intent satisfaction;
- factual truth of every returned Claim;
- continuing world state after the effect;
- Authorization correctness;
- future idempotency.

```text
succeeded != parent intent satisfied by default
succeeded != Authorization proof
```

## 5. `failed`

Conceptually, `failed` means there is sufficient attributable evidence that the bounded attempt did not satisfy its required Completion Semantics.

Failure MUST NOT be interpreted as proof that no external effect occurred.

An operation can fail after producing a partial or otherwise material effect.

Examples include conceptually:

```text
file write partially completed, then validation failed
remote operation created resource, then postcondition check failed
worker produced some artifacts, then could not satisfy completion contract
process launched, then readiness check failed
```

Therefore:

```text
failed != no effect
failed != safe to retry
```

Any known partial effects remain attributable historical facts and must not be erased by the failure classification.

## 6. `blocked`

Conceptually, `blocked` means a required transition cannot currently begin or continue because a known prerequisite or boundary condition is unsatisfied.

Illustrative blockers include:

- `missing_capability`;
- known Capability unavailability;
- invocation unreadiness;
- missing required Context/Observation;
- unresolved Material Ambiguity;
- insufficient Authorization;
- explicit Denial for the relevant authority context;
- Worker escalation requiring new scope/information/authority.

The cause remains separately classified.

```text
blocked != Denial
blocked != missing_capability
blocked != failure by definition
```

A blocked state at one transition does not prove that no prior effects occurred elsewhere in the parent lifecycle.

## 7. `interrupted`

Conceptually, `interrupted` means an in-progress attempt or lifecycle stopped before its normal completion protocol finished.

Interruption may be caused by conceptually:

```text
process termination
worker cancellation
host shutdown
network disconnection
session loss
operator stop
runtime crash
```

Interruption describes the lifecycle discontinuity; it does not by itself determine whether the intended external effect occurred.

```text
interrupted != no effect
interrupted != unknown_outcome by definition
```

For example, a local read computation may be interrupted before any effect and have a known incomplete result, while a remote send may be interrupted after the external service accepted the request and therefore have uncertain effect status.

## 8. `unknown_outcome`

Conceptually, `unknown_outcome` means material evidence is insufficient to establish whether the bounded effect/completion semantics occurred.

This is not failure.

```text
unknown_outcome != failed
```

Typical causes include:

```text
request may have reached remote service but acknowledgement was lost
process may have committed mutation before crash
worker may have produced an external side effect before transport failure
status source is unavailable and no independent evidence exists
```

Unknown outcome MUST preserve what is known and what is unknown rather than collapsing uncertainty into a convenient terminal label.

## 9. Unknown outcome is scoped to material uncertainty

Not every missing detail requires the whole operation to be classified `unknown_outcome`.

The uncertainty must be material to the represented Completion Semantics or effect history.

For example, if a capability independently proves that a file was atomically published at digest D but a non-material telemetry acknowledgement was lost, the operation need not become unknown merely because one auxiliary response disappeared.

Conversely, if the missing acknowledgement is the only evidence that an external message was accepted, effect status may remain unknown.

```text
missing telemetry != unknown semantic outcome by default
missing material effect evidence -> may require unknown_outcome
```

## 10. Timeout is not an Outcome by itself

A timeout is a temporal/transport observation about not receiving an expected signal within a bounded period.

```text
timeout != failed
timeout != unknown_outcome by definition
timeout != no effect
```

The correct outcome classification depends on what effect/completion evidence remains available.

A timeout before any effect attempt may support a known blocked/failed classification under a specific contract. A timeout after an external request may instead leave the effect unknown.

Exact timeout values and mechanisms are deferred.

## 11. Lost acknowledgement is not proof of no effect

If an executor sends an effectful request and loses the acknowledgement, IRR MUST NOT infer:

```text
no ACK -> operation failed -> send again
```

unless an explicit downstream contract supplies sufficient stronger evidence.

```text
lost acknowledgement != proof of no effect
```

This is the canonical M0.9 duplicate-effect hazard.

## 12. Outcome evidence is attributable

Every material Outcome classification must be supported by attributable result/effect evidence appropriate to the claimed semantics.

A future record may conceptually preserve:

```text
attempt lineage
reported status
completion evidence
effect evidence
known partial effects
uncertainty
source/provider/executor/Worker provenance
temporal basis when material
```

Exact fields are deferred.

A fluent Worker or Executor assertion alone does not strengthen the evidence beyond its contract and provenance.

## 13. Executor assertion is not necessarily independent effect evidence

An Executor may report `success` or `failure`.

IRR/Host may rely on that report according to the admitted downstream contract, but the semantic meaning must remain explicit.

```text
executor says success != stronger completion than executor contract supports
executor says failure != proof of no effect
```

Where an operation requires stronger confirmation, a weaker executor result cannot silently satisfy it.

## 14. WorkerResult and Outcome remain distinct

M0.8 remains normative.

A `WorkerResult` is a broad delegated-result envelope. It may contain or reference zero, one, or many subordinate Outcome records.

```text
WorkerResult != Outcome by default
```

A Worker may complete its analysis deliverable while one subordinate external operation remains unknown, or may fail its completion contract despite several successful subordinate operations.

Those semantics MUST NOT be collapsed.

## 15. Parent failure is not implied by child failure

Failure of one attempt, WorkStep, Executor, Capability instance, or Worker does not automatically prove that the parent intent is invalid or impossible.

```text
executor failure != intent invalidity
worker failure != parent intent failure by definition
attempt failure != global impossibility
```

IRR Continuation may later determine whether another admitted path exists, clarification is needed, the parent is blocked, or the parent should terminate under a future lifecycle policy.

## 16. Parent success is not implied by child success

Likewise:

```text
attempt success != parent completion
worker subtask success != parent completion
```

IRR retains parent Completion Semantics and must evaluate them explicitly.

## 17. Retry

A `Retry` is a new attributable Attempt to perform semantic work that substantially corresponds to an earlier Attempt.

```text
retry != hidden loop
retry != same attempt resuming
```

M0.3's no-hidden-retry rule remains normative.

A retry may create additional external effects even when it uses the same inputs and capability.

## 18. Retry requires an explicit basis

IRR/downstream lifecycle logic MUST NOT retry merely because the prior attempt did not report success.

A retry requires an explicit admitted basis appropriate to the effect surface.

Conceptually, the recovery boundary must determine at least:

```text
what is known about prior effect/completion
whether a new attempt is semantically still desired
whether duplicate or repeated effects are acceptable/prevented
whether capability semantics remain valid
whether bound inputs/resources remain valid
whether applicable Authorization covers the new attempt/effect
whether retry changes provider/service/scope/cost/disclosure
```

Exact algorithms are deferred.

## 19. Unknown effectful outcome never implies automatic retry

This rule is absolute at the M0.9 semantic boundary:

> **An effectful `unknown_outcome` MUST NOT be converted into an automatic retry merely because success was not confirmed.**

```text
unknown effectful outcome != automatic retry
```

A new attempt may duplicate the original effect.

Examples include:

- duplicate Telegram messages;
- duplicate purchases;
- duplicate issue/comment creation;
- repeated external disclosure;
- duplicate process/job launch;
- repeated mutation;
- duplicate commit/push-like effects.

Recovery must first establish a safe explicit basis or remain unresolved/blocked.

## 20. `failed` also does not automatically imply retry

Even a confirmed `failed` classification does not by itself establish retry safety.

A failed attempt may have produced partial effects or changed preconditions.

```text
failed != automatic retry
```

Retry assessment must use effect history and current semantics, not the label alone.

## 21. Retry eligibility is not Authorization

A recovery system may determine that another attempt is semantically safe or appropriate.

That does not create permission.

```text
retry eligibility != Authorization
```

If the new attempt performs authority-requiring work, applicable external Authorization coverage must exist under M0.6.

Prior Authorization does not automatically cover every retry unless its externally defined scope explicitly does so.

```text
Authorization for attempt N != Authorization for attempt N+1 by default
```

## 22. Authorization is not retry safety

Conversely, Governance may authorize another attempt, but that does not prove the attempt is safe from duplicate effects or semantically valid.

```text
retry authorization != retry safety
Authorization != effect-state knowledge
```

Authority and recovery correctness remain separate.

## 23. Capability availability is not retry safety

A capability being online and callable does not prove retry safety.

```text
available capability != safe retry
```

Capability existence, Match, Availability, invocation readiness, retry semantics, and Authorization remain distinct.

## 24. Idempotency

`Idempotency` is the semantic property that repeating an operation under a defined contract does not create an additional material effect beyond the intended stable result.

M0.9 does not assume idempotency merely because an API uses PUT, UPSERT, a deterministic function name, or a stable input.

```text
same request bytes != idempotent effect
same operation name != idempotent effect
```

Idempotency must be explicitly supported by the applicable capability/execution contract at the relevant effect scope.

Exact representation is deferred.

## 25. Idempotency scope matters

An operation can be idempotent for one effect but not another.

For example, setting a file's exact contents may be idempotent with respect to final file bytes while still creating repeated audit events, billing, notifications, timestamps, or remote requests.

Therefore:

```text
idempotent final state != no repeated side effects by default
```

A retry policy must reason about the material effect semantics actually relevant to the intent/Governance boundary.

## 26. Idempotency claim is not proof by itself

A provider, Worker, Executor, or arbitrary metadata field saying `idempotent=true` does not automatically establish the property.

```text
idempotency claim != idempotency guarantee by default
```

The property must come from an admitted attributable contract or stronger evidence appropriate to the downstream boundary.

## 27. Duplicate suppression / idempotency key

A downstream capability may later support a bounded duplicate-suppression mechanism such as an idempotency key, request identity, CAS precondition, transaction identity, or other deduplication contract.

M0.9 freezes only the semantic requirement:

```text
dedup mechanism must cover the material effect being protected
```

A client-generated key that the downstream service does not enforce is not duplicate-effect protection.

```text
idempotency key present != duplicate suppression guaranteed
```

Exact tokens/protocols are deferred.

## 28. Safe replay evidence must be explicit

If a downstream system can prove that reissuing an attempt cannot duplicate the material effect, that proof may support retry eligibility.

Examples conceptually include:

```text
server-enforced request identity
CAS with exact expected-old value
transaction already committed with known durable identity
read-only pure operation under stable bounded semantics
```

M0.9 does not declare these universally safe; the concrete contract must support the claim.

## 29. Pure computation is different from effectful retry

Repeating a deterministic, side-effect-free computation over already admitted immutable inputs may have different recovery semantics from repeating an external mutation.

But IRR MUST NOT assume purity from a name or implementation convention.

```text
analysis-like label != proof of purity
```

Purity/effect-free behavior must follow from the applicable semantic contract.

## 30. Read/observation retry can still be semantically material

A read-only operation may avoid mutation but can still:

- disclose data to a remote provider;
- incur cost;
- observe a changed world state;
- reveal new information that changes semantic decisions;
- trigger rate limits or audit effects.

Therefore:

```text
read-only != universally harmless retry
```

M0.2/M0.4/M0.6 boundaries remain applicable.

## 31. Retry preserves attempt history

A successful later retry MUST NOT rewrite the earlier attempt as if it had succeeded.

```text
attempt N failed/unknown
attempt N+1 succeeded
    !=
attempt N succeeded historically
```

Historical Outcome/effect evidence remains attributable.

## 32. Retry input must be revalidated when material

A retry cannot blindly reuse stale Binding or capability assumptions.

Before a new attempt, material conditions may require revalidation of:

```text
Bound Value freshness
resource existence
Capability Match
Capability Availability
invocation readiness
provider/Worker identity
scope/disclosure semantics
Authorization applicability
```

Exact revalidation algorithms are deferred.

## 33. Retry must not silently change semantics

If retry requires a materially different:

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

then it is not merely the same attempt repeated under unchanged semantics.

It must return through the applicable IRR Continuation/successor/review boundaries.

```text
retry != permission for semantic mutation
```

## 34. Fallback

A `Fallback` is a proposed alternate downstream path after an earlier path is unavailable, blocked, failed, interrupted, or otherwise unsuitable.

Fallback is not capability synthesis and not semantic substitution authority.

```text
fallback != capability synthesis
fallback != semantic substitution authority
```

M0.5/M0.8 remain normative.

## 35. Fallback may be semantically equivalent only under explicit basis

A fallback capability/provider/Worker may be used without new parent semantics only when all material admitted dimensions remain equivalent or are already covered by an explicit admitted selection/fallback rule.

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

Otherwise fallback requires IRR Continuation or successor semantics.

## 36. Fallback does not inherit authority

```text
Authorization for provider A != provider B by default
Authorization for Worker A != Worker B by default
```

A fallback path must independently remain inside applicable Authorization coverage.

```text
fallback != authority inheritance
```

## 37. Fallback does not erase prior unknown effects

If attempt A has an `unknown_outcome`, switching to fallback B does not make A's effect disappear.

The parent state must preserve the possibility that both A and B effects may exist if B is attempted.

```text
fallback after unknown != prior effect absent
```

This is especially important for external sends, purchases, mutations, publication, process launches, and other non-idempotent operations.

## 38. Recovery is not semantic goal improvisation

Recovery logic may not invent a smaller/different objective merely to achieve a terminal state.

```text
recovery convenience != intent reinterpretation
```

If the attainable objective changes, IRR Continuation/successor resolution must make that change explicit.

## 39. Recovery does not bypass Material Ambiguity

A failure does not authorize guessing a new resource, recipient, executable, provider, or scope.

```text
failure != permission to guess
```

M0.2 remains normative.

## 40. Recovery does not bypass capability admission

A failure does not authorize shell/browser/arbitrary-code fallback when the required capability is missing or incompatible.

```text
failure != capability fallback authority
unknown_outcome != capability widening authority
```

M0.5 remains normative.

## 41. Recovery does not bypass Governance

A retry/fallback/recovery path does not become authorized merely because it is attempting to repair a prior failure.

```text
recovery objective != authority exemption
```

M0.6 remains normative.

## 42. Recovery does not bypass Worker boundaries

A Worker cannot self-retry an authority/effect attempt beyond the DelegatedWork envelope merely because the previous attempt failed.

Worker-local retry is permitted only where the delegation, capability, effect, and later recovery contracts explicitly admit it.

```text
Worker retry != scope widening authority
```

M0.8 remains normative.

## 43. Worker internal pure retries and external attempts are distinct

A Worker may internally repeat a pure computation as an implementation detail when that repetition remains inside its bounded subordinate lifecycle and creates no new material effect.

That is distinct from reissuing an external effectful attempt.

```text
internal computation retry != external effect retry
```

M0.9 does not require every internal pure iteration to become an IRR Attempt record; it freezes that material external attempts/effects cannot be hidden as internal retry behavior.

## 44. Cancellation

Cancellation is an attributable request/transition to stop further work.

Cancellation does not erase already produced effects and does not prove that an in-flight external effect was prevented.

```text
cancel requested != effect prevented
cancel acknowledged != prior effects erased
```

A cancellation may therefore lead to a known interrupted outcome, a clean no-effect result under a stronger contract, or `unknown_outcome` depending on evidence.

Exact cancellation protocol is deferred.

## 45. Revocation and cancellation are distinct

Authorization revocation changes authority applicability.

Cancellation asks a lifecycle to stop.

```text
Authorization revoked != cancellation delivered
cancellation delivered != Authorization history erased
```

A downstream system must not infer one from the other unless an explicit external contract establishes the relationship.

## 46. Unknown authority state is not unknown outcome

M0.6 authority uncertainty and M0.9 effect uncertainty are separate semantic dimensions.

```text
unknown Authorization state != unknown_outcome
```

A system may know exactly that no effect was attempted while authority is unresolved, or may have an unknown effect outcome even though the attempt was clearly authorized.

## 47. Capability unavailability is not failure outcome by itself

A capability being unavailable before an attempt starts is normally a readiness/blocking condition, not evidence that an effectful attempt failed.

```text
Capability unavailable != failed attempt by default
```

If an attempt began and the provider became unavailable mid-flight, the applicable evidence may instead support failed, interrupted, or unknown_outcome semantics.

## 48. `missing_capability` is not an Outcome

`missing_capability` is a planning/admission condition under M0.5.

It is not a downstream execution Outcome.

```text
missing_capability != Outcome
```

It may cause the parent work path to be blocked, but the semantic roles remain distinct.

## 49. Denial is not an Outcome

A Governance Denial is an authority decision, not an execution result.

```text
Denial != Outcome
```

A denied operation may remain unattempted; no fake failed Outcome should be manufactured simply because execution cannot proceed.

## 50. `require_review` is not an Outcome

Likewise:

```text
require_review != Outcome
```

It is a Governance state/decision, not evidence about an effect attempt.

## 51. Clarification is not failure

A path requiring clarification is not a failed execution.

```text
clarification_required != failure
```

It is an unresolved semantic path under M0.2/M0.3.

## 52. Candidate rejection is not failure outcome

A rejected Cognitive Provider candidate is not a downstream execution failure.

```text
Candidate rejection != Outcome
```

M0.7 remains normative.

## 53. Worker escalation is not failure by definition

A Worker may correctly discover a need outside its delegation envelope and escalate it.

```text
Worker escalation != worker failure by definition
```

Escalation may be the correct bounded result of the delegated subtask.

## 54. Partial effect evidence remains explicit

If an attempt is known to have produced some but not all intended effects, the partial effect history must remain explicit.

A future lifecycle representation may classify the overall attempt as failed while separately preserving the known partial effects.

```text
failed completion != erased partial effects
```

Recovery must account for those effects before attempting compensating or repeated work.

## 55. Compensation is not retry

A compensating operation attempts to counteract or mitigate an earlier effect.

It is a distinct new semantic operation, not a retry of the original attempt.

```text
compensation != retry
```

Compensation requires its own Capability Match, effect representation, and applicable Authorization.

M0.9 does not freeze automatic compensation algorithms.

## 56. Rollback is not historical erasure

Even when a later operation successfully restores external state, the earlier effect and rollback remain historical facts.

```text
rollback success != original effect never happened
```

This preserves audit/provenance semantics.

## 57. Recovery can require Observation

Resolving an `unknown_outcome` may require a bounded attributable Observation, status query, receipt lookup, or other evidence-gathering operation.

The need for that evidence does not grant authority to acquire it.

```text
unknown outcome evidence need != observation authority
```

Any acquisition path remains subject to Context/Capability/Governance boundaries.

## 58. Status query is a separate operation

A recovery status check such as:

```text
query message by request identity
read transaction receipt
inspect remote resource state
check process existence
```

is a separate semantic operation with its own capability/effect/disclosure semantics.

It is not ambient introspection granted by failure.

```text
recovery status need != ambient query authority
```

## 59. New evidence may refine outcome classification

An earlier `unknown_outcome` may later become known when new attributable evidence arrives.

Conceptually:

```text
unknown_outcome
      |
new attributable evidence
      |
IRR / lifecycle continuation
      |
refined known outcome
```

The historical fact that the outcome was previously unknown remains part of lineage; later evidence does not rewrite what was knowable at the earlier time.

## 60. Later evidence does not retroactively justify unsafe retry

If an unsafe retry occurred while the first attempt was unknown, later evidence showing that the first attempt actually failed does not make the earlier retry decision historically well-founded.

```text
later knowledge != retroactive recovery justification
```

Decision provenance must preserve the evidence available at decision time.

## 61. Outcome freshness matters

An Outcome may establish that an effect occurred at a particular time, but it is not necessarily proof of current world state forever.

```text
historical success != current state guarantee
```

A later continuation may require fresh Observation when current state is material.

## 62. Outcome is not Observation

M0.2/M0.4 remain normative.

```text
Outcome != Observation
```

One downstream event may support both an Outcome record and separately classified returned information, but their semantic roles remain distinct.

## 63. Outcome is not Authorization

M0.6 remains normative.

```text
Outcome != Authorization
Effect != proof of Authorization
```

A successful effect does not legitimize itself after the fact.

## 64. Outcome is not Capability Match

A successful historical execution does not prove that an incompatible capability should have been admitted or that the same capability remains semantically compatible now.

```text
historical success != Capability Match proof
```

M0.5 remains normative.

## 65. Outcome is not factual truth for arbitrary Claims

A successful operation can coexist with incorrect or uncertain Claims elsewhere in a WorkerResult or provider response.

```text
successful Outcome != every associated Claim true
```

M0.2 evidence semantics remain in force.

## 66. Multiple outcome sources have no implicit precedence

Executor status, remote service receipt, Worker report, local observation, and other sources may disagree.

IRR/Host MUST preserve material provenance and Conflict rather than silently choosing:

```text
newest wins
executor wins
worker wins
remote service wins
majority wins
```

An explicit bounded precedence/evidence rule is required when the disagreement changes material recovery behavior.

## 67. Recovery policy is not Governance policy

A retry/fallback algorithm may decide what recovery action is semantically admissible to propose.

Governance decides permission.

```text
Recovery Policy != Governance policy
retry policy != Authorization
```

Exact policy interfaces are deferred.

## 68. Recovery policy cannot create capabilities

A recovery policy cannot manufacture an operation absent from the exact applicable Catalog.

```text
recovery policy != capability factory
```

M0.5 remains normative.

## 69. Recovery policy cannot erase uncertainty

A policy preference such as `retry_on_timeout=true` cannot convert an effectful ambiguous attempt into known failure.

```text
retry preference != outcome evidence
```

The policy may only act within the evidence and contracts actually available.

## 70. Bounded automatic retry may exist later

M0.9 does not ban all automatic retry.

A future system may automatically retry when an explicit admitted contract establishes that doing so cannot create a material duplicated/forbidden effect and all required capability/authority/revalidation conditions remain satisfied.

For example, some pure computations or server-enforced idempotent operations may support bounded automatic retry.

The semantic requirement is:

```text
automatic retry requires explicit safe-replay basis
```

Exact retry count, backoff, jitter, scheduler, and timeout policy are deferred.

## 71. Retry budgets are not frozen

M0.9 does not define:

```text
max_attempts
backoff schedule
retry delay
jitter
timeout constants
circuit-breaker thresholds
```

Those are runtime/policy decisions for later milestones.

M0.9 freezes only semantic safety and lineage requirements.

## 72. Infinite retry is forbidden

No recovery policy may smuggle an unbounded retry loop into an ordinary WorkStep or DelegatedWork boundary.

```text
retry-until-success != bounded recovery
```

Any future automatic retry mechanism must be bounded by an explicit contract.

## 73. Retry cost is a material semantic dimension

Repeated attempts may create additional cost, quota use, rate-limit consumption, compute use, or external commitment.

If retry materially changes cost/commitment beyond already admitted semantics, it cannot remain hidden recovery behavior.

```text
retry cost widening -> explicit continuation/review as applicable
```

## 74. Retry disclosure is a material semantic dimension

A repeated remote attempt may disclose the same data again or disclose it to a different provider.

```text
retry != disclosure exemption
```

M0.6 authority and M0.5 provider/effect semantics remain applicable.

## 75. Retry recipient/resource scope remains bounded

A recovery system MUST NOT choose another recipient/resource merely because the original one failed or is unavailable.

```text
retry target change != same retry by default
```

Material target changes return to IRR Continuation.

## 76. Worker fallback is explicit

If a Worker becomes unavailable or fails, another Worker is not automatically equivalent.

M0.8 remains normative:

```text
Worker substitution != semantic equivalence by default
Worker fallback != scope/disclosure expansion authority
```

M0.9 adds only that fallback lineage must preserve the earlier Worker outcome/effects and cannot hide them.

## 77. Executor/provider fallback is explicit

Likewise, switching executor/provider may change disclosure, account boundary, cost, effects, provenance, or authority requirements.

```text
executor fallback != semantic equivalence by default
provider fallback != authority inheritance
```

M0.5/M0.6 remain normative.

## 78. Unknown outcome may block parent completion

If an unresolved unknown effect is material to the parent intent or could make further work unsafe/duplicative, parent completion MUST NOT be asserted merely for convenience.

```text
material unknown outcome != parent completion proof
```

The parent may remain unresolved/blocked pending evidence or explicit policy/decision under later lifecycle contracts.

## 79. Unknown outcome may coexist with successful parent progress

An unknown subordinate effect does not imply that every other branch or result is invalid.

IRR may preserve known successful progress while keeping the unknown branch explicit.

```text
one unknown outcome != erase known progress
```

## 80. Failure may coexist with useful result material

A failed Worker subtask or capability attempt may still return useful attributable data/artifacts.

Those materials do not disappear, but their use must preserve provenance, uncertainty, partial-completion semantics, and authority/effect history.

```text
failed attempt != returned data nonexistent
```

## 81. Outcome classification does not rewrite history

A later refined classification MUST preserve attempt lineage and prior effect evidence.

For example:

```text
attempt 1: unknown_outcome at T1
new receipt at T2
attempt 1: effect confirmed at T2
```

The record should preserve both the effect occurrence evidence and the fact that T1 recovery decisions were made under uncertainty.

Exact event sourcing/persistence is deferred.

## 82. Reference scenario — Telegram acknowledgement loss

Intent:

```text
"Send report R to recipient A in Telegram."
```

Executor sends a request. Connection drops before material acknowledgement.

Correct semantics:

```text
attempt 1
  effect/completion: unknown_outcome
  known: request transmission began
  unknown: whether recipient-visible send occurred
```

Incorrect recovery:

```text
no ACK -> failed -> automatically send attempt 2
```

A retry requires an explicit safe basis, such as a downstream duplicate-suppression contract or attributable status evidence, plus applicable Authorization for the new attempt if required.

## 83. Reference scenario — local atomic write with confirmed CAS failure

A bounded local mutation uses an exact compare-and-swap precondition and the downstream contract proves the CAS failed before mutation.

Possible semantics:

```text
attempt 1: failed
known effect: target mutation did not occur under the CAS contract
```

A later retry may be semantically possible after revalidation, but:

```text
failed != automatic retry
```

because the bound resource/current state and Authorization may need to be reconsidered.

## 84. Reference scenario — process launch response lost

Executor requests a process launch and loses the response after the launch call may have succeeded.

Correct semantics may be:

```text
unknown_outcome
```

not:

```text
failed -> launch again
```

Recovery may require a separately admitted process-status Observation/query if such a capability exists and is authorized where required.

## 85. Reference scenario — Worker returns partial patch then fails

Delegated coding Worker creates a patch artifact but cannot satisfy the full delegated completion contract.

Correct semantics:

```text
WorkerResult:
  patch artifact: attributable
  completion claim: not satisfied
  subordinate Outcome: failed / blocked as supported by evidence
```

The patch does not disappear merely because the Worker subtask failed, and it does not become applied mutation automatically.

## 86. Reference scenario — fallback Worker after unknown external effect

Worker A may have published an external artifact but loses confirmation and returns an unknown outcome.

IRR MUST NOT silently delegate the same publication to Worker B as fallback.

```text
Worker B available != Worker A effect absent
```

The prior uncertainty remains material.

## 87. Relationship to M0.2 Trust/Context

M0.2 owns Claims, Evidence, provenance, Conflict, Completeness, Freshness, and Material Ambiguity.

M0.9 uses those semantics to decide what an Outcome classification is justified to claim.

```text
recovery preference != evidence
```

## 88. Relationship to M0.3 Work Boundary

M0.3 forbids hidden retries and unbounded plan control flow.

M0.9 defines the semantic principles under which later bounded retries may be represented as new Attempts.

```text
retry != hidden WorkPlan loop
```

## 89. Relationship to M0.4 Binding/Observation

M0.4 owns returned-data classification, Observation, Binding Input, Bound Value, and Continuation.

M0.9 may require fresh evidence or status Observations to resolve uncertain outcomes, but recovery does not gain ambient observation authority.

## 90. Relationship to M0.5 Capability Boundary

M0.5 owns Capability Match, Catalog Membership, Availability, invocation readiness, effect/scope metadata, and drift.

M0.9 cannot create capabilities and must revalidate material capability/resource conditions before a new attempt when necessary.

## 91. Relationship to M0.6 Governance

M0.6 owns Authorization, Denial, Governance Constraint, and require_review.

M0.9 owns recovery semantics, not permission.

```text
retry eligibility != Authorization
Denial != Outcome
```

## 92. Relationship to M0.7 Cognitive Provider

M0.7 owns CandidateResolution/Candidate Admission.

Provider recommendations about retry/failure are candidate material, not Outcome evidence or Governance authority by themselves.

```text
provider recommends retry != retry authority
provider says failed != failed Outcome by default
```

## 93. Relationship to M0.8 Worker Delegation

M0.8 owns DelegatedWork/WorkerResult/Worker lifecycle boundaries.

M0.9 owns the general failure/retry/unknown-outcome principles applicable to material Worker attempts and subordinate outcomes.

Worker internal pure iteration may remain implementation detail; material external attempts and effects must preserve M0.9 lineage/safety semantics.

## 94. Acceptance criteria

M0.9 is complete when the repository states unambiguously that:

1. Outcome classification is scoped to bounded downstream work/lifecycle semantics.
2. Retry is a new attributable Attempt.
3. Transport success does not automatically satisfy semantic Completion Semantics.
4. `succeeded` means sufficient evidence for the scoped completion claim, not parent intent satisfaction by default.
5. `failed` means scoped completion was not satisfied and does not imply no effect.
6. `blocked` is distinct from Denial, `missing_capability`, and failure.
7. `interrupted` is distinct from no-effect and from `unknown_outcome` by definition.
8. `unknown_outcome` is distinct from failure.
9. Timeout is not failure or no-effect proof by itself.
10. Lost acknowledgement is not proof that an external effect did not occur.
11. Outcome evidence remains attributable.
12. WorkerResult remains broader than Outcome.
13. Child failure does not automatically imply parent intent failure.
14. Child success does not automatically imply parent intent completion.
15. Retry never occurs merely because success was not confirmed.
16. Effectful unknown outcome never implies automatic retry.
17. Confirmed failure also does not automatically imply retry safety.
18. Retry eligibility is distinct from Authorization.
19. Authorization is distinct from retry safety.
20. Capability Availability is distinct from retry safety.
21. Idempotency must come from an explicit admitted contract at the material effect scope.
22. Same request bytes/name do not prove idempotency.
23. Idempotency scope cannot ignore repeated material side effects.
24. `idempotent=true` metadata alone does not establish an idempotency guarantee.
25. Duplicate-suppression mechanisms must actually cover the protected effect.
26. Read-only retry is not universally harmless.
27. Retry preserves prior attempt history.
28. Material binding/capability/authority conditions are revalidated before a new attempt when required.
29. Retry cannot silently mutate semantics.
30. Fallback is distinct from capability synthesis and semantic substitution authority.
31. Fallback equivalence requires an explicit semantic basis.
32. Fallback does not inherit Authorization by default.
33. Fallback after unknown outcome does not erase the possible earlier effect.
34. Recovery cannot improvise a new goal.
35. Recovery cannot bypass ambiguity, Capability Match, Governance, or Worker delegation boundaries.
36. Cancellation does not prove an in-flight effect was prevented.
37. Revocation and cancellation remain distinct.
38. Unknown authority state is distinct from unknown effect outcome.
39. Capability unavailability before attempt is not failed execution by default.
40. `missing_capability`, Denial, `require_review`, clarification, and candidate rejection are not Outcomes.
41. Worker escalation is not worker failure by definition.
42. Partial effects remain explicit under failure.
43. Compensation is a new semantic operation, not retry.
44. Rollback does not erase historical effects.
45. Resolving unknown outcomes may require separately admitted/authorized evidence acquisition.
46. Recovery status queries are separate semantic operations.
47. New evidence may refine an earlier unknown outcome without rewriting what was known earlier.
48. Later evidence does not retroactively justify an unsafe retry decision.
49. Outcome freshness is bounded; historical success is not permanent current-state proof.
50. Outcome remains distinct from Observation, Authorization, Capability Match, and arbitrary factual truth.
51. Conflicting outcome sources preserve provenance and require explicit resolution basis.
52. Recovery Policy is distinct from Governance policy.
53. Recovery Policy cannot create capabilities or erase uncertainty.
54. Bounded automatic retry may exist only under an explicit safe-replay basis.
55. Retry budgets/backoff/timeouts remain deferred runtime policy.
56. Infinite retry is forbidden.
57. Retry cost/disclosure/target changes remain material semantic dimensions.
58. Worker/executor/provider fallback remains explicit and attributable.
59. Material unknown outcome may block parent completion.
60. One unknown branch does not erase known successful progress.
61. Failed attempts may still return useful attributable data/artifacts.
62. Later outcome refinement preserves attempt/evidence lineage.
63. M0.1–M0.8 ownership remains preserved.
64. Exact runtime state machines/schemas remain deferred to M1/later milestones.
65. No runtime code or `src/` tree is introduced.

## 95. M0.9 exclusions

M0.9 intentionally does NOT freeze:

- Python Outcome/Attempt classes or enums;
- exact `succeeded` / `failed` / `blocked` / `interrupted` / `unknown_outcome` wire values;
- terminal/non-terminal state-machine representation;
- exact attempt IDs, digests, or lineage serialization;
- persistence/event-sourcing schemas;
- timeout values;
- retry counts;
- exponential-backoff algorithms;
- jitter;
- circuit breakers;
- retry queues/schedulers;
- executor transport adapters;
- Worker orchestration/recovery implementation;
- exact idempotency-key format;
- exact duplicate-suppression protocol;
- exact status-query capabilities;
- automatic compensation algorithms;
- rollback implementation;
- concrete Governance retry policy;
- concrete CapabilityHandoff/DelegatedWorkHandoff runtime protocol;
- M1 immutable Python schemas;
- M5 concrete governed handoff/recovery implementation;
- M7 concrete Worker recovery integration.

M0.9 freezes the failure/recovery semantic boundary, not a recovery orchestration engine.
