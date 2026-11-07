# G7A.4 — Original HUMAN lineage to existing M32 work-disposition candidate

## Why

G7A.1–G7A.3 already demonstrate real Runplane plugin discovery and
provider-agnostic bounded WorkPlan materialization. This slice connects
the resulting *unadmitted* real IRR WorkPlan to the **existing**
`CandidateWorkDisposition` / `orchestrate_work_disposition()` M32 boundary.
It creates neither a new work-plan authority nor a terminal.

## Exact check

`prepare_dynamic_human_work_candidate()` requires exact typed:

- original `IntentRequest` with `OriginKind.HUMAN` and exact actor/principal;
- original `ContextEnvelope` matching exact request identity;
- existing admitted `ResolvedIntent` matching request and context identities;
- G7A.3 `UnadmittedBoundWorkPlan` matching exact resolved intent identity;
- fresh authenticated Host G7A.1 `CandidatePlanningSurface` whose actor and
  catalog/policy/descriptor identity match the unchanged bound WorkPlan;
- explicit Host `WorkDispositionProposalAttribution` and rationale.

Only then it mints an original IRR `CandidateWorkDisposition` holding the
unchanged real G7A.3 WorkPlan. The returned `PendingDynamicHumanWork` has
`admitted=False` and `execution_authorized=False`. Existing M32 without
admitter returns `ADMISSION_REQUIRED`, *not* an admitted WorkPlan.

## Trust and lifecycle

This module authenticates **none** of its own inputs. A malicious caller
could instantiate the same Python types. The trusted HDE Core/Host must
independently establish HUMAN presence, identity, durable M31 provenance,
scope consent, trusted model observation, policy revision, registry source
and freshness. Structural identity matches are necessary, not sufficient.

Before any actual M32 admission, call
`assert_current_dynamic_human_work_candidate()` with a newly authenticated
planning surface. The ordinary HUMAN M32 decision, binding completion,
M33 proposal and review, Governance, Authorization and Attempt all remain
separate original IRR/HDE boundaries. Nothing executes.

## Existing Kaguya Console V2

`hde-home/tools/kaguya_console_v2.py` already provides a foreground
human-owned `/work`, `/decide`, `/review` and speech, and should be reused.
**Not done by this PR:** composing old Kaguya Shell `1052c302...` with
new G7 Shell `bc85def...`. These Shell branches diverged; swapping
`-ExpectedShellCommit` or blindly importing G7 modules into old Shell
is unsafe. A subsequent test-only adapter on the existing Console V2
must authenticate its host-side sources and display the pending candidate
without auto-admission. We should test with a temporary plugin and retain
the old 3-operation path until that live integration is explicitly proven.

## CI

Seven targeted tests exercise original HUMAN identity, existing M32 pending
frontier, non-HUMAN rejection, foreign actor/context/ResolvedIntent, stale
catalog/policy and refused forged attribution. Full IRR CI matrix also
covers Ruff, mypy and pytest on Python 3.11–3.14.
