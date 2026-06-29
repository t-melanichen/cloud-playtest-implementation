# Playtest UI meeting prep — Karla & Kush

**Date:** TBD · **Attendees:** Melanie Chen, Karla (design/UX), David Kushmerick (Kush, PM) · **Owner:** @t-melanichen

**Purpose:** Align on the playtest UI changes across the two front ends, agree on priority/scope for the
remaining internship time, and get design + PM decisions on the open UX questions.

---

## The two UIs (what each surface is)

| Surface | Repo | Who uses it | Role in the flow |
|---------|------|-------------|------------------|
| **Partner Center (creator portal)** | `Xbox.Gpx.PartnerCenter.Client` | The **game creator** | Turns on cloud streaming for a playtest, sets the audience, and gets the shareable link. |
| **Bayside (play.xbox.com)** | `Xbox.JS` (`apps/play-xbox`) | The **invited tester** | Where a tester lands when they click the link and actually streams the build. |

**One-line framing for the meeting:** the backend (audience → offering → ingestion → PC servers → readiness) is
now largely merged; the remaining work is the **two UIs that bookend it** — the creator turning it on and sharing,
and the tester clicking in and streaming.

---

## Partner Center (creator) — what I plan to change

Already in a PR: the **"Enable Cloud Streaming" toggle + end date/time + 30-day cap** (PR #15946761).

| # | Change | Priority | Effort | Notes |
|---|--------|----------|--------|-------|
| 1 | **Shareable streaming link** in the portal (copy button), shown once the build is ready | P0 | FE 🟢 / E2E 🟡 | Reuses the existing `SharePlaytestModal`. Link: `play.xbox.com/play/launch/{productId}?offering.id=xpt{ProductId}`. Needs backend to expose URL + "ready" status. |
| 2 | **Audience restricted to Xbox-Live-ID groups** when streaming is on | P0 | 🟡 | Filter selectable groups + validation error when a non-XL group is picked. Maps to `AllowedDnaGroups`. |
| 3 | **"Build ready for testing" status** feedback (per endpoint: download vs stream) | P2 (stretch) | 🟡 | Needs the readiness signal to roll up from ingestion. |
| 4 | Launch args / region / touch controls / feedback collection | P3 (stretch) | 🔴 | Cross-team (GSSV) support needed; likely out of internship scope. |

## Bayside (player) — what I plan to change

Already merged: **C1** — the launch link's `offering.id` is read and set as the active offering before streaming.

| # | Change | Priority | Effort | Notes |
|---|--------|----------|--------|-------|
| 5 | **Login-first + "you're not in this playtest" denial UX** (no metadata leak) | P0/P1 | 🟢–🟡 | Reuses existing `OfferingErrorPage` + offering-scoped login; mostly copy + a gate if a leak path is found. |
| 6 | **Show playtest title / art / genre** for the private build | P0 | 🟢 / 🟡 | Validate retail catalog serves a private product; add a fallback if not. |
| 7 | **"Install locally vs stream now" choice** | P0 (stream) / P3 (install) | 🔴 | Install branch needs Garrison/Bastion private-offering support (largest unknown). |
| 8 | **"Build still preparing, keep trying" retry state** (PC build not on a server yet) | P0 | 🟡 | Friendly retry instead of a 404 during the PC first-install window. |
| 9 | **Feature-flag gate** (ship dark, light up for allow-listed sellers) | P1 | 🟡 | ECS / preview-gate; David K owns ECS. |

---

## Cross-cutting UX decisions to align on

1. **"Build preparing" experience** — what does the tester see in the window between clicking the link and the
   PC build actually being streamable? (retry spinner? progress? "we'll email you"?) Same idea appears creator-side (#3) and player-side (#8).
2. **Denial / no-leak copy** — exact wording when a non-member clicks the link. Must reveal nothing about the title.
3. **Link sharing UX** — copy-button only, or also "invite by group"? Where does the link live in the portal (review page vs list)?
4. **Stream vs install** — do we even surface "install" for v1, or stream-only first and add install later?
5. **Streaming vs non-streaming audience** — when streaming is on we must restrict to Xbox-Live-ID groups; how do we explain that constraint to the creator without confusion?

---

## Discussion topics / questions

**For Karla (design/UX):**
- Mocks/flows for the **share-link surface** and the **"not in this playtest" denial page** — do we have or need designs?
- The **"preparing your playtest" retry state** — preferred pattern (spinner + retry, progress %, etc.)?
- Should there be a **"non-public / preview build" badge** in Bayside so testers know it's a playtest?
- Where does the **audience-restriction explanation** live in the creator form (inline helper text, tooltip, disabled-with-reason)?

**For Kush (PM / scope):**
- **Priority call for the remaining time:** confirm P0 set = Partner Center #1 (share link) + #2 (audience) and Bayside #5 (denial) + #6 (metadata) + #8 (preparing). Agree what's explicitly out (install #7, launch-args #4).
- **Stream-only for v1?** Defer the "install locally" branch (Garrison/Bastion) entirely?
- **Feature-flag / private-preview gating (#9)** — who's on the allow-list for first testing, and is ECS the gating mechanism (David K owns it)?
- **Metadata for private products** — is there a known answer on whether catalog serves a private playtest product, or do we need a CAS ask?

**Open dependencies to flag:**
- Does the cloud session-allocation API accept an **offering id** today, or is a platform change needed? (gates Bayside stream-start)
- xPlaytest must expose the **launch URL + "streaming ready" status** for the portal to show the link (#1, #3).
- The **status/404 window** (XProduct is async) — link must not surface until the build is truly live.

---

## Asks / decisions I want to leave with
1. Agreed **P0 scope** for both UIs (so I can sequence the remaining PRs).
2. Design direction (or designs) for the **share link**, **denial page**, and **preparing/retry** states.
3. Decision on **stream-only vs install** for v1.
4. Owner + mechanism for the **feature-flag gate** and the first allow-list.

## References
- `FuturePlans/ui-steps-partnercenter.md` — creator-side breakdown (#1–#4).
- `FuturePlans/ui-steps-bayside.md` and `FuturePlans/bayside-playxbox-playtest-modifications.md` — player-side breakdown (#5–#9, C1–C6 / W1–W7).
- `FuturePlans/launch-link-and-status-accuracy.md`, `FuturePlans/ecs-feature-flag.md`, `FuturePlans/pc-install-readiness-polling-implementation.md`.
