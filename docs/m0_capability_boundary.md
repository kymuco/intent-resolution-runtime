# M0.5 — Capability Boundary

Status: **normative for M0.5**.

This document freezes how Intent Resolution Runtime (IRR) relates semantic operational work to an externally supplied Capability Catalog, how missing capabilities fail closed, what capability metadata means, and how capability availability or drift may affect already-resolved work.

It extends M0.1 Product Charter & Vocabulary, M0.2 Trust/Context/Resolution Semantics, M0.3 Intent → Work Boundary, and M0.4 Late Binding & Observation Boundary without introducing runtime code, exact Python schemas, execution adapters, Governance policy, or authority.

M0.5 answers one question:

> How may IRR plan bounded operational work without inventing execution powers that were never supplied to it?

The answer is:

> **IRR plans only against an explicit, bounded, attributable Capability Catalog snapshot.**

```text
Semantic Operation
       |
       v
Capability Catalog Snapshot
       |
       +--------------------------+
       |                          |
       v                          v
compatible Capability       no compatible Capability
       |                          |
       v                          v
bounded WorkStep          missing_capability
       |
       v
proposed work only
       |
       v
Governance / downstream execution
```

The central invariants are:

```text
semantic operation != capability
catalog membership != availability
availability != authorization
capability metadata != permission
missing capability != fallback authority
```

## 1. Capability boundary is externally supplied

IRR does not discover its own execution powers.

The Host or another explicit embedding boundary supplies the Capability Catalog applicable to a resolution.

IRR MUST NOT silently:

- scan installed programs;
- inspect shell commands;
- enumerate browser automation APIs;
- discover plugins;
- query service registries;
- inspect a Runplane installation;
- probe worker tools;
- search PATH;
- infer capabilities from operating-system conventions;
- construct capabilities from ambient machine state.

A capability surface is therefore explicit input, not ambient context.

```text
capability catalog != ambient capability discovery
```

If an embedding system wishes to build a Catalog from its environment, that discovery occurs outside IRR and enters IRR through an explicit attributable boundary.

## 2. Semantic Operation versus Capability

A `Semantic Operation` describes what work is requested.

A `Capability` describes a bounded operation contract that an external execution environment can potentially provide.

They are related but not identical.

For example:

```text
Semantic Operation:
    archive.extract

Capability:
    a catalog-defined bounded contract that can accept
    an archive input and destination and can produce
    the represented extraction effect surface
```

The same semantic operation may be unsupported, supported by one Capability, or supported by several materially equivalent or materially different Capability definitions.

A Capability may intentionally use the same human-readable label as a Semantic Operation. Matching text does not collapse the two semantic roles.

```text
semantic operation != capability
same textual label != same semantic object
capability != implementation command
```

A Capability MUST NOT be treated as a shell command, arbitrary code fragment, or opaque invitation to execute anything needed to achieve a goal.

## 3. Capability Catalog

A `Capability Catalog` is the explicit attributable set of Capability definitions admitted for a resolution or continuation.

The Catalog defines the capability surface against which IRR is allowed to plan.

It is not necessarily a statement about every operation the wider machine, account, network, or ecosystem could theoretically perform.

Therefore:

```text
catalog scope != global environment capability
```

IRR MUST NOT widen the applicable Catalog merely because a required operation is absent.

## 4. Applicable Catalog Snapshot

A `Catalog Snapshot` is the exact bounded version of the Capability Catalog used for a resolution or planning decision.

Every admitted WorkPlan containing operational WorkSteps MUST remain attributable to the exact Catalog Snapshot used to validate those WorkSteps.

Each capability-bound WorkStep must also remain attributable to the specific admitted Capability contract that justified the match within that snapshot. Exact representation of that relationship is deferred.

A future representation must preserve enough identity to distinguish one materially different snapshot or capability contract from another.

Exact snapshot IDs, digests, serialization, canonicalization, matched-descriptor references, and persistence are deferred to M1.

The semantic invariant is frozen now:

```text
WorkPlan capability meaning
    is attributable to
exact applicable Catalog Snapshot
and admitted capability contracts within it
```

A later Catalog MUST NOT silently retroactively reinterpret a prior WorkPlan.

## 5. Catalog attribution

