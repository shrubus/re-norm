"""
Declarative regex specifications with explicit normalization semantics.

This module defines small, composable specifications that pair a regular
expression pattern with a deterministic normalization strategy. Each spec
describes a precise grammar for a class of textual values and guarantees
that matched groups can be transformed into a canonical representation.
"""

from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Self, ClassVar
import re


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
class Num(NormSpec):
    """
    Declarative specification for plain (non-scientific) numeric literals.

    Supports configurable decimal and thousands separators, with optional
    tolerance for inter-token whitespace. The grammar is fully defined by
    the provided separators and flags, and normalization produces a
    canonical dot-decimal representation.
    """

    ths: str = "all"
    dec: str = "."
    signal: str = "-"
    ungrouped: bool = True
    mixed: bool = True

    _allowed_ths: ClassVar[str] = ",' ."
    _allowed_dec: ClassVar[str] = ",."
    _allowed_signal: ClassVar[str] = "-+"
    _allowed_nbsp: ClassVar[str] = " \u00a0\u202f"

    _ths: str = field(init=False, repr=False)
    _all_ths: str = field(init=False, repr=False)
    _invalid_ths: str = field(init=False, repr=False)

    def __post_init__(self) -> None:

        # validation
        for ch in self.signal:
            if ch not in self._allowed_signal:
                raise ValueError(f'Signal must be "+", "-" or "" (not specified): {ch}')

        if len(self.dec) > 1:
            raise ValueError(f"Can only specify one decimal separator: {self.dec}")
        if self.dec not in self._allowed_dec:
            raise ValueError(f'Decimal separator must be ",", "." or "" (integer): {self.dec}')

        if self.ths != "all":
            for ch in self.ths:
                if ch not in self._allowed_ths:
                    raise ValueError(f"Thousand separators must be in {self._allowed_ths}: {ch}")
        else:
            object.__setattr__(self, "ths", self._allowed_ths.replace(self.dec, ""))

        if overlap := set(self.dec) & set(self.ths):
            raise ValueError(f"Args dec and ths cannot have common characters: {overlap}")
        if overlap := set(self.dec) & set(self.signal):
            raise ValueError(f"Args dec and signal cannot have common characters: {overlap}")
        if overlap := set(self.ths) & set(self.signal):
            raise ValueError(f"Args ths and signal cannot have common characters: {overlap}")

        # construction
        _ths = self.ths.replace(" ", self._allowed_nbsp)
        _all_ths = self._allowed_ths.replace(self.dec, "").replace(" ", self._allowed_nbsp)
        _invalid_ths = "".join(ch for ch in _all_ths if ch not in _ths)

        object.__setattr__(self, "_ths", _ths)
        object.__setattr__(self, "_all_ths", _all_ths)
        object.__setattr__(self, "_invalid_ths", _invalid_ths)

    @property
    def pattern(self) -> str:
        """Matches everything that resembles a number"""
        extraspace = 3

        xs = rf"\s{{0,{extraspace}}}"
        sep = rf"{xs}[;._,']?{xs}"
        signal = r"(?:[\+\-]\s?)"
        return rf"{signal}?(?:{sep}\d+)+"

    @property
    def num_pattern(self) -> str:
        """Construct plain number general pattern"""

    def normalize(self, group: str | None) -> str | None:
        """Normalize the captured number"""

        return group
