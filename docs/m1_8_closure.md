# M1.8 — Executable M0.10 Fixtures & M1 Closure

Status: **complete and frozen in `main` once this closure PR merges**.

M1.8 closes the implementation phase that began with the frozen M0 Runtime Charter. The goal of M1 was not to build an autonomous agent or executor. It was to encode the M0 boundaries as immutable, attributable, canonical Intent Resolution IR and then prove those boundaries against the eight canonical M0.10 architecture scenarios.

At the start of this closure branch, all Scenario A–H executable fixtures are already merged through:

```text
main = 74c6290a1ed3bfabbf2dfaf4b218cb70ae012b9c
```

No new semantic runtime type is introduced by this closure. M1.8 closes by recording the executable scenario coverage and the final M1 boundary.

## 1. M1 is an IR closure, not an autonomy claim

The completed M1 chain can represent:

```text
IntentRequest
    |
    v
explicit attributable Context / Evidence
    |
    v
CandidateResolution
    |
    v
ResolvedIntent | ClarificationNeed | InformationNeed
    |
    +--> non-operational resolution / answer
    |
    v
BindingRule / BindingInput / BoundValue | BindingIssue
    |
    v
WorkPlan / WorkStep
    |
    +--> DelegatedWork / DelegatedWorkHandoff / WorkerResult
    |
    v
CapabilityRequirement
    |
    v
CapabilityCatalogSnapshot / CapabilityMatchEvaluation
    |
    v
WorkProposal
    |
    v
external GovernanceDecision / Authorization where applicable
    |
    v
CapabilityAttempt
    |
    v
CapabilityOutcome
    |
    v
ContinuationInput
    |
    v
SuccessorResolutionLineage
    |
    +--> ResolvedIntent | ClarificationNeed | InformationNeed
```

The existence of this representational chain does not mean IRR executes effects, owns Governance, schedules Workers, retries operations, or autonomously chooses new semantics.

## 2. Canonical M0.10 Scenario A — restore latest organism_lab backup

Scenario A is executable in two deliberately separate halves.

Discovery / binding / capability fixture:

```text
ResolvedIntent
→ bounded backup search
→ attributable returned candidates
→ admitted MAX_ATTRIBUTE BindingRule
→ unique newest backup BoundValue
→ restore WorkPlan
→ exact capability matching
```

Lifecycle / recovery fixture:

```text
archive.extract Attempt
→ normal protocol completion
→ completion not satisfied
→ filesystem read confirmed
→ filesystem write confirmed partial
→ ContinuationInput
→ successor Resolution requiring bounded inspection
```

The fixture preserves distinct source/read and destination/write scopes and proves:

```text
failed completion != no effect
partial effect != safe automatic retry
returned value != ambient authority
missing capability != shell fallback
```

## 3. Scenario B — send latest Voice Engine report through Telegram

Scenario B is also split between planning and lifecycle.

Planning proves:

```text
latest report Binding
+ exact Telegram destination Binding
→ telegram.send_file semantics
→ explicit filesystem read / network / disclosure effects
→ exact Capability Match
→ Governance-reviewed authority material
```

Lifecycle proves that a lost acknowledgement yields:

```text
lifecycle = interrupted
completion = unknown
network.use = confirmed_occurred
external.disclosure = unknown
```

and therefore:

```text
lost acknowledgement != failed
unknown delivery != no delivery
unknown outcome != automatic resend
```

## 4. Scenario C — bounded Codexia delegation

The successful delegation half proves that complex subordinate work is represented as explicit `DelegatedWork`, not disguised as an ordinary command.

The escalation half proves:

```text
WorkerNeed
!= scope grant
!= capability grant
!= Authorization

forbidden effect
+ "needed for the task"
!= permitted effect

WorkerResult
→ ContinuationInput
→ successor Resolution
```

The historical delegation envelope remains immutable when the Worker discovers a new scope or effect requirement.

## 5. Scenario D — ambiguous referent

Canonical request:

```text
"Запусти его."
```

The executable fixture proves:

```text
provider thinks organism_lab is likely
+ fluent rationale
!= referent authority

Material Ambiguity
→ ClarificationNeed
→ no WorkPlan
```

Provider confidence and Authorization cannot repair missing semantics.

## 6. Scenario E — Companion initiative

A Companion may originate a bounded operational suggestion without being rewritten as the human Principal.

The fixture preserves:

```text
Origin = companion
Principal = user
Origin != Principal
initiative != standing grant
capability match != authority
executor result provenance != companion provenance
```

A bounded authority-neutral read-only inspection can proceed without fabricating Authorization, while still exposing exact scope and actual executor provenance.

## 7. Scenario F — missing Signal capability

The exact requested operation is:

```text
signal.send_file
```

while the applicable Catalog contains:

```text
telegram.send_file
```

The fixture classifies Telegram as `OPERATION_MISMATCH`, produces `NO_COMPATIBLE_CAPABILITY`, and then fails closed before `ProposedWorkStep`.

