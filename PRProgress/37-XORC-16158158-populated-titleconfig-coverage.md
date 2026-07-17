# [XORC] PR 16158158 — Add unit coverage for populated XboxLiveTitleConfig branch in ProductXboxLiveConfigurationHandler

- **Pull Request:** 16158158
- **Repo:** xorc (Xbox.Services)
- **Source branch:** `t-melanichen/add-populated-titleconfig-coverage` → `develop`
- **Status:** Active (opened 2026-07-13)
- **Reviewers:** Brian Trevethan, Anthony Keller
- **Link:** https://dev.azure.com/microsoft/Xbox.Services/_git/xorc/pullrequest/16158158
- **Work item:** Task 63048045

## Summary
Test-only follow-up to PR 15894506. Brian Trevethan flagged (on the `develop` → `master` PR **16061059**) that the
tests in `ProductXboxLiveConfigurationHandlerTests` never exercised the branch they claimed to: because
`GetXboxLiveTitleConfigAsync` is an **extension method** over `IScidClient.GetScidDocumentsAsync`, the loose mock
returned empty documents and all four tests silently ran the `titleConfig == null` path — so the populated branch
that copies `XboxLiveEmbargoDate` / `EmbargoInvitesEnabled` from the SCID result had **no coverage**, and two tests
were behavioural duplicates.

- Parametrizes `ExecuteHandlerAsync` with an optional productdeveloper document and stubs `GetScidDocumentsAsync`
  (matching the product's service config id, `AllSandbox`, and the productdeveloper document filter) — the only
  mockable seam, since Moq **cannot** stub the extension method directly (it throws `NotSupportedException`). Reuses
  the pattern already in `ScidClientExtensionsTest`.
- Adds `GetXboxLiveConfig_PopulatedTitleConfig_CopiesEmbargoFieldsFromScid`, asserting the embargo date and invites
  flag are copied from the SCID result.
- Strengthens the null-config test to assert `XboxLiveEmbargoDate == null` / `EmbargoInvitesEnabled == false`, so it
  is no longer a duplicate of the title-id test.
- Kept the `GetScidDocumentsAsync` setup and `CreateEmptyScidDocumentsResponse()` (not dead code — that is the real
  call the handler makes through the extension, and the empty response drives the null path).

**Validation:** solution builds with 0 errors; all 5 `ProductXboxLiveConfigurationHandlerTests` pass (net472).

## Context
- Follow-up to [`16-XORC-15894506-expose-xbox-live-title-id.md`](./16-XORC-15894506-expose-xbox-live-title-id.md)
  — the PR that added the `TitleId` field and these tests.
- Gap raised by **Brian Trevethan** on PR 16061059 (xorc `develop` → `master` merge); **Anthony Keller** asked for
  the follow-up and pointed at the work item.
- Work item: Task **63048045** (`Xbox\Developer\CORS\Publishing`; tags `Instant-Playtest`, `ProjectJuno`).
- Note: `xorc` targets `develop` (not `main`/`master`).
