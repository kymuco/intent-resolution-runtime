# M1.4 — Binding / Symbolic Reference IR

Status: **implementation slice**.

M1.4 encodes the frozen M0.4 Late Binding & Observation boundary as immutable, inspectable Python contracts.

It answers one implementation question:

> How can IRR carry a future concrete value through bounded semantics without turning an Executor, provider, or binding evaluator into a hidden intent resolver?

The answer remains:

```text
late binding != unadmitted semantic discretion
```

M1.4 introduces exact v1 records for symbolic references, attributable binding inputs, bounded mechanical rules, explicit selection policy, successful bound values, and mechanically checkable unresolved binding issues.

It deliberately does **not** introduce WorkPlan/WorkStep, generic IRR Continuation, Observation records, Capability, Governance, Authorization, execution transport, retry, or persistence. Those remain later slices.

## 1. Architecture

```text
ResolvedIntent identity
        |
        v
SymbolicReference
        |
        v
BindingRule
        |
        +-----------------------------+
        |                             |
        v                             v
attributable BindingInput[]      material new semantics
        |                             |
        v                             v
mechanical evaluate_binding      NOT BindingInput
        |                        -> later Continuation
   +----+----+
   |         |
   v         v
BoundValue  BindingIssue
```

`evaluate_binding()` is effect-free. It consumes only the supplied immutable rule and supplied attributable inputs.

It does not read files, query services, inspect ambient process/UI state, consult a wall clock, retrieve Context, invoke a model, widen scope, mutate external state, or perform fallback.

## 2. Two scope roles

M1.4 explicitly separates the domain over which a value is selected from the concrete resource/surface represented by an individual candidate.

```text
selection_scope != value_scope
```

Example:

```text
selection_scope = D:\Backups
value_scope     = D:\Backups\backup-b.zip
```

The first is part of the admitted selection semantics. The second is material concrete scope that becomes known only when the value is bound.

This distinction matters to later Capability/Governance contracts:

```text
concrete value scope becoming known
    !=
Authorization over that scope
```

M1.4 therefore never requires a candidate's `value_scope` to equal the enclosing `selection_scope`.

## 3. SymbolicReference

```text
SymbolicReference
├─ schema = irr.symbolic_reference.v1
├─ resolved_intent_identity
├─ slot_ref
├─ semantic_type
├─ selection_scope
└─ description
```

A SymbolicReference denotes a future value whose meaning and selection domain are already fixed but whose concrete value is not yet known.

```text
symbolic reference != observed value
symbolic reference != guessed value
symbolic reference != authority
symbolic reference != general-purpose scripting variable
```

`slot_ref` is an opaque `StableRef`. Its namespace does not confer trust or authority.

## 4. BindingInput

```text
BindingInput
├─ schema = irr.binding_input.v1
├─ resolved_intent_identity
├─ input_ref
├─ attribution
│  ├─ source_ref
│  └─ source_event_ref
├─ role
├─ source_identity
├─ semantic_type
├─ value
├─ selection_scope
├─ value_scope
├─ attributes[]
├─ temporal_basis_refs[]
├─ completeness_refs[]
└─ evidence_refs[]
```

A BindingInput is attributable data supplied specifically for mechanical binding.

`role` is one of:

```text
plan_local_output
context
observation
outcome
other_explicit
```

These are classification labels at the binding boundary, not implementations of later Observation or Outcome schemas.

```text
Binding Input != Observation by default
Binding Input != Context by default
Binding Input != Outcome by default
```

`source_identity` is an exact admitted source-record/source-contract identity. It is lineage, not Capability identity, truth, availability, or authority.

`selection_scope` must match the rule's admitted selection domain. `value_scope` describes the concrete candidate and is retained independently.

## 5. Binding attributes and constraints

BindingInput may carry a closed tuple of named attributes. M1.4 v1 supports:

```text
text
rfc3339_timestamp
```

RFC3339 timestamp attributes require an explicit timezone offset (`Z` or `±HH:MM`). No ambient timezone or wall clock is consulted.

M1.4 v1 intentionally supports a minimal bounded predicate language:

```text
attribute equals expected value
```

