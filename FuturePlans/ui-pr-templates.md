# Future plan: UI PR templates & branch policy (both UI repos)

**Why it matters:** The two creator/player UI repos in the Instantly Shareable Playtest project
enforce **different** PR title formats and templates. Use the right one when opening UI PRs so
branch policy doesn't block the PR. Records the as-of-2026-06-19 templates and the filled-in
descriptions for the two current UI branches.

---

## Xbox.Gpx.PartnerCenter.Client (Partner Center / GPM creator UI)

**Branch policy — enforced for PRs touching `apps/packages/`** (see `docs/BuildPipelines.md`,
`apps/packages/README.md`):
- PR **title** must start with `[feature|fix|chore|docs|refactor|task] <subject>`.
- A `Design Doc:` link (or `N/A`) is required for **feature / refactor / docs** PRs.
- At least one **CODEOWNERS** reviewer approval.
- The template also carries Accessibility / Globalization / UX / Testing / General checklists.
- For other apps these fields are optional but encouraged.

### Filled PR — `t-melanichen/playtest-streaming-enable-flag` (Enable Cloud Streaming + 30-day cap)

> Title: `[feature] Add Enable Cloud Streaming option to the Playtest form (flag-gated, 30-day cap)`
> Checked boxes = done on the branch. Unchecked items (manual a11y / RTL / browser / visual) need
> validation in a running GPM app before submitting.

```markdown
## Type

-   [x] `[feature]`
-   [ ] `[fix]`
-   [ ] `[chore]`
-   [ ] `[docs]`
-   [ ] `[refactor]`
-   [ ] `[task]`

## Design Doc

Design Doc: N/A  <!-- replace with the Instantly Shareable Playtest design-doc URL if one exists -->

## What changed?

Adds an additive, **feature-flagged** "Enable Cloud Streaming" option to the Playtest creation
form (`apps/packages/src/components/PlaytestForm`). Gated behind the `XboxPlaytestCloudStreaming`
GPM feature flag (default **off** → no change to today's download-only flow):

-   New **Enable Cloud Streaming** checkbox (`fields/PlaytestCloudStreamingField.tsx`). When
    checked it reveals a **Cloud streaming end date** date-picker + a **Time** select.
-   Validation (`playtestFormSchema.ts` `superRefine`): the cloud-streaming end date is **required**
    when streaming is enabled, must be **after the start date**, and **at most 30 days after the
    start date** (raised from the initial 7-day cap per InternSync4). `noEndDate` stays disallowed
    for streaming.
-   New form state `enableCloudStreaming` / `cloudStreamingEndDate` / `cloudStreamingEndTime`
    (`playtestTypes.ts`, `PlaytestForm.tsx`), defaulting streaming off so existing flows are
    unchanged. Review/model/mocks updated accordingly.
-   `XboxPlaytestCloudStreaming` added to `helpers/featureFlags.ts` (default `false`).
-   Localized strings added to **both** `strings.en-us.json` and `strings.json` (toggle label,
    end-date label, and the three validation errors).
-   Unit tests added/updated and green; `yarn lint` clean.

## Screenshot(s)

<!-- Flag-gated. To view: run the GPM app, then in the browser console set
     `window.gpmFeatureFlags = { ...window.gpmFeatureFlags, XboxPlaytest: true, XboxPlaytestCloudStreaming: true }`
     and open the Playtest wizard. Add before (toggle off, unchanged) and after (checkbox + end
     date/time) shots. -->

## Link to Figma

N/A

## Accessibility

-   [ ] Did you check that both light and dark themes meet color contrast guidelines?
-   [ ] Are you using semantic HTML elements?
-   [ ] Do all buttons have accessible names and labels?
-   [ ] Did you check keyboard and screenreader support?
-   [ ] Did you check that all elements are visible at zoom levels of at least 400%?

<!-- Field reuses existing Harmony Checkbox / DatePicker / Select; verify the above in a running app. -->

## Globalization

-   [ ] Did you check that RTL behaves as expected?
-   [ ] Did you make sure to follow pluralization rules when needed?

<!-- Strings added to en-us + base per convention; RTL/plural still need a manual pass. -->

## UX

-   [ ] Did you check that the project works in all supported browsers (Edge, Chrome, Firefox on Windows, Safari on Mac)?
-   [ ] Did you make sure that pages are responsive for all window sizes > 500px?

## Testing

-   [ ] Did you perform manual tests to check the new component(s)?
-   [x] Did you write any necessary unit/integration tests? (schema, field, feature-flag, form, review)
-   [ ] Did you update _coverageThreshold_ in _jest.config.js_ files to reflect the new minimum code coverage percentage?
-   [ ] Did you update storybook snapshots?
-   [ ] If you added or modified a data service, did you update `apiMocks.ts`? (n/a — no data service change)

## General

-   [ ] Did you update any necessary documentation?
```

---

## Xbox.JS (Bayside / play.xbox.com player-side client)

**PR title — Conventional Changelog / Conventional Commits:** `{type}({scope}): {short description}`
- **type**: `feat | fix | docs | style | refactor | perf | test | chore | revert`
- **scope**: affected area, e.g. `play-xbox/{context}`, `xbox-js/{module}`, `edgewater/{context}`,
  `xds/{component}`, or repo-level `xbox-js` / `play-xbox` / `edgewater` / `xds`.
- Body sections: **Context** (the *why*), **Changes** (what was added/changed/removed),
  **Screenshots** (remove the section if not applicable).

### Filled PR — `t-melanichen/playxbox-playtest-launch` (launch-link offeringId → active offering)

> No Screenshots section (behavioral change, no new UI).

```markdown
feat(play-xbox/game-stream): apply launch-link offeringId to the active offering

# Context

Bayside is the surface a playtester lands on when they click a shared streaming link,
`https://play.xbox.com/play/launch/{productId}?offering.id=xpt{PlaytestProductId}`. Today the
cloud-stream route reads only the `productId` path param and ignores the `offeringId` query param,
so a clicked playtest link streams the default **retail** offering instead of the private,
DNA-gated **playtest** offering. This change threads `offeringId` into Bayside's existing offering
subsystem by setting it as the active offering before streaming, so the offering-scoped (DNA-gated)
login and stream start run against the playtest offering. It reuses the proven `setActiveOfferingId`
mutation (the same one the Developer settings tab uses) and is fully backward compatible — retail
links without the param behave exactly as before. This is the "C1" core wire from
`FuturePlans/bayside-playxbox-playtest-modifications.md`; the server-side first-paint hardening and
the denial / "still preparing" UX are tracked as follow-ups.

# Changes

-   **Feature:** `apps/play-xbox/src/app/routes/CloudConsoleStreamRoute.tsx` now reads `?offering.id`
    via `useSearchParams` and applies it with `setActiveOfferingId({ offeringId, shouldPersist: true })`
    in an effect before streaming. A ref-guard applies each distinct id once; absent param = no-op.
```

---

## References / Sources
- User-provided PR templates (2026-06-19) for both repos.
- `Repos/Xbox.Gpx.PartnerCenter.Client.md`, `Repos/Xbox.JS.md`.
- `FuturePlans/bayside-playxbox-playtest-modifications.md`, `FuturePlans/expiration-cap-30-days.md`.
- Branches: `t-melanichen/playtest-streaming-enable-flag` (PartnerCenter, commit `40e5b2fd8`),
  `t-melanichen/playxbox-playtest-launch` (Xbox.JS, commit `f8451f133`).
