# Bayside CAS playtest metadata plan

Bayside can show real playtest art, title, publisher, and details in the My playtests library tab and PDP once the CAS playtest metadata contract is pulled into Xbox.JS, the playtest xToken claim is confirmed, and the client hydrates products by explicit playtest `offeringId`; today the UI shows a placeholder because retail catalog hydration cannot serve private playtest products, the private-offering fallback has no display metadata, and the fallback only runs for the app's active private offering.

## Ask

Make the placeholder playtest tile render like a real game tile and make the playtest PDP render the same metadata: box art or other image, friendly title, publisher, description/details, and a playtest badge/pill where needed.

Use CAS as the metadata source if the new CAS content-access proto carries the fields the CAS team referenced, then hydrate by `productId` within an explicit `offeringId` so the library tab can show playtests without changing Bayside's app-wide active offering.

## Goal and current state

The player-facing goal is: a tester opens `play.xbox.com`, signs in, visits the My playtests library tab, and sees each invited playtest as a real game tile with artwork and a friendly title; pressing the tile opens a PDP under that playtest offering with the same product details and correct install/stream actions.

The current library implementation renders a placeholder tile. `packages/@play-xbox/-route/library/src/components/PlaytestSection/PlaytestSection.tsx:30-43` describes a single playtest title as a placeholder, and `PlaytestTile` renders a square with the `TestBeaker` glyph plus the raw `productId` caption at `PlaytestSection.tsx:43-83`. The rail fetches playtest `TitleInfo` records by offering (`offeringTitlesByOffering`) at `PlaytestSection.tsx:220-241`, then passes only `titleInfo.details.productId` into the placeholder tile at `PlaytestSection.tsx:184-199`.

The placeholder exists for three grounded reasons:

1. **Retail catalog hydration does not serve private playtest builds.** Game tiles and PDP data hydrate through the catalog system in `packages/@play-xbox/-system/catalog/src/CatalogSystem.ts`. The private-offering catalog paths begin by fetching normal catalog product info, then decide whether to augment only when `activeOfferingInfo.isPrivate` is true and the user is signed in (`CatalogSystem.ts:235-371`). A DNA-gated playtest product is private content, so the public DCAT-style product path is not enough for real tile art and display details in the library.
2. **The private-offering fallback has no display metadata.** The fallback builders prove what the client can construct from GameStream `TitleInfo`: `createBasicProductInfoFromTitleInfo` returns `title: titleInfo.titleId` (`CatalogSystem.ts:760-774`), and `createDetailedProductInfoFromTitleInfo` sets `ProductTitle: titleInfo.titleId`, stores `JSON.stringify(titleInfo)` in both description fields, leaves `PublisherName` empty, and sets `Image_Tile`, `Image_Poster`, and `Image_Hero` to `null` (`CatalogSystem.ts:777-845`). This is useful for keeping a private-offering product resolvable; it is not enough for a real visual tile or PDP.
3. **That fallback is tied to the app's active offering.** The catalog queries depend on `gameStream.authentication.queries.activeOfferingInfo` and branch on `isPrivate` (`CatalogSystem.ts:247-282` for basic and `CatalogSystem.ts:315-354` for detailed). In the library tab, the app can list playtest offerings through additional offerings while the active offering remains the default/public offering, so the private-offering augmentation does not run for every playtest rail. A metadata seam needs an explicit `offeringId` input, not only the global active offering.

The PDP has the same offering-context gap. The playtest library tile builds a product-detail URL with `searchParams: { offeringId: offering.id }` at `PlaytestSection.tsx:118-130`, but product-detail code reads active/default offering context from systems. `AdditionalInformation.tsx:294-300` calls `getActiveOrDefaultOfferingData(productInfo, activeOfferingInfo?.offeringId, defaultOfferingId)`, and `ProductDetailPageSystem.ts:827-845` derives cloud programs from `activeOfferingInfo` plus `defaultOfferingId`. There is no verified PDP path here that consumes `?offeringId=` as the target playtest offering for hydration.

## What CAS provides now versus what Bayside needs

The Content Access Service is the intended access source and, based on the Teams thread, the likely display-metadata source for playtest content. The Xbox.JS contract checked into the repo is access-only today.

Verified current CAS facts:

- `packages/@xbox-js/-protobuf/content-access/proto/ContentAccessMessage.proto:59-64` defines `OPTIONAL_ACCESS_TYPE_XPLAYTEST`, so playtest is visible to the client as a content-access type.
- `ContentAccessMessage.proto:119-127` defines `StaticProductMetadata` with `supportedPlatforms`, `productKind`, and a deprecated field. It does not define image URL, title, publisher, description, hero art, poster art, or tile art fields.
- `ContentAccessMessage.proto:190-197` defines `ContentAccessAllV1Response.productsByProductId` as a `map<string, ProductData>`, and `ContentAccessMessage.proto:203-205` does the same for the xuid-only response.
- `packages/@xbox-js/-service-sdk/content-access/src/ContentAccessService.ts:144-153` exposes `fetchAllContentAccess(market, offeringId)`, calls `all/v1?market=...&offering=...`, and returns the decoded protobuf response at `ContentAccessService.ts:165-168`. The SDK surface returns access records keyed by product id; it does not shape or expose display metadata fields because the checked-in proto has none.
- Nothing in the verified library, catalog, or product-detail paths hydrates art from CAS today. The library rail uses GameStream offering titles (`PlaytestSection.tsx:220-241`), and the catalog fallback uses GameStream `TitleInfo` (`CatalogSystem.ts:260-282`, `CatalogSystem.ts:338-358`).

