# M0.3 — Intent → Work Boundary

Status: **normative for M0.3**.

This document freezes how Intent Resolution Runtime (IRR) may transform an admitted `ResolvedIntent` into bounded semantic operational work. It extends the M0.1 product charter and M0.2 trust/context/resolution semantics without introducing runtime code, exact Python schemas, executable adapters, or authority.

M0.3 answers one question:

> When operational work is required, what kind of representation may IRR produce?

The answer is a bounded semantic `WorkPlan`, not executable code.

```text
IntentRequest
     |
     v
resolution
     |
     v
ResolvedIntent
     |
     +--------------------+
     | no work required   | operational work required
     v                    v
non-operational        WorkPlan
resolution                |
                          v
                      WorkStep[]
```

A `WorkPlan` describes requested work. It does not execute that work and does not authorize it.

```text
work description != execution
work description != authorization
```

## 1. Work planning is conditional, not universal

Not every `ResolvedIntent` yields operational work.

IRR MUST create a `WorkPlan` only when the admitted semantics actually require operational work.

IRR MUST NOT manufacture work merely to normalize every intent into the same shape.

Paths that do not require a `WorkPlan` include:

- answer-only inquiries;
- explanation-only requests;
- determinations that no operational work is required;
- clarification or continuation paths that have not yet admitted a successor `ResolvedIntent`.

A clarification or pre-resolution continuation path does not produce a WorkPlan, but it also does not by itself complete the parent intent lifecycle.

Therefore:

```text
ResolvedIntent != WorkPlan requirement
clarification != intent completion
```

## 2. Semantic operations, not implementation commands

A `WorkPlan` MUST represent **what operation is requested**, not a platform-specific command sequence for how an executor happens to implement it.

Conceptual semantic operation examples include:

```text
filesystem.search
artifact.select
archive.inspect
archive.extract
workspace.inspect
process.launch
```

IRR MUST NOT lower those semantics into implementation commands such as:

```text
Expand-Archive ...
Start-Process ...
tar -xf ...
cmd.exe /c ...
powershell.exe -Command ...
bash -c ...
```

merely because such commands could implement the operation.

The mapping from semantic operation to executable mechanism belongs downstream of IRR.

```text
semantic operation != implementation command
```

Exact operation identifier syntax remains deferred.

## 3. Platform neutrality without effect-changing substitution

IRR core work semantics MUST NOT depend on a hard-coded catalog of Windows commands, Linux utilities, macOS applications, shell built-ins, browser automation snippets, or language-specific libraries.

A plan that means `archive.extract` should remain semantically recognizable as the same requested operation whether a downstream executor eventually uses:

- a native operating-system API;
- a library call;
- a sandboxed local process;
- another bounded implementation whose material effect surface is compatible with the represented work semantics.

Platform neutrality does **not** mean that any implementation is semantically interchangeable.

An implementation choice that introduces a new material effect — for example uploading an archive to a remote service in order to extract it — is not a transparent implementation substitution unless that disclosure is already represented explicitly in the work semantics and handled by the applicable downstream authority boundary.

```text
platform neutrality != effect-changing substitution
implementation equivalence != permission to hide new effects
```

Platform-specific execution details may exist downstream. They MUST NOT become IRR work semantics merely because one implementation currently uses them, and they MUST NOT silently add material effects that the WorkPlan does not represent.

## 4. WorkPlan is not a scripting language

A `WorkPlan` is a bounded work representation. It is not a general-purpose programming language.

IRR MUST NOT turn WorkPlan into a mini-Python, mini-shell, workflow DSL with arbitrary control flow, or another embedded execution language.

A v1 `WorkPlan` may conceptually represent:

```text
finite steps
explicit dependencies
symbolic inputs and outputs
bounded ordering
explicit continuation points
```

It MUST NOT contain or acquire semantics equivalent to:

```text
arbitrary loops
unbounded recursion
hidden retries
arbitrary embedded code
eval / exec semantics
self-modifying plan generation
opaque shell fragments as plan control flow
```

Exact schemas are deferred to M1.

## 5. Boundedness

A `WorkPlan` MUST be structurally bounded at the time it is admitted.

Boundedness means the plan has a finite, inspectable set of planned work units and does not hide an unbounded autonomous process behind a step or control construct.

Boundedness MUST NOT be laundered through a single opaque WorkStep. An ordinary WorkStep's semantic contract must itself be bounded enough to inspect as a requested operation.

For example, an ordinary WorkStep MUST NOT mean:

```text
keep observing the environment,
deciding what to do,
and acting until the goal is achieved
```

while presenting that open-ended agent loop as one finite step.

```text
finite wrapper != bounded semantics
bounded WorkPlan != opaque autonomous WorkStep
```

