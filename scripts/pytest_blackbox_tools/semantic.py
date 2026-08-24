"""Semantic audit reminders that cannot be proven by static linting."""

from __future__ import annotations

from pathlib import Path

from .models import Finding, Policy


def semantic_findings(root: Path, tests_dir: Path, policy: Policy) -> list[Finding]:
    findings = [
        Finding(
            path=str(tests_dir.relative_to(root)),
            line=1,
            severity="MANUAL",
            code="SEM001",
            message=(
                "reconcile a transient contract-evidence matrix: complete operation "
                "census, applicable policy depth, primary node/categories, and every "
                "application-owned observable outcome class"
            ),
        )
    ]
    focused = sorted(
        selector
        for selector, decision in policy.coverage_rules
        if decision == "focused"
    )
    if focused:
        findings.append(
            Finding(
                path=str(tests_dir.relative_to(root)),
                line=1,
                severity="MANUAL",
                code="SEM002",
                message=(
                    "focused selectors still require a complete matching-surface "
                    "census: " + ", ".join(focused)
                ),
            )
        )
    schedulers = tests_dir / "test_schedulers"
    if schedulers.is_dir():
        findings.append(
            Finding(
                path=str(schedulers.relative_to(root)),
                line=1,
                severity="MANUAL",
                code="SEM003",
                message=(
                    "verify selected scheduler contracts observe actual framework "
                    "callback/trigger registration without a live-clock race"
                ),
            )
        )
    workers = tests_dir / "test_workers"
    if workers.is_dir():
        findings.append(
            Finding(
                path=str(workers.relative_to(root)),
                line=1,
                severity="MANUAL",
                code="SEM004",
                message=(
                    "verify selected worker success paths have a positive settlement "
                    "artifact and handler outcome matrices cover preservation/rejection "
                    "branches"
                ),
            )
        )
    return findings
