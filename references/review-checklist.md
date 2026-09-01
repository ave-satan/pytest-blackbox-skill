# Review checklist

Use this after reading the task-relevant references. Mark mechanically proven M violations as errors, departures from non-binding D recommendations as warnings, active D-policy drift as errors, and semantic uncertainty as manual review.

## Project policy

- Is the nearest applicable `[tool.pytest-blackbox]` present or has temporary policy been explicitly confirmed?
- Does code agree with active layout, infrastructure, Compose, external-service, TestClass, and generator-backend choices?
- Does code agree with the active `test_concurrency` choice, with concurrency absent by default and independently committing transactions used when enabled?
- If managed dependencies are enabled, does the dedicated AI/tooling group supply the baseline enhanced toolchain while treating compatible declarations elsewhere as satisfied, with only concrete missing packages installed through the project package manager and no duplicate, unrelated upgrade, runtime/general-dev fallback, or hand-edited lockfile?
- Does the coverage registry contain only generalized non-contract surface decisions, never public operations or per-operation entries?
- For a mature suite, were legacy violations reported without an unauthorized broad refactor?

## Contract boundary and coverage

- For an application-development task, was the complete scoped contract/scenario matrix written before production behavior changed, and was a meaningful red run classified before implementation?
- Did red fail on the missing/wrong contract rather than fixture, environment, syntax/import, or oracle defects; if tests unexpectedly passed, was weak/already-existing behavior investigated before production edits?
- If collection failure, `404`, or another registration-only outcome masked the whole new matrix, was only the approved real registration skeleton added and a second assertion-level red obtained before behavior implementation?
- Was the whole scoped matrix implemented cohesively, followed by focused green, deterministic lint, semantic audit/reconciliation, and broader checks; after refactoring, were affected checks rerun, and was pure refactoring handled with green-before/after instead of an artificial red?

- Does each test enter through a supported application/job/worker/message boundary and avoid implementation handlers/state/registries/codecs/constants?
- Are input/action and expected truth independently expressed rather than built through production DTO/schema/default/validation/serialization?
- For configuration-controlled behavior, are explicit test-owned overrides and expected outcomes paired independently instead of reading expected truth from production `Settings` or defaults?
- Is every public product HTTP/JSON-RPC/WebSocket operation and registered job/scheduler/handler independently covered, while documentation-only endpoints and generated API docs stay outside the contract suite?
- Was the final framework registration/action table inspected so synthesized confirmation/rendering GETs, mutating POSTs, mounted actions, and other method-specific functional routes were inventoried separately?
- Was a transient contract-evidence matrix reconciled against collected nodes, including every operation matched by a `focused` rule and every application-owned observable outcome class?
- After the final case set was known, were names reconciled bottom-up so every category filename truthfully covers all contained cases and every terminal component still maps one-to-one to its public operation/component? Were stale historical names renamed or coherently split instead of receiving convenient unrelated additions?
- Was scenario completeness checked semantically from authoritative requirements plus source behavior, including reachable/tolerated state partitions, compound ownership/isolation dimensions, boundaries, terminal/no-op/stale outcomes, mixed batch partitions, and direct artifacts—without manufacturing corrupt states or relying only on component/file presence? When ownership affects selection/access, does each operation cover the same resource owned by another principal?
- Is ordinary HTTP identity method + path, JSON-RPC identity HTTP method + RPC method, and WebSocket identity route lifecycle or route + contractual subprotocol/discriminator?
- Do WebSocket tests keep handshake denials as values, prove required non-terminal continuation and close outcomes, avoid empty connection contexts whose body is only `pass`, and propagate unexpected application-task failures without timeout waits?
- Does the route-level WebSocket component use a clear connection/lifecycle category—preferably `test_connection.py` in the standard layout—while independently invokable message commands choose categories by their own behavior?
- Are WebSocket outcome variants immutable, mutually exclusive, and limited to current contractual fields, using a zero-field accepted marker when success carries no data?
- Does an async-dispatching API test stop at response + queued artifact, leaving execution to a separate worker contract, and use a supported deterministic completion boundary instead of racing later fire-and-forget work?
- Are shared worker/runtime contracts tested once and kept distinct from handler contracts?
- Are non-contract surfaces classified by the generalized registry before scope expands?
- Is there one primary full contract plus every applicable category, with domain-state rejection owned by `test_business_logic.py`, transport/dependency/operational failures owned by `test_errors.py`, and any other cohesive aspect given a concise behavior-specific name that remains true for its complete current case set?
- Does each primary contract exact-compare the complete stable public response/value, including unchanged fields returned by partial updates?
- Are runtime legacy-format/backward-compatibility cases present only for an authoritative product/operational promise, named and asserted as preserved public behavior through repositories/builders rather than as a conversion/migration implementation? Are database schema migrations still checked only by suite bootstrap/reversal?
- Does every repeated public invocation cite an explicit authoritative repetition contract rather than infer idempotency/retry from implementation or naming?
- Does each idempotency case use the same contractual identity, exactly two calls unless another phase is promised, a complete first result, the promised second terminal result, and positive exact evidence that direct artifacts were not duplicated, rather than one call against prearranged final state?
- Is a cohesive idempotency matrix named `test_idempotency.py` rather than hidden in generic business logic?
- Does every registered scheduler test observe the actual callback/trigger registration without a live-clock race?
- If worker settlement is selected, does success have a positive acknowledgement/non-redelivery artifact rather than only an empty rejected queue?
- Is broker topology absent from the operation matrix and collected test surface, including files/components named `test_topology` or equivalent?
- Are health checks opt-in and limited to application-owned operational mapping?

