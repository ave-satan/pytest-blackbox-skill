"""Fallback/enhanced discovery command."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from . import fallback_discover
from .toolchain import ENHANCED_REQUIREMENTS, toolchain_status


def _parse_args(argv: Iterable[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover pytest-blackbox project facts without mutation/imports."
    )
    parser.add_argument("project_root", nargs="?", default=".", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument(
        "--mode",
        choices=("auto", "fallback", "enhanced"),
        default="auto",
    )
    return parser.parse_args(argv)


def _dependency_opt_in(result: dict[str, Any]) -> bool:
    return bool(
        result.get("optional_capabilities", {})
        .get("managed_dependencies", {})
        .get("enabled")
    )


def discover(root: Path, requested_mode: str) -> tuple[dict[str, Any], int]:
    result = fallback_discover.discover(root)
    status = toolchain_status()
    dependency_opt_in = _dependency_opt_in(result)
    use_enhanced = dependency_opt_in and (
        requested_mode == "enhanced" or (requested_mode == "auto" and status.complete)
    )
    exit_code = 0
    if requested_mode == "enhanced" and not dependency_opt_in:
        result["enhanced_error"] = (
            "dependency_group is not enabled; enhanced mode requires onboarding opt-in"
        )
        exit_code = 2
    elif dependency_opt_in and not status.complete:
        result["enhanced_error"] = "missing enhanced dependencies: " + ", ".join(
            status.missing
        )
        use_enhanced = False
        exit_code = 2 if requested_mode == "enhanced" else 0
    if use_enhanced:
        from .enhanced_discover import enhance

        result = enhance(root, result)
    result["analysis_mode"] = "enhanced" if use_enhanced else "fallback"
    result["toolchain"] = {
        "requirements": list(ENHANCED_REQUIREMENTS),
        "available": list(status.available),
        "missing": list(status.missing),
    }
    return result, exit_code


def _render_text(result: dict[str, Any]) -> str:
    lines = [
        f"Project: {result['project_root']}",
        f"Pyproject: {result['pyproject'] or 'not found'}",
        f"Discovery mode: {result['analysis_mode']}",
    ]
    if result.get("pyproject_error"):
        lines.append(f"Pyproject error: {result['pyproject_error']}")
    if result.get("enhanced_error"):
        lines.append(f"Enhanced discovery unavailable: {result['enhanced_error']}")
    if result["nested_pyprojects"]:
        lines.append("Nested pyproject candidates:")
        lines.extend(f"  - {path}" for path in result["nested_pyprojects"])
    lines.extend(
        [
            "\nObserved facts:",
            json.dumps(result["facts"], indent=2, sort_keys=True),
            "\nProposed patch (review and confirm before writing):",
            fallback_discover.toml_proposal(result["proposal"]),
        ]
    )
    managed = result["optional_capabilities"]["managed_dependencies"]
    state = "enabled" if managed["enabled"] else "disabled until confirmed"
    lines.extend(
        [
            f"\nOptional capability ({state}):",
            f"{managed['config_key']} = {json.dumps(managed['suggested_value'])}",
            "Enhanced toolchain: " + ", ".join(result["toolchain"]["requirements"]),
            "\nManual confirmation:",
        ]
    )
    lines.extend(f"  - {item}" for item in result["manual_confirmation"])
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    result, exit_code = discover(args.project_root.resolve(), args.mode)
    print(
        json.dumps(result, indent=2, sort_keys=True)
        if args.as_json
        else _render_text(result)
    )
    return exit_code
