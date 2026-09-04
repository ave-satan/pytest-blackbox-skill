from app.config import Settings
from tests.cmp import AnyDateTime


async def test_contract(client, settings: Settings):
    actual_response = await client.get("/resource")
    expected_ttl = settings.response_ttl_seconds

    assert actual_response.json() == {
        "created_at": AnyDateTime(),
        "ttl": expected_ttl,
    }
