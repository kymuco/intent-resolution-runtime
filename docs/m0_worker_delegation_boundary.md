# M0.8 — Worker Delegation Boundary

Status: **normative for M0.8**.

This document freezes how Intent Resolution Runtime (IRR) may delegate bounded long-form work to a Worker without turning an ordinary WorkStep into an opaque autonomous loop, transferring ownership of the parent intent, inventing authority, or allowing delegated work to widen its own scope.

It extends M0.1 Product Charter & Vocabulary, M0.2 Trust/Context/Resolution Semantics, M0.3 Intent → Work Boundary, M0.4 Late Binding & Observation Boundary, M0.5 Capability Boundary, M0.6 Governance & Authority Boundary, and M0.7 Cognitive Provider Boundary without introducing runtime code, exact Python schemas, Codexia integration, worker transport adapters, retry/recovery algorithms, or M1 data models.

M0.8 answers one question:

> How may IRR hand a bounded complex subtask to a Worker that owns its own subordinate lifecycle while IRR retains ownership of the parent intent, semantic scope, authority boundary, and final continuation/completion decision?

The answer is:

> **IRR may create an attributable DelegatedWork representation with an explicit objective, scope, context surface, capability ceiling, authority constraints, forbidden effects, deliverables, and completion contract. A Worker may autonomously manage subordinate work only inside that envelope. Material widening returns to IRR rather than becoming hidden worker discretion.**

```text
Parent IntentRequest
       |
       v
      IRR
       |
       v
ResolvedIntent / WorkPlan
       |
       v
DelegatedWork
       |
       v
DelegatedWorkHandoff
       |
       v
     Worker
   subordinate
    lifecycle
       |
       +-------------------+
       |                   |
       v                   v
 WorkerResult       escalation / new need
       |                   |
       +---------+---------+
                 |
                 v
           IRR Continuation
                 |
        +--------+---------+
        |                  |
        v                  v
parent continues      parent completes
or successor work     if actually satisfied
```

Central invariants:

```text
Worker != Cognitive Provider
Worker != Executor by default
DelegatedWork != ordinary WorkStep
DelegatedWork != blanket authority
DelegatedWorkHandoff != Authorization
worker subplan != parent WorkPlan mutation
worker judgment != parent Authorization
worker capability ceiling != capability discovery authority
allowed capability set != worker selection policy
worker context availability != disclosure authority
WorkerResult != parent intent completion
WorkerResult != factual truth by default
WorkerResult != Authorization
WorkerResult != Governance Decision
WorkerResult != Outcome by default
worker completion claim != Delegated Completion Contract satisfied
worker progress != completion
worker failure != parent intent failure by definition
worker escalation != authority grant
worker-created subtask != inherited parent authority by default
material delegation widening != worker-local discretion
```

## 1. Worker is a distinct downstream role

A `Worker` is a downstream component that performs delegated bounded work with its own subordinate lifecycle.

Conceptual examples may include:

```text
Codexia
research worker
coding worker
analysis worker
artifact-production worker
future specialized worker
```

A Worker is not defined by vendor, model family, process layout, or internal agent architecture.

```text
Worker implementation != IRR delegation contract
```

IRR MUST remain independently implementable without importing Codexia or any other worker runtime.

## 2. Worker is not a Cognitive Provider

M0.7 remains normative.

A Cognitive Provider proposes candidate intent semantics inside the IRR resolution seam.

A Worker owns a bounded delegated subtask lifecycle after delegation semantics have already been admitted.

```text
Cognitive Provider -> CandidateResolution
Worker -> WorkerResult
```

A provider MUST NOT be used as a hidden Worker merely to avoid delegation constraints, and a Worker result MUST NOT be silently treated as provider candidate semantics.

## 3. Worker is not ordinary WorkStep execution

M0.3 remains normative: ordinary WorkSteps must themselves be bounded and inspectable.

Long-form work such as:

```text
"study 40 pull requests and propose the next experiment"
```

must not be hidden inside an ordinary step such as:

```text
codexia.do_work
```

when the real semantics involve open-ended subordinate analysis, intermediate decisions, artifact creation, or iterative reasoning.

```text
worker delegation != ordinary WorkStep execution
```

A Worker boundary exists precisely so that bounded subordinate autonomy is visible instead of disguised as one opaque capability call.

## 4. CapabilityHandoff and DelegatedWorkHandoff are distinct

