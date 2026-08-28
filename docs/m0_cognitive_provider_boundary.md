# M0.7 — Cognitive Provider Boundary

Status: **normative for M0.7**.

This document freezes how Intent Resolution Runtime (IRR) may use a Cognitive Provider such as an LLM, deterministic resolver, Organism-derived resolver, or hybrid resolver without allowing provider output to become ambient context, factual truth, authority, capability existence, or final IRR state by implication.

It extends M0.1 Product Charter & Vocabulary, M0.2 Trust/Context/Resolution Semantics, M0.3 Intent → Work Boundary, M0.4 Late Binding & Observation Boundary, M0.5 Capability Boundary, and M0.6 Governance & Authority Boundary without introducing runtime code, exact Python schemas, prompt templates, model SDKs, tool adapters, worker delegation, retry algorithms, or an organism_lab dependency.

M0.7 answers one question:

> How may replaceable cognitive systems propose useful intent semantics while IRR remains the owner of validation, admission, lineage, capability correctness, and the boundary between proposed cognition and externally authorized effects?

The answer is:

> **A Cognitive Provider proposes attributable candidate semantics from an explicitly disclosed bounded input surface. IRR validates and admits only semantics that satisfy the frozen IRR contracts. Provider output is never final state, truth, permission, or effect merely because a provider produced it.**

```text
IntentRequest + admitted IRR material
               |
               v
      Provider Disclosure Boundary
               |
               v
      Provider Input Envelope
               |
               v
        Cognitive Provider
       /       |        \
     LLM   Deterministic  Organism-derived
       \       |        /
               v
       CandidateResolution
               |
               v
          IRR Admission
      /---------+----------\
     v          v           v
 admitted   clarification  rejected /
 semantics  / info need    not admitted
     |
     v
ResolvedIntent / bounded successor semantics
```

The central invariants are:

```text
provider proposes != IRR admits
CandidateResolution != ResolvedIntent
provider output != Context by default
provider output != Observation by default
provider confidence != factual truth
provider confidence != admission authority
provider recommendation != Governance Decision
provider identity != trust amplification
provider tool access != ambient IRR observation
provider retrieval != admitted evidence by default
provider disclosure != context availability
model prior != admitted Evidence
private reasoning != IRR evidence
same prompt != same candidate by default
provider failure != intent invalidity
```

## 1. Cognitive Provider is a replaceable semantic dependency

A `Cognitive Provider` is a component that proposes interpretation or candidate resolution semantics to IRR.

Conceptual provider implementations may include:

```text
LLMResolver
DeterministicResolver
OrganismResolver
HybridResolver
```

IRR MUST NOT make its public semantic contract depend on one provider family, one model vendor, one prompt format, one organism_lab internal representation, or one provider-specific hidden state.

```text
provider implementation != IRR semantic contract
```

## 2. IRR owns admission and final runtime semantics

A Cognitive Provider does not own final IRR state.

The provider may propose candidate semantics, but IRR owns the admission boundary that determines whether those semantics become part of an admitted resolution path.

```text
Cognitive Provider -> CandidateResolution
CandidateResolution -> IRR admission
IRR admission -> admitted semantics
```

The provider MUST NOT directly mint a `ResolvedIntent`, `WorkPlan`, `Authorization`, `Observation`, `Outcome`, or Effect that bypasses the corresponding IRR boundary.

A future API may allow provider output to use structurally similar candidate representations, but semantic ownership remains separate.

## 3. CandidateResolution

A `CandidateResolution` is attributable provider-produced semantic material offered to IRR for validation and possible admission.

Conceptually it may propose:

- intent interpretation;
- referent interpretation;
- relevant Claims or candidate inferences;
- explicit Assumptions;
- identified Material Ambiguity or Conflict;
- Clarification proposals;
- Information Need or Observation Need proposals;
- candidate non-operational resolution semantics;
- candidate operational semantics;
- candidate Semantic Operations or bounded work structure;
- references to explicitly disclosed capability information;
- material uncertainty and confidence metadata.

Exact fields and wire schemas are deferred to M1/M3.

```text
CandidateResolution != ResolvedIntent
CandidateResolution != WorkPlan
CandidateResolution != Authorization
```

## 4. Candidate material remains attributable to the provider

Provider-produced material MUST retain enough provenance to identify that it originated from a provider rather than from the Principal, Origin, Host, Context source, Observation source, Governance boundary, Executor, or Worker.

Attribution MUST NOT be silently rewritten.

For example, a provider inference:

```text
"Ivan probably means Ivan Petrov"
```

must not become:

```text
user said Ivan Petrov
```