A downstream capability may perform a bounded operation according to its own explicit contract, but IRR MUST NOT encode an unbounded semantic loop such as:

```text
while not done:
    inspect environment
    decide next action
    execute action
```

inside an ordinary `WorkPlan`.

If long-form delegated cognition or an open-ended subordinate lifecycle is required, it belongs to the distinct Worker delegation boundary frozen later by M0.8, not to an ordinary WorkStep disguised as a capability.

If new semantic decisions become necessary after new information arrives, the plan returns to an IRR continuation boundary rather than extending itself indefinitely.

```text
new semantic decision -> IRR continuation
```

## 6. WorkStep semantics

A `WorkStep` is a bounded semantic unit of requested operational work inside a `WorkPlan`.

M0.3 does not freeze exact fields, but later representations MUST preserve enough semantics to distinguish at least:

- what operation the step requests;
- what prior information or symbolic inputs it depends on;
- what semantic output it is expected to produce, if any;
- what ordering or dependency constraints apply;
- what material effect or observation role the step has when that distinction matters;
- how the step derives from the parent `ResolvedIntent` and `WorkPlan`.

An ordinary WorkStep MUST be inspectably bounded in its semantic purpose. Naming a broad or opaque operation MUST NOT bypass the WorkPlan boundedness invariant.

A `WorkStep` MUST NOT gain authority merely because it is well formed.

```text
valid WorkStep != authorized WorkStep
```

## 7. Dependency is not general control flow

A dependency states that one planned work unit requires another planned result or ordering constraint.

Dependencies MAY express a finite partial order between steps.

Dependencies MUST NOT be used to smuggle arbitrary program control flow into the plan.

In particular, dependency semantics MUST NOT become hidden equivalents of:

- unbounded loops;
- arbitrary exception handlers;
- implicit retries;
- open-ended branch generation;
- runtime code evaluation.

A WorkPlan dependency graph MUST be finite and acyclic for v1 planning semantics.

This does not prohibit downstream capabilities from having their own bounded internal implementation behavior. It prohibits IRR from becoming the owner of a general-purpose execution language.

## 8. Ordering is semantic and minimal

Ordering constraints MUST exist only where order matters to the meaning or validity of the requested work.

IRR SHOULD NOT impose unnecessary total ordering when steps are semantically independent.

For example:

```text
filesystem.search
      |
      v
artifact.select
      |
      v
archive.inspect
```

has meaningful dependencies.

By contrast, two independent inspections need not become sequential merely because a planner generated them in a particular textual order.

```text
presentation order != execution dependency
```

Exact scheduling belongs downstream.

## 9. Symbolic inputs and outputs

A `WorkPlan` may refer to values that do not yet exist at planning time.

Conceptually:

```text
Step 1:
filesystem.search
output -> backup_candidates

Step 2:
artifact.select
input <- $step1.backup_candidates
```

A symbolic reference identifies a future data dependency. It does not claim that the referenced value is already known or true.

```text
symbolic reference != observed value
```

M0.3 freezes the need for symbolic dataflow. M0.4 freezes exact Late Binding and Observation semantics.

## 10. Explicit continuation points

A `WorkPlan` may identify a bounded point where additional attributable information must return to IRR before semantics can safely continue.

A continuation point is not an embedded planner loop.

Conceptually:

```text
WorkPlan
   |
   v
bounded downstream work
   |
   v
Observation / Outcome
   |
   v
IRR Continuation
   |
   +--> clarification
   +--> successor ResolvedIntent
   +--> successor WorkPlan
   +--> completion
```

If an Observation exposes a new material choice, IRR MUST NOT let an existing plan silently decide that choice through hidden branching.

Exact continuation mechanics belong to M0.4 and later lifecycle milestones.

## 11. Successor plans instead of semantic self-mutation

When new information changes material work semantics, an existing `WorkPlan` MUST NOT silently rewrite itself in place.

The new information returns through IRR continuation and, when further operational work is admitted, produces a successor work representation with preserved lineage.

```text
old WorkPlan
    |
Observation / clarification
    |
IRR continuation
    |
new semantics
    |
successor WorkPlan
```

M0.3 freezes the semantic rule; exact identity, digest, persistence, and lineage fields are deferred.

This distinction is important because an inspected or authorized plan must not silently become a different plan after new information arrives.

## 12. Plan derivation and semantic fidelity

Every material `WorkStep` MUST be attributable to the operational semantics of its parent `ResolvedIntent`, an explicit admitted constraint, or a necessary bounded prerequisite for those semantics.

IRR MUST NOT add unrelated work merely because it might be useful, convenient, or customary.

Examples of invalid semantic expansion include silently adding:

