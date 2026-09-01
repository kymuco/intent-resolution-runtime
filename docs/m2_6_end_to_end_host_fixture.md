# M2.6 — End-to-End Host Fixture

Status: **implementation slice — first executable M2 end-to-end Host composition**.

M2.6 does not add a new orchestrator, mutable Host session, workflow engine, scheduler, executor, provider API, or authority layer. It proves that the already-frozen M2.1–M2.5 runtime slices can compose around one realistic M0.10 Scenario A lifecycle while exact immutable M1 records remain the semantic source of truth.

The fixture is intentionally an executable integration test rather than a new public `HostRuntime` abstraction.

```text
fixture composition != new orchestration authority
Host sequencing != canonical lifecycle state
M2 frontier != canonical record
```

## 1. Scenario

M2.6 uses the frozen Scenario A family:

```text
"Найди последний backup organism_lab,
распакуй в W:\organism_lab и запусти."
```

The fixture follows the path until an archive extraction returns known partial filesystem effects. At that point the correct lifecycle cannot continue to workspace inspection / launch as if restore succeeded. The explicit successor instead requires inspection of the exact destination state before any recovery action.

```text
partial extract != restore success
partial extract != launch readiness
failed completion != no effect
```

Stopping before launch is therefore part of the architecture proof, not an incomplete test.

## 2. Host composition path

The executable path is:

```text
IntentRequest
+ bounded ContextEnvelope
+ CandidateResolution
        |
        v
M2.1 Initial Resolution Orchestrator
        |
        +-- provider candidate alone -> ADMISSION_REQUIRED
        |
        `-- explicit IRR-owned admitter -> ResolvedIntent

ResolvedIntent
+ bounded search WorkPlan
        |
        v
M2.2 Work / Binding Orchestrator
        |
        `-- search plan has no external symbolic input

search CapabilityRequirement
+ exact Catalog evaluation
        |
        v
M2.3 Capability / Governance Orchestrator
        |
        `-- exact unique Capability Match; no hidden Governance inference

explicit attributable bounded search result material
+ already-admitted latest BindingRule
        |
        v
M1.4 evaluate_binding
        |
        +-- unique latest -> BoundValue
        `-- equal latest -> BindingIssue.TIE

BoundValue
+ exact extract WorkPlan
        |
        v
M2.2 Work / Binding Orchestrator
        |
        `-- external binding complete only after exact BoundValue is supplied

extract CapabilityRequirement
+ exact Catalog evaluation
+ WorkProposal
+ GovernanceDecision
        |
        v
M2.3 Capability / Governance Orchestrator
        |
        +-- exact Authorization transition candidate
        `-- admitted Authorization only after Host supplies it back

CapabilityAttempt
+ partial CapabilityOutcome
        |
        v
M2.4 Attempt / Outcome / Continuation Orchestrator
        |
        +-- Outcome history alone != automatic Continuation
        `-- explicit selected source + Host re-entry + successor lineage

same ResolvedIntent
+ exact extract WorkPlan
+ no delegation records
        |
        v
M2.5 Worker Lifecycle Orchestrator
        |
        `-- empty Worker surface remains valid ordinary capability path

successor ResolvedIntent
        |
        v
M2.2 Work / Binding Orchestrator
        |
        `-- no WorkPlan -> work disposition required, not automatic retry/recovery plan
