async def drain(queue):
    deliveries = []
    while (delivery := await queue.get(fail=False)) is not None:
        deliveries.append(delivery)
    return deliveries
