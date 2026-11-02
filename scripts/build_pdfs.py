"""Assemble processed images into A4 PDFs, plus a full package with the claim form first.

usage: python build_pdfs.py CASE_DIR

CASE_DIR/manifest.json:
  {"form": "MetLife_Claim_Form_....pdf",          # already in CASE_DIR/pdf, optional
   "full": "..._Full_Package.pdf",
   "docs": {"01_....pdf": [["a.jpg"], ["b.jpg", "c.jpg"]],
            "02_....pdf": {"pdf": ["digital/x.pdf", "digital/y.pdf"]}}}
Images come from CASE_DIR/processed; each inner list is one page, images side by side.
A {"pdf": [...]} entry concatenates ready PDFs (paths relative to CASE_DIR) as is.
"""
import io
import json
import os
import sys

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

MARGIN = 8 * mm
GAP = 6 * mm
MAX_SIDE = 2200


def jpeg(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True)
    buf.seek(0)
    return ImageReader(buf), im.size


def build(src, pages, out):
    pw, ph = A4
    c = canvas.Canvas(out, pagesize=A4)
    for row in pages:
        imgs = [jpeg(os.path.join(src, f)) for f in row]
        n = len(imgs)
        cell_w = (pw - 2 * MARGIN - GAP * (n - 1)) / n
        cell_h = ph - 2 * MARGIN
        x = MARGIN
        for reader, (w, h) in imgs:
            k = min(cell_w / w, cell_h / h)
            dw, dh = w * k, h * k
            y = ph - MARGIN - dh if n > 1 else (ph - dh) / 2
            c.drawImage(reader, x + (cell_w - dw) / 2, y, dw, dh)
            x += cell_w + GAP
        c.showPage()
    c.save()


def main(case):
    manifest = json.load(open(os.path.join(case, "manifest.json")))
    src, dst = os.path.join(case, "processed"), os.path.join(case, "pdf")
    os.makedirs(dst, exist_ok=True)
    writer = PdfWriter()
    form = os.path.join(dst, manifest.get("form", ""))
    if manifest.get("form") and os.path.exists(form):
        writer.append(PdfReader(form), outline_item="MetLife Claim Form")
    for name, pages in manifest["docs"].items():
        out = os.path.join(dst, name)
        if isinstance(pages, dict):
            merged = PdfWriter()
            for f in pages["pdf"]:
                merged.append(PdfReader(os.path.join(case, f)))
            with open(out, "wb") as fh:
                merged.write(fh)
        else:
            build(src, pages, out)
        r = PdfReader(out)
        writer.append(r, outline_item=name[3:-4].replace("_", " "))
        print(f"{name}: {len(r.pages)} pages, {os.path.getsize(out) / 1e6:.1f} MB")
    full = os.path.join(dst, manifest["full"])
    with open(full, "wb") as f:
        writer.write(f)
    print(f"{manifest['full']}: {len(PdfReader(full).pages)} pages, {os.path.getsize(full) / 1e6:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1])
