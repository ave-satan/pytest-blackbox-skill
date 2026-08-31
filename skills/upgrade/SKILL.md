---
name: upgrade
description: Apply release-specific Pytest Blackbox migrations to an existing configured project after the plugin is updated. Use when the user asks what changed, requests a project migration, or wants local test tooling aligned with a newer plugin release. Do not use for ordinary test repair, new coverage, or a full audit.
---

# Upgrade an Existing Pytest Blackbox Project

Read the repository-root [changelog](../../CHANGELOG.md) and the project's
nearest `[tool.pytest-blackbox]` configuration. Determine the relevant release
interval from the user's stated previous version or reliable host metadata. If
the previous version is unknown, evaluate the changelog's idempotent conditions
against the project and ask only when that uncertainty changes an action.

Use only actions contained in released version sections inside that interval.
Ignore `[Unreleased]` completely unless the user explicitly asks to preview or
apply migrations from a source checkout; make that preview status visible and
never infer it merely because the checkout contains newer files.

Apply only matching entries under **Existing-project actions**:

- preserve each action's condition, no-op, and **Do not** boundaries;
- when a later action explicitly **Supersedes** an earlier one, apply only the
  final form and skip transient artifacts required solely by the older action;
- show exact configuration and dependency changes before mutation;
- never infer an O capability such as managed dependencies;
- treat an already-satisfied action as complete without rewriting it;
- do not record the plugin release number in project configuration unless a
  future changelog action explicitly changes the schema.

This is a targeted migration, not a fresh onboarding or full-suite audit. Run
only the discovery, lint, focused tests, or package-manager checks needed to
validate the applied actions. Report the release interval, action IDs applied,
actions skipped with reasons, changed files, and validation evidence.
