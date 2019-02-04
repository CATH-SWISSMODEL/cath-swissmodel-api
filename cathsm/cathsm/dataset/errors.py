"""
Defines errors that can occur within this library
"""

class CannotParseModelFilenameError(Exception):
    """Exception thrown when model filename could not be parsed (probably discontinuous domains)."""
    pass

class NoCathDomainsError(Exception):
    pass

class NoTemplateDomainError(Exception):
    pass

class NoDiscontinuousDomainsError(Exception):
    pass
