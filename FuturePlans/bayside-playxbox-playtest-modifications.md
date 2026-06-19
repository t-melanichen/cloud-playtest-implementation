# Future plan: Bayside (Play Xbox) playtest streaming-link modifications

**Repo:** `Xbox.JS` → `apps/play-xbox` (**Bayside** = the play.xbox.com cloud-gaming web client).
**Active branch:** _tbd_ (`t-melanichen/playxbox-playtest-launch` off `main`).
**Status:** Planning — no code written yet.

## Why it matters
Bayside is the surface a **playtester lands on when they click the shared streaming link**. The
rest of the project (xPlaytest → SAGE → contentingestion → offering/title) makes a playtest build
*streamable*; Bayside is what actually *renders and starts the stream* for that build. Today Bayside
is wired entirely around a **retail `productId`** — it has no concept of starting a stream against a
**playtest offering** (`xpt{PlaytestProductId}`), no eligibility/"not in this playtest" UX, and no
handling for the PC "build isn't installed yet" window. Without changes, a tester who clicks the link
either streams the wrong (retail) offering, hits a generic 404/error, or gets denied with no
explanation.

## The launch link (the contract Bayside must honor)
From `FuturePlans/launch-link-and-status-accuracy.md` (Sync 3 — Anthony), the shareable link is:

```
https://play.xbox.com/play/launch/{productId}?offeringId=xpt{PlaytestProductId}
```

So the **only** playtest-specific signal Bayside receives is the **`offeringId` query param**. Everything
hinges on threading that value from the URL down into the stream-start path and the offering-scoped
auth/login. The offering id convention is literal `xpt` + `PlaytestProductId`, no hyphen, no hashing
(see `.github/agents/playtest-streaming.md` "Key conventions").

## Current behavior in Bayside (as-built, cited)
- **Link transform preserves the query string.** `/play/launch/:productId` redirects to
  `/stream/:productId`, and the original `URLSearchParams` are carried through unchanged
  (`src/server/middleware/edgewaterLinkTransformation.ts:243-289`, final URL built as `path?search`
  at `156-158`). ✅ Good news: `?offeringId=...` *survives* to the stream route.
- **But nothing reads it.** The stream route reads only the `productId` **path** param and never the
  query (`src/app/routes/CloudConsoleStreamRoute.tsx:18-36`). `GameStreamPage` takes only
  `productId`/`serverId` props — no `useSearchParams`
  (`packages/@play-xbox/-route/game-stream/src/GameStreamPage.tsx:15-40,75-120`).
- **Stream start is `productId`-driven, no offering concept.** Bootstrap chain:
  `CloudStreamingClientSideContext.tsx:147-207` → `GameStreamBootstrapper` → `useSessionConnect`.
  - Auth user: `authentication.queries.activeOfferingStreamUser.getActiveUserQuery()`
    (`CloudStreamingClientSideContext.tsx:157-160`) — note this is already **offering-scoped**, the
    natural seam for a playtest offering.
  - Title info: `play.queries.titleInfo...getOptions({ id: productId, idType: 'productId' })`
    (`161-164`).
  - Launch call: `gameStream.cloudConnect(config.titleInfo, { options, … }, …)`
    (`useSessionConnect.ts:466-485`) — **no `offeringId` is passed today.**
- **Metadata is retail-catalog keyed by `productId`** (`titleInfo`/`productInfo`; background image and
  title name at `GameStreamPage.tsx:83-105`, `useSessionConnect.ts:212-221`). A generated playtest
  product is a real (but private/DNA-gated) XProduct entry, so catalog lookup *should* resolve, but
  this needs validation for private products.
- **Auth gating today is generic signed-in state** (`ProductDetailPageSystem.ts:292-365`,
  `isFullySignedIn`). The delegated playtest login (`/v2/login/user/delegated`, DNA-group gated, Xbox
  gamertag claim) and its `OfferingAccessDenied` live server-side; Bayside surfaces an offering-denied
  error inside `GameStreamPage.tsx:36-50`.
