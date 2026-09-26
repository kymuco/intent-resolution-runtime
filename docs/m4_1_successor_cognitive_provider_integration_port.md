# M4.1 — Successor Cognitive Provider Integration Port

Status: **design freeze candidate**.

Exact base:

```text
intent-resolution-runtime/main@052e13860736728d924622dec3dfc974a30ecfc6
```

## Purpose

M4.0 closes successor semantic admission inside IRR:

```text
ResolvedIntent predecessor
+ exact ContinuationInput[]
+ explicit ContextEnvelope
+ SuccessorCandidateResolution[]
→ explicit SuccessorResolutionAdmitter
→ ResolutionOutput
→ SuccessorResolutionLineage
```

M4.1 adds only the missing proposal-source integration:

```text
explicit Host-permitted successor projection
→ Cognitive Provider
→ CandidateResolution
→ exact SuccessorCandidateResolution
```

The provider remains proposal-only.

## Why M3.2 is not silently reused

M3.2 `CognitiveProviderRequest` contains:

- exact IntentExpression;
- exact IntentRequest identity;
- exact ContextEnvelope identity;
- explicit projected Context records.

It does not contain:

- predecessor ResolvedIntent semantics;
- ContinuationInput material.

Therefore an M3.2 provider invocation cannot honestly claim that its proposal is based on
successor re-entry material.

M4.1 does not mutate the frozen M3.2 request or port.

## Core rule

```text
provider saw exact successor projection
!= provider owns successor semantics

CandidateResolution
!= SuccessorCandidateResolution

SuccessorCandidateResolution
!= admitted ResolutionOutput
```

M4.1 transports attributable proposal material only.

# 1. Separate successor provider request

M4.1 introduces mechanism state conceptually equivalent to:

```python
@dataclass(frozen=True, slots=True)
class SuccessorCognitiveProviderRequest:
    provider_ref: StableRef
    invocation_ref: StableRef

    intent_request_identity: RecordIdentity
    context_envelope_identity: RecordIdentity
    intent_expression: IntentExpression

    predecessor_identity: RecordIdentity
    predecessor_semantics: str
    predecessor_assumptions: tuple[AssumptionRecord, ...]
    predecessor_unresolved_issues: tuple[ResolutionIssue, ...]

    continuation_inputs: tuple[ContinuationInput, ...]

    context_records: tuple[ProviderContextRecord, ...]
```

This request is integration mechanism state, not canonical semantic history.

It is not persisted as a new semantic IR record.

# 2. Predecessor semantic projection

M4.1 intentionally does not disclose the full `ResolvedIntent` object.

The request discloses exactly the admitted predecessor semantic state needed for
successor interpretation:

- predecessor identity;
- semantics;
- assumptions;
- unresolved issues.

It does not automatically disclose:

- predecessor candidate_inputs;
- old provider identities/invocation refs;
- old provider proposal text beyond admitted semantics;
- Host repository state.

The builder validates that the projection is byte-semantically derived from the exact
supplied predecessor.

```text
predecessor projection != another semantic summary
```

No provider or Host may rewrite the predecessor semantic state inside this mechanism.

# 3. Exact continuation disclosure

The successor request includes the exact supplied `ContinuationInput[]`.

This is deliberate.

M4.0 binds each `SuccessorCandidateResolution` to the exact continuation inputs on which
the proposal is claimed to depend. A provider that did not receive those inputs cannot
produce an honestly attributable successor candidate for them.

Therefore:

```text
all continuation inputs used for one provider proposal
must cross that provider boundary exactly
```

The Host remains responsible for deciding whether this exact material may be disclosed
to this provider before building/invoking the request.

M4.1 does not grant disclosure authority.

If exact ContinuationInput content must not cross a remote boundary, the Host must:

- use a provider permitted to receive it;
- use a local provider;
- or construct a different explicit semantic/acquisition boundary before successor
  provider invocation.

M4.1 does not silently redact a ContinuationInput while retaining its full semantic
identity.

# 4. Continuation normalization

The request requires:

