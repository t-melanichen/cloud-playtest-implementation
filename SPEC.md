# Instantly Shareable Playtest — Implementation Spec

**Status:** Draft, post May 29 2026 alignment meeting
**Owner:** Melanie Chen (xPlaytest intern)
**Reviewers:** Brian Bowman (xPlaytest), Anthony Keller (xPlaytest), David Kushmerick (xPlaytest), Timi Bolaji (xCloud), Jack Heuberger (xCloud), Aditya Toney (xCloud)
**Companion docs:** [`ARCHITECTURE.md`](./ARCHITECTURE.md) (code-grounded), [`openapi/playtest-ingestion.yaml`](./openapi/playtest-ingestion.yaml), [`ado/ado-tasks.md`](./ado/ado-tasks.md)

> This document is the **dev spec** for cross-team alignment. It captures *what* we're building, *who owns what*, *why* the contract looks the way it does, and *how long* each piece should take. The deeper *how* (file-level code citations, validators, exact line numbers) lives in `ARCHITECTURE.md`.

> **Divergences from `ARCHITECTURE.md`:** SPEC.md is the **newer** of the two docs and supersedes ARCHITECTURE.md on the following points: (a) `TitleId` is distinct from `OfferingId` — see §5.3; (b) the external SAGE path is `/playtest/ingestion` (no `/v3` prefix) — see §6 routing note; (c) for v1, `AumID` ships with a constant default rather than a plumbed `ApplicationId` — see §8 + §7. The cross-tenant Green→PME item in ARCHITECTURE.md §7 P0 list is **deferred** out of summer scope — see Known Blockers §7 below. ARCHITECTURE.md remains the source of truth for file/line citations and the existing-code surface area; treat any prose contradiction as resolved in SPEC.md's favor unless ARCHITECTURE.md is updated more recently.

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

**AumID resolution path:** Timi confirmed (meeting 20:11) that the server-side use of `AumID` is **telemetry only** for upload — a default value is acceptable in v1. We will still plumb the real `ApplicationId` from the AppX manifest as a follow-up in v1.1 to be principled about it, but v1 is unblocked.

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

**Decision:** Use `/v3/...` paths matching the existing `WorkflowsControllerV3` convention in `services.contentingestion`. Document required vs. optional fields explicitly in the OpenAPI contract (`openapi/playtest-ingestion.yaml`). Prefer adding optional fields over breaking required ones.

