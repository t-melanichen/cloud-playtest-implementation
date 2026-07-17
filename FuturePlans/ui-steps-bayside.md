# UI implementation steps — Bayside (play.xbox.com player client)

**Repo (frontend):** `Xbox.JS` → `apps/play-xbox` (+ `packages/@play-xbox/*`).
**Scope:** the remaining player-facing UI pieces from `Context/InternProjectDocument.pdf` not yet in a
PR, each broken into frontend + backend (per service) steps. Effort: 🟢 easy · 🟡 medium · 🔴 hard.

**Foundation already in a PR:** **C1** — the launch link's `offeringId` is threaded into the active
offering before streaming (`apps/play-xbox/src/app/routes/CloudConsoleStreamRoute.tsx`,
PR #15946666). Everything below builds on C1. Full design:
[`bayside-playxbox-playtest-modifications.md`](./bayside-playxbox-playtest-modifications.md).

Service legend: **AUTH** = `services.auth` · **PTNR** = `services.partnerregistry` ·
**CAS/GSSV** = Content Access / Game Streaming Services (`/offerings`, catalog) ·
**CTIN** = `services.contentingestion` · **xPlaytest** = `Xbox.Xbet.Service`.

---

## #0 (foundation, partially done) — stream-start against the playtest offering  ·  P0/P1

C1 sets the **active** offering from `?offering.id`. The deeper wire — passing the offering id directly
into `gameStream.cloudConnect(...)` (`useSessionConnect.ts:466-485`) — is a **cross-team open
question**: does the cloud session-allocation API accept an offering id today, or is a platform change
needed? Resolve this with the game-stream/auth package owners before relying on allocation targeting.
**Effort 🔴 (cross-team).**

---

## #5 — Login-first gate + no-leak "not in this playtest" denial UX  ·  P0/P1  ·  🟢–🟡

**Goal:** "Members not part of the playtest do not see any information…Bayside does not leak details"
and "player gets logged in first (before revealing any details)."

**Status:** partially covered by existing machinery; no dedicated playtest gate/denial page.

### Frontend (`Xbox.JS`)
1. **Login-first:** confirm an unauthenticated tester is sent through auth before any render for
   private offerings — the offering-scoped `activeOfferingStreamUser`
   (`CloudStreamingClientSideContext.tsx:157-160`) + the loader's `isPrivate` early-return
   (`packages/@play-xbox/-route/game-stream/src/loader.server.ts`) already do most of this. Add an
   explicit gate modeled on `apps/play-xbox/src/app/layouts/InsiderPreviewGateLayout.tsx` only if a
   leak path is found.
2. **Denial UX:** on `OfferingAccessDeniedError` (`GameStreamPage.tsx:44`) the existing
   `OfferingErrorPage.tsx` already renders with no title details — add playtest-specific copy
   ("You're not part of this playtest — ask the creator for access").
3. Tests for both the gated (not-signed-in) and denied (signed-in, not-eligible) paths.

### Backend (per service)
- **AUTH** (`services.auth`): delegated playtest login enforces `AllowedDnaGroups` (PR #15738761) and
  the offering's `AuthenticationOptions = Xbox` (PR #15892276) → returns `OfferingAccessDenied` for
  non-members. **Done.**
- **PTNR** (`services.partnerregistry`): offering carries `AllowedDnaGroups` + `AuthenticationOptions`.
  **Done.**
- **CAS/GSSV**: `/offerings` must return the private offering **only** to authorized users (service-
  level no-leak), so a non-member never learns it exists.

### Dependencies
- Builds directly on C1. No new backend work — mostly FE wiring + copy.

### Acceptance
Non-member opens the link → logged in first, then sees a clean "not in this playtest" page with **no**
title/art/metadata. Eligible member proceeds.

---

## #6 — Playtest title/genre/art metadata display  ·  P0  ·  🟢 (FE) — CAS shipped; gated on the xToken playtest claim

**Goal:** "testers know this is a non-public version…as much metadata as possible (title, genre, art)
…is available to be seen."

### Frontend (`Xbox.JS`)
1. Surface the playtest title/art/genre from **CAS hydration** (see backend), keyed to the active
   playtest offering, on the tile and the PDP.
2. When metadata is not yet available, render a playtest-aware placeholder (the library "My playtests"
   tab already does this — a beaker placeholder tile captioned with the product id).
3. **Playtest badge** — a white beaker on a pink box, lower-left, overlaying the tile art (and beside
   the title on the PDP), so testers know it is a non-public build. Design: Chris / design team;
   reference `Documentation\playtest-badge-beaker.png`.

### Backend (per service)
- **CAS / Catalog / Hydration** — *CAS shipped this (≈2026-07); no CAS service work remains.* A private
  playtest product is **never** in the retail Display Catalog ("big cat"); its title/art/genre come from
  **CAS (Content Access Service) hydration**. CAS made Playtest a **standard access type** and now
  returns playtest data whenever it sees a **new xToken _playtest user claim_** (created by the playtest
  team) in the caller's token — gating that matches #5 no-leak. CAS has **no client-specific
  endpoints/contracts**; the client just consumes the shared hydration proto.
  **Client action (Bayside):** (1) get the caller's **xToken to carry the playtest claim** — owner
  **Anthony Keller** (playtest lead); (2) **snag the new contract proto** into
  `packages/@xbox-js/-service-sdk/catalog/src/hydration/baysideTypes.ts` if CAS added fields (today it
  vends `BaysideLowTopaz0` = the "Topaz 0" contract, which **already** carries `title`, `KeyArt` (art)
  and `Categories` (genre)). **Bayside is already wired:** the PDP hydrates via `CatalogSystem`
  (`packages/@play-xbox/-system/catalog/src/CatalogSystem.ts`), which already special-cases private
  offerings (skeleton-from-title-info fallback + `augment*ForPrivateOffering`). So once the token carries
  the claim, the existing PDP should render the metadata with little/no new FE code.
- **xPlaytest / XProduct**: ensures the product entry (name/art/genre) exists for the playtest.

### Dependencies
- **Resolved (6/30 Design Brainstorm; confirmed 2026-07-02 CAS thread):** metadata does **not** come
  from big cat — it comes from CAS hydration, which CAS has now **shipped**, gated on the xToken
  playtest claim (see `Explanations\transcript-decisions.md` → "CAS shipped playtest hydration").
- **Owners to enlist:** **Anthony Keller** (playtest lead — how to get the xToken _playtest claim_
  minted for test users + gotchas). CAS itself needs **no service work**; **Oscar** / the **CAS team**
  (Juno-side relationship) remain useful context only.

### Acceptance
Eligible tester sees correct title, art (and genre if available) for the private build before/while
streaming.

---

## #7 — "Install locally vs stream now" choice  ·  P0 (install side overlaps P3)  ·  🔴

**Goal:** "testers are offered the option to either install locally or stream now."

### Frontend (`Xbox.JS`)
1. New choice UI on the playtest entry: **Stream now** → existing cloud-stream flow; **Install** →
   Garrison/Bastion install path.
2. Conditional rendering based on which endpoints the offering/build supports.

### Backend (per service)
- **Garrison / Bastion**: must support private-offering playtests for the "install" branch (P3 in the
  intern doc — "Currently xplaytest is supporting Garrison… Ideally Garrison/Bastion will support
  private offering playtests").
- **xPlaytest**: already provides the download/install path; expose both endpoints' availability.

### Dependencies
- Garrison/Bastion private-offering support (P3) — largest unknown; this is the hardest item.

### Acceptance
Tester sees both options when supported; each launches the correct experience.

---

## #8 — "Build still preparing" / not-live-yet retry state  ·  P0  ·  🟡 (FE) gated on backend

**Goal:** "A few seconds/minutes after uploading a new build, launching streaming will use the new
version" — handle the window where the offering is live but no PC server has the build yet.

### Frontend (`Xbox.JS`)
1. In the stream route/loader, when the offering is live but allocation/title 404s (no PC server has the
   build), show a **"preparing your playtest, keep trying" retry** state instead of a hard error.
2. Reuse/extend the existing error boundary (`apps/play-xbox/src/app/routes/root/ErrorBoundary.tsx`).

### Backend (per service)
- **CTIN** (`services.contentingestion`): PC **install-readiness polling** must determine when a PC
  build is installed/streamable and surface a signal (PR #15896502, draft).
- **PC Orchestrator / GSSV**: query whether a PC server has the content
  (`IPCOrchestratorClient.QueryServersPagedAsync` with `ContentFileFilter{Id=installId, Version=hash}`)
  — the PC-fork of the install-readiness path.

### Dependencies
- [`pc-install-readiness-polling-implementation.md`](./pc-install-readiness-polling-implementation.md),
  [`Blockers/pc-install-readiness-poll.md`](../Blockers/pc-install-readiness-poll.md).

### Acceptance
Click the link right after a build upload → friendly "preparing" + auto-retry until the PC build is
streamable, instead of a 404/error.

---

## #9 — Feature-flag gating of the Bayside playtest entry  ·  P1 (ship dark)  ·  🟡

**Goal:** ship the playtest wiring dark, lit up only for allow-listed sellers/preview.

### Frontend (`Xbox.JS`)
1. Gate the `offeringId`→`setActiveOfferingId` wiring (and new UX) behind a flag. Bayside already uses
   config/experiment flags (`InsiderPreviewGateLayout.tsx:23-37`,
   `ProductDetailPageSystem.ts:124-137`) and env files (`src/server/utils/env.ts:16-40`).

### Backend (per service)
- **ECS**: config to gate by seller id (private preview). David K owns ECS setup; **deployment
  required** to change ECS values.

### Dependencies
- [`ecs-feature-flag.md`](./ecs-feature-flag.md). Open: ECS vs env vs existing preview-gate; ECS
  reachable from the front end today.

### Acceptance
With the flag off, retail path is unchanged; on (for allow-listed sellers), the playtest flow lights up.

---

## Sequencing (Bayside)
1. **#5 + #6** (denial/no-leak + metadata) — sit directly on the merged C1 wire, reuse existing
   components; easiest high-value next PR.
2. **#9 flag gating** (ship dark) — small once the flag system is chosen.
3. **#8 preparing/retry** — once CTIN PC install-readiness signal exists.
4. **#0 cloudConnect offering param** — resolve the cross-team API question.
5. **#7 install-vs-stream** — largest; needs Garrison/Bastion (P3).

## References
- `Context/InternProjectDocument.pdf` (pg3 #5–8; pg4–5 P0/P1).
- `FuturePlans/bayside-playxbox-playtest-modifications.md` (file-by-file C1–C6 / W1–W7).
- `FuturePlans/ui-pr-templates.md`, `Repos/Xbox.JS.md`.
