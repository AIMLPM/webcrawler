#!/usr/bin/env python3
"""Pre-flight check for the 7-tool benchmark comparison.

Run this before benchmarks/benchmark_all_tools.py to verify all tools are installed,
binaries are present, environment variables are set, and the network is reachable.

Usage:
    python benchmarks/preflight.py              # check only
    python benchmarks/preflight.py --install    # check, then install missing packages
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

# Suppress noisy import warnings (e.g. requests version mismatch in fresh venvs)
os.environ.setdefault("PYTHONWARNINGS", "ignore")

# ---------------------------------------------------------------------------
# Colour helpers (graceful fallback if terminal doesn't support ANSI)
# ---------------------------------------------------------------------------

_NO_COLOR = not sys.stdout.isatty() or os.environ.get("NO_COLOR")


def _c(text: str, code: str) -> str:
    return text if _NO_COLOR else f"\033[{code}m{text}\033[0m"


def green(t):  return _c(t, "32")
def yellow(t): return _c(t, "33")
def red(t):    return _c(t, "31")
def bold(t):   return _c(t, "1")
def dim(t):    return _c(t, "2")


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BENCH_DIR = Path(__file__).parent
REPO_ROOT  = BENCH_DIR.parent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _can_import(*modules: str) -> bool:
    for mod in modules:
        try:
            __import__(mod)
        except ImportError:
            return False
    return True


def _check_network(host: str, port: int = 80, timeout: float = 3.0) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        with socket.create_connection((host, port)):
            return True
    except OSError:
        return False


def _pip(*args: str, pip_exe: str | None = None) -> bool:
    """Run pip install, suppress [notice] upgrade hints, return True on success."""
    python = pip_exe or sys.executable
    cmd = [python, "-m", "pip", "install", "--quiet", *args]
    print(dim(f"    $ pip install {' '.join(args)}"))
    result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    # Print stderr but filter out pip's [notice] lines
    for line in result.stderr.splitlines():
        if not line.startswith("[notice]"):
            print(line, file=sys.stderr)
    return result.returncode == 0


def _ensure_venv() -> str:
    """Create .venv in the repo root if not already in a venv. Returns the venv Python path."""
    venv_dir = REPO_ROOT / ".venv"
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    if venv_python.exists():
        return str(venv_python)

    print(f"\n  {bold('Creating virtual environment')} at {dim(str(venv_dir))} ...")
    print(dim(f"    $ python3 -m venv {venv_dir}"))
    result = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)])
    if result.returncode != 0:
        print(red("  ✗ Failed to create virtual environment"))
        sys.exit(1)
    print(green("  ✓ Virtual environment created"))
    return str(venv_python)


def _in_venv() -> bool:
    """Return True if we're already running inside a virtual environment."""
    return sys.prefix != sys.base_prefix


def _go_exe() -> str | None:
    """Return the path to the go executable, or None if not found."""
    return shutil.which("go")


def _brew_exe() -> str | None:
    """Return the path to brew, or None if not found."""
    return shutil.which("brew")


def _chromium_installed() -> bool:
    """Return True if Playwright's chromium browser is installed."""
    if not _can_import("playwright.sync_api"):
        return False
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _firecrawl_creds() -> tuple[bool, bool, str]:
    """Return (pkg_ok, key_ok, mode_label)."""
    pkg_ok = _can_import("firecrawl")
    fc_key = bool(os.environ.get("FIRECRAWL_API_KEY"))
    fc_url = bool(os.environ.get("FIRECRAWL_API_URL"))

    if not (fc_key or fc_url) and _can_import("dotenv"):
        try:
            from dotenv import dotenv_values
            env_file = REPO_ROOT / ".env"
            if env_file.exists():
                env = dotenv_values(env_file)
                fc_key = bool(env.get("FIRECRAWL_API_KEY"))
                fc_url = bool(env.get("FIRECRAWL_API_URL"))
        except Exception:
            pass

    mode = "SaaS API key" if fc_key else ("self-hosted URL" if fc_url else "")
    return pkg_ok, (fc_key or fc_url), mode


# ---------------------------------------------------------------------------
# Check recorder
# ---------------------------------------------------------------------------

# Each entry: (label, ok: bool|None, detail: str, warn_only: bool)
_results: list[tuple[str, bool | None, str, bool]] = []


def check(label: str, ok: bool | None, detail: str = "", warn_only: bool = False) -> bool | None:
    if ok is None:
        symbol = dim("~")
    elif ok:
        symbol = green("✓")
    elif warn_only:
        symbol = yellow("!")
    else:
        symbol = red("✗")
    _results.append((label, ok, detail, warn_only))
    suffix = f"  {dim(detail)}" if detail else ""
    print(f"  {symbol}  {label}{suffix}")
    return ok


