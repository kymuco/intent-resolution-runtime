# M4.0 — Successor Semantic Resolution Candidate & Admission Boundary

Status: **design freeze candidate**.

Exact base:

```text
intent-resolution-runtime/main@76d65a8055bb49e5da836d13ea03f2c8cffacf00
```

## Why M4 exists

M0–M3 deliberately froze initial resolution, continuation, worker return, provider,
Governance, Executor, and Host integration without inventing a universal mutable runtime.

Concrete HDE embedding evidence now exposes one missing semantic authority boundary:

```text
durable ContinuationInput
→ ?
→ successor ResolvedIntent | ClarificationNeed | InformationNeed
→ SuccessorResolutionLineage
```

The frozen core already has:

- `CandidateResolution`;
- `ResolvedIntent`;
- `ClarificationNeed`;
- `InformationNeed`;
- `ContinuationInput`;
- `SuccessorResolutionLineage`;
- initial-resolution proposal/admission semantics.

But it does **not** have a clean successor-resolution candidate/admission orchestrator.

This is no longer speculative integration glue. A real Host now reaches an exact durable
`ContinuationInput` and must stop because successor semantic authority is absent.

## Central rule

```text
ContinuationInput != successor semantics
provider proposal != IRR admission
successor admission != WorkPlan
successor admission != Authorization
```

M4.0 fills only the semantic resolution gap.

## Why initial-resolution M2.1 cannot simply be reused

M2.1 resolves:

```text
IntentRequest
+ ContextEnvelope
+ CandidateResolution[]
→ ResolutionOutput
```

A successor decision additionally depends on exact attributable re-entry material:

```text
predecessor ResolvedIntent
+ ContinuationInput[]
+ ContextEnvelope
```

The frozen `CandidateResolution` schema has no `ContinuationInput` lineage.

Adding continuation fields to `CandidateResolution` would mutate the frozen M1.3 wire
contract and would also make initial candidates carry successor-only concepts.

Treating ContinuationInput as Context would be equally incorrect:

```text
ContinuationInput != ClaimRecord
ContinuationInput != EvidenceRecord
ContinuationInput != ContextEnvelope
WorkerResult != automatically admitted Context
CapabilityOutcome != automatically admitted Context
```

Therefore M4.0 adds a successor-specific canonical proposal wrapper while preserving
`CandidateResolution` unchanged.

# 1. New canonical SuccessorCandidateResolution

M4.0 introduces conceptually:

```python
@dataclass(frozen=True, slots=True)
class SuccessorCandidateResolution:
    predecessor: ResolvedIntent
    continuation_inputs: tuple[ContinuationInput, ...]
    candidate: CandidateResolution
```

Proposed schema:

```text
irr.successor_candidate_resolution.v1
```

This record means:

> This exact provider candidate is proposed for this exact predecessor branch using this
> exact canonical successor re-entry material.

It is still proposal provenance.

```text
SuccessorCandidateResolution != ResolutionOutput
SuccessorCandidateResolution != admission
SuccessorCandidateResolution != factual truth
SuccessorCandidateResolution != provider trust
```

## 1.1 Exact predecessor lineage

`predecessor` is the full exact `ResolvedIntent`, not a narrative label or Host-local
session identifier.

Every continuation input must satisfy:

```text
ContinuationInput.resolved_intent_identity
==
predecessor.identity
```

The wrapper therefore cannot mix re-entry material from another resolved branch.

## 1.2 Exact continuation material

`continuation_inputs` is non-empty.

It uses the already-frozen `ContinuationInput` values unchanged.

Normalization follows the existing successor lineage rule:

- exact tuple type;
- exact `ContinuationInput` values;
- duplicate ContinuationInput identities rejected;
- one exact semantic source cannot be amplified by multiple re-entry wrappers inside one
  successor candidate.

Therefore:

```text
same source submitted twice
!= two independent semantic facts
```

## 1.3 Existing CandidateResolution remains the provider semantic body

The nested `candidate` stays the existing frozen M1.3 type.

It continues to own:

- provider/invocation attribution;
- proposed semantics;
- assumptions;
- resolution issues;
- clarification proposals;
- information-need proposals;
- exact `IntentRequest` identity;
- exact `ContextEnvelope` identity.

M4.0 does not duplicate those fields in another candidate schema.

The wrapper adds only the missing successor lineage.

## 1.4 Candidate intent lineage

The nested candidate must satisfy:

```text
candidate.intent_request_identity
==
predecessor.intent_request_identity
```