A future `CapabilityHandoff` represents bounded operational work suitable for an Executor/Capability boundary.

A future `DelegatedWorkHandoff` represents an admitted DelegatedWork subtask suitable for a Worker boundary.

```text
CapabilityHandoff != DelegatedWorkHandoff
```

The distinction is semantic, not transport-specific.

Both handoffs remain separate from Authorization.

## 5. DelegatedWork

`DelegatedWork` is the bounded semantic representation of a subtask that IRR delegates to a Worker.

Conceptually, it includes at least the semantics of:

```text
objective
scope
context surface
allowed capability surface / ceiling
forbidden effects
expected deliverables
completion contract
material constraints
lineage to parent intent/work
applicable authority references or requirements
```

Exact fields and serialization are deferred to M1/M7.

A DelegatedWork object is not itself execution permission.

```text
DelegatedWork != Authorization
```

## 6. Delegated objective

The delegated objective describes what the Worker is asked to accomplish inside the parent intent lifecycle.

It MUST be bounded enough that a reviewer can distinguish:

```text
inside objective
outside objective
```

For example:

```text
valid bounded objective:
"analyze the supplied CG2.42 evidence and propose one or more
next experiment candidates with supporting rationale"
```

is materially different from:

```text
unbounded objective:
"do whatever research seems useful until the project is solved"
```

An unbounded objective cannot be made safe merely by calling it delegated work.

## 7. Delegated scope

Delegated scope bounds the resources, repositories, artifacts, accounts, datasets, services, time windows, or semantic domains the Worker may operate over when material.

```text
parent resource universe != delegated scope by default
```

A Worker MUST NOT infer that every resource relevant to the parent intent is inside its delegated scope.

## 8. Delegated context surface

The Worker receives an explicit bounded context surface.

Context available to IRR is not automatically Worker-disclosable.

```text
IRR Context availability != Worker disclosure authority
```

The delegated context surface may contain selected Context, Evidence, prior Outcomes, capability information, artifacts, or parent-work lineage only when explicitly permitted for the Worker boundary.

Material provenance, uncertainty, Freshness, Completeness, and evidentiary distinctions MUST NOT be erased merely to simplify Worker input.

## 9. Worker has no ambient-context entitlement

Delegation does not grant a Worker ambient authority to inspect:

- unrelated repositories;
- the user's home directory;
- memory stores;
- browser state;
- accounts;
- arbitrary network resources;
- unrelated project artifacts;
- additional HDE state;
- undisclosed Capability Catalog entries.

If additional information is materially required beyond the delegated envelope, the Worker must report the need through an attributable result/escalation path.

```text
worker needs data != worker may acquire arbitrary data
```

## 10. Allowed capability surface is a ceiling, not a promise or selection policy

DelegatedWork may identify an allowed capability surface or capability ceiling.

This means only that use of capabilities outside that surface is not admitted by the delegation.

It does not prove that every listed capability:

- exists;
- is currently available;
- is invocation-ready;
- is authorized;
- will succeed.

```text
allowed capability != capability existence
allowed capability != availability
allowed capability != Authorization
allowed capability set != worker selection policy
```

Listing multiple capabilities does not declare them semantically interchangeable and does not authorize Worker-local selection when the choice would materially change provider/service, disclosure, effect, cost/commitment, authority, completion meaning, or another admitted semantic dimension. Such a material choice returns to IRR.

M0.5 remains normative.

## 11. Worker cannot invent capability fallback

A Worker MUST NOT respond to an absent or unavailable required capability by silently substituting:

- shell execution;
- browser automation;
- another provider;
- another service;
- arbitrary code;
- a broader Worker;
- a newly discovered plugin;
- a hidden human action.

```text
worker capability ceiling != capability discovery authority
missing capability != Worker fallback authority
```

A materially required missing capability returns as attributable blocked/need information under later lifecycle contracts.

## 12. Delegated authority is bounded separately from semantic scope

A delegation may identify authority material or authority requirements applicable to the delegated work.

This does not allow IRR or the Worker to mint Authorization.

```text
DelegatedWorkHandoff != Authorization
worker receipt of delegation != permission
```

M0.6 remains normative.

## 13. Semantic delegation scope and Authorization scope are distinct

A Worker can be semantically asked to perform work that is not yet fully authorized.

Conversely, an Authorization may cover work more broadly or narrowly than one Worker delegation.

Therefore:

```text
delegated semantic scope != Authorization scope
```

Before authority-requiring effects occur, downstream execution must still establish applicable Authorization coverage.

M0.8 does not freeze one universal ordering between DelegatedWork creation, Worker handoff, Governance review, and subordinate effect authorization. An external system may authorize a bounded delegated class, review concrete subordinate effects, or require another explicit pattern. The invariant is that no authority-requiring effect may exceed applicable Authorization coverage.

## 14. Worker cannot amplify authority

A Worker MUST NOT infer additional permission from:

- the parent intent;
- the fact that IRR delegated work;
- a capability being allowed;
- a previous authorized substep;
- an adjacent resource;
- a related recipient;
- worker confidence;
- worker judgment that a step is safe or necessary.

```text
worker judgment != parent Authorization
necessary worker step != authority inheritance
```

## 15. Forbidden effects are explicit negative bounds

DelegatedWork may identify forbidden effects or effect classes that the Worker must not perform within the delegation.

Conceptual examples:

```text
no external disclosure
no repository mutation
no process launch
no network publication
no deletion
no purchase / financial commitment
```

A forbidden-effect declaration is not a complete positive Authorization model. It only makes an additional bounded restriction explicit.

```text
not forbidden != authorized
```

## 16. Worker may own a subordinate lifecycle

A Worker may internally perform multiple subordinate reasoning/planning/execution cycles needed to satisfy the delegated objective, provided those cycles remain inside the admitted delegation envelope and applicable downstream authority boundaries.

This subordinate lifecycle may conceptually include:

```text
analyze
plan subordinate steps
inspect supplied results
revise subordinate plan
produce artifacts
check deliverables
return result
```

Exact Worker internal state is outside IRR core.

## 17. Worker subplan is not the parent WorkPlan

A Worker may maintain an internal subordinate plan.

That plan is not automatically an IRR `WorkPlan` and does not mutate the parent WorkPlan.

```text
worker subplan != parent WorkPlan
worker subplan revision != parent WorkPlan mutation
```

Only explicit IRR Continuation may create successor parent semantics when material parent meaning changes.

## 18. Worker-local discretion is bounded by the delegation envelope

Worker-local choices may be permitted when they do not materially widen the delegated objective, scope, disclosure, authority, effect surface, capability class, cost/commitment, or deliverable meaning.

Examples of potentially worker-local choices when explicitly compatible with the envelope include:

- ordering analysis of already supplied files;
- choosing among equivalent internal analysis strategies;
- formatting a draft deliverable;
- retrying an internal pure computation when M0.9/later contracts permit it;
- using a permitted deterministic transformation over already delegated data.

The existence of Worker-local discretion does not create general semantic discretion.

## 19. Material widening must return to IRR

A Worker MUST NOT silently widen delegation when new information requires a materially different:

- objective;
- resource class;
- repository/account;
- recipient;
- disclosure;
- mutation surface;
- executable target;
- provider/service;
- capability class;
- cost or commitment;
- authority scope;
- external effect;
- completion meaning.

```text
material delegation widening != worker-local discretion
```

Such a need must return through an attributable WorkerResult/escalation/continuation path.

## 20. Prerequisites do not create hidden side tasks

A Worker may discover that a prerequisite is needed.

The prerequisite is not automatically within scope merely because it is useful or necessary.

```text
necessary prerequisite != delegated authority
necessary prerequisite != delegated scope expansion
```

If the prerequisite was not already represented by the delegation envelope, material expansion returns to IRR.

## 21. Worker cannot delegate recursively by default

A Worker does not gain authority to create another Worker delegation merely because it owns a subordinate lifecycle.

```text
Worker delegation != recursive-delegation authority
```

Future contracts may explicitly permit bounded nested delegation, but M0.8 does not assume it.

Internal helper agents, model components, subprocesses, or other Worker implementation details are not automatically nested IRR Worker delegations. They become a nested Worker boundary only when the system semantically delegates a distinct subtask with its own Worker identity/lifecycle beyond the opaque implementation boundary.

If nested delegation is later supported, each nested delegation must preserve lineage, scope, capability ceilings, disclosure constraints, and authority limits rather than inheriting them ambiently.

## 22. Worker may not relabel Origin or Principal

A Worker can produce new worker-originated requests, findings, or proposed continuations.

It MUST NOT relabel them as human-originated merely because the parent intent came from a human.

