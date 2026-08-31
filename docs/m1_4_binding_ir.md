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

The first is part of admitted selection semantics. The second is material concrete scope that becomes known only when a value is bound.

```text
concrete value scope becoming known != Authorization over that scope
```

M1.4 does not infer resource containment or permission from path-like strings. A later Capability/Governance contract may validate the concrete scope according to the relevant domain.

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

## 4. BindingInput and source provenance

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

M1.4 preserves two distinct source dimensions:

```text
SourceAttribution.source_ref
source_identity
```

`source_ref` is the attributed source actor/component for the occurrence. `source_identity` is an exact admitted source-record/source-contract identity associated with the supplied material. A BindingRule may restrict both dimensions independently.

```text
source attribution != source-record identity
source attribution != verification
source identity != Capability identity
```

M1.4 does not cryptographically prove that a caller-supplied `source_identity` belongs to a caller-supplied `source_ref`; it preserves and checks the admitted association dimensions. Authentication/source-registry verification remains outside this slice.

`selection_scope` must match the rule's admitted selection domain. `value_scope` describes the concrete candidate and remains independently attributable.

## 5. Binding attributes and exact RFC3339 instant semantics

BindingInput may carry a closed tuple of named attributes. M1.4 v1 supports:

```text
text
rfc3339_timestamp
```

For `rfc3339_timestamp`, comparison preserves **all supplied fractional-second digits**. It does not round/truncate to Python microseconds.

Offset-equivalent lexical representations compare as the same instant:

```text
2026-08-30T12:00:00+06:00
==
2026-08-30T06:00:00Z
```

M1.4 v1 fail-closes on two RFC3339 forms it cannot safely use as a known absolute instant:

- `-00:00`, whose RFC3339 meaning is unknown local offset;
- leap-second notation (`:60`), whose exact UTC timeline handling is deliberately deferred.

This is an explicit v1 comparator boundary, not permission to reinterpret those forms.

```text
unknown offset != known instant
unsupported leap-second comparison != lexical fallback
```

No ambient timezone or wall clock is consulted.

## 6. BindingConstraint

M1.4 v1 intentionally supports a minimal bounded predicate language:

```text
attribute equals expected value
```

Each constraint freezes the attribute name, operator, expected semantic kind, and expected value.

For text attributes, equality is lexical Unicode-scalar string equality. For RFC3339 timestamp attributes, equality is equality of the exact parsed instant, so equivalent offsets are equal.

No shell, regex execution, Python expression, query language, model judgment, script fragment, or arbitrary comparator exists in the v1 rule schema.

```text
BindingRule != hidden program
```

A required constraint attribute that is absent is `missing_required_data`. A present attribute with the wrong admitted semantic kind is `incompatible_input`; it is not silently treated as an ordinary constraint mismatch.

## 7. BindingSelectionPolicy

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

RFC3339 extrema compare exact instants with arbitrary fractional precision. Equal instants produce `BindingIssue.tie`; no filename/order/provider/model tie-break is invented.

`any_interchangeable` is valid only when admitted semantics already declare every compatible candidate materially interchangeable. M1.4 v1 then makes the mechanical policy explicit as:

```text
canonical_identity_min
```

This ordering is not semantic preference or presentation precedence. It is permitted only after semantic interchangeability is already fixed.

## 8. BindingRule

```text
BindingRule
├─ schema = irr.binding_rule.v1
├─ resolved_intent_identity
├─ rule_ref
├─ symbolic_reference
├─ allowed_input_roles[]
├─ allowed_source_refs[]
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

The rule requires at least one admitted source ref and at least one admitted source identity. Those checks remain attribution/lineage constraints, not authentication.

The rule may require exact Temporal Basis, Completeness, or Evidence identities. Binding succeeds only when supplied candidates carry that required material provenance.

```text
binding does not amplify evidence
binding does not imply completeness
binding does not imply freshness
```

The rule does not constrain concrete `value_scope` unless a future version adds an explicit bounded value-scope predicate. M1.4 does not infer one from primitive/path shape.

## 9. Mechanical evaluation phases

Public function:

```text
evaluate_binding(rule, binding_inputs, attribution)
    -> BoundValue | BindingIssue
```

Evaluation is performed over the **complete normalized input set**, not candidate-by-candidate with early return based on identity or presentation order.

The phases are explicit:

```text
1. lineage / role / source-ref / source-identity / type / selection-scope compatibility
2. required temporal / completeness / evidence provenance
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

Phase order itself is an explicit v1 mechanical classification rule. For example, an input set containing structural incompatibility and missing completeness is `incompatible_input` regardless of presentation order.

