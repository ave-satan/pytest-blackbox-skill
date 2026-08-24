# Project policy and onboarding

## Contents

- [Policy levels](#policy-levels)
- [Configuration](#configuration)
- [Managed skill dependencies](#managed-skill-dependencies-o)
- [Coverage registry](#coverage-registry)
- [Read-only discovery](#read-only-discovery)
- [Enforcement and drift](#enforcement-and-drift)
- [Mature suites and monorepos](#mature-suites-and-monorepos)

## Policy levels

`pytest-blackbox` separates universal correctness constraints from project architecture:

- **M** is invariant. A project cannot configure it away.
- **D** has a recommended default but may be replaced by one coherent project-wide choice during onboarding.
- **O** is inactive until selected.

A D recommendation is advisory while unselected. Once a project records a D architecture choice, that choice is required locally; mechanically detectable disagreement is configuration drift, not an ignorable style warning.

## Configuration

Store confirmed choices in the nearest applicable `pyproject.toml`. Do not create `.pytest-blackbox.*`, a skill-local project file, or environment-variable-only policy.

Recommended new-project defaults:

```toml
[tool.pytest-blackbox]
config_version = 1
layout = "standard"
prefer_test_classes = true
infrastructure = "existing-services"
compose_lifecycle = "disabled"
external_services = "intercept"
generators_backend = "faker"
```

Meaning:

- `layout`: `standard` uses the predefined functional/area/operation hierarchy and category filenames; `preserve` adapts to a coherent mature layout.
- `prefer_test_classes`: recommend TestClass grouping when several complete cases can reuse expensive preparation safely. It never permits splitting one case across methods.
- `infrastructure`: `existing-services`, `embedded`, or an established project-owned provider such as explicitly selected `testcontainers`. Every choice must remain protocol-compatible and create isolated logical resources. This choice provisions internal dependencies and is independent from external mock servers.
- `compose_lifecycle`: `disabled` by default; `enabled` preserves a consciously selected project-owned Compose lifecycle. This setting concerns Compose only and does not block Testcontainers.
- `external_services`: `intercept` by default; `testcontainers` uses containerized external mock servers; `mixed` assigns either backend to different external integrations when one backend is not suitable for all of them. Every mode exposes the same test-owned domain Service interface and is independent from the internal-infrastructure provider. In `mixed` mode the assignment is stable per domain integration across the suite, never selected per test case.
- `generators_backend`: `faker` by default or another confirmed generated-data backend hidden behind the project facade.

Do not configure invariant behavior such as black-box boundaries, one tested invocation, no sleeping, real time bounds, in-process HTTP, transaction rollback, or fixture privacy. Do not configure individual fixture names, support module names, category filename aliases, operation-specific exceptions, or a per-Service backend map. Mixed external-service routing belongs to coherent fixture composition and stays stable per external integration.

The generator facade defaults to `tests.generators`. Preserve a mature project's coherent existing facade instead of adding a configuration key just to rename it.

## Managed skill dependencies (O)

During onboarding, always ask once whether pytest-blackbox may install its baseline enhanced toolchain and later add missing Python packages required by tests it authors. This capability is opt-in and cannot be inferred from existing dependencies. Record it by adding one key to the main policy table:

```toml
[tool.pytest-blackbox]
dependency_group = "dev-ai"
```

The key's presence enables the capability and names its destination; do not add a second boolean flag. For a new project, propose `dev-ai`. If a mature project already has a clearly dedicated AI/agent-tooling dependency group, show the evidence and offer to reuse it. Never silently select the general runtime, default, `dev`, test, or lint group. If the project's package manager cannot represent a separate named group, report that limitation and ask for a coherent alternative instead of falling back.

Enabling this capability installs the baseline enhanced analysis toolchain documented in [tooling.md](tooling.md): Ruff, Packaging, PathSpec, and TOMLKit. This is a fixed capability implementation, not a speculative test dependency. Use the project-native package-manager command so the group, environment, and lockfile are updated coherently; then rerun discovery in auto mode. For later workflow-specific dependencies:

1. Confirm that `dependency_group` is active and identify the owning `pyproject.toml`.
2. Treat a compatible package already declared in any project dependency section as satisfied. Do not duplicate or move it merely to normalize layout.
3. Name the exact missing packages, destination group, and project-native package-manager command before mutation.
4. Use that command so `pyproject.toml`, the environment, and any lockfile change coherently. Never edit a lockfile by hand or upgrade unrelated packages.
5. Add only development/tooling packages needed to execute pytest-blackbox helpers or the generated suite—for example a pytest plugin, data generator, HTTP interceptor, or protocol test client. The pytest-blackbox plugin itself remains installed through its host marketplace and never belongs in the project's Python dependencies.

When the key is absent, dependency management is inactive: do not modify dependency declarations or install packages. Report the concrete missing dependency and offer to enable the capability through an exact confirmed `pyproject.toml` patch. Host or sandbox approval may still be required for the eventual package-manager command even when the project policy is enabled.

## Coverage registry

Public HTTP/JSON-RPC operations and registered jobs, schedulers, and incoming-message handlers are always contract-bearing and always covered. Never add them to the registry and never request permission to omit them. A worker's registered handlers are covered this way; generic dispatch/acknowledgement/requeue/runtime mechanics are a separate non-contract surface unless intentionally selected.

The registry contains decisions only for generalized classes of non-contract or ambiguous surfaces:

```toml
[[tool.pytest-blackbox.coverage]]
selector = "health-probes"
decision = "focused"
rationale = "Operational status mapping only"

[[tool.pytest-blackbox.coverage]]
selector = "developer-debug-surfaces"
decision = "exclude"
rationale = "Not shipped in supported environments"
```

Allowed decisions are `exclude`, `focused`, and `standard`. A selector describes a surface class, namespace, visibility class, or operational role. Do not record HTTP method/path pairs, JSON-RPC method names, individual job names, or handler identifiers; that becomes per-operation micromanagement.

When discovery finds a non-contract operation:

1. Apply an existing generalized registry rule when it clearly matches.
2. If no rule matches, ask once about the new surface class and proposed depth.
3. Show the generalized registry entry before writing it.
4. Record the decision and rationale only after confirmation.

## Read-only discovery

Run `scripts/discover_project.py <project-root>` when `[tool.pytest-blackbox]` is absent or the user requests a refresh. The script inspects filenames, Python imports, dependency declarations, pytest settings, and existing test layout without importing project code. Auto mode uses the bundled fallback until the O capability is enabled and its toolchain is available; enhanced mode then adds library-backed requirement parsing, package-manager evidence, and gitignore-aware file evidence without weakening the safety boundary.

Run the bundled scripts with an interpreter new enough to parse the project's Python syntax. They use stdlib `tomllib` on Python 3.11+ and fall back to the `tomli` backport on older Python. If neither is available they stop policy parsing with a clear diagnostic rather than installing a dependency or mutating the environment. Discovery reports how many Python files its interpreter could not parse.

Discovery must not:

- read `.env`, credentials, tokens, key files, or secret-manager data;
- import or start the application;
- run migrations, Docker, Compose, Testcontainers, tests, or subprocess-backed project commands;
- connect to databases, brokers, caches, object stores, or external systems;
- modify `pyproject.toml` or any project file.

Discovery reports existing named dependency groups and proposes `dependency_group = "dev-ai"` separately from the default policy patch. The discover workflow must ask whether to enable it; include the key in the final patch only after confirmation. A declined O capability remains absent rather than being recorded as `false`.

The bundled scanner skips common secret-bearing Python filenames such as `credentials.py`, `secrets.py`, `tokens.py`, `keys.py`, and `private_keys.py`; it never prints source contents. If a project uses another sensitive naming convention, exclude that location from the scan or inspect it manually rather than broadening automated reads.

Treat output as evidence and a proposal, not authority. Show ambiguous facts and confidence. Ask only about material choices that cannot be inferred safely, then show the exact patch. Because stdlib `tomllib` is read-only, let the agent apply the confirmed minimal patch so existing formatting and comments remain intact.

If no `pyproject.toml` exists, offer either a minimal new file or temporary confirmed settings for the task. Never silently create the file.

## Enforcement and drift

Audit output has two deliberately separate sections:

- deterministic diagnostics: `ERROR` for a mechanically proven M violation or active D contradiction, and `WARNING` for a non-binding D recommendation;
- semantic review: preserved `MANUAL` items, including every applicable `SEM*` requirement, which the static tool cannot prove;
- no result for an O capability that is not enabled.

`scripts/lint_suite.py` emits only deterministic diagnostics. `scripts/audit_suite.py` emits the same diagnostics plus semantic review. Both support bundled fallback and enhanced modes and use Ruff-like `path:line:column: CODE message` output; read [tooling.md](tooling.md) for mode and dependency details.

Examples:

- `prefer_test_classes = true` plus repeated expensive preparation may produce a warning because the opportunity is heuristic.
- `external_services = "intercept"` plus confirmed Testcontainers mock-server code is configuration-drift error; `external_services = "mixed"` intentionally permits both external backends.
- A production-independent oracle remains manual review; AST similarity cannot prove semantic independence reliably.
- An absent `dependency_group` produces no dependency-management finding. A present but empty or general-purpose destination is configuration error; whether a custom group is genuinely dedicated remains manual review.

Do not promote uncertain heuristics to errors. Do not downgrade a mechanically proven invariant merely because the suite is mature.

## Mature suites and monorepos

For a mature suite, discovery and audit are read-only. Apply M rules to every new or changed test, record all known legacy violations, and do not perform a broad refactor without explicit authorization. Do not claim full suite conformance while known M violations remain.

Use the nearest `pyproject.toml` that owns the tested component. In a monorepo with several plausible owners, report the candidates and ask which one governs the work. A child component may override parent D choices, but M invariants never change.
