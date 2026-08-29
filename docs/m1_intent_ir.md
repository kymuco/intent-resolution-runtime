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

`IntentRequest.v1` intentionally uses a narrow canonical domain: nested JSON objects whose keys and leaf values are Unicode scalar strings. M1.1 does not define canonical numbers, arrays, booleans, or null because the v1 record does not contain them.

Canonical bytes are defined independently of Python object insertion order:

- object keys are ordered lexicographically by Unicode code point;
- keys and values must contain Unicode scalar values only; lone surrogate code points are rejected;
- `"` is encoded as `\"`;
- `\` is encoded as `\\`;
- U+0000 through U+001F are encoded as lowercase `\u00xx` escapes;
- all other Unicode scalar values are emitted directly as UTF-8;
- no insignificant whitespace is emitted;
- duplicate object keys are rejected while parsing;
- unknown fields are rejected at every M1.1 record boundary;
- schema discriminator is required exactly.

Input JSON need not already be canonical. Parsing produces typed IR; identity is computed only from re-encoded canonical bytes.

The restricted object/string domain is deliberate. Later M1 slices may extend the canonical value domain only with explicit encoding rules while preserving byte-for-byte encoding of the M1.1 subset.

Unknown fields are fail-closed. In particular, a producer cannot smuggle authority or verification semantics into `IntentRequest` by adding fields the schema does not own.

## Identity

Record identity is:

```text
sha256(canonical_json_bytes(record))
```

The digest is exactly 64 lowercase ASCII hexadecimal characters.

The M1.1 golden vector is frozen by tests. The canonical Kaguya companion request with source event `hde.event:evt-001`, principal `hde.principal:user:self`, and text `Стоит проверить последние логи.` has SHA-256:

```text
bedad2f962490352db8d156a3e39cbd40c2cbc6071a0bfc64899607fdd2967e8
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
- canonical numeric/array/boolean/null encoding;
- transport or persistence.

Those arrive in later M1 slices and must preserve the M0 distinctions.

## Acceptance

M1.1 is correct when tests prove at least:

```text
immutable records
origin != principal representability
origin attribution != verification
same text + different source event -> different identity
canonical golden bytes + digest
canonical round-trip determinism
material field change -> identity change
Unicode surrogate rejection
unknown fields rejected
duplicate JSON keys rejected
authority-like extra fields rejected
unknown v1 origin kinds rejected
strict lowercase ASCII SHA-256 identity
```
