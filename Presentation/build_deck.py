"""
Generate the final intern presentation for Instantly Shareable Playtest.

Styled after ../Context/PlaytestIntroDeck.pdf (dark theme, Xbox-green accents),
structured around ../Context/InternProjectDocument.pdf (asked -> built -> delivered).

Usage:
    python build_deck.py

Requires: python-pptx  (pip install python-pptx)
Content source of truth: outline.md  (keep the two in sync).
"""

import os
import tempfile
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
DIAGRAM = os.path.join(REPO, "Documentation", "xPlayTestDiagram.png")
OUT = os.path.join(BASE, "Final-Intern-Presentation.pptx")

# --------------------------------------------------------------------------- #
# Theme (derived from the intro deck)
# --------------------------------------------------------------------------- #
THEME = {
    "bg":     RGBColor(0x00, 0x00, 0x00),   # black
    "white":  RGBColor(0xFF, 0xFF, 0xFF),
    "body":   RGBColor(0xBF, 0xBF, 0xBF),   # light gray
    "dim":    RGBColor(0x80, 0x80, 0x80),   # footer gray
    "green":  RGBColor(0x10, 0x7C, 0x10),   # Xbox green (bars/rules)
    "bright": RGBColor(0x52, 0xB0, 0x43),   # bright green (highlights)
}
TITLE_FONT = "Segoe UI Semibold"
BODY_FONT = "Segoe UI"

SLIDE_W = 13.333
SLIDE_H = 7.5
MARGIN = 0.9
BODY_W = SLIDE_W - 2 * MARGIN

FOOTER = "Instantly Shareable Playtest  \u00b7  Melanie Chen  \u00b7  Xbox / Juno"


# --------------------------------------------------------------------------- #
# Low-level helpers
# --------------------------------------------------------------------------- #
def set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def box(slide, l, t, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Pt(0)
    tf.margin_right = Pt(0)
    tf.margin_top = Pt(0)
    tf.margin_bottom = Pt(0)
    return tf


def bar(slide, l, t, w, h, color):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


class Frame:
    """Thin wrapper so the first (auto-created) paragraph is reused."""

    def __init__(self, tf):
        self.tf = tf
        self.first = True

    def para(self, level=0, space_after=8, space_before=0, line_spacing=1.06, align=None):
        p = self.tf.paragraphs[0] if self.first else self.tf.add_paragraph()
        self.first = False
        p.level = level
        if space_after is not None:
            p.space_after = Pt(space_after)
        if space_before is not None:
            p.space_before = Pt(space_before)
        if line_spacing is not None:
            p.line_spacing = line_spacing
        if align is not None:
            p.alignment = align
        return p


def emit(p, text, size, color, font=BODY_FONT, bold=False, italic=False, emph_color=None):
    """Add runs to paragraph p. Text wrapped in **...** is bolded/highlighted."""
    emph_color = emph_color or THEME["white"]
    for i, seg in enumerate(text.split("**")):
        if seg == "":
            continue
        r = p.add_run()
        r.text = seg
        f = r.font
        f.size = Pt(size)
        f.name = font
        strong = (i % 2 == 1)
        f.bold = bold or strong
        f.italic = italic
        f.color.rgb = emph_color if strong else color


def run(p, text, size, color, font=BODY_FONT, bold=False):
    r = p.add_run()
    r.text = text
    f = r.font
    f.size = Pt(size)
    f.name = font
    f.bold = bold
    f.color.rgb = color


# --------------------------------------------------------------------------- #
# Slide furniture
# --------------------------------------------------------------------------- #
def footer(slide, page):
    tf = box(slide, MARGIN, 7.04, 9.0, 0.35)
    p = Frame(tf).para(space_after=0, line_spacing=1.0)
    run(p, FOOTER, 9.5, THEME["dim"])
    tf2 = box(slide, SLIDE_W - MARGIN - 1.2, 7.04, 1.2, 0.35)
    p2 = Frame(tf2).para(space_after=0, line_spacing=1.0, align=PP_ALIGN.RIGHT)
    run(p2, str(page), 9.5, THEME["dim"])


def header(slide, kicker, title):
    if kicker:
        tf = box(slide, MARGIN, 0.55, BODY_W, 0.4)
        emit(Frame(tf).para(space_after=0, line_spacing=1.0), kicker.upper(), 14,
             THEME["bright"], font=BODY_FONT, bold=True)
    tf = box(slide, MARGIN, 0.92, BODY_W, 1.0)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0), title, 34,
         THEME["white"], font=TITLE_FONT, bold=True)
    bar(slide, MARGIN, 1.74, 2.1, 0.07, THEME["green"])


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def prepared_diagram():
    """Return a path to an embed-ready diagram: downscaled (to temp) if huge, else the original.

    The very high-res source (~13591x8719) bloats the file and trips Pillow's decompression-bomb
    guard, so we cache a max-3600px-wide copy in the temp dir (never written into the repo).
    """
    if not os.path.exists(DIAGRAM):
        return None
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        cached = os.path.join(tempfile.gettempdir(), "xplaytest_diagram_scaled.png")
        if os.path.exists(cached) and os.path.getmtime(cached) >= os.path.getmtime(DIAGRAM):
            return cached
        im = Image.open(DIAGRAM)
        max_w = 3600
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        im.save(cached, "PNG", optimize=True)
        return cached
    except Exception as exc:  # noqa: BLE001 - fall back to the original on any imaging error
        print(f"(diagram downscale skipped: {exc})")
        return DIAGRAM


