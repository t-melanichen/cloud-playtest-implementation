# [GPM] PR 15946761 — Enable Playtest Cloud Streaming (Partner Center form toggle)

- **Pull Request:** 15946761
- **Repo:** Xbox.Gpx.PartnerCenter.Client (Xbox)
- **Source branch:** `t-melanichen/playtest-streaming-enable-flag` → `main`
- **Status:** Draft
- **Opened:** 2026-06-19
- **Link:** https://dev.azure.com/microsoft/Xbox/_git/Xbox.Gpx.PartnerCenter.Client/pullrequest/15946761

## Summary
Adds the creator-facing **Enable Cloud Streaming** option to the Playtest creation form
(`apps/packages/src/components/PlaytestForm`), additive and gated behind the `XboxPlaytestCloudStreaming`
GPM feature flag (default **off**, so today's download-only flow is unchanged).

- New **Enable Cloud Streaming** checkbox (`fields/PlaytestCloudStreamingField.tsx`); when checked it reveals
  a **Cloud streaming end date** date-picker and a **Time** select.
- Validation (`playtestFormSchema.ts` `superRefine`): the cloud-streaming end date is required when streaming
  is enabled, must be after the start date, and **at most 30 days after start** (raised from the initial
  7-day cap per InternSync4). `noEndDate` stays disallowed for streaming.
- New form state `enableCloudStreaming` / `cloudStreamingEndDate` / `cloudStreamingEndTime`
  (`playtestTypes.ts`, `PlaytestForm.tsx`), defaulting off; review/model/mocks updated.
- `XboxPlaytestCloudStreaming` added to `helpers/featureFlags.ts` (default `false`); localized strings added
  to both `strings.en-us.json` and `strings.json`.

## Context
- The front-end half of the streaming opt-in; the backend reads the resulting intent (eventually the
  `IncludeStreaming` flag — XBET PR 15834601, #10, AB#62878234).
- Enforces the 30-day expiration cap decision (InternSync4) at the UX, per Anthony's "cap the UX if the
  platform caps."

## Validation
- Unit tests added/updated (schema, field, feature-flag, form, review) and green; `yarn lint` clean.
- Manual/accessibility/globalization passes still pending (front-end checklist).
