"""Compose fallback, enhanced, and semantic checks."""

from __future__ import annotations

from pathlib import Path

from .fallback_audit import Audit, load_policy, nearest_pyproject
from .fallback_discover import dependency_names, read_pyproject
from .models import CheckResult, Finding
from .ruff_runner import DELEGATED_FALLBACK_CODES, run_ruff
from .semantic import semantic_findings
from .toolchain import BASELINE_DISTRIBUTIONS, toolchain_status


def _resolve_scopes(
    root: Path,
    tests_dir: Path,
    requested_scopes: tuple[Path, ...],
) -> tuple[tuple[Path, ...], list[Finding]]:
    scopes: list[Path] = []
    errors: list[Finding] = []
    for requested in requested_scopes:
        scope = (
            (root / requested).resolve()
            if not requested.is_absolute()
            else requested.resolve()
        )
        try:
            relative = scope.relative_to(root)
            scope.relative_to(tests_dir)
        except ValueError:
            errors.append(
                Finding(
                    path=str(requested),
                    line=1,
                    severity="ERROR",
                    code="SCOPE001",
                    message="scope must resolve inside the project tests directory",
                )
            )
            continue
        if not scope.exists():
            errors.append(
                Finding(
                    path=str(relative),
                    line=1,
                    severity="ERROR",
                    code="SCOPE001",
                    message="scope path does not exist",
                )
            )
            continue
        if scope.is_file() and scope.suffix != ".py":
            errors.append(
                Finding(
                    path=str(relative),
                    line=1,
                    severity="ERROR",
                    code="SCOPE001",
                    message="scope file must be a Python test/support module",
                )
            )
            continue
        if scope.is_dir() and not any(scope.rglob("*.py")):
            errors.append(
                Finding(
                    path=str(relative),
                    line=1,
                    severity="ERROR",
                    code="SCOPE001",
                    message="scope directory contains no Python test/support modules",
                )
            )
            continue
        if not scope.is_file() and not scope.is_dir():
            errors.append(
                Finding(
                    path=str(relative),
                    line=1,
                    severity="ERROR",
                    code="SCOPE001",
                    message="scope must be a Python file or directory",
                )
            )
            continue
        if scope not in scopes:
            scopes.append(scope)
    return tuple(scopes), errors


def _finding_in_scope(root: Path, finding: Finding, scopes: tuple[Path, ...]) -> bool:
    if not scopes or finding.path == "pyproject.toml":
        return True
    path = Path(finding.path)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    return any(scope == path or scope in path.parents for scope in scopes)


def run_checks(
    root: Path,
    *,
    requested_mode: str,
    include_semantic: bool,
    requested_scopes: tuple[Path, ...] = (),
) -> CheckResult:
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        missing = Finding(
            path=str(tests_dir),
            line=1,
            severity="ERROR",
            code="ROOT001",
            message="tests directory does not exist",
        )
        return CheckResult("fallback", (missing,), ())

    scopes, scope_errors = _resolve_scopes(root, tests_dir, requested_scopes)
    scope_names = tuple(str(scope.relative_to(root)) for scope in scopes)
    if scope_errors:
        return CheckResult("fallback", tuple(sorted(scope_errors)), (), scope_names)

    policy, policy_errors = load_policy(root)
    status = toolchain_status()
    dependency_opt_in = policy.dependency_group is not None
    use_enhanced = dependency_opt_in and (
        requested_mode == "enhanced" or (requested_mode == "auto" and status.complete)
    )
    diagnostics: list[Finding] = []
    if requested_mode == "enhanced" and not dependency_opt_in:
        diagnostics.append(
            Finding(
                path="pyproject.toml",
                line=1,
                severity="ERROR",
                code="TOOL004",
                message="enhanced mode requires onboarding opt-in through dependency_group",
            )
        )
    elif dependency_opt_in and not status.complete:
        diagnostics.append(
            Finding(
                path="pyproject.toml",
                line=1,
                severity="ERROR" if requested_mode == "enhanced" else "WARNING",
                code="TOOL001",
                message=(
                    "enhanced checks require missing dependencies in "
                    f"{policy.dependency_group or 'the configured AI group'}: "
                    + ", ".join(status.missing)
                ),
            )
        )
        use_enhanced = False

    if dependency_opt_in:
        pyproject, _ = read_pyproject(nearest_pyproject(root))
        declared = dependency_names(pyproject)
        missing_declared = sorted(BASELINE_DISTRIBUTIONS - declared)
        if missing_declared:
            diagnostics.append(
                Finding(
                    path="pyproject.toml",
                    line=1,
                    severity="ERROR",
                    code="TOOL003",
                    message=(
                        "dependency_group is enabled but baseline requirements are "
                        "not declared: " + ", ".join(missing_declared)
                    ),
                )
            )

    fallback = Audit(root, tests_dir, policy).run()
    manual = [finding for finding in fallback if finding.severity == "MANUAL"]
    mechanical = [finding for finding in fallback if finding.severity != "MANUAL"]
    if use_enhanced:
        mechanical = [
            finding
            for finding in mechanical
            if finding.code not in DELEGATED_FALLBACK_CODES
        ]
        diagnostics.extend(run_ruff(root, scopes or (tests_dir,)))

    config_severity = "ERROR" if policy.configured else "WARNING"
    diagnostics.extend(
        Finding("pyproject.toml", 1, config_severity, "CFG001", message)
        for message in policy_errors
    )
    diagnostics.extend(
        finding for finding in mechanical if _finding_in_scope(root, finding, scopes)
    )
    if include_semantic:
        manual = [
            finding for finding in manual if _finding_in_scope(root, finding, scopes)
        ]
        manual.extend(semantic_findings(root, tests_dir, policy, scopes=scopes))
    else:
        manual = []
    mode = "enhanced" if use_enhanced else "fallback"
    return CheckResult(
        mode,
        tuple(sorted(diagnostics)),
        tuple(sorted(manual)),
        scope_names,
    )
