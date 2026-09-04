async def drain(queue):
    deliveries = []
    while (delivery := await queue.get(fail=False, timeout=0)) is not None:
        deliveries.append(delivery)
    return deliveries
