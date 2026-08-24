"""Ruff-like text and machine-readable output."""

from __future__ import annotations

import json
from dataclasses import asdict

from .models import CheckResult, Finding


def _line(finding: Finding) -> str:
    return (
        f"{finding.path}:{finding.line}:{finding.column}: "
        f"{finding.code} {finding.message} [{finding.severity.lower()}]"
    )


def render_concise(result: CheckResult) -> str:
    lines = [f"pytest-blackbox checks: {result.mode}"]
    lines.extend(_line(finding) for finding in result.diagnostics)
    if result.semantic:
        if len(lines) > 1:
            lines.append("")
        lines.append("Semantic review required:")
        lines.extend(_line(finding) for finding in result.semantic)
    errors = sum(item.severity == "ERROR" for item in result.diagnostics)
    warnings = sum(item.severity == "WARNING" for item in result.diagnostics)
    lines.extend(
        [
            "",
            (
                f"Found {errors} error(s), {warnings} warning(s), "
                f"{len(result.semantic)} semantic review item(s)."
            ),
        ]
    )
    return "\n".join(lines)


def render_json(result: CheckResult) -> str:
    return json.dumps(
        {
            "mode": result.mode,
            "diagnostics": [asdict(item) for item in result.diagnostics],
            "semantic": [asdict(item) for item in result.semantic],
            "summary": {
                "errors": sum(item.severity == "ERROR" for item in result.diagnostics),
                "warnings": sum(
                    item.severity == "WARNING" for item in result.diagnostics
                ),
                "semantic": len(result.semantic),
            },
        },
        indent=2,
        sort_keys=True,
    )
