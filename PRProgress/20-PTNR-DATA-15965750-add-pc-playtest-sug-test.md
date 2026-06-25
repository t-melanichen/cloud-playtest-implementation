# [PTNR-DATA] PR 15965750 — [ADD] Add PCSystemUpdateGroup at /PCSystemUpdateGroups/PC_PLAYTEST (Test)

- **Pull Request:** 15965750
- **Repo:** services.data.partnerregistry (Xbox.Streaming)
- **Source branch:** `d3f3523a-8ae4-4ef7-85f7-b4a0a12ac1b8` → `master`
- **Status:** Merged
- **Opened:** 2026-06-22  |  **Closed:** 2026-06-22
- **Merge commit:** `530328dd29a74f1f395cca97d8240888cbe29e06`
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15965750

## Summary
Registers the `PC_PLAYTEST` PC System Update Group (SUG) **definition** in the **Test** environment — the
data-driven half of standing up the PC playtest server lane (data-driven SUG recognition). Adds
`/ServiceGroups/XCLOUD/Environments/TEST/PCSystemUpdateGroups/PC_PLAYTEST/PCSystemUpdateGroup.json`:

```json
{ "Id": "PC_PLAYTEST", "InheritsFrom": "PC_GA", "PCOSFlightingConfigs": null, "PCDevelopmentOptions": null }
```

A SUG definition assigns the OS image versions the GPU servers run; inheriting from a parent SUG pulls that
parent's known-good flighting configs, so `PCOSFlightingConfigs` / `PCDevelopmentOptions` are left `null`
(inherited rather than hand-specified). This is the platform-level SUG registration the offering and
Content Targets chain depend on — it gives `PC_PLAYTEST` a recognized, OS-image-backed definition.

> **Inherits from `PC_GA`.** Jack recommended `PC_TAKEHOME` in the original walkthrough, but the user later confirmed
> that `PC_GA` is fine for Test/Int, so no parent change was needed.

## Context
- Sibling of PR [21](./21-PTNR-DATA-15965763-add-pc-playtest-sug-int.md) (the **Int** SUG add). The `PC_PLAYTEST`
  SUG was created in **both Test and Int**; this is the **Test** member of the pair.
- Clears the **SUG-registration** half of blocker
  [`../Blockers/pc-playtest-sug-registration.md`](../Blockers/pc-playtest-sug-registration.md). Step-by-step:
  [`../FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md`](../FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md) §3.
- Pairs with the dynamic-config quota PR [22](./22-DCFG-15966616-contenttargets-pc-playtest-quota.md) (Int only) and
  the offering SUG PR [19](./19-PTNR-15949594-playtest-offering-sug.md).
- **Note:** Test has the SUG *definition* but **no quota** yet — the quota (PR 22) was applied in **Int** only, due to
  the documented Test region/capacity mismatch (offering targets WESTUS2/WestEurope; Test fleet capacity is in WESTUS3).
