# [PTNR-DATA] PR 15965763 — [ADD] Add PCSystemUpdateGroup at /PCSystemUpdateGroups/PC_PLAYTEST (Int)

- **Pull Request:** 15965763
- **Repo:** services.data.partnerregistry (Xbox.Streaming)
- **Source branch:** `6e5b6b2c-ad04-4b2e-8b16-c5dc4cd70712` → `master`
- **Status:** Merged
- **Opened:** 2026-06-22  |  **Closed:** 2026-06-22
- **Merge commit:** `9d325b5b45da730191faac1a86841515c00c28c3`
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15965763

## Summary
Registers the `PC_PLAYTEST` PC System Update Group (SUG) **definition** in the **Int** environment — the sibling
of the Test SUG add (PR [20](./20-PTNR-DATA-15965750-add-pc-playtest-sug-test.md)), so the lane is defined in both
non-prod environments. Adds
`/ServiceGroups/XCLOUD/Environments/INT/PCSystemUpdateGroups/PC_PLAYTEST/PCSystemUpdateGroup.json`:

```json
{ "Id": "PC_PLAYTEST", "InheritsFrom": "PC_GA", "PCOSFlightingConfigs": null, "PCDevelopmentOptions": null }
```

A SUG definition assigns the OS image versions the GPU servers run; inheriting from a parent SUG pulls that
parent's known-good flighting configs, so `PCOSFlightingConfigs` / `PCDevelopmentOptions` are left `null`
(inherited rather than hand-specified). This is the data-driven SUG recognition the offering and Content Targets
chain depend on. **Int is the environment that goes end-to-end ready** because it also receives the dynamic-config
quota (PR [22](./22-DCFG-15966616-contenttargets-pc-playtest-quota.md)) and matches the offering's WESTUS2 region.

> **Inherits from `PC_GA`.** Jack recommended `PC_TAKEHOME` in the original walkthrough, but the user later confirmed
> that `PC_GA` is fine for Test/Int, so no parent change was needed.

## Context
- Sibling of PR [20](./20-PTNR-DATA-15965750-add-pc-playtest-sug-test.md) (the **Test** SUG add). This is the
  **Int** member of the Test/Int pair.
- Together with PR 20, **clears the long-standing SUG-registration blocker**
  [`../Blockers/pc-playtest-sug-registration.md`](../Blockers/pc-playtest-sug-registration.md) (the
  `PC_PLAYTEST` SUG is now registered / data-driven recognized in non-prod). Setup steps:
  [`../FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md`](../FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md) §3.
- Pairs with the dynamic-config quota PR [22](./22-DCFG-15966616-contenttargets-pc-playtest-quota.md) (Int) and the
  offering SUG PR [19](./19-PTNR-15949594-playtest-offering-sug.md). With the SUG defined (here) and the quota
  applied (PR 22), the two long-standing PC-playtest platform blockers are now cleared in **Int**.
