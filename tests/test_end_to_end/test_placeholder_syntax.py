"""Placeholder syntax end-to-end tests"""

# pylint: disable=missing-function-docstring

import re
import pytest
import renorm as rn
from .assert_utils import assert_pattern_correctly_compiled_from_specs


# -----------------------------------------------------------
# Test no matching pattern


def test_no_match_found():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ({@price}), total: ({@price})",
            price=rn.Num(ths="'", dec=","),
        ),
        text="subtotal: 1 231,3, total: 123,45",
        expected=None,
    )


# -----------------------------------------------------------
# Test placeholder syntax errors


def test_invalid_syntax_empty_placeholder():
    with pytest.raises(ValueError, match=r"Empty.*?{}.*?not allowed"):
        rn.compile(r"\w+:?\s({})", rn.Num())


def test_invalid_syntax_incomplete_placeholder():
    with pytest.raises(ValueError, match=r"Empty.*?{@}.*?not allowed"):
        rn.compile(r"\w+:?\s({@})", rn.Num())


def test_invalid_syntax_regex_named_groups():
    """Standard library re named groups are reserved to renorm engine"""
    with pytest.raises(ValueError, match=r"Named groups.*?not allowed"):
        rn.compile(r"\w+:?\s(?P<group_name>{@0})", rn.Num())


def test_missing_positional_spec():
    with pytest.raises(IndexError, match="@1"):
        rn.compile(
            r"subtotal: ({@0}), total: ({@1})",
            rn.Num(ths=" ", dec="."),
        )


def test_missing_named_spec():
    with pytest.raises(KeyError, match="@total"):
        rn.compile(
            r"subtotal: ({@0}), total: ({@total})",
            rn.Num(ths=" ", dec="."),
        )


# -----------------------------------------------------------
# Test placeholder syntax for positional specs


def test_capture_one_positional_spec():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(r"\w+:?\s({@0})", rn.Num(dec=",")),
        text="total: 123,45",
        expected=("123.45",),
    )


def test_capture_two_positional_specs():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ({@0}), total: ({@1})",
            rn.Num(ths=" ", dec="."),
            rn.Num(dec=","),
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=("1231.3", "123.45"),
    )


def test_capture_one_of_two_positional_specs():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: {@0}, total: ({@1})",
            rn.Num(ths=" ", dec="."),
            rn.Num(dec=","),
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=("123.45",),
    )


def test_unused_positional_spec():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ({@0})",
            rn.Num(ths=" ", dec="."),
            rn.Num(dec=","),
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=("1231.3",),
    )


def test_capture_reused_positional_spec():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ({@0}), total: ({@0})",
            rn.Num(ths=" ", dec=","),
        ),
        text="subtotal: 1 231,3, total: 123,45",
        expected=("1231.3", "123.45"),
    )


def test_capture_one_of_two_reused_positional_spec():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: {@0}, total: ({@0})",
            rn.Num(ths=" ", dec=","),
        ),
        text="subtotal: 1 231,3, total: 123,45",
        expected=("123.45",),
    )


# -----------------------------------------------------------
# Test placeholder syntax for named specs


def test_capture_two_named_specs():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ({@subtotal}), total: ({@total})",
            subtotal=rn.Num(ths=" ", dec="."),
            total=rn.Num(dec=","),
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=("1231.3", "123.45"),
    )


def test_capture_one_of_two_named_specs():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ({@subtotal}), total: {@total}",
            subtotal=rn.Num(ths=" ", dec="."),
            total=rn.Num(dec=","),
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=("1231.3",),
    )


def test_unused_named_spec():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ({@0})",
            rn.Num(ths=" ", dec="."),
            total=rn.Num(dec=","),
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=("1231.3",),
    )


def test_capture_reused_named_spec():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ({@value}), total: ({@value})",
            value=rn.Num(ths=" ", dec=","),
        ),
        text="subtotal: 1 231,3, total: 123,45",
        expected=("1231.3", "123.45"),
    )


def test_capture_one_of_two_reused_named_spec():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: {@value}, total: ({@value})",
            value=rn.Num(ths=" ", dec=","),
        ),
        text="subtotal: 1 231,3, total: 123,45",
        expected=("123.45",),
    )


# -----------------------------------------------------------
# Test placeholder syntax for positional and named specs


def test_capture_one_positional_and_one_named_specs():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ({@0}), total: ({@total})",
            rn.Num(ths=" ", dec="."),
            total=rn.Num(dec=","),
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=("1231.3", "123.45"),
    )


# -----------------------------------------------------------
# Test mixing capture groups with and without renorm normalization


def test_capture_spec_and_capture_without_normalization():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ([\d ]+,\d+), total: ({@value})",
            value=rn.Num(ths=" ", dec=","),
        ),
        text="subtotal: 1 231,3, total: 123,45",
        expected=("1 231,3", "123.45"),
    )


# -----------------------------------------------------------
# Test placeholder syntax compatibility with re pattern syntax


def test_placeholder_outside_lookahead_lookbehind():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"(?<=subtotal: )({@0})(?=, total:)",
            rn.Num(ths=" ", dec="."),
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=("1231.3",),
    )


def test_placeholder_inside_lookahead():
    """Expected to fail by re standard library"""
    with pytest.raises(re.PatternError, match="requires fixed-width pattern"):
        rn.compile(r"(?<=subtotal: ({@0}))", rn.Num(ths=" ", dec="."))


def test_placeholder_inside_lookbehind():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"(?= ({@0}), total)",
            rn.Num(ths=" ", dec="."),
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=("1231.3",),
    )
