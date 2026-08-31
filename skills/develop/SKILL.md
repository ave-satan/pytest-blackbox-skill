---
name: develop
description: Implement or change Python application behavior through a contract-first, test-first black-box pytest workflow. Use whenever the user asks to build or fix an HTTP, JSON-RPC, or WebSocket API, job, scheduler, worker, message handler, or observable integration, even when tests are not mentioned explicitly. Do not use for test-only coverage, test-suite repair, pure refactoring, or read-only review/audit.
---

# Develop With Pytest Blackbox

Read the complete [shared policy](../../core/POLICY.md) and [contracts reference](../../references/contracts.md) before acting. If `[tool.pytest-blackbox]` is absent, perform the shared onboarding workflow before changing tests. Read fixtures, repositories, infrastructure, and tooling references only when the requested behavior implicates them.

Keep the task plan aligned to these visible phases:

1. **Contract:** inventory the requested public/registered operation and build the complete scoped scenario-evidence matrix from authoritative requirements and observable application outcomes. Resolve material ambiguity before writing expected truth.
2. **Red:** write all scoped black-box cases and required test support before editing production behavior. Collect and run the focused selection. Classify and report a meaningful red result; fixture, environment, syntax/import, or oracle failures are not acceptable evidence when the public boundary already exists. If one coarse absence failure such as `404`, an unregistered discriminator, or a missing public symbol masks every case, treat it as provisional red: add only the approved real registration/composition skeleton, rerun, and obtain assertion-level red for the remaining behavior before implementing it.
3. **Green:** implement the smallest cohesive production change that satisfies the whole matrix. Do not add test-only entrypoints, expose internals, patch application source, or weaken cases one by one to follow the implementation.
4. **Verify:** rerun focused collection/execution, deterministic lint, semantic audit/reconciliation, and then broader project checks proportional to risk. Reconcile every matrix row to a collected green node.
5. **Refactor:** improve implementation or test support only while the relevant suite remains green.
6. **Final:** rerun every check affected by refactoring and report the final matrix reconciliation, red/green evidence, exclusions, changed files, and remaining blockers.

If all new tests pass before production changes, stop and determine whether the behavior already exists or the tests fail to distinguish plausible regressions. If a genuinely new public symbol cannot collect, treat that only as the temporary first red; after adding its real production composition boundary, rerun before implementing behavior. A requested production change does not authorize unrelated feature expansion or a broad legacy-suite refactor.

If the request is actually a pure behavior-preserving refactor, stop applying this workflow and establish a green relevant baseline instead of manufacturing red. For test-only work use `write`; for failing/flaky test-support repair use `repair`; for read-only evaluation use `review` or `audit`.
