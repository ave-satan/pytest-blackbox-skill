# Changelog

All notable Pytest Blackbox changes are documented here. Release entries keep
existing-project actions explicit and idempotent so the `upgrade` workflow can
apply only relevant migrations without rerunning a full suite audit.

## [Unreleased]

## [0.10.0] - 2026-09-04

### Changed

- Semantic reconciliation is now explicitly bidirectional. The transient
  matrix maps authoritative requirements to collected cases and every existing
  behavior test back to precise authority, with mandatory `covered`, `partial`,
  `missing`, `ambiguous`, and `unsourced` counts.
- Scenario completeness now includes explicit applicability decisions for
  actor/owner isolation, lifecycle state, compound identity, local date/timezone/
  TTL, configuration, external-call snapshot and post-call guards, async phase
  ownership, batch partitions, authoritative repetition, and enabled
  concurrency. A counterfactual pass asks which case distinguishes deletion,
  inversion, wrong-actor scoping, or movement of each observable condition.
- A covered scenario must distinguish every independently breakable public
  promise, including exact created/changed artifacts and explicitly absent or
  preserved effects. One asserted response no longer covers unverified negative
  artifacts.
- `write`, `develop`, and `repair` now perform scoped contract-drift
  reconciliation so removed/disabled behavior, obsolete compatibility,
  documentation-only routes, accidental aliases, and async ownership shifts do
  not survive as source-derived contracts. `review` and `audit` apply the same
  reverse-authority gate read-only.
- `SEM013`–`SEM017` separate reverse authority mapping, scenario dimensions and
  counterfactual analysis, complete promises, independent oracle encoding, and
  hidden wait/retry defaults into individually reconcilable audit items.
- `ORC001` rejects assertions and expected builders derived from production
  `Settings`/configuration; `TIME002` rejects unconstrained expected-side
  timestamp matchers; `WAIT003` rejects messaging `get(fail=False)` drains that
  inherit a positive timeout instead of passing `timeout=0`.
- The repository now includes dependency-free deterministic regression
  evaluations plus an independent forward-evaluation project for the semantic
  classes that static analysis cannot prove.

### Existing-project actions

#### PBB-MIG-0.10.0-01 — Reconcile tests back to current authority

- **Condition:** an owning component contains behavior tests whose exact
  requirement is unclear, removed, disabled, documentation-only, inferred from
  source, or contradicted by the current product contract.
- **Action:** build the bidirectional transient matrix from
  `references/reconciliation.md`. Map every authoritative requirement forward
  and every existing test backward, classify all rows as `covered`, `partial`,
  `missing`, `ambiguous`, or `unsourced`, resolve product ambiguity, and remove
  or rewrite unsupported expectations only within the authorized scope.
- **Do not:** preserve behavior because production still contains a branch,
  create a persistent per-operation registry, or broaden a focused migration
  into a full-suite refactor.
- **No-op when:** every behavior case in the selected component maps to current
  authority and all authoritative rows are fully covered.

#### PBB-MIG-0.10.0-02 — Decouple configuration-derived oracles

- **Condition:** a test or expected-artifact builder reads production
  `Settings`, DTOs, schemas, defaults, constants, codecs, registries, or private
  algorithms to calculate input boundaries or expected truth.
- **Action:** bind the explicit test-owned input/configuration override and its
  independent expected value in parametrization or an immutable case context.
  Keep production configuration only in fixture-owned composition. Assert a
  public invariant rather than cloning a private selection/hash/ranking
  algorithm when the algorithm itself is not contractual.
- **Do not:** change only a variable name, copy a production default into a
  second helper without authoritative evidence, or construct expected data
  through production types.
- **No-op when:** changing production configuration/algorithm alone cannot
  update both actual and expected values together.

#### PBB-MIG-0.10.0-03 — Remove hidden waits and bound timestamps

- **Condition:** an expected-side timestamp matcher has no invocation lower and
  upper bounds; a messaging drain uses `get(fail=False)` without explicit
  `timeout=0`; or test configuration inherits avoidable positive timeout,
  retry, backoff, or quiet-window defaults.
- **Action:** capture real start/finish bounds around the tested invocation and
  apply both to generated timestamps/TTL-derived values. Pass explicit zero for
  no-wait protocol calls when supported, otherwise use the documented minimum
  and report the unavoidable bound. Disable test-only retries/backoff.
- **Do not:** freeze time, sleep, add polling, introduce arbitrary slack, or
  treat a method name such as `drain` as proof of no-wait behavior.
- **No-op when:** application-produced time values are bounded and every
  protocol/library wait is explicitly disabled or minimized.

## [0.9.0] - 2026-09-01

### Changed

- Validation coverage now uses separate homogeneous parametrized functions for
  acceptance and rejection of each field or contractual field relationship.
  Valid boundaries and all allowed enum/discriminator members stay in
  `test_<field>_accepted`; outside-boundary and other invalid values stay in
  `test_<field>_rejected`.
- Validation parametrization no longer carries expected status or nullable
  error sentinels across mixed outcomes. Each function asserts its fixed public
  outcome directly; rejection rows parameterize only input and genuinely
  varying error details. `VAL001` detects the common mixed structural form and
  `SEM012` owns the complete semantic reconciliation.
- Reusable expected response artifacts now use pure builders at the narrowest
  common owner. Role-explicit modules such as `responses.py` contain callables
  named for the exact returned artifact (`<contract>_body`,
  `<contract>_headers`, or a true complete `<contract>_response`), while
  one-off expected structures remain inline. `SEM011` reviews this naming and
  ownership without imposing a heuristic filename lint.

