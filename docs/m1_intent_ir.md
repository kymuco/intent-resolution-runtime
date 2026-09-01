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

---

# M1.2 — Context / Claims / Evidence IR

M1.2 encodes the M0.2 epistemic input boundary as immutable Context records while preserving the separation between Claims, source Attribution, Evidence, Completeness, Temporal Basis, Context References, truth, and authority.

The detailed normative implementation contract is maintained in [M1.2 Context / Claims / Evidence IR](m1_2_context_ir.md).

Core executable distinctions:

```text
Context boundary source + occurrence are attributable
Claim != factual truth
Evidence for Claim != Evidence for Attribution
Evidence target != evidentiary scope
Evidence != authority
Completeness != inferred exhaustiveness
Temporal Basis != ambient clock
Context Reference != retrieval/disclosure authority
record order != source precedence
```

M1.2 extends canonical IR values only with arrays while preserving M1.1 object/string encoding byte-for-byte. Resolution, Clarification, Observation, Binding, Work, Governance, Attempt/Outcome, trust algorithms, retrieval, disclosure policy, and persistence remain later slices.

---

# M1.3 — Resolution / Clarification IR

M1.3 encodes the M0.2/M0.7 boundary between provider-produced candidate semantics and IRR-owned admitted resolution or pause semantics.

The detailed normative implementation contract is maintained in [M1.3 Resolution / Clarification IR](m1_3_resolution_ir.md).

Core executable distinctions:

```text
provider proposes != IRR admits
CandidateResolution != ResolvedIntent
ClarificationNeed != ResolvedIntent
InformationNeed != retrieval authority
Material Ambiguity -> blocking
unresolved blocking issue -> no ResolvedIntent
non-blocking uncertainty may remain explicit
Assumption != established fact
resolution admission != Authorization
resolution admission != Effect
```

`CandidateResolution` is bound to exact IntentRequest and ContextEnvelope identities plus provider invocation attribution. Any candidate retained as provenance by `ResolvedIntent`, `ClarificationNeed`, or `InformationNeed` must belong to that same request/context lineage.

M1.3 preserves ordinary epistemic `uncertainty` separately from `conflict` and `missing_information`; uncertainty may be blocking or non-blocking, does not invent competing alternatives, and is not a confidence or trust score.

M1.3 does not introduce WorkPlan, Binding, Observation, Capability/Governance, Attempt/Outcome, provider transport, trust scoring, retrieval authority, or persistence. Those remain later M1 slices.

---

# M1.4 — Binding / Symbolic Reference IR

M1.4 encodes the frozen M0.4 Late Binding boundary as immutable symbolic-reference, attributable binding-input, bounded rule, successful bound-value, and unresolved binding-issue records.

The detailed normative implementation contract is maintained in [M1.4 Binding / Symbolic Reference IR](m1_4_binding_ir.md).

Core executable distinctions:

```text
late binding != unadmitted semantic discretion
symbolic reference != observed value
Binding Input != Observation by default
selection_scope != value_scope
Binding Rule != hidden program
input order != binding precedence
source attribution != source verification
binding evaluation != retrieval
binding evaluation != external effect
BoundValue != Authorization
BindingIssue != Continuation
binding failure != fallback authority
```

`BindingRule` freezes the semantic type, bounded selection domain, admitted input roles, source-attribution and source-lineage dimensions, required material provenance, declarative constraints, and selection policy before future values arrive. M1.4 does not cryptographically prove an association between a caller-supplied `SourceAttribution.source_ref` and `source_identity`; both remain explicit admitted dimensions and neither becomes authentication or authority.

`selection_scope` names the admitted domain over which mechanical selection occurs. `value_scope` is the concrete resource/surface associated with one candidate and may become known only at binding time. A concrete value scope becoming known does not grant Authorization over that scope.

RFC3339 timestamp comparison in M1.4 preserves arbitrary supplied fractional precision and compares offset-equivalent lexical forms as the same instant. The v1 comparator fail-closes on RFC3339 `-00:00` unknown-offset form and leap-second notation rather than silently interpreting either as a known ordinary instant.

M1.4 golden identity fixtures freeze the current canonical wire for a representative symbolic backup-selection path:

```text
SymbolicReference  ec1a9dc741af9bded6fbcfcf39e09b8772ca866ea77314b7e5553ebfca451a69
BindingInput A     80d924d187cb42fd2385d258294e6069d7fc601d127f3788dd8c609ebcb0e8c8
BindingInput B     d87a892f54532f4acb6367fc0a62195001e9bdcfa509ac2cbaccf1e02b21c5e8
BindingRule        cdf10037dbeeae766b5eb7aaba51702d2828a7e11b4888f2db4b85ffbc32db03
BoundValue         c42a00e3a5632831215e56a2739d0b6671454d575b81d69bcbb3bc2cc2c9bd68
BindingIssue       ba6fe8fb6071a8eec52e5893a37faf6967d2f00df894ac1d2a55471180e76b5e
```

