#!/usr/bin/env python3
"""Run deterministic checks and the preserved semantic audit checklist."""

from pytest_blackbox_tools.check_cli import main

if __name__ == "__main__":
    raise SystemExit(main(include_semantic=True, command="audit"))
