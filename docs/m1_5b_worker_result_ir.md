# M1.5b2 — WorkerResult / Need Re-entry IR

Status: **implementation slice — Part B2: attributable Worker result surface**.

M1.5b2 extends the frozen M0.8 Worker Delegation boundary after the Part B1 `DelegatedWork` / `DelegatedWorkHandoff` envelope. It freezes returned Worker material without importing M1.7 Attempt / Outcome / Continuation state semantics.

This slice answers one question:

> What immutable result envelope may cross back from the exact Worker handoff without turning Worker assertions into truth, authorization, operational Outcome, delegated-completion proof, or parent intent completion?

The answer is an attributable `WorkerResult` that embeds the exact `DelegatedWorkHandoff` and contains only explicit returned material plus explicit `WorkerNeed` records.

```text
DelegatedWork -> DelegatedWorkHandoff -> Worker -> WorkerResult
                                                /          \
                                          material       WorkerNeed
                                                \          /
                                            later Host / IRR
                                             classification
```

Core invariants:

```text
WorkerResult != factual truth by default
WorkerResult != Observation by default
WorkerResult != Outcome by default
WorkerResult != Governance Decision
WorkerResult != Authorization
WorkerResult != parent intent completion
worker completion claim != delegated completion proof
WorkerNeed != authority grant
WorkerNeed != scope expansion
worker-generated executable text != execution authority
```

## 1. Exact handoff lineage

`WorkerResult` embeds the complete immutable `DelegatedWorkHandoff`. The returned Worker attribution must match the exact Worker targeted by that handoff.

```text
same DelegatedWork + different Worker handoff != same WorkerResult lineage
Worker substitution -> new handoff
```

The result therefore retains the exact ResolvedIntent, optional parent WorkPlan, delegation envelope, capability ceiling, constraints, deliverables, dispatcher, target Worker, and handoff-event lineage frozen by Part B1.

## 2. WorkerResultAttribution

```text
WorkerResultAttribution
├─ schema = irr.worker_result_attribution.v1
├─ worker_ref
└─ result_event_ref
```

Attribution is not authentication, factual verification, trust amplification, Worker availability, authority, or proof that the Worker obeyed its delegation.

## 3. No lifecycle status enum

Part B2 deliberately does not add `success`, `failed`, `blocked`, `interrupted`, or `unknown_outcome`. Those states belong to M1.7 / M0.9 lifecycle semantics.

A WorkerResult may carry only needs, only material, or both. It must contain at least one of them.

```text
WorkerResult existence != success
WorkerResult existence != failure
WorkerResult existence != delegated completion
```

## 4. WorkerResultMaterial

```text
WorkerResultMaterial
├─ schema = irr.worker_result_material.v1
├─ material_ref
├─ role
├─ semantic_type
├─ scope_refs[]
├─ expected_deliverable_refs[]
├─ source_refs[]
├─ source_identity_refs[]
├─ content
└─ description
```

Frozen material roles are:

```text
deliverable
finding
artifact_reference
completion_claim
uncertainty
scope_coverage
omission
other_explicit
```

These classify Worker-returned material only. They do not instantiate Context, Claim, Evidence, Observation, Outcome, Authorization, Governance Decision, or Continuation.

## 5. Required deliverable relation is explicit

A material with role `deliverable` must reference at least one exact Part B1 `ExpectedDeliverable`. Non-deliverable material cannot claim an expected-deliverable reference.

Every referenced expected deliverable must exist in the embedded DelegatedWork, use the same semantic type, and have its delegated scope covered by the returned material.

```text
useful output != required deliverable by default
artifact reference != required deliverable by default
finding != required deliverable by default
```

This structural relation does not prove the Delegated Completion Contract is satisfied.

## 6. Completion claim remains an assertion

A Worker may return `role = completion_claim` and content such as `done`. That preserves the assertion without strengthening it.

```text
completion_claim != delegated completion evidence by itself
completion_claim != parent WorkPlan completion
completion_claim != parent intent satisfaction
```

There is deliberately no `delegated_complete`, `parent_completed`, or equivalent boolean field.

## 7. Scope preservation

Every `WorkerResultMaterial.scope_refs` entry must belong to the admitted DelegatedWork scope surface. A Worker cannot make a new scope admitted merely by returning material about it.

