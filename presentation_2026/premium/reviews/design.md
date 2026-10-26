# Scientific Presentation Art Direction

## Recommendation

Rebuild the visual language as an editorial scientific talk: white canvas, restrained typography, large evidence figures, explicit experimental conditions, and very few explanatory text blocks. The substantial improvement should come from making the experiment visible, especially the distinction between fixed rankings and changing judgments. Changing fonts and recoloring the existing layouts will not be enough.

Two viable directions:

- **Editorial evidence, recommended:** white background, charcoal text, green for human judgments, vermilion for model predictions. Strongest for projection, precise charts, and a readable PDF. Requires more care with composition because there is no decorative background to carry the slide.
- **Graphite keynote:** dark cover and section transitions, white analytical slides. More theatrical, but creates adaptation between backgrounds and invites unnecessary section slides in a short talk. Reserve this direction for a longer keynote.

Preserve the current deck as a separate deliverable. This report proposes a new design; it does not authorize changes to either builder or to the manuscript.

## Inspection Basis

- Visually inspected all 16 existing PNGs, individually, including cover 01, example 02, methods 04 and 06, and charts 05, 07, 08, 09, 10.
- Read Presentation skill `style_guidelines.md`, its main instructions, and `references/native_evidence.md`.
- Read the existing speaker script and builder without executing or modifying either. The script allocates 810 seconds to the 12 main slides: 13 minutes 30 seconds. The four appendices have no speaking allocation.
- Verified numerical recommendations against `revision_2026/results/manual_summary.json` and `fullset_summary.json`; checked experimental meaning against `delivery_revision/manuscript_en.tex`. No legacy manuscript numbers were used.
- This is a visual and editorial review of the rendered deck, not a PowerPoint compatibility test. The project root is not a Git repository.

## Concrete Findings

The existing slides are generally readable, aligned, and appropriately cautious. The weakness is visual hierarchy and scientific explanation, rather than a widespread overflow problem.

| Slide | Observed problem | Specific change |
| --- | --- | --- |
| 01, cover | The stock-like paper illustration explains neither retrieval nor incomplete qrels. The large three-line title and separate subtitle feel like two competing titles. DAMDID appears twice. | Use a typographic cover with a deliberate title hierarchy, one conference label, three authors, and the affiliation. Remove the illustration rather than replace it with a neural-network metaphor. |
| 02, real example | The black cell grid is almost as prominent as the evidence. Seven-digit IDs precede passage text at the same size. Only one green cell directs attention to the key change. | Keep three passages but remove vertical borders. Move IDs to a quieter position and emphasize the entire newly judged row. Pair clear status words with editable markers. |
| 03, study scale | Huge query counts look like equivalent populations, while their different evidence status appears in smaller text. The corpus number takes substantial space without explaining the experiment. | Establish two labeled stages, human assessment and model labeling, with counts attached to their roles. Keep corpus size as one context sentence. Do not draw nested populations without qualifying overlap. |
| 04, pooling | Four large pastel boxes and converging diagonal arrows read as a generic process template. The known-answer channel is buried in a long paragraph. | Use aligned source lanes and orthogonal connectors. Show the known relevant answer as an explicit input to auxiliary selection and assessment, separate from query-only retrieval. |
| 05, density | Two columns correctly start at zero, but one value is reduced to a sliver. A second giant count on the right competes with the main comparison. | Use two directly labeled horizontal bars, 1.05 and 17.47, on one 0-20 scale. Put 1,243 and 20,597 pairs into their respective row captions, not a separate KPI. Keep the pool denominator adjacent. |
| 06, evaluation | The two label branches converge into one NDCG box. This can visually imply a shared combined result. The unchanged order is asserted but never shown. | Show the same ordered documents beside two aligned label columns and two separate evaluations. Place the shared-per-query-and-label-set IDCG rule next to the comparison. |
| 07, manual result | Eight heavy bars and a bottom legend require scanning away from the values. A small p-value sentence is the only visible uncertainty. The near-identical annotation effects are hard to compare. | Use paired endpoints for each system and a row-aligned effect/95% CI column. Keep absolute NDCG and its paired change visually distinct. |
| 08, judge | A giant AUC and three similar-height bars create a performance dashboard. The most important method distinction, joint text input with no reference answer, is relegated to subtitle/footer text. | Make the input and validation protocol the primary composition. Present held-out AUC, precision, recall, and F1 as a compact aligned metric row. Do not fabricate a ROC curve from one AUC value. |
| 09, pool depth | The gray candidate line dominates the positive line by scale, while the large 128.6 callout competes with both. Teal now means predicted relevance, although it previously meant human relevance. | Retain counts with direct endpoint labels and give predictions their own consistent encoding. Add a small aligned share-of-candidates plot only with an explicit denominator. Remove the floating endpoint KPI. |
| 10, RRF | A narrow 0.82-0.89 vertical range makes two close scores appear widely separated. The warning is present but distant. The side numbers omit the available uncertainty. | Make RRF minus E5 the main chart, with a zero reference and paired CIs. Display the joint change in pool depth and fusion depth beside the chart, not only in the footer. |
| 11, next experiment | Two large text columns occupy most of the canvas without visually isolating the one new input. Green emphasis makes the planned model look like a measured result. | Align the common inputs and add only the reference-answer row in the proposed branch. Use a dashed boundary and an explicit "Proposed" label, with no performance number. |
| 12, conclusion | "Higher NDCG" is less precise than the earlier result, while the red RRF phrase attracts disproportionate attention relative to the main manual finding. | Give the manual annotation effect the largest hierarchy. Keep the conditional fusion result subordinate and retain "under model-generated labels" immediately beside it. |
| 13, metric appendix | A large equation leaves a heavy table to carry all of the actual evaluation rules. | Reduce the equation and use a border-light native table. Emphasize the zero-gain and common-IDCG rules rather than every cell boundary. |
| 14, judge appendix | The split is clear, but held-out reranking scores sit alone at the bottom without an equally visible enriched-pool qualification. | Attach "Reranking within the enriched manual pool" directly to those scores. Preserve query-level split information and the raw-score threshold distinction. |
| 15, sensitivity | A large bordered table and a second large result statement compete. Rounding conceals the scale of the tiny manual changes. | Keep the native table, with aligned decimals and light horizontal rules. Separate manual cleaning from full-set query exclusion by whitespace and short labels. |
| 16, references | Long model identifiers wrap awkwardly, and the repeated footer adds no retrieval value. | Use hanging-indent bibliography entries, concise model labels, and working hyperlinks. Keep full identifiers and source provenance in notes. |

