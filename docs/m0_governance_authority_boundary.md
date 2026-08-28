# M0.6 — Governance & Authority Boundary

Status: **normative for M0.6**.

This document freezes how Intent Resolution Runtime (IRR) presents bounded proposed work to an external Governance boundary, how Governance decisions relate to WorkPlans and downstream execution, and how Authorization remains separate from intent, semantic validity, capability admission, execution, and effect evidence.

It extends M0.1 Product Charter & Vocabulary, M0.2 Trust/Context/Resolution Semantics, M0.3 Intent → Work Boundary, M0.4 Late Binding & Observation Boundary, and M0.5 Capability Boundary without introducing runtime code, exact Python schemas, a concrete policy engine, consent implementation, executor adapters, or Outcome state machines.

M0.6 answers one question:

> How may bounded proposed work become eligible for downstream execution without allowing IRR to manufacture authority or silently rewrite the work being authorized?

The answer is:

> **IRR presents attributable proposed work. Governance decides authority. Authorization remains a separate bounded decision over exact work semantics. Effects remain downstream evidence, not proof of prior authority.**

```text
IntentRequest
     |
     v
    IRR
     |
     v
ResolvedIntent
     |
     v
 WorkPlan
     |
     v
WorkProposal
     |
     v
 Governance
  /    |      |       \
 v     v      v        v
allow deny constrain require_review
 |             |          |
 v             v          v
Authorization  IRR       no execution authority yet
 |          Continuation
 v             |
Handoff        v
 |       successor semantics
 v
Executor
 |
 +------> Effect
 |
 +------> attributable Outcome / returned data
```

The diagram shows conceptual decision paths, not a mutually exclusive wire enum. One Governance response may carry more than one decision component over explicitly distinct portions of proposed work, for example Authorization for an already represented read-only subset plus a Governance Constraint over a mutation remainder.

The central invariants are:

```text
intent != authorization
resolution != authorization
WorkPlan != authorization
WorkProposal != authorization
Governance decision != effect
Authorization != effect evidence
absence of Authorization != Denial
require_review != Authorization
Governance Constraint != Authorization by default
Governance Constraint != silent WorkPlan mutation
```

## 1. Governance is external to IRR

Governance is an external authority boundary.

IRR does not own the policy, consent, identity-authority, approval, institutional-control, or user-review mechanism by which proposed work becomes permitted.

IRR MAY present the semantic facts needed for an authority decision, including conceptually:

```text
requested scope
requested effects
affected resources
material data flow
recipient / destination when material
capability/provider semantics when material
uncertainty
provenance and lineage
```

IRR MUST NOT convert those facts into its own permission decision.

```text
inspectable work semantics != IRR-granted authority
```

## 2. Governance input is proposed work, not ambient machine state

M0.6 does not give Governance discovery powers to IRR.

The work and authority-relevant material presented by IRR must remain attributable and bounded under M0.1–M0.5.

If Governance requires additional identity, consent, organizational policy, account ownership, current session state, or another authority input, that material is supplied through an external Governance/Host boundary under the embedding system's rules.

IRR MUST NOT silently acquire ambient authority context merely because Governance would need it.

```text
need for authority evidence != authority to acquire authority evidence
```

## 3. WorkProposal

A `WorkProposal` is the attributable bounded operational work representation presented to Governance for an authority decision.

Conceptually, a WorkProposal refers to the exact proposed work semantics rather than creating a second independent plan.

A future WorkProposal representation must preserve enough information to identify at least conceptually:

```text
parent Intent / Resolution lineage
exact WorkPlan or bounded WorkStep subset under review
exact Capability Catalog / matching lineage where material
requested scope
requested effects
material affected resources or symbolic bounds
material data flow / disclosure
Completion Semantics where authority depends on them
material uncertainty or unresolved authority-relevant conditions
```

Exact field names, IDs, digests, canonicalization, and serialization are deferred to M1.

```text
WorkProposal != WorkPlan mutation
WorkProposal != Authorization
```

## 4. Proposal identity must be exact enough for authority binding

Authorization cannot safely bind to a vague natural-language summary while different underlying work is executed.

A future representation MUST preserve an exact attributable relation between the Governance decision and the work semantics reviewed.

The exact mechanism may later use immutable IDs, digests, canonical representations, lineage references, or another mechanism.

M0.6 freezes the semantic invariant:

```text
Authorization applies to reviewed work semantics
not merely to a lossy description of them
```

A display summary MAY be shown to a human reviewer, but the summary is not the sole source of truth when it omits material scope, effects, recipients, data flow, provider boundaries, or other authority-relevant semantics.

```text
human-readable summary != authority-binding semantic identity
```

## 5. WorkProposal is not automatically required for non-operational resolution

A ResolvedIntent that completes as an answer, explanation, no-operational-work result, or another non-operational path does not require IRR to manufacture a WorkProposal merely because Governance exists in the architecture.

M0.6 governs proposed operational work.

