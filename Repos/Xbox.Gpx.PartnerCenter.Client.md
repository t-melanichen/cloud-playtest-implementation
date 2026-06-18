# Repo: Xbox.Gpx.PartnerCenter.Client

**Role:** Partner Center creator-facing Playtest wizard — surfaces streaming enable, duration cap, audience restriction.

## Changes made

Branch: `t-melanichen/playtest-streaming-enable-flag` / `playtest-streaming-enable-flag`

Base found: `origin/main` (`f2bd626e382805174d01df69dd935283e461fa59`)

Merge base: `dfdbab282b152ab90df0a113b15b77993bd7d915`

Status: branch exists locally and at `origin/t-melanichen/playtest-streaming-enable-flag`; no PRProgress entry was found for this repo, so treat status as branch-only/local-to-remote branch (not tracked by PRProgress). The working tree currently also has unrelated local deletes/untracked files outside this playtest change.

Commits:

- `2932e951b` Add playtest cloud streaming flag

Diff summary from merge base:

- 17 files changed, 451 insertions, 1 deletion.
- Added a feature-gated **Enable Cloud Streaming** field to the Playtest form.
- Added `XboxPlaytestCloudStreaming` to the Partner Center/GPM feature flag defaults, disabled by default.
- Added form state fields for `enableCloudStreaming`, `cloudStreamingEndDate`, and `cloudStreamingEndTime`.
- Added validation and tests for a cloud streaming end date: required when streaming is enabled, not before start date, and no more than 7 days after start.
- Added localized strings for the toggle, cloud streaming end date label, and validation errors.
- Updated review/mocks/model tests so existing Playtest flows understand the new fields while defaulting streaming to off.

Key files:

- `apps/packages/src/helpers/featureFlags.ts` — adds `XboxPlaytestCloudStreaming: boolean` and default `false`.
- `apps/packages/src/components/PlaytestForm/fields/PlaytestCloudStreamingField.tsx` — new React field hidden unless `XboxPlaytestCloudStreaming` is enabled; shows the checkbox and, when selected, cloud streaming end date/time controls capped to 7 days.
- `apps/packages/src/components/PlaytestForm/PlaytestForm.tsx` — initializes the new form fields and renders `PlaytestCloudStreamingField` after the existing date fields.
- `apps/packages/src/components/PlaytestForm/playtestFormSchema.ts` — adds schema fields and `superRefine` validation for streaming end date required/before-start/too-late cases.
- `apps/packages/src/components/PlaytestForm/playtestTypes.ts` — extends `PlaytestFormValues` with streaming fields.
- `apps/packages/src/localization/strings/strings.en-us.json` and `strings.json` — add `Enable Cloud Streaming`, `Cloud streaming end date`, and error strings.
- Test coverage added/updated in `PlaytestCloudStreamingField.test.tsx`, `playtestFormSchema.test.ts`, `PlaytestForm.test.tsx`, `featureFlags.test.ts`, `models/playtest.test.ts`, `PlaytestReview.test.tsx`, and `ReviewDetailsSection.test.tsx`.

## Planned / remaining changes

From `.github/agents/playtest-streaming.md` Partner Center UI plan and `FuturePlans/ecs-feature-flag.md`:

- **Enable Cloud Streaming toggle** — finish the additive wizard behavior behind a feature flag/ECS seller allow-list. When off, Playtest remains download-only. Remaining work likely includes wiring the selected value/end date to the create/update API once backend contract support exists.
- **30-day max duration cap for streaming playtests** — enforce the InternSync4 rule (raised from 7 days on 2026-06-18) that streaming-enabled playtests cannot run longer than 30 days and cannot use `noEndDate`; see [`FuturePlans/expiration-cap-30-days.md`](../FuturePlans/expiration-cap-30-days.md). The current branch adds a separate cloud-streaming end-date cap; remaining planned work should align this with the overall Playtest start/end-date validation (`playtestFormSchema.ts` / `PlaytestDatesField.tsx`) per spec.
- **Xbox-Live-IDs-only audience restriction** — when streaming is enabled, restrict `components/AudienceSelection` to groups backed by Xbox Live IDs and surface a validation error using the existing `playtestServiceErrorMap`/`constants/playtest.ts` pattern.
- **ECS feature-flag gating** — use ECS to gate private preview access by seller ID (seller-only vs seller+product granularity still open). David K is expected to help create/configure the ECS settings/permissions; deployment is required for ECS config changes.

## References

- Repo path: `C:\Users\t-melanichen\OneDrive - Microsoft\Desktop\Xbox.Gpx.PartnerCenter.Client`
- Branch: `t-melanichen/playtest-streaming-enable-flag`
- Git commands used: `git -C "<repo>" --no-pager log --oneline origin/main..t-melanichen/playtest-streaming-enable-flag`; `git -C "<repo>" merge-base origin/main t-melanichen/playtest-streaming-enable-flag`; `git -C "<repo>" --no-pager diff --stat <mergebase>..t-melanichen/playtest-streaming-enable-flag`; `git -C "<repo>" --no-pager diff --name-only <mergebase>..t-melanichen/playtest-streaming-enable-flag`.
- Spec: `.github/agents/playtest-streaming.md`, section `Partner Center UI changes (planned, Xbox.Gpx.PartnerCenter.Client)`.
- Future plan: `FuturePlans/ecs-feature-flag.md`.
- PRProgress: no `Xbox.Gpx.PartnerCenter.Client` PRProgress file found under `cloud-playtest-implementation\PRProgress`; current PRProgress entries cover PTNR, AUTH, DEVAPI, PTNR-DATA, CTIN, SAGE, XBET, and PTNR follow-ups.
