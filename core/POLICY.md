# Pytest Blackbox

Protect application-owned functional contracts through the real composed application. Treat public product HTTP/JSON-RPC/WebSocket operations and every registered job, scheduler, and incoming-message handler as contract-bearing operations that require their own coverage. Documentation-only endpoints, generated schemas, and API documentation are supporting material rather than product contracts and are excluded.

## Policy levels

- **M — mandatory invariant.** Apply in every supported project. A mechanically proven violation is an audit error.
- **D — adaptive default.** Recommend the default during onboarding. A project may confirm another coherent choice. Once a project-wide D choice is recorded, code that contradicts it is configuration drift and an audit error; a non-binding departure from a recommendation is a warning.
- **O — opt-in capability.** Ignore unless the project explicitly enables it.

Do not turn fixture names, individual operations, or other implementation trivia into configuration. Store only material project-wide choices.

## Project onboarding

Before changing tests, inspect the nearest applicable `[tool.pytest-blackbox]`. If it is absent, run read-only discovery through an interpreter compatible with the project, ask only about material ambiguous D choices plus the managed-dependency O choice, and show the exact `pyproject.toml` patch before writing it. Discovery never reads secrets, imports/starts the application, contacts systems, or mutates the project; parse failures block its proposal. In a monorepo, confirm ambiguous ownership. Never create a separate skill configuration file.

Managed dependencies are inactive without a confirmed non-empty dedicated group such as `dev-ai`. When enabled, use the project package manager to add only documented baseline or concrete missing test/tool packages to that group. Never add the plugin itself, use runtime/general-dev groups, duplicate/move compatible declarations, upgrade unrelated packages, or hand-edit a lockfile. Read [configuration.md](../references/configuration.md) for the complete schema/onboarding and [tooling.md](../references/tooling.md) before changing dependencies or running analysis.

## Contract-first test-first delivery

For authorized application behavior, use `develop`: derive the complete scoped contract matrix from authoritative requirements and public outcomes, write its black-box cases first, obtain a meaningful behavior-level red, implement the smallest cohesive production change, and finish with focused green plus scoped semantic reconciliation. Registration-only collection/`404` failures prove only registration; add only an approved real composition skeleton before seeking assertion-level red. Unexpectedly green new tests require investigation before production edits.

Application defects need a failing public-contract case before the fix. Pure behavior-preserving refactors use green-before/after rather than artificial red. Never weaken expectations or alternate invented implementation branches with one test at a time. Audit/review remain read-only. Report matrix, red/green evidence, changes, exclusions, and blockers; final-tree tooling cannot prove chronology. Read [contracts.md](../references/contracts.md) for the detailed workflow and oracle rules.

## Mandatory contract boundary

- Exercise a supported public application composition/invocation boundary. Do not write unit tests.
- Use the real production composition and independently encode inputs and expected truth. Do not construct the oracle through production DTOs, schemas, codecs, defaults, validators, handlers, registries, or constants.
- Keep every test-owned protocol/outcome type as a minimal projection of the current public contract. Do not expose dependency metadata or speculative optional fields merely because the underlying SDK provides them.
- Do not patch, monkeypatch, or mock application source or internal calls. A narrow typed performance double is allowed only through a supported composition seam under the conditions in [contracts.md](../references/contracts.md).
- Trust installed dependencies. Test application-owned composition, mapping, validation, error translation, contracts, and direct artifacts—not dependency reliability.
- Invoke the tested operation once per ordinary test. Repeat only when repetition is explicitly promised by a public contract and named by the test, such as idempotency, duplicate delivery, retry, or replay. Concurrency repetitions additionally require the active D choice `test_concurrency = true`. A suggestive test name or current implementation behavior is not evidence of a repetition contract.
- Arrange prerequisites through fixtures, repositories, generated-data builders, configuration, Publishers, and external Services. Do not call neighboring application operations as setup.
- An API that starts asynchronous work owns only the dispatch contract. Classify its public completion semantics before testing: response completion may synchronize an awaited broker acceptance; an explicitly scheduled local task needs a public queued-task artifact; later fire-and-forget work with no deterministic supported completion boundary is an observability blocker, not permission to race an immediate read. Assert only the dispatch artifact there and test execution separately at the worker/job/handler boundary.
- If a required production composition seam is missing, report it and request separate authorization for a general production refactor. Never add a test-only entrypoint or reach into runtime internals.

