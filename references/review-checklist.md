# Review checklist

Use this after reading the task-relevant references. Mark mechanically proven M violations as errors, departures from non-binding D recommendations as warnings, active D-policy drift as errors, and semantic uncertainty as manual review.

## Project policy

- Is the nearest applicable `[tool.pytest-blackbox]` present or has temporary policy been explicitly confirmed?
- Does code agree with active layout, infrastructure, Compose, external-service, TestClass, and generator-backend choices?
- Does the coverage registry contain only generalized non-contract surface decisions, never public operations or per-operation entries?
- For a mature suite, were legacy violations reported without an unauthorized broad refactor?

## Contract boundary and coverage

- Does each test enter through a supported application/job/worker/message boundary and avoid implementation handlers/state/registries/codecs/constants?
- Are input/action and expected truth independently expressed rather than built through production DTO/schema/default/validation/serialization?
- Is every public HTTP/JSON-RPC operation and registered job/scheduler/handler independently covered?
- Was a transient contract-evidence matrix reconciled against collected nodes, including every operation matched by a `focused` rule and every application-owned observable outcome class?
- Is ordinary HTTP identity method + path and JSON-RPC identity HTTP method + RPC method?
- Does an async-dispatching API test stop at response + queued artifact, leaving execution to a separate worker contract?
- Are shared worker/runtime contracts tested once and kept distinct from handler contracts?
- Are non-contract surfaces classified by the generalized registry before scope expands?
- Is there one primary full contract plus every applicable access/validation/error/business/metrics category?
- Does each primary contract exact-compare the complete stable public response/value, including unchanged fields returned by partial updates?
- Does every repeated public invocation cite an explicit authoritative repetition contract rather than infer idempotency/retry from implementation or naming?
- If scheduler registration is selected, does the test observe the actual registered callback/trigger without a live-clock race?
- If worker settlement is selected, does success have a positive acknowledgement/non-redelivery artifact rather than only an empty rejected queue?
- Are health checks opt-in and limited to application-owned operational mapping?

## Cases and assertions

- Does each collected test contain one complete behavioral case and normally one tested invocation?
- Are arrange, invocation, and assertions visible in ordinary functions?
- If TestClass is used, does it group several complete cases for safe performance reuse without splitting one case across methods or sharing mutable case state?
- Do parameter rows contain values/expected values or uniform arrange-time factories with explicit readable IDs?
- Are fresh time/UUID/generated values created during arrange rather than collection?
- Is the general case complete, with edge cases asserting only the changed fact?
- Are separately bound results named `actual`/`actual_*` and expectations `expected`/`expected_*`?
- Are compound values compared whole and independent observations kept separate without a manufactured aggregate?
- Does every assertion remain an explicit `assert`, with builders/matchers rather than assertion helpers?
- Are expected exceptions checked with `pytest.raises`, and unexpected tracebacks preserved?

## Validation and performance doubles

- Does validation vary one field at a time, except contractually related fields?
- Does each field cover an ordinary valid value, valid boundaries, nearest invalid values, representative invalid shapes, every enum member, and an invalid enum member?
- Does validation assert only acceptance/rejection and validation error rather than repeat downstream business artifacts?
- If a performance double is used, is it injected through a supported seam, unrelated to the asserted artifact, backed by real-path coverage, semantically removable except for cost, typed/reset, and free of internal call assertions?

## Fixtures and composition

- Does every `conftest.py` contain only fixtures/hooks/plugin registration, with root fixtures registered from focused modules?
- Do local conftests delegate raw SDK topology/runtime/cleanup algorithms to ordinary modules?
- Are fixture-only dependencies private and absent from test signatures?
- Are cleanup and ordering explicit, with no meaningless `del` or pass-through fixture aliases?
- Does shared support avoid imports from narrower/sibling test groups and unsupported production internals?
- Are immutable factories/bootstrap widest-safely-scoped while transactions, actors, credentials, clients, messages, and case state remain function-scoped?
- Are known prepared entities/credentials reused through typed contexts rather than rediscovered?
- Is base configuration immutable/session-scoped and every behavior-affecting case override explicit before startup?
- Is base configuration recursively immutable or case-derived with a verified deep copy?
- Do public client/runner fixtures hide raw SDK, runtime, broker topology, Publisher/DeliverySource, and production worker fields behind domain methods?
- Are generated UUID/time/payload/domain values ordinary arrange-time calls rather than value-only fixtures?
- Does an asyncio suite use exactly one pytest-managed session loop while a synchronous project remains synchronous?
- Are HTTP requests in-process and authorization clients prepared without login/setup endpoints?

## Repositories and generated data

- Do tests use repositories for addressable stored state and never raw DB/cache/object/search clients or SQLAlchemy sessions?
- Do SQLAlchemy repositories use sync/async `Connection` statement APIs matching the project and share the application's outer transaction?
- Does `create` build the minimally valid object, with optional fields omitted and semantic constructors for recurring states?
- Was repository minimality checked against the real storage/resource contract, and do file/object `create` methods generate ordinary valid key/body defaults?
- Does `create_many` build fresh values then execute one bulk write?
- Do aggregate/domain bulk constructors delegate to bulk primitives instead of looping over single creates?
- Are repository methods minimal, canonically named, strict about cardinality, and filterless by default in a clean case?
- Does coherent multi-store work live in a narrow aggregate repository, while queues use Publishers/Collectors?
- Are independently meaningful existence states separate domain methods?
- Do structured reusable results cross support boundaries as typed immutable values, while natural JSON/mapping/scalars remain natural?
- Do tests use the project generator facade, random logged seed with explicit replay, and in-constraint values?
- Do file contracts use builders that derive success/boundary/error variants, with real files only as templates?
- Do matcher constraints avoid finite sentinels for unbounded domains?

## Infrastructure, messaging, and time

- Are real protocol-compatible internal dependencies reduced only by unobservable reliability guarantees?
- Does the selected infrastructure/Compose/Testcontainers policy match `pyproject.toml`?
- Are isolated database/vhost/bucket/namespace resources created programmatically, uniquely named, and always removed?
- Are migrations upgraded and obligatorily downgraded in process, with downgrade failures visible even while cleanup continues?
- Does every DB case use one rollback transaction, with savepoint opt-in only when an expected production rollback can invalidate it?
- Is savepoint selection absent from the general binding path and activated only by the explicit opt-in composition?
- Are Publisher/Collector/DeliverySource roles distinct, domain-named, test-owned in wire encoding, deterministic, exact-cardinality, no-wait, and fully cleaned?
- Do outbound systems use isolated domain Services over the selected external backend policy? In `mixed` mode, is each integration's backend stable across the suite and hidden behind the same Service API?
- Are retries/backoff disabled, timeout failures immediate, messaging waits absent, and `sleep` banned everywhere?
- Is bounded immediate polling limited to non-messaging artifacts with no deterministic completion signal?
- Are timestamps/deadlines/TTL checked against real invocation bounds and documented resolution without time freezing or arbitrary slack?

## Audit result

- Did `scripts/audit_suite.py` run successfully?
- Were warnings and manual-review items evaluated rather than ignored?
- For a large full-suite audit, were independent surfaces optionally delegated while the primary agent retained census/policy/reconciliation?
- Does the report name coverage boundary, exclusions, changed files, commands, pass counts, known legacy M violations, and blockers?