The same full test suite continues to execute the frozen M1.1 request, M1.2 context, and M1.3 candidate/resolved golden identities, so adding M1.4 cannot silently redefine earlier canonical bytes.

M1.4 deliberately does not introduce WorkPlan/WorkStep, DelegatedWork, Capability/Governance records, generic Continuation, Observation/Outcome schemas, external retrieval, execution scheduling, retry/fallback, or persistence. Those remain later slices.

---

# M1.5 — Work / Delegation IR

M1.5 encodes the M0.3 Intent → Work boundary and M0.8 Worker Delegation boundary as separate immutable contracts so ordinary bounded WorkSteps cannot become disguised Worker-owned autonomous lifecycles.

**M1.5 is complete.** Part A freezes bounded `WorkPlan` / `WorkStep` IR; Part B freezes explicit Worker delegation, handoff, returned material, and need re-entry. Detailed contracts are maintained in [M1.5 Work / Delegation IR — Part A](m1_5_work_delegation_ir.md), [M1.5 Worker Delegation IR — Part B1](m1_5b_delegation_ir.md), and [M1.5 Worker Result IR — Part B2](m1_5b_worker_result_ir.md).

Core executable distinctions include:

```text
work description != execution
work description != authorization
semantic operation != implementation command
presentation order != execution dependency
symbolic input != known value
internal symbolic dataflow -> producer dependency path
WorkStep lineage includes parent WorkPlan ref
step completion != plan completion
plan completion != intent satisfaction by default
return_to_irr != embedded planner loop
WorkStep != Worker delegation
DelegatedWork != ordinary WorkStep
DelegatedWork != Authorization
DelegatedWorkHandoff != Authorization
capability allowance != Capability Match
same capability_ref != same capability semantics
worker context surface != ambient context entitlement
WorkerResult != factual truth by default
WorkerResult != Observation by default
WorkerResult != Outcome by default
WorkerResult != Governance Decision
WorkerResult != Authorization
WorkerResult != parent intent completion
worker completion claim != delegated completion proof
WorkerNeed != authority grant
WorkerNeed != scope expansion
```

Part A introduces immutable `WorkLiteralInput`, `WorkSymbolicInput`, `WorkOutput`, `WorkStep`, and `WorkPlan`. A WorkPlan is finite and acyclic, its steps are bound to one exact ResolvedIntent identity and explicit parent-plan reference, internal symbolic dataflow must follow dependency lineage, and `return_to_irr` cannot hide a pre-admitted dependent successor. WorkStep and WorkPlan carry distinct identity-covered completion contracts.

Part B1 introduces immutable `DelegatedScope`, `DelegatedContextReference`, `DelegatedCapabilityAllowance`, `DelegationConstraint`, `ExpectedDeliverable`, `DelegatedWork`, `DelegationHandoffAttribution`, and `DelegatedWorkHandoff`. The delegation envelope carries exact ResolvedIntent/optional parent WorkPlan lineage, bounded objective and scope, explicit Worker context, exact capability-contract ceiling identities, material/negative/authority-requirement constraints, required deliverables, and delegated completion semantics without minting Capability Match, Catalog membership, availability, or Authorization.

Part B2 introduces immutable `WorkerResultAttribution`, `WorkerResultMaterial`, `WorkerNeed`, and `WorkerResult`. A result embeds the exact immutable handoff; Worker attribution must match the handoff target; result and handoff occurrences remain distinct; returned deliverables are explicitly related to the admitted `ExpectedDeliverable`; Worker needs may request new semantics without granting them; source provenance remains distinct from Worker intermediary attribution. There is deliberately no success/failure/blocked/unknown-outcome status or parent-completion boolean in M1.5b — those lifecycle semantics remain M1.7.

Representative canonical identities are frozen by executable tests:

```text
WorkPlan               8b0996a65a513ee16a68cab39ef62d66ec9b076fee214a9e158f4b864448d54c
DelegatedWork           660a82e4badfa4bfc9a90a9ed36e1e1b5cafc1c172c79fd0252a3a590292c64b
DelegatedWorkHandoff    a0375ee355da896938abd2cd862d4ffe8b07c4b2896d1ce7de0c415c83469a1f
WorkerResult            6369f754f3c56c1ccbf175bc3193ce19582ef4c46aa62b238a47562316bc2b79
```

The M1.5b golden fixture additionally freezes the component identities for delegated scope/context/capability allowance/constraint/deliverable, handoff attribution, result attribution/material, and WorkerNeed. The same full test suite continues to execute all earlier M1 frozen identities.

M1.5 deliberately does not introduce concrete Capability Catalog / Match / Availability / Governance / Authorization records, executable capability handoffs, Attempt / Outcome / generic Continuation state, retry/fallback/compensation, Worker progress/cancellation/transport/registry/scheduling, nested delegation, generic Observation admission, persistence, or Codexia integration. Capability/Governance references are M1.6; Attempt/Outcome/Continuation is M1.7.