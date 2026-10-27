#!/usr/bin/env python3
"""Find a button-photo (template) inside a screen frame. Prints: <cx> <cy> <conf>

    match.py FRAME.png TEMPLATE.png [--near CX CY R]

conf is 0..1 (normalized cross-correlation). --near restricts the search to a
window around (CX,CY) so we prefer the button where it was taught and don't get
fooled by an identical-looking button elsewhere. Uses OpenCV if present, else a
NumPy fallback.
"""
import sys, argparse
import numpy as np
from PIL import Image


def load(p):
    return np.asarray(Image.open(p).convert("RGB"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frame")
    ap.add_argument("template")
    ap.add_argument("--near", nargs=3, type=int, metavar=("CX", "CY", "R"))
    a = ap.parse_args()

    frame = load(a.frame)
    templ = load(a.template)
    fh, fw = frame.shape[:2]
    th, tw = templ.shape[:2]

    x0, y0, x1, y1 = 0, 0, fw, fh
    if a.near:
        cx, cy, r = a.near
        x0 = max(0, cx - tw // 2 - r); y0 = max(0, cy - th // 2 - r)
        x1 = min(fw, cx + tw // 2 + r); y1 = min(fh, cy + th // 2 + r)
    sub = frame[y0:y1, x0:x1]
    if sub.shape[0] < th or sub.shape[1] < tw:      # search window too small; use whole frame
        sub, x0, y0 = frame, 0, 0

    try:
        import cv2
        res = cv2.matchTemplate(sub, templ, cv2.TM_CCOEFF_NORMED)
        _, maxv, _, maxloc = cv2.minMaxLoc(res)
        mx = x0 + maxloc[0] + tw // 2; my = y0 + maxloc[1] + th // 2; conf = float(maxv)
    except Exception:
        t = templ.astype(np.float32); t -= t.mean(); tnorm = np.sqrt((t * t).sum()) + 1e-6
        sh, sw = sub.shape[:2]; best = (-1.0, 0, 0)
        for yy in range(0, sh - th + 1, 4):
            for xx in range(0, sw - tw + 1, 4):
                p = sub[yy:yy + th, xx:xx + tw].astype(np.float32); p -= p.mean()
                v = float((p * t).sum() / ((np.sqrt((p * p).sum()) + 1e-6) * tnorm))
                if v > best[0]: best = (v, xx, yy)
        conf, xx, yy = best; mx = x0 + xx + tw // 2; my = y0 + yy + th // 2

    print(f"{mx} {my} {conf:.3f}")


if __name__ == "__main__":
    main()