### Existing-project actions

#### PBB-MIG-0.9.0-01 — Split validation acceptance and rejection

- **Condition:** one validation function mixes accepted and rejected rows,
  parameterizes expected response status, uses `None`/a no-error factory as an
  acceptance sentinel, or branches assertions by outcome/error presence.
- **Action:** split each affected field or contractual field relationship into
  homogeneous `test_<field>_accepted` and `test_<field>_rejected` functions.
  Move ordinary valid values, valid boundaries, and every allowed enum member
  to the accepted parametrization; move nearest outside-boundary values,
  disallowed enum members, and other invalid forms to the rejected
  parametrization. Assert the fixed acceptance/rejection status directly and
  keep only genuinely varying exact error details in rejection rows. When
  rejected variants have distinct public error contracts, use additional
  narrowly named rejection-only functions rather than a mixed outcome matrix.
- **Do not:** duplicate downstream business/artifact assertions in valid rows,
  create a function per parameter row, combine unrelated fields, or replace the
  split with status/error conditionals.
- **No-op when:** every validation field/relationship already has homogeneous
  accepted and rejected coverage with readable row IDs and direct fixed-outcome
  assertions.

#### PBB-MIG-0.9.0-02 — Name reusable response oracles by artifact

- **Condition:** a reusable expected response builder lives in a domain-noun or
  vague helper/builder module, or its callable name looks like a domain entity
  factory and does not reveal whether it returns a body, headers, or a complete
  response projection.
- **Action:** keep one-off expected structures inline. Under the standard
  layout, move genuinely reused response-oracle builders to `responses.py` at
  their narrowest common owning test surface (or to the precise natural
  protocol artifact module). With `layout = "preserve"`, retain an existing
  equally role-explicit equivalent. Rename each touched callable after its exact
  returned artifact: `<contract>_body`, `<contract>_headers`, or
  `<contract>_response` only for a complete response projection. Update direct
  imports so the call site remains self-describing.
- **Do not:** add an `expected_*` prefix to builders, call a body dictionary a
  full response, merge merely similar sibling contracts, move a local builder
  to broader shared support, or extract a builder used by only one expected
  assertion.
- **No-op when:** every reused response oracle already has truthful artifact
  naming, pure test-owned construction, narrow common ownership, and a
  role-explicit standard or coherently preserved module.

## [0.8.0] - 2026-08-31

### Changed

- `audit_suite.py` and `lint_suite.py` now accept repeatable test-path
  `--scope` arguments. Scoped runs still index the complete suite for cross-file
  analysis but report only selected diagnostics and intersecting semantic
  surfaces; omitting scope preserves the complete-suite audit.
- `write`, `develop`, and `repair` now use scoped semantic reconciliation.
  Complete read-only audit is reserved for an explicit whole-suite or complete
  component request, so ordinary focused work no longer inherits unrelated
  `SEM*` obligations.
- `repair` now supports an authorized green behavior-preserving structural
  correction through green-before/after evidence instead of requiring an
  artificial failing test.
- Discovery now fails closed, lists representative unparseable Python paths,
  and withholds its policy proposal until rerun with a compatible interpreter.
- `ENC001` now proves calls from public support classes to collaborator-private
  methods without assuming the collaborator field itself is private, while
  private implementation classes and own private methods remain allowed.
- The shared policy was reduced to cross-workflow invariants and routing; the
  detailed procedures remain in task-specific references.
- Coverage expansion now ends with mandatory bottom-up naming reconciliation:
  individual cases map to a category whose filename describes the complete
  current case set, and every terminal component continues to map one-to-one to
  its public operation or independently invokable component.
- A stale historical filename is no longer preserved merely because new cases
  fit there approximately. Rename a still-cohesive touched category to its
  narrowest truthful shared behavior, or split genuinely different cohesive
  aspects. This local correction is not treated as an unauthorized broad layout
  refactor, including under a mature preserved layout.
- `SEM001` and the `write`, `develop`, and `audit` workflows now perform this
  reconciliation after the final scoped case set is known.

### Existing-project actions

#### PBB-MIG-0.8.0-02 — Scope focused pytest-blackbox automation

- **Condition:** project automation or agent instructions run unscoped
  `audit_suite.py`/`lint_suite.py` for a focused write, develop, repair, or
  component-local lint task; or a green structural test refactor is blocked
  solely because no failing pytest case exists.
- **Action:** pass each complete owning test component and every changed shared
  support path through repeatable `--scope` arguments and keep the task's
  semantic matrix limited to those public operations/components. For a green
  structural correction, record the policy finding/objective and relevant
  green baseline, then prove green after the change.
- **Do not:** scope a promised whole-suite audit, select only convenient files
  inside a component whose complete coverage was requested, stop indexing
  shared support, or manufacture a red result for behavior-preserving work.
- **No-op when:** focused automation already supplies complete owning component
  paths and whole-suite audits still run without scope.

#### PBB-MIG-0.8.0-01 — Reconcile expanded test-surface names

- **Condition:** a category file or terminal component was named for an earlier
  narrower case set and now contains cases outside that name, or newly added
  cases were placed in the nearest plausible file without re-evaluating the
  resulting full node IDs.
- **Action:** inventory every case in the touched terminal component and
  reconcile names bottom-up. Keep accurate case names; rename a cohesive
  category/component to the narrowest behavior covering all assigned cases, or
  split distinct cohesive aspects. Update imports and collection selectors
  affected by that local move.
