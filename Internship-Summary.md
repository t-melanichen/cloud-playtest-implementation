# Internship summary — Instantly Shareable Playtest (as of 2026-07-13)

**Intern:** Melanie Chen (@t-melanichen) · **Team:** Xbox / Juno (xPlaytest × xCloud streaming)

## The problem I worked
Let a game creator share an unreleased build that an invited tester **streams from the cloud in seconds** —
no multi-gigabyte install. That meant threading a build through a chain that spans two orgs and ~13 services:

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

**7. Distribution + provisioning — get the build onto the server (the ContentId fix)**
- Root-caused why a PC playtest wouldn't install: the streaming `StoreAsset` sent the SUCU **`servicingContentId`**
  as `ContentId`, but the PC MSIXVC is keyed on the **real `contentId`**, so installs failed with
  `ERROR_NOT_FOUND`. Fixed with a **5-PR ContentId separation** — STORECLIENT 16128230, XBET 16130422,
  CTIN 16129840, CTDR 16137972 (merged), SESSIONS 16140301 (active) — so sourcing keeps the SourceId while
  distribution/provisioning use the real content id. The build now **installs and provisions** on a PC server.
- Provisioned the **`PC_PLAYTEST` lane in PROD**: SUG definition (16103484), Content Targets quota (16103771),
  predicted-targets overrides (16114214 / 16114118), `DefaultAllocationPools` (16112987), and the offering data
  (16139815). Pinned playtest ingestion to the **Americas SAGE cluster** so submit + status-poll agree
  (16102792, active — CTIN is Americas-only and jobs are cluster-local).

**8. Client (Bayside) — surface the playtest to the tester**
- Built the new **"My playtests" tab** in the play.xbox.com web client (Xbox.JS), gated to appear only for a user
  who has an `xpt` playtest offering, handling the **signed-out** and **not-invited** states. Tiles show the
  offering's friendly name; **game art + display metadata are still blocked** — private playtests aren't in
  BigCat and CAS's playtest contract carries access flags only, so where developer-provided art lives is an open
  question with Anthony / CAS.
- Built a small **"collect the stars"** GDK desktop package as a real, playable (non-stub) demo title.

## Where it stands on 2026-07-13
- **31 of 36 tracked PRs merged** (4 active, 1 draft), across ~13 service areas and 3 ADO projects. The backend
  spine is in `main` and **deployed to prod**.
- **The full pipeline runs end to end in prod** under the pilot seller (`65050620`): create a playtest → XORc
  resolves the Xbox title → the Xbet builder assembles the payload → SAGE routes to CTIN → CTIN ingests and opens
  an **auto-PR** → the PC offering + title go live. After the **ContentId 5-PR fix**, the build now **installs and
  provisions** on a cloud PC server (the `ERROR_NOT_FOUND` install blocker is resolved).
- **One blocker from a live stream:** the cloud launch (`LaunchByContentIdV1`) currently **times out** — a
  **server-side GRTS build issue** Nate's server team is fixing. Once that rolls to the `PC_TAKEHOME`/`PC_GA` lanes
  `PC_PLAYTEST` draws from, the same prod path should stream.
- **Remaining beyond that:** the Partner Center creator toggle (GPM 15946761, draft), the Bayside tile
  **art/metadata source** (BigCat/CAS open question), dropping the Americas ingestion pin once durable SAGE→CTIN
  routing lands, and the tracked follow-ups/blockers. See [`PC-Polling-Status.md`](./PC-Polling-Status.md),
  [`Blockers/`](./Blockers/), and [`FuturePlans/`](./FuturePlans/).

## In one sentence
I built and shipped the **backend spine** of Instantly Shareable Playtest end to end — from resolving audience/
StoreAsset/DNA-group/title-id inputs in xPlaytest, to sending them MSFTGreen → Corp through SAGE, to the CTIN
workflow that binds the title id and offering, into the distribution/provisioning path that now **installs and
provisions the build on a cloud PC server in prod** — plus the Bayside "My playtests" tab — across ~13 service
areas and 31 merged PRs, with a single server-side GRTS fix now standing between this and a live stream.
