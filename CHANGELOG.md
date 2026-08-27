# Changelog

All notable Pytest Blackbox changes are documented here. Release entries keep
existing-project actions explicit and idempotent so the `upgrade` workflow can
apply only relevant migrations without rerunning a full suite audit.

## [Unreleased]

No changes yet.

## [0.3.0] - 2026-08-28

### Added

- First-class WebSocket contract guidance: route-level handshake/lifecycle,
  independently invokable message discriminators, required continuation and
  close outcomes, natural typed handshake results, and deterministic in-process
  task/event completion.
- Behavior-derived category naming: `test_business_logic.py` is reserved for
  actual business behavior, while other cohesive contract aspects use precise
  names. `test_connection.py` is the recommended WebSocket route example.
- `SEM005` manual audit reconciliation for detected WebSocket surfaces.
- `WS001` deterministic diagnostics for expected handshake denials expressed as
  `pytest.raises` around an empty accepted-session context.

### Changed

- Documentation-only endpoints and generated OpenAPI/Swagger/schema artifacts
  are explicitly outside the product contract suite.
- Removed `VAL002`. A test-only AST cannot reliably distinguish an enum-only
  matrix from an incomplete non-enum matrix; semantic review owns that decision,
  while enums intentionally test every allowed member without a randomized row.
- Expanded `STR003` from `test_success.py` to other vague standard-layout
  categories such as `test_happy_path.py`, `test_behavior.py`, and
  `test_technical.py`; the diagnostic asks for the public behavior instead.
- Shared-support dependency direction now covers hardcoded route,
  discriminator, topology, and expected literals in addition to imports.
- Prepared typed contexts retain stable identifiers needed by later arrange
  steps, and state helpers belong to the repository owning the mutated state.

### Existing-project actions

These actions are conditional and idempotent. They migrate existing projects
to `0.3.0`; the configuration schema remains at `config_version = 1`.

#### PBB-MIG-0.3.0-01 — WebSocket operation matrix

- **Condition:** the project has a functional WebSocket surface.
- **Action:** inventory the route handshake/lifecycle separately from every
  independently invokable client-message discriminator. Give each identity an
  unambiguous terminal component, and add only currently required denial,
  frame, close, continuation, and direct artifact outcomes.
- **Do not:** derive requirements from Swagger/OpenAPI prose, mirror internal
  exception branches, add sleeps/timeouts, or test future documented behavior
  that is not yet a functional requirement.
- **No-op when:** the project has no WebSocket surface or its existing matrix
  already satisfies these boundaries.

#### PBB-MIG-0.3.0-02 — Natural handshake outcomes

- **Condition:** an expected WebSocket handshake denial is asserted through a
  custom/third-party exception and an empty `async with ...: pass` block.
- **Action:** normalize the documented denial in the test-owned client to an
  immutable typed result and compare it directly. Keep an accepted-session
  context manager for post-upgrade tests. When awaiting wire output, race it
  against completion of the application/runner task and propagate the original
  task exception if it finishes first.
- **Do not:** convert unexpected application/support failures to values,
  swallow tracebacks, add a wall-clock timeout, or open a localhost socket.
- **No-op when:** denial is already a natural value and the harness already
  observes both protocol output and task completion.

#### PBB-MIG-0.3.0-03 — Shared transport and prepared-state ownership

- **Condition:** shared support hardcodes a child route/discriminator/topology
  literal, or a repository scans storage to recover a known identifier and then
  mutates state owned by another repository.
- **Action:** make generic transports accept component-owned values explicitly;
  put defaults in the narrow functional adapter. Preserve required identifiers
  in the original typed preparation context and pass them to the repository
  that owns the next mutation.
- **Do not:** promote component literals to root constants, rediscover known
  state through storage, or create a generic catch-all repository.
- **No-op when:** dependency direction and state ownership are already clean.

#### PBB-MIG-0.3.0-04 — Documentation-only tests

- **Condition:** the product contract suite contains tests whose sole subject is
  a documentation/schema-only endpoint or generated OpenAPI/Swagger output.
- **Action:** remove those tests and their terminal component from the product
  contract matrix.
- **Do not:** remove the documentation itself or omit a functional endpoint
  merely because it is also documented.
- **No-op when:** the suite contains no documentation-only contract tests.

#### PBB-MIG-0.3.0-05 — Newly discovered runtime surface classes

- **Condition:** the change discovers an unclassified non-contract runtime
  surface such as observability bootstrap and no generalized coverage rule
  applies.
- **Action:** ask once for `exclude`, `focused`, or `standard` depth and record a
  generalized selector/rationale only after confirmation.