For a requested widening, the Worker returns a `WorkerNeed` instead.

## 8. WorkerNeed

```text
WorkerNeed
├─ schema = irr.worker_need.v1
├─ need_ref
├─ kind
├─ related_scope_refs[]
└─ statement
```

Frozen need kinds are:

```text
information
capability
authority
scope
clarification
objective_change
effect_boundary
other_explicit
```

A need is attributable Worker-returned information, not permission to satisfy it.

```text
need information != retrieval authority
need capability != capability discovery/fallback authority
need authority != Authorization
need scope != admitted scope expansion
need objective_change != successor objective
need effect_boundary != effect authority
```

`related_scope_refs` may be empty, which permits a Worker to request a materially new scope without pretending that scope is already admitted. When refs are present, they must reference existing delegated scopes.

## 9. Source provenance is distinct from Worker attribution

Returned material may carry both opaque `source_refs` and exact `source_identity_refs`. The outer WorkerResult attribution still identifies the Worker intermediary.

```text
original source != Worker intermediary
source_ref != source verification
source_identity_ref != factual truth
WorkerResult source lineage != Evidence admission by default
```

Later epistemic admission must preserve original-source and Worker-intermediary provenance rather than rewriting the Worker as the original factual source.

## 10. Returned content is inert data

`WorkerResultMaterial.content` is arbitrary Unicode-scalar string data, including executable-looking text.

```text
worker-generated code != execution
worker patch text != applied mutation
shell text != authority
tool-call syntax != invocation
```

Part B2 does not execute, parse, lower, interpolate, or schedule returned content.

## 11. Canonicalization

Presentation order is non-semantic. Materials canonicalize by `material_ref`; needs by `need_ref`; scope/source refs by `(namespace, value)`; exact source identities by `(algorithm, digest)`. Duplicate material refs and duplicate need refs fail closed.

## 12. WorkerResult is not factual admission or Outcome

`finding`, `uncertainty`, `omission`, and other returned material remain Worker-produced material.

```text
WorkerResult != factual truth
finding != admitted Claim by default
source lineage != Evidence admission
Worker confidence != evidence amplification
WorkerResult != Outcome by default
```

M0.2 owns later epistemic classification. M1.7 owns Attempt / Outcome / Continuation IR.

## 13. No parent history mutation

A WorkerResult cannot rewrite prior IntentRequest, ResolvedIntent, WorkPlan, DelegatedWork, Authorization, Effects, or Outcomes. It can only return attributable material to a later explicit re-entry boundary.

```text
Worker proposal != successor ResolvedIntent
Worker proposal != successor WorkPlan
WorkerNeed != successor semantics
```

## 14. Closed public IR and deferrals

Part B2 records are immutable frozen slot dataclasses, sealed through the public package surface, and reject unknown wire fields.

Part B2 does not freeze progress/event streaming, cancellation, timeout, retry/fallback, failed/interrupted/unknown-outcome states, generic Continuation, WorkerResult-to-Context/Observation/Claim/Evidence admission algorithms, delegated completion evaluation, parent completion evaluation, concrete Capability/Governance schemas, Worker transport/registry/scheduling, nested delegation, persistence, artifact receipt schemas, or Codexia integration.

## 15. Acceptance

Part B2 is correct when executable tests prove at least:

```text
WorkerResult embeds exact DelegatedWorkHandoff
result Worker attribution matches handed-off Worker
Worker substitution changes handoff lineage
WorkerResult requires material and/or need
WorkerResult has no success/failure lifecycle status
completion claim remains ordinary returned material
deliverable material explicitly references ExpectedDeliverable
non-deliverable material cannot claim ExpectedDeliverable
deliverable semantic type and scope are revalidated
all returned material scopes belong to DelegatedWork
WorkerNeed may request new scope without pretending it is admitted
WorkerNeed related existing scopes are revalidated
WorkerNeed is not authority/scope expansion
source refs and source identities remain distinct provenance dimensions
returned executable-looking text remains inert data
material/need tuple order is canonical
duplicate material/need refs fail closed
unknown fields fail closed
public records are immutable and closed
```

After Part B2 hardening, M1.5b can freeze representative canonical identities for the delegation → handoff → result path before the outer M1.5b merge.