or:

```text
verified recipient = Ivan Petrov
```

```text
provider inference != user statement
provider inference != verified world fact
```

## 5. Provider Input Envelope

A future `Provider Input Envelope` is the explicitly bounded material disclosed to one Cognitive Provider invocation.

Conceptually it may contain only material deliberately selected for that provider boundary, such as:

```text
IntentRequest or bounded projection
selected Context Items
selected Claims / Evidence summaries with provenance
Temporal Basis when permitted and material
prior admitted resolution lineage when needed
bounded Capability Catalog projection when permitted
explicit task/request for candidate semantics
```

Any projection, redaction, or summary supplied to a provider MUST preserve material source distinctions, uncertainty, completeness/freshness limits, and evidentiary limitations needed for the candidate task. Provider convenience does not permit a lossy projection to be presented as semantically equivalent when omitted material could change the interpretation.

```text
provider projection != uncertainty erasure
provider summary != stronger Evidence
```

Exact fields, canonicalization, IDs, and transport are deferred.

The Provider Input Envelope is not the whole IRR state by default.

```text
IRR state != Provider Input Envelope by default
```

## 6. Provider Disclosure is explicit and bounded

M0.2 remains normative:

```text
context available to IRR != context authorized for Provider Disclosure
```

M0.7 extends this rule to all material crossing the provider boundary.

Availability inside IRR does not by itself authorize disclosure of:

- Context;
- Capability Catalog entries;
- provider/executor identities;
- Authorization material;
- private account or recipient data;
- prior Observations;
- Worker results;
- memory-derived material supplied by a Host;
- other sensitive semantic state.

A provider receives only material explicitly permitted for that boundary.

## 7. Provider Disclosure may itself have external effects

A local provider and a remote provider are semantically interchangeable only where all material boundary semantics are preserved.

Sending Provider Input to a remote model may involve network use or external disclosure.

M0.7 does not classify that disclosure as automatically safe or permitted merely because it occurs during cognition.

```text
reasoning transport != authority exemption
provider invocation != permission to disclose
```

The embedding Host/Governance architecture owns any required authority for provider disclosure effects.

IRR does not grant that authority.

## 8. Local provider does not imply unrestricted disclosure

A provider running locally MAY reduce external disclosure risk, but local execution does not imply that every Context Item, secret, memory item, account datum, or capability descriptor should be disclosed to it.

Provider Disclosure remains explicit even for local providers.

```text
local provider != all-context entitlement
```

## 9. Provider cannot widen its input boundary

The Cognitive Provider contract does not grant authority to discover additional IRR context or machine state.

A provider MUST NOT, merely because it would improve an answer:

- scan files;
- inspect repositories;
- query a browser;
- read memory stores;
- query GitHub;
- inspect accounts;
- contact external services;
- enumerate tools or capabilities outside the disclosed surface;
- acquire authority evidence.

If additional information is required, the candidate may propose a bounded Information Need or Observation Need.

```text
provider needs data != provider may acquire data
```

## 10. Tool-using cognition must not hide retrieval or effects

A provider implementation may technically support tools, retrieval, browsing, plugins, or internal agents.

Those mechanisms MUST NOT be treated as part of the pure Cognitive Provider semantic contract when they acquire new external information or produce external effects.

If provider-side retrieval or action is permitted by a future embedding system, the resulting material must cross an explicit attributable acquisition/Host boundary before IRR may use it as Context, Observation, or other admitted evidence.

```text
provider tool result != admitted Observation by default
provider retrieval != IRR Context by default
```

M0.7 forbids using hidden provider tool access as an ambient-context backdoor around M0.2, M0.5, or M0.6.

## 11. Provider output is not Observation by default

M0.2 remains in force:

```text
provider output != Observation by default
```

A provider may describe the world, infer likely state, or summarize disclosed material. That does not make its output an external Observation.

If provider-produced material later enters IRR as Context or Observation, the Host must classify it explicitly and preserve its provider provenance and evidentiary limitations.

## 12. Provider output is not Context by default

CandidateResolution material does not silently become canonical Context merely because IRR received it.

```text
CandidateResolution != Context by default
```

This prevents iterative self-conditioning from laundering earlier provider guesses into later established premises.

A later provider invocation may receive selected prior candidate material only when the Host/IRR contract explicitly discloses and labels it as such.

## 13. Provider Claims do not become factual truth automatically

A provider may emit Claims about resources, identities, likely meanings, or world state.

IRR MUST preserve the M0.2 evidentiary boundary:

```text
provider claim != factual truth
provider fluency != evidence
```

