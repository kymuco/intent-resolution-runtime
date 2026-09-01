# M1.5b — Worker Delegation IR

Status: **implementation slice — Part B1: DelegatedWork / Handoff core**.

M1.5b encodes the frozen M0.8 Worker Delegation boundary without turning IRR into a Worker orchestration runtime, importing Codexia-specific semantics, minting authority, or collapsing Worker result lifecycle into M1.7.

Part B1 answers one implementation question:

> What exact immutable envelope may IRR hand to a Worker when long-form subordinate autonomy is required?

The answer is an explicit `DelegatedWork` contract plus an attributable `DelegatedWorkHandoff`.

```text
ResolvedIntent identity
       |
       +---- optional exact parent WorkPlan identity
       |
       v
 DelegatedWork
       |
       v
DelegatedWorkHandoff
       |
       v
     Worker
 subordinate lifecycle
       |
       v
 WorkerResult / need
   (later Part B2)
```

Core invariants:

```text
Worker != Cognitive Provider
Worker != Executor by default
DelegatedWork != ordinary WorkStep
DelegatedWork != Authorization
DelegatedWorkHandoff != Authorization
worker context surface != ambient context entitlement
capability allowance != Capability Match
same capability_ref != same capability semantics
allowed capability set != worker selection policy
forbidden effect != complete authority model
not forbidden != authorized
worker subplan != parent WorkPlan mutation
material delegation widening != worker-local discretion
```

Part B1 stops before `WorkerResult`, progress, cancellation, retry, Outcome, and generic Continuation. Those semantics receive a separate Part B2 review so M1.5 does not accidentally absorb M1.7.

## 1. DelegatedWork

```text
DelegatedWork
├─ schema = irr.delegated_work.v1
├─ resolved_intent_identity
├─ delegation_ref
├─ parent_work_plan_identity_refs[]
├─ objective
├─ scopes[]
├─ context_surface[]
├─ allowed_capabilities[]
├─ constraints[]
├─ expected_deliverables[]
├─ completion_contract
└─ description
```

`DelegatedWork` is the complete admitted semantic envelope for one bounded Worker-owned subordinate lifecycle. It is not itself a Worker invocation, permission, Governance decision, or proof that a listed capability is present or usable.

```text
DelegatedWork != handoff
DelegatedWork != execution
DelegatedWork != Authorization
DelegatedWork != Capability Match
```

## 2. Parent lineage

Every delegation carries exact `resolved_intent_identity`.

`parent_work_plan_identity_refs` contains zero or one exact WorkPlan record identities. Empty means direct derivation from the admitted ResolvedIntent surface; one identity preserves derivation from one exact WorkPlan.

Multiple parent WorkPlan identities fail closed in v1.

```text
parent lineage != inherited authority
same objective + different parent work != same delegation record
```

`delegation_ref` is an opaque Host-supplied stable reference. It is identity-covered but does not authenticate the delegation or grant authority.

## 3. Bounded objective

`objective` is required non-empty semantic text describing the subordinate goal.

The schema cannot infer boundedness from prose. Admission must still reject an objective whose real semantics are effectively `do whatever seems useful until solved`.

```text
finite envelope != bounded objective proof
```

## 4. DelegatedScope

```text
DelegatedScope
├─ schema = irr.delegated_scope.v1
├─ scope_ref
├─ semantic_type
├─ value
└─ description
```

A DelegatedWork record requires at least one scope. A scope can represent a repository, artifact set, dataset, account surface, time window, semantic domain, output surface, or another explicitly bounded domain.

`scope_ref` is opaque. `semantic_type` and `value` are identity-covered semantics, but IRR does not infer ownership, containment, reachability, or permission from them.

```text
delegated scope != whole parent resource universe
scope_ref != resource verification
scope != permission
```

## 5. DelegatedContextReference

```text
DelegatedContextReference
├─ schema = irr.delegated_context_reference.v1
├─ context_ref
├─ semantic_type
├─ scope_ref
├─ source_identity_refs[]
└─ description
```

The context surface is explicit rather than ambient. Every entry must reference one admitted delegated scope.

```text
IRR context availability != Worker context surface
Worker context surface != ambient retrieval authority
Worker context surface != transport Authorization
```

`source_identity_refs` preserves exact canonical source-record lineage where such identities exist. It may be empty for externally referenced material because generic artifact digest/receipt semantics remain deferred.

A context reference does not prove truth, freshness, completeness, retrievability, or permission for a particular remote transport.

## 6. Delegated capability allowance

The capability ceiling is a canonical tuple of exact allowance records:

```text
DelegatedCapabilityAllowance
├─ schema = irr.delegated_capability_allowance.v1
├─ allowance_ref
├─ capability_ref
├─ capability_contract_identity
├─ scope_refs[]
└─ description
```