A Host may impose additional product-level review around non-operational behavior, but that is not an IRR requirement frozen here.

## 6. Governance Decision

A `Governance Decision` is an attributable external decision about whether bounded proposed work may proceed under stated authority conditions.

M0.6 freezes four conceptual decision classes:

```text
authorize
deny
constrain
require_review
```

These names are conceptual semantics, not a frozen enum or wire format, and they are not required to be mutually exclusive components of one Governance response.

For example, one Governance response may explicitly:

```text
authorize:
    already represented read-only inspection subset

constrain:
    mutation/extraction remainder
```

The Authorization component covers only the stated subset. The Governance Constraint component does not itself authorize the constrained successor work.

```text
Governance Constraint != Authorization by default
```

A Governance Decision is not itself an Effect or Outcome.

```text
Governance Decision != execution result
```

## 7. Authorization

`Authorization` is an attributable Governance decision permitting explicitly bounded proposed work under stated conditions.

Authorization may cover one exact proposal, one bounded subset already represented inside a proposal, or another explicitly bounded authority scope supported by a later Governance contract.

M0.6 does not require every future permission mechanism to be one-shot. Standing grants, leases, delegated authority tokens, organizational policy grants, or reusable bounded permissions may exist later, but IRR never invents them and every use must establish that the concrete proposed work falls within the externally granted scope.

```text
Authorization != ambient general permission
```

Exact reusable-grant mechanics are deferred.

## 8. Authorization is separate from the WorkPlan

A WorkPlan remains a semantic work representation.

Governance MUST NOT cause IRR to rewrite the historical WorkPlan with fields whose semantics imply IRR-owned authority, such as:

```text
approved = true
safe = true
permission_granted = true
user_consented = true
```

Authorization remains a separate attributable authority object/decision linked to the work it covers.

```text
WorkPlan validity != Authorization
Authorization != WorkPlan field mutation
```

## 9. Authorization scope is bounded

Authorization MUST NOT be treated as broader than the work scope it actually covers.

Material authority scope may include conceptually:

- exact WorkProposal or WorkStep subset;
- affected resources or bounded resource class;
- recipient or destination;
- requested effect surface;
- data disclosure boundary;
- executor/provider identity when authority-relevant;
- capability semantics when authority-relevant;
- allowed timing or validity conditions;
- count/one-shot limits or another externally defined bounded condition.

Exact scope language is deferred.

```text
Authorization for A != Authorization for related B
```

## 10. No authority amplification

IRR and downstream execution MUST NOT silently amplify one Authorization into another.

Examples:

```text
read authorization != mutation authorization
local mutation authorization != external disclosure authorization
authorization for recipient A != authorization for recipient B
authorization for one resource != authorization for neighboring resources
authorization for prerequisite != authorization for downstream effect
authorization for provider A != provider B when provider identity is material
```

A relationship between work items does not create transitive authority.

```text
work dependency != authority inheritance
```

## 11. Origin and Principal do not create Authorization

M0.1 remains in force:

```text
origin != authority
principal != permission
```

A human-originated IntentRequest does not automatically become a Governance Authorization merely because a human produced it.

Likewise, a companion-, worker-, or system-originated request does not inherit the Principal's authority merely because it serves that Principal.

```text
human intent != Authorization by default
companion intent != delegated authority by default
```

An embedding system MAY treat a particular attributable human action as sufficient evidence or as the event that creates Authorization under its explicit Governance mechanism. When it does so, the authority classification is made by Governance, not inferred by IRR from natural-language intent alone.

## 12. A textual "yes" is not automatically an Authorization

A user utterance such as:

```text
"yes"
"do it"
"go ahead"
```

may be relevant to an external consent or approval mechanism.

IRR MUST NOT treat text alone as an authority token without the Host/Governance boundary establishing what proposal the response refers to, who is authorized to approve it, and what authority semantics the response has.

```text
approval-like text != Authorization by itself
```

This prevents conversational ambiguity from silently becoming execution authority.

## 13. Authorization provenance

Authorization is attributable authority material.

A future Authorization representation must preserve enough provenance to know conceptually:

```text
which Governance boundary produced it
what authority context or mechanism it used when material
what proposal/work semantics it covers
what conditions apply
when its validity matters
```

Authorization provenance does not itself prove that the Governance mechanism was correct or secure; it preserves what authority basis was claimed.

Exact identity and cryptographic mechanisms are deferred.

## 14. Authorization may be time-bounded

Authorization is not automatically timeless.

A Governance decision may be subject to explicit temporal or session conditions.

IRR and downstream components MUST NOT silently treat an expired, stale, revoked, or otherwise no-longer-applicable Authorization as permanent permission.

```text
Authorization != timeless permission
```

Exact TTL, lease, revocation, session, and freshness mechanisms are deferred.

## 15. Authorization Condition

An `Authorization Condition` is a Governance-imposed authority condition that can be applied without changing the admitted semantic meaning of the WorkProposal.

