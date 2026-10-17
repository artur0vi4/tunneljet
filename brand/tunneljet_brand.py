#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tunneljet brand generator.
Single source of truth: geometry defined here emits BOTH Android vector XMLs
and PNG previews (supersampled, analytic masks).
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
# Если скрипт лежит в <repo>/brand/ — репозиторий определяется автоматически;
# иначе задайте TJ_REPO. TJ_OUT — куда писать превью.
ROOT = os.environ.get("TJ_REPO") or (os.path.dirname(_HERE) if os.path.basename(_HERE) == "brand" else _HERE)
RES = os.path.join(ROOT, "app/src/main/res")
PREV = os.environ.get("TJ_OUT", os.path.join(_HERE, "out"))
os.makedirs(PREV, exist_ok=True)

# ---------------- geometry ----------------
PLANE = [(17.5, 0.0), (-16.0, -12.5), (-4.6, -0.8), (-16.0, 12.5)]  # нос, хвост-верх, выемка, хвост-низ
PLANE_SCALE = 1.06
ANG = -28.0  # поворот самолёта (нос вверх-вправо в y-down координатах)

def rot(x, y, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return (x * c - y * s, x * s + y * c)

def plane_pts(cx, cy, scale, deg=ANG):
    return [(cx + rot(x * scale, y * scale, deg)[0], cy + rot(x * scale, y * scale, deg)[1]) for x, y in PLANE]

def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s else "0"

def circle_path(cx, cy, r, sweep):
    return (f"M {f(cx + r)},{f(cy)} A {f(r)},{f(r)} 0 1,{sweep} {f(cx - r)},{f(cy)} "
            f"A {f(r)},{f(r)} 0 1,{sweep} {f(cx + r)},{f(cy)} Z")

def donut(cx, cy, r_out, r_in):
    # outer CCW + inner CW => hole with nonzero winding (API21-safe, no fillType needed)
    return circle_path(cx, cy, r_out, 0) + " " + circle_path(cx, cy, r_in, 1)

def path_M(pts, close=True):
    d = "M " + " L ".join(f"{f(x)},{f(y)}" for x, y in pts)
    return d + (" Z" if close else "")

def arc_dash(cx, cy, r, a0, a1):
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    large = 1 if abs(a1 - a0) > 180 else 0
    sweep = 1 if a1 > a0 else 0
    return f"M {f(x0)},{f(y0)} A {f(r)},{f(r)} 0 {large},{sweep} {f(x1)},{f(y1)}"

# ---------------- XML emitters ----------------
GRAD = ('<aapt:attr name="android:fillColor">\n'
        '                <gradient android:type="linear" android:startX="{x0}" android:startY="{y0}" '
        'android:endX="{x1}" android:endY="{y1}" android:startColor="{c0}" android:endColor="{c1}"/>\n'
        '            </aapt:attr>')

def vec108_header():
    return ('<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
            '    xmlns:aapt="http://schemas.android.com/aapt"\n'
            '    android:width="108dp" android:height="108dp"\n'
            '    android:viewportWidth="108" android:viewportHeight="108">\n')

def write_launcher_fg():
    p = plane_pts(54, 54, PLANE_SCALE)
    nose, ttop, notch, tbot = p
    gd_top = GRAD.format(x0=f(nose[0]), y0=f(nose[1]), x1=f(ttop[0]), y1=f(ttop[1]),
                         c0="#66D0FF", c1="#2496DE")
    gd_bot = GRAD.format(x0=f(nose[0]), y0=f(nose[1]), x1=f(tbot[0]), y1=f(tbot[1]),
                         c0="#45B7F2", c1="#1A6699")
    xml = vec108_header() + f'''    <!-- tunnel ring (outer) -->
    <path android:pathData="{donut(54, 54, 30.0, 24.2)}">
        {GRAD.format(x0="26", y0="26", x1="82", y1="82", c0="#36A9EC", c1="#1D6FA8")}
    </path>
    <!-- tunnel ring (inner, receding) -->
    <path android:pathData="{donut(54, 54, 19.4, 15.2)}">
        {GRAD.format(x0="36", y0="36", x1="72", y1="72", c0="#2492D6", c1="#16547F")}
    </path>
    <!-- paper plane: top facet -->
    <path android:pathData="{path_M([nose, ttop, notch])}">
        {gd_top}
    </path>
    <!-- paper plane: bottom facet -->
    <path android:pathData="{path_M([nose, notch, tbot])}">
        {gd_bot}
    </path>
</vector>
'''
    open(f"{RES}/drawable/ic_launcher_fg.xml", "w").write(xml)

def write_launcher_bg():
    xml = vec108_header() + '''    <path android:pathData="M0,0h108v108h-108z">
        <aapt:attr name="android:fillColor">
            <gradient android:type="radial" android:centerX="54" android:centerY="54"
                android:gradientRadius="76" android:startColor="#22354A" android:endColor="#0B1016"/>
        </aapt:attr>
    </path>
</vector>
'''
    open(f"{RES}/drawable/ic_launcher_bg.xml", "w").write(xml)

def write_mono():
    xml = vec108_header() + f'''    <!-- themed-icon layer: ring + plane, flat white -->
    <path android:fillColor="#FFFFFF" android:pathData="{donut(54, 54, 25.5, 19.8)}"/>
    <path android:fillColor="#FFFFFF" android:pathData="{path_M(plane_pts(54, 54, 0.95))}"/>
</vector>
'''
    open(f"{RES}/drawable/ic_launcher_mono.xml", "w").write(xml)

def write_glyph():
    """24dp white glyph: ring + plane (QS tile, notification)."""
    body = f'''    <path
        android:fillColor="#FFFFFFFF"
        android:pathData="{donut(12, 12, 10.0, 7.7)}"/>
    <path
        android:fillColor="#FFFFFFFF"
        android:pathData="{path_M(plane_pts(12, 12, 0.36))}"/>'''
    for name in ("ic_qs_proxy_t.xml", "ic_notification.xml"):
        xml = ('<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
               '    android:width="24dp" android:height="24dp"\n'
               '    android:viewportWidth="24" android:viewportHeight="24">\n'
               + body + "\n</vector>\n")
        open(f"{RES}/drawable/{name}", "w").write(xml)

def write_adaptive():
    mono = '\n    <monochrome android:drawable="@drawable/ic_launcher_mono"/>'
    for d in ("mipmap-anydpi", "mipmap-anydpi-v26"):
        os.makedirs(f"{RES}/{d}", exist_ok=True)
        xml = ('<?xml version="1.0" encoding="utf-8"?>\n'
               '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
               '    <background android:drawable="@drawable/ic_launcher_bg"/>\n'
               '    <foreground android:drawable="@drawable/ic_launcher_fg"/>' + mono + "\n</adaptive-icon>\n")
        for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
            open(f"{RES}/{d}/{name}", "w").write(xml)

# ---------------- PIL rendering (previews) ----------------
def mask_circle(size, cx, cy, r, ss):
    im = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(im).ellipse([(cx - r) * ss, (cy - r) * ss, (cx + r) * ss, (cy + r) * ss], fill=255)
    return np.asarray(im, dtype=np.float32) / 255.0

def mask_poly(size, pts, ss):
    im = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im, dtype=np.float32) / 255.0