Its `context_envelope_identity` is validated against the exact successor resolution
ContextEnvelope by the orchestrator.

# 2. Context remains a separate Host boundary

M4.0 accepts an exact `ContextEnvelope` for the successor resolution cycle.

The envelope must satisfy:

```text
context_envelope.intent_request_identity
==
predecessor.intent_request_identity
```

It may be:

- the same exact ContextEnvelope used by the predecessor; or
- a new explicit Host-admitted ContextEnvelope for the same IntentRequest lineage.

M4.0 does not synthesize, merge, enrich, or mutate Context.

Most importantly:

```text
ContinuationInput is supplied separately from ContextEnvelope
```

A Host that wants new world/context records must admit them through the existing truthful
Context boundary rather than laundering a WorkerResult or Outcome into Context.

# 3. SuccessorResolutionFrontier

M4.0 introduces a derived non-canonical frontier analogous in role to M2.1 but specific
to successor semantics.

Conceptually:

```python
class SuccessorResolutionFrontierKind(Enum):
    RESOLUTION_INPUT_REQUIRED
    ADMISSION_REQUIRED
    ADJUDICATION_REQUIRED
    RESOLUTION_OUTPUT_AVAILABLE
```

and:

```python
@dataclass(frozen=True, slots=True)
class SuccessorResolutionFrontier:
    predecessor: ResolvedIntent
    continuation_inputs: tuple[ContinuationInput, ...]
    context_envelope_identity: RecordIdentity
    kind: SuccessorResolutionFrontierKind
    candidate_inputs: tuple[SuccessorCandidateResolution, ...]
    successor_lineage: SuccessorResolutionLineage | None
```

The frontier is not canonical semantic history.

```text
SuccessorResolutionFrontier != admitted lifecycle record
```

The canonical semantic history remains:

- `SuccessorCandidateResolution` proposal records;
- the eventual `ResolutionOutput`;
- `SuccessorResolutionLineage`.

# 4. Successor candidate normalization

Multiple successor candidates remain separately attributable proposals.

Input ordering creates no precedence.

Candidates are normalized by exact identity.

Duplicate wrapper identities are rejected.

Every wrapper must preserve the exact supplied:

```text
predecessor
continuation_inputs
ContextEnvelope identity through nested CandidateResolution
```

A wrapper for another predecessor, another re-entry set, or another ContextEnvelope is
foreign material and fails closed.

# 5. Semantic equivalence and unresolved frontier kind

M4.0 mirrors the already-frozen M2.1 rule:

Provider attribution is provenance, not voting weight.

Semantic equivalence compares the nested `CandidateResolution` semantic payload:

```text
proposed_semantics
assumptions
issues
clarification_proposals
information_need_proposals
```

It does not use:

- provider count;
- input order;
- provider identity;
- candidate digest ordering;
- "latest" candidate.

Therefore:

```text
no candidates
→ RESOLUTION_INPUT_REQUIRED

one candidate or semantically equivalent candidates
→ ADMISSION_REQUIRED

semantically divergent candidates
→ ADJUDICATION_REQUIRED
```

No case automatically becomes admitted merely because it is unique or unanimous.

# 6. Explicit SuccessorResolutionAdmitter

M4.0 introduces an explicit admitter type conceptually:

```python
SuccessorResolutionAdmitter = Callable[
    [
        ResolvedIntent,
        ContextEnvelope,
        tuple[ContinuationInput, ...],
        tuple[SuccessorCandidateResolution, ...],
        ResolutionAttribution,
    ],
    ResolutionOutput | None,
]
```

The admitter is IRR semantic admission authority for this exact transition.

It is not:

- Cognitive Provider transport;
- Governance;
- Authorization;
- user approval;
- Executor;
- Worker.

The orchestrator never invokes an admitter implicitly.

# 7. Successor output validation

A proposed admitted output must be an exact existing M1.3 `ResolutionOutput`:

```text
ResolvedIntent
| ClarificationNeed
| InformationNeed
```

It must preserve:

```text
successor.intent_request_identity
==
predecessor.intent_request_identity

successor.context_envelope_identity
==
exact supplied ContextEnvelope.identity

successor.admission_attribution
==
exact supplied ResolutionAttribution
```

The output's `candidate_inputs` must equal the exact nested `CandidateResolution`
provenance represented by the supplied `SuccessorCandidateResolution` set.

This preserves the frozen M1.3 output schema while the new wrappers preserve exact
Continuation lineage separately.

