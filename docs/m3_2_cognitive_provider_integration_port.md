# M3.2 — Cognitive Provider Integration Port

Status: **implementation candidate**.

Exact base:

```text
intent-resolution-runtime/main@df734a216658e2fea60ee24d1bc621ccbaa1efb0
```

M3.0 froze the Host rule that external integration mechanisms do not become semantic or
Governance authority. M3.1 added exact admitted-history persistence/replay without a
mutable canonical session state.

M3.2 introduces the first narrow external integration port: a Cognitive Provider may
receive one explicit Host-permitted projection and return attributable
`CandidateResolution` proposal material.

## Core boundary

```text
Host-permitted exact projection
        ↓
CognitiveProviderRequest
        ↓
CognitiveProviderPort.propose(...)
        ↓
CandidateResolution
        ↓
M3.2 lineage / attribution validation
        ↓
existing M2.1 Initial Resolution admission
```

The central invariant is:

```text
provider proposal != IRR admission
```

M3.2 does not allow a provider to produce `ResolvedIntent`, `ClarificationNeed`,
`InformationNeed`, Governance, Authorization, WorkPlan, execution, or canonical Host
state through this port.

## 1. Explicit disclosure projection

A Provider does not receive the complete `IntentRequest` or complete `ContextEnvelope`
through the M3.2 request.

`CognitiveProviderRequest` contains only:

```text
provider_ref
invocation_ref
exact IntentRequest identity
exact ContextEnvelope identity
IntentExpression
explicitly disclosed Context records
```

It deliberately does not contain:

```text
principal_ref
OriginAttribution
complete ContextEnvelope
HistoryRepository
Host state
acquisition/retrieval handle
Governance
Authorization
Executor
Worker
```

This prevents adapter convenience from silently widening the provider disclosure surface.

```text
Host possesses material != Provider may receive material
Context admitted to IRR != automatically disclosed to Provider
Provider request construction != permission proof
```

The Host remains responsible for deciding that the exact projection may be disclosed to
the exact provider before constructing/invoking the port.

## 2. Intent disclosure

The Provider receives the exact `IntentExpression` being resolved, but not the complete
`IntentRequest` identity/principal/origin structure as content.

The request carries the exact `IntentRequest.identity` separately so returned proposal
material can be bound to the correct IRR lineage.

```text
intent expression disclosure != principal disclosure
intent expression disclosure != origin relabeling
```

If a future provider integration genuinely requires additional identity-related semantic
material, that requirement must be represented through an explicit truthful Host/Context
boundary rather than by widening this port to ambient account state.

## 3. Context projection is selective and dependency-closed

`build_cognitive_provider_request(...)` accepts explicit Context record identities from
the exact `ContextEnvelope`.

Every disclosed record must already exist in that exact envelope.

The projection may be empty.

```text
empty projection != ambient fallback
```

When Context records carry semantic links, the disclosed subset must remain closed enough
for those links to remain interpretable:

- a disclosed `EvidenceRecord` must also disclose its referenced target record, except
  `ORIGIN_ATTRIBUTION` evidence which must target the exact `IntentRequest`;
- a disclosed `CompletenessRecord` must also disclose every referenced
  `TemporalBasisRecord`.

M3.2 does not invent a text/blob provider context format and does not flatten typed IRR
Context into anonymous strings.

```text
Provider projection != arbitrary prompt blob
ContextReferenceRecord != retrieved content
```

## 4. Provider invocation attribution

Each request carries:

```text
provider_ref
invocation_ref
```

The returned `CandidateResolution` must carry exactly the same values through its frozen
`CandidateAttribution`.

It must also reference the exact:

```text
IntentRequest identity
ContextEnvelope identity
```

M3.2 fails closed when any of those four links differ.

This prevents a Host adapter from accidentally accepting a candidate produced for a
foreign request, foreign Context lineage, different provider, or different invocation
occurrence.

```text
provider installed != proposal provenance
provider_ref != trust
invocation_ref != admission
```

## 5. Output remains proposal material

A successful port return is exactly one `CandidateResolution`.

That record already has the correct M1 meaning:

```text
Provider-produced candidate semantics. This is not admitted IRR state.
```

M3.2 adds no wrapper that changes that meaning.

