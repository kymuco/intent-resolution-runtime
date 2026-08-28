# M0.2 — Trust, Context & Resolution Semantics

Status: **normative for M0.2**.

This document freezes how Intent Resolution Runtime (IRR) may know, interpret, and resolve intent. It extends the M0.1 product charter without introducing runtime code, exact schemas, persistence, or executable authority.

M0.2 governs epistemic trust, explicit bounded context, ambiguity, assumptions, information needs, and admission of resolved semantics.

It does **not** grant authority and it does **not** define execution.

```text
knowledge != authority
trust != permission
resolution != approval
```

## 1. Resolution input boundary

The conceptual resolution path is:

```text
IntentRequest
      |
      v
explicit bounded context
      |
      v
interpretation
      |
      v
ambiguity / conflict analysis
      |
      +-------------------------+
      |                         |
      v                         v
clarification /            ResolvedIntent
information need
```

IRR MUST resolve only from material explicitly admitted through its Host boundary plus attributable continuation inputs already belonging to the same intent lineage.

IRR MUST NOT silently widen that boundary because additional information would be useful.

## 2. Epistemic trust is separate from authority

M0.2 uses **trust** only in the epistemic sense: what evidence supports a claim, attribution, or observation and what conclusions that evidence can justify.

Epistemic trust MUST NOT be interpreted as permission, consent, authorization, or execution authority.

Examples:

```text
verified origin attribution != permission
trusted context source      != permission
high-confidence claim       != authorization
```

A Host may provide strong evidence that an IntentRequest originated from a particular human. That evidence can support provenance. It cannot authorize a filesystem mutation, external disclosure, process launch, or any other effect.

Governance remains the authority boundary defined by M0.1.

## 3. Claims, attribution, and evidence

A **Claim** is semantic content presented as describing some fact, state, identity, relation, preference, constraint, or other proposition relevant to resolution.

An **Attribution** states who or what is presented as the source of a claim, request, observation, or context item.

**Evidence** is attributable material that supports or weakens a claim or attribution.

IRR MUST preserve the distinction between:

```text
claim
attribution of that claim
evidence for the attribution
evidence for the claim itself
```

Evidence that proves one layer MUST NOT silently prove another layer.

For example, a cryptographic signature may strongly verify that a particular principal signed a payload. That does not by itself prove that every descriptive statement inside the payload is factually correct, nor does it grant permission for requested effects.

## 4. Evidentiary status

M0.2 does not freeze a concrete enum, score, or cryptographic mechanism. It freezes the semantics any later representation must preserve.

Evidence may conceptually be self-asserted, Host-attested, externally verified, or supported by another attributable mechanism. Later schemas may represent these differently.

Any evidentiary status MUST be:

- attributable to its evidence source;
- scoped to the claim or attribution it actually supports;
- explicit rather than silently inferred;
- preserved when material to downstream resolution;
- incapable of granting authority by itself.

IRR MUST NOT perform trust amplification.

In particular:

```text
verified A        != verified B
trusted source A  != trusted source B
verified identity != verified payload truth
verified payload  != permission
```

Trust MUST NOT propagate transitively merely because two claims, identities, or context items are related.

## 5. Origin attribution and verification

M0.1 froze:

```text
origin attribution != origin verification
```

M0.2 makes that distinction operationally normative.

An Origin value supplied to IRR is an attribution. Evidence may strengthen or weaken confidence in that attribution, but IRR MUST NOT silently upgrade an attribution into verified identity.

If origin verification is material to a resolution and sufficient evidence is absent, IRR MUST represent that uncertainty or information need rather than fabricate verification.

Even verified Origin remains provenance, not authority.

## 6. Explicit bounded context

IRR has no ambient semantic context.

Context available to IRR MUST be:

```text
caller-supplied
explicit
bounded
attributable
```

The Host boundary may provide content directly or provide explicitly governed references whose resolution is handled outside IRR. Merely mentioning or referencing a resource does not grant IRR ambient retrieval authority.

IRR MUST NOT independently:

- scan a home directory;
- scan a project or repository;
- read HDE or another memory store;
- inspect a browser or desktop;
- search local files;
- query GitHub or another service;
- inspect accounts or devices;
- follow arbitrary links or references;
- widen a supplied filesystem, repository, account, or network scope.

If additional material is required, IRR represents an information or observation need and waits for attributable input through the Host boundary.

## 7. Context references are not retrieval authority

A context reference identifies material; it does not itself authorize retrieval or disclosure.

```text
reference != retrieval authority
reference != disclosure authority
```

If a Host supplies only a reference whose content is not present, IRR MUST treat the referenced content as unavailable unless an external bounded observation later supplies it.

IRR MUST NOT reinterpret a reference as permission to fetch from a filesystem, repository, browser, network service, memory store, or worker.

Exact reference and context-envelope schemas remain deferred.

## 8. Context provenance

Material context used for resolution MUST retain enough attributable provenance to distinguish where material semantic claims came from.

M0.2 does not require a particular provenance schema or digest algorithm, but later representations MUST be able to avoid collapsing materially different sources into an unattributed pool of facts.

