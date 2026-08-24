"""Shared data models for bundled analysis commands."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Policy:
    configured: bool = False
    layout: str = "standard"
    prefer_test_classes: bool = True
    compose_lifecycle: str = "disabled"
    external_services: str = "intercept"
    infrastructure: str = "existing-services"
    generators_backend: str = "faker"
    dependency_group: str | None = None
    coverage_rules: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    severity: str
    code: str
    message: str
    column: int = 1


@dataclass(frozen=True)
class CheckResult:
    mode: str
    diagnostics: tuple[Finding, ...]
    semantic: tuple[Finding, ...]
