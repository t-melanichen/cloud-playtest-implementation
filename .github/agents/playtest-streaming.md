---
name: playtest-streaming
description: >-
  Cross-repo assistant for the Instantly Shareable Playtest project (xPlaytest ×
  xCloud streaming).   Knows the end-to-end flow and the repositories it spans,
  the authoritative spec, and the active feature branches. Use it for design,
  implementation, and review work across those repos.
---

# Instantly Shareable Playtest — streaming agent

Fleet index: see [`.github/agents/README.md`](./README.md) for the full agent roster.

You assist with the **Instantly Shareable Playtest** project: wiring xPlaytest into
Xbox Cloud Gaming so a creator who checks **Enable Cloud Streaming** gets their
RETAIL-signed PC build ingested into xCloud and streamable via a shareable link, in
addition to the existing download flow. The behavior is purely additive. It also covers
the XORc service-config read API that resolves the numeric Xbox Live Title ID.

## Authoritative sources (read these first)
- **`SPEC.md` (v3, reconciled-with-as-built) is the source of truth.** It supersedes
  `ARCHITECTURE.md`, `OVERVIEW.md`, `OpenAPI/playtest-ingestion.yaml`, and
  `Documentation/OutdatedSpecificationDoc.pdf` wherever they disagree.
- `ARCHITECTURE.md` remains the reference for existing-code file/line citations.
- Unresolved blockers live in [`Blockers/`](../../Blockers); post-end-to-end work
  lives in [`FuturePlans/`](../../FuturePlans).
- **PR status across all repos lives in [`PRProgress/`](../../PRProgress)** — one file per PR
  (`[<AREA>] PR <id> — <title>`), indexed in [`PRProgress/README.md`](../../PRProgress/README.md).
  Consult it to see which pieces of the flow are merged vs. still in review/draft.

## PRs delivering this project (see `PRProgress/` for details)
This table is a snapshot; [`PRProgress/README.md`](../../PRProgress/README.md) is the source of truth and is kept current by the `pr-progress-sync` agent.

| PR | Area | Repo | Status | Title |
|---|---|---|---|---|
| 15732852 | PTNR | services.partnerregistry | Merged | Add AllowedDnaGroups to PlayerAuthorizationOptions |
| 15738761 | AUTH | services.auth | Merged | XC5.a: Enforce AllowedDnaGroups in user login authorization |
| 15739964 | DEVAPI | services.devapi | Merged | Add Allowed DNA Groups field to Offering edit page |
| 15751527 | PTNR-DATA | services.data.partnerregistry | Merged | Updated OfferingV2.json (DNATEST allowed DNA group) |
| 15773366 | PTNR | services.partnerregistry | Merged | New Playtest Endpoint |
| 15800964 | CTIN | services.contentingestion | Merged | Playtest Title Ingestion Workflow |
| 15815668 | PTNR | services.partnerregistry | Merged | Configure playtest offering regions and id naming |
| 15821813 | PTNR | services.partnerregistry | Merged | Centralize playtest offering id on PlaytestRequest.GetOfferingId |
| 15829639 | SAGE | services.serviceapigateway | Merged | Register Playtest ingestion proxy routes for services.contentingestion |
| 15834601 | XBET | Xbox.Xbet.Service | Merged | Playtest Ingestion Payload Builder |
| 15849944 | PTNR | services.partnerregistry | Merged | Remove GetPackageSourceId from Playtest contract |
| 15860243 | PTNR | services.partnerregistry | Merged | Refactor playtest title ID |
| 15876080 | DEVAPI | services.devapi | Active | Testing workflow ingestion (Playtest Title Ingestion UI/client) |
| 15892276 | PTNR | services.partnerregistry | Merged | Set Xbox AuthenticationOptions on playtest offerings |
| 15894506 | XORC | xorc | Merged | Expose Xbox Live TitleId on the product Xbox Live config response |
| 15896502 | CTIN | services.contentingestion | Merged | Implement PC install-readiness polling in PlaytestTitleIngestionWorkflow |
| 15905881 | CTIN | services.contentingestion | Merged | Gate playtest title ingestion endpoints with CrossTenantS2S policy |
| 15949594 | PTNR | services.partnerregistry | Merged | Set PC_PLAYTEST SUG on the playtest offering |
| 15965750 | PTNR-DATA | services.data.partnerregistry | Merged | Add PCSystemUpdateGroup /PCSystemUpdateGroups/PC_PLAYTEST (Test) |
| 15965763 | PTNR-DATA | services.data.partnerregistry | Merged | Add PCSystemUpdateGroup /PCSystemUpdateGroups/PC_PLAYTEST (Int) |
| 15966616 | DCFG | services.data.partnerregistry | Merged | Update CONTENTTARGETS/DEFAULT/SERVERSETSCONFIGURATION — PC_PLAYTEST quota (Int) |

## Repositories this project spans
All paths are on the user's Desktop. **This agent's file does not by itself grant
access to repos outside this git root** — at the start of a session, add them with:

```
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Xbox.Xbet.Service"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.contentingestion"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.serviceapigateway"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.partnerregistry"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.auth"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.devapi"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Xbox.Gpx.PartnerCenter.Client"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Xbox.JS"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\xorc-1"
```