# --------------------------------------------------------------------------- #
# Slide renderers
# --------------------------------------------------------------------------- #
def render_title(slide, d):
    bar(slide, MARGIN, 0.72, 2.4, 0.09, THEME["green"])
    tf = box(slide, MARGIN, 0.98, BODY_W, 0.4)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0), d["kicker"].upper(), 14,
         THEME["bright"], font=BODY_FONT, bold=True)

    tf = box(slide, MARGIN, 2.55, BODY_W, 1.4)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0), d["title"], 52,
         THEME["white"], font=TITLE_FONT, bold=True)

    tf = box(slide, MARGIN, 3.75, BODY_W - 1.0, 1.1)
    emit(Frame(tf).para(space_after=0, line_spacing=1.1), d["subtitle"], 22, THEME["body"])

    tf = box(slide, MARGIN, 5.5, BODY_W, 1.2)
    fr = Frame(tf)
    emit(fr.para(space_after=4, line_spacing=1.0), d["presenter"], 22,
         THEME["white"], font=TITLE_FONT, bold=True)
    emit(fr.para(space_after=0, line_spacing=1.0), d["affil"], 16, THEME["body"])
    notes(slide, d["notes"])


def render_content(slide, d):
    header(slide, d.get("kicker"), d["title"])
    top = d.get("body_top", 2.15)
    tf = box(slide, MARGIN, top, BODY_W, 6.7 - top)
    fr = Frame(tf)

    if d.get("lead"):
        emit(fr.para(space_after=14, line_spacing=1.1), d["lead"], 21,
             THEME["white"], emph_color=THEME["bright"])

    for text in d.get("checks", []):
        p = fr.para(space_after=11, line_spacing=1.05)
        run(p, "\u2713  ", 20, THEME["bright"], bold=True)
        emit(p, text, 20, THEME["white"], emph_color=THEME["bright"])

    for item in d.get("bullets", []):
        if isinstance(item, tuple):
            level, text = item
        else:
            level, text = 0, item
        p = fr.para(level=level, space_after=(10 if level == 0 else 6), line_spacing=1.05)
        if level == 0:
            run(p, "\u25aa  ", 20, THEME["bright"], bold=True)
            emit(p, text, 20, THEME["body"], emph_color=THEME["white"])
        else:
            run(p, "     \u2013  ", 17, THEME["dim"])
            emit(p, text, 17, THEME["body"], emph_color=THEME["white"])

    footer(slide, d["page"])
    notes(slide, d["notes"])


def render_diagram(slide, d):
    header(slide, d.get("kicker"), d["title"])
    img_top, img_bottom = 2.05, 6.35
    avail_h = img_bottom - img_top
    diagram_path = prepared_diagram()
    if diagram_path:
        pic = slide.shapes.add_picture(diagram_path, Inches(0), Inches(img_top), height=Inches(avail_h))
        pic.left = Inches((SLIDE_W - pic.width.inches) / 2)
        pic.line.color.rgb = THEME["green"]
        pic.line.width = Pt(1.25)
    else:
        ph = bar(slide, MARGIN, img_top, BODY_W, avail_h, RGBColor(0x1A, 0x1A, 0x1A))
        ph.line.color.rgb = THEME["green"]
        emit(Frame(ph.text_frame).para(align=PP_ALIGN.CENTER), "[ xPlayTestDiagram.png ]",
             18, THEME["dim"])

    tf = box(slide, MARGIN, 6.42, BODY_W, 0.5)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0, align=PP_ALIGN.CENTER),
         d["caption"], 14, THEME["body"], emph_color=THEME["bright"])
    footer(slide, d["page"])
    notes(slide, d["notes"])


