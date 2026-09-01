# M1.7b2 — Successor Resolution Lineage IR

Status: **candidate normative M1.7b2 contract**.

M1.7b1 froze exact downstream/blocking material re-entry as `ContinuationInput` without deciding retry, fallback, authority, parent completion, or successor work.

M1.7b2 freezes the next boundary only: how one exact predecessor `ResolvedIntent`, one or more exact continuation inputs descended from it, and one exact successor Resolution Output are related canonically.

It does **not** create successor work and does **not** implement recovery policy.

```text
exact predecessor ResolvedIntent
             +
one or more ContinuationInput
             +
exact successor ResolutionOutput
             |
             v
 SuccessorResolutionLineage
```

Core invariants:

```text
SuccessorResolutionLineage != Retry
SuccessorResolutionLineage != fallback
SuccessorResolutionLineage != WorkPlan
SuccessorResolutionLineage != WorkPlan mutation
SuccessorResolutionLineage != Authorization
SuccessorResolutionLineage != Evidence
SuccessorResolutionLineage != parent completion
successor ResolutionOutput != successor WorkPlan
lineage association != causal proof
predecessor admission occurrence != source production occurrence
predecessor admission occurrence != Host re-entry occurrence
source production occurrence != Host re-entry occurrence
successor admission occurrence != predecessor/source/re-entry occurrence
one source re-submitted many times != many independent lineage inputs
```

## 1. Why this boundary exists

After M1.7b1, IRR can receive exact continuation material but there is no frozen representation of the next semantic state.

Jumping directly from an Outcome or blocking issue to a new WorkPlan would bypass the Resolution boundary and allow downstream facts to mutate executable semantics without first becoming an IRR-owned semantic decision.

M1.7b2 therefore requires the successor to remain one of the already-frozen Resolution Outputs:

```text
ResolvedIntent
ClarificationNeed
InformationNeed
```

Only a successor `ResolvedIntent` may later enter the ordinary frozen planning pipeline.

```text
ContinuationInput
      |
      v
successor ResolutionOutput
      |
      +--> ClarificationNeed  -> semantic pause
      +--> InformationNeed    -> bounded information requirement
      `--> ResolvedIntent     -> ordinary Intent-to-Work pipeline may run later
```

B2 itself does not perform later planning.

## 2. Public IR surface

M1.7b2 adds only:

```text
SuccessorResolutionKind
SuccessorResolutionLineage
```

`SuccessorResolutionKind` is the closed wire discriminator:

```text
resolved_intent
clarification_need
information_need
```

The discriminator must exactly match the concrete successor IR type. It is not caller-selected policy.

`SuccessorResolutionLineage` has exactly:

```text
schema = irr.successor_resolution_lineage.v1
predecessor: ResolvedIntent
continuation_inputs: tuple[ContinuationInput, ...]
successor_kind: SuccessorResolutionKind
successor: ResolvedIntent | ClarificationNeed | InformationNeed
```

There is deliberately no independent:

```text
lineage_ref
lineage_event_ref
description
reason
retry
fallback
parent_complete
authorized
successor_work_plan
```

Its identity is therefore a pure function of the exact predecessor, normalized exact continuation inputs, and exact successor. Repeated materialization of the same relation is identity-idempotent.

## 3. Exact predecessor lineage

Every `ContinuationInput` already exposes a mechanically derived `resolved_intent_identity` through its exact source lineage.

M1.7b2 requires for every input:

```text
continuation_input.resolved_intent_identity == predecessor.identity
```

This rejects material from sibling semantic branches even when both branches share the same original user request.

```text
same IntentRequest != same ResolvedIntent branch
```

A continuation from another predecessor cannot be relabeled as material for this lineage.

## 4. Original IntentRequest continuity

The successor must preserve the predecessor's exact `IntentRequest` identity:

```text
successor.intent_request_identity == predecessor.intent_request_identity
```

B2 is continuation of one intent lineage, not a mechanism for silently attaching material to another request.

The successor `context_envelope_identity` is not required to equal the predecessor context identity. A later resolution may legitimately use a newly admitted Context Envelope or retain the existing one.

B2 does not create or mutate that Context Envelope:

```text
ContinuationInput != ContextEnvelope mutation
lineage relation != context admission
```

## 5. Four occurrence roles remain distinct

M1.7b2 preserves four semantic occurrence roles across one successor lineage:

```text
1. predecessor Resolution admission
2. continuation source production
3. Host re-entry submission
4. successor Resolution admission
```

These are different semantic layers even when all four are represented by `StableRef` values.

For each continuation input, its source-production occurrence is mechanically derived from the exact source record. Examples include the exact `CapabilityOutcome.outcome_event_ref`, `WorkerResult.result_event_ref`, `BindingIssue.binding_event_ref`, capability-match evaluation event, or Governance decision event selected by the continuation material.

The predecessor admission occurrence must differ from every source-production occurrence and every Host re-entry occurrence:

```text
predecessor.admission_event_ref != continuation_input.source_event_ref
predecessor.admission_event_ref != continuation_input.attribution.reentry_event_ref
```

No source-production occurrence may be reused as a Host re-entry occurrence anywhere in the same lineage:

```text
source_event_refs ∩ reentry_event_refs = empty
```

The successor admission occurrence must differ from the predecessor admission occurrence, every source-production occurrence, and every Host re-entry occurrence:

```text
successor.admission_event_ref != predecessor.admission_event_ref
successor.admission_event_ref != continuation_input.source_event_ref
successor.admission_event_ref != continuation_input.attribution.reentry_event_ref
```

Therefore a single occurrence cannot impersonate another semantic role:

```text
predecessor Resolution admitted
        !=
