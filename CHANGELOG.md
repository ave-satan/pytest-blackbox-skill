# Changelog

All notable Pytest Blackbox changes are documented here. Release entries keep
existing-project actions explicit and idempotent so the `upgrade` workflow can
apply only relevant migrations without rerunning a full suite audit.

## [Unreleased]

No changes yet.

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

[Unreleased]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.1.0...v0.1.2
[0.1.0]: https://github.com/ave-satan/pytest-blackbox-skill/releases/tag/v0.1.0
