---
name: discover
description: Onboard or refresh pytest-blackbox policy for a Python project. Use when project configuration is missing, the user asks to connect pytest-blackbox, or project-wide testing choices need rediscovery. Do not use for ordinary test writing, repair, review, or audit in an already configured project.
---

# Discover Pytest Blackbox

Read the complete [shared policy](../../core/POLICY.md) before acting, then follow its **Project onboarding** section and [configuration reference](../../references/configuration.md).

Keep the scan and proposal phase read-only. Run `../../scripts/discover_project.py <project-root>`, inspect its evidence, and ask only about material ambiguous project-wide choices. During first onboarding, explicitly confirm whether authoritative concurrency guarantees belong to the suite; recommend and record `test_concurrency = false` unless the user selects the D override. During refresh, preserve an existing valid concurrency choice and ask again only when the key is absent or new evidence contradicts it. If the recorded policy is invalid, discovery fails closed and withholds a replacement proposal: show a separate exact minimal repair patch for only the invalid keys/rules, apply it only after confirmation, then rerun the read-only scan without substituting defaults for unrelated valid choices. Also ask whether pytest-blackbox may install its baseline enhanced toolchain in the proposed dedicated group (default `dev-ai`); this O capability is never inferred. Number questions sequentially. Omit `dependency_group` when declined. Only after the user confirms the exact proposed `pyproject.toml` patch may the onboarding mutation phase write it. Then follow [tooling.md](../../references/tooling.md): use the project-native package manager to install the baseline only when opted in, and rerun discovery in auto mode. Otherwise retain the bundled fallback without a managed install.

If discovery was entered automatically from another workflow because configuration is absent, finish onboarding before returning to that requested workflow.
