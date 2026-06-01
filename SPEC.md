# Instantly Shareable Playtest — Implementation Spec

**Status:** Draft v2, post May 29 2026 alignment meeting + June 3 follow-up sync
**Owner:** Melanie Chen (xPlaytest intern)
**Reviewers:** Brian Bowman (xPlaytest), Anthony Keller (xPlaytest), David Kushmerick (xPlaytest), Timi Bolaji (xCloud), Jack Heuberger (xCloud), Aditya Toney (xCloud)
**Companion docs:** [`ARCHITECTURE.md`](./ARCHITECTURE.md) (code-grounded), [`DIAGRAMS.md`](./DIAGRAMS.md) (visual reference), [`openapi/playtest-ingestion.yaml`](./openapi/playtest-ingestion.yaml), [`ado/ado-tasks.md`](./ado/ado-tasks.md)
**Source inputs:** `Documentation/XD-Chen Melanie-Instantly Shareable Playtest.pdf` (formal project description), `Documentation/Xbox Playtest - Partner Intro Deck -- May 2026.pdf`, `Transcripts/Sync1.docx` (May 29 group sync, authoritative), `Transcripts/Jack.docx` / `Jack2.docx`, `Transcripts/Timi.docx`, `Documentation/Instantly Shareable Playtest - Gaming Intern Project Sync 2026-06-03.pdf` (June 3 sync agenda + AI-generated summary of May 29), `Files/` (real `TitleIngestion.cs`, `TitleIngestionWorker.cs`, `ProductIngestionWorkflow.cs`, and an actual XProduct document JSON sample).

> This document is the **dev spec** for cross-team alignment. It captures *what* we're building, *who owns what*, *why* the contract looks the way it does, and *how long* each piece should take. The deeper *how* (file-level code citations, validators, exact line numbers) lives in `ARCHITECTURE.md`.

> **Divergences from `ARCHITECTURE.md`:** SPEC.md is the **newer** of the two docs and supersedes ARCHITECTURE.md on the following points: (a) `TitleId` is distinct from `OfferingId` — see §5.3; (b) the external SAGE path is `/playtest/ingestion` (no `/v3` prefix) — see §6 routing note; (c) for v1, `AumID` ships with a constant default rather than a plumbed `ApplicationId` — see §8 + §7; (d) `ExpirationTime` is **required** when `IsStreamingEnabled = true` (per June 3 sync) — see §9 Q3; (e) XC6 must fork the install-poll path for PC because `TitleIngestionWorker.PollFirstInstallAsync` hardcodes Xbox allocator parameters — see §3.6 risk callout. The cross-tenant Green→PME item in ARCHITECTURE.md §7 P0 list is **deferred** out of summer scope — see Known Blockers §7 below. ARCHITECTURE.md remains the source of truth for file/line citations and the existing-code surface area; treat any prose contradiction as resolved in SPEC.md's favor unless ARCHITECTURE.md is updated more recently.

---

## Table of Contents

