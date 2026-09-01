# M1.5b — Worker Delegation IR

Status: **implementation slice — Part B1: DelegatedWork / Handoff core**.

M1.5b encodes the frozen M0.8 Worker Delegation boundary without turning IRR into a worker orchestration runtime, importing Codexia-specific semantics, minting authority, or collapsing WorkerResult into M1.7 lifecycle records.

This first Part B slice answers one implementation question:

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
allowed capability refs != Capability Match
allowed capability set != worker selection policy
forbidden effect != complete authority model
not forbidden != authorized
worker subplan != parent WorkPlan mutation
material delegation widening != worker-local discretion
```

Part B1 deliberately stops before `WorkerResult`, progress, cancellation, retry, Outcome, and generic Continuation. Those semantics require a separate result/re-entry review so M1.5 does not accidentally absorb M1.7.

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
├─ allowed_capability_refs[]
├─ constraints[]
├─ expected_deliverables[]
├─ completion_contract
└─ description
```

`DelegatedWork` is the complete admitted semantic envelope for one bounded Worker-owned subordinate lifecycle.

It is not itself a Worker invocation, execution permission, Governance decision, or proof that the listed capabilities exist.

```text
DelegatedWork != handoff
DelegatedWork != execution
DelegatedWork != Authorization
DelegatedWork != Capability Match
```

## 2. Parent lineage

Every delegation carries exact `resolved_intent_identity`.

`parent_work_plan_identity_refs` contains zero or one exact WorkPlan record identities:

- empty means the delegation derives directly from the admitted ResolvedIntent surface;
- one identity preserves derivation from one exact parent WorkPlan.

Part B1 intentionally does not permit multiple parent WorkPlan identities in one delegation.

```text
parent lineage != inherited authority
same objective + different parent work != same delegation record
```

The Host-supplied `delegation_ref` is opaque. It is identity-covered but does not authenticate the delegation or create persistence semantics beyond this record.

## 3. Explicit delegated objective

`objective` is required non-empty semantic text describing the bounded subordinate goal.

The schema cannot infer whether arbitrary prose is semantically bounded. Admission must still reject an objective whose real meaning is effectively:

```text
do whatever seems useful until the project is solved
```

A finite record does not make an unbounded objective safe.

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

A delegation has at least one explicit scope.

A scope may represent a bounded repository, artifact set, dataset, account surface, time window, semantic domain, output surface, or another explicitly admitted domain.

`scope_ref` is an opaque stable reference. `semantic_type` and `value` describe the admitted scope semantics without interpreting resource ownership, reachability, containment, or authority.

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

The context surface is an explicit list of material intended for the Worker boundary.

Every entry must point to one admitted delegated scope. Context available elsewhere inside IRR is not automatically present here.

```text
IRR context availability != Worker context surface
Worker context surface != ambient retrieval authority
Worker context surface != transport Authorization
```

`source_identity_refs` preserves exact canonical source-record lineage when such identities exist. It may be empty for externally referenced material that does not yet have an IRR record identity.

Including a context reference does not prove the material is true, fresh, complete, retrievable, or authorized for a particular remote transport. Those remain separate boundaries.

## 6. Allowed capability ceiling

`allowed_capability_refs` is a canonical tuple of opaque `StableRef` values.

Part B1 deliberately does not import M1.6 Capability Descriptor, Catalog, Match, Availability, or Governance schemas.

```text
allowed capability ref != known Capability
allowed capability ref != Capability Match
allowed capability ref != availability
allowed capability ref != invocation readiness
allowed capability ref != Authorization
allowed capability set != worker selection policy
```

An empty tuple means **no IRR-visible capability reference is admitted by this ceiling**. It never means unrestricted capability access.

Worker-internal pure cognition or implementation detail is not represented as an ambient IRR Capability merely because the tuple is empty.

If a later Worker requires a materially new capability outside this ceiling, the need returns to IRR rather than becoming hidden Worker fallback.

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

Part B1 freezes only the **role** of the constraint, not a universal effect taxonomy or Governance language.

### `material`

An admitted semantic restriction that bounds the delegated objective or subordinate discretion.

### `forbidden_effect`

An explicit negative effect bound such as no external publication or no repository mutation.

```text
forbidden effect != complete positive authority model
not forbidden != authorized
```

### `authority_requirement`

An explicit statement that some part of the delegated semantics is authority-sensitive or requires an external authority boundary.

This is not Authorization and does not name or instantiate a future M1.6 Governance record.

```text
authority requirement != Authorization
DelegationConstraint != Governance Decision
```

Concrete effect classification, Capability matching, Governance review, Authorization coverage, Denial, and constraints that rewrite work semantics remain M1.6.

## 8. ExpectedDeliverable

```text
ExpectedDeliverable
├─ schema = irr.expected_deliverable.v1
├─ deliverable_ref
├─ semantic_type
├─ scope_ref
└─ description
```

A DelegatedWork v1 record requires at least one expected deliverable.

Each expected deliverable belongs to one admitted delegated scope. The scope may be an output/artifact surface rather than an input resource surface.

