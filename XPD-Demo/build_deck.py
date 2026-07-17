"""
Generate the XPD / XBOX Developer Demos deck for Instantly Shareable Playtest.

A sub-10-minute talk for an internal Xbox-developer audience, following the same
"asked -> built -> delivered" arc as my end-of-internship demo, with a recorded
end-to-end demo (publish -> stream) as the payoff.

Styled after ../Presentation (dark theme, Xbox-green accents). Reuses the same
python-pptx helpers, and adds a `demo` slide that auto-embeds a recording dropped
into ./Demo/ (a styled placeholder is shown until one exists).

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
DEMO_DIR = os.path.join(BASE, "Demo")
OUT = os.path.join(BASE, "XPD-Developer-Demo.pptx")

VIDEO_EXTS = (".mp4", ".m4v", ".mov", ".webm", ".avi")
VIDEO_MIME = {
    ".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime",
    ".webm": "video/webm", ".avi": "video/x-msvideo",
}

# --------------------------------------------------------------------------- #
# Theme (mirrored from ../Presentation/build_deck.py)
# --------------------------------------------------------------------------- #
THEME = {
    "bg":     RGBColor(0x00, 0x00, 0x00),   # black
    "white":  RGBColor(0xFF, 0xFF, 0xFF),
    "body":   RGBColor(0xBF, 0xBF, 0xBF),   # light gray
    "dim":    RGBColor(0x80, 0x80, 0x80),   # footer gray
    "green":  RGBColor(0x10, 0x7C, 0x10),   # Xbox green (bars/rules)
    "bright": RGBColor(0x52, 0xB0, 0x43),   # bright green (highlights)
    "panel":  RGBColor(0x14, 0x14, 0x14),   # demo placeholder panel
    "ink":    RGBColor(0x06, 0x12, 0x0A),   # near-black text on the green pill
    "dot":    RGBColor(0x3A, 0x3A, 0x3A),   # inactive progress dot
    "band":   RGBColor(0x0D, 0x0D, 0x0D),   # footer grounding band
    "hair":   RGBColor(0x2A, 0x2A, 0x2A),   # hairline rule
    "rail":   RGBColor(0x18, 0x18, 0x18),   # left spine (dim base)
    "wm":     RGBColor(0x12, 0x12, 0x12),   # watermark glyph
}
TITLE_FONT = "Segoe UI Semibold"
BODY_FONT = "Segoe UI"

SLIDE_W = 13.333
SLIDE_H = 7.5
MARGIN = 0.9
BODY_W = SLIDE_W - 2 * MARGIN

FOOTER = "Instantly Shareable Playtest  \u00b7  XBOX Developer Demos  \u00b7  Melanie Chen"


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
def pill(slide, l, t, text, h=0.36):
    """Rounded 'pill' kicker: bright-green fill, dark text, fully rounded ends."""
    from pptx.enum.shapes import MSO_SHAPE
    w = min(6.8, 0.132 * len(text) + 0.55)
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = THEME["bright"]
    sh.line.fill.background()
    sh.shadow.inherit = False
    try:
        sh.adjustments[0] = 0.5
    except Exception:  # noqa: BLE001 - some shapes lack the adjustment handle
        pass
    tf = sh.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Pt(4)
    tf.margin_right = Pt(4)
    tf.margin_top = Pt(0)
    tf.margin_bottom = Pt(0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text.upper()
    f = r.font
    f.size = Pt(12.5)
    f.name = BODY_FONT
    f.bold = True
    f.color.rgb = THEME["ink"]
    return sh


def left_rail(slide):
    """A thin full-height spine with a bright accent segment up top."""
    bar(slide, 0.0, 0.0, 0.09, SLIDE_H, THEME["rail"])
    bar(slide, 0.0, 0.0, 0.09, 2.0, THEME["bright"])


def watermark(slide):
    """A large, barely-there play glyph in the corner, behind content."""
    tf = box(slide, SLIDE_W - 6.2, SLIDE_H - 5.4, 6.0, 5.0)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0, align=PP_ALIGN.RIGHT),
         "\u25b6", 300, THEME["wm"], font=TITLE_FONT, bold=True)


def progress_dots(slide, page, total):
    """A centered row of dots marking position in the deck."""
    from pptx.enum.shapes import MSO_SHAPE
    dia, gap = 0.075, 0.17
    x0 = (SLIDE_W - (total - 1) * gap) / 2.0
    y = 7.18
    for i in range(total):
        color = THEME["bright"] if (i + 1) == page else THEME["dot"]
        o = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                   Inches(x0 + i * gap - dia / 2), Inches(y), Inches(dia), Inches(dia))
        o.fill.solid()
        o.fill.fore_color.rgb = color
        o.line.fill.background()
        o.shadow.inherit = False


def chrome(slide, d, label=True):
    """Consistent slide chrome: spine, footer band + hairline, footer label, page no., progress dots."""
    left_rail(slide)
    bar(slide, 0.0, 6.98, SLIDE_W, SLIDE_H - 6.98, THEME["band"])
    bar(slide, MARGIN, 6.965, SLIDE_W - 2 * MARGIN, 0.012, THEME["hair"])
    if label:
        tf = box(slide, MARGIN, 7.05, 9.6, 0.32)
        run(Frame(tf).para(space_after=0, line_spacing=1.0), FOOTER, 9.5, THEME["dim"])
        tf2 = box(slide, SLIDE_W - MARGIN - 1.2, 7.05, 1.2, 0.32)
        run(Frame(tf2).para(space_after=0, line_spacing=1.0, align=PP_ALIGN.RIGHT),
            str(d["page"]), 9.5, THEME["dim"])
    if d.get("appendix"):
        tf = box(slide, (SLIDE_W - 2.0) / 2, 7.12, 2.0, 0.26)
        run(Frame(tf).para(space_after=0, line_spacing=1.0, align=PP_ALIGN.CENTER),
            "APPENDIX", 9.5, THEME["dim"])
    else:
        progress_dots(slide, d["page"], d["total"])


def header(slide, kicker, title):
    if kicker:
        pill(slide, MARGIN, 0.62, kicker)
    tf = box(slide, MARGIN, 1.08, BODY_W, 1.0)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0), title, 34,
         THEME["white"], font=TITLE_FONT, bold=True)
    bar(slide, MARGIN, 1.88, 1.5, 0.055, THEME["bright"])


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def prepared_diagram():
    """Return an embed-ready diagram: downscaled (to temp) if huge, else the original.

    The very high-res source bloats the file and trips Pillow's decompression-bomb guard,
    so we cache a max-3600px-wide copy in temp (never written into the repo).
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


