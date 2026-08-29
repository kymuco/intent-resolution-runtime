# M0.10 — Reference Scenarios

Status: **normative architecture fixtures for M0.10**.

This document closes the M0 boundary freeze by exercising the already-frozen M0.1–M0.9 contracts against concrete end-to-end scenarios.

M0.10 does **not** introduce a new runtime model, Python schema, command language, policy engine, executor protocol, Worker protocol, provider API, or recovery implementation. It supplies architecture fixtures: stable semantic examples that later M1+ implementations and tests must be able to represent without violating the M0 contracts.

The fixtures answer one question:

> Can the frozen IRR architecture explain realistic human-, companion-, provider-, Worker-, capability-, governance-, execution-, and recovery-facing flows without hidden context, hidden authority, hidden capability discovery, hidden semantic choice, or hidden retry?

The required answer is **yes**.

---

## 1. How to read these fixtures

Each reference scenario contains:

```text
request / trigger
explicit attributable inputs
expected resolution semantics
expected work / no-work shape
binding / capability expectations
applicable authority boundary
handoff / downstream role
result / continuation semantics
forbidden shortcuts
M0 contracts exercised
```

The examples are semantic, not executable wire fixtures yet.

Names such as `filesystem.search`, `archive.extract`, or `telegram.send_file` are illustrative Semantic Operations or Capability labels consistent with the frozen M0 documents. M1+ decides exact identifiers, immutable schemas, serialization, digests, and validation APIs.

A reference scenario therefore constrains meaning while intentionally leaving representation open.

```text
architecture fixture != frozen JSON
architecture fixture != executable command sequence
architecture fixture != Authorization
architecture fixture != test implementation
```

Later tests MAY encode these scenarios as immutable fixtures, but the encoded form must preserve the semantics frozen here rather than redefining them.

---

## 2. Cross-scenario invariants

Every scenario in this document preserves the following global invariants:

```text
origin != principal
origin != authority
context != authority
intent != authorization
resolution != authorization
WorkPlan != execution
WorkPlan != Authorization
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

No fixture may be made to “work” by weakening one of those distinctions.

---

# Scenario A — Restore the latest `organism_lab` backup

## A.1 Request

```text
"Найди последний backup organism_lab,
распакуй в W:\\organism_lab и запусти."
```

Conceptual English gloss:

```text
Find the latest organism_lab backup,
extract it to W:\organism_lab, and launch it.
```

This scenario tests bounded discovery, explicit selection semantics, Late Binding, archive inspection/extraction, filesystem mutation, process launch, capability admission, authority separation, and result continuation.

## A.2 Explicit fixture inputs

The fixture assumes the Host supplies attributable material sufficient to bound the request, conceptually:

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

Temporal / evidence basis:
    candidate timestamps are supplied by the bounded search result

Capability Catalog Snapshot:
    filesystem.search
    artifact.select or equivalent admitted selection support
    archive.inspect
    archive.extract
    workspace.inspect
    process.launch
```

The exact paths are fixture data, not an IRR right to inspect the rest of the machine.

```text
D:\Backups in Context
    !=
authority to search the whole computer
```

If the Host does **not** supply a bounded search root or another admitted scope rule, IRR must not invent `D:\Backups`, scan home directories, inspect every drive, or ask a Cognitive Provider to discover the backup ambiently.

## A.3 Expected initial resolution

The request is operational and may resolve into bounded semantic work when all material terms are sufficiently specified.

Conceptually:

```text
IntentRequest
    |
    v
ResolvedIntent
    |
    v
WorkPlan
```

The WorkPlan represents semantic work, not commands:

```text
1. filesystem.search
      scope: D:\Backups
      match: organism_lab backup constraint
      output: $backup_candidates

2. artifact.select
      input: $backup_candidates
      rule: greatest admitted modification timestamp
      output: $selected_backup

3. archive.inspect
      input: $selected_backup
      output: $archive_manifest / launch-relevant metadata

4. archive.extract
      input: $selected_backup
      destination: W:\organism_lab

5. workspace.inspect
      scope: W:\organism_lab
      output: bounded launch metadata

6. process.launch
      target: a launch target selected only under already-admitted bounded semantics
```