- unrelated cleanup;
- telemetry upload;
- package installation;
- repository mutation;
- network disclosure;
- account login;
- destructive maintenance;

when those operations are not required by the resolved intent or an explicit admitted constraint.

A necessary prerequisite MAY be planned, but it must remain explicit and inspectable.

```text
necessary prerequisite != hidden side task
```

## 13. No effect smuggling

A plan MUST NOT hide one material effect inside a step described as another semantic operation.

For example, a step described as:

```text
artifact.inspect
```

must not semantically include:

```text
upload artifact to remote service
```

unless that disclosure is itself explicitly represented in the work semantics.

Similarly, `process.launch` must not silently imply unrelated package installation, privilege changes, or persistence mechanisms.

Material effects must remain inspectable as work semantics even though exact effect metadata belongs to M0.5 and Governance remains external.

```text
semantic convenience != permission to hide effects
```

## 14. Literal executable text remains data unless a downstream contract says otherwise

An IntentRequest or Context Item may literally contain source code, a shell command, a script, SQL, a URL, or another executable-looking string.

Its textual form does not automatically make it IRR control flow.

IRR MUST NOT execute, evaluate, interpolate, or adopt such text as hidden WorkPlan program semantics.

If future capability contracts support a bounded operation involving user-supplied executable material, that material must remain attributable input under that capability's explicit contract and downstream Governance. It MUST NOT bypass semantic planning merely because the user supplied the bytes.

```text
executable-looking text != executable authority
executable-looking text != WorkPlan control flow
```

M0.3 does not freeze such future capability contracts.

## 15. WorkPlan validity is not current executability

A `WorkPlan` may be semantically valid even when downstream execution cannot currently proceed.

Examples include:

- a capability already admitted under the applicable later catalog contract has no currently reachable executor/provider;
- Governance denies authorization;
- required scope is unavailable;
- required observation cannot be obtained;
- an otherwise applicable downstream executor is offline.

Therefore:

```text
valid plan != currently executable plan
valid plan != authorized plan
valid plan != successful effect
```

This section MUST NOT be read as permission to plan against unknown or absent capabilities.

M0.3 deliberately does not decide whether a WorkPlan may be admitted when a required semantic operation has no corresponding capability in the applicable catalog. M0.5 freezes capability admission, `missing_capability`, exact catalog binding, availability semantics, and capability drift.

M0.6 freezes the Governance boundary. M0.9 freezes downstream outcome and unknown-outcome semantics.

## 16. WorkPlan is not capability authority

Naming a semantic operation does not grant the capability to perform it.

For example:

```text
process.launch
```

inside a plan means only that the resolved operational semantics request a launch operation.

It does not mean:

```text
launcher capability is known
launcher is currently executable
scope is authorized
process was started
```

The exact relationship between planned operations and the externally supplied Capability Catalog is frozen by M0.5.

## 17. Completion semantics

A `WorkPlan` MUST preserve the intended completion meaning of the operational part of its parent `ResolvedIntent`.

Completing an individual `WorkStep` is not automatically equivalent to completing the plan, and completing all planned steps is not automatically proof that the parent intent's desired result was achieved.

```text
step completion != plan completion
plan completion != intent satisfaction by default
```

For example:

```text
archive.extract succeeded
```

is not sufficient evidence that:

```text
"restore the backup and launch the project"
```

has been satisfied.

Later lifecycle and outcome contracts may formalize completion conditions and evidence. M0.3 freezes only that these meanings must remain distinct.

## 18. Observation work versus mutating work

A WorkPlan may contain read/observation-oriented operations and effectful operations.

The presence of an observation-oriented step does not make the overall plan non-effectful, and the presence of an effectful step does not authorize it.

A planner MUST preserve material distinctions between work that seeks information and work that changes external state.

Exact effect classes and capability metadata belong to M0.5.

## 19. No hidden retries

A `WorkPlan` MUST NOT contain implicit retry semantics.

A retry is a new attempt with potentially new external consequences. It must not be assumed merely because an earlier step did not return a desired result.

M0.3 therefore freezes:

```text
failure != automatic retry
unknown result != automatic retry
```

Exact failure and unknown-outcome handling belongs to M0.9.

A downstream capability may define bounded transport-level behavior that does not create a new semantic effect attempt, but IRR MUST NOT model open-ended retries as hidden plan behavior.

## 20. No hidden fallback implementation

If an intended semantic operation cannot be supported by the downstream capability surface, IRR MUST NOT silently replace it with arbitrary shell commands, browser automation, another service, or a different implementation path whose semantics or effects differ.

The missing-capability contract itself belongs to M0.5.

M0.3 freezes only the invariant:

```text
missing implementation != permission to invent a different operation
```