source produced
        !=
Host submitted source back to IRR
        !=
IRR admitted successor semantic state
```

The prohibition is **cross-category**. M1.7b2 does not require all source-production events to be mutually unique with other source-production events, nor all re-entry events to be mutually unique with other re-entry events. One real downstream occurrence may legitimately produce multiple exact records, and one real Host submission occurrence may legitimately submit multiple exact continuation records. What is forbidden is reuse of one occurrence across different semantic roles.

`ContinuationInput.source_event_ref` is a mechanically derived, non-serialized projection. It does not alter the frozen M1.7b1 wire identity.

## 6. Duplicate-source amplification is forbidden

M1.7b1 deliberately allows the same exact source to be submitted more than once at different re-entry occurrences. Delivery history is not new source semantics.

```text
exact source S
  +--> re-entry A
  `--> re-entry B
```

A and B are distinct `ContinuationInput` identities, but both expose the same `source_identity`.

M1.7b2 rejects a lineage containing both A and B:

```text
same source_identity twice != two independent semantic grounds
```

Otherwise one Outcome, WorkerResult, BindingIssue, capability-match issue, or Governance component could be amplified by repeated submission.

`continuation_inputs` therefore requires:

- a tuple;
- at least one exact `ContinuationInput`;
- no duplicate `ContinuationInput.identity`;
- no duplicate `ContinuationInput.source_identity`.

Inputs are canonically ordered by exact source identity, not caller presentation order.

## 7. Successor kind is mechanical

The serialized discriminator is checked against the exact nested type:

```text
ResolvedIntent    -> resolved_intent
ClarificationNeed -> clarification_need
InformationNeed   -> information_need
```

A caller cannot label a `ResolvedIntent` as `clarification_need` or introduce kinds such as `retry`, `fallback`, or `complete`.

```text
wire discriminator != policy selector
```

## 8. ResolvedIntent successor

A successor `ResolvedIntent` means only that IRR admitted a new non-blocking semantic state for the same original IntentRequest after exact continuation material re-entered.

It does not mean:

```text
retry the previous CapabilityAttempt
reuse previous Authorization
reuse previous CapabilityMatch
reuse previous BoundValue
reuse previous WorkPlan
complete parent work
```

If the successor later requires work, it enters the ordinary frozen pipeline from `ResolvedIntent` onward. Previous execution authority does not flow through B2 automatically.

## 9. ClarificationNeed successor

A successor `ClarificationNeed` preserves an IRR-owned semantic pause. B2 can relate exact continuation material to that pause, but it does not answer the question or choose an alternative.

```text
ContinuationInput + ClarificationNeed != automatic user answer
```

