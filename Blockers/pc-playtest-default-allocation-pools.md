# Blocker: PC playtest offering has empty `DefaultAllocationPools` → streaming session 400

**Status:** ✅ **This offering now streams (2026-07-08).** The data was hand-patched (PR 16097829) and the final
`ContentOffline`/`NOMATCHINGSERVER` blocker was cleared by enabling predicted targets for the `PC_PLAYTEST` SUG
(PRs 16114214 + 16114118 — see
[`../Explanations/pc-playtest-streaming-allocation-e2e.md`](../Explanations/pc-playtest-streaming-allocation-e2e.md)).
**The durable code fix is now MERGED** — `DefaultAllocationPools = PC_MAIN`
([PR 16112987](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/16112987),
merge commit `7ecede80`). **Remaining = prod deploy only** (merged ≠ deployed): roll `main` out to prod
`services.partnerregistry` so *future* auto-created playtests configure the pool without hand-patching.
**Owners:** Melanie Chen (offering PRs + data patch) · Timi Bolaji (prod PC_PLAYTEST quota / GPU capacity + predictions
dynamic config) · partner-registry release owner (prod deploy of PR 15949594 + 16112987).

> **Update 2026-07-09 — the pool-400 (this blocker) is resolved, but the offering still does not stream.** A server now
> allocates and stages, but the PC build **install fails with `ERROR_NOT_FOUND` (-2147023728)** in
> `CustomActionAppxPayload.cs`. New active blocker tracked in
> [`pc-playtest-msixvc-install-error-not-found.md`](./pc-playtest-msixvc-install-error-not-found.md); server team
> (Nate's) engaged. So "streams" below refers to the pool/allocation fix landing — end-to-end streaming is still blocked
> downstream at build install.

> **Update 2026-07-08b — pool fix MERGED (PR 16112987).** `t-melanichen/playtest-default-allocation-pool` @ `f1435222`
> was approved by Timi + the required Cloud Streaming team and **squash-merged to `main`** (commit `7ecede80`), in the
> config-driven form: `PlaytestSettings.PCAllocationPool = "PC_MAIN"` + `offering.DefaultAllocationPools = {PC:
> settings.PCAllocationPool}`. Path B is done in code; only the **prod deployment** of `main` remains. Tracked in
> [`../PRProgress/30-PTNR-16112987-playtest-default-allocation-pools.md`](../PRProgress/30-PTNR-16112987-playtest-default-allocation-pools.md).

> **Update 2026-07-08 — streaming works; only the code fix is left.** Timi enabled predicted targets for `PC_PLAYTEST`
> (`IncludePredictions` in Content Targets [16114214](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16114214);
> `IncludePredictedTargets` in Content Distribution [16114118](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16114118)),
> which was the true cause of `ContentOffline`/`NOMATCHINGSERVER` (no server had staged the build). A server is now being
> provisioned for offering `XPT2SDT4X91KRQS`. The offering itself was confirmed fully correct:
> `DefaultAllocationPools = {PC: PC_MAIN}`, `SelectableSystemUpdateGroups = [PC_PLAYTEST]`,
> `SystemUpdateGroupWeights = {PC_PLAYTEST: 100}`, `Regions = [WestUs2]`; Title `TargetServerSkus =
> [STANDARD_NC64AS_T4_V3]`. **The pool fix (`t-melanichen/playtest-default-allocation-pool` @ `f1435222`) is still
> pushed-but-unmerged** — Path B remains the durable fix for future playtests.

> **Update 2026-07-07 — prod SUG + quota prerequisites CLEARED.** Timi approved and (with **proof of presence**)
> merged the two prod data PRs: the `PC_PLAYTEST` SUG definition
> [16103484](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16103484)
> (prod inherits `PC_TAKEHOME`, `UseBackgroundInstall:false`) and the Content Targets quota
> [16103771](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16103771)
> (`PC_PLAYTEST=1 @ STANDARD_NC64AS_T4_V3 / WESTUS2`). Both are on `master`. Timi also confirmed the offering must set
> `DefaultAllocationPools` and shared the `KOLARITESTXNEW` prod offering as the template — it uses
> `"DefaultAllocationPools": { "PC": "PC_MAIN", "XBOX": "XBOX_MAIN" }`, confirming `PC_MAIN` is the correct PC pool.
> **Remaining gap = the offering config only** (the four fields below). The prod `PC_MAIN` pool exists **only in
> WESTUS2**, so `Regions` must be `WestUs2` (not `NorthCentralUs`) for the pool to resolve.

> **Update 2026-07-06:** Path A staged as a **pool-only** test —
> [PR 16097829](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/16097829)
> (branch `t-melanichen/fix-xpt2sdt4x91krqs-pc-allocation-pool` → `master`) adds **only** `DefaultAllocationPools={PC:PC_MAIN}`
> to the prod offering, leaving SUG/weights/`Regions=NorthCentralUs` unchanged. This clears the specific 400 to see whether
> the allocator then proceeds — but the build is staged in `PC_PLAYTEST`/`WestUs2`, so we expect a follow-up 400 on
> region/SUG (then layer in `SelectableSystemUpdateGroups=[PC_PLAYTEST]`, `SystemUpdateGroupWeights={PC_PLAYTEST:100}`,
> `Regions=[WestUs2]`). PR is **open, not merged** — awaiting human review.

## TL;DR
Launching the pilot offering **`XPT2SDT4X91KRQS`** (product `2SDT4X91KRQS`, "Melanie Playtest TEST2") fails at streaming
session creation with a hard **400**:

```json
{ "code": "Unknown", "statusCode": 400,
  "message": "Offering does not specify any default allocation pools for the selected content platform: PC" }
```

The front end surfaces this generically as **"Couldn't start your game streaming session — Unable to communicate with
servers."** The offering resolves and the title tile shows in the dev-tools browser
(`play.xbox.com/_internal/dev-tools/offering/XPT2SDT4X91KRQS`), but the offering config is missing the PC allocation
pool (and the SUG/weights/region), so the streaming allocator rejects every session.

## Root cause
The prod **`services.partnerregistry`** that created this offering is running **older code than what's merged to `main`**:

- The **`DefaultAllocationPools` code is unmerged** — local commit `bf3a9d41` (2026-07-06, `sci-ptnr` /
  `t-melanichen/playtest-offering-sug`) adds `offering.DefaultAllocationPools = { PC: settings.PCAllocationPool }` and
  `PlaytestSettings.PCAllocationPool = "PC_MAIN"`. It has **no PR yet** and is **not** an ancestor of `origin/main`.
- The **SUG/weights/region PR (15949594)** is merged to `main` but the prod service that wrote this offering **predates
  its release** — the offering has no SUG, no weights, and the *old hardcoded* `NorthCentralUs` region (the XBOX region),
  not the config-driven PC region `WestUs2`.

Offering config is written **once**, at `PlaytestProcessor.ConfigurePlaytestAsync → registryProcessor.BulkEditAsync`
(which commits the `OfferingV2.json` to `services.data.partnerregistry` and opens a PR). Deploying the fix later does
**not** back-fill the existing offering — it must be re-created (or the doc patched).

## Evidence — the actual prod doc
`ServiceGroups/XCLOUD/Environments/PROD/Partners/MICROSOFT/Offerings/XPT2SDT4X91KRQS/OfferingV2.json`
(created by registry-data commit `229834f "[PLAYTEST] Configure playtest offering XPT2SDT4X91KRQS with title
XPT2SDT4X91KRQS-MELANIEPLAYTESTTEST2-PC"`):

```jsonc
"DefaultAllocationPools": {},          // ← empty → the 400
"SelectableSystemUpdateGroups": null,  // ← no PC_PLAYTEST SUG
"SystemUpdateGroupWeights": {},        // ← no weights
"Regions": ["NorthCentralUs"],         // ← old XBOX region, not PC's WestUs2
"AuthenticationOptions": { "AuthenticationType": "Xbox", ... },
"AuthorizationOptions": { "AllowedDnaGroups": ["4611686019004512103"], ... },
"ExpirationTime": "2026-07-10T00:00:00Z"   // ← offering expires in 4 days
```

The **Title** doc is fine: `Platform: "PC"`, `TargetServerSkus: ["STANDARD_NC64AS_T4_V3"]`, `XboxTitleId: 2088843345`,
`ProductId: "2SDT4X91KRQS"`.

Deployed `origin/main` `PlaytestProcessor` PC branch now sets `TargetServerSkus` + `SelectableSystemUpdateGroups`
(`PC_PLAYTEST`) + `SystemUpdateGroupWeights` (`{PC_PLAYTEST:100}`) — but **not** `DefaultAllocationPools`. Commit
`bf3a9d41` is the only place that adds it.

## What the offering must have (what the fully-fixed code writes)
| Field | Current (prod) | Needs to be | Source |
|---|---|---|---|
| `DefaultAllocationPools` | `{}` | `{ "PC": "PC_MAIN" }` | `bf3a9d41` + `PlaytestSettings.PCAllocationPool` |
| `SelectableSystemUpdateGroups` | `null` | `[ "PC_PLAYTEST" ]` | PR 15949594 |
| `SystemUpdateGroupWeights` | `{}` | `{ "PC_PLAYTEST": 100 }` | PR 15949594 |
| `Regions` | `["NorthCentralUs"]` | `[ "WestUs2" ]` | `appsettings.en-prod.json` `RegionsByPlatform.PC` |

## Fix — plan for both paths

### Path A — Patch the prod offering data (fast; unblocks *this* title; no service redeploy)
1. In `services.data.partnerregistry`, edit
   `ServiceGroups/XCLOUD/Environments/PROD/Partners/MICROSOFT/Offerings/XPT2SDT4X91KRQS/OfferingV2.json`:
   set `DefaultAllocationPools = {"PC":"PC_MAIN"}`, `SelectableSystemUpdateGroups = ["PC_PLAYTEST"]`,
   `SystemUpdateGroupWeights = {"PC_PLAYTEST":100}`, `Regions = ["WestUs2"]`.
2. Open a PR → **human review + merge**. `FilesystemRegistry` reloads from git, so the allocator sees the pool/SUG on
   next load — no PartnerRegistryService deploy needed.
3. Re-try the launch.
- **Caveat:** this only fixes the *offering config*. It does **not** create servers. Streaming still needs a prod
  `PC_PLAYTEST` server in `PC_MAIN` / `WestUs2` that has **staged the build** (first-install). Prod PC_PLAYTEST OS
  Targets/quota/GPU capacity is **not confirmed** (only Test/Int were set up — see
  [`pc-playtest-sug-registration.md`](./pc-playtest-sug-registration.md)). If those don't exist, allocation still fails —
  with a *different* error.

### Path B — Deploy code + re-ingest (durable; fixes all future playtests)
1. Cherry-pick `bf3a9d41` onto a fresh branch off `origin/main` (`services.partnerregistry`), open a PR, get it reviewed
   + merged. (Cherry-picks cleanly; adds `PlaytestSettings.PCAllocationPool` + the PC-branch assignment.)
2. Ensure **PR 15949594 + the pool fix** are **released to prod** PartnerRegistryService (merged ≠ deployed — this
   offering proves prod is behind).
3. Confirm `appsettings.en-prod.json` `PlaytestSettings.RegionsByPlatform.PC = ["WestUs2"]` + `PCAllocationPool` ship.
4. **Re-publish the playtest** so `ConfigurePlaytestAsync` writes a fresh offering *with* all four fields.

## Prerequisites / related (needed regardless of path)
- **Prod PC_PLAYTEST servers** — OS Targets manifest entry + `SERVERSETSCONFIGURATION` quota + GPU capacity for
  `STANDARD_NC64AS_T4_V3` in **WESTUS2 prod**. **SUG definition + quota now DONE in prod** (PRs 16103484 + 16103771,
  merged 2026-07-07); GPU capacity availability in prod WESTUS2 still to confirm at launch. See
  [`pc-playtest-sug-registration.md`](./pc-playtest-sug-registration.md) and
  [`../FuturePlans/content-targets-pc-playtest-enablement.md`](../FuturePlans/content-targets-pc-playtest-enablement.md).
- **First-install / staging** — CTIN `PollFirstPCInstallAsync` must find a server that staged the version before the
  title is launchable. See [`pc-install-readiness-poll.md`](./pc-install-readiness-poll.md).
- The earlier prod **0-SAGE-rows** S2S bug is a *separate* issue — see
  [`../Explanations/prod-streaming-ingestion-debug.md`](../Explanations/prod-streaming-ingestion-debug.md).

## References
- Live 400 on launching `XPT2SDT4X91KRQS`: *"Offering does not specify any default allocation pools for the selected
  content platform: PC"*.
- `services.partnerregistry` commit `bf3a9d41` (unmerged) — `fix(PlaytestProcessor): set DefaultAllocationPools for PC
  playtest offerings`.
- [PR 15949594](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15949594) —
  SUG + weights on the playtest offering (merged; prod release status = **behind**).
- Prod offering doc: `services.data.partnerregistry` →
  `ServiceGroups/XCLOUD/Environments/PROD/Partners/MICROSOFT/Offerings/XPT2SDT4X91KRQS/OfferingV2.json`
  (created by commit `229834f`).
- Offering expiry: **2026-07-10** — if a fix slips past this, re-ingest is required anyway.