This is illustrative dataflow. M0.10 does not freeze whether selection is represented as its own WorkStep, a Binding Rule attached to a Symbolic Reference, or another M1-compatible representation, provided the M0 semantics remain visible and bounded.

## A.4 Late Binding expectations

The concrete backup path is unknown before search.

Therefore:

```text
$selected_backup
    = future Bound Value
```

The value may be filled later only by applying the already-admitted selection semantics to attributable Binding Input.

```text
unknown concrete backup
    !=
unknown decision rule
```

IRR must not permit:

```text
"pick whichever archive looks right"
```

unless such discretion was already admitted as a bounded Selection Policy.

## A.5 Capability expectations

Every operational capability-dependent unit must match the exact applicable Catalog Snapshot.

If `archive.extract` is absent:

```text
missing_capability
```

is the correct capability condition.

IRR must not silently lower extraction into:

```text
PowerShell Expand-Archive
tar
7-Zip CLI
browser upload to an online extractor
arbitrary Python code
```

merely because those mechanisms might implement extraction.

A generic command capability is not a universal semantic adapter.

## A.6 Governance / authority expectations

Semantic validity does not authorize effects.

The scenario may involve materially distinct authority surfaces:

```text
read/search backup directory
read archive metadata
write/replace W:\organism_lab
launch a process
```

An external Governance mechanism may authorize all of them, authorize only an already represented subset, constrain mutation, require review, or deny some portion.

For example:

```text
Governance:
    inspect backup and archive metadata: authorized
    extraction / mutation: require review
    process launch: require review
```

This does not silently rewrite the original objective into “inspect only.”

If Governance semantically changes the objective, that change returns through IRR Continuation / successor semantics.

## A.7 Handoff expectations

Ordinary bounded operations use the capability/executor path rather than Worker delegation merely because several steps exist.

```text
bounded WorkStep
    -> applicable authority boundary when required
    -> CapabilityHandoff
    -> Executor
```

A Worker is not required for the canonical fixture.

## A.8 Result expectations

Each downstream result remains scoped.

```text
search succeeded
    !=
restore succeeded

archive extraction succeeded
    !=
process launch succeeded

process launch succeeded
    !=
parent intent satisfied unless the admitted completion semantics say so
```

Known partial effects survive failure classification. For example, extraction may modify the destination and later readiness validation may fail.

## A.9 Forbidden shortcuts

The implementation must not:

- scan arbitrary drives because the backup root was omitted;
- infer a backup from filename aesthetics rather than admitted selection semantics;
- choose the first search result as an implicit tie-breaker;
- invent archive/process capabilities;
- convert plan validity into permission;
- let an Executor choose a materially different launch target;
- erase partial filesystem effects after failure;
- hide a retry loop inside `process.launch`.

## A.10 Contracts exercised

```text
M0.1  Origin / Principal / roles
M0.2  explicit Context / ambiguity / attribution
M0.3  semantic WorkPlan / bounded steps
M0.4  symbolic dataflow / Late Binding / Selection Policy
M0.5  Capability Catalog / missing capability
M0.6  Governance / Authorization
M0.9  scoped Outcome / partial effects / Retry boundary
```

---

# Scenario B — Send the latest Voice Engine report through Telegram

## B.1 Request

```text
"Отправь мне последний Voice Engine report в Telegram."
```

This scenario tests artifact discovery, recipient binding, external disclosure, network effects, authority, and uncertain effect recovery.

## B.2 Explicit fixture inputs

Conceptually:

```text
Origin attribution:
    human

Principal:
    user

Context:
    bounded report search scope
    report family = Voice Engine report
    explicit recipient identity / Telegram destination for "me"

Selection semantics:
    latest = explicit bounded report ordering rule

Capability Catalog Snapshot:
    artifact search / selection capability
    telegram.send_file or equivalent bounded Telegram-send capability
```

The pronoun `me` is resolvable only if the Host supplies one attributable recipient binding suitable for the request.

```text
Principal=user
    !=
automatic Telegram recipient binding
```