Constraint/selector semantic-kind mismatches are `incompatible_input`; missing required data is `missing_required_data`.

A constraint value mismatch may exclude a complete candidate. Missing/wrong-kind material cannot be silently treated as an excluded candidate because doing so could hide a candidate that changes the bounded result.

No evaluator path retrieves missing data, changes the rule, substitutes another selection scope, invents another source, falls back to shell/browser/model judgment, or treats failure as permission to try another semantic operation.

## 10. BindingAttribution

```text
BindingAttribution
├─ evaluator_ref
└─ binding_event_ref
```

This records which mechanical evaluator occurrence produced the binding result.

It is not authentication, trust, Governance authority, Authorization, or Effect evidence.

## 11. BoundValue

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

## 12. BindingIssue

```text
BindingIssue
├─ schema = irr.binding_issue.v1
├─ binding_attribution
├─ rule
├─ binding_inputs[]
├─ kind
└─ selection_scope
```

M1.4 v1 machine-semantic issue kinds:

```text
zero_matches
multiple_matches
tie
missing_required_data
incompatible_input
```

A BindingIssue constructor re-evaluates the rule/input set and requires `kind` to match the mechanical result.

Human diagnostic prose is deliberately **not part of BindingIssue.v1**. This avoids freezing one implementation's English wording into canonical cross-language wire semantics. UIs/loggers may render explanations from the machine kind and embedded provenance without changing the IR record.

```text
human diagnostic wording != binding semantic identity
```

A BindingIssue is not generic IRR Continuation, InformationNeed, authorization, or fallback permission.

## 13. Material new information

M1.4 does not represent material new semantic decisions as ordinary BindingInput merely to keep evaluation moving.

If returned data reveals a new disclosure surface, different executable target, unsupported tie policy, contradicted assumption, or another material choice, the fixed binding path stops.

```text
material new information != mechanical BindingInput
```

M1.7 owns generic Continuation re-entry records.

## 14. Ordering and normalization

Set-like tuples are canonicalized independently of caller presentation order:

- BindingInput attributes by attribute name;
- provenance identities by RecordIdentity;
- BindingRule roles by enum value;
- BindingRule source refs by `(namespace, value)`;
- BindingRule source identities by RecordIdentity;
- BindingRule constraints by complete declarative content;
- evaluated BindingInput sets by BindingInput identity.

Canonical ordering is used for identity/representation only. It does not choose which validation defect becomes semantically visible; explicit whole-set phase evaluation owns that classification.

For `any_interchangeable`, canonical identity order appears explicitly in SelectionPolicy and is permitted only because the candidates were already admitted as interchangeable.

## 15. Closed Python schema

All public M1.4 record classes are frozen, slotted, exact-type validated where retained by another record, and sealed against public subclassing through the package surface.

```text
complete admitted constructor state == complete identity-covered state
```

Unknown wire fields fail closed.

## 16. Canonical identity

M1.4 does not extend the canonical value domain. All records use only object, array, and Unicode-scalar string values, preserving earlier M1 canonical bytes.

Identity remains:

```text
sha256(canonical_json_bytes(record))
```

## 17. Authority boundary

M1.4 contains no authority field.

```text
symbolic reference != authority
Binding Input != authority
Binding Input availability != disclosure authority
source attribution != authorization
Binding Rule != Authorization
Binding evaluation != Authorization
Bound Value != permission
concrete value_scope != authorization over that scope
BindingIssue != permission to fallback
```

M1.6 owns Capability/Governance references.

## 18. Explicit deferrals

M1.4 does not freeze WorkPlan/WorkStep, DelegatedWork, concrete Capability I/O schemas, Observation/Outcome schemas, generic Continuation, Governance/Authorization, executor scheduling, external retrieval, disclosure policy, source authentication, source-registry verification, world-drift revalidation, rebinding lifecycle, fallback/retry, persistence, canonical numbers/booleans/null, leap-second timeline semantics, or arbitrary executable comparators.

## 19. Acceptance

M1.4 is correct when executable tests prove at least:

```text
SymbolicReference is immutable and round-trippable
BindingInput preserves explicit attribution and source role
source_ref and source_identity are separately admitted dimensions
selection_scope and concrete value_scope remain distinct
BindingRule source / role / type / selection-scope boundaries fail closed
selector comparison kind is admitted before runtime input
RFC3339 comparison preserves arbitrary fractional precision
offset-equivalent RFC3339 values compare as one instant
unknown RFC3339 offset and leap-second forms fail closed in v1
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
BindingIssue carries stable machine semantics without frozen human prose
unknown wire fields are rejected
public M1.4 records are closed against subclass state
no authority fields are introduced
```