- **Access-gate precedent exists:** `InsiderPreviewGateLayout.tsx:23-90` already implements
  "config-flag + access-allowed + welcome-dialog → outlet, else gate page" — a strong model to reuse
  for playtest eligibility.

## Running Bayside locally (to develop/test these changes)
`yarn nx start play-xbox` is the **last** step of a prerequisite chain (per
`Xbox.JS/docs/How Tos/Installation and Setup/`; on Windows the **WSL** path is recommended).

Prerequisites: Node **v24.13.0** (`.nvmrc`), Yarn **4.12.0** via Corepack
(`package.json` `"packageManager"`), and ADO package auth.

```bash
corepack enable && corepack install         # activate Yarn 4.12.0
yarn auth                                   # ADO auth for private @xbox-js/@play-xbox packages
yarn                                        # install the whole monorepo (slow first run)
yarn nx setup:dev play-xbox --force         # REQUIRED: dev certs + local.play.xbox.com hosts entry
yarn nx start play-xbox                      # start Bayside
```
Open **`https://local.play.xbox.com:1337`** (not `localhost`).

What it runs: the `nx:start` target (`apps/play-xbox/project.json:208-216`) with
`dependsOn: ["build:server","setup:dev:check"]` → compiles the SSR server, verifies certs (fails fast
if missing — `scripts/setup-dev.mjs:93-108`), then
`NODE_ENV=development node --import tsx/esm --inspect build/server/index.js`. For a fast inner loop use
`yarn nx dev-ts play-xbox` (`tsx watch`, hot reload). `setup:dev` generates a local root CA + SSL cert
(`~/.play-xbox/certs/`) and the hosts entry (needs admin/UAC).

## How it works end-to-end (step by step)
Mapped to the intern project doc (`Context/InternProjectDocument.pdf`) P0/P1 objectives.

