# Library playtest discovery surface (how testers find a playtest)

How an invited tester **discovers** a playtest in their library on play.xbox.com (Bayside) and console
(Garrison). Decided in the **2026-06-30 Design Brainstorm** (`Transcripts/Design Brainstorm - Playtest UX.docx`,
local-only). Companion to [`ui-steps-bayside.md`](./ui-steps-bayside.md) (which covers the launch-link/stream
path) and the meeting outcomes in [`../Playtest-UI-Meeting-Karla-Kush.md`](../Playtest-UI-Meeting-Karla-Kush.md).

## Decision

**Surface playtests as a dedicated *section at the top of the library*** — move the existing library content
down and render a playtests section above it.

- ❌ **Not a library filter.** Filtering was judged too hard to land in the timeline, and burying playtests
  behind a filter is poor discovery — a tester would have to know to open filters to find the build they were
  invited to. (Melanie pushed back on the filter/access-pill idea for this reason.)
- ❌ **Not a separate playtest tab / left-nav element.** Considered and rejected ("not final"; over-weighted
  for a pilot surface).
- ✅ **Section within the library, at the top.** Called "totally acceptable" once filtering was ruled out.

> Nuance from the meeting: *"if you can do library filtering, then do that"* — filtering is the nicer end state
> if feasible, but the section-at-top is the agreed fallback and the v1 plan.

## Platform differences

| Surface | Click a playtest in the library → |
|---------|-----------------------------------|
| **PC / web (Bayside)** | **Playtest details page** → install / stream. |
| **Console (Garrison)** | **Flash card** — a pop-over pane (not a full view) that flips between **stats** and **product metadata**, with **Install** + **Play** buttons. A custom playtest flash card. |

A **playtest badge/pill** differentiates the product as a non-public build in the library.

## Discovery mechanism (backend)

- Library hydration is **authenticated** (X tokens). Populating the library makes an authenticated hydration
  call that returns the playtest content the tester has access to.
- **CAS decides** whether to return playtest content. Web calls a specific CAS endpoint (the equivalent of PC's
  "low amber 0 / high diamond 1"); **console needs a new CAS contract endpoint** ("console normal" vs "console
  playtest"). **Must not break existing console test support.**
- A playtest offering is "no different than any other offering," so a library that sorts content from configured
  offering groups gets playtest offerings largely for free.

## Library filtering — feasibility (the "how hard is filtering?" question)

If we do pursue real library filtering instead of (or in addition to) the section-at-top:

- **Difficulty: Medium (~2–3 days)** for a complete implementation.
- **Reusable, pre-existing infra:** `packages/@play-xbox/-dialog/-route/library-filter/` (`LibraryFilterDialog`)
  is a full, production-quality filter dialog (L1 category list → L2 tag list, in-memory `selectedTags` state
  exposed as TanStack queries/mutations, `FilterButton` trigger with badge, `getFilteredItems` category-handler
  table). This is **not** from Brian's PR — it already exists and can be copied/adapted.
- **What's new:** playtest-specific filter categories/tags (status: Streaming Ready / Download Only, expiry,
  title) that map to `TitleInfo` rather than catalog `BasicProductInfo`; a small `PlaytestFilterSystem`; route
  registration boilerplate; a localization namespace.
- **Prerequisite:** a multi-title **list/grid** of playtest tiles must exist first (filtering is only useful on a
  list). Borrow `packages/@play-xbox/-route/library/src/components/Grid/Grid.tsx`. Today's playtest UI shows a
  single tile (one playtest = one title), so the grid is net-new.

## Relationship to Brian's prototype (Xbox.JS PR 16046428)

Brian Bowman's PR **16046428** — *"Playtests tab + additional (playtest) offerings [prototype]"* (branch
`user/bbowman/playtests-additional-offerings`, **active, explicitly a "show don't tell" prototype not meant to
merge as-is**) — makes the model demoable e2e on Bayside. It adds (48 files): a dedicated **Playtests page/route**
(under `-route/dev-tools/src/PlaytestsPage.tsx` + `app/routes/PlaytestsRoute.ts`), **nav entries** (DockNavBar /
TopNavBar), an **additional-offerings manager** in the Developer settings tab, and **product-detail playtest
UX** (`PlaytestBanner`, `PlaytestSignInLanding`, `usePlaytestDeepLink`, `usePlaytestOfferingId`).

> Melanie's UI should be **similar but** land the **section-in-library** discovery (above) rather than Brian's
> throwaway dedicated-page/nav prototype. Brian's product-detail banner / sign-in-landing pieces are the most
> directly reusable for the tester landing experience.

## Effort & dependencies

- **Section-at-top (chosen v1):** 🟡 — library page layout change + the CAS hydration returning playtest content.
- **Library filtering (optional/nice-to-have):** 🟡 medium (~2–3 days) + the playtest grid prerequisite.
- **Console flash card:** 🔴 — new CAS contract endpoint for console + custom flash-card component.
- Depends on the **CAS** discovery work and the existing offering/audience gating (see `ui-steps-bayside.md` #5/#6).

## References

- `Transcripts/Design Brainstorm - Playtest UX.docx` (local-only) — discovery decision, console flash card, CAS.
- [`../Playtest-UI-Meeting-Karla-Kush.md`](../Playtest-UI-Meeting-Karla-Kush.md) — meeting conclusions.
- [`ui-steps-bayside.md`](./ui-steps-bayside.md) — launch-link / denial / metadata / install-vs-stream.
- [`../Blockers/playtest-content-leak-signed-out.md`](../Blockers/playtest-content-leak-signed-out.md) — e2e leak blocker.
- Xbox.JS PR 16046428 (Brian Bowman, prototype) — player-surface reference.