Examples may include conceptually:

```text
valid only until time T
one use only
requires execution through already-admitted provider P
requires an external approval receipt to remain valid
```

An Authorization Condition does not silently alter requested work semantics.

```text
Authorization Condition != semantic WorkPlan mutation
```

If satisfying the condition would materially change resource, recipient, effect, data flow, provider semantics, Completion Semantics, or another admitted meaning, it is not merely an Authorization Condition; it becomes a semantic Governance Constraint under the following sections.

## 16. Governance Constraint

A `Governance Constraint` is an attributable Governance decision requiring narrower or otherwise changed operational semantics before work may proceed.

A Governance Constraint alone does not grant permission for the constrained successor semantics. A Governance response MAY separately contain an Authorization component for an already represented subset, but the two authority roles remain distinct.

```text
Governance Constraint != Authorization by default
```

Example:

```text
proposal:
    inspect archive and extract it

Governance:
    reading/inspection may proceed,
    extraction/mutation may not
```

If accepting the Governance decision means the requested operational semantics change, the prior WorkPlan MUST NOT be edited silently.

```text
Governance Constraint != in-place WorkPlan rewrite
```

## 17. Semantic Governance Constraint returns to IRR

A semantic Governance Constraint is input to IRR Continuation or another explicit successor-resolution path.

Conceptually:

```text
WorkProposal v1
      |
      v
Governance Constraint
      |
      v
IRR Continuation
      |
      v
Successor ResolvedIntent
      |
      v
Successor WorkPlan v2
```

The successor preserves lineage to the original intent, proposal, and Governance decision.

The Governance Constraint does not itself become a successor WorkPlan.

```text
Governance Constraint != Successor WorkPlan
```

IRR still validates semantics, ambiguity, capabilities, Binding rules, and other applicable contracts before admitting successor work.

Any authority required for executable successor work remains external. The Constraint itself is not reused as implicit Authorization for the successor plan.

## 18. Constraining work is not hidden reinterpretation of intent

If Governance permits only a subset or narrower form of the requested work, IRR MUST preserve that semantic change explicitly.

It MUST NOT claim that the original full objective was satisfied merely because a constrained subset was authorized or executed.

```text
constrained work completion != original intent satisfaction by default
```

The parent lifecycle may later require clarification, explicit acceptance of the smaller objective, a successor resolution, or another continuation under later lifecycle contracts.

## 19. Partial Authorization of already represented work

Governance MAY authorize an explicitly identified bounded subset of an existing WorkProposal when that subset is already semantically represented and can proceed without pretending that the remaining work is authorized.

For example, a plan may already contain separate bounded read-only inspection steps followed by a mutation step. Governance may authorize only the inspection steps.

This does not mutate the WorkPlan and does not make the full WorkPlan authorized.

```text
Authorization of subset != Authorization of whole plan
```

If Governance intends the subset to become the **new objective** rather than merely the currently authorized portion of the original objective, that is a semantic constraint and requires successor semantics under sections 16–18.

## 20. Denial

`Denial` is an explicit attributable Governance decision that the reviewed work may not proceed under the stated authority context.

Denial is not a semantic claim that the IntentRequest is malformed, false, irrational, unsupported by capabilities, or globally forbidden forever.

```text
Denial != semantic invalidity
Denial != missing_capability
Denial != global impossibility
```

Denial blocks execution under the authority context it covers.

## 21. Denial does not mutate historical intent or work

A Denial does not erase the IntentRequest, ResolvedIntent, WorkPlan, or WorkProposal from history.

Those remain attributable records of what was requested and resolved.

```text
Denial != delete proposal history
```

Later lineage may record that execution did not proceed because Governance denied it.

Exact persistence/audit schemas are deferred.

## 22. No denial bypass through hidden substitution

IRR and downstream components MUST NOT evade a Denial by silently changing:

- provider;
- executor;
- capability;
- resource;
- recipient;
- effect;
- scope;
- timing;
- external service;
- implementation technique.

A materially changed proposal is successor work and requires its own resolution/capability/governance path.

```text
Denial != permission to policy-shop
```

## 23. Absence of Authorization is not Denial

A proposal may have no Authorization because:

- Governance has not reviewed it;
- review is pending;
- authority evidence is missing;
- the decision is unknown or unavailable;
- an applicable grant has expired;
- no Governance decision has yet been produced.

Those states are not automatically an explicit Denial.

```text
no Authorization != Denial
```

However, absence of sufficient Authorization remains fail-closed for downstream execution requiring authority.

```text
not proven authorized -> no authority-requiring execution
```

This does not freeze one universal Host policy that every non-operational or internal computation requires Governance; it freezes only that work requiring authority cannot proceed on an unproven permission assumption.

Exact pending/unknown authority state enums are deferred.

## 24. require_review

`require_review` is a Governance decision or state indicating that additional external review is required before Authorization may exist.

