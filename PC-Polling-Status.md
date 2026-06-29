# PC streaming-readiness polling — consolidated status

**Last updated:** 2026-06-29 · **Owner:** Melanie Chen (@t-melanichen)

One-stop tracker for the PC install-readiness polling work in xCloud: every PR in the chain, what each one
does, what's done, the pending review comments/questions, the open bugs, and what's left to do.

---

## 1. What PC polling is (the chain)

PC (WINDOWS.DESKTOP) streaming playtest content is **not pre-pulled** the way Xbox content is, so the ingestion
workflow must confirm the **exact ingested version** is staged on a PC server before declaring the title ready:

1. **Ingest** the PC playtest version — CTIN `PlaytestTitleIngestionWorkflow`.
2. **Attach** the title to the offering under a `PC_PLAYTEST` SUG — Partner Registry.
3. **Content Targets** maps the install to a PC server set that has **quota** — dynamic config.
4. **CTIN resolves** the exact version's install id + content **hash**, then **polls PC Orchestrator**
   (`IPCOrchestratorClient.QueryServersPagedAsync` with a `ContentFileFilter { Id, Version=hash }`) until a
   server reports it → `NotifyReadyAsync`.

---

## 2. All PRs in the chain

| # | PR | Repo | Status | What it does |
|---|----|------|--------|--------------|
| CTIN | **[15896502](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15896502)** | services.contentingestion | **Merged** (2026-06-29) | The readiness poll itself (resolve version hash → poll PC Orchestrator). Branch `t-melanichen/playtest-pc-install-polling`. |
| PTNR | **[15949594](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.partnerregistry/pullrequest/15949594)** | services.partnerregistry | **Merged** (2026-06-29) | Sets `PC_PLAYTEST` `SelectableSystemUpdateGroups` + `SystemUpdateGroupWeights` on the offering. |
| PTNR-DATA | **[15965750](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15965750)** | services.data.partnerregistry | **Merged** | `PC_PLAYTEST` SUG definition (Test, inherits `PC_GA`). |
| PTNR-DATA | **[15965763](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15965763)** | services.data.partnerregistry | **Merged** | `PC_PLAYTEST` SUG definition (Int). |
| DCFG | **[15966616](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15966616)** | services.data.partnerregistry | **Merged** | PC server quota via dynamic config (**Int**: `STANDARD_NC64AS_T4_V3` / WESTUS2 / `PC_PLAYTEST: 1`). |
| DCFG | **[15980328](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.data.partnerregistry/pullrequest/15980328)** | services.data.partnerregistry | **Merged** | PC server quota via dynamic config (**Test**: WESTUS3). The "enable in Test" follow-up Jack pushed for — Test's Azure-granted quota is in WESTUS3. Portal PR raised by the `xcld-test-envr-wus3-ptnr-msi` service account on your behalf. |
| CTIN-RES | **[15983599](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15983599)** | services.contentingestion (**content resolution** sub-project) | **Merged** (2026-06-29) | The resolution fix. Content ingestion **scopes package search to GA by default**; playtest builds are never ingested as GA. This makes resolution **not** scope a playtest's asset-version search to specific flights (detects playtest from the `xpt…` Title id). Branch `t-melanichen/resolution-playtest-no-ga-flight`. |
| CTGT | **[15946980](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contenttargets/pullrequest/15946980)** | services.contenttargets | **Abandoned** | Superseded by the dynamic-config quota (PR 15966616); kept 3 regression tests only. |

Per-PR detail lives in [`PRProgress/`](./PRProgress/README.md) (files 17–22).

---

## 3. CTIN PR 15896502 — current state

- **Branch:** `t-melanichen/playtest-pc-install-polling` — pushed to ADO at **`d094937e`**.
  - `2bffc05c` — SUG-constant (earlier)
  - `9414d5dc` — review fixes A1–A6
  - `d094937e` — resolve-state refactor (B + C1)
- **Build/tests:** full solution builds clean; **25/25 unit tests pass**.
- **Working copy:** `C:\Users\t-melanichen\source\sci-pcpolling` (clean clone **outside OneDrive** — see §7).
- **All 12 review threads have replies.** 11 of 12 are implemented in code; 1 (`Flights`) is intentionally
  deferred. 5 threads still carry an **open question for Timi** (see §4).

---

## 4. Review comments — status of every active thread

Legend: ✅ implemented · ⏳ implemented but awaiting Timi's confirmation · ⛔ deferred (blocked)

