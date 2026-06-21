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