- **Do not:** keep a stale historical name to minimize the diff, replace it with
  vague `test_behavior`/`test_success`/`test_technical`, create a file per case,
  merge independently invokable operations, or refactor unrelated test groups.
- **No-op when:** every touched category filename truthfully covers its complete
  current case set and every terminal component still maps exactly one public
  operation or independently invokable component.

## [0.7.0] - 2026-08-31

### Changed

- Assertions are native-first: exact mappings/lists, cardinality, membership,
  and focused scalar projections use ordinary Python before custom matchers.
  `OrderedList` remains valid when contractual order benefits from matcher
  composition or diagnostics; a one-field ordered projection instead uses a
  list comprehension when complete item contracts are already protected.
- Partial structural semantics are visible in matcher names such as
  `PartialMapping`/`PartialObject`, never hidden behind `partial=True`. Exact
  mappings remain dictionaries, and matchers that merely restate `len` or
  membership are discouraged.
- Public test-support APIs now start from the shortest canonical owner-relative
  operation. Repository, Publisher, Collector, Service, Client, runner, and
  builder names do not repeat their owning noun; qualifiers distinguish only
  real sibling targets, states, outcomes, or cardinalities. The deterministic
  `ENC001` check rejects cross-component private-member access.
- Schema migration upgrade/downgrade remains a fixture bootstrap invariant.
  Runtime legacy-data compatibility receives a public-behavior test only when
  an authoritative product or operational requirement promises it; source
  conversion branches alone do not create a contract.
- Scenario completeness now calls out same-resource/different-principal
  isolation explicitly. `WS001` rejects every empty WebSocket connection
  context rather than only the nested handshake-exception spelling.
- `SEM006`, `SEM010`, and `SEM011` were refined to audit these boundaries
  without turning implementation vocabulary or matcher class names into a
  per-project configuration surface.

### Existing-project actions

These actions are conditional and idempotent. Apply only those whose condition
matches the current suite.

#### PBB-MIG-0.7.0-01 — Native-first and explicit partial comparisons

- **Supersedes:** `PBB-MIG-0.6.0-01`.
- **Condition:** an exact mapping/list, simple cardinality/membership predicate,
  or one-field ordered projection is expressed through a custom matcher without
  adding semantics; a partial matcher hides its semantics behind a boolean
  option; or actual compound data is still merged/deleted/overwritten before
  comparison.
- **Action:** replace exact matcher wrappers with ordinary dictionaries/lists
  and simple predicates with `len`, membership, `all`, or comprehensions. Give
  true partial matchers an explicitly partial public name and pass the complete
  observed compound value. Keep `OrderedList` when order is contractual and its
  matcher composition/diagnostics are useful; for a focused ordered field whose
  complete item contract is protected elsewhere, compare native list
  comprehensions.
- **Do not:** weaken a closed primary contract, convert a multiplicity-sensitive
  collection to a set, project unprotected stable fields, or remove
  `OrderedList` merely because an ordinary list could also work.
- **No-op when:** native structures/operators express simple checks, matchers add
  real semantics, partiality is explicit in the public matcher name, and every
  focused collection projection is already backed by complete item coverage.

#### PBB-MIG-0.7.0-02 — Owner-relative support APIs and encapsulation

- **Supersedes:** `PBB-MIG-0.6.0-02`.
- **Condition:** a public support method mechanically repeats its owning domain
  noun, exposes raw storage references, omits a canonical base CRUD operation,
  or a support object calls another object's private member.
- **Action:** start from the shortest canonical operation (`create`, `get_one`,
  `get_many`, `count`, `update`, `delete`, `publish`, `collect_one`, `run_once`)
  and add only the qualifier needed among siblings. Return typed domain values.
  Expose the smallest truthful public collaborator capability or move cohesive
  multi-object work to an aggregate owner.
- **Do not:** rename a method after a caller/argument/discriminator, expose raw
  keys/hashes/index members, make base `create` private because current cases
  prefer semantic constructors, or silence `ENC001` by renaming underscores.
- **No-op when:** owner context plus method name already communicates one
  truthful domain operation/cardinality and all collaborator boundaries are
  public, narrow, and typed.

#### PBB-MIG-0.7.0-03 — Contractual compatibility and isolation

- **Condition:** a collected test asserts a migration/conversion implementation
  without an authoritative backward-compatibility promise; a promised legacy
  behavior inspects raw storage instead of the public outcome; or a
  principal-scoped operation lacks the same-resource/different-principal case.
- **Action:** remove source-inferred compatibility cases, or—when an
  authoritative requirement exists—arrange legacy state through a domain
  repository/builder and assert only preserved public behavior/direct
  artifacts. Add the missing isolation case for each operation whose result is
  ownership-scoped.
- **Do not:** remove database upgrade/downgrade bootstrap, infer a requirement
  from current source, name a public-behavior test after its migration
  algorithm, or manufacture inaccessible/corrupt states.
- **No-op when:** migration lifecycle is fixture-owned, runtime compatibility is
  tested only when promised, and every ownership-sensitive operation proves
  cross-principal isolation.

#### PBB-MIG-0.7.0-04 — Explicit WebSocket lifecycle outcomes

- **Condition:** a collected test enters `connect()`/`websocket_connect()` with
  a body containing only `pass`, including inside `pytest.raises`.
- **Action:** make the test-owned adapter expose the natural accepted, denied,
  close, or continuation outcome and assert that value directly.
- **Do not:** invent an exception for a wire outcome, assert SDK internals, or
  retain an empty context merely to trigger `__aenter__`/`__aexit__`.
