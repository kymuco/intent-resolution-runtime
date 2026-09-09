# M3.0.4 — Capability Requirement Admission Prerequisite

Status: **proposed prerequisite for HDE M33.1**.

Exact base:

```text
intent-resolution-runtime/main@3491708caeeef3fab650e70e44f8b579d62c6646
```

M2.3 already freezes the capability-facing active graph:

```text
WorkStep
→ CapabilityRequirement
→ CapabilityMatchEvaluation
→ WorkProposal
→ GovernanceDecision
→ Authorization
```

But M2.3 intentionally does not synthesize `CapabilityRequirement` records. A WorkStep
with no active requirement appears only in:

```text
capability_disposition_required_step_refs
```

and that state means neither:

```text
no capability required
```

nor:

```text
missing capability
```

It means only that explicit capability-facing semantics have not yet been supplied.

M3.0.4 closes the semantic authority gap between one exact `WorkStep` and one active
`CapabilityRequirement` without changing M2.3, discovering capabilities, performing
matching, or granting authority.

## 1. Boundary

```text
exact WorkPlan + exact WorkStep
        ↓
CandidateCapabilityRequirement[]
        ↓
CapabilityRequirementAdmissionFrontier
        ↓
explicit CapabilityRequirementAdmitter
        ↓
AdmittedCapabilityRequirement
        ↓
STOP
```

The admitted record is eligible to become the exact active `CapabilityRequirement`
material supplied to M2.3 by a Host integration boundary.

M3.0.4 itself does not call `orchestrate_capability_governance(...)`.

## 2. Requirement construction is not admission

A valid `CapabilityRequirement` can describe:

- requested scopes;
- requested effects;
- execution-boundary requirements;
- one exact WorkStep in one exact WorkPlan.

That record is semantic material, not active runtime disposition merely because it is
well-formed.

```text
CapabilityRequirement construction
!= CapabilityRequirement admission
```

Likewise:

```text
CandidateCapabilityRequirement
!= active CapabilityRequirement
```

Only an exact `AdmittedCapabilityRequirement` produced by explicit admission may cross
the admission boundary.

## 3. Proposal provenance does not vote

`CandidateCapabilityRequirement` contains:

```text
CapabilityRequirementProposalAttribution
CapabilityRequirement
rationale
```

Proposal attribution and rationale are provenance/explanation. They do not establish
precedence.

If several candidates carry the same exact `CapabilityRequirement` semantics but were
produced by different proposers or with different rationales:

```text
ADMISSION_REQUIRED
```

not:

```text
majority wins
trusted proposer wins
first wins
latest wins
```

If candidates contain materially different requirement semantics:

```text
ADJUDICATION_REQUIRED
```

## 4. Explicit admission authority

Only an explicit caller-supplied admitter together with exact
`CapabilityRequirementAdmissionAttribution` may produce a new admitted output.

The admitter receives:

```text
exact WorkPlan
exact WorkStep
complete normalized CandidateCapabilityRequirement[]
exact admission attribution
```

It may deterministically adjudicate or synthesize the final requirement semantics,
including a zero-provider-candidate case, but it must preserve the complete exact
candidate provenance supplied to that transition.

```text
admitter mechanism != hidden provider voting
admission attribution != Authorization
```

Abstention preserves the exact unresolved frontier.

## 5. Frontier kinds

```text
PROPOSAL_INPUT_REQUIRED
ADMISSION_REQUIRED
ADJUDICATION_REQUIRED
REQUIREMENT_OUTPUT_AVAILABLE
```

### `PROPOSAL_INPUT_REQUIRED`

No candidate material is currently supplied and no admission output exists.

This is not a decision that no capability is required.

### `ADMISSION_REQUIRED`

At least one candidate exists and all candidates carry the same exact requirement
semantics. Explicit admission is still required.

### `ADJUDICATION_REQUIRED`

At least two materially different exact requirement semantics are present. No ordering
or proposer metadata selects one.

### `REQUIREMENT_OUTPUT_AVAILABLE`

One exact `AdmittedCapabilityRequirement` exists for the exact WorkPlan/WorkStep target.

## 6. Absence remains unresolved

M3.0.4 deliberately does **not** introduce a `NoCapabilityRequirement` record.

