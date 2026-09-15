# M3.3 — Governance Integration Port

Status: **proposed Host integration boundary for external Governance review**.

Exact base:

```text
intent-resolution-runtime/main@9ae73ff80e372895d2b718d26ce4dcabc677844b
```

M1 froze `WorkProposal`, `GovernanceDecision`, and `Authorization` as separate
canonical records. M2.3 froze replayable orchestration over those records, including a
separate Authorization materialization frontier. M3.3 moves one layer outward and
answers one Host-integration question:

> How does a real Host transport one exact `WorkProposal` to external Governance and
> receive one attributable `GovernanceDecision` without turning the integration adapter
> into Governance authority, Authorization materialization, or execution authority?

The answer is deliberately narrow.

## 1. Boundary

```text
exact WorkProposal
+ governance occurrence attribution
+ exact authority-context ref / identity
        ↓
GovernanceReviewRequest
        ↓
GovernancePort.review(...)
        ↓
GovernanceDecision
        ↓
existing M2.3
        ↓
separate Authorization materialization transition
```

`GovernanceReviewRequest` is Host mechanism state. It is not a new canonical semantic
record and it does not grant authority.

## 2. Exact proposal, not a lossy approval prompt

Governance reviews the exact canonical `WorkProposal`.

M3.3 does not replace it with:

- a boolean `requires_approval` flag;
- a natural-language summary as sole authority source;
- a mutable session object;
- a generic JSON policy payload;
- a list of tool names detached from proposal lineage.

This preserves the M0.6 invariant:

```text
Authorization applies to reviewed work semantics
not merely to a lossy description of them
```

Human-facing summaries may exist outside this boundary, but they do not replace the exact
proposal carried by the integration request.

## 3. Explicit authority-context attribution

One request contains:

```text
governance_ref
decision_event_ref
authority_context_ref
authority_context_identity
proposal
```

The authority context itself remains external Governance/Host-owned material. IRR does
not gain ambient access to identity, consent, account state, organizational policy, or
session state through this port.

The ref/identity pair records what authority context the external mechanism claims it
used. It is not cryptographic attestation and not proof that the Governance mechanism was
correct or secure.

```text
authority-context attribution != trust verification
governance_ref != verified authority identity
decision_event_ref != permission token
```

## 4. GovernancePort is review-only

The public protocol is conceptually:

```python
def review(request: GovernanceReviewRequest) -> GovernanceDecision: ...
```

It deliberately has no:

```text
authorize(...)
materialize_authorization(...)
execute(...)
invoke_capability(...)
retrieve(...)
search(...)
```

The fact that a Governance adapter is installed does not grant any authority.

```text
GovernancePort installed != authority
Governance transport success != Authorization
```

## 5. Input provenance is checked before disclosure

`invoke_governance(...)` receives the exact source `WorkProposal` separately and verifies
that the prepared request contains that proposal before calling external Governance.

This prevents a manually constructed mechanism request from retaining plausible
Governance attribution while silently substituting different work.

```text
exact source WorkProposal
→ validated GovernanceReviewRequest
→ external Governance
```

A request bound to another proposal fails before the external adapter is invoked.

## 6. Output binding is fail-closed

A successful external return must be an exact `GovernanceDecision` whose:

- `proposal` equals the reviewed exact proposal;
- `governance_ref` equals the request value;
- `decision_event_ref` equals the request occurrence;
- `authority_context_ref` equals the request value;
- `authority_context_identity` equals the request value.

A structurally valid decision with different lineage or attribution does not cross the
M3.3 boundary.

M3.3 validates binding consistency. It does not independently prove that external
Governance was entitled to make the decision.

## 7. Decision remains separate from Authorization

This is the most important M3.3 invariant.

```text
GovernanceDecision != Authorization
GovernanceDecision(AUTHORIZE) != admitted Authorization history
```

An `AUTHORIZE` decision component means that the existing M2.3 graph may expose the
corresponding canonical `Authorization` as an eligible idempotent transition.

