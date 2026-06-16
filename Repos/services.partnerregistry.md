# Repo: services.partnerregistry

**Role:** Partner Registry defines the xCloud playtest offering/title contract and service endpoint: `ConfigurePlaytestAsync` creates the offering + title PR, sets Studio service level/regions/auth, and gates access with `AllowedDnaGroups` / `AllowedSandboxId` on `PlayerAuthorizationOptions`.

## Changes made

### PR 15732852 — Add AllowedDnaGroups to PlayerAuthorizationOptions — branch `t-melanichen/add-allowed-dna-groups` (Status: Merged)
- Added `AllowedDnaGroups` to `PlayerAuthorizationOptions` so offerings can authorize users by membership in at least one DNA group.
- Documented the expected DNA group ID format as standard hyphenated GUID strings, case-insensitive for hex letters but format-sensitive.
- This is the Partner Registry contract foundation for DNA-group-gated playtest offerings.
- Key files: `src/Product/PartnerRegistryClient/Contracts/PlayerAuthorizationOptions.cs`
- Commits: `736f7a81` Summary update; `96df9794` Add AllowedDnaGroups to PlayerAuthorizationOptions

### Configure playtest endpoint — branch `t-melanichen/configure-playtest-endpoint` (Status: Active; no PRProgress entry)
- Added `PlaytestRequest` and `PlaytestTitle` contracts for a playtest offering, its display name/product id, allowed DNA groups, expiration, partner id, and attached title metadata.
- Added `IPartnerRegistryClient.ConfigurePlaytestAsync`, `PlaytestsController` (`POST /v1/playtests`), `IPlaytestProcessor`, DI registration, and route tests.
- Implemented `PlaytestProcessor.ConfigurePlaytestAsync` to validate the request, build one `OfferingV2` plus one `Title`, set `ServiceLevel.Studio`, pass through `AllowedDnaGroups`, set empty countries, and write both objects in one `BulkEditAsync` PR.
- Added PC-title handling with a temporary hardcoded server SKU and tests for mapping, validation failures, Xbox titles, first-title behavior, and routing.
- Key files: `src/Product/PartnerRegistryClient/Contracts/PlaytestRequest.cs`; `src/Product/PartnerRegistryClient/Contracts/PlaytestTitle.cs`; `src/Product/PartnerRegistryService/Controllers/PlaytestsController.cs`; `src/Product/PartnerRegistryService/Processors/PlaytestProcessor.cs`; `src/Tests/Unit/PartnerRegistryService.UnitTests/Processors/PlaytestProcessorTests.cs`
- Commits: `f9d73b50` Add ConfigurePlaytest endpoint to create offering + title in one PR; `e3329091` Use a numeric DNA group id for playtest test data; `75f1d755` Add real title; `ca466401` Phase 2 of implementing: add ConfigurePlaytestAsync(PlaytestRequest) for real playtest data; `d49d0398` Default expiration time 7 days and remove old endpoint; `41effda6` comments update; `5dc29824` Reject unsupported platform and sandbox; `678e7ce4` Resolving Jack's PR comments; `b8a2b85e` clean up; `422a19ba` Resolving comments; `b766911b` Resolving comments; `5646c32d` Resolving comments; `6eaf530d` Resolving comments; `2ce5c30d` Removing platform from playtest title; `b4ac50e5` Making XboxTitleId non-nullable and adding back platform; `946b686c` Clean up controller and processor files and add PC string; `007cca07` Add playtest name and update tests; `61447319` Add product big id for offering id and add tests; `0fec080a` Clean up comments; `4db009f8` Add required for expiration date; `fd64aaa0` Add required for expiration date; `173da095` Nit; `7f1942a8` Nit; `9702b174` Nit; `f7176636` Set service level to studio

### Playtest offering id on request — branch `t-melanichen/playtest-offering-id-on-request` (Status: Active; no PRProgress entry)
- Centralized the offering id convention on `PlaytestRequest.GetOfferingId()`, using `xpt` + `PlaytestProductId` with no hyphen.
- Added `PlaytestRequest.GetPackageSourceId(PlaytestTitle)` so producer and Partner Registry agreed on title/package-source id formatting.
- Updated `PlaytestProcessor` to call the request helper methods instead of constructing ids inline.
- Key files: `src/Product/PartnerRegistryClient/Contracts/PlaytestRequest.cs`; `src/Product/PartnerRegistryService/Processors/PlaytestProcessor.cs`
- Commits: `d17cf3ed` Centralize playtest offering id and package source id on PlaytestRequest

