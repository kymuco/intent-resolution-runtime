# M3.0.5 — Deterministic Capability Match Evaluation

Status: **proposed prerequisite for HDE M33.2**.

Exact base:

```text
intent-resolution-runtime/main@0abb4f35d8b4424a2256bf21bbe279a1720430f9
```

M2.3 already accepts canonical `CapabilityMatchEvaluation` records and derives:

```text
one compatible match  -> CapabilityMatch
zero compatible       -> NO_COMPATIBLE_CAPABILITY
multiple compatible   -> MULTIPLE_COMPATIBLE_MATCHES
```

But before M3.0.5 IRR had no mechanical function that constructed an exhaustive
`CapabilityMatchEvaluation` from one admitted `CapabilityRequirement` and one exact
externally supplied `CapabilityCatalogSnapshot`. An embedding Host would therefore
have needed to construct match semantics itself.

M3.0.5 closes that gap without discovering capabilities, choosing among multiple
compatible capabilities, proposing work, invoking Governance, authorizing effects, or
executing anything.

## Boundary

```text
exact CapabilityRequirement
        +
exact externally supplied CapabilityCatalogSnapshot
        +
explicit evaluation event ref
        ↓
build_capability_match_evaluation(...)
        ↓
CapabilityMatchEvaluation
        ↓
STOP
```

The evaluator examines every exact descriptor in the supplied snapshot and classifies
it as either:

```text
one unique exact structural CapabilityMatch
```

or:

```text
CapabilityIncompatibleDescriptorAssessment
```

The resulting `CapabilityMatchEvaluation` therefore covers the complete exact bounded
snapshot.

## Externally supplied catalog remains externally supplied

M3.0.5 does not discover or widen capability availability.

The caller must supply an already-existing exact `CapabilityCatalogSnapshot`, including
its own supplier and snapshot-event attribution.

```text
catalog construction != matching
catalog supplier != matcher
catalog membership != compatibility
catalog omission != global impossibility
catalog membership != Authorization
```

The evaluator never scans PATH, plugins, Runplane, browsers, services, accounts, or the
machine.

## Exact-structural-v1 semantics

A descriptor can produce a `CapabilityMatch` only when all currently representable v1
relations can be established mechanically and uniquely.

The checks are:

1. exact WorkStep operation;
2. lexically exact completion contract;
3. every explicit execution-boundary requirement is present;
4. requested scopes and descriptor scope requirements form one unique exact
   semantic-type bijection;
5. WorkStep inputs and descriptor input contracts form one unique exact semantic-type
   bijection;
6. every WorkStep output maps uniquely to a distinct descriptor output contract;
7. every requested effect maps uniquely by semantic type and mapped scope surface;
8. every unavoidable descriptor effect is covered.

The existing canonical `CapabilityMatch` constructor remains the final invariant check
for every emitted match.

## Ambiguity fails closed

Some v1 records intentionally do not carry enough semantics to distinguish two
otherwise valid structural pairings. For example, two requested scopes may have the
same semantic type while two descriptor scope requirements also have that type.

M3.0.5 does not choose by tuple order, ref ordering, catalog order, or first match.

The bounded assignment search stops as soon as it proves:

```text
0 mappings
exactly 1 mapping
more than 1 mapping
```

More than one mapping produces:

```text
CapabilityMismatchKind.INSUFFICIENT_SEMANTICS
```

for that descriptor.

```text
ambiguity != hidden selection authority
canonical ordering != precedence
presentation order != semantic authority
```

This deliberately prefers an explicit unresolved semantic surface over accidental
pairing.

## Descriptor mismatch semantics

The evaluator uses the existing mismatch vocabulary:

```text
OPERATION_MISMATCH
SCOPE_MISMATCH
INPUT_MISMATCH
OUTPUT_MISMATCH
UNAVOIDABLE_EFFECT_MISMATCH
COMPLETION_MISMATCH
EXECUTION_BOUNDARY_MISMATCH
INSUFFICIENT_SEMANTICS
```

A mismatch is evidence only about the exact descriptor under the exact supplied
snapshot.

```text
NO_COMPATIBLE_CAPABILITY
!= capability does not exist elsewhere
!= permission to widen the catalog
!= permission to discover another provider
!= fallback authority
```

## Multiple compatible descriptors remain unresolved

M3.0.5 evaluates every descriptor independently. If two different descriptors each have
one unique exact structural match, both exact `CapabilityMatch` records remain inside
the evaluation.

The already-frozen classifier then returns:

```text
MULTIPLE_COMPATIBLE_MATCHES
```

No ranking is introduced.

```text
catalog order != winner
supplier attribution != winner
capability ref ordering != winner
first match != winner
```

## Attribution

The caller supplies only the explicit evaluation event ref.

IRR fixes evaluator identity to:

```text
irr.evaluator / capability-match-evaluation-v1
```

and matcher identity to:

```text
irr.matcher / exact-structural-v1
```

Per-descriptor match-event refs are deterministic digests of the explicit evaluation
event plus exact descriptor identity under the fixed `irr.capability_match` namespace.

There is no ambient UUID, wall-clock tie-break, or caller-selected matcher identity.

```text
attribution != authority
match attribution != Authorization
```

## Public surface

```python
build_capability_match_evaluation(
    requirement,
    catalog_snapshot,
    *,
    evaluation_event_ref,
) -> CapabilityMatchEvaluation

mechanical_capability_matcher_ref()
mechanical_capability_evaluator_ref()
```

## Frozen authority boundaries

```text
CapabilityRequirement != CapabilityMatch
CapabilityCatalogSnapshot != availability outside its stated surface
catalog membership != compatibility
catalog membership != authorization
CapabilityMatch != WorkProposal
CapabilityMatch != GovernanceDecision
CapabilityMatch != Authorization
CapabilityMatchEvaluation != capability selection authority
CapabilityMatchIssue != fallback authority
NO_COMPATIBLE_CAPABILITY != global impossibility
MULTIPLE_COMPATIBLE_MATCHES != permission to choose
INSUFFICIENT_SEMANTICS != permission to guess
mechanical evaluation != execution
```

## Non-goals

M3.0.5 adds no:

- capability discovery;
- catalog widening;
- provider or model call;
- semantic similarity matching;
- fuzzy operation matching;
- ranking or preference among compatible capabilities;
- WorkProposal construction;
- Governance policy;
- Authorization;
- capability invocation;
- Runplane/executor integration;
- retry/fallback/recovery;
- Worker/delegation semantics.

## HDE consequence

HDE M33.2 can now remain a true integration boundary:

```text
M33.1 exact admitted CapabilityRequirement
        +
explicit exact attributable CapabilityCatalogSnapshot
        ↓
IRR M3.0.5 mechanical evaluation
        ↓
CapabilityMatchEvaluation
        ↓
STOP
```

HDE therefore does not need to become the capability semantic matcher.
