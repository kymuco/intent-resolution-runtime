# M3.0.2 — Work Disposition Admission Prerequisite

## Purpose

M3.0.2 adds the missing IRR-owned semantic boundary between an admitted
`ResolvedIntent` and an active `WorkPlan` or an explicit decision that no operational
work is required.

The gap was exposed by the first real HDE post-resolution Host integration slice:

```text
ResolvedIntent
    ↓
orchestrate_work_binding(resolved_intent)
    ↓
work_plan = None
work_disposition_required = True
```

M2.2 correctly refuses to interpret absence of a WorkPlan as either "no work" or
"a plan must be synthesized". M3.0.2 provides the explicit semantic transition that
M2.2 intentionally does not own.

## Existing contracts remain distinct

The existing `WorkPlan` schema is not changed.

The existing `WorkProposal` is also not reused. `WorkProposal` is a later M1.6 object
that relates an exact WorkPlan to admitted capability-match evaluations and authority
material for downstream Governance. It is therefore downstream of work disposition.

```text
CandidateWorkDisposition
!= WorkProposal

work disposition admission
!= capability proposal
!= Governance review
!= Authorization
```

## New lifecycle slice

```text
exact admitted ResolvedIntent
        ↓
CandidateWorkDisposition[]
        ↓
WorkDispositionFrontier
        ↓
explicit IRR WorkDispositionAdmitter
        ↓
NoOperationalWork | AdmittedWorkPlan
```

The candidate layer is attributable proposal material, not admitted state.

The admitted output layer is canonical immutable semantic history.

The frontier is a derived non-canonical runtime view and has no wire identity.

## CandidateWorkDisposition

`CandidateWorkDisposition` carries:

```text
exact ResolvedIntent identity
proposal attribution
kind = no_operational_work | work_plan
optional exact WorkPlan according to kind
rationale
```

Validation freezes:

```text
NO_OPERATIONAL_WORK → work_plan is None
WORK_PLAN → exact WorkPlan is present
WORK_PLAN.WorkPlan.resolved_intent_identity
    == CandidateWorkDisposition.resolved_intent_identity
```

Proposal attribution is provenance, not precedence, confidence, voting weight, or
admission authority.

Candidate ordering is canonicalized and duplicate identities are rejected.

## Admitted outputs

M3.0.2 adds two exact canonical output records.

### NoOperationalWork

`NoOperationalWork` is the positive admitted semantic statement that the exact
ResolvedIntent requires no operational work.

It is not represented as an empty plan:

```text
NoOperationalWork
!= WorkPlan(steps=())
!= noop operation
!= missing WorkPlan
```

The existing `WorkPlan` invariant that `steps` is non-empty remains unchanged.

### AdmittedWorkPlan

`AdmittedWorkPlan` admits one exact existing bounded `WorkPlan` into the active
post-resolution semantic history.

It does not modify or replace the `WorkPlan` record. It records the separate fact that
this exact plan was admitted for this exact ResolvedIntent under an exact work-
disposition admission occurrence.

```text
valid WorkPlan
!= admitted active WorkPlan

AdmittedWorkPlan
!= GovernanceDecision
!= Authorization
!= capability availability
!= execution permission
```

Downstream M2.2 binding continues to consume the embedded exact `WorkPlan`; the wrapper
exists only to preserve the missing proposal/admission distinction in canonical history.

## Explicit admission

`orchestrate_work_disposition(...)` mirrors the already-proven M2.1 initial-resolution
pattern without coupling work disposition to initial resolution.

Without an admitter:

```text
zero candidates
→ PROPOSAL_INPUT_REQUIRED

one / semantically equivalent candidates
→ ADMISSION_REQUIRED

divergent candidates
→ ADJUDICATION_REQUIRED
```

No candidate means only that explicit work-disposition input is absent. It does not mean
`NoOperationalWork`.

A new canonical output may appear only through an explicit callable
`WorkDispositionAdmitter` plus exact `WorkDispositionAdmissionAttribution`.

The orchestrator independently validates:

- exact ResolvedIntent lineage;
- exact admitted output type;
- exact supplied admission attribution;
- complete exact supplied candidate provenance.

Admitter abstention preserves the unresolved frontier.

## Existing history / replay

