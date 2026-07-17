# E2E Test — PC Playtest Streaming (2026-07-06)

**Product:** `2SDT4X91KRQS` ("Melanie Playtest TEST2") · **Title:** `XPT2SDT4X91KRQS-MELANIEPLAYTESTTEST2-PC`
(xboxTitleId `2088843345`) · **Offering:** `XPT2SDT4X91KRQS` · **Seller:** `65050620` · **DNA group:**
`4611686019004512103` · **Account:** EnoughDaisy5498 (XGP Ultimate).

Attached evidence (this folder): `logs-2026-07-06-e2e/SAGE-ingestion-europe-500_2026-07-06.csv`,
`logs-2026-07-06-e2e/SAGE-session-commandproxy-404_2026-07-04.csv`.

---

## Design principle being validated
**A PC playtest must not be marked streamable until its exact ingested build is staged on a PC server.** Unlike Xbox
(servers pre-pull content), PC streaming servers **don't pre-pull**, and **every publish can be a new version**. So
readiness is only real once the specific version's first install is confirmed on a PC server
(CTIN `PollFirstPCInstallAsync`). Any "Get Ready To Stream" shown before that is premature.

---

## ✅ What worked
- **Playtest publish → Live** — pilot seller gate `65050620` passed; the publish reached Live.
- **Cross-tenant S2S auth** — worker → CTIN token now passes (audience fix, CTIN PR 15996626).
- **SAGE → CTIN ingestion (when routed to Americas)** — an ingestion POST reached CTIN and ran the
  `PlaytestTitleIngestion` workflow, which **created the offering + title** (registry-data
  **PR 16097366**, merged 2026-07-06 17:47, by the worker's S2S identity).
- **Offering + title exist and resolve in prod:**
  - Offering `XPT2SDT4X91KRQS` present under `.../Environments/PROD/Partners/MICROSOFT/Offerings/`.
  - Title metadata resolves fully: `productId 2SDT4X91KRQS`, `xboxTitleId 2088843345`, `hasEntitlement true`,
    `userSubscriptions [XGPULTIMATE, XGPSTANDARD, XGPCORE]`, `maxSessionLengthInSeconds 82800`.
  - **Product page renders** at `play.xbox.com/products/2SDT4X91KRQS/xpt2sdt4x91krqs-melanieplaytesttest2-pc`
    with a **"Get Ready To Stream"** CTA.
  - **Dev-tools offering browser** lists the title tile (`play.xbox.com/_internal/dev-tools/offering/XPT2SDT4X91KRQS`).
- **Resolution fix merged** — playtest `xpt`-prefix flight scoping is live in `origin/main` (CTIN PR 15983599).

## ❌ What didn't work
1. **Streaming launch → HTTP 400 (allocation pool):**
   ```json
   { "code": "Unknown", "statusCode": 400,
     "message": "Offering does not specify any default allocation pools for the selected content platform: PC" }
   ```
   Front end shows *"Couldn't start your game streaming session — Unable to communicate with servers."*
2. **Session allocation → SAGE `commandproxy` 404s** (07/04 log, 255 rows): repeated
   `POST .../northcentralus.americas.gssv-sage-prod.xboxlive.com/v1/commandproxy/... 404` and
   `eastus2.americas... 404`, plus a `gssv-sage-prod.../v1/user/metadata 500`. The session tried the offering's
   **`NorthCentralUs`** region and found **no PC playtest server**.
3. **Re-ingestion → HTTP 500 (SAGE→CTIN co-location gap)** (07/06 log): the ingestion POST landed on **europe** SAGE:
   ```
   POST http://gssv-sage-prod.xboxlive.com/v3/playtest/playtesttitleingestion → 500
   HttpRequestException: Name or service not known (contentingestion-svc.contentingestion:80)
   ```
   Europe/APAC SAGE cannot resolve the same-cluster CTIN service (CTIN is centralized in Americas). Ingestion success
   is **region-nondeterministic** — Americas works, Europe/APAC 500s.

**Net:** the offering/title **shell** is real and resolves, and the UI even offers "Get Ready To Stream", but the title
is **not actually streamable** — it fails at allocation (pool 400, then region/SUG 404) and re-ingestion is flaky by
region.

---

## The bugs

### Bug 1 — Offering written without a PC allocation pool (+ wrong region, no SUG/weights)
The prod offering `XPT2SDT4X91KRQS` has `DefaultAllocationPools: {}`, `SelectableSystemUpdateGroups: null`,
`SystemUpdateGroupWeights: {}`, and `Regions: ["NorthCentralUs"]` (the **XBOX** region) on a **PC** title. Root cause:
the prod `services.partnerregistry` that stamped this offering **predates the release of SUG PR 15949594** *and* the
`DefaultAllocationPools` code (`bf3a9d41`) is **unmerged**. Offering config is write-once (at
`ConfigurePlaytestAsync → BulkEditAsync`), so it doesn't back-fill.
- **Interim data patch (staged):** registry-data **PR 16097829** — pool-only test
  (`DefaultAllocationPools={PC:PC_MAIN}`), leaving region/SUG/weights to confirm the next failure. Follow-up adds
  `SelectableSystemUpdateGroups=[PC_PLAYTEST]`, `SystemUpdateGroupWeights={PC_PLAYTEST:100}`, `Regions=[WestUs2]`.
- **Durable fix:** merge + deploy `bf3a9d41` so `PlaytestProcessor` stamps the pool automatically; then re-ingest.
- Details: [`../Blockers/pc-playtest-default-allocation-pools.md`](../Blockers/pc-playtest-default-allocation-pools.md).

### Bug 2 — Two required Partner Registry changes
- **2a — Region:** PC playtest offerings must target the **PC region `WestUs2`**, not the XBOX region
  `NorthCentralUs`. The config-driven `RegionsByPlatform` (en-prod `PC=[WestUs2]`) is **not yet deployed to prod**, so
  the prod service still stamps the old hardcoded XBOX region — which is why session allocation 404s (no PC servers in
  NorthCentralUs).
- **2b — Offering must also carry the pool:** `PlaytestProcessor.ConfigurePlaytestAsync` must set
  `offering.DefaultAllocationPools = { PC: PC_MAIN }` (commit `bf3a9d41`) in addition to the SUG + weights
  (PR 15949594, merged). Without the pool the allocator hard-400s before it ever looks for a server.

### Bug 3 (prerequisite) — `PC_PLAYTEST` lane not provisioned in PROD
The `PC_PLAYTEST` SUG (server lane) + content-targets server-set quota are **merged in TEST + INT only**. Prod has **no
`PC_PLAYTEST` lane**, so even a perfectly-configured offering can't allocate or stage a build in prod. This is the
deepest blocker for a real prod stream. See [How to create PC_PLAYTEST in prod](#how-to-create-pc_playtest-in-prod-main).

---

## How to create PC_PLAYTEST in prod (main)
Two things must both be true before a PC playtest can stream, **per environment** (this must now be done for **PROD**):

### 1. Quota — content-targets dynamic config (says "a `PC_PLAYTEST` server is allowed to exist")
Portal: `DynamicConfigPartnerRegistry/ConfigSections/CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION` (**Prod**). Add the
`PC_PLAYTEST` quota to the SKU/region block, leaving existing live blocks untouched — mirroring the **INT** change
(PR 15966616):
```jsonc
"STANDARD_NC64AS_T4_V3": {
  "GameplaySlotsPerServer": 4,
  "DefaultMaxLocalSpaceInMB": 2000000,
  "QuotasBySugByRegion": { "WESTUS2": { "PC_PLAYTEST": 1 } }   // 1 NC64 box = 4× T4 = 4 concurrent testers
}
```
- **Region:** `WESTUS2` (prod PC region — matches the offering's required `Regions=[WestUs2]`).
- **Needs Timi / capacity owner:** confirm real **NC64 (`STANDARD_NC64AS_T4_V3`) GPU capacity in WESTUS2 prod** (else the
  server set is a no-op), or switch to the NC8 fleet (`STANDARD_NC8AS_T4_V3`) and change the code SKU to match.

### 2. SUG definition — PC SUG Definitions page (says "the lane's servers know which OS image to run")
Page: `https://americas.gssv-dev-prod.xboxlive.com/PcSugDefinitions` → **Add PC Sug Definition** (self-serve):
- **Sug Id** = `PC_PLAYTEST`
- **Inherits From** = `PC_TAKEHOME` (Jack: "currently our most solid"; `PC_GA` was accepted for Test/Int)
- **Link to Parent** for **Developer Settings** *and* **Flighting Configs** (inherits OS images — avoids the
  "At least one Flighting Config is required" error). **Save.**

### 3. Offering must stamp the lane (Partner Registry)
- SUG + weights: **PR 15949594** (merged) sets `SelectableSystemUpdateGroups=[PC_PLAYTEST]` +
  `SystemUpdateGroupWeights={PC_PLAYTEST:100}`.
- Pool: **`bf3a9d41`** (pending) sets `DefaultAllocationPools={PC:PC_MAIN}`.
- Region: **en-prod `PlaytestSettings.RegionsByPlatform.PC=[WestUs2]`** (pending prod release).
- **All three must be released to prod**, then **re-ingest** so the offering is rewritten with them.

> Optional recognition cleanup: add `PC_PLAYTEST` to `Services.Common.Ids` `SystemUpdateGroup` (unknown SUGs only produce
> a non-critical validation warning today).

Full copy/paste reference: [`../FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md`](../FuturePlans/pc-playtest-dynamic-config-and-sug-setup.md).

---

## Deploy / merge status matrix
| Piece | Repo | TEST | INT | PROD |
|---|---|---|---|---|
| `PC_PLAYTEST` SUG definition | services.data.partnerregistry | ✅ merged | ✅ merged | ❌ **todo** |
| Content-targets quota (SERVERSETSCONFIGURATION) | services.data.partnerregistry (dyn cfg) | ⚠️ region mismatch | ✅ PR 15966616 | ❌ **todo** |
| Offering SUG + weights | services.partnerregistry | ✅ (PR 15949594 code) | ✅ | ⚠️ merged to main, **prod release lagging** |
| Offering `DefaultAllocationPools` | services.partnerregistry | — | — | ❌ **`bf3a9d41` unmerged** |
| Offering `RegionsByPlatform.PC=WestUs2` | services.partnerregistry (en-prod) | — | — | ❌ **not released to prod** |
| Resolution `xpt` flight scoping | services.contentingestion | ✅ | ✅ | ✅ (PR 15983599 in main) |
| Cross-tenant audience auth | services.contentingestion | ✅ | ✅ | ✅ (PR 15996626) |
| PC install-readiness poll | services.contentingestion | ✅ | ✅ | ✅ (PR 15896502) |
| SAGE→CTIN routing (europe/apac) | services.serviceapigateway / infra | ❌ | ❌ | ❌ **co-location gap (GameStreaming-owned)** |

---

## Next steps
1. **Merge PR 16097829** (pool-only) and re-test the launch → expect the pool 400 to clear and a region/SUG failure to
   surface (confirms Bug 2a/3). Then patch region/SUG or wait for the code deploy.
2. **Provision `PC_PLAYTEST` in prod** — quota (§1, Timi) + SUG definition (§2, self-serve).
3. **Release to prod** the Partner Registry set: PR 15949594 + `bf3a9d41` + en-prod region config; then **re-ingest**.
4. **Raise SAGE→CTIN routing** (europe/apac 500s) with the GameStreaming/CTIN team — the ingestion POST must reach a
   cluster co-located with CTIN, or CTIN needs a stable cross-region endpoint. Tracks with
   [`../Explanations/prod-streaming-ingestion-debug.md`](../Explanations/prod-streaming-ingestion-debug.md).
   - **Interim pin — Xbet PR 16102792** (`t-melanichen/pin-playtest-ingestion-to-americas`): sets
     `XCloudPlaytestIngestionServiceClient.Host = americas.gssv-sage-prod.xboxlive.com`. **Why the Americas core (not
     global or a sub-cluster):** submit (POST) and status-poll (GET) use the *same* client/Host
     (`SendForOperationStatusAsync`), but DNS resolves each request independently. The global `gssv-sage-prod` can hit
     Europe/APAC (no CTIN → 500). Per the CTIN owner, Americas is the only core with Content ingestion; `eastus2`
     (20.41.13.162) and `northcentralus` (20.241.33.111) are rotating Americas sub-clusters and must not be pinned
     directly. CTIN jobs use a single shared Cosmos account per environment, so a created job is visible to polls from
     any Americas sub-cluster; the observed 702 ms eastus2 `NotFound` was most likely for a submit that had 500'd in
     Europe/APAC and was never created. Pinning only the XPackageWorkflow playtest ingestion host to the Americas core
     fixes the Europe/APAC 500 and prevents false poll 404s from failed submits; other prod Xbet SAGE callers stay on the
     global host, and Staging/Dev stay on `gssv-sage-test`. Revert once the durable SAGE/CTIN routing fix lands (ADO Task
     63013710: https://microsoft.visualstudio.com/Xbox/_workitems/edit/63013710).
5. **Readiness gating** — confirm the product isn't surfaced as "Get Ready To Stream" until first-install is confirmed
   (the design principle above), so testers don't hit a dead launch.

## References
- Offering doc: `services.data.partnerregistry` → `.../PROD/Partners/MICROSOFT/Offerings/XPT2SDT4X91KRQS/OfferingV2.json`
- Offering-creation PR (worker): 16097366 · Pool-only patch PR: 16097829
- Partner Registry SUG/weights PR: 15949594 · Pool fix commit: `bf3a9d41` (unmerged)
- CTIN: 15983599 (resolution), 15996626 (auth), 15896502 (install poll) · INT quota: 15966616
- Blockers: `pc-playtest-default-allocation-pools.md`, `pc-playtest-sug-registration.md`, `pc-install-readiness-poll.md`
- Logs: `logs-2026-07-06-e2e/` (europe-500 ingestion, 07/04 commandproxy-404 session)