### Playtest studio regions — branch `t-melanichen/playtest-studio-regions` (Status: Active; no PRProgress entry)
- Extends the configure-playtest endpoint branch with playtest offering region/id naming work.
- Configures created offerings with explicit regions in addition to `ServiceLevel.Studio`, DNA-group auth options, expiration, and title attachment.
- This branch contains the full older endpoint commit stack plus one region/id commit; `t-melanichen/playtest-studio-regions-main` is the smaller mainline version of the same region work.
- Key files: `src/Product/PartnerRegistryService/Processors/PlaytestProcessor.cs`; `src/Tests/Unit/PartnerRegistryService.UnitTests/Processors/PlaytestProcessorTests.cs`; `src/Product/PartnerRegistryClient/Contracts/PlaytestRequest.cs`
- Commits: `a4446e62` Configure playtest offering regions and id naming, plus the configure-playtest endpoint commits listed above (`f7176636` through `f9d73b50`)

### Playtest studio regions mainline — branch `t-melanichen/playtest-studio-regions-main` (Status: Active; no PRProgress entry)
- Reworked the region/id change as a smaller branch on mainline.
- Adds environment-conditional offering regions: non-prod uses `WestUS2` and `WestEurope`; prod uses `NorthCentralUs`.
- Keeps offering id construction centralized on `PlaytestRequest.GetOfferingId()` and preserves the title id prefix behavior expected at that point in the branch history.
- Added/updated unit tests for default non-prod regions and prod regions.
- Key files: `src/Product/PartnerRegistryClient/Contracts/PlaytestRequest.cs`; `src/Product/PartnerRegistryService/Processors/PlaytestProcessor.cs`; `src/Tests/Unit/PartnerRegistryService.UnitTests/Processors/PlaytestProcessorTests.cs`
- Commits: `adb9c215` Configure playtest offering regions and id naming; `72655938` Remove title id prefix change; `4bebae91` Make playtest regions environment-conditional; `665b8158` Centralize playtest offering id on PlaytestRequest.GetOfferingId

### PR 15849944 — Remove GetPackageSourceId from Playtest contract — branch `t-melanichen/remove-getpackagesourceid` (Status: Merged)
- Removed `PlaytestRequest.GetPackageSourceId`; Partner Registry no longer constructs a package-source/title id from offering id + title id.
- Changed `PlaytestProcessor` to register `requestTitle.TitleId` verbatim because ingestion sends the fully qualified `xpt{PlaytestProductId}-...` title id.
- Added `ConfigurePlaytest.linq` as a manual caller sample for POSTing the current contract and finding the created PR.
- Updated tests for the full title id format from ingestion.
- Key files: `src/Product/PartnerRegistryClient/Contracts/PlaytestRequest.cs`; `src/Product/PartnerRegistryService/Processors/PlaytestProcessor.cs`; `src/Tests/Unit/PartnerRegistryService.UnitTests/Processors/PlaytestProcessorTests.cs`; `ConfigurePlaytest.linq`
- Commits: `1c2469e9` Remove GetPackageSourceId from Playtest contract; `c998a44a` Fix playtest title Id to combine offering id and title id; `89a21c39` Update playtest tests to use full title ID format from Ingestion

### PR 15860243 — Refactor playtest title ID — branch `t-melanichen/refactor-title-id` (Status: Merged)
- Refactored playtest title handling so the title id supplied by ingestion is used directly as `Title.Id`.
- Avoids double-prefixing title ids and keeps content resolution aligned with the package id generated upstream.
- Updated unit test expectations and comments to use the full `XPT...-...` title id format.
- Key files: `src/Product/PartnerRegistryService/Processors/PlaytestProcessor.cs`; `src/Tests/Unit/PartnerRegistryService.UnitTests/Processors/PlaytestProcessorTests.cs`
- Commits: `8642d437` Refactor playtest title ID to use full format from Ingestion; `e7b55ce3` Refactor playtest title ID to use full format from Ingestion

