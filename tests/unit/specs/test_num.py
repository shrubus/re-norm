"""Unit tests for renorm specs"""

# pylint: disable=missing-function-docstring
# pylint: disable=unused-argument
# pylint: disable=protected-access
# pylint: disable=invalid-name

import re
from itertools import product
import pytest
import renorm as rn
from ._data import number_literal

##########################################################
##### Num() basic tests
##########################################################


def test_num_subclass_norm():
    assert issubclass(rn.Num, rn.NormSpec)


##########################################################
##### Num() initialization
##########################################################


def ids_num_init(case):
    dec, ths = case
    return f"Num(dec={dec}, ths={ths})"


def test_num_default_parameters():
    num = rn.Num()
    assert num.dec == "."
    assert num.ths == ""


@pytest.mark.parametrize("case", ((sep, sep) for sep in [",", "."]), ids=ids_num_init)
def test_num_same_separators(case):
    dec, ths = case
    with pytest.raises(ValueError):
        rn.Num(dec=dec, ths=ths)


@pytest.mark.parametrize("case", ((dec, "") for dec in [";", ".,"]), ids=ids_num_init)
def test_num_wrong_dec_separator(case):
    dec, ths = case
    with pytest.raises(ValueError):
        rn.Num(dec=dec, ths=ths)


@pytest.mark.parametrize("case", ((".", ths) for ths in ["_", ". "]), ids=ids_num_init)
def test_num_wrong_ths_separator(case):
    dec, ths = case
    with pytest.raises(ValueError):
        rn.Num(dec=dec, ths=ths)


@pytest.mark.parametrize(
    "case", product([",", ".", ""], [" ", "'", ",", ".", ""]), ids=ids_num_init
)
def test_num_pattern_raw_capture_independent_on_instance(case):
    _dec, _ths = case
    default_pattern = rn.Num().pattern
    if _dec != "" and _dec == _ths:
        pytest.skip("dec == ths")
    assert default_pattern == rn.Num(dec=_dec, ths=_ths).pattern


##########################################################
##### Well-formed literal numbers
##########################################################


def idsfn(case: tuple[rn.Num, tuple[str, float | int]]):
    num, (lit, nbr) = case
    return f'{num!r}; (lit, nbr) = ("{lit}", {nbr})'


pos_ints: list[float | int] = [0, 1234, 12345678]
neg_ints: list[float | int] = [-1234, -12345678]
pos_floats: list[float | int] = [1234.5, 1234.5678, 12345678.9]
neg_floats: list[float | int] = [-1234.5, -12345678.9]
decimals: list[float | int] = [0.12345, -0.12345]
all_floats: list[float | int] = neg_floats + pos_floats + decimals
all_ints: list[float | int] = neg_ints + pos_ints
numbers: list[float | int] = all_ints + all_floats


##########################################################
##### Capture


@pytest.mark.parametrize("case", number_literal.gen_cases(numbers), ids=idsfn)
def test_num_capture_well_formed_literals(case):
    num, (literal, _) = case
    m = re.search(num.pattern, literal)
    assert m.group(0) == literal


data_ackward_number_literals = [
    # zero
    (rn.Num(dec="."), ("000.000", 0)),
    (rn.Num(dec="."), ("- 000.000", 0)),
    (rn.Num(dec="."), ("+ 000.000", 0)),
    # decimal with no left-zero
    (rn.Num(dec="."), (".1234", 0.1234)),
    (rn.Num(dec="."), ("-.1234", -0.1234)),
    (rn.Num(dec="."), ("+.1234", 0.1234)),
    (rn.Num(dec="."), ("- .1234", -0.1234)),
    (rn.Num(dec="."), ("+ .1234", 0.1234)),
    (rn.Num(dec=","), (",1234", 0.1234)),
    (rn.Num(dec=","), ("-,1234", -0.1234)),
    (rn.Num(dec=","), ("+,1234", 0.1234)),
    (rn.Num(dec=","), ("- ,1234", -0.1234)),
    (rn.Num(dec=","), ("+ ,1234", 0.1234)),
]


@pytest.mark.parametrize("case", data_ackward_number_literals, ids=idsfn)
def test_num_capture_ackward_number_literals(case):
    num, (literal, number) = case
    p = re.compile(num.pattern)
    m = p.search(literal)
    assert m is not None
    assert m.group(0) == literal
    assert float(num.normalize(m.group(0))) == number


data_symbols_in_different_context = [
    "abc-efd ",
    " + ",
    "stop. ",
    "it's ",
    "comma, ",
]


@pytest.mark.parametrize("symbol", data_symbols_in_different_context)
def test_num_capture_no_symbols_in_different_context(symbol):
    num = rn.Num()
    p = re.compile(num.pattern)
    m = p.search(symbol)
    assert m is None


