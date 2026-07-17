# [DCFG] PR 16103771 — [UPDATE] Update ConfigSection at CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION (Prod)

- **Pull Request:** 16103771
- **Repo:** services.data.partnerregistry (Xbox.Streaming)
- **Source branch:** `a987fe46-e1ab-46e4-87fd-8b4b3e2bb7b2` → `master`
- **Status:** Merged
- **Opened:** 2026-07-07  |  **Closed:** 2026-07-07
- **Merge commit:** `151d0516e53cbeedb5080b06db6a18d0b9f616b0`
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16103771

## Summary
Applies the **PC playtest server quota** to Content Targets via **dynamic config** in the **Prod** environment — the
prod counterpart of the Int quota PR [22](./22-DCFG-15966616-contenttargets-pc-playtest-quota.md). Edits
`/ServiceGroups/XCLOUD/Environments/PROD/DynamicConfigs/Services/CONTENTTARGETS/Namespaces/DEFAULT/ConfigSections/SERVERSETSCONFIGURATION/ConfigSection.json`,
adding `PC_PLAYTEST` to the existing `STANDARD_NC64AS_T4_V3` / `WESTUS2` block (alongside the live `PC_TAKEHOME`,
`PC_GA`, etc. — everything else untouched):

```json
"STANDARD_NC64AS_T4_V3": {
  "QuotasBySugByRegion": { "WESTUS2": { "PC_GA": 5, "PC_PLAYTEST": 1, ... } }
}
```

Quota `1` × `GameplaySlotsPerServer 4` ⇒ concurrency of **4** (one NC64 T4 box serves up to 4 concurrent testers).
Region `WESTUS2` matches the prod PC playtest offering region (`appsettings.en-prod.json` `RegionsByPlatform.PC =
["WestUs2"]`) and the prod `PC_MAIN` pool (which exists only in WESTUS2). WESTUS2 T4 quota sum is well under the
documented `$_Notes` max of 30.

## Context
- **Approved by Timi 2026-07-07**, then completed with **proof of presence** (required for prod config PRs).
- This is the capacity half that makes Content Targets provision a T4 for the `PC_PLAYTEST` SUG lane, so a playtest
  title actually installs and can stream. Pairs with the prod SUG-definition PR
  [26](./26-PTNR-DATA-16103484-add-pc-playtest-sug-prod.md).
- Clears the **prod** dynamic-config-quota half of
  [`../Blockers/pc-playtest-sug-registration.md`](../Blockers/pc-playtest-sug-registration.md) (previously Int-only).
- The offering must still reference `PC_PLAYTEST` + `WestUs2` + `PC_MAIN` for the quota to bind — tracked in
  [`../Blockers/pc-playtest-default-allocation-pools.md`](../Blockers/pc-playtest-default-allocation-pools.md).