A Catalog Snapshot is supplied material and must remain attributable.

IRR MUST preserve material information about the boundary that supplied the Catalog when that information affects trust, semantics, or later validation.

Catalog attribution does not grant authority.

```text
catalog attribution != authorization
```

A Catalog supplied by a Host does not become trustworthy, complete, safe, or permitted merely because the Host supplied it.

M0.2 trust semantics continue to apply.

## 6. Catalog scope and completeness

The applicable Catalog is the authoritative planning surface **for that resolution**, not necessarily an exhaustive inventory of everything technically possible elsewhere.

If completeness is declared, it is bounded by the Catalog's stated scope and time.

IRR MUST NOT infer global impossibility from absence in a Catalog.

```text
absent from applicable catalog
    !=
impossible everywhere
```

IRR also MUST NOT infer that omission is a Governance denial. A Host may supply a deliberately narrow planning surface for many reasons; authority semantics remain external.

```text
catalog omission != Governance denial
catalog membership != Governance approval
```

However, fail-closed planning still applies:

> If no compatible Capability exists in the exact applicable Catalog Snapshot, IRR MUST NOT plan that required operation as an executable WorkStep under that snapshot.

This remains true even if IRR suspects that PowerShell, a browser, another service, a plugin, or another runtime could perform something similar.

## 7. Capability Descriptor semantics

A future `CapabilityDescriptor` representation must preserve enough semantics to identify at least conceptually:

```text
capability identity
purpose / operation semantics
input contract
output contract
material effect metadata
scope requirements
executor / provider identity when material
```

Exact field names and wire types are deferred to M1.

M0.5 freezes the semantic obligations, not a concrete schema.

A Descriptor MUST be inspectable enough that IRR can validate whether a proposed WorkStep fits the capability contract without treating arbitrary executable implementation details as the source of truth.

## 8. Capability Identity

A `Capability Identity` distinguishes one declared capability contract from another.

A stable human-readable `capability_id` alone MUST NOT be treated as proof that semantics are unchanged forever.

Two descriptors using the same identifier may still differ materially in:

- input contract;
- output contract;
- effect surface;
- scope requirements;
- provider/executor identity;
- implementation boundary where that identity is semantically material.

Therefore:

```text
same capability_id != same capability semantics
```

Later representations may use versions, digests, immutable descriptor identities, or another mechanism. Exact identity algorithms are deferred.

## 9. Capability purpose is bounded

A Capability describes a bounded operation class, not a goal-seeking mandate.

A Capability MUST NOT mean:

```text
do whatever is necessary to complete the task
```

or:

```text
keep observing and acting until success
```

when used as an ordinary WorkStep capability.

M0.3 boundedness still applies.

```text
capability != autonomous goal loop
```

Long-form delegated cognition remains a Worker boundary under M0.8.

## 10. Input Contract

A Capability input contract describes the semantic input shape and constraints that the capability may consume.

Input compatibility is semantic, not merely structural.

For example, two strings are not interchangeable merely because both serialize as text; a filesystem path, recipient identity, repository ref, and shell command have different semantics.

```text
same primitive shape != compatible capability input
```

A Capability MUST NOT reinterpret incompatible input merely to make execution possible.

Exact type systems and validation representations are deferred to M1.

## 11. Symbolic inputs remain valid only under compatible contracts

A WorkStep may reference an M0.4 Symbolic Reference before its concrete value is known.

The Capability contract used to admit that WorkStep must be compatible with the **semantic slot**, not merely with an eventual primitive representation.

When the value later binds, the Bound Value MUST still satisfy the relevant capability input, scope, and effect constraints.

If the Bound Value reveals incompatibility or a new material semantic choice:

```text
binding result
    -> no silent capability substitution
    -> IRR Continuation / revalidation as applicable
```

Late Binding MUST NOT become a way to postpone capability compatibility checks until an Executor can improvise.

## 12. Output Contract

A Capability output contract describes attributable data or result semantics that the capability may produce.

Outputs may later serve as:

- plan-local Binding Input;
- Observation returned to IRR;
- Outcome evidence;
- completion evidence;
- another explicitly classified downstream value.

M0.4 returned-data classification remains in force.

A Capability output contract does not establish that any returned value is true beyond its evidence or fresh forever.

## 13. Capability Match