### PR 15892276 — Set Xbox AuthenticationOptions on playtest offerings — branch `t-melanichen/playtest-offering-authentication-type` (Status: Merged; branch not present locally)
- Added `AuthenticationOptions` to playtest offerings with `AuthenticationType = Xbox`.
- Sets `UserIdClaimType` to the Xbox gamertag claim URI, matching the login path needed for DNA-group population and authorization.
- Added a unit test that verifies created playtest offerings include the Xbox authentication type and gamertag user-id claim.
- Key files: `src/Product/PartnerRegistryService/Processors/PlaytestProcessor.cs`; `src/Tests/Unit/PartnerRegistryService.UnitTests/Processors/PlaytestProcessorTests.cs`
- Commits: `cc253887` Merged PR 15892276: Set Xbox AuthenticationOptions on playtest offerings (merge commit found on `origin/main`; source branch not available in local refs)

### XC4B allow content ingestion S2S — branch `t-melanichen/xc4b-allow-content-ingestion-s2s` (Status: Active; no PRProgress entry)
- Git showed no commits and no changed files relative to `origin/main` for this branch.
- No Partner Registry code changes could be documented from this branch.
- Key files: none
- Commits: none

## Planned / remaining changes

- Resolve/confirm Xbox Live Title ID sourcing before the end-to-end flow can be fully reliable: the current plan is for Playtest to read service config through XORc/XCon once the title-id field is added, then thread the numeric title id into the ingestion payload. Source: [`Blockers/xbox-live-title-id.md`](../Blockers/xbox-live-title-id.md).
- Keep accounting for the manual Partner Registry PR approval gap: offering/title writes are ADO PRs, cannot be self-approved, and v1 should persist the returned `jobId`, poll indefinitely, and document the human approval requirement. Source: [`Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md).
- Cross-tenant S2S / SAGE integration tasks now consolidated in [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md).
- Region handling remains a v1/later split: v1 can assume West US2/single PC server + offering-conflict routing; later work may expose allowed-region selection and investigate DNS/IP-based routing. Source: [`FuturePlans/region-configuration-routing.md`](../FuturePlans/region-configuration-routing.md).
- Delete/tombstone lifecycle still needs xCloud sign-off: v1 likely tombstones by clearing `AllowedDnaGroups`, then performs a delayed GC delete after a grace period; the DELETE route is documented but not implemented/provisioned yet. Source: [`FuturePlans/delete-tombstone-lifecycle.md`](../FuturePlans/delete-tombstone-lifecycle.md).

## Open code TODOs / FIXMEs (in-branch)

Added by these branches (scanned from each branch's diff vs `origin/main`):

- `t-melanichen/configure-playtest-endpoint` and `t-melanichen/playtest-studio-regions` — `src/Product/PartnerRegistryService/Processors/PlaytestProcessor.cs`:
  - `// TODO: PC titles currently require a single hardcoded server SKU. This string is a temporary` placeholder. Remaining work is to replace the hardcoded PC server SKU with config/ECS-driven SKU selection (ties into [`FuturePlans/region-configuration-routing.md`](../FuturePlans/region-configuration-routing.md)).

## References

- Base branch used for git analysis: `origin/main`.
- Branches analyzed: `t-melanichen/add-allowed-dna-groups`; `t-melanichen/configure-playtest-endpoint`; `t-melanichen/playtest-offering-id-on-request`; `t-melanichen/playtest-studio-regions`; `t-melanichen/playtest-studio-regions-main`; `t-melanichen/refactor-title-id`; `t-melanichen/remove-getpackagesourceid`; `t-melanichen/xc4b-allow-content-ingestion-s2s`.
- PRProgress files: [`PRProgress/01-PTNR-15732852-add-allowed-dna-groups.md`](../PRProgress/01-PTNR-15732852-add-allowed-dna-groups.md); [`PRProgress/08-PTNR-15849944-remove-getpackagesourceid.md`](../PRProgress/08-PTNR-15849944-remove-getpackagesourceid.md); [`PRProgress/09-PTNR-15860243-refactor-playtest-title-id.md`](../PRProgress/09-PTNR-15860243-refactor-playtest-title-id.md); [`PRProgress/11-PTNR-15892276-playtest-offering-authentication-type.md`](../PRProgress/11-PTNR-15892276-playtest-offering-authentication-type.md).
- Planned/remaining docs: [`Blockers/xbox-live-title-id.md`](../Blockers/xbox-live-title-id.md); [`Blockers/manual-pr-polling.md`](../Blockers/manual-pr-polling.md); [`FuturePlans/s2s-cross-tenant-call.md`](../FuturePlans/s2s-cross-tenant-call.md); [`FuturePlans/region-configuration-routing.md`](../FuturePlans/region-configuration-routing.md); [`FuturePlans/delete-tombstone-lifecycle.md`](../FuturePlans/delete-tombstone-lifecycle.md).
