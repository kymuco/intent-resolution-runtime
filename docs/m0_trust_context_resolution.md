# M0.2 — Trust, Context & Resolution Semantics

Status: **normative for M0.2**.

This document freezes how Intent Resolution Runtime (IRR) may know, interpret, and resolve intent. It extends the M0.1 product charter without introducing runtime code, exact schemas, persistence, or executable authority.

M0.2 governs epistemic trust, explicit bounded context, ambiguity, assumptions, information needs, temporal grounding, and admission of resolved semantics.

It does **not** grant authority and it does **not** define execution.

```text
knowledge != authority
trust != permission
resolution != approval
```

## 1. Resolution input boundary

The conceptual path is:

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

IRR MUST resolve only from material explicitly admitted through its Host boundary plus attributable continuation inputs belonging to the same intent lineage.

IRR MUST NOT silently widen that boundary merely because additional information would be useful.

## 2. Epistemic trust is separate from authority

M0.2 uses **trust** only in the epistemic sense: what evidence supports a claim, attribution, or observation and what conclusions that evidence can justify.

Epistemic trust MUST NOT be interpreted as permission, consent, authorization, or execution authority.

```text
verified origin attribution != permission
trusted context source      != permission
high-confidence claim       != authorization
```

Governance remains the authority boundary defined by M0.1.

## 3. Claims, attribution, and evidence

A **Claim** is semantic content presented as describing some fact, state, identity, relation, preference, constraint, or other proposition relevant to resolution.

An **Attribution** states who or what is presented as the source of a claim, request, observation, or context item.

**Evidence** is attributable material that supports or weakens a Claim or Attribution.

IRR MUST preserve the distinction between:

```text
claim
attribution of that claim
evidence for the attribution
evidence for the claim itself
```

Evidence that establishes one layer MUST NOT silently establish another.

For example, a cryptographic signature may verify who signed a payload. It does not automatically prove that every descriptive statement inside the payload is factually correct, and it grants no authority for requested effects.

## 4. Evidentiary status and trust amplification

M0.2 does not freeze a concrete trust enum, score, cryptographic mechanism, or identity provider. It freezes the semantics any later representation must preserve.

Evidence may conceptually be self-asserted, Host-attested, externally verified, or supported by another attributable mechanism.

Any evidentiary status MUST be:

- attributable to its evidence source;
- scoped to what the evidence actually supports;
- explicit rather than silently inferred;
- preserved when material to resolution;
- incapable of granting authority by itself.

IRR MUST NOT perform trust amplification.

```text
verified A        != verified B
trusted source A  != trusted source B
verified identity != verified payload truth
verified payload  != permission
```

Trust MUST NOT propagate transitively merely because two claims, identities, sources, or context items are related.

## 5. Origin attribution and verification

M0.1 froze:

```text
origin attribution != origin verification
```

M0.2 makes that distinction operationally normative.

An Origin value supplied to IRR is an Attribution. Evidence may strengthen or weaken that attribution, but IRR MUST NOT silently upgrade it into verified identity.

Lack of verification does not make an attribution unusable. IRR MAY use an explicitly attributed but unverified Origin when verification is not material to the semantic path, provided the evidentiary status is not strengthened or hidden.

If Origin verification is material and sufficient evidence is absent, IRR MUST preserve the uncertainty or represent the required information need rather than fabricate verification.

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

The Host may supply material directly or supply explicit references whose resolution is handled outside IRR.

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

If additional material is required, IRR represents a bounded information or observation need and waits for attributable input through the Host boundary.

## 7. Context references are not retrieval authority

A **Context Reference** identifies possible material. It does not itself authorize retrieval or disclosure.

```text
reference != retrieval authority
reference != disclosure authority
```

If the Host supplies only a reference whose content is not present, IRR MUST treat the referenced content as unavailable. A system outside IRR may later resolve that reference under its own applicable authority and re-admit the resulting material through the Host boundary as attributable Context or, when semantically appropriate, as an Observation.