Bayside needs a new or updated CAS proto that carries display metadata fields for each playtest product. At minimum, the client needs friendly title, publisher, description or short description, and image URLs or image IDs that can populate the `BasicProductInfo` and `DetailedProductInfo` shapes consumed by `GameTile` and product-detail UI.

The unblocking dependency is the new CAS content-access contract that the CAS team said the client should pull. That contract is not present in the verified Xbox.JS files above.

## Implementation chain

1. **Pull the CAS playtest metadata proto into Xbox.JS and regenerate TypeScript.** Add the new `ContentAccessMessage.proto` version under `packages/@xbox-js/-protobuf/content-access`, run the repo's protobuf generation path, and inspect the generated types for the exact fields that carry title, publisher, description, tile/poster/hero imagery, and offering/product identifiers. **Status:** blocked on locating the new proto; client work starts once the contract is available.
2. **Confirm the xToken playtest claim is issued for Bayside callers.** CAS returns playtest data when the xToken contains the playtest user claim created by the playtest team, based on DNA-group membership. Anthony Keller is the named owner for claim details and gotchas. **Status:** server/token dependency; client can add diagnostics but cannot manufacture the claim.
3. **Extend the CAS SDK surface.** Update `ContentAccessService.fetchAllContentAccess(market, offeringId)` consumers and types so the decoded `productsByProductId[productId]` entry exposes the new display fields. Keep the offering parameter explicit because CAS data is offering-scoped in the current SDK call shape. **Status:** client work, blocked until the generated proto types exist.
4. **Add a product-metadata hydration seam keyed by explicit `offeringId`.** Preferred shape: a content-access-backed system/query that accepts `{ offeringId, productId, market }` and returns a normalized display model that can map into `BasicProductInfo` and `DetailedProductInfo`. An alternate shape is extending `CatalogSystem`'s private-offering augmentation so it can fetch CAS metadata for a specified offering, but the current active-offering dependency means that extension must avoid switching the whole app context for the library tab. **Status:** client work after SDK contract is available.
5. **Swap `PlaytestTile` to a real tile.** Replace the beaker placeholder in `PlaytestSection.tsx` with the same tile component/model used by the library grid, add the playtest badge/pill, and bind the tile image/title to the hydrated CAS-backed product info. Preserve the explicit PDP link with `offeringId` so the tile opens the playtest product context. **Status:** client work after the hydration seam exists.
6. **Wire the PDP to honor `?offeringId=`.** Product-detail must read the query param and use it as the target offering for product hydration and actions. Today the verified product-detail path resolves from `activeOfferingInfo` and `defaultOfferingId` (`AdditionalInformation.tsx:294-300`, `ProductDetailPageSystem.ts:827-845`), while the library link already sends `offeringId` (`PlaytestSection.tsx:118-130`). This can be implemented as client work independent of the CAS proto for offering selection, with metadata fidelity still blocked on CAS fields.
7. **Validate with a real invited tester.** Use an account in the playtest DNA group, a playtest offering id of the `xpt{PlaytestProductId}` form, and at least one product returned by `offeringTitlesByOffering`. Confirm CAS returns metadata only when the claim is present, that the library tab renders art/title/details without changing the app-wide active offering, and that PDP actions target the playtest offering.

## Blocked versus unblocked work

| Work item | Status | Owner shape |
|---|---|---|
| Locate and pull the new CAS content-access proto | Blocked | Anthony/CAS tells Melanie where the proto lives and which version to consume |
| Confirm xToken playtest claim issuance | Blocked | Playtest/auth side, Anthony for details and propagation gotchas |
| Regenerate content-access TypeScript | Client-only after proto | Xbox.JS once proto location is known |
| Extend `ContentAccessService` types and SDK helpers | Client-only after proto | Xbox.JS |
| Add explicit-`offeringId` CAS hydration seam | Client-only after SDK types | Xbox.JS |
| Replace placeholder `PlaytestTile` with real tile | Client-only after hydration seam | Xbox.JS |
| Make PDP consume `?offeringId=` for offering context | Client-only/unblocked for the offering-context part | Xbox.JS |
| Verify end-to-end metadata against a real playtest | Blocked on proto and claim | Xbox.JS plus Anthony/CAS support |

## Evidence — what people said

### David Kushmerick origin