## 21. Inspection before authority

A WorkPlan is intended to be inspectable before downstream authority and execution decisions.

Its semantics therefore MUST be explicit enough that an external Governance boundary can reason about requested work without treating opaque executable code as the source of truth.

This does not mean IRR decides safety or permission.

```text
inspectable != approved
```

It means IRR must not defeat downstream Governance by hiding semantics in arbitrary code or implementation-specific fragments.

## 22. Worker delegation remains separate

M0.3 freezes bounded operational WorkPlan semantics. It does not collapse long-form delegated worker tasks into ordinary tiny WorkSteps.

A future delegated-work handoff may contain an objective, scope, context, constraints, allowed capabilities, and deliverables while a Worker owns a subordinate lifecycle.

M0.8 freezes that boundary in detail.

IRR MUST NOT use a generic `worker.do_everything` step as an escape hatch from bounded work semantics.

```text
worker delegation != ordinary WorkStep execution
worker delegation != arbitrary capability fallback
```

A WorkPlan path through ordinary WorkSteps therefore MUST NOT be depicted or interpreted as automatically equivalent to delegated Worker execution.

## 23. Relationship to later M0 milestones

M0.3 intentionally leaves several details to later contracts:

- M0.4 — exact Late Binding, symbolic dataflow, Observation return, and continuation mechanics;
- M0.5 — Capability Catalog, capability identity, availability, effect metadata, scope requirements, and capability drift;
- M0.6 — Governance and authority decisions;
- M0.8 — delegated-worker handoff semantics;
- M0.9 — downstream failure, interruption, retry, and unknown-outcome semantics;
- M1 — exact immutable Python representations, validation, serialization, identity, and digests.

Later milestones may refine representation, but they MUST preserve the work boundary frozen here.

## 24. M0.3 exclusions

M0.3 intentionally does NOT freeze:

- Python classes, enums, protocols, or serialization schemas;
- exact `WorkPlan` or `WorkStep` fields;
- exact operation identifier syntax;
- exact symbolic-reference syntax;
- exact output-binding representation;
- scheduling algorithms;
- parallelism policy;
- executor selection;
- Capability Catalog schemas;
- platform adapters;
- shell/process adapters;
- effect-risk taxonomies;
- Governance policy or consent rules;
- worker-delegation schemas;
- persistence, plan IDs, digests, or lineage wire formats;
- retry or recovery algorithms;
- terminal Outcome schemas.

M0.3 freezes semantic constraints, not implementation types.

## 25. Acceptance criteria

M0.3 is complete when the repository states unambiguously that:

1. A `WorkPlan` is produced only when a `ResolvedIntent` requires operational work.
2. Clarification or pre-resolution continuation does not require a WorkPlan and does not by itself complete the parent intent lifecycle.
3. Work is represented as semantic operations rather than platform-specific implementation commands.
4. IRR core work semantics are platform-neutral without permitting effect-changing implementation substitution.
5. A `WorkPlan` is not a scripting language or general-purpose execution program.
6. A v1 `WorkPlan` is finite and bounded.
7. Ordinary WorkStep semantics are themselves inspectably bounded; a finite wrapper cannot launder an opaque autonomous loop into a bounded plan.
8. `WorkStep` dependencies express bounded ordering/data dependencies rather than arbitrary control flow.
9. The v1 dependency graph is finite and acyclic.
10. Presentation order does not silently become execution dependency.
11. Symbolic references do not pretend future values are already observed.
12. New material semantic decisions return to IRR continuation rather than hidden plan branching.
13. Material plan changes produce successor semantics rather than silent in-place self-mutation.
14. Every material WorkStep is derivable from the parent resolved intent, an admitted constraint, or a necessary explicit prerequisite.
15. Material effects cannot be hidden inside misleading step semantics or implementation substitution.
16. Executable-looking user/context text is data unless an explicit downstream contract gives it bounded meaning; it is never hidden IRR control flow.
17. Plan validity does not imply current executability, authorization, or effect, and does not permit planning against unknown capabilities.
18. Naming a semantic operation does not establish that its capability is known, currently executable, authorized, or performed.
19. Step completion, plan completion, and intent satisfaction remain distinct.
20. Observation-oriented and effectful work remain semantically distinguishable.
21. Failure or unknown result does not imply automatic retry.
22. Missing implementation does not permit arbitrary fallback operations.
23. Work semantics remain inspectable before downstream Governance.
24. Worker delegation remains distinct from ordinary WorkStep execution and is not an escape hatch from bounded operation semantics.
25. M0.4+, M0.5+, M0.6+, M0.8+, M0.9+, and M1 implementation details remain explicitly deferred.
26. No runtime code or `src/` tree is introduced.
