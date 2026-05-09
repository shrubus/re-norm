"""Performance tests"""

import time
import pytest
import renorm as rn


@pytest.mark.slow
def test_compile_scales_reasonably():
    """Fails if rn.compile scales quadratically with number of placeholders"""
    size = 500
    sizes = [size, 2 * size]
    times = []
    spec = rn.Num()
    for n in sizes:
        pattern = " ".join(["({@0})"] * n)
        t0 = time.perf_counter()
        rn.compile(pattern, spec)
        times.append(time.perf_counter() - t0)

    # crude check: doubling size should not quadruple time
    assert times[-1] < 3 * times[-2]
