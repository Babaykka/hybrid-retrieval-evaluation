# PDF v3: Independent Export Findings

## Scope

This report concerns the actual **validated-v3.pdf export**, separately from the candidate-v1 presentation review in `design_final.md`. It is not a restatement of v1 findings and does not assess the forthcoming v4 fixes.

- PDF: `presentation_2026/premium/build/validated/validated-v3.pdf`
- SHA-256, reconfirmed when writing this report: `2b78e7f02cbeb5dfb8bf8abc87b5e6c6fd8804d3202edb66673df43f1a778e87`
- PDF metadata: 18 pages, LibreOffice 26.2.3.2 exporter, creation time 2026-09-21 00:19:39 MSK.
- Individually inspected the supplied actual-PDF PNGs for pages **06, 08, 10, 11, 16** in `premium/build/pdf-render`. This was a targeted export check, not a complete 18-page PDF review.
- That shared PNG directory may be regenerated. Findings below belong to the PDF hash above and the PNGs inspected before the v4 rebuild.

## Findings

### PDF-01 [P1] Page 10: All plotted evidence disappears

The plotting rectangle contains axes, gridlines, and the zero reference, but **none of the five mean markers or confidence-interval segments/caps is visible**. The right-side numerical callouts and the caption promising intervals survive. This is a release-blocking loss of scientific evidence in the exported PDF.

This differs from v1: v1 displayed five means with intervals visually obscured by the markers. The v3 PDF displays neither the means nor their intervals. Do not close this finding merely because interval series or values exist in the PPTX.

**Acceptance:** a fresh PDF must visibly show the five means at K=10, 30, 50, 100, 200, with correctly positioned 95% intervals and distinguishable end caps. At K=10 the point is negative; the four deeper points are positive. Verify the actual exported page at presentation size, including the short intervals near +0.009. Keep interval geometry faithful to the data.

### PDF-02 [P2] Page 08: Operating point and chance diagonal disappear

The ROC curve survives, but its highlighted validation-threshold operating point and diagonal reference line do not. The curve's fractional horizontal tick labels now correctly read **0.0 to 1.0**. The old v1 tick-format defect is therefore resolved and is not part of this finding.

**Acceptance:** the exported PDF must preserve the intended operating-point marker, approximately FPR=0.280 and TPR=0.902, and the diagonal from (0,0) to (1,1). Preserve the curve and the corrected fractional axis. Any accompanying threshold label must describe a validation-selected threshold, not test-set optimization.

### PDF-03 [P2] Pages 08, 10, 11: Axis-title typography regresses

Axis titles export as small black bold text, substantially smaller than the neighboring tick labels and their appearance in the earlier presentation renders. The long vertical "NDCG@10 difference" title is particularly weak at projection scale. This is a PDF typography issue, not a request to rewrite chart terminology.

**Acceptance:** explicitly preserve an axis-title font size and style appropriate to the deck. Aim for approximately 17-18 pt or comparable visual size to the ticks. Confirm horizontal and vertical titles in the actual PDF without squeezing the plot or clipping the text.

### PDF-04 [P3] Page 16: Dark cell grid reappears

The PDF adds conspicuous black vertical and horizontal cell borders to the previously border-light results table. Values and headings remain readable, with no blocking clipping. This is a styling/export regression, not a numerical or table-width defect.

**Acceptance:** make cell borders explicit in the export representation and retain the intended restrained table rules. Check the other native tables during the full PDF pass because this targeted review establishes the regression on page 16 only.

## Controls That Survive

- **Page 06:** all eight bar values render and remain associated with the correct human/original series. The PDF reverses their within-group vertical order relative to the earlier PNG, but the legend reverses consistently; this is not a data-label mismatch. No blocking clipping was observed.
- **Page 11:** the fixed-input comparison line and its points survive. Its fixed top-200 input condition, zero reference, and 14.4% callout remain readable. The axis-title regression above still applies.
- **Page 16:** all five depth rows and six columns remain visible; the dark grid is the observed export problem.

## Diagnosis Versus Observation

The findings above are independent visual observations. The main implementer subsequently reported `a:noFill` in `c:marker/c:spPr` despite intended colored markers and is correcting marker fills, chart-series compatibility, and table-border XML. That is a reported diagnosis, not a root cause independently established by this PDF check.

The main implementer also reports that PowerPoint opens without repair and its native Excel chart-data view contains the correct values. Those checks are useful but were not performed by this reviewer, and they do not resolve missing PDF graphics. The PDF export must pass its own visual verification after the XML fixes.

## Handoff

Reinspect **10 first**, then **08, 11, 06, 16**, in the new PDF. Proceed to the planned full 18-page PDF review after confirming that the missing series and markers render. Copy-only changes belong to the language pass and are intentionally not duplicated here. Preserve 13 core slides and 5 backups.

Only this report was created. No source, PPTX, PDF, builder, or previous review was changed.