Each constraint freezes the attribute name, operator, expected semantic kind, and expected value.

No shell, regex execution, Python expression, query language, model judgment, script fragment, or arbitrary comparator exists in the v1 rule schema.

```text
BindingRule != hidden program
```

A required constraint attribute that is absent is `missing_required_data`. A present attribute with the wrong admitted semantic kind is `incompatible_input`; it is not silently treated as an ordinary constraint mismatch.

## 6. BindingSelectionPolicy

M1.4 v1 has four bounded selection modes:

```text
require_unique
max_attribute
min_attribute
any_interchangeable
```

For `max_attribute` / `min_attribute`, both selector name and selector semantic kind are frozen before BindingInput arrives.

```text
unknown future value != unknown future comparison semantics
```

Equal extremum winners produce `BindingIssue.tie`; no filename/order/provider/model tie-break is invented.

`any_interchangeable` is valid only when admitted semantics already declare every compatible candidate materially interchangeable. M1.4 v1 then makes the mechanical policy explicit as:

```text
canonical_identity_min
```

This ordering is not semantic preference or presentation precedence. It is permitted only after semantic interchangeability is already fixed.

## 7. BindingRule

```text
BindingRule
├─ schema = irr.binding_rule.v1
├─ resolved_intent_identity
├─ rule_ref
├─ symbolic_reference
├─ allowed_input_roles[]
├─ allowed_source_identities[]
├─ input_semantic_type
├─ required_selection_scope
├─ constraints[]
├─ selection_policy
├─ description
├─ required_temporal_basis_refs[]
├─ required_completeness_refs[]
└─ required_evidence_refs[]
```

The input semantic type and required selection scope must exactly match the SymbolicReference.

The rule may require exact Temporal Basis, Completeness, or Evidence identities. Binding succeeds only when supplied candidates carry that required material provenance.

```text
binding does not amplify evidence
binding does not imply completeness
binding does not imply freshness
```

The rule does not constrain concrete `value_scope` unless a future version adds an explicit bounded value-scope predicate. M1.4 does not infer one from path-string shape.

## 8. Mechanical evaluation phases

Public function:

```text
evaluate_binding(rule, binding_inputs, attribution)
    -> BoundValue | BindingIssue
```

Evaluation is performed over the **complete normalized input set**, not candidate-by-candidate with early return based on identity/presentation order.

The phases are explicit:

```text
1. structural / lineage compatibility across the whole input set
2. required temporal / completeness / evidence provenance across the whole input set
3. constraint attribute presence and semantic kinds
4. declarative constraint filtering
5. selector attribute presence and semantic kinds
6. admitted selection policy
```

Thus:

```text
input order != diagnostic precedence
canonical identity order != failure classification
presentation order != binding precedence
```

A set containing an unadmitted role/source/type/selection-scope candidate is classified as `incompatible_input` independently of which input sorts first. Required provenance is checked only after structural compatibility of the complete set is established.

Constraint and selector semantic-kind mismatches are `incompatible_input`; missing required data is `missing_required_data`.

No evaluator path retrieves missing data, changes the rule, substitutes another selection scope, invents another source, falls back to shell/browser/model judgment, or treats failure as permission to try another semantic operation.

## 9. BindingAttribution

```text
BindingAttribution
├─ evaluator_ref
└─ binding_event_ref
```

This records which mechanical evaluator occurrence produced the binding result.

It is not authentication, trust, Governance authority, Authorization, or Effect evidence.

## 10. BoundValue

```text
BoundValue
├─ schema = irr.bound_value.v1
├─ binding_attribution
├─ rule
├─ binding_inputs[]
├─ selected_input_identity
├─ semantic_type
├─ value
├─ selection_scope
└─ value_scope
```

A BoundValue is constructible only when re-running the embedded BindingRule over the embedded full BindingInput set yields exactly the selected input.

The concrete `value`, `semantic_type`, `selection_scope`, and `value_scope` must match that selected input and the admitted symbolic/rule semantics.

The complete candidate set is retained so an extremum or unique-selection decision remains inspectable.

```text
bound value != provenance-free value
bound value != authorization
bound value != timeless fact
```