A materially important world Claim that lacks sufficient admitted Evidence cannot be upgraded merely because the provider expressed it confidently.

## 14. Semantic interpretation is different from inventing world facts

IRR may admit provider-proposed semantic interpretation when it is supported by the admitted IntentRequest and Context and satisfies ambiguity/trust rules.

This does not authorize a provider to invent missing world state.

For example, interpreting:

```text
"send the latest report"
```

as an intent to perform artifact selection plus external sending may be valid semantic interpretation.

Inventing:

```text
latest report = D:\reports\final.pdf
recipient = account 123
```

without admitted evidence is not valid semantic completion.

```text
semantic interpretation != fabricated referent
```

## 15. Candidate Inference

A provider may propose an inference derived from disclosed material, provider-internal/parametric prior knowledge, or both.

Its support MUST remain distinguishable: admitted Context/Evidence may support an inference, while provider-internal prior knowledge remains provider-originated candidate support rather than Host-supplied Context or independently established Evidence.

```text
model prior != admitted Evidence
provider prior != Host Context
```

A material candidate inference MUST remain distinguishable from an established Claim or Observation when its evidentiary status matters.

IRR may use a provider inference only within the support provided by admitted evidence and frozen trust rules. Provider prior may help generate a candidate, but it MUST NOT silently satisfy a material factual choice that requires attributable evidence.

Unsupported factual inference MUST NOT silently satisfy a material resource, recipient, disclosure, mutation, executable, cost, authority, or trust choice.

Exact inference representation is deferred.

## 16. Candidate Assumption remains subject to M0.2

A provider may suggest an explicit Assumption.

The provider does not gain a broader assumption policy than IRR.

A candidate Assumption is admissible only if getting it wrong cannot silently choose between materially different meanings.

```text
provider assumption != permission to guess
```

A provider cannot use an Assumption to fill a recipient, material resource identity, mutation target, executable target, authority, verified identity, material cost, or external-effect choice forbidden by M0.2.

## 17. Provider may identify ambiguity; it cannot erase ambiguity by confidence

A provider may identify competing interpretations and propose Clarification.

If Material Ambiguity remains after admission validation, IRR MUST preserve the ambiguity even when the provider strongly prefers one interpretation.

```text
provider preference != ambiguity resolution
provider confidence != tie-break authority
```

## 18. Provider may propose Clarification and Information Needs

A CandidateResolution may propose:

```text
Clarification
Information Need
Observation Need
```

IRR validates whether the need is actually material and bounded.

The provider proposal itself does not authorize acquisition of the missing information.

```text
provider-proposed Observation Need != observation authority
```

## 19. Provider cannot create authority

M0.6 remains absolute across the provider boundary.

Provider output such as:

```text
"This is safe."
"The user probably approves."
"I recommend proceeding."
"Risk is low."
```

is not Authorization.

```text
provider recommendation != Governance Decision
provider confidence != Authorization
CandidateResolution != Authorization
```

A provider cannot classify conversational approval-like text as executable permission except as candidate semantic material for an external Governance mechanism to evaluate under its own rules.

## 20. Provider cannot create capabilities

A provider may propose use of capability semantics only from the capability material actually disclosed to it.

Even then, provider assertion does not establish Capability Match.

IRR MUST validate required capabilities against the exact authoritative Capability Catalog Snapshot under M0.5.

```text
provider says capability exists != Catalog Membership
provider suggests capability != Capability Match
```

A provider MUST NOT invent a shell/browser/tool fallback when a required capability is missing.

## 21. Catalog projection is not the authoritative Catalog

A provider may receive a bounded projection of the Capability Catalog.

That projection is provider input, not the authoritative capability planning surface.

IRR performs final Capability Match against the exact applicable Catalog Snapshot.

A provider seeing only a projection may therefore legitimately propose incomplete candidate work; IRR must detect missing or incompatible capability requirements rather than expanding the provider view ambiently.

```text
Provider Catalog projection != authoritative Catalog Snapshot
```

## 22. Provider selection does not create capability precedence

If multiple compatible capabilities/providers could implement the same semantic operation, provider preference is not automatically the IRR selection rule.

M0.5 remains in force:

```text
multiple matches != permission for hidden provider preference
catalog order != capability precedence
```

A Cognitive Provider may propose a choice only if admitted semantics already contain the bounded selection basis required for that choice.

## 23. Provider cannot bypass WorkPlan boundedness

A provider may propose operational semantics, but candidate work remains subject to M0.3.

A provider MUST NOT smuggle:

- arbitrary loops;
- unbounded recursion;
- hidden retries;
- self-modifying plans;
- arbitrary embedded code;
- shell fragments as semantic control flow;
- an open-ended observe/decide/act agent loop