A provider-generated summary, human statement, worker report, Host assertion, and external observation may all be context. They are not automatically equivalent evidence.

IRR MUST NOT erase source distinctions when those distinctions affect ambiguity, trust, conflict, or resolution.

## 9. Context availability is not provider disclosure

Context admitted to IRR is not automatically authorized for disclosure to a Cognitive Provider.

```text
context available to IRR != context authorized for provider disclosure
```

This distinction applies whether the Cognitive Provider is local or remote.

A future provider boundary MUST receive only context explicitly permitted for that boundary. M0.2 does not freeze the provider API, disclosure schema, or policy mechanism; M0.7 freezes the Cognitive Provider boundary in more detail.

IRR MUST NOT infer disclosure permission merely from context availability, relevance, or trust level.

## 10. Context does not become memory automatically

Context is resolution input, not canonical memory ownership.

IRR MUST NOT silently persist caller-supplied context as durable canonical memory merely because it was useful during resolution.

Later persistence contracts may retain lineage, references, receipts, or bounded runtime state, but canonical memory ownership remains outside the M0.2 boundary.

## 11. Absence, uncertainty, and negation

Absence of information is not evidence that the opposite proposition is true.

```text
not present != false
not observed != did not happen
not verified != false
unknown != denied
```

IRR MUST represent relevant unknowns as unknowns.

For example, if bounded context contains no recipient named Ivan, IRR cannot conclude that Ivan does not exist. It can only conclude that the supplied context does not resolve the referent.

If a material claim cannot be established from admitted context and evidence, IRR MUST preserve the uncertainty or request the information needed to continue.

## 12. Freshness and temporal claims

Time-sensitive claims require attributable temporal context when freshness changes their meaning.

IRR MUST NOT silently treat an undated observation as current, or an old context item as current, when that distinction could materially change resolution.

Examples include:

- `latest backup`;
- `current branch`;
- `today's report`;
- `the running process`;
- `the file I just downloaded`.

A timestamp or sequence marker is evidence about time only within its stated provenance and scope. Exact timestamp formats and freshness policies are deferred.

## 13. Conflicting context

Two attributable sources may disagree.

IRR MUST NOT resolve a material conflict by silently choosing the source it prefers unless an explicit, bounded precedence rule supplied through the Host boundary already governs that conflict.

If competing claims could materially change the resolution, IRR MUST:

- preserve the conflict;
- apply an explicit admissible precedence rule if one exists; or
- request clarification / additional attributable information.

There is no universal M0.2 rule that "human beats worker", "newer beats older", "verified beats unverified", or "Host beats context" for all semantic claims.

Evidence strength, freshness, source role, and explicit caller rules may matter, but they do not create an implicit global precedence order.

## 14. Intent statements and descriptive world claims

An IntentRequest may contain both desired semantics and descriptive claims about the world.

Example:

```text
"Send my latest report to Ivan."
```

The request expresses desired work, but it also contains referential claims such as `my latest report` and `Ivan` that may require contextual resolution.

IRR MUST NOT treat the existence, identity, location, or uniqueness of referenced resources as true merely because the desired action mentions them.

Likewise, a current intent statement may supersede an earlier preference only where the semantics actually express that change. M0.2 defines no universal hidden precedence for all prior context.

## 15. Material ambiguity

A **Material Ambiguity** exists when competing interpretations could materially change any of the following:

- resource identity;
- recipient or destination;
- scope;
- disclosure;
- mutation;
- executable target;
- cost or externally meaningful commitment;
- external effect;
- authority-relevant identity or trust interpretation.

Material Ambiguity blocks admission of a ResolvedIntent.

IRR MUST NOT guess through Material Ambiguity.

Examples:

```text
"Send Ivan the file."
```

Two plausible Ivans with no explicit selection rule require clarification.

```text
"Launch it."
```

Multiple plausible referents require clarification.

```text
"Delete the old backup."
```

If `old` has no explicit or contextually unique rule, IRR cannot choose an artifact arbitrarily.

## 16. Assumptions

An **Assumption** is an explicit premise used to continue resolution without claiming that the premise is established fact.

Assumptions MUST be visible and attributable to the resolution that uses them.

An assumption is admissible only when getting it wrong cannot silently choose between materially different meanings under the Material Ambiguity definition.

An assumption MUST NOT be used to invent or choose:

- a resource identity;
- a recipient;
- a disclosure destination;
- a mutation target;
- an executable target;
- authority, consent, or permission;
- verified identity or trust status;
- a material cost or external commitment.

Presentation-only or otherwise non-material choices may be assumptions when explicitly recorded.

Example:

```text
assumption:
    presentation ordering = newest first
```

A hidden default is not an assumption contract.

```text
assumption != hidden default
assumption != established fact
```

## 17. Explicit selection rules versus assumptions

A bounded selection rule supplied by the IntentRequest or admitted context is not the same thing as an assumption.

For example:

```text
"use the newest backup by modification time"
```

may define an explicit semantic rule even though the concrete artifact is not known yet.

The future concrete value may be supplied through observation and late binding. The rule itself must already be unambiguous.

M0.4 freezes exact late-binding and observation mechanics.

