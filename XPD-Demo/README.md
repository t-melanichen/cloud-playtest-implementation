# XPD / XBOX Developer Demos deck

My **sub-10-minute** talk for the internal **XBOX Developer Demos** series
(Wed Jul 22, 2026), on **Instantly Shareable Playtest** (xPlaytest × xCloud streaming).

Follows the same **"asked → built → delivered"** arc as my end-of-internship demo
([`../Presentation`](../Presentation)), trimmed, with a **recorded end-to-end demo** as the payoff.
Reuses that deck's theme and `python-pptx` tooling.

Flow: **Title → About me → Problem → Vision → How it works → Payload builder → Hard problem → DEMO
→ What I delivered → Thanks**.

## Contents

| File | What it is |
|------|------------|
| `XPD-Developer-Demo.pptx` | The generated deck (10 slides + a detailed-architecture appendix, 16:9), speaker notes in the notes pane. |
| `outline.md` | Slide-by-slide narrative **+ speaker notes** — the content source of truth. |
| `speaker-script.md` | Word-for-word **talk track**, timed to sub-10 min. |
| `demo-script.md` | The **recording plan** for the slide-8 demo (setup, beats, narration, fallback). |
| `build_deck.py` | The `python-pptx` generator. |
| `Demo/` | Drop your screen recording here; it auto-embeds on the DEMO slide. |
| `README.md` | This file. |

## Add your recorded demo

Record the end-to-end flow (publish → stream), then drop the file in `Demo/`:

```
XPD-Demo\Demo\<your-recording>.mp4    # .mp4 / .m4v / .mov / .webm / .avi
```

Re-run `build_deck.py` and it embeds the **first** video it finds on the DEMO slide
(a styled ▶ placeholder is shown until then). Suggested beats for the recording:

1. Creator opts in to cloud streaming and **publishes** a playtest.
2. Backend threads the build across two clouds (payload → cross-tenant Green→Corp via SAGE → ingest → readiness poll).
3. Invited tester opens the **share link** and **streams** the private retail build — no install, no devkit.

> Keep the recording ~3 min so the whole talk stays sub-10. Big videos bloat the `.pptx`;
> 1080p H.264 is plenty.

## Regenerate the deck

```powershell
cd "XPD-Demo"
python build_deck.py
```

Rewrites `XPD-Developer-Demo.pptx` in place. Requires `python-pptx` (and Pillow for the diagram):

```powershell
pip install python-pptx pillow
```

The architecture slide embeds [`../Documentation/xPlayTestDiagram.png`](../Documentation/xPlayTestDiagram.png).

## Editing tips

- **Content:** edit the `SLIDES` data in `build_deck.py` (kicker, title, bullets, `notes`), then re-run.
  Keep `outline.md` in sync.
- **Slide kinds:** `title`, `content`, `flow` (native step diagram), `diagram` (image/appendix), `demo`, `closing`.
- **Style** is centralized in `THEME` at the top of `build_deck.py`.

## Visual style

- 16:9 (13.333in × 7.5in), **black** background with a thin left **spine rail** (bright-green accent on top).
- **Pill kickers** (rounded, bright-green with dark text) label every slide's section.
- Accents: Xbox green `#107C10` and bright green `#52B043`; titles white **Segoe UI Semibold**, body light gray `#BFBFBF` (Segoe UI).
- **Progress dots** mark the current slide; a subtle footer band + hairline ground the page number and footer label.
- A large, low-contrast **▶ watermark** (title + closing) reads as a "stream/play" motif.
- Delivered checklist uses green **✓**; secondary points use **▪** bullets.
- All styling is centralized in `THEME` + the furniture helpers (`pill`, `left_rail`, `watermark`, `progress_dots`, `chrome`, `header`) at the top of `build_deck.py`.
