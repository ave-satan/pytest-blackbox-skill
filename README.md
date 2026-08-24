# pytest-blackbox

<img src="assets/logo.png" alt="Pytest Blackbox logo" width="160">

Black-box pytest contract testing workflows for Codex and Claude Code.

Pytest Blackbox helps coding agents discover, write, repair, review, and audit
Python contract tests through public application boundaries. It is designed for
HTTP and JSON-RPC APIs, jobs, schedulers, workers, message handlers, databases,
caches, object stores, brokers, and outbound HTTP integrations.

> **Status:** early release. Marketplace publication is planned separately.

## What it optimizes for

- Public contracts instead of implementation details.
- The real composed application instead of unit tests.
- Independent inputs and expectations instead of production-derived oracles.
- No mocking or monkeypatching of application source internals.
- Protocol-compatible test infrastructure with isolated logical resources.
- Deterministic completion without sleeps, retry delays, or messaging timeouts.
- Fixture-owned lifecycle, cleanup, configuration, and application composition.
- Focused cases with readable parameter IDs and explicit observable outcomes.

The complete policy is documented in [core/POLICY.md](core/POLICY.md). Project
choices, such as test layout and external-service strategy, are recorded in the
project's existing `pyproject.toml` rather than in a separate plugin config.

## Workflows

| Workflow | Purpose |
| --- | --- |
| `discover` | Inspect a project read-only and propose project-wide test policy. |
| `write` | Add black-box contract coverage for requested application behavior. |
| `repair` | Diagnose and repair existing failing or nondeterministic tests. |
| `review` | Perform a focused, read-only review of tests or a test diff. |
| `audit` | Audit a complete suite or explicitly named full component surface. |

All workflows support model-driven automatic invocation. They can also be
invoked explicitly.

### Codex

```text
$pytest-blackbox:discover
$pytest-blackbox:write
$pytest-blackbox:repair
$pytest-blackbox:review
$pytest-blackbox:audit
```

### Claude Code

```text
/pytest-blackbox:discover
/pytest-blackbox:write
/pytest-blackbox:repair
/pytest-blackbox:review
/pytest-blackbox:audit
```

## Installation

Public marketplace installation will be documented with the first release.
For local evaluation, clone the repository:

```bash
git clone https://github.com/ave-satan/pytest-blackbox-skill.git
cd pytest-blackbox-skill
```

Claude Code can load the checkout directly:

```bash
claude --plugin-dir ./
```

For Codex, expose the checkout through a local plugin marketplace following the
[official local plugin instructions](https://developers.openai.com/plugins/build/plugins#install-a-local-plugin-manually).

## Project onboarding

On first use, Pytest Blackbox looks for `[tool.pytest-blackbox]` in the nearest
applicable `pyproject.toml`. If it is absent, the `discover` workflow:

1. Scans project structure without importing or starting the application.
2. Proposes material project-wide choices with confidence and evidence.
3. Asks only about ambiguous choices.
4. Shows the exact `pyproject.toml` patch before writing anything.

Recommended defaults for a new suite are:

```toml
[tool.pytest-blackbox]
config_version = 1
layout = "standard"
prefer_test_classes = true
infrastructure = "existing-services"
compose_lifecycle = "disabled"
external_services = "intercept"
generators_backend = "faker"
```

See [references/configuration.md](references/configuration.md) for the complete
schema, adaptive choices, and non-public coverage registry.

## Bundled tooling

The plugin includes two read-only Python helpers:

```bash
python scripts/discover_project.py /path/to/project
python scripts/audit_suite.py /path/to/project
```

- `discover_project.py` gathers onboarding evidence without importing project
  code, reading common secret files, starting infrastructure, or mutating the
  project.
- `audit_suite.py` detects mechanically provable policy violations and reports
  semantic checks that still require manual review.

The helpers require Python 3.10 or newer. Python 3.11+ is recommended; Python
3.10 requires the `tomli` backport for TOML policy parsing.

## Repository structure

```text
pytest-blackbox-skill/
├── .claude-plugin/plugin.json
├── .codex-plugin/plugin.json
├── assets/
├── core/POLICY.md
├── references/
├── scripts/
├── submission/
└── skills/
    ├── audit/
    ├── discover/
    ├── repair/
    ├── review/
    └── write/
```

The shared policy lives outside `skills/` so it is loaded by the selected
workflow without becoming a duplicate `pytest-blackbox:pytest-blackbox`
command.

## Contributing

Issues and pull requests are welcome. Please open an issue before proposing a
broad policy change: universal rules should be backed by repeatable failures or
clear contract-testing invariants rather than a single project convention.

## Support and legal

- Report non-sensitive bugs and request features through
  [GitHub Issues](https://github.com/ave-satan/pytest-blackbox-skill/issues).
- Review the [Privacy Policy](PRIVACY.md) and [Terms of Use](TERMS.md).
- Do not post secrets, credentials, proprietary source code, or personal data in
  public issues.

## License

Distributed under the [MIT License](LICENSE). Copyright © 2026 ave-satan.