M0.5 freezes that a stable human-readable capability ID alone does not prove unchanged capability semantics. Therefore Part B1 does **not** freeze the Worker ceiling as plain `StableRef[]`.

`capability_ref` is the logical reference. `capability_contract_identity` is the exact immutable semantic identity of the capability contract admitted into this ceiling. Changing that identity changes the allowance and DelegatedWork identities.

```text
same capability_ref != same capability semantics
capability_contract_identity != Capability Match
```

`scope_refs` is non-empty and every referenced scope must be admitted by the parent DelegatedWork. One logical `capability_ref` may occur at most once in a delegation; a single allowance carries its complete admitted scope set rather than creating precedence between duplicate entries.

Part B1 does not import the M1.6 Capability Descriptor or Catalog schema. M1.6 will still establish that an exact contract identity belongs to the applicable Catalog Snapshot, matches the requested semantics, is available/readiness-compatible, and satisfies downstream Governance requirements.

```text
capability allowance != Catalog membership proof
capability allowance != Capability Match
capability allowance != Availability
capability allowance != invocation readiness
capability allowance != Authorization
allowed capability set != worker selection policy
```

An empty `allowed_capabilities` tuple means no IRR-visible capability contract is admitted by this ceiling. It never means unrestricted access. Worker-internal pure cognition or implementation detail does not become an ambient IRR Capability merely because the tuple is empty.

A materially new capability contract or scope returns to IRR rather than becoming Worker fallback authority.

## 7. DelegationConstraint

```text
DelegationConstraint
├─ schema = irr.delegation_constraint.v1
├─ constraint_ref
├─ kind
│  ├─ material
│  ├─ forbidden_effect
│  └─ authority_requirement
└─ statement
```

Part B1 freezes constraint roles, not a universal effect taxonomy or Governance language.

`material` is a semantic restriction on subordinate discretion.

`forbidden_effect` is an explicit negative bound such as no external publication or no repository mutation.

```text
forbidden effect != complete positive authority model
not forbidden != authorized
```

`authority_requirement` records that some represented semantics require an external authority boundary. It is an identity-covered requirement statement, not Authorization and not a future M1.6 Governance record.

```text
authority requirement != Authorization
DelegationConstraint != Governance Decision
```

Concrete effect classification, Capability Match, WorkProposal, Governance, Authorization coverage, Denial, and authority-bearing records remain M1.6.

## 8. ExpectedDeliverable

```text
ExpectedDeliverable
├─ schema = irr.expected_deliverable.v1
├─ deliverable_ref
├─ semantic_type
├─ scope_ref
└─ description
```

A DelegatedWork v1 record requires at least one expected deliverable. Each deliverable references an admitted delegated scope; that scope may represent an output/artifact surface.

```text
useful output != required deliverable by default
```

Actual Worker-produced material and whether it satisfies a deliverable belong to Part B2.

## 9. Delegated completion contract

`completion_contract` records the bounded semantic meaning of completing the delegated subtask.

It is distinct from Worker assertion, transport success, one subordinate effect, parent WorkPlan completion, and parent intent satisfaction.

```text
delegated completion contract != worker completion claim
delegated completion != parent completion
```

Part B1 stores the contract only. Result claims/evidence remain Part B2/M1.7 territory.

## 10. Canonical set-like surfaces

Presentation order is not semantic for these sets. Canonical order is:

- scopes by `scope_ref`;
- context entries by `context_ref`;
- capability allowances by `allowance_ref`;
- allowance scope refs by `(namespace, value)`;
- constraints by `constraint_ref`;
- expected deliverables by `deliverable_ref`;
- source record identities by `(algorithm, digest)`.

Duplicate semantic keys fail closed. In particular, duplicate logical `capability_ref` values fail closed even when their allowance refs differ, preventing one logical capability label from carrying competing contract identities inside one delegation.

```text
tuple order != Worker precedence
duplicate semantic key != implicit override
```

## 11. DelegationHandoffAttribution

```text
DelegationHandoffAttribution
├─ schema = irr.delegation_handoff_attribution.v1
├─ dispatcher_ref
├─ worker_ref
└─ handoff_event_ref
```

This preserves the dispatcher, target Worker, and exact handoff occurrence. Attribution is not authentication, trust amplification, Worker availability, or authority.

```text
worker_ref != trusted result
dispatcher_ref != Governance
handoff occurrence != Authorization
```

## 12. DelegatedWorkHandoff

```text
DelegatedWorkHandoff
├─ schema = irr.delegated_work_handoff.v1
├─ attribution
└─ delegated_work
```

The handoff embeds the complete immutable DelegatedWork rather than relying on mutable ambient state.

