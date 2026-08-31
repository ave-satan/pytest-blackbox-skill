"""Command-line entrypoints for lint and audit."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path

from .output import render_concise, render_json
from .runner import run_checks


def _parse_args(argv: Iterable[str] | None, *, command: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Run pytest-blackbox {command} checks."
    )
    parser.add_argument("project_root", nargs="?", default=".", type=Path)
    parser.add_argument(
        "--mode",
        choices=("auto", "fallback", "enhanced"),
        default="auto",
        help="analysis mode (default: auto)",
    )
    parser.add_argument(
        "--output-format",
        choices=("concise", "json"),
        default="concise",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return a failing exit code for warnings as well as errors",
    )
    parser.add_argument(
        "--scope",
        action="append",
        default=[],
        type=Path,
        metavar="PATH",
        help=(
            "limit reported diagnostics and semantic review to a test file or "
            "directory; repeat for multiple paths"
        ),
    )
    return parser.parse_args(argv)


def main(
    argv: Iterable[str] | None = None,
    *,
    include_semantic: bool,
    command: str,
) -> int:
    args = _parse_args(argv, command=command)
    result = run_checks(
        args.project_root.resolve(),
        requested_mode=args.mode,
        include_semantic=include_semantic,
        requested_scopes=tuple(args.scope),
    )
    renderer = render_json if args.output_format == "json" else render_concise
    print(renderer(result))
    errors = sum(item.severity == "ERROR" for item in result.diagnostics)
    warnings = sum(item.severity == "WARNING" for item in result.diagnostics)
    return 1 if errors or (args.strict and warnings) else 0
