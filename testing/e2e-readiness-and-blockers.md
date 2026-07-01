# E2E readiness — will the streaming playtest flow work?

Consolidated from a deep end-to-end review (2026-07-01) after PR 15834601 (xPlaytest streaming ingestion) merged. **This is the "before you run E2E" gate.**

## Verdict

**The merged XBET backend path is correctly wired, but the full E2E is not yet reliably runnable** — the remaining blockers are **external** (deploy/auth/env/UI), not in the merged payload-builder/workflow code.

**Critical path:** pilot seller gate → PlayTest publish → XORc title-id resolution → XBET workflow schedules SAGE ingestion → CTIN `PlaytestTitleIngestionWorkflow` → asset ingestion / configure offering → PC install-readiness poll → readiness/status → launch link → Bayside stream.

**Single most likely first break:** **xPackage → SAGE → CTIN cross-tenant auth/route** — if the SAGE route and the CTIN bare-GUID audience fix (PR 15996626) aren't merged **and deployed** in the target env, the POST 401s before ingestion starts.

## CRITICAL blockers (block E2E)

> **UPDATE (2026-07-01, later):** The two gating cross-tenant PRs are now **MERGED**, and the pilot backend path is deployed:
> - **SAGE routes `15829639`** — merged to `main` (merge commit `d4b0808a42`, 17:04).
> - **CTIN bare-GUID audience fix `15996626`** — merged to `main` (merge commit `a16f6f325e`, 16:04).
> - **PlayTest** deployed from `main` (build `PlayTest_K8S_20260701.1` @ `aea0776aad`, which includes the streaming merge `9b0e1c5`); **XPackageWorkflow** deployed `9b0e1c5` earlier at 05:51.
>
> So blocker #1 below is **resolved**; the remaining items (2–7) are the current gates. Everything else on the path was already merged: CTIN CrossTenantS2S gate `15905881`, CTIN workflow `15800964`, CTIN PC-polling `15896502`, CTIN resolution `15983599`, XORc title-id `15894506`, partner-registry SUG `15949594`, data.partnerregistry SUG defs + quota `15965750`/`15965763`/`15966616`.

1. ~~**Cross-tenant S2S + SAGE route.**~~ ✅ **RESOLVED** — SAGE `15829639` + CTIN `15996626` merged and deployed (see update above). Still worth decoding a live token once to confirm `aud == <bare CTIN Green app id>` and `appid` is allow-listed.
2. **Signed-out / cached content leak.** Signed-out Garrison deep link still showed playtest content. Must fix server-side no-leak + cache scoping + login-first gate before any pilot share-link test. Refs: `Blockers/playtest-content-leak-signed-out.md`, `Playtest-UI-Meeting-Karla-Kush.md`.
3. **PC readiness polls before offering attach is live.** CTIN can start the PC Orchestrator poll before the Partner Registry offering PR is merged/propagated → no install triggered, 6h timeout vs ~48h approval. Gate polling on offering merge/propagation, or split "approval wait" from "server install wait." Refs: `PC-Polling-Status.md` (B5b), `FuturePlans/pc-install-readiness-polling-implementation.md`.

## HIGH risks

4. **Test env region/quota mismatch.** Test quota is WESTUS3 but offering targets WESTUS2/WestEurope; Int aligns with WESTUS2. **Run first E2E in Int**, or reroute Test to WESTUS3. Ref: `PC-Polling-Status.md`.
5. **Launch link before title is live.** XProduct is async (~85–90% status accuracy) → tester can 404. Don't surface/enable the launch link until CTIN terminal success + offering/XProduct liveness. Ref: `FuturePlans/launch-link-and-status-accuracy.md`.
6. **Expiration cap mismatch.** Code clamps **7 days**; project decision is **30**. Either land the 30-day change or test with ≤7-day playtests and document the pilot limitation. Refs: `Documentation/xbet-15834601-spec-deltas.md`, `FuturePlans/expiration-cap-30-days.md`, `StreamingPlaytestTitleIngestionBuilder.cs` (`MaxExpirationWindow`).
7. **Title-id resolution is fail-fast + env-sensitive.** Pilot publish throws if XORc is unreachable or the product isn't XBL-configured. Preflight the pilot product with `GetXboxServicesConfigAsync` and confirm nonzero `TitleId`. Ref: `Blockers/xbox-live-title-id.md`, `testing/pc-video-graphics-stream-test.md`.

## Deferred pilot risks (merged code follow-ups)
See `FuturePlans/xbet-15834601-rubber-duck-followups.md`: transient-XORc non-blocking (#1), poll-timeout basis (#2), crash-safe scheduling (#3), multi-package selection (#4), extend builder `Validate` (#5, do before E2E for cleaner failures).

## Pre-E2E checklist
1. Merge **and deploy** (CI/CD, not PR pipeline): SAGE route, CTIN `CrossTenantS2S` gate, CTIN bare-GUID audience fix.
2. Confirm the xPackage token: Green tenant, `aud` = bare CTIN app id, `appid` = xPackage caller, allow-listed.
3. Run as pilot seller **65050620**.
4. Confirm the pilot product has a nonzero Xbox Live `TitleId` via XORc in the target env.
5. Prefer **Int** first, or fix the Test WESTUS3 ↔ WESTUS2 region mismatch.
6. Verify `PC_PLAYTEST` SUG definition + dynamic-config quota + IncludePredictions behavior.
7. Ensure the offering attach is merged/live **before** the PC install-readiness timeout starts.
8. Don't expose the launch link until CTIN terminal success + XProduct/offering live signal.
9. Fix/verify signed-out and non-member no-leak before any pilot share-link test.
10. Keep test playtest expiry **≤7 days** unless the 30-day backend/UX change has landed.
11. (Recommended) Do rubber-duck follow-up **#5** (extend builder `Validate`) so a bad payload fails locally, not as an opaque SAGE 400.

## Fastest way to smoke-test the ingestion half now
Bypass the Xbet publish and POST the payload directly via the DevApi ingestion page (PR 15876080) using `testing/devapi-xsth-pc-polling.json` (fresh `PlaytestId`, future `ExpirationTime`). Watch the CTIN job through `ValidateParameters → TriggerAssetIngestion → PollAssetIngestion → CreatePackage → ConfigureOffering → PollFirstPCInstall → ConcludeWorkflow`. See `testing/README.md`.

## Source
Deep review of the tracking hub + merged `Xbox.Xbet.Service` PR 15834601, 2026-07-01.