An already admitted exact `NoOperationalWork` or `AdmittedWorkPlan` may be supplied in
`admitted_outputs` and is returned as the exact existing disposition history.

```text
historical replay
!= new admission transition
```

Existing admitted history cannot be combined with a new admitter/admission attribution.
Competing admitted outputs fail closed rather than using first/last/latest/storage order.
Candidate material outside the admitted output's exact provenance is orphaned and fails
closed.

M3.0.2 does not add persistence. A Host persistence boundary may retain these exact
canonical bytes later, under the already-frozen Host principle:

```text
Host mechanism != semantic authority
```

## Semantic equivalence and ordering

Candidate proposal attribution is excluded from semantic equivalence.

For the M3.0.2 frontier, materially equal disposition proposals are compared by the
proposed disposition kind and exact proposed WorkPlan. Rationale text is explanatory
proposal material and does not become provider-count or ordering authority.

Therefore:

```text
same exact WorkPlan from two proposers
!= two votes
!= automatic admission

same proposal semantics + different attribution/rationale
→ still ADMISSION_REQUIRED
```

Divergent work/no-work proposals or distinct WorkPlans remain
`ADJUDICATION_REQUIRED`.

## Relationship to M2.2 Work / Binding

M2.2 remains unchanged:

```text
ResolvedIntent + zero active WorkPlan
→ work_disposition_required = True
```

After an exact `AdmittedWorkPlan` exists, the Host may project its exact embedded
`WorkPlan` into the existing M2.2 graph:

```text
AdmittedWorkPlan.work_plan
        ↓
orchestrate_work_binding(
    resolved_intent,
    work_plans=(exact_work_plan,),
)
```

This does not make the Host the semantic authority. The canonical admission record is
the basis for supplying that active plan.

`NoOperationalWork` does not enter M2.2 as a fake WorkPlan. It is an explicit terminal
work-disposition semantic record for this slice.

## Relationship to capability and Governance

M3.0.2 is strictly upstream of:

```text
Binding
CapabilityRequirement
CapabilityMatch
WorkProposal
GovernanceDecision
Authorization
CapabilityAttempt
CapabilityOutcome
Executor
Worker
```

It does not construct or admit any of those records.

A plan may be semantically admitted and still be impossible, unavailable, unmatched,
unauthorized, or unexecuted downstream.

## Existing frozen-schema compatibility

M3.0.2 does **not** change the canonical bytes, validation, identity, or schema of any
existing M1/M2 record, including `ResolvedIntent`, `WorkPlan`, `WorkStep`,
`WorkProposal`, `GovernanceDecision`, or `Authorization`.

It introduces a new versioned canonical post-resolution admission family required by
real Host integration. This is an additive M3 Host-integration prerequisite, not a
claim that the historical M1 inventory already contained these records.

## Non-goals

M3.0.2 adds no:

- planner or Cognitive Provider transport;
- ranking, confidence, majority voting, or latest-wins policy;
- BindingInput acquisition or binding evaluation;
- capability discovery, matching, availability, or readiness;
- WorkProposal synthesis;
- Governance invocation or policy;
- Authorization;
- Executor/Runplane handoff or effects;
- Worker delegation;
- retry, fallback, recovery, scheduler, or persistence.

## Frozen M3.0.2 invariants

```text
ResolvedIntent != WorkPlan
valid WorkPlan != admitted active WorkPlan

CandidateWorkDisposition != admitted work disposition
proposal attribution != precedence
proposal count != voting authority
proposal order != semantic authority

no candidate != NoOperationalWork
missing WorkPlan != NoOperationalWork
NoOperationalWork != empty/no-op WorkPlan

planner/provider proposal != IRR work admission
IRR work admission != Governance Authorization
AdmittedWorkPlan != execution authority

WorkDispositionFrontier != canonical semantic history
historical replay != new admission transition
competing admitted outputs != latest-write-wins

Host mechanism != work semantic authority
```

## HDE consequence

Once this prerequisite is merged and pinned, HDE M32.2 can remain a Host mechanism
boundary:

```text
M32.1 work_disposition_required frontier
+ explicit candidate work-disposition source
        ↓
IRR WorkDispositionFrontier
        ↓
explicit IRR admission
        ↓
NoOperationalWork | AdmittedWorkPlan
```

HDE does not need to invent its own WorkPlan admission semantics.