```text
missing Signal capability
→ no WorkProposal
→ no Governance path
→ no Authorization
→ no Attempt
```

A nearby mechanism does not create fallback authority.

## 8. Scenario G — no operational intent

Canonical request:

```text
"Как ты думаешь, этот эксперимент хороший?"
```

The fixture proves that a valid `ResolvedIntent` may terminate as a non-operational conversational resolution.

```text
ResolvedIntent
→ answer / no operational work
```

It does not require a `WorkPlan`, and an empty/no-op WorkPlan is rejected by the Work IR itself.

```text
valid intent resolution != operational work
no operational work != fake noop operation
```

## 9. Scenario H — returned search data creates a material choice

Two returned backup candidates share the same greatest admitted modification time.

The original mechanical rule therefore produces:

```text
BindingIssue.TIE
```

not a winner.

The fixture proves:

```text
returned data
→ BindingIssue.TIE
→ ContinuationInput
→ successor ClarificationNeed
```

Input presentation order cannot choose the artifact. `ANY_INTERCHANGEABLE` / canonical-identity selection cannot be retrofitted after the result arrives. An unresolved BindingRule cannot be laundered into `BoundValue`.

Returned plan-local data is also not automatically rewritten as ambient Context or Observation merely because it influences the next semantic decision.

## 10. Cross-scenario negative architecture closure

Across A–H, the executable fixtures jointly preserve the M0 boundaries:

```text
Intent != Permission != Effect
Origin != Principal
Context != authority
Evidence != authority
provider proposal != IRR admission
ResolvedIntent != WorkPlan
WorkPlan != Authorization
Capability Match != Authorization
Catalog membership != availability
missing capability != fallback authority
DelegatedWork != Authorization
WorkerNeed != permission expansion
Attempt != Outcome
Outcome completion != effect certainty
unknown outcome != failed
failed completion != no effect
Retry != mutation of an old Attempt
ContinuationInput != Observation by default
returned data != new semantic decision authority
Binding tie != hidden tie-break
successor Resolution != successor WorkPlan
```

The fixtures are intentionally adversarial. Their purpose is not to demonstrate that happy paths serialize; it is to prove that tempting but invalid shortcuts remain unrepresentable or fail closed.

## 11. M1 implementation slices now closed

M1 is complete through the following frozen slices:

```text
M1.1  IntentRequest / canonical identity
M1.2  Context / Claim / Evidence / temporal / completeness IR
M1.3  CandidateResolution / Resolution outputs / uncertainty IR
M1.4  SymbolicReference / Binding IR
M1.5  Work / Delegation / WorkerResult IR
M1.6  Capability Catalog / Match / WorkProposal / Governance / Authorization IR
M1.7  Attempt / Outcome / Continuation / Successor Resolution IR
M1.8  Executable M0.10 Scenario A–H fixtures and M1 closure
```

M1.8 did not reopen the M0 charter and did not require a Scenario-specific DTO layer. The canonical scenarios compose the ordinary frozen M1 records.

## 12. What M1 deliberately does not claim

M1 completion does **not** mean IRR is a complete autonomous runtime.

M1 does not add:

- effect execution;
- shell/browser lowering as a universal fallback;
- ambient filesystem, network, memory, or account access;
- policy ownership inside IRR;
- automatic Governance approval;
- automatic retry or fallback policy;
- retry scheduling or loops;
- idempotency inference;
- Worker orchestration or recursive delegation policy;
- transport/provider implementations;
- persistence or event sourcing;
- parent-intent completion policy beyond represented local contracts;
- autonomous successor WorkPlan synthesis;
- background monitoring;
- HDE-, Companion-, Codexia-, or Organism-specific authority shortcuts.

Those are later implementation concerns and must preserve the now-frozen M0/M1 separation rather than bypass it.

## 13. Verification standard

Every M1.8 scenario slice was merged only after exact-head repository CI on the supported matrix:

```text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

The M1.8 development sequence repeatedly found useful errors despite otherwise-valid record construction, including source-contract/capability identity conflation, read/write scope conflation, and fixture assertions that referenced the wrong frozen field. Those were corrected before their outer scenario slices merged.

This is evidence for keeping executable architectural fixtures as permanent regression tests rather than treating M0.10 as documentation-only examples.

## 14. Closure criterion

M1 closes when all of the following remain true on the exact closure head:

```text
all eight M0.10 canonical scenarios have executable coverage
all M1.8 fixture tests pass
all earlier M1 tests and frozen identities still pass
README status describes M1 as complete
no runtime/API/wire-schema expansion is hidden in the closure delta
exact-head CI passes on Python 3.11–3.14
```

Once this closure PR merges, **M1 — Intent Resolution IR is complete and frozen**.

No M2 semantic milestone is declared here. The next milestone should be chosen explicitly rather than inferred from M1 completion.