def find_demo_video():
    """First recording found in ./Demo/, or None."""
    if not os.path.isdir(DEMO_DIR):
        return None
    vids = sorted(f for f in os.listdir(DEMO_DIR) if f.lower().endswith(VIDEO_EXTS))
    return os.path.join(DEMO_DIR, vids[0]) if vids else None


# --------------------------------------------------------------------------- #
# Slide renderers
# --------------------------------------------------------------------------- #
def render_title(slide, d):
    watermark(slide)
    left_rail(slide)
    pill(slide, MARGIN, 1.2, d["kicker"])

    tf = box(slide, MARGIN, 2.5, BODY_W, 1.3)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0), d["title"], 52,
         THEME["white"], font=TITLE_FONT, bold=True)

    bar(slide, MARGIN, 3.72, 1.8, 0.08, THEME["bright"])

    tf = box(slide, MARGIN, 3.98, 8.7, 1.4)
    emit(Frame(tf).para(space_after=0, line_spacing=1.12), d["subtitle"], 22, THEME["body"])

    tf = box(slide, MARGIN, 5.6, BODY_W, 1.2)
    fr = Frame(tf)
    emit(fr.para(space_after=4, line_spacing=1.0), d["presenter"], 22,
         THEME["white"], font=TITLE_FONT, bold=True)
    emit(fr.para(space_after=0, line_spacing=1.0), d["affil"], 16, THEME["body"])
    progress_dots(slide, d["page"], d["total"])
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

    chrome(slide, d)
    notes(slide, d["notes"])


def render_diagram(slide, d):
    header(slide, d.get("kicker"), d["title"])
    img_top, img_bottom = 2.05, 6.35
    avail_h = img_bottom - img_top
    diagram_path = prepared_diagram()
    if diagram_path:
        pic = slide.shapes.add_picture(diagram_path, Inches(0), Inches(img_top), height=Inches(avail_h))
        pic.left = Inches((SLIDE_W - pic.width.inches) / 2)
        pic.line.color.rgb = THEME["bright"]
        pic.line.width = Pt(1.5)
    else:
        ph = bar(slide, MARGIN, img_top, BODY_W, avail_h, THEME["panel"])
        ph.line.color.rgb = THEME["green"]
        emit(Frame(ph.text_frame).para(align=PP_ALIGN.CENTER), "[ xPlayTestDiagram.png ]",
             18, THEME["dim"])

    tf = box(slide, MARGIN, 6.42, BODY_W, 0.5)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0, align=PP_ALIGN.CENTER),
         d["caption"], 14, THEME["body"], emph_color=THEME["bright"])
    chrome(slide, d)
    notes(slide, d["notes"])