David Kushmerick surfaced that CAS already has a Garrison-facing contract path for extra playtest info when the user is in DNA groups associated with playtests. That origin is captured in the ask to CAS below and is the reason Bayside treats CAS as the leading metadata-source candidate.

### CAS enablement thread (Teams, 2026-07-07)

The exchange that opened the Bayside playtest-data path. Quoted verbatim.

**The ask to the CAS team:**

> "we have an intern this summer, Melanie (just added here), who is working on adding game streaming as a capability to the PlayTest service. We heard from David Kushmerick today that you all have a contract with Garrison to send back extra playtest info when you detect the user is in DNA groups associated with one or more playtests? Is there any way this can be easily added to Bayside as well? We are happy to handle the client side of changes that may be needed but would love to understand what it would take service side!"

**CAS team reply:**

> "Yes, we have actually just deployed the CAS code this week to enable Playtests as a standard access type (was optional before - weve removed that concept). It worked by checking the xToken for a new user claim that the playtest folks created. If we see the playtest user claim in the token, we will call for playtest data."

> "CAS has no client specific contracts or endpoints. It is enabled right now - you just need to snag the new contract proto file. There is no service work from CAS to enable this for you!"

> "I would suggest talking to Anthony Keller about it more in depth - he has been heading up the playtest project, and may have more info about how to get those user claims added and any other gotchas that may be encountered around this!"

What this establishes for the plan:

- CAS playtest is now a standard access type.
- CAS returns playtest data when the xToken carries the new playtest user claim.
- The playtest user claim is DNA-group based and was created by the playtest team.
- CAS says there is no CAS service work and no client-specific endpoint for Bayside.
- The client-side dependency is pulling the new contract proto file.
- Anthony Keller is the contact for claim issuance and gotchas.

## Open questions for Anthony and CAS

- Where is the new CAS content-access proto published, and what exact pull/regeneration path should Xbox.JS use for `packages/@xbox-js/-protobuf/content-access`?
- Which fields in the new proto carry tile image, poster image, hero image, title, publisher, and description?
- Is the metadata keyed per `productId`, per `offeringId`, or both?
- Does CAS return one image type or the same tile/poster/hero variants that `DetailedProductInfo` expects?
- Does Bayside's current token acquisition already carry the playtest user claim for signed-in testers in the DNA group?
- What is the claim propagation delay after a tester joins the DNA group or after a playtest is published?
- Is CAS intended to be the durable source for playtest display metadata, or should catalog serve private products when the request includes a playtest offering context?
- Are there gotchas for revoked/expired playtest invites where CAS access and GameStream offering titles can disagree?
- Should PDP use `offeringId` as a query parameter, `offering.id`, or both for compatibility with the launch-link work?

## References

- `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\cloud-playtest-implementation\7-8 sync discussion topics\README.md` — source sync doc for the CAS thread, current placeholder explanation, CAS status, and open questions.
- `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\cloud-playtest-implementation\FuturePlans\bayside-playxbox-playtest-modifications.md` — Bayside launch-link, stream-start, active-offering, denial UX, and PDP/playtest-offering context.
- `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\cloud-playtest-implementation\FuturePlans\library-playtest-discovery.md` — My playtests discovery surface, section-at-top decision, playtest badge, console flash-card context, and CAS discovery notes.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:30-83` — placeholder tile renders a beaker icon and raw product id.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:118-130` — playtest tile link includes `offeringId` in PDP search params.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-route\library\src\components\PlaytestSection\PlaytestSection.tsx:220-241` — library rail fetches GameStream titles by explicit playtest offering.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-system\catalog\src\CatalogSystem.ts:235-371` — catalog private-offering augmentation depends on `activeOfferingInfo.isPrivate` and GameStream `TitleInfo`.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-system\catalog\src\CatalogSystem.ts:760-845` — `TitleInfo` fallback builders have ids and debug descriptions, not art or friendly display fields.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-protobuf\content-access\proto\ContentAccessMessage.proto:59-64` — current proto includes `OPTIONAL_ACCESS_TYPE_XPLAYTEST`.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-protobuf\content-access\proto\ContentAccessMessage.proto:119-127` — current `StaticProductMetadata` has `supportedPlatforms` and `productKind`, with no display metadata fields.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-protobuf\content-access\proto\ContentAccessMessage.proto:190-205` — current CAS responses are keyed by `productsByProductId`.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@xbox-js\-service-sdk\content-access\src\ContentAccessService.ts:144-168` — `fetchAllContentAccess(market, offeringId)` returns decoded access records.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-route\product-detail\src\components\Information\AdditionalInformation\AdditionalInformation.tsx:294-300` — product detail additional information reads active/default offering data.
- `C:\Users\t-melanichen\projects\Xbox.JS\packages\@play-xbox\-route\product-detail\src\ProductDetailPageSystem\ProductDetailPageSystem.ts:827-845` — product-detail cloud programs derive from `activeOfferingInfo` and `defaultOfferingId`.
