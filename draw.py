#!/usr/bin/env python3
"""draw.py — '3D BROADSHEET POP-UP' for make.fun bounty news-image-20261120.

Draws a floating 3D newspaper front page summing up Friday 20 November 2026.
Every element carries depth (soft blurred drop shadows, highlight edges,
layered gradients) while all text sits on flat, front-facing panels so it
stays 100% readable. Pillow only; output is deterministic.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W = H = 1024

CREAM = (246, 240, 226)
CREAM_D = (232, 222, 198)
INK = (18, 22, 30)
NAVY = (20, 33, 61)
RED = (165, 42, 33)          # brick red
RED_D = (128, 30, 24)
BLUE = (20, 80, 122)         # sea blue
BLUE_L = (64, 128, 175)
WHITE = (255, 255, 255)
PAPER = (252, 250, 244)
GREY = (92, 96, 104)

SERIF_B = os.path.join(HERE, "fonts", "DejaVuSerif-Bold.ttf")
SERIF = os.path.join(HERE, "fonts", "DejaVuSerif.ttf")
SANS_B = os.path.join(HERE, "fonts", "DejaVuSans-Bold.ttf")
SANS = os.path.join(HERE, "fonts", "DejaVuSans.ttf")

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def text_w(draw, s, fnt):
    return draw.textlength(s, font=fnt)


def fit_size(draw, s, path, size, max_w, min_size=9):
    """Largest font size <= size at which s fits max_w."""
    while size > min_size and text_w(draw, s, font(path, size)) > max_w:
        size -= 1
    return size


def wrap(draw, s, fnt, max_w):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if text_w(draw, t, fnt) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def vgrad(size, top, bottom):
    """Vertical gradient image of the given size."""
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return img


def soft_shadow(base, box, radius=14, blur=12, alpha=110, dy=10, dx=0):
    """Composite a soft blurred shadow of a rounded rect onto base (RGBA)."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0 + dx, y0 + dy, x1 + dx, y1 + dy],
                        radius=radius, fill=(10, 10, 20, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def raised_panel(base, box, fill, radius=12, shadow_alpha=110, dy=10,
                 edge=(255, 255, 255), edge_w=2):
    """A panel with soft shadow, a light top edge and a darker bottom edge."""
    soft_shadow(base, box, radius=radius, alpha=shadow_alpha, dy=dy)
    d = ImageDraw.Draw(base)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=radius, fill=fill + (255,))
    # top highlight
    d.line([x0 + radius, y0 + 1, x1 - radius, y0 + 1], fill=edge + (255,),
           width=edge_w)
    d.arc([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270,
          fill=edge + (255,), width=edge_w)
    d.arc([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360,
          fill=edge + (255,), width=edge_w)
    # bottom shade
    shade = tuple(max(0, c - 46) for c in fill)
    d.line([x0 + radius, y1 - 2, x1 - radius, y1 - 2], fill=shade + (255,),
           width=2)


def embossed(draw, xy, s, fnt, fill, shadow=(60, 52, 40), hi=(255, 252, 240),
             anchor="la"):
    """Raised-letter text: dark offset below, light offset above, face on top."""
    x, y = xy
    draw.text((x + 2, y + 3), s, font=fnt, fill=shadow, anchor=anchor)
    draw.text((x - 1, y - 1), s, font=fnt, fill=hi, anchor=anchor)
    draw.text((x, y), s, font=fnt, fill=fill, anchor=anchor)


def centered(draw, cx, y, s, fnt, fill):
    draw.text((cx, y), s, font=fnt, fill=fill, anchor="ma")


# ---------------------------------------------------------------- canvas ---
def base_canvas():
    img = vgrad((W, H), (250, 245, 231), (233, 224, 200)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # faint paper frame
    d.rounded_rectangle([10, 10, W - 10, H - 10], radius=18,
                        outline=(178, 164, 128, 255), width=2)
    return img


def header(img):
    d = ImageDraw.Draw(img)
    # masthead band shadow + band
    raised_panel(img, [24, 22, 1000, 158], PAPER, radius=14, dy=8)
    d = ImageDraw.Draw(img)
    f_mast = font(SERIF_B, 56)
    embossed(d, (512, 38), "THE WORLD IN ONE DAY", f_mast, NAVY, anchor="ma")
    # red rule with 3D notch
    d.rectangle([44, 104, 980, 108], fill=RED + (255,))
    d.rectangle([44, 108, 980, 110], fill=RED_D + (255,))
    f_date = font(SERIF_B, 33)
    embossed(d, (512, 114), "FRIDAY 20 NOVEMBER 2026", f_date, RED,
             anchor="ma")


# ------------------------------------------------------------------ hero ---
def cyclone_scene(img, box):
    """Layered 3D cyclone: gradient sky, spiral cloud, waves, tiny house."""
    x0, y0, x1, y1 = box
    soft_shadow(img, box, radius=14, alpha=120, dy=10)
    scene = vgrad((x1 - x0, y1 - y0), (38, 74, 116), (122, 168, 205))
    mask = Image.new("L", scene.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, scene.size[0], scene.size[1]], radius=14,
                         fill=255)
    img.paste(scene.convert("RGBA"), (x0, y0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=14, outline=(16, 40, 66, 255), width=3)

    cx, cy = x0 + 208, y0 + 84
    # spiral cloud arms (layered arcs, light greys with shading)
    for i, (r, a0, col, wd) in enumerate([
            (70, 200, (196, 208, 220), 15), (61, 30, (222, 230, 238), 14),
            (52, 230, (178, 194, 210), 13), (43, 60, (235, 240, 245), 12),
            (34, 250, (190, 204, 218), 11), (26, 90, (240, 244, 248), 10),
            (18, 270, (205, 218, 230), 9)]):
        d.arc([cx - r, cy - r * 0.82, cx + r, cy + r * 0.82], a0, a0 + 235,
              fill=col + (255,), width=wd)
    d.ellipse([cx - 10, cy - 8, cx + 10, cy + 8], fill=(30, 54, 84, 255))
    d.ellipse([cx - 5, cy - 4, cx + 5, cy + 4], fill=(12, 26, 44, 255))

    # rain streaks
    for i in range(7):
        rx = x0 + 330 + i * 34
        d.line([rx, y0 + 26, rx - 9, y0 + 48], fill=(210, 226, 240, 200),
               width=3)

    # 3D waves: three layered sine bands across the visible scene band
    for k, (wy, col, col_d) in enumerate([
            (128, (38, 106, 156), (24, 78, 120)),
            (146, (30, 92, 140), (18, 66, 106)),
            (164, (22, 76, 122), (12, 54, 92))]):
        pts = []
        for x in range(x0, x1 + 8, 8):
            pts.append((x, y0 + wy + 7 * math.sin((x - x0) / 46.0 + k * 1.7)))
        pts += [(x1, y1 - 64), (x0, y1 - 64)]
        d.polygon(pts, fill=col + (255,))
        crest = pts[:-2]
        d.line(crest, fill=(168, 205, 232, 255), width=3)

    # tiny 3D evacuation house on the right shore
    hx, hy = x0 + 500, y0 + 112
    d.polygon([(hx, hy), (hx + 26, hy - 20), (hx + 52, hy)], fill=RED + (255,))
    d.polygon([(hx + 52, hy), (hx + 66, hy - 12), (hx + 66, hy + 30),
               (hx + 52, hy + 34)], fill=RED_D + (255,))
    d.rectangle([hx + 4, hy, hx + 52, hy + 34], fill=(250, 238, 210, 255))
    d.rectangle([hx + 22, hy + 12, hx + 34, hy + 34], fill=(90, 60, 30, 255))
    d.rectangle([hx + 8, hy + 8, hx + 16, hy + 16], fill=BLUE + (255,))


def hero(img):
    box = [24, 176, 636, 474]
    cyclone_scene(img, box)
    # flat white text panel in front of the scene (text stays 100% flat)
    raised_panel(img, [40, 356, 620, 458], WHITE, radius=10, dy=6,
                 shadow_alpha=90)
    d = ImageDraw.Draw(img)
    d.rectangle([40, 356, 50, 458], fill=RED + (255,))
    f_h = font(SANS_B, 25)
    d.text((66, 366), "CYCLONE AKVAN LANDFALLS", font=f_h, fill=INK + (255,))
    f_b = font(SANS, 19)
    lines = ["72,000 evacuated — winds 90–100 km/h",
             "Andhra Pradesh / Odisha, India"]
    y = 400
    for ln in lines:
        d.text((66, y), ln, font=f_b, fill=(40, 44, 52, 255))
        y += 26


def float_card(img, box, fill, title_lines, body_lines, title_col=WHITE,
               body_col=(238, 240, 244)):
    raised_panel(img, box, fill, radius=12, dy=12, shadow_alpha=130,
                 edge=(255, 255, 255))
    d = ImageDraw.Draw(img)
    x0, y0, x1, _ = box
    y = y0 + 16
    f_t = font(SANS_B, 24)
    for ln in title_lines:
        sz = fit_size(d, ln, SANS_B, 24, x1 - x0 - 36)
        d.text((x0 + 18, y), ln, font=font(SANS_B, sz), fill=title_col + (255,))
        y += sz + 5
    y += 3
    f_b = font(SANS, 18)
    for ln in body_lines:
        d.text((x0 + 18, y), ln, font=f_b, fill=body_col + (255,))
        y += 24


def side_cards(img):
    float_card(img, [652, 176, 1000, 318], RED,
               ["EU SUMMONS", "RUSSIAN ENVOY"],
               ["After Kyiv attack damages", "EU embassies"])
    float_card(img, [652, 334, 1000, 474], INK,
               ["BERLIN SUMMIT", "€45B LOAN PLEDGE"],
               ["Coalition of the Willing —", "EU loan for Ukraine to 2027"])


COLUMNS = [
    ("EUROPE", BLUE, [
        "Kyiv: fire in Obolonskyi district after strikes",
        "Odesa bombardment: 4 dead, 13 wounded",
        "Trump–Xi–Putin summit in China: nuclear + Ukraine talks",
        "Kushner & Witkoff head to Berlin",
    ]),
    ("ASIA", RED, [
        "ICJ: historic Rohingya genocide ruling vs Myanmar",
        "North Korea: IAEA says enrichment increasing",
        "Japan: 5.6 quake in the southwest, 2 injured",
        "Cricket: India vs New Zealand Test",
    ]),
    ("AMERICAS", INK, [
        "US DOJ: 200+ subpoenas in Alaska election inquiry",
        "Trump puts Iran strikes 'on hold'",
        "Washington watches Berlin talks",
        "Gaza ceasefire holds — region on edge",
    ]),
]


def columns(img):
    boxes = [[24, 490, 344, 762], [352, 490, 672, 762], [680, 490, 1000, 762]]
    for (name, col, briefs), box in zip(COLUMNS, boxes):
        raised_panel(img, box, PAPER, radius=12, dy=9)
        d = ImageDraw.Draw(img)
        x0, y0, x1, _ = box
        # 3D header band
        d.rounded_rectangle([x0, y0, x1, y0 + 44], radius=12, fill=col + (255,))
        d.rectangle([x0, y0 + 30, x1, y0 + 44], fill=col + (255,))
        d.line([x0 + 12, y0 + 2, x1 - 12, y0 + 2],
               fill=(255, 255, 255, 255), width=2)
        shade = tuple(max(0, c - 40) for c in col)
        d.line([x0 + 8, y0 + 42, x1 - 8, y0 + 42], fill=shade + (255,),
               width=2)
        d.text(((x0 + x1) / 2, y0 + 8), name, font=font(SANS_B, 24),
               fill=WHITE + (255,), anchor="ma")
        y = y0 + 58
        f_b = font(SANS, 15)
        for i, b in enumerate(briefs):
            lines = wrap(d, b, f_b, x1 - x0 - 44)
            d.ellipse([x0 + 14, y + 4, x0 + 22, y + 12], fill=col + (255,))
            for ln in lines:
                d.text((x0 + 30, y), ln, font=f_b, fill=INK + (255,))
                y += 20
            y += 12
            if i < len(briefs) - 1:
                d.line([x0 + 16, y - 5, x1 - 16, y - 5],
                       fill=(214, 206, 184, 255), width=1)


# ------------------------------------------------------------------- map ---
CONTINENTS = [
    # (polygon points in a 952x118 strip space, shade offset for 3D)
    [(30, 30), (120, 16), (196, 26), (210, 52), (168, 66), (150, 96),
     (118, 104), (96, 74), (52, 66), (24, 50)],                        # Americas
    [(238, 44), (268, 66), (262, 96), (238, 108), (220, 84), (222, 58)],
    # Africa
    [(330, 22), (420, 14), (470, 30), (452, 52), (392, 56), (348, 44)],
    # Europe
    [(486, 40), (560, 26), (640, 34), (668, 58), (610, 76), (540, 70),
     (492, 60)],                                                       # Middle East/Asia west
    [(690, 24), (800, 16), (884, 30), (896, 58), (830, 84), (760, 92),
     (700, 66)],                                                       # Asia east
    [(806, 92), (858, 86), (884, 100), (862, 112), (820, 110)],        # Oceania
]

PINS = [
    (752, 44, "ASIA", "Odisha"),
    (392, 34, "EUROPE", "Kyiv"),
    (96, 40, "AMERICAS", "Alaska"),
    (244, 78, "AFRICA", "Cairo"),
    (846, 100, "OCEANIA", "Sydney"),
    (520, 52, "MIDDLE EAST", "Gaza"),
]


def pin(img, cx, cy, label, sub):
    d = ImageDraw.Draw(img)
    # soft shadow + stem + 3D ball with highlight
    soft_shadow(img, [cx - 13, cy + 16, cx + 13, cy + 30], radius=8, blur=6,
                alpha=90, dy=2)
    d = ImageDraw.Draw(img)
    d.polygon([(cx - 6, cy + 6), (cx + 6, cy + 6), (cx, cy + 24)],
              fill=RED_D + (255,))
    d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=RED + (255,))
    d.ellipse([cx - 8, cy - 10, cx + 1, cy - 2], fill=(226, 120, 108, 255))
    f = font(SANS_B, 13)
    sz = fit_size(d, label, SANS_B, 13, 150)
    d.text((cx, cy + 27), label, font=font(SANS_B, sz), fill=NAVY + (255,),
           anchor="ma")
    d.text((cx, cy + 45), sub, font=font(SANS, 12), fill=GREY + (255,),
           anchor="ma")


def map_strip(img):
    box = [24, 778, 1000, 956]
    raised_panel(img, box, (228, 238, 246), radius=12, dy=8)
    d = ImageDraw.Draw(img)
    ox, oy = 36, 792
    # raised continents: darker offset copy below, lighter face above
    for poly in CONTINENTS:
        off = [(ox + x, oy + y + 4) for x, y in poly]
        d.polygon(off, fill=(148, 168, 150, 255))
        face = [(ox + x, oy + y) for x, y in poly]
        d.polygon(face, fill=(196, 208, 178, 255))
        d.line(face + [face[0]], fill=(240, 246, 226, 255), width=2)
    for px, py, label, sub in PINS:
        pin(img, ox + px, oy + py, label, sub)
    d = ImageDraw.Draw(img)
    d.text((512, 940), "", font=font(SANS, 10), fill=GREY + (255,))


def footer(img):
    d = ImageDraw.Draw(img)
    s = ("10 stories · 6 continents · Friday 20 November 2026 · "
         "All stories first reported on 20 Nov 2026")
    sz = fit_size(d, s, SANS_B, 18, 940)
    d.text((512, 968), s, font=font(SANS_B, sz), fill=NAVY + (255,),
           anchor="ma")


def main():
    img = base_canvas()
    header(img)
    hero(img)
    side_cards(img)
    columns(img)
    map_strip(img)
    footer(img)
    img.convert("RGB").save(os.path.join(HERE, "entry.png"), optimize=True)
    print("wrote entry.png")


if __name__ == "__main__":
    main()
