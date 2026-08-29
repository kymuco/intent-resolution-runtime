# M0.10 — Reference Scenarios

Status: **normative architecture fixtures for M0.10**.

This document closes the M0 boundary freeze by exercising the already-frozen M0.1–M0.9 contracts against concrete end-to-end scenarios.

M0.10 does **not** introduce a runtime model, Python schema, command language, policy engine, executor protocol, Worker protocol, provider API, recovery state machine, or fixture JSON format. It freezes architecture fixtures: stable semantic examples that M1+ implementations must be able to represent without weakening the M0 boundaries.

The fixtures answer one question:

> Can IRR explain realistic human-, companion-, provider-, Worker-, capability-, governance-, execution-, and recovery-facing flows without hidden context, hidden authority, hidden capability discovery, hidden semantic choice, or hidden retry?

The required answer is **yes**.

---

## 1. Fixture interpretation

Each scenario records conceptually:

```text
request / trigger
explicit attributable inputs
resolution / clarification expectation
work / delegation / no-work expectation
Binding and Capability expectations
applicable authority boundary
handoff role
result / recovery / continuation expectation
forbidden shortcuts
M0 contracts exercised
```

The examples constrain meaning, not representation.

```text
architecture fixture != frozen JSON
architecture fixture != command sequence
architecture fixture != Authorization
architecture fixture != executable test implementation
```

Exact class names, operation identifiers, serialization, digests, adapters, and state layout remain later-milestone work.

---

## 2. Cross-scenario invariants

All fixtures preserve:

```text
origin != principal
origin != authority
context != authority
intent != authorization
resolution != authorization
WorkPlan != execution
semantic operation != implementation command
symbolic reference != observed value
late binding != hidden semantic choice
catalog membership != availability
availability != Authorization
missing_capability != fallback authority
provider proposes != IRR admits
Worker != Cognitive Provider
DelegatedWork != ordinary WorkStep
DelegatedWorkHandoff != Authorization
WorkerResult != parent completion
unknown_outcome != failed
failed != no effect
Retry != continuation of the same Attempt
```

No fixture may be made to pass by weakening one of these distinctions.

---

# Scenario A — Restore the latest `organism_lab` backup

## A.1 Request

```text
"Найди последний backup organism_lab,
распакуй в W:\\organism_lab и запусти."
```

This fixture exercises bounded discovery, Late Binding, selection, archive operations, filesystem mutation, process launch, capability admission, Governance, and scoped outcomes.

## A.2 Explicit inputs

Conceptually the Host supplies:

```text
Origin attribution:
    human

Principal:
    user

Context:
    backup search root = D:\Backups
    backup family / match constraint = organism_lab
    destination = W:\organism_lab

Selection semantics:
    "latest" = greatest admitted modification timestamp
    within the bounded matching candidate set

Binding Input basis:
    candidate identities/timestamps returned by the bounded search

Capability Catalog Snapshot:
    filesystem.search
    archive.inspect
    archive.extract
    workspace.inspect
    process.launch
```

The bounded search root is fixture Context, not ambient discovery authority.

```text
D:\Backups in Context
    !=
authority to search the whole machine
```

If no bounded search scope is supplied, IRR must not invent one, scan every drive, or ask a provider to discover the backup ambiently.

## A.3 Expected semantic path

Conceptually:

```text
IntentRequest
    -> ResolvedIntent
    -> bounded operational semantics
```

One valid semantic shape is:

```text
filesystem.search
    scope: D:\Backups
    output: $backup_candidates

Binding / selection
    input: $backup_candidates
    rule: greatest admitted modification timestamp
    output: $selected_backup

archive.inspect
    input: $selected_backup

archive.extract
    input: $selected_backup
    destination: W:\organism_lab

workspace.inspect
    scope: W:\organism_lab

process.launch
    target selected only under already-admitted bounded semantics
```

The selection line above is deliberately **not** frozen as an external Capability or ordinary WorkStep. M0.4 allows effect-free Binding/Selection semantics inside IRR. A later implementation may represent selection as a Binding Rule, a dedicated semantic work unit, or a capability-backed operation only if the resulting representation still satisfies M0.3–M0.5.

