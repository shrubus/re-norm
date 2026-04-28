"""Unit tests for renorm specs"""

# pylint: disable=missing-function-docstring

import pytest
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


# -----------------------------------------------------------
# Test Num basics


def test_num_subclass_norm():
    assert issubclass(rn.Num, rn.NormSpec)


# -----------------------------------------------------------
# Test Num use cases

patterns = {
    "default": rn.compile(r"({@0})", rn.Num()),
}

nobr = ["\u00a0", "\u202f"]  # no-break and no-break narrow space
test_data = [
    ("33.4", patterns["default"], ("33.4",)),
    ("-33.4", patterns["default"], ("-33.4",)),
    ("- 33.4", patterns["default"], ("-33.4",)),
    ("-  33.4", patterns["default"], ("33.4",)),  # danger/ambiguity
    (f"-{nobr[0]}33.4", patterns["default"], ("-33.4",)),
    (f"-{nobr[1]}33.4", patterns["default"], ("-33.4",)),
    ("1333.4", patterns["default"], ("1333.4",)),
    ("1 333.4", patterns["default"], (None,)),
    ("1'333.4", patterns["default"], (None,)),
    ("1,333.4", patterns["default"], (None,)),
    (f"1{nobr[0]}333.4", patterns["default"], (None,)),
    (f"1{nobr[1]}333.4", patterns["default"], (None,)),
]


@pytest.mark.parametrize("text,pattern,expected", test_data)
def test_num_spec_capture(text, pattern, expected):
    print(pattern.pattern)
    match = pattern.search(text)
    assert match.groups() == expected
