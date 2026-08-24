"""Library-backed additions to fallback project discovery."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import tomlkit
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from pathspec import PathSpec
from tomlkit.exceptions import ParseError

from .fallback_discover import IGNORED_PARTS, SENSITIVE_PYTHON_NAMES


def _requirement_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return canonicalize_name(Requirement(value).name)
    except InvalidRequirement:
        return None


def _dependency_names(data: Mapping[str, Any]) -> set[str]:
    names: set[str] = set()
    project = data.get("project", {})
    if isinstance(project, Mapping):
        sections = [project.get("dependencies", [])]
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, Mapping):
            sections.extend(optional.values())
        for values in sections:
            if isinstance(values, list):
                names.update(
                    name
                    for value in values
                    if (name := _requirement_name(value)) is not None
                )

    groups = data.get("dependency-groups", {})
    if isinstance(groups, Mapping):
        for values in groups.values():
            if isinstance(values, list):
                names.update(
                    name
                    for value in values
                    if (name := _requirement_name(value)) is not None
                )

    tool = data.get("tool", {})
    if not isinstance(tool, Mapping):
        return names
    poetry = tool.get("poetry", {})
    if isinstance(poetry, Mapping):
        mappings = [
            poetry.get("dependencies", {}),
            poetry.get("dev-dependencies", {}),
        ]
        poetry_groups = poetry.get("group", {})
        if isinstance(poetry_groups, Mapping):
            mappings.extend(
                group.get("dependencies", {})
                for group in poetry_groups.values()
                if isinstance(group, Mapping)
            )
        for mapping in mappings:
            if isinstance(mapping, Mapping):
                names.update(canonicalize_name(str(name)) for name in mapping)
    pdm = tool.get("pdm", {})
    if isinstance(pdm, Mapping):
        pdm_groups = pdm.get("dev-dependencies", {})
        if isinstance(pdm_groups, Mapping):
            for values in pdm_groups.values():
                if isinstance(values, list):
                    names.update(
                        name
                        for value in values
                        if (name := _requirement_name(value)) is not None
                    )
    return names


def _gitignored_python_count(root: Path) -> int:
    ignore_file = root / ".gitignore"
    if not ignore_file.is_file():
        return 0
    try:
        spec = PathSpec.from_lines(
            "gitwildmatch", ignore_file.read_text(encoding="utf-8").splitlines()
        )
    except (OSError, UnicodeError):
        return 0
    count = 0
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if (
            path.name.lower() not in SENSITIVE_PYTHON_NAMES
            and not any(part in IGNORED_PARTS for part in relative.parts)
            and spec.match_file(relative.as_posix())
        ):
            count += 1
    return count


def enhance(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    pyproject_value = result.get("pyproject")
    if not isinstance(pyproject_value, str):
        result["facts"]["declared_dependency_count"] = 0
        result["facts"]["gitignored_python_files"] = _gitignored_python_count(root)
        return result
    try:
        document = tomlkit.parse(Path(pyproject_value).read_text(encoding="utf-8"))
        data = document.unwrap()
    except (OSError, UnicodeError, ParseError) as error:
        result["enhanced_error"] = str(error)
        return result
    result["facts"]["declared_dependency_count"] = len(_dependency_names(data))
    result["facts"]["gitignored_python_files"] = _gitignored_python_count(root)
    return result