into an ordinary WorkStep.

```text
provider-generated plan != scripting authority
provider-generated WorkStep != autonomous-agent exemption
```

Long-form delegated cognition remains M0.8 Worker territory.

## 24. Executable-looking provider output is data until admitted

Provider output may contain shell, SQL, code, URLs, commands, or other executable-looking text.

Such material is candidate data, not execution authority or WorkPlan control flow.

M0.3 remains normative:

```text
executable-looking text != executable authority
executable-looking text != WorkPlan control flow
```

## 25. Candidate references must be validated

A provider may refer to IntentRequest items, Context Items, prior lineage, symbolic values, Capability descriptors, or other disclosed entities.

IRR MUST validate material references against the authoritative admitted inputs.

A provider-generated identifier, path, recipient, resource, capability ID, or lineage reference that does not resolve under admitted semantics MUST NOT be treated as real merely because it has a plausible shape.

```text
provider-mentioned reference != resolved reference
```

Exact reference identity mechanics are deferred.

## 26. Semantics-preserving normalization is allowed

IRR may normalize provider output when normalization does not change material semantic meaning.

Conceptual examples include:

- canonical field ordering;
- equivalent enum spelling under a later schema;
- whitespace/presentation normalization;
- deterministic canonical representation.

```text
normalization != semantic repair
```

If repair would require choosing a new referent, resource, recipient, effect, scope, capability, assumption, or other material meaning, IRR MUST NOT hide that choice as normalization.

## 27. Malformed output does not authorize semantic repair

A CandidateResolution may be malformed, incomplete, internally inconsistent, or incompatible with the current contract.

IRR may reject it, request another candidate, produce a bounded clarification/info path where justified, or otherwise fail closed under later lifecycle contracts.

IRR MUST NOT fabricate material semantics merely to make provider output parse.

```text
malformed candidate != permission to invent missing semantics
```

Exact retry/fallback behavior remains M0.9/M3.

## 28. Partial candidate admission must not change meaning silently

A provider may return a candidate containing both valid and invalid pieces.

IRR MAY admit an independently valid subset only when removing the rejected material cannot materially change the meaning, scope, ambiguity, evidence basis, capability requirements, or authority-relevant surface of what remains.

Otherwise the candidate must remain not admitted as a whole semantic path or return through clarification/re-resolution.

```text
partial parse success != permission to cherry-pick a different intent
```

Exact admission-result schemas are deferred.

## 29. Provider confidence is descriptive metadata only

A provider may emit confidence, probability, ranking, score, or uncertainty metadata.

Such metadata MAY help inspection or orchestration, but it does not establish:

- factual truth;
- evidentiary trust;
- correct Origin;
- ambiguity resolution;
- Capability Match;
- Authorization;
- safety;
- successful effect.

```text
provider confidence != Evidence by default
provider confidence != factual truth
provider confidence != Authorization
```

A numeric score is not assumed calibrated merely because it is numeric.

## 30. Provider identity and reputation do not amplify trust automatically

Provider identity, vendor, model family, local/remote placement, prior benchmark performance, or reputation may be attributable metadata.

They do not silently upgrade candidate Claims into truth or permission.

```text
trusted provider != trusted payload by default
provider reputation != claim verification
```

Any external evidence about provider reliability is itself Evidence with bounded scope under M0.2.

## 31. Provider provenance should be preserved when material

A future CandidateResolution representation SHOULD preserve enough provenance to distinguish material provider execution facts, potentially including:

```text
provider identity / adapter identity
provider version or model identity when material
provider configuration identity when material
request/input-envelope identity
candidate response identity
relevant temporal basis
```

Exact digests, model strings, prompt hashes, seeds, sampling parameters, and cryptographic formats are deferred.

Provider provenance supports inspection and reproducibility analysis; it is not authority.

## 32. Same provider input does not imply identical output

A Cognitive Provider may be nondeterministic.

M0.7 does not require:

```text
same input -> byte-identical candidate
```

unless a specific provider contract explicitly guarantees it.

IRR MUST therefore distinguish provider nondeterminism from admitted semantic identity.

A replay system may preserve the exact candidate that was admitted rather than silently re-querying a provider and pretending the new answer is historical state.

```text
same Provider Input != same CandidateResolution by default
re-query != replay
```

Exact replay/persistence mechanics are deferred.

## 33. Private reasoning is not required for admission

IRR admission MUST depend on inspectable candidate semantics and attributable input/evidence, not on access to a provider's private chain-of-thought or hidden internal reasoning state.

