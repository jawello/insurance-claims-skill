"""Fill the MetLife group claim form.

usage: python fill_form.py BLANK_PDF OUT_PDF VALUES_JSON [VALUES_JSON ...]

Values files are merged in order (shared person data first, then the case):
  {"gender": "male" | "female",               # Part A, the patient
   "main_insured_gender": "male" | "female",  # Part B
   "fields": {"<qualified field name>": "text" | "/On" | "/Yes"},
   "overlay": [[x, y, "text"], ...]}   # page-1 labels the form has no fields for

Form quirks handled here:
- gender checkboxes are misnamed: "5 Gender" is the Male box, "Male" is the Female box,
  and the same goes for "5 Gender_2" and "Male_2" in Part B;
- text is rendered as 10pt Helvetica with no shrink, so long values are rejected;
- TOTAL has a JS auto-sum that zeroes text amounts, so it is removed;
- date combs Y_9..Y_11 have MaxLen 5 but need DDMMYY;
- checkbox widgets carry partial names, so they are matched by the full parent chain.
"""
import io
import json
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

GENDER_FIELDS = {
    "gender": {"male": "5 Gender", "female": "Male"},
    "main_insured_gender": {"male": "5 Gender_2", "female": "Male_2"},
}


def qualified(annot):
    node, parts = annot, []
    while node is not None:
        if node.get("/T") is not None:
            parts.append(str(node["/T"]))
        node = node["/Parent"].get_object() if node.get("/Parent") else None
    return ".".join(reversed(parts))


def inherited(annot, key):
    node = annot
    while node is not None:
        if key in node:
            return node[key]
        node = node["/Parent"].get_object() if node.get("/Parent") else None
    return None


def main(blank, out, value_files):
    fields, overlay, genders = {}, [], {}
    for path in value_files:
        data = json.load(open(path))
        fields.update(data.get("fields", {}))
        overlay += data.get("overlay", [])
        genders.update({k: data[k] for k in GENDER_FIELDS if k in data})

    for key, value in genders.items():
        if value not in GENDER_FIELDS[key]:
            sys.exit(f"{key} must be male or female, got {value!r}")
        fields[GENDER_FIELDS[key][value]] = "/On"

    w = PdfWriter(clone_from=PdfReader(blank))
    widgets = {}
    for page in w.pages:
        for a in page.get("/Annots", []):
            a = a.get_object()
            widgets.setdefault(qualified(a), []).append(a)

    problems = [f"unknown field {k}" for k in fields if k not in widgets]
    for k, v in fields.items():
        if k not in widgets or v.startswith("/"):
            continue
        a = widgets[k][0]
        if inherited(a, "/MaxLen") is None:
            room = float(a["/Rect"][2]) - float(a["/Rect"][0]) - 4
            if stringWidth(v, "Helvetica", 10) > room:
                problems.append(f"too long {k}: {stringWidth(v, 'Helvetica', 10):.0f} > {room:.0f}")
    if problems:
        sys.exit("\n".join(problems))

    af = w._root_object["/AcroForm"]
    if "/CO" in af:
        del af["/CO"]
    for name, annots in widgets.items():
        for a in annots:
            if name == "total" and "/AA" in a:
                del a["/AA"]
            if name in ("Y_9", "Y_10", "Y_11"):
                a[NameObject("/MaxLen")] = NumberObject(6)

    text = {k: v for k, v in fields.items() if not v.startswith("/")}
    for page in w.pages:
        w.update_page_form_field_values(page, text, auto_regenerate=False)
    for k, v in fields.items():
        if not v.startswith("/"):
            continue
        for a in widgets[k]:
            target = a if a.get("/T") is not None else a["/Parent"].get_object()
            target[NameObject("/V")] = NameObject(v)
            a[NameObject("/AS")] = NameObject(v)
    w.set_need_appearances_writer(True)

    if overlay:
        box = w.pages[0].mediabox
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(float(box.width), float(box.height)))
        c.setFont("Helvetica", 8)
        for x, y, s in overlay:
            c.drawString(x, y, s)
        c.save()
        buf.seek(0)
        w.pages[0].merge_page(PdfReader(buf).pages[0])

    w.write(out)
    print("written", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