If multiple Telegram destinations for the user remain materially possible, IRR must clarify rather than guess.

## B.3 Expected work semantics

Conceptually:

```text
artifact.search
    -> $report_candidates

artifact.select
    rule: admitted latest-report semantics
    -> $selected_report

telegram.send_file
    artifact: $selected_report
    recipient: explicit bound Telegram destination
```

The send operation must expose its material effect surface:

```text
network use
external disclosure of selected report
recipient / destination
```

## B.4 Disclosure and authority

Reading/selecting the report is not the same authority as sending it externally.

```text
read authorization != disclosure authorization
local artifact access != Telegram send authorization
recipient A authorization != recipient B authorization
```

A Cognitive Provider knowing that Telegram supports files does not create the capability or authority.

## B.5 Normal success path

If the downstream capability provides sufficient attributable completion evidence under its admitted contract, the send Attempt may be classified `succeeded` for that scoped send operation.

```text
transport response
    is sufficient only if
admitted capability completion semantics say so
```

The exact receipt schema is deferred.

## B.6 Lost acknowledgement / unknown outcome branch

This branch is normative for M0.9 compatibility.

Suppose:

```text
Attempt 1
    request transmitted to Telegram-side service
    connection lost before material completion acknowledgement
```

If evidence is insufficient to establish whether the recipient-visible send occurred:

```text
Outcome = unknown_outcome
```

IRR must **not** infer:

```text
no acknowledgement
    -> failed
    -> send again
```

The correct recovery path is conceptually:

```text
unknown_outcome
    -> explicit recovery assessment
    -> optional separately admitted status query / evidence acquisition
    -> retry only if safe-replay basis + capability + authority conditions permit
```

A Retry, if later admitted, is a **new Attempt** with separate lineage.

## B.7 Fallback branch

Switching to email, Signal, another Telegram account, a browser UI, or another provider is not an automatic retry.

A material change of recipient, provider/service, disclosure surface, capability, or completion semantics is fallback/successor work and must pass the applicable semantic/capability/authority boundaries.

```text
Telegram unknown_outcome
    !=
permission to send through another channel
```

## B.8 Forbidden shortcuts

The implementation must not:

- infer recipient from an unverified username guess;
- disclose the report to a Cognitive Provider merely because it helps select the file;
- treat `telegram.send_file` existence as Authorization;
- retry an effectful unknown send automatically;
- change recipient/channel to “make it work”;
- erase Attempt 1 after a later successful Attempt 2.

## B.9 Contracts exercised

```text
M0.1  Principal / Origin
M0.2  recipient evidence / explicit Context
M0.4  late-bound report selection
M0.5  Telegram Capability Match
M0.6  external disclosure Authorization
M0.7  provider knowledge != capability / authority
M0.9  Attempt / unknown_outcome / retry / fallback
```

---

# Scenario C — Delegate CG2.42 analysis to Codexia

## C.1 Request

```text
"Изучи результаты CG2.42 и предложи следующий experiment."
```

This is intentionally different from an ordinary bounded operation such as `filesystem.search`.

It requires long-form subordinate analysis and therefore exercises the Worker delegation boundary.

## C.2 Explicit fixture inputs

Conceptually:

```text
Origin attribution:
    human

Principal:
    user

Context:
    bounded CG2.42 result/evidence surface
    relevant project lineage

Worker surface:
    Worker identity/adapter = Codexia-compatible worker
    permitted context = explicitly delegated CG2.42 material
    permitted objective = analyze supplied results and propose next experiment candidate(s)
    forbidden effects = no repository mutation, no push, no external publication unless separately represented/authorized
    expected deliverables = candidate experiment proposal(s) + rationale + evidence references
    completion contract = return bounded attributable analysis result
```

Exact Worker transport and schemas are deferred.

## C.3 Expected delegation semantics

The request may resolve into a bounded `DelegatedWork` representation rather than an ordinary opaque WorkStep.

Conceptually:

```text
ResolvedIntent / parent WorkPlan semantics
        |
        v
DelegatedWork
        |
        v
DelegatedWorkHandoff
        |
        v
Codexia Worker
```