def lerp_colors(c0, c1, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t

def radial_layer(w, h, c0, c1):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - w / 2) ** 2 + (yy - h / 2) ** 2) / (min(w, h) * 0.7071)
    return lerp_colors(c0, c1, d)

def linear_layer(w, h, c0, c1, p0, p1):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    t = ((xx - p0[0]) * dx + (yy - p0[1]) * dy) / (dx * dx + dy * dy)
    return lerp_colors(c0, c1, t)

def compose(canvas, layer, mask):
    m = np.clip(mask, 0, 1)[..., None]
    return canvas * (1 - m) + layer * m

def render_fg(size, ss=4, variant_b=False):
    sc = size / 108.0          # 108-пространство -> пиксели финального размера
    W = size * ss
    canvas = np.zeros((W, W, 3), np.float32)
    cover = np.zeros((W, W), np.float32)

    def mc(cx, cy, r):
        return mask_circle(size, cx * sc, cy * sc, r * sc, ss)

    def mp(pts):
        return mask_poly(size, [(x * sc, y * sc) for x, y in pts], ss)

    if variant_b:
        la2 = linear_layer(W, W, (0x36, 0xA9, 0xEC), (0x1D, 0x6F, 0xA8),
                           (28 * sc * ss, 28 * sc * ss), (80 * sc * ss, 80 * sc * ss))
        ma2 = mc(54, 54, 26.5) - mc(54, 54, 21.8)
        canvas = compose(canvas, la2, ma2)
        cover = np.maximum(cover, np.clip(ma2, 0, 1))
    else:
        la = linear_layer(W, W, (0x36, 0xA9, 0xEC), (0x1D, 0x6F, 0xA8),
                          (26 * sc * ss, 26 * sc * ss), (82 * sc * ss, 82 * sc * ss))
        ma = mc(54, 54, 30.0) - mc(54, 54, 24.2)
        canvas = compose(canvas, la, ma)
        cover = np.maximum(cover, np.clip(ma, 0, 1))
        lb = linear_layer(W, W, (0x24, 0x92, 0xD6), (0x16, 0x54, 0x7F),
                          (36 * sc * ss, 36 * sc * ss), (72 * sc * ss, 72 * sc * ss))
        mb = mc(54, 54, 19.4) - mc(54, 54, 15.2)
        canvas = compose(canvas, lb, mb)
        cover = np.maximum(cover, np.clip(mb, 0, 1))
    if variant_b:
        # speed dashes behind the tail
        for (r, a0, a1) in ((30.5, 120, 150), (30.5, 160, 174)):
            im = Image.new("L", (W, W), 0)
            ImageDraw.Draw(im).arc([(54 - r) * sc * ss, (54 - r) * sc * ss, (54 + r) * sc * ss, (54 + r) * sc * ss],
                                   start=a0, end=a1, fill=255, width=max(1, int(4.2 * sc * ss)))
            md = np.asarray(im, np.float32) / 255.0
            ld = np.tile(np.array((0x7E, 0xB8, 0xE0), np.float32), (W, W, 1))
            canvas = compose(canvas, ld, md)
            cover = np.maximum(cover, np.clip(md, 0, 1))
    # plane
    p = plane_pts(54, 54, PLANE_SCALE)
    nose, ttop, notch, tbot = p
    mt = mp([nose, ttop, notch])
    lt = linear_layer(W, W, (0x66, 0xD0, 0xFF), (0x24, 0x96, 0xDE),
                      (nose[0] * sc * ss, nose[1] * sc * ss), (ttop[0] * sc * ss, ttop[1] * sc * ss))
    canvas = compose(canvas, lt, mt)
    cover = np.maximum(cover, np.clip(mt, 0, 1))
    mbf = mp([nose, notch, tbot])
    lbf = linear_layer(W, W, (0x45, 0xB7, 0xF2), (0x1A, 0x66, 0x99),
                       (nose[0] * sc * ss, nose[1] * sc * ss), (tbot[0] * sc * ss, tbot[1] * sc * ss))
    canvas = compose(canvas, lbf, mbf)
    cover = np.maximum(cover, np.clip(mbf, 0, 1))
    rgba = np.dstack([np.clip(canvas / 255.0, 0, 1), np.clip(cover, 0, 1)[..., None]])
    out = Image.fromarray((rgba * 255).astype(np.uint8))
    return out.resize((size, size), Image.LANCZOS)