It is not Authorization and does not predict eventual approval.

```text
require_review != Authorization
require_review != eventual approval
```

Downstream execution MUST NOT treat a review requirement as permission to proceed optimistically.

## 25. Review result must remain attributable

When a human, organization, policy service, or another authority source completes required review, the resulting Governance decision must remain attributable to that review boundary.

IRR may consume the resulting decision for continuation or handoff coordination, but IRR does not become the authority source merely because it receives the decision.

## 26. Governance may use policy; IRR is not the policy engine

An external Governance implementation may use:

- static rules;
- human review;
- organizational policy;
- consent state;
- delegated authority;
- identity/role checks;
- risk/effect metadata;
- combinations of these or other mechanisms.

M0.6 does not freeze their algorithms.

IRR's responsibility is to preserve the work semantics Governance needs and to respect the returned authority decision.

```text
IRR authority boundary != policy engine implementation
```

## 27. Descriptive risk labels do not decide authority inside IRR

M0.5 remains in force.

A WorkProposal may include or refer to descriptive effect/risk metadata, but IRR MUST NOT interpret labels such as:

```text
low_risk
read_only
local
trusted_provider
```

as automatic Authorization.

Governance may use such metadata under its own rules.

```text
risk label != IRR permission decision
```

## 28. Capability admission and Authorization remain separate

A compatible Capability proves only that the planned Semantic Operation can be represented by an admitted capability contract.

It does not prove that the operation is permitted.

Likewise, Authorization does not create a Capability that is absent from the applicable Catalog.

```text
Capability Match != Authorization
Authorization != Capability existence
Authorization != Capability Availability
```

Both capability compatibility and sufficient authority may be required before execution.

## 29. missing_capability is not repaired by Authorization

If the exact applicable Catalog Snapshot has no compatible Capability for required work, Governance approval cannot make the nonexistent capability contract appear.

```text
Authorization + missing_capability != executable WorkStep
```

A later Catalog extension may permit successor planning under M0.5, but it does not retroactively make the earlier proposal capability-supported.

## 30. Availability is not repaired by Authorization

A valid Authorization does not prove the executor/provider is currently available or that one concrete invocation is ready.

```text
authorized != available
Authorization != invocation readiness
```

Execution may remain blocked despite valid authority.

Exact scheduling/waiting behavior is deferred.

## 31. Binding before Governance

M0.6 does not require every symbolic value to be concrete before Governance review.

Governance MAY authorize work expressed over bounded symbolic semantics when its authority mechanism explicitly covers those bounds.

For example, a policy may authorize read-only inspection of whichever artifact is selected by an already admitted bounded rule inside a declared directory.

This is not automatic; authority scope must actually cover that symbolic class/rule.

```text
symbolic work != automatically ungovernable
```

Exact policy semantics remain external.

## 32. Binding after Authorization

If a Symbolic Reference binds after Authorization, the Bound Value does not gain authority merely because Binding succeeded.

The concrete value must remain within the Authorization scope.

```text
Binding success != Authorization expansion
```

If binding reveals a resource, recipient, scope, disclosure, provider, effect, or other authority-relevant fact not covered by the existing Authorization, execution requires Governance re-review or successor authority as applicable.

## 33. Concrete binding may require re-review without semantic change

A Bound Value can remain semantically valid under M0.4/M0.5 while still falling outside the scope of an earlier Authorization.

This is an authority-coverage problem, not necessarily a semantic-resolution problem.

```text
semantic validity != authority coverage
```

If the binding itself does not change semantic meaning, IRR need not manufacture a successor WorkPlan merely because Governance needs to review the newly concrete resource.

The same WorkProposal semantics may be presented again with additional concrete authority-relevant detail under a later representation contract.

Exact re-review identity mechanics are deferred.

## 34. Rebinding does not inherit Authorization silently

A Rebinding to a materially different concrete value MUST NOT silently inherit authority granted for an earlier concrete value unless the Authorization explicitly covered the bounded class that includes both.

```text
Authorization for bound value A != Authorization for rebound value B by default
```

Historical binding and authority lineage must remain distinguishable.

## 35. Capability Drift after Authorization

A material Capability Drift event may change the work semantics on which Authorization depended.

Existing Authorization MUST NOT silently transfer to materially different capability semantics.

Examples include changed:

- effect surface;
- provider boundary;
- data disclosure behavior;
- scope model;
- result/completion semantics.

```text
Authorization over capability semantics v1
    !=
Authorization over materially changed capability semantics v2
```

The path may require capability revalidation, IRR Continuation, Governance re-review, or successor work under later lifecycle contracts.

## 36. Availability Drift is different

A capability becoming temporarily unavailable does not by itself change what was authorized.

```text
availability drift != automatic authority revocation
```

Whether a particular Authorization contains conditions tied to availability, session, time, or provider state belongs to its explicit authority conditions.

M0.6 keeps semantic/authority drift distinct from pure availability state.