- **No-op when:** each connection context observes a meaningful public value or
  behavior and no empty lifecycle body remains.

## [0.6.0] - 2026-08-31

### Changed

- Focused variations/edge cases and intentionally extensible natural containers
  now pass the complete observed compound value to an
  implementation-independent structural matcher. Selected-field projections
  and mutation/merging of ignored actual values are forbidden; whole-container
  normalization remains available for incompatible equality semantics, while
  closed primary values stay exact.
- Domain naming now governs every public domain-facing test-support class,
  fixture, and method, including repositories, Publishers, Collectors,
  Services, Clients, runners, builders, and generators. Names express the role
  plus the observable domain action/target/state/outcome and truthful
  cardinality rather than storage, transport, persisted discriminators, caller
  scenarios, or optimizations. Intentionally generic structural/protocol
  primitives keep precise abstraction-level names without invented domain terms.
- `SEM010` and `SEM011` add explicit semantic review for those two rules without
  pretending that a deterministic linter can infer contract intent or domain
  vocabulary.

### Existing-project actions

These source-preview actions are conditional and idempotent. The `upgrade`
workflow ignores them until they are released unless the user explicitly opts
into an unreleased checkout preview.

#### PBB-MIG-0.6.0-01 — Scoped partial compound comparisons

- **Condition:** a variation/edge case or intentionally extensible natural
  container manually builds a selected-field projection from one existing
  compound observation, deletes fields, or merges or overwrites ignored actual
  values before comparison; or partial matching omits a stable application-owned
  element from a closed primary contract.
- **Action:** compare the complete observed value once through an appropriate
  test-owned structural matcher that requires every declared element and allows
  only unrelated elements. Use it only when the remainder is already protected
  by the exact primary contract or the declared subset is the complete
  application-owned contract of an intentionally extensible container. When the
  container's equality implementation cannot delegate to the matcher, normalize
  the complete natural container without selecting fields or losing contractual
  multiplicity.
- **Do not:** make the policy depend on one matcher class/name, weaken the
  closed primary contract to partial matching, hide a missing declared element, or
  manufacture an aggregate from independent observations.
- **No-op when:** closed primary values are exact and every permitted partial
  check passes one intact compound observation (or its complete natural
  normalized representation) to a pure matcher while declaring the complete
  application-owned subset for an extensible container.

#### PBB-MIG-0.6.0-02 — Domain-named public test support

- **Condition:** a public domain-facing repository, Publisher, Collector,
  Service, Client, runner, builder, generator, fixture, or method is named after
  storage, transport, a persisted discriminator, its calling test, or an
  implementation optimization; misstates its returned/mutated entity or
  cardinality; or uses a generic name while one component exposes several
  contracts.
- **Action:** rename the public API by its role plus the smallest domain action,
  target, state, or outcome visible to tests; keep domain nouns consistent across
  connected layers and move technical/performance mechanics behind private
  methods. Preserve canonical generic operations when the owning component has
  one unambiguous contract, and keep intentionally generic structural/protocol
  primitives precisely named at their real abstraction level.
- **Do not:** rename a method after an owner/context argument when it returns
  another entity, expose backend/protocol details, mechanically repeat the class
  noun, or mass-rename an already coherent mature vocabulary merely to copy an
  example.
- **No-op when:** every public domain-facing support name truthfully communicates
  role, domain meaning, result/cardinality, and ambiguity without leaking
  private implementation details.

## [0.5.0] - 2026-08-31

### Added

- `develop` workflow for contract-first, test-first application delivery:
  complete scoped scenario matrix, meaningful red evidence, cohesive production
  implementation, green verification, and refactoring only while green.
- Staged red evidence for newly registered operations: a coarse missing-route,
  discriminator, or symbol failure is followed by assertion-level red after
  adding only the approved real composition skeleton.
- Explicit scenario dimensions for compound ownership/isolation, acknowledged
  no-op and stale handler outcomes, framework-generated functional actions, and
  mixed batch/dependency result partitions.

### Changed

- Operation census now inspects final framework registrations and treats each
  functional confirmation/rendering GET and mutating POST as its own operation.
- Broker topology and consumer/handler registration are no longer test
  surfaces. One private session/autouse fixture runs the real production
  bootstrap in an isolated namespace; setup failure is the check, with no
  expected-topology model, broker-state comparison, or topology downgrade.
- A single call against prearranged final state is explicitly not idempotency
  evidence; idempotency reuses the complete primary oracle and proves the full
  stored terminal result plus exact non-duplication artifacts.
- Collection assertions preserve cardinality and duplicate multiplicity;
  rendered HTML/SSR cases cover complete relevant application-owned view state
  without snapshotting framework markup.
- Registered handler matrices include distinct observable missing, no-op,
  stale/mismatched, prerequisite, lock-ownership, preservation, and time-boundary
  outcomes without mirroring unobservable internal branches.
- External Services may express homogeneous and mixed per-item dependency
  responses so tests protect application-owned partial-error mapping without
  patching production clients or retesting SDK reliability.
- Async dispatch tests classify their supported completion boundary and report
  genuinely unobservable fire-and-forget work as a blocker; validation keeps
  its compact matrix while one focused case may prove rejection side effects
  are absent.
- Category ownership follows contract meaning: domain-state rejections remain
  business logic, while transport, dependency, and operational failures remain
  errors.
- `upgrade` ignores `[Unreleased]` migrations unless the user explicitly opts
  into a source-checkout preview.
