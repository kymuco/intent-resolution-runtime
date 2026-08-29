# M1 — Intent IR

Status: **implementation milestone**.

M0 froze IRR's semantic boundaries. M1 encodes those semantics as immutable, inspectable Python contracts without reopening the product boundary.

```text
M0 semantics
    -> immutable contracts
    -> validation
    -> canonical serialization
    -> stable identity / digests
    -> executable architecture fixtures
```

## Execution slices

M1 is implemented incrementally:

```text
M1.1  IntentRequest Core & Canonical Identity
M1.2  Context / Claims / Evidence IR
M1.3  Resolution / Clarification IR
M1.4  Binding / Symbolic Reference IR
M1.5  Work / Delegation IR
M1.6  Capability / Governance References
M1.7  Attempt / Outcome / Continuation IR
M1.8  Executable M0.10 Fixtures & M1 Closure
```

The sequence is an implementation plan, not permission to collapse semantic roles between slices.

---

# M1.1 — IntentRequest Core & Canonical Identity

M1.1 creates the first `src/intent_resolution_runtime/` package and freezes only the smallest input record required to preserve M0.1 attribution semantics.

## Contract

```text
IntentRequest
├─ schema = irr.intent_request.v1
├─ origin
│  ├─ kind = human | companion | worker | system
│  ├─ actor_ref
│  └─ source_event_ref
├─ principal_ref
└─ expression
   └─ text
```

All records are immutable.

`StableRef` is an opaque namespaced Host-supplied reference. M1.1 does not interpret its namespace or infer trust/authority from it.

`source_event_ref` is required because two identical textual requests can be two distinct attributable occurrences.

```text
same text != same occurrence
```

## Origin semantics

`OriginAttribution` records **attribution**, not verification.

```text
origin attribution != origin verification
origin != principal
origin != authority
```

M1.1 therefore has no `verified`, `trusted`, `approved`, `safe`, `permission`, or equivalent authority fields.

A companion initiative can be represented directly:

```text
origin.kind = companion
origin.actor_ref = character_os.actor:kaguya
principal_ref = hde.principal:user:self
```

without relabeling the companion as human.

## Canonical serialization

The v1 wire representation is deterministic UTF-8 JSON:

- object keys sorted lexicographically;
- no insignificant whitespace;
- UTF-8 text preserved without silent Unicode normalization;
- duplicate object keys rejected while parsing;
- `NaN` / `Infinity` rejected;
- unknown fields rejected at every M1.1 record boundary;
- schema discriminator required exactly.

Unknown fields are fail-closed. In particular, a producer cannot smuggle authority or verification semantics into `IntentRequest` by adding fields the schema does not own.

## Identity

Record identity is:

```text
sha256(canonical_json_bytes(record))
```

The digest is content identity for the complete v1 record, including origin attribution, source event, principal, and expression.

It is not:

- user identity;
- authentication;
- authorization;
- proof of truth;
- persistence identity outside the record contract.

## Explicit deferrals

M1.1 does **not** freeze:

- Context / Claim / Evidence schemas;
- Temporal Basis;
- CandidateResolution;
- ResolvedIntent;
- Clarification;
- Binding / symbolic references;
- WorkPlan / WorkStep;
- DelegatedWork / WorkerResult;
- Capability Catalog / Match;
- Governance / Authorization;
- Attempt / Outcome / Continuation;
- non-text expression schemas;
- transport or persistence.

Those arrive in later M1 slices and must preserve the M0 distinctions.

## Acceptance

M1.1 is correct when tests prove at least:

```text
immutable records
origin != principal representability
origin attribution != verification
same text + different source event -> different identity
canonical round-trip determinism
material field change -> identity change
unknown fields rejected
duplicate JSON keys rejected
authority-like extra fields rejected
unknown v1 origin kinds rejected
```
