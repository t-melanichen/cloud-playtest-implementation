# Blocker — signed-out / cached playtest content leak (e2e)

**Status:** 🔴 Open · **Found:** 2026-06-30 Design Brainstorm (live demo) · **Surface:** Bayside / Garrison
(play.xbox.com) · **Owner:** @t-melanichen (to repro), Bayside/Garrison client owners

## Symptom

During the live demo, **signing out of Garrison and then launching the playtest deep link still showed the
playtest content** — believed to be **cached client-side**. Paraphrasing the meeting: *"I just found a bad bug —
when I signed out of Garrison and then launched, the deep link showed me the playtest content… I believe that's
because that playtest had been cached"* and *"I'm getting all sorts of playtests that I shouldn't be seeing."*

## Why it's a blocker

It violates the **login-first / no-leak** requirement for private playtests (Bayside step **#5**): a
signed-out or non-member user must **not** see the playtest's title, art, metadata, or content. A cached
deep-link path that renders playtest content without a valid, authorized session is a privacy/leak defect and is
a hard gate for the pilot.

## Suspected cause

- Client-side **caching** of playtest content (offering/title) that is served from cache on the deep-link path
  **without re-validating** the auth/authorization state — so after sign-out the cached content still renders.
- Possibly compounded by the deep-link route not forcing the **login-first** gate before any render for private
  (`xpt`) offerings.

## What to verify / fix

1. **Reproduce** deterministically: sign in → open playtest → sign out → relaunch deep link → observe leak.
2. Confirm whether the content is coming from **client cache** vs the **server** (CAS / `/offerings`).
3. **Server-side no-leak:** CAS / `/offerings` must return a private playtest offering **only** to authorized
   users, so an anonymous/non-member request never learns it exists (defense in depth, independent of cache).
4. **Client-side:** clear/scope playtest content cache on **sign-out**, and force the **login-first** gate on the
   deep-link path before rendering anything for a private offering (model on `InsiderPreviewGateLayout`).
5. Add regression coverage for the signed-out and non-member deep-link paths.

## References

- [`../FuturePlans/ui-steps-bayside.md`](../FuturePlans/ui-steps-bayside.md) #5 (login-first + no-leak denial UX).
- `Transcripts/Design Brainstorm - Playtest UX.docx` (local-only) — the live repro.
- [`../Playtest-UI-Meeting-Karla-Kush.md`](../Playtest-UI-Meeting-Karla-Kush.md) — meeting conclusions / e2e status.