```text
worker-originated continuation != human Origin
worker result != Principal statement
```

M0.1 provenance rules remain normative.

## 23. WorkerResult

`WorkerResult` is attributable result material returned by a Worker for a delegated subtask.

Conceptually it may contain:

```text
deliverables
findings
claims / evidence references
produced artifact references
subtask completion claim
blocked needs
material uncertainty
scope actually covered
known omissions
observed effects / outcome references where applicable
```

Exact schema is deferred to M1/M7/M0.9.

## 24. WorkerResult is not parent completion

A Worker may correctly complete its delegated subtask while the parent intent remains incomplete.

```text
WorkerResult != parent intent completion
worker subtask completion != parent intent satisfaction
```

IRR owns the determination of how the WorkerResult affects the parent lifecycle.

## 25. WorkerResult is not automatically factual truth

Worker-produced findings remain attributable Claims/Evidence-bearing material under M0.2 semantics.

A Worker may be wrong, incomplete, stale, or uncertain.

```text
WorkerResult != factual truth by default
worker confidence != evidence amplification
```

IRR or another downstream consumer must preserve provenance and evidentiary limitations when worker findings matter to parent resolution.

If a Worker acquires information from an external source, material provenance must preserve both the original source and the Worker intermediary when those distinctions matter. Worker-mediated research must not be rewritten as a direct IRR Observation of the original source or as if Worker identity itself were the original factual source.

## 26. WorkerResult is not Governance material by default

A Worker may recommend proceeding, stopping, changing scope, or requesting approval.

Those recommendations do not become Governance Decisions.

```text
WorkerResult != Governance Decision
worker recommendation != Authorization
```

## 27. WorkerResult is distinct from Observation

A WorkerResult may contain information learned during delegated work.

The result itself is not automatically an M0.2 Observation.

A Host/continuation contract may classify returned worker information as Context, Observation, Evidence, Outcome, or another explicit semantic role while preserving Worker provenance.

```text
WorkerResult != Observation by default
```

One returned payload may support multiple explicit records later, but their semantic roles must not be collapsed.

## 28. WorkerResult is broader than an Outcome record

M0.9 owns exact Outcome/failure states.

A WorkerResult may reference or contain subordinate Outcome information, but WorkerResult is a broader delegated-result envelope and is not automatically itself the `Outcome` semantic record.

```text
WorkerResult != Outcome by default
```

An Outcome is an explicitly classified downstream operational/lifecycle result record under the later execution/recovery contract. The distinction matters because a WorkerResult can include analysis, deliverables, claims, omissions, or escalation needs even when one subordinate effect has a failed, interrupted, or unknown Outcome.

## 29. Progress is not completion

A Worker may emit progress or intermediate status.

Progress may be useful for inspection, cancellation, or UI, but it does not establish final subtask completion.

```text
worker progress != WorkerResult completion
worker progress != parent completion
```

Exact progress schemas and streaming are deferred.

## 30. Worker escalation / need

A Worker may report that delegated work cannot continue without additional information, capability, authority, scope, clarification, or a changed objective.

Such a report is a need/escalation, not permission to satisfy the need itself.

```text
worker escalation != authority grant
worker escalation != scope expansion
```

IRR decides how that information re-enters the parent lifecycle.

## 31. Parent lifecycle remains owned by IRR

The Worker owns only the lifecycle of its delegated subtask.

IRR retains ownership of:

- the parent IntentRequest lineage;
- parent ResolvedIntent semantics;
- parent WorkPlan/successor semantics;
- parent capability validation;
- the Governance boundary;
- continuation after WorkerResult;
- determination of parent satisfaction/completion.

```text
Worker owns subtask lifecycle
IRR owns parent intent lifecycle
```

## 32. Worker completion claim is not completion evidence by itself

A Worker may return:

```text
"done"
```

but that text is only a Worker assertion about subtask status.

The receiving IRR/Host boundary must evaluate whether returned deliverables and result semantics actually satisfy the Delegated Completion Contract. A worker-local completion assertion alone does not establish delegated completion and, a fortiori, does not establish the parent objective.

```text
worker completion claim != Delegated Completion Contract satisfied
worker says done != parent done
```

## 33. Expected deliverables are part of the delegation contract

DelegatedWork should identify the expected deliverables when material.

Examples:

```text
analysis report
patch proposal
candidate experiment set
code artifact
review findings
structured comparison
```

