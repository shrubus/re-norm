"""Public API"""

from .pattern import compile_, Pattern, Match
from .exceptions import PatternError, PatternIndexError, PatternKeyError
from .specs import NormSpec, NOSPEC, Num

compile = compile_  # pylint: disable=redefined-builtin

# public symbols
__all__ = [
    "compile",
    "Pattern",
    "PatternError",
    "PatternIndexError",
    "PatternKeyError",
    "Match",
    # specs
    "NormSpec",  # spec abc
    "NOSPEC",  # no-spec singleton instance
    "Num",  # general number spec
]
