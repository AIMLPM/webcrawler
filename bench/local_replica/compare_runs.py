"""Side-by-side comparison of two replica runs.

Reads `runs/<label>/summary.json` for both labels and prints a delta
table covering speed, MRR, the 4 leadership dimensions, and per-site
MRR (for SC-3's "no single-site regression >0.10" check).

Usage:
    python compare_runs.py --baseline v098-baseline --candidate v099-rc1

If the baseline summary lives outside the local runs/ dir (e.g. in a
worktree from a different git ref), pass --baseline-path explicitly.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPLICA = Path(__file__).resolve().parent
RUNS = REPLICA / "runs"


def load(label: str, path: Path = None) -> dict:
    if path is not None:
        return json.loads(path.read_text())
    summary = RUNS / label / "summary.json"
    return json.loads(summary.read_text())


def per_site_map(label: str, path: Path = None) -> dict:
    """Return {site_name: {mrr, pages, wallclock}} from per-site reports."""
    base = path.parent if path is not None else RUNS / label
    out = {}
    for site_dir in base.iterdir():
        rpt = site_dir / "report.json"
        if not rpt.is_file():
            continue
        d = json.loads(rpt.read_text())
        out[d.get("name", site_dir.name)] = {
            "mrr": d.get("mrr", 0.0),
            "pages": d.get("pages", 0),
            "wallclock": d.get("wallclock", 0.0),
        }
    return out


def delta_str(a: float, b: float, fmt: str = "{:+.3f}") -> str:
    """Format b - a, with arrow for direction."""
    d = b - a
    arrow = "↑" if d > 0 else ("↓" if d < 0 else "·")
    return f"{fmt.format(d)} {arrow}"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--baseline-path", help="Override path to baseline summary.json")
    p.add_argument("--candidate-path", help="Override path to candidate summary.json")
    p.add_argument("--out", help="Write comparison markdown here")
    args = p.parse_args()

    bp = Path(args.baseline_path) if args.baseline_path else None
    cp = Path(args.candidate_path) if args.candidate_path else None

    base = load(args.baseline, bp)
    cand = load(args.candidate, cp)

    base_sites = per_site_map(args.baseline, bp)
    cand_sites = per_site_map(args.candidate, cp)

    lines: list[str] = []

    def line(s: str = "") -> None:
        lines.append(s)
        print(s)

    line(f"# Comparison: {args.baseline} vs {args.candidate}")
    line()
    line("## Aggregate")
    line()
    line("| metric | baseline | candidate | delta |")
    line("|---|---|---|---|")
    for key, label, fmt in [
        ("pages_per_sec_crawl_only", "speed (p/s, crawl-only)", "{:+.3f}"),
        ("pages_per_sec_ex_npr", "speed (p/s, ex-NPR)", "{:+.3f}"),
        ("pages_per_sec_end_to_end", "speed (p/s, end-to-end)", "{:+.3f}"),
        ("mrr_mean", "MRR mean", "{:+.4f}"),
        ("mrr_median", "MRR median", "{:+.4f}"),
        ("n_pages_total", "pages crawled", "{:+d}"),
        ("wallclock_total_sec", "wallclock total (s)", "{:+.1f}"),
    ]:
        bv = base.get(key, 0)
        cv = cand.get(key, 0)
        if isinstance(bv, (int, float)) and isinstance(cv, (int, float)):
            d = cv - bv
            arrow = "↑" if d > 0 else ("↓" if d < 0 else "·")
            line(f"| {label} | {bv} | {cv} | {fmt.format(d)} {arrow} |")

    # Full-report dimensions if both have them
    if "full_report" in base and "full_report" in cand:
        line()
        line("## 4 leadership dimensions (SC-6)")
        line()
        line("| dimension | baseline | candidate | delta |")
        line("|---|---|---|---|")
        for key, label, fmt in [
            ("content_signal_pct", "content_signal_pct", "{:+.2f}"),
            ("cost_at_scale_50M_dollars", "cost_at_scale_50M ($)", "{:+.2f}"),
            ("pipeline_timing_1k_pages_sec", "pipeline_timing_1k (s)", "{:+.2f}"),
        ]:
            bv = base["full_report"].get(key)
            cv = cand["full_report"].get(key)
            if bv is not None and cv is not None:
                d = cv - bv
                arrow = "↑" if d > 0 else ("↓" if d < 0 else "·")
                line(f"| {label} | {bv} | {cv} | {fmt.format(d)} {arrow} |")

    # Per-site MRR delta — SC-3 enforcement
    line()
    line("## Per-site MRR (SC-3: no regression >0.10)")
    line()
    line("| site | baseline | candidate | delta | flag |")
    line("|---|---|---|---|---|")
    sc3_violations = []
    all_sites = sorted(set(base_sites) | set(cand_sites))
    for site in all_sites:
        bv = base_sites.get(site, {}).get("mrr", 0.0)
        cv = cand_sites.get(site, {}).get("mrr", 0.0)
        d = cv - bv
        flag = ""
        if d < -0.10:
            flag = "❌ SC-3 VIOLATION"
            sc3_violations.append((site, d))
        elif d > 0.05:
            flag = "✅ improved"
        elif d < -0.05:
            flag = "⚠ minor regress"
        arrow = "↑" if d > 0 else ("↓" if d < 0 else "·")
        line(f"| {site} | {bv:.3f} | {cv:.3f} | {d:+.3f} {arrow} | {flag} |")

    line()
    line("## Per-site speed (p/s)")
    line()
    line("| site | baseline | candidate | delta |")
    line("|---|---|---|---|")
    for site in all_sites:
        bs = base_sites.get(site, {})
        cs = cand_sites.get(site, {})
        bp_pps = (bs.get("pages", 0) / bs.get("wallclock", 1)) if bs.get("wallclock", 0) > 0 else 0
        cp_pps = (cs.get("pages", 0) / cs.get("wallclock", 1)) if cs.get("wallclock", 0) > 0 else 0
        d = cp_pps - bp_pps
        arrow = "↑" if d > 0 else ("↓" if d < 0 else "·")
        line(f"| {site} | {bp_pps:.2f} | {cp_pps:.2f} | {d:+.2f} {arrow} |")

    line()
    if sc3_violations:
        line(f"### ❌ SC-3 violations: {len(sc3_violations)}")
        for s, d in sc3_violations:
            line(f"  - **{s}** regressed {d:+.3f}")
    else:
        line("### ✅ No SC-3 violations (no per-site MRR regression >0.10)")

    if args.out:
        Path(args.out).write_text("\n".join(lines) + "\n")
        print(f"\nWritten to {args.out}")


if __name__ == "__main__":
    main()
