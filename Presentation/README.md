# Final Intern Presentation

My end-of-internship shareout for **Instantly Shareable Playtest** (xPlaytest × xCloud streaming),
Xbox / **Juno**, Summer 2026.

It is styled after the original **Xbox Playtest** intro deck
([`../Context/PlaytestIntroDeck.pdf`](../Context/PlaytestIntroDeck.pdf)) but retargeted to *my* work,
and it follows the **"asked → built → delivered"** structure of the intern project doc
([`../Context/InternProjectDocument.pdf`](../Context/InternProjectDocument.pdf)).

## Contents

| File | What it is |
|------|------------|
| `Final-Intern-Presentation.pptx` | The generated slide deck (12 slides, 16:9), with speaker notes in the notes pane. |
| `outline.md` | Slide-by-slide narrative **+ speaker notes** — the content source of truth. |
| `build_deck.py` | The `python-pptx` generator that produces the `.pptx` from the outline content. |
| `README.md` | This file. |

## Regenerate the deck

```powershell
cd "Presentation"
python build_deck.py
```

This rewrites `Final-Intern-Presentation.pptx` in place. Requires `python-pptx`:

```powershell
pip install python-pptx
```

The script embeds the architecture diagram from
[`../Documentation/xPlayTestDiagram.png`](../Documentation/xPlayTestDiagram.png).

## Editing tips

- **Content:** edit the `SLIDES` data in `build_deck.py` (title, bullets, and `notes`), then re-run.
  Keep `outline.md` in sync so the two stay aligned.
- **Speaker notes** live both in the `.pptx` notes pane and in `outline.md`.
- **Style** is centralized at the top of `build_deck.py` (`THEME`): edit colors/fonts there.

## Source materials

- **Framing / goals / P0 metrics / skills / contacts:** `../Context/InternProjectDocument.pdf`
- **Style + narrative reference:** `../Context/PlaytestIntroDeck.pdf`
- **What I built:** `../Internship-Summary.md`, `../Explanations/`, `../PC-Polling-Status.md`
- **Diagram:** `../Documentation/xPlayTestDiagram.png`

## Visual style (mirrored from the intro deck)

- 16:9 (13.333in × 7.5in), **black** background.
- Accents: Xbox green `#107C10` and bright green `#52B043`.
- Titles: white **Segoe UI Semibold**; body: light gray `#BFBFBF` (Segoe UI).
- Small gray footer motif on every slide.