## Test form

- Keep one complete behavioral case per collected test. Multiple assertions may remain together when they prove that case's response and direct artifacts.
- Keep arrange -> one public invocation -> assertions visible. Parameter rows carry values/expected values or uniform arrange-time factories, each with a concise ID that never drives logic; create fresh values during arrange.
- Validation keeps acceptance and rejection in separate homogeneous parametrized functions for each field or contractual field relationship. Rows never select the outcome through a parametrized status or nullable error sentinel, and rejected rows never share control flow with accepted rows.
- Parameterize configuration overrides explicitly before startup and bind expected truth independently from production settings/defaults.
- Put one exact complete primary contract first; later edge cases assert only their changed fact. Prefer native equality/operators and preserve multiplicity. Use explicit partial/matcher semantics only when they add contractual meaning; never reshape actual data or manufacture an aggregate solely for comparison.
- Name bound observations `actual*` and expectations `expected*`; keep `assert` in the test. Wire outcomes remain values unless the public boundary is naturally exception-based. Never freeze time or sleep; use real interval/TTL bounds.

Read [contracts.md](../references/contracts.md) for HTML, assertion layering, matchers, parametrization, validation, naming, TestClass, and failure signaling.

### Adaptive TestClass default

Prefer a pytest `TestClass` when several complete cases can safely reuse expensive identical composition/preparation. Class methods contain only the complete assertions for their own independently prepared case; one case is never split across methods. A fixture performs arrange and invocation before each case, while only immutable behavior-independent machinery may be shared at class/session scope. Do not create a class for one case or for cosmetic grouping.

## Coverage

- A focused change inventories only its relevant surface; a full audit inventories the complete registered/reachable surface. Before a completeness claim, map operation identity, applicable policy depth, owning component/categories, primary contract, public outcome classes, and collected cases in transient evidence—not project configuration.
- Cover every public product HTTP/JSON-RPC/WebSocket operation and registered job, scheduler, and incoming-message handler. HTTP identity is method + path, JSON-RPC adds the RPC method, and WebSocket separates route lifecycle from each command discriminator. Include framework-synthesized functional actions; exclude documentation-only generation.
- Reconcile names bottom-up whenever the case set changes: every category describes all contained cases and every terminal component still maps one-to-one to its operation/component. A local rename/split required by touched scope is ordinary scoped work; unrelated mass layout changes still need authorization.
- Apply the relevant primary/access/validation/errors/business/metrics matrix and map every distinct authoritative public outcome, isolation dimension, boundary, and direct artifact. Do not mirror observationally identical private branches or manufacture corrupt states.
- Registered handlers keep their own contracts; shared worker/runtime behavior is optional separate coverage. Broker topology and registration are session-bootstrap invariants, never collected tests or registry entries.
- Non-contract/operational/hidden/debug surfaces follow the generalized coverage registry. Ask only for a new unmatched surface class; never create a per-operation registry.
- Idempotency, runtime backward compatibility, and concurrency are never inferred. Cover them only from authoritative promises; concurrency additionally requires the active D choice. Schema migration and broker topology remain bootstrap concerns.

Read [contracts.md](../references/contracts.md) for scenario completeness, operation layout, validation, idempotency/isolation, batching, performance doubles, async dispatch, health checks, and category naming.

## Support architecture

