# M2.1 — Initial Resolution Orchestrator

Status: **implementation slice**.

M2.1 is the first runtime implementation built on the M2.0 Runtime Orchestration Charter. It turns the frozen M1.3 resolution records into a deliberately narrow initial-resolution orchestration path without introducing a mutable canonical session, provider transport, ambient retrieval, Governance, WorkPlan construction, or effect execution.

The central M2.1 correction is the same boundary frozen in M0.7/M1.3:

```text
provider proposes != IRR admits
```

A `CandidateResolution` is never promoted to `ResolvedIntent`, `ClarificationNeed`, or `InformationNeed` merely because it is unique, fluent, structurally valid, or supported by several providers.

## 1. Implemented boundary

```text
exact IntentRequest
+ exact ContextEnvelope
+ zero or more explicit CandidateResolution records
+ zero or one already-admitted initial ResolutionOutput
+ optional explicit IRR-owned admission strategy
+ exact ResolutionAttribution for a new admission transition
        |
        v
orchestrate_initial_resolution(...)
        |
        v
InitialResolutionFrontier
```

`InitialResolutionFrontier` is a derived runtime view. It is **not** a new canonical IR record: it has no content identity and no canonical serialization surface.

```text
frontier != canonical lifecycle history
frontier != authority
frontier != global session status
```

The canonical history remains the exact immutable M1 records.

## 2. Narrow public runtime surface

M2.1 adds:

```text
InitialResolutionFrontierKind
    RESOLUTION_INPUT_REQUIRED
    ADMISSION_REQUIRED
    ADJUDICATION_REQUIRED
    RESOLUTION_OUTPUT_AVAILABLE

InitialResolutionFrontier

orchestrate_initial_resolution(...)
```

This is intentionally scoped to the initial resolution slice. It is not the universal M2 `TransitionFrontier` API deferred by M2.0.

The frontier carries:

- exact `IntentRequest.identity`;
- exact `ContextEnvelope.identity`;
- normalized exact candidate provenance where applicable;
- one exact admitted M1 `ResolvedIntent | ClarificationNeed | InformationNeed`, when available.

It does not carry Authorization, executor selection, WorkPlan state, retry state, provider confidence, or a mutable session phase.

## 3. Minimum lifecycle-graph admission

M2.0 froze:

```text
valid individual records != automatically valid lifecycle graph
```

M2.1 implements the minimum graph consistency required for the initial resolution path.

The supplied ContextEnvelope must descend from the exact supplied IntentRequest.

Every separately supplied CandidateResolution must reference:

```text
candidate.intent_request_identity == IntentRequest.identity
candidate.context_envelope_identity == ContextEnvelope.identity
```

Every already-admitted initial ResolutionOutput must preserve the same exact request/context lineage.

Duplicate candidate identities are rejected rather than counted as extra semantic support.

More than one already-admitted initial ResolutionOutput is rejected fail-closed as competing active initial lineage.

```text
output A + output B
!= choose first
!= choose newest
!= scheduler choice
```

If one admitted output already exists, separately supplied candidate material must already occur in that output's exact `candidate_inputs` provenance. Late/unrelated candidate material cannot be attached to historical admission merely because it shares the same request/context.

## 4. No material does not imply provider invocation

M2.1 does not invoke a Cognitive Provider by itself.

```text
IntentRequest + ContextEnvelope
+ no CandidateResolution
+ no admitted ResolutionOutput
+ no admission strategy transition
        ↓
RESOLUTION_INPUT_REQUIRED
```

This intentionally does **not** say `provider_required`.

M1.3 already permits a deterministic IRR path with empty `candidate_inputs`. An explicit IRR admission strategy may therefore resolve a simple request directly from the exact request/context graph without provider material.

```text
RESOLUTION_INPUT_REQUIRED
!= provider invocation authority
!= ambient retrieval authority
```

## 5. Candidate material still requires independent IRR admission

A single CandidateResolution is not sufficient for admission.

```text
one CandidateResolution
        ↓
ADMISSION_REQUIRED
```

Likewise, several semantically equivalent provider candidates remain candidate material until an independent IRR admission strategy accepts or transforms them.

```text
provider agreement != admission
provider count != authority
provider confidence != admission
```

The orchestrator therefore never contains logic equivalent to:

```text
if len(candidates) == 1:
    return ResolvedIntent(candidate.proposed_semantics)
```

That shortcut would collapse the provider/admission boundary and is explicitly forbidden.

## 6. Provider attribution is provenance, not voting weight

For frontier classification only, candidates are considered semantically equivalent when these exact payload dimensions match:

```text
proposed_semantics
assumptions
issues
clarification_proposals
information_need_proposals
```

Provider/invocation attribution is intentionally excluded from semantic-equivalence comparison because it is provenance, not precedence.

Candidate collections are normalized by exact candidate identity, so presentation/input order cannot become ranking.

Two providers proposing identical semantics therefore produce:

```text
ADMISSION_REQUIRED
```

not automatic admission.

Two providers disagreeing materially produce:

```text
ADJUDICATION_REQUIRED
```

A majority also does not win:

```text
2 x alpha candidate + 1 x beta candidate
!= alpha wins
```

## 7. ADJUDICATION_REQUIRED is not Governance

`ADJUDICATION_REQUIRED` means the currently supplied provider candidate material contains more than one semantic payload and no admitted ResolutionOutput has resolved that disagreement.

It is not:

- Governance review;
- user authorization;
- a trust score;
- provider election;
- scheduler arbitration;
- permission to discard a minority candidate.

An explicit IRR-owned admission/adjudication strategy may later resolve the candidate set. If it does, the final M1 ResolutionOutput must preserve the complete exact supplied candidate provenance.

## 8. Explicit IRR-owned admission strategy boundary

M2.1 allows the Host/runtime composition to supply an explicit callable admission strategy to `orchestrate_initial_resolution`.

Conceptually:

```text
admitter(
    exact IntentRequest,
    exact ContextEnvelope,
    normalized CandidateResolution[],
    exact ResolutionAttribution,
)
    -> ResolvedIntent | ClarificationNeed | InformationNeed | None
```

This callable represents the **IRR-owned admission policy/implementation boundary**, not a Cognitive Provider.

It may be deterministic rule logic or another separately governed resolver implementation. M2.1 does not freeze its concrete class hierarchy or transport protocol.

The important distinction is structural:

```text
CandidateResolution producer
!= Resolution admission strategy
```

The orchestrator does not treat the admitter's existence as authority. `ResolutionAttribution` is still not Governance Authorization.

## 9. Admitter output is validated, not trusted wholesale

Even an explicit admission strategy does not get to return arbitrary graph material.

A non-`None` returned output must be an exact M1 ResolutionOutput type and must preserve:

```text
output.intent_request_identity == IntentRequest.identity
output.context_envelope_identity == ContextEnvelope.identity
output.admission_attribution == supplied ResolutionAttribution
output.candidate_inputs == complete normalized supplied candidate set
```

The final equality is deliberate.

An admission strategy may adjudicate disagreement, reject candidate claims, or produce independent admitted semantics, but it cannot erase inconvenient provider provenance or invent hidden provider candidate inputs.

```text
adjudication != provenance erasure
admission != hidden candidate injection
```

M1 constructor validation continues to enforce the output-specific invariants, for example a `ResolvedIntent` cannot contain unresolved blocking issues.

## 10. Deterministic no-provider path remains representable

Because M1.3 permits empty `candidate_inputs`, M2.1 supports an IRR admission strategy that resolves directly from exact request/context material.

```text
IntentRequest
+ ContextEnvelope
+ candidate_inputs = ()
+ explicit admitter
+ ResolutionAttribution
        ↓
ResolvedIntent | ClarificationNeed | InformationNeed
```

This preserves:

```text
IRR != LLM wrapper
```

The core orchestrator still performs no ambient lookup. A deterministic strategy only receives the explicit request/context/candidate arguments passed through the boundary.

## 11. Admitter abstention preserves the frontier

An admission strategy may return `None`.

That is an explicit abstention, not a failure and not an automatic provider retry.

The orchestrator then returns the same unresolved frontier class implied by the current explicit material:

```text
no candidates                    -> RESOLUTION_INPUT_REQUIRED
semantically equivalent candidates -> ADMISSION_REQUIRED
semantically distinct candidates   -> ADJUDICATION_REQUIRED
```

No retry/fallback loop is synthesized.

