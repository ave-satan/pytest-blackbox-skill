"""Run first-party Ruff rules and translate their JSON diagnostics."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from .models import Finding

DELEGATED_FALLBACK_CODES = {"DB001", "LOOP001", "PY001", "TIME001", "WAIT001"}

_BANNED_APIS = {
    "anyio.sleep": "sleep is forbidden in tests",
    "asyncio.Runner": "manual event-loop creation is forbidden",
    "asyncio.new_event_loop": "multiple event loops are forbidden",
    "asyncio.run": "manual event-loop driving is forbidden",
    "asyncio.set_event_loop": "manual event-loop setup is forbidden",
    "asyncio.sleep": "sleep is forbidden in tests",
    "freezegun": "time freezing is forbidden",
    "sqlalchemy.ext.asyncio.AsyncSession": (
        "SQLAlchemy Session APIs are forbidden in test support"
    ),
    "sqlalchemy.ext.asyncio.async_sessionmaker": (
        "SQLAlchemy Session APIs are forbidden in test support"
    ),
    "sqlalchemy.orm.Session": "SQLAlchemy Session APIs are forbidden in test support",
    "sqlalchemy.orm.sessionmaker": (
        "SQLAlchemy Session APIs are forbidden in test support"
    ),
    "time.sleep": "sleep is forbidden in tests",
    "trio.sleep": "sleep is forbidden in tests",
}

_COMPATIBLE_PYTEST_RULES = (
    "PT006",
    "PT007",
    "PT009",
    "PT010",
    "PT011",
    "PT012",
    "PT013",
    "PT014",
    "PT015",
    "PT016",
    "PT017",
    "PT020",
    "PT021",
    "PT022",
    "PT024",
    "PT025",
    "PT026",
    "PT027",
    "PT028",
    "PT029",
    "PT030",
    "PT031",
)


def _config_text() -> str:
    selected = json.dumps([*_COMPATIBLE_PYTEST_RULES, "TID251"])
    lines = [
        "[lint]",
        f"select = {selected}",
        "",
        "[lint.flake8-tidy-imports.banned-api]",
    ]
    for name, message in _BANNED_APIS.items():
        lines.append(f"{json.dumps(name)} = {{ msg = {json.dumps(message)} }}")
    return "\n".join(lines) + "\n"


def run_ruff(root: Path, tests_dir: Path) -> list[Finding]:
    with TemporaryDirectory(prefix="pytest-blackbox-ruff-") as directory:
        config = Path(directory) / "ruff.toml"
        config.write_text(_config_text(), encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--config",
                str(config),
                "--output-format",
                "json",
                str(tests_dir),
            ],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    if completed.returncode not in {0, 1}:
        detail = (completed.stderr or completed.stdout).strip()
        return [
            Finding(
                path="pyproject.toml",
                line=1,
                severity="ERROR",
                code="TOOL002",
                message=f"Ruff execution failed: {detail or 'unknown error'}",
            )
        ]
    try:
        payload = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as error:
        return [
            Finding(
                path="pyproject.toml",
                line=1,
                severity="ERROR",
                code="TOOL002",
                message=f"Ruff returned invalid JSON: {error}",
            )
        ]
    findings: list[Finding] = []
    for item in payload:
        filename = Path(item["filename"])
        try:
            path = str(filename.relative_to(root))
        except ValueError:
            path = str(filename)
        location = item.get("location") or {}
        findings.append(
            Finding(
                path=path,
                line=int(location.get("row", 1)),
                column=int(location.get("column", 1)),
                severity="ERROR",
                code=str(item.get("code") or "E999"),
                message=str(item.get("message") or "Ruff violation"),
            )
        )
    return findings
