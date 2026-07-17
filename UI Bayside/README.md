# UI Bayside — playtest player-surface changes

The UI changes Melanie owns to make cloud playtests look and work well in **Bayside** (the play.xbox.com web client, in the `Xbox.JS` repo) for the e2e demo. This folder collects the three areas of work — where the playtest tab lives, how to surface real game metadata from CAS, and how to fix the name/id the tile shows — each with cited code anchors and the branch that backs the demo.

## Start here

- **Demo branch:** `t-melanichen/playtest-library-section` in `C:\Users\t-melanichen\projects\Xbox.JS` (tracks `origin/user/bbowman/playtests-additional-offerings`, Brian Bowman's Playtests-tab prototype, Xbox.JS PR 16046428). Keep it as-is — `origin/main` has overlapping library playtest work that conflicts.
- **Run Bayside locally:** `yarn nx start play-xbox --no-tui`, then open **`https://local.play.xbox.com:1337`** (first page load compiles SSR on demand, so give it ~20–30s).
- **Reach the surface:** library → **My playtests** tab. The tab only appears when the signed-in user has an `xpt` playtest offering (DNA-group gated), so sign in with an account invited to a playtest.

## The three docs

| Doc | What it covers | One-line takeaway |
| --- | --- | --- |
| [`playtest-tab-location.md`](./playtest-tab-location.md) | Where the playtest tab lives and how it is separated from the library; the branch and e2e steps. | Playtests are a gated **My playtests** tab in the library (`PlaytestSection.tsx`), shown only for users with an `xpt` offering (`TabsHeader.tsx` + `usePlaytestOfferings.ts`). |
| [`cas-playtest-metadata.md`](./cas-playtest-metadata.md) | How to replace the placeholder tile with real art, title, publisher, and details sourced from CAS. | The tile is a placeholder because retail catalog and TitleInfo carry no playtest art; the fix chain is pull the new CAS proto → confirm the xToken playtest claim → hydrate by explicit `offeringId` → render a real tile → wire the PDP `?offeringId=`. |
| [`title-friendly-name-and-displayed-id.md`](./title-friendly-name-and-displayed-id.md) | What name/id the tile shows, why `Title.FriendlyName` is not friendly, and how to fix it for the demo. | The tile shows the raw `productId`; `PlaytestProcessor.cs` sets `Title.FriendlyName = requestTitle.TitleId`, while the offering `Name = request.PlaytestName` is already friendly — a demo-quality fix needs a real display-name source **and** a UI change (fixing `Title.json` alone does not change the tile). |

## State of play

- **Built and on the demo branch:** the gated My playtests tab, the per-offering rails, the placeholder tile, and (uncommitted working-tree changes) the signed-out ("Sign in to see your playtests") and not-invited ("You are not invited to this playtest") states.
- **Unblocked client work, not yet started:** wire the PDP (`product-detail`) to honor `?offeringId=` (it resolves offering from `activeOfferingInfo` only today); render a friendly name on the tile instead of the raw `productId`.
- **Blocked on the playtest/CAS side:** real art + friendly product title from CAS depend on pulling CAS's new content-access proto into `@xbox-js/-protobuf/content-access` (not in the repo yet) and on the xToken playtest claim being issued — both owned by Anthony Keller / the CAS team. See `cas-playtest-metadata.md` for the evidence and the open questions.

## Related hub docs

- [`../FuturePlans/bayside-playxbox-playtest-modifications.md`](../FuturePlans/bayside-playxbox-playtest-modifications.md) — the launch-link / stream-start / denial-UX path.
- [`../FuturePlans/library-playtest-discovery.md`](../FuturePlans/library-playtest-discovery.md) — the decision to surface playtests as a section/tab in the library, plus the console flash-card plan.
- [`../7-8 sync discussion topics/README.md`](../7-8%20sync%20discussion%20topics/README.md) — the sync agenda, including the CAS metadata evidence thread.