- `SEM001`, `SEM004`, `SEM006`, conditional `SEM008`, and `SEM009` now separate
  final HTTP/framework registrations, mandatory handler outcomes, optional
  worker-runtime behavior, messaging bootstrap ownership, ownership/isolation,
  and mixed batch partitions.
- SQLAlchemy, Alembic, and pytest-asyncio mechanics are explicitly conditional
  on those technologies while their underlying repository, lifecycle, and
  single-runtime invariants remain stack-neutral.
- Source branches now reveal candidate scenario gaps but never define expected
  truth; undocumented observable behavior becomes a finding or product question.
- Test-only future contracts report coarse missing-registration red honestly
  without adding a production skeleton or overstating scenario evidence.
- `STR007` reports collected `test_topology.py` modules and directs migration
  to the private session bootstrap.
- Terms now explicitly include test-first application development in the
  plugin's intended use.

### Existing-project actions

These actions are conditional and idempotent. They prepare existing projects
for the next minor release; the configuration schema remains at
`config_version = 1`.

#### PBB-MIG-0.5.0-01 — Registered actions and ownership isolation

- **Condition:** a selected framework action expands into multiple functional
  method/path registrations without separate test owners, or a resource keyed
  by principal/tenant plus resource has only same-principal positive coverage.
- **Action:** inventory the final registration table, add the missing operation
  component, and add another-principal isolation cases for every independently
  observable read/write contract.
- **Do not:** test documentation-only routes, infer hidden endpoints from helper
  names, or combine distinct operations into one workflow test.
- **No-op when:** every selected functional registration and compound ownership
  dimension already maps to concrete collected evidence.

#### PBB-MIG-0.5.0-02 — Session-owned production topology bootstrap

- **Condition:** a broker-backed suite has `test_topology.py`, a topology test or
  expected-topology model under another name, case/local fixtures that declare
  production routes, or no private session bootstrap invoking the real
  production declaration/composition seam.
- **Action:** create only an isolated enclosing broker namespace, move the real
  production bootstrap call into one private session/autouse fixture backed by
  `tests/environment/`, make every broker-dependent fixture depend on it, and
  remove collected topology cases, state comparison, and duplicate declarations.
- **Do not:** inspect broker state as an equality oracle, catch bootstrap errors,
  leave a bootstrap consumer competing with test workers, invoke inverse
  production declarations at teardown, or replace isolated resource deletion
  with a topology downgrade test.
- **No-op when:** production topology bootstrap completes once during session
  setup, every broker-dependent fixture relies on it, no topology test/spec
  exists, and teardown only deletes the isolated namespace/resources.
- **Supersedes:** the topology branch of `PBB-MIG-0.4.0-06`. When an upgrade
  interval includes both actions, apply this final bootstrap form directly;
  retain only the independent `SEM006` reconciliation from the older action.

#### PBB-MIG-0.5.0-03 — Exact repeated and collection artifacts

- **Condition:** an idempotency test invokes only prearranged final state,
  weakens the first/terminal artifact to count/type fragments, or a collection
  assertion converts to a set and loses duplicate multiplicity.
- **Action:** perform the promised first and second invocations with the same
  contractual identity, compare the complete first and terminal outcomes, and
  prove exact artifact content/cardinality with ordered equality or one-to-one
  unordered matching.
- **Do not:** infer idempotency, add a third call, or manufacture ordering when
  only multiplicity is contractual.
- **No-op when:** repetition and every collection already preserve the complete
  contract and exact multiplicity.

#### PBB-MIG-0.5.0-04 — Handler, batch, and rendered outcome completeness

- **Condition:** a registered handler or continuing batch operation omits a
  distinct observable no-op/stale/mismatch/prerequisite/mixed outcome from a
  contractually reachable or explicitly tolerated state, an
  application-owned dependency partial-error mapping is untested, or an SSR
  primary case omits relevant echoed/action/control/result fields.
- **Action:** confirm the authoritative meaning of each candidate outcome, add
  only the missing confirmed cases, configure dependency partial responses
  through the selected domain Service or real protocol path, compare exact
  partition multiplicity, and parse the complete relevant application-owned
  rendered state. Record or ask about an undocumented source-only candidate.
- **Do not:** mirror private branches that collapse to an existing outcome,
  freeze current source behavior as expected truth, patch a production client,
  snapshot framework markup, or test SDK reliability.
- **No-op when:** every distinct direct response/settlement/state/message/object
  artifact and mixed partition is already protected.

#### PBB-MIG-0.5.0-05 — Dispatch completion and rejection safety

- **Condition:** an async-dispatch API test races an immediate collector read,
  sleeps/polls for a message, inspects a private task registry, or a mutating
  validation boundary can return the right rejection while still creating a
  direct artifact with no focused case capable of detecting it.
- **Action:** bind observation before invocation and synchronize through awaited
  broker acceptance, a public queued-task artifact, or another supported
  deterministic completion boundary; add one focused rejection-safety artifact
  case where the contract requires side-effect-free rejection.
- **Do not:** run the downstream worker in the API test, add elapsed waits,
  duplicate artifact checks across every invalid parameter row, or expose a
  test-only completion hook.
- **No-op when:** dispatch observation has a supported deterministic boundary
  and rejected input cannot silently create the protected direct artifact.

## [0.4.0] - 2026-08-30

### Added

- `DEP001` deterministic diagnostics for broad or sibling test support importing
  an implementation from a narrower `test_*` group.
- `FIX005` deterministic diagnostics for public capability fixtures that mutate
  repository state directly instead of consuming a private baseline context or
  leaving a special transition visible in test arrange.
