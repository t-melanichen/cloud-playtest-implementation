# [PTNR-DATA] PR 16103484 — [ADD] Add PCSystemUpdateGroup at /PCSystemUpdateGroups/PC_PLAYTEST (Prod)

- **Pull Request:** 16103484
- **Repo:** services.data.partnerregistry (Xbox.Streaming)
- **Source branch:** `c9cb5b9d-28a4-4be4-b6e1-cdff6839ce28` → `master`
- **Status:** Merged
- **Opened:** 2026-07-07  |  **Closed:** 2026-07-07
- **Merge commit:** `7d1a7cd7c2b38a595f8bcdf51b422f9ce45b75a9`
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16103484

## Summary
Registers the `PC_PLAYTEST` PC System Update Group (SUG) **definition** in the **Prod** environment — the prod member
of the SUG-registration set (Test [20](./20-PTNR-DATA-15965750-add-pc-playtest-sug-test.md) / Int
[21](./21-PTNR-DATA-15965763-add-pc-playtest-sug-int.md) landed earlier). Adds
`/ServiceGroups/XCLOUD/Environments/PROD/PCSystemUpdateGroups/PC_PLAYTEST/PCSystemUpdateGroup.json`:

```json
{
  "Id": "PC_PLAYTEST",
  "InheritsFrom": "PC_TAKEHOME",
  "PCOSFlightingConfigs": null,
  "PCDevelopmentOptions": { "DeveloperSettings": null, "TipSessionId": null, "UseBackgroundInstall": false }
}
```

A SUG definition assigns the OS image versions the GPU servers run; inheriting from a parent SUG pulls that parent's
known-good flighting configs. **Prod inherits `PC_TAKEHOME`** — Jack recommended `PC_TAKEHOME` as the most solid
release SUG, and unlike Test/Int (which have no `PC_TAKEHOME` and so inherit `PC_GA`), prod has it. `UseBackgroundInstall`
is set `false` so playtest installs are foreground/on-demand.

## Context
- **Approved by Timi 2026-07-07**, then completed with **proof of presence** (required for prod config PRs).
- Clears the **prod** half of the SUG-registration blocker
  [`../Blockers/pc-playtest-sug-registration.md`](../Blockers/pc-playtest-sug-registration.md) — Test/Int were done via
  15965750 / 15965763; this is the **Prod** member.
- Pairs with the **prod** Content Targets quota PR [27](./27-DCFG-16103771-contenttargets-pc-playtest-quota-prod.md)
  (`PC_PLAYTEST=1 @ STANDARD_NC64AS_T4_V3 / WESTUS2`), merged the same day.
- Prerequisite for the prod playtest offering to reference `SelectableSystemUpdateGroups=[PC_PLAYTEST]` — see the
  allocation-pool blocker [`../Blockers/pc-playtest-default-allocation-pools.md`](../Blockers/pc-playtest-default-allocation-pools.md).
