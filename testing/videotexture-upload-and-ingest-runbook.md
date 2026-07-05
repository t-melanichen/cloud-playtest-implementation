# Runbook: VideoTexture PC build → xPackage → PC server (DevApi → CTIN)

Goal: take the **built + packaged** ATG VideoTexture MSIXVC (see
[`pc-video-graphics-stream-test.md`](./pc-video-graphics-stream-test.md) "Build & packaging log") and prove it can
be **ingested onto an xCloud PC server**: upload it to xPackage, then trigger the CTIN
**PlaytestTitleIngestion** workflow via DevApi and watch the **PC install-readiness poll** land the exact build on
a PC server.

This is the xCloud-side ingest test only (not the full Partner Center publish path); DevApi lets us POST a
hand-crafted `StoreAsset` straight at CTIN.

## The package under test
- MSIXVC: `C:\Users\t-melanichen\source\_gdk\out\MelanieATG.VideoTexturePC12_1.0.0.0_x64__qfz1z4rvaj27y.msixvc`
- Identity `Name` = `MelanieATG.VideoTexturePC12`, `Publisher` = `CN=MelanieATGTest`, `Version` 1.0.0.0, x64
- **PackageFamilyName** = `MelanieATG.VideoTexturePC12_qfz1z4rvaj27y`
- **AumID** = `MelanieATG.VideoTexturePC12_qfz1z4rvaj27y!Game`  (ApplicationId `Game`)
- makepkg ContentId = `D1172C85-8FD3-6502-29B8-CE5BF4FDD367` (store may assign its own on upload — see Phase 1)

## Checklist
- [ ] 0. Confirm the PC lane is set up in the target env (SUG + quota + offering) — pick **Int** first
- [ ] 1. Upload the MSIXVC to xPackage (get a resolvable PFN + ContentId)
- [ ] 2. Fill in `devapi-videotexture-pc-polling.json` (PFN/AumID/ContentId/expiry/new PlaytestId)
- [ ] 3. Trigger CTIN via the DevApi ingestion page → record the job id
- [ ] 4. Watch stages through **PollFirstPCInstall → ConcludeWorkflow**
- [ ] 5. Verify the exact version hash is installed on a PC server (PC Orchestrator)

---

## Phase 0 — Prerequisites (or the poll never finds a server)
From [`../PC-Polling-Status.md`](../PC-Polling-Status.md) §6:
- The **PC_PLAYTEST** SUG must have (1) a **definition** on the PC SUG Definitions page and (2) **Content Targets
  quota** (dynamic config), and the **offering** must be tagged with the SUG. Already done for **Test + Int**.
- **Env choice — use Int first.** Int lines up cleanly (quota + offering both **WESTUS2**). Test's Azure quota is
  in **WESTUS3** while the offering targets WESTUS2/WestEurope → mismatch (point Test's offering/SKU at WESTUS3, or
  just validate in Int).
- Confirm Int actually has **NC64 (`STANDARD_NC64AS_T4_V3`) GPU capacity in WESTUS2** (else the server set is a no-op).

## Phase 1 — Upload the MSIXVC to xPackage
CTIN's `TriggerAssetIngestion` pulls the package **by PackageFamilyName / ContentId** from the package store, so the
build has to exist there first.
- Upload `MelanieATG.VideoTexturePC12_..._x64__qfz1z4rvaj27y.msixvc` via the xPackage / Partner Center package-upload
  path for the target sandbox (RETAIL).
- After it processes, note the store-assigned **ContentId** (and confirm the **PackageFamilyName** matches
  `MelanieATG.VideoTexturePC12_qfz1z4rvaj27y`).
- ⚠️ This is a **placeholder identity** (`CN=MelanieATGTest`, all-zero ProductId). If xPackage rejects an
  unregistered identity, either (a) re-pack with a real StoreId/identity and real logos (`makepkg pack ... /pc
  /productid <id>`), or (b) upload under the existing test product **XSTH `2SDT4X91KMWM`** (publisher `65050620`).

## Phase 2 — Prepare the DevApi payload
Start from [`devapi-videotexture-pc-polling.json`](./devapi-videotexture-pc-polling.json) (already filled with this
package's PFN/AumID). Per-run edits:
- **PlaytestId** — new unique value each run (`p2-test-<guid>`), else it collides on the `playtest_{PlaytestId}`
  partition key.
- **StoreAsset.ContentId** — set to the ContentId from Phase 1.
- **ExpirationTime** — future and within the **30-day** cap; bump before reusing.
- **AllowedDnaGroups** — your test DNA group (`4611686019004512103` from the sibling XSTH payload).
- Keep **PlaytestProductId = `2SDT4X91KMWM`** (XSTH) — it's Xbox-Live-configured so the publish resolves a
  `TitleId` (a non-configured product hard-fails the pilot-seller publish). `StoreEntry` therefore describes XSTH,
  while `StoreAsset` (PFN/AumID/ContentId) points at the VideoTexture build.

## Phase 3 — Trigger CTIN via DevApi
1. Open the DevApi gateway **ingestion page** (the Blazor "trigger ingestion" page, `services.devapi` PR 15876080).
2. Paste the payload and submit → it POSTs to **`v3/workflows/playtesttitleingestion`** on ContentIngestion.
3. Record the returned **job id**.

## Phase 4 — Watch the workflow reach a PC server
Stages: `ValidateParameters → TriggerAssetIngestion → PollAssetIngestion → CreatePackage → ConfigureOffering →`
**`PollFirstPCInstall`** `→ ConcludeWorkflow`.

The PC poll (CTIN PR 15896502): resolves the exact ingested version's **install id + content hash**, then polls
**PC Orchestrator** (`IPCOrchestratorClient.QueryServersPagedAsync` with `ContentFileFilter { Id, Version=hash }`)
until a PC server reports that exact build, then calls **`NotifyReadyAsync`**.

## Phase 5 — Verify it's on a PC server
- Job status advances past **PollFirstPCInstall** to **ConcludeWorkflow** with **NotifyReady** fired.
- Cross-check on the **PC Orchestrator "Server set overview"** dashboard: the content (matching **version hash**) is
  installed on ≥1 PC server in the target region/SUG (`PC_PLAYTEST`). The version on a PC content install *is the
  hash* — filter by it.

## Troubleshooting (open bugs from PC-Polling-Status §5)
- **B5b** — poll (6h `FirstInstallPollingPolicy`) can start before the offering PR is merged/approved (~48h) → false
  "not found." Make sure the offering is live before/at ingest.
- **B5c** — the Orchestrator filter checks SUG/SKU/Content but not health → may match an unusable server.
- **B5d** — a Catalog read-lag on resolve can throw instead of retrying.
- Playtest is detected from the **`xpt` TitleId prefix** (resolution PR 15983599, merged) — no `IsPlaytest` flag.
- Empty first page from the poll = **retry**, not a terminal "not found".

## References
- [`pc-video-graphics-stream-test.md`](./pc-video-graphics-stream-test.md) — the build/packaging that produced this MSIXVC.
- [`../PC-Polling-Status.md`](../PC-Polling-Status.md) — the full PC install-readiness polling chain, PRs, quota/SUG setup, bugs.
- [`README.md`](./README.md) + [`devapi-xsth-pc-polling.json`](./devapi-xsth-pc-polling.json) — the sibling XSTH/Ninja-Gaiden payload this mirrors.
- [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md) — design notes.
