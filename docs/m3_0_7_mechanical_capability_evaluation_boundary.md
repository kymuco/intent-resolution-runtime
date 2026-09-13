# M3.0.7 — Mechanical Capability Evaluation Boundary

Status: **proposed final M3.0 capability-pipeline prerequisite before M3.1**.

Exact base:

```text
intent-resolution-runtime/main@e5b05bde3758ac3c9b699d12c6532753e2648c09
```

M3.0.4 made `CapabilityRequirement` semantic construction explicit admission.
M3.0.5 moved descriptor matching into one deterministic IRR-owned exact-structural
engine. M3.0.6 made the exact candidate `CapabilityCatalogSnapshot` domain explicit
admission before matching.

One integration gap remains: M2.3 accepts a structurally valid
`CapabilityMatchEvaluation` as active evaluation history. Because the canonical record
constructors are public, an embedding Host can still manually construct a different
valid-looking exhaustive evaluation and feed it to M2.3 without proving that it is the
M3.0.5 mechanical result.

M3.0.7 closes that gap without introducing a new semantic admitter.

## Boundary

```text
AdmittedCapabilityRequirement
        +
AdmittedCapabilityCatalogSnapshot
        +
explicit evaluation_event_ref
        ↓
derive_mechanical_capability_match_evaluation(...)
        ↓
IRR exact-structural-v1 engine
        ↓
MechanicallyDerivedCapabilityMatchEvaluation
        │
        └── evaluation: CapabilityMatchEvaluation
                ↓
             existing M2.3
```

The wrapper preserves both exact admission records and the exact mechanical evaluation.

## Why this is derivation, not admission

The old experimental capability-evaluation-admission design predated M3.0.5. At that
time a Host/provider could author compatible/incompatible assessment semantics, so an
explicit semantic admission/adjudication boundary was reasonable.

M3.0.5 changed the architecture. Once the exact requirement and exact catalog domain are
fixed, the current v1 evaluation is mechanically determined by the frozen IRR match
engine.

Therefore M3.0.7 deliberately has no:

```text
CandidateCapabilityMatchEvaluation
CapabilityMatchEvaluationAdmitter
provider vote
semantic adjudication
ranking
selection callback
```

Adding an admitter after deterministic derivation would manufacture semantic discretion
where none is required.

```text
mechanical derivation != semantic choice
recomputation != admission vote
```

## Self-verifying derivation record

`MechanicallyDerivedCapabilityMatchEvaluation` is valid only when:

1. `admitted_requirement` is an exact `AdmittedCapabilityRequirement`;
2. `admitted_catalog` is an exact `AdmittedCapabilityCatalogSnapshot`;
3. `evaluation.requirement` equals the exact admitted requirement semantics;
4. `evaluation.catalog_snapshot` equals the exact admitted catalog snapshot;
5. re-running `build_capability_match_evaluation(...)` with the evaluation's explicit
   event ref produces an evaluation exactly equal to the supplied evaluation.

The fifth condition validates the complete current mechanical surface, including:

- fixed evaluator identity;
- fixed matcher identity;
- exact descriptor coverage;
- compatible match mappings;
- incompatible descriptor assessments;
- mismatch reasons;
- deterministic match occurrence refs;
- fixed mechanical descriptions.

A manually created record that is structurally valid but semantically different cannot
cross this boundary.

A manually recreated record that is *exactly equal* to the deterministic result is not a
semantic problem: the boundary proves equivalence of semantics rather than claiming that
a particular Python call physically occurred.

## Admission provenance remains material

The wrapper retains the complete admitted requirement and admitted catalog records, not
only their raw nested semantics.

Therefore replay can distinguish:

```text
same raw requirement semantics
under different exact admission provenance
```

and:

```text
same raw catalog snapshot
under different exact catalog-admission provenance
```

without treating admission provenance as capability selection or permission.

```text
admission provenance != Authorization
admission provenance != availability
```

## Existing M2.3 remains frozen

M3.0.7 does not modify M2.3's canonical orchestration contract and does not make M2
depend on M3.

The safe Host integration path unwraps the exact verified evaluation only after this M3
boundary:

```text
mechanically_derived.evaluation
        ↓
orchestrate_capability_governance(...)
```

Low-level M1/M2 constructors remain public canonical IR surfaces. M3 defines the
integration path a real Host should use; it does not retroactively make M2 import M3.

## Replay

For the same exact:

```text
AdmittedCapabilityRequirement
AdmittedCapabilityCatalogSnapshot
evaluation_event_ref
```

M3.0.7 derives the same canonical wrapper identity and bytes.

Deserialization re-runs the mechanical equality check. Persisted wrapper bytes therefore
cannot silently re-enter with altered match semantics.

```text
replay != re-execution
replay != new semantic admission
restart != capability reselection
```

## Authority boundaries

M3.0.7 preserves:

```text
CapabilityRequirement admission != Capability Match
Catalog Snapshot admission != capability availability
mechanical evaluation != capability selection
CapabilityMatch != WorkProposal
CapabilityMatch != GovernanceDecision
CapabilityMatch != Authorization
Authorization != invocation
mechanical evaluation != execution
```

`MULTIPLE_COMPATIBLE_MATCHES` remains unresolved ambiguity. `NO_COMPATIBLE_CAPABILITY`
remains bounded to the exact admitted catalog domain. `INSUFFICIENT_SEMANTICS` remains a
fail-closed result rather than permission to guess.

## Non-goals

M3.0.7 adds no:

- capability discovery or catalog widening;
- live availability/readiness probing;
- external Cognitive Provider call;
- fuzzy or semantic-similarity matcher;
- capability ranking or preference;
- WorkProposal synthesis;
- Governance policy;
- Authorization;
- Executor invocation;
- Attempt or Outcome;
- retry/fallback/recovery;
- Worker/delegation semantics;
- HDE-specific dependency;
- persistent history repository;
- universal HostRuntime.

## M3 consequence

The host-safe capability path is now:

```text
candidate capability requirement semantics
→ M3.0.4 exact requirement admission
→ AdmittedCapabilityRequirement

candidate capability catalog domain
→ M3.0.6 exact catalog admission
→ AdmittedCapabilityCatalogSnapshot

both exact admitted inputs
→ M3.0.7 mechanical derivation boundary
→ MechanicallyDerivedCapabilityMatchEvaluation
→ existing exact CapabilityMatchEvaluation projection
→ M2.3 CapabilityMatch | CapabilityMatchIssue
→ STOP before WorkProposal / Governance / Authorization / execution
```

This closes the capability-semantic prerequisite chain exposed while preparing real Host
integration.

After M3.0.7, the next IRR milestone should return to the M3.0 charter sequence:

# **M3.1 — Admitted History Repository / Replay Boundary**

unless a failing integration test demonstrates another concrete prerequisite rather than
a speculative one.