| Thread | Reviewer ask | Status | Resolution / commit |
|--------|--------------|--------|---------------------|
| `127704815` | Drop 2 redundant PCServices csproj refs | ✅ | Removed; transitive via Orchestrator.Client (`9414d5dc`). |
| `127703938` | Rename poll stages + `PC` casing | ✅ | `PollFirstXboxInstallAsync` / `PollFirstPCInstallAsync`, `Pc`→`PC` (`9414d5dc`). |
| `127703160` | Config props shouldn't be null | ✅ | `SystemUpdateGroup` default `PC_PLAYTEST`, `Skus` default `[]`, `PlaytestPcReadinessQuery` non-null (`9414d5dc`). |
| `127589595` | SUG/SKU never null; pass directly | ⏳ | Removed the hardcoded constant; config-with-defaults passed straight to the filter (`9414d5dc`). **Open Q:** confirm empty `Skus=[]` means "no SKU constraint" in `GameStreamingServerFilter`. |
| `127703703` | One-line `CommonValidate` guard | ✅ | `CommonValidate.IsNotEmpty(...)` (`9414d5dc`). |
| `127703375` | Read-delay on the state transition | ✅ | Applied as `nextStageDelay` into `ResolveContentInstallAsync` (`9414d5dc` / `d094937e`). |
| `127703477` | Distinct `ResolveContentInstallAsync` state; store `InstallId` | ⏳ | New shared stage resolves once, stores `InstallId` (+ PC version hash) (`d094937e`). **Open Q:** store the version hash in state (current choice) vs re-resolve in the PC poll? |
| `127703914` | Selector = TitleId + US market; store `InstallId` | ✅ | Selector `(PartnerId, TitleId, "US")`; `StreamingPackageIds` removed from JobState (`d094937e`). |
| `127704658` | Xbox poll uses `context.State.InstallId` | ⏳ | `LocalPackageId = context.State.InstallId` (`d094937e`). **Open Q:** does the allocator expect the resolved (flight-encoded) install id vs the old `Generate(packageId)`? |
| `127703297` | Drop `ServerTypes` from the resolution query | ✅ | Removed (`d094937e`). |
| `127702807` | Remove `TryGetCurrentVersion`; use `GetCurrentVersion`. Timi follow-up: zero current versions should throw too. | ✅ | Helper removed; resolve stage calls `GetCurrentVersion`, so **both zero and multiple** current versions throw (`6ac9560a`). The read delay on the transition covers the "intentionally delayed availability" caveat Timi noted. |
| `127703251` | Drop `Flights` (resolver infers playtest) | ⛔ | **Flights KEPT on purpose.** Dropping them before the resolution PR ([15983599](https://dev.azure.com/microsoft/Xbox.Streaming/_git/services.contentingestion/pullrequest/15983599)) merges folds in the GA flight → playtest never resolves (rubber-duck confirmed). That PR now detects playtest **from the TitleId prefix** (no `IsPlaytest` flag), so once it merges CTIN just drops `Flights` (no flag to set). |

### Pending questions for Timi (consolidated)
1. **`127589595`** — empty `Skus=[]` ⇒ "no SKU filter" on `GameStreamingServerFilter`? (tests assume yes; also: kept config defaults rather than `required` since `required` conflicts with the `= new()` default)
2. **`127703477`** — PC version hash: store it in job state (current) or re-resolve in the PC poll?
3. **`127704658`** — does the allocator's `LocalPackageId` expect the resolved flight-encoded install id?
4. **`127703251`** — drop `Flights` once the resolution PR (15983599) merges.

---

## 4b. Resolution PR 15983599 — review comments (addressed locally, NOT pushed)

Timi asked for a different mechanism than the original branch (which added an `IsPlaytest` flag). Redesigned per his guidance; **6 threads addressed + replies posted**, build + 481/481 tests green. **Pushed** to ADO at `b5b31009` (working copy: `C:\Users\t-melanichen\source\sci-resolution`).

| Thread | Ask | Resolution |
|--------|-----|-----------|
| `127702177` / `127702203` | Don't add an `IsPlaytest` flag to `ResolutionQuery` / `ResolutionContext` — the catalog already knows a Title is a playtest. | Removed the flag from both; reverted the plumbing through `ResolutionProcessor`. |
| `127702287` | Detect playtest with a local `bool isPlaytest = TitleId.StartsWith(...)`. | Added a local `isPlaytest` in both catalogs from `context.Package.TitleId`. **Note:** used prefix `"xpt"` (the real generated `xpt{productId}-…` format), **not** the literal `"XPT-"` Timi typed — flagged in a reply. |
| `127702456` / `127702505` | Don't alter the InstallId/flight-mapping part (keep InstallId consistent). | Reverted `mappedFlightIds` to original (always folds in GA); InstallId unchanged. |
| `127702588` | Alter the asset-version **filter** to `isPlaytest \|\| mappedFlightIds.Contains(av.FlightId)`. | Done in Cosmos + InMemory catalogs. New behavior: a playtest surfaces **all** ingested flights; best version picked downstream. Rewrote `PlaytestFlightScopingTests` to match. |

**One open reply for Timi:** the playtest TitleId prefix is `xpt` (lowercase, `xpt{productId}-…`), not `XPT-`; confirm that's the intended detection (ideally a shared constant with the generation side).

## 4c. PTNR PR 15949594 — review comment (addressed + pushed `66723a4f`)

| Thread | Ask | Resolution |
|--------|-----|-----------|
| `127705350` | Replace the hardcoded PC SKU/SUG + Prod/NonProd region lists (and the temp work-item TODOs) with a `PlaytestSettings` config record via `IOptionsMonitor`, with `RegionsByPlatform` per environment. | Added `PlaytestSettings` (`PCServerSku`, `PCSystemUpdateGroup`, `RegionsByPlatform: Dictionary<string,string[]>`); inject `IOptionsMonitor<PlaytestSettings>`; region now selected by the title's platform; removed the consts + TODO(62812760). Added the config to `appsettings.json` + `appsettings.en-{prod,test,int}.json` exactly per Timi's spec; wired `services.Configure<PlaytestSettings>` in Startup. Build + 14/14 tests green. Working copy: `C:\Users\t-melanichen\source\sci-ptnr`. |

---

## 5. Open bugs (found by rubber-duck — not yet PR comments)

| Id | Bug | Severity | Action |
|----|-----|----------|--------|
| B5b | Poll starts before the offering PR is merged; `FirstInstallPollingPolicy` is 6h, but manual approval can lag (~48h) → false "not found". | High | Gate the poll on the offering PR being merged, or extend/separate the approval wait. |
| B5c | Orchestrator filter sets only SUG/SKU/Content; doesn't require a healthy/usable server. | Med | Add `IsHealthy = true` (+ ready, not deleted). |
| B5d | `ResolveContentInstallMetadataAsync` can throw on Catalog read-lag → faults instead of retrying. | Med | Catch the not-visible case → route to the same retry/not-found path. |
| B3/B4 | Confirm a republish resolves the **newest** hash; confirm an empty first page = "retry", not premature terminal. | Med | Add coverage once the resolver-infers-playtest path is in. |
| migration | In-flight jobs already at a poll stage deserialize without `InstallId` (legacy `StreamingPackageIds`) → guard throws → job fails. | Low (feature not live) | If deploying to an env with active jobs, add a "fall back to re-resolve when `TitleId` present" path. |

Full design notes: [`FuturePlans/pc-install-readiness-polling-implementation.md`](./FuturePlans/pc-install-readiness-polling-implementation.md),
[`FuturePlans/polling-strategy-refinement.md`](./FuturePlans/polling-strategy-refinement.md),
[`FuturePlans/replace-polling-with-callback.md`](./FuturePlans/replace-polling-with-callback.md).

---

## 6. Platform / cross-repo items (Timi / Jack)

- **Quota is Azure-allocated.** Server quota is *"determined by Azure wherever they decide to give it to us — not
  something we can scale up/down on our own"* (Jack). So the Test region question can't be solved by "adding
  WESTUS2 capacity"; we work with the regions Azure has actually given us quota in.
- **Enable Test if possible** — Jack: *"we should try to enable this in Test since we do have quota there."* Today
  Test quota is in **WESTUS3** but the offering targets **WESTUS2/WestEurope**. Because we can't self-provision
  WESTUS2 quota, the realistic options are: point the Test offering/SKU at **WESTUS3** (where the quota is), or
  confirm with Timi whether Azure can grant WESTUS2 Test quota for `STANDARD_NC64AS_T4_V3`. **Int** already lines
  up (quota + offering both WESTUS2), so Int is the clean first validation env.
- Confirm **Int has real NC64 (`STANDARD_NC64AS_T4_V3`) GPU capacity in WESTUS2** (else the server set is a no-op).
- Confirm whether the `IncludePredictions` override is needed for `PC_PLAYTEST` in non-prod.
- **SUG setup recap (Timi/Jack):** a SUG needs (1) **quota** (dynamic config) and (2) a **definition** on the
  **PC SUG Definitions page** — <https://americas.gssv-dev-prod.xboxlive.com/PcSugDefinitions> — where it's assigned
  OS image versions by **inheriting from a production/release SUG** (`PC_TAKEHOME` is the most solid; `PC_GA` is
  fine for Test/Int, confirmed). Already done for `PC_PLAYTEST` in Test + Int.

Setup reference: [`FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md`](./FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md).

---

## 7. Done vs. to-do

### ✅ Done
- **All three review PRs merged to `main` (2026-06-29): CTIN `15896502` (PC polling), CTIN `15983599` (resolution no-GA-flight), PTNR `15949594` (offering SUG).** Latest review comments (Timi nits + Brian's questions) addressed and pushed before merge.
- CTIN code: all 6 review fixes (A1–A6) **and** the resolve-state refactor — pushed; 25/25 tests green, full build clean.
- All CTIN review threads replied.
- PTNR-DATA `15965750` / `15965763` and DCFG `15966616` / `15980328` — **merged**.

### 🔲 What I need to do
1. **Manually deploy + test the merged chain** — combined test branch `t-melanichen/pc-polling-resolution-test` exists (PC polling + resolution); or test off `main` now that all three are merged.
2. Address the open bugs **B5b / B5c / B5d** (§5).
3. Work the **platform/cross-repo items** with Timi (§6).
4. **Follow-up ADO tasks (§9):** extract `PC_PLAYTEST` to a shared constant (AB#62907255); long-term region routing (AB#62907370).
5. **Move `services.contentingestion` out of OneDrive** (or exclude `.git` from sync) — see §8.

---

## 8. Environment note (important)

The original clone `…\OneDrive - Microsoft\Desktop\services.contentingestion` keeps its **`.git` under OneDrive**,
which syncs git internals from another machine/session and **flips the checked-out branch mid-session** (the
working tree becomes a mix of branches). All CTIN work was therefore done in a clean clone **outside OneDrive**:
`C:\Users\t-melanichen\source\sci-pcpolling` (origin → ADO). Continue PC-polling work there until the OneDrive
repo is fixed (move it out of OneDrive, or exclude `.git` from sync).

### Build / test (CTIN)
```
cd C:\Users\t-melanichen\source\sci-pcpolling
dotnet test src/Tests/Unit/ContentCatalog.Ingestion.Core.UnitTests/ContentCatalog.Ingestion.Core.UnitTests.csproj
```

---

## 9. Follow-up ADO tasks (Brian review on PR 15949594)

Filed from Brian Bowman's review comments so the longer-term work isn't lost. Both are `Proposed`, assigned to Melanie Chen.

| AB# | Task | Parent | What |
|-----|------|--------|------|
| **62907255** | Extract `PC_PLAYTEST` SUG to a shared `Services.Common.Ids` constant | Instant Playtest scenario `62490517` | `"PC_PLAYTEST"` is hardcoded independently in PTNR `PlaytestSettings.cs`, CTIN `IngestionWorkflowSettings.cs`, the partner-registry SUG definition, and the content-targets quota. Producer (offering tag) and consumer (readiness poll) must match exactly, so a typo/rename silently breaks the flow with no compile-time check. Promote it to a named `SystemUpdateGroup` constant (alongside `SystemUpdateGroup.GA`), publish a new package version, then migrate PTNR + CTIN. See [`FuturePlans/shared-sug-constant.md`](./FuturePlans/shared-sug-constant.md). |
| **62907370** | Long-term region configuration + routing for streamable playtests | [Intern] Stretch Goals `62684196` (reactivated) | v1 = static per-env `RegionsByPlatform` (test/int WESTUS2 + WestEurope, prod NorthCentralUs) + offering-conflict routing, no client region param. Long term: creator-selected allowed regions in Partner Center; investigate automatic DNS/IP routing to drop the client region param; eventually multiple PC GPU flavors with the PC-server team. See [`FuturePlans/region-configuration-routing.md`](./FuturePlans/region-configuration-routing.md). |