```text
selection semantics != external Capability requirement by default
```

## A.4 Late Binding

The concrete archive path is unknown before search.

```text
$selected_backup = future Bound Value
```

The value may be bound only by applying the already-admitted rule to compatible attributable Binding Input.

```text
unknown value != unknown decision rule
```

No “looks best” choice, implicit first-result preference, or new tie-breaker may be invented later.

## A.5 Capability boundary

Every **capability-dependent** operational unit must match the exact applicable Catalog Snapshot.

If `archive.extract` is absent:

```text
missing_capability
```

IRR must not silently lower the operation into PowerShell, `tar`, 7-Zip, browser upload, arbitrary Python, or another mechanism merely because it could implement extraction.

## A.6 Governance / authority

Material authority surfaces may include:

```text
read/search backup directory
read archive metadata
write/replace W:\organism_lab
launch process
```

Semantic validity does not authorize them.

Governance may authorize an already represented subset, require review, constrain, or deny. A semantic constraint that changes the objective returns through IRR Continuation rather than rewriting the old work silently.

## A.7 Handoff and result

Ordinary bounded effectful operations use the capability/executor path when applicable:

```text
bounded operation
    -> applicable authority boundary when required
    -> CapabilityHandoff
    -> Executor
```

Results remain scoped:

```text
search succeeded != restore succeeded
extract succeeded != launch succeeded
launch succeeded != parent intent satisfied by default
```

Failure does not erase known partial filesystem effects.

## A.8 Forbidden shortcuts

The implementation must not:

- scan arbitrary locations because scope is missing;
- conflate Binding/Selection with an automatically required external capability;
- choose the first candidate as an implicit tie-break;
- invent archive/process capabilities;
- convert work validity into permission;
- let an Executor choose a materially different launch target;
- erase partial effects after failure;
- hide Retry inside an operation.

## A.9 Contracts exercised

```text
M0.1 roles
M0.2 Context / ambiguity / attribution
M0.3 bounded semantic work
M0.4 Late Binding / Selection Policy
M0.5 Capability Catalog
M0.6 Governance / Authorization
M0.9 scoped Outcome / partial effect / Retry boundary
```

---

# Scenario B — Send the latest Voice Engine report through Telegram

## B.1 Request

```text
"Отправь мне последний Voice Engine report в Telegram."
```

This fixture exercises artifact selection, recipient binding, external disclosure, network effect, Governance, and unknown-outcome recovery.

## B.2 Explicit inputs

Conceptually:

```text
Origin attribution:
    human

Principal:
    user

Context:
    bounded report search scope
    report family = Voice Engine report
    explicit attributable Telegram destination for "me"

Selection semantics:
    latest = explicit bounded ordering rule

Capability Catalog Snapshot:
    artifact.search
    telegram.send_file
```

Selection of the report is Binding/selection semantics unless a later representation explicitly and validly models some part as capability-backed work.

```text
report selection != external Capability requirement by default
```

`Principal=user` does not itself bind a Telegram account/chat.

If multiple material destinations remain possible, IRR clarifies instead of guessing.

## B.3 Expected semantic path

```text
artifact.search
    -> $report_candidates

Binding / selection
    rule: admitted latest-report semantics
    -> $selected_report

telegram.send_file
    artifact: $selected_report
    recipient: explicit bound Telegram destination
```

The send semantics expose:

```text
network use
external disclosure
recipient / destination
```

Read/select authority is not send/disclosure authority.

## B.4 Provider boundary

A Cognitive Provider knowing that Telegram supports file transfer does not create either:

```text
Capability Match
Authorization
```

The report also is not automatically Provider-disclosable merely because a provider could help reason about it.

## B.5 Confirmed success branch

If attributable evidence is sufficient under the admitted capability Completion Semantics, the scoped send Attempt may have a `succeeded` completion condition.

Transport convenience does not strengthen completion semantics by itself.

## B.6 Lost acknowledgement branch

Suppose:

```text
Attempt 1
    request transmitted
    connection/lifecycle disrupted before material completion evidence
```

If evidence cannot establish whether the recipient-visible effect occurred, the **effect/completion condition is `unknown_outcome`**.

The same real-world episode may also be described as lifecycle `interrupted`. M0.10 does not collapse lifecycle discontinuity and effect certainty into one flat enum.

```text
interrupted != unknown_outcome by definition
unknown_outcome != failed
```

IRR must not infer:

```text
no ACK -> failed -> send again
```

Recovery is conceptually:

```text
unknown_outcome
    -> explicit recovery assessment
    -> optional separately admitted status/evidence operation
    -> new Retry Attempt only if safe-replay + capability + authority conditions permit
```

A status query is itself subject to its own applicable capability/disclosure/authority boundary; “need to know whether it sent” is not query authority.

## B.7 Fallback

Switching channel/account/provider is not automatic Retry.

A material fallback:

- preserves the prior Attempt/effect uncertainty;
- is not proof the first effect was absent;
- must pass applicable resolution/capability/authority boundaries;
- becomes a new Attempt if actually executed.

## B.8 Forbidden shortcuts

The implementation must not:

- guess recipient identity;
- turn report selection into an ambient provider task;
- treat `telegram.send_file` existence as permission;
- flatten interruption and effect certainty into one required enum;
- automatically retry an unknown effect;
- switch channel to “make it work” without successor/fallback semantics;
- rewrite Attempt 1 after later evidence or a later successful Attempt.

## B.9 Contracts exercised

```text
M0.1 roles
M0.2 recipient/context evidence
M0.4 Binding / selection
M0.5 Telegram Capability Match
M0.6 disclosure Authorization
M0.7 provider boundary
M0.9 Attempt / interruption / unknown_outcome / Retry / fallback
```

---

# Scenario C — Delegate CG2.42 analysis to Codexia

## C.1 Request

```text
"Изучи результаты CG2.42 и предложи следующий experiment."
```

This is long-form subordinate analysis rather than one ordinary bounded capability invocation.

## C.2 Delegation envelope

Conceptually:

```text
Origin attribution:
    human

Principal:
    user

Context:
    bounded CG2.42 evidence surface
    relevant project lineage

DelegatedWork:
    Worker identity/adapter = Codexia-compatible Worker
    objective = analyze supplied CG2.42 results and propose next experiment candidate(s)
    context surface = explicitly delegated material
    capability ceiling = only explicitly admitted subordinate capability surface
    forbidden effects = repository mutation / commit / push / external publication are outside this delegation
    deliverables = candidate(s) + rationale + evidence references
    completion contract = bounded attributable analysis result
```

A forbidden effect is a semantic negative bound of the current delegation.

```text
Authorization != permission to mutate DelegatedWork semantics
```

If mutation, push, publication, a new external search, or another material widening later becomes necessary, the Worker returns the need to IRR. Any successor work/delegation must represent the new semantics explicitly and then satisfy its own capability/authority requirements. Authorization alone does not “lift” a forbidden effect inside the old DelegatedWork.

## C.3 Worker path

Conceptually:

```text
ResolvedIntent / parent work semantics
        -> DelegatedWork
        -> DelegatedWorkHandoff
        -> Worker
        -> WorkerResult / escalation
        -> IRR Continuation
```

M0.10 does not freeze the exact M1 structural relation between `WorkPlan` and `DelegatedWork`; it freezes that Worker delegation is explicit and is **not** hidden inside an ordinary opaque WorkStep.

The Worker may manage an internal subordinate lifecycle inside the envelope:

```text
analyze
plan subordinate work
compare candidates
revise internal plan
produce deliverable
```

That internal plan is not the parent IRR WorkPlan.

## C.4 Capability and authority ceilings

Allowed capabilities are ceilings, not promises, discovery authority, Authorization, or a hidden selection policy.

A necessary subordinate step does not inherit authority merely because it helps the objective.

## C.5 WorkerResult

`WorkerResult` may contain:

```text
proposed experiment candidate(s)
rationale
evidence/source references
uncertainty / omissions
completion claim
```

But:

```text
WorkerResult != CandidateResolution by default
WorkerResult != factual truth by default
WorkerResult != Governance Decision
WorkerResult != Authorization
WorkerResult != parent intent completion
```

A Worker saying `done` does not establish the delegated completion contract; the receiving boundary checks the returned deliverables/semantics.

## C.6 Escalation

If additional material outside the envelope is required:

```text
WorkerResult / escalation need
    -> IRR Continuation
```

not ambient scanning and not automatic nested IRR Worker delegation.

## C.7 Forbidden shortcuts

The implementation must not:

- hide the lifecycle inside `codexia.do_work` ordinary WorkStep;
- give ambient repository/home access;
- let Authorization silently erase a forbidden-effect bound;
- let “necessary for the task” expand delegation automatically;
- relabel Worker findings as user statements;
- turn Worker confidence into Evidence;
- treat Worker output as admitted successor semantics without continuation.

## C.8 Contracts exercised

```text
M0.1 roles
M0.2 provenance / Context / Evidence
M0.3 ordinary WorkStep boundedness
M0.5 capability boundary
M0.6 authority separation
M0.7 Cognitive Provider != Worker
M0.8 DelegatedWork / WorkerResult / parent ownership
M0.9 Worker result/failure remains scoped
```

---

# Scenario D — Ambiguous referent: “Launch it”

## D.1 Request

```text
"Запусти его."
```

Assume admitted Context does not identify one unique launch target and no already-admitted referent rule resolves the pronoun.

## D.2 Expected result

This is blocking `Material Ambiguity`:

```text
IntentRequest
    -> Material Ambiguity
    -> Clarification
```

There is no admitted process-launch ResolvedIntent/operational work yet.

```text
clarification != ResolvedIntent
clarification != WorkPlan
clarification != parent completion
```

## D.3 Provider and ambient context

A provider may propose a likely referent and confidence score, but:

```text
provider confidence != ambiguity-resolution authority
model prior != admitted Evidence
```

IRR/provider must not silently inspect foreground windows, running processes, shell history, recent files, HDE memory, or arbitrary machine state to manufacture the missing referent.

## D.4 Governance

Even broad launch Authorization cannot answer **which target was meant**.

```text
Authorization != ambiguity resolution
```

## D.5 Contracts exercised

```text
M0.2 Material Ambiguity / no ambient Context
M0.3 no operational work before admitted semantics
M0.6 authority cannot repair semantics
M0.7 provider confidence cannot choose material referent
```

---

# Scenario E — Companion initiative

## E.1 Trigger

A companion such as Kaguya proposes:

```text
"Стоит проверить последние логи."
```

## E.2 Attribution

```text
Origin = companion
Principal = user
```

The companion is not relabeled as human because it serves the user.

```text
origin != principal
origin != authority
```

## E.3 Resolution and Context

If log scope and “latest” semantics are sufficiently bounded by explicit attributable Context, IRR may resolve a bounded inspection objective. Otherwise clarification/information is required.

Companion familiarity or confidence does not create missing Context.

## E.4 Authority

```text
companion intent != Authorization
companion recommendation != Governance Decision
```

A Host may later supply an externally defined reusable grant for a bounded class, but IRR does not infer such a grant from the relationship.

## E.5 Capability and result

Any required log-inspection capability comes from the applicable Catalog Snapshot. Result provenance remains with the actual source/executor boundary and is not rewritten as a human statement.

## E.6 Forbidden shortcuts

The implementation must not:

- relabel companion Origin as human;
- treat relationship/history as authority;
- give ambient memory/filesystem access;
- infer standing grants;
- report effects as if the human explicitly originated them.

## E.7 Contracts exercised

```text
M0.1 Origin / Principal
M0.2 Context / attribution
M0.5 Capability Catalog
M0.6 external authority
M0.7 recommendation != authority
```

---

# Scenario F — Missing Signal capability

## F.1 Request

```text
"Отправь файл через Signal."
```

