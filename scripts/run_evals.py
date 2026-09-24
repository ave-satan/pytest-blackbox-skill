"""Run dependency-free deterministic Pytest Blackbox regression evaluations."""

from __future__ import annotations

from pathlib import Path

from pytest_blackbox_tools.runner import run_checks


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    projects = root / "evals" / "projects"
    violated = run_checks(
        projects / "static-checks",
        requested_mode="fallback",
        include_semantic=False,
    )
    actual_codes = {finding.code for finding in violated.diagnostics}
    expected_codes = {"MIG001", "ORC001", "TIME002", "WAIT003"}
    missing = expected_codes - actual_codes
    if missing:
        print("missing expected diagnostics: " + ", ".join(sorted(missing)))
        return 1
    migration_findings = (
        finding for finding in violated.diagnostics if finding.code == "MIG001"
    )
    if not any(
        "remove this standalone" in finding.message
        and "without moving data-preservation" in finding.message
        for finding in migration_findings
    ):
        print("MIG001 must direct removal without moving assertions into fixtures")
        return 1

    clean = run_checks(
        projects / "static-clean",
        requested_mode="fallback",
        include_semantic=False,
    )
    unexpected = expected_codes & {finding.code for finding in clean.diagnostics}
    if unexpected:
        print("unexpected diagnostics: " + ", ".join(sorted(unexpected)))
        return 1

    print("deterministic evaluations passed: " + ", ".join(sorted(expected_codes)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
