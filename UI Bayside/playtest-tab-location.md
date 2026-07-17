# Bayside playtest tab location

The e2e demo branch puts playtest discovery in the Bayside library as a gated **My playtests** tab between **My games** and **Full library**. The tab is separate from the normal games grid: Bayside builds the tab only when the signed-in user has an `xpt` playtest offering, and the tab body renders one rail per invited playtest offering with placeholder playtest tiles that deep-link to the product detail page carrying the playtest `offeringId`.

## Ask

Use `t-melanichen/playtest-library-section` for the e2e sync demo and keep the branch as-is. It tracks Brian Bowman's prototype branch, contains the six playtest-library commits listed below, and has uncommitted handling for signed-out and access-denied library states; `origin/main` has overlapping library playtest work that conflicts with this branch.

## What and why

The playtest UI lives inside the existing `/library` experience as a **My playtests** tab, not as a standalone left-nav destination. That keeps tester discovery near the normal game library while keeping playtest content out of the main library grid, which matches the FuturePlans design direction to make playtests a library-contained discovery surface and connects to Brian Bowman's prototype for demoable Bayside e2e work (`FuturePlans\library-playtest-discovery.md:10`, `FuturePlans\library-playtest-discovery.md:58`, `FuturePlans\library-playtest-discovery.md:60`).

