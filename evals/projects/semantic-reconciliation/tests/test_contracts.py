async def test_gift_unavailable(client):
    actual_response = await client.post("/gift")

    assert actual_response.event == "gift.unavailable"


def test_legacy_gift_worker_success(application):
    actual = application.legacy_gift_worker(balance=100, price=20)

    assert actual == {"event": "gift.completed", "balance": 80}


async def test_media_owner_can_download(client, owner_access):
    actual_response = await client.get(f"/media/{owner_access.media_id}")

    assert actual_response.status_code == 200


async def test_premium_generation(client, premium_user):
    actual_response = await client.post("/generation", user=premium_user)

    assert actual_response.quality == "premium"


async def test_daily_message_same_day(client, used_allowance):
    actual_response = await client.post("/daily-message", state=used_allowance)

    assert actual_response.status_code == 429


async def test_protocol_document(client):
    actual_response = await client.get("/protocol")

    assert actual_response.status_code == 200
