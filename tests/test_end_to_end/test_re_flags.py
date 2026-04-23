"""Basic end-to-end tests"""

# pylint: disable=missing-function-docstring

import re
import renorm as rn
from .assert_utils import assert_pattern_correctly_compiled_from_specs

# -----------------------------------------------------------
# Test use of re flags


def test_re_verbose_flag():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"""
        subtotal:\s*({@0})  # subtotal
        ,\s*total:\s*({@1}) # total
        """,
            rn.Num(ths=" ", dec="."),
            rn.Num(dec=","),
            flags=re.VERBOSE,
        ),
        text="subtotal: 1 231.3, total: 123,45",
        expected=("1231.3", "123.45"),
    )


def test_re_ignorecase_flag():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"subtotal: ({@0}),\s* total: ({@1})",
            rn.Num(ths=" ", dec="."),
            rn.Num(dec=","),
            flags=re.IGNORECASE,
        ),
        text="subtotal: 1 231.3, TOTAL: 123,45",
        expected=("1231.3", "123.45"),
    )


def test_re_verbose_and_ignorecase_flags():
    assert_pattern_correctly_compiled_from_specs(
        p=rn.compile(
            r"""
        subtotal:\s*({@0})  # subtotal
        ,\s*total:\s*({@1}) # total
        """,
            rn.Num(ths=" ", dec="."),
            rn.Num(dec=","),
            flags=re.VERBOSE | re.IGNORECASE,
        ),
        text="subtotal: 1 231.3, TOTAL: 123,45",
        expected=("1231.3", "123.45"),
    )
