---
name: write
description: Design and add new black-box pytest contract tests for Python application behavior. Use when the user asks to test or add coverage for an HTTP or JSON-RPC API, job, scheduler, worker, message handler, or observable integration contract. Do not use merely to repair existing failing tests or to perform a read-only review or full audit.
---

# Write Pytest Blackbox Tests

Read the complete [shared policy](../../core/POLICY.md) before acting. If `[tool.pytest-blackbox]` is absent, perform the shared onboarding workflow before changing tests.

Inventory the requested contract surface, create the transient evidence matrix, and read only the shared references implicated by the work. Add the smallest complete set of public-boundary tests and support code, run the deterministic auditor plus focused project checks, and report the exact coverage boundary and evidence.

Do not expand a focused test request into a full-suite refactor or audit without authorization.
