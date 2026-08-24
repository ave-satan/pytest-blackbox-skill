---
name: discover
description: Onboard or refresh pytest-blackbox policy for a Python project. Use when project configuration is missing, the user asks to connect pytest-blackbox, or project-wide testing choices need rediscovery. Do not use for ordinary test writing, repair, review, or audit in an already configured project.
---

# Discover Pytest Blackbox

Read the complete [shared policy](../../core/POLICY.md) before acting, then follow its **Project onboarding** section and [configuration reference](../../references/configuration.md).

Keep discovery read-only. Run `../../scripts/discover_project.py <project-root>`, inspect its evidence, and ask only about material ambiguous project-wide choices. Number questions sequentially. Never write configuration until the user confirms the exact proposed `pyproject.toml` patch.

If discovery was entered automatically from another workflow because configuration is absent, finish onboarding before returning to that requested workflow.
