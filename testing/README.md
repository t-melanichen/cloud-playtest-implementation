# DevApi test payloads

Ready-to-paste JSON for triggering **Playtest Title Ingestion** jobs from the DevApi ingestion page
(PR 15876080, `services.devapi`), used to validate the PC install-readiness polling workflow end to end.

## `devapi-xsth-pc-polling.json`

Publishes a **PC** playtest build for **XSTH ("Xbox Stream Test", ProductId `2SDT4X91KMWM`)** so the
`PlaytestTitleIngestionWorkflow` ingests it, configures the offering, and runs the **PC install-readiness
poll** (resolve install id + version hash → poll PC Orchestrator until a server has the exact build).

### How to use
1. Open the DevApi gateway ingestion page (the Blazor "trigger ingestion" page added in PR 15876080).
2. Paste the JSON into the parameters box and submit. It POSTs to
   `v3/workflows/playtesttitleingestion` on ContentIngestion.
3. Note the returned **job id**, then use the page's status check to watch the job through its stages
   (ValidateParameters → TriggerAssetIngestion → PollAssetIngestion → CreatePackage → ConfigureOffering →
   **PollFirstPCInstall** → ConcludeWorkflow).

### What to watch for (PC polling)
- The job should reach the **PC first-install poll** and keep retrying until a PC server reports the exact
  ingested version, then transition to `NotifyReady`.
- Requires the PC lane to be set up in the target env: the `PC_PLAYTEST` SUG definition + Content Targets
  quota, and the offering tagged with the SUG (see `../PC-Polling-Status.md`).

### Field notes
| Field | Value / meaning |
|-------|-----------------|
| `PlaytestId` | Unique per run (`p2-test-<guid>`). **Generate a new one for each fresh test** to avoid colliding with a prior job's partition key (`playtest_{PlaytestId}`). |
| `PartnerId` | `MICROSOFT` — owns the resulting offering. |
| `PlaytestProductId` | `2SDT4X91KMWM` — builds the offering id `xpt2SDT4X91KMWM`. |
| `StoreAsset.Platform` | `PC` — drives the PC readiness path (the point of this test). |
| `StoreAsset.PackageFamilyName` / `AumID` | The actual installable PC build behind the test product (Ninja Gaiden 2 Black). Required for PC. |
| `AllowedDnaGroups` | `["4611686019004512103"]` — the test DNA group authorized to access the offering. At least one is required. |
| `ExpirationTime` | Must be **in the future** and within the **30-day** cap. Bump it before reusing this file. |
| `AllowedSandboxId` | `RETAIL` (all playtests target retail today). |

> Note: these payloads carry internal test product/package ids; keep them to test/int environments.
