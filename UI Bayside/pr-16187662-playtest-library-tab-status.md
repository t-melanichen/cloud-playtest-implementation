# Bayside "My playtests" tab — PR 16187662 status, explained

**PR:** `16187662` (draft) — *feat(play-xbox/library): add hydrated My playtests tab*
**Repo/branch:** Xbox.JS · `t-melanichen/playtest-library-tab`
**Net change:** ~2,610 insertions / 96 deletions across 35 files
**State:** merged latest `main`, 3 conflicts resolved, lint gate clean (0 errors), pushed.

> This doc is written to be read start-to-finish by someone new to the codebase (me!). Section 0
> explains the concepts; Section 1 explains what the PR does *and why*; Section 4 is the honest
> "here's what it can't do yet and why" list.

---

## 0. Background concepts (read this first)

**Bayside** is the internal name for the play.xbox.com web app. It's a big client-side system split
into "systems" (data/business logic) and "routes" (pages/UI). My work lives in the **library route**
(`packages/@play-xbox/-route/library`) plus a couple of shared systems.

**Offering.** An "offering" is a catalog/streaming *context* a user can play under — e.g. the public
Game Pass Ultimate web offering (`xgpuweb`). A **playtest** is a private, additive offering whose id
starts with **`xpt`** (e.g. `xpt2sdt4x91krpc`). "Additive" means it's layered on top of your normal
offerings; "private" means only invited users can stream it. The app keeps a list of your extra
offerings called **`additionalOfferings`**.

**Hydration.** The playtest *offering* only gives us an id. To draw a nice tile we need the game's
**friendly name + box art**. "Hydration" is the term for calling a catalog service to turn a bare
product id into that display metadata. Because playtest builds are private, we can't use the normal
anonymous catalog call — we have to make an **authenticated** hydration call that proves who the user
is. That authenticated variant is the hydration type **`BaysideLowUserTopaz0`**.

**The auth contract (the tricky part).** The authenticated hydration call to
`catalog.gamepass.com/v3/products` only works if we send:
- the header **`X-Store-Authorization`** (NOT the usual `Authorization` header — using the wrong one
  returns `400 MissingOrInvalidStoreAuthorization`), and
- a **MDollar token** (an Xbox token minted for the `http://mp.microsoft.com/` audience). The default
  token-mapping (NSAL) maps `*.gamepass.com` to the wrong audience, so we explicitly mint via
  `catalog.mp.microsoft.com`.
This contract was found by trial-and-error and is easy to break; that's why it's isolated in the
catalog service system.

**Tabs / views.** The library page shows one "view" at a time (full library, play history, etc.).
This PR adds a new **`playtests`** view and a tab to switch to it.

**Active offering.** The streaming page figures out *which title to stream* from the user's currently
**active** offering. So to stream a private playtest title, we first have to *switch the active
offering* to that playtest, then navigate to the stream page.

---

## 1. What this PR implements (and why)

### a) Finding the user's playtests — and proving they're allowed
File: `utils/usePlaytestOfferings.ts`

- Reads the auth `additionalOfferings` list and keeps only the `xpt`-prefixed ones.
- **Why the extra check:** an id sitting in that list does **not** prove the user still has access — a
  tester can type a random `xpt…` id into developer settings, and invites get revoked. So each
  candidate is checked against the `additionalOfferingAccess` query and we keep **only** offerings that
  come back `accessible`. This is why the tab won't light up for a revoked or mistyped playtest.
- The same hook feeds both the **tab** (should we show it?) and the **tab body** (render a rail per
  offering), so "does the user have a real playtest" is decided in exactly one place.

### b) Auto-including your playtests (so you don't have to add them by hand)
File: `GameStreamAuthenticationServiceSystem.ts` — commit `83dc3eab7cd`, work item AB#63139296

- Before this, a tester had to manually paste their `xpt` id into a hidden developer panel. Now the
  app **derives** your playtest offerings from the offerings list it *already fetches* (to get names)
  and unions them into `additionalOfferings`.
- **Why it's cheap/safe:** it's derived only — nothing is written to your saved config, and it reuses a
  fetch that already happens, so there's **no extra network call**. If the offerings fetch fails (e.g.
  signed out) it falls back to your saved ids.
- `removeAdditionalOffering` is made a **no-op for playtest offerings** — because they'd just
  re-derive on the next load, and actually removing would delete their per-offering settings.

### c) The tab + the rail/tile UI
Files: `TabsHeader.tsx`, `PlaytestSection.tsx`