# 8. Mechanical SuccessorResolutionLineage construction

After an admitter returns one valid ResolutionOutput, IRR constructs:

```python
SuccessorResolutionLineage(
    predecessor=predecessor,
    continuation_inputs=exact_inputs,
    successor_kind=mechanically_derived_kind,
    successor=admitted_output,
)
```

This construction is mechanical.

It does not create semantic authority beyond the already-explicit admitter result.

The existing frozen lineage constructor then enforces:

- exact predecessor;
- exact continuation inputs;
- no same-source semantic amplification;
- successor IntentRequest preservation;
- predecessor/source/re-entry/successor occurrence separation;
- exact successor kind.

M4.0 does not weaken any M1.7 rule.

# 9. Existing admitted lineage replay

The orchestrator supports replay from an already-existing exact
`SuccessorResolutionLineage`.

Conceptually:

```python
orchestrate_successor_resolution(
    predecessor,
    context_envelope,
    continuation_inputs,
    candidate_inputs=...,
    admitted_lineages=(lineage,),
)
```

Replay requires:

```text
lineage.predecessor == exact predecessor
lineage.continuation_inputs == exact supplied continuation_inputs
lineage.successor.context_envelope_identity == exact ContextEnvelope.identity
lineage.successor.candidate_inputs == exact nested CandidateResolution provenance
```

More than one competing active lineage fails closed.

```text
multiple successor lineages != latest wins
multiple successor lineages != identity ordering
multiple successor lineages != hidden branch selection
```

An existing admitted lineage cannot be combined with a fresh admitter transition.

# 10. Deterministic no-provider path remains valid

M1.3 already permits an admitted ResolutionOutput with:

```text
candidate_inputs = ()
```

for deterministic IRR resolution.

M4.0 preserves this.

A deterministic successor admitter may therefore admit successor semantics directly from
exact predecessor + continuation material + ContextEnvelope without a Cognitive Provider.

This is still explicit IRR admission, not automatic continuation.

# 11. Provider integration is intentionally a later M4 slice

M4.0 freezes core canonical proposal/admission semantics only.

It does not modify the frozen M3.2 `CognitiveProviderPort`.

A later M4 provider slice should introduce an explicit successor-provider mechanism that
can receive, subject to Host disclosure policy:

- original IntentExpression;
- exact admitted predecessor semantic state or an explicit predecessor projection;
- exact selected ContinuationInput material;
- explicit Context projection.

That future mechanism may return the existing `CandidateResolution`, after which IRR
constructs/validates the canonical `SuccessorCandidateResolution`.

The old M3.2 request must not be reused while silently withholding ContinuationInput from
the provider.

```text
provider did not receive re-entry material
!= successor candidate based on re-entry material
```

# 12. Persistence implications

`SuccessorCandidateResolution` is canonical IR and therefore must support the
existing M3.1 exact-history mechanism.

M3.1 is intentionally schema-agnostic: `HistoryRecord` preserves exact canonical bytes
and the top-level schema string without a semantic parser registry. The implementation
slice must therefore add exact `HistoryRecord` persistence/replay coverage plus typed
`SuccessorCandidateResolution.from_json_bytes(...)` reconstruction without inventing a
new registry or changing the meaning of existing schemas.

The derived `SuccessorResolutionFrontier` is not persisted.

The final lineage already has canonical identity through the frozen
`SuccessorResolutionLineage`.

# 13. Relationship to WorkerResult

Concrete HDE evidence motivating M4.0 is:

```text
WorkerResult
→ ContinuationInput
→ M4.0 successor resolution
```

But M4.0 remains Host/product neutral.

The same boundary supports any frozen Continuation source class:

- CapabilityOutcome;
- WorkerResult;
- BindingIssue;
- CapabilityMatchIssue;
- GovernanceContinuationMaterial.

M4.0 must not special-case Codexia or HDE.

# 14. Relationship to parent completion

A successor `ResolvedIntent` is still semantic state.

It does not prove:

- parent WorkPlan completion;
- parent intent completion;
- delegated completion acceptance;
- capability success;
- effect occurrence;
- authority.

```text
successor ResolvedIntent != parent completion
```

If the successor semantics say that no further operational work is required, the normal
post-resolution work-disposition boundary still decides that explicitly.

# 15. Relationship to WorkPlan and Governance

After an admitted successor ResolvedIntent:

```text
SuccessorResolutionLineage
→ ordinary post-resolution work lifecycle
```

