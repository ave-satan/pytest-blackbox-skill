#!/usr/bin/env python3
"""Read-only static audit for mechanically detectable pytest-blackbox rules."""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


@dataclass(frozen=True)
class Policy:
    configured: bool = False
    layout: str = "standard"
    prefer_test_classes: bool = True
    compose_lifecycle: str = "disabled"
    external_services: str = "intercept"
    infrastructure: str = "existing-services"
    generators_backend: str = "faker"
    coverage_rules: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class TestNode:
    node: ast.FunctionDef | ast.AsyncFunctionDef
    inherited_decorators: tuple[ast.expr, ...] = ()


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        owner = dotted_name(node.value)
        return f"{owner}.{node.attr}" if owner else node.attr
    return None


def function_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    positional = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    return {
        argument.arg
        for argument in positional
        if argument.arg not in {"self", "cls"}
    }


def is_fixture(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        candidate = decorator.func if isinstance(decorator, ast.Call) else decorator
        name = dotted_name(candidate)
        if name and name.rsplit(".", 1)[-1] in {"fixture", "yield_fixture"}:
            return True
    return False


def has_multiple_param_rows(decorators: Sequence[ast.expr]) -> bool:
    for decorator in decorators:
        if not isinstance(decorator, ast.Call) or len(decorator.args) < 2:
            continue
        name = dotted_name(decorator.func) or ""
        rows = decorator.args[1]
        if (
            name.rsplit(".", 1)[-1] == "parametrize"
            and isinstance(rows, (ast.List, ast.Tuple))
            and len(rows.elts) > 1
        ):
            return True
    return False


def has_wide_scoped_fixture(
    nodes: Sequence[ast.FunctionDef | ast.AsyncFunctionDef],
) -> bool:
    for node in nodes:
        if not is_fixture(node):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            scope = next(
                (keyword.value for keyword in decorator.keywords if keyword.arg == "scope"),
                None,
            )
            if (
                isinstance(scope, ast.Constant)
                and scope.value in {"class", "session"}
            ):
                return True
    return False


def is_simple_alias_fixture(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(
        body[0].value, ast.Constant
    ) and isinstance(body[0].value.value, str):
        body = body[1:]
    if len(body) != 1:
        return None
    statement = body[0]
    value: ast.AST | None = None
    if isinstance(statement, ast.Return):
        value = statement.value
    elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Yield):
        value = statement.value.value
    if isinstance(value, ast.Name) and value.id in function_args(node):
        return value.id
    return None


def fixture_returns_generated_value(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(
        body[0].value, ast.Constant
    ) and isinstance(body[0].value.value, str):
        body = body[1:]
    if len(body) != 1:
        return False
    statement = body[0]
    value: ast.AST | None = None
    if isinstance(statement, ast.Return):
        value = statement.value
    elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Yield):
        value = statement.value.value
    if value is None:
        return False
    visitor = FreshValueVisitor()
    visitor.visit(value)
    return bool(visitor.calls)


def literal_param_ids(decorators: Sequence[ast.expr]) -> set[str]:
    result: set[str] = set()
    for decorator in decorators:
        if not isinstance(decorator, ast.Call):
            continue
        if (dotted_name(decorator.func) or "").rsplit(".", 1)[-1] != "parametrize":
            continue
        if len(decorator.args) < 2:
            continue
        rows = decorator.args[1]
        if isinstance(rows, (ast.List, ast.Tuple)):
            for row in rows.elts:
                if not isinstance(row, ast.Call) or dotted_name(row.func) != "pytest.param":
                    continue
                for keyword in row.keywords:
                    if (
                        keyword.arg == "id"
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                    ):
                        result.add(keyword.value.value.lower())
        ids_node = next(
            (keyword.value for keyword in decorator.keywords if keyword.arg == "ids"),
            None,
        )
        if isinstance(ids_node, (ast.List, ast.Tuple)):
            result.update(
                element.value.lower()
                for element in ids_node.elts
                if isinstance(element, ast.Constant)
                and isinstance(element.value, str)
            )
    return result


def is_json_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "json"
    )


def observation_root(node: ast.AST) -> str | None:
    current = node
    while isinstance(current, (ast.Attribute, ast.Subscript, ast.Call)):
        if isinstance(current, (ast.Attribute, ast.Subscript)):
            current = current.value
        else:
            current = current.func
    return current.id if isinstance(current, ast.Name) else None


class LambdaSkippingVisitor(ast.NodeVisitor):
    def visit_Lambda(self, node: ast.Lambda) -> None:
        return None


