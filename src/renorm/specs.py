"""
Declarative regex specifications with explicit normalization semantics.

This module defines small, composable specifications that pair a regular
expression pattern with a deterministic normalization strategy. Each spec
describes a precise grammar for a class of textual values and guarantees
that matched groups can be transformed into a canonical representation.
"""

import re
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Self, ClassVar
from functools import cached_property


class NormSpec[T](ABC):
    """Abstract base class to specify a regex pattern coupled to a normalization strategy"""

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
    """Singleton class that signal that a NormSpec is not provided (empty)"""

    _instance = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def pattern(self) -> str:
        return ""

    def normalize(self, group: str | None) -> str | None:
        return group


NOSPEC = _NoSpec()


@dataclass(frozen=True)
class Num(NormSpec[float]):  # pylint: disable=too-many-instance-attributes
    """
    Declarative specification for plain (non-scientific) numeric literals.

    Supports configurable decimal and thousands separators, with optional
    tolerance for inter-token whitespace. The grammar is fully defined by
    the provided separators and flags, and normalization produces a
    canonical dot-decimal representation.
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
        """Normalize the captured number"""

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
