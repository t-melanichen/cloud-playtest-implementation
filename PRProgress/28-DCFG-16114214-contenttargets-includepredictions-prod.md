# [DCFG] PR 16114214 — [ADD] Add ConfigSection at CONTENTTARGETS/DEFAULT/RESOLUTIONCONFIGURATION (Prod)

- **Pull Request:** 16114214
- **Repo:** services.data.partnerregistry (Xbox.Streaming)
- **Status:** Merged (2026-07-08)
- **Author:** Timi Bolaji (*"I'll do the config changes for you"*)
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16114214

## Summary
**Enables predicted targets (install-on-attach) for the `PC_PLAYTEST` SUG** in Content Targets — the fix for the
`ContentOffline` / `NOMATCHINGSERVER` streaming failure. Adds a **new** dynamic ConfigSection
`/ServiceGroups/XCLOUD/Environments/PROD/DynamicConfigs/Services/CONTENTTARGETS/Namespaces/DEFAULT/ConfigSections/RESOLUTIONCONFIGURATION/ConfigSection.json`:

```jsonc
"IncludePredictions": {
  "DefaultValue": true,          // predictions ON by default (XBOX ✓, PC_PLAYTEST ✓)
  "Override": {
    "Value": false,              // ...OFF only for this list of internal PC test SUGs
    "ServerType": "PC",
    "Sugs": [ "PC_GA", "PC_TAKEHOME", "PC_BUGBASH", "PC_TESTX", "PC_GAUNTLET",
              "PC_QUALITY_TESTING", "PC_ENCODING_TESTING", "SYNTHETIC_TESTS", ... ]
              // PC_PLAYTEST intentionally excluded from the deny-list → stays true
  }
}
```

## Why the inverted (deny-list) shape
`ConfigItem.Override` holds **one** override object, not a list, and prod already used it for `ServerType: XBOX`. You
can't express "true for XBOX **and** PC_PLAYTEST" with a single allow-list override. So the logic was inverted:
`DefaultValue: true` turns predictions on for everyone, and one PC override turns them **off** for the internal PC test
SUGs — with `PC_PLAYTEST` deliberately **not** in that list, so it falls through to `true`. This preserves XBOX
predictions and Timi's earlier intent
([PR 14317689](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/14317689)) that
internal PC SUGs can sit at quota 0.

## Context
- Consumed by `services.contenttargets` `ResolutionProcessor.cs:69-70`:
  `if (HasFlag(Predictions) && Config.IncludePredictions.GetValue(serverSetId)) { QueryPredictionsAsync(...) }`.
- Pairs with the content-distribution half
  [29 · PR 16114118](./29-DCFG-16114118-contentdistribution-includepredictedtargets-prod.md) — **both** are required
  (compute + stage).
- Re-applies what the abandoned PR
  [15946980](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/15946980) had put
  in appsettings and then reverted to dynamic config (but never re-added) — this is that missing enable.
- Full write-up: [`../Explanations/pc-playtest-streaming-allocation-e2e.md`](../Explanations/pc-playtest-streaming-allocation-e2e.md).