A provider may internally use private reasoning, latent state, or search over already disclosed/internal material. Any mechanism that acquires new external information remains subject to section 10 and is not automatically IRR Evidence or Context.

```text
private reasoning != IRR Evidence
private reasoning != Authorization
internal search != ambient retrieval authority
```

A future provider may optionally expose concise rationale or derivation metadata, but admission cannot require hidden chain-of-thought disclosure.

## 34. Provider rationale does not substitute for provenance

A fluent explanation such as:

```text
"I chose this because it looks newest"
```

does not prove that the underlying evidence actually supports the choice.

IRR validates material references, rules, evidence, and ambiguity against admitted inputs.

```text
provider rationale != evidence provenance
```

## 35. Multiple providers have no implicit universal precedence

IRR may later use zero, one, or multiple Cognitive Providers.

M0.7 does not freeze a universal rule such as:

```text
Organism beats LLM
LLM beats deterministic resolver
majority vote = truth
highest confidence wins
newest provider wins
```

If provider candidates conflict materially, IRR must preserve the conflict or apply an explicit bounded orchestration/admission rule rather than silently selecting by provider identity or confidence.

Exact ensemble/orchestration strategy is deferred to M3 or later.

## 36. Provider disagreement is candidate disagreement, not Context Conflict by default

Two Cognitive Providers may produce incompatible candidates.

Their disagreement is first a disagreement between candidate proposals, not automatically a factual Conflict between admitted Context sources.

If admitted candidate Claims are later used as evidence/context under an explicit boundary, M0.2 Conflict semantics then apply according to their actual classification and provenance.

```text
provider disagreement != admitted Context Conflict by default
```

## 37. Provider fallback must not widen disclosure

If one provider is unavailable or rejects an input, fallback to another provider MUST NOT silently disclose additional Context, Catalog material, account data, or authority material.

A different provider boundary requires its own applicable Provider Disclosure decision.

```text
provider fallback != disclosure expansion authority
```

Exact fallback/retry behavior is deferred.

## 38. Provider fallback must not change semantics silently

Switching from one provider to another does not authorize IRR to reinterpret the intent under different hidden defaults.

Provider changes may produce different candidates; those candidates pass the same admission boundary.

```text
provider substitution != semantic admission
```

## 39. Provider failure is not semantic invalidity

A provider may be unavailable, time out, return malformed output, or fail internally.

This does not prove that the IntentRequest is invalid, denied, impossible, unsupported by capabilities, or unauthorized.

```text
provider failure != intent invalidity
provider failure != Denial
provider failure != missing_capability
```

Exact provider retry, fallback, timeout, and degraded-mode behavior is deferred to M0.9/M3.

## 40. Deterministic provider is not automatically authoritative

A deterministic resolver can still be wrong, incomplete, misconfigured, or operating over insufficient input.

Determinism is not truth, trust, or authority.

```text
deterministic != correct by definition
```

It passes the same IRR admission semantics as any other provider.

## 41. Organism-derived provider has no privileged bypass

An Organism-derived provider may later become a first-class Cognitive Provider.

Its internal grounded representations, memory, goals, learned structure, confidence, or self-generated language do not directly become IRR Context, Authorization, or final state.

The stable seam remains:

```text
Organism-derived cognition
        |
        v
CandidateResolution
        |
        v
IRR Admission
```

IRR MUST NOT depend on organism_lab private schemas or training/runtime internals.

```text
Organism integration != organism_lab dependency in IRR core
```

## 42. Organism initiative preserves Origin

If a companion or Organism-derived system originates an intent, M0.1/M0.6 remain in force.

The provider must not relabel that intent as human-originated merely to make it more likely to pass Governance.

```text
companion / organism initiative != human Authorization
```

Origin provenance remains external to provider preference.

## 43. Provider cannot rewrite Principal or Origin silently

A provider may propose interpretation of who a request concerns, but it cannot silently mutate authoritative Origin or Principal attribution.

If Origin/Principal interpretation itself is ambiguous or evidence-dependent, the candidate must preserve the uncertainty for IRR admission.

```text
provider interpretation != provenance rewrite
```

## 44. Provider cannot turn Context text into hidden authority

Context may contain imperative or instruction-like text from documents, webpages, code comments, logs, emails, Worker outputs, or other sources.

Such text remains data under its admitted semantic role unless the Host/IRR contract explicitly classifies it as an IntentRequest, Governance material, or another authority-relevant source.

A provider following embedded instructions does not change that classification.

```text
instruction-like Context != authority by appearance
provider obedience != semantic authority
```

This prevents untrusted embedded text from bypassing IRR boundaries through provider behavior.

