---
name: audit
description: Perform a complete read-only semantic and structural audit of a black-box pytest suite or an explicitly named full application component surface. Use only when the user asks for a full, complete, or whole-suite coverage and conformance audit. Do not use for ordinary test writing, repair, or a focused file or diff review.
---

# Audit Pytest Blackbox Tests

Read the complete [shared policy](../../core/POLICY.md) and [review checklist](../../references/review-checklist.md) before acting. Confirm the audit boundary, inventory every reachable or registered contract-bearing operation in that boundary, and reconcile the transient contract-evidence matrix against collected test nodes.

Run `../../scripts/audit_suite.py <project-root>` and relevant collection, lint, type, and test checks. Treat deterministic output as evidence, not proof of semantic completeness. When available and authorized, use independent subagents for large functional surfaces; the primary agent retains ownership of the census, reconciliation, and final findings.

Keep the audit read-only. Report prioritized findings, tested evidence, excluded surfaces, warnings, and manual-review items. Do not repair findings unless the user separately authorizes changes.
