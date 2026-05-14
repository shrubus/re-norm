"""Defines the public API function and classes"""

import re

from typing import Never, Any, Self

from .specs import NormSpec, NOSPEC
from .parser import _Parser

type _FlagsType = int | re.RegexFlag


class Match[T]:
    """renorm.Match object that exposes a minimal API similar to python native re.Match"""

    __slots__ = ("_parser", "_match", "_groups")

    _parser: _Parser[T]
    _match: re.Match[str]
    _groups: tuple[str | None, ...]

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        raise TypeError("renorm.Match objects cannot be instantiated directly")

    @classmethod
    def _from_engine(cls, parser: _Parser[T], match: re.Match[str]) -> Self:
        """Internal method to instantiate renorm.Match objects"""
        self = object.__new__(cls)
        object.__setattr__(self, "_parser", parser)
        object.__setattr__(self, "_match", match)
        object.__setattr__(self, "_groups", None)
        return self

    def __setattr__(self, name: str, _: Any) -> Never:
        """Freeze instance attributes"""
        raise AttributeError(
            f"Cannot set {name} attribute: "
            f"{self.__class__.__name__} instance attributes are frozen"
        )

    def groups(self) -> tuple[str | None, ...]:
        """Return captured groups after normalization"""

        if self._groups is not None:
            return self._groups

        idx_to_groupname = {i: n for n, i in self._match.re.groupindex.items()}

        normalized_groups: list[str | None] = []
        for idx, value in enumerate(self._match.groups(), start=1):

            groupname = idx_to_groupname.get(idx)

            if groupname is None:  # non-specified capturing groups
                normalized_groups.append(value)
                continue

            spec = self._parser.groupname_to_spec.get(groupname, NOSPEC)
            normalized_groups.append(spec.normalize(value))

        object.__setattr__(self, "_groups", tuple(normalized_groups))
        return self._groups

    def group(self, idx: int) -> str | None:
        """Return captured group"""
        if idx == 0:
            return self._match.group()
        return self.groups()[idx - 1]

    def __getitem__(self, idx: int) -> str | None:
        return self.group(idx)

    def groupdict(self) -> Never:
        """Disallow groupdict attribute"""
        raise AttributeError("""Named capture groups are reserved to renorm internal engine""")


class Pattern[T]:
    """renorm.Pattern object that exposes a minimal API similar to python native re.Pattern"""

    __slots__ = ("_parser", "_flags", "compiled")

    _parser: _Parser[T]
    _flags: _FlagsType
    compiled: re.Pattern[str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        raise TypeError("renorm.Pattern objects cannot be instantiated directly")

    @classmethod
    def _from_engine(cls, parser: _Parser[T], flags: _FlagsType) -> Self:
        """Internal method to instantiate renorm.Match objects"""
        self = object.__new__(cls)
        object.__setattr__(self, "_parser", parser)
        object.__setattr__(self, "_flags", flags)
        object.__setattr__(self, "compiled", self._compile())
        return self

    def _compile(self) -> re.Pattern[str]:
        """Compile the python native re pattern constructed from renorm specs"""
        return re.compile(self._parser.pattern, flags=self._flags)

    def __setattr__(self, name: str, _: Any) -> Never:
        """Freeze instance attributes"""
        raise AttributeError(
            f"Cannot set {name} attribute: "
            f"{self.__class__.__name__} instance attributes are frozen"
        )

    @property
    def pattern(self) -> str:
        """View of compiled native python re.Pattern constructed from renorm specs"""
        return self.compiled.pattern

    def search(self, text: str) -> Match[T] | None:
        """Scan through string looking for a match to the pattern constructed from renorm specs,
        returning a renorm.Match object, or None if no match was found."""

        if (match := self.compiled.search(text)) is None:
            return None
        return Match._from_engine(self._parser, match)  # pylint: disable=protected-access


def compile_[T](
    pattern: str, *specs: NormSpec[T], flags: _FlagsType = 0, **named_specs: NormSpec[T]
) -> Pattern[T]:
    """Compile the regex pattern constructed from renorm specs and return renorm.Pattern"""
    parser = _Parser(pattern, *specs, **named_specs)
    return Pattern._from_engine(parser, flags=flags)  # pylint: disable=protected-access