A `Capability Match` is the bounded determination that a catalog-defined Capability can represent a planned Semantic Operation under the required input, output, effect, and scope semantics.

Matching MUST preserve semantic meaning.

IRR MUST NOT match a capability merely because:

- its name looks similar;
- its implementation could probably be coerced;
- it accepts the same primitive types;
- a Cognitive Provider claims it is close enough;
- a shell command could bridge the gap;
- an Executor might know how to adapt it.

```text
name similarity != capability compatibility
implementation possibility != capability admission
```

A Descriptor that is present in the Catalog but incompatible with the required operation does not satisfy the WorkStep merely because its identifier looks relevant.

```text
descriptor present != compatible capability
```

Exact matching algorithms are deferred.

## 14. Multiple compatible capabilities

More than one Capability may appear compatible with a Semantic Operation.

IRR MUST NOT silently choose between them when the choice can materially change:

- effect surface;
- disclosure;
- scope;
- provider/executor boundary;
- cost or external commitment;
- trust-relevant handling;
- output semantics;
- any other Material Ambiguity dimension frozen by M0.2.

If several descriptors are semantically interchangeable under already admitted semantics, a bounded selection rule may choose among them.

Otherwise the choice requires explicit resolution or continuation.

```text
multiple matches != permission for hidden provider preference
```

Presentation order, registration order, or Catalog order MUST NOT become implicit capability precedence.

## 15. Provider / Executor identity

A Capability Descriptor may identify the Executor, provider, adapter family, or execution boundary expected to provide the capability when that identity is material to semantics.

Provider identity can matter because two implementations of an apparently similar operation may differ in:

- external disclosure;
- account boundary;
- network use;
- persistence;
- side effects;
- trust boundary;
- output provenance.

IRR MUST NOT silently substitute another provider when doing so changes material semantics.

```text
same operation name != provider interchangeability
```

Provider identity itself does not grant authority or establish trust.

## 16. Effect Metadata

`Effect Metadata` describes the material externally observable effect surface associated with a Capability contract.

It exists so IRR and downstream Governance can inspect what the proposed operation may do without treating implementation code as the semantic source of truth.

Illustrative effect concepts may include:

- observation/read;
- local mutation;
- process execution;
- network interaction;
- external disclosure;
- durable external side effect.

These examples are **not** a frozen enum or risk taxonomy.

M0.5 freezes only that material effects must be explicit enough to prevent effect smuggling.

```text
effect metadata != authorization
effect metadata != safety verdict
effect metadata != risk approval
```

IRR may state:

```text
this capability can disclose selected data externally
```

IRR MUST NOT infer:

```text
therefore disclosure is allowed
```

M0.6 owns Governance and authority decisions.

### 16.1 Descriptor effect surface versus requested effect

A Capability Descriptor may describe an **effect envelope** broader than the effect requested by one particular WorkStep.

For example, one bounded capability family might support both read-only and mutating modes under explicit parameters.

IRR MUST preserve the material effect semantics of the specific proposed WorkStep; it MUST NOT treat every possible Descriptor effect as automatically requested, and it MUST NOT omit an unavoidable effect merely because the WorkStep requested a narrower operation.

```text
descriptor effect envelope != requested invocation effect
```

A Capability Match is invalid when the capability's unavoidable material effects exceed or contradict the represented WorkStep semantics.

Exact per-invocation effect-projection representation is deferred.

## 17. Descriptor effects must cover implementation effects

A downstream implementation MUST NOT claim conformance to a Capability contract while introducing a material effect omitted from the Descriptor semantics.

For example, a capability described as local `archive.extract` cannot transparently implement itself by uploading the archive to a remote service unless the external disclosure/network effect is part of the admitted capability/work semantics.

```text
implementation convenience != permission to exceed descriptor effect surface
```

This extends M0.3 platform neutrality without turning IRR into an implementation owner.

## 18. Scope Requirements

`Scope Requirements` describe what bounded resource, destination, account, recipient, path, repository, network domain, or other semantic scope must be supplied for a Capability invocation.

Scope requirements are descriptive constraints, not permission.

```text
scope requirement != authorized scope
```

A generic capability such as `filesystem.search` does not authorize all filesystems merely because its contract supports a path scope.

