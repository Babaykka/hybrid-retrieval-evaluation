# Editorial manuscript sources

This directory contains the latest editorial version of the English and Russian manuscripts, their PDFs, figures, examples, references, and reviewer responses.

This version retains the earlier reported numerical values. It is distinct from the [manuscript with recalculated results](../../delivery_revision/README_RU.md). The corresponding checked calculations are in [revision_2026](../../revision_2026/); the scope and numerical differences are described in [ПОЯСНЕНИЕ.md](../ПОЯСНЕНИЕ.md).

## Build

Use TeX Live or MacTeX with `latexmk`. From this directory:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript_en.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error manuscript_ru.tex
```

The English version uses pdfLaTeX and scalable Computer Modern fonts (`cm-super`). The Russian version uses XeLaTeX and Computer Modern Unicode fonts (`cm-unicode`). Install the packages listed in the manuscript preambles when using a minimal TeX installation.

Keep the neighboring `.tex` files, `figures/`, and the bundled LNCS class and bibliography style with the root files. Bibliographic entries are included in the LaTeX sources; these build commands do not require a separate BibTeX run.
