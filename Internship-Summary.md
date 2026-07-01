# Internship summary — Instantly Shareable Playtest (as of 2026-07-01)

**Intern:** Melanie Chen (@t-melanichen) · **Team:** Xbox / Juno (xPlaytest × xCloud streaming)

## The problem I worked
Let a game creator share an unreleased build that an invited tester **streams from the cloud in seconds** —
no multi-gigabyte install. That meant threading a build through a chain that spans two orgs and ~8 services:

> **audience** (who may see it) → **offering** (publish) → **payload** (StoreAsset + DNA groups from xPlaytest)
> → **cross-tenant send** (MSFTGreen → Corp through SAGE) → **CTIN ingestion workflow** (bind title id + offering,
> ingest the asset) → **PC/Xbox server readiness poll** → **share link → tester streams**.

A lot of the early work was *figuring out the flow* — reverse-engineering how audience, offering, StoreAsset,
title id, and servicing content ids fit together, and where the Green→Corp trust boundary sat — then building
each hop and getting it reviewed/merged across the different service repos.

## What I built (by area)

**1. Audience model — who's allowed in**
- Added `AllowedDnaGroups` to the offering authorization model and **enforced it at user login** so only invited
  DNA groups can see a private playtest offering (PRs 15732852 partnerregistry, 15738761 auth, 15739964 devapi,
  15751527 offering data).

**2. Offering + title identity**
- New playtest **offering endpoint**, region/id-naming config, and centralized offering-id derivation
  (`xpt{ProductId}`); set Xbox authentication options on playtest offerings; refactored the playtest title id and
  removed a stale package-source-id from the contract (PRs 15773366, 15815668, 15821813, 15892276, 15849944,
  15860243).
- **Exposed the Xbox Live TitleId** from XORc on the product config response so publish can bind it (PR 15894506).

**3. The payload builder — assemble everything xCloud needs (my headline xPlaytest PR)**
- `StreamingPlaytestTitleIngestionBuilder` (PR **15834601**, Xbox.Xbet.Service): builds the receiver's
  `PlaytestTitleIngestion` payload from the publish snapshot — **StoreAsset** (StoreEntry name/description,
  package family name, AumID, platform, servicing content id), **AllowedDnaGroups** resolved from the playtest's
  audiences, retail sandbox, and a bounded expiration. Streaming is opt-in (`EnableStreaming`, gated to the pilot
  seller) and **non-blocking** — a streaming failure never fails the normal download publish.
- Added the **cross-tenant S2S client** (MSFTGreen confidential-client token via the xPackage cert) and two publish
  workflow states — `SchedulingStreamingIngestionJob` + `PollingStreamingIngestionJob` — plus a publish rule that
  blocks publishing an already-expired playtest.

**4. Green → Corp through SAGE**
- Registered the **SAGE proxy routes** `POST/GET /v3/playtest/playtesttitleingestion` → contentingestion, with
  token pass-through (PR 15829639, services.serviceapigateway).
- On the receiver side, **gated** the ingestion endpoints with the CrossTenantS2S policy and **fixed the
  cross-tenant auth**: the Green caller mints a v1.0 token whose `aud` is the bare app-id GUID, so I made
  contentingestion accept that bare-GUID audience (PRs 15905881, **15996626**).

**5. CTIN ingestion workflow — bind title + offering, then poll readiness**
- The `PlaytestTitleIngestionWorkflow` (PR 15800964, services.contentingestion) ingests the asset, **binds the
  title id and configures the offering in one flow**, and then **polls for server readiness** — the
  **PC install-readiness poll** against PC Orchestrator (PR 15896502), and the equivalent for Xbox servers —
  before marking the title ready to stream. Also fixed resolution to not scope the package search to the GA flight
  (PR 15983599).

**6. The PC server lane (environment plumbing)**
- Set the `PC_PLAYTEST` **SUG** on the playtest offering, registered the SUG definitions (Test + Int), and added
  the Content Targets **quota** via dynamic config (PRs 15949594, 15965750, 15965763, 15966616).

## Where it stands on 2026-07-01
- **22 of 24 tracked PRs merged.** The entire backend spine is in `main`: audience → offering → title id →
  **payload builder** → **SAGE cross-tenant route** → **CTIN ingest + bind + readiness poll**.
- The two last cross-tenant gates (**SAGE 15829639**, **CTIN 15996626**) merged today, and **PlayTest +
  XPackageWorkflow are deployed from `main`** with the streaming change — so a publish by the pilot seller now
  actually fires the Green→SAGE→CTIN call.
- **Remaining:** the two front ends (Partner Center creator toggle + shareable link; Bayside tester landing/stream)
  and a set of tracked follow-ups/blockers (signed-out content-leak, PC region/quota env alignment, launch-link
  404 window, 30-day expiration cap). See [`testing/e2e-readiness-and-blockers.md`](./testing/e2e-readiness-and-blockers.md)
  and [`FuturePlans/`](./FuturePlans/).

## In one sentence
I built and shipped the **backend spine** of Instantly Shareable Playtest end to end — from resolving audience/
StoreAsset/DNA-group/title-id inputs in xPlaytest, to sending them MSFTGreen → Corp through SAGE, to the CTIN
workflow that binds the title id and offering and polls PC/Xbox servers for streaming readiness — across ~8
services and 22 merged PRs.