The explicit deliverable contract prevents a Worker from satisfying a bounded task merely by returning unrelated useful material.

```text
useful output != required deliverable by default
```

Actual Worker-produced material and whether it satisfies an expected deliverable belong to Part B2 WorkerResult semantics.

## 9. Delegated completion contract

`completion_contract` states the bounded semantic meaning of completing the delegated subtask.

It is distinct from:

- a Worker saying `done`;
- transport success;
- one subordinate effect succeeding;
- parent WorkPlan completion;
- parent intent satisfaction.

```text
delegated completion contract != worker completion claim
delegated completion != parent completion
```

Part B1 stores the contract only. Part B2/M1.7 will preserve returned claims and later result/evidence semantics without silently turning them into truth.

## 10. Canonical set-like surfaces

Where presentation order is not semantic, Part B1 canonicalizes by explicit reference:

- scopes by `scope_ref`;
- context entries by `context_ref`;
- allowed capability refs by `(namespace, value)`;
- constraints by `constraint_ref`;
- expected deliverables by `deliverable_ref`;
- source record identities by `(algorithm, digest)`.

Duplicate refs fail closed instead of creating presentation-order precedence.

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

This records attribution of one handoff occurrence:

- who/what dispatched the admitted envelope;
- which Worker target received that semantic handoff;
- which exact handoff event occurrence is represented.

Attribution is not authentication, trust amplification, Worker availability, or authority.

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

The handoff embeds the complete exact DelegatedWork record rather than referencing mutable ambient state.

Changing the Worker target changes handoff identity while leaving the DelegatedWork identity unchanged when the admitted delegation semantics themselves are unchanged.

```text
Worker substitution != delegation mutation by definition
Worker substitution != semantic equivalence proof
DelegatedWorkHandoff != Authorization
```

Whether substitution is actually admissible depends on preserving disclosure, capability, effect, cost, completion, and authority semantics. Part B1 does not assume that two Worker refs are interchangeable merely because both can be represented.

## 13. Handoff is not transport or execution

Part B1 does not open a socket, launch a process, disclose bytes, invoke a model, schedule work, select an adapter, or create an external effect.

```text
DelegatedWorkHandoff != transport
DelegatedWorkHandoff != Worker acceptance
DelegatedWorkHandoff != execution
DelegatedWorkHandoff != Outcome
```

A remote Worker transport may itself require disclosure/network authority. A local Worker still does not gain ambient local context.

Those effect/authority checks remain external.

## 14. Worker-local autonomy remains bounded

The existence of DelegatedWork makes subordinate autonomy explicit, but it does not encode the Worker subplan.

A Worker may internally analyze, revise subordinate plans, use implementation-internal helpers, or generate artifacts only inside the admitted envelope and applicable downstream authority boundaries.

```text
worker subplan != parent WorkPlan
worker subplan mutation != parent WorkPlan mutation
internal helper != nested IRR Worker by default
```

Part B1 contains no recursive Worker-delegation field.

## 15. Material widening returns to IRR

Part B1 does not include any method or field that lets a Worker widen:

- objective;
- scopes;
- context disclosure;
- capability ceiling;
- forbidden effects;
- authority requirements;
- expected deliverables;
- completion meaning.

A need for such widening must later appear as attributable WorkerResult/need material and return through the explicit continuation boundary.

```text
necessary prerequisite != delegated expansion authority
material widening != Worker-local discretion
```

## 16. Closed schema and authority boundary

All public Part B1 records are immutable frozen slot dataclasses and are sealed through the package public surface.

Unknown fields fail closed.

The wire schemas contain no fields such as:

```text
authorized
approved
safe
permission_granted
execute
retry_until_success
```

An `authority_requirement` constraint is an explicit requirement statement, not an authority grant.

## 17. Canonical identity

All Part B1 records remain inside the existing M1 object/array/string canonical domain.

Identity remains:

```text
sha256(canonical_json_bytes(record))
```

No numeric, boolean, null, arbitrary code, or executable-control-flow canonical extension is introduced.

Representative Part B1 golden identities will be frozen only after first-party semantic review of the initial candidate.

## 18. Explicit deferrals

Part B1 does not freeze:

- WorkerResult;
- Worker result material/finding schemas;
- Worker need/escalation schema;
- Worker completion-claim schema;
- progress/streaming;
- Worker acceptance/rejection;
- Worker lifecycle state machine;
- cancellation;
- timeout;
- retry/fallback;
- interrupted/unknown-outcome semantics;
- Outcome records;
- generic IRR Continuation;
- result re-entry classification;
- nested Worker delegation;
- Worker discovery/registry;
- scheduling/concurrency;
- transport/protocol;
- concrete Capability Descriptor/Catalog/Match;
- Capability Availability/readiness;
- concrete effect taxonomy;
- WorkProposal/Governance/Authorization;
- disclosure-policy implementation;
- artifact digest/receipt schema;
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
allowed capability refs are an explicit ceiling
empty allowed capability tuple is representable and not omitted
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