**Setup (before the click):** Creator checks "Enable Cloud Streaming" in xPlaytest → a private
offering `xpt{PlaytestProductId}` is created, DNA-group gated, with one title bound to the latest
build (intern-doc P0 #2–4). xPlaytest crafts the URL
`https://play.xbox.com/play/launch/{productId}?offeringId=xpt{PlaytestProductId}` (intern-doc P0:
"craft a URL usable for streaming").

1. **Click → land in Bayside** (intern-doc P1: "takes the user to an Xbox Gaming Endpoint (Bayside)").
   `edgewaterLinkTransformation.ts:243-289` redirects `/play/launch/{productId}` → `/stream/{productId}`,
   **preserving `?offeringId`**. ✅ Already works.
2. **Log in FIRST, reveal nothing yet** (intern-doc P1: "player gets logged in first (before revealing
   any details)"; P0: "Members not part of the playtest do not see any information"). New playtest gate
   modeled on `InsiderPreviewGateLayout.tsx:23-90`. → W2/W4.
3. **Authenticate against the playtest offering / DNA-group check** (intern-doc P0: "checked during
   offering 'login'"). Thread `offeringId` into `activeOfferingStreamUser`
   (`CloudStreamingClientSideContext.tsx:157-160`); delegated login validates DNA-group + gamertag. → W1/W2.
4. **Not eligible → deny without leaking** (intern-doc P0: "Bayside does not leak details… to members
   not in it"). On `OfferingAccessDenied` (`GameStreamPage.tsx:36-50`) show a "not in this playtest"
   page, not a 404, not metadata. → W4.
5. **Eligible → render the non-public title** (intern-doc page-3 #6: title/art available). `titleInfo`/
   `productInfo` by `productId` (`useStreamConnectConfig.ts`), art at `GameStreamPage.tsx:83-105`;
   validate catalog serves a private product. → W3.
6. **Start the stream against the playtest offering** (intern-doc P0 #7/8, P1: "streams successfully
   started"). Pass `offeringId` into `gameStream.cloudConnect(...)` (`useSessionConnect.ts:466-485`) so
   allocation targets the private offering — **not done today**. → W1 (core).
7. **New build just uploaded → newest version** (intern-doc P0: "launching streaming uses the new
   version"). For PC the build lands on-demand; if no server has it yet, show "preparing, keep trying"
   retry instead of failing. → W5/W6.
8. **Stream + feedback** (intern-doc page-3 #8). Stream runs; feedback funnels via xPlaytest (P3,
   out of Bayside scope).

**One-line summary:** Bayside today is entirely retail-`productId`-driven and ignores `offeringId`; the
project reduces to threading `offeringId` into (a) offering-scoped login and (b) `cloudConnect`, wrapped
with login-first gating and leak-proof denial UX.

## What already exists in Bayside (key discovery)
Bayside already has a full **offering** subsystem — the intern work is mostly *wiring the launch link into it*, not building it:
- **Active-offering state + setter mutation:** `gameStream.authentication.mutations.setActiveOfferingId({ offeringId, shouldPersist })` and `resetOfferingId`, plus queries `activeOfferingId`, `activeOfferingInfo`, `offerings` (user's **private** offerings), `publicOfferings`, `defaultOfferingId`. Proven in the Developer settings tab where a user manually switches offerings (`packages/@play-xbox/-dialog/-route/settings/.../DeveloperTab/OfferingInfo.tsx:336-408`).
- **Offering-scoped login already wired:** `activeOfferingStreamUser` (`CloudStreamingClientSideContext.tsx:157-160`) logs the user into the *active* offering via `/v2/login/user[/delegated]` (`packages/@xbox-js/-game-stream/auth-service/src/AuthenticationService.ts:55-89`) — the DNA-gated playtest login.
- **Private-offering no-leak already partially handled:** the stream loader fetches `activeOfferingInfo` and, when `isPrivate`, **returns early without hydrating retail product metadata** (`packages/@play-xbox/-route/game-stream/src/loader.server.ts` — "Avoid throwing hydration errors for private offerings").
- **Denial UX already exists:** `OfferingErrorPage.tsx` (rendered on `OfferingAccessDeniedError`, `GameStreamPage.tsx:44`) shows "Cannot connect to the requested streaming offering. Please ensure you have access" with an enrollment CTA and **no title details** — satisfies the no-leak requirement.
- **`offeringId` is already a known query string** in the older edgewater stack (`packages/xbox-web-partner-edgewater/src/routes/routes.ts:408`, cookie `gs_of_id` at `constants/cookies.ts:8`). The intern doc confirms: *"private offering support is possible today in the web cloud streaming endpoint."*

**=> The one missing wire:** nothing in the new play-xbox `/stream/:productId` flow reads `?offeringId=` and calls `setActiveOfferingId`. That is the core intern change.

## Concrete code changes (file-by-file)

### C1 — Apply `offeringId` from the launch link (the core change)
- **`apps/play-xbox/src/app/routes/CloudConsoleStreamRoute.tsx`** — read the query param and set the active offering before streaming:
  - `const [searchParams] = useSearchParams(); const offeringId = searchParams.get('offeringId');`
  - get `setActiveOfferingId` from `useSystems().services.gameStream.authentication.mutations`, and in an effect call `setActiveOfferingId({ offeringId, shouldPersist: true })` when `offeringId` is present and differs from the current `activeOfferingId` (mirror `OfferingInfo.tsx:388-396`). Optionally hold rendering of `<GameStreamPage>` until the active offering matches, so login/metadata run under the playtest offering.
- **`packages/@play-xbox/-route/game-stream/src/loader.server.ts`** — parse `offeringId` from `request.url` and set it as the active offering (cookie, same key the offering subsystem reads) **before** `activeOfferingInfo`/product fetch, so SSR resolves the private offering and the existing `isPrivate` early-return (no-leak) path applies on the very first paint.

### C2 — Login-first + no-leak (verify; likely minimal)
- Ensure an unauthenticated tester is sent through auth before any render. The offering-scoped `activeOfferingStreamUser` + the loader's private-offering guard already cover most of this; confirm `ClientSideRenderGate.tsx` / the `/auth/*` flow blocks render until signed in for private offerings, and add a gate only if a leak path exists.

### C3 — Playtest-tailored denial copy (polish)
- Reuse `OfferingErrorPage.tsx`; optionally branch copy for playtest ("You're not part of this playtest — ask the creator for access"). No new page needed.

### C4 — Playtest title metadata (validate)
- Confirm `play.queries.titleInfo` + `catalog` resolve name/art for a **private** playtest product under the active offering. If not, add a playtest metadata fallback (the page already supports a local fallback). Largely validation.

### C5 — PC "still preparing" + status 404 window (new, additive)
- Add a retry/"preparing your playtest" state for when the offering is live but no PC server has the build yet, instead of a hard error (ties to `pc-install-readiness-polling-implementation.md` and `launch-link-and-status-accuracy.md`).

### C6 — Feature-flag gate (ship dark)
- Gate the `offeringId`→`setActiveOfferingId` wiring behind a flag (align with `ecs-feature-flag.md`); retail path unchanged when off.

## Required modifications (workstreams)

### W1 — Thread `offeringId` from the link into stream start  *(core change)*
1. Read `offeringId` from the query in the stream route
   (`CloudConsoleStreamRoute.tsx`, via `useSearchParams`) and pass it into `GameStreamPage`.
2. Plumb it through `CloudStreamingClientSideContext` → `useStreamConnectConfig` → `useSessionConnect`.
3. Pass `offeringId` into:
   - the offering-scoped auth user query (`activeOfferingStreamUser`) so the **playtest offering's**
     DNA-gated login is used, and
   - the `gameStream.cloudConnect(...)` session config (`useSessionConnect.ts:466-485`) so the session
     is allocated against the playtest offering, not the default retail offering.
4. Backward-compatible: when `offeringId` is absent, behavior is identical to today (retail).

### W2 — Playtest offering authentication / eligibility
- Confirm the offering-scoped stream-user/login path honors the DNA-group + Xbox-gamertag gate that
  the auth service enforces (PR 15738761). Bayside should send the delegated login for the playtest
  offering and treat `OfferingAccessDenied` as the **eligibility signal**.
- Decide whether to pre-check eligibility (gate page) vs. attempt-then-handle-denial. Recommended:
  reuse the `InsiderPreviewGateLayout` pattern for a **playtest gate** (W4) and still handle the
  server denial defensively.

### W3 — Playtest title metadata rendering
- Validate that `titleInfo`/`productInfo` resolve for a **private, DNA-gated playtest product** by
  `productId`. If retail catalog can't serve private products, add a playtest-aware metadata source
  (name/image) or a graceful fallback (the page already supports a local fallback —
  `ProductDetailPage.tsx:68-87`).

### W4 — Access-denied / "not in this playtest" UX
- Add a dedicated denial experience instead of the generic `ErrorPage`/404
  (`src/app/routes/root/ErrorBoundary.tsx:18-95`). Model it on `InsiderPreviewGateLayout.tsx:52-90`:
  clear "you're not part of this playtest / ask the creator for access" messaging keyed off the
  offering-denied error from `GameStreamPage.tsx:36-50`.

### W5 — PC "build still preparing" / first-install wait UX
- PC content lands on-demand; the first install can lag (see
  `FuturePlans/pc-install-readiness-polling-implementation.md` and `Blockers/pc-install-readiness-poll.md`).
  When the offering is live but no PC server has the build yet, Bayside should show a **"preparing your
  playtest, keep trying" / retry** state rather than a hard failure (Timi: "keep trying until ready").

### W6 — Status-accuracy / 404 window
- Coordinate with `FuturePlans/launch-link-and-status-accuracy.md`: because XProduct is async, a link
  clicked immediately can 404. Bayside should degrade gracefully for the "not live yet" window (retry
  + friendly message) instead of a raw not-found.

### W7 — Feature-flag gating
- Gate the entire playtest entry behavior behind a flag so it ships dark and only lights up for
  allow-listed sellers/preview (align with `FuturePlans/ecs-feature-flag.md`). Bayside already uses
  config/experiment flags (`InsiderPreviewGateLayout.tsx:23-37`,
  `ProductDetailPageSystem.ts:124-137`) and env files (`.env.production`,
  `src/server/utils/env.ts:16-40`) — reuse that mechanism rather than inventing one.

## Step list (sequencing)
1. Spike: confirm with the game-stream/auth package owners exactly how `offeringId` should reach the
   offering-scoped login + `cloudConnect` (does the platform session API already accept an offering id,
   or is a new param needed?). **This is the key open dependency.**
2. W1 — thread `offeringId` end-to-end behind the feature flag (W7), retail path unchanged.
3. W3 — verify/added playtest title metadata resolution.
4. W4 — eligibility/denial UX.
5. W5/W6 — preparing/not-live-yet retry states.
6. End-to-end validation against a real DNA-gated playtest offering (the demo title, see
   `FuturePlans/demo-prep-game-selection.md`).

## Open questions
- Does the cloud session-allocation API (`gameStream.cloudConnect` / the play service) accept an
  **offering id** today, or does the platform side need a change first? (Determines whether W1 is
  Bayside-only or cross-team.)
- Can retail catalog (`titleInfo`/`productInfo`) serve metadata for a **private playtest product**, or
  is a separate metadata path required (W3)?
- Eligibility model: **pre-gate** (check before streaming) vs **attempt-then-deny**? (W2/W4)
- Which flag system gates this in Bayside — ECS, the existing preview-gate config, or an env flag? (W7)
- Owner confirmation that `apps/play-xbox` (not `xboxcom-edgewater`) is the only Xbox.JS surface in
  scope (spec lists Xbox.JS role as "TBD" in `.github/agents/playtest-streaming.md`).

## Owners
Melanie Chen · Xbox.JS / Bayside (Play Xbox) game-stream + auth package owners · Anthony Keller
(XProduct status / launch-link).

## References
- `Context/InternProjectDocument.pdf` — intern project objectives (P0/P1 Bayside items: login-first,
  no-leak, stream-start, new-build version).
- `FuturePlans/launch-link-and-status-accuracy.md` — launch URL shape + 404/status-accuracy window.
- `FuturePlans/pc-install-readiness-polling-implementation.md`, `Blockers/pc-install-readiness-poll.md`
  — PC first-install wait (drives W5).
- `FuturePlans/ecs-feature-flag.md` — feature-flag gating model (W7).
- `FuturePlans/demo-prep-game-selection.md` — demo title for end-to-end validation.
- `.github/agents/playtest-streaming.md` — offering-id convention, DNA-group auth, end-to-end flow.
- `FuturePlans/ui-pr-templates.md` — Xbox.JS PR title (Conventional Commits `{type}({scope}): …`) +
  the filled PR description for `t-melanichen/playxbox-playtest-launch`.
- `PRProgress/02-AUTH-15738761-enforce-allowed-dna-groups-login.md`,
  `PRProgress/11-PTNR-15892276-playtest-offering-authentication-type.md` — offering auth / DNA gate.
- Bayside code anchors: `apps/play-xbox/src/server/middleware/edgewaterLinkTransformation.ts:243-289`;
  `apps/play-xbox/src/app/routes/CloudConsoleStreamRoute.tsx:18-36`;
  `packages/@play-xbox/-route/game-stream/src/GameStreamPage.tsx`,
  `…/CloudStreamingClientSideContext.tsx:147-207`, `…/useSessionConnect.ts:466-485`;
  `apps/play-xbox/src/app/layouts/InsiderPreviewGateLayout.tsx:23-90`.