- exact tuple type;
- non-empty tuple;
- exact `ContinuationInput` values;
- no duplicate input identities;
- no repeated re-entry amplification of one semantic source;
- every input descends from the exact predecessor ResolvedIntent.

Normalization follows the same source-identity ordering frozen by M4.0/M1.7.

# 5. Context disclosure remains M3.2-compatible

M4.1 reuses the existing `ProviderContextRecord` set and projection-link rules.

The Host explicitly supplies `disclosed_context_identities`.

Only exact records from the supplied `ContextEnvelope` may cross the provider boundary.

Evidence/completeness dependency validation remains identical to M3.2.

Continuation is not converted into Context.

```text
ContinuationInput != ProviderContextRecord
```

# 6. Original IntentExpression remains available

Successor resolution still belongs to the same IntentRequest lineage.

The provider receives the original exact `IntentExpression` together with:

- predecessor admitted semantics;
- new continuation material;
- current explicit Context projection.

This allows a provider to interpret the semantic delta without losing the original user
intent.

The request must preserve:

```text
intent_request.identity
==
predecessor.intent_request_identity
==
context_envelope.intent_request_identity
==
every continuation_input.resolved_intent_identity's parent request lineage
```

# 7. Separate provider protocol

M4.1 introduces a separate protocol conceptually:

```python
@runtime_checkable
class SuccessorCognitiveProviderPort(Protocol):
    def propose_successor(
        self,
        request: SuccessorCognitiveProviderRequest,
    ) -> CandidateResolution:
        ...
```

It does not overload or mutate M3.2:

```python
CognitiveProviderPort.propose(CognitiveProviderRequest)
```

A concrete provider implementation may implement both protocols.

The separation keeps initial and successor disclosure contracts independently
inspectable.

# 8. Builder

Conceptual surface:

```python
build_successor_cognitive_provider_request(
    *,
    provider_ref,
    invocation_ref,
    intent_request,
    predecessor,
    context_envelope,
    continuation_inputs,
    disclosed_context_identities=(),
) -> SuccessorCognitiveProviderRequest
```

The builder validates:

- exact IntentRequest;
- exact predecessor lineage;
- exact ContextEnvelope lineage;
- exact continuation lineage;
- explicit Context disclosure subset;
- all projection dependency rules.

Construction itself grants no permission.

# 9. Invocation

Conceptual surface:

```python
invoke_successor_cognitive_provider(
    provider,
    request,
    *,
    intent_request,
    predecessor,
    context_envelope,
    continuation_inputs,
) -> SuccessorCandidateResolution
```

Invocation first revalidates that the request exactly matches the supplied source
material.

Then it calls:

```text
provider.propose_successor(request)
```

The provider must return an exact `CandidateResolution`.

M4.1 validates:

```text
candidate.intent_request_identity
== request.intent_request_identity

candidate.context_envelope_identity
== request.context_envelope_identity

candidate.attribution.provider_ref
== request.provider_ref

candidate.attribution.invocation_ref
== request.invocation_ref
```

Finally IRR constructs mechanically:

```python
SuccessorCandidateResolution(
    predecessor=exact predecessor,
    continuation_inputs=exact continuation_inputs,
    candidate=validated_candidate,
)
```

The provider never constructs the canonical wrapper itself.

# 10. Why the wrapper is IRR-created

`SuccessorCandidateResolution` is canonical IRR proposal provenance.

Provider ownership ends at `CandidateResolution`.

This preserves:

```text
provider proposes body
IRR binds exact successor lineage
IRR admits successor semantics separately
```

A provider cannot substitute:

- another predecessor;
- another continuation set;
- another ContextEnvelope;
- another provider attribution.

# 11. Provider failure

Transport/model/provider exceptions remain mechanism failures.

M4.1 does not convert them into:

- ClarificationNeed;
- InformationNeed;
- ResolutionIssue;
- CapabilityOutcome;
- retry request;
- fallback proposal.

A Host may separately decide whether another provider invocation should occur.

```text
provider failure != semantic ResolutionOutput
```

# 12. No provider voting