Each playtest offering renders as its own rail. Each game tile is a placeholder with the beaker glyph, a Playtest badge, and the product id caption because private playtest products do not have the same retail catalog art path in this component; pressing a tile navigates to the PDP with `offeringId: offering.id` so the PDP can switch to the playtest build (`packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:29`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:68`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:122`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:128`).

## Exact location

- `packages\@play-xbox\-types\library\src\types.ts` — defines `LIBRARY_TABS.myGames`, `LIBRARY_TABS.playtests`, and `LIBRARY_TABS.fullLibrary`, so `playtests` is a first-class library tab key (`packages\@play-xbox\-types\library\src\types.ts:52`, `packages\@play-xbox\-types\library\src\types.ts:54`, `packages\@play-xbox\-types\library\src\types.ts:58`).
- `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx` — builds the ordered inline tab list as My games, optional My playtests, Full library, and passes `hasPlaytests: playtestOfferings.length > 0` from `usePlaytestOfferings` (`packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:28`, `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:33`, `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:35`, `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:67`, `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:83`).
- `packages\@play-xbox\-route\library\src\utils\usePlaytestOfferings.ts` — reads the user's `additionalOfferings` auth query and filters it to playtest offerings with `isPlaytestOffering(offering.id)` (`packages\@play-xbox\-route\library\src\utils\usePlaytestOfferings.ts:19`, `packages\@play-xbox\-route\library\src\utils\usePlaytestOfferings.ts:34`, `packages\@play-xbox\-route\library\src\utils\usePlaytestOfferings.ts:41`).
- `packages\@play-xbox\-types\game-stream\src\offerings.ts` — defines `PLAYTEST_OFFERING_PREFIX = 'xpt'` and `isPlaytestOffering`, which identifies playtest offerings by the `xpt` prefix (`packages\@play-xbox\-types\game-stream\src\offerings.ts:39`, `packages\@play-xbox\-types\game-stream\src\offerings.ts:43`, `packages\@play-xbox\-types\game-stream\src\offerings.ts:54`).
- `packages\@play-xbox\-route\library\src\LibraryPage.tsx` — computes `isPlaytestsTab` from `currentTab === LIBRARY_TABS.playtests`, hides the normal grid header on that tab, and renders `<PlaytestSection />` while the normal library tabs render `<Grid />` (`packages\@play-xbox\-route\library\src\LibraryPage.tsx:59`, `packages\@play-xbox\-route\library\src\LibraryPage.tsx:66`, `packages\@play-xbox\-route\library\src\LibraryPage.tsx:75`, `packages\@play-xbox\-route\library\src\LibraryPage.tsx:76`, `packages\@play-xbox\-route\library\src\LibraryPage.tsx:78`).
- `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx` — renders the tab content: one playtest offering rail per offering, access-aware rail state, placeholder tiles, and PDP navigation with `offeringId` (`packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:85`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:138`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:186`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:197`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:319`).
- `apps\play-xbox\locales\en-US\Library.json` — provides the visible tab label `My playtests` (`apps\play-xbox\locales\en-US\Library.json:38`).
- `apps\play-xbox\locales\en-US\LibraryPlaytestSection.json` — provides the signed-out and not-invited copy added in the working tree (`apps\play-xbox\locales\en-US\LibraryPlaytestSection.json:8`, `apps\play-xbox\locales\en-US\LibraryPlaytestSection.json:12`, `apps\play-xbox\locales\en-US\LibraryPlaytestSection.json:14`).

## How the tab is separated from the library

`TabsHeader` separates discovery at the navigation layer. It builds `tabKeys` with `LIBRARY_TABS.myGames`, conditionally inserts `LIBRARY_TABS.playtests` only when `hasPlaytests` is true, and then adds `LIBRARY_TABS.fullLibrary`; `hasPlaytests` comes from the length of `usePlaytestOfferings()` (`packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:33`, `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:35`, `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:36`, `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:67`, `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:83`).

`usePlaytestOfferings` separates the data set at the offering layer. It reads `gameStream.authentication.queries.additionalOfferings.getActiveUserQuery().getOptions()` and returns only offerings whose id passes `isPlaytestOffering`, which is the shared `xpt` prefix predicate (`packages\@play-xbox\-route\library\src\utils\usePlaytestOfferings.ts:34`, `packages\@play-xbox\-route\library\src\utils\usePlaytestOfferings.ts:41`, `packages\@play-xbox\-types\game-stream\src\offerings.ts:43`, `packages\@play-xbox\-types\game-stream\src\offerings.ts:54`).

`LibraryPage` separates rendering at the page layer. When the current tab is `playtests`, it renders `PlaytestSection`; all other library tabs render the normal `Grid`, and the normal grid header is omitted from the playtests tab (`packages\@play-xbox\-route\library\src\LibraryPage.tsx:59`, `packages\@play-xbox\-route\library\src\LibraryPage.tsx:66`, `packages\@play-xbox\-route\library\src\LibraryPage.tsx:75`, `packages\@play-xbox\-route\library\src\LibraryPage.tsx:78`).

`PlaytestSection` keeps the content offering-scoped. It maps each invited `xpt` offering to a `PlaytestOfferingRail`, checks `additionalOfferingAccess` before fetching titles, fetches titles with `offeringTitlesByOffering` only for accessible offerings, and shows the not-invited rail state when access is denied (`packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:230`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:236`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:243`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:246`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:319`).

## Branch and e2e

Verified branch state in `C:\Users\t-melanichen\projects\Xbox.JS`: the active branch is `t-melanichen/playtest-library-section`, and `git branch -vv` shows it tracking `origin/user/bbowman/playtests-additional-offerings` with `ahead 13, behind 1`.

`git --no-pager log --oneline -8` shows the playtest feature commits at the top of the branch:

```text
65695708179 chore(play-xbox/library): align playtest comments with repo durability conventions
c39b214d87a fix(play-xbox/library): match playtest tile size to the library grid
4dde18c9203 feat(play-xbox/library): add temporary "Playtest" badge to playtest tiles
3738836c7cb feat(play-xbox/library): placeholder tile for playtest builds
b95ed6f4cdd feat(play-xbox/library): make playtests a gated "My playtests" tab
3f8fecee22c feat(play-xbox/library): add Playtests section for xpt offerings
```

The branch is Melanie's local demo branch for Brian Bowman's Xbox.JS PR 16046428 prototype, **Playtests tab + additional (playtest) offerings**. The FuturePlans discovery doc calls Brian's PR an active show-don't-tell prototype that added player-surface playtest pieces and additional-offerings work (`FuturePlans\library-playtest-discovery.md:58`, `FuturePlans\library-playtest-discovery.md:60`, `FuturePlans\library-playtest-discovery.md:84`).

`git status --short` shows uncommitted changes in three files: `apps\play-xbox\locales\en-US\Library.json`, `apps\play-xbox\locales\en-US\LibraryPlaytestSection.json`, and `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx`. The diff adds the `My playtests` tab label, signed-out copy, not-invited copy, `PageStateBanner` sign-in handling, and an `additionalOfferingAccess` gate that enables the title query only when the offering is accessible (`apps\play-xbox\locales\en-US\Library.json:38`, `apps\play-xbox\locales\en-US\LibraryPlaytestSection.json:8`, `apps\play-xbox\locales\en-US\LibraryPlaytestSection.json:14`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:230`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:246`, `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:275`).

Concrete e2e checkout and run steps:

```powershell
git -C "C:\Users\t-melanichen\projects\Xbox.JS" checkout t-melanichen/playtest-library-section
cd "C:\Users\t-melanichen\projects\Xbox.JS"
yarn nx start play-xbox --no-tui
```

Open `https://local.play.xbox.com:1337`. The companion Bayside plan uses that same local URL for Play Xbox development and documents the launch-link stream path that Bayside must honor for playtest streaming (`FuturePlans\bayside-playxbox-playtest-modifications.md:59`, `FuturePlans\bayside-playxbox-playtest-modifications.md:73`, `FuturePlans\bayside-playxbox-playtest-modifications.md:21`).

Merge caveat: keep this branch as-is for the demo. A read-only `git merge-tree --write-tree --name-only HEAD origin/main` check reports content conflicts in overlapping library playtest files, including `packages\@play-xbox\-route\library\src\LibraryPage.tsx`, `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx`, `packages\@play-xbox\-route\library\src\utils\constants.ts`, `packages\@play-xbox\-route\library\src\utils\useLibraryStrings.ts`, and `packages\@play-xbox\-types\library\src\types.ts`.

## How to reach the tab in the running app

1. Sign in with a tester account whose playtest membership maps to a DNA group and whose account receives an `xpt` playtest offering in `additionalOfferings`.
2. Open `https://local.play.xbox.com:1337` after starting `play-xbox`, then go to Library.
3. Select the **My playtests** tab between **My games** and **Full library**.
4. If the tab is missing, the signed-in account has no `xpt` offering in `additionalOfferings`, the offering id does not pass `isPlaytestOffering`, or the branch/local state is not the demo branch described above.
5. If a rail says **You are not invited to this playtest**, the offering appeared in the playtest list but `additionalOfferingAccess` returned `denied`; check the DNA-group membership and offering access setup.

## Open questions

- Should the e2e demo keep the uncommitted signed-out and not-invited work in the working tree, or should Melanie commit it before the sync branch is shared?
- Which real test account and DNA group will be used for the sync, and which `xpt` offering should appear in `additionalOfferings`?
- Should the demo open via Library first, or should it pair Library discovery with the launch-link stream path from `https://play.xbox.com/play/launch/{productId}?offering.id=xpt{PlaytestProductId}` (`FuturePlans\bayside-playxbox-playtest-modifications.md:21`)?
- How should the prototype reconcile with `origin/main` after the demo, given the confirmed conflicts in the same library tab files?

## References

- `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:29` — placeholder tile shape and PDP deep-link intent.
- `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:122` — PDP navigation with `offeringId`.
- `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:230` — access check through `additionalOfferingAccess`.
- `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:243` — offering-scoped title query.
- `packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:319` — one rail per playtest offering.
- `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:33` — ordered tab list.
- `packages\@play-xbox\-route\library\src\components\TabsHeader\TabsHeader.tsx:83` — `hasPlaytests` gating.
- `packages\@play-xbox\-route\library\src\utils\usePlaytestOfferings.ts:34` — additional offerings query.
- `packages\@play-xbox\-route\library\src\utils\usePlaytestOfferings.ts:41` — playtest offering filter.
- `packages\@play-xbox\-types\game-stream\src\offerings.ts:43` — `xpt` playtest offering prefix.
- `packages\@play-xbox\-types\game-stream\src\offerings.ts:54` — `isPlaytestOffering` predicate.
- `packages\@play-xbox\-route\library\src\LibraryPage.tsx:59` — playtests tab detection.
- `packages\@play-xbox\-route\library\src\LibraryPage.tsx:75` — conditional PlaytestSection render.
- `packages\@play-xbox\-types\library\src\types.ts:52` — library tab key registry.
- `apps\play-xbox\locales\en-US\Library.json:38` — `My playtests` tab label.
- `apps\play-xbox\locales\en-US\LibraryPlaytestSection.json:8` — not-invited rail copy.
- `apps\play-xbox\locales\en-US\LibraryPlaytestSection.json:14` — signed-out tab copy.
- `FuturePlans\library-playtest-discovery.md:10` — design direction for a library-contained playtest discovery surface.
- `FuturePlans\library-playtest-discovery.md:58` — Brian prototype relationship.
- `FuturePlans\bayside-playxbox-playtest-modifications.md:21` — launch-link offering contract.
- `FuturePlans\bayside-playxbox-playtest-modifications.md:59` — local Bayside run section.
- `FuturePlans\bayside-playxbox-playtest-modifications.md:73` — `https://local.play.xbox.com:1337` local URL.