A Worker producing an unrelated useful artifact does not silently satisfy a different completion contract.

```text
useful output != required deliverable by default
```

## 34. Completion contract is explicit

The delegated completion contract states what must be established for the subtask to count as completed.

For example:

```text
"return a ranked set of experiment candidates with cited evidence"
```

is stronger than:

```text
"return any note about the experiments"
```

Worker confidence, transport success, or a Worker completion assertion cannot strengthen a weaker deliverable into a stronger completion meaning.

## 35. Deliverable acceptance and factual correctness are different

A deliverable may satisfy its structural completion contract while still containing uncertain or incorrect factual Claims.

```text
deliverable complete != every claim true
```

M0.2 evidentiary semantics remain in force.

## 36. Worker identity does not amplify trust

Worker identity, vendor, reputation, prior success, local/remote placement, or specialization may be attributable metadata.

They do not automatically prove returned Claims or authorize work.

```text
trusted Worker != trusted WorkerResult by default
Worker reputation != claim verification
```

## 37. Worker substitution is material when semantics change

Replacing one Worker with another is allowed only when all material delegation semantics remain compatible.

A Worker substitution MUST NOT silently change:

- context disclosure;
- capability surface;
- provider/service boundary;
- external disclosure;
- cost/commitment;
- completion meaning;
- authority requirements.

```text
Worker substitution != semantic equivalence by default
Worker substitution != authority inheritance
```

## 38. Local and remote Workers have different possible effect surfaces

A remote Worker may require network transport or external disclosure of delegated context/artifacts.

A local Worker may reduce external disclosure but still does not gain blanket access to local context or secrets.

```text
remote Worker transport != authority exemption
local Worker != all-context entitlement
```

Disclosure and authority boundaries remain explicit.

## 39. Worker artifacts retain provenance

Artifacts created or modified by a Worker should remain attributable to the delegated subtask and Worker boundary when material.

A produced file, patch, report, or repository change does not become human-authored or IRR-authored merely because it was requested by a parent human intent.

```text
worker-produced artifact != human-authored artifact
```

Exact artifact digests, receipts, and provenance schemas are deferred.

## 40. Worker mutation still requires represented effects and authority

Delegation does not make mutation invisible.

If worker work may modify repositories, files, external services, accounts, or other state, those effect surfaces must remain represented and subject to applicable Capability/Governance boundaries.

```text
delegated mutation != hidden effect exemption
```

## 41. Worker cannot launder external disclosure through research

A research-like objective does not authorize uploading local material, querying external services with secrets, publishing artifacts, or contacting third parties unless those effects are represented and authorized.

```text
research objective != disclosure authority
```

## 42. Worker-created executable text remains data until admitted/executed through the proper boundary

A Worker may produce:

- code;
- shell commands;
- SQL;
- patches;
- tool-call syntax;
- execution suggestions.

Such output is deliverable/result data unless a downstream admitted execution path separately represents and authorizes its effects.

```text
worker-generated code != execution authority
worker patch != applied mutation
```

## 43. Worker may return proposed successor semantics, not mint them

A Worker may recommend a changed parent plan or new objective.

That recommendation is attributable WorkerResult material for IRR Continuation, not a Successor WorkPlan created by Worker authority and not a CandidateResolution merely because it proposes semantics.

```text
worker proposal != successor ResolvedIntent
worker proposal != successor WorkPlan
worker proposal != CandidateResolution by default
```

IRR re-applies the applicable M0.1–M0.7 trust, ambiguity, work, capability, provider, and Governance boundaries. M0.7 Candidate Admission applies only if a Cognitive Provider is actually invoked and returns CandidateResolution material; WorkerResult does not silently enter that provider-specific seam.

## 44. Worker result re-entry is explicit and attributable

Material WorkerResult information that affects the parent path must re-enter through an explicit attributable classification and IRR Continuation boundary.

It does not become ambient parent Context, CandidateResolution, Observation, Evidence, or Outcome merely because the Worker returned it. The Host/IRR boundary classifies the material role explicitly while preserving Worker and source provenance.

```text
WorkerResult availability != ambient Context admission
WorkerResult re-entry != Candidate Admission by default
```

## 45. Worker result cannot silently rewrite prior parent history

A later WorkerResult may change what IRR should do next.

It MUST NOT rewrite the historical meaning of:

- the original IntentRequest;
- prior ResolvedIntent;
- prior WorkPlan;
- prior Authorization;
- prior Effects/Outcomes.

