"""Rebuild bilingual, 12.2 cm PDF/PNG/SVG figures from the saved evaluation.

Run with revision_2026/.venv/bin/python revision_2026/make_figures.py.
The manuscript owns captions; diagnostics cover all eligible annotated pairs,
including training pairs, and must not be described as held-out performance.
No metric, confidence interval, or judge score is estimated from a picture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "package" / "figures"
# Keep Matplotlib's generated cache within this task's exclusive write scope.
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.text import Text
from matplotlib.ticker import FixedLocator, FuncFormatter, MaxNLocator
import numpy as np
from scipy.stats import rankdata


WIDTH_CM = 12.2
DPI = 300
MODELS = ("bm25", "e5", "bge", "rrf3")
MODEL_NAMES = {"bm25": "BM25", "e5": "E5", "bge": "BGE", "rrf3": "RRF(3)"}
COLORS = {"gray": "#62676C", "blue": "#0072B2", "orange": "#D55E00", "green": "#00856A"}
INK = "#25282B"
LIGHT = "#DDE0E2"
MODEL_COLORS = dict(zip(MODELS, (COLORS["gray"], COLORS["blue"], COLORS["orange"], COLORS["green"])))
MODEL_MARKERS = dict(zip(MODELS, ("s", "o", "^", "D")))


def configure_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.titlesize": 9,
        "axes.titleweight": "bold",
        "axes.labelsize": 8.5,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.edgecolor": COLORS["gray"],
        "axes.linewidth": 0.65,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.major.width": 0.65,
        "ytick.major.width": 0.65,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "lines.linewidth": 1.2,
        "lines.markersize": 4,
        "legend.frameon": False,
        "legend.handlelength": 1.6,
        "legend.borderaxespad": 0.3,
        "legend.labelspacing": 0.35,
        "savefig.dpi": DPI,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "figure.dpi": DPI,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "pdf.compression": 9,
        "svg.fonttype": "none",
        "svg.hashsalt": "revision_2026_figures",
        "axes.unicode_minus": True,
        "path.simplify": False,
        "mathtext.fontset": "dejavusans",
    })


def translate(lang, en, ru):
    return en if lang == "en" else ru


def number(value, lang, digits=0):
    if digits:
        result = f"{value:.{digits}f}"
        return result if lang == "en" else result.replace(".", ",")
    return f"{value:,}".replace(",", " " if lang == "ru" else ",")


def format_ticks(ax, lang, axis="both", digits=1, signed=False):
    def fmt(value, _):
        result = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
        if lang == "ru":
            result = result.replace(".", ",")
        return result.replace("-", "\N{MINUS SIGN}")
    if axis in ("both", "x"):
        ax.xaxis.set_major_formatter(FuncFormatter(fmt))
    if axis in ("both", "y"):
        ax.yaxis.set_major_formatter(FuncFormatter(fmt))


def read_json(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_manual(results):
    summary = read_json(results / "manual_summary.json")
    with np.load(results / "manual_per_query.npz", allow_pickle=False) as data:
        models = data["models"].tolist()
        require(len(data["qids"]) == summary["queries"], "Manual query count mismatch")
        require(len(set(data["qids"].tolist())) == summary["queries"], "Duplicate query IDs")
        for model in MODELS:
            index = models.index(model)
            stats = summary["metrics"][model]
            for name in ("official", "human"):
                values = data[name][:, index]
                require(np.all(np.isfinite(values)) and np.all((values >= 0) & (values <= 1)),
                        f"Invalid manual {name} NDCG for {model}")
                require(np.isclose(values.mean(), stats[name], rtol=0, atol=1e-12),
                        f"Manual mean disagrees with JSON: {model}/{name}")
            delta = stats["human_minus_official"]
            difference = data["human"][:, index] - data["official"][:, index]
            require(np.isclose(difference.mean(), delta["mean"], rtol=0, atol=1e-12),
                    f"Paired mean disagrees with JSON: {model}")
            low, high = delta["ci95"]
            require(np.isfinite([low, high]).all() and low <= delta["mean"] <= high,
                    f"Invalid paired confidence interval: {model}")
            require(delta["queries"] == summary["queries"], "Paired query count mismatch")
    with np.load(results / "manual_judge_diagnostics.npz", allow_pickle=False) as data:
        truth, scores = data["truth"].copy(), data["scores"].copy()
    require(truth.ndim == scores.ndim == 1 and truth.shape == scores.shape,
            "Judge truth and score arrays must have matching one-dimensional shapes")
    require(np.isfinite(scores).all() and np.isin(truth, [0, 1]).all(), "Invalid diagnostic input")
    recorded = summary["judge_valid_text_and_labels"]
    require(len(truth) == recorded["n"], "Diagnostic population mismatch")
    positives, negatives = int(truth.sum()), int((truth == 0).sum())
    require(positives > 0 and negatives > 0, "ROC requires both classes")
    auc = (rankdata(scores)[truth == 1].sum() - positives * (positives + 1) / 2) / (positives * negatives)
    require(np.isclose(auc, recorded["auc"], rtol=0, atol=1e-12), "Diagnostic AUC mismatch")
    threshold = summary["judge_threshold"]
    require(np.isfinite(threshold), "Non-finite judge threshold")
    predicted = scores >= threshold
    cm = [[int(np.sum(~predicted & (truth == 0))), int(np.sum(predicted & (truth == 0)))],
          [int(np.sum(~predicted & (truth == 1))), int(np.sum(predicted & (truth == 1)))]]
    require(cm == recorded["confusion_matrix"], "Diagnostic threshold/confusion matrix mismatch")
    return summary, truth, scores


def empirical_roc(truth, scores):
    # Aggregate equal-score groups, so the curve and AUC handle ties identically.
    order = np.argsort(-scores, kind="stable")
    sorted_scores, sorted_truth = scores[order], truth[order]
    ends = np.r_[np.flatnonzero(np.diff(sorted_scores)), len(scores) - 1]
    tp = np.cumsum(sorted_truth)[ends]
    fp = ends + 1 - tp
    return np.r_[0, fp / (truth == 0).sum()], np.r_[0, tp / truth.sum()]


def check_layout(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    frame = fig.bbox
    problems = []
    hidden_ticks = set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            low, high = sorted(axis.get_view_interval())
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                if not low - 1e-10 <= tick.get_loc() <= high + 1e-10:
                    hidden_ticks.update((tick.label1, tick.label2))
    for item in fig.findobj(Text):
        if item in hidden_ticks or not item.get_visible() or not item.get_text().strip():
            continue
        bounds = item.get_window_extent(renderer)
        if bounds.width == 0 or bounds.height == 0:
            continue
        if bounds.x0 < -1 or bounds.y0 < -1 or bounds.x1 > frame.x1 + 1 or bounds.y1 > frame.y1 + 1:
            problems.append(f"Clipped text: {item.get_text()!r}")
        if item.get_fontsize() < 8:
            problems.append(f"Text smaller than 8 pt: {item.get_text()!r}")
    for text, patch in getattr(fig, "_node_texts", []):
        tb, pb = text.get_window_extent(renderer), patch.get_window_extent(renderer)
        inset = 3 * DPI / 72
        if tb.x0 < pb.x0 + inset or tb.x1 > pb.x1 - inset or tb.y0 < pb.y0 + inset or tb.y1 > pb.y1 - inset:
            problems.append(f"Protocol label exceeds its box: {text.get_text()!r}")
    require(not problems, "; ".join(problems))


def export(fig, basename, lang, records, details):
    check_layout(fig)
    stem = OUTPUT / f"{basename}_{lang}"
    metadata = {"Title": f"{basename} ({lang})", "Creator": "make_figures.py / Matplotlib",
                "CreationDate": None, "ModDate": None}
    # Do not use bbox_inches='tight': it changes the requested physical size.
    fig.savefig(stem.with_suffix(".pdf"), metadata=metadata)
    fig.savefig(stem.with_suffix(".png"), dpi=DPI, metadata={"Software": "make_figures.py / Matplotlib"})
    fig.savefig(stem.with_suffix(".svg"), metadata={"Title": f"{basename} ({lang})",
                                                  "Creator": "make_figures.py / Matplotlib", "Date": None})
    records.append({"basename": stem.name, "language": lang, "width_cm": WIDTH_CM,
                    "height_cm": float(fig.get_size_inches()[1] * 2.54), "png_dpi": DPI,
                    "formats": ["pdf", "png", "svg"], "svg_text": "editable; requires DejaVu Sans",
                    "minimum_font_pt": 8, **details})
    plt.close(fig)
    print(f"Saved {stem.name}.pdf + .png + .svg")


def protocol_figure(summary, lang):
    fig = plt.figure(figsize=(WIDTH_CM / 2.54, 8.0 / 2.54))
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, WIDTH_CM), ylim=(0, 8.0))
    ax.set_axis_off()
    fig._node_texts = []

    def node(x, y, w, h, label, color=COLORS["gray"]):
        box = Rectangle((x, y), w, h, edgecolor=color, facecolor="white", linewidth=0.9)
        ax.add_patch(box)
        text = ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8, linespacing=1.35)
        fig._node_texts.append((text, box))

    def arrow(points, color=COLORS["gray"]):
        for start, end in zip(points[:-2], points[1:-1]):
            ax.plot([start[0], end[0]], [start[1], end[1]], color=color, lw=0.85, solid_capstyle="butt")
        ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle="-|>", mutation_scale=8,
                                    linewidth=0.85, color=color, shrinkA=0, shrinkB=1.5))

    ax.text(0.25, 7.70, translate(lang, "a  Manual annotation and judge calibration",
                                "a  Ручная разметка и настройка судьи"), fontsize=9, weight="bold", va="top")
    query_count = number(summary["queries"], lang)
    node(0.25, 6.0, 3.4, 1.15, translate(lang, f"Manual pool\n{query_count} queries",
                                      f"Пул ручной разметки\n{query_count} запросов"))
    node(4.4, 6.0, 3.2, 1.15, translate(lang, "Human relevance\nlabels", "Ручные метки\nрелевантности"), COLORS["blue"])
    node(8.45, 6.0, 3.5, 1.15, translate(lang, "Judge training\nand calibration", "Обучение судьи\nи настройка"), COLORS["green"])
    arrow([(3.65, 6.575), (4.4, 6.575)])
    arrow([(7.6, 6.575), (8.45, 6.575)])

    ax.text(0.25, 4.50, translate(lang, "b  Full-set protocol", "b  Полный набор"), fontsize=9, weight="bold", va="top")
    node(0.25, 2.65, 2.75, 1.15, translate(lang, "BM25 / E5 / BGE\nTop-K union", "BM25 / E5 / BGE\nПул top-K"))
    node(3.65, 2.65, 2.4, 1.15, translate(lang, "Judge inference\ns(q, d)", "Оценка пар\ns(q, d)"), COLORS["green"])
    node(6.7, 2.65, 2.4, 1.15, translate(lang, "Pseudo-labels\ns(q, d) ≥ τ", "Псевдометки\ns(q, d) ≥ τ"), COLORS["blue"])
    node(9.7, 2.65, 2.25, 1.15, translate(lang, "Evaluation\nNDCG@10", "Оценка\nNDCG@10"))
    for left, right in ((3.0, 3.65), (6.05, 6.7), (9.1, 9.7)):
        arrow([(left, 3.225), (right, 3.225)])
    arrow([(10.2, 6.0), (10.2, 5.15), (4.85, 5.15), (4.85, 3.8)], COLORS["green"])
    ax.text(7.525, 5.36, translate(lang, "Fixed judge and threshold", "Фиксированные судья и порог"),
            ha="center", va="bottom", fontsize=8, color=COLORS["green"])
    arrow([(1.625, 2.65), (1.625, 1.55), (10.825, 1.55), (10.825, 2.65)])
    ax.text(6.225, 1.25, translate(lang, "Ranked lists: BM25, E5, BGE, RRF(3)",
                                "Ранжированные списки: BM25, E5, BGE, RRF(3)"), ha="center", va="top", fontsize=8)
    return fig


def manual_figure(summary, lang):
    fig, (left, right) = plt.subplots(1, 2, figsize=(WIDTH_CM / 2.54, 6.8 / 2.54),
                                      gridspec_kw={"width_ratios": [1.08, 1]})
    fig.subplots_adjust(left=0.14, right=0.965, bottom=0.24, top=0.76, wspace=0.44)
    rows = np.arange(len(MODELS))
    official = np.array([summary["metrics"][m]["official"] for m in MODELS])
    human = np.array([summary["metrics"][m]["human"] for m in MODELS])
    left.hlines(rows, official, human, color=LIGHT, lw=1.6, zorder=1)
    left.scatter(official, rows, s=25, marker="o", facecolors="white", edgecolors=COLORS["gray"], linewidth=1.1, zorder=3)
    left.scatter(human, rows, s=25, marker="o", color=COLORS["blue"], zorder=3)
    left.set(xlim=(0, 1), yticks=rows, yticklabels=[MODEL_NAMES[m] for m in MODELS], xlabel="NDCG@10")
    left.set_title(translate(lang, "a  Mean NDCG@10", "a  Средний NDCG@10"), loc="left", pad=10)
    left.xaxis.set_major_locator(FixedLocator([0, 0.5, 1]))
    format_ticks(left, lang, axis="x")

    stats = [summary["metrics"][m]["human_minus_official"] for m in MODELS]
    means = np.array([s["mean"] for s in stats])
    intervals = np.array([s["ci95"] for s in stats])
    right.errorbar(means, rows, xerr=np.array([means - intervals[:, 0], intervals[:, 1] - means]),
                   fmt="o", color=COLORS["green"], ecolor=COLORS["green"], capsize=3, capthick=0.9,
                   elinewidth=1.2, markersize=4, zorder=3)
    pad = max(0.01, float(np.ptp(intervals)) * 0.18)
    right.set(xlim=(intervals.min() - pad, intervals.max() + pad), yticks=rows, yticklabels=[],
              xlabel=translate(lang, "ΔNDCG@10\n(Human − original)", "ΔNDCG@10\n(Ручные − исходные)"))
    right.set_title(translate(lang, "b  Paired gain (95% CI)", "b  Прирост (95% ДИ)"), loc="left", pad=10)
    right.xaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 5, 10]))
    format_ticks(right, lang, axis="x", digits=2, signed=True)
    right.spines["left"].set_visible(False)
    right.tick_params(axis="y", length=0)
    for ax in (left, right):
        ax.set_ylim(3.5, -0.5)
        ax.grid(axis="x", color=LIGHT, lw=0.45, zorder=0)
        ax.set_axisbelow(True)
    handles = [Line2D([], [], marker="o", ls="none", markerfacecolor="white", markeredgecolor=COLORS["gray"],
                      label=translate(lang, "Original (official)", "Исходные (официальные)")),
               Line2D([], [], marker="o", ls="none", color=COLORS["blue"], label=translate(lang, "Human", "Ручные"))]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.52, 0.995), ncol=2, columnspacing=1.5)
    return fig


def judge_figure(summary, truth, scores, lang):
    fig, (roc, hist) = plt.subplots(1, 2, figsize=(WIDTH_CM / 2.54, 6.9 / 2.54))
    fig.subplots_adjust(left=0.11, right=0.975, bottom=0.22, top=0.82, wspace=0.42)
    threshold = summary["judge_threshold"]
    recorded = summary["judge_valid_text_and_labels"]
    fpr, tpr = empirical_roc(truth, scores)
    require(np.isclose(np.trapezoid(tpr, fpr), recorded["auc"], rtol=0, atol=1e-12), "ROC integral mismatch")
    roc.plot([0, 1], [0, 1], ls="--", color=COLORS["gray"], lw=0.75)
    roc.plot(fpr, tpr, color=COLORS["green"], lw=1.3)
    (tn, fp), (fn, tp) = recorded["confusion_matrix"]
    roc.plot(fp / (tn + fp), tp / (tp + fn), "o", color=COLORS["green"], ms=4, markeredgecolor="white", markeredgewidth=0.5)
    roc.set(xlim=(0, 1.02), ylim=(0, 1.02), xlabel="FPR", ylabel="TPR", xticks=[0, 0.5, 1], yticks=[0, 0.5, 1])
    roc.set_aspect("equal", adjustable="box")
    roc.set_title(translate(lang, "a  ROC: annotated pool", "a  ROC: размеченный пул"), loc="left", pad=10)
    format_ticks(roc, lang)
    roc.text(0.97, 0.09, f"AUC = {number(recorded['auc'], lang, 3)}\nn = {number(recorded['n'], lang)}",
             transform=roc.transAxes, ha="right", va="bottom", fontsize=8, linespacing=1.5)

    low, high = math.floor(scores.min()), math.ceil(scores.max())
    bins = np.linspace(low, high, 41)
    peaks = []
    for value, color, label in ((0, COLORS["orange"], translate(lang, "Non-relevant", "Нерелевантные")),
                                (1, COLORS["blue"], translate(lang, "Relevant", "Релевантные"))):
        density, _ = np.histogram(scores[truth == value], bins=bins, density=True)
        peaks.append(density.max())
        hist.stairs(density, bins, color=color, lw=1.1, label=label)
        hist.stairs(density, bins, color=color, fill=True, alpha=0.07, linewidth=0)
    hist.axvline(threshold, ymax=1.10 / 1.62, color=COLORS["gray"], ls="--", lw=0.9,
                 label=f"τ = {number(threshold, lang, 3)}".replace("-", "\N{MINUS SIGN}"))
    hist.set(xlim=(low, high), ylim=(0, max(peaks) * 1.62),
             xlabel=translate(lang, "Judge score", "Оценка судьи"),
             ylabel=translate(lang, "Density", "Плотность"))
    hist.set_title(translate(lang, "b  Judge scores", "b  Оценки судьи"), loc="left", pad=10)
    hist.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
    hist.yaxis.set_major_locator(MaxNLocator(nbins=3))
    format_ticks(hist, lang, axis="y")
    hist.legend(loc="upper left")
    return fig


def load_fullset(results):
    path = results / "fullset_summary.json"
    if not path.exists():
        return None
    summary = read_json(path)
    require(summary["schema_version"] == 1, "Unsupported fullset schema version")
    require(summary["status"] == "complete", "Fullset evaluation is not complete")
    population = summary["populations"]["all_queries"]
    rows = sorted(population["depths"], key=lambda row: row["k"])
    depths = [row["k"] for row in rows]
    require(depths == summary["protocol"]["depths"] and len(set(depths)) == len(depths),
            "Fullset depth grid disagrees with the protocol")
    require(all(k > 0 for k in depths), "Pooling depths must be positive")
    contrasts = {(row["contrast"], row["k"]): row for row in summary["paired_inference"]["all_queries"]}
    for row in rows:
        n = row["queries"]
        require(n == population["query_count"] and n > 0, "Fullset query count mismatch")
        require(0 <= row["positive_pairs"] <= row["candidate_pairs"], "Invalid positive/candidate counts")
        require(row["positive_queries"] + row["zero_idcg_queries"] == n, "Zero-IDCG population mismatch")
        for total, mean in (("candidate_pairs", "candidates_mean_all_queries"), ("positive_pairs", "positives_mean_all_queries")):
            require(np.isclose(row[total] / n, row[mean], rtol=0, atol=1e-10), "Fullset count/mean mismatch")
        for model in ("bm25", "e5", "bge", "rrf_variable", "rrf_fixed200"):
            value = row["models"][model]["ndcg10_mean_all_queries"]
            require(np.isfinite(value) and 0 <= value <= 1, f"Invalid fullset NDCG: {model}")
        for model in ("rrf_variable", "rrf_fixed200"):
            contrast = contrasts[(model + "_minus_e5", row["k"])]
            mean = row["models"][model]["ndcg10_mean_all_queries"] - row["models"]["e5"]["ndcg10_mean_all_queries"]
            require(np.isclose(contrast["mean_delta"], mean, rtol=0, atol=1e-12), "Fullset paired mean mismatch")
            low, high = contrast["bootstrap_ci95"]
            require(np.isfinite([low, high]).all() and low <= mean <= high and contrast["queries"] == n,
                    "Invalid fullset confidence interval")
    for field in ("candidate_pairs", "positive_pairs"):
        require(np.all(np.diff([row[field] for row in rows]) >= 0), f"Non-nested fullset counts: {field}")

    per_query = results / "fullset_perquery.npz"
    if per_query.exists():
        with np.load(per_query, allow_pickle=False) as data:
            require(data["ks"].tolist() == depths, "Fullset NPZ depth mismatch")
            require(len(data["query_ids"]) == population["query_count"], "Fullset NPZ query count mismatch")
            model_ids = data["model_names"].tolist()
            ndcg = data["ndcg"]
            require(np.isfinite(ndcg).all() and np.all((ndcg >= -1e-12) & (ndcg <= 1 + 1e-12)),
                    "Invalid fullset per-query NDCG")
            zero_idcg = data["idcg"] == 0
            require(np.all(ndcg[zero_idcg] == 0), "Zero-IDCG queries were not retained as zero")
            candidates, positives = data["candidate_count"], data["positive_count"]
            for index, row in enumerate(rows):
                require(int(candidates[:, index].sum()) == row["candidate_pairs"], "Fullset candidate NPZ mismatch")
                require(int(positives[:, index].sum()) == row["positive_pairs"], "Fullset positive NPZ mismatch")
                for model in ("bm25", "e5", "bge", "rrf_variable", "rrf_fixed200"):
                    actual = ndcg[:, index, model_ids.index(model)].mean()
                    require(np.isclose(actual, row["models"][model]["ndcg10_mean_all_queries"], rtol=0, atol=1e-12),
                            f"Fullset mean disagrees with NPZ: {model}/K={row['k']}")
    return summary


def depth_axis(ax, depths, lang):
    ax.set_xscale("log")
    ax.set_xlim(min(depths) / 1.13, max(depths) * 1.13)
    ax.set_xticks(depths, [str(k) for k in depths])
    ax.minorticks_off()
    ax.set_xlabel(translate(lang, "Pooling depth K (log scale)", "Глубина пула K (лог. шкала)"))
    ax.grid(axis="y", color=LIGHT, lw=0.45)
    ax.set_axisbelow(True)


def fullset_figure(summary, lang):
    rows = sorted(summary["populations"]["all_queries"]["depths"], key=lambda row: row["k"])
    depths = [row["k"] for row in rows]
    fig, (growth, scores) = plt.subplots(1, 2, figsize=(WIDTH_CM / 2.54, 7.0 / 2.54))
    fig.subplots_adjust(left=0.13, right=0.97, bottom=0.21, top=0.82, wspace=0.43)
    growth.plot(depths, [row["candidates_mean_all_queries"] for row in rows], "s-", color=COLORS["gray"],
                label=translate(lang, "Candidates", "Кандидаты"), markersize=4)
    growth.plot(depths, [row["positives_mean_all_queries"] for row in rows], "o-", color=COLORS["blue"],
                label=translate(lang, "Pseudo-positive", "Положительные\nпсевдометки"), markersize=4)
    growth.set_ylim(0, max(row["candidates_mean_all_queries"] for row in rows) * 1.08)
    growth.set_ylabel(translate(lang, "Mean documents / query", "Среднее на запрос"))
    growth.set_title(translate(lang, "a  Pool growth", "a  Рост пула"), loc="left", pad=10)
    growth.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    growth.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="none", framealpha=1)

    for model in MODELS:
        key = "rrf_variable" if model == "rrf3" else model
        scores.plot(depths, [row["models"][key]["ndcg10_mean_all_queries"] for row in rows],
                    marker=MODEL_MARKERS[model], color=MODEL_COLORS[model],
                    markerfacecolor="white" if model == "rrf3" else MODEL_COLORS[model],
                    markersize=4, label=MODEL_NAMES[model], zorder=4 if model == "rrf3" else 3)
    all_values = [row["models"][key]["ndcg10_mean_all_queries"] for row in rows for key in ("bm25", "e5", "bge", "rrf_variable")]
    scores.set_ylim(max(0, math.floor(min(all_values) * 20) / 20), min(1, math.ceil(max(all_values) * 20) / 20))
    scores.set_ylabel(translate(lang, "Mean NDCG@10", "Средний NDCG@10"))
    scores.set_title("b  NDCG@10", loc="left", pad=10)
    scores.yaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 5, 10]))
    format_ticks(scores, lang, axis="y", digits=2)
    scores.legend(loc="center", bbox_to_anchor=(0.54, 0.41), ncol=2, columnspacing=0.9, handlelength=1.1)
    for ax in (growth, scores):
        depth_axis(ax, depths, lang)
    return fig


def fixed_rrf_figure(summary, lang):
    rows = sorted(summary["populations"]["all_queries"]["depths"], key=lambda row: row["k"])
    depths = [row["k"] for row in rows]
    contrasts = {(row["contrast"], row["k"]): row for row in summary["paired_inference"]["all_queries"]}
    fig, (gain, coverage) = plt.subplots(1, 2, figsize=(WIDTH_CM / 2.54, 7.0 / 2.54))
    fig.subplots_adjust(left=0.16, right=0.97, bottom=0.21, top=0.75, wspace=0.47)
    for model, color, marker, label in (
        ("rrf_variable", COLORS["green"], "D", "RRF(3): top-K"),
        ("rrf_fixed200", COLORS["gray"], "s", translate(lang, "RRF(3): fixed top-200", "RRF(3): фикс. top-200")),
    ):
        items = [contrasts[(model + "_minus_e5", k)] for k in depths]
        means = np.array([item["mean_delta"] for item in items])
        ci = np.array([item["bootstrap_ci95"] for item in items])
        gain.errorbar(depths, means, yerr=[means - ci[:, 0], ci[:, 1] - means], fmt=marker + "-",
                      color=color, markerfacecolor="white" if model == "rrf_fixed200" else color,
                      markersize=2.7, elinewidth=0.85, capsize=2.5, capthick=0.85, barsabove=True, label=label)
    gain.axhline(0, color=COLORS["gray"], ls="--", lw=0.75, zorder=0)
    gain.set_ylabel("ΔNDCG@10")
    gain.set_title(translate(lang, "a  Gain vs E5 (95% CI)", "a  К E5 (95% ДИ)"), loc="left", pad=10)
    gain.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))
    format_ticks(gain, lang, axis="y", digits=2, signed=True)
    percent = [100 * row["models"]["rrf_fixed200"]["top10_outside_pool_total"] /
               row["models"]["rrf_fixed200"]["top10_count_total"] for row in rows]
    coverage.plot(depths, percent, "s-", color=COLORS["gray"], markerfacecolor="white", markersize=4)
    coverage.set_ylim(0, max(percent) * 1.10 if max(percent) else 1)
    coverage.set_ylabel(translate(lang, "Top-10 outside pool (%)", "Top-10 вне пула (%)"))
    coverage.set_title("b  RRF(3): top-200", loc="left", pad=10)
    coverage.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
    for ax in (gain, coverage):
        depth_axis(ax, depths, lang)
    handles, labels = gain.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.52, 0.99), ncol=2, columnspacing=1.2)
    return fig


def main():
    global OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results", help="Read-only evaluation input directory")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="Directory for PDF, PNG and SVG figures")
    parser.add_argument("--language", choices=["en", "ru", "both"], default="both")
    args = parser.parse_args()
    OUTPUT = args.output
    OUTPUT.mkdir(parents=True, exist_ok=True)
    configure_style()
    summary, truth, scores = load_manual(args.results)
    fullset = load_fullset(args.results)
    records = []
    languages = ("en", "ru") if args.language == "both" else (args.language,)
    for lang in languages:
        export(protocol_figure(summary, lang), "protocol", lang, records,
               {"source": "manual_summary.json", "queries": summary["queries"]})
        export(manual_figure(summary, lang), "manual_effect", lang, records,
               {"sources": ["manual_summary.json", "manual_per_query.npz"], "systems": list(MODEL_NAMES.values()),
                "queries": summary["queries"], "ci_source": "metrics.<model>.human_minus_official.ci95"})
        export(judge_figure(summary, truth, scores, lang), "judge_diagnostics", lang, records,
               {"sources": ["manual_summary.json", "manual_judge_diagnostics.npz"],
                "population": "Valid labels and nonempty text; all eligible annotated pairs INCLUDING training; not held-out",
                "n": len(truth), "auc": summary["judge_valid_text_and_labels"]["auc"],
                "threshold": summary["judge_threshold"], "histogram": "40 shared bins; each class normalized separately"})
        if fullset is not None:
            shared = {"sources": ["fullset_summary.json"], "population": "all_queries; zero-IDCG queries retained",
                      "queries": fullset["populations"]["all_queries"]["query_count"],
                      "depths": fullset["protocol"]["depths"], "x_axis": "logarithmic pooling depth K",
                      "interpretation": fullset["validity_notes"]}
            export(fullset_figure(fullset, lang), "fullset_pooling", lang, records,
                   {**shared, "rrf_source": "rrf_variable", "label": "RRF(3)",
                    "means": "candidates_mean_all_queries, positives_mean_all_queries, ndcg10_mean_all_queries"})
            export(fixed_rrf_figure(fullset, lang), "fullset_fixed_rrf_diagnostic", lang, records,
                   {**shared, "ci_source": "paired_inference.all_queries.<contrast>.bootstrap_ci95",
                    "contrasts": ["rrf_variable_minus_e5", "rrf_fixed200_minus_e5"],
                    "coverage": "100 * top10_outside_pool_total / top10_count_total for rrf_fixed200"})
    if fullset is None:
        print("Fullset figures skipped: fullset_summary.json is not available.")
    source_names = ["manual_summary.json", "manual_per_query.npz", "manual_judge_diagnostics.npz"]
    if fullset is not None:
        source_names.append("fullset_summary.json")
        if (args.results / "fullset_perquery.npz").exists():
            source_names.append("fullset_perquery.npz")
    sources = {name: hashlib.sha256((args.results / name).read_bytes()).hexdigest() for name in source_names}
    manifest = {"width_cm": WIDTH_CM, "dpi": DPI, "font": "DejaVu Sans", "source_sha256": sources,
                "fullset_available": fullset is not None, "figures": records}
    (OUTPUT / "figure_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
