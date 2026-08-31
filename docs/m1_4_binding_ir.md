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

## 2. SymbolicReference

```text
SymbolicReference
├─ schema = irr.symbolic_reference.v1
├─ resolved_intent_identity
├─ slot_ref
├─ semantic_type
├─ scope
└─ description
```

A SymbolicReference is a concrete IR record for a future slot whose **meaning is already fixed** but whose concrete value is not yet known.

It is explicitly bound to one admitted `ResolvedIntent` lineage.

```text
symbolic reference != observed value
symbolic reference != guessed value
symbolic reference != authority
symbolic reference != general-purpose scripting variable
```

`slot_ref` is an opaque `StableRef`. Its namespace does not confer trust or authority.

## 3. BindingInput

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
├─ scope
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

These are **classification labels at the binding boundary**, not implementations of the later Observation or Outcome schemas.

In particular:

```text
BindingInput.role = observation
    !=
M1.4 defines Observation schema

BindingInput.role = outcome
    !=
M1.4 defines Outcome schema
```

The same bytes may later participate in more than one explicit role, but M1.4 does not collapse those roles.

Core distinction:

```text
Binding Input != Observation by default
Binding Input != Context by default
Binding Input != Outcome by default
```

`source_identity` is the exact admitted source-record/source-contract identity that the BindingRule is allowed to consume. It is lineage, not proof of truth, availability, or authority.

`input_ref` identifies the attributable input occurrence. It is not a permission token.

## 4. Binding attributes

BindingInput may carry a closed tuple of named attributes.

M1.4 v1 supports two attribute kinds:

```text
text
rfc3339_timestamp
```

RFC3339 timestamp attributes require an explicit timezone offset (`Z` or `±HH:MM`). No ambient timezone or wall clock is consulted.

```text
timestamp value != "now"
timestamp attribute != freshness proof by itself
```

Material freshness remains represented through the rule's required temporal-basis provenance.

Duplicate attribute names are rejected and attribute order is canonicalized by name.

## 5. BindingConstraint

M1.4 v1 intentionally supports a minimal bounded predicate language:

```text
attribute equals expected value
```

Each constraint freezes:

```text
attribute_name
operator = equals
expected_kind
expected_value
```

No shell, regex execution, Python expression, query language, model judgment, script fragment, or arbitrary comparator exists in the v1 rule schema.

The small language is deliberate:

```text
BindingRule != hidden program
```

Future rule forms require an explicit versioned extension rather than smuggling executable semantics into strings.

## 6. BindingSelectionPolicy

M1.4 v1 has four bounded selection modes:

```text
require_unique
max_attribute
min_attribute
any_interchangeable
```

### require_unique

After explicit compatibility checks and constraints, exactly one candidate must remain.

```text
0 candidates -> BindingIssue.zero_matches
>1 candidates -> BindingIssue.multiple_matches
```

No implicit first-result or presentation-order preference exists.

### max_attribute / min_attribute

The admitted rule freezes both:

```text
selector attribute name
selector attribute semantic kind
```

before BindingInput arrives.

This is important:

```text
unknown future value
    !=
unknown future comparison semantics
```

A candidate cannot decide at runtime that `modification_time` should be compared as arbitrary text when the rule admitted an RFC3339 timestamp comparator.

If the extremum has multiple equal winners:

```text
tie -> BindingIssue.tie
```

There is no hidden filename/order/provider/model tie-break.

### any_interchangeable

This mode is valid only when admitted semantics have already declared every compatible candidate materially interchangeable.

M1.4 v1 makes the mechanical choice policy explicit:

```text
canonical_identity_min
```

The canonical-identity ordering is **not semantic preference or presentation precedence**. It is an inspectable deterministic implementation policy that is permitted only after the rule already states that any compatible candidate is semantically interchangeable.

If different candidates can materially change downstream work, `any_interchangeable` is not an admissible rule.

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
├─ required_scope
├─ constraints[]
├─ selection_policy
├─ description
├─ required_temporal_basis_refs[]
├─ required_completeness_refs[]
└─ required_evidence_refs[]
```

A BindingRule is fully explicit before input values arrive.

The v1 constructor requires at least one allowed input role and at least one exact allowed source identity.

That closes an important substitution boundary:

```text
same primitive shape != semantic substitutability
same path string != same admitted source
```

The input semantic type and required scope must equal the SymbolicReference semantic type and scope.

The rule may also require exact Temporal Basis, Completeness, or Evidence record identities. Binding succeeds only when each supplied candidate carries the required material provenance.

```text
binding does not amplify evidence
binding does not imply completeness
binding does not imply freshness
```

The rule is immutable and content-addressed.

## 8. Mechanical evaluation

Public function:

```text
evaluate_binding(rule, binding_inputs, attribution)
    -> BoundValue | BindingIssue
