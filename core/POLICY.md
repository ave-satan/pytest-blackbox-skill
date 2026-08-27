# Pytest Blackbox

Protect application-owned functional contracts through the real composed application. Treat public product HTTP/JSON-RPC/WebSocket operations and every registered job, scheduler, and incoming-message handler as contract-bearing operations that require their own coverage. Documentation-only endpoints, generated schemas, and API documentation are supporting material rather than product contracts and are excluded.

## Policy levels

- **M — mandatory invariant.** Apply in every supported project. A mechanically proven violation is an audit error.
- **D — adaptive default.** Recommend the default during onboarding. A project may confirm another coherent choice. Once a project-wide D choice is recorded, code that contradicts it is configuration drift and an audit error; a non-binding departure from a recommendation is a warning.
- **O — opt-in capability.** Ignore unless the project explicitly enables it.

Do not turn fixture names, individual operations, or other implementation trivia into configuration. Store only material project-wide choices.

## Project onboarding

Before changing tests, locate the nearest applicable `pyproject.toml` and inspect `[tool.pytest-blackbox]`.

If it is absent:

1. Run `../scripts/discover_project.py <project-root>` read-only. First onboarding always has a bundled fallback path that does not install the enhanced toolchain.
2. Inspect the proposed choices and confidence. Do not read secrets, import or start the application, contact external systems, or mutate the project.
3. Ask only about material ambiguous choices, plus the explicit O choice of whether pytest-blackbox may manage missing Python dependencies in a dedicated project dependency group. Number questions sequentially.
4. Show the exact `pyproject.toml` patch and write it only after confirmation.
5. If the confirmed patch enables `dependency_group`, show and run the project-native command that installs the baseline enhanced toolchain in that group, then rerun discovery in auto mode. This installation is part of the selected O capability, not a speculative test dependency.
6. In a monorepo, use the nearest component configuration; ask when ownership is ambiguous.

If the project has no `pyproject.toml`, offer to create one or continue with confirmed temporary choices. Never create a separate skill configuration file. Read [configuration.md](../references/configuration.md) for the schema, non-public coverage registry, discovery rules, and M/D/O enforcement.

The managed-dependency capability is inactive unless onboarding records a non-empty `dependency_group` such as `dev-ai`. When active, install the documented baseline analysis toolchain and later add only concrete missing packages required by pytest-blackbox tooling or generated tests, using the project's package manager and that dedicated group. Without the capability, use bundled fallback commands and do not mutate dependencies. Never add the plugin itself to project dependencies, fall back to runtime/default/general `dev` dependencies, duplicate or move an already declared package, upgrade unrelated packages, or hand-edit a lockfile. Read the managed-dependency section in [configuration.md](../references/configuration.md) and [tooling.md](../references/tooling.md) before changing dependencies.

## Mandatory contract boundary

- Exercise a supported public application composition/invocation boundary. Do not write unit tests.
- Use the real production composition and independently encode inputs and expected truth. Do not construct the oracle through production DTOs, schemas, codecs, defaults, validators, handlers, registries, or constants.
- Do not patch, monkeypatch, or mock application source or internal calls. A narrow typed performance double is allowed only through a supported composition seam under the conditions in [contracts.md](../references/contracts.md).
- Trust installed dependencies. Test application-owned composition, mapping, validation, error translation, contracts, and direct artifacts—not dependency reliability.
- Invoke the tested operation once per ordinary test. Repeat only when repetition is explicitly promised by a public contract and named by the test, such as idempotency, duplicate delivery, retry, replay, or concurrency. A suggestive test name or current implementation behavior is not evidence of that promise.
- Arrange prerequisites through fixtures, repositories, generated-data builders, configuration, Publishers, and external Services. Do not call neighboring application operations as setup.
- An API that starts asynchronous work owns only the dispatch contract. Assert the queued operation there; test its execution separately at the worker/job/handler boundary.
- If a required production composition seam is missing, report it and request separate authorization for a general production refactor. Never add a test-only entrypoint or reach into runtime internals.

## Test form

