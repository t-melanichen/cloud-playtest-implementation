# UI implementation steps — Partner Center (creator portal)

**Repo (frontend):** `Xbox.Gpx.PartnerCenter.Client` → `apps/packages/src` (GPM creator UI).
**Scope:** the remaining creator-facing UI pieces from `Context/InternProjectDocument.pdf` that are
**not yet in a PR**, each broken into frontend + backend (per service) steps. Numbers match
`FuturePlans/` analysis. Effort: 🟢 easy · 🟡 medium · 🔴 hard.

**Already in a PR (for reference):** Enable Cloud Streaming toggle + end-date/time + 30‑day cap →
PR #15946761 (`t-melanichen/playtest-streaming-enable-flag`). See
[`expiration-cap-30-days.md`](./expiration-cap-30-days.md).

Service legend: **xPlaytest** = `Xbox.Xbet.Service` · **CTIN** = `services.contentingestion` ·
**SAGE** = `services.serviceapigateway` · **PTNR** = `services.partnerregistry` ·
**AUTH** = `services.auth` · **CAS/GSSV** = Content Access / Game Streaming Services.

---

## #1 — Surface the shareable streaming link in the portal  ·  P0  ·  FE 🟢 / E2E 🟡

**Goal:** "Xplaytest portal has a link that can be shared to members of the playtest that lets them
stream." After a streaming playtest is published & ready, show/copy the launch URL
`https://play.xbox.com/play/launch/{productId}?offering.id=xpt{PlaytestProductId}`.

**Status:** not started. A non‑streaming `SharePlaytestModal` already exists.

### Frontend (`apps/packages/src`)
1. Extend `components/PlaytestList/SharePlaytestModal.tsx` (and/or `PlaytestReview`) to render the
   **streaming launch URL** with a copy button when `enableCloudStreaming` is true.
2. Read the URL + streaming status from `data/dataServices/playtestDataService.ts`
   (add `streamingLaunchUrl` / `streamingStatus` to the playtest model in `models/playtest.ts`).
3. Gate the link on `streamingStatus === StreamingReady`; show a "preparing…" state otherwise.
4. Strings in `localization/strings/strings*.json`; tests + storyshot updates.