def render_demo(slide, d):
    header(slide, d.get("kicker"), d["title"])
    top, bottom = 2.05, 6.35
    h = bottom - top
    w = h * 16 / 9
    left = (SLIDE_W - w) / 2

    video = find_demo_video()
    if video:
        ext = os.path.splitext(video)[1].lower()
        mv = slide.shapes.add_movie(
            video, Inches(left), Inches(top), Inches(w), Inches(h),
            mime_type=VIDEO_MIME.get(ext, "video/unknown"))
        mv.line.color.rgb = THEME["green"]
        mv.line.width = Pt(1.5)
        print(f"Embedded demo video: {os.path.basename(video)}")
    else:
        panel = bar(slide, left, top, w, h, THEME["panel"])
        panel.line.color.rgb = THEME["green"]
        panel.line.width = Pt(1.5)
        tf = box(slide, left, top, w, h, anchor=MSO_ANCHOR.MIDDLE)
        fr = Frame(tf)
        emit(fr.para(space_after=6, line_spacing=1.0, align=PP_ALIGN.CENTER),
             "\u25b6", 54, THEME["bright"], font=TITLE_FONT, bold=True)
        emit(fr.para(space_after=4, line_spacing=1.0, align=PP_ALIGN.CENTER),
             "Recorded end-to-end demo", 24, THEME["white"], font=TITLE_FONT, bold=True)
        emit(fr.para(space_after=0, line_spacing=1.0, align=PP_ALIGN.CENTER),
             "Drop your recording in  XPD-Demo\\Demo\\  and re-run build_deck.py to embed it.",
             13, THEME["dim"])
        print("No demo video found in ./Demo/ - placeholder used.")

    tf = box(slide, MARGIN, 6.42, BODY_W, 0.5)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0, align=PP_ALIGN.CENTER),
         d["caption"], 14, THEME["body"], emph_color=THEME["bright"])
    chrome(slide, d)
    notes(slide, d["notes"])


def blockarrow(slide, l, t, w, h, direction="right", color=None):
    from pptx.enum.shapes import MSO_SHAPE
    m = {"right": MSO_SHAPE.RIGHT_ARROW, "left": MSO_SHAPE.LEFT_ARROW,
         "down": MSO_SHAPE.DOWN_ARROW, "up": MSO_SHAPE.UP_ARROW}
    sh = slide.shapes.add_shape(m[direction], Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color or THEME["bright"]
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def flow_node(slide, l, t, w, h, step, badge=True, border=None, lw=1.25, tsize=16, ssize=11):
    from pptx.enum.shapes import MSO_SHAPE
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    card.fill.solid()
    card.fill.fore_color.rgb = THEME["panel"]
    card.line.color.rgb = border or THEME["bright"]
    card.line.width = Pt(lw)
    card.shadow.inherit = False
    try:
        card.adjustments[0] = 0.08
    except Exception:  # noqa: BLE001 - shape lacks the corner handle
        pass
    if badge:
        dia = 0.36
        badge_sh = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(l + w / 2 - dia / 2), Inches(t - dia / 2),
                                           Inches(dia), Inches(dia))
        badge_sh.fill.solid()
        badge_sh.fill.fore_color.rgb = THEME["bright"]
        badge_sh.line.color.rgb = THEME["bg"]
        badge_sh.line.width = Pt(1.5)
        badge_sh.shadow.inherit = False
        btf = badge_sh.text_frame
        for side in ("left", "right", "top", "bottom"):
            setattr(btf, f"margin_{side}", Pt(0))
        btf.vertical_anchor = MSO_ANCHOR.MIDDLE
        bp = btf.paragraphs[0]
        bp.alignment = PP_ALIGN.CENTER
        br = bp.add_run()
        br.text = step["n"]
        br.font.size = Pt(13)
        br.font.bold = True
        br.font.name = TITLE_FONT
        br.font.color.rgb = THEME["ink"]
        tf = box(slide, l + 0.08, t + 0.46, w - 0.16, h - 0.54)
    else:
        tf = box(slide, l + 0.1, t + 0.12, w - 0.2, h - 0.24, anchor=MSO_ANCHOR.MIDDLE)
    fr = Frame(tf)
    emit(fr.para(space_after=3, line_spacing=1.0, align=PP_ALIGN.CENTER),
         step["t"], tsize, THEME["white"], font=TITLE_FONT, bold=True)
    emit(fr.para(space_after=0, line_spacing=1.05, align=PP_ALIGN.CENTER),
         step["s"], ssize, THEME["body"])


