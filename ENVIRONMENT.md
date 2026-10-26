# Working environment

Run maintained analysis scripts from the repository root in a separate Python
environment. The analysis sources use NumPy, SciPy, pandas, matplotlib, and ijson;
install only the modules needed by the command being run. Historical notebooks
also record the retrieval/model dependencies and require the appropriate upstream
data and model access. No training checkpoint is claimed to be present.

Document builders use python-docx, pdfplumber, PyMuPDF, and lxml where imported.
LaTeX manuscripts require a compatible TeX distribution and their local class/
bibliography files. Set `LATEX_COMPILE_HELPER` if a historical packaging script
uses an external compilation helper; otherwise compile the manuscript with the
corresponding TeX engine directly.

Presentation builders retain their source and use Node.js, `@oai/artifact-tool`,
and presentation helper utilities. Configure `PRESENTATIONS_SKILL` and, where
needed, `RUNTIME_NODE_MODULES` for that optional toolchain. Set `PROJECT_ROOT` to
this checkout, or run builders from the repository root; `PYTHON` can select a
Python executable. The preserved PPTX/PDF files remain readable without that
authoring toolchain. A new machine must supply compatible dependencies rather
than reuse any archived local virtual environment or Office profile.
