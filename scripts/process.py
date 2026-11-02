"""Crop, deskew and clean document photos.

usage: python process.py SRC_DIR DST_DIR
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps


def load(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def order(pts):
    s = pts.sum(1)
    d = np.diff(pts, axis=1).ravel()
    return np.array([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]], dtype=np.float32)


def find_page(img):
    """Return 4 corner points of the paper sheet, or None."""
    h, w = img.shape[:2]
    k = 1000 / max(h, w)
    small = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    area = cv2.contourArea(c) / (small.shape[0] * small.shape[1])
    if area < 0.3:
        return None
    hull = cv2.convexHull(c)
    for eps in (0.01, 0.02, 0.03, 0.05):
        approx = cv2.approxPolyDP(hull, eps * cv2.arcLength(hull, True), True)
        if len(approx) == 4:
            return order(approx.reshape(4, 2).astype(np.float32) / k), area
    box = cv2.boxPoints(cv2.minAreaRect(hull))
    return order(box.astype(np.float32) / k), area


def warp(img, quad):
    tl, tr, br, bl = quad
    w = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    h = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
    m = cv2.getPerspectiveTransform(quad, dst)
    return cv2.warpPerspective(img, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def whiten_outside(img):
    """Paint dark, low-saturation regions touching the border (table/background) white."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    dark = ((hsv[..., 2] < 110) & (hsv[..., 1] < 80)).astype(np.uint8)
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(dark, 8)
    h, w = dark.shape
    mask = np.zeros_like(dark)
    for i in range(1, n):
        x, y, bw, bh, a = stats[i]
        touches = x == 0 or y == 0 or x + bw == w or y + bh == h
        if touches and a > 0.002 * h * w:
            mask[lab == i] = 1
    mask = cv2.dilate(mask, np.ones((15, 15), np.uint8))
    img = img.copy()
    img[mask > 0] = 255
    return img


def flatten(img):
    """Remove shadows/uneven lighting, keep ink colour."""
    out = []
    for ch in cv2.split(img):
        bg = cv2.dilate(ch, np.ones((9, 9), np.uint8))
        bg = cv2.medianBlur(bg, 41)
        norm = cv2.divide(ch, bg, scale=255)
        out.append(norm)
    img = cv2.merge(out)
    # levels: push paper to pure white, deepen ink a bit
    lut = np.clip((np.arange(256) - 40) * 255.0 / (235 - 40), 0, 255).astype(np.uint8)
    return cv2.LUT(img, lut)


def trim(img, margin=0.006):
    h, w = img.shape[:2]
    my, mx = int(h * margin), int(w * margin)
    return img[my:h - my, mx:w - mx]


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    for f in sorted(os.listdir(src)):
        if not f.lower().endswith(".jpg"):
            continue
        img = load(os.path.join(src, f))
        is_scan = f.startswith("Сканирование")
        note = ""
        if not is_scan:
            res = find_page(img)
            # already-cropped shots read as ~100%; shadows can fake a small "page"
            if res is not None and 0.5 < res[1] < 0.92:
                quad, area = res
                img = trim(warp(img, quad))
                note = f"warped, page {area:.0%}"
            img = whiten_outside(img)
            img = flatten(img)
        else:
            img = whiten_outside(trim(img, 0.01))
        cv2.imwrite(os.path.join(dst, f), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(f, img.shape[1], "x", img.shape[0], note)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