Assume file/recipient semantics are otherwise resolved, but the exact applicable Catalog Snapshot has no compatible Signal-send capability.

## F.2 Expected result

```text
missing_capability
    -> blocked work path
    -> no Signal effect Attempt is implied to have started
```

`blocked` describes inability to proceed; the cause remains `missing_capability`.

```text
missing_capability != Denial
missing_capability != global impossibility
missing_capability != fallback authority
```

## F.3 Forbidden fallback

IRR/provider/Worker/Executor must not silently substitute Telegram, email, browser automation, shell, arbitrary code, plugin discovery, or another service.

If a later Host supplies a new Catalog Snapshot or the user explicitly accepts another channel, that enters through explicit successor/revalidation semantics with preserved lineage.

## F.4 Governance

Authorization cannot synthesize an absent capability.

```text
Authorization + missing_capability != executable work
```

## F.5 Contracts exercised

```text
M0.3 semantic operation != mechanism
M0.5 fail-closed Capability Catalog
M0.6 Authorization != capability existence
M0.7 provider knowledge != capability
M0.8 Worker != fallback authority
M0.9 pre-attempt blocked != failed Attempt
```

---

# Scenario G — No operational intent

## G.1 Request

```text
"Как ты думаешь, этот эксперимент хороший?"
```

Assume the relevant experiment material is already admitted as bounded Context.

## G.2 Expected resolution

This is an inquiry/evaluation, not automatically a request for effects.

IRR may admit a non-operational ResolvedIntent:

```text
answer / assessment requested
no operational work required
```

```text
ResolvedIntent != WorkPlan requirement
```

## G.3 Provider boundary

A permitted Cognitive Provider may propose evaluative semantics/answer material. Its output remains CandidateResolution until IRR admission.

Remote provider transport may create disclosure effects; “just reasoning” does not exempt disclosure from the surrounding boundary.

## G.4 Governance

M0 does not impose a universal Governance requirement on every non-operational/internal computation. A Host may impose additional product policy, but IRR does not manufacture a WorkProposal just to normalize every request into actions.

## G.5 Forbidden shortcuts

The implementation must not silently:

- run another experiment;
- inspect additional files ambiently;
- delegate mutation work to Codexia;
- commit changes;
- execute provider tool-call syntax.

## G.6 Contracts exercised

```text
M0.2 bounded Context
M0.3 conditional WorkPlan creation
M0.6 non-operational path need not manufacture WorkProposal
M0.7 provider proposes / disclosure remains explicit
```

---

# Scenario H — Returned search data creates a new material choice

The preserved roadmap historically called this fixture **“Observation changes plan.”** Under the later-frozen M0.4 terminology, the search output used below is `Binding Input` / returned data and is **not an Observation by default**. The fixture preserves the roadmap intent without collapsing those semantic roles.

## H.1 Initial selection semantics

Use the backup family from Scenario A.

The admitted rule is:

```text
select the unique latest matching backup
by greatest modification timestamp
```

Search returns:

```text
backup-A.zip  mtime = T
backup-B.zip  mtime = T
```

Both satisfy the match constraint and no tie-break rule was admitted.

## H.2 Binding result

The Binding Rule cannot produce one unique Bound Value.

```text
Binding Input
    -> multiple equally admissible candidates
    -> no Bound Value
```

The implementation must not choose by result order, lexical order, size, provider preference, Executor preference, randomness, or another invented rule.

## H.3 Continuation

```text
returned search data / Binding Input
        -> unresolved material selection
        -> IRR Continuation
        -> Clarification
```

A later clarification such as:

```text
"Use backup-B.zip."
```

may produce successor/binding lineage. The historical earlier rule is not rewritten to pretend that tie-break existed originally.

## H.4 Governance

Authority over a symbolic class/rule does not automatically expand merely because a later material choice is resolved differently. Applicability of prior external Authorization must be checked against the actual successor/bound semantics.

## H.5 Provider

A provider may explain the tie or propose clarification. It must not resolve the material choice via confidence unless such provider judgment was already admitted as the selection semantics.

