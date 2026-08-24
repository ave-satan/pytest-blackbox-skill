#!/usr/bin/env python3
"""Run only mechanically provable pytest-blackbox checks."""

from pytest_blackbox_tools.check_cli import main

if __name__ == "__main__":
    raise SystemExit(main(include_semantic=False, command="lint"))
