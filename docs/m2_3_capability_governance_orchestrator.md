# M2.3 — Capability / Governance Orchestrator

Status: **implementation slice**.

M2.3 extends the M2 runtime over the frozen M1.6 Capability / Governance / Authorization IR. Its purpose is to derive a complete capability-and-authority transition surface from exact active M1.6 records without collapsing semantic capability compatibility, Governance, Authorization, availability, readiness, or execution into one approval state.

The implemented boundary is:

```text
exact WorkPlan
+ explicit active CapabilityRequirement[]
+ explicit active CapabilityMatchEvaluation[]
+ explicit active WorkProposal[]
+ explicit active GovernanceDecision[]
+ explicit admitted Authorization[]
        |
        v
orchestrate_capability_governance(...)
        |
        v
CapabilityGovernanceFrontier
```

The frontier is derived runtime state, not canonical history.

## 1. Source of truth

`CapabilityGovernanceFrontier` stores only the exact active M1.6 records supplied to it:

```text
WorkPlan
CapabilityRequirement[]
CapabilityMatchEvaluation[]
WorkProposal[]
GovernanceDecision[]
Authorization[]
```

All secondary surfaces are derived from those records.

Callers cannot construct the frontier by separately supplying claims such as:

```text
matched_steps
approved_steps
denied_steps
```

that disagree with the canonical records.

The frontier constructor normalizes and revalidates the full active graph slice.

```text
frontier != canonical record
frontier != mutable authority state
secondary projection != source of truth
```

The frontier intentionally has no wire schema, `identity`, or `canonical_bytes()`.

## 2. No linear approval pipeline

The conceptual M1.6 chain is useful:

```text
WorkStep
→ CapabilityRequirement
→ CapabilityMatchEvaluation
→ WorkProposal
→ GovernanceDecision
→ Authorization
```

but it is not one global status machine.

Different WorkSteps may simultaneously be:

- awaiting explicit capability disposition;
- waiting for an evaluation;
- uniquely matched;
- blocked by no compatible capability;
- blocked by multiple compatible capabilities;
- capability-matched but without explicit proposal disposition;
- included in a proposal waiting for Governance;
- omitted by a partial Governance decision;
- denied;
- constrained;
- waiting for additional review;
- covered by an authorize decision whose exact Authorization record is an eligible transition;
- already represented by an admitted Authorization.

M2.3 preserves those facts independently.

```text
Capability Match != Governance state
Governance state != Authorization history
Authorization history != execution state
```

## 3. Neutral capability disposition

M0/M1 do not state that every ordinary WorkStep necessarily requires an M1.6 `CapabilityRequirement`.

Therefore a WorkStep with no supplied active CapabilityRequirement is exposed in:

```text
capability_disposition_required_step_refs
```

This means only that M2.3 cannot determine a capability-facing path from the explicit graph.

```text
capability_disposition_required
!= missing capability
!= capability unavailable
!= capability unnecessary
!= permission to synthesize CapabilityRequirement
```

The Host or a later explicit planning boundary must supply the semantic disposition.

## 4. One active CapabilityRequirement per WorkStep

Within the M2.3 active graph slice, at most one CapabilityRequirement may be active for one WorkStep.

Every supplied requirement must preserve the exact active WorkPlan.

```text
foreign WorkPlan requirement -> fail closed
requirement A + requirement B for same step -> fail closed
```

M2.3 has no requirement-supersession lineage and therefore cannot choose:

```text
first
latest
most specific
provider preferred
```

between competing requirements.

This does not claim that historical requirement revisions can never exist. It means an explicit successor/supersession relation is required before several historical records can be reduced to one active requirement.

## 5. Pending capability evaluation

An active CapabilityRequirement without a supplied active `CapabilityMatchEvaluation` appears in:

```text
pending_capability_requirements
```

This is deliberately narrower than availability/readiness.

```text
pending evaluation
!= no capability exists
!= capability unavailable
!= invocation not ready
!= Governance denial
```

M2.3 does not synthesize a Catalog Snapshot or run external catalog discovery.

## 6. Exact CapabilityMatchEvaluation admission

A supplied evaluation must embed one exact active requirement.

More than one active evaluation for the same exact requirement fails closed because M2.3 has no evaluation-supersession relation.

```text
competing evaluations
!= latest wins
!= successful-looking evaluation wins
```