- Keep one complete behavioral case per collected test. Multiple assertions may remain together when they prove that case's response and direct artifacts.
- For ordinary functions keep arrange -> one public invocation -> assertions visible in that order.
- Parameterize variations with actual values/expected values or same-signature arrange-time factories. Every row has a concise explicit ID; IDs never drive test logic.
- Create timestamps, UUIDs, generated values, and other fresh data during arrange, not collection.
- Put the complete general contract first. Its primary assertion covers the exact complete public response/value, including stable fields unaffected by a PATCH or partial input. Edge cases assert only their changed observable fact.
- Prefer `assert actual == expected`. Compare an existing compound value whole through exact structures or `tests.cmp`; never manufacture an aggregate merely to combine independent observations.
- Name separately bound observed values `actual`/`actual_*` and separately bound expectations `expected`/`expected_*`.
- Keep the `assert` operator in the test. Extract expected builders or pure equality matchers, not assertion helpers.
- Use `pytest.raises` only when the public invocation contract is naturally exception-based. Keep response, frame, handshake-denial, rejection, and other wire outcomes as ordinary values; a test adapter never invents an exception for them. Use `pytest.fail` only for an explicitly forbidden reached branch and preserve unexpected tracebacks.
- Never freeze time or sleep. Check timestamps, deadlines, expiration, and TTL against real invocation bounds and documented storage precision.

### Adaptive TestClass default

Prefer a pytest `TestClass` when several complete cases can safely reuse expensive identical composition/preparation. Class methods contain only the complete assertions for their own independently prepared case; one case is never split across methods. A fixture performs arrange and invocation before each case, while only immutable behavior-independent machinery may be shared at class/session scope. Do not create a class for one case or for cosmetic grouping.

## Coverage

- Inventory the requested surface before claiming completeness. A focused change may inspect only the relevant surface; a coverage review inventories the complete registered/reachable surface.
- Before claiming coverage, build a transient contract-evidence matrix: discovered operation identity, applicable registry decision/depth, owning test component, applicable categories, primary contract node, and application-owned observable outcome classes. Keep it in working notes/report evidence, not project configuration or a per-operation registry.
- Cover every public product HTTP/JSON-RPC/WebSocket operation and every registered job, scheduler, and incoming-message handler. Ordinary HTTP identity is method + path template; JSON-RPC identity is HTTP method + JSON-RPC method. WebSocket identity separates the route handshake/lifecycle contract from every independently invokable client-message discriminator.
- Name every test module after the public contract aspect it proves. Use `test_business_logic.py` only for business rules, state transitions, and domain outcomes; access, validation, errors, and metrics keep their established names, while another coherent aspect gets a concise behavior-specific name. For example, `test_connection.py` is the recommended name for a route-level WebSocket handshake/lifecycle contract. Do not use `test_business_logic.py` as a generic success bucket or create empty category files.
- Do not create product-contract tests for Swagger/OpenAPI/schema/documentation-only operations or generated documentation artifacts. A functional endpoint remains contract-bearing merely when it also has documentation; the exclusion applies only when documentation is the whole purpose.
- A handler executed by a worker is mandatory; generic shared worker/runtime mechanics are a separate non-contract surface unless intentionally selected. Never let shared runtime coverage substitute for a handler contract.
- For non-contract, operational, hidden, debug, or ambiguous surfaces, consult the generalized coverage registry before asking. Ask only when a newly discovered class of operation has no applicable decision; never maintain a per-operation registry.
- Apply the applicable matrix: primary contract, access, validation, application errors, business rules/state transitions, and metrics when declared.
- Validation varies one field at a time, except contractually related fields. For non-enum fields cover an ordinary valid value when appropriate, valid boundaries, the nearest invalid values outside them, and representative invalid forms. For enums cover every allowed member and at least one disallowed member instead of adding an ordinary randomized row. Validation tests assert acceptance/rejection and the validation error—not downstream business work.

Read [contracts.md](../references/contracts.md) for performance doubles, operation layout, TestClass constraints, validation, naming, assertions, matchers, async dispatch, and health checks.

## Support architecture

