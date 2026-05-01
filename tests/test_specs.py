"""Unit tests for renorm specs"""

# pylint: disable=missing-function-docstring
# pylint: disable=unused-argument
# pylint: disable=protected-access
# pylint: disable=invalid-name

import re
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


test_data_decimal_comma = [
    # grouping ...
    ("1.234", "1.234", True),
    # no grouping, no signal
    ("1234,5", "1234,5", True),
    # no grouping, signal (-)
    ("-1234,5", "-1234,5", True),
    ("- 1234,5", "- 1234,5", True),
    # no grouping, signal (+)
    ("+1234,5", "+1234,5", True),
    ("+ 1234,5", "+ 1234,5", True),
]

test_data_num_default = [
    # decimal only
    (".1234", ".1234", True),
    ("-.1234", "-.1234", True),
    ("+.1234", "+.1234", True),
    ("- .1234", "- .1234", True),
    ("+ .1234", "+ .1234", True),
    # no grouping, integer, no signal
    ("1", "1", True),
    ("12", "12", True),
    ("1234", "1234", True),
    # no grouping, integer, signal (-)
    ("-1234", "-1234", True),
    ("- 1234", "- 1234", True),
    # no grouping, float, no signal
    ("1234.5", "1234.5", True),
    # no grouping, float, signal (-)
    ("-1234.5", "-1234.5", True),
    ("- 1234.5", "- 1234.5", True),
    # no grouping, float (.), signal (-) with nbsp
    ("-\xa01234.5", "-\xa01234.5", True),
    # grouping, non-mixed, integer, no signal
    ("1 234", "1 234", True),
    ("1 234 567", "1 234 567", True),
    ("1'234'567", "1'234'567", True),
    ("1,234,567", "1,234,567", True),
    ("1\xa0234\xa0567", "1\xa0234\xa0567", True),
    # grouping, non-mixed, integer, signal
    ("-1 234", "-1 234", True),
    ("-\xa01 333.4", "-\xa01 333.4", True),
    ("+1 234 567", "+1 234 567", True),
    ("- 1'234'567", "- 1'234'567", True),
    ("+ 1,234,567", "+ 1,234,567", True),
    # wrong grouping using decimal separator
    ("1.234.567", "1.234.567", False),
    ("1.234.5", "1.234.5", False),
    # grouping, non-mixed, float, no signal
    ("1 234.5", "1 234.5", True),
    ("1 234 567.8", "1 234 567.8", True),
    ("1 234\xa0567.8", "1 234\xa0567.8", True),
    ("1'234'567.8", "1'234'567.8", True),
    ("1,234,567.8", "1,234,567.8", True),
    ("1\xa0234\xa0567.8", "1\xa0234\xa0567.8", True),
    # grouping, non-mixed, float, signal
    ("-1 234.5", "-1 234.5", True),
    ("- 1 234 567.8", "- 1 234 567.8", True),
    ("+ 1'234'567.8", "+ 1'234'567.8", True),
    ("+1,234,567.8", "+1,234,567.8", True),
    # ==================================================
    # grouping, mixed, integer
    ("1 333'222", "1 333'222", False),
    # grouping, mixed, float
    ("1 333'222.4", "1 333'222.4", False),
    ("1,333 222.4", "1,333 222.4", False),
    ("1'333,222.4", "1'333,222.4", False),
    # grouping and no grouping,float
    ("1333'333.4", "1333'333.4", False),
    # =====================================
    # ("  -   1  333   222   .4  ", "-   1  333   222   .4", False),
    # ("1  \xa0333.4", "1  \xa0333.4", False),
    ("1 333.4abc", "1 333.4", True),
    ("1 333.4'", "1 333.4", True),
    ("0", "0", True),
    ("00", "00", True),
    ("000.000", "000.000", True),
    ("1 333.4ab3.4", "1 333.4", True),
    ("1 333.4£", "1 333.4", True),
    ("$1 333.4", "1 333.4", True),
    # wrong ths
    ("1;333;222.4", "1;333;222.4", False),
    ("1_333_222.4", "1_333_222.4", False),
    # dec vs ths ambiguity
    ("1.333.222.4", "1.333.222.4", False),
    ("1.333.4", "1.333.4", False),
    ("1,333,4", "1,333,4", False),
    # wrong grouping
    ("1,333,4 5", "1,333,4 5", False),
    ("0,0.0.0'0_0", "0,0.0.0'0_0", False),
    ("0,0.0a0'0_0", "0,0.0", False),
    ("1'22'33,4", "1'22'33,4", False),
    ("1 22 33,4", "1 22 33,4", False),
    # isolated symbols
    (" - ", None, NaN := float("nan")),
    (" + ", None, NaN),
    (" . ", None, NaN),
    (" ' ", None, NaN),
]