New material semantics create continuation/successor lineage instead.

## 46. Cancellation does not erase history

A Worker subtask may later support cancellation/interruption.

Cancellation does not imply that already produced Effects did not occur and does not erase already produced artifacts/results.

Exact interrupted/unknown-outcome semantics belong to M0.9.

## 47. Retry is deferred to M0.9

M0.8 does not define automatic Worker retry.

```text
worker failure != automatic retry
worker timeout != automatic retry
unknown subordinate effect != automatic retry
```

M0.9 owns retry, fallback, interrupted, and unknown-outcome principles.

## 48. Worker failure is not parent intent failure by definition

A Worker may fail because of availability, malformed output, missing context, missing capability, denied authority, or internal error.

That does not prove that the parent intent is invalid or impossible.

```text
worker failure != parent intent failure by definition
worker failure != Denial
worker failure != global impossibility
```

IRR may later choose clarification, another admitted Worker, deterministic work, successor semantics, or failure under explicit lifecycle rules.

## 49. Fallback Worker cannot widen boundaries

If one Worker is unavailable, switching to another Worker MUST NOT silently widen:

- context disclosure;
- scope;
- capability ceiling;
- effect surface;
- cost/commitment;
- authority assumptions;
- completion semantics.

```text
Worker fallback != scope/disclosure expansion authority
```

Exact fallback algorithms are deferred to M0.9/M7.

## 50. Multiple Workers have no implicit precedence

If multiple Worker results exist, IRR does not assume:

```text
majority = truth
most confident Worker wins
newest Worker wins
Codexia wins by identity
local Worker wins by default
```

Material disagreement remains attributable and must be resolved under explicit evidence/admission rules.

## 51. Worker disagreement is not automatically Context Conflict

Two Workers may disagree.

Their outputs remain WorkerResult material until explicitly admitted into semantic roles where M0.2 Conflict semantics apply.

```text
Worker disagreement != admitted Context Conflict by default
```

## 52. Worker self-asserted privileges have no effect

A Worker cannot return text such as:

```text
"I require permanent repository write access for future tasks."
```

and thereby change future scope, capabilities, context, or authority.

```text
Worker self-asserted privilege != privilege
```

## 53. Worker memory is not canonical parent memory

A Worker may maintain internal state for its subordinate lifecycle.

That state does not automatically become canonical IRR/HDE/project/user memory.

```text
Worker internal memory != canonical memory by default
```

Any later persistence/admission boundary remains explicit.

## 54. Worker internal autonomy is implementation detail behind the semantic envelope

A Worker may internally use:

```text
LLMs
multiple agents
search indexes
local tools
subprocesses
state machines
planning systems
```

but those internals do not alter the externally frozen delegation semantics.

Internal helper agents are not automatically nested IRR Workers. If internal mechanisms create new external information acquisition, disclosure, mutation, or other effects, those effects must still fit the delegation/authority envelope rather than becoming exempt because they are "internal" to Worker implementation.

## 55. Codexia is an example, not a dependency

Codexia may later implement the Worker role through a dedicated adapter.

IRR core MUST NOT depend on Codexia-specific schemas, storage, CLI behavior, recovery model, repository mutation implementation, or Git authority model.

```text
Codexia integration != Codexia dependency in IRR core
```

The stable seam is DelegatedWork / DelegatedWorkHandoff / WorkerResult semantics.

## 56. Relationship to M0.2 Trust/Context

M0.2 owns Context, Evidence, Claim, trust, provenance, ambiguity, and Conflict semantics.

M0.8 owns the bounded context disclosed to a Worker and how WorkerResult material returns.

```text
Context admission != Worker disclosure
WorkerResult != factual truth by default
```

## 57. Relationship to M0.3 Work Boundary

M0.3 owns finite WorkPlan/WorkStep semantics and the rule that ordinary steps cannot hide autonomous loops.

M0.8 provides the explicit boundary for long-form delegated work.

```text
ordinary WorkStep != DelegatedWork
```

## 58. Relationship to M0.5 Capability Boundary

M0.5 owns Capability Catalog Membership, Capability Match, Availability, scope/effect metadata, and capability drift.

M0.8 may bound the capability surface available to a Worker but does not create capability existence or compatibility.

```text
worker allowed capability != Capability Match
allowed capability set != worker selection policy
```