The current M2.3 contract does not ingest such a record; adding it here would silently
change already-frozen M2.3 semantics.

Therefore:

```text
no admitted CapabilityRequirement
→ existing capability_disposition_required semantics remain
```

This preserves:

```text
absence != decision
```

If a future concrete scenario needs an explicit capability-free disposition, that must
be designed together with the M2.3 active graph rather than smuggled through this
prerequisite.

## 7. Exact target lineage

Every candidate and admitted output is bound to:

```text
exact WorkPlan
exact WorkStep.step_ref
```

A candidate for another WorkPlan or another WorkStep fails closed.

The admission layer cannot use a requirement to rewrite the WorkPlan or retarget a
neighboring step.

```text
valid requirement shape != active target authority
```

## 8. Canonical admitted provenance and replay

`AdmittedCapabilityRequirement` contains:

```text
CapabilityRequirementAdmissionAttribution
exact CapabilityRequirement
complete CandidateCapabilityRequirement[] provenance
```

An already-admitted output may be replayed without invoking a fresh admitter.

Replay is semantic/history verification only:

```text
admitted-output replay != new admission
```

Competing admitted outputs for one exact WorkStep fail closed. No timestamp, tuple
ordering, proposer identity, or apparent semantic quality chooses a winner.

## 9. Admission is weaker than capability matching

An admitted requirement states only:

> These are the exact capability-facing semantics currently admitted for this exact
> WorkStep.

It does not state:

```text
capability exists
catalog contains a compatible descriptor
capability is available
capability is ready
capability is selected
Governance applies
Governance approved
Authorization exists
execution may begin
```

Frozen:

```text
AdmittedCapabilityRequirement != CapabilityMatch
AdmittedCapabilityRequirement != Availability
AdmittedCapabilityRequirement != WorkProposal
AdmittedCapabilityRequirement != GovernanceDecision
AdmittedCapabilityRequirement != Authorization
AdmittedCapabilityRequirement != Attempt
```

## 10. No catalog discovery or matching

M3.0.4 accepts no `CapabilityCatalogSnapshot` and does not call capability matching.

```text
requirement admission
!= catalog discovery
!= catalog membership
!= semantic compatibility
```

A Host may later supply an explicit attributable catalog snapshot to the separate match
evaluation boundary.

Missing or ambiguous catalog state cannot cause M3.0.4 to invent a fallback capability.

## 11. Non-goals

M3.0.4 adds no:

- ambient capability discovery;
- Capability Catalog provider invocation;
- CapabilityDescriptor construction;
- CapabilityMatch synthesis;
- CapabilityMatchEvaluation;
- availability/readiness probing;
- hidden capability selection;
- WorkProposal synthesis;
- Governance invocation;
- Authorization;
- executor/Runplane invocation;
- Attempt/Outcome lifecycle;
- retry/fallback/recovery;
- Worker delegation;
- persistence or supersession history;
- explicit `NoCapabilityRequirement` semantics.

## 12. Frozen invariants

```text
absence != decision
CapabilityRequirement construction != admission
CandidateCapabilityRequirement != active requirement
proposal provenance != precedence
same semantics from several proposers != automatic admission
different semantics != hidden selection
AdmittedCapabilityRequirement != CapabilityMatch
Capability Match != Availability
AdmittedCapabilityRequirement != GovernanceDecision
AdmittedCapabilityRequirement != Authorization
Authorization != Attempt
semantic replay != new admission
Host mechanism != capability requirement semantic authority
```

## 13. HDE M33.1 handoff

After this prerequisite closes, HDE M33.1 can safely bridge:

```text
exact M32 binding-complete WorkPlan
+ exact WorkStep
+ explicit CandidateCapabilityRequirement[]
        ↓
IRR M3.0.4 admission frontier
        ↓
explicit IRR admission
        ↓
AdmittedCapabilityRequirement
        ↓
exact requirement enters M2.3 active graph
        ↓
STOP before catalog/match evaluation
```

That keeps the M33 progression disciplined:

```text
M32: WHAT is the exact bounded work?
M33.1: WHAT capability semantics does one WorkStep require?
M33.2+: WHICH supplied capability can satisfy them?
later: MAY it execute?
```
