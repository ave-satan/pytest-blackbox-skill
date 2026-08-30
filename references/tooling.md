# Analysis tooling

Pytest Blackbox exposes two checks and one discovery command:

- `scripts/lint_suite.py`: mechanically provable diagnostics only;
- `scripts/audit_suite.py`: the same diagnostics plus manual semantic review, including all applicable `SEM*` items;
- `scripts/discover_project.py`: read-only onboarding evidence and policy proposal.

All commands accept `--mode auto|fallback|enhanced`. `auto` is the normal mode. `fallback` never installs anything and uses only the standard library on Python 3.11+ (`tomli` is required on Python 3.10). `enhanced` requires the project to have opted in through `dependency_group` and uses the baseline toolchain. `--output-format concise|json` is available for lint and audit.

## Baseline enhanced toolchain

Install these requirements together in the confirmed dedicated group:

```text
ruff>=0.16,<0.17
packaging>=24
pathspec>=0.12
tomlkit>=0.13
tomli>=2; python_version < '3.11'
```

Use the project-native command. Examples for a group named `dev-ai`:

```bash
uv add --group dev-ai 'ruff>=0.16,<0.17' 'packaging>=24' 'pathspec>=0.12' 'tomlkit>=0.13' 'tomli>=2; python_version < "3.11"'
poetry add --group dev-ai 'ruff>=0.16,<0.17' 'packaging>=24' 'pathspec>=0.12' 'tomlkit>=0.13' 'tomli>=2; python_version < "3.11"'
pdm add --group dev-ai 'ruff>=0.16,<0.17' 'packaging>=24' 'pathspec>=0.12' 'tomlkit>=0.13' 'tomli>=2; python_version < "3.11"'
```

Show the exact command before running it. Treat compatible requirements already declared anywhere in the project as satisfied; do not duplicate or move them. If the package manager cannot represent a named group, report that limitation instead of using runtime or general development dependencies.

Run enhanced commands with the project's managed interpreter so the confirmed
group is importable. For example, use `uv run --group dev-ai python ...`,
`poetry run python ...`, or `pdm run python ...` as appropriate; invoking an
unrelated system interpreter must not silently downgrade an installed toolchain
to fallback.

## Enhanced audit

Ruff owns only compatible first-party syntax and pytest rules plus explicit banned APIs. The allowlist intentionally excludes rules that contradict Pytest Blackbox. In particular, do not enable `PT003`: explicit `scope="function"` is required for the transaction fixture even though generic pytest style considers it redundant. Project-specific and cross-file rules remain in the PBB checker because Ruff has no third-party rule API.

The enhanced runner invokes Ruff through its supported CLI and parses Ruff JSON. It does not patch Ruff, use internal Rust crates, or replace the project's ordinary Ruff configuration. The project's own `ruff check` remains a separate normal project check.

Pytest Blackbox keeps deterministic cross-file/fixture rules in its own Ruff-like checker. In particular:

- `DEP001` rejects an import from broad or sibling test support into a narrower `test_*` group;
- `FIX005` rejects direct repository state mutation inside a public capability fixture such as a client, transport, worker, runner, publisher, collector, scheduler, or job fixture. Baseline creation moves to a private cohesive context; special transitions stay visible in test arrange.

These diagnostics intentionally prove only the visible structural violation. They do not replace semantic review of protocol type minimality, fixture naming, or whether an apparently baseline state is actually scenario-specific.

## Semantic review

Manual findings never appear in `lint_suite.py`. They remain in the `Semantic review required` section of `audit_suite.py`. `SEM001` always requires the complete operation/evidence matrix; `SEM006` always requires a separate semantic scenario/outcome completeness pass over authoritative requirements and application-owned source behavior. `SEM002` follows focused registry selections; `SEM003` and `SEM004` follow scheduler and worker surfaces; `SEM005` follows detected WebSocket test support/surfaces and includes current-contract-only outcome projections plus Transport/Connection/Client ownership; `SEM007` appears only when `test_concurrency = true`. A clean deterministic section does not satisfy these items or prove coverage completeness.

Neither bundled check imports project code, collects pytest, executes tests, or runs the project's own lint/type commands. The `audit` workflow invokes those separately when the environment and audit scope allow them; their results are evidence reconciled alongside, not hidden inside, `audit_suite.py`.

The deterministic checker does not warn merely because a validation matrix with explicit boundaries lacks a randomized ordinary row: deciding whether the field is enum-only requires contract knowledge. Enum matrices intentionally use every allowed member instead. The semantic contract review remains responsible for distinguishing enums from incomplete non-enum matrices.

## Enhanced discovery

First onboarding can always run fallback discovery. After opt-in and installation, auto mode uses Packaging for requirement parsing, PathSpec for gitignore-aware evidence, and TOMLKit for project metadata. Enhanced discovery preserves the same read-only boundary: it does not import project code, start infrastructure, execute project commands, or mutate files.
