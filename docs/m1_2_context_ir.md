# M1.2 — Context / Claims / Evidence IR

Status: **implementation slice**.

M1.2 encodes the M0.2 epistemic boundary without introducing a trust score, retrieval engine, provider disclosure policy, resolution state machine, or authority semantics.

```text
IntentRequest identity
        +
explicit Host Context boundary event
        |
        v
ContextEnvelope
        |
        +-- ClaimRecord
        +-- EvidenceRecord
        +-- TemporalBasisRecord
        +-- CompletenessRecord
        `-- ContextReferenceRecord
```

## Core distinctions

M1.2 preserves:

```text
Claim != factual truth
Claim attribution != Claim truth
Evidence for attribution != Evidence for Claim
Evidence != authority
Context Reference != retrieval authority
Context available to IRR != provider/worker disclosure authority
absence != negation
Completeness != inferred exhaustiveness
Temporal Basis != ambient wall clock
record order != source precedence
```

There is deliberately no `trusted`, `verified`, `confidence`, `approved`, `safe`, `authorized`, `retrieval_allowed`, or `disclosure_allowed` field in these records.

## SourceAttribution

Every Context record carries an explicit `SourceAttribution`:

```text
SourceAttribution
├─ source_ref
└─ source_event_ref
```

Both are opaque `StableRef` values. They preserve attributable source lineage and occurrence identity; they do not verify that source or grant authority.

## ClaimRecord

```text
ClaimRecord
├─ schema = irr.claim.v1
├─ attribution
└─ statement
```

A ClaimRecord represents semantic content presented as a proposition relevant to resolution. Its presence in Context does not make it true.

## EvidenceRecord

```text
EvidenceRecord
├─ schema = irr.evidence.v1
├─ attribution
├─ relation = supports | weakens
├─ target_kind
│  ├─ claim
│  ├─ attribution
│  └─ origin_attribution
├─ target_identity
└─ description
```

The target is explicit.

- `claim` targets the proposition represented by a `ClaimRecord` or the structured completeness assertion represented by a `CompletenessRecord`.
- `attribution` targets the source attribution attached to a Context record.
- `origin_attribution` targets the Origin attribution of the `IntentRequest` identified by the enclosing `ContextEnvelope`.

This prevents evidence that authenticates a source from silently becoming evidence that the source's descriptive claim is true.

`EvidenceRecord.description` is the attributable semantic description of the admitted evidentiary material/basis. M1.2 does not define cryptographic proof formats, evidence strength scores, or an automated trust algorithm. Representing evidence does not mean IRR accepts the target as established.

## TemporalBasisRecord

```text
TemporalBasisRecord
├─ schema = irr.temporal_basis.v1
├─ attribution
├─ kind
│  ├─ resolution_time
│  ├─ timestamp
│  ├─ sequence
│  └─ named
├─ value
└─ scope
```

`value` remains an attributable string in M1.2. This slice does not freeze a universal timestamp parser, clock provider, timezone database, or ordering rule.

A TemporalBasisRecord exists only when explicitly admitted. `ContextEnvelope` never reads the machine clock or inserts a current timestamp.

## CompletenessRecord

```text
CompletenessRecord
├─ schema = irr.completeness.v1
├─ attribution
├─ bounded_domain
├─ purpose
└─ temporal_basis_refs[]
```

Completeness is an explicit attributable assertion over a bounded domain and purpose. It is not inferred from collection size, apparent exhaustiveness, or absence of another record.

`temporal_basis_refs` may be empty when no temporal claim is represented. When present, every referenced Temporal Basis must be included in the same bounded ContextEnvelope.

M1.2 does not itself derive negative Claims. It merely preserves the structured completeness material required by later resolution logic to reason about scoped absence safely.

## ContextReferenceRecord

```text
ContextReferenceRecord
├─ schema = irr.context_reference.v1
├─ attribution
├─ reference
└─ description
```

A ContextReferenceRecord says that a possible source/material is identified. It does not say that its content is present.

```text
Context Reference != content
Context Reference != retrieval authority
Context Reference != disclosure authority
```

M1.2 contains no fetch, filesystem, network, account, browser, memory, GitHub, or Worker retrieval API.

## ContextEnvelope

```text
ContextEnvelope
├─ schema = irr.context_envelope.v1
├─ intent_request_identity
├─ boundary_event_ref
└─ records[]
```

The envelope is the explicit bounded Host-supplied semantic surface for one `IntentRequest` occurrence.

`boundary_event_ref` makes the admission occurrence attributable. Re-admitting the same Context records through a different Host boundary event is a distinct envelope occurrence.

All evidence targets that refer to Context records must resolve inside the same envelope. Evidence for `origin_attribution` must target the exact `intent_request_identity` carried by that envelope.

The envelope permits an explicit empty Context boundary. Empty Context is not evidence that anything is false or absent.

## No implicit precedence

M0.2 froze that there is no universal rule such as:

```text
human > worker
newer > older
verified > unverified
first item > later item
```

Accordingly, Context records are normalized by their content identity before canonical serialization. Reordering the same set of records does not change `ContextEnvelope` identity and cannot smuggle precedence through array order.

This normalization is only for the unordered Context-record set. Arrays in the canonical format are otherwise ordered data unless a record contract explicitly defines set semantics.

## Canonical encoding extension

M1.1 froze canonical JSON for nested objects and Unicode scalar strings.

M1.2 extends that domain only with arrays:

```text
object
array
Unicode scalar string
```

Arrays are encoded in declared order. Object key ordering, Unicode handling, escaping, UTF-8 output, duplicate-key rejection, and the M1.1 object/string encoding remain unchanged byte-for-byte.

Numbers, booleans, and null remain unsupported in canonical IR values until a later schema actually requires them.

The frozen M1.1 golden digest remains:

```text
bedad2f962490352db8d156a3e39cbd40c2cbc6071a0bfc64899607fdd2967e8
```

The M1.2 reference ContextEnvelope golden digest is:

```text
5929077095122f7315b5e4380cc817688c5ec47641bae0750002db9d5cae1d46
```

## Validation and fail-closed behavior

M1.2 rejects:

- mutable `list` construction where immutable record tuples are required;
- duplicate Context record identities;
- unsupported record schemas;
- unknown fields;
- invalid enum values;
- non-scalar Unicode;
- evidence targets outside the bounded envelope;
- `claim` evidence targeting a non-claim record;
- `origin_attribution` evidence targeting another IntentRequest;
- Completeness temporal references that do not resolve to an included TemporalBasisRecord;
- authority, retrieval, verification, or provider-disclosure field smuggling.

## Explicit deferrals

M1.2 does **not** freeze:

- trust scores or trust-level enums;
- cryptographic proof or identity-provider formats;
- truth-admission algorithms;
- Conflict or Material Ambiguity runtime state;
- Assumption schemas;
- Clarification / Information Need schemas;
- Observation schemas;
- Freshness scoring or universal recency precedence;
- provider or Worker disclosure policy schemas;
- Context retrieval/resolution;
- canonical numbers, booleans, or null;
- persistence;
- Resolution / Work / Governance / Attempt state.

Observation and Binding-related IR remain later slices. In particular, ordinary Context data is not silently reclassified as Observation.

## Acceptance

M1.2 is correct when executable tests prove at least:

```text
all records immutable
Context boundary occurrence attributable
same record set in different order -> same envelope identity
Claim evidence != attribution evidence
Origin-attribution evidence can be represented without authority
evidence target must remain inside bounded Context
explicit Completeness required
Completeness temporal links are bounded
empty Context != Completeness
Context Reference has no retrieval/disclosure authority
provider-disclosure field smuggling rejected
cross-record links survive canonical round-trip
M1.2 golden digest frozen
M1.1 golden digest unchanged
unknown attribution fields rejected
invalid evidence enum values rejected
Temporal Basis explicit and attributable
```