def render_closing(slide, d):
    bar(slide, MARGIN, 1.35, 2.4, 0.09, THEME["green"])
    tf = box(slide, MARGIN, 1.6, BODY_W, 1.2)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0), d["title"], 48,
         THEME["white"], font=TITLE_FONT, bold=True)

    tf = box(slide, MARGIN, 3.15, BODY_W, 2.4)
    fr = Frame(tf)
    for line in d["lines"]:
        emit(fr.para(space_after=10, line_spacing=1.1), line, 19, THEME["body"],
             emph_color=THEME["white"])

    tf = box(slide, MARGIN, 5.95, BODY_W, 0.8)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0), d["closer"], 30,
         THEME["bright"], font=TITLE_FONT, bold=True)
    footer(slide, d["page"])
    notes(slide, d["notes"])


RENDERERS = {
    "title": render_title,
    "content": render_content,
    "diagram": render_diagram,
    "closing": render_closing,
}

# --------------------------------------------------------------------------- #
# Content (kept in sync with outline.md)
# --------------------------------------------------------------------------- #
SLIDES = [
    {
        "kind": "title",
        "kicker": "Final shareout  \u00b7  Summer 2026",
        "title": "Instantly Shareable Playtest",
        "subtitle": "Streaming pre-release builds from the cloud \u2014 in seconds, no install.",
        "presenter": "Melanie Chen \u2014 Software Engineering Intern",
        "affil": "Xbox / Juno  \u00b7  Summer 2026",
        "notes": (
            "Hi, I'm Melanie \u2014 a software engineering intern on the Xbox Juno team. This summer I "
            "worked on Instantly Shareable Playtest: letting a game creator share an unreleased build that a "
            "tester can stream from the cloud in seconds, with no download and no install. Here's what it is, "
            "what I built, and what shipped."
        ),
    },
    {
        "kind": "content",
        "kicker": "About me",
        "title": "About me",
        "bullets": [
            "[University \u00b7 Degree \u00b7 Expected year]",
            "Team **Juno** (Xbox) \u2014 reducing friction for game creators",
            "Manager **Brian Bowman**  \u00b7  Mentor **Emma Park**",
            "My summer: backend across **~8 services**, **two orgs**",
            "[One line \u2014 an interest or something fun about you]",
        ],
        "notes": (
            "A quick bit about me. [Fill in your school and background.] I joined Juno, whose whole mission is "
            "to lower the barrier for game creators. My project lived almost entirely in the backend, threading "
            "a build across about eight services \u2014 which meant ramping up fast. Big thanks to my manager "
            "Brian and my mentor Emma for the support."
        ),
    },
    {
        "kind": "content",
        "kicker": "The problem",
        "title": "Testing shouldn't mean shipping the whole game",
        "lead": "xPlaytest already shares **RETAIL-signed private builds** \u2014 no cert, no store page.",
        "bullets": [
            "Games are **hundreds of GB** \u2014 every tester waits on a slow install",
            "Creators must **provision many hardware profiles** for compatibility",
            "Physical devices **risk leaking** locally-inspectable game code",
        ],
        "notes": (
            "Where did this start? The xPlaytest team had already made testing easier \u2014 a creator can share "
            "a retail-signed private build without certification or a store page. But three barriers remained. "
            "Modern games are hundreds of gigabytes, so every tester sits through a huge download. Creators have "
            "to buy and set up lots of hardware to test compatibility. And physical devices are a security risk "
            "\u2014 a lost devkit means the unreleased code is right there to inspect. We wanted to remove all three."
        ),
    },
    {
        "kind": "content",
        "kicker": "The vision",
        "title": "Instantly Shareable Playtest",
        "lead": "**xPlaytest \u00d7 Xbox Cloud Gaming**",
        "bullets": [
            "The creator flips on **\u201callow cloud streaming\u201d** and shares a link",
            "An invited tester **streams the private RETAIL build in seconds**",
            "**No install. No download. No devkit.**",
        ],
        "notes": (
            "The idea is to combine xPlaytest with Xbox Cloud Gaming. The creator just opts in to cloud streaming "
            "and shares a link. An invited tester clicks it and \u2014 instead of downloading anything \u2014 "
            "streams the build straight from the cloud, in seconds. It's still a real retail build; it just runs "
            "in xCloud instead of on the tester's own hardware. That's the north star."
        ),
    },
    {
        "kind": "content",
        "kicker": "The goal",
        "title": "What I was asked to build \u2014 connect two clouds",
        "lead": "To make that link work, the backend had to\u2026",
        "bullets": [
            "Stand up a new **service-to-service** link: publishing \u2194 Game Streaming",
            "Create a **private streaming offering** per playtest",
            "Scope access to **only invited testers** (DNA groups)",
            "**Ingest each new build** and point the offering at it",
            "Return a **shareable link** that streams",
        ],
        "notes": (
            "Under the hood, that link needs a lot to happen. My goals \u2014 the P0s from the project doc \u2014 "
            "were: create a brand-new service-to-service connection between publishing and Xbox Game Streaming "
            "Services; on publish, spin up a private streaming offering just for that playtest; make sure only "
            "invited testers can see it; ingest every new build and point the offering at it; and hand back a link "
            "that actually streams. That's the checklist I was measured against."
        ),
    },
    {
        "kind": "diagram",
        "kicker": "How it works",
        "title": "The backend spine",
        "caption": ("audience \u2192 offering \u2192 payload \u2192 **cross-tenant send (Green\u2192Corp)** "
                    "\u2192 ingest \u2192 readiness poll \u2192 share link"),
        "notes": (
            "Here's the whole flow on one slide. Reading left to right: we resolve who's allowed in (the audience), "
            "publish an offering, assemble a payload of everything xCloud needs, send it across an organizational "
            "boundary \u2014 from the MSFT Green cloud to Corp \u2014 through a gateway called SAGE, ingest the build "
            "while binding its title and offering together, poll until the servers are ready to stream, and then the "
            "share link works. I touched every hop; the next slides zoom into the two I'm proudest of."
        ),
    },
    {
        "kind": "content",
        "kicker": "My contribution",
        "title": "The payload builder",
        "lead": "**PR 15834601** \u2014 assembling everything xCloud needs to stream a build",
        "bullets": [
            "Builds the payload from the publish snapshot: **StoreAsset**, **allowed DNA groups**, "
            "sandbox, bounded expiration",
            "Mints a **cross-tenant token** and fires the streaming ingest",
            "**Opt-in** (pilot seller) and **non-blocking** \u2014 never breaks the normal download publish",
        ],
        "notes": (
            "My headline piece is the payload builder. When a creator publishes, I take a snapshot of that publish "
            "and assemble everything Game Streaming Services needs: the store asset details, the allowed audience "
            "groups, the sandbox, and a bounded expiration. Then it mints a cross-tenant token and fires the "
            "ingestion. Two design choices I care about: it's opt-in, gated to a pilot seller so we could roll it "
            "out safely; and it's non-blocking \u2014 if streaming ever fails, the normal download publish still "
            "succeeds. We never degrade the existing product to add the new one."
        ),
    },
    {
        "kind": "content",
        "kicker": "The hard problem",
        "title": "Making two clouds trust each other",
        "lead": "The send crosses an org boundary: **MSFT Green \u2192 Corp**",
        "bullets": [
            "Green mints a **v1.0 token** whose audience is a **bare app-id GUID**",
            "The receiver rejected it \u2014 \u201caudience (null) is invalid\u201d",
            "I traced it end-to-end and made ingestion **accept the bare-GUID audience** "
            "\u2014 auth **and** authz passed",
        ],
        "notes": (
            "The hardest problem was authentication across that org boundary. The caller lives in the MSFT Green "
            "tenant and the receiver lives in Corp \u2014 two separate trust domains. The Green side mints an "
            "older-style token whose audience claim is just a bare GUID, and the receiver kept rejecting it with "
            "'audience null is invalid.' I traced the token through both services to find that mismatch, then fixed "
            "the receiver to accept the bare-GUID audience. When that clicked, the request finally authenticated and "
            "authorized end to end. It's the kind of bug that's invisible until you understand both sides."
        ),
    },
    {
        "kind": "content",
        "kicker": "Impact",
        "title": "What shipped",
        "lead": "Against the P0 goals:",
        "checks": [
            "Private offering created per playtest",
            "Audience scoped to invited DNA groups",
            "New build ingested into streaming on publish",
            "Seller flighting to limit blast radius",
            "Shareable-stream backend",
        ],
        "bullets": [
            "**~22 merged PRs** across **~8 services**, two orgs",
            "Backend spine in **main** and **deployed to prod** \u2014 a pilot-seller publish fires the "
            "full Green\u2192SAGE\u2192ingest call",
            "Next: the two **front ends**",
        ],
        "body_top": 1.95,
        "notes": (
            "So what actually shipped? Going down the P0 list: private offering per playtest \u2014 done; audience "
            "scoping \u2014 done; build ingestion on publish \u2014 done; seller flighting to limit blast radius "
            "\u2014 done; and the shareable-stream backend \u2014 done. All told that's about 22 merged pull "
            "requests across roughly eight services and two organizations. The entire backend spine is merged to "
            "main and deployed to production \u2014 today a publish by our pilot seller fires the whole cross-cloud "
            "call for real. What's left is the two front ends."
        ),
    },
    {
        "kind": "content",
        "kicker": "What I learned",
        "title": "What I grew in",
        "bullets": [
            "**Ramping fast with AI** across many unfamiliar repos and services",
            "**Microservice & systems design** in .NET \u2014 resilient, non-blocking",
            "**Cross-team & cross-functional** collaboration (GSSV \u00d7 xPlaytest \u00d7 PM)",
            "**Working through ambiguity** \u2014 reverse-engineering an undocumented flow",
            "**Detail-oriented** problem solving at the trust boundary",
        ],
        "notes": (
            "On the growth side \u2014 these map to the skills my project set out to build. I got much faster at "
            "ramping into unfamiliar codebases, using AI to understand many repos and services quickly. I learned "
            "real microservice and systems design in .NET, especially designing each hop to fail safely. I "
            "collaborated across the Game Streaming, xPlaytest, and PM teams to get decisions made and code "
            "reviewed. And a huge amount of the work was navigating ambiguity \u2014 reverse-engineering a flow "
            "nobody had fully documented \u2014 then handling the edge cases carefully."
        ),
    },
    {
        "kind": "content",
        "kicker": "What's next",
        "title": "What's next",
        "bullets": [
            "**Two front ends:** creator toggle + share link; tester landing that **logs in first & doesn't leak**",
            "**End-to-end validation** once the front ends land",
            "Roadmap: **Library integration, invite tokens, console support**",
        ],
        "notes": (
            "The backend is ready and waiting for two front ends. On the creator side, Partner Center needs a "
            "toggle to enable streaming and surface the share link. On the tester side, the Bayside landing page "
            "needs to log the user in before revealing anything, so a playtest never leaks to people who aren't "
            "invited. Once those land we can run the full end-to-end flow. Beyond that, the roadmap has Library "
            "integration, invite tokens, and console support. I've documented all of it for the next engineer."
        ),
    },
    {
        "kind": "closing",
        "title": "Thank you",
        "lines": [
            "Mentor **Emma Park**  \u00b7  Manager **Brian Bowman**",
            "Feature leads **David Kushmerick** & **Bec Lyons**",
            "Experts **Anthony Keller \u00b7 Timi Bolaji \u00b7 Ashton Summer \u00b7 Chuy Galvan**",
            "The **Juno**, **xPlaytest**, and **GSSV** teams",
        ],
        "closer": "Questions?",
        "notes": (
            "Thank you \u2014 especially to my mentor Emma and my manager Brian, to David and Bec on the feature "
            "side, and to Anthony, Timi, Ashton, and Chuy, who answered endless questions about services I'd never "
            "seen before. And thanks to the whole Juno, xPlaytest, and Game Streaming teams. I'd love to take any "
            "questions."
        ),
    },
]


def build():
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    blank = prs.slide_layouts[6]

    for i, d in enumerate(SLIDES, start=1):
        d["page"] = i
        slide = prs.slides.add_slide(blank)
        set_bg(slide, THEME["bg"])
        RENDERERS[d["kind"]](slide, d)

    prs.save(OUT)
    size_kb = os.path.getsize(OUT) / 1024
    print(f"Wrote {OUT}")
    print(f"Slides: {len(prs.slides._sldIdLst)}  |  Size: {size_kb:.0f} KB")
    if not os.path.exists(DIAGRAM):
        print(f"WARNING: diagram not found at {DIAGRAM} (placeholder used).")


if __name__ == "__main__":
    build()
