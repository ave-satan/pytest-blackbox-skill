# Repositories, generated data, matchers, and time

## Contents

- [Repository boundary](#repository-boundary)
- [Repository interfaces](#repository-interfaces)
- [Aggregate repositories](#aggregate-repositories)
- [Artifact inspection](#artifact-inspection)
- [Generated data](#generated-data)
- [Payload builders](#payload-builders)
- [Compound-value matchers](#compound-value-matchers)
- [Time-dependent artifacts](#time-dependent-artifacts)

## Repository boundary

Use test repositories for case-level state with storage semantics: database rows, cache entries, stored objects, search documents, and equivalent addressable resources that can naturally be created, queried, updated, or deleted.

Tests perform all arrange and artifact inspection against such sources through public function-scoped repository fixtures. They never request raw database connections, Redis clients, S3 clients, search clients, or private repository dependencies.

Repository classes are ordinary allowed support classes under `tests/repositories/`; they are not pytest test classes. Public fixtures constructing them live in `tests/fixtures/` and depend on the relevant private isolated client or on the exact `Connection`/`AsyncConnection` yielded by `_database_transaction`.

Do not import or use SQLAlchemy `Session`, `AsyncSession`, `sessionmaker`, or `async_sessionmaker` anywhere in test functions or test support. Database repositories execute SQLAlchemy statement objects through `Connection.execute` or `AsyncConnection.execute`, matching the project's concurrency model: `select()`, `insert()`, `update()`, and `delete()`. Do not use ORM unit-of-work methods such as `add`, `add_all`, `flush`, `refresh`, relationship mutation, or session query APIs. The production application may keep its own ORM session internally; test composition passes only the outer connection through a production-owned binding hook.

Repositories manipulate case data only. They do not provision/drop databases, buckets, namespaces, or indexes; do not run migrations; do not send the HTTP request/job/message under test; and do not contain assertions.

Do not model transports, queues, topics, streams, deliveries, or emitted messages as repositories. Use domain Publishers and Collectors from `tests/messaging/`.

## Repository interfaces

Group by the state being mutated or observed: model/table, aggregate root, cache namespace, object resource type, or another coherent ownership boundary. A helper belongs to the repository that owns its target state; never place it in a neighboring repository merely because that repository can discover a foreign key or identifier. Implement only operations tests need, using canonical names:

- `create(**overrides)`;
- optional `create_many(amount, **overrides)`;
- `get_one(**filters)`;
- `get_one_or_none(**filters)`;
- `get_many(**filters)`;
- `count(**filters)`;
- `exists(**filters)` for one clearly defined resource/state;
- `update(target, **changes)`;
- `delete(target)`;
- explicit `update_many`/`delete_many` only for a real reusable bulk case.

Do not add generic aliases such as `get`, `find`, `fetch`, `list`, or `remove`. `get_one` requires exactly one match; `get_one_or_none` returns `None` only for zero and rejects multiplicity; `get_many` returns a concrete collection; `count` returns an integer; `exists` returns a boolean.

For an ordinary single-resource repository, read/cardinality methods share optional keyword-only exact-match filters. No filters means the complete already-isolated case scope. Add a domain-named query only when a join, predicate, ordering, projection, or relationship cannot be expressed clearly with exact filters. Never rely on incidental store order.

`create(**overrides)` generates only the minimally valid default resource: every required field/relationship receives a fresh in-constraint generated value; optional fields remain absent so model/store defaults apply; explicit genuinely case-specific overrides apply last. Review this against the actual table/resource contract—requiredness, nullability, defaults, keys, and body constraints—not against what an existing fixture happens to provide. For object/file repositories, ordinary `create()` generates a minimal valid key/body itself; tests supply them only when their value is the case.

Factor minimal value construction into one private builder used by both write paths. `create` builds one value set and performs one insert. `create_many` calls the builder once per item so values remain fresh, then performs one real bulk insert and returns the complete typed collection; it never calls `create` in a loop. For a multi-store aggregate, preserve the same principle wherever the involved APIs support bulk semantics: a domain bulk constructor delegates to lower-level bulk methods and must not conceal repeated single-record writes.

Recognized domain kinds/roles/statuses/states use semantic constructors:

```python
await media_asset_repository.create_avatar()
await user_repository.create_admin()
await order_repository.create_pending()
```

Do not write raw discriminator calls such as `create(media_type="avatar")` or `create(status="pending")` in tests. Each semantic method delegates to `create`, calculates fresh execution-time defaults, and applies defining fields last so `**overrides` cannot contradict its name. Use base `create(...)` explicitly for an intentionally nonstandard/contradictory edge state.

`update` and `delete` target one explicit model/resource or stable identifier. Bulk variants accept explicit filters and return the affected count.

Database repositories use the same transaction-owned `Connection`/`AsyncConnection` as the application and never independently commit, roll back, begin another transaction, open an engine/connection, or escape the transaction. Build statements against mapped tables. Return explicit immutable DTOs/records for multi-column domain results and scalars for counts, existence checks, identifiers, and primitive projections—never generic SQL row mappings or session-bound ORM instances. Return a mapping only when that mapping is itself the explicit stored domain value, such as JSON/JSONB metadata:

```python
class UserRepository:
    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def create(self, **overrides: object) -> UserRecord:
        values = minimal_user_values() | overrides
        result = await self._connection.execute(
            insert(User.__table__).values(**values).returning(*User.__table__.c)
        )
        return UserRecord(**result.mappings().one())

    async def get_one(self, **filters: object) -> UserRecord:
        statement = select(User.__table__)
        for field, value in filters.items():
            statement = statement.where(User.__table__.c[field] == value)
        result = await self._connection.execute(statement)
        return UserRecord(**result.mappings().one())
```

## Aggregate repositories

When one coherent state requires coordinated work across several tables or stores, create a narrowly named aggregate/domain repository. Do not copy multi-repository setup into tests, force it into an unrelated model repository, or create a generic `TestRepository`/`DataRepository`.

Treat one arrange/inspection operation requiring multiple repositories in the test as a missing capability. The aggregate fixture owns private clients/connections/lower-level repositories; the test receives only the aggregate public fixture for that operation. A test may still use several repositories for genuinely independent entities or observations.

Aggregate `create(**overrides)` builds the minimally valid coherent aggregate across its stores. It may generate object bodies/keys, persist objects, propagate returned metadata into database rows, and return one stable domain object. Specialized constructors delegate to this base path.

Do not expose one broad aggregate `exists()` when it collapses independently meaningful states. Provide one method per domain observation:

```python
class MediaAssetRepository:
    def __init__(self, connection, objects) -> None:
        self._media = MediaRepository(connection)
        self._objects = objects

    async def create(self, **overrides: object) -> Media:
        original = await self._objects.create(body=generators.binary())
        preview = await self._objects.create(body=generators.binary())
        return await self._media.create(
            storage_key=original.key,
            preview_storage_key=preview.key,
            **overrides,
        )

    async def create_avatar(self, **overrides: object) -> Media:
        return await self.create(**(overrides | {"media_type": "avatar"}))

    async def media_exists(self, media: Media) -> bool:
        return await self._media.exists(id=media.id)

    async def original_exists(self, media: Media) -> bool:
        return await self._objects.exists(media.storage_key)

    async def preview_exists(self, media: Media) -> bool:
        return await self._objects.exists(media.preview_storage_key)
```

Name observations in domain/resource terms, not hidden backend terms such as `s3_exists` or `database_exists`. Separate methods make partial deletion/leakage visible instead of redefining `exists` to mean “any constituent remains”.

Assert those independent observations directly. Do not return `(False, False)` and do not synthesize a mapping/dataclass solely to collapse assertions:

```python
async def test_deletes_media(media_asset_repository, worker_client):
    media = await media_asset_repository.create_avatar()

    await worker_client.process(media.id)

    assert await media_asset_repository.media_exists(media) is False
    assert await media_asset_repository.original_exists(media) is False
    assert await media_asset_repository.preview_exists(media) is False
```

## Artifact inspection

Start every test from no mutable application state left by another test. Inspect newly produced database artifacts without filters by default:

- `get_one()` proves exactly one artifact;
- exact `get_many()` collection comparison proves content and cardinality;
- `count()` proves cardinality when content is not the contract;
- `count() == 0` proves absence when no stable target is available;
- a focused `exists(...)` proves one clearly identified resource/state.

Do not query by an ID returned by the operation merely to hide unexpected extras. Add filters only when the case explicitly arranged unrelated records or tests selection/isolation behavior. Do not redundantly assert both count and complete collection equality.

Natural independent observations receive direct assertions. A separately bound checked observation uses `actual`/`actual_*`; arrange-only entities keep domain names. An already compound artifact receives one exact comparison. Never rebind independent observations to generic `result` or manufacture a combined object only to merge database, cache, object, status, or body assertions.

Functions defined inside test modules may perform only pure in-memory construction/transformation. If a helper creates, reads, updates, deletes, or correlates external state—or accepts fixtures/repositories to do so—move it to the narrowest repository method. Reusable payload building belongs in `payload.py`.

Reusable helpers and support APIs return named typed objects for structured internal results. Use immutable dataclasses or focused DTOs for created entities, credentials, prepared contexts, object metadata, collected messages, and any result with multiple semantically named fields. Do not make callers remember string keys in `dict[str, object]` or positions in tuples. A dictionary remains appropriate only when the dictionary itself is the public/natural value: JSON or message payload, headers, configuration overrides, arbitrary metadata, or an intentionally raw stored mapping. Convert multi-column database result mappings to DTOs before returning them from repositories.

Preserve and reuse known preparation data. A repository or fixture that creates an entity returns the complete typed record required by downstream setup, including stable storage identifiers needed to address related state. Client/worker/consumer fixtures, state repositories, and public entity fixtures reuse that record rather than issuing `get_one`, `select`, index scans, Redis reads, or equivalent lookups merely to recover known setup data. Pass the known identifier into the repository that owns the next mutation; do not make another repository rediscover it and then mutate foreign state. Re-read when a later setup step or the tested application operation may have changed persisted state, or when the current persisted state is itself the artifact. Disposable intermediates that no consumer needs do not have to be returned.

## Generated data

Do not keep case-specific payloads, messages, rows, or object bodies as ready-made JSON/YAML/CSV/binary cases. Generate them during arrange through one project-owned facade and ordinary builders.

For a new suite, use `tests.generators/` as the single public facade. Select the backend during onboarding; Faker is the default, not the public interface contract. Keep backend initialization and providers in private domain modules and export only stable domain generator functions/objects. Tests and payload builders never import Faker/provider classes directly. Preserve a coherent existing facade in a mature suite instead of renaming it mechanically.

Choose a random effective seed for every ordinary run, initialize the backend before generated values are used, and report the seed in test-session output so a failed run can be reproduced. Accept an explicit CLI seed override. Under the same effective seed, providers remain deterministic and produce values inside domain/model constraints. Parallel workers may derive stable worker sub-seeds, but environment resource uniqueness also includes a run/worker identifier and never relies on generated data alone.

When a file itself is the public contract, create a file-contract builder that produces successful, boundary, and invalid variants. The builder may use checked-in real files as templates, but tests do not substitute a directory of ready-made cases for an explicit matrix. Return bytes/file-like values when natural; let a fixture own any temporary filesystem lifecycle.

## Payload builders

Generated-data access and functions that build in-memory request/message data are never fixtures. Put component-specific payload/data functions in a neighboring `payload.py` and import them directly. This does not prohibit lifecycle-bound fixtures from returning persisted entities through the typed preparation context described in the fixture reference:

```python
def user_payload(**overrides: object) -> dict[str, object]:
    values = {
        "name": generators.user_name(),
        "email": generators.email(),
    }
    return values | overrides
```

Repositories own persisted state; payload builders own in-memory request/message mapping values; fixtures own lifecycle and injected capabilities. Do not replace a natural JSON/message dictionary with a DTO merely to satisfy the typed-helper rule.

## Compound-value matchers

When the natural actual value is an object, dictionary, list, or nested structure, compare it as one whole value. Use exact literals for known leaves and `tests.cmp` matchers only for dynamic constraints:

```python
assert actual_response.json() == {
    "id": AnyStr(),
    "name": AnyStr(length=10),
    "retry_count": AnyInt(lte=3),
    "steps": OrderedList([{"name": "created", "position": 1}]),
    "tags": UnorderedList(["featured", AnyStr(length_gt=2)]),
}

assert actual_created == Object(
    id=AnyUUID(),
    status="ready",
    score=AnyInt(gte=0),
)
```

Matcher classes are ordinary allowed support classes, never fixtures or pytest test classes. Keep one public `tests.cmp` import surface and private implementation modules. Matchers implement pure exact-type-aware `__eq__`, useful constraints, constructor validation, immutability, and informative `repr`; they contain no fixtures, generators, clocks, I/O, or application access.

Matcher constructor validation compares only constraints the caller supplied. Never substitute finite numeric/string-length sentinels for an unbounded side: domains may exceed an arbitrary machine-width assumption, and a valid matcher such as `AnyInt(gt=2**63)` must remain constructible. Validate each present bound directly, then validate only present lower/upper pairs against each other.

`Object(...)` (or one consistently named equivalent exposed by `tests.cmp`) compares an object/DTO as one natural value. By default it requires exactly the advertised public attributes and recursively compares their values with literals or nested matchers. Allow an optional exact type constraint only when the output type itself is public and contractual; using that type for `isinstance`-style matching does not permit constructing expected values, applying production defaults/validation, or reusing production serialization. Partial attribute matching must be explicit and reserved for intentionally extensible public objects, never used to ignore unknown stable fields.

`UnorderedList` preserves exact length and duplicate multiplicity with correct one-to-one matching. Use an ordinary list for exact ordered literals, `OrderedList` when matcher diagnostics/composition help, and `UnorderedList` only when order is genuinely not contractual.

## Time-dependent artifacts

Never freeze/patch time or use `freezegun`. Capture a real interval around the public operation, then retrieve the artifact through its repository:

```python
started_at = datetime.now(UTC)

actual_response = await api_client.post(PATH, json=user_payload())

finished_at = datetime.now(UTC)
actual_created = await user_repository.get_one()
assert started_at <= actual_created.created_at <= finished_at
```

Capture the lower bound during arrange as close as practical to invocation and the upper bound immediately after completion, before slow inspection. Use timezone-aware values, normalize database precision only when contractual, and compare interval/order rather than exact `now()`. Do not hide the artifact read in a test-local helper.

Apply the same rule to absolute expiration/deadline values and relative TTLs. For a configured duration `ttl`, an application-produced absolute expiry normally satisfies:

```python
assert started_at + ttl <= created.expires_at <= finished_at + ttl
```

For a storage TTL, capture `started_at` immediately before invocation, read the TTL through its repository immediately after deterministic completion, and then capture `observed_at`. Derive the lower bound from the real elapsed interval and the documented storage precision/rounding; the upper bound is the configured TTL. For example, with a one-second-resolution integer TTL, allow only the one-second quantization implied by that API, not an arbitrary safety margin:

```python
actual_ttl = await token_repository.get_ttl(token.id)
observed_at = datetime.now(UTC)

elapsed_seconds = (observed_at - started_at).total_seconds()
elapsed_bound = (
    math.ceil(elapsed_seconds / storage_resolution) * storage_resolution
)
expected_min_ttl = configured_ttl - elapsed_bound
assert expected_min_ttl <= actual_ttl <= configured_ttl
```

Keep configured duration and storage resolution explicit and independently sourced from the public contract/test environment. Do not copy a production TTL constant into the expectation, freeze time, sleep, retry, poll with delays, or add unexplained slack such as `expected_ttl - 2`. If the store exposes an absolute expiry artifact, prefer checking that value because it avoids read-time TTL quantization.
