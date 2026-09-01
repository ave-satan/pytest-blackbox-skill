"""Semantic audit reminders that cannot be proven by static linting."""

from __future__ import annotations

from pathlib import Path

from .models import Finding, Policy


def _scoped_python_files(tests_dir: Path, scopes: tuple[Path, ...]) -> list[Path]:
    if not scopes:
        return sorted(tests_dir.rglob("*.py"))
    files: set[Path] = set()
    for scope in scopes:
        if scope.is_file():
            files.add(scope)
        else:
            files.update(scope.rglob("*.py"))
    return sorted(files)


def _has_websocket_surface(tests_dir: Path, scopes: tuple[Path, ...]) -> bool:
    for path in _scoped_python_files(tests_dir, scopes):
        if any("websocket" in part.lower() for part in path.parts):
            return True
    return False


def _has_validation_surface(tests_dir: Path, scopes: tuple[Path, ...]) -> bool:
    return any(
        path.name == "test_validation.py"
        for path in _scoped_python_files(tests_dir, scopes)
    )


def _named_surfaces(tests_dir: Path, *tokens: str) -> tuple[Path, ...]:
    candidates = sorted(
        (
            path
            for path in tests_dir.rglob("*")
            if path.is_dir() and any(token in path.name.lower() for token in tokens)
        ),
        key=lambda path: (len(path.relative_to(tests_dir).parts), str(path)),
    )
    shallowest: dict[str, Path] = {}
    for path in candidates:
        key = next(token for token in tokens if token in path.name.lower())
        shallowest.setdefault(key, path)
    return tuple(shallowest.values())


def _intersects_scopes(path: Path, scopes: tuple[Path, ...]) -> bool:
    return not scopes or any(
        path == scope or path in scope.parents or scope in path.parents
        for scope in scopes
    )


def _semantic_path(root: Path, tests_dir: Path, scopes: tuple[Path, ...]) -> str:
    if len(scopes) == 1:
        return str(scopes[0].relative_to(root))
    return str(tests_dir.relative_to(root))


def _scope_has_token(scopes: tuple[Path, ...], *tokens: str) -> bool:
    return any(
        any(token in part.lower() for token in tokens)
        for scope in scopes
        for part in scope.parts
    )