## 37. Provider or Executor substitution after Authorization

A different provider/executor MUST NOT inherit Authorization silently when identity or execution boundary is material to the authority decision.

If the Authorization explicitly covers a provider-independent capability class and substitution preserves all material semantics, a later Governance contract may allow it.

Otherwise:

```text
provider substitution != authority inheritance
```

M0.5 semantic equivalence and M0.6 authority coverage are both required.

## 38. Data-flow and disclosure changes are authority-relevant

A WorkProposal must make material data flow and external disclosure inspectable enough for Governance to evaluate them.

If a later implementation, binding, capability substitution, or successor plan introduces a new disclosure destination or data flow not covered by Authorization, the old Authorization does not expand automatically.

```text
new disclosure != inherited Authorization
```

This extends the M0.3/M0.5 prohibition on hidden effect-changing substitution.

## 39. Recipient changes are authority-relevant

Authorization to disclose or send data to one recipient does not automatically cover another recipient merely because the same file and capability are involved.

```text
recipient A authorization != recipient B authorization
```

A changed recipient that also changes intent semantics requires IRR Continuation; even when semantic intent already permitted a bounded interchangeable recipient class, Governance authority must still cover the concrete recipient or admitted class.

## 40. Authorization and Handoff

A Handoff transfers bounded proposed work to a downstream boundary.

Handoff is still not Authorization.

A later CapabilityHandoff or other executor-bound handoff may carry or reference external Authorization evidence, but the handoff itself MUST NOT manufacture or widen that authority.

```text
Handoff != Authorization
Handoff carrying Authorization != Handoff-created Authorization
```

Exact handoff schemas are deferred to later milestones.

## 41. Executor must enforce authorization coverage at its boundary

M0.6 does not implement an Executor, but it freezes the downstream contract needed to preserve separation of authority and effect.

An Executor MUST NOT treat proposed work as authorized merely because IRR produced it.

Before an authority-requiring effect, the downstream path must establish that applicable Authorization covers the concrete operation under the relevant conditions.

```text
IRR output != executor permission
```

Exact executor verification mechanics are deferred.

## 42. Authorization does not prove execution

An authorized operation may never execute because:

- the capability becomes unavailable;
- the invocation is not ready;
- the user cancels;
- the process crashes;
- the handoff never occurs;
- downstream validation fails;
- another condition blocks execution.

Therefore:

```text
Authorization != Effect
Authorization != Outcome
Authorization != successful completion
```

## 43. Effect does not prove Authorization

The fact that an Effect occurred does not prove that it was authorized.

A buggy or unauthorized Executor may perform an effect.

```text
Effect != proof of Authorization
```

Outcome/effect evidence must not be retroactively converted into prior permission.

```text
effect evidence != retroactive Authorization
```

## 44. Authorization does not become effect evidence

Likewise, an Authorization record proves only that Governance permitted bounded work under stated conditions.

It does not prove that the work was attempted, completed, or produced the intended effect.

```text
Authorization != effect evidence
```

This distinction is normative and survives all later lifecycle contracts.

## 45. Post-hoc approval does not rewrite history

If an effect occurred before sufficient Authorization, a later approval or policy change MUST NOT rewrite the historical record to claim that the earlier effect was authorized at the time.

A later Governance decision may affect future actions, remediation, acknowledgement, or other external handling, but historical authority lineage remains truthful.

```text
later approval != retroactive historical Authorization
```

## 46. Outcome is not Governance Decision

An Executor or Worker Outcome reports what happened or what was observed downstream.

Governance Decision reports what authority was granted or denied.

Even if one external system produces both records, their semantic roles remain distinct.

```text
Outcome != Governance Decision
```

Exact Outcome states remain M0.9.

## 47. Authorized observation does not grant authority over observed resources

Authorization to perform a bounded observation/read effect does not automatically create authority to mutate, disclose, execute, or otherwise act on resources discovered by that observation.

Example:

```text
authorized:
    filesystem.search(scope=D:\Backups)

observed:
    backup-42.zip
```

This does not imply:

```text
authorized:
    delete backup-42.zip
    upload backup-42.zip
    execute backup-42.zip
```

```text
authorized observation effect != authority over observed resources
```

## 48. Authorization to acquire data does not authorize downstream disclosure

A Governance decision allowing data acquisition/read does not automatically authorize sending that data to another provider, service, model, recipient, or account.

```text
read authority != disclosure authority
```

Provider Disclosure under M0.2 and external effects under M0.5/M0.6 remain separately governed when material.

## 49. Cognitive Provider cannot grant authority

A Cognitive Provider may propose:

```text
"This work seems safe."
"The user probably wants this."
"I recommend approving it."
```

Those statements do not create Authorization.

```text
provider recommendation != Governance Decision
provider confidence != Authorization
```

M0.7 freezes the broader provider contract.

## 50. Worker cannot self-authorize parent intent

