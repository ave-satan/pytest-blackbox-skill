#!/usr/bin/env python3
"""Read-only pytest-blackbox project discovery and policy proposal."""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


IGNORED_PARTS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "node_modules",
    "site-packages",
    "venv",
}

SENSITIVE_PYTHON_NAMES = {
    "credentials.py",
    "keys.py",
    "private_keys.py",
    "secrets.py",
    "tokens.py",
}


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover pytest-blackbox project facts without mutation/imports."
    )
    parser.add_argument("project_root", nargs="?", default=".", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def safe_paths(root: Path, pattern: str) -> Iterator[Path]:
    for path in root.rglob(pattern):
        if not any(part in IGNORED_PARTS for part in path.parts):
            yield path


def find_pyprojects(root: Path) -> tuple[Path | None, list[Path]]:
    direct = root / "pyproject.toml"
    owner: Path | None = direct if direct.is_file() else None
    if owner is None:
        for parent in root.parents:
            candidate = parent / "pyproject.toml"
            if candidate.is_file():
                owner = candidate
                break
            if (parent / ".git").exists():
                break
    nested = sorted(path for path in safe_paths(root, "pyproject.toml") if path != owner)
    return owner, nested


def read_pyproject(path: Path | None) -> tuple[dict[str, Any], str | None]:
    if path is None:
        return {}, None
    if tomllib is None:
        return {}, "TOML parser unavailable; run with Python 3.11+ or install tomli"
    try:
        return tomllib.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeError, ValueError) as error:
        return {}, str(error)


def dependency_names(data: Mapping[str, Any]) -> set[str]:
    names: set[str] = set()

    def add_value(value: object) -> None:
        if not isinstance(value, str):
            return
        token = value.split(";", 1)[0].strip().split("[", 1)[0]
        token = token.replace("_", "-")
        for marker in (" ", "<", ">", "=", "!", "~"):
            token = token.split(marker, 1)[0]
        if token:
            names.add(token.lower())

    project = data.get("project", {})
    if isinstance(project, Mapping):
        for value in project.get("dependencies", []):
            add_value(value)
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, Mapping):
            for values in optional.values():
                if isinstance(values, list):
                    for value in values:
                        add_value(value)

    groups = data.get("dependency-groups", {})
    if isinstance(groups, Mapping):
        for values in groups.values():
            if isinstance(values, list):
                for value in values:
                    add_value(value)

    poetry = data.get("tool", {}).get("poetry", {}) if isinstance(data.get("tool"), Mapping) else {}
    if isinstance(poetry, Mapping):
        for section_name in ("dependencies", "dev-dependencies"):
            section = poetry.get(section_name, {})
            if isinstance(section, Mapping):
                names.update(str(name).replace("_", "-").lower() for name in section)
    return names


def python_facts(root: Path) -> tuple[Counter[str], int, bool, int]:
    imports: Counter[str] = Counter()
    async_defs = 0
    compose_literal = False
    parse_failures = 0
    for path in safe_paths(root, "*.py"):
        if path.name.lower() in SENSITIVE_PYTHON_NAMES:
            continue
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeError, SyntaxError):
            parse_failures += 1
            continue
        compose_literal = compose_literal or "docker compose" in source.lower()
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_defs += 1
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.name.split(".", 1)[0]] += 1
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports[node.module.split(".", 1)[0]] += 1
    return imports, async_defs, compose_literal, parse_failures


def layout_facts(root: Path) -> dict[str, Any]:
    tests = root / "tests"
    if not tests.is_dir():
        return {
            "tests_present": False,
            "suggested": "standard",
            "reason": "new suite",
        }
    test_files = sorted(safe_paths(tests, "test_*.py"))
    nonstandard: list[str] = []
    for path in test_files:
        directories = path.relative_to(tests).parts[:-1]
        if directories == ("test_health",):
            continue
        if not 2 <= len(directories) <= 3 or any(
            not part.startswith("test_") for part in directories
        ):
            nonstandard.append(str(path.relative_to(root)))
    suggested = "preserve" if test_files and nonstandard else "standard"
    return {
        "tests_present": True,
        "test_file_count": len(test_files),
        "nonstandard_examples": nonstandard[:10],
        "suggested": suggested,
        "reason": (
            "existing layout differs from the standard hierarchy"
            if suggested == "preserve"
            else "existing layout matches the standard hierarchy"
        ),
    }


