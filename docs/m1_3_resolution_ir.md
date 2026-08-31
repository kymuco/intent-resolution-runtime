# M1.3 — Resolution / Clarification IR

Status: **implementation slice**.

M1.3 encodes the frozen M0.2 and M0.7 boundary between provider-produced candidate semantics, IRR-owned admission, blocking ambiguity/conflict/missing information/uncertainty, clarification, information needs, explicit non-material assumptions, and admitted `ResolvedIntent`.

It does not introduce WorkPlan, Binding, Observation, Capability, Governance, Authorization, execution, provider transport, trust scores, or retry semantics.

```text
IntentRequest identity + ContextEnvelope identity
                    |
                    v
             Cognitive Provider
                    |
                    v
          CandidateResolution
                    |
                    v
               IRR admission
          /-----------+-----------\
         v            v            v
ResolvedIntent  ClarificationNeed  InformationNeed
```

Core invariants:

```text
provider proposes != IRR admits
CandidateResolution != ResolvedIntent
ClarificationNeed != ResolvedIntent
InformationNeed != retrieval authority
Material Ambiguity -> blocking
unresolved blocking issue -> no ResolvedIntent
Assumption != established fact
Assumption != hidden material choice
resolution admission != Authorization
resolution admission != Effect
```

## Candidate attribution

`CandidateResolution` is provider-produced candidate material. Its provenance is explicit:

```text
CandidateAttribution
├─ provider_ref
└─ invocation_ref
```

Both values are opaque `StableRef` values. They identify the attributed provider and provider invocation occurrence. They do not verify that provider, strengthen its claims, or grant admission authority.

The term provider includes replaceable LLM, deterministic, Organism-derived, or hybrid cognitive providers under M0.7.

```text
provider identity != trust amplification
provider invocation != authority
```

## CandidateResolution

```text
CandidateResolution
├─ schema = irr.candidate_resolution.v1
├─ intent_request_identity
├─ context_envelope_identity
├─ attribution
├─ proposed_semantics
├─ assumptions[]
├─ issues[]
├─ clarification_proposals[]
└─ information_need_proposals[]
```

A CandidateResolution is always tied to exact content identities of the request occurrence and bounded ContextEnvelope it claims to interpret.

Candidate collections are normalized by content identity. Their array order cannot become an implicit provider preference or issue precedence rule.

Candidate semantics may be incomplete or may preserve blocking issues. A structurally valid candidate is still not admitted IRR state.

```text
candidate validity != admission
candidate fluency != truth
candidate confidence != admission authority
```

M1.3 deliberately does not include a `confidence`, `trusted`, `verified`, `approved`, `authorized`, or `safe` field. Provider-specific confidence metadata remains outside this core IR slice and cannot satisfy admission by implication.

## AssumptionRecord

```text
AssumptionRecord
├─ schema = irr.assumption.v1
├─ kind = presentation | formatting | other_non_material
├─ statement
├─ scope
└─ rationale
```

An AssumptionRecord makes an otherwise implicit premise inspectable. The kind explicitly asserts that the assumption is non-material under M0.2; final IRR admission is still responsible for rejecting a premise that actually chooses a material referent, recipient, disclosure destination, mutation target, executable target, authority, verified identity, material cost, or external commitment.

```text
AssumptionRecord != established fact
AssumptionRecord != permission to guess
```

The schema intentionally has no `material=true/false` boolean. M0 already forbids material assumptions in an admitted path; M1.3 does not create a representation that legitimizes them.

## ResolutionIssue

```text
ResolutionIssue
├─ schema = irr.resolution_issue.v1
├─ kind
│  ├─ material_ambiguity
│  ├─ conflict
│  ├─ missing_information
│  └─ uncertainty
├─ impact = blocking | non_blocking
├─ scope
├─ description
└─ alternatives[]
```

`alternatives` are unordered semantic alternatives, not ranked choices. They are normalized lexicographically so input order cannot smuggle precedence.

