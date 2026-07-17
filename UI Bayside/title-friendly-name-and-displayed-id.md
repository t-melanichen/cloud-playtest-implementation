# Bayside playtest title-friendly name and displayed id

For the demo, the current Bayside library playtest tile shows the raw Store `productId` such as `2SDT4X91KRQT`, not a friendly product title and not the partner-registry `Title.FriendlyName`. The partner-registry `Title.FriendlyName` is also not friendly today because `PlaytestProcessor.cs` writes `FriendlyName = requestTitle.TitleId`; changing `Title.json` alone can improve partner-registry/service-side data, but the current Bayside tile has no `FriendlyName` field to read. A demo-quality fix needs a real display-name source plus a UI change that renders that source on the tile.

## Ask

Make Melanie's demo explain three separate names, why the generated `Title.json` value is the title id, and which edit points make the Bayside surface show a friendly title.

Concrete demo data from partner-registry data PR `!16115783`: offering `XPT2SDT4X91KRQT`, title id `XPT2SDT4X91KRQT-MELANIEPLAYTESTTEST1-PC`, product id `2SDT4X91KRQT`, and generated `FriendlyName` equal to the title id.

## TL;DR for the demo

- **Tile caption and accessibility label:** Bayside renders `titleInfo.details?.productId` into `PlaytestTile`, then `PlaytestTile` uses that `productId` for both `aria-label` and visible caption (`C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:43`, `:50`, `:77`, `:187`, `:196`). For this example, the tile caption is `2SDT4X91KRQT`.
- **Rail heading:** Bayside renders the offering name only when `offering.name !== offering.id` (`PlaytestSection.tsx:119-120`, `:207-209`). That name comes from the GSSV user-offerings response, not from the title's `FriendlyName`.
- **Partner-registry title friendly name:** `services.partnerregistry` generates the title with `FriendlyName = requestTitle.TitleId` (`C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryService\Processors\PlaytestProcessor.cs:85-93`). That is why the data PR has `FriendlyName` equal to `XPT2SDT4X91KRQT-MELANIEPLAYTESTTEST1-PC`.
- **Key demo implication:** Editing `Title.json` `FriendlyName` by itself does not change the current Bayside tile because the tile renders `productId` and the TypeScript `TitleInfo` contract exposes `titleId`, `details.productId`, and `details.xboxTitleId`, not `FriendlyName` (`C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-game-stream\play-service\src\TitleInfo.ts:5-25`).

## The three names

| Name source | Where set | What value it has in the example | Where it surfaces in Bayside today | Anchors |
|---|---|---|---|---|
| Partner-registry `Title.FriendlyName` | `PlaytestProcessor` builds a `Title` and sets `FriendlyName = requestTitle.TitleId`. | `XPT2SDT4X91KRQT-MELANIEPLAYTESTTEST1-PC` | Not directly rendered by the library tile. The Bayside title contract used here does not expose `FriendlyName`. | `C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryService\Processors\PlaytestProcessor.cs:85-93`; `C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryClient\Contracts\Title.cs:57-61`; `C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-game-stream\play-service\src\TitleInfo.ts:5-25` |
| GSSV offering `name` | The partner-registry offering is created with `Name = request.PlaytestName`; Bayside later joins configured additional offering ids against the GSSV `/v1/offerings/user` result and sets `name: match?.name ?? id`. | Expected to be the playtest/offering display name when GSSV returns one; falls back to `XPT2SDT4X91KRQT` when not found. | Used as the playtest rail heading only when it differs from the id. It is not used as the tile caption. | `C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryService\Processors\PlaytestProcessor.cs:69`; `C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-game-stream\auth-service\src\AuthenticationService.ts:91-120`; `C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-game-stream\auth-service\src\types.ts:64-72`; `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-system\-service\-game-stream\authentication\src\GameStreamAuthenticationServiceSystem.ts:837-866`; `PlaytestSection.tsx:119-120`, `:207-209` |
| Tile `productId` | `PlaytestSection` enumerates titles for the offering, reads `titleInfo.details?.productId`, and passes it into `PlaytestTile`. | `2SDT4X91KRQT` | This is the visible tile caption and the tile's `aria-label`. | `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:43`, `:50`, `:77`, `:186-197`; `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-system\-service\-game-stream\play\src\GameStreamPlayServiceSystem.ts:459-490` |

