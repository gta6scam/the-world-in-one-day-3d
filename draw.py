#!/usr/bin/env python3
"""draw.py — generative builder for 'THE WORLD IN ONE DAY' (3D pop-up
broadsheet), make.fun bounty news-image-20261120, account @yutulboy.

Correction build (challenger-a2): SAME 3D pop-up concept, same masthead,
same Friday 20 November 2026 edition and story pool as the standing entry —
but the content is rebuilt to the winning evidence system: hook band with
the day's biggest story + biggest number, UTC timeline, bound numbers
strip, 13 fact-dense cards with data-carrying strips and source/certainty
tags, a real-polygon map with 13 numbered 3D pins, ALSO ON briefs 14-40,
and a named DATE CHECK. All text sits on flat front-facing panels; depth
comes from soft shadows, raised edges and embossed type. Pillow only;
deterministic. The hand-in program is main.py (copies entry.png); this
file is the build-time tool and is never executed by the grader.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from mapdata import WORLD

HERE = os.path.dirname(os.path.abspath(__file__))
W = H = 1024
MX = 24
CW = W - 2 * MX  # 976

CREAM = (246, 240, 226)
INK = (18, 22, 30)
NAVY = (20, 33, 61)
RED = (165, 42, 33)
RED_D = (128, 30, 24)
BLUE = (20, 80, 122)
WHITE = (255, 255, 255)
PAPER = (252, 250, 244)
GREY = (92, 96, 104)
BAND = (22, 40, 63)  # caption band navy

REGIONS = {
    "EUROPE": (20, 80, 122),
    "ASIA": (165, 42, 33),
    "MIDEAST": (146, 96, 20),
    "AFRICA": (34, 110, 60),
    "AMERICAS": (20, 33, 61),
    "OCEANIA": (110, 60, 140),
    "GLOBAL": (96, 96, 96),
}

PLAYFAIR = os.path.join(HERE, "fonts", "PlayfairDisplay-900.ttf")
ARCH_B = os.path.join(HERE, "fonts", "Archivo-Bold.ttf")
ARCH_M = os.path.join(HERE, "fonts", "Archivo-Medium.ttf")

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def tw(draw, s, fnt):
    return draw.textlength(s, font=fnt)


def fit_size(draw, s, path, size, max_w, min_size=8):
    while size > min_size and tw(draw, s, font(path, size)) > max_w:
        size -= 1
    return size


def wrap(draw, s, fnt, max_w):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if tw(draw, t, fnt) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def vgrad(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return img


def soft_shadow(base, box, radius=12, blur=10, alpha=105, dy=8):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0 + dy, x1, y1 + dy], radius=radius,
                        fill=(10, 10, 20, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def raised_panel(base, box, fill, radius=12, shadow_alpha=105, dy=8):
    soft_shadow(base, box, radius=radius, alpha=shadow_alpha, dy=dy)
    d = ImageDraw.Draw(base)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=radius, fill=fill + (255,))
    d.line([x0 + radius, y0 + 1, x1 - radius, y0 + 1],
           fill=(255, 255, 255, 255), width=2)
    shade = tuple(max(0, c - 42) for c in fill)
    d.line([x0 + radius, y1 - 2, x1 - radius, y1 - 2], fill=shade + (255,),
           width=2)


def embossed(draw, xy, s, fnt, fill, anchor="ma",
             shadow=(60, 52, 40), hi=(255, 252, 240)):
    x, y = xy
    draw.text((x + 2, y + 3), s, font=fnt, fill=shadow, anchor=anchor)
    draw.text((x - 1, y - 1), s, font=fnt, fill=hi, anchor=anchor)
    draw.text((x, y), s, font=fnt, fill=fill, anchor=anchor)


def centered(draw, cx, y, s, fnt, fill):
    draw.text((cx, y), s, font=fnt, fill=fill, anchor="ma")


# ------------------------------------------------------------------ data ---
# Pool: ~/workspace/makefun-news-image-20all/POOL.md (Friday 20 Nov 2026).
# fields: no, place, region, topic, headline, deck (sources at end),
#         certainty tag (strip), strip data label, pin lon/lat
LEADS = [
    (1, "KYIV, UKRAINE", "EUROPE", "MISSILE BARRAGE",
     "Russian missiles hit three Kyiv bridges",
     "Overnight barrage of 110 missiles and 400 drones killed at least "
     "nine people and cut power and water in the capital. "
     "(Kyiv Independent, BBC)",
     "Officials' count", "3 BRIDGES HIT", (30.5, 50.4)),
    (2, "ODISHA, INDIA", "ASIA", "CYCLONE LANDFALL",
     "Cyclone Akvan comes ashore in eastern India",
     "Crossed the coast near Gopalpur from about 8 am after 300,000+ "
     "people were moved to shelters. No deaths were reported. "
     "(IMD, Deccan Herald)",
     "Weather office", "LANDFALL - 8 AM", (84.9, 19.3)),
    (3, "TAIPEI - SEOUL - TOKYO", "ASIA", "MARKETS",
     "AI sell-off sinks Asia's stock markets",
     "Taiwan's index fell 6.2% to end its worst week since 1991. Seoul "
     "lost 5.2% and Tokyo 5.1% as chipmakers led the slide. "
     "(Al Jazeera, Anadolu)",
     "Closing prices", "TAIPEI -6.2% - SEOUL -5.2% - TOKYO -5.1%",
     (121.0, 25.0)),
]

MINIS = [
    (4, "BRUSSELS", "EUROPE", "UK and EU seal a \"reset\" deal",
     "Food trade, youth visas, carbon link - 100,000 youth visas a year. "
     "(Reuters)", "AGREED", "100,000 VISAS / YEAR", (4.3, 50.8)),
    (5, "ANTALYA", "GLOBAL", "COP31 reaches its last day with no deal",
     "Draft omits fossil fuels; $120bn adaptation gap stays open. "
     "(UN News)", "ONGOING", "NO DEAL - FINAL DAY", (30.7, 36.9)),
    (6, "EASTERN POLAND", "EUROPE", "Russian cruise missile lands in Poland",
     "Fell in a field; two airports paused; crossed in the Kyiv barrage. "
     "(Reuters)", "MINISTER SAYS", "FELL IN A FIELD", (22.5, 51.2)),
    (7, "CENTRAL IRAQ", "MIDEAST", "Iraqi army enters militia stronghold",
     "Troops deploy to Jurf al-Sakhar - first push into the town in "
     "years. (Reuters)", "WITNESSED", "JURF AL-SAKHAR", (44.2, 32.9)),
    (8, "ITALY", "EUROPE", "General strike over Italy's budget",
     "Marches in about 100 squares in a 24-hour CGIL stoppage. "
     "(Reuters, AFP)", "REPORTED", "SCIOPERO - 24H", (12.5, 41.9)),
    (9, "TOKYO", "ASIA", "Japan's inflation picks up to 2.3%",
     "CPI rose to 2.3% in October from 2.1%; December rate rise in view. "
     "(Reuters)", "OFFICIAL DATA", "CPI +2.3% OCT", (139.7, 35.7)),
    (10, "SEOUL", "ASIA", "Korea's ruling party to impeach top judge",
     "Impeach Chief Justice Cho Hee-dae after overturned conviction. "
     "(Korea Herald)", "PARTY DECISION", "CAUCUS VOTE", (127.0, 37.6)),
    (11, "TURKANA, KENYA", "AFRICA", "Kenya starts drilling its first oil well",
     "Ceremony opened the Turkana field; first crude due 1 December. "
     "(allAfrica)", "CEREMONY HELD", "FIRST CRUDE 1 DEC", (35.9, 3.1)),
    (12, "SAN SALVADOR", "AMERICAS", "Bukele files to run for a third term",
     "Filed with the electoral tribunal on Friday; vote is 28 Feb 2027. "
     "(AP)", "FILED", "VOTE 28 FEB 2027", (-89.2, 13.7)),
    (13, "WELLINGTON", "OCEANIA", "Phillips hits 118 against India",
     "Phillips 118, Nicholls 175, stand of 216; hundreds in all three "
     "formats. (ICC)", "SCORECARD", "118 - RECORD", (174.8, -41.3)),
]

TIMELINE = [
    ("OVERNIGHT", "Kyiv barrage: seven waves from 01:25 local"),
    ("02:30 UTC", "Cyclone Akvan makes landfall in Odisha"),
    ("06:00 UTC", "Tokyo close: Nikkei -5.1% in the AI sell-off"),
    ("MIDDAY", "Brussels: UK and EU seal the \"reset\" deal"),
    ("EVENING", "Wellington: Phillips completes 118 vs India"),
]

NUMBERS = [
    ("3", "bridges over the Dnipro damaged in Kyiv"),
    ("300,000+", "people moved to shelters before Akvan"),
    ("-6.2%", "Taiwan's share index, Friday's close"),
    ("100,000", "youth visas a year in the UK-EU deal"),
    ("$120bn", "adaptation finance gap left open at COP31"),
    ("118", "runs by Glenn Phillips against India"),
]

REGION_LINE = [("EUROPE", 9), ("ASIA", 10), ("MIDEAST", 3), ("AFRICA", 5),
               ("AMERICAS", 5), ("OCEANIA", 3), ("GLOBAL", 5)]

# Briefs 14-40: one line each, <=49 chars, number/name + source kept.
BRIEFS = [
    (14, "Lviv rail-station strike kills two (BBC)", (24.0, 49.8)),
    (15, "Russia decries Estonia closure (Reuters)", (37.6, 55.8)),
    (16, "Berlin pupils strike vs service (Al Jazeera)", (13.4, 52.5)),
    (17, "UK general: cyber attacks abroad (Sky News)", (-0.1, 51.5)),
    (18, "China holds loan rates, 18th month (Xinhua)", (116.4, 39.9)),
    (19, "SoftBank falls 14%+ in a day (Al Jazeera)", (139.7, 35.7)),
    (20, "Kospi ends the week 7.9% lower (Anadolu)", (127.0, 37.6)),
    (21, "209 mm rain as Akvan crosses Odisha (PTI)", (84.9, 19.3)),
    (22, "Israel strikes Lebanon south, east (Anadolu)", (35.5, 33.3)),
    (23, "Gunmen fire on ship off Yemen (UKMTO)", (43.3, 11.8)),
    (24, "Abuja court bars Tinubu evidence (Channels)", (7.5, 9.1)),
    (25, "Kampala enforces Ebola rally ban (allAfrica)", (32.6, 0.3)),
    (26, "Malawi fuel crisis: night queues (Al Jazeera)", (33.8, -13.9)),
    (27, "AfDB: 22 countries in debt distress (allAfrica)", (20.0, 5.0)),
    (28, "Russell tops wet Vegas practice (Autosport)", (-115.1, 36.2)),
    (29, "Nasdaq futures -1.6% pre-bell (24/7 Wall St)", (-74.0, 40.7)),
    (30, "Democrats query firm's free work (Al Jazeera)", (-77.0, 38.9)),
    (31, "Australian shares -1.6% in sell-off (Reuters)", (151.2, -33.9)),
    (32, "Panama asks COP31 for oil cap (Al Jazeera)", (30.7, 36.9)),
    (33, "EU official: climate draft unacceptable (RTE)", (30.7, 36.9)),
    (34, "ATP backs $350m player-pay plan (Anadolu)", (7.7, 45.1)),
    (35, "Rio Tinto: $370m Panguna cleanup (Reuters)", (155.9, -6.3)),
    (36, "Iowa: 68 explosive barrels detonated (AP)", (-93.6, 41.9)),
    (37, "Hormuz: 4 ship attacks in 96 hours (UKMTO)", (56.3, 26.6)),
    (38, "Jakarta passes asset-forfeiture bill (Reuters)", (106.8, -6.2)),
    (39, "Cancer pill shrinks tumours 60.7% (Reuters)", (2.2, 41.4)),
    (40, "BepiColombo: Mercury after 8 years (ESA)", None),
]

DATE_CHECK = (
    "Left out as Thursday 19 Nov's news: the World Court's Myanmar "
    "ruling, Shenzhen's three-leader declaration, the Senegal migrant "
    "boat, Anthropic's $83bn IPO pricing, GTA VI's midnight launch, the "
    "$190.4m Van Gogh sale, the Senate's 48-51 Iran vote. Not yet: "
    "COP31's final text; BepiColombo's Mercury orbit entry (Saturday)."
)

FOOTER = ("Every story here happened, or was first reported, on Friday "
          "20 November 2026. Contested claims are attributed.")


# ---------------------------------------------------------------- header ---
def base_canvas():
    img = vgrad((W, H), (250, 245, 231), (233, 224, 200)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, W - 10, H - 10], radius=18,
                        outline=(178, 164, 128, 255), width=2)
    return img


def kicker(img):
    raised_panel(img, [MX, 18, W - MX, 42], NAVY, radius=8, dy=4,
                 shadow_alpha=80)
    d = ImageDraw.Draw(img)
    f = font(ARCH_B, 11)
    d.text((MX + 14, 24), "THE WORLD'S NEWS IN ONE PICTURE", font=f,
           fill=WHITE + (255,))
    right = "40 STORIES - 7 REGIONS - EVERY ONE FROM FRIDAY"
    d.text((W - MX - 14, 24), right, font=f, fill=(255, 213, 128, 255),
           anchor="ra")


def masthead(img):
    raised_panel(img, [MX, 48, W - MX, 136], PAPER, radius=14, dy=8)
    d = ImageDraw.Draw(img)
    f_mast = font(PLAYFAIR, 46)
    embossed(d, (512, 46), "THE WORLD IN ONE DAY", f_mast, NAVY,
             anchor="ma")
    d.rectangle([44, 103, 980, 106], fill=RED + (255,))
    d.rectangle([44, 106, 980, 108], fill=RED_D + (255,))
    f_date = font(PLAYFAIR, 23)
    d.text((512, 111), "FRIDAY 20 NOVEMBER 2026", font=f_date,
           fill=RED + (255,), anchor="ma")


def hook_band(img):
    """The hook: biggest story + biggest number, one red band."""
    raised_panel(img, [MX, 142, W - MX, 170], RED, radius=10, dy=6,
                 shadow_alpha=110)
    d = ImageDraw.Draw(img)
    s = ("110 MISSILES - 400 DRONES OVER KYIV   ·   "
         "300,000+ MOVED BEFORE CYCLONE AKVAN")
    sz = fit_size(d, s, ARCH_B, 17, CW - 40, min_size=12)
    centered(d, 512, 149, s, font(ARCH_B, sz), WHITE + (255,))


def timeline(img):
    raised_panel(img, [MX, 176, W - MX, 216], PAPER, radius=10, dy=6,
                 shadow_alpha=85)
    d = ImageDraw.Draw(img)
    slot_w = CW / 5
    f_lab = font(ARCH_B, 10)
    f_txt = font(ARCH_M, 10)
    for i, (lab, txt) in enumerate(TIMELINE):
        x = MX + i * slot_w + 12
        d.text((x, 181), lab, font=f_lab, fill=RED + (255,))
        for j, ln in enumerate(wrap(d, txt, f_txt, slot_w - 22)[:2]):
            d.text((x, 193 + j * 11), ln, font=f_txt, fill=INK + (255,))
        if i:
            d.line([MX + i * slot_w, 182, MX + i * slot_w, 210],
                   fill=(214, 206, 184, 255), width=1)


def numbers_strip(img):
    d = ImageDraw.Draw(img)
    d.text((MX + 2, 220), "THE DAY IN NUMBERS", font=font(ARCH_B, 10),
           fill=RED + (255,))
    col_w = CW / 6
    f_num = font(PLAYFAIR, 27)
    f_cap = font(ARCH_M, 9)
    for i, (num, cap) in enumerate(NUMBERS):
        x = MX + i * col_w + 2
        d.text((x, 230), num, font=f_num, fill=RED + (255,))
        for j, ln in enumerate(wrap(d, cap, f_cap, col_w - 14)[:2]):
            d.text((x, 262 + j * 10), ln, font=f_cap, fill=INK + (255,))


def region_line(img):
    d = ImageDraw.Draw(img)
    f = font(ARCH_B, 11)
    parts = []
    total = 0
    for name, n in REGION_LINE:
        s = "%s %d" % (name, n)
        parts.append((s, REGIONS[name]))
        total += tw(d, s, f)
    total += tw(d, "   ·   ", f) * (len(parts) - 1)
    x = (W - total) / 2
    for i, (s, col) in enumerate(parts):
        d.text((x, 284), s, font=f, fill=col + (255,))
        x += tw(d, s, f)
        if i < len(parts) - 1:
            d.text((x, 284), "   ·   ", font=f, fill=GREY + (255,))
            x += tw(d, "   ·   ", f)


# ----------------------------------------------------------------- scenes ---
def caption_band(img, box, text, tag):
    """Navy band at the bottom of a scene strip + certainty tag chip."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y1 - 16, x1, y1], fill=BAND + (235,))
    sz = fit_size(d, text, ARCH_B, 10, x1 - x0 - 16)
    centered(d, (x0 + x1) / 2, y1 - 13, text, font(ARCH_B, sz),
             WHITE + (255,))
    # tag chip, top right
    f_t = font(ARCH_B, 9)
    wdt = tw(d, tag.upper(), f_t) + 14
    d.rounded_rectangle([x1 - wdt - 6, y0 + 6, x1 - 6, y0 + 22], radius=7,
                        fill=(10, 16, 28, 215))
    d.text((x1 - wdt / 2 - 6, y0 + 9), tag.upper(), font=f_t,
           fill=(255, 226, 160, 255), anchor="ma")