A concrete `value_scope` may be narrower or otherwise more specific than the selection domain. Later governance may need to review that concrete scope; M1.4 itself grants no authority over it.

## 11. BindingIssue

```text
BindingIssue
├─ schema = irr.binding_issue.v1
├─ binding_attribution
├─ rule
├─ binding_inputs[]
├─ kind
├─ selection_scope
└─ description
```

M1.4 v1 mechanical issue kinds:

```text
zero_matches
multiple_matches
tie
missing_required_data
incompatible_input
```

A BindingIssue constructor re-evaluates the rule/input set and requires **both** kind and description to match the mechanical result. Diagnostic records therefore cannot tell a different story while preserving the same input provenance.

A BindingIssue is not generic IRR Continuation, InformationNeed, authorization, or fallback permission.

## 12. Material new information

M1.4 does not represent material new semantic decisions as ordinary BindingInput merely to keep evaluation moving.

If returned data reveals a new disclosure surface, different executable target, unsupported tie policy, contradicted assumption, or another material choice, the fixed binding path stops.

```text
material new information != mechanical BindingInput
```

M1.7 owns generic Continuation re-entry records.

## 13. Ordering and normalization

Set-like tuples are canonicalized independently of caller presentation order:

- BindingInput attributes by attribute name;
- provenance identities by RecordIdentity;
- BindingRule roles by enum value;
- BindingRule source identities by RecordIdentity;
- BindingRule constraints by complete declarative content;
- evaluated BindingInput sets by BindingInput identity.

Canonical ordering is used for identity/representation only. It does not choose which validation defect becomes semantically visible; phase-based whole-set evaluation owns that classification.

For `any_interchangeable`, canonical identity order appears explicitly in SelectionPolicy and is permitted only because the candidates were already admitted as interchangeable.

## 14. Closed Python schema

All public M1.4 record classes are frozen, slotted, exact-type validated where retained by another record, and sealed against public subclassing through the package surface.

```text
complete admitted constructor state
    ==
complete identity-covered state
```

Unknown wire fields fail closed.

## 15. Canonical identity

M1.4 does not extend the canonical value domain. All records use only object, array, and Unicode-scalar string values, preserving earlier M1 canonical bytes.

Identity remains:

```text
sha256(canonical_json_bytes(record))
```

## 16. Authority boundary

M1.4 contains no authority field.

```text
symbolic reference != authority
Binding Input != authority
Binding Input availability != disclosure authority
Binding Rule != Authorization
Binding evaluation != Authorization
Bound Value != permission
concrete value_scope != authorization over that scope
BindingIssue != permission to fallback
```

M1.6 owns Capability/Governance references.

## 17. Explicit deferrals

M1.4 does not freeze WorkPlan/WorkStep, DelegatedWork, concrete Capability I/O schemas, Observation/Outcome schemas, generic Continuation, Governance/Authorization, executor scheduling, external retrieval, disclosure policy, world-drift revalidation, rebinding lifecycle, fallback/retry, persistence, canonical numbers/booleans/null, or arbitrary executable comparators.

## 18. Acceptance

M1.4 is correct when executable tests prove at least:

```text
SymbolicReference is immutable and round-trippable
BindingInput preserves explicit attribution and source role
selection_scope and concrete value_scope remain distinct
BindingRule source / role / type / selection-scope boundaries fail closed
selector comparison kind is admitted before runtime input
whole-input-set diagnostic classification is presentation-order independent
constraint attribute wrong kind is incompatible, not an ordinary mismatch
newest-by-timestamp selects a unique winner
timestamp-equivalent values produce a tie
tie does not invent a hidden tie-break
zero matches does not guess
missing material completeness/freshness data blocks binding
require_unique rejects multiple matches
any_interchangeable requires an explicit mechanical policy
any_interchangeable is presentation-order independent
BoundValue retains the full material BindingInput set
BoundValue preserves selected concrete value_scope
BoundValue cannot replace selected value or value_scope
BindingIssue kind and description are mechanically reproducible
unknown wire fields are rejected
public M1.4 records are closed against subclass state
no authority fields are introduced
```