The capability's maximum supported scope is also not automatically the requested WorkStep scope.

```text
capability-supported scope != requested scope
```

The concrete requested scope remains proposed work and may later require Governance authorization.

## 19. Bound resources and scope

A capability may be admitted while a resource is still symbolic if its semantic input and scope contract are already bounded.

When a Symbolic Reference later becomes a concrete Bound Value, the concrete resource MUST remain within the capability/work semantics already admitted.

If binding widens or changes the material scope:

```text
new material scope
    -> not mechanical capability reuse
    -> IRR Continuation / Governance re-review as applicable
```

M0.5 does not freeze exact authority timing.

## 20. Catalog membership

`Catalog Membership` means a Capability Descriptor is present in the exact applicable Catalog Snapshot and is eligible for matching under that snapshot's stated scope.

Membership means only that the capability is **known to the planning surface**.

It does not mean:

- an executor is online;
- credentials exist;
- required scope is reachable;
- Governance approves use;
- the operation will succeed;
- the effect occurred.

```text
catalog membership != current availability
catalog membership != authorization
catalog membership != successful effect
```

## 21. Availability

`Capability Availability` describes whether a catalog-known capability can currently be offered by the applicable downstream environment under stated runtime conditions.

Availability is not the same as Catalog Membership.

A capability may be:

```text
known but currently unavailable
```

for reasons such as:

- executor offline;
- required service unreachable;
- adapter temporarily absent;
- resource unavailable;
- runtime dependency unavailable.

This condition is distinct from:

```text
missing_capability
```

because the semantic Capability definition remains known.

```text
known capability + unavailable != missing capability
```

Exact availability enums, probes, leases, health checks, and temporal guarantees are deferred.

## 22. Availability is attributable and time-bounded

Availability statements are attributable, time-bounded Claims about runtime state, not timeless facts.

IRR MUST NOT treat an old availability statement as permanent proof that a capability is still reachable.

```text
availability != timeless fact
```

Where availability materially affects a current path, its provenance and temporal basis must remain inspectable.

IRR MUST NOT silently probe the environment to refresh availability. Fresh availability state must enter through an explicit external boundary and retain its actual classification; it becomes an M0.4 `Observation` only when explicitly supplied back to IRR as Observation material.

```text
availability claim != Observation by default
```

## 23. Availability does not grant authority

A capability being online and ready does not make it permitted.

```text
available != authorized
```

Likewise, Governance authorization does not prove current availability.

```text
authorized != available
```

Both conditions may be necessary downstream, but they remain separate dimensions.

## 24. Planning against known but unavailable capabilities

M0.3 freezes that a semantically valid WorkPlan may exist even when a known capability is not currently executable.

M0.5 preserves that rule.

A WorkPlan MAY remain semantically valid when:

- the required Capability exists in the applicable Catalog Snapshot;
- the WorkStep matches that Capability contract;
- current availability is false, unknown, or later changes;
- no semantic substitution is performed.

Such a plan is not currently executable merely because it is valid.

```text
valid capability-bound plan != currently executable plan
```

Exact blocking, waiting, scheduling, or recovery states are deferred to later lifecycle contracts.

## 25. missing_capability

`missing_capability` is the conceptual condition where a required Semantic Operation has no compatible Capability admitted in the exact applicable Catalog Snapshot.

It does **not** claim that no implementation exists anywhere.

```text
missing_capability
    = absent compatible contract in applicable Catalog Snapshot

missing_capability
    != global impossibility
```

A same-named but semantically incompatible Descriptor does not satisfy the requirement. Later diagnostics may distinguish `absent` from `present-but-incompatible`, but both remain fail-closed for WorkStep admission unless a compatible contract exists.

When `missing_capability` applies, IRR MUST NOT admit a WorkStep pretending the required Capability exists.

Exact result/state schema is deferred.

## 26. Missing capability blocks required WorkSteps

If a capability is required to satisfy the resolved operational semantics, absence of a compatible Capability MUST fail closed for that WorkStep.

IRR MUST NOT:

- emit an unsupported WorkStep and hope an Executor can improvise;
- replace it with arbitrary shell execution;
- substitute browser automation;
- call an unrelated service;
- widen the Catalog;
- reinterpret a Worker as a capability fallback;
- invent a generic `execute_command` capability;
- silently omit the required step.

