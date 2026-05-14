"""Placeholder syntax compatibility end-to-end tests"""

# pylint: disable=missing-function-docstring

import re
import pytest
import renorm as rn
from .assert_utils import assert_pattern_correctly_compiled_from_specs

# -----------------------------------------------------------
# Test placeholder syntax compatibility with re pattern syntax


def test_placeholder_outside_lookahead_lookbehind():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"(?<=subtotal: )({@0})(?=, total:)",
            rn.Num(ths=" ", dec="."),
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=(1231.3,),
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
        expected=(1231.3,),
    )


# -----------------------------------------------------------
# Test placeholder syntax compatibility with literal braces


def test_escaped_braces_are_literal():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"\{not_a_placeholder\} ({@0})",
            rn.Num(),
        ),
        text="{not_a_placeholder} 123.45",
        expected=(123.45,),
    )


def test_raw_string_braces_are_literal():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"{not_a_placeholder} ({@0})",
            rn.Num(),
        ),
        text="{not_a_placeholder} 123.45",
        expected=(123.45,),
    )


def test_correct_use_of_f_strings_placeholders():
    str_frac = "f-string placeholder"
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            rf"{str_frac} ({{@0}})",
            rn.Num(),
        ),
        text="f-string placeholder 123.45",
        expected=(123.45,),
    )


# -----------------------------------------------------------
# Test placeholder syntax compatibility with regex quantifiers


def test_regex_quantifier():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"\w{4}: ({@0}) k€",
            rn.Num(),
        ),
        text="corn: 1.1 k€, barley: 1.2 k€",
        expected=(1.1,),
    )


def test_regex_range_quantifier():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"\w{5,6}: ({@0}) k€",
            rn.Num(),
        ),
        text="corn: 1.1 k€, barley: 1.2 k€",
        expected=(1.2,),
    )


def test_quantifier_around_capture():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"(?:item: ({@0})(?:,?\s?)){2}",
            rn.Num(),
        ),
        text="item: 1.1, item: 1.2",
        expected=(1.2,),
    )


# -----------------------------------------------------------
# Test placeholder syntax compatibility with back references


def test_backreference_to_placeholder_capture():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"({@0})-\1",
            rn.Num(),
        ),
        text="42.3-42.3",
        expected=(42.3,),
    )