def scene_frame(img, box, top, bottom):
    x0, y0, x1, y1 = box
    soft_shadow(img, box, radius=12, alpha=110, dy=8)
    scene = vgrad((x1 - x0, y1 - y0), top, bottom)
    mask = Image.new("L", scene.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, scene.size[0], scene.size[1]], radius=12,
                         fill=255)
    img.paste(scene.convert("RGBA"), (x0, y0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=12, outline=(16, 40, 66, 255), width=2)
    return d


def kyiv_scene(img, box):
    x0, y0, x1, y1 = box
    d = scene_frame(img, box, (24, 34, 64), (74, 92, 128))
    # river + bridge silhouette
    d.rectangle([x0, y1 - 34, x1, y1 - 16], fill=(16, 44, 74, 255))
    for bx in range(x0 + 30, x1 - 20, 64):
        d.rectangle([bx, y1 - 62, bx + 7, y1 - 30], fill=(10, 16, 30, 255))
    d.rectangle([x0 + 8, y1 - 64, x1 - 8, y1 - 58], fill=(10, 16, 30, 255))
    d.line([x0 + 30, y1 - 58, x0 + 94, y1 - 34], fill=(10, 16, 30, 255),
           width=3)
    d.line([x0 + 94, y1 - 58, x0 + 30, y1 - 34], fill=(10, 16, 30, 255),
           width=3)
    # missile streaks with glow heads
    for sx, sy, ex, ey in [(x0 + 36, y0 + 10, x0 + 84, y0 + 40),
                           (x0 + 120, y0 + 6, x0 + 160, y0 + 34),
                           (x0 + 210, y0 + 12, x0 + 244, y0 + 38),
                           (x0 + 268, y0 + 6, x0 + 296, y0 + 30)]:
        d.line([sx, sy, ex, ey], fill=(255, 196, 120, 255), width=3)
        d.ellipse([ex - 4, ey - 4, ex + 4, ey + 4], fill=(255, 226, 160, 255))
    # searchlight beams
    d.polygon([(x0 + 250, y1 - 16), (x0 + 196, y0 + 8), (x0 + 224, y0 + 8)],
              fill=(240, 240, 200, 60))
    caption_band(img, box, "KYIV - OVERNIGHT BARRAGE", "Officials' count")


def akvan_scene(img, box):
    x0, y0, x1, y1 = box
    d = scene_frame(img, box, (38, 74, 116), (122, 168, 205))
    cx, cy = x0 + 92, y0 + 36
    for r, a0, col, wd in [(44, 200, (196, 208, 220), 11),
                            (37, 30, (222, 230, 238), 10),
                            (30, 230, (178, 194, 210), 9),
                            (23, 60, (235, 240, 245), 8),
                            (16, 250, (190, 204, 218), 7)]:
        d.arc([cx - r, cy - r * 0.82, cx + r, cy + r * 0.82], a0, a0 + 235,
              fill=col + (255,), width=wd)
    d.ellipse([cx - 6, cy - 5, cx + 6, cy + 5], fill=(30, 54, 84, 255))
    for i in range(5):
        rx = x0 + 190 + i * 24
        d.line([rx, y0 + 8, rx - 6, y0 + 24], fill=(210, 226, 240, 200),
               width=3)
    for k, (wy, col) in enumerate([(50, (38, 106, 156)),
                                    (60, (30, 92, 140)),
                                    (70, (22, 76, 122))]):
        pts = []
        for x in range(x0, x1 + 8, 8):
            pts.append((x, y0 + wy + 4 * math.sin((x - x0) / 40.0 + k * 1.7)))
        pts += [(x1, y1 - 16), (x0, y1 - 16)]
        d.polygon(pts, fill=col + (255,))
        d.line(pts[:-2], fill=(168, 205, 232, 255), width=2)
    hx, hy = x0 + 232, y0 + 38
    d.polygon([(hx, hy), (hx + 16, hy - 12), (hx + 32, hy)],
              fill=RED + (255,))
    d.rectangle([hx + 3, hy, hx + 32, hy + 20], fill=(250, 238, 210, 255))
    d.rectangle([hx + 13, hy + 7, hx + 20, hy + 20], fill=(90, 60, 30, 255))
    caption_band(img, box, "GOPALPUR, ODISHA - LANDFALL", "Weather office")


def markets_scene(img, box):
    x0, y0, x1, y1 = box
    d = scene_frame(img, box, (14, 20, 36), (30, 40, 60))
    f = font(ARCH_B, 11)
    for lx, s in [(x0 + 16, "TAIPEI"), (x0 + 128, "SEOUL"),
                  (x0 + 238, "TOKYO")]:
        d.text((lx, y0 + 8), s, font=f, fill=(200, 210, 226, 255))
    # falling index line across the three markets
    pts = [(x0 + 14, y0 + 28), (x0 + 80, y0 + 36), (x0 + 130, y0 + 32),
           (x0 + 190, y0 + 50), (x0 + 240, y0 + 46), (x0 + 300, y0 + 62)]
    d.line(pts, fill=(255, 92, 72, 255), width=4)
    for px, py in pts:
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(255, 150, 130, 255))
    caption_band(img, box, "TAIPEI - SEOUL - TOKYO - CLOSING PRICES",
                 "Closing prices")


