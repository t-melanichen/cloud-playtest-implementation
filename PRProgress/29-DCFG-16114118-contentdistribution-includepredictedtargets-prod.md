# [DCFG] PR 16114118 — [UPDATE] Update ConfigSection at CONTENTDISTRIBUTION/DEFAULT/ORCHESTRATIONCONFIG (Prod)

- **Pull Request:** 16114118
- **Repo:** services.data.partnerregistry (Xbox.Streaming)
- **Status:** Merged (2026-07-08)
- **Author:** Timi Bolaji
- **Link:** https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16114118

## Summary
The content-distribution half of the predicted-targets fix — makes the orchestrator **actually stage** the build for the
`PC_PLAYTEST` SUG. Updates
`/ServiceGroups/XCLOUD/Environments/PROD/DynamicConfigs/Services/CONTENTDISTRIBUTION/Namespaces/DEFAULT/ConfigSections/ORCHESTRATIONCONFIG/ConfigSection.json`:

```jsonc
"IncludePredictedTargets": {
  "DefaultValue": false,
  "Override": { "Value": true, "Sugs": [ "PC_PLAYTEST" ] }   // ServerType defaults to PC
},
"InstallsPerServer": {
  "DefaultValue": 6,
  "Override": { "Value": 20, "Skus": [ "STANDARD_NC64AS_T4_V3" ], "InstallIds": [ "*" ] }
}
```
No prior override existed on this section, so `IncludePredictedTargets` is a clean single add (no XBOX conflict, unlike
the content-targets side).

## Context
- Consumed by `services.contentdistribution` `OrchestrationProcessor.cs:62-64`:
  `if (!Config.IncludePredictedTargets.GetValue(serverSetId)) { targetsCalculationMode &= ~Predictions; }`. When false
  the orchestrator **strips** predicted targets and never installs them — which is why this must be `true` for
  `PC_PLAYTEST`.
- Pairs with the content-targets half
  [28 · PR 16114214](./28-DCFG-16114214-contenttargets-includepredictions-prod.md). **Both** required: 16114214
  *computes* the target, 16114118 *stages* it.
- After both merged, Timi confirmed *"Server is being created now"* for offering `XPT2SDT4X91KRQS`.
- Full write-up: [`../Explanations/pc-playtest-streaming-allocation-e2e.md`](../Explanations/pc-playtest-streaming-allocation-e2e.md).
