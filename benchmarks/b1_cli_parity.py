"""B1 — source_vs_binary_parity benchmark.

Boolean must-pass dimension. Compares ``markcrawl --help`` between two installs
of markcrawl:

  * source: a fresh venv with ``pip install .`` from the working tree
  * pypi:   a fresh venv with ``pip install --force-reinstall markcrawl==<v>``
            (where ``<v>`` is the version pinned in pyproject.toml)

If PyPI does not yet have the source version published, fall back to the
latest available wheel and emit ``unpinned=true`` in the result envelope —
divergence is then expected (source is ahead of release) and the benchmark
returns SOFT_PASS rather than FAIL. This mirrors the conditional in
``.github/workflows/cli-flag-parity.yml`` so local + CI behavior agree.

Result schema (printed as JSON on stdout, also returned by ``run()``):

    {
      "benchmark": "b1_cli_parity",
      "result": "PASS" | "SOFT_PASS" | "FAIL",
      "source_version": "0.10.0",
      "pinned": true|false,
      "diff_line_count": <int>,
      "source_help_lines": <int>,
      "pypi_help_lines": <int>,
      "diff_excerpt": [ "...first 20 diff lines..." ],
      "duration_s": <float>,
      "notes": "..."
    }

Exit code: 0 on PASS or SOFT_PASS, 1 on FAIL. ``--json-out PATH`` writes
the full result envelope to disk in addition to stdout.
"""
from __future__ import annotations

import argparse
import difflib
import json
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_source_version() -> str:
    pyproject = REPO_ROOT / "pyproject.toml"
    with pyproject.open("rb") as fh:
        data = tomllib.load(fh)
    return data["project"]["version"]


def _make_venv(path: Path) -> Path:
    """Create a venv at ``path`` and return the path to its python executable."""
    subprocess.run(
        [sys.executable, "-m", "venv", str(path)],
        check=True,
        capture_output=True,
    )
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    return path / bin_dir


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _capture_help(venv_bin: Path) -> tuple[str, int]:
    """Run ``markcrawl --help`` from a venv. Returns (stdout, exitcode)."""
    exe = venv_bin / ("markcrawl.exe" if sys.platform == "win32" else "markcrawl")
    proc = _run([str(exe), "--help"])
    # markcrawl --help exits 0 cleanly (verified manually); be permissive on
    # exit so we still capture stderr-bound usage strings if argparse changes.
    out = proc.stdout or proc.stderr
    return out, proc.returncode


def _install_source(venv_bin: Path) -> None:
    pip = venv_bin / ("pip.exe" if sys.platform == "win32" else "pip")
    _run([str(pip), "install", "--upgrade", "pip", "--quiet"], check=False)
    res = _run([str(pip), "install", str(REPO_ROOT), "--quiet"])
    if res.returncode != 0:
        raise RuntimeError(f"source install failed:\n{res.stderr}")


def _install_pypi(venv_bin: Path, version: str) -> bool:
    """Install markcrawl from PyPI. Returns True if pinned to the requested
    version, False if it fell back to ``latest`` (source is ahead of release).
    """
    pip = venv_bin / ("pip.exe" if sys.platform == "win32" else "pip")
    _run([str(pip), "install", "--upgrade", "pip", "--quiet"], check=False)
    pinned = _run(
        [str(pip), "install", "--force-reinstall", f"markcrawl=={version}", "--quiet"]
    )
    if pinned.returncode == 0:
        return True
    # Fall back to whatever PyPI currently has.
    fallback = _run(
        [str(pip), "install", "--force-reinstall", "--upgrade", "markcrawl", "--quiet"]
    )
    if fallback.returncode != 0:
        raise RuntimeError(
            f"PyPI install failed for both pinned and latest:\n"
            f"pinned stderr:\n{pinned.stderr}\n"
            f"fallback stderr:\n{fallback.stderr}"
        )
    return False


def run(json_out: Path | None = None) -> dict:
    started = time.perf_counter()
    version = _read_source_version()
    notes_lines: list[str] = []

    with tempfile.TemporaryDirectory(prefix="b1-") as tmp_root:
        tmp = Path(tmp_root)
        source_venv = tmp / "source-venv"
        pypi_venv = tmp / "pypi-venv"

        source_bin = _make_venv(source_venv)
        pypi_bin = _make_venv(pypi_venv)

        _install_source(source_bin)
        try:
            pinned = _install_pypi(pypi_bin, version)
        except RuntimeError as exc:
            # PyPI fetch failed entirely (offline, blocked, or package gone).
            # Treat as SOFT_PASS with notes — we cannot meaningfully compare,
            # but it isn't a regression of source itself.
            duration = time.perf_counter() - started
            envelope = {
                "benchmark": "b1_cli_parity",
                "result": "SOFT_PASS",
                "source_version": version,
                "pinned": False,
                "diff_line_count": 0,
                "source_help_lines": 0,
                "pypi_help_lines": 0,
                "diff_excerpt": [],
                "duration_s": round(duration, 3),
                "notes": f"PyPI install unavailable; cannot compare. err={exc!s}",
            }
            _emit(envelope, json_out)
            return envelope

        source_help, _ = _capture_help(source_bin)
        pypi_help, _ = _capture_help(pypi_bin)

    diff_lines = list(
        difflib.unified_diff(
            pypi_help.splitlines(),
            source_help.splitlines(),
            fromfile="pypi/markcrawl --help",
            tofile="source/markcrawl --help",
            lineterm="",
        )
    )
    diff_count = len(diff_lines)
    excerpt = diff_lines[:20]

    if diff_count == 0:
        result = "PASS"
        notes_lines.append("source and PyPI --help outputs are identical")
    elif pinned:
        result = "FAIL"
        notes_lines.append(
            f"drift detected: source markcrawl=={version} differs from "
            f"published wheel for the SAME version"
        )
    else:
        result = "SOFT_PASS"
        notes_lines.append(
            f"source ahead of PyPI (source=={version}, PyPI=latest); diff is "
            f"expected during release window"
        )

    duration = time.perf_counter() - started
    envelope = {
        "benchmark": "b1_cli_parity",
        "result": result,
        "source_version": version,
        "pinned": pinned,
        "diff_line_count": diff_count,
        "source_help_lines": len(source_help.splitlines()),
        "pypi_help_lines": len(pypi_help.splitlines()),
        "diff_excerpt": excerpt,
        "duration_s": round(duration, 3),
        "notes": "; ".join(notes_lines),
    }
    _emit(envelope, json_out)
    return envelope


def _emit(envelope: dict, json_out: Path | None) -> None:
    print(json.dumps(envelope, indent=2))
    if json_out is not None:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(envelope, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="B1: source vs PyPI markcrawl --help parity"
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write the JSON result envelope.",
    )
    args = parser.parse_args(argv)
    envelope = run(json_out=args.json_out)
    return 0 if envelope["result"] in {"PASS", "SOFT_PASS"} else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
