"""
Pytest configuration and fixtures for the Twitter Microblogging App test suite.

Fixtures:
  reset   (autouse, function scope) — wipes all in-memory storage before AND after each test.
  client  (function scope)          — a FastAPI TestClient backed by the app.
"""

import pytest
from fastapi.testclient import TestClient

from twitter_app.main import app
from twitter_app import storage


@pytest.fixture(autouse=True)
def reset():
    """
    Reset all in-memory storage before and after every test.

    autouse=True means this runs automatically for every test in the suite
    without needing to be listed in the test function's parameters.
    """
    storage.reset_storage()
    yield
    storage.reset_storage()


@pytest.fixture
def client() -> TestClient:
    """
    Return a synchronous FastAPI TestClient.

    The TestClient uses httpx under the hood and supports all HTTP methods.
    Storage is clean for each test thanks to the `reset` autouse fixture.
    """
    return TestClient(app)