class FreshValueVisitor(LambdaSkippingVisitor):
    def __init__(self) -> None:
        self.calls: list[ast.Call] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = dotted_name(node.func) or ""
        leaf = name.rsplit(".", 1)[-1]
        owner = name.split(".", 1)[0]
        if leaf in {"now", "utcnow", "today", "uuid1", "uuid4"} or owner in {
            "fake",
            "faker",
            "generators",
        }:
            self.calls.append(node)
        self.generic_visit(node)


class NameUseVisitor(ast.NodeVisitor):
    def __init__(self, names: set[str]) -> None:
        self.names = names
        self.found = False

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in self.names:
            self.found = True


def nearest_pyproject(root: Path) -> Path:
    for directory in (root, *root.parents):
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            return candidate
        if directory != root and (directory / ".git").exists():
            break
    return root / "pyproject.toml"


def load_policy(root: Path) -> tuple[Policy, list[str]]:
    pyproject = nearest_pyproject(root)
    if not pyproject.is_file():
        return Policy(), ["pyproject.toml is absent; run project onboarding"]
    if tomllib is None:
        return Policy(configured=True), [
            "TOML parser unavailable; run with Python 3.11+ or install tomli"
        ]
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        return Policy(), [f"cannot read pyproject.toml: {error}"]
    raw = data.get("tool", {}).get("pytest-blackbox")
    if not isinstance(raw, dict):
        return Policy(), ["[tool.pytest-blackbox] is absent; run project onboarding"]

    errors: list[str] = []
    version = raw.get("config_version")
    layout = raw.get("layout", "standard")
    compose = raw.get("compose_lifecycle", "disabled")
    external = raw.get("external_services", "intercept")
    infrastructure = raw.get("infrastructure", "existing-services")
    generators_backend = raw.get("generators_backend", "faker")
    prefer_classes = raw.get("prefer_test_classes", True)
    if version != 1:
        errors.append(f"unsupported or missing config_version {version!r}")
    if layout not in {"standard", "preserve"}:
        errors.append(f"unsupported layout {layout!r}")
    if compose not in {"disabled", "enabled"}:
        errors.append(f"unsupported compose_lifecycle {compose!r}")
    if external not in {"intercept", "testcontainers", "mixed"}:
        errors.append(f"unsupported external_services {external!r}")
    if not isinstance(prefer_classes, bool):
        errors.append("prefer_test_classes must be boolean")
        prefer_classes = True
    for key in ("infrastructure", "generators_backend"):
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string")
    if not isinstance(infrastructure, str) or not infrastructure.strip():
        infrastructure = "existing-services"
    if not isinstance(generators_backend, str) or not generators_backend.strip():
        generators_backend = "faker"
    coverage = raw.get("coverage", [])
    coverage_rules: list[tuple[str, str]] = []
    if not isinstance(coverage, list):
        errors.append("coverage must be an array of tables")
    else:
        http_prefixes = ("GET ", "POST ", "PUT ", "PATCH ", "DELETE ", "HEAD ")
        for index, rule in enumerate(coverage, start=1):
            if not isinstance(rule, dict):
                errors.append(f"coverage rule {index} must be a table")
                continue
            selector = rule.get("selector")
            decision = rule.get("decision")
            if not isinstance(selector, str) or not selector.strip():
                errors.append(f"coverage rule {index} requires a selector")
            elif selector.startswith(http_prefixes) or selector.startswith("/"):
                errors.append(
                    f"coverage rule {index} looks operation-specific; "
                    "use a generalized non-contract surface selector"
                )
            if decision not in {"exclude", "focused", "standard"}:
                errors.append(f"coverage rule {index} has invalid decision {decision!r}")
            if isinstance(selector, str) and decision in {"exclude", "focused", "standard"}:
                coverage_rules.append((selector, decision))
    return (
        Policy(
            configured=True,
            layout=layout if layout in {"standard", "preserve"} else "standard",
            prefer_test_classes=prefer_classes,
            compose_lifecycle=(
                compose if compose in {"disabled", "enabled"} else "disabled"
            ),
            external_services=(
                external
                if external in {"intercept", "testcontainers", "mixed"}
                else "intercept"
            ),
            infrastructure=infrastructure,
            generators_backend=generators_backend,
            coverage_rules=tuple(coverage_rules),
        ),
        errors,
    )