SCENES = {1: kyiv_scene, 2: akvan_scene, 3: markets_scene}


def lead_card(img, card, box):
    no, place, region, topic, head, deck, tag, label, _pin = card
    x0, y0, x1, y1 = box
    raised_panel(img, box, PAPER, radius=12, dy=9)
    col = REGIONS[region]
    scene_box = [x0 + 8, y0 + 8, x1 - 8, y0 + 92]
    SCENES[no](img, scene_box)
    d = ImageDraw.Draw(img)
    # region accent rule under the scene
    d.rectangle([x0 + 8, y0 + 92, x1 - 8, y0 + 96], fill=col + (255,))
    # data label, bold, under the band
    f_lab = font(ARCH_B, 12)
    lsz = fit_size(d, label, ARCH_B, 12, x1 - x0 - 28)
    d.text((x0 + 14, y0 + 100), label, font=font(ARCH_B, lsz),
           fill=col + (255,))
    f_meta = font(ARCH_B, 11)
    meta = "%d %s - %s - %s" % (no, place, region, topic)
    sz = fit_size(d, meta, ARCH_B, 11, x1 - x0 - 28)
    d.text((x0 + 14, y0 + 117), meta, font=font(ARCH_B, sz),
           fill=RED + (255,))
    f_h = font(PLAYFAIR, 20)
    y = y0 + 133
    for ln in wrap(d, head, f_h, x1 - x0 - 28)[:2]:
        d.text((x0 + 14, y), ln, font=f_h, fill=INK + (255,))
        y += 23
    f_deck = font(ARCH_M, 12)
    y += 1
    for ln in wrap(d, deck, f_deck, x1 - x0 - 28)[:3]:
        d.text((x0 + 14, y), ln, font=f_deck, fill=(40, 44, 52, 255))
        y += 14


