# [PTNR] PR 15949594 — Set PC_PLAYTEST SUG on the playtest offering

- **Pull Request:** 15949594
- **Repo:** services.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/playtest-offering-sug` → `main`
- **Status:** Merged
- **Opened:** 2026-06-19  |  **Closed:** 2026-06-29
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15949594

## Summary
Names the PC playtest server lane **on the offering** so Content Targets maps the title's installs to it.
`PlaytestProcessor` now sets `OfferingV2.SelectableSystemUpdateGroups = [PC_PLAYTEST]` for PC playtest titles
(alongside the existing `TargetServerSkus = [STANDARD_NC64AS_T4_V3]`).

**Why:** Content Targets' `UpdateInstallIdsByServerSetAsync` reads `offering.GetSystemUpdateGroups()` and maps the
title's installs to `ServerSetId.CreatePC(region, sug, sku)`. Before this the offering set Regions + SKU but **no SUG**,
so the title mapped to no server set and the PC‑server install had nowhere to land.

**Files:** `src/Product/PartnerRegistryService/Processors/PlaytestProcessor.cs`,
`src/Tests/Unit/PartnerRegistryService.UnitTests/Processors/PlaytestProcessorTests.cs`. **Tests: 12/12.**

## Review updates (PR feedback)
- **Jack Heuberger** — clarified the comments so the SUG comment and the region comment each unambiguously describe their
  own member (the region comment no longer reads as if it describes the SUG). Comment-only. Commit `9359a20a`.
- **Brian Bowman** — the `PC_PLAYTEST` SUG (and the hardcoded `STANDARD_NC64AS_T4_V3` SKU) are temporary stand-ins, so
  added `// TODO (62812760)` on both consts linking to ADO Task **62812760** (assigned to **Timi**, under XC4) to remove/
  finalize them once long-term PC playtest provisioning lands — so the cleanup isn't lost.
- **Id typing** — the PC SUG/SKU values set on the offering are now strongly-typed `Id` (`static readonly Id`) instead of
  `string`, matching the Id-typed offering fields they feed (`SelectableSystemUpdateGroups` / `TargetServerSkus`) and the
  CTIN readiness-settings change. Tests 12/12. Commit `18a0226e`.
- **Timi (`SystemUpdateGroupWeights`)** — `SelectableSystemUpdateGroups` only lets a client *request* the SUG; default
  session allocation is driven by `SystemUpdateGroupWeights` (SUG→weight). Added `SystemUpdateGroupWeights = { PC_PLAYTEST: 100 }`
  so launched playtest sessions allocate to PC_PLAYTEST servers (Content Targets already unions both for install mapping;
  this fixes runtime allocation). **Why:** without the weight, the offering can advertise the SUG but launched sessions
  do not actually land on it. Tests 12/12. Commit `4f0d329a`.
- **All review threads resolved (status=fixed).** Timi's `SystemUpdateGroupWeights` comment (above, commit `4f0d329a`) is
  resolved on ADO; no active review threads remain. Tests 12/12.

## Context
- The missing link between CTIN PR [17](./17-CTIN-15896502-pc-install-readiness-polling.md) (the readiness poll) and
  CTGT PR [18](./18-CTGT-15946980-pc-playtest-install-on-attach.md) (enable + quota).
- Full design + test plan: [`../FuturePlans/content-targets-pc-playtest-enablement.md`](../FuturePlans/content-targets-pc-playtest-enablement.md).

## Dependencies
- **`PC_PLAYTEST` SUG registration — now satisfied in non-prod (2026-06-22).** Partner-registry validation rejects an
  unknown SUG (`ValidationProcessorUtilities.cs:421`, `SystemUpdateGroup.GetId(sug, env)` must be non-null) and OS Targets
  must provision it. The SUG is now **registered** via the data-repo SUG-definition adds
  [20](./20-PTNR-DATA-15965750-add-pc-playtest-sug-test.md) (Test) / [21](./21-PTNR-DATA-15965763-add-pc-playtest-sug-int.md)
  (Int), and the Content Targets quota is applied in Int via [22](./22-DCFG-15966616-contenttargets-pc-playtest-quota.md).
  PR now **Active** (out of draft); the SUG parent remains `PC_GA`, which is acceptable for Test/Int per user guidance.
- Deploy via CI/CICD, not the PR pipeline.
- **Follow-up (temporary hardcodes):** ADO Task **62812760** (assigned to Timi, under XC4) tracks replacing the
  hardcoded `PC_PLAYTEST` SUG and `STANDARD_NC64AS_T4_V3` SKU with config-driven / dynamically-resolved values.
