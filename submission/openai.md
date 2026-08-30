# OpenAI Marketplace Submission Material

This document is a maintainer-facing, copy-ready source for the OpenAI plugin
submission form. It does not submit or publish the plugin.

## Listing

- **Submission type:** Skills only
- **Plugin name:** Pytest Blackbox
- **Developer name:** ave-satan
- **Category:** Engineering
- **Short description:** Black-box pytest contract testing workflows
- **Long description:** Discover project policy, lint deterministic rules,
  write and repair contract tests, apply release migrations, review focused
  changes, and audit complete Python pytest suites through public application
  boundaries.
- **Website:** https://github.com/ave-satan/pytest-blackbox-skill
- **Support:** https://github.com/ave-satan/pytest-blackbox-skill/issues
- **Privacy:** https://github.com/ave-satan/pytest-blackbox-skill/blob/main/PRIVACY.md
- **Terms:** https://github.com/ave-satan/pytest-blackbox-skill/blob/main/TERMS.md
- **Logo:** `assets/logo.png`
- **Composer icon:** `assets/icon.png`
- **Brand color:** `#6D28D9`

The verified OpenAI developer identity must match `ave-satan` and the public
URLs above. If OpenAI verification exposes a different publisher name, align
the listing, manifest, and legal pages before submission.

## Starter prompts

1. Discover the black-box test policy for this Python service.
2. Add contract tests for this new API endpoint.
3. Audit this pytest suite for missing contracts and policy drift.

## Positive test cases

### 1. Discover project policy

- **User prompt:** Inspect this Python service and propose an initial
  pytest-blackbox configuration. Do not modify files until I confirm it.
- **Expected behavior:** Invoke the `discover` workflow, scan the repository
  without importing or starting the application, infer high-confidence choices,
  identify material ambiguities, and request confirmation before writing.
- **Expected result shape:** Evidence summary, proposed project-wide choices,
  unresolved questions, and an exact `[tool.pytest-blackbox]` TOML patch.
- **Fixture data:** A local Python service checkout with `pyproject.toml`, at
  least one application package, and either an existing `tests/` directory or
  enough source structure to infer a proposed layout. No account or credentials.

### 2. Write endpoint contract tests

- **User prompt:** Add black-box contract tests for the new authenticated
  `POST /v1/orders` endpoint, including authorization, validation, business
  errors, and the created database artifact.
- **Expected behavior:** Invoke `write`, inventory the endpoint's public
  contract, create endpoint-specific tests through the in-process HTTP client,
  use fixture-owned state and repositories, and avoid mocking application
  source internals.
- **Expected result shape:** Focused test files grouped by the configured layout,
  readable parameter IDs, validation output, and a concise summary of covered
  outcomes and any explicitly unresolved contract.
- **Fixture data:** A throwaway Python HTTP service with an authenticated
  `POST /v1/orders` endpoint, a configured test database, and
  `[tool.pytest-blackbox]` in `pyproject.toml`. No external account.

### 3. Repair a failing contract test

- **User prompt:** These API contract tests started failing after a response
  schema change. Diagnose the cause and repair the tests without mocking app
  internals or weakening the assertions.
- **Expected behavior:** Invoke `repair`, reproduce the failure, distinguish a
  contract change from a test-harness defect, make the smallest in-scope test
  or fixture correction, and validate the affected surface.
- **Expected result shape:** Root-cause statement, changed files, preserved
  contract assertions, commands run, and remaining limitations.
- **Fixture data:** A local Python service with one or more failing pytest API
  contract tests whose current public response differs from the old expected
  shape. No credentials.

### 4. Review a focused test diff

- **User prompt:** Review the staged pytest changes for contract gaps,
  implementation coupling, fixture ownership, and nondeterminism. Do not edit
  anything.
- **Expected behavior:** Invoke `review`, remain read-only, respect the staged
  diff as the boundary, and report only evidence-backed findings.
- **Expected result shape:** Findings ordered by severity with file and line
  references, followed by assumptions, validation evidence, and scope limits.
  If no actionable issue exists, say so explicitly.
- **Fixture data:** A Git checkout with a staged Python test diff. No account,
  network access, or private reviewer context.

### 5. Audit a complete suite

- **User prompt:** Audit this complete pytest suite against pytest-blackbox.
  Reconcile every public API endpoint, registered job, scheduler, worker, and
  message handler with its contract coverage. Do not change files.
- **Expected behavior:** Invoke `audit`, build an operation census, run the
  deterministic auditor when available, then independently reconcile both
  operation presence and every distinct application-owned scenario/outcome
  from requirements and source with concrete collected test evidence. Keep the
  audit read-only and do not treat a green primary contract as completeness.
- **Expected result shape:** Audited boundary, operation-to-test census,
  findings ordered by severity, mechanical validation output, manual semantic
  checks, and explicit limitations.
- **Fixture data:** A local Python service with application source and a
  collected pytest suite. Infrastructure may be unavailable because discovery
  and static audit must still provide a useful result.

## Negative test cases

### 1. Request to mock application internals

- **User prompt:** Use pytest-blackbox to unit-test this service method. Patch
  its repository and internal helper calls so the test runs without composing
  the application.
- **Expected safe behavior:** Explain that the requested unit-test shape and
  application-internal mocks are outside the plugin's contract-testing model.
  Offer a public-boundary black-box alternative and ask for the relevant public
  operation if it cannot be inferred safely.
- **Why it should not complete the action:** Doing so would couple the test to
  source implementation and contradict the plugin's defining boundary.

### 2. Unrelated non-Python testing task

- **User prompt:** Use pytest-blackbox to write Playwright component tests for
  this React button.
- **Expected safe behavior:** Do not apply the plugin's Python pytest policy.
  State that the plugin is not the right workflow and fall back to ordinary
  assistance or a relevant frontend-testing capability if one is available.
- **Why it should not complete the action:** The request is unrelated to Python
  pytest contract testing and automatic invocation would be a routing error.

### 3. Unsupported completeness claim

- **User prompt:** Inspect only
  `tests/test_orders/test_business_logic.py` and certify that every endpoint,
  job, scheduler, and worker in the repository is fully covered. Do not inspect
  any other file.
- **Expected safe behavior:** Refuse to certify full-suite completeness from a
  one-file boundary. Offer a focused review of the named file, or explain that a
  complete audit requires permission to inventory the corresponding application
  and test surfaces.
- **Why it should not complete the action:** A coverage claim without an
  operation census would be unsupported and would hide uninspected contracts.

## Proposed availability

All countries and regions offered by the portal where an English-language
open-source plugin, GitHub-based support, and these legal terms are appropriate.
Confirm the final selection against the verified publisher's legal and support
readiness immediately before submission.

## Initial release notes

Initial skills-only submission of Pytest Blackbox. The plugin provides seven
workflows for discovering project policy, linting deterministic rules, writing
and repairing Python contract tests, applying release migrations, reviewing
focused changes, and auditing complete pytest suites. It has no hosted backend,
authentication, test account, telemetry, or reviewer credentials. The final
bundle has been tested through a local Codex marketplace; Claude Code runtime
validation remains pending until the CLI is available.
