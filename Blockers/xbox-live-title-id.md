# Blocker: Xbox Live Title ID resolution

**Status:** Open — P0 for the end-to-end flow
**Owners:** Melanie Chen (xPlaytest) · Anthony Keller / XCon + XORc team

## Problem
The xCloud ingestion contract requires a resolvable numeric **Xbox Title ID** on the `StoreAsset` (`StoreAsset.XboxTitleId`). The receiver's `StoreAsset.Validate()` rejects a null or `0` title id for games, and the xPlaytest payload builder (`PlaytestIngestionPayloadBuilder`) also requires a nonzero value.

Today there is no source for it:
- `PlaytestProductDocumentBuilder.cs:53-70` hardcodes `XboxLiveTitleId = string.Empty`.
- The value can't be reverse-resolved at publish time, because the generated playtest product does not exist in XProduct until **after** we write it, so nothing upstream fills the title id in for us.

## Current direction (Sync 3, 2026-06-10 — Anthony)
> "The way the Playtest service will do it is to query the Xbox Live service config from XCon via a number of services. Implementation would be to read it from an API on the XORc service (both of these services our team owns). There's already an API to read service config… the title ID is not one of those items yet, but it would be easy to add."

So the resolution path is: **Playtest → (XORc service-config API) → Xbox Live service config sourced from XCon.** An API to read service config already exists; the title id simply isn't one of the fields it returns yet.

## Next actions
1. Confirm the exact XORc service-config read API (endpoint + auth + required inputs) with Anthony's team.
2. Request/PR to **add the Title ID field** to that service-config API response.
3. Wire a resolver in the xPlaytest publish path that reads the title id and threads it into `PlaytestIngestionPayloadBuilder.Build(...)` (and replaces the hardcoded empty value in `PlaytestProductDocumentBuilder`).
4. Remove the temporary placeholder once the real value flows.

## References
- `SPEC.md` §3.0 (streaming requires a resolvable Xbox Title ID), §5 StoreAsset field map (`XboxTitleId`).
- `Transcripts/Sync3.docx` — Anthony on XCon/XORc service config.
- Outdated spec (`Documentation/OutdatedSpecificationDoc.pdf`) §7 listed the earlier direction (`alternateIds[idType=XboxTitleId].value`); superseded by the XORc service-config approach above.
