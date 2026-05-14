"""
Declarative regex specifications with explicit normalization semantics.

This module defines composable specifications that pair a regular expression
pattern with a deterministic normalization strategy. Each specification
describes a precise grammar for a class of textual values and guarantees that
matched groups can be transformed into a canonical representation.
"""

import re
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Self, ClassVar
from functools import cached_property


class NormSpec[T](ABC):
    """
    Abstract specification of a regex pattern coupled to a normalization strategy

    A NormSpec defines:
      - a regex pattern describing acceptable textual representations
      - a normalization function that converts a matched group into a canonical
        value of type T (or None if the group is invalid)

    Subclasses must implement `pattern` and `normalize()`.
    """

    @property
    @abstractmethod
    def pattern(self) -> str:
        """Construct a pattern based on instance attributes"""

    @abstractmethod
    def normalize(self, group: str | None) -> T | None:
        """
        Normalize the regex group captured using the constructed regex pattern.
        Returns None if group is None (e.g. for optional capturing groupd r"(a)?(b)").
        """

    def __str__(self) -> str:
        return self.pattern


class _NoSpec(NormSpec[str]):
    """
    Internal placeholder specification used when a capturing group has no
    associated rule, i.e. normalize() returns the raw matched group unchanged.

    The pattern is the empty string (a neutral element in regex composition).
    Note: the empty pattern matches zero-width when used alone, but acts as a
    neutral element when embedded in composed regex patterns.

    Implemented as a singleton. Intended for internal use only.
    """

    _instance = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def pattern(self) -> str:
        """
        Return the empty string (a neutral element in regex composition).
        Note: the empty pattern matches zero-width when used alone, but acts as a
        neutral element when embedded in composed regex patterns.
        """
        return ""

    def normalize(self, group: str | None) -> str | None:
        """No normalization applied: returns the raw matched group unchanged."""
        return group


NOSPEC = _NoSpec()


@dataclass(frozen=True)
class Num(NormSpec[float]):
    """
    Specification for plain (non-scientific) numeric literals with configurable
    decimal and thousands separators.

    The `pattern` property exposes a permissive regex used only for capture: it
    greedily matches number-like fragments to avoid truncating malformed literals.
    Normalization then applies a strict pattern that enforces the instance's
    numeric specification. If the captured literal does not satisfy the strict
    rules, normalization returns None; otherwise it returns a float.

    Parameters:
        dec: Decimal separator ('.', ',', or '' for integers only).
        ths: Thousands separator ('.', ',', ''', space, or '' for no grouping).

    Semantics:
    - If `ths == ''`, the integer part must be ungrouped.
    - If `ths != ''`, the integer part must be grouped in 3-digit blocks from
      the right, using `ths` as the thousands separator (or a single space
      when `ths == ' '`).

    - If `dec == ''`, only integers (no fractional part) are valid.
    - If `dec != ''`, a fractional part is optional and must use `dec`.

    - An optional sign ('+' or '-') is allowed, with optional trailing
      whitespace (not configurable).
    """

    _all_dec: ClassVar[str] = ".,"
    _all_ths: ClassVar[str] = ".,' "
    _all_signals: ClassVar[str] = "-+"
    _all_ws: ClassVar[str] = " \N{NBSP}\N{NNBSP}"

    dec: str = "."
    ths: str = ""

    def __post_init__(self) -> None:

        # validation
        if not (len(self.dec) == 1 or self.dec == ""):
            raise ValueError(f"More than one decimal separator: {self.dec}")
        if self.dec not in self._all_dec:
            raise ValueError(f'Decimal separator must be ",", "." or "": {self.dec}')

        if not (len(self.ths) == 1 or self.ths == ""):
            raise ValueError(f"More than one thousands separator: {self.ths}")
        if self.ths not in self._all_ths:
            raise ValueError(
                f'Thousands separator must be {", ".join(self._all_ths)} or "": {self.ths}'
            )

        if self.dec and self.ths and self.dec == self.ths:
            raise ValueError(f"Same separator: 'dec = '{self.dec}', 'ths = {self.ths}'")

    # ===============================================
    # Pattern constructions: fragments
    # ===============================================

    @property
    def _re_signal(self) -> str:
        signals = re.escape(self._all_signals)
        return rf"(?:[{signals}]\s?)?"

    @property
    def _re_frac(self) -> str:
        dec = re.escape(self.dec)
        return rf"(?:{dec}\d+)"

    @property
    def _re_int_grouped(self) -> str:
        ths = rf"[{self._all_ws}]" if self.ths == " " else re.escape(self.ths)
        return rf"\d{{0,3}}(?:({ths})\d{{3}})*"

    @cached_property
    def _re_int_ungrouped(self) -> str:
        return r"\d*"

    @cached_property
    def _re_int(self) -> str:
        is_grouped = self.ths != ""
        return self._re_int_grouped if is_grouped else self._re_int_ungrouped

    # ===============================================
    # Pattern constructions: full
    # ===============================================

    @cached_property
    def _pattern_capture(self) -> re.Pattern[str]:
        """
        Permissive pattern: greedly matches string fragments that resemble a numeric
        representation.
        """
        all_sep_symbols = f"{self._all_ths};_".replace(" ", r"\s")
        all_sep = rf"[{all_sep_symbols}]?"
        pattern = rf"{self._re_signal}(?:{all_sep}\d+)+"
        return re.compile(pattern)

    # ===============================================

    @cached_property
    def _pattern_spec(self) -> re.Pattern[str]:

        is_integer = self.dec == ""

        if is_integer:
            num_pattern = rf"{self._re_signal}{self._re_int}"
            return re.compile(num_pattern)

        num_pattern = rf"{self._re_signal}{self._re_int}{self._re_frac}?"
        return re.compile(num_pattern)

    # ===============================================
    # Views
    # ===============================================

    @cached_property
    def pattern(self) -> str:
        """
        Permissive regex pattern used for initial capture of number-like fragments.
        This pattern is intentionally broad and does not enforce the numeric
        specification; strict validation is applied during normalization.
        """
        return self._pattern_capture.pattern

    # ===============================================
    # check number candidate
    # ===============================================

    def _is_number_candidate(self, re_group: str) -> bool:
        return self._pattern_spec.fullmatch(re_group) is not None

    # ===============================================
    # Normalize number candidate if any
    # ===============================================

    def normalize(self, group: str | None) -> float | None:
        """
        Normalize a captured numeric literal according to this specification.

        Returns:
            A float if the literal satisfies the strict numeric rules defined by
            this instance (grouping, decimal separator, optional sign, etc.).
            Returns None if the extracted group is None or does not match the
            strict pattern.
        """

        re_group = group
        if re_group is None:
            return None

        if not self._is_number_candidate(re_group):
            return None

        re_group = re.sub(r"([+-])\s?", lambda m: m[1], re_group)  # remove signal trailing space
        re_group = re_group.replace("+", "")
        re_group = re.sub(rf"{re.escape(self.ths)}", "", re_group)
        re_group = re.sub(r"\s+", "", re_group)
        number_literal = re_group.replace(self.dec, ".") if self.dec else re_group
        return float(number_literal)
