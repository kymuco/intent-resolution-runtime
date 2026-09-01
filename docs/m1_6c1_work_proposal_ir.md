# M1.6c1 — WorkProposal IR

Status: **implementation slice — authority-neutral Governance input surface**.

M1.6a froze exact Capability Descriptor / Catalog Snapshot semantics. M1.6b1 froze exact WorkStep ↔ Capability Match relations. M1.6b2 froze exhaustive bounded match evaluation and the fail-closed `0 / 1 / >1` cardinality boundary. M1.6c1 now freezes the immutable operational work representation that IRR may present to an external Governance boundary.

This slice does **not** introduce Governance decisions, Authorization, Denial, require-review, authority conditions, execution, Attempt/Outcome, or generic Continuation state.

```text
exact WorkPlan
      +
unique exact CapabilityMatchEvaluation per reviewed WorkStep
      +
authority-relevant attributable material
      ↓
WorkProposal
      ↓
external Governance   [M1.6c2]
```

Core invariants:

```text
WorkProposal != WorkPlan mutation
WorkProposal != Authorization
proposal attribution != authority
Capability Match != Authorization
authority-relevant material != permission
human-readable statement != sole authority-binding source
B2 multiple-match issue != permission to choose one match for proposal
mixed Catalog occurrences != one WorkProposal v1
proposal subset != Authorization of that subset
unproposed WorkStep != deleted historical work
```

## 1. Why WorkProposal is a separate record

A `WorkPlan` is semantic work. It must not gain fields such as `approved`, `safe`, `permission_granted`, or `user_consented` when Governance is introduced.

`WorkProposal` is a separate immutable occurrence that identifies exactly which already-admitted operational work is being placed before Governance.

```text
WorkPlan validity != authority
WorkProposal creation != authority
```

The complete exact `WorkPlan` is embedded so historical intent/work semantics cannot be replaced by a lossy review summary.

## 2. WorkProposalAttribution

```text
WorkProposalAttribution
├─ schema = irr.work_proposal_attribution.v1
├─ proposer_ref
└─ proposal_event_ref
```

This records which boundary produced one proposal occurrence. It is provenance only.

```text
proposer_ref != authorized principal
proposal_event_ref != approval event
proposal attribution != Governance Decision
```

Changing the proposal occurrence changes WorkProposal identity even when reviewed work semantics are unchanged.

## 3. ProposedWorkStep

```text
ProposedWorkStep
├─ schema = irr.proposed_work_step.v1
├─ step_ref
└─ capability_evaluation
```

The capability surface is deliberately an exact `CapabilityMatchEvaluation`, **not** a bare B1 `CapabilityMatch`.

A `ProposedWorkStep` is valid only when evaluating that exact B2 record returns exactly one `CapabilityMatch`.

```text
0 compatible matches -> cannot become ProposedWorkStep
>1 distinct compatible match relations -> cannot become ProposedWorkStep
exactly 1 admitted match -> eligible for proposal materialization
```

This prevents M1.6c from bypassing M1.6b2 by manually selecting one candidate out of a material ambiguity set.

```text
manual B1 match selection != admitted proposal capability relation
Catalog order != proposal selection rule
provider preference != proposal selection rule
```

`capability_match` is a derived property of the unique evaluation result. It is not a separately supplied wire field.

## 4. Exact WorkPlan lineage

Every proposed step must belong to the exact embedded WorkPlan, and its `CapabilityMatchEvaluation.requirement.work_plan` must equal that exact WorkPlan.

```text
same plan_ref != same exact WorkPlan
same step_ref in different plan bytes != same proposal lineage
```

The proposal may review a bounded subset of already represented WorkSteps. The remaining WorkSteps stay in the embedded historical WorkPlan; they are neither deleted nor implicitly authorized.

```text
proposal subset != WorkPlan rewrite
proposal subset != claim that remaining objective disappeared
```

M1.6c1 does not require the reviewed subset to be dependency-closed. Governance may review one already represented portion separately; downstream execution still cannot infer authority for omitted dependencies.

## 5. One exact Catalog occurrence per WorkProposal v1

Every proposed step in one `WorkProposal.v1` must use the same exact `CapabilityCatalogSnapshot` occurrence through its embedded B2 evaluation.

```text
WorkStep A validated under Catalog occurrence X
+
WorkStep B validated under Catalog occurrence Y
    !=
one WorkProposal v1
```

This closes capability-drift laundering. A WorkPlan must not be presented as one coherent authority review surface while silently mixing capability semantics from different Catalog occurrences.

If capability drift requires revalidation under a later Catalog, that later lineage must remain explicit rather than being merged invisibly into the same proposal occurrence.

## 6. WorkProposalMaterial

```text
WorkProposalMaterial
├─ schema = irr.work_proposal_material.v1
├─ material_ref
├─ kind
├─ step_refs[]
├─ source_ref
├─ source_identity
├─ scope
└─ statement
```

`WorkProposalMaterial` carries authority-relevant facts that Governance may need in addition to the exact WorkPlan / Capability semantics.

M1.6c1 kinds are:

```text
affected_resource
data_flow
disclosure
recipient
uncertainty
other_explicit
```

This is a presentation/admission vocabulary, not a policy or risk taxonomy.

Examples include:

- the concrete or symbolic resource whose mutation is proposed;
- a material local→external data flow;
- a recipient identity or bounded recipient class;
- uncertainty that must remain visible during review;
- another explicit authority-relevant fact.

## 7. Material provenance

