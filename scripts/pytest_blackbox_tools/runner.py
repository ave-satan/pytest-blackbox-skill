"""Compose fallback, enhanced, and semantic checks."""

from __future__ import annotations

from pathlib import Path

from .fallback_audit import Audit, load_policy, nearest_pyproject
from .fallback_discover import dependency_names, read_pyproject
from .models import CheckResult, Finding
from .ruff_runner import DELEGATED_FALLBACK_CODES, run_ruff
from .semantic import semantic_findings
from .toolchain import BASELINE_DISTRIBUTIONS, toolchain_status


def run_checks(
    root: Path,
    *,
    requested_mode: str,
    include_semantic: bool,
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
        diagnostics.extend(run_ruff(root, tests_dir))

    config_severity = "ERROR" if policy.configured else "WARNING"
    diagnostics.extend(
        Finding("pyproject.toml", 1, config_severity, "CFG001", message)
        for message in policy_errors
    )
    diagnostics.extend(mechanical)
    if include_semantic:
        manual.extend(semantic_findings(root, tests_dir, policy))
    else:
        manual = []
    mode = "enhanced" if use_enhanced else "fallback"
    return CheckResult(mode, tuple(sorted(diagnostics)), tuple(sorted(manual)))