- `test_concurrency` adaptive project choice, disabled by default.
- Explicit idempotency contract rules and the `test_idempotency.py` category.
- `test_topology.py` guidance for selected worker declaration and consumer
  registration contracts.
- `SEM006` semantic scenario-completeness reconciliation and conditional
  `SEM007` concurrency review.

### Changed

- Test-owned protocol outcomes are explicitly minimal projections of the
  current public contract: mutually exclusive immutable variants, zero-field
  success markers when appropriate, and no speculative SDK metadata.
- Protocol support now distinguishes generic `Transport`, accepted
  `Connection`, and functional `Client` roles; public fixture names describe the
  actual returned capability.
- Child-specific fixture composition belongs to the narrowest owning group,
  while revoked/expired/deleted/pending and other special states stay visible in
  the test arrange phase.
- `SEM005` now reconciles WebSocket outcome minimality, layer ownership, and
  fixture locality in addition to operation and lifecycle coverage.
- The `audit` workflow now treats operation census and scenario/outcome
  completeness as two separate mandatory semantic reconciliations.
- Policy parsing now rejects unknown `[tool.pytest-blackbox]` keys so a typo
  cannot silently activate a default.
- Discovery refreshes preserve already recorded project-wide choices in the
  proposed patch instead of silently proposing onboarding defaults again.
- Generic Testcontainers imports remain a manual internal-vs-external
  classification in every mode; `mixed` no longer silently treats them as
  external mock servers.
- Policy parsing now fails closed for unreadable/malformed TOML and rejects
  wrong scalar types without crashing or accepting boolean/float config
  versions.
- Discovery refreshes preserve generalized coverage rules in the rendered TOML
  proposal.
- Discovery with an invalid recorded policy now withholds a replacement patch
  instead of resetting unrelated valid project choices to inferred defaults.
- Discovery rejects missing or non-directory project roots instead of proposing
  onboarding configuration for a mistyped path.
- Explicit concurrency cases use independently committing transactions plus
  deterministic committed-state cleanup instead of the ordinary shared
  rollback transaction.
- The fallback checker resolves ordinary import aliases for banned calls,
  rejects obvious concurrent public invocations when concurrency is disabled,
  enforces the selected custom generator backend facade, and finds scheduler or
  worker surfaces in preserved layouts.
- Coverage rules now require strict keys, a rationale, and unique generalized
  selectors; rendered refresh proposals retain the complete registry.
- Validation treats registered discriminators like enums, so a broader schema
  string bound does not fabricate successful rows for unsupported operations.
- Toolchain declaration checks require the `tomli` backport only on Python
  versions that actually need it.

### Existing-project actions

These actions are conditional and idempotent. They prepare existing projects
for the next minor release; the configuration schema remains at
`config_version = 1`.

#### PBB-MIG-0.4.0-01 — Test-support dependency direction

- **Condition:** a broad surface or sibling test module imports a functional
  adapter from a narrower `test_*` component.
- **Action:** keep the generic mechanism at the broad layer and move the
  child-specific adapter fixture to the narrowest common owning `conftest.py`.
- **Do not:** promote child route/discriminator defaults into shared support or
  make a parent fixture import a child implementation.
- **No-op when:** every test-support import points broad-to-narrow toward its
  consumer and component composition is already local.

#### PBB-MIG-0.4.0-02 — Stable capability fixtures

- **Condition:** a public client/transport/worker/runner/publisher/collector/
  scheduler/job fixture directly mutates a repository.
- **Action:** move baseline actor/session/resource creation to a private cohesive
  typed context consumed by the capability fixture. For revoked, expired,
  deleted, pending, blocked, or another case-specific state, expose the known
  identifier and arrange the transition visibly through a semantic repository
  method in the test.
- **Do not:** replace visible arrange with a family of state-named client
  fixtures or re-query storage for an identifier already prepared by context.
- **No-op when:** capability fixtures are stable and special state transitions
  are already visible in each owning case's arrange phase.

#### PBB-MIG-0.4.0-03 — Minimal protocol outcomes and role names

- **Condition:** a test-owned protocol result contains unused/future optional
  fields, combines mutually exclusive shapes into a nullable bag, or layers
  multiple vaguely named clients.
- **Action:** retain only current contractual fields, use separate frozen
  variants plus a union alias, use a zero-field success marker when the contract
  returns no success data, and distinguish Transport/Connection/functional
  Client roles. Rename public fixtures to match the capability they return.
- **Do not:** copy all metadata exposed by the underlying SDK, invent future
  contract fields, or create a third class for a union alias.
- **No-op when:** protocol projections are already minimal and layer/fixture
  names communicate their real roles.

#### PBB-MIG-0.4.0-04 — Concurrency coverage choice

- **Condition:** `[tool.pytest-blackbox]` does not record the concurrency D
  choice.
- **Action:** ask whether the suite intentionally tests explicit concurrency
  guarantees and add `test_concurrency = false` by default or `true` when
  confirmed.
- **Do not:** infer opt-in from async code, locks, transactions, requirements
  prose, or existing sequential repetition tests.
- **No-op when:** the boolean choice is already recorded.

#### PBB-MIG-0.4.0-05 — Explicit idempotency contracts

- **Condition:** repeated-operation tests claim idempotency or duplicate
  delivery without an authoritative promise, stable identity, complete first
  result, second terminal result, or positive non-duplication artifact.