1. [What We Are Building](#1-what-we-are-building)
2. [End-to-End Flow](#2-end-to-end-flow)
3. [Design Decisions & Tradeoffs](#3-design-decisions--tradeoffs) ← *new section*
4. [Team Responsibilities](#4-team-responsibilities) (with SWAGs + parallelization)
5. [Data Contract](#5-data-contract)
6. [REST API Contract](#6-rest-api-contract) ← *new section*
7. [Known Blockers](#7-known-blockers)
8. [Resolved Decisions](#8-resolved-decisions)
9. [Open Questions & Recommendations](#9-open-questions--recommendations)
10. [Success Criteria (P0)](#10-success-criteria-p0)
11. [Milestones & Foundational Demo](#11-milestones--foundational-demo)

---

## 1. What We Are Building

Today, xPlaytest lets game creators distribute private pre-release builds to testers as downloadable installs through Garrison. Modern games are hundreds of gigabytes — downloads are slow, hardware provisioning does not scale, and shipping physical devices to testers risks unreleased code leaking.

**The Instantly Shareable Playtest project wires xPlaytest into Xbox Cloud Gaming's streaming pipeline.** When a creator publishes a playtest with the **Enable Cloud Streaming** option checked, their RETAIL-signed PC build is ingested into xCloud and becomes streamable to authorized testers via a one-click shareable link — **in addition to** still being available for download.

This is purely additive. Creators who do not opt in get the existing download-only flow. Creators who do opt in get both download and streaming for the same playtest.

---

## 2. End-to-End Flow

A streaming-enabled playtest goes through four phases. The first phase runs entirely on xPlaytest; the middle two run on xCloud; the fourth is a status reconciliation across both.

| # | Phase | What Happens | Owner |
|---|---|---|---|
| 1 | **Publish Trigger** | Creator clicks **Publish** in Partner Center. `PublishPlaytest` validates the playtest and hands off to the existing `XPackagePlaytestPublishWorkflow`. The workflow runs the existing state machine (`FetchingContentIds` → `StartingContentSubmissionJob` → `PollingContentSubmissionJob` → `PlaytestProductCreation`). We **insert a new state**, `XCloudIngestionTrigger`, immediately after `PlaytestProductCreation` and before `SuccessCompletion`. This is the right integration point because the workflow already calls cross-system services (XProduct, SUCU, GMS) and is built for long-running, retriable execution. | xPlaytest |
| 2 | **xCloud Handoff** | The new state builds a single `PlaytestIngestionJobParameters` payload (see §5) that combines the resolved DNA group IDs, expiry, sandbox, and a fully-formed `StoreAsset` derived from data the workflow has already resolved for XProduct. It POSTs the payload to SAGE, which proxies the call cross-tenant to `services.contentingestion`. The response is `202 Accepted` with a `jobId`. **Ingestion failure does not block the download playtest from publishing** — streaming is best-effort. | xPlaytest → xCloud |
| 3 | **xCloud Ingestion Workflow** | A new `PlaytestTitleIngestionWorkflow` runs inside `services.contentingestion`. It (a) validates inbound parameters, (b) chains the existing `AssetIngestionWorkflow` using the supplied `StoreAsset` (no BigCat lookup), (c) upserts a playtest-specific offering `xpt-{shortId}` in Partner Registry with `AllowedDnaGroups` + `AllowedSandboxId` + `ExpirationTime`, (d) attaches the title, and (e) polls the install pipeline for capacity. The offering write + title attach are combined into a single ADO PR via `BulkEditAsync` to halve the SFI approval cost. | xCloud |
| 4 | **Streamable** | When the xCloud workflow reaches a terminal state (`Streamable` / `Failed` / `InstallNotFound`), xPlaytest learns about it by **polling** the SAGE status endpoint with the `jobId` (exponential backoff — see §3.1). On `Streamable`, xPlaytest sets `PlaytestStatus = StreamingReady` (new enum value) and surfaces the launch URL `https://play.xbox.com/play/launch/{productId}?offeringId=xpt-{id}` in Partner Center. | xCloud → xPlaytest |

> **Detailed sequence diagram, state machine, and file-by-file insertion points are in `ARCHITECTURE.md` §2–§3.**

---

## 3. Design Decisions & Tradeoffs

Every important decision below was either confirmed in the May 29 meeting or is a recommendation grounded in the existing code in the four backing services (see `ARCHITECTURE.md` for code citations).

### 3.1 Terminal-state delivery: polling, not callback (for v1)

**Decision:** xPlaytest learns about ingestion completion by polling `GET /playtest/ingestion/{jobId}` on SAGE.

**Rationale:**
- SAGE today is a **request/response proxy** (`ProxyController.cs:73-155`). There is no callback/event-hub orchestration layer. Adding one is a non-trivial gateway change that does not fit summer scope.
- xPlaytest already polls inside its own workflow (`XPackagePlaytestPublishWorkflow.cs:329-383` polls Content Submission). The pattern is well-understood and we reuse the existing workflow framework primitives.
- `services.contentingestion` already exposes job status through `WorkflowsControllerV3`; SAGE just needs to forward.

**Polling strategy:** Exponential backoff. Initial delay 30 s, doubled each attempt, capped at 5 min. Foreground wall-clock deadline 60 min — beyond that, the publish workflow exits and a **background reconciliation job** takes over.

| Attempt | Wait |
|---|---|
| 1 | 30 s |
| 2 | 60 s |
| 3 | 2 min |
| 4–N | 5 min (cap) |
| Foreground deadline | 60 min |
| Background reconciliation | 15 min interval, 24 h cap |

**Why a background reconciliation pass:** Asset ingestion can legitimately run longer than 60 minutes (Timi flagged this risk in the meeting). If we drop the `jobId` on the publish-workflow timeout, the offering may go live in xCloud minutes later with no `StreamingReady` transition on the xPlaytest side. The reconciliation job (a new singleton timer in xPlaytest, owned by PT5.d in `ado/ado-tasks.md`) re-reads the persisted `XCloudIngestionJobId` from `PublishedPlaytestEntity` and continues polling until the workflow terminates. If we hit the 24 h cap without a terminal state, an operator alert fires and the entry is manually triaged.

**Retry semantics:** If xPlaytest needs to retry a publish for any reason, the workflow first calls `POST /playtest/ingestion` again. xCloud returns either `202` (new job) or `409 Conflict` whose body includes the in-flight `jobId` and `statusUrl` (see [`openapi/playtest-ingestion.yaml`](./openapi/playtest-ingestion.yaml) `JobConflict` schema). The xPlaytest client treats `409` as "use the existing job" rather than failing the publish.

**Tradeoff accepted:** Polling adds load to SAGE and `services.contentingestion` and delays the "playtest ready" UX by up to 5 min in the worst case. The alternative (callbacks) requires a cross-tenant message bus story that the GSS platform team has already flagged as on their roadmap but explicitly *not* for this summer (Jack, meeting 27:38). Revisit in v1.1 once cross-tenant messaging exists.

### 3.2 Auth gate at the offering level (not at title level)

**Decision:** Playtest offerings are **private**. Access is gated by a new `AllowedDnaGroups` field on the offering's `PlayerAuthorizationOptions`. The title inside the offering bypasses the per-title entitlement check.

**Rationale:**
- The alternative (public offering, gate at title level via package flighting) requires entitlement plumbing that complicates the developer experience — creators would need to "buy" their own game to test.
- Gating at the offering level gives us a single, firm `GsToken.DnaGroups` check at offering entry, after which any title in that offering is reachable.
- This is the pattern TestX already uses successfully (Jack, meeting comment JH29).
- One-offering-per-playtest (§3.5) means there is no risk of accidentally exposing an unrelated title.

**Tradeoff accepted:** Skipping the per-title entitlement check is a slight relaxation of defense-in-depth. The mitigation is that the offering is private and DNA-group-locked, and the playtest title is not catalogued anywhere a non-tester could find it.

**External dependency:** The actual `GsToken.DnaGroups` ↔ `AllowedDnaGroups` enforcement lives in the streaming-token / Bayside path (XC5). Partner Registry only holds the **data** for the allow-list. Adding the data field without the enforcement is not enough — both halves of XC4 + XC5 must land for the auth model to work.

### 3.3 XC6: pick one DNA group as the effective "flight" for install

**Decision:** When the xCloud install pipeline (SUCU/allocator) needs a single flight identifier to resolve the package version, the workflow passes the **lexicographically smallest DNA group GUID** from `AllowedDnaGroups`.

**Rationale:**
- A playtest can have multiple DNA groups. Each materializes in SUCU as its own "flight."
- All DNA groups for a single playtest point to **the same effective build version** — there is no per-group divergence in this scenario.
- SUCU/the install pipeline expects exactly one flight ID at the lookup site (`TitleIngestionWorker.cs:197-225`).
- A deterministic choice (lex-smallest) means re-runs of the workflow with the same input pick the same flight, which is helpful for idempotency and debugging.

> **Caveat — flight selection is not "sticky":** "Lex-smallest of the current set" is computed at every resolve. If the audience changes such that a *new* GUID is added that sorts lower than the previous smallest (or the previous smallest is removed), the resolved flight id *will* change for subsequent resolves. This is acceptable v1 behavior because the install pipeline addresses flights by GUID alone and there is no notion of "first-chosen flight." A sticky model was considered but rejected for v1 — it would require new per-playtest state on the install side that does not exist today. XC6.b emits a `XCloudFlightSelectionFlipped` telemetry event whenever the resolved flight id changes between consecutive resolves for the same playtest, so the install team can detect churn.

**This is an install-time lookup rule only.** It does NOT change audience auth — XC5 still checks the user's GsToken against the full `AllowedDnaGroups` set.

**Tradeoff accepted:** If the install pipeline ever needed per-DNA-group version divergence, this rule would have to change. That is not a near-term scenario; the workaround is contained inside `PlaytestTitleIngestionWorkflow` and easy to revisit.

**Action item:** XC6 includes an audit pass against the SUCU/allocator client to confirm it tolerates a DNA-group GUID rather than a "real" GA flight ID.

### 3.4 Streaming is an opt-in addition to the standard playtest

**Decision:** **And, not or.** Publishing a streaming-enabled playtest also produces a downloadable playtest in the existing flow. The streaming part is gated behind an "Enable Cloud Streaming" checkbox at publish time.

**Rationale (from meeting, David K. 9:29 + Anthony K. 10:01):** Treating the two as mutually exclusive would surprise creators who already rely on the download flow and would force a hard cut-over. Layering streaming on top keeps the existing behavior unchanged for everyone who doesn't opt in, and gives streaming users the maximum surface to share their build.

**Tradeoff accepted:** xCloud ingestion runs even when nobody plans to stream the build, costing capacity. Mitigated because (a) the toggle is explicit, (b) ingestion failure does not block the download flow, and (c) we can add a "publish for download only" path later if streaming-without-download proves common.

### 3.5 One playtest = one title = one offering (locked for v1)

**Decision:** Each published playtest gets exactly one xCloud offering with exactly one title. The offering id is `xpt-{shortId(PlaytestId)}`.

**Rationale (from meeting, Brian B. 21:06 / 26:18; Timi 21:22; David K. 22:14):**
- Each playtest can target a different audience (different DNA group set). Offering ↔ audience must be 1:1 to keep the auth model crisp.
- Timi's preference long-term is to cluster a single developer's playtests into one offering to reduce catalog noise, but explicitly *not* for this project's scope.
- Anthony confirmed each playtest is already its own document in XProduct, so a 1:1 mapping on the xCloud side matches the upstream identity model.
- Anthony's "library tile" concern (each playtest appears as its own tile) is preserved with 1:1.

**Tradeoff accepted:** A developer with many active playtests creates many offerings — Timi's clustering instinct will not be served. If this becomes a catalog noise problem, the offering id scheme is stable enough to evolve later. The xCloud client could implement a "log into all my private offerings" flow without changing the data model.

### 3.6 PC-first, Xbox console deferred

**Decision:** v1 scope = **PC builds only.**

**Rationale (from meeting, Anthony K. 16:21 + Brian B. 16:44):**
- The data path is already set up for PC (`WINDOWS.DESKTOP` platform constant, PC-only `ContainsMSIXVCByDeviceFamily`).
- PC requires `AumID` and `PackageFamilyName`, both either available or sourceable.
- Console adds Xbox-specific Title ID and package handling that we don't need for the foundational integration.

**AumID resolution path:** Timi confirmed (Sync1 transcript ~20:11): *"I just took a quick look at the server code that uses [aumid] only for upload and it's just a login thing. It's just telemetry. So I can just put a default value there for now."* A constant default is acceptable in v1. We will still plumb the real `ApplicationId` from the AppX manifest as a follow-up in v1.1 to be principled about it, but v1 is unblocked.

**Risk callout — PC support in the install poll path:** The existing `TitleIngestionWorker.PollFirstInstallAsync` (`TitleIngestionWorker.cs:197-225`) hardcodes Xbox-specific allocator parameters:

```csharp
ServerFilter serverFilter = new()
{
    Region = this.environmentProvider.IsProd() ? GsRegionName.WestUs2 : GsRegionName.WestEurope,
    PoolId = ... ? "XBOX_CERT" : "XBOX_MAIN",
    SystemUpdateGroup = SystemUpdateGroup.GA,
    ServerType = ServerType.XboxV3SeriesS,  // ← Xbox-only
    LocalPackageId = targetInstallId
};
```

`ServerType.XboxV3SeriesS` and the `XBOX_*` pool ids are console-only. The PC streaming pipeline uses its own pool / server type that this code never references. **XC6 must include an explicit audit + fork of the install poll path so PC playtests pick a PC pool (likely a different `ServerType` value and a PC pool id) before any PC end-to-end test can succeed.** If the PC install path differs more than a per-parameter swap (e.g., entirely different allocator service), XC6 grows in scope and the call site needs a platform-aware branch. This is now tracked as an open item under XC6 in `ado/ado-tasks.md` and as a row in Known Blockers §7.

**Tradeoff accepted:** Xbox users can't stream playtests until v1.1. The plumbing for Xbox is incremental (`XboxLiveTitleId` is already a P0 we need anyway), so adding it later is bounded.

### 3.7 Naming and identifiers — opaque, not human-readable

**Decision:** Offering id is `xpt-{shortId}` (opaque). Title id is `<alphanumOnly(PlaytestName)>{PlaytestGeneratedXProductBigId}` (semi-readable, suffixed for uniqueness).

**Rationale:**
- Offering id must be ≤ 32 chars (`OfferingV2.cs:20-23`). A full GUID is 36 chars; the `xpt-` prefix + GUID would be 40. We hash/truncate to a short id.
- Title id is more visible in some xCloud UX. Timi's convention (meeting comment TB65) is "strip whitespace/special characters from the game's name." Appending the playtest product id gives uniqueness for a developer with multiple playtests sharing the same game name.
- We accept some opacity because mapping schemes that try to be "pretty" would either lose uniqueness or force us to maintain a name-resolution layer.

**Tradeoff documented (per Brian's spec comment):** When a tester or developer sees `xpt-7a3b8f1c…` in any URL or diagnostic, they will not be able to identify the playtest by name. We mitigate by surfacing the friendly playtest name everywhere we control the UX (Partner Center, launch tile), and reserving the opaque id for backend/URL use only.

### 3.8 Bespoke endpoint vs. generic "CreateOfferingFromStoreData"

**Decision:** Bespoke `POST /playtest/ingestion`.

**Rationale (per Brian B. spec comment B35; Jack H. JH36 agrees):**
- A generic "CreateOfferingFromStoreData" surface is the future direction (Jack confirmed the GSS platform team is discussing an orchestration layer on top of their workflow service), but is explicitly out of summer scope.
- The bespoke shape lets us encode playtest-specific defaults (sandbox = RETAIL, isPrivate = true, etc.) on the server side and keep the contract small.
- We do not yet know what the next caller's payload looks like, so designing the generic contract now would be premature.

**Tradeoff accepted:** Future scenarios that resemble playtest may duplicate boilerplate. The bespoke route is small enough that migrating to a generic one later is a controlled refactor.

### 3.9 Cross-tenant S2S strategy

**Short term (v1):** xPlaytest Service (MSFTGreen tenant) → xCloud SAGE (Corp tenant) using the Green→Corp cross-tenant auth scheme being added by PR [#15715445](https://dev.azure.com/microsoft/Xbox/_git/SAGE/pullrequest/15715445).

**Long term:** xCloud is migrating to PME by end of summer. PME does not accept Green callers out of the box. The GSS platform team owns the long-term solution (Jack, meeting 27:38), which is **explicitly not** summer scope.

**Action items:**
- Verify PR #15715445 actually adds Green→Corp (the spec previously had the direction inverted) and ride it.
- Leave a clearly-marked TODO at the xCloud-call site indicating the auth scheme must be revisited when xCloud moves to PME.
- The Greenbelt team solved a similar problem via a proxy in Corp/PME — keep that pattern available as a fallback.

### 3.10 Manual PR approval blocker — mitigations

**Constraint:** Every Partner Registry write creates an ADO PR. SFI policy forbids the caller from self-approving (Jack confirmed in meeting 30:17: "I'll make a PR and then have my SCL approve it, and I got a very angry email saying to never do that again.").

**v1 mitigation:**
1. **Combine offering write + title attach into a single PR** using `BulkEditAsync` (`RegistryProcessor{T}.cs:128-167`). Halves the per-publish manual approval cost from 2 PRs to 1.
2. For the duration of the internship, accept that someone on the xCloud side will approve those PRs out-of-band. This was explicitly accepted by Brian in the meeting (26:18).

**v1.1+ (out of summer scope):**
- Anthony's suggestion (meeting 28:31): if the payload carried the parent product ID, an automated pre-approval could match "this ladders up to something I've already approved" and gate auto-approval that way. This requires an SFI exception and is GSS's call.

### 3.11 API versioning strategy

**Decision (resolves spec comment B42):** Two layers, two conventions.

| Layer | Routes | Versioning convention | Why |
|---|---|---|---|
| **External (xPlaytest → SAGE)** | `POST /playtest/ingestion`, `GET /playtest/ingestion/{jobId}`, `DELETE /playtest/ingestion/by-playtest/{playtestId}` | **Unversioned today; versioned via OpenAPI `info.version` (currently `1.0.0`)** | SAGE's existing public route style is unversioned. We treat the OpenAPI document as the authoritative versioned contract and rely on additive evolution (new optional fields), reserving a future `/v2/playtest/ingestion` prefix only for breaking changes. |
| **Internal (SAGE → `services.contentingestion`)** | `POST /v3/workflows/playtestingestion`, `GET /v3/workflows/playtestingestion/{jobId}`, `DELETE /v3/workflows/playtestingestion/by-playtest/{playtestId}` | **URL-versioned** (`/v3/...`) | Matches the existing `WorkflowsControllerV3` convention. Downstream callers are all in-tenant and already follow this pattern. |

**Evolution rules — both layers:**
- Prefer **additive optional fields** over breaking required ones.
- Document required vs. optional explicitly in `openapi/playtest-ingestion.yaml` (the OpenAPI doc covers the external SAGE layer; the internal layer is documented inline in `services.contentingestion`).
- A breaking change to the external surface bumps to `/v2/playtest/ingestion` and is supported in parallel for at least one xPlaytest release.

**Specifically expected future additions (not breaking):**
- `CallbackUrl` once cross-tenant messaging exists (replaces polling).
- PC-specific config block (Jack noted in JH58 that more PC fields will be needed; the shape is not finalized).
- Per-region or per-pool overrides (when xCloud productizes them).

---

## 4. Team Responsibilities

### 4.1 xPlaytest deliverables

> **Ordering note (resolves spec comment B17):** The table is presented in **call sequence** order. Recommended *execution* order — including what can be parallelized — is in §4.3.

| ID | Task | Notes | SWAG (days) |
|---|---|---|---|
| **PT1** | Integrate xCloud trigger into `XPackagePlaytestPublishWorkflow` | New `XCloudIngestionTriggerState` between `PlaytestProductCreation` and `SuccessCompletion`. Reuses existing workflow orchestration + retry policy. Failure does NOT block publish. Also: streaming-publish validators — (a) requires `PlaytestEndDate` to be set when streaming is on (June 3 sync); (b) seller / title allow-list gate (project-description P0). | 6 |
| **PT2** | Construct `StoreAsset` from Playtest product/package data | By the time the new xCloud-trigger state runs, `PlaytestLifecycleState` is fully populated (`FetchContentIds` resolved `ProductId` / `ContentId` / `PackageFamilyName` / `XProductBigId`; `PollContentSubmission` confirmed they are committed in Partner Center), so most of the payload is a direct projection of in-memory state — no new external calls. Two pieces are *not* present today: (1) **`XboxTitleId` resolver (P0 cross-team blocker)** replacing the `XboxLiveTitleId = string.Empty` hardcode at `PlaytestProductDocumentBuilder.cs:53–70` by reading `alternateIds[XboxTitleId]` from the XProduct response; (2) **`AumID` default-or-resolver** — per Timi the server uses `AumID` only for ingestion telemetry, so the constant `"{packageFamilyName}!App"` is acceptable for v1 (v1.1 plumbs the real `ApplicationId` from the AppX manifest). | 4 |
| **PT3** | Build offering config from audience data | DNA group IDs already resolved via GMS (`PlaytestPublishJobParameters.FlightIds`). Just package into payload. | 1 |
| **PT4** | Send ingestion request via SAGE | New `XCloudIngestionClient` (no equivalent today). Cross-tenant S2S token acquisition. `202 Accepted` + `jobId` handling, persistence of `jobId` on `PublishedPlaytestEntity`. Blocked on SAGE allow-list (XC2). | 3 |
| **PT5** | Handle completion signal | Polling loop with exponential backoff (§3.1) + background reconciliation job for slow ingestions past the 60-min foreground deadline. State transition to `StreamingReady`. New launch URL builder. New `StreamingReady` value in `PlaytestStatus` enum. | 6 |
| **PT6** | Handle lifecycle updates | Re-trigger ingestion on audience change, expiry change, build republish; teardown on delete via the new SAGE `DELETE /playtest/ingestion/by-playtest/{playtestId}` route. Hooks into existing `UpdatePlaytestAsync` (`PlaytestBusinessLogic.cs:408-553`) and delete workflow. | 5 |
| | **xPlaytest total** | | **25** |

### 4.2 xCloud deliverables

| ID | Service | Task | Notes | SWAG (days) |
|---|---|---|---|---|
| **XC1** | SAGE | Add new routes: `POST /playtest/ingestion`, `GET /playtest/ingestion/{jobId}`, `DELETE /playtest/ingestion/by-playtest/{playtestId}` | Config-driven in `appsettings.xcloud.json`. No C# change. Returns whatever `services.contentingestion` returns (so 202 contract lives downstream). | 3 |
| **XC2** | SAGE | Allow-list the Playtest Service S2S identity | `AuthorizedClientAppIds` + `UseCrossTenantAuth = true` on both new routes. Depends on cross-tenant scheme being live. | 1 |
| **XC3** | `services.contentingestion` | Implement `PlaytestTitleIngestionWorkflow` | New sealed workflow class. Stages: validate → schedule asset ingestion → poll → upsert offering (via partner registry HTTP client) → attach title → poll install readiness → emit terminal state. Also new contract type `PlaytestIngestionJobParameters`, `WorkflowsControllerV3.PlaytestIngestion` POST/GET routes, and the `DELETE …/by-playtest/{playtestId}` tombstone route used by PT6.d. | 9 (split into 4 tasks ≤ 5d each in ADO breakdown) |
| **XC4** | `services.partnerregistry` | Extend `PlayerAuthorizationOptions` with `AllowedDnaGroups` + `AllowedSandboxId` | New fields on `OfferingV2` contract. JSON schema migration for stored offering documents (storage is git/ADO, not SQL). Also: bulk-edit support (combine create-offering + attach-title in one PR to satisfy SFI manual-approval policy) and content-ingestion SPN allow-listing on Partner Registry write routes. | 5 |
| **XC5** | User Login / Offering Auth path | Add DNA-group check to offering access | `GsToken.DnaGroups` ⊇ at least one of `offering.AuthorizationOptions.AllowedDnaGroups` → grant; else deny. For playtest titles, bypass the per-title entitlement check. Lives outside the four repos in the streaming-token / Bayside path. | 5 |
| **XC6** | Install pipeline | Single-flight-id selection from DNA groups + PC fork | Pick lex-smallest GUID; audit `TitleIngestionWorker.cs:197-225` install path to confirm tolerance of non-GA flight ID; branch `ServerFilter` build on `Platform` so PC playtests don't fall into the Xbox-only allocator parameters (see §3.6 risk callout). | 4 |
| | **xCloud total** | | | **27** |

> **SWAG reconciliation with `ado/ado-tasks.md`:** The ADO roll-up adds **M1.demo (2 days)** to the xCloud column for running the Milestone 1 foundational demo end-to-end. The reconciliation across both documents is therefore: `xCloud feature subtotal (27) + M1.demo (2) + xPlaytest feature subtotal (25) = 54 dev-days`, which is the Epic total in `ado/ado-tasks.md`.

### 4.3 Recommended execution order & parallelization (resolves comment B17 / "what's parallelizable")

The flow below assumes two developers (Melanie on xPlaytest, an xCloud counterpart). Phases A–D each fit into roughly 1–2 weeks.

```
Week 1–2  [Phase A — foundational, all parallel]
  XC4 (DNA groups in OfferingV2)         ───┐
  XC5 (auth check)                          │  no dependencies on each other
  XC2 (SAGE S2S allow-list — needs PR)      │
  PT3 (offering config from audience data)  │  (smallest piece, can finish in 1d)
                                            ▼
Week 2–4  [Phase B — depends on A]
  XC1 (SAGE routes)                ── needs XC2 to be live cross-tenant
  XC3 (PlaytestTitleIngestionWorkflow) ── needs XC4 to write offering shape
  XC6 (install pipeline shim)      ── needs XC3 wiring
  PT2 (StoreAsset construction)    ── independent of xCloud work; can run anytime
                                            ▼
Week 4–6  [Phase C — depends on B]
  PT1 (workflow integration)       ── needs PT2 ready
  PT4 (send ingestion request)     ── needs XC1 + XC2 live
  PT5 (handle completion signal)   ── needs XC3 emitting terminal state
                                            ▼
Week 6–7  [Phase D — last]
  PT6 (lifecycle updates)          ── needs PT1 + PT4 + PT5 stable
                                            ▼
Week 7–8  [Stabilization + foundational demo (see §11)]
```

**What this leaves room for in a 10–12 week internship:**
- Weeks 8–10: end-to-end soak, blocker mitigation, writing the OpenAPI/SDK, partner-facing docs.
- Weeks 10–12: buffer for the inevitable "PR approval took a week" and "cross-tenant token didn't work" incidents.

### 4.4 ADO tracking

The full Epic → Feature → Task breakdown, with each task ≤ 5 days and acceptance criteria, lives in [`ado/ado-tasks.md`](./ado/ado-tasks.md). The breakdown mirrors PT1–PT6 / XC1–XC6 but splits the larger items (notably XC3 and PT6) into smaller tasks so they can be assigned independently.

---

## 5. Data Contract

### 5.1 `PlaytestIngestionJobParameters` (xPlaytest builds, xCloud consumes)

| Field | Type | Source on xPlaytest | Required | Notes |
|---|---|---|---|---|
| `PlaytestId` | `Guid` | See §9 Open Q1 — recommended `PartnerCenterProductId` for stable offering identity | yes | Used to derive `OfferingId = xpt-{shortId(PlaytestId)}` |
| `AllowedDnaGroups` | `string[]` | `PlaytestPublishJobParameters.FlightIds` (resolved via GMS) | yes | xCloud wraps each in `XusAudience(g, RetailSandboxId)` |
| `ExpirationTime` | `DateTime` | `PlaytestPublishJobParameters.PlaytestEndDate` | **yes when `IsStreamingEnabled = true`** | Per the June 3 sync, a streaming-enabled playtest must carry an explicit end date. Download-only playtests are unaffected. No hard cap; soft warning at 180d (see §9 Q3). |
| `AllowedSandboxId` | `string` | `PackageConstants.RetailSandbox = "RETAIL"` | no | Defaults to `RETAIL` server-side — passing is allowed but discouraged |
| `StoreAsset` | object | See §5.2 | yes | Existing xCloud contract `StoreAsset.cs:17` |
| `IsGreenSigned` | `bool` | `PlaytestPublishJobParameters.IsGreenSigned` | no | Defaults to `true` (all playtests are green-signed today) |
| `CallbackUrl` | `Uri` | n/a | no | **Reserved**, not used in v1. v1.1 hook for callback delivery once cross-tenant messaging exists. |
| `CorrelationId` | `string` | xPlaytest-supplied trace id | no | For diagnostics; xCloud echoes in status response |

### 5.2 `StoreAsset` (xPlaytest fills)

This is the existing contract at `StoreAsset.cs:17` — we do not redefine it. xPlaytest must produce values that pass `StoreAsset.Validate()` (`StoreAsset.cs:25-61`).

| Field | Source | Notes |
|---|---|---|
| `StoreEntry.ProductId` | `PlaytestPublishJobParameters.PlaytestGeneratedXProductBigId` | Confirmed in meeting (Anthony, 14:00). Big Cat lookup is not done from this id. |
| `StoreEntry.Flags` | const `GAME` | |
| `StoreEntry.Name` | `PlaytestResponse.Name` | |
| `StoreEntry.Description` | `PlaytestResponse.Description` | |
| `StoreEntry.PublisherId` | `PublishedPlaytestEntity.SellerId` | |
| `StoreEntry.IsPrivateAudience` | `true` | All playtests are private |
| `StoreEntry.ParentProductIds` | `[]` | Playtests have no parent-product hierarchy today |
| `Markets` | `[Id.Parse("US")]` | Single-market for playtest publish path |
| `Platform` | `"WINDOWS.DESKTOP"` | PC-first (§3.6) |
| `ContentId` | `PlaytestLifecycleState.PlaytestContentId` | In the XProduct doc this corresponds to `packages.{packageId\|versionId}.contentId`. For a playtest product the published XProduct typically contains multiple package entries, some with `null` `contentId` (verified against `Files/product_testproduct0001_xproduct-document_primary.json`). xPlaytest selects the package using these rules: (1) filter `packages` to entries whose `platform` matches the publish platform (v1 = `WINDOWS.DESKTOP`); (2) keep only entries with state ∈ {`Published`, `Active`} (skip `Draft`/`Pending`); (3) prefer entries with a non-null `contentId`; (4) if multiple remain, choose the most recently uploaded by `packageVersionUploadTime`. If `contentId` is still null after selection, fall back to `servicingContentId` (also on the `packages.{packageId\|versionId}` object) — both fields are produced by the same downstream BigCat pipeline and the playtest workflow accepts either. The selected value must equal `SourceId` derived inside the workflow. |
| `XboxTitleId` | XProduct `alternateIds[idType=XboxTitleId].value` (verified path in `Files/product_testproduct0001_xproduct-document_primary.json`; string-typed in the doc, cast to `uint`) | **P0 blocker** — validator throws if null/0 for games. `PlaytestProductDocumentBuilder.cs:53-70` currently hardcodes empty. |
| `PackageFamilyName` | XProduct `properties.packageFamilyName` (verified). Already surfaced today as `PlaytestLifecycleState.PackageFamilyName`. | Required for PC |
| `AumID` | v1: constant default acceptable per Timi (meeting 20:11). v1.1: `{PackageFamilyName}!{ApplicationId}` with `ApplicationId` from XProduct / AppX manifest. | Validator throws on null for PC games. |

### 5.3 Derived inside `PlaytestTitleIngestionWorkflow` (xPlaytest does NOT send)

| Field | Computation |
|---|---|
| `PartnerId` | `Id.Parse("PLAYTEST")` (per Timi/David comment thread — keep namespacing simple) |
| `OfferingId` | `$"xpt-{ToShortId(PlaytestId)}"`, must be ≤ 32 chars |
| `TitleId` | `<alphanumOnly(StoreAsset.StoreEntry.Name)><PlaytestGeneratedXProductBigId>` (resolves comment TB65). **Supersedes ARCHITECTURE.md §2 / §4.3** which previously documented `TitleId = OfferingId` as a placeholder. The two values are intentionally distinct: `OfferingId` is the catalog/auth key (opaque, short); `TitleId` is the install/streaming key (user-readable, append-style uniqueness per Anthony). Both are persisted on `PublishedPlaytestEntity` so the xPlaytest side can refer to either. |
| `SourceId` | `StoreAsset.ContentId` |
| `PackageNameOverride` | `StoreAsset.StoreEntry.Name` (display name for the offering) |
| `Audiences` | `AllowedDnaGroups.Select(g => new XusAudience(g, XusAudience.RetailSandboxId))` |
| `AssetId` | Generated by `AssetIngestionWorkflow.CreateAssetAsync` |
| `StreamingPackageIds` | From child `AssetVersionIngestion` jobs (SUCU query using `SourceId` + `Audiences`) |
| Effective flight id for SUCU | Lex-smallest GUID from `AllowedDnaGroups` (§3.3) |

### 5.4 Additional PC-specific configuration (TBD — resolves comment JH58)

Jack noted that xCloud needs more PC-specific config fields than what's listed above, but those won't vary per title — they're title-class settings. The PC config space is **not finalized** and is guaranteed to change between public preview and launch as capacity comes online.

**Plan:** xCloud configures the PC defaults internally inside `PlaytestTitleIngestionWorkflow`. xPlaytest does not send them — they live in `services.contentingestion` config. The OpenAPI contract reserves no field for them; if a future caller needs to override, we add an optional `PcConfigOverrides` object as an additive change (no version bump required since it would be optional).

---

## 6. REST API Contract

> The full machine-readable contract is in [`openapi/playtest-ingestion.yaml`](./openapi/playtest-ingestion.yaml). The summary below is enough to scaffold a client.

### 6.1 `POST /playtest/ingestion`

Triggers asynchronous playtest ingestion. Returns immediately with a `jobId`.

- **Auth:** S2S bearer, cross-tenant. Caller SPN must be in SAGE's `AuthorizedClientAppIds` for this route.
- **Request body:** `PlaytestIngestionJobParameters` (§5.1).
- **Response:** `202 Accepted` with `{ jobId: string, statusUrl: string }`.
- **Error codes:**
  - `400` invalid `StoreAsset` (validator rejection) — body includes field-level errors
  - `401/403` auth failure
  - `409` duplicate `PlaytestId` already in flight in a non-terminal state — response body (`JobConflict` schema) includes the existing `jobId` and `statusUrl` so the caller rejoins polling instead of starting a fresh job
  - `5xx` retryable; caller should requeue via the existing workflow retry policy

### 6.2 `GET /playtest/ingestion/{jobId}`

Polls workflow state. Caller uses the exponential backoff from §3.1.

- **Auth:** Same S2S bearer as POST.
- **Response 200:** `{ jobId, status, terminalState?, errors[], updatedAt, correlationId? }` where `status ∈ { Running, Streamable, Failed, InstallNotFound }`. `terminalState` is set when `status` is terminal.
- **Response 404:** Unknown `jobId`.

### 6.2.1 `DELETE /playtest/ingestion/by-playtest/{playtestId}`

Tombstones a published playtest's xCloud offering (called by PT6.d on playtest delete).

- **Auth:** Same S2S bearer.
- **Behavior:** Sets `offering.PlayerAuthorizationOptions.AllowedDnaGroups = []` (denies everyone, preserves history). Schedules a GC pass to fully delete the offering and asset entries after a 7-day grace period.
- **Response 200:** `{ playtestId, offeringId, tombstoneTime }`. Idempotent — re-deleting an already-tombstoned offering still returns 200.
- **Response 404:** No offering exists for this `playtestId` (never ingested).

> **Scoped deviation from project-description P0 wording:** the formal project description says "Deleting a playtest deletes any [private offering] ... fully cleaned up and DevApi portal no longer [shows it]." We implement this as **tombstone-then-GC** rather than synchronous hard delete because (a) the same SFI / manual-PR approval that gates *creation* also gates a true hard-delete PR, so end-to-end synchronous delete is not achievable in v1; (b) tombstoning is reversible if a developer accidentally deletes a playtest mid-session; (c) clearing `AllowedDnaGroups` immediately denies all testers, which is the user-visible behavior the P0 actually cares about. From the developer's perspective in Partner Center / DevApi, the offering disappears on the next page load (the DevApi listing filters tombstones out). This deviation is called out in §7 "Open blockers" and needs explicit sign-off from Anthony / Brian before v1 sign-off.

> **Routing note:** These three paths are the **external** SAGE routes that xPlaytest calls. SAGE forwards them to `services.contentingestion`'s `/v3/workflows/playtestingestion[/{jobId}]` and the new `/v3/workflows/playtestingestion/by-playtest/{playtestId}` (see XC1 in §4.2). Treating the downstream `/v3/workflows/...` paths as an implementation detail keeps the external surface area stable when content-ingestion's internal versioning changes.

### 6.3 Required vs optional fields

See OpenAPI `required:` lists. Summary (resolves comment B42):
- **Required:** `PlaytestId`, `AllowedDnaGroups` (min 1), `ExpirationTime` (this endpoint is streaming-only — see §9 Q3), `StoreAsset`, plus the StoreAsset's intrinsically required fields.
- **Conditionally required (v1 = GAME + WINDOWS.DESKTOP):** `StoreAsset.XboxTitleId`, `StoreAsset.PackageFamilyName`, `StoreAsset.AumID` — enforced by `StoreAsset.Validate()` server-side and captured in the OpenAPI `if/then` block on `PlaytestIngestionJobParameters`.
- **Optional with server defaults:** `AllowedSandboxId` (→ `RETAIL`), `IsGreenSigned` (→ `true`).
- **Optional, reserved for future:** `CallbackUrl` (replaces polling once cross-tenant messaging exists), `CorrelationId`.

### 6.4 Versioning

The external SAGE paths (`/playtest/ingestion[/...]`) are currently unversioned, matching the existing SAGE route convention. Internally, content-ingestion routes start at `/v3/...` to match the existing `WorkflowsControllerV3`. Additive changes (new optional fields, new response fields) keep the same external path. Breaking changes (renames, required-field removals, semantic changes) bump the external path to `/v2/playtest/ingestion` and run both in parallel through a deprecation window.

### 6.5 Error model

Use the existing `ProblemDetails` shape already in use by `services.contentingestion`. SAGE currently strips bodies in favor of an `x-Proxy-Error` header (`ProxyController.cs:255-270`); for these two routes, request that SAGE forwards the response body unchanged so the `ProblemDetails` reaches the caller.

---

## 7. Known Blockers

| Blocker | Problem | Solution |
|---|---|---|
| **Cross-tenant S2S** | Playtest Service runs in MSFTGreen tenant. xCloud SAGE expects Corp or PME callers. | Short term: ride PR [#15715445](https://dev.azure.com/microsoft/Xbox/_git/SAGE/pullrequest/15715445) adding Green→Corp cross-tenant auth. Long term: GSS platform team owns the PME story (out of summer scope). |
| **Partner Registry PR approvals** | Each PR Registry write creates an ADO PR. SFI forbids self-approval. Naïve flow = 2 PRs per publish, both blocking. | Combine offering write + title attach into a single PR via `BulkEditAsync` (`RegistryProcessor{T}.cs:128-167`). Accept manual approval out-of-band during internship; long-term automation needs an SFI exception. See [PR #15685697](https://dev.azure.com/microsoft/Xbox/_git/services.partnerregistry/pullrequest/15685697). |
| **`XboxTitleId` source** | `PlaytestProductDocumentBuilder.cs:53-70` hardcodes empty; validator rejects null/0 for games. | New resolver pulls from XProduct `alternateIds[idType=XboxTitleId].value`. P0 task inside PT2. |
| **`AumID` for PC** | Validator rejects null `AumID` on PC games. `ApplicationId` not currently propagated into the publish path. | v1: ship with a constant default (Timi confirmed telemetry-only server side). v1.1: plumb real `ApplicationId` from AppX manifest. |
| **PC vs Xbox install poll path** | `TitleIngestionWorker.PollFirstInstallAsync` hardcodes `ServerType.XboxV3SeriesS` + `XBOX_*` pool ids (`TitleIngestionWorker.cs:210-218`). v1 = PC. | XC6 audit-and-fork task: confirm the PC install path's pool id + server type, branch the filter on `Platform`. If the PC pipeline uses a different allocator entirely, XC6 grows in scope — see §3.6 risk callout. |
| **Streaming expiration missing today** | Existing playtests can have `PlaytestEndDate = null` (defaults to `DateTime.MaxValue`). xCloud needs an explicit end date for streaming offerings (June 3 sync decision). | PT1.b adds a publish-time validation: when `IsStreamingEnabled = true`, `PlaytestEndDate` must be set. Partner Center UI pre-fills 90d. See §9 Q3. |
| **Delete model = tombstone (not hard delete)** | Project-description P0 says "deleting a playtest deletes the offering"; SFI manual-PR approval makes synchronous hard delete impractical in v1. | v1 ships tombstone-then-GC (see §6.2.1 + §8). User-visible behavior (offering disappears from DevApi portal, testers blocked within GsToken refresh window) matches P0 intent. **Action required:** explicit sign-off from Anthony / Brian on the deviation before v1 sign-off. |

---

## 8. Resolved Decisions

The meeting closed these — they are no longer up for debate, and the rest of the spec assumes them.

- **Streaming is an opt-in addition** to standard playtest publish (not a replacement). Both modes coexist on the same publish action.
- **xCloud does not read XProduct directly.** xPlaytest fills the `StoreAsset` and passes it through; the existing BigCat ingestion path is unchanged.
- **Offerings are created only when a playtest is published**, not on package upload or other intermediate steps. This prevents offering sprawl.
- **All playtests use the RETAIL sandbox** as a fixed value. The `AllowedSandboxId` field exists in the payload for explicitness but defaults to RETAIL server-side.
- **v1 platform = PC only.** Xbox console deferred to v1.1.
- **1 playtest = 1 title = 1 offering** for v1. Clustering deferred.
- **`StoreEntry.ProductId` = `PlaytestGeneratedXProductBigId`** (not the Partner Center product id). See §5.2 first row.
- **Multiple DNA groups in one offering is supported** by xCloud's authorization model.
- **Polling (not callback) for terminal state delivery** in v1.
- **`AumID` default is acceptable** for v1 per Timi; v1.1 plumbs the real value.
- **Streaming-enabled playtests must carry an explicit `PlaytestEndDate`** (June 3 sync). Download-only playtests are unaffected.
- **Delete model = tombstone + 7-day GC** (not synchronous hard delete). This deviates from the literal P0 wording in the project description and needs explicit sign-off — see §6.2.1 and §7. The user-visible behavior (offering disappears from the DevApi portal, testers lose access within the GsToken refresh window) matches the P0 intent.

---

## 9. Open Questions & Recommendations

Each open question now has a recommended close (resolves comment B72).

### Q1. Which `PlaytestId` is the canonical key for the offering?

**Tension:** Today's publish flow uses `PublishedPlaytestId`, which is a *per-snapshot* identity — it regenerates on every republish. The offering id needs to be **stable across republishes** so a nightly build updates the existing offering rather than creating a new one each night.

**Recommendation:** Use `PublishedPlaytestEntity.PartnerCenterProductId` (or the draft `ParentPlaytestId` if that is the stable upstream identity in the playtest data model). Offering id becomes `xpt-{shortId(PartnerCenterProductId)}`. Keep `PublishedPlaytestId` in the payload as a snapshot identifier for tracing only.

**Action:** xPlaytest (David K. / Anthony K.) confirms which of the two identities is the stable one. This is the *one* spec item that materially changes the rest of the design if it goes the other way (because a non-stable key means offering proliferation on nightly republishes).

### Q2. Terminal-state delivery: poll vs. callback?

**Recommendation:** **Polling for v1** (see §3.1). Callback deferred to v1.1, gated on the GSS platform team's cross-tenant messaging story.

**Action:** None this summer beyond reserving the `CallbackUrl` field in the contract.

### Q3. Default expiration — what's reasonable? (resolves comment JH38)

**Tension:** Jack's spec comment suggested a 3-day default. David K. confirmed today's `PlaytestEndDate` is user-configurable with no upper bound and defaults to `DateTime.MaxValue`. Forcing 3 days would surprise creators. The June 3 sync follow-up added a new constraint: *"Today Playtests can have no expiration date. When the Streamable option is selected we'll have to force an end date"* (`Documentation/Instantly Shareable Playtest - Gaming Intern Project Sync 2026-06-03.pdf`, Decisions section).

**Recommendation:**
- **Download-only playtests:** unchanged — `PlaytestEndDate` stays optional, defaults to `DateTime.MaxValue`.
- **Streaming-enabled playtests (`IsStreamingEnabled = true`):** require an explicit `PlaytestEndDate` at publish time. Reject the publish with a `400` and a clear validation message if the field is missing. This honors the June 3 decision without imposing a cap on existing download-only flows.
- **Suggested default surfaced in Partner Center UI:** **90 days**. Long enough for typical closed beta cycles; short enough to keep xCloud streaming-side resource use bounded. The UI shows this as a pre-filled value the creator can override.
- **Soft cap of 180 days, server-side:** the playtest publish accepts any explicit value; if the value exceeds 180 days, surface a warning ("streaming offerings >180 days may be reclaimed by xCloud") but do not block. Hard caps are unnecessary as long as xCloud can independently reclaim capacity through tombstoning.
- **Reject the 3-day default.** It is too aggressive for studio-led private testing cycles and would break parity with the existing download flow.
- **Internal expiration plumbing on the xCloud side:** the workflow sets `CollectionTitle.ExpirationTime = PlaytestEndDate` (matches the existing `TitleIngestionWorker.AddTitleToCollectionAsync` at `TitleIngestionWorker.cs:177`, which already accepts a nullable expiry). For streaming-enabled playtests, this will always be non-null.

**Action:** PT1.b adds the validation rule. Partner Center UI updates the pre-fill default to 90d when the streaming checkbox is checked.

### Q4. Title-id collision when a developer renames their playtest

**Recommendation:** Once an offering exists, its `TitleId` is locked. If the playtest name changes, the on-screen display (`PackageNameOverride`) updates but the underlying `TitleId` stays. This avoids title-id churn in xCloud's catalog.

### Q5. Behavior when SAGE returns `5xx` repeatedly during the trigger call

**Recommendation:** The existing `XPackagePlaytestPublishWorkflow` retry policy (`XPackagePlaytestPublishWorkflow.cs:74-85`) already applies exponential backoff. After workflow-exhausted retries, the playtest still publishes for download; streaming stays unprovisioned and the creator sees a "streaming setup failed — retry?" banner. Manual retry re-runs the trigger state.

---

## 10. Success Criteria (P0)

These map 1:1 to the P0 objectives in the formal project description (`Documentation/XD-Chen Melanie-Instantly Shareable Playtest.pdf`). A v1 release passes when **all** of the following hold:

- [ ] Publishing a playtest with **Cloud Streaming enabled** triggers the xCloud ingestion submission within seconds of the publish completing (project-description target). *Caveat: the offering becomes live as soon as the GSS Partner Registry PR is approved — see §7 "Manual PR blocker." End-to-end "live within seconds" is gated on the SFI PR-approval workflow and is therefore tracked as a follow-on once an automation path exists. For v1, the SLO we commit to is "**submission within seconds, live within one approver round-trip**."*
- [ ] A playtest-specific offering (`xpt-{id}`) is created in Partner Registry, with `AllowedDnaGroups` populated from the audience and a non-null `ExpirationTime` (streaming-enabled publishes must supply one — see §9 Q3).
- [ ] The offering contains exactly **one title** corresponding to the playtest product.
- [ ] An authorized tester can use the launch URL and successfully stream the playtest through xCloud.
- [ ] An **unauthorized** user opening the launch URL is denied with no playtest metadata leakage (Bayside privacy P0 — enforcement = XC5; partner registry only holds the data).
- [ ] Audience changes after publish **re-propagate** to xCloud within one publish-workflow cycle (PT6.a).
- [ ] Expiration changes after publish **re-propagate** (PT6.b).
- [ ] Build republish (new package upload) **updates the offering in place** rather than creating a new offering (PT6.c).
- [ ] Deleting the playtest removes tester access **within the GsToken refresh window** and removes the offering from the DevApi portal listing. *Scoped deviation: internal storage uses a 7-day GC tombstone instead of hard delete — see §6.2.1 + §8 "Delete model." From the developer's perspective in Partner Center / DevApi, the offering disappears immediately on the next page load (the DevApi listing filters out tombstones). This is functionally equivalent to the P0 wording in the project description; flagged for explicit reviewer sign-off in §7 "Open blockers."*
- [ ] **Seller / title allow-list:** Streaming-enabled publish is gated behind a feature flag scoped to an allow-list of enrolled seller IDs (and optionally title IDs) during private preview, so we can limit blast radius while the cross-tenant + SFI surfaces stabilize (project-description P0 — "Creation of a private offering can be limited to a specific title / allow list of sellers"). Implemented as a new xPlaytest publish-side validator (see PT1.c in `ado/ado-tasks.md`).
- [ ] On `Streamable`, xPlaytest sets `PlaytestStatus = StreamingReady` and Partner Center surfaces the launch URL.
- [ ] xCloud ingestion failure does **not** block the download playtest from publishing.

**P1 (stretch, deferred to v1.1):**
- GSSV `/offerings` returns the user's accessible playtest offerings so a Bayside login flow can discover them automatically (project-description P1).
- Bayside login flow on the launch URL: an authenticated tester who follows the link is dropped directly into the playtest's offering page without a separate sign-in friction step (project-description P1 — "user clicks the link → lands on the playtest").

**P3 (out of summer scope):**
- Garrison / Bastion (Xbox console) support, launch arguments, region / touch-control configuration, in-stream feedback collection.

---

## 11. Milestones & Foundational Demo

Brian's spec comment (B23): *"A huge step forward would be being able to manually create an offering in the portal, assign a DNA group id, and then go to partner center and adjust customer group membership and see it reflected in who can play games."*

**This becomes our explicit Milestone 1 ("Foundational Demo")** — it validates the auth model end-to-end *before* any cross-team ingestion plumbing is in place, and it derisks XC4 + XC5 which are the most novel pieces.

The milestone schedule below maps to the official internship calendar in `Documentation/XD-Chen Melanie-Instantly Shareable Playtest.pdf` (Connect 6/2, Midpoint Connect 6/30, Final Connect 7/28, presentation week 11–12).

### Milestone 1 — Foundational Demo (end of Phase A, ~Week 2, target ≤ 6/20)

- XC4 shipped: `AllowedDnaGroups` writable on `OfferingV2`.
- XC5 shipped: GsToken DNA-group check enforced at offering entry.
- Manual operator script creates an offering with a fixed DNA group GUID, attaches an existing test title.
- Partner Center customer-group membership change for a tester is visible in xCloud access within the GMS propagation latency.
- **Acceptance:** a tester added to the group can stream the test title; a tester removed from the group is denied.

### Milestone 2 — Ingestion (end of Phase B, ~Week 4, target ≤ 6/30 / **Midpoint Connect**)

- XC1 + XC2 + XC3 + XC6 shipped: a manual `curl` against SAGE with a hand-built `PlaytestIngestionJobParameters` succeeds end-to-end and produces a streamable offering.
- PT2 shipped: `StoreAsset` builder produces a valid payload for an existing playtest.
- **This is the Midpoint Connect demo**: an end-to-end ingestion driven from a script, even if the Partner Center UI integration is not yet wired in.

### Milestone 3 — xPlaytest integration (end of Phase C, ~Week 6, target ≤ 7/14)

- PT1 + PT4 + PT5 shipped: publishing a streaming-enabled playtest in Partner Center end-to-end produces a launch URL.

### Milestone 4 — Lifecycle (end of Phase D, ~Week 7, target ≤ 7/21)

- PT6 shipped: audience/expiry/republish/delete all reflect correctly on the xCloud side.

### Milestone 5 — Soak + handoff (Weeks 8–10, target ≤ 7/28 / **Final Connect**)

- End-to-end test with a real studio build.
- OpenAPI / partner docs published.
- Runbook for cross-tenant token rotation and PR approval triage.

### Weeks 11–12 — Presentation week

- Intern presentation (per project description).
- Buffer for inevitable cross-tenant token or PR approval slippage.

---

## Appendix A — Comment Resolutions (cross-reference)

| Spec comment | Resolution | Section |
|---|---|---|
| B16 — SWAG column | Added | §4.1 + §4.2 |
| B15 — ADO tasks | Created | [`ado/ado-tasks.md`](./ado/ado-tasks.md) |
| B17 — call-sequence vs execution order | Execution order documented | §4.3 |
| B23 — XC4/XC5 first + manual demo | Adopted as Milestone 1 | §11 |
| JH38 / B39 — 3-day expiration cap | Rejected; honor existing `PlaytestEndDate` | §9 Q3 |
| B42 — API versioning + OpenAPI | OpenAPI created; v3 path; required vs optional documented | §6 + `openapi/playtest-ingestion.yaml` |
| JH58 — extra PC fields | Documented as TBD; reserved for xCloud-internal config | §5.4 |
| B64 — 1:1:1 offering↔title↔playtest | Locked for v1 | §3.5 |
| TB65 — TitleId from playtest name + product id | Adopted | §5.3 |
| B73 / B74 — polling backoff specifics | Exponential, 30 s → 5 min cap, 60 min wall clock | §3.1 |
| B72 — recommendation per open Q | Done | §9 |

---

## Appendix B — Glossary

- **DNA group** — GMS audience grouping; the identifier we resolve to from Partner Center customer groups.
- **GMS** — Group Management Service. Resolves audience → `FlightIds` (which in this codebase are DNA group GUIDs, despite the name).
- **GsToken** — Game Streaming token; carries `DnaGroups` claims for the signed-in user.
- **SAGE** — Service API Gateway; cross-tenant ingress proxy for xCloud.
- **SUCU** — Streaming Update Catalog; xCloud's package-version resolution layer.
- **SFI** — Secure Future Initiative; the policy regime that forbids PR self-approval.
- **xpt-{id}** — Offering id prefix for playtest-derived offerings.
