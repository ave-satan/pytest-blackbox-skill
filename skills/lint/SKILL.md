---
name: lint
description: Run deterministic, machine-checkable pytest-blackbox policy diagnostics without claiming semantic coverage completeness. Use when the user asks for a fast static policy check or lint pass. Do not use as a substitute for a full semantic audit.
---

# Lint Pytest Blackbox Tests

Read the complete [shared policy](../../core/POLICY.md) and
[tooling reference](../../references/tooling.md) before acting. Run
`../../scripts/lint_suite.py <project-root>` in auto mode unless the user
explicitly requests fallback or enhanced mode.

When the user names files or one component, pass each owning test path through
`--scope`; omit scope only for an explicitly project-wide lint pass. The checker
still indexes the complete suite for cross-file evidence.

Report the selected mode and every error or warning. This workflow covers only
mechanically provable rules: it does not emit `SEM*` findings, inventory public
contracts, or establish suite completeness. If the requested conclusion needs
any of those, use the `audit` workflow instead.
