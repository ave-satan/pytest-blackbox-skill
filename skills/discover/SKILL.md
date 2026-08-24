---
name: discover
description: Onboard or refresh pytest-blackbox policy for a Python project. Use when project configuration is missing, the user asks to connect pytest-blackbox, or project-wide testing choices need rediscovery. Do not use for ordinary test writing, repair, review, or audit in an already configured project.
---

# Discover Pytest Blackbox

Read the complete [shared policy](../../core/POLICY.md) before acting, then follow its **Project onboarding** section and [configuration reference](../../references/configuration.md).

Keep discovery read-only. Run `../../scripts/discover_project.py <project-root>`, inspect its evidence, and ask only about material ambiguous project-wide choices. Also ask the explicit onboarding question whether pytest-blackbox may install its baseline enhanced toolchain in the proposed dedicated group (default `dev-ai`); this O capability is never inferred. Number questions sequentially. Omit `dependency_group` when declined. After the user confirms the exact proposed `pyproject.toml` patch, follow [tooling.md](../../references/tooling.md): use the project-native package manager to install the baseline only when opted in, then rerun discovery in auto mode. Otherwise retain the bundled fallback without a managed install.

If discovery was entered automatically from another workflow because configuration is absent, finish onboarding before returning to that requested workflow.
