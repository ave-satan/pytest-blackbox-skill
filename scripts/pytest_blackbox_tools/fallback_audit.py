"""Stdlib-first fallback checks for pytest-blackbox rules."""

from __future__ import annotations

import ast
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .models import Finding, Policy

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


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


def import_aliases(tree: ast.Module) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for imported in node.names:
                local = imported.asname or imported.name.split(".", 1)[0]
                aliases[local] = imported.name if imported.asname else local
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for imported in node.names:
                if imported.name == "*":
                    continue
                local = imported.asname or imported.name
                aliases[local] = f"{node.module}.{imported.name}"
    return aliases


def resolved_dotted_name(node: ast.AST, aliases: dict[str, str]) -> str | None:
    name = dotted_name(node)
    if not name:
        return None
    root, separator, remainder = name.partition(".")
    resolved_root = aliases.get(root, root)
    return f"{resolved_root}.{remainder}" if separator else resolved_root


class _ScopeSymbols(ast.NodeVisitor):
    def __init__(self) -> None:
        self.aliases: dict[str, str] = {}
        self.bound: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for imported in node.names:
            local = imported.asname or imported.name.split(".", 1)[0]
            self.aliases[local] = imported.name if imported.asname else local

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level != 0 or not node.module:
            return
        for imported in node.names:
            if imported.name != "*":
                self.aliases[imported.asname or imported.name] = (
                    f"{node.module}.{imported.name}"
                )

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self.bound.add(node.id)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.bound.add(node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.bound.add(node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.bound.add(node.name)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return None


def function_aliases(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    inherited: dict[str, str],
) -> dict[str, str]:
    symbols = _ScopeSymbols()
    for statement in node.body:
        symbols.visit(statement)
    bound = symbols.bound | function_args(node)
    aliases = {
        name: target
        for name, target in inherited.items()
        if name not in bound or name in symbols.aliases
    }
    aliases.update(symbols.aliases)
    return aliases


class _ResolvedCallVisitor(ast.NodeVisitor):
    def __init__(self, aliases: dict[str, str]) -> None:
        self.aliases = aliases
        self.names: dict[int, str] = {}

    def visit_Call(self, node: ast.Call) -> None:
        self.names[id(node)] = resolved_dotted_name(node.func, self.aliases) or ""
        self.generic_visit(node)

    def _visit_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        parent_aliases = self.aliases
        self.aliases = function_aliases(node, parent_aliases)
        for statement in node.body:
            self.visit(statement)
        self.aliases = parent_aliases

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)


def resolved_call_names(tree: ast.Module) -> dict[int, str]:
    visitor = _ResolvedCallVisitor(import_aliases(tree))
    visitor.visit(tree)
    return visitor.names


def function_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    positional = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    return {
        argument.arg for argument in positional if argument.arg not in {"self", "cls"}
    }


def function_arguments(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[ast.arg, ...]:
    return (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)


def assigned_names(node: ast.Assign | ast.AnnAssign) -> set[str]:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return {
        candidate.id
        for target in targets
        for candidate in ast.walk(target)
        if isinstance(candidate, ast.Name) and isinstance(candidate.ctx, ast.Store)
    }


def uses_any_name(node: ast.AST, names: set[str]) -> bool:
    return any(
        isinstance(candidate, ast.Name)
        and isinstance(candidate.ctx, ast.Load)
        and candidate.id in names
        for candidate in ast.walk(node)
    )


def production_settings_arguments(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: dict[str, str],
    tests_package: str,
) -> set[str]:
    result: set[str] = set()
    for argument in function_arguments(node):
        if argument.annotation is None:
            continue
        annotation = resolved_dotted_name(argument.annotation, aliases) or ""
        leaf = annotation.rsplit(".", 1)[-1].lower()
        if annotation.startswith(f"{tests_package}."):
            continue
        if leaf == "settings" or leaf.endswith(("settings", "config", "configuration")):
            result.add(argument.arg)
    return result


def tainted_names(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    initial: set[str],
) -> set[str]:
    tainted = set(initial)
    assignments = [
        candidate
        for candidate in ast.walk(node)
        if isinstance(candidate, (ast.Assign, ast.AnnAssign))
        and candidate.value is not None
    ]
    changed = True
    while changed:
        changed = False
        for assignment in assignments:
            if any(
                isinstance(candidate, ast.Await)
                for candidate in ast.walk(assignment.value)
            ):
                continue
            if not uses_any_name(assignment.value, tainted):
                continue
            new_names = {
                name
                for name in assigned_names(assignment) - tainted
                if not name.startswith("actual")
            }
            if new_names:
                tainted.update(new_names)
                changed = True
    return tainted


def source_test_owner(path: Path, tests_dir: Path) -> tuple[str, ...]:
    relative = path.relative_to(tests_dir).with_suffix("").parts
    return (tests_dir.name, *relative[:-1])


def imported_modules(
    node: ast.Import | ast.ImportFrom,
    source_owner: tuple[str, ...],
) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if node.level == 0:
        return [node.module or ""]

    retained = max(0, len(source_owner) - node.level + 1)
    parts = [*source_owner[:retained]]
    if node.module:
        parts.extend(node.module.split("."))
        return [".".join(parts)]
    return [".".join((*parts, alias.name)) for alias in node.names]


def imports_narrow_test_group(
    source_owner: tuple[str, ...],
    module: str,
    tests_package: str,
) -> bool:
    target = tuple(part for part in module.split(".") if part)
    if not target or target[0] != tests_package:
        return False
    common = 0
    for source_part, target_part in zip(source_owner, target, strict=False):
        if source_part != target_part:
            break
        common += 1
    return any(part.startswith("test_") for part in target[common:])


_CAPABILITY_FIXTURE_ROLES = {
    "client",
    "collector",
    "connection",
    "job",
    "publisher",
    "runner",
    "scheduler",
    "transport",
    "worker",
}
_CASE_STATE_MUTATION_NAMES = {
    "clear",
    "create",
    "delete",
    "expire",
    "insert",
    "mark",
    "remove",
    "replace",
    "reset",
    "revoke",
    "set",
    "update",
}


def is_capability_argument(name: str) -> bool:
    parts = set(name.split("_"))
    return bool(
        "client" in parts
        or parts
        & {
            "connection",
            "job",
            "publisher",
            "runner",
            "scheduler",
            "transport",
            "worker",
        }
    )


def is_stimulus_method(name: str) -> bool:
    exact_stimuli = {
        "connect",
        "delete",
        "get",
        "handle",
        "handshake",
        "head",
        "options",
        "patch",
        "post",
        "put",
        "request",
        "run",
        "run_once",
        "trace",
    }
    stimulus_prefixes = (
        "dispatch_",
        "execute_",
        "handle_",
        "invoke_",
        "process_",
        "publish_",
        "run_",
        "send_",
        "trigger_",
    )
    return name in exact_stimuli or name.startswith(stimulus_prefixes)


def direct_capability_call(
    node: ast.Call,
    capability_arguments: set[str],
) -> bool:
    name = dotted_name(node.func) or ""
    owner, separator, remainder = name.partition(".")
    if not separator or owner not in capability_arguments:
        return False
    leaf = remainder.rsplit(".", 1)[-1]
    return is_stimulus_method(leaf)


def capability_fixture_repository_mutation(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[str, str, int] | None:
    if node.name.startswith("_"):
        return None
    name_parts = set(node.name.split("_"))
    if not name_parts & _CAPABILITY_FIXTURE_ROLES:
        return None
    non_capability_suffixes = {
        "config",
        "context",
        "credentials",
        "identity",
        "record",
        "repository",
        "result",
        "settings",
        "state",
    }
    if node.name.rsplit("_", 1)[-1] in non_capability_suffixes:
        return None
    repositories = {
        argument for argument in function_args(node) if argument.endswith("_repository")
    }
    if not repositories:
        return None
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call):
            continue
        function = candidate.func
        if not (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id in repositories
        ):
            continue
        method_root = function.attr.split("_", 1)[0]
        if method_root in _CASE_STATE_MUTATION_NAMES:
            return function.value.id, function.attr, candidate.lineno
    return None


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
                (
                    keyword.value
                    for keyword in decorator.keywords
                    if keyword.arg == "scope"
                ),
                None,
            )
            if isinstance(scope, ast.Constant) and scope.value in {"class", "session"}:
                return True
    return False


def is_simple_alias_fixture(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    body = list(node.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
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
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
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
    def __init__(self, aliases: dict[str, str] | None = None) -> None:
        self.calls: list[ast.Call] = []
        self.aliases = aliases or {}

    def visit_Call(self, node: ast.Call) -> None:
        name = resolved_dotted_name(node.func, self.aliases) or ""
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
    if (root / ".git").exists() and not (root / "pyproject.toml").is_file():
        return root / "pyproject.toml"
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
        return Policy(configured=True), [f"cannot read pyproject.toml: {error}"]
    tool = data.get("tool")
    if not isinstance(tool, dict) or "pytest-blackbox" not in tool:
        return Policy(), ["[tool.pytest-blackbox] is absent; run project onboarding"]
    raw = tool.get("pytest-blackbox")
    if not isinstance(raw, dict):
        return Policy(configured=True), ["[tool.pytest-blackbox] must be a table"]

    errors: list[str] = []
    supported_keys = {
        "compose_lifecycle",
        "config_version",
        "coverage",
        "dependency_group",
        "external_services",
        "generators_backend",
        "infrastructure",
        "layout",
        "prefer_test_classes",
        "test_concurrency",
    }
    unknown_keys = sorted(set(raw) - supported_keys)
    if unknown_keys:
        errors.append("unsupported configuration keys: " + ", ".join(unknown_keys))
    version = raw.get("config_version")
    layout = raw.get("layout", "standard")
    compose = raw.get("compose_lifecycle", "disabled")
    external = raw.get("external_services", "intercept")
    infrastructure = raw.get("infrastructure", "existing-services")
    generators_backend = raw.get("generators_backend", "faker")
    dependency_group = raw.get("dependency_group")
    prefer_classes = raw.get("prefer_test_classes", True)
    test_concurrency = raw.get("test_concurrency", False)
    if type(version) is not int or version != 1:
        errors.append(f"unsupported or missing config_version {version!r}")
    if not isinstance(layout, str) or layout not in {"standard", "preserve"}:
        errors.append(f"unsupported layout {layout!r}")
    if not isinstance(compose, str) or compose not in {"disabled", "enabled"}:
        errors.append(f"unsupported compose_lifecycle {compose!r}")
    if not isinstance(external, str) or external not in {
        "intercept",
        "testcontainers",
        "mixed",
    }:
        errors.append(f"unsupported external_services {external!r}")
    if not isinstance(prefer_classes, bool):
        errors.append("prefer_test_classes must be boolean")
        prefer_classes = True
    if not isinstance(test_concurrency, bool):
        errors.append("test_concurrency must be boolean")
        test_concurrency = False
    for key, value in (
        ("infrastructure", infrastructure),
        ("generators_backend", generators_backend),
    ):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string")
    if not isinstance(infrastructure, str) or not infrastructure.strip():
        infrastructure = "existing-services"
    if not isinstance(generators_backend, str) or not generators_backend.strip():
        generators_backend = "faker"
    if dependency_group is not None:
        if not isinstance(dependency_group, str) or not dependency_group.strip():
            errors.append("dependency_group must be a non-empty string when enabled")
            dependency_group = None
        elif dependency_group.strip().lower() in {
            "default",
            "dev",
            "development",
            "lint",
            "linting",
            "main",
            "qa",
            "runtime",
            "test",
            "testing",
        }:
            errors.append(
                "dependency_group must name a dedicated AI/tooling group, "
                "not a runtime, general dev, or test group"
            )
            dependency_group = None
        else:
            dependency_group = dependency_group.strip()
    coverage = raw.get("coverage", [])
    coverage_rules: list[tuple[str, str]] = []
    seen_selectors: dict[str, int] = {}
    if not isinstance(coverage, list):
        errors.append("coverage must be an array of tables")
    else:
        http_prefixes = (
            "CONNECT ",
            "DELETE ",
            "GET ",
            "HEAD ",
            "OPTIONS ",
            "PATCH ",
            "POST ",
            "PUT ",
            "TRACE ",
        )
        for index, rule in enumerate(coverage, start=1):
            if not isinstance(rule, dict):
                errors.append(f"coverage rule {index} must be a table")
                continue
            unknown_rule_keys = sorted(
                set(rule) - {"selector", "decision", "rationale"}
            )
            if unknown_rule_keys:
                errors.append(
                    f"coverage rule {index} has unsupported keys: "
                    + ", ".join(unknown_rule_keys)
                )
            selector = rule.get("selector")
            decision = rule.get("decision")
            rationale = rule.get("rationale")
            if not isinstance(selector, str) or not selector.strip():
                errors.append(f"coverage rule {index} requires a selector")
            else:
                selector = selector.strip()
                selector_key = selector.casefold()
                if selector.upper().startswith(http_prefixes) or selector.startswith(
                    "/"
                ):
                    errors.append(
                        f"coverage rule {index} looks operation-specific; "
                        "use a generalized non-contract surface selector"
                    )
                if selector_key in seen_selectors:
                    errors.append(
                        f"coverage rule {index} duplicates selector {selector!r} "
                        f"from rule {seen_selectors[selector_key]}"
                    )
                else:
                    seen_selectors[selector_key] = index
            if not isinstance(decision, str) or decision not in {
                "exclude",
                "focused",
                "standard",
            }:
                errors.append(
                    f"coverage rule {index} has invalid decision {decision!r}"
                )
            if not isinstance(rationale, str) or not rationale.strip():
                errors.append(f"coverage rule {index} requires a rationale")
            if (
                isinstance(selector, str)
                and isinstance(decision, str)
                and decision
                in {
                    "exclude",
                    "focused",
                    "standard",
                }
            ):
                coverage_rules.append((selector, decision))
    return (
        Policy(
            configured=True,
            layout=(
                layout
                if isinstance(layout, str) and layout in {"standard", "preserve"}
                else "standard"
            ),
            prefer_test_classes=prefer_classes,
            test_concurrency=test_concurrency,
            compose_lifecycle=(
                compose
                if isinstance(compose, str) and compose in {"disabled", "enabled"}
                else "disabled"
            ),
            external_services=(
                external
                if isinstance(external, str)
                and external in {"intercept", "testcontainers", "mixed"}
                else "intercept"
            ),
            infrastructure=infrastructure,
            generators_backend=generators_backend,
            dependency_group=dependency_group,
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
        self.findings.append(Finding(display_path, line, severity, code, message))

    def run(self) -> list[Finding]:
        for path in sorted(self.tests_dir.rglob("*.py")):
            self.audit_file(path)
        self.audit_fixture_visibility()
        self.audit_source_savepoints()
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
        aliases = import_aliases(tree)
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
            collected_variants = has_multiple_param_rows(
                test_class.decorator_list
            ) or any(
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
        forbidden_generic_categories = {
            "test_behavior.py",
            "test_happy_path.py",
            "test_success.py",
            "test_technical.py",
            "test_works.py",
        }
        if (
            path.name in forbidden_generic_categories
            and self.policy.layout == "standard"
        ):
            self.add(
                "ERROR" if self.policy.configured else "WARNING",
                "STR003",
                path,
                1,
                f"active standard layout forbids vague category {path.name!r}; "
                "name the public contract behavior instead",
            )
        if tests and path.name == "test_topology.py":
            self.add(
                "ERROR",
                "STR007",
                path,
                1,
                "broker topology is a private session-bootstrap invariant, not a "
                "collected test module; remove this surface and invoke the real "
                "production bootstrap from fixture-owned environment setup",
            )

        self.audit_imports(path, tree)
        self.audit_calls(path, tree, aliases)
        self.audit_conftest(path, tree, fixtures)
        self.audit_assertion_helpers(path, tree, tests, fixtures)
        self.audit_public_client_fields(path, tree)
        self.audit_cross_component_private_access(path, tree)
        self.audit_matcher_bounds(path, tree)
        self.audit_temporal_matchers(path, tree, aliases)
        self.audit_production_settings_oracles(
            path,
            functions,
            fixtures,
            tests,
            aliases,
        )

        for fixture in fixtures:
            self.fixtures.append((fixture.name, path, fixture.lineno))
            self.fixture_dependency_uses.append((path, function_args(fixture)))
            mutation = capability_fixture_repository_mutation(fixture)
            if mutation:
                repository, method, line = mutation
                self.add(
                    "ERROR",
                    "FIX005",
                    path,
                    line,
                    f"public capability fixture {fixture.name!r} mutates repository "
                    f"state through {repository}.{method}(); move baseline creation "
                    "to a private typed context or arrange a special transition "
                    "visibly in the test",
                )
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
                aliases,
            )
            self.audit_test_semantics(
                path,
                test.node,
                (*test.inherited_decorators, *test.node.decorator_list),
                aliases,
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
        _decorators: Sequence[ast.expr],
        aliases: dict[str, str],
    ) -> None:
        scoped_aliases = function_aliases(test, aliases)
        for node in ast.walk(test):
            if not isinstance(node, (ast.With, ast.AsyncWith)):
                continue
            connects = [
                item.context_expr
                for item in node.items
                if isinstance(item.context_expr, ast.Call)
                and (dotted_name(item.context_expr.func) or "").rsplit(".", 1)[-1]
                in {"connect", "websocket_connect"}
            ]
            if connects and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                self.add(
                    "ERROR",
                    "WS001",
                    path,
                    node.lineno,
                    "empty WebSocket connection context hides the observable lifecycle "
                    "outcome; expose and assert a natural accepted/denied/close value "
                    "through the test-owned adapter",
                )

        call_counts: dict[str, list[ast.Call]] = {}
        tested_arguments = {
            name for name in function_args(test) if is_capability_argument(name)
        }
        for node in ast.walk(test):
            if not isinstance(node, ast.Call):
                continue
            name = dotted_name(node.func) or ""
            owner = name.split(".", 1)[0]
            if direct_capability_call(node, tested_arguments):
                call_counts.setdefault(owner, []).append(node)
        if self.policy.configured and not self.policy.test_concurrency:
            concurrent_invocations: list[ast.Call] = []
            scheduled_invocations: list[ast.Call] = []
            for node in ast.walk(test):
                if not isinstance(node, ast.Call):
                    continue
                name = resolved_dotted_name(node.func, scoped_aliases) or ""
                nested_invocations = [
                    candidate
                    for candidate in ast.walk(node)
                    if isinstance(candidate, ast.Call)
                    and candidate is not node
                    and direct_capability_call(candidate, tested_arguments)
                ]
                if (
                    name in {"asyncio.gather", "anyio.gather"}
                    and len(nested_invocations) > 1
                ):
                    concurrent_invocations.extend(nested_invocations)
                elif nested_invocations and (
                    name in {"asyncio.create_task", "asyncio.ensure_future"}
                    or name.rsplit(".", 1)[-1] == "create_task"
                ):
                    scheduled_invocations.extend(nested_invocations)
                elif name.rsplit(".", 1)[-1] == "start_soon" and node.args:
                    target = dotted_name(node.args[0]) or ""
                    target_owner, separator, target_leaf = target.partition(".")
                    if (
                        separator
                        and target_owner in tested_arguments
                        and is_stimulus_method(target_leaf)
                    ):
                        scheduled_invocations.append(node)
            violation = concurrent_invocations or (
                scheduled_invocations if len(scheduled_invocations) > 1 else []
            )
            if violation:
                self.add(
                    "ERROR",
                    "CONC001",
                    path,
                    violation[0].lineno,
                    "concurrent application invocations contradict active "
                    "test_concurrency = false",
                )
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

    def audit_cross_component_private_access(
        self,
        path: Path,
        tree: ast.Module,
    ) -> None:
        public_support_classes = (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and not node.name.startswith(("_", "Test"))
        )
        for class_node in public_support_classes:
            for method in class_node.body:
                if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if method.name.startswith("__") and method.name.endswith("__"):
                    continue
                for node in ast.walk(method):
                    if not isinstance(node, ast.Call) or not isinstance(
                        node.func, ast.Attribute
                    ):
                        continue
                    if not node.func.attr.startswith("_") or node.func.attr.startswith(
                        "__"
                    ):
                        continue
                    owner = node.func.value
                    if isinstance(owner, ast.Name) and owner.id in {"self", "cls"}:
                        continue
                    self.add(
                        "ERROR",
                        "ENC001",
                        path,
                        node.lineno,
                        "public support component calls a collaborator's private "
                        "member; expose a truthful narrow public capability on the "
                        "owner or move the cohesive operation to an aggregate owner",
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

    def audit_temporal_matchers(
        self,
        path: Path,
        tree: ast.Module,
        aliases: dict[str, str],
    ) -> None:
        lower_bounds = {"after", "gt", "gte", "min", "minimum", "start"}
        upper_bounds = {"before", "end", "lt", "lte", "max", "maximum"}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = resolved_dotted_name(node.func, aliases) or ""
            leaf = name.rsplit(".", 1)[-1].lower()
            if leaf not in {"anydatetime", "anyinstant", "anytimestamp"}:
                continue
            keywords = {keyword.arg for keyword in node.keywords if keyword.arg}
            if keywords & lower_bounds and keywords & upper_bounds:
                continue
            self.add(
                "ERROR",
                "TIME002",
                path,
                node.lineno,
                "expected-side timestamp matcher needs explicit lower and upper "
                "invocation bounds; a type-only timestamp does not protect when the "
                "application produced it",
            )

    def audit_production_settings_oracles(
        self,
        path: Path,
        functions: Sequence[ast.FunctionDef | ast.AsyncFunctionDef],
        fixtures: Sequence[ast.FunctionDef | ast.AsyncFunctionDef],
        tests: Sequence[TestNode],
        aliases: dict[str, str],
    ) -> None:
        test_ids = {id(test.node) for test in tests}
        fixture_ids = {id(fixture) for fixture in fixtures}
        all_functions = list(functions)
        known_ids = {id(function) for function in all_functions}
        for function in (*fixtures, *(test.node for test in tests)):
            if id(function) not in known_ids:
                all_functions.append(function)
                known_ids.add(id(function))
        for function in all_functions:
            settings_names = production_settings_arguments(
                function,
                aliases,
                self.tests_dir.name,
            )
            if not settings_names:
                continue
            tainted = tainted_names(function, settings_names)
            if id(function) in test_ids:
                leaking_assert = next(
                    (
                        candidate
                        for candidate in ast.walk(function)
                        if isinstance(candidate, ast.Assert)
                        and uses_any_name(candidate.test, tainted)
                    ),
                    None,
                )
                if leaking_assert is not None:
                    self.add(
                        "ERROR",
                        "ORC001",
                        path,
                        leaking_assert.lineno,
                        "expected assertion is derived from production Settings/config; "
                        "bind the configured input and independent expected truth in "
                        "test-owned parametrization/context",
                    )
                continue
            if id(function) in fixture_ids or function.name.startswith("_"):
                continue
            oracle_module = path.name in {
                "events.py",
                "frames.py",
                "responses.py",
                "urls.py",
            }
            oracle_callable = function.name.startswith("expected_") or (
                oracle_module
                and function.name.endswith(
                    ("_body", "_event", "_frame", "_headers", "_response")
                )
            )
            if not (oracle_module or oracle_callable):
                continue
            leaking_return = next(
                (
                    candidate
                    for candidate in ast.walk(function)
                    if isinstance(candidate, (ast.Return, ast.Yield))
                    and candidate.value is not None
                    and uses_any_name(candidate.value, tainted)
                ),
                None,
            )
            if leaking_return is not None:
                self.add(
                    "ERROR",
                    "ORC001",
                    path,
                    leaking_return.lineno,
                    "expected builder is derived from production Settings/config; "
                    "construct its oracle from independent test-owned values",
                )

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
        monitored_backend_modules = set(backend_modules.values()) | {
            selected_backend_module
        }
        relative_parts = path.relative_to(self.tests_dir).parts
        source_owner = source_test_owner(path, self.tests_dir)
        generator_facade = path.name in {"fake.py", "generators.py"} or any(
            part in {"data_generation", "factories", "fake", "generators"}
            for part in relative_parts[:-1]
        )
        for node in ast.walk(tree):
            modules: list[str] = []
            line = getattr(node, "lineno", 1)
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = imported_modules(node, source_owner)
            if isinstance(node, ast.ImportFrom):
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
            dependency_modules = list(modules)
            if isinstance(node, ast.ImportFrom) and node.module is not None and modules:
                dependency_modules.extend(
                    f"{modules[0]}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )
            dependency_violations = [
                module
                for module in sorted(
                    set(dependency_modules),
                    key=lambda item: (item.count("."), item),
                )
                if imports_narrow_test_group(
                    source_owner,
                    module,
                    self.tests_dir.name,
                )
            ]
            if dependency_violations:
                module = dependency_violations[0]
                self.add(
                    "ERROR",
                    "DEP001",
                    path,
                    line,
                    f"broader or sibling test support imports narrower group "
                    f"{module!r}; move composition to the narrowest owning "
                    "group or promote only the shared mechanism",
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
                    self.add(
                        "ERROR", "TIME001", path, line, "time freezing is forbidden"
                    )
                if module in {"mock", "unittest.mock", "pytest_mock"}:
                    self.add(
                        "WARNING",
                        "MOCK002",
                        path,
                        line,
                        "generic mock tooling requires manual application-source "
                        "boundary review; prefer a typed performance double/Service",
                    )
                if root_module in monitored_backend_modules:
                    if (
                        self.policy.configured
                        and root_module != selected_backend_module
                    ):
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
                            if self.policy.configured
                            and self.policy.layout == "standard"
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
                    if not internal_role:
                        self.add(
                            "MANUAL",
                            "ENV001",
                            path,
                            line,
                            "classify generic Testcontainers usage as internal "
                            "infrastructure or an external mock server and confirm "
                            "the matching project policy",
                        )
                        continue
                    if self.policy.infrastructure == "testcontainers":
                        continue
                    severity = "ERROR" if self.policy.configured else "WARNING"
                    message = (
                        "internal Testcontainers usage contradicts active "
                        "infrastructure policy"
                        if self.policy.configured
                        else "confirm Testcontainers as the internal infrastructure provider"
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

    def audit_calls(
        self,
        path: Path,
        tree: ast.Module,
        aliases: dict[str, str],
    ) -> None:
        call_names = resolved_call_names(tree)
        forbidden_calls = {
            "time.sleep": ("WAIT001", "sleep is forbidden"),
            "asyncio.sleep": ("WAIT001", "sleep is forbidden"),
            "anyio.sleep": ("WAIT001", "sleep is forbidden"),
            "trio.sleep": ("WAIT001", "sleep is forbidden"),
            "asyncio.run": ("LOOP001", "manual event-loop driving is forbidden"),
            "asyncio.Runner": ("LOOP001", "manual event-loop creation is forbidden"),
            "asyncio.new_event_loop": ("LOOP001", "multiple event loops are forbidden"),
            "asyncio.set_event_loop": (
                "LOOP001",
                "manual event-loop setup is forbidden",
            ),
        }
        forbidden_leaf_calls = {
            "run_until_complete": (
                "LOOP002",
                "manual event-loop driving is forbidden",
            ),
            "freeze_time": ("TIME001", "time freezing is forbidden"),
        }
        forbidden_session_calls = {
            "sqlalchemy.ext.asyncio.AsyncSession",
            "sqlalchemy.ext.asyncio.async_sessionmaker",
            "sqlalchemy.orm.Session",
            "sqlalchemy.orm.sessionmaker",
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = call_names.get(id(node), "")
            leaf = name.rsplit(".", 1)[-1]
            violation = forbidden_calls.get(name) or forbidden_leaf_calls.get(leaf)
            if violation:
                code, message = violation
                self.add("ERROR", code, path, node.lineno, message)
            if name in forbidden_session_calls:
                self.add(
                    "ERROR",
                    "DB001",
                    path,
                    node.lineno,
                    "SQLAlchemy session APIs are forbidden in test support",
                )
            if leaf == "wait_for" and "messaging" in path.parts:
                self.add(
                    "ERROR",
                    "WAIT002",
                    path,
                    node.lineno,
                    "messaging must use deterministic completion and no-wait collection",
                )
            if leaf == "get" and "messaging" in path.parts:
                fail = next(
                    (
                        keyword.value
                        for keyword in node.keywords
                        if keyword.arg == "fail"
                    ),
                    None,
                )
                timeout = next(
                    (
                        keyword.value
                        for keyword in node.keywords
                        if keyword.arg == "timeout"
                    ),
                    None,
                )
                no_wait = isinstance(timeout, ast.Constant) and timeout.value == 0
                if (
                    isinstance(fail, ast.Constant)
                    and fail.value is False
                    and not no_wait
                ):
                    self.add(
                        "ERROR",
                        "WAIT003",
                        path,
                        node.lineno,
                        "messaging get(fail=False) still inherits a positive library "
                        "timeout; pass timeout=0 for a real no-wait drain",
                    )
            if name in {
                "patch",
                "mock.patch",
                "unittest.mock.patch",
            } or name.startswith(("monkeypatch.", "mocker.patch")):
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
                if (
                    "docker compose" in joined
                    and self.policy.compose_lifecycle == "disabled"
                ):
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
                    (
                        keyword.value
                        for keyword in node.keywords
                        if keyword.arg == "deep"
                    ),
                    None,
                )
                if not (isinstance(deep, ast.Constant) and deep.value is True):
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
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
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
        allowed_ids = {id(test.node) for test in tests} | {
            id(node) for node in fixtures
        }
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
        aliases: dict[str, str],
    ) -> None:
        parametrized_names: set[str] = set()
        validation_expected_status = False
        validation_no_error_sentinel = False
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
            parameter_names = self.parametrize_names(decorator.args[0])
            parametrized_names.update(parameter_names)
            rows = decorator.args[1]
            if path.name == "test_validation.py":
                validation_expected_status = validation_expected_status or any(
                    parameter_name.lower().startswith("expected")
                    and "status" in parameter_name.lower()
                    for parameter_name in parameter_names
                )
                error_indexes = {
                    index
                    for index, parameter_name in enumerate(parameter_names)
                    if "error" in parameter_name.lower()
                }
                if error_indexes and isinstance(rows, (ast.List, ast.Tuple)):
                    validation_no_error_sentinel = validation_no_error_sentinel or any(
                        index < len(values) and self.is_none_sentinel(values[index])
                        for row in rows.elts
                        for values in (self.parametrize_row_values(row),)
                        for index in error_indexes
                    )
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
            fresh = FreshValueVisitor(aliases)
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
        if path.name == "test_validation.py" and (
            validation_expected_status or validation_no_error_sentinel
        ):
            self.add(
                "ERROR",
                "VAL001",
                path,
                test.lineno,
                "validation acceptance and rejection use separate homogeneous "
                "parametrizations; assert the fixed status directly and do not use "
                "a nullable/no-error parameter sentinel",
            )
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
    def parametrize_names(node: ast.AST) -> tuple[str, ...]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return tuple(part.strip() for part in node.value.split(",") if part.strip())
        if isinstance(node, (ast.List, ast.Tuple)):
            return tuple(
                element.value
                for element in node.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            )
        return ()

    @staticmethod
    def parametrize_row_values(row: ast.AST) -> tuple[ast.AST, ...]:
        if isinstance(row, ast.Call) and dotted_name(row.func) == "pytest.param":
            return tuple(row.args)
        if isinstance(row, (ast.List, ast.Tuple)):
            return tuple(row.elts)
        return (row,)

    @staticmethod
    def is_none_sentinel(node: ast.AST) -> bool:
        if isinstance(node, ast.Constant):
            return node.value is None
        return (
            isinstance(node, ast.Lambda)
            and isinstance(node.body, ast.Constant)
            and node.body.value is None
        )

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
                message = (
                    "public fixture is not requested by a test; verify or privatize it"
                )
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
