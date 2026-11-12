"""Property-based test skeleton using Hypothesis.

Requires: pip install hypothesis
"""

import pytest

pytest.importorskip("hypothesis")
from hypothesis import given, strategies as st  # noqa: E402


@pytest.mark.skip(reason="TestForge scaffold: implement ${id}")
@given(st.integers(), st.integers())
def test_scaffold_property(a: int, b: int) -> None:
    """${title}

    Replace with the invariant the implementation must satisfy.
    """
    raise NotImplementedError("${id}")
