"""Define renorm exceptions and errors."""


class RenormError(Exception):
    """Base class for all renorm exceptions."""


class PatternError(RenormError):
    """Raised when a renorm pattern violates parser rules."""


class PatternIndexError(PatternError):
    """Raised when a positional placeholder index is out of range."""


class PatternKeyError(PatternError):
    """Raised when a named placeholder is missing from named_specs."""
