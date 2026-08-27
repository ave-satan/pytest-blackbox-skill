# Fixtures, application composition, and asyncio

## Contents

- [Ownership and dependency direction](#ownership-and-dependency-direction)
- [Conftest and fixture visibility](#conftest-and-fixture-visibility)
- [Configuration](#configuration)
- [Application and API clients](#application-and-api-clients)
- [Worker, job, and consumer composition](#worker-job-and-consumer-composition)
- [Reusable clients and runtimes](#reusable-clients-and-runtimes)
- [One event loop](#one-event-loop)
- [Scope and cleanup](#scope-and-cleanup)

## Ownership and dependency direction

Fixtures own pytest scope, ordering, orchestration, and guaranteed `yield`/`finally` cleanup. Ordinary modules implement reusable work:

- `tests/fixtures/`: suite-wide fixtures and construction of public repositories, messaging adapters, and external Services;
- `tests/environment/`: resource provisioning, migrations, bootstrap, inspection, and removal;
- `tests/repositories/`: case-level CRUD and artifact inspection for addressable stored state;
- `tests/messaging/`: domain Publishers/Collectors plus private generic broker mechanics and DeliverySources when required by a public worker boundary;
- `tests/services/`: outbound external-network response adapters;
- `tests/cmp/`: equality matchers;
- `tests/generators/` by default: project-owned generated-data facade; Faker is the default replaceable backend;
- neighboring `payload.py`: component-local payload/data builders.

These are the predefined roles/names for a new suite. Adapt to a coherent mature support layout instead of renaming it automatically; filenames/package aliases are not individual configuration choices, and a broad move requires explicit authorization. Do not create a generic `tests/support/`. Do not place fixtures or tests in the environment-provisioning module, and do not let repositories/Services/messaging adapters provision session resources.

Allowed import direction is:

```text
production and third-party code
              ↑
root shared test support
              ↑
functional test group
              ↑
optional organizational group
              ↑
terminal operation/component
```

Narrower code may import broader code. Broader layers never import `tests/test_*/`; groups never import narrower components; siblings never import each other's private implementation. This dependency rule includes values as well as imports: shared clients, fixtures, and helpers never hardcode a child's route path, message discriminator, routing key, topology name, or expected literal. Promote only the smallest genuinely shared mechanism to the correct root layer; keep component-owned defaults in the narrow adapter.

This diagram governs test-layer ownership; it does not authorize arbitrary imports from production. Root support may import supported public construction/lifecycle entrypoints such as `create_app(...)`, `create_admin_worker(...)`, or their application-specific equivalents, plus their public interfaces and configuration/composition types. Public production types are allowed only as required arguments/results of those boundaries or as annotations around actual values; they never construct expected values or encode/decode the test oracle. Repository modules may additionally import mapped `Table`/`__table__` metadata solely for SQLAlchemy Core state operations. No test support imports internal handlers, registries, runtime classes, application-state attributes, serializers/deserializers, message/envelope models, routing or task constants, production Publishers/Consumers, or topology helpers to build test inputs or interpret outputs. The storage exception never permits ORM instances or behavior. Third-party protocol/client types remain allowed.

## Conftest and fixture visibility

Root `tests/conftest.py` defines suite hooks and registers focused fixture plugins only:

```python
pytest_plugins = (
    "tests.fixtures.application",
    "tests.fixtures.database",
    "tests.fixtures.repositories",
    "tests.fixtures.messaging",
    "tests.fixtures.services",
    "tests.fixtures.storage",
)
```

Local `conftest.py` owns fixtures at the narrowest directory covering their consumers: functional-group fixtures at group level, area fixtures at area level, terminal-only fixtures beside that component. Every `conftest.py` is pytest-only; move helpers, constants, builders, classes, context managers, providers, and raw SDK topology/runtime construction to ordinary modules. A fixture may enter one focused context manager/factory and expose its typed projection, but `conftest.py` must not become the implementation owner for broker channels, exchanges, queues, worker runtimes, codecs, or cleanup algorithms.

Fixture names form a public test API:

- public only when requested directly by a test or `usefixtures`;
- `_`-prefixed when consumed only by fixtures, bootstrap, teardown, ordering, or autouse behavior;
- test function signatures never contain `_fixture` arguments.

Do not forward a private fixture through a test-local helper. Expose one purposeful public repository/client/Service/Publisher/Collector fixture instead.

Every fixture must own lifecycle, ordering, configuration, prepared state, or a purposeful typed projection from a cohesive context. Do not create pass-through aliases that merely return/yield another fixture under a new name; request the owning public fixture directly or expose a meaningful projection such as `authorized_user` from `_authorized_context`.

Do not use `del` to consume an ordering dependency, silence lint, release resources, or claim cleanup. An unused underscore-prefixed fixture argument already declares ordering. Perform real cleanup with rollback, close/aclose, cancellation plus awaiting, queue/object/key deletion, or the resource's lifecycle API.

## Configuration

Keep the base configuration recursively immutable and session-scoped. Derive a function-scoped copy per case, pass behavior-affecting overrides explicitly through parametrization, and make the application consume the derived object before startup. If the settings library permits mutable nested models/collections, use a verified deep copy or rebuild from immutable source data; a shallow `model_copy` plus an agreement not to mutate is insufficient isolation.

```python
@pytest.fixture(scope="session")
def _base_settings() -> Settings:
    return load_test_settings()


@pytest.fixture(scope="function")
def settings(_base_settings, request) -> Settings:
    overrides = getattr(request, "param", {})
    return _base_settings.model_copy(update=overrides, deep=True)


@pytest.mark.parametrize(
    ("settings", "expected_status"),
    [
        pytest.param(
            {"feature_enabled": True},
            200,
            id="enabled",
        ),
        pytest.param(
            {"feature_enabled": False},
            404,
            id="disabled",
        ),
    ],
    indirect=["settings"],
)
async def test_applies_feature_setting(api_client, settings, expected_status):
    actual_response = await api_client.get(PATH)

    assert actual_response.status_code == expected_status
```

The public `settings` argument makes the per-test behavior explicit. The private application fixture depends on that same `settings` fixture and passes it to the supported application factory/wiring before lifespan begins. Never mutate `_base_settings` or rely on a test changing ambient global configuration.

Generated values are ordinary arrange-time function calls, never fixtures. A fixture that only returns `generators.login()`, a UUID, timestamp, payload, or other in-memory value adds no lifecycle/capability and hides variation; call the generator or payload builder in arrange instead.

## Application and API clients

Give application lifecycle, surface HTTP mechanics, and pytest composition one owner each. In a new standard-layout suite use:

- `tests/fixtures/application.py`: generic application construction, production-owned infrastructure composition, and lifespan; no HTTP transport or authorization details;
- `tests/test_<surface>/client.py`: transport, client/wrapper types, base URL, headers/cookies/tokens, open/close functions; no pytest fixtures, DB setup, dependency overrides, or lifespan;
- `tests/test_<surface>/conftest.py`: fixture declarations and dependency composition only.

With `layout = "preserve"`, retain an equivalent coherent separation in the mature suite. Do not make filenames configurable or perform a broad move without explicit authorization. A performance double may be supplied by fixture composition only through the supported application seam and only under the contracts reference conditions.

Public domain clients/runners expose only operations and natural artifact reads that tests are allowed to use. Constructor dependencies and fields for raw SDK clients, Publisher/DeliverySource/Collector mechanics, production workers/runtimes, exchanges/topics/queues, routing keys, codecs, and topology handles are private. A dataclass field is part of the fixture API: prefix such mechanisms with `_` or replace the dataclass with an explicit class so tests cannot bypass the domain method accidentally.

```python
# tests/fixtures/application.py
@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def _application(settings, _database_transaction, _redis_isolation):
    application = create_app(
        settings=settings,
        database_connection=_database_transaction,
    )
    async with application.router.lifespan_context(application):
        yield application


# tests/test_api_v1/client.py
@asynccontextmanager
async def open_api_client(application):
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


@asynccontextmanager
async def open_authorized_api_client(application, credentials):
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {credentials.access_token}"},
    ) as client:
        yield client


# tests/test_api_v1/conftest.py
@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def api_client(_application, _database_transaction):
    async with open_api_client(_application) as client:
        yield client


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def authorized_api_client(
    _application,
    _database_transaction,
    _authorization_credentials,
):
    async with open_authorized_api_client(
        _application,
        _authorization_credentials,
    ) as client:
        yield client
```

Use distinct unauthorized and authorized client instances over the same application and transaction. Prepare identity/session/token/cookie state through private fixtures and repositories without calling registration/login endpoints. Apply credentials through the application's real authorization mechanism; do not mock authorization or mutate `api_client` into the authorized client.

The `database_connection` argument above represents a production-owned composition hook; use the application's supported equivalent. It accepts or binds the outer `Connection`/`AsyncConnection` matching the project's concurrency model, while production code internally creates and uses its normal ORM sessions on that connection. Test functions and all test support never import, request, construct, configure, or operate SQLAlchemy `Session`/`AsyncSession` objects or session factories. If the application lacks this boundary, report the blocker and request separate authorization to add/refactor a general production seam; never define a test-only ORM provider. Repositories and other test-owned database preparation use the connection directly with SQLAlchemy Core statement APIs.

The synthetic ASGI `base_url` never opens a socket. Never start Uvicorn/Gunicorn, bind a port, or call localhost for the application under test.

Apply the same in-process rule to WebSockets. Keep raw ASGI queue/task mechanics in a generic transport module that accepts route and protocol inputs explicitly, then expose component-level handshake/session clients through the owning functional group. Expected pre-upgrade denial is a typed value returned by a handshake probe; do not require `pytest.raises` around an empty `async with ...: pass` block. A live-session context manager may raise a clear adapter exception when a test that requires acceptance is unexpectedly denied.

Every in-process async transport/runner adapter waits on both sides of its completion protocol. When expecting the next frame/event, race that queue read against completion of the application/runner task and propagate the original task exception if it finishes first. Cancel and await only the losing internal wait task during cleanup. Never add a wall-clock timeout to mask missing completion.

## Worker, job, and consumer composition

Give every non-HTTP runtime one production-owned public composition boundary analogous to `create_app(...)`. The boundary builds the real handler registry, production sessions, broker adapters, and internal runtime from explicit public configuration and injected case resources. Test support may invoke the returned public process-one/handle/run-once capability, but it never assembles the registry or handler graph itself.

Pass the outer test `Connection`/`AsyncConnection` or another supported production database binding into this boundary. Production code creates and uses its normal ORM sessions internally. Never read `_application.state.*`, retrieve or pass a production session factory, instantiate an internal handler/runtime directly, or reproduce the task-type-to-handler mapping in tests.

For an incoming-message contract, the test-owned Publisher sends one independently encoded message through the real broker route. Prefer a composed production run-once/process-one boundary that consumes from that route itself. If the supported boundary accepts an unacknowledged delivery, a private DeliverySource retrieves and hands it over. The test sees only a domain client method such as `process_delete(...)`, never the raw delivery, channel, queue, runtime, handler, or registry.

If a suitable boundary does not exist, report the blocker and request separate authorization to add or refactor a general production composition API used by the real entrypoint. Never infer permission from the testing task, add a process/handle path reachable only by tests, reach into application state, or import implementation classes.

## Reusable clients and runtimes

Do not repeat identical behavior-independent preparation in every test. Hoist only stateless or immutable machinery—application/client/transport factories, worker/job/consumer runner factories, signers, compiled base configuration, connection pools, and administration clients—into private session-scoped fixtures.

Use the widest safe scope:

- make the prepared object itself session-scoped only when it cannot retain any case state;
- when it retains cookies, credentials, actors, mutable headers, transaction handles, case configuration, queue bindings, jobs, collected messages, or other case state, keep only its expensive immutable factory/bootstrap session-scoped;
- expose a thin function-scoped public fixture that binds the shared bootstrap to the current `_database_transaction`, derived `settings`, isolated namespace, or per-case state and resets any mutable surface in teardown;
- create a fully isolated function-scoped actor/runtime only when the case mutates that actor/runtime, tests its creation/lifecycle, or requires behavior-affecting configuration incompatible with the shared instance.

Persisted identities/actors, authorization sessions and credentials, Redis sessions, mutable clients, workers/consumers, prepared jobs, and baseline application records are case state and remain function-scoped inside the current transaction or isolated namespace. Prepare them once per test through repositories and fixtures. Never invoke login, registration, token, startup, or another public application operation merely to bootstrap them.

Maximize the scope of stateless preparation, not necessarily the scope of the fixture requested by a test. A cheap function-scoped facade over a session-scoped factory/bootstrap is preferable to repeating expensive construction or leaking mutable state between cases.

Preserve every bootstrap value needed by a downstream fixture or test consumer. If authorization preparation creates a user, session, credentials, cookie, or related resource that consumers need, return them together as one focused immutable typed context. All dependent fixtures project those cached values; none re-query the database/cache merely to recover already-known setup data. Disposable intermediates need not be exposed:

```python
@dataclass(frozen=True, slots=True)
class AuthorizedContext:
    user: UserRecord
    session_id: UUID
    credentials: Credentials


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def _authorized_context(
    user_repository,
    session_repository,
) -> AuthorizedContext:
    user = await user_repository.create()
    credentials = await session_repository.create_credentials(user)
    return AuthorizedContext(user=user, credentials=credentials)


@pytest.fixture(scope="function")
def authorized_user(_authorized_context: AuthorizedContext) -> UserRecord:
    return _authorized_context.user


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def authorized_api_client(_application, _authorized_context):
    async with open_authorized_api_client(
        _application,
        _authorized_context.credentials,
    ) as client:
        yield client
```

Pytest caches `_authorized_context` once for the test, so a test requesting the client, user, credentials, or session identifier receives the exact values used during authorization with no extra storage call. Apply the same pattern to workers, consumers, admin clients, prepared jobs, tenants, buckets, and similar fixture graphs. Preserve every stable handle that a later arrange step reasonably needs; never scan a database/cache/index merely to reconstruct one. Re-read through a repository when a later setup step or the tested operation may have changed persisted state, or when current persisted state is itself the artifact under assertion.

Fixture contexts and helper results use named typed fields. Prefer frozen dataclasses or focused DTOs; do not return `dict[str, object]` or positional tuples for internal multi-value results. This context models cohesive preparation and is not a synthetic assertion aggregate. Dictionaries remain correct for natural mapping contracts such as JSON payloads, headers, settings overrides, and raw external wire bodies.

## One event loop

For an asyncio project, use exactly one pytest-managed event loop from session setup through session teardown:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
asyncio_default_test_loop_scope = "session"
```

Every explicitly configured async fixture uses `loop_scope="session"`, regardless of its cache scope. Create, use, and close engines, connections, clients, tasks, futures, locks, queues, transports, lifespan, and environment resources on that loop. Production-owned ORM sessions remain inside application code on this same loop.

Never call `asyncio.run`, `asyncio.Runner`, `asyncio.new_event_loop`, `asyncio.set_event_loop`, or `run_until_complete`; never define another event-loop fixture. Convert synchronous fixtures that bridge to async work into async fixtures and `await` setup/teardown.

Do not force an event loop or async fixtures onto a fully synchronous project. Match the application's concurrency model end to end.

## Scope and cleanup

Use session scope for the single async loop when applicable, immutable base configuration, service-administration connections, isolated logical-resource lifecycle, migrated schema, and expensive stateless/immutable application, client, transport, signer, and runner factories.

Use function scope for derived settings, database transactions, repositories, persisted actors and credentials, generated records, prepared jobs, queue bindings/collectors, Redis/S3 case namespaces, external network interceptors/Services, and every application/client/worker/consumer/runtime layer that captures or mutates those values. Split stable session factories/bootstrap from this thin case binding instead of rebuilding the whole stack.

A TestClass may reuse immutable expensive composition at class scope. Each method still receives a newly prepared function-scoped case context containing its own invocation result and all assertions for that complete case. Never share a mutable record, credential, message, transaction, response, or produced artifact across methods.

Use `yield` plus `finally` for symmetric cleanup. Avoid autouse fixtures unless every test in that scope requires the behavior. Fixtures never hide the operation under test or its assertions.