The Worker may own a subordinate lifecycle inside the envelope:

```text
inspect supplied evidence
analyze
compare candidates
revise internal subordinate plan
produce deliverable
```

That subordinate lifecycle is not the parent IRR WorkPlan.

## C.4 Capability and authority ceiling

If the Worker is allowed to read supplied files or use admitted analysis capabilities, that allowed surface is a **ceiling**, not a promise and not a hidden selection policy.

```text
allowed capability != capability existence
allowed capability != Authorization
allowed capability set != arbitrary Worker choice
```

A newly required network search, repository mutation, external model disclosure, commit, push, or process launch cannot be smuggled in as a “necessary” Worker step unless already represented inside the delegation and covered by applicable downstream authority.

## C.5 WorkerResult semantics

The Worker returns attributable `WorkerResult` material.

Conceptually:

```text
WorkerResult:
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

IRR receives the result through an explicit continuation boundary and determines what it means for the parent lifecycle.

## C.6 Worker says `done`

A bare completion claim is insufficient.

```text
worker says done
    !=
Delegated Completion Contract satisfied
```

The receiving boundary must establish whether required deliverables are actually present under the delegated completion semantics.

## C.7 Escalation branch

Suppose the Worker decides it needs an additional experiment archive outside the delegated context.

The correct behavior is:

```text
WorkerResult / escalation need
    -> IRR Continuation
```

not:

```text
Worker scans unrelated directories
```

and not:

```text
Worker launches another IRR Worker automatically
```

## C.8 Forbidden shortcuts

The implementation must not:

- encode the whole delegated lifecycle as `codexia.do_work` ordinary WorkStep;
- give Codexia ambient repository/home-directory access;
- let the Worker create its own authority;
- let “needed for the task” expand scope automatically;
- relabel Worker-originated findings as user statements;
- treat Worker confidence as Evidence amplification;
- treat returned proposal as an admitted successor plan without IRR continuation.

## C.9 Contracts exercised

```text
M0.1  Worker / Origin / Principal roles
M0.2  provenance / Evidence / Context
M0.3  ordinary WorkStep boundedness
M0.5  capability ceiling remains external catalog semantics
M0.6  Worker does not own Authorization
M0.7  Cognitive Provider != Worker
M0.8  DelegatedWork / WorkerResult / parent lifecycle ownership
M0.9  Worker failure/result does not collapse parent outcome
```

---

# Scenario D — Ambiguous referent: “Launch it”

## D.1 Request

```text
"Запусти его."
```

Assume the admitted Context does not identify one unique launch target and no already-admitted bounded referent rule resolves the pronoun.

## D.2 Expected result

This is a blocking `Material Ambiguity`.

IRR must return a clarification path rather than a ResolvedIntent for process launch.

Conceptually:

```text
IntentRequest
    |
    v
Material Ambiguity
    |
    v
Clarification
```

There is no operational WorkPlan yet.

```text
clarification != ResolvedIntent
clarification != WorkPlan
clarification != parent intent completion
```

## D.3 Cognitive Provider branch

A Cognitive Provider may propose:

```text
"probably the project discussed most recently"
confidence = 0.94
```

That remains provider-produced candidate inference.

```text
provider confidence != ambiguity-resolution authority
model prior != admitted Evidence
```

IRR must not admit a materially different executable target solely because the model prefers it.

## D.4 No ambient discovery

IRR/provider must not resolve the ambiguity by silently:

- scanning running processes;
- inspecting the foreground window;
- reading shell history;
- searching recent files;
- inspecting HDE memory not supplied in Context;
- choosing the first executable found.

If the Host explicitly supplies new attributable information, Continuation may resolve the referent later.

## D.5 Authority cannot repair ambiguity

Even if Governance says “launching applications is generally allowed,” that does not tell IRR **which application** the user meant.

```text
Authorization != ambiguity resolution
```

## D.6 Contracts exercised

```text
M0.2  Material Ambiguity / Clarification / no ambient Context
M0.3  no WorkPlan before admitted semantics
M0.6  Authorization cannot repair semantics
M0.7  provider confidence cannot choose material referent
```

---

# Scenario E — Companion initiative

## E.1 Trigger

A companion such as Kaguya proposes:

```text
"Стоит проверить последние логи."
```

The fixture intentionally distinguishes who generated the request from whose interests the request may serve.

## E.2 Attribution

Conceptually:

```text
Origin:
    companion