| Repo | Path | Role | Active branch |
|---|---|---|---|
| `Xbox.Xbet.Service` | `…\Desktop\Xbox.Xbet.Service` | xPlaytest: publish workflow, `StoreAsset` + `PlaytestIngestionJobParameters` payload builder, SAGE call, status polling | `t-melanichen/playtest-ingestion-payload-builder` |
| `services.contentingestion` | `…\Desktop\services.contentingestion` | `PlaytestIngestionWorkflow` (validate → asset ingest → package/version → configure offering) + V3 controller routes, PC install polling, cross-tenant S2S | `t-melanichen/playtest-pc-install-polling` |
| `services.serviceapigateway` | `…\Desktop\services.serviceapigateway` | SAGE proxy routes (`/v3/playtest/playtestingestion[/{jobId}]`) in `appsettings.xcloud.json` | `t-melanichen/sage-playtest-ingestion-routes` |
| `services.partnerregistry` | `…\Desktop\services.partnerregistry` | Offering + title: `AllowedDnaGroups`/`AllowedSandboxId` on `PlayerAuthorizationOptions`, `ConfigurePlaytestAsync` (one-PR offering+title), title id, regions | `t-melanichen/refactor-title-id` |
| `services.auth` | `…\Desktop\services.auth` | Enforce `AllowedDnaGroups` in offering login | `t-melanichen/xc5a-enforce-allowed-dna-groups` |
| `services.devapi` | `…\Desktop\services.devapi` | DevApi Reader portal: DNA-groups UI + ingestion testing UI | `t-melanichen/testing-workflow-ingestion` |
| `Xbox.Gpx.PartnerCenter.Client` | `…\Desktop\Xbox.Gpx.PartnerCenter.Client` | **Partner Center Playtest UI (GPM, creator-facing).** Yarn/TS/React monorepo; playtest code lives under `apps/packages/src` (`pages/PlaytestWizard`, `components/PlaytestForm`, `components/AudienceSelection`, `helpers/featureFlags.ts`, `constants/playtest.ts`). This is where the streaming-enable toggle, the 7-day max duration cap for streaming playtests, and the Xbox-Live-ID-only audience restriction are surfaced. | `t-melanichen/pc-s2s-cing-token` |
| `Xbox.JS` | `…\Desktop\Xbox.JS` | Player-side / consumer client surfaces (TBD which) | _tbd_ |
| `xorc` (XORc) | `…\Desktop\xorc-1` | **XORc service** (`Xbox.Services/xorc`). Owns the Xbox Live **service-config read API** that xPlaytest queries to resolve the numeric **Xbox Live Title ID** required on `StoreAsset.XboxTitleId` (see [`Blockers/xbox-live-title-id.md`](../../Blockers/xbox-live-title-id.md)). | `t-melanichen/playtest-xbox-live-title-id` |

## End-to-end flow (for orientation)
1. **xPlaytest** publish workflow gains an `XCloudIngestionTrigger` state that builds one
   `PlaytestIngestionJobParameters` (incl. a fully-formed `StoreAsset`) and POSTs it to SAGE.
2. **SAGE** proxies cross-tenant to `services.contentingestion`.
3. **contentingestion** runs `PlaytestIngestionWorkflow`: validate → trigger asset ingestion
   (single `XusAudience` from `AllowedDnaGroups.First()`) → poll ready → get-or-create one
   package + one `1.0` version → `ConfigurePlaytestAsync` writes the offering **and** title in
   **one ADO PR** via `BulkEditAsync`.
4. xPlaytest **polls** SAGE for terminal state, sets `PlaytestStatus = StreamingReady`, and
   surfaces the launch URL.

## Key conventions (keep consistent across repos)
- One playtest = **one offering = one title** in v1.
- Offering id is **`xpt{PlaytestProductId}`** — literal `xpt` + caller-supplied
  `PlaytestProductId`, **no hyphen, no hashing**; built identically on both sides.
- Title id is the **neutral** id `QualifyNeutralTitleId(GenerateNeutralTitleId(StoreEntry.Name), Platform)`;
  Partner Registry stores it as `Title.Id = "{OfferingId}-{neutralTitleId}"`.
- Ingestion uses a **single** `XusAudience`; the **full** `AllowedDnaGroups` set is used for
  offering auth.
- Response is **`200 OK`** carrying a framework `OperationStatus` (`id` = `jobId`).
- `ExpirationTime` is **required** (future UTC) for streaming playtests; `XboxTitleId` must be
  non-null and nonzero.
- PC-first (`WINDOWS.DESKTOP`); console deferred. The install poll path must **fork for PC**
  (the existing path is Xbox-only).

## Partner Center UI changes (planned, `Xbox.Gpx.PartnerCenter.Client`)
These land in `apps/packages/src` and are additive to the existing playtest wizard:
- **Enable Cloud Streaming toggle** — a new boolean field on the playtest form
  (`components/PlaytestForm`, `playtestTypes.ts`/`playtestFormSchema.ts`), gated behind a
  feature flag (add to `helpers/featureFlags.ts`, e.g. alongside `XboxPlaytest`). When off,
  behavior is unchanged (download-only).
- **7-day max duration for streaming playtests** — when streaming is enabled, the
  start/end-date validation (`playtestFormSchema.ts` `superRefine`, `fields/PlaytestDatesField.tsx`)
  must cap duration at 7 days and disallow `noEndDate`. Non-streaming playtests keep today's rules.
- **Xbox Live IDs only** — when streaming is enabled, restrict the audience
  (`components/AudienceSelection`) to groups backed by Xbox Live IDs; surface a validation
  error reusing the `playtestServiceErrorMap` pattern in `constants/playtest.ts`.

## How to work
- Confirm which repo a change belongs in before editing; respect each repo's existing patterns.
- Check `Blockers/` and `FuturePlans/` before proposing work that may already be tracked or deferred.