def group_box(slide, l, t, w, h, label):
    from pptx.enum.shapes import MSO_SHAPE
    gb = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    gb.fill.background()
    gb.line.color.rgb = THEME["hair"]
    gb.line.width = Pt(1.0)
    gb.shadow.inherit = False
    try:
        gb.adjustments[0] = 0.045
    except Exception:  # noqa: BLE001 - shape lacks the corner handle
        pass
    tf = box(slide, l + 0.06, t - 0.34, w, 0.3)
    emit(Frame(tf).para(space_after=0, line_spacing=1.0), label.upper(), 11.5,
         THEME["bright"], font=BODY_FONT, bold=True)


def render_flow_grouped(slide, d):
    groups = d["groups"]
    w, gi, pad, bridge = 1.36, 0.16, 0.14, 0.65
    gy, gh, cy, ch = 3.05, 1.85, 3.30, 1.40
    mid_y = cy + ch / 2

    boxes, all_cards, x = [], [], MARGIN
    for g in groups:
        m = len(g["steps"])
        box_w = m * w + (m - 1) * gi + 2 * pad
        cx0 = x + pad
        cards = [(cx0 + j * (w + gi), s) for j, s in enumerate(g["steps"])]
        boxes.append((x, box_w, g["label"], cards))
        all_cards.extend(cards)
        x += box_w + bridge

    for bx, bw, label, _ in boxes:
        group_box(slide, bx, gy, bw, gh, label)

    for _, _, _, cards in boxes:
        for k in range(len(cards) - 1):
            axc = (cards[k][0] + w + cards[k + 1][0]) / 2
            blockarrow(slide, axc - 0.09, mid_y - 0.08, 0.18, 0.16, "right", THEME["green"])

    for i in range(len(boxes) - 1):
        bx, bw = boxes[i][0], boxes[i][1]
        gap_c = (bx + bw + boxes[i + 1][0]) / 2
        blockarrow(slide, gap_c - 0.11, mid_y - 0.10, 0.22, 0.20, "right", THEME["green"])
        if d.get("bridge"):
            tf = box(slide, gap_c - 0.6, 3.44, 1.2, 0.3)
            emit(Frame(tf).para(space_after=0, line_spacing=1.0, align=PP_ALIGN.CENTER),
                 d["bridge"], 12, THEME["bright"], font=TITLE_FONT, bold=True)

    for cxl, step in all_cards:
        flow_node(slide, cxl, cy, w, ch, step, badge=False, border=THEME["dot"], lw=1.0,
                  tsize=12.5, ssize=9)

    if d.get("caption"):
        tf = box(slide, MARGIN, cy + ch + 0.5, BODY_W, 0.5)
        emit(Frame(tf).para(space_after=0, line_spacing=1.1, align=PP_ALIGN.CENTER),
             d["caption"], 15, THEME["body"], emph_color=THEME["bright"])

    chrome(slide, d)
    notes(slide, d["notes"])


