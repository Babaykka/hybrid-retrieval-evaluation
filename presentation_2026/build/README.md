# DAMDID presentation build

Deliver only the two files in `../../Презентация_DAMDID`.
The manuscript was not edited. This presentation uses the verified recomputation
authorized by the user on 20 September 2026.

## Content and timing

Twelve main slides plus four appendix slides. Speaker notes are Russian, visible
slide copy is English. The notes allocate 810 seconds (13 minutes 30 seconds),
excluding questions. This is a working talk length, not an official time limit.
At the 20 September check, the conference program page still announced future
publication of the program. No duration or presentation template was found in
the provided registration pages. The authors/editors subpage returned HTTP 404.

Official pages checked:
- https://damdid.unn.ru/conference-program/
- https://damdid.unn.ru/overview/
- https://damdid.unn.ru/registration/
- https://damdid.unn.ru/registration/for-authors-and-editors

## Rebuild

Use the bundled Node executable to run `build_deck.mjs`. Set `DECK_FILENAME` to
a new filename before rebuilding because the finalizer preserves existing final
files. Native chart values are rounded to eight decimal places for Excel's
numeric precision. The complete original inputs and checksums remain in
`data_snapshot.json`. The five embedded workbooks contain editable chart data.

`stamp_pptx.py` changes only document metadata and explicitly disables smooth
interpolation for scatter charts. It does not change chart data or slide text.
The finalizer runs after this stamp. Convert the final PPTX using LibreOffice
with the isolated `lo-en` user profile to keep English decimal separators.
PowerPoint may follow the user's regional decimal-separator preference.

`audit_deck.py` verifies final chart values against the source JSON, presentation
structure, speaker notes, forbidden stale values and key text in the final PDF.
Final visual review includes every PDF slide and PowerPoint spot checks of the
cover, the evaluation diagram and the manual results chart.

## Cover asset

Saved asset: `assets/annotation-cover.png`.
Generated with the built-in image generation tool. It illustrates printed
passage annotation and is not presented as experimental evidence.

Final prompt:

Create a refined editorial photograph for the cover of a scientific information retrieval conference talk. Horizontal 3:2 image. Several small white printed passage cards carefully arranged on a pure white studio surface, one card partially overlapping another, with two thin translucent teal annotation highlights and one restrained vermilion pencil mark on the paper. An elegant tangible metaphor for researchers finding multiple relevant answers. Close-up oblique overhead camera, soft daylight, extremely subtle shadows, crisp paper edges, quiet minimal composition. Objects concentrated in the right half and lower-right, abundant white negative space on the left. The printed material consists only of tiny subtle neutral gray typographic texture, no readable words, no letters as a focal point, no titles, no logos, no numbers. No computers, no people, no neural network graphics, no magnifying glass, no icons, no colored background, no gradient, no infographic, no slide layout. White background must blend into a white slide.
