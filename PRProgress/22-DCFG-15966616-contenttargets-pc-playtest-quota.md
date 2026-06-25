# [DCFG] PR 15966616 — [UPDATE] Update ConfigSection at CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION (Int)

- **Pull Request:** 15966616
- **Repo:** services.data.partnerregistry (Xbox.Streaming)
- **Source branch:** `501ac519-d2a9-4f24-b506-f7910e8771a5` → `master`
- **Status:** Merged
- **Opened:** 2026-06-22  |  **Closed:** 2026-06-22
- **Merge commit:** `0015d7374ba7008c5ad808b66844e90467b79ff3`
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15966616

## Summary
Applies the **PC playtest server quota** to Content Targets via **dynamic config** in the **Int** environment — the
approach Timi asked for instead of checking the values into `appsettings`. Edits
`/ServiceGroups/XCLOUD/Environments/INT/DynamicConfigs/Services/CONTENTTARGETS/Namespaces/DEFAULT/ConfigSections/SERVERSETSCONFIGURATION/ConfigSection.json`,
**adding a new `STANDARD_NC64AS_T4_V3` SKU block** with the `PC_PLAYTEST` quota (the existing live `STANDARD_NC8AS_T4_V3`
`GA` block and `STANDARD_D4S_V3` `PC_INTEGRATION_TESTING` block are left untouched):

```json
"STANDARD_NC64AS_T4_V3": {
  "GameplaySlotsPerServer": 4,
  "DefaultMaxLocalSpaceInMB": 2000000,
  "QuotasBySugByRegion": { "WESTUS2": { "PC_PLAYTEST": 1 } }
}
```

This is **Option A** from the setup doc (keep the code's NC64 SKU and add NC64 capacity), **not** Option B (ride the
existing NC8 fleet). Quota `1` × `GameplaySlotsPerServer 4` ⇒ concurrency of **4** — one NC64 box can serve up to 4
concurrent testers. Region `WESTUS2` matches the offering's non-prod regions, so **Int** is where the lane goes ready
first.

**Supersedes the checked-in appsettings approach.** This dynamic-config edit is the realized version of the quota that
CTGT PR [18](./18-CTGT-15946980-pc-playtest-install-on-attach.md) originally tried to check into
`appsettings.ContentTargets.Int.json` (reverted per Timi's feedback). PR 18 is now **abandoned**; its 3 regression
tests remain its only value.

## Context
- Clears the **dynamic-config quota** blocker:
  [`../Blockers/pc-playtest-sug-registration.md`](../Blockers/pc-playtest-sug-registration.md) (question 4) — done in **Int**.
- Exact values + the Option A / Option B analysis and the concurrency math:
  [`../FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md`](../FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md) §2.
- Pairs with the SUG-definition adds [20](./20-PTNR-DATA-15965750-add-pc-playtest-sug-test.md) (Test) /
  [21](./21-PTNR-DATA-15965763-add-pc-playtest-sug-int.md) (Int) and the offering SUG PR
  [19](./19-PTNR-15949594-playtest-offering-sug.md). The CTIN readiness poll PR
  [17](./17-CTIN-15896502-pc-install-readiness-polling.md) is pinned to the same `PC_PLAYTEST` / `WESTUS2` /
  `STANDARD_NC64AS_T4_V3`.
- **Int only.** Only the Int ConfigSection was edited. Test was intentionally left out: the setup doc documents a Test
  region/capacity mismatch (offering targets WESTUS2/WestEurope, but the Test fleet has capacity in WESTUS3), so the
  Test quota stays deferred until Timi aligns region/capacity.
