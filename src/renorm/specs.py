"""
Declarative regex specifications with explicit normalization semantics.

This module defines small, composable specifications that pair a regular
expression pattern with a deterministic normalization strategy. Each spec
describes a precise grammar for a class of textual values and guarantees
that matched groups can be transformed into a canonical representation.
"""

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Self
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

    ths: str = ""
    dec: str = "."
    signal: str = "-"
    extraspace: bool = False

    def __post_init__(self) -> None:
        common = set(self.dec) & set(self.ths) & set(self.signal)
        if common:
            raise ValueError(f"Args dec, ths and signal cannot have common characters: {common}")
        if len(self.dec) != 1:
            raise ValueError(f"Can only specify one decimal separator: specified {self.dec}")

    @property
    def pattern(self) -> str:
        """Construct plain number general pattern"""
        ws = r"\s?" if self.extraspace else ""

        signal = rf"(?:[{re.escape(self.signal)}]?\s?)" if self.signal else ""
        dec = rf"(?:{re.escape(self.dec)}{ws}\d*)"
        ths = rf"(?:[{re.escape(self.ths)}]{ws}\d{{3}}{ws})*" if self.ths else ""
        end = rf"\d{{0,3}}{ws}"

        return signal + end + ths + dec

    def normalize(self, group: str | None) -> str | None:
        """Normalize the captured number"""
        if group is None:
            return None
        if self.extraspace:
            group = re.sub(r"\s+", "", group)
        group = re.sub(f"[{re.escape(self.ths)}]", "", group)
        return group.replace(self.dec, ".")
