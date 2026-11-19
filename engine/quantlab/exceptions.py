"""Exception hierarchy of the scientific engine.

Every error raised on purpose by the engine derives from :class:`QuantLabError`.
Validation errors (the caller supplied bad data or parameters) are kept apart
from future computation errors (a numerical method failed), so that callers such
as the backend can map them to different responses (RULE 010).

Wrong *types* (for example a list where a :class:`pandas.Series` is required)
raise the built-in :class:`TypeError`, following Python conventions.
"""


class QuantLabError(Exception):
    """Base class for every error raised deliberately by the engine."""


class InputValidationError(QuantLabError, ValueError):
    """Input data or parameters violate the requirements of an algorithm.

    Examples: missing or non-finite values, a time index that is not strictly
    increasing, a negative tolerance.
    """


class InsufficientDataError(InputValidationError):
    """The sample is too small for the requested computation."""


class DomainError(InputValidationError):
    """A value lies outside the mathematical domain of a formula or model.

    Examples: a non-positive price passed to a logarithm, a logistic-map
    parameter outside ``[0, 4]``.
    """