Multiple provider invocations remain multiple separately attributable candidates. M3.2
performs no voting, ranking, majority selection, confidence aggregation, or semantic
merge.

```text
provider count != voting authority
candidate count != precedence
same proposal text != same invocation provenance
```

Existing M2.1 remains responsible for deriving the initial-resolution frontier and for
explicit IRR admission/adjudication.

## 6. Retrieval is intentionally absent

`CognitiveProviderPort` exposes only:

```text
propose(CognitiveProviderRequest) -> CandidateResolution
```

There is no repository, acquisition, search, browser, filesystem, network-retrieval, or
Host callback parameter in the contract.

A concrete provider implementation may of course use network transport to reach the
configured provider service; that transport effect is mechanism owned by the Host
integration. It does not grant the provider semantic permission to retrieve additional
world/Host material.

An implementation that performs hidden retrieval outside the supplied projection violates
the M3.2 contract.

If new external information is required, it must return through an explicit future Host
acquisition boundary and then through truthful semantic admission before it can become
IRR Context.

```text
Provider invocation != hidden retrieval
Provider output != newly admitted Context
Provider output != Observation by default
```

## 7. Transport failure is not semantic state

`invoke_cognitive_provider(...)` deliberately does not convert provider/transport
exceptions into `InformationNeed`, `ClarificationNeed`, `Outcome`, or any other IRR
semantic record.

```text
transport unavailable != missing semantic information
provider exception != Resolution
provider timeout != Outcome
```

A later Host integration layer may expose operational failure/retry UX, but that cannot be
silently encoded as IRR semantic history or retry authority.

## 8. Mechanism type, not new canonical IR

`CognitiveProviderRequest` is immutable typed integration mechanism state. It is not a new
M1 semantic record and deliberately has no IRR `SCHEMA`, content identity, or canonical
lifecycle meaning.

Its identities refer to existing canonical IRR records; the request itself does not become
canonical semantic history merely because an invocation occurred.

```text
Provider request != canonical lifecycle state
Provider invocation mechanism != semantic transition
```

The provider-produced `CandidateResolution`, by contrast, is an existing canonical
attributable proposal record and may be persisted in admitted history according to the
existing Host admission/persistence rules.

## 9. Authority boundaries

M3.2 preserves:

```text
Provider != resolver
Provider != IRR admission policy
Provider != Governance
Provider != Authorization
Provider != Executor
Provider != Worker
Provider proposal != Context
Provider proposal != evidence truth
CandidateResolution != ResolvedIntent
CandidateResolution != WorkPlan
CandidateResolution != permission
CandidateResolution != effect
```

`CognitiveProviderRequest` also carries no permission token. The Host's decision to call a
configured provider remains a Host integration responsibility under product-owned
disclosure/network policy.

## 10. Non-goals

M3.2 adds no:

- provider SDK implementation;
- OpenAI/Gemini/local-model-specific adapter;
- prompt template or generic text/blob request;
- provider router or model selection policy;
- provider confidence voting;
- automatic Resolution admission;
- hidden retrieval/acquisition;
- Context mutation;
- persistent provider cache;
- retry/backoff/fallback policy;
- Governance transport;
- Authorization;
- Executor invocation;
- Worker dispatch;
- universal `HostRuntime`;
- HDE-specific dependency.

## 11. Acceptance

M3.2 is accepted when the exact implementation proves:

```text
Provider receives only explicit IntentExpression + selected Context projection
principal/origin/full Context are not implicitly disclosed
selected Context records must belong to the exact ContextEnvelope
linked projected Context remains dependency-closed
empty projection does not trigger ambient Context access
port surface is proposal-only
returned value must be exact CandidateResolution
request and Context lineage are preserved exactly
provider_ref and invocation_ref are preserved exactly
foreign lineage/attribution fails closed
transport failure does not become semantic IR
multiple provider invocations remain separate provenance
Provider proposal gains no admission/Governance/Authorization/execution authority
CI passes format/lint/mypy and Python 3.11–3.14
```

After M3.2, the next planned Host-integration slice remains:

# **M3.3 — Governance Integration Port**

unless an executable integration test exposes a concrete smaller prerequisite rather than
a speculative one.