## H.6 Contracts exercised

```text
M0.2 Material Ambiguity / Clarification
M0.3 successor semantics instead of self-modifying plan
M0.4 Binding Input / Binding Rule / no invented Selection Policy
M0.6 successor binding does not amplify authority
M0.7 provider confidence cannot invent tie-break semantics
```

---

# 3. Scenario × boundary matrix

| Scenario | M0.1 | M0.2 | M0.3 | M0.4 | M0.5 | M0.6 | M0.7 | M0.8 | M0.9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A Restore backup | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |  |  | ✓ |
| B Telegram | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |  | ✓ |
| C Codexia | ✓ | ✓ | ✓ |  | ✓ | ✓ | ✓ | ✓ | ✓ |
| D Ambiguous referent |  | ✓ | ✓ |  |  | ✓ | ✓ |  |  |
| E Companion initiative | ✓ | ✓ | ✓ |  | ✓ | ✓ | ✓ |  |  |
| F Missing Signal capability |  |  | ✓ |  | ✓ | ✓ | ✓ | ✓ | ✓ |
| G No operational intent |  | ✓ | ✓ |  |  | ✓ | ✓ |  |  |
| H Returned data changes path |  | ✓ | ✓ | ✓ |  | ✓ | ✓ |  |  |

A blank means the milestone is not the scenario's primary distinguishing feature, not that it ceases to apply.

---

# 4. Negative architecture assertions

The fixture set fails if an implementation requires:

```text
ambient filesystem/repository/browser/memory inspection
implicit wall clock/timezone when material
provider confidence as truth/ambiguity authority
provider tool-call syntax as execution permission
shell/browser/Worker fallback for missing capability
Binding/Selection automatically reclassified as external Capability
WorkPlan as arbitrary scripting language
ordinary WorkStep hiding autonomous Worker lifecycle
companion/Worker Origin relabeled as human
Principal identity treated as permission
Governance used to repair semantic ambiguity
Authorization used to mutate DelegatedWork forbidden effects
Capability availability treated as Authorization
WorkerResult treated as parent completion
failed treated as no effect
timeout treated as failure
interrupted forced to equal unknown_outcome
unknown effectful outcome automatically retried
fallback treated as continuation of same Attempt
later success rewriting earlier uncertainty/history
```

---

# 5. Future executable-fixture requirements

M1+ fixture encodings should preserve enough structure to inspect conceptually:

```text
fixture identity/version
IntentRequest attribution
Origin / Principal distinction
explicit Context and Temporal Basis when material
Catalog Snapshot identity
Provider provenance when used
ResolvedIntent / clarification / no-work classification
ordinary bounded work vs DelegatedWork role
Binding Rules / symbolic lineage
Capability Match / missing-capability condition
Governance / Authorization references when applicable
Executor vs Worker handoff role
Attempt / Outcome / WorkerResult lineage
Continuation lineage
expected forbidden transitions
```

Exact fields remain later work.

The fixture encoding must prove semantic distinctions rather than compare one opaque expected blob.

---

# 6. Stability rule

Later milestones may change Python types, serialization, identifiers, adapters, persistence, UI wording, provider/Worker transport, or recovery representation.

They must not silently change the **material semantic outcome** of these fixtures without an explicit architecture revision.

Examples:

```text
Scenario H:
no admitted tie-break -> no silent selection -> explicit continuation

Scenario B:
unknown effectful outcome -> no automatic Retry

Scenario C:
forbidden effect in current DelegatedWork
    -> cannot be enabled by Authorization alone
    -> material widening returns to IRR
```

---

# 7. M0.10 fixture verdict

The eight roadmap scenarios compose coherently under M0.1–M0.9 without requiring IRR to become:

- an ambient environment scanner;
- a shell-command generator;
- a policy/permission engine;
- an Executor;
- a general autonomous Worker;
- a provider-specific LLM wrapper;
- an HDE-, Character_OS-, Codexia-, Runplane-, or organism_lab-specific core.

The closure proof and M1 handoff are recorded in [`m0_closure.md`](m0_closure.md).
