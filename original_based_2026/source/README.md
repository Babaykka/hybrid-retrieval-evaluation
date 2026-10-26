# LaTeX sources

The English and Russian manuscripts include their figures, references, and responses to the reviewers.

- English root file: `manuscript_en.tex`, compiler: pdfLaTeX.
- Russian root file: `manuscript_ru.tex`, compiler: XeLaTeX.
- Keep the additional `.tex` files and the `figures` directory alongside the root files.
- The two PDFs were compiled from these sources.

With TeX Live or MacTeX and `latexmk` available, run from this directory:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript_en.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error manuscript_ru.tex
```

The English version uses scalable Computer Modern fonts (`cm-super`). The Russian version uses the CMU Serif, CMU Sans Serif, and CMU Typewriter Text fonts. Install these fonts and the packages named in the manuscript preambles if using a minimal TeX installation.

This package is an editorial revision of the supplied original. Its scope and the numerical questions requiring author agreement are described in `ПОЯСНЕНИЕ.md` at the package root.