# ----------------------------------------------------------------- minis ---
def mini_card(img, card, box):
    no, place, region, head, deck, tag, label, _pin = card
    x0, y0, x1, y1 = box
    raised_panel(img, box, PAPER, radius=10, dy=7, shadow_alpha=95)
    col = REGIONS[region]
    d = ImageDraw.Draw(img)
    # data strip: tinted band with the data label + certainty chip
    tint = tuple(int(c + (255 - c) * 0.82) for c in col)
    d.rounded_rectangle([x0 + 6, y0 + 6, x1 - 6, y0 + 30], radius=7,
                        fill=tint + (255,))
    d.rectangle([x0 + 6, y0 + 22, x1 - 6, y0 + 30], fill=tint + (255,))
    sz = fit_size(d, label, ARCH_B, 11, x1 - x0 - 96)
    d.text((x0 + 12, y0 + 12), label, font=font(ARCH_B, sz),
           fill=(24, 28, 38, 255))
    f_t = font(ARCH_B, 8)
    wdt = tw(d, tag, f_t) + 10
    d.rounded_rectangle([x1 - wdt - 9, y0 + 11, x1 - 9, y0 + 25], radius=6,
                        fill=BAND + (255,))
    d.text((x1 - wdt / 2 - 9, y0 + 14), tag, font=f_t,
           fill=(255, 226, 160, 255), anchor="ma")
    # place line, region-coloured
    f_p = font(ARCH_B, 11)
    d.text((x0 + 12, y0 + 36), "%d  %s - %s" % (no, place, region),
           font=f_p, fill=col + (255,))
    # headline
    f_h = font(ARCH_B, 14)
    y = y0 + 52
    for ln in wrap(d, head, f_h, x1 - x0 - 24)[:2]:
        d.text((x0 + 12, y), ln, font=f_h, fill=INK + (255,))
        y += 17
    # deck
    f_deck = font(ARCH_M, 12)
    y += 2
    for ln in wrap(d, deck, f_deck, x1 - x0 - 24)[:3]:
        d.text((x0 + 12, y), ln, font=f_deck, fill=(40, 44, 52, 255))
        y += 14


