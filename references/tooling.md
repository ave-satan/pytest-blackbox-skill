# Analysis tooling

Pytest Blackbox exposes two checks and one discovery command:

- `scripts/lint_suite.py`: mechanically provable diagnostics only;
- `scripts/audit_suite.py`: the same diagnostics plus every manual `SEM*` item applicable to the selected scope or complete suite;
- `scripts/discover_project.py`: read-only onboarding evidence and policy proposal.

All commands accept `--mode auto|fallback|enhanced`. `auto` is the normal mode. `fallback` never installs anything and uses only the standard library on Python 3.11+ (`tomli` is required on Python 3.10). `enhanced` requires the project to have opted in through `dependency_group` and uses the baseline toolchain. `--output-format concise|json` is available for lint and audit.

`lint_suite.py` and `audit_suite.py` accept repeatable `--scope <tests-path>` arguments. A scoped run indexes the complete suite so cross-file fixture/import analysis still works, but reports diagnostics at selected files/directories and emits semantic items only for intersecting contract surfaces. Include the complete owning component plus every changed shared-support path; add another component only when it is intentionally in task scope. Use paths relative to the project root or absolute paths inside its `tests/` directory. An invalid, missing, outside-project, non-Python file, or directory without Python modules fails closed. Omitting `--scope` keeps the complete-suite behavior.

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
- `ENC001` rejects a public support class method calling a collaborator's private member, whether that collaborator is stored on `self` or received locally; calls to the class's own private methods and private implementation classes remain allowed. Other ownership shapes stay under `SEM011` rather than becoming heuristic errors;
- `FIX005` rejects direct repository state mutation inside a public capability fixture such as a client, transport, worker, runner, publisher, collector, scheduler, or job fixture. Baseline creation moves to a private cohesive context; special transitions stay visible in test arrange.
- `STR007` rejects a collected `test_topology.py`: production messaging topology belongs to private session bootstrap, not the test surface.
- `WS001` rejects an empty WebSocket connection context in a collected test; accepted/denied/close lifecycle must be a natural value asserted through the test-owned adapter.

These diagnostics intentionally prove only the visible structural violation. They do not replace semantic review of protocol type minimality, fixture naming, or whether an apparently baseline state is actually scenario-specific.

## Semantic review

Manual findings never appear in `lint_suite.py`. They remain in the `Semantic review required` section of `audit_suite.py`. Without scope, `SEM001` requires the complete operation/evidence matrix from final framework registrations and actions plus bottom-up reconciliation of the final case set against category and terminal-component names; `SEM006` requires a separate complete-suite scenario/outcome pass. With scope, both apply only to the selected public operations/components, and conditional scheduler/worker/WebSocket items appear only when their surface intersects the selected paths. The agent still derives semantic truth from authoritative requirements and registration/source evidence—the path filter does not prove completeness by itself. `SEM010` reviews native-first assertions, explicitly named partial matchers, and the narrow ordered scalar-projection exception without binding policy to one implementation. `SEM011` reviews shortest truthful owner-relative names, canonical operations, typed domain results, and support ownership boundaries across public domain-facing test support while allowing precisely named generic structural/protocol primitives. If the tests root is absent or cannot be inspected, the runner reports that structural blocker instead of pretending to emit a complete semantic checklist. Complete-suite `SEM002` follows focused registry selections; scoped workflows instead reconcile the selected operation against its applicable registry decision explicitly. `SEM003` follows schedulers; `SEM004` covers mandatory handler contracts independently from shared worker runtime; conditional `SEM008` covers selected shared runtime/settlement behavior; `SEM009` verifies that broker topology is a private session-bootstrap invariant rather than a collected test surface and has no inverse-topology teardown. `SEM005` follows detected WebSocket test support/surfaces and includes current-contract-only outcome projections plus Transport/Connection/Client ownership; `SEM007` appears only when `test_concurrency = true`. A clean deterministic section does not satisfy these items or prove coverage completeness. Test-first chronology is execution evidence owned by the `develop` workflow and is intentionally not inferred from the final tree.

Neither bundled check imports project code, collects pytest, executes tests, or runs the project's own lint/type commands. The `audit` workflow invokes those separately when the environment and audit scope allow them; their results are evidence reconciled alongside, not hidden inside, `audit_suite.py`.

The deterministic checker does not warn merely because a validation matrix with explicit boundaries lacks a randomized ordinary row: deciding whether the field is enum-only requires contract knowledge. Enum matrices intentionally use every allowed member instead. The semantic contract review remains responsible for distinguishing enums from incomplete non-enum matrices.

## Enhanced discovery

First onboarding can always run fallback discovery. After opt-in and installation, auto mode uses Packaging for requirement parsing, PathSpec for gitignore-aware evidence, and TOMLKit for project metadata. Enhanced discovery preserves the same read-only boundary: it does not import project code, start infrastructure, execute project commands, or mutate files. Discovery fails closed and withholds its policy proposal when the active interpreter cannot parse any scanned Python file; rerun it through the project's compatible managed interpreter.