- Fixtures own pytest lifecycle and cleanup. Root `conftest.py` only registers plugins/hooks; suite-wide fixtures live in `tests/fixtures/`; local fixtures live in the nearest group `conftest.py`. No ordinary helpers, classes, providers, constants, or tests belong in any `conftest.py`.
- Only fixtures requested by tests are public. Prefix fixture-graph/bootstrap/cleanup dependencies with `_`; tests never request private fixtures.
- Keep dependencies broad-to-narrow. Shared support never imports or hardcodes a functional group's private implementation, including its route paths, message discriminators, topology names, and other component-owned literals.
- In a new suite use repositories for addressable stored state, Publishers/Collectors for messaging, Services for external network systems, `cmp` for equality matchers, and a project-owned generator facade (default `tests.generators`, default backend Faker) for generated values. Adapt a coherent mature support layout without automatic mass moves; do not create a generic `support` package.
- Keep case data function-scoped. Hoist only immutable/stateless factories and bootstrap. Reuse typed preparation contexts rather than rediscovering known actors, credentials, identifiers, or resources. A state helper belongs to the repository that owns the state it mutates, not to a neighboring repository merely capable of rediscovering its key.
- Keep configuration base session-scoped and immutable; derive a per-case copy and parameterize every behavior-affecting override before application startup.

Read [fixtures.md](../references/fixtures.md) whenever changing fixtures, scopes, configuration, application/client/worker composition, dependency direction, or event-loop setup.

## State and infrastructure

- Tests receive purposeful repository fixtures, never raw storage clients or SQLAlchemy sessions. Repositories use the project's sync/async statement API and the same function-scoped transaction-owned `Connection`/`AsyncConnection` as the application.
- `create` builds the minimally valid object; semantic constructors express recurring states. Bulk creation builds fresh value sets and uses a real bulk write.
- Use an opt-in savepoint for cases where an expected application rollback could invalidate the outer transaction. Ordinary tests do not pay for it.
- Use real protocol-compatible internal dependencies, but omit reliability guarantees the application cannot observe. Create isolated logical resources programmatically and delete them in reverse lifecycle order.
- Run every migration and mandatory downgrade in-process. A downgrade failure must fail visibly while cleanup still attempts resource removal.
- Do not use infrastructure/startup tests. Optional health checks are focused operational contracts, not dependency reliability tests.
- Ban sleeps, delayed polling, messaging timeouts, quiet windows, and retry backoff. Prefer deterministic completion; bounded immediate polling is a non-messaging fallback only when no completion signal exists. An in-process async transport harness waits for either the next protocol event or completion of its application/runner task and propagates the original task failure instead of hanging behind an event queue.

Read [repositories.md](../references/repositories.md) for repository APIs, aggregate state, generated data, file-contract builders, artifacts, typed values, matchers, and time/TTL checks. Read [infrastructure.md](../references/infrastructure.md) for environment choices, Compose/Testcontainers/subprocess policies, migrations, transactions/savepoints, messaging, external Services, retries, timeouts, and cleanup.

## Workflow and audit

1. Confirm project policy and requested coverage boundary.
2. Read only the references implicated by the task.
3. Build or update the transient contract-evidence matrix before editing tests; map each discovered operation and application-owned observable outcome class to a concrete test node or an explicit policy decision.
4. Build the smallest fixture/repository/Service/messaging graph that exposes public test capabilities.
5. Implement one-case contract tests with independent inputs and expectations.
6. Run `../scripts/lint_suite.py <project-root>` for deterministic diagnostics and `../scripts/audit_suite.py <project-root>` for the same diagnostics plus the preserved semantic review section, then focused and broader project checks as practical.
7. Reconcile the matrix against collected test nodes; classify failures before editing behavior: application defect, contract mistake, support/environment failure, leaked state, or nondeterminism.
8. Report the matrix summary, coverage boundary/exclusions, changed files, commands, pass counts, warnings, manual-review items, and blockers.

For a mature suite, perform a complete read-only audit. New/changed tests must obey M rules; record existing violations but never start a broad legacy refactor without explicit authorization. Do not claim full conformance while known mandatory violations remain.

Read [review-checklist.md](../references/review-checklist.md) for reviews. The deterministic auditor cannot decide public-contract scope or semantic independence. For a large full-suite semantic audit, prefer independent subagents per functional surface when available; the primary agent owns the census, policy decisions, reconciliation, and final result.
