# M1.6c2 — Governance Decision / Authorization IR

Status: **candidate normative M1.6c2 contract**.

This document freezes the first exact M1 representation of external Governance decisions over an immutable `WorkProposal` and the separate `Authorization` record that may be materialized only from an explicit `authorize` component.

It extends M0.6 and M1.6c1 without introducing a policy engine, consent UX, capability availability, executable handoff, executor verification, attempt/outcome state, retries, revocation, reusable grants, or generic continuation.

## 1. Boundary

```text
exact WorkProposal
      |
      v
external Governance
      |
      v
GovernanceDecision
  ├─ authorize
  ├─ deny
  ├─ constrain
  └─ require_review
      |
      +-- authorize component only --> Authorization
```

The central invariants are:

```text
WorkProposal != Authorization
GovernanceDecision != Effect
authorize component != execution
deny != missing_capability
absence of Authorization != Denial
require_review != Authorization
constrain != Authorization
Authorization != Capability Match
Authorization != Availability
Authorization != Outcome
```

## 2. GovernanceDecisionAttribution

`GovernanceDecisionAttribution` preserves:

```text
governance_ref
decision_event_ref
authority_context_ref
authority_context_identity
```

The authority context pair is provenance for the externally supplied authority context used by Governance.

```text
authority_context_identity != proof that Governance was correct
Governance attribution != cryptographic authentication
Governance attribution != factual truth
```

The decision occurrence must be distinct from the `WorkProposal` occurrence. Proposal creation and authority decision are separate events.

## 3. GovernanceDecisionKind

M1.6c2 freezes four component kinds:

```text
authorize
deny
constrain
require_review
```

They are explicit authority roles, not effect states or lifecycle outcomes.

## 4. GovernanceDirective

`GovernanceDirective` is an immutable typed directive nested under a decision component:

```text
directive_ref
semantic_type
scope
statement
```

Its semantic role depends on the parent component:

- under `authorize`, a directive is an **Authorization Condition**;
- under `constrain`, a directive is a **semantic Governance Constraint** that must return through successor IRR semantics before execution;
- under `require_review`, a directive describes required external review material/conditions.

A `deny` component does not admit directives in v1; its rationale carries the denial basis.

Most importantly:

```text
Authorization Condition != semantic WorkPlan mutation
```

If satisfying an `authorize` directive would materially change resource, recipient, effect, data flow, provider semantics, Completion Semantics, or another admitted meaning, the directive is not a valid Authorization Condition. It belongs under `constrain` and requires successor semantics.

The schema preserves the distinction but cannot prove the truth of arbitrary semantic statements. Correct directive admission remains the responsibility of the Governance/IRR boundary.

## 5. GovernanceDecisionComponent

A component contains:

```text
component_ref
kind
step_refs[]
directives[]
rationale
```

`step_refs` must be a non-empty subset of the exact `WorkProposal.proposed_steps`.

A component never creates or mutates a WorkStep.

```text
component step subset != new WorkPlan
component rationale != authority by itself
```

### authorize

An `authorize` component permits exactly its represented WorkStep subset under zero or more non-semantic Authorization Conditions.

```text
authorize(A) != authorize(related B)
```

### deny

A `deny` component explicitly denies exactly its represented WorkStep subset under the supplied Governance context.

```text
Denial != semantic invalidity
Denial != missing capability
Denial != global impossibility
```

### constrain

A `constrain` component must contain at least one directive. It does not authorize the constrained successor semantics.

```text
Governance Constraint != Authorization
Governance Constraint != in-place WorkPlan rewrite
```

### require_review

A `require_review` component must contain at least one directive identifying the additional external review requirement.

```text
require_review != Authorization
require_review != eventual approval
```

## 6. Partial decisions and absence of authority

A `GovernanceDecision.v1` does **not** have to cover every WorkStep in the WorkProposal.

This is deliberate:

```text
unmentioned step != denied step
unmentioned step != authorized step
```

A step omitted from all components simply has no authority result in that decision.

Downstream authority-requiring execution remains fail-closed.

## 7. No overlapping decision components in v1

One WorkStep may appear in at most one component of a single `GovernanceDecision.v1`.

This conservative rule prevents contradictory or silently composed authority roles.