## 59. Relationship to M0.6 Governance

M0.6 owns Authorization, Denial, Governance Constraint, require_review, and authority coverage.

M0.8 carries or references applicable authority semantics without minting them and does not impose one universal authority-check ordering for every Worker implementation.

```text
DelegatedWorkHandoff != Authorization
worker recommendation != Governance Decision
```

## 60. Relationship to M0.7 Cognitive Provider

M0.7 owns CandidateResolution/Candidate Admission semantics.

M0.8 owns delegated subordinate lifecycle semantics.

A Worker may internally use cognitive systems, but Worker output remains WorkerResult under the Worker boundary.

```text
Cognitive Provider != Worker
CandidateResolution != WorkerResult
WorkerResult re-entry != Candidate Admission by default
```

## 61. Relationship to M0.9 Failure & Recovery

M0.9 owns exact failure, retry, fallback, interrupted, and unknown-outcome principles.

M0.8 freezes only that Worker failure/progress/result states do not by themselves imply parent failure/completion or automatic retry, and that WorkerResult is broader than any explicit Outcome record later produced under M0.9 semantics.

## 62. Research-worker scenario

Parent intent:

```text
"Study the CG2.42 results and propose the next experiment."
```

IRR may admit DelegatedWork conceptually like:

```text
objective:
    analyze supplied CG2.42 evidence and propose next experiment candidates
scope:
    supplied CG2.42 reports and explicitly listed related records
context:
    bounded supplied artifacts + project vocabulary
allowed capabilities:
    read supplied artifacts
    produce report artifact
forbidden effects:
    no repository mutation
    no external publication
    no unrelated network research
expected deliverables:
    candidate experiments + rationale + evidence references
completion contract:
    return inspectable proposal set or explicit blocked need
```

Worker may analyze many supplied records and revise its internal reasoning.

If it decides it needs an unrelated private repository or external publication, that is a material widening and returns to IRR rather than happening silently.

## 63. Coding-worker scenario

Parent intent:

```text
"Implement the approved fix in repository R."
```

A Worker delegation may include bounded repository scope and a capability ceiling for inspection/patch creation.

If Git commit or push authority was not delegated/authorized, the Worker cannot infer it from the implementation objective.

```text
code-change objective != commit authority
commit authority != push authority
```

The Worker may return a patch artifact without applying/pushing it when the authority/effect envelope stops there.

## 64. Missing-capability scenario

DelegatedWork requires a capability that is absent from the applicable allowed/admitted surface.

Correct result is a blocked/missing-capability need under M0.5/later lifecycle semantics.

Incorrect behavior:

```text
"I'll just use shell/browser/another Worker instead."
```

```text
missing capability != Worker workaround authority
```

## 65. New-recipient scenario

A Worker tasked with preparing a report discovers that sending it to an external reviewer would help.

Unless recipient/disclosure semantics were already within the delegation and authorized surface, the Worker cannot send it.

It returns a proposal/need to IRR.

```text
useful external recipient != delegated recipient
```

## 66. Worker-completion scenario

Delegated objective:

```text
"produce three experiment candidates"
```

Worker returns three candidates and also asserts `done`.

The receiving boundary first evaluates whether the three candidates actually satisfy the delegated completion contract. Even if the delegated subtask is complete, the parent intent may still require IRR to compare candidates, request clarification, obtain Governance review, or construct successor work.

```text
worker completion claim != Delegated Completion Contract satisfied
subtask complete != parent complete
```

## 67. Acceptance criteria

M0.8 is complete when the repository states unambiguously that:

