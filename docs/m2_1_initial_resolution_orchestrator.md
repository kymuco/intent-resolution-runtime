# M2.1 — Initial Resolution Orchestrator

Status: **implementation slice**.

M2.1 is the first runtime implementation built on the M2.0 Runtime Orchestration Charter. It turns the frozen M1.3 resolution records into a deliberately narrow initial-resolution orchestration path without introducing a mutable canonical session, provider transport, ambient retrieval, Governance, WorkPlan construction, or effect execution.

The implemented boundary is:

```text
exact IntentRequest
+ exact ContextEnvelope
+ zero or more explicit CandidateResolution records
+ zero or one already-admitted initial ResolutionOutput
+ explicit ResolutionAttribution when a new admission is deterministic
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

## 1. Narrow public runtime surface

M2.1 adds:

```text
InitialResolutionFrontierKind
    CANDIDATE_INPUT_REQUIRED
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

## 2. Minimum lifecycle-graph admission

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

If one admitted output already exists, separately supplied candidate material must be contained in that output's exact `candidate_inputs` provenance. A late/unrelated candidate cannot be attached to the historical output merely because it belongs to the same request/context.

## 3. No candidate material means an explicit frontier requirement

M2.1 does not invoke a provider by itself.

```text
IntentRequest + ContextEnvelope
+ no CandidateResolution
+ no admitted ResolutionOutput
        ↓
CANDIDATE_INPUT_REQUIRED
```

This frontier means only that the current M2.1 path lacks candidate/admission material.

It does not grant provider invocation, data disclosure, retrieval, or network authority.

```text
candidate input required != provider invocation authority
```

A later Host/provider orchestration slice may satisfy this boundary explicitly.

## 4. Provider count is provenance, not voting weight

M1.3 intentionally separates provider production from IRR admission. M2.1 therefore does not rank providers and does not treat repeated agreement as authority.

Before deterministic admission, candidates are compared by their exact semantic payload:

```text
proposed_semantics
assumptions
issues
clarification_proposals
information_need_proposals
```

Provider attribution is intentionally excluded from that semantic-equivalence comparison.

Thus two candidates with identical semantic payloads but different provider/invocation provenance may be admitted together as exact provenance inputs.

Their collection is normalized by canonical candidate identity, so input order does not become precedence.

```text
provider A agrees with provider B
!= stronger authority
!= trust score
!= majority rule
```

The final M1 ResolutionOutput retains every exact equivalent candidate in `candidate_inputs`, so provenance remains identity-material even though provider count does not select semantics.

## 5. Semantically distinct candidates stop at adjudication

If supplied candidates differ in any admitted semantic payload dimension, M2.1 returns:

```text
ADJUDICATION_REQUIRED
```

and admits no ResolutionOutput.

This remains true even when a majority of providers return one interpretation.

```text
2 x alpha candidate + 1 x beta candidate
!= alpha wins
```

M2.1 has no provider precedence, confidence weighting, latest-provider rule, insertion-order rule, or canonical-identity winner.

`ADJUDICATION_REQUIRED` is a runtime frontier classification, not Governance review and not authority. A later deterministic IRR policy, explicit additional material, or other bounded adjudication mechanism may resolve it without changing this invariant.

## 6. Deterministic ResolvedIntent admission

When all supplied candidates are semantically equivalent and contain no blocking ResolutionIssue, M2.1 may admit a `ResolvedIntent`.

The output uses:

```text
semantics          = candidate.proposed_semantics
assumptions        = candidate.assumptions
unresolved_issues  = candidate.issues
candidate_inputs   = all exact semantically equivalent candidates
```

M1.3 validation remains authoritative: a blocking issue still cannot enter ResolvedIntent.

The orchestrator does not manufacture a `ResolutionAttribution`. The caller must supply an explicit exact IRR admission occurrence when a new admission is deterministic.

```text
deterministic semantics
!= implicit admission occurrence
```

## 7. Deterministic pause admission is deliberately narrow

M1.3 allows several kinds of blocking issue and several ways to continue. It did not freeze a general candidate-admission algorithm mapping arbitrary provider proposals to arbitrary blockers.

M2.1 therefore automates only an unambiguous cardinality case:

```text
exactly one blocking ResolutionIssue
+
exactly one ClarificationProposal
+
zero InformationNeedProposal
        ↓
ClarificationNeed
```

or:

```text
exactly one blocking ResolutionIssue
+
exactly one InformationNeedProposal
+
zero ClarificationProposal
        ↓
InformationNeed
```

The exact proposal remains nested inside CandidateResolution provenance. The admitted pause copies only the fields already defined by the frozen M1.3 output schema.

## 8. Cases that remain ADJUDICATION_REQUIRED

M2.1 deliberately stops instead of guessing when the candidate contains:

- more than one blocking issue;
- both clarification and information-need proposal paths;
- more than one applicable pause proposal;
- a blocking issue without one unique proposal path;
- semantically distinct CandidateResolution payloads.

For example:

```text
blocking issue A
blocking issue B
+ one clarification proposal
```

is not mechanically mapped because M1.3 has no typed proposal-to-issue edge proving that one question resolves both blockers.

Similarly:

```text
one missing-information issue
+ clarification proposal
+ information-need proposal
```

contains a real continuation-mode choice. M2.1 does not choose the mode by preference.

## 9. Existing admitted output wins only as history, not precedence

If the admitted lifecycle graph already contains exactly one initial ResolutionOutput, M2.1 returns it unchanged.

It does not create a second admission occurrence and does not rewrite candidate provenance.

```text
existing admitted output
→ RESOLUTION_OUTPUT_AVAILABLE
```

A newly supplied `ResolutionAttribution` does not replace the historical output attribution.

This is history preservation, not semantic precedence over a competing admitted output. Two distinct admitted initial outputs fail closed rather than selecting one.

## 10. Frontier is explicitly non-canonical

`InitialResolutionFrontier` is immutable and slotted for runtime hygiene, but it intentionally does not implement:

```text
canonical_bytes()
identity
wire schema
```

This is a direct implementation of the M2.0 rule:

```text
materialized runtime view != canonical semantic history
```

Persisting or transporting this derived view cannot replace persistence of the exact underlying M1 records.

## 11. What M2.1 does not add

M2.1 does not add:

- Cognitive Provider transport or invocation;
- provider disclosure policy;
- ambient retrieval;
- trust/confidence scoring;
- majority voting;
- general candidate adjudication;
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

## 12. M2.1 invariants

```text
frontier != canonical record
frontier != global lifecycle state

ContextEnvelope lineage must match exact IntentRequest
CandidateResolution lineage must match exact request + context
one valid record != arbitrary graph admission
duplicate candidate delivery != extra semantic weight
competing admitted ResolutionOutputs != scheduler choice
orphan candidate != historical output provenance

provider attribution != semantic precedence
provider count != voting authority
candidate input order != precedence
semantically distinct candidates -> ADJUDICATION_REQUIRED

no candidate != ambient provider invocation
blocking issue != ResolvedIntent
multiple blockers != guessed pause mapping
competing pause modes != hidden choice

ResolutionAttribution != Authorization
ResolutionOutput != WorkPlan
```

## 13. Acceptance

M2.1 is complete when executable tests prove at least:

```text
no candidate -> CANDIDATE_INPUT_REQUIRED
frontier has no canonical identity/wire surface
foreign request/context/candidate lineage fails closed
duplicate candidate identity fails closed
one unblocked candidate -> ResolvedIntent
semantically equivalent provider candidates preserve all provenance
candidate input order does not change result
provider majority does not choose semantics
semantically distinct candidates -> ADJUDICATION_REQUIRED
one blocker + one clarification path -> ClarificationNeed
one blocker + one information path -> InformationNeed
multiple blockers -> ADJUDICATION_REQUIRED
competing pause modes -> ADJUDICATION_REQUIRED
deterministic new admission requires explicit ResolutionAttribution
one existing admitted output is preserved exactly
multiple admitted initial outputs fail closed
candidate outside existing output provenance is rejected as orphan material
all frozen M0/M1 tests and identities remain unchanged
Python 3.11–3.14 CI passes
```

After M2.1 closes, the next planned slice is **M2.2 — Work / Binding Orchestrator**.
