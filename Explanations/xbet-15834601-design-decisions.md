# XBET PR 15834601 — Design decisions (streaming opt-in & workflow purity)

Design rationale for **PR 15834601** (*Playtest Ingestion Payload Builder*, `Xbox.Xbet.Service`,
branch `t-melanichen/playtest-ingestion-payload-builder`). Companion to the per-comment
[review responses](./xbet-15834601-review-responses.md); this doc records the **decisions and the why**,
reflecting the **final, as-merged shape** — which evolved past the review-responses snapshot
(see [Naming & evolution](#naming--evolution)).

> Settled with Anthony Keller and Brian Trevethan, late June 2026.

## The core decision

Keep **`XPackageWorkflow` a pure function of its inputs.** All job-configuration data — specifically the
Xbox Live title id needed for streaming — is **resolved and validated at the API boundary
(`PlaytestBusinessLogic`) at publish time** and passed into the workflow as explicit job parameters. The
workflow does no external reads and holds no seller logic; it only runs an **optional** SAGE ingestion
stage when streaming was opted in.

## Why

- **Determinism / retryability** — workflow steps are retried; an external read inside a step can return a
  different answer between attempts and silently invalidate what later steps assumed. Resolving at the
  boundary keeps jobs replayable and debuggable.
- **Separation of concerns** — the workflow *executes* jobs; it doesn't *assemble* them. Gathering and
  validating inputs is the submitter's job. Pushing lookups into the workflow would add a client, an auth
  scope, and a failure mode to a service that should stay narrow. (Naveen's early guidance: minimize
  workflow coupling, especially for job-configuration data.)
- **Fail early + clearer failures** — whether a product is Xbox-Live-configured is knowable at submit
  time, so we bail before doing expensive async work, and we surface a meaningful error at the boundary
  instead of a generic workflow failure.
- **Don't overload semantics** — streaming enablement is a dedicated flag, **not** inferred from "a title
  id is present" (Brian / Anthony). That keeps the title-id field's meaning clean.

## As-built design

### 1. Streaming is opt-in, decided in PlayTest (one place)
- `PlaytestBusinessLogic.QueuePublishJobAsync` computes **`EnableStreaming`**. Today that's
  `IsStreamingEnabled(sellerId)` == the **pilot seller `65050620`** — a temporary gate so the full flow can
  be exercised in prod scoped to one seller. (ADO#62878234 replaces it with a persisted flag from the UX
  checkbox; ADO#62684638 ECS-allowlists who sees the checkbox.)
- The Xbox Live title id is resolved from XORc via `IProductsBusinessLogic.GetXboxServicesConfigAsync`
  **only when `EnableStreaming` is true**. Download-only publishes never call XORc.
- If a publish opts in but the product isn't Xbox-Live-configured, resolution **fails fast** with a
  validation error (`ServiceErrorHelper.CreateValidationError`) — it no longer returns null / silently
  skips.

### 2. `PlaytestStreamingParameters` carries the streaming inputs
Resolved inputs are bundled into a `PlaytestStreamingParameters` record (today: `XboxLiveTitleId`;
defaults `ApplicationId` = `"App"` and `Platform` = `ServerPlatform.PC`; region/launch settings later).
The job parameters carry `EnableStreaming` (bool) + `StreamingParameters` (null when not opted in).

### 3. Workflow gates on the flag, with an isolated optional stage
- `PlaytestProductCreation` → `EnableStreaming ? SchedulingStreamingIngestion : SuccessCompletion`.
- `SchedulingStreamingIngestion` builds + POSTs the SAGE payload (`XCloudPlaytestTitleIngestionBuilder` +
  `IXCloudPlaytestIngestionServiceClient.SchedulePlaytestTitleIngestionAsync`) and captures the job id;
  re-schedule is **idempotent** (skips if a job id already exists).
- `PollingStreamingIngestion` polls SAGE status on a **bounded self-delay loop** (5-min interval, 24-hr
  cap) — *not* a retry policy, which would fail the whole publish at its cap. On timeout/error it
  **completes the publish** and flags streaming for triage.
- The download publish (SUCU / xProduct) completes first; we wait on SAGE **only IFF** we scheduled it.
  **Streaming never blocks or fails the standard download flow.**

### 4. Validation moved into the synchronous rule pipeline
Publish validations are `IPlaytestRule`s on the Publish trigger that return **structured errors**
(surfaceable to the UI). The end-date-in-future check was **broadened from streaming-only to all
playtests** as `PlaytestEndDateMustBeInFutureRule` (ADO#62908755) — publishing an already-expired playtest
is now blocked for everyone. (The two async checks — GMS flight-id resolution and the XORc XBL-config
lookup — don't fit the synchronous rule contract yet and stay in the publish path.)

### 5. DI: cross-tenant (Green) S2S auth as a keyed singleton
The xCloud ingestion client needs a Green-tenant confidential client (xPackage cert/app, Green authority)
so the token audience matches content ingestion's Green app registration. It's registered as a **keyed
singleton** (`XCloudPlaytestIngestionS2SAuthHelperFactory`) and injected via `[FromKeyedServices]`, instead
of a dedicated interface.

## How this addresses reviewer feedback

- **Brian Trevethan** — XORc no longer runs on every publish; it's behind the `EnableStreaming` gate, so an
  XORc outage only affects opted-in streaming publishes, not all of them. Enablement is a dedicated flag,
  not title-id presence, so that field isn't overloaded.
- **Anthony Keller** — `EnableStreaming` is introduced as high in the stack as the publish path allows,
  gated on seller, with resolution only when true. SAGE is an optional workflow stage we wait on only when
  invoked, decoupled from the SUCU / xProduct publish. The end-date rule applies to all playtests.

## Naming & evolution

This supersedes the earlier snapshot in [review responses](./xbet-15834601-review-responses.md):

| Earlier (review-responses) | Final (as-merged) |
|---|---|
| `IncludeStreaming` | **`EnableStreaming`** |
| single `XboxLiveTitleId` field on job params | wrapped in a **`PlaytestStreamingParameters`** record |
| "kept the dedicated S2S helper" | **keyed-singleton** S2S helper (`[FromKeyedServices]`) |
| `StreamingEndDateMustBeInFutureRule` (streaming-only) | **`PlaytestEndDateMustBeInFutureRule`** (all playtests) |

## Follow-ups

| Item | Work |
|---|---|
| **ADO#62878234** | Replace the pilot seller-id gate with a persisted `EnableStreaming` flag flowed from the publish request (UX streaming checkbox) through the ProductConfigurationFD / Playtest contracts + a new Playtest SQL column. |
| **ADO#62684638** | ECS allowlist controlling who sees the streaming checkbox; externalize the poll interval / max-wait alongside the gate. |
| **ADO#62893742** | Multiple market groups (distinct servicing content ids). |
| **ADO#62881046** | Real per-package `ApplicationId` (v1.1). |
| **ADO#62893743** | Derive `ServerPlatform` from the published package format (MSIXVC / XVC). |
| **ADO#62907370** | Region configuration / routing. |
| **ADO#62908755** | ✅ Done — end-date-in-future rule, broadened to all playtests. |

## Related

- Per-comment fixes & replies: [review responses](./xbet-15834601-review-responses.md)
- As-built spec deltas: [`../Documentation/xbet-15834601-spec-deltas.md`](../Documentation/xbet-15834601-spec-deltas.md)
- PR ledger: [`../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md`](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md)
- Forward work: [`../FuturePlans/ecs-feature-flag.md`](../FuturePlans/ecs-feature-flag.md),
  [`../FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md),
  [`../FuturePlans/region-configuration-routing.md`](../FuturePlans/region-configuration-routing.md),
  [`../FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md)