@pytest.mark.parametrize("text, raw, filtered", test_data_num_default)
def test_num_default_raw_capture(text, raw, filtered):
    p = re.compile(rn.Num().pattern)
    m = p.search(text)
    result = m.group(0) if m is not None else None
    assert result == raw


@pytest.mark.parametrize("text, raw, filtered", test_data_num_default)
def test_num_default_raw_capture_is_number(text, raw, filtered):
    if raw is not None:
        result = rn.Num()._is_number_candidate(raw)
        assert result == filtered


# stress_num_data = [
#     # --- Ungrouped integers of arbitrary length ---
#     ("123456789.0", r"({@0})", rn.Num(), ("123456789.0",)),
#     # --- Mixed separators (allowed by default: mixed=True) ---
#     ("1 333'222.4", r"({@0})", rn.Num(), ("1333222.4",)),
#     ("1,333 222.4", r"({@0})", rn.Num(), ("1333222.4",)),
#     ("1'333,222.4", r"({@0})", rn.Num(), ("1333222.4",)),
#     # --- Invalid separators (in _invalid_ths) should be rejected ---
#     ("1.333.222.4", r"({@0})", rn.Num(), None),  # dot is decimal, not ths
#     ("1;333;222.4", r"({@0})", rn.Num(), None),  # semicolon never allowed
#     ("1_333_222.4", r"({@0})", rn.Num(), None),  # underscore never allowed
#     # --- NBSP / NNBSP variants ---
#     (f"1{nbsp[0]}333{nbsp[1]}222.4", r"({@0})", rn.Num(), ("1333222.4",)),
#     (f"-{nbsp[1]}1{nbsp[0]}333.4", r"({@0})", rn.Num(), ("-1333.4",)),
#     # --- Decimal edge cases ---
#     (".4", r"({@0})", rn.Num(), (".4",)),  # leading decimal
#     ("-.4", r"({@0})", rn.Num(), ("-.4",)),
#     ("+.4", r"({@0})", rn.Num(), (".4",)),  # plus removed
#     # --- Whitespace hell ---
#     ("  -   1  333   222   .4  ", r"({@0})", rn.Num(), (None,)),
#     (f"1{nbsp[0]} {nbsp[1]}333.4", r"({@0})", rn.Num(), (None,)),
#     # --- Trailing garbage should truncate or reject cleanly ---
#     ("1 333.4abc", r"({@0})", rn.Num(), ("1333.4",)),  # suffix lookahead stops at '4'
#     ("1 333.4'", r"({@0})", rn.Num(), ("1333.4",)),  # trailing ths char rejected by suffix
#     # --- Ambiguous separators: multiple decimals (invalid) ---
#     ("1.333.4", r"({@0})", rn.Num(), None),
#     ("1,333,4", r"({@0})", rn.Num(dec=","), None),
#     # --- Lone sign ---
#     ("-", r"({@0})", rn.Num(), None),
#     ("+ ", r"({@0})", rn.Num(), None),
#     # --- Zero variants ---
#     ("0", r"({@0})", rn.Num(), ("0",)),
#     ("00", r"({@0})", rn.Num(), ("00",)),
#     ("000.000", r"({@0})", rn.Num(), ("000.000",)),
# ]


# @pytest.mark.parametrize("text, pat, spec, expected", stress_num_data)
# def test_stress_default_num_spec_capture(text, pat, spec, expected):
#     p = rn.compile(pat, spec)
#     m = p.search(text)
#     result = m.groups() if m else None
#     assert result == expected
