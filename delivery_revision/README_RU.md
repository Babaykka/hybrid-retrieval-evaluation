# Статья с пересчитанными результатами

Английская и русская версии используют общий знаменатель NDCG и одинаковый набор запросов для сравнения систем. Численные результаты, код расчётов и построения рисунков находятся в [revision_2026](../revision_2026/). Методические пояснения приведены в [AUTHOR_NOTES_RU.md](AUTHOR_NOTES_RU.md).

- [Английский PDF](manuscript_en.pdf) и [LaTeX](manuscript_en.tex).
- [Русский PDF](manuscript_ru.pdf) и [LaTeX](manuscript_ru.tex).
- `tables/`, `figures/`, `results_macros.tex`, `fullset_interpretation_*.tex`, `references.tex` и `reviewer_responses_*.tex` — материалы, подключаемые исходниками статьи. Ответы рецензентам включены в оба PDF.

## Сборка

Нужны XeLaTeX и `latexmk` из TeX Live или MacTeX, шрифты Computer Modern Unicode (`cm-unicode`) и пакеты, перечисленные в преамбулах. Файл класса `llncs.cls` находится в этом каталоге. Из каталога `delivery_revision`:

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error manuscript_en.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error manuscript_ru.tex
```

Без `latexmk` можно дважды выполнить `xelatex` для каждого главного файла. Библиография включена через `references.tex`, поэтому отдельный запуск BibTeX не нужен. Для сборки статьи не требуются модели, Python или исследовательские данные.

Сохранённые расчёты используют ранее полученные выдачи, оценки судьи и разметку. Они не означают повторного обучения моделей или восстановления отсутствующего checkpoint. Последняя редакторская версия текста с прежними численными значениями находится [отдельно](../original_based_2026/README.md); численные результаты этих двух версий следует различать.