Every material record carries two provenance dimensions:

```text
source_ref
source_identity
```

`source_ref` identifies the attributed source record/boundary in the embedding contract. `source_identity` pins exact source content identity where supplied.

Neither proves truth, authenticity, freshness, ownership, consent, or authority.

```text
material provenance != factual truth
material provenance != Authorization
material source identity != source verification
```

A material record can cite, for example, an exact BoundValue, Claim, external Governance-input record, Host-provided recipient record, or another admitted source without reclassifying that source.

## 8. Material is not semantic-widening authority

`WorkProposalMaterial` describes authority-relevant semantics already admitted or attributable for review. It must not be used to invent a new recipient, scope, effect, provider, disclosure, or other material operational meaning that is absent from the WorkPlan/capability/continuation lineage.

```text
materialization != authority to widen work semantics
```

If new material information changes work semantics, IRR must use the applicable successor resolution/binding/capability path. It cannot hide that change inside a Governance presentation statement.

## 9. Material must point only to proposed work

Every `WorkProposalMaterial.step_refs` tuple is non-empty and may reference only WorkSteps included in this proposal occurrence.

This prevents a proposal from presenting authority material for a step that is not actually under review while implying that it is part of the reviewed subset.

One material record may refer to several proposed steps when the same data flow, recipient, resource, or uncertainty spans them.

Set-like step references are canonicalized and duplicate refs fail closed.

## 10. Empty extra material is allowed

`authority_material` itself may be empty.

This does **not** mean no authority-relevant semantics exist. Exact WorkPlan, CapabilityRequirement, Descriptor effects/scopes/provider boundaries, and B2 evaluation lineage remain embedded through each proposed step.

The semantic admission rule remains:

> when recipient, disclosure, concrete bound resource, uncertainty, or another fact is materially authority-relevant and not already inspectable enough through frozen IR, the WorkProposal must preserve it explicitly rather than erase it.

M1.6c1 cannot mechanically infer all domain-specific materiality from open semantic tokens, so correctness of that admission is an IRR responsibility rather than a fake boolean completeness proof.

## 11. Human-readable material is not authority identity

`scope`, `statement`, and `description` fields are identity-covered, inspectable semantic text. They do not replace exact embedded WorkPlan / Capability / source identity lineage.

```text
"send report to Alice" text
    !=
exact authority-binding recipient/work identity by itself
```

Governance may render human-readable summaries, but M1.6c2 Authorization must bind to exact reviewed proposal semantics rather than only to prose.

## 12. No Governance state in C1

The following fields/states are intentionally absent:

```text
approved
authorized
denied
safe
consented
review_required
policy_result
permission_token
```

Unknown authority-like wire fields fail closed through exact-key parsing.

```text
WorkProposal existence != external review occurred
WorkProposal existence != optimistic permission
```

## 13. Capability and authority remain separate

A proposed step contains a unique exact capability relation only because Governance must know what capability semantics are associated with the reviewed work.

```text
CapabilityMatch != Authorization
CapabilityMatchEvaluation != Authorization
unique capability candidate != permission
```

Likewise, future Authorization cannot create a missing Capability or repair a multiple-match ambiguity.

## 14. Canonical ordering

Set-like surfaces are canonicalized using explicit stable identifiers:

```text
proposed_steps      -> step_ref
authority_material  -> material_ref
material.step_refs  -> StableRef
```

Duplicate semantic keys fail closed rather than creating tuple-order precedence.

## 15. Canonical identity

All C1 records use the frozen M1 canonical JSON domain and SHA-256 `RecordIdentity`.

WorkProposal identity covers at least:

- proposal attribution/occurrence;
- complete exact WorkPlan;
- exact B2 evaluation for every proposed step;
- exact unique CapabilityMatch relation derived from each evaluation;
- exact Catalog occurrence through those evaluations;
- all authority material and its provenance;
- proposal description.

Therefore:

```text
changed WorkPlan -> changed proposal identity
changed capability contract -> changed proposal identity
changed Catalog occurrence -> changed proposal identity
changed authority material -> changed proposal identity
changed proposal occurrence -> changed proposal identity
```

## 16. Explicit deferrals

M1.6c1 deliberately does not introduce:

- Governance Decision records;
- authorize/deny/constrain/require-review components;
- Authorization scope or conditions;
- reusable grants, leases, expiry, revocation, quorum, or policy composition;
- authority evidence acquisition;
- Capability Availability or invocation readiness;
- executable CapabilityHandoff;
- Executor verification;
- Attempt / Outcome / generic Continuation;
- retry/fallback/compensation;
- persistence.

M1.6c2 owns Governance Decision / Authorization IR. M1.7 owns execution lifecycle and recovery state.

## 17. Acceptance

M1.6c1 is correct when tests prove at least:

```text
immutable closed records
exact WorkPlan lineage
ProposedWorkStep requires B2 cardinality == 1
no-match B2 evaluation cannot become proposed work
multiple-match B2 evaluation cannot become proposed work
bare/manual B1 candidate cannot bypass B2
step_ref belongs to exact evaluation requirement
all proposal evaluations use exact embedded WorkPlan
all proposed steps use one exact Catalog Snapshot occurrence
proposal may cover an explicit WorkStep subset without mutating WorkPlan
authority material references only proposed steps
material refs and step refs are canonical and duplicate-free
material provenance is identity-covered
proposal occurrence is identity-covered
unknown authority-like fields fail closed
canonical round-trip preserves identity
all earlier M1 goldens remain unchanged
```