# ---------------------------------------------------------------------------
# All checks
# ---------------------------------------------------------------------------


def run_checks() -> tuple[dict[str, bool], bool]:
    """Run all pre-flight checks. Clears and repopulates _results."""
    _results.clear()

    # ── 1. Python version ──────────────────────────────────────────────────
    print(bold("\n── Python ──────────────────────────────────────────────"))
    py = sys.version_info
    check(
        f"Python {py.major}.{py.minor}.{py.micro}",
        py >= (3, 10),
        detail="" if py >= (3, 10) else "requires Python ≥ 3.10",
    )

    # ── 2. Core dependencies ───────────────────────────────────────────────
    print(bold("\n── Core dependencies ───────────────────────────────────"))

    core_deps = [
        ("markcrawl",      ["markcrawl.core"],  "pip install -e .  (from repo root)"),
        ("beautifulsoup4", ["bs4"],             "pip install beautifulsoup4"),
        ("markdownify",    ["markdownify"],     "pip install markdownify"),
        ("requests",       ["requests"],        "pip install requests"),
    ]
    for name, mods, hint in core_deps:
        ok = _can_import(*mods)
        check(name, ok, detail="" if ok else f"→ {hint}")

    psutil_ok = _can_import("psutil")
    check(
        "psutil (memory tracking)",
        psutil_ok,
        detail="" if psutil_ok else "→ pip install psutil  (optional — falls back to resource module)",
        warn_only=True,
    )

    dotenv_ok = _can_import("dotenv")
    check(
        "python-dotenv (.env loading)",
        dotenv_ok,
        detail="" if dotenv_ok else "→ pip install python-dotenv  (optional — set env vars manually instead)",
        warn_only=True,
    )

    # ── 3. Benchmark tools ─────────────────────────────────────────────────
    print(bold("\n── Benchmark tools ─────────────────────────────────────"))
    print(dim("  (tools marked ! will be skipped; benchmark still runs with available tools)\n"))

    tool_results: dict[str, bool] = {}

    ok = _can_import("markcrawl.core")
    tool_results["markcrawl"] = ok
    check("markcrawl", ok, detail="" if ok else "→ pip install -e .  from repo root")

    ok = _can_import("scrapy", "markdownify")
    tool_results["scrapy+md"] = ok
    check("scrapy+md", ok, detail="" if ok else "→ pip install scrapy markdownify", warn_only=True)

    ok = _can_import("crawl4ai")
    tool_results["crawl4ai"] = ok
    check("crawl4ai", ok, detail="" if ok else "→ pip install crawl4ai", warn_only=True)

    crawlee_pkg = _can_import("crawlee")
    if crawlee_pkg:
        bf_ok = _can_import("browserforge")
        tool_results["crawlee"] = bf_ok
        check(
            "crawlee",
            bf_ok,
            detail="" if bf_ok else "→ pip install browserforge  (missing sub-dependency)",
            warn_only=True,
        )
    else:
        tool_results["crawlee"] = False
        check("crawlee", False, detail="→ pip install 'crawlee[playwright]'", warn_only=True)

    ok = _can_import("playwright.sync_api")
    tool_results["playwright"] = ok
    check("playwright (raw)", ok, detail="" if ok else "→ pip install playwright", warn_only=True)

    colly_bin = BENCH_DIR / "colly_crawler" / "colly_crawler"
    colly_ok = colly_bin.is_file()
    tool_results["colly+md"] = colly_ok
    if colly_ok:
        check("colly+md (Go binary)", True, detail=str(colly_bin))
    else:
        go_exe = _go_exe()
        if go_exe:
            check(
                "colly+md (Go binary)", False, warn_only=True,
                detail=f"→ Go found ({go_exe}) but binary not built — will build automatically with --install",
            )
        elif _brew_exe():
            check(
                "colly+md (Go binary)", False, warn_only=True,
                detail="→ Go not found — will install via Homebrew + build automatically with --install",
            )
        else:
            check(
                "colly+md (Go binary)", False, warn_only=True,
                detail="→ Go not found and Homebrew not available — install Go from https://go.dev/dl/ then re-run",
            )

    fc_pkg, fc_cred, fc_mode = _firecrawl_creds()
    tool_results["firecrawl"] = fc_pkg and fc_cred
    if not fc_pkg:
        check("firecrawl", False, detail="→ pip install firecrawl-py", warn_only=True)
    elif not fc_cred:
        check(
            "firecrawl", False, warn_only=True,
            detail="→ set FIRECRAWL_API_KEY (SaaS) or FIRECRAWL_API_URL (self-hosted) in .env or environment",
        )
    else:
        check("firecrawl", True, detail=f"({fc_mode} found)")

    # ── 4. Playwright browsers ─────────────────────────────────────────────
    print(bold("\n── Playwright browsers ─────────────────────────────────"))

    needs_playwright = (
        tool_results.get("crawl4ai")
        or tool_results.get("crawlee")
        or tool_results.get("playwright")
    )

    if not needs_playwright:
        check("Playwright browsers", None, detail="no Playwright-based tools installed")
    elif not _can_import("playwright.sync_api"):
        check("Playwright browsers", False, detail="→ pip install playwright && playwright install chromium")
    else:
        chromium_ok = _chromium_installed()
        check(
            "Playwright → chromium",
            chromium_ok,
            detail="" if chromium_ok else "→ playwright install chromium",
            warn_only=True,
        )

    # ── 5. Network ─────────────────────────────────────────────────────────
    print(bold("\n── Network (test sites) ────────────────────────────────"))

    sites = [
        ("quotes.toscrape.com",  80,  "quotes-toscrape (15 pages)"),
        ("books.toscrape.com",   80,  "books-toscrape (60 pages)"),
        ("fastapi.tiangolo.com", 443, "fastapi-docs (25 pages)"),
        ("docs.python.org",      443, "python-docs (20 pages)"),
    ]
    for host, port, label in sites:
        ok = _check_network(host, port)
        check(label, ok, detail="" if ok else f"→ {host}:{port} unreachable", warn_only=True)

    return tool_results, dotenv_ok