**Rationale (per Brian's spec comment B42):**
- Versioning a contract at the URL is easy to reason about.
- An OpenAPI spec lets both teams generate clients/server stubs and lint changes for breakage.
- Most likely future changes are additive (more PC config fields, callback URL, region overrides) — these go in as `optional` and don't break v3.

**Specifically expected future additions (not breaking):**
- `IsGreenSigned` flag (already optional, defaults to true).
- `CallbackUrl` once cross-tenant messaging exists (replaces polling).
- PC-specific config block (Jack noted in JH58 that more PC fields will be needed; the shape is not finalized).

---

## 4. Team Responsibilities

### 4.1 xPlaytest deliverables

> **Ordering note (resolves spec comment B17):** The table is presented in **call sequence** order. Recommended *execution* order — including what can be parallelized — is in §4.3.

| ID | Task | Notes | SWAG (days) |
|---|---|---|---|
| **PT1** | Integrate xCloud trigger into `XPackagePlaytestPublishWorkflow` | New `XCloudIngestionTriggerState` between `PlaytestProductCreation` and `SuccessCompletion`. Reuses existing workflow orchestration + retry policy. Failure does NOT block publish. | 4 |
| **PT2** | Construct `StoreAsset` from Playtest product/package data | By the time the new xCloud-trigger state runs, `PlaytestLifecycleState` is fully populated (`FetchContentIds` resolved `ProductId` / `ContentId` / `PackageFamilyName` / `XProductBigId`; `PollContentSubmission` confirmed they are committed in Partner Center), so most of the payload is a direct projection of in-memory state — no new external calls. Two pieces are *not* present today: (1) **`XboxTitleId` resolver (P0 cross-team blocker)** replacing the `XboxLiveTitleId = string.Empty` hardcode at `PlaytestProductDocumentBuilder.cs:53–70` by reading `alternateIds[XboxTitleId]` from the XProduct response; (2) **`AumID` default-or-resolver** — per Timi the server uses `AumID` only for ingestion telemetry, so the constant `"{packageFamilyName}!App"` is acceptable for v1 (v1.1 plumbs the real `ApplicationId` from the AppX manifest). | 4 |
| **PT3** | Build offering config from audience data | DNA group IDs already resolved via GMS (`PlaytestPublishJobParameters.FlightIds`). Just package into payload. | 1 |
| **PT4** | Send ingestion request via SAGE | New `XCloudIngestionClient` (no equivalent today). Cross-tenant S2S token acquisition. `202 Accepted` + `jobId` handling, persistence of `jobId` on `PublishedPlaytestEntity`. Blocked on SAGE allow-list (XC2). | 3 |
| **PT5** | Handle completion signal | Polling loop with exponential backoff (§3.1) + background reconciliation job for slow ingestions past the 60-min foreground deadline. State transition to `StreamingReady`. New launch URL builder. New `StreamingReady` value in `PlaytestStatus` enum. | 6 |
| **PT6** | Handle lifecycle updates | Re-trigger ingestion on audience change, expiry change, build republish; teardown on delete via the new SAGE `DELETE /playtest/ingestion/by-playtest/{playtestId}` route. Hooks into existing `UpdatePlaytestAsync` (`PlaytestBusinessLogic.cs:408-553`) and delete workflow. | 5 |
| | **xPlaytest total** | | **23** |

### 4.2 xCloud deliverables

| ID | Service | Task | Notes | SWAG (days) |
|---|---|---|---|---|
| **XC1** | SAGE | Add new routes: `POST /playtest/ingestion`, `GET /playtest/ingestion/{jobId}`, `DELETE /playtest/ingestion/by-playtest/{playtestId}` | Config-driven in `appsettings.xcloud.json`. No C# change. Returns whatever `services.contentingestion` returns (so 202 contract lives downstream). | 3 |
| **XC2** | SAGE | Allow-list the Playtest Service S2S identity | `AuthorizedClientAppIds` + `UseCrossTenantAuth = true` on both new routes. Depends on cross-tenant scheme being live. | 1 |
| **XC3** | `services.contentingestion` | Implement `PlaytestTitleIngestionWorkflow` | New sealed workflow class. Stages: validate → schedule asset ingestion → poll → upsert offering (via partner registry HTTP client) → attach title → poll install readiness → emit terminal state. Also new contract type `PlaytestIngestionJobParameters`, `WorkflowsControllerV3.PlaytestIngestion` POST/GET routes, and the `DELETE …/by-playtest/{playtestId}` tombstone route used by PT6.d. | 9 (split into 4 tasks ≤ 5d each in ADO breakdown) |
| **XC4** | `services.partnerregistry` | Extend `PlayerAuthorizationOptions` with `AllowedDnaGroups` + `AllowedSandboxId` | New fields on `OfferingV2` contract. JSON schema migration for stored offering documents (storage is git/ADO, not SQL). Also: bulk-edit support (combine create-offering + attach-title in one PR to satisfy SFI manual-approval policy) and content-ingestion SPN allow-listing on Partner Registry write routes. | 5 |
| **XC5** | User Login / Offering Auth path | Add DNA-group check to offering access | `GsToken.DnaGroups` ⊇ at least one of `offering.AuthorizationOptions.AllowedDnaGroups` → grant; else deny. For playtest titles, bypass the per-title entitlement check. Lives outside the four repos in the streaming-token / Bayside path. | 5 |
| **XC6** | Install pipeline | Single-flight-id selection from DNA groups | Pick lex-smallest GUID; audit `TitleIngestionWorker.cs:197-225` install path to confirm tolerance of non-GA flight ID. | 3 |
| | **xCloud total** | | | **26** |

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
| `ExpirationTime` | `DateTime?` | `PlaytestPublishJobParameters.PlaytestEndDate` | no | Defaults to `DateTime.MaxValue` (matches current playtest behavior — see §9 Open Q3) |
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
| `ContentId` | `PlaytestLifecycleState.PlaytestContentId` | Must equal `SourceId` derived inside the workflow |
| `XboxTitleId` | XProduct `alternateIds[XboxTitleId]` or `dimTitleProperties.titleId` | **P0 blocker** — validator throws if null/0 for games. `PlaytestProductDocumentBuilder.cs:53-70` currently hardcodes empty. |
| `PackageFamilyName` | `PlaytestLifecycleState.PackageFamilyName` | Required for PC |
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

> **Routing note:** These three paths are the **external** SAGE routes that xPlaytest calls. SAGE forwards them to `services.contentingestion`'s `/v3/workflows/playtestingestion[/{jobId}]` and the new `/v3/workflows/playtestingestion/by-playtest/{playtestId}` (see XC1 in §4.2). Treating the downstream `/v3/workflows/...` paths as an implementation detail keeps the external surface area stable when content-ingestion's internal versioning changes.

### 6.3 Required vs optional fields

See OpenAPI `required:` lists. Summary (resolves comment B42):
- **Required:** `PlaytestId`, `AllowedDnaGroups` (min 1), `StoreAsset`, plus the StoreAsset's intrinsically required fields.
- **Conditionally required (v1 = GAME + WINDOWS.DESKTOP):** `StoreAsset.XboxTitleId`, `StoreAsset.PackageFamilyName`, `StoreAsset.AumID` — enforced by `StoreAsset.Validate()` server-side and captured in the OpenAPI `if/then` block on `PlaytestIngestionJobParameters`.
- **Optional with server defaults:** `ExpirationTime` (→ `DateTime.MaxValue`), `AllowedSandboxId` (→ `RETAIL`), `IsGreenSigned` (→ `true`).
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
| **`XboxTitleId` source** | `PlaytestProductDocumentBuilder.cs:53-70` hardcodes empty; validator rejects null/0 for games. | New resolver pulls from XProduct `alternateIds[XboxTitleId]`. P0 task inside PT2. |
| **`AumID` for PC** | Validator rejects null `AumID` on PC games. `ApplicationId` not currently propagated into the publish path. | v1: ship with a constant default (Timi confirmed telemetry-only server side). v1.1: plumb real `ApplicationId` from AppX manifest. |

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

**Tension:** Jack suggested a 3-day default. David K. confirmed (meeting comment) that today `PlaytestEndDate` is user-configurable with no upper bound and defaults to `DateTime.MaxValue`. Forcing 3 days would surprise creators.

**Recommendation:**
- v1: **honor the existing `PlaytestEndDate` as-is.** Default = `DateTime.MaxValue`. No hard cap.
- Playtest expiration is currently uncapped — a playtest will persist indefinitely unless the developer explicitly sets an end date. Before we change that, confirm with xCloud whether long-lived streaming offerings present a real capacity / storage constraint. If they do, introduce a **soft cap of 100 days** on the xCloud-derived offering expiration (capacity reclaim) — enforced server-side at publish time with a clear validation error and an override path for studios that legitimately need longer windows — while keeping the playtest itself active for download. The download playtest is cheap; only the streaming offering needs the soft cap.
- A soft cap is preferable to a hard one because it preserves the existing developer-controlled lifecycle while giving xCloud a knob to pull back on if usage grows faster than capacity.
- The 3-day cap is too aggressive for studio-led private testing cycles and would break parity with the existing download flow.

**Action:** Document the soft-cap intention in the OpenAPI; do not enforce in v1.

### Q4. Title-id collision when a developer renames their playtest

**Recommendation:** Once an offering exists, its `TitleId` is locked. If the playtest name changes, the on-screen display (`PackageNameOverride`) updates but the underlying `TitleId` stays. This avoids title-id churn in xCloud's catalog.

### Q5. Behavior when SAGE returns `5xx` repeatedly during the trigger call

**Recommendation:** The existing `XPackagePlaytestPublishWorkflow` retry policy (`XPackagePlaytestPublishWorkflow.cs:74-85`) already applies exponential backoff. After workflow-exhausted retries, the playtest still publishes for download; streaming stays unprovisioned and the creator sees a "streaming setup failed — retry?" banner. Manual retry re-runs the trigger state.

---

## 10. Success Criteria (P0)

A v1 release passes when **all** of the following hold:

- [ ] Publishing a playtest with **Cloud Streaming enabled** automatically triggers xCloud ingestion via SAGE.
- [ ] A playtest-specific offering (`xpt-{id}`) is created in Partner Registry, with `AllowedDnaGroups` populated from the audience.
- [ ] The offering contains exactly **one title** corresponding to the playtest product.
- [ ] An authorized tester can use the launch URL and successfully stream the playtest through xCloud.
- [ ] An **unauthorized** user opening the launch URL is denied with no playtest metadata leakage. (Enforcement = XC5 in the streaming-token path; partner registry only holds the data.)
- [ ] Audience / expiry / build changes after publish **re-propagate** through the integration (PT6).
- [ ] On `Streamable`, xPlaytest sets `PlaytestStatus = StreamingReady` and Partner Center surfaces the launch URL.
- [ ] xCloud ingestion failure does **not** block the download playtest from publishing.

---

## 11. Milestones & Foundational Demo

Brian's spec comment (B23): *"A huge step forward would be being able to manually create an offering in the portal, assign a DNA group id, and then go to partner center and adjust customer group membership and see it reflected in who can play games."*

**This becomes our explicit Milestone 1 ("Foundational Demo")** — it validates the auth model end-to-end *before* any cross-team ingestion plumbing is in place, and it derisks XC4 + XC5 which are the most novel pieces.

### Milestone 1 — Foundational Demo (end of Phase A, ~Week 2)

- XC4 shipped: `AllowedDnaGroups` writable on `OfferingV2`.
- XC5 shipped: GsToken DNA-group check enforced at offering entry.
- Manual operator script creates an offering with a fixed DNA group GUID, attaches an existing test title.
- Partner Center customer-group membership change for a tester is visible in xCloud access within the GMS propagation latency.
- **Acceptance:** a tester added to the group can stream the test title; a tester removed from the group is denied.

### Milestone 2 — Ingestion (end of Phase B, ~Week 4)

- XC1 + XC2 + XC3 + XC6 shipped: a manual `curl` against SAGE with a hand-built `PlaytestIngestionJobParameters` succeeds end-to-end and produces a streamable offering.
- PT2 shipped: `StoreAsset` builder produces a valid payload for an existing playtest.

### Milestone 3 — xPlaytest integration (end of Phase C, ~Week 6)

- PT1 + PT4 + PT5 shipped: publishing a streaming-enabled playtest in Partner Center end-to-end produces a launch URL.

### Milestone 4 — Lifecycle (end of Phase D, ~Week 7)

- PT6 shipped: audience/expiry/republish/delete all reflect correctly on the xCloud side.

### Milestone 5 — Soak + handoff (Weeks 8–10)

- End-to-end test with a real studio build.
- OpenAPI / partner docs published.
- Runbook for cross-tenant token rotation and PR approval triage.

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
