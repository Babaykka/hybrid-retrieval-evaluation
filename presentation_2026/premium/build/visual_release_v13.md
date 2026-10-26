# Presentation Revision v13

## Scope

User requested improvements after a critique of the final v10 presentation. The
revision keeps 18 slides, all measured results, all editable charts and tables,
and the existing 13-main/5-appendix structure. Manuscripts and research outputs
were not edited. No new model experiment was run.

Slides 6-13 clarify RRF, the role of the judge, K/L settings, conditional
uncertainty, human-validation limitations and the planned reference-passage
experiment. The Russian speaker notes remain present. Their 810-second
allocation is a planning estimate, not a measured rehearsal or official slot.

## Verification

- Finalizer v13 passed package, geometry, fonts and first-party import checks.
- All five chart datasets and both sets of native confidence bounds match the
  saved corrected source results. Five embedded chart workbooks remain editable.
- `audit_deck.py v13` passed numeric, notes, wording and preservation assertions.
- All 18 PDF pages were rendered. Pixel comparison to v10 proves that only
  slides 6-13 changed. Their v12 PDF pages were viewed individually; final v13
  differs only in the slide 8 held-out-query wording, which was rendered and
  viewed again. The other ten pages are pixel-identical to the reviewed v10.
- Native Microsoft PowerPoint opened final v13 without a repair prompt. All
  eight changed slides were inspected individually in full-screen slide-show
  mode. Text, graphs, labels, confidence intervals and tables were visible and
  free of unintended overlap. PowerPoint was closed without saving.
- A read-only scientific-communication review found no blockers. Its suggested
  clarification of reference-passage input was incorporated.
- Original, v5 and v10 delivered files retain their recorded hashes.

## Delivery

The output directory `Презентация_DAMDID_Для_выступления` contains exactly two
files, copied byte-for-byte from finalized v13:

- `DAMDID_2026_Presentation.pptx`: SHA256
  `7f8e873ef396a414aeb1ef9ecad61c77a7115521dc7498b65d5e6463edaf837c`
- `DAMDID_2026_Presentation.pdf`: SHA256
  `4bbb428c036fa771e95cfddd223763644af10c884bcfaad87faa81680d335446`

Native PowerPoint uses local decimal separators in chart labels. The PDF uses
decimal points. This does not change numeric values.