## Why `FriendlyName` is not friendly

`PlaytestProcessor.ConfigurePlaytestAsync` validates the request, takes the first `PlaytestTitle`, builds an `OfferingV2`, then builds a `Title` from that request title (`C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryService\Processors\PlaytestProcessor.cs:41-93`). The title assignment is literal:

```csharp
FriendlyName = requestTitle.TitleId,
```

The better source available on the current request is `request.PlaytestName`, which the same method already uses for `OfferingV2.Name` (`PlaytestProcessor.cs:69`). The request does not currently carry a per-title display name: `PlaytestRequest` has `PlaytestName`, `PlaytestProductId`, and `Titles`, while `PlaytestTitle` has `TitleId`, `Platform`, `ProductId`, and `XboxTitleId` (`C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryClient\Contracts\PlaytestRequest.cs:32-58`; `C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryClient\Contracts\PlaytestTitle.cs:21-36`). For single-title v1, `PlaytestName` may be an acceptable interim title label; for multi-title support, the durable contract should add or hydrate a per-title product display name.

The unit test also locks in the current behavior by asserting `title.FriendlyName.Should().Be("XPT2SDT4X91KMWM-MYGAME")` (`C:\Users\t-melanichen\source\sci-ptnr\src\Tests\Unit\PartnerRegistryService.UnitTests\Processors\PlaytestProcessorTests.cs:88-101`). A service change needs a matching test update.

## What the UI shows today and where to change it

`PurePlaytestOfferingRail` fetches `offeringTitlesByOffering` for the offering id (`PlaytestSection.tsx:243-245`). That query binds a title manager to the specific offering, calls `fetchTitles`, and returns `TitleInfo[]` (`C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-system\-service\-game-stream\play\src\GameStreamPlayServiceSystem.ts:184-212`, `:459-490`).

Inside the map, Bayside reads `const productId = titleInfo.details?.productId`, drops titles without a product id, and renders `<PlaytestTile productId={productId} />` (`PlaytestSection.tsx:186-197`). `PlaytestTile` then uses that same string as the accessible label and caption (`PlaytestSection.tsx:43-77`).

The exact UI edit point is `PlaytestTileProps` and `PlaytestTile`: add a `displayName` or `titleName` prop, use it for `aria-label` and the caption, and keep `productId` for navigation. The map in `PurePlaytestOfferingRail` should compute that display name from CAS metadata when available, or from an interim offering/title name source, then pass both `productId` and `displayName` into the tile.

The rail heading edit point is separate: `offeringLabel` already hides raw ids by checking `offering.name && offering.name !== offering.id` (`PlaytestSection.tsx:119-120`). If the demo needs a named section, make sure the GSSV offering has a real `name`; if it falls back to the id, the heading is intentionally suppressed.

## Fix options for the demo

1. **Fastest data-only fix:** Edit the offering's partner-registry data so `Title.json` has a real `FriendlyName` such as `Melanie Playtest Test 1`. This makes the registry data and service-side title record cleaner. Caveat: current Bayside tile rendering does not read `Title.FriendlyName`, so this data-only fix does not change the tile caption from `2SDT4X91KRQT` unless another service maps `FriendlyName` into a client-visible field and the UI starts reading it.

2. **Best demo UI fix:** Change `PlaytestTile` to render a friendly display name while keeping `productId` for navigation. Preferred source is CAS playtest metadata once the CAS work exists; cross-link that plan in [`cas-playtest-metadata.md`](./cas-playtest-metadata.md). Interim source for a one-title demo can be the rail/offering name (`offeringLabel`) or a title-name field added to the title enumeration contract, with fallback to `productId` so the tile always renders.

