---
name: review
description: Perform a focused read-only review of specified black-box pytest tests, test-support files, or a test diff. Use when the user asks for findings about correctness, contract coverage, or pytest-blackbox conformance in a bounded scope. Do not use for writing fixes or auditing the whole suite or complete application surface.
---

# Review Pytest Blackbox Tests

Read the complete [shared policy](../../core/POLICY.md), [semantic reconciliation protocol](../../references/reconciliation.md), and [review checklist](../../references/review-checklist.md) before acting. Respect the requested files, diff, or functional surface as the review boundary.

Inspect enough production registration and public composition to verify the claimed contract without broadening into a full-suite audit. Reconcile every reviewed behavior test back to precise authority and test claimed requirements forward to the selected nodes; report `partial`, `missing`, `ambiguous`, or `unsourced` cases instead of treating green code as proof. Lead with prioritized, evidence-backed findings and exact file locations. Report the reviewed boundary, checks run, and residual semantic questions. Do not edit files unless the user separately asks for changes.
