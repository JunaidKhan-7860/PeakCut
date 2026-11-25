"""Turns a time range into a vertical clip: 9:16 layout, bouncy word captions, hook title, cover."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import config, roman
from .media import NO_WINDOW, run

W, H = config.OUT_W, config.OUT_H

# ASS colours are &HBBGGRR. `size` is the ASS font size (line height); _Font turns it into real pixels.
STYLES = {
    "bounce": {"label": "Bounce (Classic Gold)", "font": "Poppins ExtraBold", "size": 78, "base": "FFFFFF", "active": "00F0FF",
               "strong": "FFFFFF", "outline": 4, "pop": 108, "upper": True, "per": 3},
    "hype": {"label": "Hype (Red / Amber)", "font": "Anton", "size": 82, "base": "FFFFFF", "active": "3C3CFF",
             "strong": "00D7FF", "outline": 4, "pop": 110, "upper": True, "per": 2},
    "beast": {"label": "MrBeast Viral (Gold & Toxic Green)", "font": "Archivo Black", "size": 80, "base": "FFFFFF", "active": "00EAFF",
              "strong": "14FF39", "outline": 5, "pop": 110, "upper": True, "per": 2},
    "neon": {"label": "Cyber Neon (Cyan & Pink Glow)", "font": "Poppins ExtraBold", "size": 78, "base": "FFFFFF", "active": "FFFF00",
             "strong": "EA00FF", "outline": 4, "pop": 108, "upper": True, "per": 3},
    "fire": {"label": "Flame (Fire Red & Golden Ember)", "font": "Anton", "size": 82, "base": "FFFFFF", "active": "0055FF",
             "strong": "00EAFF", "outline": 4, "pop": 110, "upper": True, "per": 2},
    "tiktok": {"label": "TikTok Viral (Lime & White)", "font": "Poppins ExtraBold", "size": 78, "base": "FFFFFF", "active": "14FF39",
               "strong": "00F0FF", "outline": 4, "pop": 108, "upper": True, "per": 3},
    "comic": {"label": "Comic Pop (Bold Comic Yellow)", "font": "Archivo Black", "size": 80, "base": "FFFFFF", "active": "00EAFF",
              "strong": "2222FF", "outline": 5, "pop": 110, "upper": True, "per": 3},
    "clean": {"label": "Clean Minimal", "font": "Poppins ExtraBold", "size": 72, "base": "FFFFFF", "active": "6BD7FF",
               "strong": "FFFFFF", "outline": 3, "pop": 105, "upper": False, "per": 3},
    "gta": {"label": "GTA Neon (Pink / Cyan / Lime)", "font": "Poppins ExtraBold", "size": 78, "base": "F7E858", "active": "A54BFF",
            "strong": "58FBD4", "outline": 4, "pop": 110, "upper": True, "per": 3},
    "pill": {"label": "Neon Pill (Electric Highlight)", "font": "Poppins ExtraBold", "size": 76, "base": "FFFFFF", "active": "58FBD4",
             "strong": "A54BFF", "outline": 4, "pop": 108, "upper": False, "per": 3},
    "oneword": {"label": "One Word Punch (Huge Impact)", "font": "Archivo Black", "size": 92, "base": "FFFFFF", "active": "A54BFF",
                "strong": "58FBD4", "outline": 5, "pop": 114, "upper": True, "per": 1},
    "cine": {"label": "Cinematic (Wide Minimal)", "font": "Poppins ExtraBold", "size": 66, "base": "EDEDED", "active": "F7E858",
             "strong": "FFFFFF", "outline": 2, "pop": 103, "upper": False, "per": 4},
    "boxed": {"label": "Boxed Highlight", "font": "Poppins ExtraBold", "size": 74, "base": "FFFFFF", "active": "58FBD4",
              "strong": "A54BFF", "outline": 5, "pop": 106, "upper": False, "per": 3},
}
HOOK_THEMES = {
    "vice": {"label": "Khan Vice Pink Pill", "ink": "FFFFFF", "box": "A54BFF"},
    "cyan_neon": {"label": "Cyber Neon Cyan", "ink": "120918", "box": "F7E858"},
    "white": {"label": "Classic White Pill", "ink": "14100E", "box": "FFFFFF"},
    "yellow": {"label": "MrBeast Yellow Pill", "ink": "0D0A00", "box": "00E5FF"},
    "cyber": {"label": "Cyber Gold Pill", "ink": "000000", "box": "FFFF00"},
    "dark": {"label": "Dark Mode Minimal", "ink": "FFFFFF", "box": "1C1917"},
    "fire": {"label": "Hot Crimson Pill", "ink": "FFFFFF", "box": "0033CC"},
}
HOOK = {"font": "Poppins ExtraBold", "size": 82, "ink": "14100E", "box": "FFFFFF", "pad_x": 30, "pad_y": 18, "radius": 22,
        "max_w": 820}
FONT_FILES = {"Poppins ExtraBold": "Poppins-ExtraBold.ttf", "Anton": "Anton-Regular.ttf", "Archivo Black": "ArchivoBlack-Regular.ttf"}
CAP_MAX_W = 760   # captions never run wider than this, keeping 70% screen width max


class _Font:
    """Measures text exactly as the renderer will draw it, so every word can be placed by hand: the highlighted
    word can grow without pushing its neighbours, and the heading box fits its text."""
    _cache: dict = {}

    def __init__(self, name):
        import struct
        path = Path(__file__).resolve().parent / "fonts" / FONT_FILES.get(name, FONT_FILES["Poppins ExtraBold"])
        d = path.read_bytes()
        tables = {}
        for i in range(struct.unpack(">H", d[4:6])[0]):
            tag, _, off, _ = struct.unpack(">4sIII", d[12 + 16 * i: 28 + 16 * i])
            tables[tag] = off
        self.upm = struct.unpack(">H", d[tables[b"head"] + 18: tables[b"head"] + 20])[0]
        o = tables[b"OS/2"]
        self.asc, self.desc = struct.unpack(">HH", d[o + 74: o + 78])      # what the renderer sizes the font by
        self.cap = struct.unpack(">h", d[o + 88: o + 90])[0] or int(self.upm * 0.7)
        self.path = str(path)
        self._pil = {}

    @classmethod
    def get(cls, name):
        if name not in cls._cache:
            cls._cache[name] = cls(name)
        return cls._cache[name]

    def em(self, size):
        return size * self.upm / (self.asc + self.desc)

    def width(self, text, size):
        """Pixels wide at this ASS size."""
        try:
            from PIL import ImageFont
            if "f" not in self._pil:
                self._pil["f"] = ImageFont.truetype(self.path, 200)
            return self._pil["f"].getlength(text) * self.em(size) / 200
        except Exception:  # noqa: BLE001 - no measuring library: a fair estimate keeps clips rendering
            return len(text) * self.em(size) * 0.62

    def cap_shift(self, size):
        """How far below the anchor the middle of a capital letter sits when text is centred on a point."""
        return ((self.asc - self.desc) / 2 - self.cap / 2) * size / (self.asc + self.desc)


CAPTION_LEAD = 0.0  # measured: word stamps are within 0.15 s of the voice, so no shift is needed
def install_fonts():
    """Copy the bundled caption fonts next to the data, so captions look the same on every machine and server."""
    src = Path(__file__).resolve().parent / "fonts"
    for f in src.glob("*.ttf"):
        if not (config.FONTS_DIR / f.name).exists():
            shutil.copyfile(f, config.FONTS_DIR / f.name)


LAYOUTS = {"auto": "Smart layout (Reaction stacked if facecam present, else crop)",
           "blur": "Full frame + blurred fill", "zoom": "Zoomed in + blurred fill", "crop": "Fill the screen (centre crop)",
           "left": "Fill the screen, keep the left side", "right": "Fill the screen, keep the right side",
           "fit": "Full frame on black", "split": "Split screen: left half on top, right half below (two people)",
           "gameplay": "Gameplay fills the screen, facecam in the corner",
           "circle": "Gameplay fills the screen, circle facecam in the corner",
           "stacked": "Stacked reaction: Facecam on top, gameplay below"}
_FILLS = ("crop", "left", "right", "gameplay", "circle", "stacked", "auto")      # layouts where the picture covers the whole frame


def _ts(t):
    t = max(0.0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


def _clean(text):
    return re.sub(r"[\x00-\x1f\x7f]+", " ", re.sub(r"[{}\\]", "", str(text))).strip()


def _key(word):
    return re.sub(r"[^a-z0-9']", "", word.lower())


def _groups(words, per):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= per or sum(len(x["w"]) for x in cur) + len(w["w"]) > 16
                    or w["s"] - cur[-1]["e"] > 0.45 or cur[-1]["w"][-1:] in ".?!"):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def geometry(src_w, src_h, layout):
    """Where the video sits in the 1080x1920 frame, and where hook and captions go."""
    if src_h >= src_w and layout != "crop":
        layout = "crop"  # already vertical or square: nothing to gain from a blurred fill
    if layout not in LAYOUTS:
        layout = "blur"
    if layout in ("blur", "fit"):
        fg_h = min(H, int(round(W * src_h / src_w / 2)) * 2)
    elif layout == "zoom":
        fg_h = 1000
    else:
        fg_h = H
    top = (H - fg_h) // 2
    if layout == "stacked":
        return layout, H, 240, 860
    if layout in _FILLS:
        return layout, fg_h, 300, 1540
    if layout == "split":
        return layout, fg_h, 230, H // 2        # captions sit on the line between the two people
    return layout, fg_h, max(230, top - 190), min(1640, top + fg_h + 180)


def _teaser_hook_events(text, dur, y=360):
    """High-energy attention grabbing pill displayed during the opening climax teaser (e.g. 'WAIT FOR IT... 👀')."""
    if not text:
        return []
    clean_text = _clean(text).upper()
    if not clean_text:
        return []
    f, size = _Font.get(HOOK["font"]), 82
    tw = max(240.0, f.width(clean_text, size))
    pad_x, pad_y, r = 38, 20, 26
    bw, bh = tw + 2 * pad_x, f.em(size) * 1.16 + 2 * pad_y
    x0, y0 = (W - bw) / 2, y - bh / 2
    x1, y1 = x0 + bw, y0 + bh
    n = lambda v: f"{v:.0f}"
    box = (f"m {n(x0 + r)} {n(y0)} l {n(x1 - r)} {n(y0)} b {n(x1)} {n(y0)} {n(x1)} {n(y0)} {n(x1)} {n(y0 + r)} "
           f"l {n(x1)} {n(y1 - r)} b {n(x1)} {n(y1)} {n(x1)} {n(y1)} {n(x1 - r)} {n(y1)} "
           f"l {n(x0 + r)} {n(y1)} b {n(x0)} {n(y1)} {n(x0)} {n(y1)} {n(x0)} {n(y1 - r)} "
           f"l {n(x0)} {n(y0 + r)} b {n(x0)} {n(y0)} {n(x0)} {n(y0)} {n(x0 + r)} {n(y0)}")
    span = f"{_ts(0)},{_ts(dur)}"
    # High-impact Crimson / Fire box with glowing white bold font
    return [
        f"Dialogue: 5,{span},Hook,,0,0,0,,{{\\an7\\pos(0,0)\\fad(100,100)\\c&H0022DD&\\p1}}{box}{{\\p0}}",
        f"Dialogue: 6,{span},Hook,,0,0,0,,{{\\an5\\pos({W // 2},{y - f.cap_shift(size):.0f})\\fad(100,100)\\fs{size}\\c&HFFFFFF&\\b1}}{clean_text}"
    ]


def _hook_events(hook, dur, y, theme_name="white", start_t=0.0, show_sec=2.4):
    """The heading: text in a rounded box that fits it, on one line or two balanced ones.
    Shows for an initial attention-grabbing window (2.4s), then smoothly fades out so the video is clean."""
    theme = HOOK_THEMES.get(theme_name, HOOK_THEMES["white"])
    ink_color = theme["ink"]
    box_color = theme["box"]
    f, size = _Font.get(HOOK["font"]), HOOK["size"]
    words = hook.split()
    if not words:
        return []
    lines = [" ".join(words)]
    if f.width(lines[0], size) > HOOK["max_w"] and len(words) > 1:      # two lines, split where they come out most even
        cut = min(range(1, len(words)), key=lambda i: max(f.width(" ".join(words[:i]), size), f.width(" ".join(words[i:]), size)))
        lines = [" ".join(words[:cut]), " ".join(words[cut:])]
    widest = max(f.width(l, size) for l in lines)
    if widest > HOOK["max_w"]:
        size = max(40, int(size * HOOK["max_w"] / widest))
        widest = max(f.width(l, size) for l in lines)
    line_h = f.em(size) * 1.16
    bw, bh = widest + 2 * HOOK["pad_x"], line_h * len(lines) + 2 * HOOK["pad_y"]
    x0, y0, r = (W - bw) / 2, y - bh / 2, min(HOOK["radius"], bh / 2)
    x1, y1 = x0 + bw, y0 + bh
    n = lambda v: f"{v:.0f}"                                                         # noqa: E731
    box = (f"m {n(x0 + r)} {n(y0)} l {n(x1 - r)} {n(y0)} b {n(x1)} {n(y0)} {n(x1)} {n(y0)} {n(x1)} {n(y0 + r)} "
           f"l {n(x1)} {n(y1 - r)} b {n(x1)} {n(y1)} {n(x1)} {n(y1)} {n(x1 - r)} {n(y1)} "
           f"l {n(x0 + r)} {n(y1)} b {n(x0)} {n(y1)} {n(x0)} {n(y1)} {n(x0)} {n(y1 - r)} "
           f"l {n(x0)} {n(y0 + r)} b {n(x0)} {n(y0)} {n(x0)} {n(y0)} {n(x0 + r)} {n(y0)}")
    end_t = min(dur, start_t + show_sec)
    span = f"{_ts(start_t)},{_ts(end_t)}"
    ev = [f"Dialogue: 3,{span},Hook,,0,0,0,,{{\\an7\\pos(0,0)\\fad(120,450)\\c&H{box_color}&\\p1}}{box}{{\\p0}}"]
    for i, line in enumerate(lines):
        cy = y - line_h * (len(lines) - 1) / 2 + i * line_h - f.cap_shift(size)
        ev.append(f"Dialogue: 4,{span},Hook,,0,0,0,,{{\\an5\\pos({W // 2},{cy:.0f})\\fad(120,450)\\fs{size}\\c&H{ink_color}&}}{line}")
    return ev


def _corner_tag_events(tag_text, dur, pos="top-left", show_sec=2.6):
    """Optional subtle frosted pill watermark in the corner (e.g. '🔴 Kai Cenat' or 'Watch @Streamer').
    Fades out after 2.6s so it doesn't clutter the rest of the video."""
    if not tag_text or not str(tag_text).strip():
        return []
    text = _clean(tag_text)
    if not text:
        return []
    f = _Font.get("Poppins ExtraBold")
    size = 42
    tw = max(100.0, f.width(text, size))
    pad_x, pad_y, r = 24, 14, 18
    bw, bh = tw + 2 * pad_x, f.em(size) * 1.1 + 2 * pad_y
    if pos == "top-right":
        x0, y0 = W - bw - 50, 60
    else:  # top-left
        x0, y0 = 50, 60
    x1, y1 = x0 + bw, y0 + bh
    n = lambda v: f"{v:.0f}"
    box = (f"m {n(x0 + r)} {n(y0)} l {n(x1 - r)} {n(y0)} b {n(x1)} {n(y0)} {n(x1)} {n(y0)} {n(x1)} {n(y0 + r)} "
           f"l {n(x1)} {n(y1 - r)} b {n(x1)} {n(y1)} {n(x1)} {n(y1)} {n(x1 - r)} {n(y1)} "
           f"l {n(x0 + r)} {n(y1)} b {n(x0)} {n(y1)} {n(x0)} {n(y1)} {n(x0)} {n(y1 - r)} "
           f"l {n(x0)} {n(y0 + r)} b {n(x0)} {n(y0)} {n(x0)} {n(y0)} {n(x0 + r)} {n(y0)}")
    end_t = min(dur, show_sec)
    span = f"{_ts(0)},{_ts(end_t)}"
    return [
        f"Dialogue: 3,{span},Hook,,0,0,0,,{{\\an7\\pos(0,0)\\fad(120,450)\\1a&H40&\\c&H14100E&\\p1}}{box}{{\\p0}}",
        f"Dialogue: 4,{span},Hook,,0,0,0,,{{\\an5\\pos({n(x0 + bw / 2)},{n(y0 + bh / 2 - f.cap_shift(size))})\\fad(120,450)\\fs{size}\\c&HFFFFFF&}}{text}"
    ]


