# Authoritative requirements

- `POST /gift` is disabled. It returns `gift.unavailable`, publishes no task,
  creates no cache operation, and does not change the balance.
- `GET /media/{media_id}` grants access only when the current actor owns the
  `(actor_id, media_id)` access record.
- `POST /generation` snapshots Premium eligibility when the operation starts;
  expiry while the provider is in flight does not change that decision.
- `POST /daily-message` resets its allowance on the next local calendar day in
  the actor's IANA timezone.
- `GET /protocol` exists solely to render documentation and is not a functional
  product contract.
- `gift.legacy_success` and `generation.start` are not supported aliases.