A Worker performing delegated work does not acquire authority to widen the parent WorkProposal or authorize new parent effects merely because the Worker believes they are useful.

Worker delegation remains subordinate to M0.8 contracts.

```text
worker judgment != parent Authorization
```

## 51. Governance Constraint cannot create hidden capabilities

A Governance Constraint may narrow or condition work, but it does not create missing capabilities.

If successor semantics require a capability absent from the applicable Catalog, M0.5 `missing_capability` semantics apply.

```text
Governance Constraint != capability synthesis
```

## 52. Governance Authorization cannot bypass semantic ambiguity

Authorization does not repair an unresolved Material Ambiguity in IRR semantics.

If the work itself is not sufficiently determined for a bounded path, Governance cannot make an ambiguous proposal semantically precise merely by saying “approved.”

```text
Authorization != ambiguity resolution
```

Governance may provide new attributable constraint/selection information through an explicit boundary, but IRR must then admit the resulting semantics under M0.2/M0.4 rather than treating approval as a magic semantic choice.

## 53. Governance cannot make incompatible Capability Match valid

Likewise, Governance cannot declare a semantically incompatible Capability to be compatible with a WorkStep merely by authorizing the effect.

```text
Authorization != Capability Match override
```

Capability semantics remain an IRR validation concern under M0.5.

## 54. Multiple authority requirements do not compose automatically

Some work may require more than one authority condition or approval source.

Satisfying one requirement does not automatically satisfy all others.

```text
Authorization A != Authorization B
one approval != all required approvals
```

Exact multi-party consent, quorum, role, organizational, and policy-composition mechanisms are deferred to Governance implementations.

IRR MUST NOT infer authority composition that Governance has not established.

## 55. Governance output may itself be unavailable or uncertain

IRR may encounter no usable Governance decision because the external authority service is unavailable, a reviewer has not responded, or decision provenance is insufficient.

M0.6 does not collapse those cases into Denial or Authorization.

```text
unknown authority state != Denial
unknown authority state != Authorization
```

Execution remains fail-closed where authority is required.

Exact timeout/retry semantics remain M0.9 or later integration contracts.

## 56. Revocation does not rewrite past effects

A future Governance implementation may revoke an Authorization or invalidate a reusable authority grant.

Revocation changes future authority applicability; it does not erase the historical fact that an earlier effect may have been authorized at the time it occurred.

```text
revoked now != unauthorized historically by definition
```

Exact revocation representation is deferred.

## 57. Successor WorkPlan does not inherit Authorization silently

When IRR Continuation produces a Successor WorkPlan with materially changed work semantics, prior Authorization MUST NOT silently apply to it unless the external Governance decision explicitly covered the broader bounded successor semantics.

Default invariant:

```text
Authorization for WorkPlan v1
    !=
Authorization for materially changed WorkPlan v2
```

A successor plan must preserve lineage to both the prior plan and relevant Governance Constraint/decision.

## 58. Non-material representation changes need not create new work semantics

A purely representational reserialization, display reformatting, or other non-semantic change does not by itself make the underlying work materially different.

M0.6 does not require authority re-review solely because bytes or presentation changed if the exact semantic identity mechanism later proves the reviewed work is unchanged.

```text
representation change != semantic work change by default
```

Exact canonical identity/digest rules remain deferred.

## 59. Semantic mutation after Authorization is forbidden

Once Authorization is bound to reviewed work semantics, downstream components MUST NOT mutate the semantics and reuse the same Authorization as if nothing changed.

Forbidden hidden changes include:

- widening scope;
- changing recipient;
- adding disclosure;
- changing effect class;
- changing a material provider boundary;
- adding extra mutation;
- weakening or changing Completion Semantics materially;
- adding unrelated prerequisite work.

```text
semantic mutation != authorized work
```

Material changes return through successor IRR/Governance paths.

## 60. WorkProposal summaries must not hide uncertainty

If uncertainty, unresolved authority-relevant provenance, symbolic scope, incomplete resource identity, or another fact is material to Governance, the proposal surface MUST preserve it rather than present a falsely concrete summary.

```text
proposal presentation != uncertainty erasure
```

This extends M0.2 epistemic rules into the authority boundary.

## 61. Governance does not convert uncertainty into truth

A Governance decision may permit work despite acknowledged uncertainty under external policy.

That does not make the underlying Claim, resource state, provider state, or predicted effect true.

```text
Authorization != factual truth
```

Epistemic Trust and authority remain separate.

## 62. Governance Denial does not prove danger

A Denial may arise for many reasons: policy, missing consent, organizational rule, timing, budget, scope, user preference, or another authority reason.

IRR MUST NOT relabel denied work as semantically `unsafe` or factually dangerous unless independent evidence supports such a Claim.

```text
Denial != factual danger verdict
```

## 63. Governance Authorization does not prove safety

Likewise:

```text
Authorization != safety guarantee
```

Governance may authorize work under accepted risk, imperfect information, or a policy decision.