```

The evaluator performs only the admitted mechanical checks.

For every supplied BindingInput it fail-closes on:

- foreign ResolvedIntent lineage;
- a role outside the rule's allowed roles;
- a source identity outside the rule's admitted sources;
- semantic type mismatch;
- scope mismatch;
- missing material temporal/completeness/evidence provenance;
- missing required constraint data;
- selector kind mismatch.

Constraint mismatch may exclude a candidate. Missing required constraint data does not silently behave like "not matched"; it is an unresolved-data issue.

No evaluator path:

- retrieves missing data;
- changes the rule;
- substitutes another scope;
- invents another source;
- uses result/presentation order;
- falls back to shell/browser/model judgment;
- treats a failure as permission to try another semantic operation.

## 9. BindingAttribution

```text
BindingAttribution
├─ evaluator_ref
└─ binding_event_ref
```

This records which mechanical evaluator occurrence produced the binding result.

It is not:

```text
authentication
trust
Governance authority
Authorization
Effect evidence
```

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
└─ scope
```

A BoundValue is constructible only when re-running the embedded immutable BindingRule over the embedded BindingInput set yields exactly the selected input.

The concrete value, semantic type, and scope must exactly match that selected BindingInput and the SymbolicReference.

This prevents a producer from taking a valid selection lineage and replacing the concrete output with another value.

The full material candidate set is retained so an extremum or unique-selection decision remains inspectable.

```text
bound value != provenance-free value
bound value != authorization
bound value != timeless fact
```

M1.4 does not say that a successfully bound resource still exists at execution time. Drift/revalidation remains a later lifecycle concern.

## 11. BindingIssue

```text
BindingIssue
├─ schema = irr.binding_issue.v1
├─ binding_attribution
├─ rule
├─ binding_inputs[]
├─ kind
├─ scope
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

A BindingIssue cannot lie about these mechanical states: its constructor re-evaluates the rule and supplied inputs and requires the issue kind to match the actual mechanical result.

A BindingIssue is **not** a generic IRR Continuation record and does not itself authorize more retrieval or fallback.

```text
BindingIssue != Continuation
BindingIssue != InformationNeed
BindingIssue != authorization
```

M1.7 will define generic Continuation/Attempt/Outcome records.

## 12. Material new information

M1.4 deliberately does not represent material new information as ordinary BindingInput merely to keep evaluation moving.

If returned data reveals a new material decision — for example a new disclosure surface, a different executable target, an unsupported tie policy, or a contradicted assumption — the fixed binding path stops.

```text
material new information != mechanical BindingInput
```

The later M1.7 Continuation layer owns the generic re-entry record.

This is why `BindingIssueKind` does not contain a generic "material_new_information" escape hatch.

## 13. Ordering and normalization

Set-like tuples are canonicalized independently of caller presentation order:

- BindingInput attributes by attribute name;
- provenance identity references by RecordIdentity;
- BindingRule roles by enum value;
- BindingRule source identities by RecordIdentity;
- BindingRule constraints by their complete declarative content;
- evaluated BindingInput sets by BindingInput identity.

Therefore:

```text
presentation order != binding precedence
input array order != semantic ranking
```

For `any_interchangeable`, canonical identity order is present explicitly in the SelectionPolicy and is valid only because the candidates were already admitted as interchangeable.

## 14. Closed Python schema

All public M1.4 record classes are:

- frozen;
- slotted;
- exact-type validated where retained by another record;
- sealed against public subclassing through the package surface.

This preserves the M1 invariant:

```text
complete admitted constructor state
    ==
complete identity-covered state
```

Unknown wire fields fail closed.

## 15. Canonical identity

M1.4 does not extend the canonical value domain.

All new records use only:

```text
object
array
Unicode-scalar string
```

and therefore preserve M1.1/M1.2/M1.3 canonical bytes byte-for-byte.

Identity remains:

```text
sha256(canonical_json_bytes(record))
```

## 16. Authority boundary

M1.4 contains no authority field.

Mandatory distinctions remain:

```text
symbolic reference != authority
Binding Input != authority
Binding Input availability != disclosure authority
Binding Rule != Authorization
Binding evaluation != Authorization
Bound Value != permission
BindingIssue != permission to fallback
```

M1.6 owns Capability/Governance references.

## 17. Explicit deferrals

M1.4 does not freeze:

- WorkPlan / WorkStep schemas;
- DelegatedWork;
- concrete Capability I/O schemas;
- Observation record schemas;
- Outcome record schemas;
- generic IRR Continuation;
- Governance / Authorization;
- executor scheduling;
- external retrieval;
- disclosure policy;
- world-drift revalidation;
- rebinding lifecycle;
- fallback/retry;
- persistence;
- canonical numbers, booleans, or null;
- arbitrary comparators or executable rule languages.

## 18. Acceptance

M1.4 is correct when executable tests prove at least:

```text
SymbolicReference is immutable and round-trippable
BindingInput preserves explicit attribution and source role
BindingInput ordering does not create precedence
BindingRule source / role / type / scope boundaries fail closed
selector comparison kind is admitted before runtime input
newest-by-timestamp selects a unique winner
timestamp-equivalent values produce a tie
tie does not invent a hidden tie-break
zero matches does not guess
missing material completeness/freshness data blocks binding
require_unique rejects multiple matches
any_interchangeable requires an explicit mechanical policy
any_interchangeable is presentation-order independent
BoundValue retains the full material BindingInput set
BoundValue cannot replace the selected concrete value
BindingIssue cannot falsely claim a mechanical failure
unknown wire fields are rejected
public M1.4 records are closed against subclass state
no authority fields are introduced
```
