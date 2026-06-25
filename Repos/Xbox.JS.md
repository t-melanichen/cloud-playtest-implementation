# Repo: Xbox.JS (Bayside)

**Role:** Player-side cloud-gaming web client (**Bayside** = `apps/play-xbox`, play.xbox.com). The
surface a playtester lands on when they open the shared streaming link
(`https://play.xbox.com/play/launch/{productId}?offering.id=xpt{PlaytestProductId}`). Renders the
pre-stream screen, runs the offering-scoped (DNA-gated) login, and starts the cloud stream.

## Changes made
**None yet.** No `t-melanichen/*` branch exists in this repo as of 2026-06-15. All work below is
planned. (Note: `Xbox.JS` is listed as a project repo in the Partner Center pullrequests link in
`Context/InternProjectDocument.pdf` p.11, but no playtest branch has been created here.)

## Planned / remaining changes
Full design + file-by-file plan: [`../FuturePlans/bayside-playxbox-playtest-modifications.md`](../FuturePlans/bayside-playxbox-playtest-modifications.md).

Key discovery: Bayside **already has** the offering subsystem (active-offering state, the
`setActiveOfferingId({ offeringId, shouldPersist })` mutation, private/public offering queries, the
offering-scoped `/v2/login/user/delegated` login, a private-offering no-leak guard in the stream
loader, and an `OfferingErrorPage` denial UX). The intern work is mostly **wiring the launch link's
`offeringId` into that existing machinery**, not building it.

- **C1 (core) — apply `offeringId` from the launch link:**
  - `apps/play-xbox/src/app/routes/CloudConsoleStreamRoute.tsx` — read `offeringId` via
    `useSearchParams()` and call `setActiveOfferingId({ offeringId, shouldPersist: true })` (from
    `useSystems().services.gameStream.authentication.mutations`) before streaming.
  - `packages/@play-xbox/-route/game-stream/src/loader.server.ts` — parse `offeringId` from the URL and
    set the active offering before the `activeOfferingInfo`/product fetch, so SSR resolves the private
    offering and the existing `isPrivate` early-return (no-leak) fires on first paint.
- **C2 — login-first + no-leak:** verify an unauthenticated tester is gated before any render for
  private offerings (`ClientSideRenderGate.tsx` / `/auth/*`); add a gate only if a leak path exists.
- **C3 — denial UX copy:** reuse `OfferingErrorPage.tsx`; optionally add playtest-specific wording.
- **C4 — playtest title metadata:** validate `titleInfo`/`catalog` resolve name/art for a private
  playtest product; add a fallback if not.
- **C5 — PC "still preparing" / 404 window:** add a retry/"preparing your playtest" state when the
  offering is live but no PC server has the build yet (ties to PC-install polling + status accuracy).
- **C6 — feature-flag gate:** ship the wiring dark behind a flag (align with ECS gating).

## References
- Plan: [`../FuturePlans/bayside-playxbox-playtest-modifications.md`](../FuturePlans/bayside-playxbox-playtest-modifications.md)
- Related: [`../FuturePlans/launch-link-and-status-accuracy.md`](../FuturePlans/launch-link-and-status-accuracy.md),
  [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md),
  [`../FuturePlans/ecs-feature-flag.md`](../FuturePlans/ecs-feature-flag.md)
- Project objectives: `../Context/InternProjectDocument.pdf` (P0/P1 Bayside items: login-first, no-leak,
  stream-start, new-build version).
- Bayside code anchors: `apps/play-xbox/src/server/middleware/edgewaterLinkTransformation.ts:243-289`;
  `apps/play-xbox/src/app/routes/CloudConsoleStreamRoute.tsx`;
  `packages/@play-xbox/-route/game-stream/src/{GameStreamPage,CloudStreamingClientSideContext,OfferingErrorPage,loader.server}.tsx`;
  `packages/@play-xbox/-dialog/-route/settings/.../DeveloperTab/OfferingInfo.tsx:336-408` (offering switch).