1. Worker is a distinct downstream role from Cognitive Provider and Executor.
2. Long-form delegated work is not hidden inside an ordinary WorkStep.
3. CapabilityHandoff and DelegatedWorkHandoff are distinct semantic boundaries.
4. DelegatedWork has an explicit bounded objective.
5. Delegated scope is explicit and is not the whole parent resource universe by default.
6. Worker context disclosure is explicit and distinct from IRR Context availability.
7. Worker has no ambient context entitlement.
8. Allowed capability surface is a ceiling, not proof of capability existence, availability, readiness, Authorization, semantic interchangeability, or a hidden Worker selection policy.
9. Worker cannot invent capability fallback or ambiently discover additional capabilities.
10. DelegatedWorkHandoff does not create Authorization.
11. Delegated semantic scope is distinct from Authorization scope and M0.8 does not impose a universal Governance timing order.
12. Worker cannot amplify parent authority or infer permission from necessity.
13. Forbidden effects can further restrict delegation but `not forbidden` does not mean authorized.
14. Worker may own a subordinate lifecycle inside the delegation envelope.
15. Worker subplan is not the parent IRR WorkPlan and does not mutate parent history.
16. Worker-local discretion cannot materially widen objective, scope, disclosure, effect, capability, cost, or authority semantics.
17. Material widening returns to IRR through an attributable continuation/escalation path.
18. New prerequisites do not automatically enter delegated scope or authority.
19. Recursive IRR Worker delegation is not allowed by default, while internal helper agents do not become nested IRR Workers merely by existing inside a Worker implementation.
20. Worker preserves Origin/Principal provenance and cannot relabel worker initiative as human Origin.
21. WorkerResult is attributable Worker-produced result material.
22. WorkerResult is not parent intent completion by itself.
23. WorkerResult is not factual truth, Governance Decision, Authorization, Observation, or Outcome by default; it is broader than any explicit Outcome record it may carry/reference.
24. Worker progress is distinct from WorkerResult completion and parent completion.
25. Worker escalation/need is not authority or scope expansion.
26. IRR retains ownership of the parent intent lifecycle and continuation/completion decision.
27. Worker completion assertions do not by themselves satisfy either the Delegated Completion Contract or the parent intent.
28. Expected deliverables and completion semantics are explicit when material.
29. Structurally complete deliverable does not prove every factual Claim true.
30. Worker identity/reputation does not amplify trust automatically.
31. Worker substitution cannot silently alter disclosure, capability, effect, cost, completion, or authority semantics.
32. Local/remote Worker placement does not exempt context disclosure/network effects from explicit boundaries.
33. Worker-created artifacts retain Worker/delegation provenance when material.
34. Delegated mutation remains represented effectful work subject to applicable capability/authority boundaries.
35. Research-like objectives do not implicitly authorize external disclosure.
36. Worker-generated code/patch/tool syntax is not execution or mutation authority.
37. Worker may propose successor semantics but cannot mint successor parent ResolvedIntent/WorkPlan or silently enter M0.7 Candidate Admission.
38. Material WorkerResult re-entry is explicit, attributable, and classified rather than ambient.
39. Worker-mediated external information preserves original-source and Worker-intermediary provenance when material.
40. WorkerResult cannot rewrite historical parent intent/work/authorization/effect state.
41. Cancellation/interruption does not erase prior effects or artifacts.
42. Worker retry/fallback/unknown-outcome algorithms remain M0.9 territory.
43. Worker failure does not prove parent intent invalidity, Denial, or global impossibility.
44. Fallback Worker cannot silently widen scope/disclosure/authority.
45. Multiple Workers have no implicit precedence or majority-is-truth rule.
46. Worker disagreement is not admitted Context Conflict by default.
47. Worker self-asserted privilege does not become privilege.
48. Worker internal memory is not canonical parent memory by default.
49. Worker internals may be complex while external delegation semantics remain bounded and inspectable.
50. Codexia is an example Worker, not an IRR core dependency.
51. M0.2/M0.3/M0.5/M0.6/M0.7 ownership remains preserved.
52. M0.9 failure/recovery, M1 schemas/runtime, and concrete M7 Codexia integration remain deferred.
53. No runtime code or `src/` tree is introduced.

## 68. M0.8 exclusions

M0.8 intentionally does NOT freeze:

- Python `Worker` protocols/classes;
- exact `DelegatedWork` fields;
- exact `DelegatedWorkHandoff` fields;
- exact `WorkerResult` fields;
- Worker progress/event schemas;
- exact worker lifecycle enum/state machine;
- worker process/transport protocol;
- worker discovery/registry implementation;
- worker scheduling/concurrency;
- nested delegation implementation;
- cancellation protocol;
- timeout values;
- retry/fallback algorithms;
- interrupted/unknown-outcome algorithms;
- WorkerResult persistence schemas;
- artifact digest/receipt formats;
- exact delegated authority references;
- disclosure-policy implementation;
- concrete CapabilityHandoff schema;
- Codexia adapter/API/CLI integration;
- Codexia internal authority/recovery models;
- model/vendor choices inside Workers;
- M1 runtime schemas;
- M7 concrete Worker integration.

M0.8 freezes the semantic boundary, not a worker orchestration stack.
