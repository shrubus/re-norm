"""Assertion helpers"""

import renorm as rn


def assert_pattern_correctly_compiled_from_specs(
    p: rn.Pattern,
    text: str,
    expected: tuple[str | None, ...] | None,
) -> None:
    """
    Helper function to assert renorm pattern is correctly constructed from specs
    """

    assert isinstance(p, rn.Pattern), f"compile() should return renorm.Pattern not {type(p)!r}"
    m = p.search(text)
    if m is not None:
        actual = m.groups()
        assert isinstance(m, rn.Match), f".search() should return renorm.Match, not {type(p)!r}"
    else:
        actual = None
    assert actual == expected, f"Normalized groups differ: actual={actual!r} expected={expected!r}"
