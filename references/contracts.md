# Contracts and test cases

## Contents

- [Scope and invocation](#scope-and-invocation)
- [Idempotency contracts](#idempotency-contracts)
- [WebSocket contracts](#websocket-contracts)
- [Performance doubles](#performance-doubles)
- [Test shape and assertions](#test-shape-and-assertions)
- [Naming and layering](#naming-and-layering)
- [Parametrization](#parametrization)
- [Validation](#validation)
- [Operation coverage and layout](#operation-coverage-and-layout)
- [Errors and matchers](#errors-and-matchers)
- [Failure signaling](#failure-signaling)

## Scope and invocation

These are integration tests in composition and infrastructure but contract tests in scope. Enter through one public application boundary and verify only that operation's input, output/error, and direct artifacts.

Keep the test input/action (sometimes called the stimulus) and independently expressed expected truth (the oracle) independent from the implementation. Test support may import a supported public composition entrypoint to construct and run the application, job, worker, scheduler, or consumer. Public production types may be used only when that invocation API requires them or to annotate the actual value. Never instantiate a production request/response/envelope/DTO as expected data, inherit its defaults or validators, or pass actual output through a production codec/schema before comparison. Encode input, decode output, and construct expected structures through a strict test-owned view of the public wire contract so a production-side protocol change fails until the expectation is intentionally reviewed.

An ordinary test performs exactly one public invocation:

- one in-process HTTP request;
- one WebSocket handshake when handshake behavior is the case, or one client command after an accepted connection when message behavior is the case;
- one scheduler/worker-facing job invocation;
- one incoming-message publication through the real test broker path.

Fixture setup, repository arrange/inspection, external Service planning, application lifespan, and deterministic completion synchronization are not application invocations. Repeat the operation only when an authoritative public contract explicitly requires repetition—idempotency, replay, duplicate delivery, or retry—and make the minimum calls needed. Concurrency additionally requires the active project choice `test_concurrency = true`. A method name, implementation branch, existing test name, or intuitively desirable property does not establish that contract. During review, list every multi-invocation case and the source of its promise; remove or request a product decision for unsupported repetitions.

Do not call registration/login/another endpoint, a preparatory job, or an unrelated message to arrange state. Trust neighboring application contracts and prebuild prerequisites with repositories, fixtures, configuration, payload builders, and Services.

When an API dispatches asynchronous work, its direct contract ends at the exact queued message/task plus the synchronous response. Do not run the worker from the API test to prove the final state. Give the worker/job/handler its own contract test through its own public invocation boundary.

## Idempotency contracts

Idempotency is an explicit repetition contract, never a default quality assumption. Test it only when an authoritative product or wire contract names the operation identity and promises a repeated-call or duplicate-delivery outcome. Do not infer it from an implementation guard, unique constraint, deterministic task ID, retry-capable dependency, or a test name.

Use the smallest complete sequence—normally exactly two invocations—and keep it in one case:

1. arrange one initial state and bind the exact contractual idempotency identity/key;
2. invoke once and observe the normal complete response plus direct artifacts;
3. invoke again with the same contractual identity and the payload relation promised by the contract;
4. assert the promised second terminal response/settlement and exact artifact cardinality/state after both calls.

Prove absence of duplicate effects positively: exact row/message/object/ledger counts, unchanged versions/balances, or the natural equivalent. An equal second response or an empty dead-letter queue alone does not prove idempotency. For duplicate message delivery, prove both deliveries settle according to policy and the handler-owned artifact occurs once. Do not add sleeps, concurrency, retries, or a third call unless the contract distinguishes another phase.

If the contract defines changed-payload reuse, in-flight replay, failure consumption, retryable failure, expiry, or an idempotency window, give each distinct promised outcome its own parameter row/case. Otherwise do not invent those variants. Keep a cohesive idempotency contract in `test_idempotency.py`; do not hide it in generic business logic or split the first and repeated observations across tests.

## WebSocket contracts

Treat a WebSocket surface as two kinds of functional operation:

- the route-level handshake and connection lifecycle, including authorization, admission limits, negotiated subprotocol when contractual, connection release, and required close outcomes;
- each independently invokable client command, identified by route plus its public message discriminator (and subprotocol when that changes meaning).

Opening an already-authorized connection is transport setup for a command test, not a second tested operation. A route-level handshake test performs only the handshake. An ordinary command test sends one command. Send multiple frames only when a functional requirement explicitly promises continuity, idempotency, replay, ordering, duplicate handling, or another multi-frame behavior. For example, proving that a validation error is non-terminal requires an invalid frame followed by the smallest valid frame on the same accepted connection.

Inventory only current functional requirements. API prose, Swagger/OpenAPI descriptions, and schema registries may help a human locate behavior but are not the oracle and do not independently require tests. Test every required application-owned denial response, frame, close code/reason, continuation rule, and direct delivery artifact; do not mirror unimplemented future documentation or enumerate internal exception branches that collapse to the same public outcome.

Preserve natural wire semantics in test support. A pre-upgrade HTTP denial is a normal typed handshake result, not an exception invented by the adapter. Normalize a third-party client's documented denial exception at the adapter boundary when necessary; unexpected application, transport, parsing, or cleanup exceptions still propagate unchanged. Keep the accepted-session context manager for post-upgrade tests:

```python
@dataclass(frozen=True, slots=True)
class AcceptedHandshake:
    pass


@dataclass(frozen=True, slots=True)
class DeniedHandshake:
    status_code: int
    body: object


HandshakeOutcome = AcceptedHandshake | DeniedHandshake


async def test_unauthenticated(websocket_client):
    actual_handshake = await websocket_client.handshake(PATH)

    assert actual_handshake == DeniedHandshake(
        status_code=401,
        body={
            "error": {
                "code": "auth.unauthorized",
                "message": "Authentication required",
                "details": {},
                "request_id": AnyStr(length_gt=0),
            }
        },
    )
```

Test-owned outcome types contain exactly the fields the current public boundary promises and the tests consume. When acceptance carries no contractual data, use a zero-field immutable marker instead of a nullable placeholder such as `subprotocol: str | None`. Add a negotiated subprotocol, headers, identifiers, or other metadata only when the current application contract exposes it. Model mutually exclusive shapes as separate frozen variants plus a union alias rather than one nullable bag; the alias is not a third runtime class. Prefer readable outcome-first names such as `AcceptedHandshake`, `DeniedHandshake`, and `HandshakeOutcome`.

Use distinct role names across layers: a generic `...Transport` owns in-process SDK/protocol mechanics, an accepted `...Connection` owns one live session, and a functional `...Client` owns domain commands and defaults. The generic transport accepts only currently supported component-owned protocol values explicitly. Put route, discriminator, and domain conveniences in the owning narrow adapter; never hardcode a child contract in root/shared transport support or import that adapter back into a broader group fixture.

An in-process async adapter must not wait only on an output queue. Race the next protocol event against the application/runner task with deterministic `FIRST_COMPLETED` semantics and re-raise the task's original exception if it finishes first. This is completion signaling, not a wall-clock timeout; do not add sleeps or timeout-based polling.

Under the standard layout, `test_connection.py` is the recommended name for the route-level accepted connection and lifecycle contract. Keep authorization in `test_access.py`, input validation in `test_validation.py`, application-owned connection failures in `test_errors.py`, and metrics in `test_metrics.py` when applicable. The route component contains transport-facing connection behavior rather than a business rule, so `test_business_logic.py` would misstate its purpose. Independently invokable message-command components choose their own categories by behavior and use `test_business_logic.py` only when they actually prove domain rules or outcomes. Never create an empty category file.

## Performance doubles

A performance double is a minimal typed fake/no-op implementation of an application-owned collaborator. It is a narrow performance exception, not permission to inspect or patch implementation details.

Use one only when all conditions hold:

1. It is injected through the same supported composition, DI, or configuration seam available to production composition—never `patch`, `monkeypatch`, or method replacement.
2. The replaced work does not create the response/artifact asserted by the current test and is not validation, authorization, mapping, serialization, transaction handling, publication, or persistence currently under test.
3. The real path already has separate contract/business-logic coverage. If that cannot be established, run the real implementation.
4. Removing the double changes only duration/resource use, never the observed result, errors, artifacts, or contractual ordering.
5. The test never asserts internal calls with `assert_called*`; doing so turns implementation interaction into the contract.
6. Fixture lifecycle isolates and resets the double for every case.

Prefer a small typed fake/no-op to a generic mock object. Use the double when it materially improves suite time; it is not mandatory for cheap work. External outbound systems remain a separate boundary represented by a domain Service and a network interceptor/mock server.

## Test shape and assertions

Keep arrange, invocation, and assertion visible:

```python
async def test_contract(authorized_api_client, character_repository):
    character = await character_repository.create_available()

    actual_response = await authorized_api_client.get(PATH)

    assert actual_response.status_code == 200
    assert actual_response.json() == {
        "id": str(character.id),
        "name": AnyStr(length_gt=0),
    }
```

Assert natural observations directly. A separately bound checked result is `actual` or `actual_*`; a separately bound expected value is `expected` or `expected_*`. Arrange-only entities retain domain names. Status, headers, body, database rows, and stored objects are separate observations and may have separate assertions. Do not rebind them to generic `result` or manufacture a dictionary/dataclass/tuple merely to combine them.

When one natural value is already compound, compare that entire value with one equality assertion. The primary contract compares the exact complete public value: a PATCH or partial input does not make unchanged stable response fields optional. Exact dictionaries enforce key sets; exact lists enforce length, order, and nesting. Do not split one response body/model/list into an assertion per member. Use a focused membership/range/identity predicate only when it is the clearest expression of one edge condition.

Keep short values inline. Expected-value builders and matchers keep semantic callable/class names rather than `expected_*`.

Do not hide assertions in helpers. Repeated expected structures become builders; reusable constraints become pure equality matchers. The test still contains a natural assertion such as `assert actual_response_body == expected_response(...)` or `assert actual_created == Matcher(...)`.

Use module-level functions for ordinary cases. Prefer a pytest `TestClass` when several complete cases can safely reuse materially expensive identical composition/preparation. A fixture performs arrange and one invocation before each method; the method contains every assertion for its own case. Never split one invocation's response/storage observations across methods, share mutable case state, rely on method order, or create a class for one case/cosmetic grouping. Only immutable behavior-independent machinery may use class/session scope. Ordinary support classes such as repositories, Services, Publishers, Collectors, matchers, dataclasses, DTOs, and client wrappers remain unrestricted by this test-class rule.

```python
@pytest.mark.parametrize(
    "make_overrides",
    [
        pytest.param(lambda: {"is_published": False}, id="unpublished"),
        pytest.param(lambda: {"deleted_at": datetime.now(UTC)}, id="deleted"),
    ],
)
class TestUnavailableCharacters:
    @pytest.fixture(scope="class")
    def _prepared_runtime(self, runtime_factory) -> PreparedRuntime:
        return runtime_factory.prepare_read_only_catalog()

    @pytest.fixture
    async def actual_case(
        self,
        _prepared_runtime,
        authorized_api_client,
        character_repository,
        make_overrides,
    ) -> ExclusionCase:
        excluded = await character_repository.create(**make_overrides())
        actual_response = await authorized_api_client.get(PATH)
        return ExclusionCase(excluded=excluded, response=actual_response)

    def test_excluded(self, actual_case: ExclusionCase) -> None:
        assert str(actual_case.excluded.id) not in {
            item["id"] for item in actual_case.response.json()["items"]
        }
```

`ExclusionCase` is a typed preparation context, not an artificial assertion aggregate: it carries the arrange handle and actual invocation result needed by one complete assertion case. If another method checks a different case, it owns its complete assertions and receives an independently executed fixture context.

## Naming and layering

Treat the full node ID as the readable name: directories identify surface and operation, filename identifies category, function identifies the remaining rule, and parameter ID identifies the concrete variant.

- Primary business contract: `test_contract`.
- Other business rules: short observable verb phrases such as `test_excludes_unavailable` or `test_preserves_order`.
- Access: `test_unauthenticated`, `test_authorized`.
- Errors: `test_not_found`, `test_conflict`, `test_dependency_unavailable`.
- Metrics: `test_emits_request_count`, `test_skips_failed_request`.
- Validation: `test_<field>` or a relationship name such as `test_date_range`.

Do not repeat the endpoint/component, category, HTTP method/path, `success`, `happy_path`, `works`, or Given/When/Then segments. Add qualifiers only to disambiguate contracts in one file.

Outside validation, put the general case first and give it the complete shared public contract. Later edge/variation tests arrange and invoke independently but assert only the fact that changes. This is assertion layering, never execution-order or state coupling.

## Parametrization

Use `pytest.mark.parametrize` for all variations of one contract. Give every row one concise explicit readable name through `pytest.param(..., id=...)` or a complete `ids=[...]` list. Describe the condition or boundary—not `case-1`, raw data, or an implementation detail.

Parameter rows contain the real values and expected outcomes. Never pass a scenario key and decode it with `match`, `if`/`elif`, or a mapping. Never read the pytest ID to drive behavior.

Stable values may be passed directly. Fresh values use same-signature factories invoked during arrange:

```python
@pytest.mark.parametrize(
    "make_overrides",
    [
        pytest.param(lambda: {"app_id": "another.app"}, id="different-app"),
        pytest.param(lambda: {"is_published": False}, id="unpublished"),
        pytest.param(
            lambda: {"deleted_at": datetime.now(UTC)},
            id="soft-deleted",
        ),
    ],
)
async def test_excludes_unavailable(
    authorized_api_client,
    character_repository,
    make_overrides,
):
    excluded = await character_repository.create(**make_overrides())

    actual_response = await authorized_api_client.get(PATH)

    assert str(excluded.id) not in {
        item["id"] for item in actual_response.json()["items"]
    }
```

Do not mix raw values and factories behind `if callable(...)`. Move a complex factory to the neighboring `payload.py`.

## Validation

Create exactly one parametrized `test_<field>` per field in `test_validation.py`. Keep unrelated fields valid and vary only the target. Combine fields only when the application defines a relationship between them. Do not introduce a TestClass merely to group the values of one validation field.

For each field include:

1. one randomized ordinary valid value when appropriate;
2. every meaningful valid lower/upper boundary;
3. the nearest representable invalid value immediately outside each boundary;
4. representative invalid shapes/values required by the contract.

For an enumeration or registered discriminator, test every publicly allowed member and at least one disallowed member instead of one randomized success. This public member set takes precedence over a broader transport/schema representation: do not invent a successful minimum/maximum string row when routing or dispatch correctly rejects every unregistered value. Keep the nearest invalid representation boundaries only when they remain useful acceptance/rejection evidence.

Keep acceptance and errors in one parametrization. Parameterize the complete expected observation so test control flow does not decode a scenario:

```python
@pytest.mark.parametrize(
    ("name_factory", "expected_status", "expected_error"),
    [
        pytest.param(
            random_valid_name,
            201,
            None,
            id="ordinary-valid-value",
        ),
        pytest.param(
            lambda: "aa",
            201,
            None,
            id="minimum-length",
        ),
        pytest.param(
            lambda: "a",
            422,
            {
                "field": "name",
                "code": "too_short",
                "message": AnyStr(length_gt=0),
            },
            id="below-minimum-length",
        ),
    ],
)
async def test_name(
    api_client,
    name_factory,
    expected_status,
    expected_error,
):
    actual_response = await api_client.post(
        PATH,
        json=user_payload(name=name_factory()),
    )

    assert actual_response.status_code == expected_status
    assert actual_response.json().get("error") == expected_error
```

Validation proves only whether the application accepts or rejects the supplied value. A valid row checks the exact public acceptance signal, not downstream business output/artifacts already protected elsewhere. An invalid row checks the validation error contract. Matchers are allowed only on the expected side for dynamic error leaves; keep the tested field, exact boundary result, location, error code, and contractual message literal whenever fixed.

When a valid row would trigger unrelated expensive work, a performance double may suppress that work only under the conditions above. It must not replace the validator or any code responsible for acceptance/rejection.

## Operation coverage and layout

Inventory depth follows the task. A focused change inspects its relevant surface; a full coverage review discovers the complete registered/reachable surface—including mounted, hidden-from-schema, feature-gated, operational, job, scheduler, worker, and message-handler entries—before claiming completeness.

Turn that inventory into a transient contract-evidence matrix before declaring the suite complete. For every discovered operation record its stable public identity, applicable generalized registry rule and depth, terminal test component, primary contract node, applicable categories, and application-owned observable outcome classes. Build outcome classes from public contracts plus implementation inspection (for example accepted, rejected, preserved, dispatched, registered, acknowledged, or dead-lettered), but assert only public responses/direct artifacts rather than internal branches. Every outcome maps to a test node or a documented scope decision. The matrix is audit evidence, not persistent micromanagement: never copy public operations into `pyproject.toml` or maintain a per-operation registry.

Operation presence and a `test_contract` node prove only census completeness. Scenario completeness is a separate semantic pass: inspect authoritative functional requirements together with application-owned source branches and partitions, then enumerate every distinct public outcome, meaningful state partition, isolation dimension, contractual boundary, and direct artifact. Map every public-contract item to an actually collected case. Generalized policy decisions may scope only non-contract surfaces and the recorded concurrency boundary; they never exempt public or registered contracts. Collapse implementation branches only when they are observationally identical at the public boundary; never omit a promised outcome merely because another case executes nearby code.

A `focused` generalized registry rule still requires enumerating the complete matching surface before selecting the promised depth. It is not permission to sample a convenient subset silently. Report which applicable aspects are covered for every matching operation and which generalized policy excludes the rest.

Always treat every public product HTTP/JSON-RPC/WebSocket operation and every registered job, scheduled task, consumer operation, and incoming-message handler as contract-bearing. They require independent coverage without a registry entry or permission to omit them. The handler contract remains mandatory when a worker hosts it; generic worker runtime mechanics do not become a separate mandatory operation merely because the process is registered.

Exclude endpoints whose sole purpose is API documentation, generated schema exposure, Swagger/OpenAPI UI support, or a documentation-only schema registry. Do not add a terminal test component or snapshot generated documentation for them. Keep a functional operation in the matrix when it also happens to be documented; classify by behavior, not by path naming or schema visibility.

For other hidden, debug, operational, runtime, or ambiguous surfaces, consult the generalized `[tool.pytest-blackbox.coverage]` registry. Ask only when a newly discovered surface class has no matching rule, and record a generalized `exclude`, `focused`, or `standard` decision—not individual operation identifiers. Do not describe a suite as complete without naming the selected boundary and known exclusions.

For ordinary product endpoints, identity is `HTTP method + path template`. For JSON-RPC endpoints, identity is `HTTP method + JSON-RPC method`; the shared transport path is not the endpoint identity. For WebSockets, the route handshake/lifecycle is one identity and each client command is `route + subprotocol when contractual + message discriminator`. Operational health/liveness/readiness probes are excluded from the product-contract mapping and governed by the exception below.

Under the standard layout, map every contract-bearing product operation one-to-one to a terminal directory:

```text
POST /api/v1/auth/token       -> test_api_v1/test_auth/test_issue_token/
GET  /api/v1/users/{user_id} -> test_api_v1/test_users/test_get_user/
POST + JSON-RPC users.create -> test_jsonrpc/test_users/test_create_user/
WS /api/v1/chat              -> test_api_v1/test_chat/test_chat_websocket/
WS /api/v1/chat + chat.send  -> test_api_v1/test_chat/test_send_chat_message/
```

The two WebSocket operation kinds therefore use different primary category files:

```text
test_chat/
├── test_chat_websocket/       # route handshake and lifecycle
│   ├── test_connection.py     # accepted connection, close, resource release
│   ├── test_access.py         # when the handshake is protected
│   └── test_errors.py         # application-owned connection failures
└── test_send_chat_message/    # independently invokable command
    ├── test_business_logic.py
    ├── test_validation.py
    └── test_errors.py
```

Use this hierarchy:

```text
tests/
└── test_api_v1/                 # mandatory functional group
    ├── client.py
    ├── conftest.py
    ├── errors.py
    └── test_auth/               # optional one-level organization
        └── test_issue_token/    # mandatory terminal operation
            ├── conftest.py
            ├── errors.py
            ├── payload.py
            ├── test_access.py
            ├── test_errors.py
            ├── test_validation.py
            ├── test_business_logic.py  # only for actual business behavior
            └── test_metrics.py
```

Three directories below `tests/` is the standard-layout maximum: functional group, optional organization, terminal operation/component. Every test-hierarchy directory starts with `test_`. Root support packages such as `fixtures/`, `environment/`, `repositories/`, `messaging/`, `services/`, `cmp/`, and `generators/` are not test groups.

The hierarchy and common category meanings are an adaptive default, not a reason to mass-move a mature coherent suite. With `layout = "preserve"`, retain an established unambiguous vocabulary. Category filename aliases are not separately configurable: a behavior-specific filename follows from the public contract aspect rather than a user-maintained name map. A broad layout refactor requires explicit authorization.

Choose every category filename by the public behavior it groups. The primary contract is not automatically business logic and belongs in the category that accurately names what it proves:

- business rules, domain outcomes, state transitions, retry, and business/config variants in `test_business_logic.py`;
- an explicitly promised repeated-operation contract in `test_idempotency.py`;
- unauthenticated rejection and authorized access in `test_access.py` when protected;
- every public input in `test_validation.py`;
- application-owned failures in `test_errors.py`;
- emitted/suppressed metrics in `test_metrics.py` when present;
- another cohesive public contract aspect in a concise `test_<behavior>.py`, such as `test_connection.py` for a WebSocket route or `test_registration.py` for an explicitly selected registration contract.

Use one category for a cohesive family of cases, not a separate filename per case, parameter, or outcome. Never use `test_business_logic.py` as a generic primary-success file, and do not create `test_success.py`, `test_happy_path.py`, `test_works.py`, vague `test_behavior.py`/`test_technical.py`, or empty category files. Prefer an established precise term over inventing a synonym. With a preserved mature layout, adapt an already unambiguous equivalent rather than renaming files without explicit authorization. Never substitute another endpoint, smoke test, access case, validation row, workflow, or fixture bootstrap for the operation's own primary contract.

Under the standard layout, non-API product groups use the same functional/optional-area/terminal-component rule. Never create `test_infrastructure/` or `test_application/`: infrastructure and application startup are suite prerequisites, not separately tested behavior.

Map every registered job, scheduled task, and incoming-message handler contract one-to-one to its own terminal component (or its coherent preserved-layout equivalent) and primary contract test. Identify a job/task by its invocation contract and a handler by its incoming message contract plus public handler/route identity. Shared processes, schedulers, queues, exchanges, topics, transports, or production modules do not merge independently invokable handler contracts:

```text
catalog_deletion job       -> test_jobs/test_catalog_deletion/
hourly economy settlement -> test_schedulers/test_economy_settlement/
media.deleted consumer    -> test_consumers/test_media_deleted/
```

Give each such component its own applicable errors, business rules, artifacts, configuration, metrics, and regressions. Use validation coverage when the public input contract has application-owned validation. Do not count another job/consumer, a workflow, fixture bootstrap, or a shared runner smoke test as coverage.

Separate shared worker/runtime contracts from handler contracts. Cross-cutting dispatch, envelope rejection, acknowledgement/requeue/dead-letter policy, and unknown-message behavior belong to one dedicated worker/runtime component only when that worker boundary is itself selected for coverage. Each handler component tests only handler-specific input, application-owned errors/business rules, and direct artifacts; it does not repeat generic runtime cases. Conversely, a shared worker/runtime contract never substitutes for a handler's own `test_contract`. If runtime mechanics are not in the public contract, observe only the handler's public outcome unless the user explicitly opts into additional focused coverage.

When worker runtime or registration is selected, put the actual broker/consumer composition contract in `test_topology.py`. Observe the production declaration/registration path and verify only application-owned choices such as exchange/topic and queue/subscription identity, binding/routing, dead-letter policy, durability/auto-delete settings, QoS/prefetch, and handler/discriminator registration when they are part of the selected contract. Do not test broker reliability or reimplement production topology through a parallel test DTO/helper. Keep the check deterministic: use a supported composition/start seam that returns after registration, inspect its natural broker/framework artifacts, and close it immediately without live waiting, timeout polling, or message-processing assertions. Settlement policy remains in its own behavior category and every handler keeps its own component.

For every registered scheduler, prove the actual framework registration: observe the callback and trigger registered through the supported scheduler composition/inspection boundary. Manually calling a wrapper plus comparing a separately maintained schedule DTO does not protect `add_job(...)`, callback wiring, or trigger configuration. Keep this deterministic; do not start a live clock-driven scheduler merely to invoke the callback manually, because a background tick creates a second-invocation race.

When worker settlement is selected, every terminal policy needs a positive deterministic artifact. Success must prove acknowledgement/settlement (or equivalent non-redelivery state); an empty rejected/dead-letter queue alone is insufficient because an unacknowledged in-flight delivery produces the same absence. Expose the smallest typed test-owned projection supported by the broker/runtime boundary and keep raw delivery objects private.

Health endpoints are the narrow opt-in operational exception. Cover them only when the coverage registry selects them. Under the standard layout put them directly under `tests/test_health/` as focused files such as `test_liveness.py` and `test_readiness.py`; do not add terminal operation directories or category files. These checks do not receive the product black-box contract matrix. Start the real composed application, invoke each probe in process, and assert only the probe's status/body and application-owned readiness classification. Do not use health checks to test PostgreSQL, Redis, RabbitMQ, S3, migrations, fixture bootstrap, retries, failure recovery, or dependency reliability.

## Errors and matchers

Put repeated expected error builders at the narrowest owning level: API-surface/group `errors.py` for shared envelopes, or terminal component `errors.py` for local ones. These ordinary modules do not use `test_` filenames and never contain fixtures or assertions.

An error builder accepts expected literals and returns an exact public structure. It never receives the actual result, sends a request, arranges state, queries repositories, catches unexpected exceptions, branches over unrelated schemas, or invokes `pytest.fail`.

Keep matcher classes under the single public `tests.cmp` interface. Matchers:

- implement pure `__eq__` and informative `repr`;
- enforce exact advertised types (`AnyInt` does not accept `bool`);
- support explicit constraints such as `length`, `length_gt/gte/lt/lte`, `gt/gte/lt/lte`;
- reject contradictory construction;
- contain no fixture, generator, clock, network, database, or application dependency.

Use exact literals whenever possible. Use `OrderedList` for explicit ordered matcher composition and `UnorderedList` only when order is not contractual. `UnorderedList` preserves exact length and duplicate multiplicity and performs one-to-one matching; never implement it with sets, heterogeneous sorting, or greedy broad matches.

For object/DTO actual values, use a test-owned object matcher such as `Object(...)` when dynamic fields prevent exact construction. It compares the object as one value, checks the advertised test-owned/public type constraint when one is intentionally supplied, and compares an explicit exact attribute set with nested literals/matchers. Partial attribute matching is opt-in and allowed only when the public contract is intentionally extensible. The matcher never constructs, validates, serializes, or decodes through a production DTO/schema.

## Failure signaling

Use normal assertions for predicates and structures. Use `pytest.raises` only when the public boundary itself is exception-based. HTTP responses, WebSocket handshake denials, frames, close events, rejected messages, and other protocol outcomes remain values even when a third-party client initially represents them as exceptions; normalize those documented outcomes in the test-owned adapter. Use `pytest.fail("reason")` only when control flow reaches an explicitly forbidden branch that cannot be expressed clearly with a direct assertion.

Never manually raise `AssertionError`/generic exceptions merely to fail a test. Never catch an unexpected application/support exception and replace it with `pytest.fail`; let the original traceback propagate. Test-support cleanup may catch and re-raise unchanged with bare `raise` after cleanup.
