"""Analyze chunk_sweep_results.tsv — produce ranked tables + per-category
+ per-site breakdowns + multi-trial median (min-max) per config.

Usage:
    python bench/local_replica/chunk_sweep_analyze.py \\
        [--tsv bench/local_replica/chunk_sweep_results.tsv] \\
        [--top N] [--md OUT.md]
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def load(tsv: Path) -> List[Dict[str, Any]]:
    rows = list(csv.DictReader(tsv.open(), delimiter="\t"))
    for r in rows:
        for k in ("max_words", "min_words", "section_overlap_words", "overlap_words",
                  "n_sites", "n_pages_total", "n_chunks_total"):
            try:
                r[k] = int(float(r[k]))
            except (ValueError, TypeError, KeyError):
                r[k] = 0
        for k in ("avg_words_per_chunk", "mrr_mean", "mrr_median", "elapsed_sec"):
            try:
                r[k] = float(r[k])
            except (ValueError, TypeError, KeyError):
                r[k] = 0.0
        r["pcjson"] = json.loads(r.get("per_site_mrr_json") or "{}")
    return [r for r in rows if r.get("status") == "completed"]


def fmt_pct_baseline(val: float, baseline: float) -> str:
    if baseline == 0:
        return ""
    delta = val - baseline
    pct = delta / baseline * 100
    return f"{delta:+.4f} ({pct:+.1f}%)"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--tsv", default="bench/local_replica/chunk_sweep_results.tsv")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--embedder", default="st-mini")
    p.add_argument("--run-dir", default=None,
                   help="Filter to single run-dir (default: all)")
    p.add_argument("--md", help="Write markdown report to this path")
    args = p.parse_args()

    rows = load(Path(args.tsv))
    rows = [r for r in rows if r["embedder"] == args.embedder]
    if args.run_dir:
        rows = [r for r in rows if r["run_dir"] == args.run_dir]

    out: List[str] = []

    def emit(s: str = "") -> None:
        out.append(s)
        print(s)

    emit(f"# chunk_sweep analysis (embedder={args.embedder})")
    emit()

    # 1) Per-trial analysis: each (config, run_dir) is a row. Group configs
    # across run_dirs for multi-trial median/min/max.
    by_cfg: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_cfg[r["label"]].append(r)

    # Single-trial summary (uses first run_dir per config)
    emit("## Single-trial ranking (1 run per config, by mean MRR)")
    emit()
    if not args.run_dir:
        # Rank against the first run_dir we see
        first_rd = rows[0]["run_dir"] if rows else "?"
        emit(f"_(within run_dir = {first_rd}; for multi-trial see section below)_")
        emit()
        single = [r for r in rows if r["run_dir"] == first_rd]
    else:
        single = rows
    single.sort(key=lambda r: r["mrr_mean"], reverse=True)
    baseline_mrr = next((r["mrr_mean"] for r in single
                         if r["label"] == "baseline-v099"), None)

    emit("| rank | label | max | min | ovl | strategy | chunks | avg_w | MRR | median | vs baseline |")
    emit("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(single[:args.top]):
        strat = []
        for k in ("adaptive", "auto_extract_title", "prepend_first_paragraph", "strip_markdown_links"):
            if r.get(k) in ("True", True):
                strat.append(k.replace("_", "-").replace("auto-extract-title", "autotitle")
                             .replace("prepend-first-paragraph", "prepend").replace("strip-markdown-links", "strip"))
        strat_s = "+".join(strat) if strat else "—"
        delta = ""
        if baseline_mrr is not None and r["label"] != "baseline-v099":
            delta = fmt_pct_baseline(r["mrr_mean"], baseline_mrr)
        emit(f"| {i+1} | {r['label']} | {r['max_words']} | {r['min_words']} | "
             f"{r['section_overlap_words']} | {strat_s} | {r['n_chunks_total']} | "
             f"{r['avg_words_per_chunk']:.0f} | {r['mrr_mean']:.4f} | "
             f"{r['mrr_median']:.4f} | {delta} |")

    # 2) Per-category for top-N
    emit()
    emit(f"## Per-category MRR for top {args.top}")
    emit()
    all_cats = set()
    for r in single[:args.top]:
        all_cats.update(r["pcjson"].get("per_category", {}))
    cat_order = ["api-function", "code-example", "conceptual", "cross-page",
                 "factual-lookup", "js-rendered"]
    cat_order = [c for c in cat_order if c in all_cats] + sorted(all_cats - set(cat_order))
    header = "| label | mean | " + " | ".join(cat_order) + " |"
    sep = "|---|---|" + "---|" * len(cat_order)
    emit(header)
    emit(sep)
    for r in single[:args.top]:
        per_cat = r["pcjson"].get("per_category", {})
        row = f"| {r['label']} | {r['mrr_mean']:.4f} | "
        row += " | ".join(f"{per_cat.get(c, 0):.4f}" for c in cat_order) + " |"
        emit(row)

    # 3) Per-site for top-3 (where it matters most)
    emit()
    emit(f"## Per-site MRR for top 3")
    emit()
    all_sites: List[str] = []
    for r in single[:3]:
        for s in r["pcjson"].get("mrr", {}):
            if s not in all_sites:
                all_sites.append(s)
    header = "| label | mean | " + " | ".join(all_sites) + " |"
    sep = "|---|---|" + "---|" * len(all_sites)
    emit(header)
    emit(sep)
    for r in single[:3]:
        site_mrr = r["pcjson"].get("mrr", {})
        row = f"| {r['label']} | {r['mrr_mean']:.4f} | "
        row += " | ".join(f"{site_mrr.get(s, 0):.3f}" for s in all_sites) + " |"
        emit(row)

    # 4) Cherry-pick ceiling — best per-site config across the whole sweep
    emit()
    emit("## Cherry-pick ceiling (per-site dispatch upper bound)")
    emit()
    site_best: Dict[str, tuple[float, str]] = {}
    for r in single:
        for s, v in r["pcjson"].get("mrr", {}).items():
            chunks = r["pcjson"].get("meta", {}).get(s, {}).get("chunks", 0)
            if chunks > 0 and (s not in site_best or v > site_best[s][0]):
                site_best[s] = (v, r["label"])
    if site_best:
        emit("| site | best MRR | best config |")
        emit("|---|---|---|")
        ceiling_total = 0.0
        for s in all_sites:
            if s in site_best:
                v, lbl = site_best[s]
                ceiling_total += v
                emit(f"| {s} | {v:.4f} | {lbl} |")
        ceiling = ceiling_total / len(site_best) if site_best else 0
        emit()
        emit(f"**Cherry-pick ceiling MRR (perfect per-site dispatcher): {ceiling:.4f}**")
        if baseline_mrr:
            emit(f"_Headroom over baseline-v099 (MRR {baseline_mrr:.4f}): {ceiling - baseline_mrr:+.4f} ({(ceiling - baseline_mrr) / baseline_mrr * 100:+.1f}%)_")

    # 5) Multi-trial section (if any config has > 1 run_dir)
    multi = {label: trials for label, trials in by_cfg.items() if len(trials) > 1}
    if multi:
        emit()
        emit("## Multi-trial median (min – max) per config")
        emit()
        emit("| label | n_trials | mean MRR median (min-max) | mean MRR mean | n_chunks median |")
        emit("|---|---|---|---|---|")
        for label, trials in sorted(multi.items(),
                                    key=lambda kv: -statistics.median([t["mrr_mean"] for t in kv[1]])):
            mrrs = [t["mrr_mean"] for t in trials]
            chunks = [t["n_chunks_total"] for t in trials]
            emit(f"| {label} | {len(trials)} | "
                 f"{statistics.median(mrrs):.4f} ({min(mrrs):.4f}-{max(mrrs):.4f}) | "
                 f"{statistics.mean(mrrs):.4f} | {statistics.median(chunks):.0f} |")

    if args.md:
        Path(args.md).write_text("\n".join(out) + "\n")
        print(f"\nWritten: {args.md}")


if __name__ == "__main__":
    main()