def choose_generator(dependencies: set[str], imports: Counter[str]) -> tuple[str, str]:
    candidates = (
        ("faker", "faker"),
        ("polyfactory", "polyfactory"),
        ("factory-boy", "factory_boy"),
    )
    for dependency, module in candidates:
        if dependency in dependencies or imports[module]:
            return dependency, "high"
    return "faker", "default"


def discover(root: Path) -> dict[str, Any]:
    owner, nested = find_pyprojects(root)
    pyproject, pyproject_error = read_pyproject(owner)
    dependencies = dependency_names(pyproject)
    imports, async_defs, compose_literal, parse_failures = python_facts(root)
    layout = layout_facts(root)
    configured = (
        isinstance(pyproject.get("tool"), Mapping)
        and isinstance(pyproject.get("tool", {}).get("pytest-blackbox"), Mapping)
    )
    generator, generator_confidence = choose_generator(dependencies, imports)
    testcontainers = "testcontainers" in dependencies or bool(imports["testcontainers"])
    interceptors = [
        module
        for module in ("aioresponses", "requests_mock", "responses", "respx")
        if module.replace("_", "-") in dependencies or imports[module]
    ]
    proposal = {
        "config_version": 1,
        "layout": layout["suggested"],
        "prefer_test_classes": True,
        "infrastructure": "existing-services",
        "compose_lifecycle": "enabled" if compose_literal else "disabled",
        "external_services": "intercept",
        "generators_backend": generator,
    }
    return {
        "project_root": str(root),
        "pyproject": str(owner) if owner else None,
        "pyproject_error": pyproject_error,
        "nested_pyprojects": [str(path) for path in nested[:20]],
        "configured": configured,
        "facts": {
            "layout": layout,
            "async_functions": async_defs,
            "runtime": "async-capable" if async_defs else "sync-only-observed",
            "python_parse_failures": parse_failures,
            "sqlalchemy": "sqlalchemy" in dependencies or bool(imports["sqlalchemy"]),
            "http_clients": [
                name
                for name in ("aiohttp", "httpx", "requests")
                if name in dependencies or imports[name]
            ],
            "testcontainers": testcontainers,
            "external_interceptors": interceptors,
            "docker_compose_literal": compose_literal,
            "generator_backend_evidence": {
                "value": generator,
                "confidence": generator_confidence,
            },
        },
        "proposal": proposal,
        "manual_confirmation": [
            "nearest pyproject ownership when nested_pyprojects contains another candidate",
            "infrastructure provider availability and protocol compatibility",
            "generalized non-contract coverage registry",
            (
                "whether observed Testcontainers usage provisions internal services, "
                "external mock servers, both, or neither"
            ),
            (
                "whether external integrations should use interception, Testcontainers "
                "mock servers, or mixed mode with one stable backend per integration"
            ),
            "whether an observed Compose mode is intentional",
        ],
    }


def toml_proposal(proposal: Mapping[str, object]) -> str:
    lines = ["[tool.pytest-blackbox]"]
    for key, value in proposal.items():
        rendered = str(value).lower() if isinstance(value, bool) else json.dumps(value)
        lines.append(f"{key} = {rendered}")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.project_root.resolve()
    result = discover(root)
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print(f"Project: {result['project_root']}")
    print(f"Pyproject: {result['pyproject'] or 'not found'}")
    if result["pyproject_error"]:
        print(f"Pyproject error: {result['pyproject_error']}")
    if result["nested_pyprojects"]:
        print("Nested pyproject candidates:")
        for path in result["nested_pyprojects"]:
            print(f"  - {path}")
    print("\nObserved facts:")
    print(json.dumps(result["facts"], indent=2, sort_keys=True))
    print("\nProposed patch (review and confirm before writing):")
    print(toml_proposal(result["proposal"]))
    print("\nManual confirmation:")
    for item in result["manual_confirmation"]:
        print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
