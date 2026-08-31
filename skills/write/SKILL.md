---
name: write
description: Design and add new black-box pytest contract tests for Python application behavior, including an explicitly test-only future contract that may remain meaningfully red. Use when the user asks only to test or add coverage for an HTTP, JSON-RPC, or WebSocket API, job, scheduler, worker, message handler, or observable integration contract. Do not use when the same task authorizes production implementation; use develop for that test-first workflow. Do not use merely to repair existing failing tests or to perform a read-only review or full audit.
---

# Write Pytest Blackbox Tests

Read the complete [shared policy](../../core/POLICY.md) before acting. If `[tool.pytest-blackbox]` is absent, perform the shared onboarding workflow before changing tests.

Inventory the requested contract surface, create the transient evidence matrix, and read only the shared references implicated by the work. Add the smallest complete set of public-boundary tests and support code. Once the final scoped case set is known, reconcile function, category-file, and terminal-component names bottom-up; a local rename/split made necessary by the added cases is part of this task, not an unrelated suite refactor. Then run focused tests, deterministic lint, and semantic audit/reconciliation and report the exact coverage boundary and evidence.

Do not change production behavior. If the new tests expose an application defect, preserve the meaningful red evidence and report it; continue into production only through a separately authorized `develop` task. For a future contract, one coarse collection/missing-symbol/`404` result proves only absent registration. Stop at that honest registration-only red, report that scenario-oracle strength remains unverified, and do not add a production skeleton or describe the whole matrix as meaningfully red without production authorization.

Do not expand a focused test request into a full-suite refactor or audit without authorization.
