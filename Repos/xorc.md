# Repo: xorc (XORc)

**Role:** Xbox Live service-config read API — resolves numeric Xbox Live Title ID for `StoreAsset.XboxTitleId`.

## Changes made

**Clone used:** `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\xorc-1` (active clone).  
**Branch:** `t-melanichen/playtest-xbox-live-title-id` / `playtest-xbox-live-title-id`.  
**Base found:** `origin/master`; merge-base `f1a12792ee83c4a98c800cab2209797c179c3bd0`.  
**Pushed/local:** branch is pushed and local is even with `origin/t-melanichen/playtest-xbox-live-title-id` (`rev-list --left-right --count` = `0 0`).  
**PRProgress:** no `PRProgress` file found in `xorc-1`; treat as branch-only/draft.

### Playtest / Xbox Live Title ID work

- Added `TitleId` to the `GET /products/{id}/xboxliveconfig` response contract so callers can receive the numeric Xbox Live Title ID.
- Populated response `TitleId` in `ProductXboxLiveConfigurationHandler` from `product.TitleId`, returning `null` when the stored value is `0`.
- Kept existing Xbox Live config fields (`XboxLiveEmbargoDate`, `EmbargoInvitesEnabled`) sourced from SCID/XCon service config.
- Follow-up commits adjusted comments and removed an unnecessary cast/nit.

### Other changes present on this branch vs merge-base

The branch diff also includes two broader merged changes that are present in the branch history:

- `c3790745` — merged PR 15759887, adding `Documentation/AiPlans/PlaytestPgManagerTool.md`.
- `bcffc572` — merged PR 15608584, removing XACH and XblConfigGateway client code/settings/NuGet packages and deleting legacy migration/image-migrator worker/tooling pieces.

### Key files

- `Contracts/Web/XboxLiveTitleConfig.cs` — adds nullable `uint? TitleId` JSON response field.
- `Service/Handlers/ProductXboxLiveConfigurationHandler.cs` — sets `TitleId = product.TitleId != 0 ? unchecked((uint)product.TitleId) : null` in the response.
- `Documentation/AiPlans/PlaytestPgManagerTool.md` — added by the carried merged PR.

### Commits

- `b5c887d8` — `nit: rm cast`
- `b8843cb3` — `Comments`
- `70006143` — `Add Xbox Live TitleId to products/{id}/xboxliveconfig response`
- `c3790745` — `Merged PR 15759887: Add AI plan for PlaytestPgManager tool`
- `bcffc572` — `Merged PR 15608584: Remove XACH and XblConfigGateway client code, settings, and NuGet packages`

### Diff summary

`git diff --stat f1a12792ee83c4a98c800cab2209797c179c3bd0..t-melanichen/playtest-xbox-live-title-id` reports **63 files changed, 555 insertions(+), 4459 deletions(-)**.

Notable file-level changes include:

- `Contracts/Web/XboxLiveTitleConfig.cs` modified for the Title ID response field.
- `Service/Handlers/ProductXboxLiveConfigurationHandler.cs` modified to populate the response field.
- `Documentation/AiPlans/PlaytestPgManagerTool.md` added.
- XACH/XblConfigGateway client config/code removed from `Common`, `Test/Functional`, `Tools/XdpShellAppImport`, `Worker`, and `XdpMigration` areas.
- Product migration worker/handler files removed, including `Worker/Workers/WorkflowWorker.ProductMigrate.cs`, `Worker/Workflows/ProductMigrate.cs`, and `Service/Handlers/XdpProductMigrateHandler.*.cs`.
- Image migration project files removed under `XdpMigration/ImageMigrator`.
- XMS translation/image processing files moved or updated under `XdpMigration/XmsTranslation` and `XmsTranslation.UnitTests`.
- `XORC.sln`, project files, package props, service cfginc files, worker wiring, and functional tests updated to reflect the removals.

### Other clone check

Checked `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\xorc` with `git branch -a --list "*t-melanichen*"`; no `t-melanichen` branches were present. Current branch there is `develop`, so it appears duplicate/stale for this work and has no unique user-branch changes to include.

## Planned / remaining changes

From `Blockers\xbox-live-title-id.md` in `cloud-playtest-implementation`:

- Confirm the exact XORc service-config read API endpoint, auth, and required inputs with Anthony's team.
- Ensure/complete adding the numeric Title ID field to the XORc service-config API response (`products/{id}/xboxliveconfig`).
- Wire an xPlaytest resolver in the publish path to call XORc, read the title id, and pass it into `PlaytestIngestionPayloadBuilder.Build(...)`.
- Replace the current hardcoded empty `XboxLiveTitleId` in `PlaytestProductDocumentBuilder`.
- Remove the temporary placeholder once the real Xbox Live Title ID flows end to end.

## References

- Active repo: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\xorc-1`
- Other clone checked: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\xorc`
- Branch: `t-melanichen/playtest-xbox-live-title-id`
- Base: `origin/master`
- Merge-base: `f1a12792ee83c4a98c800cab2209797c179c3bd0`
- Primary driver doc: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\cloud-playtest-implementation\Blockers\xbox-live-title-id.md`
- Context: Playtest needs `StoreAsset.XboxTitleId`; resolution path is **Playtest → XORc service-config API → Xbox Live service config sourced from XCon**.
