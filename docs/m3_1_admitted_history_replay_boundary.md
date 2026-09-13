# M3.1 — Admitted History Repository / Replay Boundary

Status: **implementation candidate**.

Exact base:

```text
intent-resolution-runtime/main@c5e5fecacee10aee23d37bc3ff93c39e5fb6d7cd
```

M1 defines immutable attributable semantic records. M2 derives replayable semantic
frontiers from exact record graph slices. M3.0 freezes the Host rule that persistence is
mechanism, not semantic authority.

M3.1 introduces the minimum executable persistence boundary needed to retain exact IRR
history without creating a mutable canonical session state.

## Core boundary

```text
validated/admitted canonical IRR record
        ↓
exact canonical bytes
+ content identity
+ top-level record type/schema
        ↓
AdmittedHistoryRepository.persist(...)
        ↓
exact lookup / bounded deterministic scan
        ↓
exact canonical bytes
        ↓
existing schema-specific from_json_bytes(...)
        ↓
M2 replay input
```

The repository does not decide which record is semantically active.

```text
persistence != semantic admission
record present != active lineage
retrieval order != lifecycle order
repository cursor != chronology
repository cursor != precedence
```

## 1. `HistoryRecord` is not a new semantic IR record

`HistoryRecord` is a Host persistence envelope. It deliberately has no IRR `SCHEMA` of
its own and no independent canonical lifecycle meaning.

It preserves:

- exact canonical record bytes;
- the SHA-256 `RecordIdentity` of those exact bytes;
- the top-level record type, represented by the exact canonical `schema` string.

Construction fails closed unless:

1. bytes decode as one canonical JSON object;
2. re-canonicalization produces exactly the supplied bytes;
3. the object has a top-level string `schema`;
4. `record_type` equals that schema exactly;
5. `identity` equals the SHA-256 identity of those exact bytes.

The storage envelope intentionally does **not** replace the existing schema-specific
validator. It does not prove that an arbitrary schema-tagged object is a valid current IRR
semantic record.

For semantic replay, retrieved exact bytes must still be parsed by the appropriate frozen
record type, for example:

```text
HistoryRecord.canonical_record_bytes
→ IntentRequest.from_json_bytes(...)
```

This keeps responsibilities separate:

```text
repository integrity validation != IR semantic validation
storage schema tag != semantic admission
```

Unknown/future schema-tagged canonical material may be retained losslessly by a backend,
but it cannot participate in current semantic replay merely because it is stored.

## 2. Repository contract

M3.1 freezes the narrow public protocol:

```text
persist(HistoryRecord) -> HistoryPersistResult
get(RecordIdentity) -> HistoryRecord | None
read(HistoryQuery) -> HistoryPage
```

There is deliberately no:

```text
latest()
current()
active()
update()
delete()
replace()
set_status()
```

The contract is append/idempotent by content identity.

Exact duplicate persistence returns `ALREADY_PRESENT` rather than creating another
semantic occurrence or changing precedence.

```text
same identity + same exact type/content
→ idempotent persistence
```

Any same-identity/different-content state is an integrity conflict and must fail closed.
The repository must never resolve such a conflict through insertion order or overwrite.

## 3. Bounded retrieval

`HistoryQuery` requires an explicit bounded `limit` with a fixed M3.1 maximum.

Optional filters are:

```text
record_type
after_identity
```

The reference backend sorts by content identity solely to provide deterministic cursor
pagination independent of insertion order.

```text
identity sort order = retrieval mechanism only
identity sort order != semantic chronology
identity sort order != recency
identity sort order != active-lineage precedence
```

A Host must not infer semantic meaning from page position.

## 4. Competing history remains competing history

If two individually valid records of the same type are persisted, both remain present.
The repository does not choose one because it was inserted later, scanned later, has a
larger digest, or appears on a later page.

```text
valid records individually != one active lifecycle automatically
competing history != latest-write-wins
competing history != repository choice
```

Conflict/adjudication semantics remain in the existing IRR record graph and orchestrator
boundaries.

## 5. Replay means exact reconstruction, not effect replay

M3.1 replay is only the recovery of exact semantic history inputs.

```text
repository replay
= retrieve exact canonical record bytes
+ revalidate using frozen record schema
+ re-derive M2 frontier from exact history/configuration
```

It is not:

```text
Executor invocation
retry
fallback
re-send
Worker redispatch
provider re-call
Governance re-call
```

Therefore:

```text
restart != retry
missing persisted Outcome != proof of no external effect
record persistence != external effect certainty
```

M3.1 does not solve crash windows around effectful invocation. That boundary remains for
the later Executor/Host integration slice.

## 6. Configuration and replay claims

M3.0 requires materially relevant replay configuration to be explicit/versioned when it
affects semantic derivation or admission.

M3.1 deliberately does not invent one universal configuration record before the later
Host ports exist. The repository stores exact IRR records; a Host may only claim complete
semantic replay when it can also identify the exact relevant configuration required by
the orchestrator/admission boundary being replayed.

```text
record repository alone != complete replay claim when configuration matters
configuration identity != authority
```

This avoids prematurely turning Host mechanism configuration into canonical semantic
history.

## 7. Reference backend

`InMemoryAdmittedHistoryRepository` is an executable reference implementation of the
contract, not the production persistence backend.

It exists to prove:

- exact idempotent persistence;
- exact identity lookup;
- bounded pagination;
- insertion-order independence;
- no latest-write-wins behavior;
- replay from exact bytes.

M3.1 intentionally adds no SQLite schema, filesystem layout, database transaction
protocol, network store, replication strategy, or cache layer.

Those are backend mechanism choices as long as they preserve the frozen repository
contract.

## 8. Authority boundaries

M3.1 adds no semantic or effect authority.

```text
persisted != admitted by persistence
persisted != active
persisted != selected
persisted != authorized
persisted != executed
persisted Outcome != parent completion proof by storage alone
HistoryRepository != scheduler
HistoryRepository != Governance
HistoryRepository != Executor
HistoryRepository != retry engine
```

## 9. Non-goals

M3.1 adds no:

- mutable `ResolutionSession`;
- universal `HostRuntime`;
- event-sourcing framework;
- global lifecycle enum;
- `latest` or active-record selector;
- schema-specific semantic registry owned by persistence;
- product/HDE dependency;
- provider transport;
- Governance transport;
- Executor transport;
- Worker transport;
- acquisition mechanism;
- retry/fallback/recovery policy;
- external-effect crash protocol;
- production database backend;
- automatic replay orchestration across all M2 slices.

## 10. Acceptance

M3.1 is accepted when the exact implementation proves:

```text
canonical bytes are retained losslessly
record identity is bound to exact bytes
record type is bound to exact top-level schema
noncanonical bytes fail closed
identity/content mismatch fails closed
exact duplicate persistence is idempotent
exact identity lookup works
history scans are always bounded
scan order is insertion-order independent
scan order carries no semantic precedence
same-type competing records are retained, not overwritten
retrieved bytes reconstruct the same typed IR record
repository exposes no latest/current/active/update/delete authority
repository adds no Governance/Authorization/execution/retry authority
CI passes format/lint/mypy and Python 3.11–3.14
```

After M3.1, the next planned Host-integration slice remains the M3 charter sequence:

# **M3.2 — Cognitive Provider Integration Port**

unless a concrete replay integration test exposes a smaller prerequisite rather than a
speculative one.
