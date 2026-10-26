"""Adjust only connector geometry in the original vector protocol diagram."""
import hashlib
import json
import math
from pathlib import Path

import pdfplumber
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, FloatObject

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "revision_2026/previous_versions/delivery_revision/figures/protocol_schematic_en.pdf"
OUTPUT = ROOT / "source/figures/protocol_schematic_en.pdf"
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == "54cc006358bc89b754c3a2032eebc59a83b9de960280554c9ae566d7cb2ef0b7"

reader = PdfReader(BASE)
writer = PdfWriter()
writer.clone_document_from_reader(reader)
page = writer.pages[0]
content = ContentStream(page.get_contents(), writer)
before = ContentStream(reader.pages[0].get_contents(), reader).operations
assert len(content.operations) == 378
changed = set()


def coordinates(index, operator, values):
    assert content.operations[index][1] == operator
    content.operations[index] = ([FloatObject(value) for value in values], operator)
    changed.add(index)


def arrow(index, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    head_length, half_width = 2.8, 1.3
    base = (end[0] - head_length * ux, end[1] - head_length * uy)
    coordinates(index, b"m", start)
    coordinates(index + 1, b"c", [
        start[0] + dx / 3, start[1] + dy / 3,
        start[0] + 2 * dx / 3, start[1] + 2 * dy / 3, *end,
    ])
    coordinates(index + 5, b"m", [base[0] - half_width * uy, base[1] + half_width * ux])
    coordinates(index + 6, b"l", end)
    coordinates(index + 7, b"l", [base[0] + half_width * uy, base[1] - half_width * ux])


# The connectors stay in the gaps, with equal clearance from both box borders.
clearance = 1.2
for index, left, right, y in [
    (103, 119.6928, 129.0672, 124.28928),
    (123, 232.1856, 241.56, 124.28928),
    (143, 344.6784, 354.0528, 124.28928),
    (223, 344.6784, 354.0528, 62.19648),
]:
    arrow(index, (left + clearance, y), (right - clearance, y))
arrow(163, (293.1192, 106.54848 - clearance), (293.1192, 79.93728 + clearance))

# Place the unchanged two-line annotation to the left of the vertical connector.
for index in (327, 335):
    values = [float(value) for value in content.operations[index][0]]
    values[4] -= 47.0
    values[5] += 3.0
    coordinates(index, b"cm", values)

assert {i for i, (a, b) in enumerate(zip(before, content.operations)) if a != b} == changed
page.replace_contents(content)
with OUTPUT.open("wb") as destination:
    writer.write(destination)

with pdfplumber.open(BASE) as original, pdfplumber.open(OUTPUT) as revised:
    first, second = original.pages[0], revised.pages[0]
    assert (first.width, first.height) == (second.width, second.height)
    assert [c["text"] for c in first.chars] == [c["text"] for c in second.chars]
    assert len(first.images) == len(second.images) == 0
    moved_chars = []
    for a, b in zip(first.chars, second.chars):
        assert a["fontname"] == b["fontname"] and a["size"] == b["size"]
        dx, dy = b["x0"] - a["x0"], b["top"] - a["top"]
        if not math.isclose(dx, 0, abs_tol=1e-6) or not math.isclose(dy, 0, abs_tol=1e-6):
            assert math.isclose(dx, -47, abs_tol=1e-6) and math.isclose(dy, -3, abs_tol=1e-6)
            assert b["x1"] < 293.1192 - 10
            moved_chars.append(b["text"])
    assert "".join(moved_chars) == "threshold = -0.2187AUC(test) = 0.907"

report = {
    "file": OUTPUT.name,
    "arrows_adjusted": 5,
    "text_and_numbers_unchanged": True,
    "blocks_and_page_size_unchanged": True,
    "annotation_shift_points": [-47, 3],
    "vector_output": True,
    "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
}
(ROOT / "verification/protocol_arrows.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