Rules frozen by executable validation:

- Material Ambiguity is always `blocking`.
- Material Ambiguity preserves at least two alternatives.
- Conflict preserves at least two conflicting alternatives.
- Missing Information does not invent alternatives that are not known.
- Uncertainty preserves epistemic limits without implying a Conflict or a missing-information acquisition requirement, and it does not invent competing alternatives.
- a `ResolvedIntent` cannot contain a blocking issue;
- a `ResolvedIntent` cannot contain Material Ambiguity even if a malformed producer labels it non-blocking.

Conflict may remain explicit as non-blocking only when it cannot change the next bounded semantic path.

## Provider proposals for needs

A candidate may contain bounded proposal records:

```text
ClarificationProposal
├─ question
├─ scope
└─ reason

InformationNeedProposal
├─ description
├─ scope
└─ reason
```

These are still provider proposals. They do not pause IRR by themselves and they grant no acquisition authority.

```text
provider-proposed clarification != IRR ClarificationNeed
provider-proposed information need != retrieval/observation authority
```

## IRR-owned admission attribution

Final M1.3 outputs carry a distinct IRR-owned admission attribution:

```text
ResolutionAttribution
├─ resolver_ref
└─ admission_event_ref
```

This preserves the distinction between provider production and IRR admission.

`ResolutionAttribution` is not Governance authority, user approval, or evidence of an Effect.

```text
resolution attribution != Authorization
resolution attribution != Effect evidence
```

## Exact candidate lineage

An admitted M1.3 output may preserve zero or more exact `CandidateResolution` objects in `candidate_inputs[]`.

The full immutable candidate is retained rather than a bare arbitrary digest. This preserves provider attribution, exact candidate semantics, assumptions, issues, and proposals without laundering any of them into Context or admitted semantics.

```text
candidate_inputs[] = provenance
candidate_inputs[] != admitted wholesale
CandidateResolution != Context by default
```

An empty `candidate_inputs` tuple is valid for a deterministic IRR path that did not use a Cognitive Provider candidate.

## ResolvedIntent

```text
ResolvedIntent
├─ schema = irr.resolved_intent.v1
├─ intent_request_identity
├─ context_envelope_identity
├─ admission_attribution
├─ semantics
├─ assumptions[]
├─ unresolved_issues[]
└─ candidate_inputs[]
```

A `ResolvedIntent` is IRR-admitted semantic state. It may represent operational or non-operational intent; M1.3 does not yet classify or plan work.

Admission validation enforced by this slice:

```text
unresolved blocking issue -> rejected
Material Ambiguity -> rejected
non-blocking Conflict/Missing Information/Uncertainty -> may remain explicit
```

M1.3 has no `WorkPlan` field and no authority/effect fields.

```text
ResolvedIntent != WorkPlan
ResolvedIntent != Authorization
ResolvedIntent != Effect
```

## ClarificationNeed

```text
ClarificationNeed
├─ schema = irr.clarification_need.v1
├─ intent_request_identity
├─ context_envelope_identity
├─ admission_attribution
├─ question
├─ scope
├─ blocking_issues[]
└─ candidate_inputs[]
```

A ClarificationNeed is an IRR-owned pause requesting attributable continuation input. It is not a `ResolvedIntent` and does not terminate the parent intent lifecycle.

Every ClarificationNeed must preserve at least one blocking issue. The issue may be Material Ambiguity, Conflict, Missing Information, or Uncertainty. M1.3 deliberately does not hard-code one acquisition path for blocking uncertainty or missing information; asking the caller to clarify is valid when semantically appropriate.

## InformationNeed

```text
InformationNeed
├─ schema = irr.information_need.v1
├─ intent_request_identity
├─ context_envelope_identity
├─ admission_attribution
├─ description
├─ scope
├─ reason
├─ blocking_issues[]
└─ candidate_inputs[]
```