def render_bg(size, ss=2):
    arr = radial_layer(size * ss, size * ss, (0x22, 0x35, 0x4A), (0x0B, 0x10, 0x16))
    return Image.fromarray(arr.astype(np.uint8)).resize((size, size), Image.LANCZOS)

def render_icon(size, shape="squircle", variant_b=False):
    fg = render_fg(size, variant_b=variant_b)
    base = render_bg(size).convert("RGBA")
    base.alpha_composite(fg)
    mask = Image.new("L", (size, size), 255)
    if shape == "squircle":
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.27), fill=255)
    elif shape == "circle":
        ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(base, (0, 0), mask)
    return out

def render_glyph(size, ss=4, color=(255, 255, 255)):
    k = size / 24.0
    im = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    col = color + (255,)
    ImageDraw.Draw(im).ellipse([(12 - 10) * k * ss, (12 - 10) * k * ss, (12 + 10) * k * ss, (12 + 10) * k * ss], fill=col)
    hole = Image.new("L", im.size, 0)
    ImageDraw.Draw(hole).ellipse([(12 - 7.7) * k * ss, (12 - 7.7) * k * ss, (12 + 7.7) * k * ss, (12 + 7.7) * k * ss], fill=255)
    im.paste((0, 0, 0, 0), (0, 0), hole)
    pts = plane_pts(12, 12, 0.36)
    ImageDraw.Draw(im).polygon([(x * k * ss, y * k * ss) for x, y in pts], fill=col)
    return im.resize((size, size), Image.LANCZOS)