# ------------------------------------------------------------------- map ---
def project(lon, lat, box):
    x0, y0, x1, y1 = box
    x = x0 + (lon + 180.0) / 360.0 * (x1 - x0)
    y = y0 + (80.0 - lat) / 135.0 * (y1 - y0)
    return x, y


def pin3d(img, cx, cy, num, col):
    d = ImageDraw.Draw(img)
    soft_shadow(img, [cx - 8, cy + 6, cx + 8, cy + 14], radius=5, blur=4,
                alpha=80, dy=1)
    d = ImageDraw.Draw(img)
    d.polygon([(cx - 4, cy + 2), (cx + 4, cy + 2), (cx, cy + 13)],
              fill=tuple(max(0, c - 40) for c in col) + (255,))
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=col + (255,))
    d.ellipse([cx - 6, cy - 7, cx, cy - 2],
              fill=tuple(min(255, c + 70) for c in col) + (255,))
    d.text((cx, cy - 6), str(num), font=font(ARCH_B, 10),
           fill=WHITE + (255,), anchor="ma")


def map_panel(img, box):
    x0, y0, x1, y1 = box
    raised_panel(img, box, (228, 238, 246), radius=12, dy=8)
    d = ImageDraw.Draw(img)
    d.text((x0 + 12, y0 + 8), "WHERE IT HAPPENED", font=font(ARCH_B, 12),
           fill=NAVY + (255,))
    mbox = [x0 + 10, y0 + 28, x1 - 10, y1 - 30]
    # real polygons: darker offset copy below, lighter face above (3D lift)
    for _name, rings in WORLD.items():
        for ring in rings.split("|"):
            pts = []
            for pair in ring.split(","):
                lon, lat = pair.split(":")
                pts.append(project(float(lon), float(lat), mbox))
            if len(pts) < 3:
                continue
            off = [(x, y + 3) for x, y in pts]
            d.polygon(off, fill=(148, 168, 150, 255))
            d.polygon(pts, fill=(196, 208, 178, 255))
    # brief dots
    for no, _txt, pin in BRIEFS:
        if pin is None:
            continue
        px, py = project(pin[0], pin[1], mbox)
        d.ellipse([px - 2.5, py - 2.5, px + 2.5, py + 2.5],
                  fill=(90, 100, 110, 255))
    # numbered card pins
    for card in LEADS + MINIS:
        no, region, pin = card[0], card[2], card[-1]
        px, py = project(pin[0], pin[1], mbox)
        pin3d(img, px, py, no, REGIONS[region])
    d = ImageDraw.Draw(img)
    # exit arrow for the space brief (40), label kept inside the panel
    ex, ey = project(155.9, -6.3, mbox)
    f_m = font(ARCH_B, 9)
    mtxt = "40 -> to Mercury"
    tx = x1 - 12 - tw(d, mtxt, f_m)
    d.line([ex + 12, ey + 10, tx - 6, ey + 12], fill=RED + (255,),
           width=2)
    d.polygon([(tx - 6, ey + 12), (tx - 14, ey + 8), (tx - 13, ey + 16)],
              fill=RED + (255,))
    d.text((tx, ey + 7), mtxt, font=f_m, fill=RED + (255,))
    d.text((x0 + 12, y1 - 22),
           "Numbered pins = the 13 pictured stories - small dots = "
           "the briefs", font=font(ARCH_M, 9), fill=GREY + (255,))