Principal:
    user
```

The companion must not be relabeled as human Origin merely because it serves the user.

```text
origin = companion
origin != human
principal = user
origin != authority
```

## E.3 Resolution

If “latest logs” and their bounded source are already sufficiently specified by explicit Context, IRR may resolve a bounded inspection objective.

If the log scope or referent is materially ambiguous, clarification / additional information is required instead.

The companion’s confidence or familiarity with the project does not create missing Context.

## E.4 Authority

Companion initiative is not delegated permission by default.

```text
companion intent != Authorization
companion recommendation != Governance Decision
```

The embedding system may later have a standing externally defined grant for a bounded read-only class. If so, its applicability is established by Governance/Host authority semantics, not inferred by IRR from the companion relationship.

## E.5 Capability path

If the resolved objective requires log inspection, required capabilities must come from the applicable Catalog Snapshot.

The companion cannot imply:

```text
"I suggested it, therefore I may inspect arbitrary files."
```

## E.6 Result provenance

Any resulting Observation/Outcome remains attributable to the actual source/executor boundary.

It is not rewritten as a human statement merely because the Principal is the user.

## E.7 Forbidden shortcuts

The implementation must not:

- relabel companion Origin as human;
- treat relationship/history as authority;
- grant companion ambient memory/filesystem access through IRR;
- infer a standing grant unless an external Governance contract supplies one;
- report executed effects as if the user explicitly requested them when they did not.

## E.8 Contracts exercised

```text
M0.1  Origin != Principal != authority
M0.2  explicit Context / attribution
M0.5  capability admission
M0.6  external Governance / reusable grants only if externally supplied
M0.7  cognition/recommendation != authority
```

---

# Scenario F — Missing Signal capability

## F.1 Request

```text
"Отправь файл через Signal."
```

Assume the file and recipient semantics are otherwise sufficiently resolved, but the exact applicable Capability Catalog Snapshot contains no compatible Signal send capability.

## F.2 Expected capability result

The required semantic operation is valid as requested work, but no compatible admitted capability exists.

Therefore:

```text
missing_capability
```

The work path is blocked under that Catalog Snapshot.

This does not require inventing a fake execution Attempt.

```text
missing_capability
    -> blocked path
    -> no Signal effect Attempt began