- Fixtures own lifecycle/cleanup. Root `conftest.py` only registers plugins/hooks; shared fixtures live in `tests/fixtures/`, local fixtures at the nearest owning group, and ordinary code never lives in `conftest.py`. Only fixtures requested by tests are public; fixture-graph dependencies are underscore-prefixed and never requested by tests.
- Dependencies point broad-to-narrow. Shared support never imports/hardcodes a narrower group, and public support never calls another component's private API or exchanges raw storage references to continue setup.
- Public support uses the shortest truthful owner-relative domain operation/cardinality; backend, transport, discriminator, caller, and optimization details stay private. New suites separate repositories, messaging adapters, external Services, matchers, generators, and environment code; mature coherent layouts are preserved without unauthorized mass moves.
- A reusable expected response structure is a pure oracle builder at the narrowest common owning test surface. Its module exposes the response/artifact role and its callable names the exact returned artifact; one-off expected structures stay inline, and builders never inspect actual results or production schemas/defaults.
- Public capability fixtures compose stable machinery and baseline typed identity/context but do not mutate repositories. Case transitions stay visible through the owning repository. Keep mutable case state function-scoped, immutable bootstrap/factories widest-safely-scoped, base settings session-immutable, and behavior overrides explicit before startup.
- Broker suites have one private session/autouse production-topology bootstrap; dependent fixtures reuse it and teardown deletes isolated resources without inverse declarations.

Read [fixtures.md](../references/fixtures.md) whenever changing fixtures, scopes, configuration, application/client/worker composition, dependency direction, or event-loop setup.

## State and infrastructure

- Tests receive repositories, never raw storage clients or ORM sessions. Ordinary database cases share one function-scoped rollback connection with the application; concurrency is the explicit separately committed exception. `create` is minimally valid, semantic constructors express recurring states, bulk operations are real bulk writes, and savepoints are opt-in only for expected rollback recovery.
- Use real protocol-compatible internal dependencies while omitting unobservable reliability guarantees. Create isolated logical resources programmatically and clean them in reverse ownership order.
- Run all database migrations and mandatory reversal in-process; failures remain visible while cleanup continues. Broker topology runs only real forward bootstrap and resource deletion.
- Do not create infrastructure/startup tests. Ban sleep, retry delays, messaging timeouts/quiet windows, and time freezing; use deterministic completion and propagate original task failures.

Read [repositories.md](../references/repositories.md) for repository APIs, aggregate state, generated data, file-contract builders, artifacts, typed values, matchers, and time/TTL checks. Read [infrastructure.md](../references/infrastructure.md) for environment choices, Compose/Testcontainers/subprocess policies, migrations, transactions/savepoints, messaging, external Services, retries, timeouts, and cleanup.

## Workflow and audit

1. Confirm project policy and requested coverage boundary.
2. Read only the references implicated by the task.
3. Build or update the transient contract-evidence matrix before editing tests; map each discovered public or registered operation and every distinct public scenario/outcome class supported by authoritative requirements to a concrete collected test node. Inspect application-owned source branches to find missing candidate partitions, never to derive expected truth. When an observable source branch has no authoritative contract, record a finding or request a product decision instead of freezing the current implementation as the oracle. Generalized policy decisions may scope only non-contract surfaces and the recorded concurrency boundary; they never exempt a public contract. Operation presence alone never proves completeness. After the final scoped case set is known, reconcile the owning category and terminal-component names against all assigned rows before considering the matrix complete.
4. Build the smallest fixture/repository/Service/messaging graph that exposes public test capabilities.
5. Implement one-case contract tests with independent inputs and expectations.
6. Run focused pytest collection/execution and `../scripts/audit_suite.py <project-root> --scope <owning-test-component>` for deterministic plus semantic reconciliation of a focused write/develop/repair task. Repeat scope for changed shared support and intentionally touched additional components. Run without scope only for an explicitly requested complete audit, then run broader project checks as practical.
7. Reconcile the matrix against collected test nodes; classify failures before editing behavior: application defect, contract mistake, support/environment failure, leaked state, or nondeterminism.
8. Report the matrix summary, coverage boundary/exclusions, changed files, commands, pass counts, warnings, manual-review items, and blockers.

For a mature suite, new/changed tests obey M rules and scoped work reports relevant pre-existing violations without starting a broad legacy refactor. Perform a complete read-only audit only when the user requests the whole suite or a complete component surface. Do not claim full conformance while known mandatory violations remain.

Read [review-checklist.md](../references/review-checklist.md) for reviews. Deterministic tooling cannot decide public-contract scope or semantic independence. For a large full-suite semantic audit, prefer independent subagents per functional surface when available; the primary agent owns the census, policy decisions, reconciliation, and final result.
