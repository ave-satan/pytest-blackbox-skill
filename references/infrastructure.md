# Infrastructure, messaging, and external systems

## Contents

- [Reliability boundary](#reliability-boundary)
- [Environment lifecycle](#environment-lifecycle)
- [Migrations and database transactions](#migrations-and-database-transactions)
- [Redis and object storage](#redis-and-object-storage)
- [Publishers and collectors](#publishers-and-collectors)
- [External HTTP Services](#external-http-services)
- [No sleeping, retries, or wall-clock waits](#no-sleeping-retries-or-wall-clock-waits)

## Reliability boundary

Use real local database, Redis, RabbitMQ, S3-compatible storage, and equivalent internal dependencies to execute application-owned code. Do not test dependency-owned durability, replication, quorum, HA, failover, backup/restore, capacity, load, restart persistence, generic ordering, or filesystem behavior. Dependency-owned topology is likewise outside scope. This does not exclude a deliberately selected application's own worker registration contract: [contracts.md](contracts.md) defines the narrow `test_topology.py` check for the production-declared exchange/queue/binding/QoS/handler choices.

Choose the cheapest supported test configuration that preserves every semantic visible to the application. Ephemeral/non-durable test databases, queues, caches, and buckets are preferred when the operation cannot observe the omitted guarantee. Never gain speed by patching application code, bypassing the adapter that produces the tested artifact, changing an application-owned declaration, or weakening assertions. A typed application-owned performance double is allowed only through a supported composition seam and only under the contracts-reference conditions.

Do not create infrastructure tests or a `test_infrastructure/` group. The application contract suite already exercises bootstrap, connectivity, migrations, configuration, and adapters through real dependencies; failures in those prerequisites fail the affected tests. Never duplicate that signal with tests whose subject is PostgreSQL, Redis, RabbitMQ, S3, migration execution, fixture bootstrap, transaction machinery, or an SDK.

Do not create a generic `test_application/` startup/smoke group either. Application startup is part of fixture bootstrap and must fail the suite directly. Minimal health/liveness/readiness probe checks are governed by the explicit operational exception in the contracts reference; they may validate application-owned readiness classification but never dependency reliability.

## Environment lifecycle

Select the environment policy during onboarding:

- `infrastructure = "existing-services"` is the default: connect to already available protocol-compatible service instances;
- an embedded/in-process or established project provider—including explicitly selected Testcontainers for internal services—is allowed when it preserves every application-visible semantic;
- `compose_lifecycle = "disabled"` is the default: pytest does not start/stop Docker Compose. A mature project may explicitly preserve its existing Compose lifecycle;
- `external_services = "testcontainers"` independently opts into Testcontainers-backed external mock servers; `external_services = "mixed"` permits interception for some external integrations and Testcontainers mock servers for others. Neither is blocked by the Compose setting. `infrastructure = "testcontainers"` is the separate choice for internal services. Container modes use the library/Docker API, not Compose.

Whichever policy is selected, test cases remain unaware of provisioning and the suite still owns isolated logical resources. Do not run service managers or ad-hoc shell scripts.

Create isolated logical resources through Python client/administrative APIs:

- unique test database;
- RabbitMQ vhost plus required credentials/permissions/exchanges/queues;
- S3-compatible bucket;
- Redis logical database or unique namespace/prefix;
- equivalent resources for every other shared service.

Resource names must be unique across concurrent runs and workers. Use a run identifier plus the pytest worker identifier where applicable; do not rely only on generated-data output or its seed. Derive application configuration automatically from these resources with no separate manual test config.

Bootstrap order:

1. connect to available service administration APIs;
2. create isolated logical resources;
3. build immutable session base settings;
4. apply all database migrations;
5. prepare shared broker/storage/cache primitives;
6. derive case settings/state;
7. start the function-scoped application.

Teardown reverses ownership safely in `yield`/`finally`: stop applications/background tasks, close clients/connections, reverse every migration, empty resources, then delete database, vhost, bucket, namespace, credentials, queues, keys, objects, and every created resource. A downgrade failure must remain a visible suite error while teardown still attempts resource removal; preserve both failures if cleanup also fails. Partial setup failures must still clean completed steps.

Keep reusable implementation in focused `tests/environment/database.py`, `migrations.py`, `redis.py`, `broker.py`, `storage.py`, and `settings.py`; keep fixture orchestration in `tests/fixtures/`.

Use Python/library/service APIs first. A subprocess is an opt-in last resort only after confirming no equivalent API exists. Localize it under `tests/environment/`, pass arguments without shell pipelines, validate exit status, return a typed result, guarantee cleanup, and report the exact limitation. Migrations never use this exception when the framework exposes an in-process API.

## Migrations and database transactions

Run migrations in process. For Alembic, use its Python command API:

```python
# tests/environment/migrations.py
from alembic import command
from alembic.config import Config


def upgrade_database(database_url: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def downgrade_database(database_url: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.downgrade(config, "base")
```

Invoke these operations from the session fixture owning the migrated database. Apply every migration before application startup; always run the complete configured downgrade at teardown, then delete the database. Do not swallow a downgrade failure: keep it as a visible suite error while still attempting resource cleanup. Do not call Alembic CLI/subprocess when its API works and do not add a standalone migration test—the suite bootstrap is the migration check.

After migrations, keep mutable application tables empty except explicitly permitted immutable migration-owned reference data.

Define one explicit private function-scoped transaction. Use `Connection` or `AsyncConnection` according to the project's concurrency model; the asynchronous shape is:

```python
@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def _database_transaction(_database_connection):
    transaction = await _database_connection.begin()
    try:
        yield _database_connection
    finally:
        await transaction.rollback()
```

In ordinary non-concurrency cases, every database-using application, HTTP client, job/consumer harness, and repository fixture depends on this exact fixture and shares the yielded `Connection`/`AsyncConnection`. Tests never request it directly. Test functions, fixtures, repositories, and environment helpers never import, construct, configure, or use `Session`, `AsyncSession`, `sessionmaker`, or `async_sessionmaker`.

An explicitly enabled concurrency contract is the narrow exception to the shared outer transaction: independently committing application transactions are required to make the race real. Keep the case in its own isolated logical state, create each participant through the normal production composition boundary, and let the owning fixture delete committed artifacts deterministically afterward. Do not share the ordinary outer transaction between participants, emulate concurrency with sequential calls, or weaken transaction rollback for unrelated tests. This exception exists only when `test_concurrency = true` and an authoritative contract requires the race.

In ordinary non-concurrency cases, all test-owned database operations execute SQLAlchemy `select()`, `insert()`, `update()`, or `delete()` statements on that connection. Do not use ORM unit-of-work methods, session queries, ORM relationship mutation, `flush`, or an independently opened engine/connection/transaction. Pass the connection through a production-owned composition hook/provider that makes the application's normal ORM sessions use the outer transaction. Test support passes only the connection; it never defines a test session factory or test-only ORM provider. If the application lacks this boundary, report it and request authorization for a general production composition seam. The explicitly enabled concurrency carve-out above instead owns its independent committed connections and deterministic cleanup through private repositories/fixtures; raw connections still never reach tests.

Provide an explicit opt-in savepoint-aware transaction fixture/marker for cases where the expected application path may roll back or invalidate its ORM transaction before returning control. The savepoint sits inside the normal function-scoped outer transaction, and production sessions plus repositories remain bound to that composition. After the application rolls back the savepoint, the outer transaction must remain usable for artifact inspection and teardown. Ordinary tests do not create a savepoint and pay no savepoint overhead. Test functions never manipulate the savepoint or raw connection directly.

Do not encode savepoints unconditionally in the general production-session binding used by all tests (for example a universal `join_transaction_mode="create_savepoint"`). The ordinary binding joins the outer test transaction without a savepoint; the explicit opt-in fixture/marker selects savepoint-aware composition only for cases that need rollback recovery. Verify both paths when adapting a production binding hook.

For ordinary cases, rollback restores the clean baseline after each test; an explicitly enabled concurrency case instead uses its fixture-owned deterministic committed-state cleanup. Do not truncate shared tables by default, leak state across tests, or rely on execution order.

## Redis and object storage

Use real isolated Redis/cache and S3-compatible resources. Expose case-level keys/objects through repository fixtures; tests never use raw clients. Keep per-case namespaces/prefixes function-scoped when practical and delete keys/objects during teardown. Delete enclosing session namespaces/buckets at suite teardown.

Treat Redis Pub/Sub/Streams as messaging, not cache repositories.

## Publishers and collectors

Keep handler contracts and shared worker/runtime contracts in different test components. A handler component publishes that handler's public input and asserts only its handler-specific response/artifacts. Cross-cutting envelope dispatch, unknown-message handling, acknowledgement/requeue/dead-letter policy, and other runtime behavior are tested once through a selected public worker boundary, never copied into every handler component. A runtime component is created only when that boundary is part of the agreed coverage scope; internal runtime mechanics otherwise remain implementation details.

Represent message transport by role under `tests/messaging/`:

- a domain `Publisher` sends the consumer's one public input through the real broker route;
- a domain `Collector` binds a test-owned queue/subscription before invocation and returns emitted public messages as artifacts.
- when the supported production worker boundary accepts a delivery rather than consuming from the route itself, a private `DeliverySource` retrieves one unacknowledged delivery for that harness; it is neither a Collector nor a test fixture API.

Name adapters by domain/channel plus role: `OrdersPublisher`, `BillingEventsCollector`, `orders_publisher`, `billing_events_collector`. Do not name them after the broker product or call them repositories.

A Publisher exposes `publish(...)` for one message contract or focused methods such as `publish_created(...)` for several. It hides exchange/topic, routing key, headers, serialization, and protocol details. Payloads come from ordinary builders/providers.

A Collector exposes immediate `collect_one()` and `collect_many()` with no timeout/quiet-period parameters and no assertions. `collect_one` enforces exactly one decoded message and raises a clear adapter multiplicity error for zero/many. `collect_many` drains with the broker's no-wait API until empty. Tests compare returned natural message values directly; use `UnorderedList` only when order is not contractual.

Keep the messaging test oracle independent. Publishers and Collectors must not import or call production envelope/message models, serializers/deserializers, task/event constants, Publishers/Consumers, handler registries, runtime classes, or topology declaration helpers. Define a strict test-owned wire DTO/schema or exact natural mapping, including contractual literals such as task type, version, headers, and field names. Reject missing and unexpected fields where the contract is exact. This intentional duplication prevents a shared production bug from making both stimulus and oracle agree.

Generic reuse is allowed only for private transport mechanics. A typical layout is:

```text
tests/messaging/
├── _rabbit.py       # private generic transport mechanics
└── admin_tasks.py   # domain DTO/codec and public domain adapters
```

The private module may define shapes equivalent to:

```python
class _RabbitPublisher[T]:
    async def publish(self, value: T) -> None: ...


class _RabbitCollector[T]:
    async def collect_one(self) -> T: ...
    async def collect_many(self) -> list[T]: ...


class _RabbitDeliverySource:
    async def take_one(self) -> AbstractIncomingMessage: ...
```

Inject test-owned encoders/decoders and explicit case topology into these private types from fixtures or domain adapters. Expose only domain wrappers such as `AdminTasksPublisher.publish_delete(...)` and `AdminTasksCollector.collect_one()` to tests. Tests never parameterize codecs, routing keys, exchanges/topics, headers, or raw bodies and never receive a generic transport or raw delivery. Do not weaken types to `dict[str, Any]`; structured internal results remain focused immutable DTOs, while an exact JSON/message mapping may remain a mapping when it is the natural wire value.

Do not put `take_one()` or another raw-delivery method on a Collector. Prefer a supported production-owned run-once/process-one boundary that consumes from the real route. When that public boundary accepts a delivery, a private DeliverySource owns the worker-facing retrieval role and may expose the delivery only to a domain worker/client harness. The harness does not construct internal handlers, registries, sessions, or runtime implementations.

Share exact-cardinality mechanics privately rather than duplicating them across `collect_one()` and the DeliverySource. After deterministic completion, `collect_one()` drains all immediately available deliveries, settles every delivery consumed for a multiplicity decision, and reports the observed count. `collect_many()` drains and settles the complete immediately available set. Observation deliveries are settled in guaranteed cleanup even when strict decoding fails, while the original decoding traceback propagates. A DeliverySource leaves the delivery unacknowledged only after proving there is exactly one and successfully handing it to the production worker; on multiplicity failure it settles every pulled delivery before raising. Never leave cleanup to a later test.

Before collection, await a deterministic signal from the real pipeline: completion of the invoked operation, real consumer task, acknowledgement observation, or a black-box harness completion primitive. Bind collectors before production can occur. If the harness cannot signal completion, improve it; do not race immediate reads or compensate with elapsed time.

Private fixtures own vhost/connection/channel/binding/queue isolation and cleanup; an adapter may provide `close` only as an explicit lifecycle operation invoked by its owning fixture. Use the broker SDK directly with explicit test configuration to create test routes and observation queues; do not call production topology helpers. Prefer exclusive/auto-delete/transient test resources when application-visible semantics remain unchanged. Drain/delete test queues/subscriptions in guaranteed teardown. Never expose raw broker clients/channels to tests.

Publisher confirms or equivalent acknowledgements may be enabled only as a deterministic no-wait signal that the broker accepted the input before immediate consumption. Do not assert broker reliability or persistence unless the application-owned public message contract explicitly includes the corresponding property.

## External HTTP Services

Replace only outbound network traffic to systems outside the local test environment. Do not patch application modules, classes, functions, production clients, repositories, or clocks.

The onboarding choice controls the backend:

- `external_services = "intercept"` (default) intercepts requests in the test process;
- `external_services = "testcontainers"` starts containerized mock servers through Testcontainers;
- `external_services = "mixed"` uses interception and Testcontainers mock servers for different external integrations in the same suite.

All modes expose the same project-owned domain Service API to tests. Backend URLs, container handles, interceptors, and mock-server administration remain private fixtures. Choosing Testcontainers here does not imply Docker Compose or permit replacing internal state dependencies with semantically weaker mocks.

In interception mode, use the production client's matching network tool: for `aiohttp`, create one private function-scoped `_external_http` fixture backed by `aioresponses`. For every external system/protocol, create an ordinary focused Service under `tests/services/` and expose it through a public function-scoped fixture.

In mixed mode, assign the backend once per domain integration in fixture composition. The same Service must use that backend in every case; never parameterize or switch it to create test variations. Different Services used by one test may use different backends. Do not add a per-Service map to `pyproject.toml`: the project-wide policy records that mixing is intentional, while the typed fixture graph makes each assignment visible and reviewable.

Service methods express external outcomes—`respond_with_profile`, `respond_not_found`, `respond_unavailable`, `raise_timeout`, or focused sequence methods. They hide exact URL, HTTP method, wire payload, headers, exceptions, response order, repetition, and interceptor registration. Tests never manipulate `aioresponses`, pass arbitrary URLs, or rebuild wire responses inline.

```python
class ProfilesService:
    def __init__(self, responses) -> None:
        self._responses = responses
        self._configured = []

    def respond_with_profile(
        self,
        profile_id: str,
        **overrides: object,
    ) -> dict[str, object]:
        payload = {"id": profile_id, "name": generators.name()} | overrides
        self._responses.get(
            f"https://profiles.example/profiles/{profile_id}",
            status=200,
            payload=payload,
        )
        self._configured.append(payload)
        return payload

    def reset(self) -> None:
        self._configured.clear()


@pytest.fixture(scope="function")
def _external_http():
    with aioresponses() as responses:
        try:
            yield responses
        finally:
            responses.clear()


@pytest.fixture(scope="function")
def profiles_service(_external_http):
    service = ProfilesService(_external_http)
    try:
        yield service
    finally:
        service.reset()
```

Every Service/interceptor starts empty. Each Service clears its local response plan/bookkeeping in `finally`; the interceptor clears its complete registry after dependents finish. Responses never leak between tests or Services.

Assert application output/artifacts, not Service internals or production-client calls. Verify outbound request details/count only when application-owned integration behavior makes them contractual.

## No sleeping, retries, or wall-clock waits

Ban `time.sleep`, `asyncio.sleep`, `anyio.sleep`, `trio.sleep`, delayed callbacks, polling delays, retry backoff, fixture teardown delays, and helpers hiding elapsed waits throughout test-suite code.

Disable application-configurable outbound retry count, delay, backoff, and jitter by default. A retry-contract test enables exactly the minimum attempts, keeps all delays zero, and queues immediate Service responses.

Set application-configurable I/O timeouts to zero only when the client defines zero as immediate/no-wait. If zero means unlimited or is invalid, use the smallest valid positive value. A timeout-contract Service raises the transport timeout immediately; never wait for wall-clock expiration.

Messaging has the stricter rule: no timeout, `asyncio.wait_for`, polling, retry loop, quiet-period window, or sleep. Await deterministic completion and collect no-wait.

For a non-messaging eventually consistent artifact with no deterministic completion API, bounded immediate polling without any delay is the last resort. Keep the attempt bound explicit and use `pytest.fail` only when the artifact is still absent after that bound. Prefer improving the fixture/harness to expose completion.
