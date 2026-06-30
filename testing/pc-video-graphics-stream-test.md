# Testing the stream with the new PC video graphics

Notes from the **2026-06-30 Design Brainstorm** (`Transcripts/Design Brainstorm - Playtest UX.docx`, local-only)
on validating the end-to-end PC playtest stream with an obviously-moving image, so you can *see* the stream is
actually rendering (not a frozen/black frame).

## Test content — ATG PC "VideoTexture12" sample

Use the Microsoft **ATG (Advanced Technology Group) PC sample "video texture"** as the streamed content:

- Find it on GitHub: search **"ATG PC samples video texture"** (a.k.a. "ATG/ATC samples PC graphics video
  texture"). Clone the whole samples repo and open the **VideoTexture12** solution (the DirectX 12 video-texture
  sample for PC / `.sln`).
- Out of the box it renders a **spinning rectangle with a video mapped onto it** — an obvious, continuously
  moving image that makes it immediately clear the stream is live.
- Optional (more engaging): with a small amount of AI-assisted tweaking, make **multiple balls bounce around**,
  each playing video — more motion across the frame, easier to eyeball latency/jank.

## Harness & accounts

- **Test harness:** the **Xbox Stream harness** drives the stream.
- **Test publisher:** **"X cloud test publisher 1."**
- **Pilot seller gate:** streaming is only enabled for the **pilot seller id `65050620`** (confirmed in the
  meeting: *"streaming's only enabled if it's my seller id"*). Run e2e as that seller.
- **PC to stream from:** you need a **provisioned PC server** with the build installed/streamable (the brainstorm
  explicitly asked *"what kind of PC are you getting to stream this off of?"*). Tie-in with PC install-readiness
  polling — see [`../FuturePlans/pc-install-readiness-polling-implementation.md`](../FuturePlans/pc-install-readiness-polling-implementation.md).

## Pre-reqs for a clean e2e (from the Xbet publish/XORc flow)

- The pilot seller's **test product must be Xbox-Live-configured** (resolves a `TitleId` in XORc) — otherwise
  publish **fails fast** when streaming is opted in.
- Give the test playtest a **future end date** (`PlaytestEndDateMustBeInFutureRule` now blocks already-expired
  playtests for all sellers).
- XORc must be reachable from PlayTest in the target env (a transient XORc 5xx fails the pilot-seller publish).

## What this validates

Configuring a playtest → publishing (PlayTest → XORc title-id resolution → workflow → SAGE ingestion) →
launching the deep link → **seeing the spinning/bouncing video render** over the cloud stream end to end.

## References

- `Transcripts/Design Brainstorm - Playtest UX.docx` (local-only) — the testing discussion.
- [`../Explanations/xbet-15834601-design-decisions.md`](../Explanations/xbet-15834601-design-decisions.md) — the publish→XORc→SAGE flow.
- [`../Playtest-UI-Meeting-Karla-Kush.md`](../Playtest-UI-Meeting-Karla-Kush.md) — meeting conclusions / e2e status.
