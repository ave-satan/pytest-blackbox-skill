---
name: repair
description: Repair failing, flaky, invalid, or poorly composed black-box pytest tests and their test-support code, including behavior-preserving structural conformance refactors. Use when an existing contract test suite is broken, nondeterministic, or needs an authorized scoped correction. Do not use to add unrelated coverage, change production behavior, or perform a read-only review or full audit.
---

# Repair Pytest Blackbox Tests

Read the complete [shared policy](../../core/POLICY.md) and [semantic reconciliation protocol](../../references/reconciliation.md) before acting. If `[tool.pytest-blackbox]` is absent, perform the shared onboarding workflow before changing tests.

Establish the smallest relevant baseline before editing. Reconcile every existing case in the complete owning component back to current authority and run scoped contract drift when requirements or behavior changed; repairing one failure must not preserve contradictory, removed, documentation-only, or source-only expectations nearby. For a failing or flaky suite, reproduce and classify the failure: application defect, contract mistake, test-support/environment failure, leaked state, or nondeterminism. For a green behavior-preserving structural correction, record the relevant lint/semantic finding or authorized refactoring objective and obtain a focused green baseline; do not manufacture a failure. Repair only test and test-support behavior within the user's scope. If the evidence points to an application defect or a missing production composition seam, report it and obtain separate authorization before changing production code.

Rerun the focused selection and `audit_suite.py --scope <repaired-test-component>`; repeat `--scope` for every changed shared-support path and for another complete component only when the authorized repair spans it. For a structural correction, prove the same relevant public behavior stays green before and after. Run broader checks proportional to the change. Do not silently turn repair into a legacy-suite refactor.