# ---------------------------------------------------------------------------
# Ready status (printed last — clean summary of everything)
# ---------------------------------------------------------------------------

def print_ready_status(tool_results: dict[str, bool]) -> None:
    """Print a clean at-a-glance status board after all checks/installs."""
    print(bold("\n══ Ready status ════════════════════════════════════════\n"))

    def row(label: str, ok: bool | None, note: str = "") -> None:
        if ok is None:
            sym = dim("~")
        elif ok:
            sym = green("✓")
        else:
            sym = red("✗")
        suffix = f"  {dim(note)}" if note else ""
        print(f"  {sym}  {label}{suffix}")

    # ── Environment ────────────────────────────────────────────────────────
    print(dim("  Environment"))
    py = sys.version_info
    row(f"Python {py.major}.{py.minor}.{py.micro}", py >= (3, 10))

    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    if _in_venv():
        row("Virtual environment", True, note=sys.prefix)
    elif venv_python.exists():
        row("Virtual environment (.venv)", True, note=str(venv_python.parent.parent))
    else:
        row("Virtual environment", False, note="→ will be created by --install")

    brew = _brew_exe()
    row("Homebrew", bool(brew), note=brew or "→ https://brew.sh")

    go = _go_exe()
    row("Go  (for Colly binary)", bool(go), note=go or "→ brew install go  or  https://go.dev/dl/")

    # ── Benchmark tools ────────────────────────────────────────────────────
    print()
    available_count = sum(1 for ok in tool_results.values() if ok)
    print(dim(f"  Benchmark tools  ({available_count}/7 ready)"))

    tool_labels = {
        "markcrawl":  "markcrawl  (core crawler + URL discovery)",
        "scrapy+md":  "scrapy + markdownify",
        "crawl4ai":   "crawl4ai",
        "crawlee":    "crawlee",
        "playwright": "playwright  (raw)",
        "colly+md":   "colly + markdownify  (Go binary)",
        "firecrawl":  "firecrawl",
    }
    for key, label in tool_labels.items():
        row(label, tool_results.get(key, False))

    # Playwright browser — check independently
    needs_pw = tool_results.get("crawl4ai") or tool_results.get("crawlee") or tool_results.get("playwright")
    if needs_pw:
        chromium_ok = _chromium_installed()
        row("Playwright chromium browser", chromium_ok,
            note="" if chromium_ok else "→ playwright install chromium")

    # FireCrawl credentials (separate from the package)
    fc_pkg, fc_cred, fc_mode = _firecrawl_creds()
    if fc_pkg:
        row(
            "FireCrawl API key / URL",
            fc_cred,
            note=fc_mode if fc_cred else "→ set FIRECRAWL_API_KEY or FIRECRAWL_API_URL in .env",
        )

    # ── Network ────────────────────────────────────────────────────────────
    print()
    sites = [
        ("quotes.toscrape.com",  80),
        ("books.toscrape.com",   80),
        ("fastapi.tiangolo.com", 443),
        ("docs.python.org",      443),
    ]
    net_results = [_check_network(h, p) for h, p in sites]
    net_ok = sum(net_results)
    print(dim(f"  Network  ({net_ok}/4 reachable)"))
    for (host, _), ok in zip(sites, net_results):
        row(host, ok, note="" if ok else "unreachable")

    # ── Final call ─────────────────────────────────────────────────────────
    print()
    all_blocking_ok = (
        tool_results.get("markcrawl")
        and py >= (3, 10)
    )

    if all_blocking_ok:
        if not _in_venv() and venv_python.exists():
            print(yellow("  Packages are in .venv — activate before running:"))
            print(f"    {bold('source .venv/bin/activate')}\n")
        if available_count < 7:
            print(yellow(f"  {7 - available_count} tool(s) unavailable — benchmark will run with {available_count}/7."))
        print(green("  Ready. Run the benchmark with:"))
        print(f"    {bold('python benchmarks/benchmark_all_tools.py')}\n")
        print(dim("  Quick test (1 site, 1 iteration, skip warmup):"))
        print(dim(f"    python benchmarks/benchmark_all_tools.py --sites quotes-toscrape --iterations 1 --skip-warmup\n"))
    else:
        print(red("  Not ready — fix blocking issues above, then re-run:"))
        print(f"    {bold('python benchmarks/preflight.py --install')}\n")


