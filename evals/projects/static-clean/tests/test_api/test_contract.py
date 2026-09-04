from datetime import UTC, datetime

from app.config import Settings
from tests.cmp import AnyDateTime


async def test_contract(client, repository, settings: Settings):
    await repository.create(application_id=settings.application_id)
    started_at = datetime.now(UTC)

    actual_response = await client.get("/resource")

    finished_at = datetime.now(UTC)
    assert actual_response.json() == {
        "created_at": AnyDateTime(gte=started_at, lte=finished_at),
    }
