# M3.0.8 — Authorization Applicability Evaluation Prerequisite

## Status

Integration-driven semantic prerequisite for HDE M33.9.

Canonical starting point:

`intent-resolution-runtime/main@66a7b4b73173053e86a2a224670a3236c68a9169`

## Big question

Can IRR represent and mechanically aggregate exact evidence that an already-admitted
Authorization applies to one exact concrete use **without** parsing policy meaning from
free-text Governance directives and without constructing a CapabilityAttempt?

## Why this prerequisite exists

HDE M33.8 closes at admitted Authorization.

The existing `CapabilityAttempt` validates structural linkage to a presented
Authorization, but existing IRR does not define applicability semantics for generic
`GovernanceDirective` values.

A directive currently carries:

```text
directive_ref
semantic_type
scope
statement
```

That is not enough for IRR to infer facts such as:

- whether a `one_use` permission has already been consumed;
- whether an expiry condition is still valid;
- whether current scope still satisfies Governance;
- whether runtime context changed after Authorization admission.

Parsing `semantic_type`, `scope`, or `statement` inside HDE would make Host the hidden
semantic authority.

Therefore M3.0.8 introduces attributable applicability evidence, not a policy parser.

## Predeclared PASS / FAIL / EXIT

### PASS

M3.0.8 passes if IRR can represent:

```text
exact admitted Authorization
+ exact authorized WorkStep
+ exact use-context snapshot identity
+ explicit evaluator occurrence
+ exact assessment for every Governance condition
        ↓
mechanical aggregation
        ↓
APPLICABLE | NOT_APPLICABLE | UNRESOLVED
```

while introducing no CapabilityAttempt, Executor invocation, retry, consumption, or
external effect.

### FAIL

The design fails if it requires any of the following:

- interpreting free-text directive meaning inside IRR;
- treating `semantic_type="one_use"` as automatically satisfied or consumed;
- allowing partial condition coverage;
- treating missing condition evidence as applicable;
- letting Host state silently substitute for an exact use-context identity;
- constructing CapabilityAttempt in order to determine applicability.

### Mandatory exit

Exit immediately once exact applicability evidence is canonical/replayable and the result
can be mechanically derived.

HDE M33.9 must then own the product-specific bridge that obtains exact current-use facts,
and only an `APPLICABLE` result may proceed toward CapabilityAttempt construction.

## New canonical records

### AuthorizationApplicabilityAttribution

Commits the evaluation to:

- exact evaluator identity;
- exact evaluation occurrence;
- exact use-context reference;
- exact use-context content identity.

```text
same Authorization
+ changed current-use context
!= same applicability evaluation
```

### AuthorizationConditionAssessment

One exact assessment for one exact Governance directive:

```text
SATISFIED
UNSATISFIED
UNKNOWN
```

with exact evidence refs and rationale.

The assessment reports evaluator evidence. IRR does not infer the disposition from the
directive text.

### AuthorizationApplicabilityEvaluation

Binds:

- exact Authorization;
- one exact WorkStep covered by that Authorization;
- exact applicability attribution;
- exactly one assessment for every Authorization condition;
- no extra assessments.

For unconditional Authorization, the exact assessment set is empty.

## Mechanical aggregation

`evaluate_authorization_applicability(...)` is deliberately simple:

```text
any UNSATISFIED
→ NOT_APPLICABLE

else any UNKNOWN
→ UNRESOLVED

else
→ APPLICABLE
```

This aggregation is semantic-neutral with respect to directive meaning.

## Frozen invariants

```text
Authorization admission != applicability

directive text != applicability fact

semantic_type != automatic policy implementation

use-context ref alone != exact use-context identity

partial condition assessment != safe applicability

UNKNOWN != SATISFIED

NOT_APPLICABLE != denial of future uses

APPLICABLE != CapabilityAttempt

CapabilityAttempt != Executor invocation

applicability replay != external re-evaluation
```

## Relationship to one_use / expiry / scope

M3.0.8 does not hard-code these policies.

Instead, an evaluator must assess the exact directive against the exact current-use
snapshot.

Examples:

```text
one_use
+ exact consumption history
→ SATISFIED | UNSATISFIED | UNKNOWN

expiry
+ exact trusted current-time evidence
→ SATISFIED | UNSATISFIED | UNKNOWN

scope_at_use
+ exact current scope snapshot
→ SATISFIED | UNSATISFIED | UNKNOWN
```

The policy/evidence source remains explicit and attributable.

## Stop point

M3.0.8 stops before:

- HDE-specific current-use snapshot construction;
- product policy/evaluator implementation;
- one-use consumption;
- CapabilityAttempt construction;
- Executor;
- CapabilityOutcome;
- external effects.

Those begin only after this prerequisite is closed.