An InformationNeed records what bounded attributable information is required to continue. It does not authorize fetching, observing, browsing, reading files, querying accounts, using a Worker, or invoking a capability.

```text
InformationNeed != retrieval authority
InformationNeed != Observation Need authority
InformationNeed != Capability Match
InformationNeed != Authorization
```

Observation-specific request/return schemas remain deferred to M1.4 and later lifecycle slices.

## No flat resolution status

M1.3 intentionally does **not** create one enum such as:

```text
resolved | ambiguous | conflict | clarification | info_needed
```

Those labels collapse independent semantic roles. Instead, issues, candidate proposals, IRR-owned pauses, and admitted resolution are separate immutable record types.

This preserves the M0 rule that a non-blocking unresolved Conflict can coexist with a ResolvedIntent while Material Ambiguity cannot.

## Canonical identity

M1.3 does not extend the canonical value domain. It continues to use only:

```text
object
array
Unicode scalar string
```

All M1.1/M1.2 canonical encoding rules remain byte-for-byte normative.

The M1.3 golden candidate digest is:

```text
480e4745d996e82b9faa8bffff4a02be6bf79e04c8423008fb825842e0976e5d
```

The M1.3 golden admitted `ResolvedIntent` digest is:

```text
c47d45338347536d6ce576598dd17bd59c91ab82581c6fb11c631be1edbb161e
```

M1.1 and M1.2 golden vectors must remain unchanged.

## Closed constructor schema

All new public identity-bearing M1.3 record types are immutable, slotted, exact-type validated at retained record boundaries, and sealed against Python subclassing through the public package surface.

This preserves the M1.2 hardening invariant:

```text
closed wire schema == closed ordinary Python constructor schema
complete admitted record state == canonical identity-covered state
```

## Fail-closed behavior

M1.3 rejects at least:

- unknown wire fields;
- authority/confidence/trust field smuggling;
- non-scalar Unicode;
- mutable list construction where tuples are required;
- duplicate identity-bearing records inside unordered sets;
- duplicate candidate inputs;
- non-blocking Material Ambiguity;
- ambiguity/conflict records that erase their alternatives;
- Missing Information or Uncertainty records that invent alternatives;
- `ResolvedIntent` with any unresolved blocking issue;
- clarification/information pause records without a blocking issue;
- arbitrary `RecordIdentity` values masquerading as exact candidate provenance;
- Python subclasses carrying hidden state outside canonical identity.

## Explicit deferrals

M1.3 does **not** freeze:

- semantic operation / WorkPlan schemas;
- symbolic references or Late Binding;
- Observation / Binding Input schemas;
- explicit precedence-rule schemas;
- automated truth/trust scoring;
- provider confidence schemas;
- provider disclosure envelopes or transport;
- Candidate Admission algorithms beyond the structural invariants encoded here;
- Work / Delegation;
- Capability / Governance / Authorization;
- Attempt / Outcome / Continuation;
- persistence;
- canonical numbers, booleans, or null.

## Acceptance

M1.3 is correct when executable tests prove at least:

```text
CandidateResolution != ResolvedIntent
provider candidate attribution is occurrence-specific
candidate identity binds request + context + provider invocation
candidate collection order != implicit precedence
Material Ambiguity always blocks
conflict alternatives are preserved without precedence
non-blocking uncertainty can remain explicit in ResolvedIntent
blocking uncertainty prevents ResolvedIntent admission
assumptions are explicit and identity-material
ResolvedIntent rejects blocking issues
non-operational ResolvedIntent requires no WorkPlan
ClarificationNeed is a pause, not resolution
ClarificationNeed can request missing caller information
InformationNeed grants no retrieval/observation authority
provider need proposal grants no authority
exact candidate provenance is retained, not a bare digest
round-trip preserves candidate and IRR-owned outputs
authority/confidence smuggling fails closed
records are immutable/slotted/sealed
M1.3 golden candidate + resolved digests frozen
M1.1/M1.2 golden identities remain unchanged
```