## Design System

### Typography

- Use **Helvetica Neue**, Regular/Medium/Bold, as one family throughout. Its local font file was found at `/System/Library/Fonts/HelveticaNeue.ttc`. Arial is the portability fallback; reflow and inspect every slide if substituted. Do not assume font embedding is available or licensed.
- For a standard 13.333 x 7.5 inch slide: cover title 42-46 pt, slide title 32-34 pt, body 21-24 pt, chart labels 18-20 pt, essential qualifications 17-18 pt, page number 11-12 pt. Approximate pixel equivalents at 96 dpi are 56-61, 43-45, 28-32, 24-27, and 23-24 respectively.
- Use Medium for most titles, Bold for a small number of values. Reserve 48-56 pt numbers for a slide whose central claim is that number. Do not repeat giant KPIs across results slides.
- Sentence case, zero letter spacing, normal paragraph spacing, and about 1.1 line spacing. Prefer one title line, accept two deliberately composed lines, and never shrink a title to force a fit.
- Use tabular figures where the font/export supports them. Keep NDCG at three decimals and confidence interval endpoints at four when the small effect needs that precision.

### Palette And Meaning

| Role | Color | Additional encoding |
| --- | --- | --- |
| Canvas | `#FFFFFF` | Flat, no gradients or texture |
| Main text | `#202428` | The dominant nonwhite element |
| Secondary text | `#596168` | Avoid pale captions on white |
| Rules | `#DCE1E3` | Thin horizontal rules, no full-cell cages |
| Original qrels / neutral candidates | `#849096` | Open circles or dashed lines as appropriate |
| Human judgments | `#007C66` | Filled circles, explicitly named |
| Judge predictions | `#C2513C` | Filled squares, explicitly named |
| Proposed work | Charcoal/gray | Dashed outlines and "Proposed" text |

Color encodes evidence provenance, not general emphasis and not model identity. Put BM25, E5, BGE, and RRF into named rows instead of giving each a new color. A colored marker never replaces a label. Essential series remain distinguishable in grayscale by fill, marker shape, and line style. Small labels use charcoal rather than the lighter neutral-series color.

### Canvas And Rhythm

