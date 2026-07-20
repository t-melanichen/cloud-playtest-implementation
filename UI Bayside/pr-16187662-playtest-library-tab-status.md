# Bayside "My playtests" tab — PR 16187662 status & roadmap

**PR:** `16187662` (draft) — *feat(play-xbox/library): add hydrated My playtests tab*
**Repo/branch:** Xbox.JS · `t-melanichen/playtest-library-tab`
**Net change:** ~2,610 insertions / 96 deletions across 35 files
**Last update:** merged `origin/main`, resolved 3 conflicts, lint gate clean (0 errors).

---

## 1. What this PR implements

A signed-in tester on play.xbox.com gets a **"My playtests" tab** in the library that lists
every playtest they're authorized to stream, with real game name + box art, and launches the
cloud stream on click.

### Discovery & gating
- **`usePlaytestOfferings` hook** (`utils/usePlaytestOfferings.ts`, +80) — derives the `xpt`-prefixed
  offerings from the auth `additionalOfferings` query, then **vets each one** against
  `additionalOfferingAccess` and returns only offerings that resolve to `accessible`. A fat-fingered
  or revoked `xpt…` id never lights up the tab. Shared by the tab header (show/hide) and the tab body
  (render a rail per offering) so both read access from one source.
- **Auto-include** (`GameStreamAuthenticationServiceSystem.ts`, AB#63139296) — the user's own `xpt`
  offerings are unioned into `additionalOfferings`, derived from the already-fetched offerings list.
  No config write, **no extra network cost**. The Playtests tab populates without a manual dev-settings
  add. `removeAdditionalOffering` no-ops for playtest offerings (they'd re-derive anyway).
- **Tab** (`TabsHeader.tsx`, +43) — a new `playtests` library tab, only rendered when the user has ≥1
  authorized playtest offering.

### Rendering
- **`PlaytestSection.tsx`** (+408) — one labelled **rail per offering**; a heading shows only when the
  offering has a friendly name (raw `xpt…` ids are suppressed as dev noise). Full loading / error /
  empty / **not-invited** states.
- **`PlaytestTile`** — shows the **hydrated friendly title + box art** (`ResponsiveImage`), or falls
  back to the branded pink square + beaker glyph when hydration hasn't resolved. Tiles are sized from
  the same responsive grid config the main library uses, so they match game tiles at every breakpoint.
- **Batched hydration** — one hydration query per rail (not per tile) for the rail's product ids.

### Hydration (the name/box-art data path)
- Authenticated **`BaysideLowUserTopaz0`** hydration via `catalog.gamepass.com/v3/products`
  (`CatalogSystem.ts` +269, `CatalogServiceSystem.ts` +53, `+CatalogServiceAdaptor.ts` +50,
  `hydrationType.ts`, service-sdk `types.ts`). Auth contract: **`X-Store-Authorization` header + MDollar
  token** (minted via `catalog.mp.microsoft.com`). `getPlaytestProductInfoQueryOptions` + authenticated
  `basic`/`detailed` fallback so a private playtest product resolves for signed-in users.

### Launch
- Pressing a tile calls `setActiveOfferingId({ offeringId, shouldPersist: true })` **then** navigates to
  `/stream/{productId}/{titleId}` — switching the active offering first so the stream page resolves the
  private title under its own offering.

### Types, tests, locales
- `isPlaytestOffering` / `PLAYTEST_OFFERING_PREFIX = 'xpt'` (`types-game-stream/offerings.ts`);
  streaming/tier config additions.
- Tests: `PlaytestSection.test.tsx` (+275), `usePlaytestOfferings.test.tsx` (+165), auth system (+88),
  service-sdk catalog tests.
- Locales: `LibraryPlaytestSection.json` (rail strings), `Library.json` (tab label).

---

## 2. What's left to do (this PR)

- [ ] **Publish the PR** — it's a **draft**. Move to active, add reviewers (Bayside owners), work the
      review (`PR-16187662-code-comments.txt` tracks open comments).
- [ ] **Confirm the build gate is green** now that the branch is updated from main (merge-conflict +
      Nx lint-affected failures were caused by the stale branch; both addressed).
- [ ] **In-browser end-to-end verify (signed in):** tab appears → real name + box art render → tile
      click activates offering → `/stream/...` launches and plays. Requires SW unregister + clear site
      data. (Hydration returning HTTP 200 with real title/box art was already verified; the full
      click-to-stream path still needs a visual pass.)
- [ ] **Locale ambiguity warnings** — `no-stale-translations` warnings on `rail_loading` ("games"),
      "Last week"/"Last month". Non-blocking, but add the ambiguity tags to clear them.
- [ ] **`prefer-shared-query` warnings** — a few `useQuery` sites; suppress with a justified
      `// eslint-disable-next-line` or migrate to `useSharedQuery` where there's no per-consumer override.
- [ ] **Full `tsc -b` typecheck** — skipped locally (whole-graph build is slow on this box); CI covers it.

---

## 3. What else would be good in Bayside for the intern project

Grouped by value. Items marked (AB#) already have a work item.

### Complete the tester flow
- **Playtest PDP / landing surface** (AB#62876672) — today a tile launches straight to `/stream`.
  A minimal dedicated playtest PDP (box art + title + Play) was prototyped on the older
  `playtest-library-ui` branch; decide: intentional direct-launch, or land the minimal PDP as the
  click target so the shareable link has a home on play.xbox.com.
- **Shareable-link deep-link** — open a `?offeringId=` / product link straight into the Playtests tab
  (or stream), so the Partner Center launch link and the Bayside tab converge.
- **Stream-entry polish** (AB#62876673) — loading/hand-off UX between tile press and stream start.

### Edge states & correctness
- **Edge states + telemetry** (AB#62876674) — expired playtest, invite revoked mid-session, an offering
  whose build isn't installable/streamable yet, zero-playtests empty state. Add an open→stream funnel.
- **Friendly-name fallback** — when hydration fails, the tile currently shows nothing/raw id; the
  underlying registry bug (`Title.FriendlyName = TitleId`) is the root cause. Track the graceful
  fallback here even after the registry fix.
- **"Title not Xbox Live configured" / licensing** — the cloud-stream launch can fail at license
  acquisition (AB#63137135 / 63137141). Surface a clear tester-facing message rather than a raw error.

### Quality bar
- **Accessibility** — keyboard + gamepad navigation across the tab and rails, `aria` labels on tiles,
  focus order, reduced-motion.
- **Localization** — clear the ambiguity warnings; make sure all new strings are translatable and the
  rail/empty states read well.
- **Analytics** — page/impression + click telemetry for the Playtests tab (adoption metric for the
  intern write-up).

### Longer horizon
- **Console (non-PC) playtests** — the tab/launch currently assumes PC streaming; generalize when
  console streaming ships (AB#62881045).
- **Refresh/invalidation** — re-derive offerings when an invite changes without a full reload.

---

## Key files (Xbox.JS)
- `packages/@play-xbox/-route/library/src/components/PlaytestSection/PlaytestSection.tsx` — rail + tile UI + launch
- `packages/@play-xbox/-route/library/src/utils/usePlaytestOfferings.ts` — discovery + access vetting
- `packages/@play-xbox/-route/library/src/LibraryPage.tsx` — `activeView` routing incl. `playtests`
- `packages/@play-xbox/-route/library/src/components/TabsHeader/TabsHeader.tsx` — the tab
- `packages/@play-xbox/-system/catalog/src/CatalogSystem.ts` — `BaysideLowUserTopaz0` hydration + fallback
- `packages/@play-xbox/-system/-service/catalog/src/CatalogServiceSystem.ts` — X-Store-Authorization + MDollar token
- `packages/@play-xbox/-system/-service/-game-stream/authentication/src/GameStreamAuthenticationServiceSystem.ts` — auto-include + `setActiveOfferingId`
- `packages/@play-xbox/-types/game-stream/src/offerings.ts` — `isPlaytestOffering`
