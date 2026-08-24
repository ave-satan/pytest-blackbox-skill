#!/usr/bin/env python3
"""Run safe fallback or library-backed pytest-blackbox discovery."""

from pytest_blackbox_tools.discover_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