Conceptually:

```text
GovernancePort
    ↓
GovernanceDecision(AUTHORIZE component)
    ↓
M2.3 authorization_materialization_frontier
    ↓
Authorization candidate projection
    ↓
explicit Host admission/persistence of that exact record
```

M3.3 does not perform the last transition automatically.

Therefore:

```text
external allow response != admitted Authorization automatically
Governance transport != authority materialization
```

## 8. Deny / constrain / require_review remain exact decision semantics

M3.3 transports all already-frozen `GovernanceDecisionKind` values without inventing a
parallel status vocabulary:

```text
AUTHORIZE
DENY
CONSTRAIN
REQUIRE_REVIEW
```

The existing M1 invariants remain authoritative:

- DENY does not erase or invalidate the proposal;
- CONSTRAIN does not silently rewrite the WorkPlan;
- REQUIRE_REVIEW is not eventual approval;
- non-AUTHORIZE components cannot materialize `Authorization`.

M3.3 does not interpret those decisions into new work. Existing continuation/successor
boundaries remain responsible for semantic consequences.

## 9. Mechanism failure is not semantic Governance output

Provider/transport exceptions propagate as mechanism failures.

M3.3 does not synthesize:

```text
DENY
REQUIRE_REVIEW
Authorization
CapabilityOutcome
```

from a socket error, timeout, adapter exception, or unavailable service.

```text
Governance unavailable != Governance denied
transport failure != semantic decision
```

Retry and fallback remain separate future Host policy and must not arise implicitly from
this port.

## 10. No ambient Host state

`GovernanceReviewRequest` has no product-owned:

- principal/user/session object;
- policy engine handle;
- history repository;
- account store;
- credential store;
- executor;
- capability invocation handle.

If external Governance needs additional authority material, the embedding system owns
that mechanism. The IRR request records its authority-context attribution rather than
absorbing that ambient state.

## 11. Multiple review occurrences remain distinct

Two reviews of the same exact proposal under different decision occurrences or authority
contexts remain separate attributable `GovernanceDecision` records.

M3.3 does not apply:

```text
latest decision wins
last adapter response wins
most permissive decision wins
```

Competing active decision history remains subject to existing fail-closed M2 replay
rules.

## 12. Public API

M3.3 adds only mechanism-level integration surface:

```text
GovernanceReviewRequest
GovernancePort
GovernanceIntegrationError
build_governance_review_request(...)
invoke_governance(...)
```

`GovernanceReviewRequest` is not added to the closed canonical IR type set because it is
not semantic history.

## 13. Non-goals

M3.3 adds no:

- Governance/policy engine implementation;
- consent UI or human-review product;
- identity verification or authentication system;
- organization/account policy model;
- Authorization admission or automatic materialization;
- Executor or capability invocation;
- CapabilityAttempt or CapabilityOutcome production;
- retry/fallback/recovery policy;
- hidden acquisition or retrieval;
- mutable canonical session state;
- universal `HostRuntime`;
- HDE-specific dependency;
- new GovernanceDecision schema;
- new Authorization schema.

## 14. Acceptance invariant

After M3.3 the Host-safe authority path is:

```text
exact WorkProposal
→ explicit GovernanceReviewRequest
→ external Governance review
→ exact attributable GovernanceDecision
→ existing M2.3 replay
→ explicit separate Authorization materialization when eligible
→ STOP before execution
```

The boundary preserves:

```text
WorkProposal != GovernanceDecision
GovernanceDecision != Authorization
GovernanceDecision(AUTHORIZE) != admitted Authorization history
GovernancePort installed != authority
Governance transport success != Authorization materialization
authority-context attribution != trust verification
Governance request != ambient Host state
Authorization != invocation
```

If this slice validates cleanly, the next direct Host-integration milestone is:

# **M3.4 — Executor / Capability Invocation Port**

unless concrete integration evidence exposes an earlier prerequisite rather than a
speculative one.