```

## F.3 What absence does not mean

```text
missing_capability != Denial
missing_capability != global impossibility
missing_capability != permission to search for plugins
missing_capability != fallback authority
```

Signal might be technically available elsewhere in the world or machine. That is irrelevant to the exact Catalog Snapshot currently admitted to IRR.

## F.4 Forbidden fallback

IRR, Cognitive Provider, Executor, or Worker must not silently substitute:

```text
Telegram
email
browser automation
shell command
Signal desktop UI scraping
new plugin discovery
arbitrary code
```

If the user later accepts a materially different channel, that is explicit successor semantics rather than hidden fallback.

If an external Host later supplies a new Catalog Snapshot containing a Signal capability, the successor path must preserve lineage and revalidate capability/authority conditions.

## F.5 Governance cannot synthesize capability

Even an explicit Authorization such as:

```text
"You may send this file through Signal."
```

cannot manufacture a missing execution capability.

```text
Authorization + missing_capability != executable work
```

## F.6 Contracts exercised

```text
M0.3  semantic operation remains distinct from mechanism
M0.5  exact Catalog Snapshot / fail-closed missing capability
M0.6  Authorization != capability existence
M0.7  provider knowledge cannot create capability
M0.8  Worker cannot be capability fallback
M0.9  pre-attempt blocked != failed Attempt
```

---

# Scenario G — No operational intent

## G.1 Request

```text
"Как ты думаешь, этот эксперимент хороший?"
```

Assume the relevant experiment material is already explicitly supplied or otherwise admitted as Context for the inquiry.

## G.2 Expected resolution

The request is an inquiry/evaluation, not automatically a request to change the world.

IRR may admit a non-operational ResolvedIntent such as conceptually:

```text
answer / assessment requested
no operational work required
```

No WorkPlan is manufactured merely to normalize the request into actions.

```text
ResolvedIntent != WorkPlan requirement
answer-only intent -> no operational WorkPlan
```

## G.3 Cognitive Provider use

IRR may invoke a permitted Cognitive Provider to propose evaluative semantics or an answer path.

Provider output remains `CandidateResolution` material until IRR admission.

If remote provider disclosure would expose experiment material, that disclosure remains an explicit boundary rather than an automatic consequence of “just reasoning.”

## G.4 Governance

M0 does not impose a universal Governance requirement on every internal/non-operational computation.

A Host may impose product-level review or disclosure controls, but IRR does not manufacture a WorkProposal solely because every intent must look operational.

## G.5 Forbidden shortcuts

The implementation must not silently turn the question into:

- run another experiment;
- inspect additional files ambiently;
- ask Codexia to modify the experiment;
- commit a proposed change;
- execute a tool call emitted by the model.

If operational follow-up is later requested, that becomes explicit successor intent/work semantics.

## G.6 Contracts exercised

```text
M0.2  bounded Context / evidence semantics
M0.3  WorkPlan is conditional, not universal
M0.6  no manufactured WorkProposal for answer-only resolution
M0.7  provider proposes, IRR admits; reasoning transport may disclose
```

---

# Scenario H — Observation creates a new material choice

## H.1 Initial request

Use the backup-restore family from Scenario A.

Assume the admitted selection semantics are:

```text
select the unique latest matching backup
by greatest modification timestamp
```

The initial search returns:

```text
backup-A.zip  mtime = T
backup-B.zip  mtime = T
```

and both otherwise satisfy the admitted match constraints.

There is no admitted tie-break rule.

## H.2 Binding result

The Binding Rule cannot produce one unique Bound Value without inventing a new semantic choice.

Therefore:

```text
Binding Rule evaluation
    -> multiple equally admissible candidates
    -> no Bound Value
```

The implementation must not choose:

- first result;
- lexicographically first filename;
- smaller/larger archive;
- most recently returned API item;
- the candidate preferred by an LLM;
- the candidate preferred by an Executor;
- a random candidate.

unless that choice rule was already admitted.

## H.3 Continuation

The new material choice returns through IRR Continuation.

Conceptually:

```text
search result / Binding Input
        |
        v
unresolved material selection
        |
        v
IRR Continuation
        |
        v
Clarification
```

A user clarification such as:

```text
"Use backup-B.zip."
```

may later support successor semantics / binding lineage.

The historical initial WorkPlan/rule is not silently rewritten to pretend the tie-break existed from the beginning.

## H.4 Governance interaction

An Authorization that covered the symbolic class “the uniquely latest backup selected by rule R” does not necessarily cover a user-selected alternative after rule R failed to yield a unique value.

The new concrete/successor semantics must be checked against the applicable external authority scope.

```text
binding ambiguity resolved
    !=
