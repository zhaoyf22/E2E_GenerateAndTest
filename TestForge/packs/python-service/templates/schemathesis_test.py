"""Contract/property test skeleton using Schemathesis.

Requires: pip install schemathesis
Set API_BASE_URL and OPENAPI_PATH in the environment.
"""

import os

import pytest

pytest.importorskip("schemathesis")
import schemathesis  # noqa: E402

schema = schemathesis.openapi.from_uri(
    os.environ.get("OPENAPI_PATH", "openapi.yaml"),
    base_url=os.environ.get("API_BASE_URL", "http://localhost:8000"),
)


@pytest.mark.skip(reason="TestForge scaffold: enable Schemathesis checks")
def test_openapi_contract() -> None:
    raise NotImplementedError("Enable @schema.parametrize() in this module")
