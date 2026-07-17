# Playtest Streaming — Progress Update (2026-07-14, refreshed 2026-07-15 AM)

**From:** Melanie Chen · **Area:** Instantly Shareable Playtest → xCloud streaming (Bayside/PC)

## TL;DR

Moved forward on three build fronts and cleared two design unknowns. On **Xbet** I built the streaming **launch-link builder** and reworked it to the real path-based link format, on a clean branch (65/65 tests). In **Partner Center** the "Enable cloud streaming" toggle PR is up with all comments resolved (and I resolved a merge conflict with main's new Game-art work), plus I stood up a **fully local end-to-end demo** — toggle + Share link — that needs no ECS, no SPA submit, and no deployed backend. On **Bayside** I root-caused the blank playtest tile and confirmed — with Anthony and against the code — that we need **authenticated Hydration, not CAS, and no special token claim**, so it's a client-only change (now wired), and I got the dev server running locally. Still **blocked** in three places: the ECS flag is **formally requested from Naveen** but needs his PME/SAW to create, the single-page create UX isn't wired for submit (true e2e gated — local demo is the backup), and **PC cloud streaming still fails on the provisioning-side launch** — Nate is enabling diagnostics bugs so we can capture the logs.

## 1. Xbet — streaming launch-link builder

Built the launch-link builder that turns a published playtest into a shareable stream URL:

- New `PlaytestStreamingLink.cs` + unit tests, wired through the mappers and response contracts (core `PlaytestMappers` / `PlaytestResponse` and the `ProductConfigurationFD` `PlaytestMapper` / `PlaytestDetailsResponseModel`).
- Reworked the output to the **real path-based format** — `/stream/{productId}/{offeringId}` with a `-pc` suffix for PC (e.g. `https://play.xbox.com/stream/2SDT4X91KRPC/xpt2sdt4x91krpc-melanieplayteststreamingtest-pc`) — matching what xCloud actually builds, rather than the older `?configs=` query form.
- Pushed a clean branch off main — `t-melanichen/playtest-streaming-launch-link` — **65/65 tests passing** (commit `c5cad6df`), no PR yet.

**In progress:** reconcile the publish gate so streaming fires on the **persisted `EnableStreaming` flag AND pilot-seller** (not the seller check alone), then open a draft PR / decide whether it folds into **PR 15834601** (the payload-builder PR) with minimal additions on the existing gate.

## 2. Partner Center — "Enable cloud streaming" toggle (single-page)

- Built the cloud-streaming toggle in the single-page playtest **Basic Info** section (`PlaytestCloudStreamingField` + `PlaytestBasicInfoSection`), with unit tests and localization.
- **PR !16139860** ("[feature] Add cloud streaming toggle to single-page playtest basic info section", branch `users/t-melanichen/playtest-streaming-singlepage`) is up with **all comments resolved**. Resolved a **merge conflict** in `PlaytestBasicInfoSection.tsx` after `main` moved to `6756b3db2` (PR 16160539 "Game art section" touched the same file) — kept main's `styles.fields` wrapper + `isComplete` check and placed `<PlaytestCloudStreamingField />` after the dates field.
- Ran the Partner Center client **locally** (not just Storybook) and **verified the toggle end to end**: it's **flag-gated** (`isFeatureEnabled("EnablePlaytestCloudStreaming")`), renders **below "No end date"** (after the dates field), and can be forced on via the **dev panel (Ctrl+Shift+F)**. The always-visible streamable-until note is intentional (reviewer Brian Bowman requested always-show over only-when-checked; thread resolved).
- **Built a fully local end-to-end demo** that needs no ECS, no SPA submit aggregator, and no deployed Xbet backend: a **pilot-seller gate** surfaces the toggle, and a **demo-mode** path injects a published playtest so the **Share → streaming link** flow works offline. Reworked the demo link to the **path-based private format** built from product id + playtest name (not hardcoded) — `https://play.xbox.com/stream/2SDT4X91KRPC/xpt2sdt4x91krpc-melanieplayteststreamingtest-pc` (commit `3f8b22ae2`).

**Blocked / backup:** the single-page **create** flow (ipineiro/roramirez) isn't wired for **submit** yet, so I can't drive the true end-to-end (create → publish → link) from their page. As a demo backup I can **surface the button + link locally by seller id** (`streamingDemo.ts`, `fakePlaytestPublish`, `SharePlaytestModal`) so we can show the flow even if their page isn't done by end of internship.

## 3. ECS feature flag (`EnablePlaytestCloudStreaming`)

- Resolved that the flag can live in **XPD_CORS_IDC** (the GPM module) instead of **MIXShared** — the FD emits all GPM boolean flags to the UI automatically, so **no allowlist change** and **no MIX/SAW access to MIXShared** is needed. Naveen confirmed the approach.
- Sent Naveen the **formal create request** (ECS writes need PME/SAW, which I don't have):
  > Flag name: `EnablePlaytestCloudStreaming` · Config Type: Feature Flag · Default value: `false` · Project team: `XPD_CORS_IDC`.

**Blocked:** waiting on **Naveen** to create the flag / grant XPD_CORS_IDC access (he confirmed the approach to Ichiro, not to me), since ECS writes require **PME/SAW** access I don't have. The Partner Center toggle is already wired to this flag name, so it lights up for real the moment the flag exists; until then it's demoable via the dev-panel override / pilot-seller gate.

## 4. Bayside — playtest tile metadata (Hydration, not CAS)

The playtest tile in the new "My playtests" surface shows no game art / friendly name. Ran this down with Anthony and against the code:

- **We need Hydration, not CAS.** Hydration (`catalog.gamepass.com`) returns the tile essentials — **friendly title + box art**; CAS answers "what can I access," which is overkill for a tile and carries no display fields.
- **No special token claim needed.** Anthony tested `PCLowUserAmber0` with his **normal xtoken**, not a sample claim — so this is a **client-only change**.
- **Key correction:** the token must be minted for relying party **`http://mp.microsoft.com/`**, not the catalog URL. My initial wiring requested the token for the request URL (wrong RP); fixed to target the `mp.microsoft.com` RP.
- Wired the **user-specific catalog/Hydration path** on the client (`+CatalogServiceAdaptor`, `CatalogServiceSystem`, hydration types, `PlaytestSection`) — the authenticated path existed but was never exercised because the user-specific list was empty.

**Next:** run Bayside locally and verify the authenticated Hydration call returns title + art for my playtest product id. **Got the dev server running locally** — root-caused why it never came up (`tsx watch` looped forever because the server rewrites `build-configuration/dist/config.server.js` on boot; the real `dev-ts` target passes `--ignore '.../build-configuration/dist/**'`, which I was missing) and relaunched it with that flag on **port 1337**. (An earlier nx daemon crash during `yarn dev-ts` was fixed with `nx reset`.)

## 5. PC cloud streaming — provisioning-side launch still failing (with Nate)

Retested the PC playtest launch on the `PC_TAKEHOME`-inherited build; it **still times out on provisioning**:

```
SessionServerError : InternalCode -2146233083
WaitForCloudLaunchCompletion:158 Cloud launch did not complete within 90000 ms
```

- Cleared up with Nate that the earlier bug thread (63080510) is about **deprovisioning**; my failure is on **provisioning**.
- Gave Nate the specifics: **offering `XPT2SDT4X91KRPC`**, **SUG `PC_PLAYTEST`** (inherits `PC_TAKEHOME`), **config PR 16158748**. Offered to repoint the SUG to any bug-free build — he didn't have a known-good one to hand.
- **Plan (Nate owns, ~2026-07-15):** enable **diagnostics bugs** on the offering — Services auto-files these with the full logs on provision/deprovision failure. Once enabled, Nate pings me to **repro** so he can pull the logs and root-cause the timeout.

Detail: [`Blockers/pc-playtest-launch-timeout-grts.md`](./Blockers/pc-playtest-launch-timeout-grts.md).

## Environment / running servers (checked 2026-07-15 ~07:20 PT)

- **Bayside (Xbox.JS `play-xbox`)** — dev process **alive**: `tsx watch` PID **18652** with the `--ignore` loop-fix, holding **port 1337**. ⚠️ But it currently returns **empty replies** (immediate connection reset) on `/library` and `/en-us/library` — bound but **not serving HTTP**, so it needs a **restart** to be demo-ready. Reminder from prior runs: if it 500s with `Cannot read properties of undefined (reading 'url')`, the runtime-environment dist is stale — rebuild with `node ../../node_modules/typescript/bin/tsc -b src/server/tsconfig.json`.
- **Partner Center (`gpx-*` worktrees)** — dev server **not running** (ports 3000/3001/6006 closed). The local demo (commit `3f8b22ae2`) is ready to relaunch when needed.

## Blocked / waiting on

- **ECS flag** — request **sent** to Naveen (`EnablePlaytestCloudStreaming`, XPD_CORS_IDC, default false); waiting on him to create it (ECS writes need PME/SAW I don't have).
- **Single-page create UX** — ipineiro/roramirez to wire submit; local demo is the backup for e2e.
- **PC cloud streaming** — Nate to enable diagnostics bugs on offering `XPT2SDT4X91KRPC`, then I repro to capture provisioning logs.

## Asks / next steps

- **Xbet:** finish the publish-gate reconciliation (`persisted EnableStreaming AND pilot-seller`) and open the draft PR / fold into PR 15834601.
- **Bayside:** local-run + verify authenticated Hydration returns title + box art.
- **PC streaming:** stand by to repro on Nate's ping once diagnostics bugs are enabled.
- **ECS:** follow up with Naveen on access.

## References

- Blocker: [`Blockers/pc-playtest-launch-timeout-grts.md`](./Blockers/pc-playtest-launch-timeout-grts.md) — provisioning launch timeout; Nate diagnostics-bugs plan.
- Prior update: [`Team Update 2026-07-09.md`](./Team%20Update%202026-07-09.md).
- Xbet branch `t-melanichen/playtest-streaming-launch-link` (commit `c5cad6df`); PC toggle PR !16139860; payload builder PR 15834601; offering config PR 16158748.