```text
authorize(step A) + deny(step A) -> invalid v1 decision
authorize(step A) + require_review(step A) -> invalid v1 decision
```

M0.6 allows work to receive different decisions over explicitly distinct portions. In v1 those portions must already be represented as distinct WorkSteps.

If a single WorkStep mixes authority-separable effects such as read and mutation, Governance does not split the WorkStep internally. IRR must first represent the semantics with a suitable explicit work boundary.

Exact multi-party/quorum authority composition is deferred.

## 8. GovernanceDecision

`GovernanceDecision` embeds the **exact immutable WorkProposal** plus its attributed components.

Therefore authority decisions bind to the reviewed proposal semantics, not to a lossy natural-language summary.

```text
decision over WorkProposal identity A
    !=
decision over materially changed WorkProposal identity B
```

Historical `WorkPlan` and `WorkProposal` records are never edited by a Governance result.

## 9. Authorization

`Authorization` is a separate immutable authority record:

```text
authorization_ref
exact GovernanceDecision
authorize component_ref
description
```

Construction fails closed unless `component_ref` identifies an `authorize` component of the exact embedded decision.

Derived properties expose:

```text
authorized_step_refs
conditions
```

No other component kind may materialize `Authorization`.

```text
Denial -> not Authorization
Constraint -> not Authorization
RequireReview -> not Authorization
```

Materializing this typed record does not make IRR the authority source. The authority source remains the external Governance boundary embedded in the exact decision provenance.

```text
Authorization materialization != IRR-created permission
```

## 10. Conditions do not widen authority

An Authorization covers only the step subset stated by its authorize component and only under its explicit conditions.

```text
authorization for one step != authorization for dependency
authorization for one recipient != another recipient
read authorization != mutation authorization
provider A authorization != provider B when provider identity is material
```

Work dependencies never create transitive authority.

## 11. No automatic authorization from text or origin

Nothing in M1.6c2 changes:

```text
human-originated intent != Authorization
"yes" != Authorization by itself
principal != permission
worker judgment != Authorization
provider recommendation != Authorization
```

External Governance must produce the explicit attributable decision.

## 12. Binding and capability remain separate

M1.6c2 does not alter M0.4/M0.5:

```text
Binding success != Authorization expansion
Capability Match != Authorization
Authorization != Capability existence
Authorization != Capability Availability
```

A later concrete binding must still fall within authority coverage.

## 13. No execution semantics

Neither `GovernanceDecision` nor `Authorization` means that work was handed off, attempted, performed, or completed.

```text
Authorization != Handoff
Authorization != Attempt
Authorization != Effect
Authorization != Outcome
Authorization != completion
```

Those lifecycle surfaces remain M1.7.

## 14. Canonical behavior

All new records:

- are immutable;
- use exact-key deserialization;
- reject Unicode surrogate code points in text;
- canonicalize set-like tuples by stable identifiers;
- reject duplicate stable refs;
- are closed against subclassing through the package public surface.

Presentation order never becomes authority precedence.

## 15. Explicit deferrals

M1.6c2 intentionally does **not** freeze:

- policy algorithms;
- consent UX;
- identity authentication or cryptographic signatures;
- reusable standing grants;
- leases / TTL parsing;
- revocation state;
- quorum or multi-party composition;
- overlapping authority axes on one WorkStep;
- automatic constraint-to-successor-plan generation;
- Capability Availability;
- executable CapabilityHandoff;
- Executor verification;
- Attempt / Outcome / Continuation;
- retries, fallback, compensation;
- persistence.

These remain later contracts.

## 16. Acceptance criteria

M1.6c2 is acceptable only if tests prove at least:

- only an explicit authorize component can materialize `Authorization`;
- deny/constrain/require-review cannot masquerade as authority;
- constrain and require-review require explicit directives;
- deny cannot carry hidden condition directives in v1;
- component steps are bounded to the exact WorkProposal;
- one WorkStep cannot appear in multiple components of the same v1 decision;
- proposal and decision occurrences remain distinct;
- authority-context identity and exact proposal identity affect decision identity;
- round-trip preserves canonical identity;
- full Python 3.11–3.14 CI passes;
- representative canonical identities are frozen before merge.