```text
missing capability != fallback authority
```

## 27. No silent partial-plan degradation

If a required capability is missing, IRR MUST NOT silently drop that required operation and present the remaining subset as if it still satisfied the same resolved intent.

For example:

```text
intent:
    restore backup and launch project

known:
    filesystem.search
    archive.extract

missing:
    process.launch
```

IRR MUST NOT silently reinterpret the intent as:

```text
restore backup only
```

No admitted downstream WorkPlan representing the original full objective may masquerade as complete while a required operation has no compatible Capability.

IRR may later expose diagnostic information about which operations are satisfiable and which are missing, but such diagnostic analysis is not an admitted full-objective WorkPlan and does not authorize partial execution.

A separately admitted successor intent or constrained resolution may later authorize a smaller objective, but that is a semantic change and must remain explicit.

```text
partial capability coverage != full intent satisfaction
```

M0.6 later freezes how Governance constraints create successor semantics rather than mutating plans silently.

## 28. No hidden capability synthesis

IRR MUST NOT synthesize a new Capability from lower-level mechanisms merely because doing so seems technically possible.

Examples of forbidden hidden synthesis include:

```text
missing archive.extract
    -> invent shell.execute("tar ...")

missing telegram.send_file
    -> invent browser.click_sequence

missing process.launch
    -> invent arbitrary code execution
```

A Host may explicitly provide a bounded lower-level Capability such as a future governed process execution contract. If so, that Capability must itself be present in the applicable Catalog and the requested work must genuinely match its explicit semantics.

A generic command-execution Capability is not a universal semantic adapter. Its presence does not automatically make unrelated Semantic Operations capability-supported.

```text
generic command execution != universal capability adapter
```

If the actual admitted intent is specifically to execute user-supplied command material, a bounded command-execution Capability may be the genuine matching operation under M0.3's executable-text boundary. That is distinct from silently lowering another Semantic Operation into shell execution.

IRR does not get to create that authority surface itself.

## 29. Cognitive Provider cannot invent capabilities

A Cognitive Provider may propose candidate work using a capability-like identifier.

IRR MUST validate that proposal against the exact applicable Catalog Snapshot.

Provider output does not add Catalog Membership.

```text
provider proposal != capability existence
```

A provider-proposed capability absent from the Catalog produces the same fail-closed capability condition as any other unsupported operation.

M0.7 freezes the broader Cognitive Provider contract.

## 30. Capability prerequisites

A Capability may require bounded prerequisites.

Those prerequisites MUST NOT become hidden side tasks.

If satisfying a prerequisite requires another operational Capability, that prerequisite operation must itself:

- derive from the parent WorkPlan semantics or necessary explicit prerequisite;
- be represented inspectably;
- have a compatible Capability in the applicable Catalog Snapshot;
- preserve its own material effect and scope semantics.

```text
capability prerequisite != implicit capability expansion
```

M0.3 Plan Derivation remains in force.

## 31. Capability Catalog order is not preference

Catalog registration order, serialization order, provider discovery order, or presentation order MUST NOT silently choose among multiple capability matches.

```text
catalog order != capability precedence
```

If a selection rule is material, it must be explicit and bounded.

## 32. Capability Drift

`Capability Drift` is a material change between the capability surface against which work was resolved and the capability surface later presented for validation, handoff, or execution.

Drift may include conceptually:

- Capability added or removed;
- descriptor semantics changed;
- input contract changed;
- output contract changed;
- effect metadata changed;
- scope requirements changed;
- provider/executor identity changed where material;
- another change that affects capability meaning or admissibility.

A Catalog change unrelated to any capability semantics or matching assumptions used by an existing WorkPlan need not change that WorkPlan's meaning merely because the overall snapshot identity differs. Historical snapshot attribution still remains exact.

Exact drift detection and snapshot comparison algorithms are deferred.

## 33. Availability Drift is distinct from semantic drift

A capability becoming temporarily online or offline does not necessarily change its semantic Descriptor.

Therefore M0.5 distinguishes:

```text
semantic / membership drift
```

from:

```text
availability drift
```

Availability drift may affect executability without changing what the WorkPlan means.

