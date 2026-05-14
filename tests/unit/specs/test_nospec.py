"""Unit tests for renorm nospecs"""

# pylint: disable=missing-function-docstring

import renorm as rn

# -----------------------------------------------------------
# Test NOSPEC


def test_nospec_subclass_norm():
    assert issubclass(rn.specs._NoSpec, rn.NormSpec)  # pylint: disable=protected-access


def test_nospec_is_singleton():
    assert rn.NOSPEC is rn.specs._NoSpec()  # pylint: disable=protected-access


def test_nospec_pattern_is_null():
    assert rn.NOSPEC.pattern == ""


def test_nospec_normalization_is_echo():
    assert rn.NOSPEC.normalize("1 222.0") == "1 222.0"


def test_nospec_capture_empty_string():
    p = rn.compile(r"(?:\w+\s)+({@0})\d+", rn.NOSPEC)
    text = "not a spec 45"
    m = p.search(text)
    assert m[0] == text
    assert m[1] == ""
