# Final Release Verification

The delivered PPTX is byte-identical to `validated/validated-v5.pptx` (SHA256 `ab9f9c9fb2d0dce8cc6c82b3965e011254a856f05cc51bd7fd9fb797baf2a135`). The delivered PDF is byte-identical to `validated/validated-v5.pdf` (SHA256 `9a54a62c2ef0b23ae81f9524d7d2abaa10325a26bb48529437a284d847a4421d`).

## Visual Evidence

- Main reviewer inspected all 18 actual v4 PDF pages individually. Independent design reviewer approved that same v4 PDF in `../reviews/design_release.md`.
- Actual v5 PDF pages 10, 11, and 13 were individually re-inspected. Page 10 shows five mean markers and capped confidence intervals; page 11 shows the fixed-input curve and caps with an unbroken axis title; page 13 correctly limits the evidence to selected English MS MARCO pools.
- Pixel comparison of all v4 and v5 page renders establishes that exactly pages 10, 11, and 13 changed. The other 15 pages are pixel-identical to the already reviewed PDF.
- The v5 presentation was opened in Microsoft PowerPoint without a repair prompt. Slides 8, 10, and 11 were inspected natively. The presentation was closed without saving.
- Native chart data editability was tested on the unchanged slide-6 bar chart in v3: PowerPoint's Edit Data in Excel command opened the embedded workbook with the expected four model rows and numeric values. No workbook changes were saved. Final v5 workbook/cache values were also checked structurally and against the corrected source JSON.

## Data And Package Evidence

`audit_deck.py v5` passes: 18 slides, 18 speaker notes, 5 editable native charts, 5 embedded workbooks, source-consistent values and custom confidence bounds, clean visible text, and the preserved old file hashes. The separate `validation-v5.json` receipt also passes package, geometry, font, import, and native chart checks. Those automated checks do not substitute for the visual evidence above.

The presentation contains 13 main slides with a planned script allocation of 810 seconds and 5 backup slides. This is a planned duration, not an official conference slot or timed rehearsal. No ML experiment was run for this deck.

## Delivery

Only `DAMDID_2026_Presentation.pptx` and `DAMDID_2026_Presentation.pdf` belong in `Презентация_DAMDID_Новая`. Build artifacts and review records remain private. The original presentation files and manuscript files were not edited.
