"""E2E test config: pin the dev-server base URL used by pytest-playwright.

Defaults to the already-running dev server (port 5000). Override with
``--base-url`` or the ``TQ_E2E_BASE`` environment variable.
"""
import os

import pytest

_DEFAULT = os.environ.get("TQ_E2E_BASE", "http://127.0.0.1:5000")


def pytest_configure(config):
    if not config.getoption("base_url"):
        config.option.base_url = _DEFAULT