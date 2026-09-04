"""Deliberately incomplete application snapshot for forward skill evaluation."""

DOCUMENTATION_ONLY_ROUTES = {("GET", "/protocol")}
FUNCTIONAL_ROUTES = {
    ("POST", "/gift"),
    ("GET", "/media/{media_id}"),
    ("POST", "/generation"),
    ("POST", "/daily-message"),
}


def media_is_available(access_records, actor_id, media_id):
    return any(record.media_id == media_id for record in access_records)


async def generation_is_premium(user, provider):
    await provider.complete()
    return user.premium_expires_at > provider.current_time


def daily_allowance_used(state, local_date):
    if state.used_at is None:
        return False
    return state.used_at.date() == local_date


def legacy_gift_worker(balance, price):
    return {"event": "gift.completed", "balance": balance - price}