### Backend (per service)
- **xPlaytest** (`Xbox.Xbet.Service`): when ingestion is terminal and the offering is live, set
  `PlaytestStatus = StreamingReady`, compute & persist the launch URL, and **expose both on the
  playtest GET contract** so the portal can read them. (Ties to the publish workflow / payload
  builder, PR #15834601.)
- **CTIN** (`services.contentingestion`): report terminal ingestion status (the existing
  `PlaytestIngestionWorkflow` poll) so xPlaytest knows "ready".
- **SAGE** (`services.serviceapigateway`): proxy the status/poll route (PR #15829639).
- **PTNR** (`services.partnerregistry`): offering + title must be live (`ConfigurePlaytestAsync`).

### Dependencies / blockers
- [`launch-link-and-status-accuracy.md`](./launch-link-and-status-accuracy.md) — XProduct is async, so
  status can read "ready" before it truly is (404 window). The link must not surface until truly live.
- [`s2s-cross-tenant-call.md`](./s2s-cross-tenant-call.md), [`Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md).

### Acceptance
Publish a streaming playtest → within seconds the portal shows a copyable launch URL that, when
opened, reaches Bayside and streams (no 404).

---

## #2 — Xbox‑Live‑ID‑only audience restriction when streaming is enabled  ·  P0  ·  🟡

**Goal:** "Updating the private audience access list / groups for a playtest updates the offering."
When streaming is on, restrict the audience to groups backed by **Xbox Live IDs**.

**Status:** not started (audience UI exists for the non‑streaming flow).

### Frontend (`apps/packages/src`)
1. In `components/AudienceSelection/AudienceSelection.tsx` (or the playtest form's audience field),
   when `enableCloudStreaming` is true, **filter selectable groups** to Xbox‑Live‑ID‑backed ones.
2. Source group backing from `data/dataServices/playtestAudienceGroupsDataService.ts` (add/consume a
   flag indicating Xbox‑Live‑ID backing per group).
3. Add a validation error (selected a non‑XL group while streaming) using the
   `playtestServiceErrorMap` pattern in `constants/playtest.ts`; wire into `playtestFormSchema.ts`.
4. Strings + tests.

### Backend (per service)
- **PTNR** (`services.partnerregistry`): offering auth already uses `AllowedDnaGroups`
  (PR #15732852); the selected groups must map to DNA groups backed by Xbox Live IDs.
- **AUTH** (`services.auth`): enforces `AllowedDnaGroups` at login (PR #15738761) — already done.
- **Audience groups source**: the groups backend must expose which groups are Xbox‑Live‑ID‑backed
  (new field, or derive from group type).

### Dependencies
- DNA‑group → Xbox‑Live‑ID backing metadata must be available to the audience data service.

### Acceptance
With streaming on, only XL‑backed groups are selectable; choosing an unsupported group blocks
submit with a clear error; the chosen group flows to `AllowedDnaGroups` on the offering.

---

## #3 — "Build ready for testing" status feedback  ·  P2 (stretch)  ·  🟡

**Goal:** "xplaytest portal has user feedback about when the build is 'ready for testing' across
different endpoints."

### Frontend (`apps/packages/src`)
1. Add a per‑endpoint readiness badge (download vs streaming) in `PlaytestReview`/`PlaytestList`.
2. Poll/consume the readiness fields from `playtestDataService.ts`.

### Backend (per service)
- **xPlaytest**: expose per‑endpoint readiness (download‑ready vs streaming‑ready) on the playtest.
- **CTIN**: ingestion progress + **PC install‑readiness** must roll up into the streaming‑ready signal.
- **SAGE**: proxy.

### Dependencies
- [`pc-install-readiness-polling-implementation.md`](./pc-install-readiness-polling-implementation.md),
  [`launch-link-and-status-accuracy.md`](./launch-link-and-status-accuracy.md).

### Acceptance
Portal shows an accurate, auto‑updating "ready to stream" indicator after a build is ingested.

---

## #4 — Launch args / streaming region / touch controls / feedback config  ·  P3 (stretch)  ·  🔴

**Goal:** P3 items — creators configure launch args, streaming region, touch controls; collect
playtester feedback.

### Frontend (`apps/packages/src`)
1. New optional fields in the playtest wizard (launch args, region select, touch‑controls toggle).
2. A feedback view (if Partner Center surfaces playtester feedback).

### Backend (per service)
- **GSSV/CAS**: private‑offering config must accept region / touch‑controls / launch‑args.
- **xPlaytest**: persist and pass these through the ingestion payload; encode launch args into the link.
- **PTNR**: offering config already sets regions/id naming (PR #15815668) — extend for the rest.
- **Feedback**: a backend store + endpoint to funnel feedback to the studio.

### Dependencies
- Cross‑team GSSV support; out of scope for the core internship (P3).

### Acceptance
Creator sets region/touch/launch‑args → reflected in the streamed session; feedback reaches the studio.

---

## Sequencing (Partner Center)
1. **#1 share link** (highest value; FE mostly done via `SharePlaytestModal`) — unblock once xPlaytest
   exposes the URL/status.
2. **#2 audience restriction** (self‑contained FE + validation).
3. **#3 status feedback** (after readiness signals exist).
4. **#4** P3 stretch.

## References
- `Context/InternProjectDocument.pdf` (pg3 flow; pg4–5 P0/P1/P3).
- `.github/agents/playtest-streaming.md` ("Partner Center UI changes").
- `Repos/Xbox.Gpx.PartnerCenter.Client.md`, `FuturePlans/ui-pr-templates.md`.