IRR must preserve the semantic distinction.

## 64. Backup scenario

Intent:

```text
"Find the newest organism_lab backup in D:\Backups,
extract it to W:\organism_lab,
and launch the project."
```

Suppose IRR resolves and capability-binds:

```text
filesystem.search
artifact.select
archive.inspect
archive.extract
workspace.inspect
process.launch
```

The WorkProposal may expose conceptually:

```text
read D:\Backups
select artifact by admitted rule
write/extract to W:\organism_lab
inspect resulting workspace
launch process from selected workspace
```

Governance may authorize all bounded work, deny all work, require review, or constrain it.

If Governance says:

```text
"inspection is permitted, extraction and launch are not"
```

that decision must not silently turn the original plan into “inspect only.”

Governance may authorize the already represented inspection subset for immediate execution, while the semantic constraint that “inspect only” becomes a successor objective only through explicit IRR Continuation if that smaller objective is adopted.

## 65. Telegram scenario

Intent:

```text
"Send the latest Voice Engine report to me in Telegram."
```

The WorkProposal must make the material disclosure visible:

```text
selected report
external Telegram recipient
data leaves local boundary
network/external disclosure effect
```

Authorization to read/select the report does not authorize Telegram disclosure.

Authorization to send to one Telegram account does not automatically authorize another account.

If the recipient changes after Binding, existing authority must explicitly cover that recipient/class or Governance re-review is required.

## 66. Companion-originated scenario

A companion proposes:

```text
"We should inspect the latest failed experiment reports."
```

IRR preserves:

```text
origin = companion
```

If the resulting WorkProposal requires filesystem reads, companion origin does not become human permission.

An external Governance mechanism may decide that bounded read-only inspection is allowed under a standing grant, requires human review, or is denied.

IRR does not manufacture that authority.

## 67. Relationship to M0.5 Capability Boundary

M0.5 asks:

```text
Can this work be represented by admitted capability contracts?
```

M0.6 asks:

```text
May this exact proposed work proceed under external authority?
```

Neither answer determines the other.

```text
Capability Match != Authorization
Authorization != Capability Match
```

## 68. Relationship to M0.4 Binding

Binding concretizes values under fixed semantics.

Governance decides whether the resulting bounded work is covered by authority.

A Binding may be reviewed before or after concretization depending on external authority scope; M0.6 does not freeze one universal ordering.

```text
Binding != Authorization
Authorization != Binding
```

## 69. Relationship to M0.7 Cognitive Provider

M0.7 may allow a Cognitive Provider to propose candidate resolution/work semantics.

The provider does not become Governance and cannot create Authorization.

Catalog/context disclosure to a provider remains separately governed.

## 70. Relationship to M0.8 Worker Delegation

M0.8 will freeze CapabilityHandoff versus DelegatedWorkHandoff.

M0.6 freezes only that delegated work and worker-side effects remain subject to applicable external authority, and Worker judgment does not widen parent authority.

Exact delegated authority envelopes belong to M0.8.

## 71. Relationship to M0.9 Failure & Recovery

M0.9 will freeze retry, failure, unknown-outcome, and recovery semantics.

M0.6 freezes that a retry is not newly authorized merely because the original attempt was authorized.

Whether the same Authorization may cover a retry depends on its explicit authority scope and later recovery contract.

```text
original Authorization != automatic retry Authorization
```

An unknown Outcome does not create fresh authority to repeat an effectful operation.

## 72. M0.6 exclusions

M0.6 intentionally does NOT freeze:

- Python classes, enums, protocols, or serialization;
- exact `WorkProposal` fields;
- exact `GovernanceDecision` representation;
- exact `Authorization` fields, IDs, digests, or signatures;
- exact authority-scope expression language;
- policy algorithms;
- consent UX or consent-state model;
- identity/role/organization providers;
- delegated authority token formats;
- standing-grant, lease, TTL, revocation, or session mechanics;
- exact human-review workflow;
- exact multi-party/quorum approval composition;
- exact risk taxonomy;
- exact Governance-to-IRR transport;
- exact Authorization-to-Executor transport;
- exact Handoff schema;
- exact re-review state machine;
- exact persistence, audit, receipt, or cryptographic format;
- runtime adapters;
- Worker delegation details;
- retry/recovery algorithms;
- terminal Outcome schemas.

M0.6 freezes authority semantics and lineage constraints, not a policy implementation.

## 73. Acceptance criteria

M0.6 is complete when the repository states unambiguously that:

1. Governance is an external authority boundary and IRR does not own policy, permission, consent, or effects.
2. IRR presents bounded attributable proposed work rather than manufacturing authority decisions.
3. WorkProposal is distinct from WorkPlan and Authorization while remaining attributable to exact reviewed work semantics.
4. A lossy human-readable summary cannot silently replace the authority-binding semantic identity of proposed work.
5. Non-operational resolution does not require IRR to manufacture a WorkProposal.
6. Governance decisions conceptually distinguish authorize, deny, constrain, and require_review without freezing a wire enum; decision components are not required to be mutually exclusive, and Governance Constraint is not Authorization by default.
7. Authorization is an attributable external decision permitting bounded work under stated conditions.
8. Authorization remains separate from WorkPlan/Capability Descriptor state and is not represented as IRR-owned `approved=true` semantics.
9. Authorization scope is bounded and does not amplify transitively across related work.
10. Work dependencies do not create authority inheritance.
11. Origin and Principal identity do not themselves create Authorization.
12. Human-originated intent is not Authorization by default.
13. Approval-like conversational text becomes authority only when an explicit Governance mechanism establishes its proposal binding and authority semantics.
14. Authorization provenance and authority scope remain attributable.
15. Authorization is not automatically timeless; stale/expired/revoked applicability cannot be assumed.
16. Authorization Conditions may constrain authority applicability without changing work semantics.
17. A condition that materially changes work meaning is a Governance Constraint rather than an authority-only condition.
18. Governance Constraint does not mutate a WorkPlan in place.
19. Semantic Governance Constraints return through IRR Continuation/successor semantics with lineage.
20. Governance Constraint itself is neither Authorization nor a Successor WorkPlan and does not bypass IRR validation.
21. Constrained subset completion does not automatically satisfy the original full intent.
22. Governance may authorize an explicitly represented bounded subset without thereby authorizing the full WorkPlan.
23. Treating a subset as the new objective requires explicit successor semantics.
24. Denial is an explicit authority decision distinct from semantic invalidity, missing capability, and global impossibility.
25. Denial does not erase historical intent/work lineage.
26. Denial cannot be bypassed by hidden provider/capability/resource/effect substitution.
27. Absence of Authorization is distinct from Denial while remaining fail-closed for authority-requiring execution.
28. require_review is not Authorization and does not imply eventual approval.
29. Review outcomes remain attributable to the external authority boundary that produced them.
30. Governance may use policy/rules/human review externally, but IRR is not the policy engine.
31. Descriptive risk/effect labels do not become IRR permission decisions.
32. Capability Match and Authorization remain separate requirements.
33. Authorization does not create missing Capability contracts.
34. Authorization does not prove Capability Availability or invocation readiness.
35. Governance may authorize bounded symbolic work when its external authority scope explicitly covers the symbolic class/rule.
36. A later Bound Value does not expand Authorization automatically.
37. A semantically valid concrete binding may still require Governance re-review because authority coverage is narrower than semantic validity.
38. Governance re-review of a concrete Bound Value does not require a successor WorkPlan when semantic meaning did not change.
39. Rebinding does not inherit value-specific Authorization silently.
40. Material Capability Drift does not inherit prior Authorization silently.
41. Pure Availability Drift is semantically distinct from authority drift unless explicit Authorization Conditions say otherwise.
42. Provider/executor substitution does not inherit authority when identity/boundary is material.
43. New data-flow/disclosure or recipient semantics do not inherit prior Authorization silently.
44. Handoff remains distinct from Authorization even when it carries/references authority evidence.
45. Executor-bound work must establish applicable Authorization rather than treating IRR output as permission.
46. Authorization does not prove execution, Outcome, or successful completion.
47. Effect/Outcome evidence does not prove prior Authorization.
48. Later approval does not retroactively rewrite an earlier unauthorized effect as historically authorized.
49. Outcome and Governance Decision remain distinct semantic roles.
50. Authorized observation/read does not grant authority over resources merely discovered by that observation.
51. Read/data-acquisition authority does not automatically authorize downstream disclosure.
52. Cognitive Provider recommendation/confidence cannot create Authorization.
53. Worker judgment cannot self-authorize widened parent effects.
54. Governance Constraint cannot create missing capabilities.
55. Authorization cannot bypass unresolved Material Ambiguity.
56. Authorization cannot override an incompatible Capability Match.
57. Multiple authority requirements do not compose automatically merely because one approval exists.
58. Unknown/pending Governance state is neither Authorization nor Denial and remains fail-closed when authority is required.
59. Revocation changes future applicability without rewriting past authority/effect history.
60. A materially changed Successor WorkPlan does not silently inherit prior Authorization.
61. Purely representational non-semantic changes do not necessarily invalidate authority when later identity mechanisms prove semantics unchanged.
62. Semantic mutation after Authorization cannot reuse the old Authorization silently.
63. WorkProposal presentation preserves material uncertainty rather than erasing it for review.
64. Authorization does not establish factual truth or safety.
65. Denial does not establish factual danger.
66. Capability, Binding, Governance, Cognitive Provider, Worker, and failure/recovery boundaries remain compositionally distinct.
67. Original Authorization does not automatically authorize effectful retry; M0.9 owns retry/recovery semantics.
68. M0.7+, M0.8+, M0.9+, and M1 implementation details remain explicitly deferred.
69. No runtime code or `src/` tree is introduced.
