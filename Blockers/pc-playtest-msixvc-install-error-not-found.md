# Blocker: PC playtest MSIXVC install fails with `ERROR_NOT_FOUND` (-2147023728)

**Status:** 🟡 **Fix merged; deploy to prod in progress (2026-07-14).** Root cause: the playtest streaming `StoreAsset` sent the **SUCU `servicingContentId`** as `ContentId`, but the PC MSIXVC is keyed on the **real `contentId`**, so the install looked it up by the wrong id and returned `ERROR_NOT_FOUND`. Fixed by a 5-PR ContentId separation — STORECLIENT 16128230 ✅, XBET 16130422 ✅, CTIN 16129840 ✅, CTDR 16137972 ✅ (merged), SESSIONS 16140301 🕗 active; see [Fix](#fix--5-prs) below. **Verified only against Timi's manually-patched DB record so far — NOT yet in prod:** the Xbet fix (16130422) merged 07-09 but the last completed `XPackageWorkflow-K8S` deploy was 07-06, so prod still runs the old behavior and installs still fail. A deploy (`20260713.1`) is in progress but hasn't reached the prod rings. Timi hand-patches the DB as a workaround until it lands. **The next-stage blocker is a server-side launch/provision issue** — see [`pc-playtest-launch-timeout-grts.md`](./pc-playtest-launch-timeout-grts.md).

**Owners:** Melanie Chen (playtest ingestion / offering) · Timi Bolaji (xCloud content resolution + distribution) · Nate's server team (PC server install agent).

## What happens

After the offering config + quota + SUG + predicted targets landed (see [`../Explanations/pc-playtest-streaming-allocation-e2e.md`](../Explanations/pc-playtest-streaming-allocation-e2e.md)), a PC server is allocated and attempts to install the build, but the install batch command fails:

```
Batch Command InstallOrUpdateMsixvcContentByUrlV1 Failed - Error: -2147023728
  at D:\a\_work\1\s\src\Product\Shared\PcServer.Common.Agents\Utilities\CustomActionAppxPayload.cs:88
```

`-2147023728` = `0x80070490` = `HRESULT_FROM_WIN32(ERROR_NOT_FOUND)` ("Element not found").

Diagnostics for log pulls:
- Time: `2026-07-09T17:40:00Z`
- cV: `QWrTeUTBOEK5ZAQNPHc1BA.4.3`
- ServerId: `PC890D4459AE0BF0`

## Debug history (with Timi)

1. The build initially landed as a ~10 MB **stub** instead of the real ~461 MB build, so the install failed and content distribution looped (install → fail → delete, every ~5 min).
2. After publishing a real (non-stub) ~461 MB build, the install **still fails with the same error code**.
3. Leftover-state theory: a prior stub-install may have left state on the reused server (reused VHD). Timi forced a **fresh server** via PC Orchestrator (check out → new server created → check in → old deleted) and retried — **still the same error**. This makes server-local leftover state an unlikely cause.

## Leading theory — `servicingContentId` vs `contentId` mismatch

Timi's hypothesis: the `servicingContentId` on the XProduct document (used by SUCU, the content query tooling / `CV` + `CM` commands) differs from the `contentId` that the MSIXVC is actually keyed on. If the install is invoked with the `servicingContentId` as the identifier, the server cannot find the matching MSIXVC content and returns `ERROR_NOT_FOUND`. This fits the evidence: a real, published build fails identically to a stub, and a fresh server does not help — pointing at a wrong **identifier**, not server state. **Confirmed** — this is the root cause.

## Fix — 5 PRs

The `servicingContentId` (SUCU) and the real `contentId` were being conflated on `StoreAsset`. The fix threads both ids through so **sourcing** (asset ingestion/resolution) keys on the servicing id (unchanged) while the **install + provisioning commands** use the real content id.

| PR | Area | Repo | Status | Description |
| --- | --- | --- | --- | --- |
| 16128230 | STORECLIENT | services.common.content | ✅ Merged | Add `ServicingContentId` to `StoreAsset`; `SourceId => ServicingContentId ?? ContentId` (computed) |
| 16130422 | XBET | Xbox.Xbet.Service | ✅ Merged (07-09) | `StoreAsset.ContentId ← PlaytestContentId` (real), `ServicingContentId ← ServicingContentId`; bump `...Common.Content.Ids` → 3.1.2607.901 |
| 16129840 | CTIN | services.contentingestion | ✅ Merged (07-10) | Add `AssetProperties.ContentId`; ingest/resolve under `StoreAsset.SourceId`; carry real `ContentId` for install |
| 16137972 | CTDR | services.contentdistribution | ✅ Merged (07-10) | Separate `SourceId` from `ContentId`: `SourceId` for **sourcing**, real `ContentId` for **distribution commands** (the MSIXVC install) |
| 16140301 | SESSIONS | services.sessions | 🕗 Active | Separate `ContentId` from `SourceId`; use explicit `ContentId` for **provisioning** commands |

**Manual DB patch (2026-07-09/10):** Timi manually patched the ingestion DB record with the proper `contentId`, so the distribution/provisioning fixes could be validated via hotfix without waiting for the full deploy. One-off — new playtests get the right `contentId` automatically once all five ship.

**ADO:** tracked by Task [63080671](https://microsoft.visualstudio.com/Xbox/_workitems/edit/63080671) (under scenario 62490517).

### How the fix works

1. **Xbet** builds `StoreAsset` with `ContentId = PlaytestContentId` (real, msixvc-keyed) and `ServicingContentId = ServicingContentId` (SUCU). — `StreamingPlaytestTitleIngestionBuilder.cs`
2. **Contract** computes `SourceId => ServicingContentId ?? ContentId` = the servicing id (IL-verified, read-only).
3. **CTIN** ingests/resolves the asset under `storeAsset.SourceId` (servicing — unchanged behavior), and stores `AssetProperties.ContentId = storeAsset.ContentId` (real). — `AssetIngestionExtensions.cs:37`, `PlaytestTitleIngestionWorkflow.cs:88,145`
4. **CTDR (distribution)** — **install** commands (`InstallOrUpdateMsixvcContentByUrlV1`) use the real `ContentId` → resolves the MSIXVC by the right id → fixes `ERROR_NOT_FOUND` at `CustomActionAppxPayload.cs:88`. — PR 16137972
5. **Sessions (provisioning)** — provisioning commands use the explicit real `ContentId` (same split, provisioning stage). — PR 16140301

### ⚠️ Deploy ordering

**CTIN 16129840 must deploy to prod before (or with) the Xbet PR.** Pre-16129840 CTIN uses `storeAsset.ContentId` directly as the asset SourceId; if Xbet ships first, the asset SourceId flips servicing→real and breaks the currently-working asset resolution. Order: **StoreClient → CTIN → Xbet.** (Deploys otherwise paused until the Monday window.)

## Outcome / next steps

- ✅ Install + provisioning now succeed on the PC server (the `ERROR_NOT_FOUND` is gone).
- 🔴 **Next blocker:** the cloud launch times out (server-side GRTS build issue) — tracked in [`pc-playtest-launch-timeout-grts.md`](./pc-playtest-launch-timeout-grts.md).
- Land the remaining Sessions PR (16140301) and let all five deploy; then a fresh playtest gets the right `contentId` end-to-end automatically.

## References

- Timi debugging session `Call with Timi Bolaji` (2026-07-09) — stub → real-build → fresh-server → identifier theory.
- [`../Explanations/pc-playtest-streaming-allocation-e2e.md`](../Explanations/pc-playtest-streaming-allocation-e2e.md) — allocation + staging chain (resolved up to the install step).
- [`pc-playtest-default-allocation-pools.md`](./pc-playtest-default-allocation-pools.md) — the prior (resolved) allocation-pool 400 blocker.
