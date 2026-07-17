# PC playtest streaming — end-to-end server allocation & staging chain

**Status:** ⚠️ **Allocation + staging work; streaming is blocked at build install (2026-07-09).** After the offering config + quota + SUG landed, the **`ContentOffline` / `NOMATCHINGSERVER`** blocker (no server had the build staged) was cleared by enabling **predicted targets** for PC, fixed by Timi via two dynamic-config PRs
([16114214](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16114214) +
[16114118](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16114118)),
so a server now allocates and stages for offering **`XPT2SDT4X91KRQS`**. **The remaining blocker (2026-07-09): the PC server's MSIXVC install fails with `ERROR_NOT_FOUND` (-2147023728)** — see
[`../Blockers/pc-playtest-msixvc-install-error-not-found.md`](../Blockers/pc-playtest-msixvc-install-error-not-found.md). Server team (Nate's) is engaged; leading theory is a `servicingContentId` vs `contentId` mismatch on the playtest MSIXVC.

**Owners:** Melanie Chen (offering/PTNR code + data) · Timi Bolaji (content-targets / content-distribution dynamic config,
GPU capacity).

---

## TL;DR

For a PC playtest to actually stream, **six** config layers must all agree on the same
`PC / PC_PLAYTEST / STANDARD_NC64AS_T4_V3 / WESTUS2 / PC_MAIN` tuple. Getting the offering right (pool + SUG + region)
is necessary but **not sufficient** — a server also has to **pre-stage the build**, and that only happens if
**predicted targets** are enabled for the `PC_PLAYTEST` SUG in *both* content-targets and content-distribution.

A brand-new playtest has **zero live players**, so there is no observed demand to trigger an install. The only thing
that puts the build on a warm server is a **prediction** ("keep 1 server warm for this SUG"). Two switches gate that,
both defaulted to exclude PC — so nothing installed → allocator found no server → `ContentOffline`.

---

## The full chain (all six layers)

| # | Layer | What it does | Value for this playtest | Where it lives |
|---|-------|--------------|-------------------------|----------------|
| 1 | **Title** `…-MELANIEPLAYTESTTEST2-PC` | Which server SKU the title runs on | `TargetServerSkus = [STANDARD_NC64AS_T4_V3]`, `XboxTitleId 2088843345` | `services.data.partnerregistry` Title.json |
| 2 | **Offering** `XPT2SDT4X91KRQS` | Which fleet + lane + region | `DefaultAllocationPools = {PC: PC_MAIN}`, `SelectableSystemUpdateGroups = [PC_PLAYTEST]`, `SystemUpdateGroupWeights = {PC_PLAYTEST: 100}`, `Regions = [WestUs2]` | `services.data.partnerregistry` OfferingV2.json |
| 3 | **Quota** | Keep N servers of the SKU warm for the lane | `STANDARD_NC64AS_T4_V3 / WESTUS2 / PC_PLAYTEST = 1` | dynamic config `CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION` |
| 4 | **Predictions — computed** | Whether content-targets **calculates** a "keep warm" target for the server set | `IncludePredictions` → **true** for PC_PLAYTEST | dynamic config `CONTENTTARGETS/DEFAULT/RESOLUTIONCONFIGURATION` |
| 5 | **Predictions — staged** | Whether content-distribution **acts** on that target and installs the build | `IncludePredictedTargets` → **true** for PC_PLAYTEST | dynamic config `CONTENTDISTRIBUTION/DEFAULT/ORCHESTRATIONCONFIG` |
| 6 | **Pool** | The physical fleet exists in the region | `PC_MAIN` exists in `WESTUS2` (prod PC pool is WESTUS2-only) | `services.data.partnerregistry` PoolConfigs |

Layers 1–3 make the offering *addressable*; **layers 4–5 are what actually put the build on a server.** Miss either of
4/5 and you get `ContentOffline` even though everything else looks correct.

---

## Why predicted targets are the missing piece

content-targets resolves what to install in two independent stages, and **both** excluded PC by default:

**Stage 1 — content-targets decides *what* to install** (`ResolutionProcessor.cs:69-70`):
```csharp
if (query.CalculationMode.HasFlag(TargetsCalculationMode.Predictions)
    && this.Config.IncludePredictions.GetValue(serverSetMetadata.Id))   // ← was false for PC
{
    ... QueryPredictionsAsync(...);   // adds the "keep 1 warm" target
}
```

**Stage 2 — content-distribution actually *stages* it** (`OrchestrationProcessor.cs:62-64`):
```csharp
if (!this.Config.IncludePredictedTargets.GetValue(serverSetId))   // ← was false for PC
{
    targetsCalculationMode &= ~TargetsCalculationMode.Predictions;   // strips predictions → nothing installs
}
```

Both flags are `ConfigItem<bool>` — a `DefaultValue` plus a single `Override` matched by **ServerSetId**
(ServerType + Regions + Sugs + Skus). Prod had `IncludePredictions` overridden **true for XBOX only**, default false,
so PC_PLAYTEST resolved to false. content-distribution's flag was false everywhere. Net: no predicted target was ever
computed *or* staged for PC_PLAYTEST → `NOMATCHINGSERVER`.

### "What does IncludePredictedTargets mean?" (Timi's question)
It's the content-distribution switch that lets the orchestrator act on **forecast** targets — pre-install / keep the
build warm on a server **before** any session exists. Off = only install where there's already observed demand, which
never happens for a fresh playtest with no players.

---

## How Timi fixed it — the inverted deny-list

The catch: `ConfigItem.Override` holds **one** override object, not a list — and in prod XBOX was already using it. You
can't express "true for XBOX **and** true for PC_PLAYTEST" with a single override. So instead of an **allow-list**, Timi
**inverted** the logic to a **deny-list**:

`CONTENTTARGETS/DEFAULT/RESOLUTIONCONFIGURATION` (new, PR 16114214):
```jsonc
"IncludePredictions": {
  "DefaultValue": true,          // predictions ON for everyone (XBOX ✓, PC_PLAYTEST ✓)
  "Override": {
    "Value": false,              // ...except this list of internal PC test SUGs
    "ServerType": "PC",
    "Sugs": [ "PC_GA", "PC_TAKEHOME", "PC_BUGBASH", "PC_TESTX", "PC_GAUNTLET",
              "PC_QUALITY_TESTING", "PC_ENCODING_TESTING", "SYNTHETIC_TESTS", ... ]
              // ← PC_PLAYTEST is deliberately NOT in this list, so it stays true
  }
}
```
- **XBOX** → `DefaultValue` true (override is `ServerType: PC`, doesn't match) → predictions on ✓
- **PC_PLAYTEST** → override matches `ServerType: PC` but its Sugs list doesn't contain `PC_PLAYTEST` → falls through to
  `DefaultValue` true → predictions **on** ✓
- **Internal PC test SUGs** (PC_GA, PC_TAKEHOME, …) → override matches → false → predictions off (preserves Timi's
  earlier [PR 14317689](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/14317689)
  intent: those SUGs can sit at quota 0 without wasting servers)

`CONTENTDISTRIBUTION/DEFAULT/ORCHESTRATIONCONFIG` (updated, PR 16114118) — no XBOX override existed here, so it's a
clean single add:
```jsonc
"IncludePredictedTargets": {
  "DefaultValue": false,
  "Override": { "Value": true, "Sugs": [ "PC_PLAYTEST" ] }   // ServerType defaults to PC
}
```
(Also bumped `InstallsPerServer` to 20 for `STANDARD_NC64AS_T4_V3`.)

This inversion is the whole reason the config "looks backwards" (`DefaultValue: true` + an override that sets `false`):
it's the only way to enable both XBOX and PC_PLAYTEST through a single override.

---

## Automated vs one-time — what future playtests need

**Server staging (predictions + quota): already automatic — nothing to add per playtest.** Layers 3–5 are **env-level
dynamic config keyed by the `PC_PLAYTEST` SUG**. Every PC playtest uses that same SUG, so all current and future
playtests inherit them for free. (They also *share* the one warm server — a capacity note, not a config-per-playtest
thing.) These are not `OfferingV2` fields, so **PTNR cannot and need not set them.**

**Offering config: the PTNR code fix is now merged; only the prod deploy remains.** Deployed `origin/main`
`PlaytestProcessor` PC branch previously set SUG + weights + Title SKU but **not** `DefaultAllocationPools`:
```csharp
// PlaytestProcessor.cs PC branch — after PR 16112987 (merge commit 7ecede80):
title.TargetServerSkus = [settings.PCServerSku];                 // ✓
offering.SelectableSystemUpdateGroups = [settings.PCSystemUpdateGroup];        // ✓
offering.SystemUpdateGroupWeights = { settings.PCSystemUpdateGroup: 100 };     // ✓
offering.DefaultAllocationPools = { ServerPlatform.PC: settings.PCAllocationPool };   // ✓ NOW ADDED
```
[PR 16112987](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/16112987) merged
`t-melanichen/playtest-default-allocation-pool` @ `f1435222` to `main` (config-driven `PlaytestSettings.PCAllocationPool
= "PC_MAIN"`). **Until `main` is deployed to prod** (merged ≠ deployed — this must roll out past the Ring gates,
alongside the SUG/region code from
[PR 15949594](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15949594)), a
newly auto-created prod playtest still comes from the older service and needs hand-patching.

**After `main` deploys to prod, future PC playtests configure themselves with zero manual patching.**

---

## Timing & how to verify

- **Config reload:** minutes (dynamic config refresh).
- **Orchestration cycle:** content-distribution runs ~every 5 min (`RunImmediately: true`) → places the install on a T4
  server in WESTUS2.
- **Build staging:** the server then downloads/installs the package (variable — ~15 min to ~1 hr by size).
- **Realistic ETA:** ~15 min to a couple hours before a server is warm and streamable.

**Verify via:**
- **contenttargets savant** — should now show a target for the `PC_PLAYTEST / STANDARD_NC64AS_T4_V3 / WESTUS2` server
  set (was "no targets").
- **pcorchestrator savant** — should show the install being placed / staged.
- **Grafana (CTDR server-set overview):**
  [dashboard](https://xcloud-grafana-fubmepfxgvfzehb7.scus.grafana.azure.com/d/dfo56x1iznaiod/ctdr-server-set-overview?orgId=1&var-Sku=STANDARD_NC64AS_T4_V3&var-ServerRegion=WESTUS2&var-SystemUpdateGroup=PC_PLAYTEST)
  filtered to `STANDARD_NC64AS_T4_V3 / WESTUS2 / PC_PLAYTEST` — watch the server come up.

Once a server shows the build staged, `ContentOffline` / `NOMATCHINGSERVER` clears and the title streams.

---

## References
- **Prediction PRs (merged 2026-07-08):**
  [16114214](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16114214)
  (RESOLUTIONCONFIGURATION / `IncludePredictions`),
  [16114118](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16114118)
  (ORCHESTRATIONCONFIG / `IncludePredictedTargets`). Tracked in
  [`../PRProgress/28-DCFG-16114214-contenttargets-includepredictions-prod.md`](../PRProgress/28-DCFG-16114214-contenttargets-includepredictions-prod.md)
  and [`../PRProgress/29-DCFG-16114118-contentdistribution-includepredictedtargets-prod.md`](../PRProgress/29-DCFG-16114118-contentdistribution-includepredictedtargets-prod.md).
- **Code:** `services.contenttargets` `Processors/Implementations/ResolutionProcessor.cs:69-70`,
  `Configuration/ConfigItem.cs` (single `Override`, `GetValue(serverSetId)`);
  `services.contentdistribution` `Processors/Implementations/OrchestrationProcessor.cs:62-64`,
  `Configuration/OrchestrationConfig.cs`.
- **The PR Timi remembered:** abandoned
  [15946980](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/15946980)
  (Melanie's `t-melanichen/pc-playtest-install-on-attach`) — its appsettings `IncludePredictions` change was reverted in
  favor of dynamic config (commit `04ac32c`) and the enable was never re-applied until PR 16114214.
- **Why PC was excluded originally:**
  [PR 14317689](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/14317689)
  "Skip using PredictedTargets for configured server sets (currently PC)".
- Related docs: [`../Blockers/pc-playtest-default-allocation-pools.md`](../Blockers/pc-playtest-default-allocation-pools.md),
  [`../FuturePlans/content-targets-pc-playtest-enablement.md`](../FuturePlans/content-targets-pc-playtest-enablement.md),
  [`../Blockers/pc-playtest-sug-registration.md`](../Blockers/pc-playtest-sug-registration.md).