- **Action:** remove unsupported repetition or move the cohesive promised matrix
  to `test_idempotency.py` and prove exact artifact cardinality after two calls.
- **Do not:** infer idempotency from implementation guards, deterministic IDs,
  unique constraints, or empty dead-letter queues.
- **No-op when:** every repeated case cites and proves its exact contract.

#### PBB-MIG-0.4.0-06 — Worker topology and semantic completeness

- **Condition:** either worker runtime/registration is selected but its actual
  declaration, binding, QoS, or handler registration is unproved, or audit
  evidence maps only operations/files without their distinct public scenarios
  and outcomes.
- **Action:** for the first condition, add deterministic `test_topology.py`
  coverage through the actual production composition seam. Independently, for
  the second condition, reconcile `SEM006` against collected cases. Apply only
  the branch whose condition is present.
- **Do not:** start a live waiting consumer, test broker reliability, duplicate
  topology in a parallel oracle, or treat a green primary contract as scenario
  completeness.
- **No-op when:** selected topology and every public-contract scenario map to
  concrete collected evidence; generalized decisions cover only non-contract
  surfaces and the recorded concurrency boundary.

#### PBB-MIG-0.4.0-07 — Strict policy keys

- **Condition:** `[tool.pytest-blackbox]` contains an unknown or misspelled key.
- **Action:** correct the key to the documented schema or remove obsolete local
  metadata that is not a supported project-wide choice.
- **Do not:** preserve an ignored typo for compatibility or move arbitrary
  implementation details into another pytest-blackbox key.
- **No-op when:** the policy table contains only documented keys.

#### PBB-MIG-0.4.0-08 — Strict generalized coverage registry

- **Condition:** a `[[tool.pytest-blackbox.coverage]]` rule lacks a non-empty
  rationale, contains an unsupported key, or repeats a selector already present
  in the registry.
- **Action:** add the confirmed project-level rationale, remove unsupported
  metadata, and merge duplicate selectors into one unambiguous generalized
  decision after asking when their decisions conflict.
- **Do not:** invent rationale text, silently choose between conflicting
  decisions, or replace the generalized registry with per-operation entries.
- **No-op when:** every selector is unique and every rule contains only
  `selector`, `decision`, and a confirmed non-empty `rationale`.

## [0.3.0] - 2026-08-28

### Added

- First-class WebSocket contract guidance: route-level handshake/lifecycle,
  independently invokable message discriminators, required continuation and
  close outcomes, natural typed handshake results, and deterministic in-process
  task/event completion.
- Behavior-derived category naming: `test_business_logic.py` is reserved for
  actual business behavior, while other cohesive contract aspects use precise
  names. `test_connection.py` is the recommended WebSocket route example.
- `SEM005` manual audit reconciliation for detected WebSocket surfaces.
- `WS001` deterministic diagnostics for expected handshake denials expressed as
  `pytest.raises` around an empty accepted-session context.

### Changed

- Documentation-only endpoints and generated OpenAPI/Swagger/schema artifacts
  are explicitly outside the product contract suite.
- Removed `VAL002`. A test-only AST cannot reliably distinguish an enum-only
  matrix from an incomplete non-enum matrix; semantic review owns that decision,
  while enums intentionally test every allowed member without a randomized row.
- Expanded `STR003` from `test_success.py` to other vague standard-layout
  categories such as `test_happy_path.py`, `test_behavior.py`, and
  `test_technical.py`; the diagnostic asks for the public behavior instead.
- Shared-support dependency direction now covers hardcoded route,
  discriminator, topology, and expected literals in addition to imports.
- Prepared typed contexts retain stable identifiers needed by later arrange
  steps, and state helpers belong to the repository owning the mutated state.

### Existing-project actions

These actions are conditional and idempotent. They migrate existing projects
to `0.3.0`; the configuration schema remains at `config_version = 1`.

#### PBB-MIG-0.3.0-01 — WebSocket operation matrix

- **Condition:** the project has a functional WebSocket surface.
- **Action:** inventory the route handshake/lifecycle separately from every
  independently invokable client-message discriminator. Give each identity an
  unambiguous terminal component, and add only currently required denial,
  frame, close, continuation, and direct artifact outcomes.
- **Do not:** derive requirements from Swagger/OpenAPI prose, mirror internal
  exception branches, add sleeps/timeouts, or test future documented behavior
  that is not yet a functional requirement.
- **No-op when:** the project has no WebSocket surface or its existing matrix
  already satisfies these boundaries.

#### PBB-MIG-0.3.0-02 — Natural handshake outcomes

- **Condition:** an expected WebSocket handshake denial is asserted through a
  custom/third-party exception and an empty `async with ...: pass` block.
- **Action:** normalize the documented denial in the test-owned client to an
  immutable typed result and compare it directly. Keep an accepted-session
  context manager for post-upgrade tests. When awaiting wire output, race it
  against completion of the application/runner task and propagate the original
  task exception if it finishes first.
- **Do not:** convert unexpected application/support failures to values,
  swallow tracebacks, add a wall-clock timeout, or open a localhost socket.
- **No-op when:** denial is already a natural value and the harness already
  observes both protocol output and task completion.

#### PBB-MIG-0.3.0-03 — Shared transport and prepared-state ownership

- **Condition:** shared support hardcodes a child route/discriminator/topology
  literal, or a repository scans storage to recover a known identifier and then
  mutates state owned by another repository.
- **Action:** make generic transports accept component-owned values explicitly;
  put defaults in the narrow functional adapter. Preserve required identifiers
  in the original typed preparation context and pass them to the repository
  that owns the next mutation.