If applying the rule later exposes a tie or new material choice not resolved by the rule, IRR MUST return to continuation or clarification.

## 18. Information and observation needs

When admitted context is insufficient, IRR may represent a bounded **Information Need** or **Observation Need** describing what information is required to continue.

An information need is not authority to acquire that information.

```text
need for information != permission to observe
observation request     != execution authority
```

The Host, Governance, Executor, Worker, or another external system may later decide how or whether the information is obtained.

Returned information becomes usable by IRR only when it re-enters through an attributable continuation boundary.

M0.2 does not freeze an `InformationNeed` or `ObservationRequest` schema.

## 19. Observation semantics

An Observation is attributable information supplied back to IRR from an external boundary or prior bounded step.

Observation does not become truth merely because a tool, worker, Host, or model produced it.

IRR MUST retain relevant provenance and evidentiary limitations of observations used for continuation.

An observation may:

- satisfy an information need;
- bind a previously explicit selection rule;
- expose a contradiction;
- expose new Material Ambiguity;
- leave the original uncertainty unresolved.

If an observation exposes a new unresolved material choice, IRR MUST return to clarification or another explicit resolution path before admitting a successor ResolvedIntent.

## 20. Resolution admission

A `ResolvedIntent` may be admitted only when the semantics required for its next bounded path are sufficiently determined.

At minimum, the resolution MUST preserve these properties:

1. Material Ambiguity blocking the next bounded path has been addressed.
2. Material assumptions are not hidden; only admissible explicit assumptions are used.
3. Material context provenance and trust limitations are not silently erased.
4. Material conflicts are resolved by an explicit rule or remain unresolved.
5. Missing information is not invented.
6. Absence is not rewritten as negation.
7. Trust is not rewritten as authority.
8. Resolution does not imply approval, authorization, or effect.

A ResolvedIntent may still contain uncertainty that does not block its next bounded path. That uncertainty MUST remain explicit when it is material to interpretation, user understanding, or downstream planning.

## 21. Non-operational resolution

Resolution may terminate without operational work.

Examples include:

- answer-only resolution;
- determination that no operational work is required;
- explanation of unresolved uncertainty;
- a request for clarification before a ResolvedIntent exists.

IRR MUST NOT manufacture a WorkPlan merely to make every resolution look operational.

Exact terminal resolution schemas remain deferred.

## 22. Cognitive Provider trust boundary

A Cognitive Provider may propose interpretation, claims, assumptions, or candidate semantics.

Provider output remains candidate material.

IRR MUST NOT treat model confidence, fluent language, provider identity, or provider reputation as proof of factual truth, permission, or verified provenance.

If provider output introduces a claim not supported by admitted context or explicit reasoning assumptions, that claim MUST NOT be silently promoted into established context.

Exact provider validation and APIs belong to M0.7 and M3.

## 23. No hidden semantic repair

IRR MUST NOT silently repair a request by inventing missing referents, recipients, paths, identities, credentials, scopes, resources, or authority.

Useful intent completion does not justify semantic fabrication.

When a missing detail is material, IRR clarifies or represents the bounded information need.

When a missing detail is non-material, IRR may use an explicit admissible assumption.

## 24. M0.2 exclusions

M0.2 intentionally does NOT freeze:

- Python classes, enums, or serialization schemas;
- exact context-envelope fields;
- exact evidence or trust-level enums;
- cryptographic verification algorithms;
- identity-provider integrations;
- canonical provenance or digest formats;
- persistence or runtime state machines;
- exact clarification or terminal-resolution schemas;
- `InformationNeed`, `ObservationNeed`, or observation request schemas;
- late-binding dataflow mechanics;
- WorkPlan or WorkStep schemas;
- Capability Catalog schemas;
- Governance policy or consent rules;
- Cognitive Provider APIs or disclosure-policy schemas;
- execution or worker adapters;
- retry or recovery algorithms.

Those belong to later milestones. M0.2 freezes the semantic constraints those mechanisms must preserve.

## 25. Acceptance criteria

M0.2 is complete when the repository states unambiguously that:

1. IRR has no ambient semantic context.
2. Context must be caller-supplied, explicit, bounded, and attributable.
3. A reference does not grant retrieval or disclosure authority.
4. Context availability does not imply Cognitive Provider disclosure permission.
5. Claim, attribution, evidence, factual truth, and authority remain distinct.
6. Evidence is scoped and cannot silently amplify trust across unrelated claims.
7. Origin attribution is not automatically Origin verification.
8. Verified identity or trusted context never grants permission.
9. Absence of information is not negation.
10. Material temporal claims preserve freshness uncertainty.
11. Material conflicting context cannot be resolved by an implicit global precedence rule.
12. Material Ambiguity blocks `ResolvedIntent` admission.
13. Assumptions are explicit and cannot choose materially different meanings.
14. Missing material information becomes clarification or a bounded information need rather than fabrication.
15. Observation is attributable data, not automatic truth or authority.
16. `ResolvedIntent` admission preserves provenance, uncertainty, conflicts, and trust limitations material to the next bounded path.
17. Non-operational intents do not require a WorkPlan.
18. No implementation code or premature M1 schema is introduced.