## 12. ResolutionAttribution is occurrence material, not approval

A new admission transition requires an explicit `ResolutionAttribution`.

M2.1 rejects an admission strategy call without it.

Conversely, supplying ResolutionAttribution without an explicit admitter is rejected rather than creating a ghost admission occurrence.

```text
ResolutionAttribution != Authorization
ResolutionAttribution alone != admission
```

The returned ResolutionOutput must preserve that exact supplied attribution.

## 13. Existing admitted output preserves history

If the admitted lifecycle graph already contains exactly one initial ResolutionOutput, M2.1 returns it unchanged.

```text
existing admitted output
→ RESOLUTION_OUTPUT_AVAILABLE
```

No new admitter or ResolutionAttribution may be supplied on that path. M2.1 rejects attempts to combine historical admitted output with a second admission transition.

This is history preservation, not precedence over another admitted output. Two distinct admitted initial outputs fail closed.

## 14. Frontier is explicitly non-canonical

`InitialResolutionFrontier` is immutable and slotted for runtime hygiene, but it intentionally does not implement:

```text
canonical_bytes()
identity
wire schema
```

This directly implements the M2.0 rule:

```text
materialized runtime view != canonical semantic history
```

Persisting or transporting this derived view cannot replace persistence of the exact underlying M1 records.

## 15. What M2.1 does not add

M2.1 does not add:

- Cognitive Provider transport or invocation;
- provider disclosure policy;
- ambient retrieval;
- automatic CandidateResolution admission;
- trust/confidence scoring;
- majority voting;
- a universal admission algorithm;
- WorkPlan construction;
- Binding orchestration;
- Capability Catalog lookup;
- Governance;
- Authorization;
- Executor or Worker handoff;
- persistence;
- scheduler implementation;
- retry/fallback;
- parent-intent completion policy;
- global LifecycleGraph public API;
- mutable ResolutionSession source of truth.

Those remain later M2 slices.

## 16. M2.1 invariants

```text
frontier != canonical record
frontier != global lifecycle state

ContextEnvelope lineage must match exact IntentRequest
CandidateResolution lineage must match exact request + context
valid individual record != arbitrary graph admission
duplicate candidate delivery != extra semantic weight
competing admitted ResolutionOutputs != scheduler choice
orphan candidate != historical output provenance

CandidateResolution != ResolutionOutput
one provider candidate != admission
provider consensus != admission
provider attribution != semantic precedence
provider count != voting authority
candidate input order != precedence
semantically distinct candidates -> ADJUDICATION_REQUIRED

admitter != Cognitive Provider
admitter output != trusted wholesale
admitter output must preserve complete exact candidate provenance
admitter abstention != retry

no candidate != provider requirement
no candidate != ambient provider invocation
ResolutionAttribution != Authorization
ResolutionAttribution alone != admission
ResolutionOutput != WorkPlan
```

## 17. Acceptance

M2.1 is complete when executable tests prove at least:

```text
no resolution material -> RESOLUTION_INPUT_REQUIRED
frontier has no canonical identity/wire surface
foreign request/context/candidate lineage fails closed
duplicate candidate identity fails closed
one provider candidate -> ADMISSION_REQUIRED, not automatic ResolvedIntent
explicit IRR admitter can produce exact M1 ResolutionOutput
deterministic no-provider admission path remains possible
semantically equivalent provider candidates preserve all provenance
candidate input order does not change frontier/result
provider majority does not choose semantics
semantically distinct candidates -> ADJUDICATION_REQUIRED
explicit admitter may adjudicate only while retaining all supplied candidate provenance
provider clarification proposal alone does not pause IRR
provider information proposal alone does not grant retrieval authority
admitter may abstain without hidden retry
ResolutionAttribution without admitter fails closed
admitter without ResolutionAttribution fails closed
admitter cannot replace admission attribution
admitter cannot erase/invent candidate provenance
one existing admitted output is preserved exactly
existing output cannot be combined with a new admission transition
multiple admitted initial outputs fail closed
candidate outside existing output provenance is rejected as orphan material
all frozen M0/M1 tests and identities remain unchanged
Python 3.11–3.14 CI passes
```

After M2.1 closes, the next planned slice is **M2.2 — Work / Binding Orchestrator**.