data_malformed_number_literals = [
    # Malformed: heterogeneous ths separator
    (rn.Num(dec="", ths=" "), ("1 333'222", None)),
    (rn.Num(dec=".", ths=" "), ("1 333'222.4", None)),
    (rn.Num(dec=".", ths=" "), ("1,333 222.4", None)),
    (rn.Num(dec=".", ths=","), ("1'333,222.4", None)),
    (rn.Num(dec=".", ths="'"), ("1333'333.4", None)),
    # Malformed: ambigous ths vs dec separator
    (rn.Num(dec="", ths="."), ("1.234.5", None)),
    (rn.Num(dec="", ths=","), ("1,234,5", None)),
    (rn.Num(dec="", ths="."), ("1.333.222.4", None)),
    # Malformed: forbiden ths separators
    (rn.Num(dec=".", ths=" "), ("1;333;222.4", None)),
    (rn.Num(dec=".", ths=" "), ("1_333_222.4", None)),
    # Malformed: severe issues
    (rn.Num(dec=",", ths=""), ("1333,4 5", None)),
    (rn.Num(dec=".", ths=","), ("1,0,0,0.0", None)),
    (rn.Num(dec=".", ths=","), ("1,2.3", None)),
    (rn.Num(dec=",", ths="'"), ("1'22'33,4", None)),
    (rn.Num(dec=",", ths=" "), ("1 22 33,4", None)),
]


@pytest.mark.parametrize("case", data_malformed_number_literals, ids=idsfn)
def test_num_capture_no_malformed_number_literals(case):
    num, (literal, _) = case
    p = re.compile(num.pattern)
    m = p.search(literal)
    assert m is not None
    assert (capture := m.group(0)) == literal
    assert num.normalize(capture) is None


##########################################################
##### Normalization


@pytest.mark.parametrize("case", number_literal.gen_cases(pos_ints), ids=idsfn)
def test_num_normalize_well_formed_positive_integers(case):
    num, (literal, number) = case
    assert float(num.normalize(literal)) == number


@pytest.mark.parametrize("case", number_literal.gen_cases(neg_ints), ids=idsfn)
def test_num_normalize_well_formed_negative_integers(case):
    num, (literal, number) = case
    assert float(num.normalize(literal)) == number


@pytest.mark.parametrize("case", number_literal.gen_cases(pos_floats), ids=idsfn)
def test_num_normalize_well_formed_positive_floats(case):
    num, (literal, number) = case
    assert float(num.normalize(literal)) == number


@pytest.mark.parametrize("case", number_literal.gen_cases(neg_floats), ids=idsfn)
def test_num_normalize_well_formed_negative_floats(case):
    num, (literal, number) = case
    assert float(num.normalize(literal)) == number


@pytest.mark.parametrize("case", number_literal.gen_cases(decimals), ids=idsfn)
def test_num_normalize_well_formed_decimals(case):
    num, (literal, number) = case
    assert float(num.normalize(literal)) == number


#########################################
# Number literal within context


@pytest.mark.parametrize("context", ["text", "$"])
@pytest.mark.parametrize("case", number_literal.gen_cases(numbers), ids=idsfn)
def test_num_ignores_context_left_side_with_space(context, case):
    num, (literal, number) = case
    p = re.compile(num.pattern)
    m = p.search(f"{context} {literal}")
    assert m is not None
    assert (capture := m.group(0).strip()) == literal
    assert float(num.normalize(capture)) == number


@pytest.mark.parametrize("context", ["text", "$"])
@pytest.mark.parametrize("case", number_literal.gen_cases(numbers), ids=idsfn)
def test_num_ignores_context_left_side_without_space(context, case):
    num, (literal, number) = case
    p = re.compile(num.pattern)
    m = p.search(f"{context}{literal}")
    assert m is not None
    assert (capture := m.group(0)) == literal
    assert float(num.normalize(capture)) == number


@pytest.mark.parametrize("context", [" EUR", "€", ",", ";", ".", "-"])
@pytest.mark.parametrize("case", number_literal.gen_cases(numbers), ids=idsfn)
def test_num_ignores_context_right_side(context, case):
    num, (literal, number) = case
    p = re.compile(num.pattern)
    m = p.search(f"{literal}{context}")
    assert m is not None
    assert (capture := m.group(0)) == literal
    assert float(num.normalize(capture)) == number


#########################################
# Reject number literals with wrong format


@pytest.mark.parametrize("case", number_literal.gen_cases(all_floats), ids=idsfn)
@pytest.mark.parametrize(
    "seps", product([".", ",", ""], [".", ",", "'", " ", ""]), ids=ids_num_init
)
def test_num_rejects_different_dec_separator(case, seps):
    num, (literal, _) = case
    dec, ths = seps
    if dec == "" or dec != ths:
        num_test = rn.Num(dec=dec, ths=ths)
        if num_test.dec != num.dec:
            assert num_test.normalize(literal) is None


@pytest.mark.parametrize("case", number_literal.gen_cases(pos_floats + neg_floats), ids=idsfn)
@pytest.mark.parametrize(
    "seps", product([".", ",", ""], [".", ",", "'", " ", ""]), ids=ids_num_init
)
def test_num_rejects_floats_with_different_ths_separator(case, seps):
    num, (literal, _) = case
    dec, ths = seps
    if dec == "" or dec != ths:
        num_test = rn.Num(dec=dec, ths=ths)
        if num_test.ths != num.ths:
            assert num_test.normalize(literal) is None


@pytest.mark.parametrize("case", number_literal.gen_cases([1234567, -1234567]), ids=idsfn)
@pytest.mark.parametrize(
    "seps", product(["", ".", ","], [".", ",", "'", " ", ""]), ids=ids_num_init
)
def test_num_rejects_ints_with_different_ths_separator(case, seps):
    num, (literal, _) = case
    dec, ths = seps
    if dec == "" or dec != ths:
        num_test = rn.Num(dec=dec, ths=ths)
        if num_test.ths != num.ths:
            assert num_test.normalize(literal) is None
