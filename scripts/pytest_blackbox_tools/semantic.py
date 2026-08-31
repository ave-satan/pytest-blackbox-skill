"""Semantic audit reminders that cannot be proven by static linting."""

from __future__ import annotations

from pathlib import Path

from .models import Finding, Policy


def _has_websocket_surface(tests_dir: Path) -> bool:
    for path in tests_dir.rglob("*.py"):
        if "websocket" in path.name.lower():
            return True
        try:
            if "websocket" in path.read_text(encoding="utf-8").lower():
                return True
        except (OSError, UnicodeError):
            continue
    return False


def _named_surface(tests_dir: Path, *tokens: str) -> Path | None:
    candidates = [
        path
        for path in tests_dir.rglob("*")
        if path.is_dir() and any(token in path.name.lower() for token in tokens)
    ]
    return min(
        candidates,
        key=lambda path: (len(path.relative_to(tests_dir).parts), str(path)),
        default=None,
    )


def semantic_findings(root: Path, tests_dir: Path, policy: Policy) -> list[Finding]:
    findings = [
        Finding(
            path=str(tests_dir.relative_to(root)),
            line=1,
            severity="MANUAL",
            code="SEM001",
            message=(
                "reconcile a transient contract-evidence matrix: complete operation "
                "census from final framework registrations/actions, applicable policy "
                "depth, primary node/categories, and every application-owned observable "
                "outcome class within the active policy boundary"
            ),
        )
    ]
    findings.append(
        Finding(
            path=str(tests_dir.relative_to(root)),
            line=1,
            severity="MANUAL",
            code="SEM006",
            message=(
                "prove scenario completeness, not only operation presence: derive "
                "expected truth from authoritative requirements and inspect "
                "application-owned source branches only for candidate gaps; map every "
                "confirmed public outcome, state partition, compound ownership/"
                "isolation dimension, boundary, terminal/no-op/stale handler outcome, "
                "mixed batch partition, and direct artifact to a collected node; "
                "report undocumented source-only candidates instead of using current "
                "implementation as the oracle; "
                "policy decisions may scope only non-contract surfaces; exclude "
                "concurrent execution when "
                "test_concurrency is false"
            ),
        )
    )
    findings.append(
        Finding(
            path=str(tests_dir.relative_to(root)),
            line=1,
            severity="MANUAL",
            code="SEM010",
            message=(
                "verify partial structural checks are limited to a focused variation/edge "
                "whose remainder is protected or an intentionally extensible natural "
                "container with a complete application-owned subset; pass the complete "
                "observation to a matcher that requires declared elements; "
                "do not project selected fields or delete/merge/overwrite ignored values; "
                "normalize only the complete container when equality requires it, preserve "
                "contractual multiplicity, and keep closed primary values exact"
            ),
        )
    )
    findings.append(
        Finding(
            path=str(tests_dir.relative_to(root)),
            line=1,
            severity="MANUAL",
            code="SEM011",
            message=(
                "verify every public domain-facing test-support class, fixture, and "
                "method uses its "
                "role plus a truthful domain action/target/state/outcome and cardinality; "
                "keep storage, transport, discriminator, caller-scenario, and optimization "
                "details private, with generic methods only for one unambiguous contract; "
                "generic structural/protocol primitives use precise abstraction-level "
                "names without child-domain defaults"
            ),
        )
    )
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
    schedulers = _named_surface(tests_dir, "scheduler")
    if schedulers is not None:
        findings.append(
            Finding(
                path=str(schedulers.relative_to(root)),
                line=1,
                severity="MANUAL",
                code="SEM003",
                message=(
                    "verify every registered scheduler contract observes actual framework "
                    "callback/trigger registration without a live-clock race"
                ),
            )
        )
    workers = _named_surface(tests_dir, "worker", "consumer")
    if workers is not None:
        findings.append(
            Finding(
                path=str(workers.relative_to(root)),
                line=1,
                severity="MANUAL",
                code="SEM004",
                message=(
                    "reconcile every registered handler contract independently from "
                    "shared worker runtime: cover distinct observable no-op/stale/preservation/"
                    "rejection outcomes without manufacturing corrupt states"
                ),
            )
        )
        findings.append(
            Finding(
                path=str(workers.relative_to(root)),
                line=1,
                severity="MANUAL",
                code="SEM008",
                message=(
                    "only when shared worker runtime behavior belongs to the selected "
                    "coverage boundary, reconcile dispatch/envelope/unknown-message "
                    "behavior; when settlement is selected, require a positive "
                    "acknowledgement/non-redelivery artifact"
                ),
            )
        )
        findings.append(
            Finding(
                path=str(workers.relative_to(root)),
                line=1,
                severity="MANUAL",
                code="SEM009",
                message=(
                    "verify broker topology is absent from the contract-test surface: "
                    "one private session/autouse fixture invokes the real production "
                    "bootstrap in an isolated namespace, propagates setup errors, and "
                    "leaves no competing consumer; teardown deletes isolated resources "
                    "without a topology spec, broker-state comparison, test_topology.py, "
                    "or inverse-topology teardown"
                ),
            )
        )
    if _has_websocket_surface(tests_dir):
        findings.append(
            Finding(
                path=str(tests_dir.relative_to(root)),
                line=1,
                severity="MANUAL",
                code="SEM005",
                message=(
                    "reconcile WebSocket route handshake/lifecycle and every client "
                    "message discriminator; keep route behavior in a clearly named "
                    "connection/lifecycle category and command behavior in its own "
                    "component with categories chosen by behavior; verify "
                    "natural denial values, required close/non-terminal outcomes, "
                    "current-contract-only immutable outcome variants, explicit "
                    "Transport/Connection/functional Client ownership, narrow "
                    "fixture composition, and application-task failure propagation "
                    "without timeout waits"
                ),
            )
        )
    if policy.test_concurrency:
        findings.append(
            Finding(
                path=str(tests_dir.relative_to(root)),
                line=1,
                severity="MANUAL",
                code="SEM007",
                message=(
                    "test only authoritative concurrency guarantees and prove them "
                    "through independently committing application transactions; "
                    "sequential calls or one shared outer transaction are not evidence"
                ),
            )
        )
    return findings
