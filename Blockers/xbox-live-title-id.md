# Blocker: Xbox Live Title ID resolution

**Status:** Partially resolved — best-effort XORc resolver wired at publish time in PR 15834601 (Draft); confirming the service-config API + removing the placeholder still pending
**Owners:** Melanie Chen (xPlaytest) · Anthony Keller / XCon + XORc team

## Update (2026-06-18)
PR 15834601 (Draft) wires a best-effort Xbox Live title-id resolver in Xbox.Xbet.Service branch
`t-melanichen/playtest-ingestion-payload-builder`: `PlaytestBusinessLogic` resolves BigId alternate-id
→ XORc product → Xbox Live config at publish time, threads `XboxLiveTitleId` into
`PlaytestPublishJobParameters`, and the ingestion payload builder consumes a nonzero `XboxTitleId`.

This partially resolves the blocker for the publish path, but the source contract still needs to be
finalized: confirm the exact XORc service-config read API (endpoint/auth/inputs), add the Title ID field
to that API response, wire/remove any placeholder, and ensure `PlaytestProductDocumentBuilder` stops
emitting an empty `XboxLiveTitleId`.

## Problem
The xCloud ingestion contract requires a resolvable numeric **Xbox Title ID** on the `StoreAsset` (`StoreAsset.XboxTitleId`). The receiver's `StoreAsset.Validate()` rejects a null or `0` title id for games, and the xPlaytest payload builder (`PlaytestIngestionPayloadBuilder`) also requires a nonzero value.

Original gap:
- `PlaytestProductDocumentBuilder.cs:53-70` hardcodes `XboxLiveTitleId = string.Empty` and still needs to stop emitting an empty value.
- The generated playtest product does not exist in XProduct until **after** we write it, so nothing upstream fills the title id in for us.

## Current direction (Sync 3, 2026-06-10 — Anthony)
> "The way the Playtest service will do it is to query the Xbox Live service config from XCon via a number of services. Implementation would be to read it from an API on the XORc service (both of these services our team owns). There's already an API to read service config… the title ID is not one of those items yet, but it would be easy to add."

So the resolution path is: **Playtest → (XORc service-config API) → Xbox Live service config sourced from XCon.** An API to read service config already exists; the title id simply isn't one of the fields it returns yet.

**Done in PR 15834601 (Draft):** best-effort resolver wired at publish time using the XORc path, with null fallback if missing/unavailable so standard publish is not blocked.

## Next actions
1. Confirm the exact XORc service-config read API (endpoint + auth + required inputs) with Anthony's team.
2. Request/PR to **add the Title ID field** to that service-config API response.
3. ~~Wire a resolver in the xPlaytest publish path that reads the title id and threads it into `PlaytestIngestionPayloadBuilder.Build(...)`.~~ **Done in PR 15834601 (Draft)** for the publish-time payload path.
4. Remove the temporary placeholder once the real value flows.
5. Ensure `PlaytestProductDocumentBuilder` stops emitting an empty `XboxLiveTitleId`.

## References
- `SPEC.md` §3.0 (streaming requires a resolvable Xbox Title ID), §5 StoreAsset field map (`XboxTitleId`).
- `Transcripts/Sync3.docx` — Anthony on XCon/XORc service config.
- Outdated spec (`Documentation/OutdatedSpecificationDoc.pdf`) §7 listed the earlier direction (`alternateIds[idType=XboxTitleId].value`); superseded by the XORc service-config approach above.
- PR 15834601 — https://microsoft.visualstudio.com/Xbox/_git/Xbox.Xbet.Service/pullrequest/15834601 (Draft).
- [`../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md`](../PRProgress/07-XBET-15834601-playtest-ingestion-payload-builder.md).
- [`../Repos/Xbox.Xbet.Service.md`](../Repos/Xbox.Xbet.Service.md).
- [`../explanations/handling-xbox-vs-pc-differences.md`](../explanations/handling-xbox-vs-pc-differences.md) — summarizes Xbox vs PC field requirements.
