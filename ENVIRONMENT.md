# Environment

The maintained evaluation scripts use Python 3.12 or newer with the versions in
[requirements.txt](requirements.txt): NumPy, SciPy, pandas, matplotlib and ijson.
Install them in a virtual environment as shown in the root README. Rebuilding
tables and figures needs only the saved files in `revision_2026/results/`.
Recomputing the evaluation also needs the matching research-data ZIP; manual
evaluation additionally needs the exact upstream small-development qrels.

The notebook records the original retrieval, model-training and inference
development. Its additional dependencies and hardware requirements are described
in its cells. Saved notebook outputs are cleared. No model checkpoint or fresh
training result is supplied by the maintained evaluation scripts.

The manuscript directories contain the necessary local TeX inputs and figures.
Use XeLaTeX and latexmk from TeX Live or MacTeX, Computer Modern Unicode fonts,
and the packages named in the document preambles. The per-manuscript README files
give the build commands. Bibliography entries are included in the TeX sources;
the bundled class and bibliography-style files retain their original notices.

The final presentation is supplied as editable PPTX and PDF; the speech is DOCX.
Old rendering caches and intermediate slide builds are outside the current tree.