The old WorkPlan is not mutated in place.

A materially changed scope/effect/objective must produce explicit successor semantics and
then explicit successor work.

Prior Authorization does not automatically transfer.

```text
successor semantics != inherited Authorization
```

# 16. M4.0 orchestrator conceptual surface

The implementation should converge on a narrow surface conceptually equivalent to:

```python
orchestrate_successor_resolution(
    predecessor: ResolvedIntent,
    context_envelope: ContextEnvelope,
    continuation_inputs: tuple[ContinuationInput, ...],
    *,
    candidate_inputs: tuple[SuccessorCandidateResolution, ...] = (),
    admitted_lineages: tuple[SuccessorResolutionLineage, ...] = (),
    admitter: SuccessorResolutionAdmitter | None = None,
    admission_attribution: ResolutionAttribution | None = None,
) -> SuccessorResolutionFrontier
```

Exact naming may change during implementation, but authority must not widen.

# 17. Explicit non-goals

M4.0 does not add:

- Host-specific persistence policy;
- HDE-specific source selection;
- Codexia integration;
- provider transport;
- provider model selection;
- Context acquisition;
- automatic Context synthesis from Continuation;
- candidate ranking/voting;
- implicit admission;
- branch precedence;
- WorkPlan synthesis;
- parent completion;
- Governance;
- Authorization;
- Executor;
- retry/fallback;
- scheduler;
- background loop.

# 18. Required negative boundaries

```text
ContinuationInput != ContextEnvelope
ContinuationInput != CandidateResolution
ContinuationInput != successor ResolutionOutput

CandidateResolution != SuccessorCandidateResolution
SuccessorCandidateResolution != admission

provider proposal != resolver authority
provider count != voting authority

old ContextEnvelope != automatically stale
new ContextEnvelope != implicit merge with old Context

successor output != WorkPlan
successor output != parent completion
successor output != Authorization

SuccessorResolutionLineage != retry
SuccessorResolutionLineage != fallback
SuccessorResolutionLineage != branch precedence
```

# 19. Acceptance proof for the implementation slice

Executable tests should prove at least:

```text
SuccessorCandidateResolution round-trips canonically
wrapper requires exact predecessor
wrapper requires non-empty exact ContinuationInput tuple
wrapper rejects duplicate ContinuationInput identities
wrapper rejects semantic amplification of one source through repeated re-entry wrappers
wrapper candidate must preserve predecessor IntentRequest identity

successor ContextEnvelope must belong to predecessor IntentRequest
candidate ContextEnvelope identity must match exact supplied successor ContextEnvelope
foreign predecessor candidate fails closed
foreign continuation candidate fails closed
foreign Context candidate fails closed

no candidates -> resolution_input_required
equivalent candidates -> admission_required
divergent candidates -> adjudication_required
provider count/input order create no authority

attribution without admitter fails closed
admitter without explicit ResolutionAttribution fails closed
admitter output must preserve exact attribution
admitter output must preserve exact ContextEnvelope
admitter output must preserve exact nested CandidateResolution provenance

successful admission mechanically creates exact SuccessorResolutionLineage
lineage occurrence collisions fail closed
ResolvedIntent / ClarificationNeed / InformationNeed are all supported successor outputs

existing exact lineage replays without new admission
competing lineages fail closed
existing lineage + fresh admitter fails closed

frontier is non-canonical
SuccessorCandidateResolution is supported by admitted-history round trip
all frozen M1/M2/M3 tests remain green
```

# 20. HDE handoff after M4.0

M4.0 alone gives HDE a correct core authority surface, but not yet a real cognitive
provider path.

Expected next sequence:

```text
IRR M4.0
  successor candidate + admission core
        ↓
IRR M4.1
  successor Cognitive Provider projection/invocation
        ↓
HDE M33.23
  durable ContinuationInput
  → explicit provider proposal(s)
  → explicit IRR successor admission
  → durable SuccessorResolutionLineage
```

HDE must not implement its own successor ResolutionOutput constructor while waiting for
these IRR surfaces.

## Frozen M4.0 invariants

```text
initial resolution schema remains frozen
CandidateResolution remains frozen
ContinuationInput remains frozen
SuccessorResolutionLineage remains frozen

new successor proposal provenance is additive
new successor admission authority is explicit

Context stays Context
Continuation stays Continuation
provider stays proposal-only
IRR owns admission

one exact successor semantic branch is explicit canonical lineage
no hidden latest/first/best branch policy
```
