"""Public API"""

from .pattern import Pattern, Match
from .pattern import compile_ as _compile
from .exceptions import PatternError, PatternIndexError, PatternKeyError
from .specs import NormSpec, NOSPEC, Num

compile = _compile  # pylint: disable=redefined-builtin
del _compile

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