- **Do not:** create per-function or per-operation registry entries, infer a
  decision from installed dependencies, or unit-test an SDK by default.
- **No-op when:** an existing generalized rule already covers the surface.

#### PBB-MIG-0.3.0-06 — Behavior-derived category names

- **Condition:** `test_business_logic.py` contains a non-business contract
  aspect, or another category has a generic success/technical name that hides
  what it proves.
- **Action:** choose a concise filename for the cohesive public behavior. Keep
  `test_business_logic.py` only for business rules/domain outcomes; prefer
  `test_connection.py` for a route-level WebSocket contract, while command
  components choose names from their own behavior.
- **Do not:** create a file per case/parameter/outcome, invent synonyms for
  established access/validation/error/metrics categories, or create empty
  category files.
- **No-op when:** filenames already describe their behavior unambiguously, or a
  deliberately preserved mature layout has a clear equivalent.

## [0.2.0] - 2026-08-24

### Added

- A dedicated `lint` workflow for deterministic policy diagnostics without a
  semantic completeness claim.
- Ruff-like concise output and stable JSON output for `lint_suite.py` and
  `audit_suite.py`.
- `auto`, `fallback`, and `enhanced` analysis modes for discovery, lint, and
  audit.
- An opt-in enhanced toolchain using Ruff, Packaging, PathSpec, TOMLKit, and a
  conditional TOMLI compatibility dependency on Python 3.10.
- Explicit `SEM001` through `SEM004` semantic review items in the audit layer.

### Changed

- `audit_suite.py` now composes deterministic diagnostics with a separate
  semantic-review section; `SEM*` checks were preserved rather than converted
  into static rules.
- Compatible syntax, pytest, banned-time, event-loop, and SQLAlchemy Session
  rules are delegated to Ruff in enhanced mode. Cross-file and
  project-specific rules remain in the bundled checker.
- Discovery remains read-only but gains library-backed dependency parsing,
  package-manager evidence, and gitignore-aware evidence in enhanced mode.
- Managed analysis dependencies are installed only after explicit onboarding
  consent and only in the configured dedicated dependency group.

### Existing-project actions

These actions are deliberately conditional. Reapplying them to an already
updated project must be a no-op.

#### PBB-MIG-0.2.0-01 — Optional enhanced analysis

- **Condition:** the user explicitly opts in to managed Pytest Blackbox
  dependencies.
- **Action:** add `dependency_group = "dev-ai"` (or a confirmed existing
  dedicated AI/tooling group) under `[tool.pytest-blackbox]`, then install the
  exact baseline from `references/tooling.md` with the project-native package
  manager.
- **Do not:** infer consent from existing tools, duplicate compatible packages
  already declared elsewhere, or modify runtime/general development groups.
- **No-op when:** `dependency_group` is absent because the user declined or has
  not decided; fallback remains supported.

#### PBB-MIG-0.2.0-02 — Auditor output consumers

- **Condition:** project automation parses the pre-0.2 human-readable auditor
  output.
- **Action:** switch machine consumers to `--output-format json`, whose root
  fields are `mode`, `diagnostics`, `semantic`, and `summary`.
- **Do not:** parse the new concise human format when structured output is
  available.
- **No-op when:** the auditor is invoked only by a person or coding agent.

#### PBB-MIG-0.2.0-03 — Deterministic-only checks

- **Condition:** an existing local workflow needs fast mechanical policy
  diagnostics and must not claim contract coverage completeness.
- **Action:** call `lint_suite.py`; keep `audit_suite.py` wherever `SEM*`
  reconciliation or full semantic coverage is required.
- **Do not:** replace a semantic audit with lint.
- **No-op when:** existing automation intentionally runs the full audit.

No production or test-source refactor is required solely to upgrade to 0.2.0.
The project configuration schema remains at `config_version = 1`.

## [0.1.2] - 2026-08-23

### Changed

- Pinned the Codex and Claude Code marketplace catalogs to the immutable
  `v0.1.2` release tag.
- Documented GitHub-only installation and update commands.

### Existing-project actions

No project-file migration was required.

## [0.1.0] - 2026-08-23

### Added

- Initial Codex and Claude Code plugin packaging for the `discover`, `write`,
  `repair`, `review`, and `audit` workflows.
- The shared black-box pytest policy, project onboarding, fallback discovery,
  and deterministic auditor.

[Unreleased]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.1.0...v0.1.2
[0.1.0]: https://github.com/ave-satan/pytest-blackbox-skill/releases/tag/v0.1.0