# ---------------------------------------------------------------------------
# Summary (brief, shown after checks, before install)
# ---------------------------------------------------------------------------


def print_summary(tool_results: dict[str, bool]) -> list[str]:
    """Print brief summary. Returns list of blocking failure labels (deduplicated)."""
    print(bold("\n── Summary ─────────────────────────────────────────────"))

    available = [t for t, ok in tool_results.items() if ok]
    skipped   = [t for t, ok in tool_results.items() if not ok]

    print(f"\n  Tools that will run  ({len(available)}/7): {green(', '.join(available)) if available else red('none')}")
    if skipped:
        print(f"  Tools that will skip ({len(skipped)}/7): {yellow(', '.join(skipped))}")
    print()

    seen: set[str] = set()
    failures: list[str] = []
    for label, ok, _, warn_only in _results:
        if ok is False and not warn_only and label not in seen:
            failures.append(label)
            seen.add(label)

    return failures


# ---------------------------------------------------------------------------
# Install logic
# ---------------------------------------------------------------------------

_PIP_INSTALL: dict[str, list[str] | None] = {
    "markcrawl":                    ["-e", str(REPO_ROOT)],
    "beautifulsoup4":               ["beautifulsoup4"],
    "markdownify":                  ["markdownify"],
    "requests":                     ["requests"],
    "psutil (memory tracking)":     ["psutil"],
    "python-dotenv (.env loading)": ["python-dotenv"],
    "scrapy+md":                    ["scrapy", "markdownify"],
    "crawl4ai":                     ["crawl4ai"],
    "crawlee":                      ["crawlee[playwright]"],
    "playwright (raw)":             ["playwright"],
    "firecrawl":                    ["firecrawl-py"],
    "colly+md (Go binary)":         None,   # handled via Go install + go build
    "firecrawl (API key)":          None,   # requires manual account setup
}


def _install_go_and_build_colly() -> bool:
    """Install Go (if missing) via Homebrew, then build the Colly binary."""
    colly_src = BENCH_DIR / "colly_crawler"
    colly_bin = colly_src / "colly_crawler"
    go_exe = _go_exe()

    if not go_exe:
        brew = _brew_exe()
        if not brew:
            print(red("  ✗ Homebrew not found — install Go manually from https://go.dev/dl/"))
            return False
        print(f"  Installing {bold('Go')} via Homebrew ...")
        print(dim("    $ brew install go"))
        result = subprocess.run([brew, "install", "go"])
        if result.returncode != 0:
            print(red("  ✗ brew install go failed"))
            return False
        go_exe = shutil.which("go")
        if not go_exe:
            for candidate in ["/usr/local/bin/go", "/opt/homebrew/bin/go"]:
                if Path(candidate).exists():
                    go_exe = candidate
                    break
        if not go_exe:
            print(red("  ✗ Go installed but not found in PATH — open a new terminal and re-run"))
            return False
        print(green("  ✓ Go installed"))

    print(f"  Building {bold('colly_crawler')} binary ...")
    print(dim(f"    $ cd {colly_src} && go build -o colly_crawler ."))
    result = subprocess.run([go_exe, "build", "-o", str(colly_bin), "."], cwd=str(colly_src))
    if result.returncode != 0:
        print(red("  ✗ go build failed"))
        return False
    print(green(f"  ✓ colly_crawler binary built"))
    return True