- At 1280 x 720, use approximately 64 px side margins, 50 px top margin, and a 40 px bottom safe area. Keep the main evidence region approximately y=185-615. A short title can release more space to a figure.
- Remove the repeated all-caps section kicker and conference footer from main slides. A quiet slide number is enough. Put essential methodological qualifications immediately beneath the relevant figure, not behind a general footer rule.
- Use a full-width analytical figure, a narrow annotation margin, or a deliberately asymmetric comparison. Do not turn those regions into bordered panels or cards.
- Each main slide should have one title, one dominant evidence composition, and at most one short interpretation sentence. Generally aim for 25-45 explanatory words excluding axis labels, necessary passage text, and source qualifications.
- Alternate typographic opening, real example, process, compact quantitative comparison, full-width analytical figure, judge protocol, depth results, and a restrained conclusion. Avoid three consecutive layouts with a chart on the left and a giant KPI on the right.
- Keep 12 main slides and four reserves as the working structure. The existing 13:30 allocation already fits 12-15 minutes; use the redesigned hierarchy to improve explanation rather than add transition slides. English on-slide text, Russian speaker notes, three authors, no email.

## Five Native Editable Compositions

### 1. Relevance Evidence And Fixed Rankings

**Replaces:** example 02 and provides a consistent visual vocabulary for evaluation 06.

Place the query as a two-line maximum heading over a full-width, three-row evidence table. Give passage text about 62% of the usable width; give "Original qrels" and "Human judgment" about 19% each. Use only horizontal separators. Keep IDs as small secondary labels, not part of the first reading line. Highlight passage 7399382 with a thin green left rule and a very light row tint. Use "Unjudged" and "Relevant" alongside open and filled native markers. Preserve the acetone negative example and mark the text as shortened paraphrases.

On the evaluation slide, use a separate, clearly labeled schematic ranked list with identical document order and aligned label columns. Show one score per label set. Do not assign observed ranks or numeric example NDCG values to the three passages unless the actual ranking is available. Caption: "Rankings stay fixed; judgments and pool-based IDCG can change." Qualify IDCG as shared across systems for the same query and label set.

**Editable construction:** native table, text, small circles, and straight rules. No rasterized table or screenshot. The example's exact labels and passage IDs come from the corrected manuscript, Section "A Concrete Example".

### 2. Pooling And Judge Provenance

**Replaces:** the block flow on 04; its visual grammar also supports 08.

Build an open left-to-right workflow with three aligned source rows named BM25, E5, and BGE, each explicitly "Top 10". A separate lower lane carries "Auxiliary candidates" and the known-answer input. Join sources with orthogonal connectors into one deduplication operation and then the human assessment operation. Draw the known relevant answer as a distinct input to both relevant stages, without implying it enters the query-only retrievers. Put "33,667 pairs / 1,179 queries" directly beneath the resulting assessed pool. Widths of the connectors must not encode undocumented channel volumes.

On 08, reuse the open alignment, not the full previous diagram: query text and candidate text enter one MiniLM operation; its score passes a validation-selected threshold. A separate labeled held-out evaluation line carries "177 queries, 5,002 pairs" and AUC 0.907, precision 0.851, recall 0.902, F1 0.875. Keep "No known answer or retrieval scores" close to the input. Treat these as agreement measures, not a retriever leaderboard. Training/validation/test boundaries should remain explicit in notes and the appendix.

**Editable construction:** native text, small functional operation rectangles, straight connectors, and a native metric table without boxes around each value. No decorative neural network, Sankey widths, or invented token interactions. Do not draw a clean all-pairs training pathway that hides the inherited unresolved-label limitation described in the manuscript.

### 3. Paired Manual Effects With Uncertainty

**Replaces:** eight bars on 07.

Use one row per system, in the existing order BM25, E5, BGE, RRF. Allocate about 68% of the figure width to a horizontal paired-endpoint plot on a fixed 0-1 NDCG axis. Original qrels use open gray circles; human judgments use filled green circles. Join each pair with a thin neutral segment and directly label both endpoints. A narrow, row-aligned plot on the right shows "Human minus original, 95% paired CI" on a separate explicitly labeled 0-0.45 effect scale. Avoid a distant legend.

| System | Original | Human | Mean change | 95% paired CI |
| --- | --- | --- | --- | --- |
| BM25 | 0.248 | 0.644 | +0.396 | [0.3724, 0.4188] |
| E5 | 0.488 | 0.879 | +0.391 | [0.3653, 0.4172] |
| BGE | 0.433 | 0.828 | +0.395 | [0.3691, 0.4194] |
| RRF | 0.459 | 0.854 | +0.395 | [0.3708, 0.4186] |

Read unrounded values from `metrics.<model>.official`, `.human`, and `.human_minus_official` in `manual_summary.json`. Intervals belong to paired changes; do not draw them around either absolute mean. Caption: "Same 1,179 queries and rankings. Common pool-based IDCG within each label set." Keep p-values and resampling details in notes or the reserve unless questions require them.