M0.5 does not freeze whether a later runtime represents availability inside a Catalog Snapshot or as separate attributable state. It freezes only that the distinction must remain semantically visible.

## 34. Drift must not reinterpret existing work

A later Catalog MUST NOT silently make an old WorkStep mean something different.

If a required Capability has materially changed, been removed, or now matches only through a materially different descriptor, the old WorkPlan cannot simply inherit the new semantics.

Depending on later contracts, the path may require:

- revalidation against the new Catalog;
- IRR Continuation;
- a Successor WorkPlan;
- renewed Governance review;
- explicit inability to continue.

```text
capability drift != silent plan reinterpretation
```

M0.5 freezes the invariant, not exact state-machine transitions.

## 35. Revalidation is not semantic mutation

A later system may revalidate whether an existing WorkStep remains compatible with a current Catalog.

Successful revalidation does not create authority.

Failed revalidation does not permit hidden remapping.

```text
revalidation != authorization
revalidation != capability substitution
```

If material semantics would change, the path returns to IRR rather than rewriting the prior WorkPlan in place.

## 36. Effect metadata changes are material drift

A Capability whose operation name remains unchanged but whose material effect surface changes MUST NOT be treated as semantically identical merely because the identifier is stable.

Example:

```text
archive.extract v1:
    local filesystem only

archive.extract v2:
    may upload archive to remote extraction service
```

This is material capability drift.

```text
same id + changed effect surface != same capability semantics
```

The existing plan must not inherit the new external disclosure silently.

## 37. Scope changes are material when they change meaning

A Descriptor change that widens or alters the possible scope of an operation may be material.

For example, changing a capability from:

```text
workspace.read(scope=declared workspace)
```

to:

```text
filesystem.read(scope=arbitrary host filesystem)
```

is not a harmless implementation update.

Capability drift analysis must preserve such scope changes as semantic changes when material.

## 38. Executor substitution

A different Executor MAY later provide the same Capability semantics only when the applicable contract establishes that the substitution preserves all material semantics required by the plan.

IRR MUST NOT assume executor interchangeability merely from identical capability names.

If executor/provider identity changes disclosure, trust, account, effect, scope, or output provenance materially, the substitution is not transparent.

```text
executor substitution != automatic semantic equivalence
```

Exact executor-selection and conformance mechanisms are deferred.

## 39. Capability metadata is descriptive, not normative authority

A Capability Descriptor may describe:

- effects;
- required scope;
- input/output constraints;
- provider identity;
- availability claims;
- other execution-relevant semantics.

None of those fields may encode or imply IRR-granted authority.

A Descriptor MUST NOT use semantics equivalent to:

```text
approved = true
safe = true
permission_granted = true
user_consented = true
```

as an IRR capability-admission conclusion.

Governance may later produce authority decisions, but those decisions are separate from the Capability Descriptor.

```text
capability descriptor != authorization record
```

## 40. Capability risk labels do not decide permission

A future Host may supply descriptive risk/effect classifications.

Even if a capability is labeled `low_risk`, `read_only`, `local`, or similar, that label MUST NOT become automatic permission.

Likewise, a capability described as effectful is not automatically forbidden.

```text
risk/effect label != Governance decision
```

Exact risk taxonomies remain deferred unless a later milestone explicitly freezes one.

## 41. Catalog updates do not mutate historical attribution

When the Host supplies a new Catalog Snapshot, the prior snapshot remains the historical planning basis for already-resolved work.

IRR MUST NOT rewrite old provenance to pretend the new Catalog was used originally.

```text
new catalog snapshot != rewritten planning history
```

Later persistence and digest contracts may make this relation durable.

## 42. Catalog extension does not retroactively repair missing capability

If a resolution previously encountered `missing_capability`, a later Catalog containing a new compatible Capability does not mean the earlier resolution secretly had that capability.

The new Catalog may permit a later Continuation or successor planning decision.

```text
later capability addition != retroactive capability existence
```

Parent intent lineage must remain attributable.

## 43. Backup scenario

Intent:

```text
"Find the newest organism_lab backup in D:\Backups,
extract it to W:\organism_lab,
and launch the project."
```

Applicable Catalog Snapshot might contain:

```text
filesystem.search
artifact.select
archive.inspect
archive.extract
workspace.inspect
process.launch
```