def _progress_bar_events(dur, color="00F0FF"):
    """Subtle animated retention progress bar moving across the bottom of the screen (0% to 100%)."""
    ms = int(dur * 1000)
    span = f"{_ts(0)},{_ts(dur)}"
    y0, y1 = 1910, 1918  # 8px high bar at bottom
    # Track background (subtle dark line with 50% opacity)
    bg_box = f"m 0 {y0} l {W} {y0} l {W} {y1} l 0 {y1}"
    return [
        f"Dialogue: 4,{span},Hook,,0,0,0,,{{\\an7\\pos(0,0)\\1a&H80&\\c&H1A1715&\\p1}}{bg_box}{{\\p0}}",
        f"Dialogue: 5,{span},Hook,,0,0,0,,{{\\an7\\pos(0,0)\\c&H{color}&\\clip(0,{y0},0,{y1})\\t(0,{ms},\\clip(0,{y0},{W},{y1}))\\p1}}{bg_box}{{\\p0}}"
    ]


def build_ass(words, start, end, hook, style_name, highlight, hook_y, cap_y, hook_theme="white", corner_tag="", progress_bar=True,
              teaser_hook=False, teaser_dur=0.0, teaser_text="") -> str:
    st = STYLES.get(style_name, STYLES["bounce"])
    words = [dict(w, s=w["s"] - CAPTION_LEAD, e=w["e"] - CAPTION_LEAD) for w in words]
    strong = {_key(h) for h in highlight if _key(h)}
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{st['font']},{st['size']},&H00{st['base']},&H00{st['base']},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,{st['outline']},0,5,0,0,0,1
Style: Hook,{HOOK['font']},{HOOK['size']},&H00{HOOK['ink']},&H00{HOOK['ink']},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    t_offset = float(teaser_dur) if teaser_hook else 0.0
    main_dur = end - start
    total_dur = main_dur + t_offset
    
    ev = []
    if teaser_hook and t_offset > 0:
        ev += _teaser_hook_events(teaser_text or "WAIT FOR IT... 👀", t_offset, hook_y)
        ev += _hook_events(_clean(hook), total_dur, hook_y, hook_theme, start_t=t_offset, show_sec=2.4)
    else:
        ev += _hook_events(_clean(hook), total_dur, hook_y, hook_theme, start_t=0.0, show_sec=2.4)

    if corner_tag:
        ev += _corner_tag_events(corner_tag, total_dur, show_sec=2.6)
    if progress_bar:
        bar_color = st.get("active", "00F0FF")
        ev += _progress_bar_events(total_dur, bar_color)
    f = _Font.get(st["font"])
    inside = [dict(w, w=_clean(w["w"])) for w in words if w["s"] >= start - 0.05 and w["s"] < end]
    inside = sorted((w for w in inside if w["w"]), key=lambda w: w["s"])
    for i, w in enumerate(inside[:-1]):
        w["e"] = max(w["s"], min(w["e"], inside[i + 1]["s"]))
    groups = _groups(inside, st["per"])
    for gi, g in enumerate(groups):
        g_start = max(0.0, g[0]["s"] - start) + t_offset
        g_end = min(g[-1]["e"] + 0.25, groups[gi + 1][0]["s"] if gi + 1 < len(groups) else end) - start + t_offset
        if g_end - g_start < 0.02:
            continue
        texts = []
        for x in g:
            t = re.sub(r"[.,;:]+$", "", x["w"])
            texts.append(t.upper() if st["upper"] else t)
        if not all(roman.drawable(t) for t in texts):
            # A script the caption font cannot draw (Japanese, Thai, Chinese...): its words cannot be measured, so
            # they are not placed one by one. The line is drawn whole and centred, in a font the system has for it.
            line = " ".join(texts)
            fs = max(44, min(int(st["size"] * 0.7), int(1500 / max(1, len(line)) * 1.6)))
            ev.append(f"Dialogue: 1,{_ts(g_start)},{_ts(g_end)},Cap,,60,60,0,,{{\\an5\\pos({W // 2},{cap_y:.0f})\\q0\\fs{fs}}}{line}")
            continue
        size = st["size"]
        gap = f.width("n n", size) - 2 * f.width("n", size) + (2 * st["outline"] + 6) * size / st["size"]   # a space, plus room for both outlines
        total = sum(f.width(t, size) for t in texts) + gap * (len(texts) - 1)
        if total > CAP_MAX_W:                                  # a long phrase: shrink it to fit, never run off the frame
            size = max(36, int(size * CAP_MAX_W / total))
            gap = f.width("n n", size) - 2 * f.width("n", size) + (2 * st["outline"] + 6) * size / st["size"]   # a space, plus room for both outlines
            total = sum(f.width(t, size) for t in texts) + gap * (len(texts) - 1)
        cy = cap_y - f.cap_shift(size)
        x = (W - total) / 2
        p = st["pop"]
        for i, (w, t) in enumerate(zip(g, texts)):
            wd = f.width(t, size)
            p = max(104, min(st["pop"], 100 + int(2200 / max(wd, 1))))   # long words grow less, so they never touch their neighbours
            pos = f"\\an5\\pos({x + wd / 2:.0f},{cy:.0f})\\fs{size}"
            x += wd + gap
            a = max(g_start, w["s"] - start + t_offset)
            b = (g[i + 1]["s"] - start + t_offset) if i + 1 < len(g) else g_end
            base = st["strong"] if _key(w["w"]) in strong else st["base"]
            if a - g_start >= 0.02:                                                   # waiting to be said
                ev.append(f"Dialogue: 1,{_ts(g_start)},{_ts(a)},Cap,,0,0,0,,{{{pos}\\c&H{base}&}}{t}")
            if b - a >= 0.02:                                                         # being said: colour and a quick pop, in front
                ev.append(f"Dialogue: 2,{_ts(a)},{_ts(b)},Cap,,0,0,0,,{{{pos}\\c&H{st['active']}&\\fscx94\\fscy94"
                          f"\\t(0,90,\\fscx{p}\\fscy{p})\\t(90,200,\\fscx{p - 5}\\fscy{p - 5})}}{t}")
            if g_end - b >= 0.02:                                                     # said
                ev.append(f"Dialogue: 1,{_ts(b)},{_ts(g_end)},Cap,,0,0,0,,{{{pos}\\c&H{base}&\\fscx{p - 5}\\fscy{p - 5}"
                          f"\\t(0,90,\\fscx100\\fscy100)}}{t}")
    return head + "\n".join(ev) + "\n"