Reference resolution does not by itself determine semantic classification: retrieved material is not automatically an Observation merely because it was fetched after a reference was supplied.

IRR MUST NOT reinterpret a reference as permission to fetch from a filesystem, repository, browser, network service, memory store, account, or worker.

Exact reference and context-envelope schemas remain deferred.

## 8. Context provenance

Material context used for resolution MUST retain enough attributable provenance to distinguish sources when those distinctions affect trust, ambiguity, conflict, freshness, or resolution.

M0.2 does not require a particular provenance schema or digest algorithm.

A provider-generated summary, human statement, worker report, Host assertion, and external observation may all be context. They are not automatically equivalent evidence.

IRR MUST NOT collapse materially distinct sources into an unattributed pool of facts.

## 9. Context availability is not provider disclosure

Context admitted to IRR is not automatically authorized for disclosure to a Cognitive Provider.

```text
context available to IRR != context authorized for provider disclosure
```

This distinction applies whether a provider is local or remote.

A future provider boundary MUST receive only context explicitly permitted for that boundary. M0.2 does not freeze the provider API, disclosure schema, or policy mechanism; M0.7 freezes the Cognitive Provider boundary in more detail.

IRR MUST NOT infer disclosure permission merely from context availability, relevance, or trust level.

## 10. Context does not become memory automatically

Context is resolution input, not canonical memory ownership.

IRR MUST NOT silently persist caller-supplied context as durable canonical memory merely because it was useful during resolution.

Later persistence contracts may retain bounded runtime state, lineage, references, receipts, or digests, but canonical memory ownership remains outside M0.2.

## 11. Absence, completeness, uncertainty, and negation

In an ordinary incomplete context boundary, absence of information is not evidence that the opposite proposition is true.

```text
not present  != false
not observed != did not happen
not verified != false
unknown      != denied
```

However, attributable evidence may explicitly assert that an observation is **complete within a bounded domain**. In that case, absence inside that declared complete scope may support a negative conclusion only within that same scope.

Example:

```text
complete listing of D:\Backups at observation T
contains no foo.zip
```

may support:

```text
foo.zip was absent from that bounded listing at T
```

It does not prove that `foo.zip` never existed elsewhere, was not created later, or is globally absent.

Therefore:

```text
absence in unspecified/incomplete context != negation
absence in explicitly complete bounded evidence may support scoped negation
```

IRR MUST NOT infer completeness merely because a result set looks exhaustive.

## 12. Temporal basis and freshness

Relative or time-sensitive semantics require an attributable **Temporal Basis** when time changes their meaning.

Examples include:

- `today`;
- `latest`;
- `current`;
- `just downloaded`;
- `running now`;
- `most recent`.

IRR MUST NOT silently use an ambient machine clock, local timezone, or execution-time clock as semantic truth when the relative time basis is material.

The Host may explicitly supply a resolution time, timezone, sequence marker, observation timestamp, or another bounded temporal reference. Exact timestamp and clock schemas are deferred.

IRR MUST NOT silently treat an undated observation as current, or an old item as current, when freshness could materially change resolution.

A timestamp or sequence marker is evidence about time only within its stated provenance and scope.

This preserves deterministic replay: the same admitted semantic inputs should not change meaning merely because replay happens later on another machine.

## 13. Conflicting context and precedence

Two attributable sources may disagree.

IRR MUST NOT resolve a material Conflict by silently choosing whichever source it prefers unless an explicit bounded precedence rule admitted through the Host boundary already governs that conflict.

If competing claims could materially change resolution, IRR MUST:

- preserve the Conflict;
- apply an explicit admissible precedence rule if one exists; or
- request clarification or additional attributable information.

There is no universal M0.2 rule that:

```text
human beats worker
newer beats older
verified beats unverified
Host beats context
```

for every semantic claim.

This is deliberate: verified provenance does not necessarily verify payload truth, and recency does not necessarily imply correctness.

An unresolved material Conflict that can change the next bounded path blocks `ResolvedIntent` admission.

