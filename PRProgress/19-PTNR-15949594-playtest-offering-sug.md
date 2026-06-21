# [PTNR] PR 15949594 — Set PC_PLAYTEST SUG on the playtest offering

- **Pull Request:** 15949594
- **Repo:** services.partnerregistry (Xbox.Streaming)
- **Source branch:** `t-melanichen/playtest-offering-sug` → `main`
- **Status:** Draft
- **Opened:** 2026-06-19  |  **Closed:** —
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

## Context
- The missing link between CTIN PR [17](./17-CTIN-15896502-pc-install-readiness-polling.md) (the readiness poll) and
  CTGT PR [18](./18-CTGT-15946980-pc-playtest-install-on-attach.md) (enable + quota).
- Full design + test plan: [`../FuturePlans/content-targets-pc-playtest-enablement.md`](../FuturePlans/content-targets-pc-playtest-enablement.md).

## Dependencies
- **Requires the `PC_PLAYTEST` SUG to be registered** — partner-registry validation rejects an unknown SUG
  (`ValidationProcessorUtilities.cs:421`, `SystemUpdateGroup.GetId(sug, env)` must be non-null) and OS Targets must
  provision it. Draft until Timi confirms the exact SUG string + provisioning.
- Deploy via CI/CICD, not the PR pipeline.
