# G7A.3 — From dynamically discovered capability route to a real unadmitted WorkPlan

## Scope

This stage materializes a **real canonical IRR WorkPlan** from a bounded G7A.1
`CandidatePlanSketch` and explicit Host-supplied argument names and binding
material. It never emits a WorkProposal, CapabilityRequirement admission,
Governance decision, Authorization, Attempt or executable provider call.

**Source lineage:** stacked over IRR G7A.1 PR #126 exact
`c853d59e2251fa202a2704ddcfb85674a050e53d`, whose
`CandidatePlanningSurface` tracks exact Host G3 candidate identity, catalog
identity, policy revision and actor. The HDE Shell G7A.2 bridge PR #156
provides the real Runplane G1/G2 source through a separately authenticated
Host policy input, but G7A.3 stays inside pure IRR.

## Explicit material, no new plugin cases

- One HostBoundStep per **exact** sketch capability ref; same order.
- Exact `CapabilityInputContract.input_ref` to reviewed technical argument
  name and one explicit source: bounded UTF-8 literal, prior step output
  contract ref, or original context-bound external `SymbolicReference`.
- Exact `CapabilityOutputContract.output_ref` to reviewed output name.
- Exact declared scope requirement refs and an explicit reviewed scope string.
- Producer output type must equal consumer input type, producer must have
  appeared earlier, and cross-scope flows are rejected for separate review.
- The goal type must occur in the final step outputs; all intermediate
  steps must contribute to the final step dependency graph.
- Deterministic namespaced symbolic output refs, canonical WorkPlan identity
  and WorkPlan's original DAG/dataflow invariants are reused unchanged.

These technical field names are **Host review data**, not strings parsed
from opaque capability identifiers or untrusted plugin descriptions.
Adding a capability changes the exact catalog + Host mappings, never the
algorithm. No automatic interpretation of an unknown tool's description.

## Evidence and limits

`UnadmittedBoundWorkPlan` contains the real `WorkPlan`, source sketch,
candidate/catalog identities, policy revision, actor, and descriptor
identities, with `admitted=False` and `execution_authorized=False`.
`assert_current_unadmitted_work_plan` rejects changed snapshot, actor,
policy or descriptor identities. A caller must check this **again** against
fresh, authenticated Host evidence before proposing any admission.

The record types are **not Host credentials**. IRR cannot prove the Host
actually reviewed a scope or that a ResolvedIntent came from a HUMAN
simply because a caller supplied a `RecordIdentity`. Literal inputs are
syntactically bounded strings, **not** verified file paths, downloaded
resources, valid plugin arguments or execution authority. The actual
Runplane JSON-schema argument and result constraints, material binding,
scope feasibility, original-human attribution and all Governance +
Authorization + Attempt gates remain mandatory downstream.

## Tests

`tests/test_g7a3_bound_work_plan.py` covers a two-step real WorkPlan with
internal symbolic dataflow, dynamically added third-party operation,
catalog/policy freshness, exact field mapping, required scopes, earlier
producer discipline, external symbolic references and absence of authority.

Existing IRR CI runs the entire pytest suite across Python 3.11–3.14 and
Ruff format/lint and mypy. A successful CI certifies this pure IRR
contract only. HDE Shell G7A.2 → G7A.3 integrated real-G2 review will
require a separately pinned targeted follow-up; it is **not** proven here.

## Next boundary

G7A.4: a trusted original-HUMAN/ResolvedIntent grounded planner proposer
must pass the exact WorkPlan through existing requirement proposal + M33
catalog admission and match evaluation, then Governance. This is **not**
a license to invent fresh authority or dispatch. G7B will separately
implement governed durable dispatch with provider isolation.
