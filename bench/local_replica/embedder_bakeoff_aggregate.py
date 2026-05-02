"""Read completed v010-emb-*/summary.json files and produce a comparison
table + decision summary against SC-B1 / SC-B2.

Usable mid-run — only includes embedders whose summary.json exists.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPLICA = Path(__file__).resolve().parent
RUNS = REPLICA / "runs"

# Same slug→spec mapping as embedder_bakeoff.py.
EMBEDDERS = [
    ("3small", "text-embedding-3-small", "openai", "current default"),
    ("3large", "text-embedding-3-large", "openai", "OpenAI premium"),
    ("bge-large", "BAAI/bge-large-en-v1.5", "local", "BGE family"),
    ("mxbai-large", "mixedbread-ai/mxbai-embed-large-v1", "local", "Mixedbread"),
    ("nomic-text", "nomic-ai/nomic-embed-text-v1.5", "local", "Nomic w/ task prefix"),
]

# SC bars from specs/v010-leaderboard-sweep.md.
RUNNER_UP_COST = 5464.0  # scrapy+md leaderboard cost-at-scale
SCB2_BAND = 0.02  # MRR neutrality band


def collect() -> list[dict]:
    rows = []
    for slug, spec, kind, notes in EMBEDDERS:
        summary_path = RUNS / f"v010-emb-{slug}" / "summary.json"
        if not summary_path.is_file():
            rows.append({"slug": slug, "spec": spec, "kind": kind,
                         "notes": notes, "missing": True})
            continue
        s = json.loads(summary_path.read_text())
        full = s.get("full_report") or {}
        rows.append({
            "slug": slug,
            "spec": spec,
            "kind": kind,
            "notes": notes,
            "mrr_mean": s.get("mrr_mean"),
            "mrr_median": s.get("mrr_median"),
            "by_category": s.get("by_category", {}),
            "cost_at_scale": full.get("cost_at_scale_50M_dollars"),
            "chunks_per_page_observed": (full.get("assumptions") or {}).get("chunks_per_page_observed"),
            "embed_dollars_per_M_chunks": (full.get("assumptions") or {}).get("embed_dollars_per_M_chunks"),
        })
    return rows


def main() -> None:
    rows = collect()
    baseline = next((r for r in rows if r["slug"] == "3small" and not r.get("missing")), None)
    if baseline is None:
        print("3small baseline missing — cannot evaluate SC-B*", file=sys.stderr)
    base_mrr = baseline["mrr_mean"] if baseline else None
    base_cost = baseline["cost_at_scale"] if baseline else None
    half_cost = round(base_cost / 2, 2) if base_cost else None
    scb1_bar = min(RUNNER_UP_COST, half_cost) if half_cost else RUNNER_UP_COST

    # Print main comparison table.
    print(f"\n=== Embedder bake-off (partial OK) ===")
    print(f"Baseline (3-small): MRR={base_mrr}, cost-at-scale=${base_cost}")
    print(f"SC-B1 budget: cost ≤ min($5,464 runner-up, ${half_cost} = baseline/2) = ${scb1_bar}")
    print(f"SC-B2 band: MRR within ±{SCB2_BAND} of {base_mrr} → "
          f"[{round((base_mrr or 0) - SCB2_BAND, 4)}, {round((base_mrr or 0) + SCB2_BAND, 4)}]")
    print()
    header = f"{'embedder':<14} {'MRR':>7} {'Δ vs 3-small':>13} {'$/50M':>10} {'SC-B1':>6} {'SC-B2':>6}"
    print(header)
    print("-" * len(header))
    for r in rows:
        slug = r["slug"]
        if r.get("missing"):
            print(f"{slug:<14} {'  pending':>50}")
            continue
        mrr = r["mrr_mean"]
        delta = round(mrr - base_mrr, 4) if base_mrr is not None else None
        cost = r["cost_at_scale"]
        scb1 = "✓" if (cost is not None and cost <= scb1_bar) else "✗"
        scb2 = "✓" if (delta is not None and abs(delta) <= SCB2_BAND) else "✗"
        scb1 = "—" if slug == "3small" else scb1
        scb2 = "—" if slug == "3small" else scb2
        delta_s = f"{delta:+.4f}" if delta is not None else "n/a"
        print(f"{slug:<14} {mrr:>7.4f} {delta_s:>13} {cost:>10.0f} {scb1:>6} {scb2:>6}")

    # Pareto decision: candidates passing both SC-B1 and SC-B2.
    print()
    candidates = []
    for r in rows:
        if r.get("missing") or r["slug"] == "3small":
            continue
        cost = r["cost_at_scale"]
        if cost is None or cost > scb1_bar:
            continue
        delta = abs((r["mrr_mean"] or 0) - (base_mrr or 0))
        if delta > SCB2_BAND:
            continue
        candidates.append(r)

    if not candidates:
        print("No candidate passes both SC-B1 and SC-B2.")
        print("→ Stay on text-embedding-3-small.")
    else:
        # Pick the candidate with the highest MRR (tiebreak: lowest cost).
        winner = max(candidates, key=lambda r: (r["mrr_mean"] or 0, -((r["cost_at_scale"] or 0))))
        print(f"WINNER: {winner['slug']} ({winner['spec']})")
        print(f"  MRR={winner['mrr_mean']:.4f}, cost=${winner['cost_at_scale']:.0f}/50M")
        print(f"→ Flip default in production paths to {winner['spec']}.")

    # Per-category for the relevant rows.
    print()
    print("Per-category MRR mean:")
    cats = []
    for r in rows:
        if not r.get("missing") and r.get("by_category"):
            cats = list(r["by_category"].keys())
            break
    if cats:
        print(f"{'embedder':<14} " + "  ".join(f"{c[:10]:>10}" for c in cats))
        for r in rows:
            if r.get("missing"):
                continue
            print(f"{r['slug']:<14} " + "  ".join(
                f"{r['by_category'].get(c, {}).get('mrr_mean', 0):>10.3f}" for c in cats))

    # Save aggregate JSON.
    out_path = REPLICA / "embedder_bakeoff.json"
    payload = {
        "rows": rows,
        "baseline_slug": "3small",
        "scb1_bar_dollars": scb1_bar,
        "scb2_band_mrr": SCB2_BAND,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\n→ wrote {out_path}")


if __name__ == "__main__":
    main()