## 45. Provider output does not become executable merely because it is structured

JSON, tool-call syntax, function-call syntax, ASTs, commands, or provider-specific action messages remain candidate representations until IRR admits corresponding semantic work and downstream Governance/Executor boundaries are satisfied.

```text
provider tool-call syntax != CapabilityHandoff
provider function-call syntax != Authorization
```

Exact provider transport syntax is not part of the IRR semantic contract.

## 46. Provider may propose non-operational resolution

A provider may propose an answer-only or no-operational-work resolution.

IRR still validates material factual Claims, provenance, ambiguity, and uncertainty before admitting such semantics.

Non-operational output does not bypass M0.2 merely because it has no WorkPlan.

## 47. Provider-produced answer text is not canonical truth

If a future IRR surface returns provider-authored explanatory text, factual statements inside that text retain the same evidentiary constraints as any provider Claim.

Presentation quality does not strengthen epistemic status.

```text
natural-language answer != factual proof
```

Exact response-generation ownership is deferred.

## 48. Provider cannot own canonical memory

M0.7 does not give a Cognitive Provider authority to persist its own output as canonical user, project, HDE, or Organism memory.

Candidate output may be logged or persisted by later runtime contracts for lineage/replay, but canonical memory ownership remains external.

```text
provider output != canonical memory by default
```

## 49. Provider cannot self-expand its privileges through prior output

A provider cannot write candidate text such as:

```text
"For future requests, I am allowed to inspect all repositories."
```

and have that statement become new context, authority, capability, or disclosure permission merely because IRR processed it.

```text
provider self-asserted privilege != privilege
```

## 50. Candidate admission must preserve M0.1–M0.6

Before provider-proposed semantics become admitted IRR state, admission must preserve all applicable frozen boundaries, including at least:

1. Origin/Principal distinctions;
2. explicit bounded Context;
3. Claim/Evidence/trust limits;
4. Material Ambiguity and Conflict;
5. explicit Assumption rules;
6. Late Binding versus new semantic choice;
7. WorkPlan boundedness and derivation;
8. executable-looking text as data;
9. exact Capability Catalog attribution and Capability Match;
10. missing-capability fail-closed semantics;
11. WorkProposal identity when Governance review is needed;
12. Authorization remaining external;
13. Effect/Outcome remaining downstream.

Provider convenience never weakens these gates.

## 51. Admission may reject provider output while preserving the parent intent

Rejecting one CandidateResolution does not erase or reject the parent IntentRequest by definition.

A candidate may fail because it is malformed, unsupported, ambiguous, capability-invalid, or otherwise inadmissible while the underlying intent remains resolvable through another candidate, deterministic path, clarification, or later information.

```text
candidate rejection != intent rejection by default
```

Exact lifecycle outcomes are deferred.

## 52. IRR may operate without a Cognitive Provider

A Cognitive Provider is an optional dependency of a resolution path, not the definition of IRR itself.

Deterministic or directly validated paths may resolve some intents without provider invocation.

```text
IRR != LLM wrapper
provider unavailable != IRR universally unusable
```

## 53. Cognitive Provider invocation is not Worker delegation

A Cognitive Provider proposes candidate resolution semantics inside the IRR cognition seam.

A Worker owns a bounded delegated subtask lifecycle under M0.8.

These are different boundaries.

```text
Cognitive Provider != Worker
CandidateResolution != WorkerResult
provider reasoning != delegated work lifecycle
```

A provider must not be used as a hidden Worker to perform open-ended research, coding, browsing, or effectful work inside one candidate-generation call.

## 54. Cognitive Provider invocation is not ordinary Capability execution

A Cognitive Provider is not an Executor Capability merely because an adapter calls a model API.

Capability execution concerns downstream operational work; provider cognition concerns candidate resolution semantics.

The transport used to invoke a provider may itself have disclosure/network authority requirements, but that does not collapse the semantic roles.

```text
Cognitive Provider != Executor
provider invocation != WorkStep effect by definition
```

## 55. Stable provider seam, unstable provider internals

M0.7 intentionally freezes the semantic seam before choosing exact provider implementations.

IRR must be able to replace:

```text
LLM A -> LLM B
LLM -> deterministic resolver
LLM -> Organism-derived resolver
single -> hybrid
```

without changing the meaning of IRR's external intent, Context, WorkPlan, Capability, Governance, and effect boundaries.

Provider-specific prompting, tokenization, context windows, embeddings, hidden states, tool schemas, and training methods remain implementation details outside this semantic contract.

## 56. M0.7 exclusions

M0.7 intentionally does NOT freeze:

- Python provider protocols/classes;
- exact `ProviderInputEnvelope` fields;
- exact `CandidateResolution` fields;
- exact admission-result enums;
- prompt templates or system messages;
- model vendors, model IDs, or API SDKs;
- token budgets or context-window algorithms;
- sampling parameters or decoding strategies;
- chain-of-thought storage or exposure;
- embedding/retrieval implementations;
- provider-side tool APIs;
- provider retry/fallback algorithms;
- provider ranking/ensemble algorithms;
- provider caching;
- exact provider provenance digest format;
- disclosure policy implementation;
- encryption, transport security, or secret-store implementation;
- exact response text-generation ownership;
- organism_lab schemas or integration adapters;
- Worker delegation contracts;
- failure/retry/unknown-outcome algorithms;
- runtime persistence schemas;
- M1 Python schemas;
- M3 concrete LLM resolver implementation.

M0.7 freezes provider semantics and admission boundaries, not a model stack.

## 57. Relationship to M0.2 Trust/Context

M0.2 owns what semantic material is admitted to IRR and what Evidence supports Claims.

M0.7 owns what bounded subset may be disclosed to a Cognitive Provider and how provider-produced candidate material returns to IRR.

```text
Context admission != Provider Disclosure
Provider Disclosure != Candidate admission
```

## 58. Relationship to M0.5 Capability Boundary

A provider may reason about disclosed capability semantics, but IRR remains responsible for authoritative Capability Match against the exact applicable Catalog Snapshot.

```text
provider capability proposal != Capability Match
```

## 59. Relationship to M0.6 Governance

A provider may expose risks, uncertainty, recommendations, or candidate work semantics.

Governance alone establishes Authorization under its external authority mechanism.

```text
provider recommendation != Governance Decision
```

## 60. Relationship to M0.8 Worker Delegation

M0.8 freezes long-form delegated work and WorkerResult semantics.

M0.7 freezes that Cognitive Provider reasoning cannot be used as a hidden delegated-work lifecycle.

## 61. Relationship to M0.9 Failure & Recovery

M0.9 owns retry, fallback, interrupted/unknown outcomes, and recovery principles.

M0.7 freezes only that provider failure does not change intent truth, authority, capability existence, or semantic validity by itself, and provider fallback cannot silently widen disclosure.

## 62. Backup scenario

Intent:

```text
"Find the newest organism_lab backup in D:\Backups,
extract it to W:\organism_lab,
and launch the project."
```

A provider may receive:

```text
intent text
bounded semantics for D:\Backups and W:\organism_lab
selected capability projection
explicit rule: newest by modification time
```

It may propose:

```text
filesystem.search
artifact.select(rule = newest_by_mtime)
archive.inspect
archive.extract
workspace.inspect
process.launch
```

IRR still validates:

```text
rule is explicit
no material ambiguity hidden
capabilities exist in exact Catalog Snapshot
work is bounded
no hidden shell fallback
requested effects are represented
```

The provider does not know or invent the concrete backup path before attributable Binding Input exists.

## 63. Ambiguous recipient scenario

Intent:

```text
"Send the report to Ivan."
```

Disclosed Context contains two plausible Ivans.

A provider returns:

```text
recipient = Ivan Petrov
confidence = 0.91
```

M0.7 requires IRR to reject that unilateral material choice unless an explicit admitted rule/evidence resolves it.

Correct path:

```text
CandidateResolution
    -> Material Ambiguity remains
    -> Clarification
```

```text
0.91 confidence != recipient authority
```

## 64. Remote-provider disclosure scenario

IRR has local Context containing a private file path and secret account metadata.

A remote LLM needs only the semantic task and a redacted capability projection.

M0.7 forbids treating all IRR Context as automatically model-disclosable.

The Provider Input Envelope may include only the permitted projection.

If external disclosure of additional material is required, the Host/Governance boundary decides that authority; the provider cannot request-and-receive it ambiently.

## 65. Provider hallucinated capability scenario

A provider suggests:

```text
telegram.send_file
```

but the exact applicable Catalog Snapshot contains no compatible capability.

IRR reports/retains M0.5 `missing_capability` semantics rather than accepting provider knowledge that "Telegram tools usually exist."

```text
model prior != Catalog Membership
```

## 66. Organism provider scenario

A future Organism-derived provider maps grounded internal state into candidate semantics:

```text
CandidateResolution:
    interpretation = inspect recent experiment failures
    uncertainty = ...
    proposed_information_need = ...
```

IRR validates the candidate under the same contracts used for an LLM or deterministic resolver.