**Editable construction:** native XY/scatter charts, embedded numeric data, and custom horizontal error bars. If the export library lacks editable error bars, use grouped native lines at coordinates calculated from the exact axis scale and disclose that they are manually editable rather than workbook-linked. Never substitute a PNG or arbitrary whisker lengths.

### 4. Pool Coverage And Predicted Share

**Replaces:** 09.

Use a full-width upper plot occupying about 70% of the figure height: numeric K at 10, 30, 50, 100, 200 on a linear axis; candidate count in neutral gray and pseudo-positive count in vermilion; a common 0-500 count axis. Directly label endpoints, including 451.5 candidates and 128.6 pseudo-positive passages at K=200. Remove the separate 128.6 KPI.

Below it, use an unframed aligned dot plot with the same K coordinates and its own 0-100% axis. Its label must read "Pseudo-positive pairs / candidate pairs". The values derived from verified pair totals are 64.9%, 51.2%, 44.8%, 36.3%, and 28.5%. This is the ratio of pooled pair totals, not a mean of per-query relevance fractions. Identify it as a derived descriptive statistic in notes; it is neither precision nor corpus relevance prevalence.

Source upper means from `populations.all_queries.depths[].candidates_mean_all_queries` and `.positives_mean_all_queries`; derive the lower series as `positive_pairs / candidate_pairs`. Caption: "101,093 queries, including zero-positive queries. Same judge and threshold at every depth." The precise scientific point is that predicted-positive counts increase while their fraction of the expanding selected pool decreases.

**Editable construction:** two vertically aligned native XY charts with straight line segments, no smoothing, no dual axis, no area fill. The lower comparison is analytically related evidence, not an extra dashboard tile.

### 5. RRF Minus E5 With A Visible Null

**Replaces:** 10.

Use a large horizontal forest plot with categorical rows K=10, 30, 50, 100, 200. The horizontal axis is "NDCG@10 difference, RRF(K) minus E5", covering about -0.025 to +0.015 with a strong thin zero line. Put "E5 higher" on the negative side and "RRF higher" on the positive side. Each row has a vermilion square and a 95% paired confidence interval. Keep one color for all depths; changing sign does not change provenance. Do not connect categorical rows as a continuous trajectory.

| K | Mean difference | 95% paired CI |
| --- | --- | --- |
| 10 | -0.0195 | [-0.0202, -0.0188] |
| 30 | +0.0109 | [+0.0102, +0.0115] |
| 50 | +0.0085 | [+0.0078, +0.0093] |
| 100 | +0.0077 | [+0.0070, +0.0084] |
| 200 | +0.0088 | [+0.0082, +0.0095] |

Read `paired_inference.all_queries` filtered strictly to `contrast == "rrf_variable_minus_e5"`; do not mix in `rrf_fixed200_minus_e5`. Place "Pool depth and RRF input depth both equal K" directly above the plot, and "Agreement under model-generated labels" directly below it. A concise takeaway is "RRF exceeds E5 at the four deeper tested input settings." Avoid claiming monotonic improvement or a causal benefit from annotation depth alone.

**Editable construction:** native XY chart with custom horizontal error bars and editable labels, or scale-linked native shapes if the chart API cannot express the interval layout. Put the absolute-score comparison and fixed-200 control into reserve material; they answer different questions.

## Priority And Acceptance

1. First rebuild 02, 06, 07, and 10: these carry the scientific mechanism and the central evidence. Then revise the cover and pooling diagram. Apply the shared type and color system only after these compositions work.
2. Preserve all labels that bound interpretation: selected pools, unchanged rankings, pseudo-labels, joint depth changes, and held-out evaluation. Editing for brevity must not remove them.
3. Keep source references and the full technical explanation in Russian speaker notes. Essential qualifications remain in English beside the relevant evidence. Remove generic production commentary from audience-facing slides and notes.
4. Render every revised slide at a consistent size and inspect it individually. Check projection-scale readability, grayscale encoding, exact K positions, marker/label alignment, signs, interval placement, author names, and text clipping.
5. Verify editability separately from appearance: charts must retain numeric data or be explicitly identified as native grouped diagrams. Inspect representative charts in an actual target application before claiming PowerPoint editing compatibility.

The intended result is a confident scientific presentation with visible experimental logic and restrained visual authority. The old deck's readable baseline and careful caveats are worth keeping; its repetitive heavy framing and KPI treatment are the parts to replace.
