"Generate data to test specs"

# pylint: disable=protected-access

from itertools import product
from typing import Generator

import renorm as rn

_WHITESPACE: tuple[str, ...] = (" ", "\u00a0", "\u202f")
_ALL_DEC: tuple[str, ...] = (",", ".")
_ALL_THS: tuple[str, ...] = (" ", ",", ".", "'")


def _create_signal_space(number, ws: tuple[str, ...] = _WHITESPACE) -> list[str]:
    """
    Create sign tokens with optional right-side whitespace padding.
    """
    padding = list(ws) + [""]
    neg = [f"-{p}" for p in padding]
    pos = [f"+{p}" for p in padding] + [""]

    if number > 0:
        return pos
    if number < 0:
        return neg
    return neg + pos


def _gen_ws_ths_space(repeat: int = 1, ws: tuple[str, ...] = _WHITESPACE) -> list[tuple[str, ...]]:
    return list(product(ws, repeat=repeat))


def _gen_ths_space(repeat: int, ths: str) -> list[tuple[str, ...]]:
    """
    Generate thousands-separator tuples with optional ungrouped, padded, and mixed variants.
    """
    if ths == "":  # .format(*())
        return [("",) * repeat]
    if ths == " ":  # .format(*ws_cases)
        return list(_gen_ws_ths_space(repeat=repeat))
    return [tuple([ths] * repeat)]  # .format(*(ths, ths, ...))


def gen_literals(
    number: float | int,
    dec: str,
    ths: str,
) -> Generator[tuple[str, float | int]]:
    """
    Yield (literal, num_spec, number) pairs for all combinations of sign tokens and
    thousands-separator tuples, using the given decimal separator and options
    for ungrouped, mixed, and extraspace-padded variants.
    """

    assert dec in ["", ",", "."], "Invalid decimal separator"
    assert dec != ths or dec == "", "Thousands and decimal separators should be different"

    # spec dec="" filter out non-integers
    has_decimal_part = number != int(number)
    accept_int_only = dec == ""
    if accept_int_only and has_decimal_part:
        return

    # Create ths placeholders and replace dec separator
    base = format(abs(number), ",").replace(",", "{}").replace(".", dec)
    repeat = base.count("{}")

    for sgn in _create_signal_space(number):
        for case in _gen_ths_space(repeat=repeat, ths=ths):
            literal = f"{sgn}{base.format(*case)}".strip()
            yield (literal, number)


def _gen_literal_space(
    number: float | int,
    all_dec: tuple[str, ...] = _ALL_DEC,
    all_ths: tuple[str, ...] = _ALL_THS,
) -> Generator[tuple[rn.Num, tuple[str, float | int]]]:

    # if number == int(number):
    #     for ths in all_ths:
    #         for case in gen_literals(number=number, dec="", ths=ths):
    #             yield
    #     return

    for dec in all_dec:
        for ths in all_ths:
            if dec != "" and (dec == ths):
                continue
            num_spec = rn.Num(dec=dec, ths=ths)
            for case in gen_literals(number=number, dec=dec, ths=ths):
                yield (num_spec, case)


def gen_cases(  # pylint: disable=R0917&R0913
    numbers: list[float | int],
    all_dec: tuple[str, ...] = _ALL_DEC,
    all_ths: tuple[str, ...] = _ALL_THS,
) -> Generator[tuple[rn.Num, tuple[str, float | int]]]:
    """
    Yield (literal, number) and  (- number, literal) pairs for each given positive number.
    """

    for number in numbers:
        yield from _gen_literal_space(
            number=number,
            all_dec=all_dec,
            all_ths=all_ths,
        )


# def gen_wrong_cases(  # pylint: disable=R0917&R0913
#     numbers: list[float],
#     dec: str,
#     ths: str,
#     ungrouped: bool,
#     mixed_ths: bool,
# ) -> Generator[tuple[str, ...]]:
#     """
#     Yield (literal, number) pairs that are valid under a more permissive
#     spec but not under the provided strict spec.

#     The permissive superset is derived from the module default `num_default`
#     and widens: thousands separators, mixed_ths=True, ungrouped=True, extraspace=1.
#     """

#     strict_cases = set(
#         gen_cases(
#             numbers,
#             dec=dec,
#             ths=ths,
#             ungrouped=ungrouped,
#             mixed_ths=mixed_ths,
#             extraspace=0,
#         )
#     )

#     permissive_ths = "".join(dict.fromkeys(ths + num_default.ths))
#     for case in gen_cases(
#         numbers,
#         dec=dec,
#         ths=permissive_ths.replace(dec, ""),
#         mixed_ths=True,
#         ungrouped=True,
#         extraspace=2,
#     ):
#         if case not in strict_cases:
#             yield case


if __name__ == "__main__":

    VERBOSE = True
    if VERBOSE:
        print("=" * 20)
        print("Signal space (number > 0)")
        print(_create_signal_space(1234.5))

        print("=" * 20)
        print("Signal space (number = 0)")
        print(_create_signal_space(0))

        print("=" * 20)
        print("Signal space (number < 0)")
        print(_create_signal_space(-1234.5))

        print("=" * 20)
        print("Whitespace space (repeat=2)")
        print(*_gen_ws_ths_space(repeat=2), sep="\n")

        print("=" * 20)
        print('Thousand separators space (repeat=2, ths="")')
        print(*_gen_ths_space(repeat=2, ths=""), sep="\n")
        print('Thousand separators space (repeat=2, ths=" ")')
        print(*_gen_ths_space(repeat=2, ths=" "), sep="\n")
        print('Thousand separators space (repeat=2, ths="\'")')
        print(*_gen_ths_space(repeat=2, ths="'"), sep="\n")

        print("=" * 20)
        print('(literal, number) cases for dec = "." and ths=" "')
        print("number = 0")
        print(*gen_literals(number=0, dec=".", ths=" "), sep="\n")

        print("=" * 20)
        print('(literal, number) cases for dec = "." and ths=""')
        print("number = -.12345")
        print(*gen_literals(number=-0.12345, dec=".", ths=""), sep="\n")

        print("=" * 20)
        print('(literal, number) cases for dec = "." and ths="\'"')
        print("number = -12345678.9")
        print(*gen_literals(number=-12345678.9, dec=".", ths="'"), sep="\n")

        print("=" * 20)
        print('(literal, number) cases for dec = "." and ths=" "')
        print("number = 12345678.9")
        print(*gen_literals(number=12345678.9, dec=".", ths=" "), sep="\n")

        print("=" * 20)
        print('(literal, number) cases for dec = "." and ths=" "')
        print("numbers = [0, -1234.5, 12345678.9]")
        print(*gen_cases(numbers=[0, -1234.5, 12345678.9]), sep="\n")

    # number_literal_cases = list(
    #     gen_wrong_cases(
    #         numbers=[0, 1234567.8, 123, 0.123],
    #         dec=".",
    #         ths="' ",
    #         ungrouped=True,
    #         mixed_ths=False,
    #         # extraspace=0,
    #     )
    # )

    # # print(*number_literal_cases, sep="\n")
    # print(len(number_literal_cases))