def also_on(img, box):
    x0, y0, x1, y1 = box
    raised_panel(img, box, PAPER, radius=12, dy=8)
    d = ImageDraw.Draw(img)
    d.text((x0 + 12, y0 + 8), "ALSO ON FRIDAY 20 NOVEMBER - 27 MORE STORIES",
           font=font(ARCH_B, 11), fill=NAVY + (255,))
    col_w = (x1 - x0 - 24) / 2
    f_n = font(ARCH_B, 10)
    f_b = font(ARCH_M, 10)
    per_col = 14
    for i, (no, txt, _pin) in enumerate(BRIEFS):
        c = 0 if i < per_col else 1
        r = i if i < per_col else i - per_col
        x = x0 + 12 + c * col_w
        y = y0 + 27 + r * 9.9
        ns = "%d " % no
        d.text((x, y), ns, font=f_n, fill=RED + (255,))
        body = txt
        maxw = col_w - tw(d, ns, f_n) - 4
        while tw(d, body, f_b) > maxw and len(body) > 10:
            body = body[:-1]
        d.text((x + tw(d, ns, f_n), y), body, font=f_b, fill=INK + (255,))


def date_check(img):
    box = [MX, 974, W - MX, 1016]
    soft_shadow(img, box, radius=10, alpha=90, dy=6)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=10, fill=(253, 244, 238, 255),
                        outline=RED + (255,), width=2)
    f = font(ARCH_M, 10)
    f_b = font(ARCH_B, 10)
    x = MX + 12
    y = 979
    pre = "DATE CHECK  "
    d.text((x, y), pre, font=f_b, fill=RED + (255,))
    # first line fills the space after the label; the rest wraps full width
    words = DATE_CHECK.split()
    line1, rest = "", []
    for i, wd in enumerate(words):
        t = (line1 + " " + wd).strip()
        if tw(d, t, f) <= CW - 24 - tw(d, pre, f_b) or not line1:
            line1 = t
        else:
            rest = words[i:]
            break
    d.text((x + tw(d, pre, f_b), y), line1, font=f, fill=INK + (255,))
    for ln in wrap(d, " ".join(rest), f, CW - 24)[:1]:
        y += 12
        d.text((MX + 12, y), ln, font=f, fill=INK + (255,))
    d.text((MX + 12, 1003), FOOTER + "  Sources named beside each story "
           "- original drawings.", font=font(ARCH_M, 9),
           fill=GREY + (255,))