Once admitted, the frozen M1.6 mechanical result is derived through:

```text
evaluate_capability_match_evaluation(evaluation)
```

and yields exactly:

```text
CapabilityMatch
or
CapabilityMatchIssue(NO_COMPATIBLE_CAPABILITY)
or
CapabilityMatchIssue(MULTIPLE_COMPATIBLE_MATCHES)
```

This derivation does not choose among multiple compatible capabilities.

```text
multiple matches != hidden selection
zero matches != impossible everywhere
```

## 7. Capability Availability remains outside M2.3

M1.6 explicitly freezes:

```text
Capability Match != Availability
Catalog membership != Availability
Availability != Authorization
```

The completed M1 IR does not currently contain a canonical Capability Availability / invocation-readiness record suitable for this frontier.

M2.3 therefore does **not** inspect process state, connection state, executor state, filesystem state, network reachability, provider status, or another ambient mechanism to invent availability.

```text
capability match surface
!= readiness surface
```

A later slice may add an explicit attributable readiness boundary if required. M2.3 does not preempt that design.

## 8. Neutral WorkProposal disposition

A uniquely capability-matched WorkStep is not automatically required to enter external Governance in all cases.

M0.6 explicitly permits authority-neutral paths where Governance is not universally required.

Therefore a uniquely matched step not covered by any active WorkProposal appears in:

```text
proposal_disposition_required_step_refs
```

This means:

```text
proposal disposition unresolved
```

not:

```text
Governance required
```

and not:

```text
safe to bypass Governance
```

M2.3 does not own the policy that decides whether external authority review is applicable.

## 9. WorkProposal active graph admission

Every active WorkProposal must preserve:

- the exact active WorkPlan;
- exact active CapabilityMatchEvaluation records for every proposed step;
- the M1.6 invariant that each proposed evaluation has exactly one match.

A proposal cannot bypass a current no-match or multiple-match issue by carrying another stale or convenient evaluation.

Within the active graph slice, one WorkStep may be covered by at most one active WorkProposal.

```text
overlapping proposals for one step
!= choose newest proposal
!= combine authority material silently
```

Disjoint WorkProposals for independent step subsets may coexist.

## 10. Governance pending is not Denial

An active WorkProposal with no active GovernanceDecision appears in:

```text
governance_pending_proposals
```

This is absence of a decision, not a decision kind.

```text
no GovernanceDecision
!= Denial
!= Authorization
!= require_review
```

M2.3 does not call Governance or infer a decision from Host behavior.

## 11. One active GovernanceDecision per proposal

Every supplied GovernanceDecision must embed one exact active WorkProposal.

More than one active decision for the same proposal fails closed because no decision-supersession/revocation lineage exists in M1.6.

```text
decision A + decision B
!= latest timestamp wins
!= authorize wins
!= deny wins
```

Later authority lifecycle semantics must be explicit rather than inferred from storage order.

## 12. Partial Governance decisions preserve omission

M1.6 allows one GovernanceDecision to cover only part of a WorkProposal.

M2.3 therefore computes:

```text
governance_unmentioned_step_refs
```

for proposed steps absent from all decision components.

```text
unmentioned step != denied step
unmentioned step != authorized step
```

A partial decision cannot be silently widened to the whole proposal.

## 13. Decision kinds remain distinct

M2.3 exposes distinct step surfaces for:

```text
denied_step_refs
constrained_step_refs
review_required_step_refs
```

No non-authorize component can create an Authorization transition.

```text
Denial != Authorization
Constraint != Authorization
require_review != Authorization
```

A semantic constraint that requires changed work semantics still belongs on a later Continuation / successor-resolution path; M2.3 does not mutate the WorkPlan or WorkProposal in place.

## 14. Authorization as an exact transition candidate

M1.6 Authorization is deliberately hardened to the canonical projection:

```text
Authorization = (exact GovernanceDecision, authorize component_ref)
```

There is no independently minted Authorization identifier.

Therefore an authorize Governance component determines exactly one canonical Authorization record.

M2.3 uses this property to derive:

```text
authorization_materialization_frontier
```

containing the exact `Authorization` records that are eligible next transitions but are not yet present in supplied admitted history.

This does **not** mean the orchestrator grants permission.

The permission semantics already originate in the external GovernanceDecision.

```text
Authorization transition derivation
!= Governance decision creation
!= authority amplification
!= fresh grant minting
```