3. **Durable service fix:** Change `PlaytestProcessor.cs` so generated titles do not default `FriendlyName` to `requestTitle.TitleId`. With today's request contract, the only human-readable field is `request.PlaytestName`; a stronger fix adds a per-title display name to `PlaytestTitle` or hydrates the product title before writing partner-registry data. This is a `services.partnerregistry` code change plus deploy, and the `PlaytestProcessorTests` assertion at `PlaytestProcessorTests.cs:101` needs to reflect the new rule.

4. **Durable metadata fix:** Use CAS as the product-title and art source for the library tile, then the UI can show the same friendly name/art that the product details experience will use. This dependency belongs with the playtest metadata plan and the tab/location plan in [`cas-playtest-metadata.md`](./cas-playtest-metadata.md) and [`playtest-tab-location.md`](./playtest-tab-location.md).

## Recommended path for the demo

For the demo, do both an interim data cleanup and a small UI rendering change: set the generated `Title.json` `FriendlyName` to a real label, confirm the offering's GSSV `name` is also real, and render a friendly label on `PlaytestTile` with `productId` as fallback. That gives the demo a readable tile now and keeps the durable path clear: `PlaytestProcessor` writes real title-friendly data, CAS supplies product name/art, and Bayside renders metadata instead of ids.

## Open questions

- Should single-title v1 reuse `PlaytestName` as `Title.FriendlyName`, or should xPlaytest send a separate per-title display name in `PlaytestTitle`?
- Does GSSV map partner-registry `Title.FriendlyName` into any field beyond the current `TitleInfo` TypeScript contract? The local client contract does not expose it, so the current UI cannot render it without a contract or metadata change.
- For the demo, is the required friendly label the playtest/offering name (`Melanie Playtest Test 1`) or the product/game name from CAS? The durable player-facing answer should be product/game name plus playtest badge.
- Are [`cas-playtest-metadata.md`](./cas-playtest-metadata.md) and [`playtest-tab-location.md`](./playtest-tab-location.md) expected to live in this `UI Bayside` folder? They are referenced here as sibling docs.

## References

- `C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryService\Processors\PlaytestProcessor.cs:41-93` — playtest request validation, offering construction, and title construction; `:69` sets `OfferingV2.Name = request.PlaytestName`; `:90` sets `FriendlyName = requestTitle.TitleId`.
- `C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryClient\Contracts\PlaytestRequest.cs:32-58` — current request fields; no per-title display name.
- `C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryClient\Contracts\PlaytestTitle.cs:21-36` — current title fields; no friendly/display name.
- `C:\Users\t-melanichen\source\sci-ptnr\src\Product\PartnerRegistryClient\Contracts\Title.cs:57-61` — partner-registry `Title.FriendlyName` contract.
- `C:\Users\t-melanichen\source\sci-ptnr\src\Tests\Unit\PartnerRegistryService.UnitTests\Processors\PlaytestProcessorTests.cs:88-101` — test coverage for offering name and generated title friendly name.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-route\library\src\utils\usePlaytestOfferings.ts:9-42` — playtest offering list consumes `additionalOfferings` and filters playtest ids.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-system\-service\-game-stream\authentication\src\GameStreamAuthenticationServiceSystem.ts:791-866` — GSSV offerings fetch and `additionalOfferings` name fallback.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-game-stream\auth-service\src\AuthenticationService.ts:91-120` and `C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-game-stream\auth-service\src\types.ts:64-72` — `/v1/offerings/user` returns `ServiceOffering.name`.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-system\-service\-game-stream\play\src\GameStreamPlayServiceSystem.ts:184-212`, `:459-490` — offering-scoped title manager and title enumeration used by the Playtests rail.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-game-stream\play-service\src\TitleInfo.ts:5-25` — current `TitleInfo` fields exposed to the UI.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:43-77`, `:119-120`, `:186-197`, `:207-209`, `:243-245` — tile rendering, rail heading, and offering-title query usage.
- [`cas-playtest-metadata.md`](./cas-playtest-metadata.md) — planned CAS source for product title and art.
- [`playtest-tab-location.md`](./playtest-tab-location.md) — planned placement/navigation guidance for the playtest surface.
