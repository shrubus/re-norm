"""Public API"""

from .pattern import compile_, Pattern, Match
from .specs import NormSpec, NOSPEC, Num

compile = compile_  # pylint: disable=redefined-builtin

# public symbols
__all__ = [
    "compile",
    "Pattern",
    "Match",
    # specs
    "NormSpec",  # spec abc
    "NOSPEC",  # no-spec singleton instance
    "Num",  # general number spec
]