## 14. Intent statements and descriptive world claims

An IntentRequest may contain both desired semantics and descriptive Claims about the world.

Example:

```text
"Send my latest report to Ivan."
```

The request expresses desired work, but `my latest report` and `Ivan` are referential semantics that may still require bounded contextual resolution.

IRR MUST NOT treat the existence, identity, location, uniqueness, or freshness of a referenced resource as established fact merely because the desired action mentions it.

Likewise, a current IntentRequest may supersede an earlier preference only where its semantics actually express that change. M0.2 defines no hidden universal precedence over prior context.

## 15. Material Ambiguity

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

An Assumption is admissible only when getting it wrong cannot silently choose between materially different meanings under the Material Ambiguity definition.

An Assumption MUST NOT invent or choose:

- a resource identity;
- a recipient;
- a disclosure destination;
- a mutation target;
- an executable target;
- authority, consent, or permission;
- verified identity or trust status;
- a material cost or external commitment.

Presentation-only or otherwise non-material choices may be assumptions when explicitly recorded.

```text
assumption:
    presentation ordering = newest first
```

A hidden default is not an Assumption contract.

```text
assumption != hidden default
assumption != established fact
```

If a caller explicitly directs IRR to use a rule that would otherwise have been an unsafe guess, that direction becomes admitted intent/context semantics rather than a hidden IRR assumption. The rule itself must still be explicit and bounded.

## 17. Explicit selection rules and Late Binding

A bounded selection rule supplied by the IntentRequest or admitted context is distinct from an Assumption.

For example:

```text
"use the newest backup by modification time"
```

may define an explicit semantic rule even though the concrete artifact is not yet known.

A future observation may provide the value required to apply that rule. M0.4 freezes the exact Late Binding and dataflow mechanics.

If applying the rule later exposes a tie or new material choice not resolved by the rule, IRR MUST return to continuation or clarification.

## 18. Information and Observation Needs

When admitted context is insufficient, IRR may represent a bounded **Information Need** or **Observation Need** describing what information is required to continue.

An information need is not authority to acquire that information.

```text
need for information != permission to observe
observation need      != execution authority
```

IRR only describes the semantic need. External orchestration may route that need; Governance may authorize any required effect; an Executor or Worker may perform an authorized bounded observation. Those roles MUST NOT be collapsed into IRR merely because the information is needed for resolution.

Returned information becomes usable by IRR only when it re-enters through an attributable continuation boundary.

M0.2 does not freeze an `InformationNeed`, `ObservationNeed`, or observation-request schema.

## 19. Observation semantics

An **Observation** is attributable information supplied back to IRR from an external boundary or prior bounded step.

Observation does not become truth merely because an external system produced it.

IRR MUST retain material provenance, completeness claims, temporal basis, and evidentiary limitations of observations used for continuation.

A Cognitive Provider's ordinary output remains CandidateResolution material under the provider boundary; it is not silently reclassified as an Observation. If provider-produced material later enters as Context or Observation, that classification and provenance must be explicit through the Host boundary.

An Observation may:

- satisfy an information need;
- bind a previously explicit selection rule;
- provide complete bounded evidence;
- expose a contradiction;
- expose new Material Ambiguity;
- leave the original uncertainty unresolved.

If an Observation exposes a new unresolved material choice, IRR MUST return to clarification or another explicit resolution path before admitting a successor ResolvedIntent.

## 20. Resolution admission

A `ResolvedIntent` may be admitted only when the semantics required for its next bounded path are sufficiently determined.

At minimum, admission MUST preserve these properties:

1. Material Ambiguity blocking the next bounded path has been addressed.
2. Material assumptions are not hidden; only admissible explicit assumptions are used.
3. Material context provenance and evidentiary limitations are not silently erased.
4. Any unresolved Conflict that could materially change the next bounded path blocks admission; non-blocking unresolved Conflict remains explicit.
5. Missing information is not invented.
6. Absence is not rewritten as negation without complete bounded evidence supporting that conclusion.
7. Temporal semantics are grounded when time is material.
8. Trust is not rewritten as authority.
9. Resolution does not imply approval, authorization, or effect.