- A new **My playtests** tab, shown only when you have ≥1 authorized playtest.
- Inside, **one rail per offering**. A heading appears only when the offering has a *friendly* name (a
  raw `xpt…` id is dev noise, so it's hidden).
- Each game is a **`PlaytestTile`**: shows the hydrated **title + box art** (`ResponsiveImage`), or a
  branded **pink square + beaker** glyph while/if hydration hasn't resolved. Tiles are sized from the
  *same* responsive grid config the main library uses, so they line up perfectly with normal game
  tiles at every screen size.
- Every state is handled: **loading**, **error**, **empty** ("no games yet"), and **not-invited**.

### d) The hydration wiring (name + box art)
Files: `CatalogSystem.ts`, `CatalogServiceSystem.ts`, `+CatalogServiceAdaptor.ts`, `hydrationType.ts`,
service-sdk `types.ts`

- Implements the authenticated `BaysideLowUserTopaz0` path described in Section 0, exposed as
  `getPlaytestProductInfoQueryOptions`, with an authenticated fallback in the `basic`/`detailed`
  catalog queries so a private product resolves for signed-in users.
- **Batched per rail:** one hydration query per rail (for all that rail's product ids) instead of one
  per tile — fewer requests.

### e) Launching the stream
File: `PlaytestSection.tsx` → `navigateToPlaytestStream`

- On tile press: call `setActiveOfferingId({ offeringId, shouldPersist: true })` **then** navigate to
  `/stream/{productId}/{titleId}`. Switching the active offering first is what lets the stream page
  resolve the private title (see "Active offering" in Section 0).

### f) Types, tests, locales
- `isPlaytestOffering` / `PLAYTEST_OFFERING_PREFIX = 'xpt'` (`types-game-stream/offerings.ts`).
- Tests: `PlaytestSection.test.tsx` (+275), `usePlaytestOfferings.test.tsx` (+165), auth system (+88),
  service-sdk catalog tests.
- Locale files for the rail strings + tab label.

---

## 2. What's left to do on THIS PR

- [ ] **Publish the draft PR** and add Bayside reviewers; work the open review comments
      (`PR-16187662-code-comments.txt`).
- [ ] **Confirm the build gate is green** now the branch is updated from `main` (the merge-conflict and
      Nx "Lint Affected" failures were both caused by the branch being ~22 commits stale — now fixed).
- [ ] **End-to-end verify in a real signed-in browser:** tab shows → real name + box art render → tile
      click switches offering → `/stream/...` actually plays. (Hydration returning HTTP 200 with real
      title/art is already proven; the *full click-to-stream* path is the last thing not visually
      confirmed.) Requires unregistering the service worker + clearing site data first.
- [ ] **Clear lint warnings** (non-blocking): locale ambiguity tags (`rail_loading` "games", "Last
      week/month") and a few `prefer-shared-query` `useQuery` sites.
- [ ] **Full `tsc -b` typecheck** — skipped locally (whole-graph build is very slow on this machine);
      CI covers it.

---

## 3. What else would be good in Bayside for the intern project

### Complete the tester flow
- **Playtest PDP / landing page** (AB#62876672): today a tile launches straight into `/stream`. A
  minimal dedicated product page (box art + title + Play) was prototyped on the older
  `playtest-library-ui` branch. Decide: is direct-launch intentional, or should the shareable Partner
  Center link land on a real Bayside page first?
- **Shareable-link deep link:** open a product/`?offeringId=` link straight into the Playtests tab or
  stream, so the Partner Center link and this tab converge on one surface.
- **Stream-entry hand-off polish** (AB#62876673): nicer transition between tile press and stream start.

### Correctness & edge cases
- **Edge states + telemetry** (AB#62876674): expired playtest, invite revoked mid-session, an offering
  whose build isn't installable/streamable yet, and a clean zero-playtests empty state. Add an
  open→stream funnel — great for an adoption metric in the intern write-up.
- **Friendly-name fallback:** if hydration fails, decide what the tile shows (today: box-art-less,
  title-less). The root cause is a registry bug (`Title.FriendlyName = TitleId`); track graceful
  fallback here regardless.
- **Licensing/`title not Xbox Live configured` surfacing** (AB#63137135 / 63137141): the stream can
  fail at license acquisition; show a clear tester-facing message instead of a raw error.

### Quality bar
- **Accessibility:** keyboard + gamepad nav across the tab/rails, `aria` on tiles, focus order,
  reduced-motion.
- **Localization:** clear the ambiguity warnings; make sure new strings translate cleanly.
- **Analytics:** impression + click telemetry for the tab (adoption signal).

### Longer horizon
- **Console (non-PC) playtests** (AB#62881045): the tab/launch assume PC streaming today.
- **Live refresh:** re-derive offerings when an invite changes, without a full page reload.

---

## 4. Limitations (in depth — what it can't do yet, and why)

These aren't bugs to fix before merge necessarily — they're the honest boundaries of the current
design. Understanding them is the point.

**1. Access checks are point-in-time, not live.**
`usePlaytestOfferings` filters to offerings that were `accessible` *at fetch time*. If an invite is
revoked while the user is sitting on the tab, the rail stays visible until React Query refetches. There
is no push/subscription telling Bayside "this invite just changed." Practical effect: a revoked
playtest can look available for a short window, and the eventual failure only shows when the user tries
to stream. **Why:** the offering-access query is request/response with normal cache staleness; there's
no real-time channel wired up.

**2. Auto-include can't be turned off per-playtest.**
Because playtest offerings are *derived* every load, `removeAdditionalOffering` is intentionally a
no-op for them. So a user can't hide a specific playtest from their tab — if they're entitled, it
shows. **Why:** removal wouldn't stick (it'd re-derive) and would also prune the offering's saved
settings. A real "hide" would need a separate suppression list, which doesn't exist yet.

**3. Auto-include depends on the offerings fetch succeeding.**
If the offerings list fails to load (transient error, or signed out), we fall back to only the
*manually persisted* ids. So in a partial-failure state a user's playtests can silently not appear.
There's no retry/backoff specific to this derivation.

**4. The hydration auth contract is fragile and all-or-nothing per rail.**
The `X-Store-Authorization` + MDollar-token contract is non-obvious and easy to break (wrong header →
`400`, wrong audience via NSAL → wrong token). If token minting fails or the contract regresses, tiles
silently fall back to the **beaker placeholder** — the tab still "works" but shows no names/art, which
can look broken to a tester. There's no visible error telling the user *why* hydration didn't resolve.
**Why:** hydration failure is treated as a soft/optional enhancement, not a hard error.

**5. Hydration still costs N requests for N rails.**
Batching is per-*rail* (one query for a rail's product ids), not global. A user in many playtests makes
one hydration call per rail. It also runs client-side after the offerings resolve, so there's a visible
moment where tiles are beakers before names/art pop in.

**6. Tile launch bypasses the product detail page entirely.**
Clicking a tile goes straight to `/stream`. That means **none** of the usual PDP surfaces run: no
content warnings / age gate, no "what is this game" detail, no explicit entitlement/purchase check UI.
For a private internal playtest that's arguably fine, but it's a deliberate shortcut, not a complete
retail flow. If product policy later requires showing warnings before play, this needs a real PDP.

**7. `setActiveOfferingId(..., shouldPersist: true)` is a global, persisted side effect.**
Launching a playtest **changes the user's active offering globally and persists it**. That's required
for the stream page to resolve the title, but it means pressing a playtest tile mutates shared
streaming state that other surfaces read, and it sticks across the session/reload. If a user bounces
between a playtest and normal Game Pass, the "active offering" is being flipped underneath them. There
is no automatic restore of the previous offering after the stream ends.

**8. The tab can surface a title it ultimately can't stream (licensing).**
Even when discovery, access, and hydration all succeed, the actual cloud stream can still fail at
**license acquisition** (the V10/V7 registry-routing + open-licensing gaps tracked in AB#63137135 /
63137141). The tab has no way to know this ahead of time, so a tester can click a fully-rendered tile
and hit a stream failure. Today that failure isn't translated into a friendly message.

**9. Playtest detection is a naive string prefix.**
"Is this a playtest?" is purely `id.startsWith('xpt')`. If the offering-id scheme ever changes, or a
non-playtest id happens to start with `xpt`, detection breaks. There's also some case juggling
(`toUpperCase`/`toLowerCase`) between discovery, auto-include, and access — a latent source of
mismatch bugs to watch.

**10. Friendly names depend on data that is currently wrong upstream.**
The registry sets `Title.FriendlyName = TitleId`, so the *offering/title* name is often an ugly id.
Hydration is what rescues the display (catalog title), so if hydration is unavailable the UI has no
good name to show. The UI is compensating for an upstream data bug, not fixing it.

**11. PC-only assumptions.**
The launch path and title-id slug (`…-pc`) assume PC cloud streaming. Console playtests aren't
supported by this UI yet.

**12. Not yet verified end-to-end, and quality gaps remain.**
The PR is a **draft**. Hydration HTTP 200 is proven, but the full signed-in click→stream→play path
hasn't had a visual pass. Locale ambiguity warnings are unresolved, there's **no telemetry** on the tab
yet, and a full local `tsc -b` typecheck hasn't been run (deferred to CI). Unit tests exist; end-to-end
(playwright) coverage of the new flow is not established.

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
