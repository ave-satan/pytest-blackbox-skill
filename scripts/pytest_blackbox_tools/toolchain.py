"""Enhanced-toolchain capability detection."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from importlib.util import find_spec

ENHANCED_DEPENDENCIES = {
    "packaging": "packaging",
    "pathspec": "pathspec",
    "ruff": "ruff",
    "tomlkit": "tomlkit",
}
if sys.version_info < (3, 11):
    ENHANCED_DEPENDENCIES["tomli"] = "tomli"

ENHANCED_REQUIREMENTS = (
    "ruff>=0.16,<0.17",
    "packaging>=24",
    "pathspec>=0.12",
    "tomlkit>=0.13",
    "tomli>=2; python_version < '3.11'",
)

BASELINE_DISTRIBUTIONS = frozenset(ENHANCED_DEPENDENCIES)


@dataclass(frozen=True)
class ToolchainStatus:
    available: tuple[str, ...]
    missing: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not self.missing


def toolchain_status() -> ToolchainStatus:
    available: list[str] = []
    missing: list[str] = []
    for distribution, module in ENHANCED_DEPENDENCIES.items():
        target = available if find_spec(module) is not None else missing
        target.append(distribution)
    return ToolchainStatus(tuple(available), tuple(missing))
