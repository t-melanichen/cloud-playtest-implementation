# Future plan: ECS feature-flag gating

**Why it matters:** During private preview we want streaming-enabled publish enabled only for a controlled set of sellers so any hiccups don't affect existing playtest customers. Playtest itself is already enabled on a limited basis by seller today, so this follows an established pattern.

## Current understanding (Sync 3 — Anthony, David K)
- Use the **ECS** config system (portal: `ecs.skype.com`) to gate the feature by **seller ID** (Brian: seller id is probably sufficient; product id optional).
- A deployment is required to change/update ECS values.
- David K is creating ECS configs for playtest and noted **two** configurations: one that shows the left-nav element (made available broadly), and a fallback "welcome to playtest / join the preview" intro page when the second config isn't present.
- ECS requires the right permissions and approval — David K said it took weeks to get approved; he offered to sync offline / create the config since editing the ECS file is gated.

## Options
- Reuse/duplicate an existing playtest ECS template that allows specifying seller IDs (and optionally product IDs).
- Gate the new ingestion endpoint/workflow so it only runs for allow-listed sellers; for early testing, hardcode Melanie's own seller id, then move to ECS.

## Open questions
- Who is the approving audience for the new ECS config?
- Seller-only vs seller+product granularity for v1.
- Is ECS reachable from the workflow yet, or only the front-end today?

## Owners
Melanie Chen · David Kushmerick (ECS setup/permissions) · Anthony Keller.

## External step (ECS portal) — the fast-follow

Lighting up the Partner Center "Enable Cloud Streaming" toggle for the pilot needs an **ECS config entry**, and — depending on which ECS module hosts the flag — possibly a one-line code edit.

**How emission actually works** (`ProductConfigurationFD.IndexBusinessLogic.GetFeatureFlagsForInlineScriptAsync`, lines ~405-425): it serializes **every** boolean flag from the **Gpm** module into `window.gpmFeatureFlags`, but only **allowlisted** flags from the **Packages** module — `allowedPackageFeatures = { "NewGamingPackageUXEnabled", "XboxPlaytest" }`. The existing `XboxPlaytest` flag lives in the **Packages** module (ECS project `MIXShared`, client `MarketplaceIngestion`, targeted by `SellerID`). The `Gpm` module maps to ECS project `XPD_CORS_IDC`, client `XboxDeveloper`, targeted by `PublisherID`.

Two ways to make `XboxPlaytestCloudStreaming` reach the UI:

- **Path A — Packages module (recommended, mirrors `XboxPlaytest`):** create a boolean `XboxPlaytestCloudStreaming` in ECS project `MIXShared`, targeted to `SellerID == 65050620`, **and** add `"XboxPlaytestCloudStreaming"` to `allowedPackageFeatures` in `IndexBusinessLogic.cs` (+ update `IndexBusinessLogicTests`). Requires an FD deploy. Keeps both playtest flags in one ECS project.
- **Path B — Gpm module (no code):** create the boolean in ECS project `XPD_CORS_IDC`, targeted to `PublisherID == 65050620`. Gpm bools emit generically, so no allowlist edit — but it splits the two playtest flags across different ECS projects and uses `PublisherID` targeting.

The client field `PlaytestCloudStreamingField.tsx` reads `isFeatureEnabled("XboxPlaytestCloudStreaming")` and defaults to `false`, so the toggle stays hidden until ECS returns it for the pilot seller. ECS is **fail-closed**. Results are cached (`EcsEnablementCacheConfiguration.TierTwoTtl = 30 min`), so allow up to ~30 min after enabling (plus a deploy if David K confirms one is required).

Until the ECS entry exists, the toggle is hidden in the UI. The backend still works when the persisted
`EnableStreaming` flag is set another way (see the reconciliation note below), which is why prod-piloting by
seller id is viable before ECS lands.

## Reconciliation note — `EnableStreaming` is now one source of truth (2026-07-08, DONE)

Previously the publish path re-derived streaming from the seller check and ignored the persisted flag. **Fixed**
on branch `t-melanichen/playtest-streaming-launch-link` (commit `4036d92`): the publish path now reads
`publishedPlaytestEntity.EnableStreaming` (set by the UI toggle through the create/update contracts), gated to
the pilot seller as defense-in-depth:

```
bool enableStreaming = publishedPlaytestEntity.EnableStreaming && IsStreamingPilotSeller(publishedPlaytestEntity.SellerId);
```

So: **toggle on + pilot seller ⇒ streaming ingestion + XORc title resolution + launch link all fire**;
toggle off ⇒ nothing; non-pilot ⇒ blocked regardless. Link and ingestion now agree on one flag. Closes
AB#62878234. (`PlaytestBusinessLogic.cs` publish gate + `IsStreamingPilotSeller`; 562 unit tests green incl. a
new pilot-seller-with-toggle-off case.)



## Implementation plan (2026-06-20) — no code yet

**Goal:** replace the hardcoded seller gate with an updatable seller allow-list (P0-5). Key insight:
**decouple the gate from its source** so the deliverable can ship on plain config now, with ECS swapped
in as the source later (David K's ECS approval is a weeks-long long pole — don't block on it).

**Code seam (today):**
- `Xbox.Xbet.Service` → `src/.../Workflows/Playtest/XPackagePlaytestPublishWorkflow.cs:97`
  `private const string StreamingIngestionPilotSellerId = "65050620"` (already TODO `AB#62684638`).
- Gate at ~line 483: `enableInstantPlaytest = string.Equals(playtestResponse.SellerId, StreamingIngestionPilotSellerId)`.
- The workflow already binds typed config via `IOptionsMonitor<XPackageWorkflowConfiguration>` →
  `.XPackagePlaytestPublishWorkflowConfiguration` (ctor line ~131; reads at 147-159). `IOptionsMonitor`
  ⇒ values can hot-reload. **This is where the allow-list goes.**

**Phases:**
0. **Decisions/unblock (parallel):** seller-only for v1 (Brian: sufficient); start ECS access with David K
   now; confirm whether ECS reaches this *service's* config today or only the front-end.
1. **Model as service config (no ECS):** add `StreamingIngestionEnabledSellerIds` (list) + a
   `StreamingIngestionEnabled` master switch to `XPackagePlaytestPublishWorkflowConfiguration`; also
   externalize the poll interval / max-wait (TODOs at lines 107-108). Default to the current pilot seller
   so behavior is unchanged.
2. **Replace the gate:** swap the `==` check for "master switch on AND `SellerId` ∈ allow-list," behind a
   small helper. **Fail-safe:** empty/missing config ⇒ feature OFF (never enable for everyone).
3. **Source the config (with or without ECS):**
   - *Without ECS (ship now):* populate the list from `appsettings`/env/keyvault — full deliverable today,
     adding a seller = config change, not code.
   - *With ECS (later):* point that same config section at ECS so `IOptionsMonitor` picks up ECS values;
     **gate code is unchanged — only the source changes.** Reuse David K's existing playtest ECS template.
4. **Tests & rollout:** unit-test fires/skips on in-list / not-in-list / flag-off / empty, and config flip
   (also closes trigger-test task `62521504`); roll out starting with just the pilot seller → INT/PROD →
   add sellers via config/ECS.
5. **Cleanup:** remove the constant + TODO; mark `62684638` done; update this doc.

**Risks/open Qs:** ECS approval lead time; whether ECS refresh is dynamic here or needs a redeploy (David K
flagged a deploy may be required); seller-only vs seller+product; who approves the ECS audience.