IRR may plan those semantic operations only because compatible Capability contracts are present in that exact Catalog Snapshot.

If `process.launch` is absent:

```text
missing_capability(process.launch)
```

IRR MUST NOT replace it with:

```text
powershell.exe Start-Process
cmd.exe /c start
browser automation
worker improvisation
```

merely to finish the plan.

If `process.launch` is present but its executor is offline:

```text
known capability
+ unavailable
!= missing_capability
```

The plan may remain semantically valid while execution is blocked under later lifecycle contracts.

## 44. Telegram scenario

Intent:

```text
"Send the latest Voice Engine report to me in Telegram."
```

Suppose the Catalog contains:

```text
filesystem.search
artifact.select
telegram.send_file
```

A `telegram.send_file` Descriptor must make the material external disclosure/network effect inspectable.

IRR may represent:

```text
requested effect:
    disclose selected file to external Telegram recipient
```

but MUST NOT conclude:

```text
allowed = true
```

If only a generic browser automation capability exists, IRR MUST NOT silently treat that as `telegram.send_file` unless the supplied capability contract genuinely and boundedly matches the requested semantics, including recipient, disclosure, effect, and completion requirements.

## 45. Relationship to M0.6 Governance

M0.5 freezes what capabilities are **known and semantically admissible for planning**.

M0.6 freezes whether proposed work may **proceed under authority**.

```text
M0.5:
    can this operation be represented by an admitted capability contract?

M0.6:
    may this proposed work proceed under stated authority conditions?
```

These questions MUST remain separate.

A positive M0.5 answer never implies a positive M0.6 answer.

## 46. Relationship to M0.4 Binding

Binding a concrete resource does not create a Capability.

A Capability Descriptor admitting a symbolic input does not authorize any concrete resource that may later bind.

After Binding, the concrete value must still satisfy the Capability contract and may remain subject to Governance.

```text
binding != capability admission
capability admission != bound-resource authorization
```

## 47. Relationship to M0.7 Cognitive Provider

A Cognitive Provider may propose capability use, but it does not own Catalog Membership.

IRR validates provider proposals against the exact applicable Catalog Snapshot.

The provider cannot expand the Catalog by fluent assertion.

## 48. Relationship to M0.8 Worker delegation

A Worker is not an automatic fallback when an ordinary Capability is missing.

Delegated work may later receive an explicit bounded allowed-capability surface, but that is a separate handoff contract.

```text
worker availability != capability fallback
```

M0.8 freezes Worker delegation in detail.

## 49. Relationship to M0.9 failure and recovery

Capability unavailability, missing capability, execution failure, and unknown outcome are distinct conditions.

M0.5 freezes only the first two capability-surface distinctions.

M0.9 freezes terminal outcome and retry/recovery semantics.

```text
missing capability != execution failure
unavailable capability != unknown outcome
```

## 50. M0.5 exclusions

M0.5 intentionally does NOT freeze:

- Python classes, enums, protocols, or serialization;
- exact `CapabilityDescriptor` fields;
- exact Capability Catalog wire format;
- exact snapshot identity or digest algorithm;
- exact capability version syntax;
- exact operation-to-capability matching algorithm;
- exact semantic type system for inputs and outputs;
- exact per-invocation effect-projection representation;
- exact effect taxonomy or risk levels;
- exact scope expression language;
- exact availability enum, probe, lease, health-check, or TTL behavior;
- whether availability is embedded in a Catalog Snapshot or supplied separately;
- exact executor/provider selection algorithm;
- runtime adapter implementation;
- executable command lowering;
- Governance policy, consent, or approval APIs;
- exact handoff schema;
- Worker delegation schema;
- persistence, receipts, audit log format, or cryptography;
- retry/recovery algorithms;
- terminal Outcome schemas.

M0.5 freezes semantic constraints, not implementation types.

## 51. Acceptance criteria

M0.5 is complete when the repository states unambiguously that:

1. IRR receives an explicit Capability Catalog through an external boundary and does not perform ambient capability discovery.
2. Semantic Operation and Capability are distinct concepts even when they use the same human-readable label.
3. A Capability is a bounded operation contract, not an implementation command or autonomous goal loop.
4. Every operational WorkPlan is attributable to the exact applicable Catalog Snapshot and admitted Capability contracts used to validate its WorkSteps.
5. Catalog attribution does not grant authority.
6. Catalog scope is not silently treated as a global inventory of everything technically possible.
7. Absence from the applicable Catalog does not prove global impossibility or Governance denial.
8. Capability Descriptor semantics conceptually preserve identity, purpose, input/output contracts, material effects, scope requirements, and provider/executor identity when material.
9. A stable capability identifier alone does not prove unchanged semantics.
10. Capability input compatibility is semantic rather than primitive-type compatibility.
11. Symbolic capability inputs remain subject to contract validation when their concrete values later bind.
12. Capability outputs remain attributable and are not automatically Observation, Outcome, or truth.
13. Capability matching preserves semantic meaning and cannot rely on name similarity or implementation coercion.
14. Descriptor presence does not establish compatibility.
15. Multiple materially different capability matches do not permit hidden provider preference.
16. Catalog order does not imply capability precedence.
17. Provider/executor identity changes are material when they change effect, disclosure, scope, trust boundary, account boundary, or output provenance.
18. Material Effect Metadata is descriptive and inspectable but does not authorize work.
19. Descriptor effect envelope remains distinct from the requested effect semantics of a particular WorkStep.
20. Capability Match fails when unavoidable capability effects exceed or contradict represented WorkStep semantics.
21. Effect metadata is not a safety verdict or risk approval.
22. Downstream implementations cannot exceed the material Descriptor effect surface silently.
23. Scope Requirements describe bounded semantic scope but do not authorize that scope, and maximum supported scope is not requested scope.
24. Catalog Membership means capability-known-for-planning, not current availability, authorization, or successful effect.
25. Capability Availability is distinct from Catalog Membership.
26. Known-but-unavailable capability is not `missing_capability`.
27. Availability is attributable and time-bounded, not a timeless fact or automatic Observation classification.
28. Availability does not grant authorization, and authorization does not establish availability.
29. A capability-bound WorkPlan may remain semantically valid while a known capability is unavailable.
30. `missing_capability` means no compatible Capability exists in the exact applicable Catalog Snapshot, not global impossibility.
31. Required missing or incompatible capabilities fail closed and cannot appear as pretend executable WorkSteps.
32. Missing capability does not authorize shell, browser, service, Worker, or arbitrary-code fallback.
33. Missing capability does not permit silently dropping required operations and claiming the original intent is satisfied.
34. Diagnostic partial capability analysis is not an admitted full-objective WorkPlan and does not authorize partial execution.
35. IRR cannot synthesize new capabilities from lower-level mechanisms unless those lower-level capabilities are themselves explicitly supplied and genuinely match admitted work semantics.
36. Generic command execution is not a universal adapter for unrelated Semantic Operations.
37. Cognitive Provider proposals do not create Catalog Membership.
38. Capability prerequisites remain explicit, capability-bound, and derivable rather than hidden side tasks.
39. Capability Drift includes material membership or descriptor-semantic changes after planning.
40. Unrelated Catalog changes need not alter WorkPlan meaning merely because snapshot identity changes, while historical snapshot attribution remains exact.
41. Availability Drift remains distinguishable from semantic/membership drift.
42. Capability Drift cannot silently reinterpret an existing WorkPlan.
43. Revalidation does not grant authority and does not permit hidden capability substitution.
44. Changed material effect metadata is capability drift even if the human-readable capability ID is unchanged.
45. Material scope changes remain visible as semantic drift.
46. Executor substitution is not automatically semantically equivalent.
47. Capability Descriptor metadata is not an authorization record.
48. Descriptive risk/effect labels do not decide permission.
49. New Catalog Snapshots do not rewrite historical planning attribution.
50. Later Catalog extension does not retroactively erase an earlier `missing_capability` condition.
51. M0.5 capability admission and M0.6 Governance authorization remain distinct stages.
52. Binding does not create capability admission, and capability admission does not authorize a later Bound Value.
53. Worker availability does not become capability fallback.
54. Missing capability, unavailability, failure, and unknown outcome remain distinguishable.
55. M0.6+, M0.7+, M0.8+, M0.9+, and M1 implementation details remain explicitly deferred.
56. No runtime code or `src/` tree is introduced.