Changing the Worker target changes handoff identity while the DelegatedWork identity remains unchanged when the admitted delegation semantics are unchanged.

```text
Worker substitution != delegation mutation by definition
Worker substitution != semantic equivalence proof
DelegatedWorkHandoff != Authorization
```

Whether substitution is admissible still depends on disclosure, capability, provider/service, cost, completion, effect, and authority compatibility. Representation of two Worker refs does not declare them interchangeable.

## 13. Handoff is not transport or execution

Part B1 does not open a socket, launch a process, disclose bytes, invoke a model, select an adapter, schedule work, or create an external effect.

```text
DelegatedWorkHandoff != transport
DelegatedWorkHandoff != Worker acceptance
DelegatedWorkHandoff != execution
DelegatedWorkHandoff != Outcome
```

Remote Worker transport may require external disclosure/network authority. Local placement still gives no ambient local context entitlement.

## 14. Subordinate autonomy remains behind the envelope

DelegatedWork makes Worker-owned subordinate autonomy explicit without encoding the Worker subplan.

```text
worker subplan != parent WorkPlan
worker subplan mutation != parent WorkPlan mutation
internal helper != nested IRR Worker by default
```

Part B1 contains no recursive Worker-delegation field.

## 15. Material widening returns to IRR

Part B1 exposes no field or mutation path that lets a Worker expand objective, scope, context disclosure, capability ceiling, forbidden effects, authority requirements, deliverables, or completion meaning.

```text
necessary prerequisite != delegated expansion authority
material widening != Worker-local discretion
```

A later need for widening must return as attributable Worker result/need material and go through explicit continuation semantics.

## 16. Closed schema and authority boundary

Public Part B1 records are frozen, slotted, exact-type validated where nested, and sealed through the package surface. Unknown wire fields fail closed.

The wire contains no authority-grant fields such as `authorized`, `approved`, `safe`, `permission_granted`, `execute`, or hidden retry flags.

An `authority_requirement` constraint states a requirement; it does not grant authority.

## 17. Canonical identity

All Part B1 records remain inside the existing M1 object/array/string canonical domain.

```text
identity = sha256(canonical_json_bytes(record))
```

No numeric, boolean, null, arbitrary-code, or execution-control canonical extension is introduced.

Representative Part B1 golden identities are intentionally deferred until the initial candidate survives first-party semantic review.

## 18. Explicit deferrals

Part B1 does not freeze:

- WorkerResult or Worker result material/finding schemas;
- Worker need/escalation or completion-claim schema;
- progress/streaming;
- Worker acceptance/rejection;
- Worker lifecycle state machine;
- cancellation, timeout, retry, fallback, interruption, unknown outcome;
- Outcome or generic IRR Continuation;
- result re-entry classification;
- nested Worker delegation;
- Worker registry/discovery, scheduling, concurrency, transport/protocol;
- concrete Capability Descriptor/Catalog/Match or Catalog Snapshot wire schemas;
- Capability Availability/readiness;
- concrete effect taxonomy;
- WorkProposal/Governance/Authorization;
- disclosure-policy implementation;
- generic artifact digest/receipt schema;
- persistence;
- Codexia-specific integration.

WorkerResult and explicit result/need re-entry are the next M1.5b sub-slice. Capability/Governance remains M1.6. Attempt/Outcome/Continuation remains M1.7.

## 19. Acceptance

Part B1 is correct when executable tests prove at least:

```text
DelegatedWork is immutable and round-trippable
DelegatedWork preserves exact ResolvedIntent lineage
zero-or-one exact parent WorkPlan identity is representable
multiple parent WorkPlan identities fail closed
delegated scope is explicit and nonempty
context surface is explicit rather than ambient
context entries must belong to admitted delegated scopes
context source identities are preserved canonically
capability allowances carry logical refs plus exact contract identities
capability contract identity changes DelegatedWork identity
capability allowances are explicitly scoped to admitted delegated scopes
same logical capability ref cannot silently carry competing contracts
empty allowed capability tuple is explicit and means no admitted capability allowance
duplicate scope/context/capability/constraint/deliverable refs fail closed
forbidden-effect and authority-requirement roles remain distinct
expected deliverables are explicit and nonempty
expected deliverables must belong to admitted delegated scopes
completion contract is explicit and identity-covered
set-like presentation order does not create precedence
DelegatedWorkHandoff embeds the exact immutable delegation
handoff preserves dispatcher/Worker/event attribution
Worker substitution changes handoff identity without rewriting DelegatedWork
unknown wire fields fail closed
public delegation records are closed against subclass state
no Authorization field is introduced
no WorkerResult/Outcome/Continuation semantics are smuggled into Part B1
```