def semantic_findings(
    root: Path,
    tests_dir: Path,
    policy: Policy,
    *,
    scopes: tuple[Path, ...] = (),
) -> list[Finding]:
    full_scope = not scopes or tests_dir in scopes
    semantic_path = _semantic_path(root, tests_dir, scopes)
    scope_label = "complete suite" if full_scope else "selected contract scope"
    findings = [
        Finding(
            path=semantic_path,
            line=1,
            severity="MANUAL",
            code="SEM001",
            message=(
                f"reconcile a transient contract-evidence matrix for the {scope_label}: "
                "operation census from final framework registrations/actions, applicable policy "
                "depth, primary node/categories, and every application-owned observable "
                "outcome class within the active policy boundary; after the final case "
                "set is known, reconcile names bottom-up so each category covers all of "
                "its cases and each terminal component still maps one-to-one to its "
                "public operation/component rather than retaining a stale historical name"
            ),
        )
    ]
    findings.append(
        Finding(
            path=semantic_path,
            line=1,
            severity="MANUAL",
            code="SEM006",
            message=(
                f"prove scenario completeness for the {scope_label}, not only operation "
                "presence: derive "
                "expected truth from authoritative requirements and inspect "
                "application-owned source branches only for candidate gaps; map every "
                "confirmed public outcome, state partition, compound ownership/"
                "isolation dimension (including the same resource owned by another "
                "principal whenever ownership affects selection/access), boundary, "
                "terminal/no-op/stale handler outcome, "
                "mixed batch partition, and direct artifact to a collected node; "
                "cover runtime legacy-format compatibility only when an authoritative "
                "requirement promises the preserved public behavior, never merely "
                "because source contains a migration/conversion branch; "
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
            path=semantic_path,
            line=1,
            severity="MANUAL",
            code="SEM010",
            message=(
                "verify assertions start with native exact structures/operators and use "
                "matchers only for added semantics or materially clearer diagnostics; "
                "partial matcher names expose partiality instead of a boolean mode and "
                "remain limited to a focused variation/edge whose remainder is protected "
                "or an intentionally extensible natural container with a complete "
                "application-owned subset; pass the complete compound observation to such "
                "a matcher and do not delete/merge/overwrite ignored values; allow a "
                "native scalar projection such as ordered IDs only when that focused "
                "collection property is the case and complete item contracts are protected; "
                "normalize only the complete container when equality requires it, preserve "
                "contractual multiplicity, and keep closed primary values exact"
            ),
        )
    )
    findings.append(
        Finding(
            path=semantic_path,
            line=1,
            severity="MANUAL",
            code="SEM011",
            message=(
                "verify every public domain-facing test-support class, fixture, "
                "callable, and module uses its "
                "role plus the shortest truthful domain action/target/state/outcome and "
                "cardinality, starting from canonical operations and adding only the "
                "smallest qualifier needed among siblings without repeating the owner noun; "
                "keep storage, transport, discriminator, caller-scenario, and optimization "
                "details and raw storage references private; keep base canonical CRUD "
                "available and forbid cross-component private-member access; "
                "generic structural/protocol primitives use precise abstraction-level "
                "names without child-domain defaults; reusable response-oracle "
                "builders live at the narrowest common owner in role-explicit modules "
                "and name the exact returned artifact (body, headers, or complete "
                "response) rather than a domain entity or generic expected_* role"
            ),
        )
    )
    focused = sorted(
        selector
        for selector, decision in policy.coverage_rules
        if decision == "focused"
    )
    if focused and full_scope:
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
    schedulers = _named_surfaces(tests_dir, "scheduler")
    if any(_intersects_scopes(surface, scopes) for surface in schedulers):
        findings.append(
            Finding(
                path=semantic_path,
                line=1,
                severity="MANUAL",
                code="SEM003",
                message=(
                    "verify every registered scheduler contract observes actual framework "
                    "callback/trigger registration without a live-clock race"
                ),
            )
        )
    workers = _named_surfaces(tests_dir, "worker", "consumer")
    worker_selected = any(_intersects_scopes(surface, scopes) for surface in workers)
    if worker_selected:
        findings.append(
            Finding(
                path=semantic_path,
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
    runtime_selected = (
        full_scope
        or any(scope == surface for scope in scopes for surface in workers)
        or _scope_has_token(
            scopes,
            "runtime",
            "settlement",
            "dispatch",
        )
    )
    if worker_selected and runtime_selected:
        findings.append(
            Finding(
                path=semantic_path,
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
    topology_selected = (
        (full_scope and bool(workers))
        or any(scope == surface for scope in scopes for surface in workers)
        or _scope_has_token(scopes, "broker", "messaging", "topology", "environment")
    )
    if topology_selected:
        findings.append(
            Finding(
                path=semantic_path,
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
    if _has_websocket_surface(tests_dir, scopes):
        findings.append(
            Finding(
                path=semantic_path,
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
    if _has_validation_surface(tests_dir, scopes):
        findings.append(
            Finding(
                path=semantic_path,
                line=1,
                severity="MANUAL",
                code="SEM012",
                message=(
                    "reconcile each validated field or contractual field relationship "
                    "as separate homogeneous accepted/rejected parametrized functions; "
                    "accepted rows own ordinary values, valid boundaries, and all "
                    "allowed enum/discriminator members, while rejected rows own "
                    "outside-boundary and invalid values plus exact varying errors; "
                    "assert each function's fixed outcome directly without parametrized "
                    "status, nullable error sentinels, or accepted/rejected branches"
                ),
            )
        )
    if policy.test_concurrency:
        findings.append(
            Finding(
                path=semantic_path,
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