The transition is idempotent:

```text
same exact decision + same authorize component
→ same Authorization identity
```

## 15. Transition candidate != admitted history

An Authorization in `authorization_materialization_frontier` is an eligible exact M1 record transition.

It is not treated as already admitted lifecycle history merely because it can be derived.

Only Authorization records explicitly supplied back in the active graph appear in:

```text
authorizations[]
materialized_authorized_step_refs
```

This preserves the M2.0 distinction:

```text
eligible transition != historical record already present
```

The Host may persist/admit the exact candidate and replay the graph; the next derivation then removes that Authorization from the transition frontier and exposes its authorized steps as materialized.

## 16. Decision identity is part of Authorization identity

`component_ref` uniqueness is scoped to one GovernanceDecision, not globally.

Two independent decisions may legally contain authorize components with the same local `component_ref`.

M2.3 therefore does not project pending authority to bare component refs.

Instead it exposes exact Authorization records whose identity includes the complete exact GovernanceDecision.

```text
(decision A, component X)
!= (decision B, component X)
```

The regression fixture explicitly proves that two disjoint decisions reusing the same component ref produce two distinct Authorization transition identities, and admitting only one leaves the other unambiguously pending.

## 17. Authorization graph admission

Every supplied Authorization must reference an exact active GovernanceDecision and one of that decision's authorize components.

Foreign/stale Authorization fails closed.

Duplicate active representation of the same canonical Authorization identity is rejected by collection normalization.

```text
Authorization for old decision
!= authority for current proposal
```

M2.3 does not infer transitive authority across proposals, steps, providers, or work revisions.

## 18. Input ordering creates no precedence

Requirements, evaluations, proposals, decisions, and authorizations are normalized by canonical identity.

Reversing caller tuple order cannot change the frontier.

```text
input ordering != active-record precedence
storage ordering != Governance ordering
```

When multiple records are semantically incompatible with one active slot, M2.3 fails closed instead of using normalized order as a hidden tie-break.

## 19. What M2.3 does not add

M2.3 does not add:

- CapabilityRequirement synthesis;
- ambient capability discovery;
- Capability Availability or readiness IR;
- readiness probing;
- hidden selection among multiple matches;
- WorkProposal synthesis;
- policy deciding whether Governance is required;
- Governance invocation or transport;
- Governance policy ownership;
- decision supersession, revocation, or leases;
- new authority token minting;
- silent WorkPlan mutation from constraints;
- executor handoff;
- Attempt / Outcome lifecycle;
- retry or fallback;
- persistence;
- a mutable global approval status.

## 20. Frozen M2.3 invariants

```text
frontier != canonical record
secondary projection != source of truth

CapabilityRequirement absence != missing capability
capability disposition required != capability required
pending evaluation != capability unavailable
Capability Match != Availability
multiple matches != hidden selection

unique Capability Match != Governance requirement
proposal disposition required != Governance required
no GovernanceDecision != Denial
unmentioned step != denied step
unmentioned step != authorized step

GovernanceDecision != Authorization history
Denial != Authorization
Constraint != Authorization
require_review != Authorization

Authorization transition candidate != admitted Authorization history
Authorization projection != fresh grant
same component_ref across decisions != same Authorization

Authorization != Attempt
Authorization != Effect
Authorization != Outcome
```

## 21. Acceptance

M2.3 is complete when executable tests prove at least:

```text
no requirement -> neutral capability disposition
frontier is non-canonical and constructor revalidates graph
requirement without evaluation -> pending evaluation
unique evaluation -> exact CapabilityMatch
zero/multiple match -> exact CapabilityMatchIssue
foreign/competing requirements fail closed
orphan/competing evaluations fail closed
matched step without proposal -> neutral proposal disposition
proposal without Governance -> pending, not denied
overlapping active proposals fail closed
partial Governance omission stays unmentioned
authorize decision yields exact Authorization transition candidate
admitting that exact Authorization removes the candidate and exposes authorized step
Deny / Constrain / RequireReview remain distinct
competing active Governance decisions fail closed
foreign Authorization fails closed
same component_ref in different decisions preserves exact decision identity
input tuple order does not create precedence
all frozen M0/M1/M2.0–M2.2 tests remain green
Python 3.11–3.14 CI passes
```

After M2.3 closes, the next planned slice is **M2.4 — Attempt / Outcome / Continuation Orchestrator**.