A ResolvedIntent may still contain uncertainty or Conflict that does not block its next bounded path. Such uncertainty or Conflict MUST remain explicit when material to interpretation, user understanding, or downstream planning.

## 21. Non-operational resolution and pause

A resolution path may complete or pause without operational work.

Examples include:

- answer-only resolution;
- determination that no operational work is required;
- explanation of unresolved uncertainty;
- a Clarification request that pauses the current resolution path pending attributable continuation input.

A Clarification request is not a ResolvedIntent and does not by itself terminate the parent intent lifecycle.

IRR MUST NOT manufacture a WorkPlan merely to make every resolution path look operational.

Exact pause, continuation, and terminal resolution schemas remain deferred.

## 22. Cognitive Provider trust boundary

A Cognitive Provider may propose interpretation, Claims, Assumptions, or candidate semantics.

Provider output remains candidate material.

IRR MUST NOT treat model confidence, fluent language, provider identity, or provider reputation as proof of factual truth, permission, or verified provenance.

Provider-introduced semantic material not supported by admitted context may be represented as an explicit candidate inference or Assumption only when allowed by later contracts; it MUST NOT be silently promoted into established context.

Exact provider validation and APIs belong to M0.7 and M3.

## 23. No hidden semantic repair

IRR MUST NOT silently repair a request by inventing missing referents, recipients, paths, identities, credentials, scopes, resources, temporal facts, or authority.

Useful intent completion does not justify semantic fabrication.

When a missing detail is material, IRR clarifies or represents a bounded information need.

When a missing detail is non-material, IRR may use an explicit admissible Assumption.

## 24. M0.2 exclusions

M0.2 intentionally does NOT freeze:

- Python classes, enums, or serialization schemas;
- exact context-envelope fields;
- exact evidence or trust-level enums;
- cryptographic verification algorithms;
- identity-provider integrations;
- canonical provenance or digest formats;
- persistence or runtime state machines;
- exact clarification, pause, continuation, or terminal-resolution schemas;
- `InformationNeed`, `ObservationNeed`, or observation-request schemas;
- clock or timestamp wire formats;
- Late Binding dataflow mechanics;
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
3. A Context Reference does not grant retrieval or disclosure authority, and externally resolved reference content may re-enter as attributable Context without being forced into Observation semantics.
4. Context availability does not imply Cognitive Provider disclosure permission.
5. Claim, Attribution, Evidence, factual truth, and authority remain distinct.
6. Evidence is scoped and cannot silently amplify trust across unrelated claims.
7. Origin attribution is not automatically Origin Verification.
8. Unverified attribution may remain usable when verification is not material, without being strengthened.
9. Verified identity or trusted context never grants permission.
10. Absence in incomplete context is not negation.
11. Explicitly complete bounded evidence may support only correspondingly scoped negative conclusions.
12. Relative temporal semantics require an attributable Temporal Basis when time is material.
13. IRR does not silently use ambient wall-clock state as semantic truth.
14. Material conflicting context cannot be resolved by an implicit global precedence rule.
15. An unresolved Conflict that can materially change the next bounded path blocks `ResolvedIntent` admission.
16. Material Ambiguity blocks `ResolvedIntent` admission.
17. Assumptions are explicit and cannot choose materially different meanings.
18. Missing material information becomes clarification or a bounded information need rather than fabrication.
19. An information need does not collapse orchestration, Governance, and observation execution into IRR.
20. Observation is attributable data, not automatic truth or authority.
21. Cognitive Provider output is not silently reclassified as Observation.
22. Clarification pauses rather than silently terminating the parent intent lifecycle.
23. `ResolvedIntent` admission preserves provenance, uncertainty, conflicts, temporal basis, completeness, and trust limitations material to the next bounded path.
24. Non-operational intents do not require a WorkPlan.
25. No implementation code or premature M1 schema is introduced.