# ------------------------------------------------------------------ main ---
def build():
    img = base_canvas()
    kicker(img)
    masthead(img)
    hook_band(img)
    timeline(img)
    numbers_strip(img)
    region_line(img)
    lead_w = 317
    for i, card in enumerate(LEADS):
        x = MX + i * (lead_w + 12)
        lead_card(img, card, [x, 298, x + lead_w, 522])
    mini_w = (CW - 4 * 14) / 5
    for i, card in enumerate(MINIS):
        c, r = i % 5, i // 5
        x = MX + c * (mini_w + 14)
        y = 528 + r * 141
        mini_card(img, card, [x, y, x + mini_w, y + 131])
    map_panel(img, [MX, 806, 520, 968])
    also_on(img, [532, 806, W - MX, 968])
    date_check(img)
    return img.convert("RGB")


def save_final(img):
    """Palette-compress toward the 110-160 KB tie-break band."""
    import io
    best = None
    for colors in (256, 224, 192, 160, 128, 96):
        q = img.quantize(colors=colors, method=Image.FASTOCTREE)
        buf = io.BytesIO()
        q.save(buf, format="PNG", optimize=True)
        size = buf.tell()
        if best is None or size < best[0]:
            best = (size, buf.getvalue())
        if size <= 160_000:
            best = (size, buf.getvalue())
            break
    out = os.path.join(HERE, "entry.png")
    with open(out, "wb") as fh:
        fh.write(best[1])
    print("wrote entry.png", best[0], "bytes")


def main():
    save_final(build())


if __name__ == "__main__":
    main()