def render_flow(slide, d):
    header(slide, d.get("kicker"), d["title"])
    if d.get("groups"):
        render_flow_grouped(slide, d)
        return
    steps = d["steps"]
    n = len(steps)
    ba = d.get("boundary_after", 0)
    calm = d.get("calm", False)
    badges = d.get("badges", not calm)
    arrow_col = THEME["green"] if calm else THEME["bright"]
    border_col = THEME["dot"] if calm else THEME["bright"]
    lw = 1.0 if calm else 1.25

    nw, nh, top = 1.72, 1.82, 3.0
    usable = SLIDE_W - 2 * MARGIN

    if ba:
        small_gap, bnd_gap = 0.20, 0.54
        xs, x = [], MARGIN
        for i in range(n):
            xs.append(x)
            x += nw + (bnd_gap if (i + 1) == ba else small_gap)
        left_cx = (xs[0] + xs[ba - 1] + nw) / 2
        right_cx = (xs[ba] + xs[n - 1] + nw) / 2
        for cx, txt in ((left_cx, d.get("lane_left", "")), (right_cx, d.get("lane_right", ""))):
            if txt:
                tf = box(slide, cx - 2.6, 2.42, 5.2, 0.3)
                emit(Frame(tf).para(space_after=0, line_spacing=1.0, align=PP_ALIGN.CENTER),
                     txt.upper(), 11, THEME["dim"], font=BODY_FONT, bold=True)
        bx = (xs[ba - 1] + nw + xs[ba]) / 2
        bar(slide, bx - 0.008, 2.82, 0.016, (top + nh + 0.12) - 2.82, THEME["green"])
        tf = box(slide, bx - 0.95, 5.0, 1.9, 0.3)
        emit(Frame(tf).para(space_after=0, line_spacing=1.0, align=PP_ALIGN.CENTER),
             "SAGE", 12, THEME["bright"], font=TITLE_FONT, bold=True)
    else:
        gap = (usable - n * nw) / (n - 1)
        xs = [MARGIN + i * (nw + gap) for i in range(n)]

    mid_y = top + nh / 2
    for i in range(n - 1):
        cx = (xs[i] + nw + xs[i + 1]) / 2
        blockarrow(slide, cx - 0.10, mid_y - 0.09, 0.20, 0.18, "right", color=arrow_col)

    for i, step in enumerate(steps):
        flow_node(slide, xs[i], top, nw, nh, step, badge=badges, border=border_col, lw=lw)

    if d.get("caption"):
        tf = box(slide, MARGIN, top + nh + 0.5, BODY_W, 0.5)
        emit(Frame(tf).para(space_after=0, line_spacing=1.1, align=PP_ALIGN.CENTER),
             d["caption"], 15, THEME["body"], emph_color=THEME["bright"])

    chrome(slide, d)
    notes(slide, d["notes"])


def render_closing(slide, d):
    watermark(slide)
    bar(slide, MARGIN, 1.35, 2.4, 0.09, THEME["bright"])
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
    chrome(slide, d)
    notes(slide, d["notes"])


RENDERERS = {
    "title": render_title,
    "content": render_content,
    "diagram": render_diagram,
    "flow": render_flow,
    "demo": render_demo,
    "closing": render_closing,
}