PIP_W = 440            # how wide the facecam is in the 1080-wide frame
PIP_MARGIN = 24


def _filter(layout, fg_h, facecam=None, punch_zoom=True, vin="0:v", vout="v0"):
    pfx = vin.replace(":", "_")
    zoom_crop = ",crop=w='if(lt(t,2.2),in_w/1.14,in_w)':h='if(lt(t,2.2),in_h/1.14,in_h)':x='(in_w-out_w)/2':y='(in_h-out_h)/2',scale="
    scale_hd = "force_original_aspect_ratio=increase:flags=lanczos+accurate_rnd"
    clarity = ",unsharp=lx=5:ly=5:la=0.65:cx=5:cy=5:ca=0.25,eq=contrast=1.05:saturation=1.08"

    # 1. STACKED FACECAM + GAMEPLAY (Top 42% Streamer Reaction, Bottom 58% Gameplay)
    if layout in ("stacked", "streamer"):
        top_h = 820
        bot_h = H - top_h  # 1100
        if facecam and len(facecam) == 4 and int(facecam[2]) > 8 and int(facecam[3]) > 8:
            fx, fy, fw, fh = (int(v) for v in facecam)
            fc_crop = f"crop={fw}:{fh}:{fx}:{fy},"
        else:
            fc_crop = "crop=iw/2:ih/2:0:0,"
        zoom_top = f"{zoom_crop}{W}:{top_h}" if punch_zoom else ""
        return (f"[{vin}]fps={config.OUT_FPS},split=2[{pfx}_t_src][{pfx}_b_src];"
                f"[{pfx}_t_src]{fc_crop}scale={W}:{top_h}:{scale_hd},crop={W}:{top_h},setsar=1{clarity}{zoom_top}[{pfx}_t];"
                f"[{pfx}_b_src]scale={W}:{bot_h}:{scale_hd},crop={W}:{bot_h},setsar=1{clarity}[{pfx}_b];"
                f"[{pfx}_t][{pfx}_b]vstack,setsar=1[{vout}];")

    if layout == "circle" and facecam:
        fx, fy, fw, fh = (int(v) for v in facecam)
        if fw > 8 and fh > 8:
            side = 300
            base_zoom = f"{zoom_crop}{W}:{H}" if punch_zoom else ""
            return (f"[{vin}]fps={config.OUT_FPS},split=2[{pfx}_base][{pfx}_fc];"
                    f"[{pfx}_base]scale={W}:{H}:{scale_hd},crop={W}:{H},setsar=1{clarity}{base_zoom}[{pfx}_b];"
                    f"[{pfx}_fc]crop={fw}:{fh}:{fx}:{fy},scale={side}:{side}:{scale_hd},crop={side}:{side},"
                    f"format=yuva420p,geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':"
                    f"a='if(lte((X-{side}/2)*(X-{side}/2)+(Y-{side}/2)*(Y-{side}/2),({side}/2-2)*({side}/2-2)),255,0)'[{pfx}_p];"
                    f"[{pfx}_b][{pfx}_p]overlay={W - side - PIP_MARGIN}:{PIP_MARGIN}[{vout}];")
    if layout == "gameplay" and facecam:
        fx, fy, fw, fh = (int(v) for v in facecam)
        if fw > 8 and fh > 8:
            pip_h = max(2, int(round(PIP_W * fh / fw)))
            base_zoom = f"{zoom_crop}{W}:{H}" if punch_zoom else ""
            return (f"[{vin}]fps={config.OUT_FPS},split=2[{pfx}_base][{pfx}_fc];"
                    f"[{pfx}_base]scale={W}:{H}:{scale_hd},crop={W}:{H},setsar=1{clarity}{base_zoom}[{pfx}_b];"
                    f"[{pfx}_fc]crop={fw}:{fh}:{fx}:{fy},scale={PIP_W}:{pip_h}:{scale_hd},setsar=1{clarity}[{pfx}_p];"
                    f"[{pfx}_b][{pfx}_p]overlay={W - PIP_W - PIP_MARGIN}:{PIP_MARGIN}[{vout}];")
    fill = f"[{vin}]fps={config.OUT_FPS},scale={W}:{H}:{scale_hd},crop={W}:{H}{clarity}"
    zoom_str = f"{zoom_crop}{W}:{H}" if punch_zoom else ""
    if layout == "crop" or (layout in ("gameplay", "circle") and not facecam):
        return f"{fill},setsar=1{zoom_str}[{vout}];"
    if layout == "left":
        return f"{fill}:0:0,setsar=1{zoom_str}[{vout}];"
    if layout == "right":
        return f"{fill}:in_w-out_w:0,setsar=1{zoom_str}[{vout}];"
    if layout == "fit":
        return f"[{vin}]fps={config.OUT_FPS},scale={W}:{fg_h}:flags=lanczos,pad={W}:{H}:0:(oh-ih)/2:black,setsar=1{clarity}[{vout}];"
    if layout == "split":
        half = f"scale={W}:{H // 2}:{scale_hd},crop={W}:{H // 2}{clarity}"
        return (f"[{vin}]fps={config.OUT_FPS},split=2[{pfx}_l][{pfx}_r];[{pfx}_l]crop=iw/2:ih:0:0,{half}[{pfx}_t];"
                f"[{pfx}_r]crop=iw/2:ih:iw/2:0,{half}[{pfx}_u];[{pfx}_t][{pfx}_u]vstack,setsar=1[{vout}];")
    fg_zoom = f"{zoom_crop}{W}:{fg_h}" if punch_zoom else ""
    return (f"[{vin}]fps={config.OUT_FPS},split=2[{pfx}_a][{pfx}_b];"
            f"[{pfx}_a]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=6:2,"
            f"scale={W}:{H},eq=brightness=-0.14:saturation=1.15[{pfx}_bg];"
            f"[{pfx}_b]scale={W}:{fg_h}:{scale_hd},crop={W}:{fg_h}{clarity}{fg_zoom}[{pfx}_fg];"
            f"[{pfx}_bg][{pfx}_fg]overlay=0:(H-h)/2,setsar=1[{vout}];")


