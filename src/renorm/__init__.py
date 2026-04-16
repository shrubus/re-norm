"""Public API"""

from .pattern import compile_, Pattern

compile = compile_  # pylint: disable=redefined-builtin

# public symbols
__all__ = [
    "compile",
    "Pattern",
]
