#!/usr/bin/env python3
"""Convert the hidden display's raw RGBA frame (+ w h stride meta) to a PNG.

Plain path (used by `shot`):
    frame_to_png.py RAW META OUT
    -> full frame, RGB, no overlay (unchanged behaviour).

Zoom path (the "look closer" trick, used by `zoom` / `grid`):
    frame_to_png.py RAW META OUT [--crop CX CY R] [--scale S] [--grid STEP]
    --crop CX CY R : keep a 2R-wide box around (CX,CY) in ORIGINAL pixels.
    --scale S      : blow the kept box up S times (nearest, so pixels stay crisp).
    --grid STEP    : draw lines every STEP ORIGINAL pixels and label each line
                     with its ORIGINAL coordinate — so the number you read off
                     the picture IS the number you pass to `tap`. A crosshair
                     marks (CX,CY) when a crop is given.

The label coordinates are always in the original, un-scaled display space, so a
zoomed-in look never lies about where to tap.
"""
import argparse
from PIL import Image, ImageDraw, ImageFont


def _font(px):
    try:
        return ImageFont.load_default(size=px)
    except TypeError:  # older Pillow: no size arg
        return ImageFont.load_default()


def _label(draw, x, y, s, font):
    # white text on a black box so it reads on any background
    try:
        l, t, r, b = draw.textbbox((0, 0), s, font=font)
        w, h = r - l, b - t
    except Exception:
        w, h = 8 * len(s), 11
    draw.rectangle((x, y, x + w + 4, y + h + 4), fill=(0, 0, 0))
    draw.text((x + 2, y + 2), s, fill=(255, 255, 255), font=font)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("meta")
    ap.add_argument("out")
    ap.add_argument("--crop", nargs=3, type=int, metavar=("CX", "CY", "R"))
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--grid", type=int, default=0)
    a = ap.parse_args()

    w, h, stride = [int(x) for x in open(a.meta).read().split()]
    raw = open(a.raw, "rb").read()
    img = Image.frombuffer("RGBA", (stride // 4, h), raw, "raw", "RGBA", 0, 1).crop((0, 0, w, h)).convert("RGB")

    # No overlay asked for -> original behaviour, byte-for-byte.
    if not a.crop and a.grid <= 0 and a.scale == 1.0:
        img.save(a.out)
        return

    # crop origin in original pixels
    ox, oy = 0, 0
    cx = cy = None
    if a.crop:
        cx, cy, r = a.crop
        x0, y0 = max(0, cx - r), max(0, cy - r)
        x1, y1 = min(w, cx + r), min(h, cy + r)
        img = img.crop((x0, y0, x1, y1))
        ox, oy = x0, y0

    s = a.scale if a.scale and a.scale > 0 else 1.0
    if s != 1.0:
        img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.NEAREST)

    if a.grid > 0 or a.crop:
        draw = ImageDraw.Draw(img)
        font = _font(max(11, int(11 * min(s, 3))))
        line = (255, 0, 128)
        step = a.grid if a.grid > 0 else 0
        if step > 0:
            # keep the fine mesh but label only every Nth line, so numbers stay
            # readable (>=34px apart on screen) no matter how wide the zoom is.
            import math
            every = max(1, math.ceil(34.0 / max(1.0, step * s)))
            # vertical lines at each original-x multiple of step inside the view
            xo = ((ox // step) + 1) * step
            while xo < ox + img.width / s:
                px = int((xo - ox) * s)
                draw.line((px, 0, px, img.height), fill=line, width=1)
                if (xo // step) % every == 0:
                    _label(draw, px + 1, 1, str(xo), font)
                xo += step
            yo = ((oy // step) + 1) * step
            while yo < oy + img.height / s:
                py = int((yo - oy) * s)
                draw.line((0, py, img.width, py), fill=line, width=1)
                if (yo // step) % every == 0:
                    _label(draw, 1, py + 1, str(yo), font)
                yo += step
        if cx is not None:
            # crosshair at the point we zoomed on
            px, py = int((cx - ox) * s), int((cy - oy) * s)
            draw.line((px - 12, py, px + 12, py), fill=(0, 220, 255), width=2)
            draw.line((px, py - 12, px, py + 12), fill=(0, 220, 255), width=2)

    img.save(a.out)


if __name__ == "__main__":
    main()