def install_missing(tool_results: dict[str, bool]) -> bool:
    """Install all missing packages. Returns True if anything was installed."""
    to_install: list[tuple[str, list[str]]] = []
    build_colly = False
    manual: list[str] = []

    for label, ok, detail, warn_only in _results:
        if ok is not False:
            continue
        if label == "colly+md (Go binary)":
            if _go_exe() or _brew_exe():
                build_colly = True
            else:
                manual.append(detail)
            continue
        pip_args = _PIP_INSTALL.get(label)
        if pip_args is None:
            if label in _PIP_INSTALL:
                manual.append(detail)
        elif label not in [l for l, _ in to_install]:
            to_install.append((label, pip_args))

    install_pw_browsers = any(
        label in ("crawl4ai", "crawlee", "playwright (raw)") for label, _ in to_install
    ) or any(
        label == "Playwright → chromium" for label, ok, _, _ in _results if ok is False
    )

    if not to_install and not install_pw_browsers and not build_colly:
        if manual:
            print(yellow("\n  The following items require manual setup:"))
            for m in manual:
                print(yellow(f"    {m}"))
        else:
            print(green("  Nothing to install."))
        return False

    print(bold("\n── Installing missing packages ─────────────────────────"))
    print()
    for label, pip_args in to_install:
        print(f"  • {label}  {dim('pip install ' + ' '.join(pip_args))}")
    if build_colly:
        go_note = "go build" if _go_exe() else "brew install go  →  go build"
        print(f"  • colly+md (Go binary)  {dim(go_note)}")
    if install_pw_browsers:
        print(f"  • Playwright chromium browser  {dim('playwright install chromium')}")
    if manual:
        print()
        print(yellow("  (skipping — require manual setup):"))
        for m in manual:
            print(yellow(f"    {m}"))

    print()
    if not sys.stdin.isatty():
        print(dim("  (non-interactive shell — proceeding automatically)"))
    else:
        try:
            answer = input("  Install the above? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        if answer not in ("y", "yes"):
            print(dim("  Skipped."))
            return False

    if not _in_venv():
        venv_python = _ensure_venv()
    else:
        venv_python = sys.executable

    print()
    installed_any = False
    all_ok = True

    for label, pip_args in to_install:
        print(f"  Installing {bold(label)} ...")
        ok = _pip(*pip_args, pip_exe=venv_python)
        if ok:
            print(green(f"  ✓ {label} installed"))
        else:
            print(red(f"  ✗ {label} failed"))
            all_ok = False
        installed_any = True

    if build_colly:
        ok = _install_go_and_build_colly()
        if not ok:
            all_ok = False
        installed_any = True

    if install_pw_browsers:
        print(f"  Installing {bold('Playwright chromium browser')} ...")
        result = subprocess.run(
            [venv_python, "-m", "playwright", "install", "chromium"],
            capture_output=False,
        )
        if result.returncode == 0:
            print(green("  ✓ Playwright chromium installed"))
        else:
            print(red("  ✗ Playwright chromium install failed"))
            all_ok = False
        installed_any = True

    # Re-exec with the venv Python so re-check sees newly installed packages
    if installed_any and not _in_venv():
        print(dim(f"\n  Re-running with venv Python to verify installs..."))
        env = os.environ.copy()
        env["PYTHONWARNINGS"] = "ignore"
        os.execve(venv_python, [venv_python, __file__, "--install"], env)

    return installed_any


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Pre-flight check for the 7-tool benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python benchmarks/preflight.py              # check only\n"
            "  python benchmarks/preflight.py --install    # check + install missing packages"
        ),
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="install any missing pip-installable packages (prompts for confirmation)",
    )
    args = parser.parse_args()

    if not args.install:
        print(dim("  Tip: run with --install to automatically install anything missing.\n"))

    tool_results, _ = run_checks()
    failures = print_summary(tool_results)

    if args.install:
        installed = install_missing(tool_results)
        if installed:
            # Re-run checks fresh if we installed anything (and didn't re-exec into venv)
            tool_results, _ = run_checks()
            failures = print_summary(tool_results)

    # Always print the ready status board last
    print_ready_status(tool_results)

    if failures:
        sys.exit(1)
    if not tool_results.get("markcrawl"):
        sys.exit(1)


if __name__ == "__main__":
    main()
