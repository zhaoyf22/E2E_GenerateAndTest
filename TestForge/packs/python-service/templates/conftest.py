"""Shared pytest fixtures for a Python service."""

import pytest


@pytest.fixture()
def api_client():
    """Return a test client for the service under test.

    Replace with the project's FastAPI/Flask/Django test client.
    """
    pytest.skip("TestForge scaffold: configure api_client fixture")