authority automatically expanded
```

## H.5 Provider interaction

A Cognitive Provider may explain the tie or propose a clarification question.

It must not resolve the tie by confidence ranking unless the admitted semantics explicitly permit provider judgment for that material choice.

## H.6 Contracts exercised

```text
M0.2  Material Ambiguity / explicit clarification
M0.3  successor semantics instead of self-modifying plan
M0.4  Binding Rule / tie / no hidden Selection Policy
M0.6  rebound/successor value does not silently inherit authority
M0.7  provider confidence cannot invent tie-break semantics
```

---

# 3. Scenario × boundary matrix

The canonical eight fixtures collectively cover the M0 boundary surface.

| Scenario | M0.1 roles | M0.2 trust/context | M0.3 work | M0.4 binding | M0.5 capability | M0.6 governance | M0.7 provider | M0.8 worker | M0.9 recovery |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A Restore backup | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |  |  | ✓ |
| B Telegram | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |  | ✓ |
| C Codexia | ✓ | ✓ | ✓ |  | ✓ | ✓ | ✓ | ✓ | ✓ |
| D Ambiguous referent |  | ✓ | ✓ |  |  | ✓ | ✓ |  |  |
| E Companion initiative | ✓ | ✓ | ✓ |  | ✓ | ✓ | ✓ |  |  |
| F Missing Signal capability |  |  | ✓ |  | ✓ | ✓ | ✓ | ✓ | ✓ |
| G No operational intent |  | ✓ | ✓ |  |  | ✓ | ✓ |  |  |
| H Observation changes plan |  | ✓ | ✓ | ✓ |  | ✓ | ✓ |  |  |

A blank means the milestone is not the scenario's primary distinguishing feature, not that the milestone ceases to apply.

---

# 4. Negative architecture assertions

The fixtures are considered failed if an implementation requires any of these shortcuts to pass:

```text
ambient filesystem/repository/browser/memory inspection
implicit wall clock/timezone when time is material
provider confidence as factual or ambiguity authority
provider tool call as direct execution permission
shell/browser fallback for missing semantic capability
WorkPlan as arbitrary scripting language
ordinary WorkStep hiding an autonomous Worker loop
companion/Worker Origin relabeled as human
principal identity treated as permission
Governance approval used to repair semantic ambiguity
Capability availability treated as Authorization
DelegatedWork treated as blanket Worker authority
WorkerResult treated as parent completion
failure treated as proof of no effect
timeout treated as proof of failure
unknown effectful outcome automatically retried
fallback treated as continuation of the same Attempt
later success rewriting earlier uncertain/failed history
```

These are not implementation preferences; they are consequences of M0.1–M0.9.

---

# 5. Future executable-fixture requirements

When M1+ turns these scenarios into code-level fixtures, each encoded case should preserve enough structure to inspect conceptually:

```text
fixture identity / version
input IntentRequest attribution
Principal / Origin distinctions when material
explicit Context surface
Temporal Basis when material
Catalog Snapshot identity
candidate/provider provenance when used
ResolvedIntent / clarification / no-work classification
WorkPlan or DelegatedWork semantics when produced
Binding Rules / symbolic lineage when used
Capability Match / missing-capability condition
WorkProposal / Governance / Authorization references when applicable
Handoff role: Executor vs Worker
Attempt / Outcome lineage when downstream work occurs
Continuation lineage when new material information arrives
expected forbidden transitions
```

Exact fields are M1+ work.

M0.10 freezes only that future executable fixtures must be capable of proving the architectural distinctions, not merely comparing one opaque expected JSON blob.

---

# 6. Fixture stability rule

These scenarios are architecture fixtures, not product-specific permanent APIs.

Later milestones may change:

- Python class names;
- serialization shapes;
- exact operation identifiers;
- adapter names;
- persistence implementation;
- UI wording;
- provider/Worker transport;
- recovery state representation.

They must **not** silently change the material semantic outcome of the fixtures without an explicit architectural revision.

For example, later implementation may represent Scenario H using a typed `BindingFailure`, a continuation record, or another schema, but it must still preserve:

```text
no admitted tie-break
    -> no silent candidate selection
    -> explicit continuation / clarification
```

Likewise Scenario B may use a durable idempotency contract later, but absent sufficient evidence it must still preserve:

```text
unknown effectful outcome != automatic retry
```

---

# 7. M0.10 reference-scenario verdict

The eight roadmap scenarios can be represented coherently using the M0.1–M0.9 boundaries without requiring IRR to become:

- a shell-command generator;
- an ambient environment scanner;
- a policy/permission engine;
- an executor;
- a general autonomous Worker;
- a provider-specific LLM wrapper;
- an HDE-, Character_OS-, Codexia-, Runplane-, or organism_lab-specific subsystem.

The architecture therefore has a coherent end-to-end semantic explanation for the reference set.

The M0 closure proof and M1 handoff are recorded separately in [`m0_closure.md`](m0_closure.md).