M4.1 may produce multiple separately attributable
`SuccessorCandidateResolution` records from multiple provider invocations.

It does not rank, vote, select, or adjudicate them.

M4.0 remains the admission boundary.

```text
provider count != semantic authority
```

# 13. No hidden fallback

M4.1 does not:

- retry the same provider;
- invoke a second provider;
- switch local/remote models;
- use tools/retrieval;
- widen Context disclosure;
- synthesize missing continuation data.

Every provider invocation is explicit and attributable.

# 14. Security / disclosure boundary

Remote provider transport may itself be an external disclosure effect in a Host product.

IRR M4.1 does not decide whether that disclosure is authorized.

The Host must establish whatever Governance/Authorization/disclosure policy applies
before invoking this mechanism.

The provider request is evidence of *what would cross the boundary*, not permission to
send it.

# 15. Relationship to M4.0

M4.1 ends at:

```text
SuccessorCandidateResolution
```

Then M4.0 handles:

```text
SuccessorCandidateResolution[]
→ successor frontier
→ explicit admitter
→ SuccessorResolutionLineage
```

M4.1 does not call the admitter automatically.

This allows a Host to:

- collect one or more proposals;
- inspect them;
- persist them;
- adjudicate them;
- or choose a deterministic no-provider path.

# 16. Relationship to HDE M33.23

After M4.1, HDE can compose:

```text
durable M33.22 ContinuationInput
→ explicit successor provider projection
→ M4.1 SuccessorCandidateResolution
→ explicit M4.0 admission
→ durable SuccessorResolutionLineage
```

HDE still owns:

- provider choice;
- disclosure policy;
- exact invocation occurrence;
- durable Host admission/reconciliation mechanism.

IRR owns:

- provider request lineage validation;
- candidate attribution validation;
- canonical successor candidate binding;
- successor semantic admission contracts.

# 17. Explicit non-goals

M4.1 does not add:

- provider discovery;
- provider ranking;
- model routing;
- automatic local/remote selection;
- retries/fallback;
- tool use;
- retrieval;
- ambient Context acquisition;
- semantic admission;
- WorkPlan synthesis;
- parent completion;
- Governance;
- Authorization;
- Executor;
- Worker dispatch;
- scheduler;
- background loop.

# 18. Acceptance proof

Executable tests should prove at least:

```text
request requires exact predecessor projection
request requires exact non-empty continuation tuple
same-source repeated re-entry is rejected
foreign continuation predecessor fails closed

builder preserves exact IntentExpression
builder preserves exact predecessor semantic state
builder excludes predecessor candidate_inputs
builder discloses only selected Context records
builder enforces Evidence/Completeness projection dependencies
ContinuationInput never appears in context_records

request/source revalidation rejects:
  foreign IntentRequest
  foreign predecessor
  foreign ContextEnvelope
  changed predecessor semantics
  changed continuation tuple
  undisclosed/foreign Context records

provider must satisfy SuccessorCognitiveProviderPort
provider must return exact CandidateResolution
foreign IntentRequest candidate fails closed
foreign ContextEnvelope candidate fails closed
wrong provider_ref fails closed
wrong invocation_ref fails closed

successful invocation returns exact SuccessorCandidateResolution
wrapper predecessor is exact
wrapper continuation_inputs are exact
wrapper candidate is exact provider output

provider exception is propagated as mechanism failure
no semantic output/admission is manufactured

M3.2 CognitiveProviderPort remains unchanged
M4.0 successor admission remains unchanged
all frozen M3.2/M4.0 tests remain green
```

## Frozen M4.1 invariants

```text
initial provider request remains frozen
successor provider request is additive

predecessor projection is exact admitted semantics
predecessor candidate provenance is not automatically disclosed

Continuation stays Continuation
Context stays Context

provider sees exact continuation material it is claimed to reason over
redacted continuation != same semantic input

provider returns CandidateResolution only
IRR constructs SuccessorCandidateResolution

provider proposal != successor admission
provider failure != semantic state
provider count != authority

Host owns disclosure decision
M4.1 request != disclosure permission
```