# ---------------- previews ----------------
FDIR = "/usr/share/fonts/truetype/dejavu"
def font(name, sz):
    return ImageFont.truetype(f"{FDIR}/{name}", sz)

def preview_sheet():
    W, H = 1500, 1000
    bg = Image.new("RGB", (W, H), (14, 17, 22))
    dr = ImageDraw.Draw(bg)
    dr.text((50, 36), "Tunneljet", font=font("DejaVuSans-Bold.ttf", 56), fill=(240, 244, 248))
    dr.text((50, 106), "Новая айдентика форка tg-ws-proxy-android", font=font("DejaVuSans.ttf", 26), fill=(140, 152, 166))

    sq = render_icon(460, "squircle"); bg.paste(sq, (50, 170), sq)
    ci = render_icon(460, "circle"); bg.paste(ci, (560, 170), ci)
    alt = render_icon(460, "circle", variant_b=True); bg.paste(alt, (1070, 170), alt)
    dr.text((50, 646), "Вариант A: туннель (2 кольца)", font=font("DejaVuSans.ttf", 22), fill=(140, 152, 166))
    dr.text((560, 646), "Круглый лончер", font=font("DejaVuSans.ttf", 22), fill=(140, 152, 166))
    dr.text((1070, 646), "Вариант B: кольцо + скорость", font=font("DejaVuSans.ttf", 22), fill=(140, 152, 166))

    for i, s in enumerate((192, 96, 48)):
        ic = render_icon(s, "circle")
        bg.paste(ic, (50 + i * 220, 700), ic)
    dr.text((50, 920), "48 / 96 / 192 px — читаемость в малом размере", font=font("DejaVuSans.ttf", 22), fill=(140, 152, 166))

    tile = Image.new("RGBA", (230, 230), (28, 27, 31, 255))
    ImageDraw.Draw(tile).rounded_rectangle([0, 0, 229, 229], radius=48, outline=(70, 74, 82, 255), width=2)
    g = render_glyph(96)
    tile.alpha_composite(g, (67, 40))
    ImageDraw.Draw(tile).text((115, 176), "Вкл", font=font("DejaVuSans.ttf", 26), fill=(230, 232, 236), anchor="mm")
    bg.paste(tile, (760, 690), tile)

    strip = Image.new("RGBA", (460, 130), (28, 27, 31, 255))
    ImageDraw.Draw(strip).rounded_rectangle([0, 0, 459, 129], radius=26, outline=(70, 74, 82, 255), width=2)
    strip.alpha_composite(render_glyph(44), (24, 24))
    ImageDraw.Draw(strip).text((88, 34), "Tunneljet", font=font("DejaVuSans-Bold.ttf", 24), fill=(235, 238, 242))
    ImageDraw.Draw(strip).text((88, 72), "Прокси работает · 10.2 МБ/с", font=font("DejaVuSans.ttf", 20), fill=(150, 158, 168))
    bg.paste(strip, (1030, 740), strip)

    bg.save(f"{PREV}/preview-sheet.png")

def social_card():
    W, H = 1200, 630
    bg = render_bg(H).resize((W, H), Image.LANCZOS).convert("RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([720, -280, 1560, 520], fill=(46, 130, 190, 42))
    bg.alpha_composite(glow)
    ic = render_icon(360, "squircle")
    bg.alpha_composite(ic, (80, 135))
    dr = ImageDraw.Draw(bg)
    dr.text((490, 190), "Tunneljet", font=font("DejaVuSans-Bold.ttf", 92), fill=(245, 248, 252))
    dr.text((492, 318), "Быстрый MTProto-туннель для Telegram", font=font("DejaVuSans.ttf", 31), fill=(126, 196, 240))
    dr.text((492, 392), "форк tg-ws-proxy-android · WebSocket · Cloudflare",
            font=font("DejaVuSans.ttf", 24), fill=(140, 152, 166))
    bg.convert("RGB").save(f"{PREV}/social-preview.png")

if __name__ == "__main__":
    write_launcher_fg()
    write_launcher_bg()
    write_mono()
    write_glyph()
    write_adaptive()
    preview_sheet()
    social_card()
    render_icon(512, "circle").save(f"{PREV}/icon-512-circle.png")
    render_icon(512, "squircle").save(f"{PREV}/icon-512-squircle.png")
    print("OK: XML ->", RES, "| previews ->", PREV)