## 10. InformationNeed successor

A successor `InformationNeed` preserves a bounded requirement for additional material. B2 does not retrieve the material and grants no observation, filesystem, network, tool, or disclosure authority.

```text
InformationNeed != retrieval permission
SuccessorResolutionLineage != observation authority
```

## 11. Lineage association is not Evidence

`SuccessorResolutionLineage` records an exact semantic lineage association: IRR admitted this exact successor Resolution Output as the next semantic state of this exact predecessor with these exact continuation inputs on the re-entry path.

It does not convert the source into `EvidenceRecord`, prove the source true or complete, or prove a candidate provider causally inspected every source field.

```text
lineage association != evidence support
lineage association != truth
lineage association != completeness
lineage association != causal model trace
```

Evidence semantics remain on the frozen evidence/provenance surfaces.

## 12. Governance remains separate

Governance constrain/review material reaches B2 only through the exact B1 `GovernanceContinuationMaterial` wrapped in `ContinuationInput`.

B2 does not authorize work, satisfy review, carry old Authorization forward, or transform a Governance directive into executable permission.

```text
Governance continuation lineage != Authorization continuity
```

A later successor WorkProposal must pass through Governance normally when authority is required.

## 13. Outcome, Worker, Binding, and capability-match material remain historical facts

B2 does not infer recovery policy from Outcome lifecycle/completion/effect certainty, WorkerResult contents, BindingIssue kind, or CapabilityMatchIssue kind.

Representable examples include:

```text
interrupted Outcome -> successor ResolvedIntent
unknown effect -> successor InformationNeed
ambiguous material -> successor ClarificationNeed
```

These are relations, not automatic mappings. There is deliberately no `evaluate_successor`, `retry_if_unknown`, fallback selector, or parent completion evaluator in B2.

## 14. Canonical identity

`SuccessorResolutionLineage.identity` uses the normal M1 canonical JSON SHA-256 domain.

Canonical primitive:

```text
{
  "continuation_inputs": [... canonical source-identity order ...],
  "predecessor": <exact ResolvedIntent>,
  "schema": "irr.successor_resolution_lineage.v1",
  "successor": <exact ResolutionOutput>,
  "successor_kind": <closed discriminator>
}
```

Consequences:

```text
same exact relation -> same identity
input presentation order -> no identity change
different re-entry occurrence -> different relation identity
different successor admission -> different relation identity
different successor semantics -> different relation identity
```

There is no caller-selected relation ID.

## 15. Serialization closure

Deserialization is schema-first and exact-keyed. Unknown fields fail closed, including attempts to smuggle in:

```text
retry
fallback
authorized
successor_work_plan
parent_complete
lineage_event_ref
description
```

Unknown or mismatched `successor_kind` also fails closed.

## 16. Explicit non-goals

M1.7b2 does not implement:

- resolver/provider invocation protocol;
- automatic candidate generation;
- ContextEnvelope construction or mutation;
- retry or fallback rules;
- successor WorkPlan construction;
- WorkPlan mutation;
- capability selection;
- Governance evaluation;
- Authorization reuse;
- tool execution;
- observation/retrieval;
- Worker dispatch;
- parent completion;
- scheduling or loop orchestration;
- persistence or event-log storage.

## 17. Acceptance gate

M1.7b2 is merge-ready only when:

- all three frozen Resolution Output kinds round-trip as successors;
- continuation inputs are tied to the exact predecessor `ResolvedIntent.identity`;
- original `IntentRequest` identity is preserved;
- predecessor admission differs from every source-production and Host re-entry occurrence;
- source-production occurrences and Host re-entry occurrences do not alias across categories;
- successor admission differs from predecessor admission, every source-production occurrence, and every Host re-entry occurrence;
- repeated re-entry of one `source_identity` cannot amplify lineage material;
- continuation presentation order cannot affect identity;
- hidden retry/fallback/authority/successor-work fields fail closed;
- the public IR type is closed against subclass extension;
- Python 3.11–3.14 CI is green;
- adversarial first-party review finds no semantic authority leak;
- representative canonical identities are independently calculated and frozen before merge;
- fresh current-head Codex review is clean.