## Cases and assertions

- Does each collected test contain one complete behavioral case and normally one tested invocation?
- Are arrange, invocation, and assertions visible in ordinary functions?
- If TestClass is used, does it group several complete cases for safe performance reuse without splitting one case across methods or sharing mutable case state?
- Do parameter rows contain values/expected values or uniform arrange-time factories with explicit readable IDs?
- Are fresh time/UUID/generated values created during arrange rather than collection?
- Is the general case complete, with edge cases asserting only the changed fact?
- Do collection assertions preserve exact cardinality and duplicate multiplicity instead of hiding duplicates with a set conversion?
- For rendered HTML/SSR, are all relevant application-owned view fields, echoed identifiers, action/CSRF state, and result/error partitions covered without snapshotting dependency-generated markup?
- Are separately bound results named `actual`/`actual_*` and expectations `expected`/`expected_*`?
- Do assertions start with native Python equality/operators—ordinary dictionaries/lists, `len`, membership, and comprehensions—and use a matcher only when it adds contract semantics or materially clearer diagnostics?
- Are compound values compared whole and independent observations kept separate without a manufactured aggregate?
- Is partial structural comparison limited to a focused variation/edge case whose remainder is already protected or an intentionally extensible natural container whose declared subset is the complete application-owned contract? Does its public matcher name expose partiality without a boolean mode, and does it receive the complete observed compound value and require every declared element without deleting, merging, or overwriting ignored values? If a list comprehension projects one ordered scalar property, are complete item contracts protected elsewhere and is that projection itself the focused case? If normalization is necessary, is the complete natural container and contractual multiplicity preserved while closed primary values remain exact?
- Does every assertion remain an explicit `assert`, with builders/matchers rather than assertion helpers?
- Is `pytest.raises` limited to naturally exception-based public boundaries, with wire errors kept as values and unexpected tracebacks preserved?

## Validation and performance doubles

- Does validation vary one field at a time, except contractually related fields?
- Does every validated field/relationship use separate homogeneous `*_accepted` and `*_rejected` parametrized functions, with fixed outcome assertions and no parametrized status, nullable error sentinel, or accepted/rejected branch?
- Do non-enum fields cover an ordinary valid value when appropriate, valid boundaries, nearest invalid values, and representative invalid shapes, while enums/registered discriminators cover every publicly allowed member plus an invalid member without fabricated successful rows from a broader schema representation?
- Does validation assert only acceptance/rejection and validation error rather than repeat downstream business artifacts, with at most one focused rejection-safety case when rejected input must not produce a direct effect?
- If a performance double is used, is it injected through a supported seam, unrelated to the asserted artifact, backed by real-path coverage, semantically removable except for cost, typed/reset, and free of internal call assertions?

## Fixtures and composition

- Does every `conftest.py` contain only fixtures/hooks/plugin registration, with root fixtures registered from focused modules?
- Do local conftests delegate raw SDK topology/runtime/cleanup algorithms to ordinary modules?
- Does one private session/autouse messaging fixture invoke the real production topology bootstrap before any broker-dependent fixture, propagate bootstrap errors unchanged, avoid a duplicate expected topology model or broker-state comparison, and leave no extra consumer competing with test workers?
- Are fixture-only dependencies private and absent from test signatures?
- Are cleanup and ordering explicit, with no meaningless `del` or pass-through fixture aliases?
- Does shared support avoid imports and hardcoded route/discriminator/topology/expected literals from narrower or sibling test groups and unsupported production internals?
- Do all public domain-facing support classes, fixtures, and methods start from the shortest canonical owner-relative operation and add only the qualifier needed to distinguish siblings, without mechanically repeating the owner noun? Do names truthfully describe their result and cardinality, keep technical storage/transport/discriminator/caller/optimization details private, and leave intentionally generic structural/protocol primitives precisely named at their actual abstraction level without child-domain defaults?
- Does every shared/public support object avoid another support object's private members, exposing a narrow truthful public capability or aggregate owner instead of crossing the underscore boundary or exchanging raw storage references?
- Does every broad-to-narrow import point toward the consumer, with child-specific fixture composition kept in the child's nearest `conftest.py`?
- Are immutable factories/bootstrap widest-safely-scoped while transactions, actors, credentials, clients, messages, and case state remain function-scoped?
- Are known prepared entities, credentials, identifiers, and resource handles reused through typed contexts rather than rediscovered?
- Is base configuration immutable/session-scoped and every behavior-affecting case override explicit before startup?
- Is base configuration recursively immutable or case-derived with a verified deep copy?
- Do public client/runner fixtures hide raw SDK, runtime, broker topology, Publisher/DeliverySource, and production worker fields behind domain methods?
- Do public capability fixtures compose only stable machinery/baseline identity, while revoked/expired/deleted/pending and other case states are visibly arranged through repositories?
- Are fixture names as specific as their returned capability, and are protocol layers clearly distinguished as Transport, Connection, and functional Client where all three exist?
- Are generated UUID/time/payload/domain values ordinary arrange-time calls rather than value-only fixtures?
- Does a pytest-asyncio suite use exactly one pytest-managed session loop; does another async backend own one coherent native runtime without mixed asyncio loops; and does a synchronous project remain synchronous?
- Are HTTP requests in-process and authorization clients prepared without login/setup endpoints?

