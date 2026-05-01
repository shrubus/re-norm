"""
Declarative regex specifications with explicit normalization semantics.

This module defines small, composable specifications that pair a regular
expression pattern with a deterministic normalization strategy. Each spec
describes a precise grammar for a class of textual values and guarantees
that matched groups can be transformed into a canonical representation.
"""

import re
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Self, ClassVar
from functools import cached_property


class NormSpec(ABC):
    """Abstract base class to specify a regex pattern coupled to a normalization strategy"""

    @property
    @abstractmethod
    def pattern(self) -> str:
        """Construct a pattern based on instance attributes"""

    @abstractmethod
    def normalize(self, group: str | None) -> str | None:
        """
        Normalize the regex group captured using the constructed regex pattern.
        Returns None if group is None (e.g. for optional capturing groupd r"(a)?(b)").
        """

    def __str__(self) -> str:
        return self.pattern


class _NoSpec(NormSpec):
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
class _NumSubPatterns:
    xs: str
    all_sep: str
    ths_sep: str
    dec_sep: str
    signal: str


@dataclass(frozen=True)
class Num(NormSpec):  # pylint: disable=too-many-instance-attributes
    """
    Declarative specification for plain (non-scientific) numeric literals.

    Supports configurable decimal and thousands separators, with optional
    tolerance for inter-token whitespace. The grammar is fully defined by
    the provided separators and flags, and normalization produces a
    canonical dot-decimal representation.
    """

    _all_ths: ClassVar[str] = ".,' "
    _all_dec: ClassVar[str] = ".,"
    _all_signal: ClassVar[str] = "-+"

    ths: str = _all_ths
    dec: str = "."  # default "."
    signal: str = _all_signal
    ungrouped: bool = True  # default True
    mixed: bool = False  # default False
    extraspace: int = 0  # default 0

    _ths: str = field(init=False, repr=False)

    def __post_init__(self) -> None:

        # validation
        if not set(self.signal) <= set(self._all_signal):
            raise ValueError(f'Signal must be "+", "-" or "" (not specified): {self.signal}')
        if not set(self.ths) <= set(self._all_ths):
            raise ValueError(f'Thousand separators must be in {self._all_ths} or "": {self.ths}')
        if not (len(self.dec) == 1 or self.dec == ""):
            raise ValueError(f"Specified more than one decimal separator: {self.dec}")
        if not set(self.dec) <= set(self._all_dec):
            raise ValueError(f'Decimal separator must be ",", "." or "" (integer): {self.dec}')

        # construction
        object.__setattr__(self, "_ths", self.ths.replace(self.dec, "").replace(" ", r"\s"))

    @cached_property
    def _sub_patterns(self) -> _NumSubPatterns:

        all_sep_symbols = f"{self._all_ths};_".replace(" ", r"\s")

        xs = rf"\s{{0,{self.extraspace}}}" if self.extraspace > 0 else ""

        all_sep = rf"{xs}[{all_sep_symbols}]?{xs}"
        ths_sep = rf"{xs}[{self._ths}]{xs}" if self._ths else ""
        dec_sep = rf"{xs}[{self.dec}]{xs}" if self.dec else ""
        print(f"{ths_sep=}")
        print(f"{dec_sep=}")

        signal = rf"(?:[{self.signal}]\s?)?" if self.signal else ""

        return _NumSubPatterns(xs, all_sep, ths_sep, dec_sep, signal)

    @cached_property
    def pattern(self) -> str:
        """
        Very permissive pattern that greedly matches string fragments that resemble
        a numeric string representation.
        """

        sp = self._sub_patterns
        return rf"{sp.signal}(?:{sp.all_sep}\d+)+"

    def _is_full_match(self, group: str, num_floor: str, decimal: str) -> bool:

        sp = self._sub_patterns
        num_pattern = rf"{sp.signal}{sp.xs}{num_floor}{decimal}?"

        print(f"{num_pattern=}")
        p = re.compile(num_pattern)
        return p.fullmatch(group) is not None

    def _is_grouped(self, group: str) -> bool:

        if self._ths == "":
            return False

        sp = self._sub_patterns
        if not self.mixed:
            same_ths_sep = rf"(?:\d{{0,3}}(?:({sp.ths_sep})\d{{3}})?(?:\1\d{{3}})*)"
            whitespace = r"(?:\d{0,3}(?:\s\d{3})*)"
            grouped = f"(?:{same_ths_sep}|{whitespace})"
        else:
            grouped = rf"(?:\d{{0,3}}(?:({sp.ths_sep})\d{{3}})*)"
        decimal = rf"(?:{sp.dec_sep}\d+)"
        return self._is_full_match(group, num_floor=grouped, decimal=decimal)

    def _is_ungrouped(self, group: str) -> bool:

        if not self.ungrouped:
            return False

        sp = self._sub_patterns
        ungrouped = r"\d+"
        decimal = rf"(?:{sp.dec_sep}\d+)"
        return self._is_full_match(group, num_floor=ungrouped, decimal=decimal)

    def _is_number_candidate(self, group: str) -> bool:
        if self._is_ungrouped(group):
            print("ungrouped".upper())
            return True
        if self._is_grouped(group):
            print("grouped".upper())
            return True
        print("not a number".upper())
        return False

    def normalize(self, group: str | None) -> str | None:
        """Normalize the captured number"""

        if group is None:
            return None

        if not self._is_number_candidate(group):
            return None

        # remove signal trailing space (ambiguity with space as ths separator)
        if self.signal:
            group = re.sub(r"([+-])\s", lambda m: m[1], group)

        if self._ths:
            group = re.sub(f"[{re.escape(self._ths)}]", "", group)

        group = re.sub(r"\s+", "", group)
        return group.replace(self.dec, ".").replace("+", "")
