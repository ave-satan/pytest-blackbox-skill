---
name: repair
description: Repair failing, flaky, invalid, or poorly composed black-box pytest tests and their test-support code. Use when an existing contract test suite is broken or nondeterministic. Do not use to add unrelated coverage, change production behavior, or perform a read-only review or full audit.
---

# Repair Pytest Blackbox Tests

Read the complete [shared policy](../../core/POLICY.md) before acting. If `[tool.pytest-blackbox]` is absent, perform the shared onboarding workflow before changing tests.

Reproduce the smallest relevant failure and classify it before editing: application defect, contract mistake, test-support/environment failure, leaked state, or nondeterminism. Repair only test and test-support behavior within the user's scope. If the evidence points to an application defect or a missing production composition seam, report it and obtain separate authorization before changing production code.

Run the focused failing selection, deterministic lint, semantic audit/reconciliation, and broader checks proportional to the change. Do not silently turn repair into a legacy-suite refactor.