class Audit:
    def __init__(self, root: Path, tests_dir: Path, policy: Policy) -> None:
        self.root = root
        self.tests_dir = tests_dir
        self.policy = policy
        self.findings: list[Finding] = []
        self.fixtures: list[tuple[str, Path, int]] = []
        self.test_fixture_uses: list[tuple[Path, set[str]]] = []
        self.fixture_dependency_uses: list[tuple[Path, set[str]]] = []

    def add(
        self,
        severity: str,
        code: str,
        path: Path,
        line: int,
        message: str,
    ) -> None:
        try:
            display_path = str(path.relative_to(self.root))
        except ValueError:
            display_path = str(path)
        self.findings.append(
            Finding(display_path, line, severity, code, message)
        )

    def run(self) -> list[Finding]:
        for path in sorted(self.tests_dir.rglob("*.py")):
            self.audit_file(path)
        self.audit_fixture_visibility()
        self.audit_source_savepoints()
        self.add(
            "MANUAL",
            "SEM001",
            self.tests_dir,
            1,
            "reconcile a transient contract-evidence matrix: complete operation "
            "census, applicable policy depth, primary node/categories, and every "
            "application-owned observable outcome class",
        )
        focused = [
            selector
            for selector, decision in self.policy.coverage_rules
            if decision == "focused"
        ]
        if focused:
            self.add(
                "MANUAL",
                "SEM002",
                self.tests_dir,
                1,
                "focused selectors still require a complete matching-surface census: "
                + ", ".join(sorted(focused)),
            )
        if (self.tests_dir / "test_schedulers").is_dir():
            self.add(
                "MANUAL",
                "SEM003",
                self.tests_dir / "test_schedulers",
                1,
                "verify selected scheduler contracts observe actual framework "
                "callback/trigger registration without a live-clock race",
            )
        if (self.tests_dir / "test_workers").is_dir():
            self.add(
                "MANUAL",
                "SEM004",
                self.tests_dir / "test_workers",
                1,
                "verify selected worker success paths have a positive settlement "
                "artifact and handler outcome matrices cover preservation/rejection "
                "branches",
            )
        return sorted(self.findings)

    def audit_file(self, path: Path) -> None:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as error:
            line = getattr(error, "lineno", None) or 1
            self.add("ERROR", "PY001", path, line, f"cannot parse file: {error}")
            return

        functions = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        fixtures = [node for node in functions if is_fixture(node)]
        tests = [TestNode(node) for node in functions if node.name.startswith("test_")]
        test_classes = [
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test")
        ]
        for test_class in test_classes:
            methods = [
                node
                for node in test_class.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            fixtures.extend(node for node in methods if is_fixture(node))
            class_tests = [node for node in methods if node.name.startswith("test_")]
            tests.extend(
                TestNode(node, tuple(test_class.decorator_list)) for node in class_tests
            )
            collected_variants = has_multiple_param_rows(test_class.decorator_list) or any(
                has_multiple_param_rows(node.decorator_list) for node in class_tests
            )
            reusable_preparation = has_wide_scoped_fixture(methods)
            if path.name == "test_validation.py":
                self.add(
                    "ERROR",
                    "CLS002",
                    path,
                    test_class.lineno,
                    "validation fields use parametrized functions, not TestClass grouping",
                )
            if (
                self.policy.prefer_test_classes
                and len(class_tests) == 1
                and not (collected_variants and reusable_preparation)
            ):
                self.add(
                    "WARNING",
                    "CLS001",
                    path,
                    test_class.lineno,
                    "TestClass contains one case; use a function unless the class "
                    "materially reuses expensive preparation",
                )

        if tests:
            self.audit_test_path(path)
        if path.name == "test_success.py" and self.policy.layout == "standard":
            self.add(
                "ERROR" if self.policy.configured else "WARNING",
                "STR003",
                path,
                1,
                "active standard layout forbids test_success.py",
            )

        self.audit_imports(path, tree)
        self.audit_calls(path, tree)
        self.audit_conftest(path, tree, fixtures)
        self.audit_assertion_helpers(path, tree, tests, fixtures)
        self.audit_public_client_fields(path, tree)
        self.audit_matcher_bounds(path, tree)

        for fixture in fixtures:
            self.fixtures.append((fixture.name, path, fixture.lineno))
            self.fixture_dependency_uses.append((path, function_args(fixture)))
            alias = is_simple_alias_fixture(fixture)
            if alias:
                self.add(
                    "ERROR",
                    "FIX003",
                    path,
                    fixture.lineno,
                    f"fixture merely aliases {alias!r}; expose its owner or a "
                    "purposeful typed projection",
                )
            if fixture_returns_generated_value(fixture):
                self.add(
                    "ERROR",
                    "GEN003",
                    path,
                    fixture.lineno,
                    "generated UUID/time/payload/domain values are arrange-time calls, "
                    "not fixtures",
                )

        for test in tests:
            arguments = function_args(test.node)
            self.test_fixture_uses.append((path, arguments))
            for argument in sorted(arguments):
                if argument.startswith("_"):
                    self.add(
                        "ERROR",
                        "FIX001",
                        path,
                        test.node.lineno,
                        f"test directly requests private fixture {argument!r}",
                    )
                if argument in {"monkeypatch", "mocker", "mock"}:
                    self.add(
                        "MANUAL",
                        "MOCK001",
                        path,
                        test.node.lineno,
                        f"verify fixture {argument!r} does not patch application source",
                    )
            self.audit_test_decorators(
                path,
                test.node,
                (*test.inherited_decorators, *test.node.decorator_list),
            )
            self.audit_test_semantics(
                path,
                test.node,
                (*test.inherited_decorators, *test.node.decorator_list),
            )

    def audit_test_path(self, path: Path) -> None:
        relative = path.relative_to(self.tests_dir)
        directories = relative.parts[:-1]
        for directory in directories:
            if directory in {"test_infrastructure", "test_application"}:
                self.add(
                    "ERROR",
                    "STR004",
                    path,
                    1,
                    f"forbidden generic test group {directory!r}",
                )
        if self.policy.layout != "standard" or directories == ("test_health",):
            return
        if not 2 <= len(directories) <= 3:
            self.add(
                "ERROR" if self.policy.configured else "WARNING",
                "STR005",
                path,
                1,
                "active standard layout requires functional group + optional "
                "area + terminal component",
            )
        for directory in directories:
            if not directory.startswith("test_"):
                self.add(
                    "ERROR" if self.policy.configured else "WARNING",
                    "STR006",
                    path,
                    1,
                    f"active standard layout requires test_ directory {directory!r}",
                )

    def audit_test_semantics(
        self,
        path: Path,
        test: ast.FunctionDef | ast.AsyncFunctionDef,
        decorators: Sequence[ast.expr],
    ) -> None:
        if path.name == "test_validation.py":
            ids = literal_param_ids(decorators)
            boundary_tokens = ("minimum", "maximum", "boundary", "below-", "above-")
            ordinary_tokens = ("ordinary", "random", "typical")
            if any(token in value for token in boundary_tokens for value in ids) and not any(
                token in value for token in ordinary_tokens for value in ids
            ):
                self.add(
                    "WARNING",
                    "VAL002",
                    path,
                    test.lineno,
                    "boundary validation matrix has no explicit randomized "
                    "ordinary-valid row; confirm the enum-only exception",
                )

        call_counts: dict[str, list[ast.Call]] = {}
        tested_arguments = {
            name
            for name in function_args(test)
            if any(
                token in name
                for token in ("api_client", "worker", "runner", "scheduler", "job", "publisher")
            )
        }
        invocation_leaves = {
            "delete",
            "get",
            "handle",
            "patch",
            "post",
            "process",
            "publish",
            "put",
            "request",
            "run",
            "run_once",
        }
        for node in ast.walk(test):
            if not isinstance(node, ast.Call):
                continue
            name = dotted_name(node.func) or ""
            owner = name.split(".", 1)[0]
            leaf = name.rsplit(".", 1)[-1]
            if owner in tested_arguments and leaf in invocation_leaves:
                call_counts.setdefault(owner, []).append(node)
        for owner, calls in call_counts.items():
            if len(calls) > 1:
                self.add(
                    "MANUAL",
                    "CALL002",
                    path,
                    calls[1].lineno,
                    f"{owner!r} is invoked {len(calls)} times; cite the authoritative "
                    "repetition contract or reduce to one invocation",
                )

        assigned_json_names = {
            target.id
            for node in ast.walk(test)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            for target in (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            if isinstance(target, ast.Name)
            and node.value is not None
            and is_json_call(node.value)
        }
        partial_json = any(
            isinstance(node, ast.Subscript)
            and (
                is_json_call(node.value)
                or isinstance(node.value, ast.Name)
                and node.value.id in assigned_json_names
            )
            for node in ast.walk(test)
        )
        full_json_equality = False
        for node in ast.walk(test):
            if not isinstance(node, ast.Compare) or not any(
                isinstance(operator, (ast.Eq, ast.NotEq)) for operator in node.ops
            ):
                continue
            operands = [node.left, *node.comparators]
            if any(
                is_json_call(operand)
                or isinstance(operand, ast.Name)
                and operand.id in assigned_json_names
                for operand in operands
            ):
                full_json_equality = True
                break
        if test.name == "test_contract" and partial_json and not full_json_equality:
            self.add(
                "MANUAL",
                "CON002",
                path,
                test.lineno,
                "primary contract indexes the response body but never exact-compares "
                "the complete public value",
            )

        split_roots: dict[str, int] = {}
        for node in ast.walk(test):
            if not isinstance(node, ast.Assert):
                continue
            roots = {
                root
                for candidate in ast.walk(node.test)
                if (root := observation_root(candidate)) is not None
                and root.startswith("actual")
                and "response" not in root
            }
            for root in roots:
                split_roots[root] = split_roots.get(root, 0) + 1
        for root, count in split_roots.items():
            if count >= 3:
                self.add(
                    "WARNING",
                    "AST002",
                    path,
                    test.lineno,
                    f"compound observation {root!r} is split across {count} "
                    "assertions; prefer one exact/matcher equality",
                )

    def audit_public_client_fields(self, path: Path, tree: ast.Module) -> None:
        if path.name != "client.py":
            return
        raw_names = {
            "channel",
            "collector",
            "deliveries",
            "delivery_source",
            "exchange",
            "publisher",
            "queue",
            "raw_exchange",
            "rejected",
            "routing_key",
            "runtime",
            "worker",
        }
        for class_node in (
            node for node in tree.body if isinstance(node, ast.ClassDef)
        ):
            if not any(
                token in class_node.name.lower()
                for token in ("client", "runner", "harness")
            ):
                continue
            for statement in class_node.body:
                field_name: str | None = None
                if isinstance(statement, ast.AnnAssign) and isinstance(
                    statement.target, ast.Name
                ):
                    field_name = statement.target.id
                elif (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                ):
                    field_name = statement.targets[0].id
                if field_name in raw_names:
                    self.add(
                        "WARNING",
                        "BOUND001",
                        path,
                        statement.lineno,
                        f"public client field {field_name!r} exposes raw "
                        "runtime/transport mechanics; keep it private behind a domain "
                        "operation",
                    )

    def audit_matcher_bounds(self, path: Path, tree: ast.Module) -> None:
        relative_parts = path.relative_to(self.tests_dir).parts
        if "cmp" not in relative_parts:
            return
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Pow)
                and isinstance(node.left, ast.Constant)
                and isinstance(node.left.value, int)
                and isinstance(node.right, ast.Constant)
                and isinstance(node.right.value, int)
            ):
                self.add(
                    "MANUAL",
                    "CMP001",
                    path,
                    node.lineno,
                    "numeric power used in matcher bounds; verify it is not a finite "
                    "sentinel for an unbounded constraint",
                )
                return

    def audit_source_savepoints(self) -> None:
        for path in sorted(self.root.rglob("*.py")):
            if path.is_relative_to(self.tests_dir) or any(
                part in {".git", ".venv", "build", "dist"} for part in path.parts
            ):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, UnicodeError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    for index, key in enumerate(node.keys):
                        value = node.values[index]
                        if (
                            isinstance(key, ast.Constant)
                            and key.value == "join_transaction_mode"
                            and isinstance(value, ast.Constant)
                            and value.value == "create_savepoint"
                        ):
                            self.add(
                                "MANUAL",
                                "DB002",
                                path,
                                node.lineno,
                                "create_savepoint appears in production binding; "
                                "verify it is selected only by an explicit test "
                                "opt-in, never the general session path",
                            )
                if not isinstance(node, ast.Call):
                    continue
                for keyword in node.keywords:
                    if (
                        keyword.arg == "join_transaction_mode"
                        and isinstance(keyword.value, ast.Constant)
                        and keyword.value.value == "create_savepoint"
                    ):
                        self.add(
                            "MANUAL",
                            "DB002",
                            path,
                            node.lineno,
                            "create_savepoint appears in production binding; verify it "
                            "is selected only by an explicit test opt-in, never the "
                            "general session path",
                        )

    def audit_imports(self, path: Path, tree: ast.Module) -> None:
        backend_modules = {
            "faker": "faker",
            "polyfactory": "polyfactory",
            "factory-boy": "factory_boy",
        }
        selected_backend_module = backend_modules.get(
            self.policy.generators_backend,
            self.policy.generators_backend.replace("-", "_"),
        )
        relative_parts = path.relative_to(self.tests_dir).parts
        generator_facade = path.name in {"fake.py", "generators.py"} or any(
            part in {"data_generation", "factories", "fake", "generators"}
            for part in relative_parts[:-1]
        )
        for node in ast.walk(tree):
            modules: list[str] = []
            line = getattr(node, "lineno", 1)
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
                imported = {alias.name for alias in node.names}
                if (node.module or "").startswith("sqlalchemy") and imported & {
                    "Session",
                    "AsyncSession",
                    "sessionmaker",
                    "async_sessionmaker",
                }:
                    self.add(
                        "ERROR",
                        "DB001",
                        path,
                        node.lineno,
                        "SQLAlchemy session APIs are forbidden in test support",
                    )
            for module in modules:
                root_module = module.split(".", 1)[0]
                if path.name == "conftest.py" and root_module in {
                    "aio_pika",
                    "aioboto3",
                    "asyncpg",
                    "boto3",
                    "redis",
                }:
                    self.add(
                        "WARNING",
                        "CONF004",
                        path,
                        line,
                        f"conftest imports raw SDK {root_module!r}; delegate "
                        "topology/runtime/cleanup mechanics to an ordinary module",
                    )
                if (
                    root_module
                    in {"aioresponses", "requests_mock", "responses", "respx"}
                    and self.policy.configured
                    and self.policy.external_services == "testcontainers"
                ):
                    self.add(
                        "ERROR",
                        "ENV005",
                        path,
                        line,
                        f"{root_module} contradicts active external_services "
                        "'testcontainers'; select 'mixed' when different external "
                        "integrations intentionally use different backends",
                    )
                if module == "freezegun" or module.startswith("freezegun."):
                    self.add("ERROR", "TIME001", path, line, "time freezing is forbidden")
                if module in {"mock", "unittest.mock", "pytest_mock"}:
                    self.add(
                        "WARNING",
                        "MOCK002",
                        path,
                        line,
                        "generic mock tooling requires manual application-source "
                        "boundary review; prefer a typed performance double/Service",
                    )
                if root_module in set(backend_modules.values()):
                    if self.policy.configured and root_module != selected_backend_module:
                        self.add(
                            "ERROR",
                            "GEN001",
                            path,
                            line,
                            f"{root_module} contradicts active generators_backend "
                            f"{self.policy.generators_backend!r}",
                        )
                    elif not generator_facade:
                        self.add(
                            "ERROR"
                            if self.policy.configured and self.policy.layout == "standard"
                            else "MANUAL",
                            "GEN002",
                            path,
                            line,
                            "generated-data backend import must stay behind the "
                            "project generator facade",
                        )
                if module == "testcontainers" or module.startswith("testcontainers."):
                    internal_tokens = {
                        "clickhouse",
                        "cockroachdb",
                        "elasticsearch",
                        "kafka",
                        "localstack",
                        "mongodb",
                        "mssql",
                        "mysql",
                        "neo4j",
                        "oracle",
                        "postgres",
                        "rabbitmq",
                        "redis",
                    }
                    parts = set(module.split("."))
                    internal_role = bool(parts & internal_tokens)
                    selected = (
                        self.policy.infrastructure == "testcontainers"
                        if internal_role
                        else self.policy.external_services in {"testcontainers", "mixed"}
                    )
                    if selected:
                        continue
                    if internal_role:
                        severity = "ERROR" if self.policy.configured else "WARNING"
                        message = (
                            "internal Testcontainers usage contradicts active "
                            "infrastructure policy"
                            if self.policy.configured
                            else "confirm Testcontainers as the internal infrastructure provider"
                        )
                    else:
                        severity = "MANUAL"
                        message = (
                            "classify Testcontainers usage as internal infrastructure "
                            "or external mock servers and confirm the matching policy"
                        )
                    self.add(severity, "ENV001", path, line, message)
                if module == "subprocess":
                    self.add(
                        "WARNING",
                        "ENV002",
                        path,
                        line,
                        "subprocess requires a documented no-library/API opt-in",
                    )

    def audit_calls(self, path: Path, tree: ast.Module) -> None:
        forbidden_calls = {
            "time.sleep": ("WAIT001", "sleep is forbidden"),
            "asyncio.sleep": ("WAIT001", "sleep is forbidden"),
            "anyio.sleep": ("WAIT001", "sleep is forbidden"),
            "trio.sleep": ("WAIT001", "sleep is forbidden"),
            "asyncio.run": ("LOOP001", "manual event-loop driving is forbidden"),
            "asyncio.Runner": ("LOOP001", "manual event-loop creation is forbidden"),
            "asyncio.new_event_loop": ("LOOP001", "multiple event loops are forbidden"),
            "asyncio.set_event_loop": ("LOOP001", "manual event-loop setup is forbidden"),
        }
        forbidden_leaf_calls = {
            "run_until_complete": ("LOOP001", "manual event-loop driving is forbidden"),
            "freeze_time": ("TIME001", "time freezing is forbidden"),
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = dotted_name(node.func) or ""
            leaf = name.rsplit(".", 1)[-1]
            violation = forbidden_calls.get(name) or forbidden_leaf_calls.get(leaf)
            if violation:
                code, message = violation
                self.add("ERROR", code, path, node.lineno, message)
            if leaf == "wait_for" and "messaging" in path.parts:
                self.add(
                    "ERROR",
                    "WAIT002",
                    path,
                    node.lineno,
                    "messaging must use deterministic completion and no-wait collection",
                )
            if (
                name in {"patch", "mock.patch", "unittest.mock.patch"}
                or name.startswith(("monkeypatch.", "mocker.patch"))
            ):
                self.add(
                    "MANUAL",
                    "MOCK003",
                    path,
                    node.lineno,
                    "verify this mutation does not replace application source/internal calls",
                )
            if name in {"subprocess.run", "subprocess.call", "subprocess.Popen"}:
                literals = [
                    value.value.lower()
                    for value in ast.walk(node)
                    if isinstance(value, ast.Constant) and isinstance(value.value, str)
                ]
                joined = " ".join(literals)
                if "docker compose" in joined and self.policy.compose_lifecycle == "disabled":
                    self.add(
                        "ERROR" if self.policy.configured else "WARNING",
                        "ENV003",
                        path,
                        node.lineno,
                        (
                            "Docker Compose contradicts active compose_lifecycle policy"
                            if self.policy.configured
                            else "confirm the Docker Compose lifecycle during onboarding"
                        ),
                    )
                if "alembic" in joined:
                    self.add(
                        "ERROR",
                        "ENV004",
                        path,
                        node.lineno,
                        "run Alembic through its in-process Python API",
                    )
            if leaf == "model_copy" and (
                path.name in {"settings.py", "conftest.py"}
                or "fixtures" in path.relative_to(self.tests_dir).parts
            ):
                deep = next(
                    (keyword.value for keyword in node.keywords if keyword.arg == "deep"),
                    None,
                )
                if not (
                    isinstance(deep, ast.Constant) and deep.value is True
                ):
                    self.add(
                        "WARNING",
                        "CFG002",
                        path,
                        node.lineno,
                        "settings model_copy is shallow; verify recursive immutability "
                        "or use an explicit deep case copy",
                    )

    def audit_conftest(
        self,
        path: Path,
        tree: ast.Module,
        fixtures: Sequence[ast.FunctionDef | ast.AsyncFunctionDef],
    ) -> None:
        if path.name != "conftest.py":
            return
        if path.parent == self.tests_dir:
            for fixture in fixtures:
                self.add(
                    "ERROR",
                    "FIX002",
                    path,
                    fixture.lineno,
                    "root conftest.py may register plugins/hooks but not define fixtures",
                )
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self.add(
                    "ERROR",
                    "CONF001",
                    path,
                    node.lineno,
                    "ordinary support classes do not belong in conftest.py",
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not is_fixture(node) and not node.name.startswith("pytest_"):
                    self.add(
                        "ERROR",
                        "CONF002",
                        path,
                        node.lineno,
                        "ordinary helper functions do not belong in conftest.py",
                    )
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                names: set[str] = set()
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
                if names and names != {"pytest_plugins"}:
                    self.add(
                        "ERROR",
                        "CONF003",
                        path,
                        node.lineno,
                        "ordinary constants/state do not belong in conftest.py",
                    )

    def audit_assertion_helpers(
        self,
        path: Path,
        tree: ast.Module,
        tests: Sequence[TestNode],
        fixtures: Sequence[ast.FunctionDef | ast.AsyncFunctionDef],
    ) -> None:
        allowed_ids = {id(test.node) for test in tests} | {id(node) for node in fixtures}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if id(node) in allowed_ids or node.name == "__eq__":
                continue
            if any(isinstance(candidate, ast.Assert) for candidate in ast.walk(node)):
                self.add(
                    "ERROR",
                    "AST001",
                    path,
                    node.lineno,
                    "assertion helper is forbidden; keep assert in the test and "
                    "extract a builder/matcher",
                )

    def audit_test_decorators(
        self,
        path: Path,
        test: ast.FunctionDef | ast.AsyncFunctionDef,
        decorators: Sequence[ast.expr],
    ) -> None:
        parametrized_names: set[str] = set()
        for decorator in decorators:
            if not isinstance(decorator, ast.Call):
                continue
            name = dotted_name(decorator.func) or ""
            if name.rsplit(".", 1)[-1] == "usefixtures":
                for argument in decorator.args:
                    if isinstance(argument, ast.Constant) and isinstance(
                        argument.value, str
                    ):
                        self.test_fixture_uses.append((path, {argument.value}))
            if name.rsplit(".", 1)[-1] != "parametrize" or len(decorator.args) < 2:
                continue
            parametrized_names.update(self.parametrize_names(decorator.args[0]))
            rows = decorator.args[1]
            if isinstance(rows, (ast.List, ast.Tuple)):
                ids_node = next(
                    (
                        keyword.value
                        for keyword in decorator.keywords
                        if keyword.arg == "ids"
                    ),
                    decorator.args[3] if len(decorator.args) > 3 else None,
                )
                if ids_node is None:
                    for row in rows.elts:
                        self.audit_param_row(path, row)
                elif isinstance(ids_node, (ast.List, ast.Tuple)):
                    valid_ids = all(
                        isinstance(value, ast.Constant)
                        and isinstance(value.value, str)
                        and bool(value.value.strip())
                        for value in ids_node.elts
                    )
                    if not valid_ids or len(ids_node.elts) != len(rows.elts):
                        self.add(
                            "ERROR",
                            "PAR005",
                            path,
                            ids_node.lineno,
                            "ids must provide one non-empty literal name per row",
                        )
                else:
                    self.add(
                        "MANUAL",
                        "PAR006",
                        path,
                        getattr(ids_node, "lineno", decorator.lineno),
                        "dynamic ids require manual readability/completeness review",
                    )
            else:
                self.add(
                    "WARNING",
                    "PAR001",
                    path,
                    decorator.lineno,
                    "dynamic parametrization rows require manual ID/value review",
                )
            fresh = FreshValueVisitor()
            fresh.visit(rows)
            for call in fresh.calls:
                self.add(
                    "ERROR",
                    "PAR002",
                    path,
                    call.lineno,
                    "fresh value is created during collection; use an arrange-time factory",
                )

        scenario_names = {
            name
            for name in parametrized_names
            if "scenario" in name.lower()
            or name.lower().endswith("case")
            or "_case_" in name.lower()
        }
        if not scenario_names:
            return
        for node in ast.walk(test):
            candidate: ast.AST | None = None
            if isinstance(node, ast.Match):
                candidate = node.subject
            elif isinstance(node, ast.If):
                candidate = node.test
            if candidate is None:
                continue
            visitor = NameUseVisitor(scenario_names)
            visitor.visit(candidate)
            if visitor.found:
                self.add(
                    "WARNING",
                    "PAR003",
                    path,
                    getattr(node, "lineno", 1),
                    "scenario label appears to drive control flow; parametrize values/factories",
                )

    @staticmethod
    def parametrize_names(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return {part.strip() for part in node.value.split(",") if part.strip()}
        if isinstance(node, (ast.List, ast.Tuple)):
            return {
                element.value
                for element in node.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            }
        return set()

    def audit_param_row(self, path: Path, row: ast.AST) -> None:
        if not isinstance(row, ast.Call) or dotted_name(row.func) != "pytest.param":
            self.add(
                "ERROR",
                "PAR004",
                path,
                getattr(row, "lineno", 1),
                "every variation needs pytest.param(..., id=...) or a complete "
                "parametrize ids list",
            )
            return
        ids = [keyword.value for keyword in row.keywords if keyword.arg == "id"]
        if (
            len(ids) != 1
            or not isinstance(ids[0], ast.Constant)
            or not isinstance(ids[0].value, str)
            or not ids[0].value.strip()
        ):
            self.add(
                "ERROR",
                "PAR005",
                path,
                row.lineno,
                "pytest.param row requires one non-empty literal id",
            )

    def audit_fixture_visibility(self) -> None:
        for name, path, line in sorted(
            self.fixtures,
            key=lambda item: (str(item[1]), item[2], item[0]),
        ):
            if name.startswith("_"):
                continue
            used_by_test = any(
                name in names and self.fixture_visible_from(path, use_path)
                for use_path, names in self.test_fixture_uses
            )
            if used_by_test:
                continue
            used_by_fixture = any(
                name in names and self.fixture_visible_from(path, use_path)
                for use_path, names in self.fixture_dependency_uses
            )
            if used_by_fixture:
                message = "fixture is used only by fixtures; prefix it with _"
            else:
                message = "public fixture is not requested by a test; verify or privatize it"
            self.add("ERROR", "FIX004", path, line, message)

    def fixture_visible_from(self, definition: Path, consumer: Path) -> bool:
        if definition.name == "conftest.py":
            try:
                consumer.relative_to(definition.parent)
            except ValueError:
                return False
            return True
        relative = definition.relative_to(self.tests_dir)
        if relative.parts and relative.parts[0] == "fixtures":
            return True
        return definition == consumer


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit mechanically detectable pytest-blackbox rules."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        type=Path,
        help="project root containing tests/ (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return a failing exit code for warnings as well as errors",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.project_root.resolve()
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        print(f"ERROR ROOT001 {tests_dir}: tests directory does not exist")
        return 2

    policy, policy_errors = load_policy(root)
    findings = Audit(root, tests_dir, policy).run()
    config_severity = "ERROR" if policy.configured else "WARNING"
    findings.extend(
        Finding("pyproject.toml", 1, config_severity, "CFG001", message)
        for message in policy_errors
    )
    findings = sorted(findings)
    for finding in findings:
        print(
            f"{finding.severity} {finding.code} "
            f"{finding.path}:{finding.line}: {finding.message}"
        )

    errors = sum(finding.severity == "ERROR" for finding in findings)
    warnings = sum(finding.severity == "WARNING" for finding in findings)
    manual = sum(finding.severity == "MANUAL" for finding in findings)
    print(
        f"\nSummary: {errors} error(s), {warnings} warning(s), "
        f"{manual} manual review item(s)"
    )
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
