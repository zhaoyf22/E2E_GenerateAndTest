"""Integration test skeleton using Testcontainers.

Requires: pip install testcontainers[postgres,redis]
"""

import pytest

pytest.importorskip("testcontainers")


@pytest.mark.skip(reason="TestForge scaffold: implement ${id}")
def test_scaffold_with_real_dependency() -> None:
    """${title}

    Steps:
${steps}
    """
    raise NotImplementedError("${id}")