- **Do not:** promote component literals to root constants, rediscover known
  state through storage, or create a generic catch-all repository.
- **No-op when:** dependency direction and state ownership are already clean.

#### PBB-MIG-0.3.0-04 — Documentation-only tests

- **Condition:** the product contract suite contains tests whose sole subject is
  a documentation/schema-only endpoint or generated OpenAPI/Swagger output.
- **Action:** remove those tests and their terminal component from the product
  contract matrix.
- **Do not:** remove the documentation itself or omit a functional endpoint
  merely because it is also documented.
- **No-op when:** the suite contains no documentation-only contract tests.

#### PBB-MIG-0.3.0-05 — Newly discovered runtime surface classes

- **Condition:** the change discovers an unclassified non-contract runtime
  surface such as observability bootstrap and no generalized coverage rule
  applies.
- **Action:** ask once for `exclude`, `focused`, or `standard` depth and record a
  generalized selector/rationale only after confirmation.
- **Do not:** create per-function or per-operation registry entries, infer a
  decision from installed dependencies, or unit-test an SDK by default.
- **No-op when:** an existing generalized rule already covers the surface.

#### PBB-MIG-0.3.0-06 — Behavior-derived category names

- **Condition:** `test_business_logic.py` contains a non-business contract
  aspect, or another category has a generic success/technical name that hides
  what it proves.
- **Action:** choose a concise filename for the cohesive public behavior. Keep
  `test_business_logic.py` only for business rules/domain outcomes; prefer
  `test_connection.py` for a route-level WebSocket contract, while command
  components choose names from their own behavior.
- **Do not:** create a file per case/parameter/outcome, invent synonyms for
  established access/validation/error/metrics categories, or create empty
  category files.
- **No-op when:** filenames already describe their behavior unambiguously, or a
  deliberately preserved mature layout has a clear equivalent.

## [0.2.0] - 2026-08-24

### Added

- A dedicated `lint` workflow for deterministic policy diagnostics without a
  semantic completeness claim.
- Ruff-like concise output and stable JSON output for `lint_suite.py` and
  `audit_suite.py`.
- `auto`, `fallback`, and `enhanced` analysis modes for discovery, lint, and
  audit.
- An opt-in enhanced toolchain using Ruff, Packaging, PathSpec, TOMLKit, and a
  conditional TOMLI compatibility dependency on Python 3.10.
- Explicit `SEM001` through `SEM004` semantic review items in the audit layer.

### Changed

- `audit_suite.py` now composes deterministic diagnostics with a separate
  semantic-review section; `SEM*` checks were preserved rather than converted
  into static rules.
- Compatible syntax, pytest, banned-time, event-loop, and SQLAlchemy Session
  rules are delegated to Ruff in enhanced mode. Cross-file and
  project-specific rules remain in the bundled checker.
- Discovery remains read-only but gains library-backed dependency parsing,
  package-manager evidence, and gitignore-aware evidence in enhanced mode.
- Managed analysis dependencies are installed only after explicit onboarding
  consent and only in the configured dedicated dependency group.

### Existing-project actions

These actions are deliberately conditional. Reapplying them to an already
updated project must be a no-op.

#### PBB-MIG-0.2.0-01 — Optional enhanced analysis

- **Condition:** the user explicitly opts in to managed Pytest Blackbox
  dependencies.
- **Action:** add `dependency_group = "dev-ai"` (or a confirmed existing
  dedicated AI/tooling group) under `[tool.pytest-blackbox]`, then install the
  exact baseline from `references/tooling.md` with the project-native package
  manager.
- **Do not:** infer consent from existing tools, duplicate compatible packages
  already declared elsewhere, or modify runtime/general development groups.
- **No-op when:** `dependency_group` is absent because the user declined or has
  not decided; fallback remains supported.

#### PBB-MIG-0.2.0-02 — Auditor output consumers

- **Condition:** project automation parses the pre-0.2 human-readable auditor
  output.
- **Action:** switch machine consumers to `--output-format json`, whose root
  fields are `mode`, `diagnostics`, `semantic`, and `summary`.
- **Do not:** parse the new concise human format when structured output is
  available.
- **No-op when:** the auditor is invoked only by a person or coding agent.

#### PBB-MIG-0.2.0-03 — Deterministic-only checks

- **Condition:** an existing local workflow needs fast mechanical policy
  diagnostics and must not claim contract coverage completeness.
- **Action:** call `lint_suite.py`; keep `audit_suite.py` wherever `SEM*`
  reconciliation or full semantic coverage is required.
- **Do not:** replace a semantic audit with lint.
- **No-op when:** existing automation intentionally runs the full audit.

No production or test-source refactor is required solely to upgrade to 0.2.0.
The project configuration schema remains at `config_version = 1`.

## [0.1.2] - 2026-08-23

### Changed

- Pinned the Codex and Claude Code marketplace catalogs to the immutable
  `v0.1.2` release tag.
- Documented GitHub-only installation and update commands.

### Existing-project actions

No project-file migration was required.

## [0.1.0] - 2026-08-23

### Added

- Initial Codex and Claude Code plugin packaging for the `discover`, `write`,
  `repair`, `review`, and `audit` workflows.
- The shared black-box pytest policy, project onboarding, fallback discovery,
  and deterministic auditor.

[Unreleased]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/ave-satan/pytest-blackbox-skill/compare/v0.1.0...v0.1.2
[0.1.0]: https://github.com/ave-satan/pytest-blackbox-skill/releases/tag/v0.1.0