```

## 3. Initial admission boundary

The fixture deliberately invokes M2.1 twice.

A single provider `CandidateResolution` first yields:

```text
ADMISSION_REQUIRED
```

Only an explicit IRR-owned admission function with exact `ResolutionAttribution` creates the `ResolvedIntent`.

The admitted semantics are not copied verbatim from provider text.

```text
provider proposes != IRR admits
one provider candidate != admission
```

## 4. Search and late Binding boundary

The bounded search phase contains no external symbolic input, so M2.2 may correctly report its external binding surface complete.

The concrete backup path still remains unknown until exact attributable search result material is available.

The Host then calls the already-frozen M1.4 mechanical `evaluate_binding` boundary using the already-admitted rule:

```text
latest = unique greatest admitted RFC3339 modification timestamp
```

No first-result or storage-order tie-break exists.

The adversarial fixture reproduces equal maximum timestamps and requires:

```text
BindingIssueKind.TIE
external_binding_complete = false
```

Therefore:

```text
unknown future value != unknown decision rule
Binding tie != hidden selection
```

## 5. Capability / Governance boundary

The search and extract phases use exact M1.6 Capability requirements and Catalog evaluations.

The fixture does not infer Capability Availability, invocation readiness, or authority from a unique match.

For the effectful extraction step the Host explicitly supplies:

```text
WorkProposal
GovernanceDecision(AUTHORIZE)
```

M2.3 first exposes the exact canonical `Authorization` as a transition candidate. That candidate is not considered admitted lifecycle history until the Host explicitly supplies the exact record back to M2.3.

```text
Capability Match != Authorization
GovernanceDecision != admitted Authorization history
Authorization transition candidate != admitted Authorization history
```

## 6. Attempt / partial Outcome boundary

The fixture creates one exact attributable `CapabilityAttempt` using:

- the exact extract capability evaluation;
- the exact selected backup `BoundValue`;
- the exact admitted `Authorization`.

The resulting `CapabilityOutcome` preserves independent dimensions:

```text
lifecycle = normal_protocol_completed
completion = not_satisfied
filesystem.read = confirmed_occurred
filesystem.write = confirmed_partial
```

This is intentionally not collapsed to one `failed` flag.

```text
not_satisfied != no effect
partial effect != retry permission
Outcome != parent completion
```

## 7. Outcome does not auto-reenter IRR

M2.4 is first invoked with Attempt + Outcome history only.

The fixture requires the Outcome to remain in:

```text
outcomes_not_selected_for_continuation
```

with no successor lineage.

Only after the Host explicitly selects that exact Outcome as continuation material and creates an attributable `ContinuationInput` does a `SuccessorResolutionLineage` become active.

```text
Outcome history != selected Continuation source
Outcome != automatic ContinuationInput
ContinuationInput != retry
```

## 8. Successor semantics do not create recovery work

The successor Resolution semantics require inspecting the exact destination state before any additional recovery operation and explicitly prohibit implicit retry and launch.

M2.2 is then invoked with the successor and no WorkPlan. The required result is:

```text
work_disposition_required = true
```

not a synthesized retry, compensation, status query, workspace inspection, or launch plan.

```text
successor ResolvedIntent != successor WorkPlan
Continuation != recovery policy
```

## 9. Worker boundary remains empty

Scenario A follows the ordinary bounded capability path. M2.5 is nevertheless invoked against the same predecessor and exact parent extract WorkPlan.

The correct Worker frontier is empty:

```text
DelegatedWork[] = ()
DelegatedWorkHandoff[] = ()
WorkerResult[] = ()
```

This proves that adding Worker lifecycle orchestration did not make Worker delegation a universal execution path.

```text
operational WorkPlan != Worker delegation by default
ordinary capability path != implicit Worker path
```

## 10. Replay / source-of-truth property

M2.6 introduces no mutable aggregate state. Every frontier is recomputed from explicit exact M1 inputs available at that point in the fixture.

The fixture itself sequences those calls like a Host would, but sequencing logic is not canonical state and does not gain semantic authority merely by living in one test.

```text
exact immutable M1 history
+ explicit Host inputs
-> existing M2 frontier derivations
```

No frontier is fed into another frontier as authoritative history. Only the exact M1 records represented by those frontiers cross slice boundaries.

## 11. What M2.6 deliberately does not add

M2.6 adds no:

- public Host API;
- mutable ResolutionSession / lifecycle object;
- orchestration super-frontier;
- effect executor;
- scheduler;
- provider transport;
- capability invocation;
- ambient retrieval;
- automatic Governance call;
- automatic Authorization admission;
- automatic Binding Input acquisition;
- retry/fallback/recovery policy;
- parent completion evaluator;
- Worker selection;
- persistence/event store;
- Scenario-A-specific production shortcut.

If a reusable Host composition abstraction is added later, it must be justified by repeated executable patterns after this integration proof rather than assumed before the orchestration boundaries have been exercised together.

## 12. Frozen M2.6 invariants

```text
Host composition != new semantic authority
provider candidate != admission
search WorkPlan != ambient search authority
unique Capability Match != Authorization
Binding tie != hidden tie-break
BoundValue != WorkPlan mutation
GovernanceDecision != admitted Authorization history
Authorization transition candidate != admitted Authorization history
Attempt != Outcome
not_satisfied != no effect
partial effect != retry permission
Outcome history != selected Continuation source
ContinuationInput != retry
SuccessorResolutionLineage != recovery policy
successor ResolvedIntent != successor WorkPlan
ordinary capability path != implicit Worker path
M2 frontier != canonical history
```
