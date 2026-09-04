# Semantic reconciliation

Use this protocol whenever a workflow writes, changes, repairs, reviews, or
audits contract tests. It turns semantic completeness into explicit evidence
without creating a persistent per-operation registry.

## Authority boundary

Expected truth comes from authoritative product requirements, accepted design
decisions, and independently owned public protocol definitions. A final
framework registration proves that an operation exists, but not what every
scenario should do. Application source reveals candidate states, branches, and
artifacts; it never promotes its current behavior to expected truth. Existing
tests are evidence to reconcile, not requirements.

When no authoritative source resolves an observable source branch, mark it
`ambiguous` and request a product decision. When an existing test has no
authoritative contract, mark it `unsourced`; do not preserve it merely because
production still contains the exercised branch.

## Transient evidence matrix

Build the matrix before editing and update it after the final case set is
known. Keep it in working notes or the task report, not project configuration.
Each row records:

- stable operation/component identity;
- precise authoritative requirement reference, or an explicit unresolved/absent
  marker for `ambiguous`/`unsourced` evidence;
- initial state and relevant actor/owner identity;
- one public stimulus;
- expected public response, event, settlement, or other direct observation;
- expected created/changed artifacts;
- explicitly promised absent or unchanged artifacts;
- owning collected test node;
- reconciliation status.

Use exactly these statuses:

- `covered`: one collected case distinguishes every independently breakable
  promise in the row;
- `partial`: a case exists but leaves at least one promised observation,
  artifact, absence, boundary, or identity dimension unprotected;
- `missing`: authoritative behavior has no distinguishing collected case;
- `ambiguous`: observable behavior exists but authoritative expected truth is
  unresolved;
- `unsourced`: an existing test asserts behavior with no authoritative basis.

Do not claim the selected scope complete while any row is `partial`, `missing`,
`ambiguous`, or `unsourced`. Report all five status counts even when some are
zero.

## Bidirectional reconciliation

Perform both passes. Neither substitutes for the other.

1. **Requirement to test.** Map every authoritative operation, scenario,
   public outcome, boundary, and direct artifact to a collected node.
2. **Test to requirement.** Map every collected behavior case back to a precise
   authoritative requirement. A route, source branch, test name, or green
   assertion is not sufficient authority.

The reverse pass must include old tests inside a changed scope. It catches
removed features, disabled behavior, obsolete compatibility promises,
documentation-only routes, accidental aliases, and implementation branches
that outlived their product requirement.

## Scenario-dimension pass

For each operation, explicitly mark each dimension below as applicable or not
applicable. Add cases only when the dimension produces an independently
observable contractual difference; never build a Cartesian product merely to
exercise branches.

- actor, owner, tenant, session, application, or namespace isolation;
- entity lifecycle and absent/present/pending/final/stale state;
- compound identity with one member changed;
- time, local date, timezone, deadline, expiry, and TTL boundaries;
- behavior-affecting configuration;
- state captured before an external call and revalidated after it;
- synchronous response, dispatch, worker execution, and later delivery phases;
- batch homogeneity, mixed outcomes, cardinality, and duplicate multiplicity;
- repetition only when an authoritative idempotency/replay/retry promise exists;
- concurrency only when both authoritative and enabled by project policy.

Whenever ownership affects selection or access, answer this question with a
case or an explicit not-applicable reason:

> Can an artifact owned by actor A incorrectly change the result observed by
> actor B for the same resource?

Whenever application state may change while an external dependency is in
flight, distinguish the contractual snapshot from any required post-call
guard. Use a deterministic Service-controlled transition or another supported
composition seam; never use sleep, time freezing, timeout races, or
application-source patching.

## Complete-promise pass

A case is complete only when it distinguishes every independently breakable
part of its requirement. Reconcile the natural public response and every direct
artifact separately, including explicitly promised absence or preservation.
Examples include an exact queued message, exact stored-row count, unchanged
balance, absent cache operation, or no emitted task.

Do not assert internal calls or manufacture a combined result object. Keep
natural observations separate when they are naturally separate, but do not
mark the matrix row `covered` merely because one of several promised outcomes
is asserted.

## Independent-encoding pass

Trace every input and expected value in a covered row to test-owned data or an
authoritative literal. Production `Settings`, DTOs, schemas, defaults,
constants, validators, codecs, registries, and private algorithms may compose
the application or annotate an actual value, but must not calculate the input
boundary or oracle.

For configuration-controlled behavior, bind the explicit override and its
independent expected value together in parametrization or a test-owned immutable
case context. The test may request the indirect production-settings fixture to
select composition, but does not read it to rediscover the value it supplied.
When requirements promise only a public invariant such as stable selection,
do not copy the current hash/ranking/selection algorithm into test support to
predict one implementation-specific result.

Counterfactually ask whether changing only the production constant/default/
codec/algorithm would also change the expected value. If so, the test has a
shared oracle and is not `covered`.

## Counterfactual source pass

Inspect every application-owned condition in scope that can change a public
response or direct artifact. Ask which collected case would fail if the
condition were deleted, inverted, moved across an external call, or scoped to
the wrong actor/identity member.

- If an authoritative result would change and no test distinguishes it, add a
  `missing` or `partial` row.
- If all changes collapse to an already protected public result, do not add a
  branch test.
- If expected truth is not authoritative, add an `ambiguous` source candidate
  rather than copying implementation behavior into the oracle.

Mutation tooling may be used only as an optional isolated probe. It never
replaces this reasoning, modifies the user's working tree, or authorizes
production changes during review/audit.

## Scoped contract drift

For `write`, `develop`, and `repair`, compare the requested/current contract
with every existing case in the complete owning component before editing:

- added behavior creates new forward rows;
- changed behavior updates its oracle and searches for contradictory old rows;
- removed or disabled behavior searches for tests that still assert it;
- renamed routes/discriminators/aliases require authority for both old and new
  identities;
- a shift between synchronous response, dispatch, worker execution, and later
  delivery moves ownership to the appropriate component rather than extending
  one test across phases.

Limit this pass to the requested owning component and changed shared support.
It is not permission for an unrelated full-suite refactor.

## Completion report

Report the selected boundary, authoritative sources, matrix counts by status,
resolved source-only candidates, excluded non-contract surfaces, collected
node evidence, executed checks, and remaining blockers. A green suite,
operation-directory census, primary `test_contract`, or clean deterministic
lint is evidence but never sufficient for semantic completeness.

Also inspect the real defaults of protocol/library calls used by test support.
An API named `get`, `drain`, or `no_wait` is not deterministic evidence if it
inherits a positive timeout, retry, backoff, or quiet window. Disable these
explicitly when supported; otherwise use the documented minimum and report the
unavoidable bound.
