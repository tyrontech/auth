"""Application-level exceptions. API layer maps them to HTTP responses."""


class InvalidRefreshTokenError(Exception):
    """Raised when refresh token is missing, expired, revoked or not found."""

    pass
