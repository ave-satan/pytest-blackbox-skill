# Expected semantic decisions

An acceptable audit must find all of these classes without seeing this file:

- `POST /gift` is partial because the test asserts its response but not the
  three explicitly absent effects.
- The legacy gift worker test is unsourced: source presence is not authority.
- Media access is missing the same-resource/different-actor isolation case.
- Generation is missing the Premium snapshot transition while the provider is
  in flight.
- Daily-message is missing the next-local-day/IANA-timezone partition.
- The documentation-only `/protocol` test is unsourced and does not count as a
  functional operation.

The report must provide nonzero `partial`, `missing`, and `unsourced` counts and
must not describe the suite as complete. It may additionally report structural
issues, but those do not substitute for these semantic decisions.
