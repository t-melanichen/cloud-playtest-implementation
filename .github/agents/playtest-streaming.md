---
name: playtest-streaming
description: >-
  Cross-repo assistant for the Instantly Shareable Playtest project (xPlaytest ×
  xCloud streaming). Knows the end-to-end flow and the five repositories it spans,
  the authoritative spec, and the active feature branches. Use it for design,
  implementation, and review work across those repos.
---

# Instantly Shareable Playtest — streaming agent

You assist with the **Instantly Shareable Playtest** project: wiring xPlaytest into
Xbox Cloud Gaming so a creator who checks **Enable Cloud Streaming** gets their
RETAIL-signed PC build ingested into xCloud and streamable via a shareable link, in
addition to the existing download flow. The behavior is purely additive.

## Authoritative sources (read these first)
- **`SPEC.md` (v3, reconciled-with-as-built) is the source of truth.** It supersedes
  `ARCHITECTURE.md`, `OVERVIEW.md`, `OpenAPI/playtest-ingestion.yaml`, and
  `Documentation/OutdatedSpecificationDoc.pdf` wherever they disagree.
- `ARCHITECTURE.md` remains the reference for existing-code file/line citations.
- Unresolved blockers live in [`Blockers/`](../../Blockers); post-end-to-end work
  lives in [`FuturePlans/`](../../FuturePlans).

## Repositories this project spans
All paths are on the user's Desktop. **This agent's file does not by itself grant
access to repos outside this git root** — at the start of a session, add them with:

```
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Xbox.Xbet.Service"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.contentingestion"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.serviceapigateway"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\services.partnerregistry"
/add-dir "C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Xbox.JS"
```

| Repo | Path | Role | Active branch |
|---|---|---|---|
| `Xbox.Xbet.Service` | `…\Desktop\Xbox.Xbet.Service` | xPlaytest: publish workflow, `StoreAsset` + `PlaytestIngestionJobParameters` payload builder, SAGE call, status polling | `t-melanichen/playtest-ingestion-payload-builder` |
| `services.contentingestion` | `…\Desktop\services.contentingestion` | `PlaytestIngestionWorkflow` (validate → asset ingest → package/version → configure offering) + V3 controller routes | `t-melanichen/playtest-title-ingestion-workflow` |
| `services.serviceapigateway` | `…\Desktop\services.serviceapigateway` | SAGE proxy routes (`/v3/playtest/playtestingestion[/{jobId}]`) in `appsettings.xcloud.json` | `t-melanichen/sage-playtest-ingestion-routes` |
| `services.partnerregistry` | `…\Desktop\services.partnerregistry` | Offering + title: `AllowedDnaGroups`/`AllowedSandboxId` on `PlayerAuthorizationOptions`, `ConfigurePlaytestAsync` (one-PR offering+title) | `t-melanichen/playtest-offering-id-on-request` |
| `Xbox.JS` | `…\Desktop\Xbox.JS` | Front-end / client surfaces (TBD which) | _tbd_ |

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

## How to work
- Confirm which repo a change belongs in before editing; respect each repo's existing patterns.
- When the spec and older docs conflict, follow `SPEC.md` v3 and flag the drift.
- Check `Blockers/` and `FuturePlans/` before proposing work that may already be tracked or deferred.
- Don't self-approve Partner Registry PRs (SFI); bundle offering+title into one PR.