The Organism's internal confidence, grounded representation, or learned memory does not bypass explicit Context, capability, Governance, or provenance boundaries.

This lets organism_lab evolve independently while IRR maintains a stable cognitive seam.

## 67. Acceptance criteria

M0.7 is complete when the repository states unambiguously that:

1. Cognitive Provider is a replaceable semantic dependency rather than owner of final IRR state.
2. LLM, deterministic, hybrid, and future Organism-derived providers can fit the same semantic seam without IRR depending on their internals.
3. Provider Input is explicit, bounded, attributable, and distinct from the whole IRR state; material projections do not erase provenance/uncertainty/evidentiary limits.
4. Context/Catalog/authority material available to IRR is not automatically authorized for Provider Disclosure.
5. Local provider placement does not create unrestricted disclosure entitlement.
6. Remote provider transport/disclosure is not exempt from external authority merely because it supports reasoning.
7. Provider cannot ambiently acquire Context or world state through hidden tools/retrieval under the Cognitive Provider contract.
8. Provider tool/retrieval results are not automatically IRR Context, Observation, or Evidence.
9. Provider output is CandidateResolution material, not Observation or Context by default.
10. CandidateResolution is distinct from ResolvedIntent, WorkPlan, Authorization, Outcome, and Effect.
11. Provider-produced material retains provider provenance and cannot be rewritten as user/Host/Observation provenance.
12. Provider Claims, fluency, rationale, identity, reputation, and provider/model prior do not establish factual truth or admitted Evidence automatically.
13. Semantic interpretation remains distinct from fabricated world facts or referents.
14. Material candidate inferences, including those influenced by provider prior, retain evidentiary limitations.
15. Provider Assumptions obey the same M0.2 restrictions as IRR assumptions.
16. Provider confidence/preference cannot resolve Material Ambiguity by itself.
17. Provider may propose Clarification/Information Need/Observation Need without receiving acquisition authority.
18. Provider recommendation/confidence cannot create Governance Authorization.
19. Provider assertion cannot create Capability Catalog Membership or Capability Match.
20. Provider Catalog projection is distinct from the authoritative exact Catalog Snapshot.
21. Provider preference does not create hidden capability precedence.
22. Provider-generated work must satisfy M0.3 boundedness and cannot hide autonomous loops, code, retries, or shell control flow.
23. Executable-looking provider output remains candidate data until admitted semantic work and downstream authority/execution gates exist.
24. Material provider references must resolve against authoritative admitted inputs.
25. IRR may perform semantics-preserving normalization but not hidden semantic repair.
26. Malformed provider output does not authorize fabrication of missing semantics.
27. Partial candidate admission cannot silently change the meaning of the candidate/path.
28. Provider confidence is descriptive metadata, not Evidence, truth, Capability Match, safety, or Authorization by default.
29. Provider provenance may be recorded without becoming authority.
30. Same provider input does not imply byte-identical output unless the provider contract says so; re-query is not historical replay.
31. IRR admission does not require private provider chain-of-thought, and internal reasoning/search does not create ambient retrieval authority.
32. Provider rationale does not substitute for evidence provenance.
33. Multiple providers have no implicit universal precedence or majority-is-truth rule.
34. Provider disagreement is candidate disagreement rather than admitted Context Conflict by default.
35. Provider fallback cannot silently widen disclosure or change semantic admission rules.
36. Provider failure is distinct from intent invalidity, Denial, and missing capability.
37. Deterministic provider output is not authoritative merely because it is deterministic.
38. Organism-derived provider has no privileged bypass and does not create an organism_lab dependency in IRR core.
39. Provider cannot rewrite Origin or Principal provenance silently.
40. Instruction-like text inside Context does not become authority merely because a provider follows it.
41. Provider-specific tool/function-call syntax is not CapabilityHandoff or Authorization.
42. Provider may propose non-operational resolution, but factual/evidentiary rules still apply.
43. Provider output does not become canonical memory automatically.
44. Provider cannot self-expand future privileges through its own candidate output.
45. IRR admission preserves all applicable M0.1–M0.6 invariants.
46. Candidate rejection does not equal parent intent rejection by default.
47. IRR may resolve some paths without any Cognitive Provider and therefore is not an LLM wrapper.
48. Cognitive Provider is distinct from Worker and Executor boundaries.
49. Provider reasoning cannot hide long-form delegated work inside candidate generation.
50. Provider integration remains stable while prompting, tokenization, model internals, and organism internals remain replaceable implementation detail.
51. M0.8 Worker, M0.9 failure/recovery, M1 schema, and M3 LLM implementation details remain deferred.
52. No runtime code or `src/` tree is introduced.