def _hook_y(layout, hook_y, facecam=None):
    """Where the heading goes. In the gameplay layout the webcam sits in the top corner, so a heading
    across the top would run under it: it goes just below the picture instead."""
    if layout == "stacked":
        return 220
    if layout == "circle" and facecam and len(facecam) == 4 and facecam[2] > 8:
        return PIP_MARGIN + 300 + 32
    if layout == "gameplay" and facecam and len(facecam) == 4 and facecam[2] > 8:
        return PIP_MARGIN + int(round(PIP_W * facecam[3] / facecam[2])) + 32
    return hook_y


_qsv_ok = None
RENDER_SECONDS = 600      # one clip's video encode; far beyond normal, so a frozen encoder is stopped, not waited on


def render_clip(src: Path, out_dir: Path, name: str, clip: dict, words: list, src_w: int, src_h: int) -> dict:
    """Writes <name>.mp4, <name>.jpg and <name>.ass into out_dir. Returns file names."""
    out_dir.mkdir(parents=True, exist_ok=True)
    start, end = clip["start"], clip["end"]
    layout, fg_h, hook_y, cap_y = geometry(src_w, src_h, clip.get("layout", "blur"))
    face = clip.get("facecam")
    if not face and src and Path(src).is_file():
        # Auto-detect streamer facecam on the source video piece
        try:
            from . import facecam
            c_name = clip.get("target_creator") or clip.get("creator") or clip.get("title") or ""
            detected = facecam.detect(src, creator=c_name)
            if detected:
                face = [detected["x"], detected["y"], detected["w"], detected["h"]]
                clip["facecam"] = face
                if layout in ("auto", "crop", "stacked", "streamer", "blur"):
                    layout = "stacked"
                    clip["layout"] = "stacked"
        except Exception:
            pass

    if layout in ("gameplay", "stacked", "streamer"):
        if not (face and len(face) == 4):
            layout = "crop"     # no webcam found: the game fills the screen, which is still the right shape
            face = None
            clip["facecam"] = None
            clip["layout"] = "crop"
        else:
            # Mandatory Human Face Verification & Reaction Quality Gate:
            # 1. Never place an empty box or game HUD at the top: must have a verified human face!
            # 2. Dynamic Reaction Check: If reaction is energetic/expressive, use stacked facecam;
            #    if streamer is deadpan, motionless, or silent, use full-screen 9:16 gameplay!
            try:
                from . import facecam
                if not facecam.verify_face_in_region(src, face, min_hits=2):
                    layout = "crop"
                    face = None
                    clip["facecam"] = None
                    clip["layout"] = "crop"
                else:
                    is_good_reaction, r_score, r_details = facecam.evaluate_reaction_quality(
                        src, face, clip_meta=clip, words=words
                    )
                    if not is_good_reaction:
                        layout = "crop"
                        face = None
                        clip["facecam"] = None
                        clip["layout"] = "crop"
                        clip["reaction_quality"] = r_details
                    else:
                        clip["reaction_quality"] = r_details
            except Exception:
                pass
    if layout == "stacked":
        cap_y = 860        # Subtitles sit in the neutral divider gap between facecam (0-820) and gameplay (820-1920)
    else:
        cap_y = 1540       # Full-screen crop/blur: lower-third safe zone, completely clear of central character/action
    hook_y = _hook_y(layout, hook_y, face)
    corner_tag = clip.get("corner_tag", "")
    prog_bar = clip.get("progress_bar", True)

    teaser_hook = bool(clip.get("teaser_hook", False))
    teaser_dur = float(clip.get("teaser_dur", 1.4)) if teaser_hook else 0.0
    teaser_text = str(clip.get("teaser_text", "WAIT FOR IT... 👀"))
    teaser_start = clip.get("teaser_start")
    if teaser_start is None:
        # Smart climax finder: scan words in second half (60-90%) for highest-energy shock words
        climax_suggest = None
        if words:
            mid_pt = start + (end - start) * 0.45
            late_words = [w for w in words if w.get("s", 0) >= mid_pt and w.get("e", 0) <= end]
            for w in late_words:
                text_u = str(w.get("w", "")).upper()
                if any(k in text_u for k in ("!", "?", "WHAT", "NO", "BRO", "OMG", "DEAD", "WTF", "CRAZY", "WAIT", "LOOK", "RUN", "LAUGH")):
                    climax_suggest = float(w.get("s", start + (end - start) * 0.70))
                    break
        if climax_suggest is None:
            climax_suggest = start + max(1.0, (end - start) * 0.70)
        teaser_start = min(climax_suggest, max(start, end - teaser_dur))
    else:
        teaser_start = float(teaser_start)

    ass = build_ass(words if clip.get("captions", True) else [], start, end, clip.get("hook", ""), clip.get("style", "bounce"),
                    clip.get("highlight_words", []), hook_y, cap_y, clip.get("hook_theme", "white"),
                    corner_tag=corner_tag, progress_bar=prog_bar,
                    teaser_hook=teaser_hook, teaser_dur=teaser_dur, teaser_text=teaser_text)

    # Background music resolution
    music_track = clip.get("music")
    music_path = None
    if music_track and music_track != "none":
        from . import music
        music_path = music.resolve_track(music_track, clip)

    music_vol = float(clip.get("music_vol", 0.18))
    punch_zoom = bool(clip.get("punch_zoom", True))
    hook_video = clip.get("hook_video")

    # Auditory pattern interrupt: Hook whoosh SFX
    hook_sfx = clip.get("hook_sfx", True)
    whoosh_path = config.DATA_DIR / "assets" / "hook_whoosh.m4a"
    if not (hook_sfx and whoosh_path.exists()):
        whoosh_path = None

    work = Path(tempfile.mkdtemp(prefix="pk"))
    try:
        # The title and description are also written into the file itself, for any place that reads them from it.
        meta = {"title": clip.get("title") or "", "description": clip.get("description") or "", "comment": clip.get("description") or ""}
        return _render_in(work, src, out_dir, name, start, end, layout, fg_h, ass, face=face,
                          music_path=music_path, music_volume=music_vol, punch_zoom=punch_zoom,
                          teaser_hook=teaser_hook, teaser_dur=teaser_dur, teaser_start=teaser_start,
                          hook_video=hook_video, whoosh_path=whoosh_path, meta=meta)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _render_in(work: Path, src: Path, out_dir: Path, name: str, start, end, layout, fg_h, ass: str, face=None,
               music_path: Path = None, music_volume: float = 0.18, punch_zoom: bool = True,
               teaser_hook: bool = False, teaser_dur: float = 0.0, teaser_start: float = 0.0,
               hook_video: str = None, whoosh_path: Path = None, meta: dict = None) -> dict:
    global _qsv_ok
    (work / f"{name}.ass").write_text(ass, encoding="utf-8")
    (work / "f").mkdir()
    for f in config.FONTS_DIR.glob("*.ttf"):
        shutil.copyfile(f, work / "f" / f.name)
    inputs = []
    maps = ["-map", "[v]"]

    if teaser_hook and teaser_dur > 0:
        # Dual-input pipeline: Climax Teaser / Hook clip + Main story
        if hook_video and Path(hook_video).exists():
            inputs += ["-t", f"{teaser_dur:.2f}", "-i", str(hook_video)]
        else:
            inputs += ["-ss", f"{teaser_start:.2f}", "-t", f"{teaser_dur:.2f}", "-i", str(src)]
        inputs += ["-ss", f"{start:.2f}", "-t", f"{end - start:.2f}", "-i", str(src)]

        # Video filters: High-energy teaser -> crisp white flash bloom -> main story
        f_teaser = _filter(layout, fg_h, face, punch_zoom=False, vin="0:v", vout="vt_raw")
        fade_dur = 0.18
        fade_st = max(0.0, teaser_dur - fade_dur)
        f_teaser_fade = f"[vt_raw]fade=t=out:st={fade_st:.2f}:d={fade_dur:.2f}:color=white[vt];"

        f_main = _filter(layout, fg_h, face, punch_zoom=punch_zoom, vin="1:v", vout="vm_raw")
        f_main_fade = f"[vm_raw]fade=t=in:st=0:d={fade_dur:.2f}:color=white[vm];"

        f_concat = f"[vt][vm]concat=n=2:v=1:a=0[v_cat];[v_cat]ass={name}.ass:fontsdir=f[v]"
        fc = f_teaser + f_teaser_fade + f_main + f_main_fade + f_concat

        # Audio concat: seamless crossfade
        f_audio = (f"[0:a]afade=t=out:st={fade_st:.2f}:d={fade_dur:.2f}[a0_f];"
                   f"[1:a]afade=t=in:st=0:d={fade_dur:.2f}[a1_f];"
                   f"[a0_f][a1_f]concat=n=2:v=0:a=1[speech_all]")

        # Hook whoosh SFX interrupt synced right at the flash transition point
        if whoosh_path and whoosh_path.exists():
            w_idx = inputs.count("-i")
            inputs += ["-i", str(whoosh_path)]
            whoosh_delay_ms = max(20, int(fade_st * 1000))
            f_whoosh = f";[{w_idx}:a]adelay={whoosh_delay_ms}|{whoosh_delay_ms},volume=0.65[wfx];[speech_all][wfx]amix=inputs=2:duration=first:dropout_transition=2[speech_base]"
        else:
            f_whoosh = ";[speech_all]anull[speech_base]"

        if music_path and music_path.exists():
            bgm_work = work / "bgm.mp3"
            try:
                shutil.copyfile(music_path, bgm_work)
            except Exception:
                bgm_work = music_path
            bgm_idx = inputs.count("-i")
            inputs += ["-i", str(bgm_work)]
            audio_filter = (
                f";[speech_base]asplit=2[sp1][sp2];"
                f"[{bgm_idx}:a]aloop=loop=-1:size=2e+09,volume={max(0.02, min(0.60, music_volume)):.2f}[bgm_loop];"
                f"[bgm_loop][sp1]sidechaincompress=threshold=0.08:ratio=5:attack=30:release=350[bgm_ducked];"
                f"[sp2][bgm_ducked]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
            )
            fc = fc + ";" + f_audio + f_whoosh + audio_filter
            maps += ["-map", "[aout]"]
        else:
            fc = fc + ";" + f_audio + f_whoosh + ";[speech_base]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
            maps += ["-map", "[aout]"]
    else:
        fc = _filter(layout, fg_h, face, punch_zoom, vin="0:v", vout="v0") + f"[v0]ass={name}.ass:fontsdir=f[v]"
        inputs = ["-ss", f"{start:.2f}", "-t", f"{end - start:.2f}", "-i", str(src)]

        if whoosh_path and whoosh_path.exists():
            w_idx = inputs.count("-i")
            inputs += ["-i", str(whoosh_path)]
            f_whoosh = f";[{w_idx}:a]adelay=50|50,volume=0.55[wfx];[0:a][wfx]amix=inputs=2:duration=first:dropout_transition=2[speech_base]"
        else:
            f_whoosh = ""

        if music_path and music_path.exists():
            bgm_work = work / "bgm.mp3"
            try:
                shutil.copyfile(music_path, bgm_work)
            except Exception:
                bgm_work = music_path
            bgm_idx = inputs.count("-i")
            inputs += ["-i", str(bgm_work)]
            sp_in = "[speech_base]" if whoosh_path else "[0:a]"
            audio_filter = (
                f";{sp_in}asplit=2[sp1][sp2];"
                f"[{bgm_idx}:a]aloop=loop=-1:size=2e+09,volume={max(0.02, min(0.60, music_volume)):.2f}[bgm_loop];"
                f"[bgm_loop][sp1]sidechaincompress=threshold=0.08:ratio=5:attack=30:release=350[bgm_ducked];"
                f"[sp2][bgm_ducked]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
            )
            fc = fc + f_whoosh + audio_filter
            maps += ["-map", "[aout]"]
        else:
            if whoosh_path and whoosh_path.exists():
                fc = fc + f_whoosh + ";[speech_base]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
                maps += ["-map", "[aout]"]
            else:
                maps += ["-map", "0:a:0", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]

    base = ["ffmpeg", "-y", "-v", "error"] + inputs + [
        "-filter_complex", fc] + maps + [
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000"
    ]
    for k, v in (meta or {}).items():
        if v:
            base += ["-metadata", f"{k}={v}"]
    base += ["-movflags", "+faststart", "-pix_fmt"]
    encoders = [
        ("nvenc", ["yuv420p", "-c:v", "h264_nvenc", "-preset", "p6", "-cq", "16", "-b:v", "18M", "-maxrate", "24M", "-bufsize", "36M"]),
        ("x264", ["yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "medium"]),
    ]
    if _qsv_ok is not False:
        encoders.append(("qsv", ["nv12", "-c:v", "h264_qsv", "-global_quality", "18", "-preset", "medium"]))
    err = None
    for label, enc in encoders:
        p = subprocess.run(base + enc + [f"{name}.mp4"], cwd=work, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", creationflags=NO_WINDOW, timeout=RENDER_SECONDS)
        if p.returncode == 0:
            if label == "qsv":
                _qsv_ok = True
            break
        err = p.stderr[-1200:]
        if label == "qsv":
            _qsv_ok = False
    else:
        raise RuntimeError(f"Render failed: {err}")

    cover_t = (teaser_dur if teaser_hook else 0.0) + min(1.2, (end - start) / 2)
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{cover_t:.2f}", "-i", f"{name}.mp4", "-frames:v", "1",
         "-q:v", "1", f"{name}.jpg"], cwd=work)
    for ext in ("mp4", "jpg", "ass"):
        shutil.move(str(work / f"{name}.{ext}"), str(out_dir / f"{name}.{ext}"))
    return {"file": f"{name}.mp4", "cover": f"{name}.jpg", "layout": layout}