## Repositories and generated data

- Do tests use repositories for addressable stored state and never raw DB/cache/object/search clients or ORM sessions?
- Do ordinary SQLAlchemy repositories use matching sync/async `Connection` statement APIs and share the application's outer transaction, while enabled concurrency cases use separately named committed-state repositories without exposing raw connections?
- Does `create` build the minimally valid object, with optional fields omitted and semantic constructors for recurring states?
- Was repository minimality checked against the real storage/resource contract, and do file/object `create` methods generate ordinary valid key/body defaults?
- Does `create_many` build fresh values then execute one bulk write?
- Do aggregate/domain bulk constructors delegate to bulk primitives instead of looping over single creates?
- Are repository methods minimal, canonically and owner-relatively named, strict about cardinality, filterless by default in a clean case, and owned by the state they mutate rather than a neighboring state used to rediscover its identifier? Does the public base CRUD method remain available alongside semantic variants?
- Do specialized repository operations name the actual created/read/updated/deleted domain target or state, keep singular/plural cardinality truthful, avoid naming an owner argument or persisted implementation discriminator as the result, and use consistent vocabulary across aggregate and lower-level repositories?
- Does coherent multi-store work live in a narrow aggregate repository, while queues use Publishers/Collectors?
- Are independently meaningful existence states separate domain methods?
- Do structured reusable results cross support boundaries as typed immutable values, while natural JSON/mapping/scalars remain natural?
- Do tests use the project generator facade, random logged seed with explicit replay, and in-constraint values?
- Do file contracts use builders that derive success/boundary/error variants, with real files only as templates?
- Do matcher constraints avoid finite sentinels for unbounded domains?
- Are exact mappings/lists and simple length/membership checks expressed natively, with `OrderedList` reserved for contractual order plus useful matcher composition/diagnostics, and one-field ordered projections expressed as ordinary list comprehensions rather than lists of partial element matchers?

## Infrastructure, messaging, and time

- Are real protocol-compatible internal dependencies reduced only by unobservable reliability guarantees?
- Does the selected infrastructure/Compose/Testcontainers policy match `pyproject.toml`?
- Are isolated database/vhost/bucket/namespace resources created programmatically, uniquely named, and always removed?
- Are migrations upgraded and their complete configured reverse lifecycle run in process, with reversal failures or unsupported irreversible migrations reported visibly even while cleanup continues?
- Does messaging teardown delete the isolated namespace/resources without invoking or testing inverse production topology declarations?
- Does every ordinary DB case use one rollback transaction, with savepoint opt-in only when an expected production rollback can invalidate it, and do enabled concurrency cases instead use independently committing participants plus deterministic committed-state cleanup?
- Is savepoint selection absent from the general binding path and activated only by the explicit opt-in composition?
- Are Publisher/Collector/DeliverySource roles distinct, domain-named, test-owned in wire encoding, deterministic, exact-cardinality, no-wait, and fully cleaned?
- Do outbound systems use isolated domain Services over the selected external backend policy? In `mixed` mode, is each integration's backend stable across the suite and hidden behind the same Service API?
- When application code maps per-item dependency errors, does the Service or real protocol-compatible path cover homogeneous and mixed responses with exact multiplicity, without patching the production client or retesting SDK reliability?
- Are retries/backoff disabled, timeout failures immediate, messaging waits absent, and `sleep` banned everywhere?
- Is bounded immediate polling limited to non-messaging artifacts with no deterministic completion signal?
- Are timestamps/deadlines/TTL checked against real invocation bounds and documented resolution without time freezing or arbitrary slack?

## Audit result

- Did a focused write/develop/repair/component-lint pass use repeatable `--scope` for the complete owning component and every changed shared-support path, while a promised whole-suite audit remained unscoped?
- Did `scripts/lint_suite.py` run successfully, and did `scripts/audit_suite.py` preserve and reconcile every applicable semantic item including the explicit operation-and-scenario completeness checks in `SEM001`/`SEM006`?
- Were warnings and manual-review items evaluated rather than ignored?
- For a large full-suite audit, were independent surfaces optionally delegated while the primary agent retained census/policy/reconciliation?
- Does the report name coverage boundary, exclusions, changed files, commands, pass counts, known legacy M violations, and blockers?