# --------------------------------------------------------------------------- #
# Content (kept in sync with outline.md)
# Same "asked -> built -> delivered" arc as ../Presentation, trimmed to sub-10 min,
# with a recorded end-to-end demo as the payoff.
# --------------------------------------------------------------------------- #
SLIDES = [
    {
        "kind": "title",
        "kicker": "XBOX Developer Demos  \u00b7  Jul 2026",
        "title": "Instantly Shareable Playtest",
        "subtitle": "Stream a pre-release build from the cloud \u2014 in seconds. No install, no devkit.",
        "presenter": "Melanie Chen \u2014 Software Engineering Intern",
        "affil": "Xbox / Juno",
        "notes": (
            "Hi everyone \u2014 I'm Melanie, an SWE intern on Xbox Juno. In under 10 minutes I'll show "
            "Instantly Shareable Playtest: a creator can share an unreleased build that a tester streams "
            "from the cloud in seconds \u2014 no download, no install, no devkit. I'll frame the problem, "
            "walk the architecture and the two hardest pieces, then play a recorded end-to-end demo."
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
            "My summer: backend across **~13 services**, **two orgs**",
            "[One line \u2014 an interest or something fun about you]",
        ],
        "notes": (
            "A quick bit about me. [Fill in your school and background.] I joined Juno, whose mission is to "
            "lower the barrier for game creators. My project lived almost entirely in the backend, threading "
            "a build across about thirteen services \u2014 which meant ramping up fast. Big thanks to my manager "
            "Brian and my mentor Emma."
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
            "Where did this start? The xPlaytest team had already made testing easier \u2014 a creator can "
            "share a retail-signed private build without certification or a store page. But three barriers "
            "remained. Modern games are hundreds of gigabytes, so every tester sits through a huge install. "
            "Creators have to buy and set up lots of hardware to test compatibility. And physical devices are "
            "a security risk \u2014 a lost devkit means the unreleased code is right there. We wanted to "
            "remove all three."
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
            "**Not aware of another platform** that does this \u2014 beta channels download; cloud gaming streams published titles",
        ],
        "notes": (
            "The idea is to combine xPlaytest with Xbox Cloud Gaming. The creator just opts in to cloud "
            "streaming and shares a link. An invited tester clicks it and \u2014 instead of downloading "
            "anything \u2014 streams the build straight from the cloud, in seconds. It's still a real retail "
            "build; it just runs in xCloud instead of on the tester's own hardware. That's the north star. "
            "Worth noting the differentiation: we're not aware of another platform where a tester streams a "
            "private, unreleased build with no install \u2014 the beta channels (Steam playtests, TestFlight) are "
            "download-based, and cloud gaming services stream published titles you already own. This combines "
            "the two."
        ),
    },
    {
        "kind": "flow",
        "kicker": "How it works",
        "title": "The backend spine",
        "calm": True,
        "groups": [
            {"label": "Xbet \u00b7 xPlaytest / xPackage", "steps": [
                {"t": "Audience", "s": "invited DNA groups"},
                {"t": "Build", "s": "xPackage publish"},
                {"t": "Payload", "s": "asset + audience"},
            ]},
            {"label": "xCloud \u00b7 GSSV", "steps": [
                {"t": "Ingest", "s": "CTIN loads build"},
                {"t": "Offering", "s": "PTNR \u00b7 gated + title"},
                {"t": "Readiness", "s": "poll until staged"},
                {"t": "Share link", "s": "tester streams"},
            ]},
        ],
        "bridge": "SAGE",
        "caption": "**One publish** \u2192 one cross-cloud call \u2192 a **private, invite-scoped stream**.",
        "notes": (
            "One slide for the whole flow, since this is a dev crowd, grouped by the two systems it spans. "
            "On the left, Xbet \u2014 that's xPlaytest and the xPackage publish workflow, the caller: it resolves "
            "the audience (the invited DNA groups), the build publishes, and I assemble the payload of "
            "everything xCloud needs. That crosses to xCloud through SAGE, the cross-tenant gateway. On the "
            "right, xCloud \u2014 Game Streaming Services: content ingestion (CTIN) ingests the build, configures "
            "the private offering and attaches the title in Partner Registry, polls until a server has staged "
            "the exact version, and the share link streams it. I touched every hop across both systems; the "
            "next two slides zoom into the pieces I'm proudest of."
        ),
    },
    {
        "kind": "content",
        "kicker": "My contribution",
        "title": "The payload builder",
        "lead": "**Assembling everything xCloud needs** to stream a build, from the publish snapshot",
        "bullets": [
            "Builds the payload from the publish snapshot: **StoreAsset**, **allowed DNA groups**, "
            "sandbox, bounded expiration",
            "Mints a **cross-tenant token** and fires the streaming ingest",
            "**Opt-in** (pilot seller) and **non-blocking** \u2014 never breaks the normal download publish",
        ],
        "notes": (
            "My headline piece is the payload builder. When a creator publishes, I take a snapshot of that "
            "publish and assemble everything Game Streaming Services needs: the store asset details, the "
            "allowed audience groups, the sandbox, and a bounded expiration. Then it mints a cross-tenant token "
            "and fires the ingestion. Two design choices I care about: it's opt-in, gated to a pilot seller so "
            "we could roll out safely; and it's non-blocking \u2014 if streaming ever fails, the normal "
            "download publish still succeeds. We never degrade the existing product to add the new one."
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
            "The hardest problem was authentication across that org boundary. The caller lives in the MSFT "
            "Green tenant and the receiver lives in Corp \u2014 two separate trust domains. The Green side "
            "mints an older-style token whose audience claim is just a bare GUID, and the receiver kept "
            "rejecting it with 'audience null is invalid.' I traced the token through both services to find "
            "that mismatch, then fixed the receiver to accept the bare-GUID audience. When that clicked, the "
            "request finally authenticated and authorized end to end \u2014 the kind of bug that's invisible "
            "until you understand both sides."
        ),
    },
    {
        "kind": "demo",
        "kicker": "Demo",
        "title": "Publish \u2192 cross-cloud ingest \u2192 live offering",
        "caption": ("**1** opt in & publish   \u00b7   **2** backend threads it across two clouds (Green\u2192Corp)   "
                    "\u00b7   **3** a private streaming offering, **live in prod**   \u2014   *goal: stream in seconds*"),
        "notes": (
            "You've seen the architecture and the two hard parts \u2014 now watch it work. Beat one: a creator "
            "publishes a playtest with cloud streaming on \u2014 opt-in. (The creator toggle front end isn't "
            "built yet, so I fire the exact same publish signal it will send.) Beat two: on publish, the backend "
            "assembles the payload, mints the cross-tenant token, sends Green\u2192Corp through SAGE, ingests the "
            "build, and polls for a server. Beat three: that one publish produces a **private, invite-scoped "
            "streaming offering that's live and resolvable in prod** \u2014 here's the product page with the "
            "'Get Ready to Stream' CTA. The **goal is the tester clicking that and streaming in seconds** \u2014 "
            "that last mile, the front ends and the prod streaming lane, is what's next. [Play recording. ~3 min.]"
        ),
    },
    {
        "kind": "content",
        "kicker": "What I delivered",
        "title": "What's shipped",
        "checks": [
            "Private streaming offering created per playtest",
            "Audience scoped to invited DNA groups",
            "New build ingested into streaming on publish",
            "Seller flighting to limit blast radius",
            "Shareable-stream backend",
        ],
        "bullets": [
            "Shipped across **~13 services** in **two orgs**",
            "Backend spine in **main** and **deployed to prod** \u2014 a pilot-seller publish fires the "
            "full Green\u2192SAGE\u2192ingest call",
            "Next: the two **front ends** (creator toggle + tester landing)",
        ],
        "body_top": 1.95,
        "notes": (
            "So what actually shipped? Going down the P0 list: private offering per playtest \u2014 done; "
            "audience scoping \u2014 done; build ingestion on publish \u2014 done; seller flighting to limit "
            "blast radius \u2014 done; and the shareable-stream backend \u2014 done. It spans roughly thirteen "
            "services across two orgs. The backend spine is in main and deployed "
            "to prod \u2014 today a publish by our pilot seller fires the whole cross-cloud call for real. "
            "Why it matters: it removes the two barriers testing had \u2014 there's no multi-hundred-GB install "
            "for the tester, and because the build only ever runs in the cloud, an unreleased game never leaves "
            "on someone's hardware, so there's no leaked-devkit risk. What's left is the two front ends."
        ),
    },
    {
        "kind": "closing",
        "title": "Thanks \u2014 questions?",
        "lines": [
            "Mentor **Emma Park**  \u00b7  Manager **Brian Bowman**",
            "Feature leads **David Kushmerick** & **Bec Lyons**  \u00b7  the **Juno**, **xPlaytest** & **GSSV** teams",
            "**What's next:** the two front ends \u2014 the creator's **share link** + the **Bayside tester "
            "experience** (log in first, then metadata + stream)",
            "**Then:** playtester **feedback** to the studio  \u00b7  **launch args**, **streaming region / touch "
            "controls**, **console** support",
        ],
        "closer": "Questions?",
        "notes": (
            "That's the demo. Huge thanks to my mentor Emma and manager Brian, to David and Bec on the feature "
            "side, and the Juno, xPlaytest, and Game Streaming teams. On what's next \u2014 straight from the "
            "project's north star: the two front ends are the big ones, the creator's shareable link in the "
            "xPlaytest portal and the Bayside tester experience, which logs the tester in first so nothing leaks, "
            "then shows the playtest's details and art and lets them stream. After that, rounding out self-serve "
            "\u2014 deleting a playtest cleans up its offering, and funneling playtester feedback back to the "
            "studio \u2014 and the stretch goals: launch args so a nightly test can jump to a level or a dev "
            "mode, streaming region and touch controls, and console support. It's all documented in the Juno "
            "repo. Happy to take questions."
        ),
    },
    {
        "kind": "diagram",
        "appendix": True,
        "kicker": "Appendix",
        "title": "Detailed architecture",
        "caption": "Full end-to-end flow & readiness polling \u2014 deep-dive reference.",
        "notes": (
            "Backup slide for Q&A \u2014 the complete, detailed architecture diagram behind the six-step spine, "
            "including the PC install-readiness polling loop."
        ),
    },
]


def build():
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    blank = prs.slide_layouts[6]

    main_total = sum(1 for s in SLIDES if not s.get("appendix"))
    for i, d in enumerate(SLIDES, start=1):
        d["page"] = i
        d["total"] = main_total
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
