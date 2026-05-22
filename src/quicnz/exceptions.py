"""Exceptions raised by the quicnz library."""

from __future__ import annotations


class QuicError(Exception):
    """Base exception for all quicnz errors."""


class QuicAuthError(QuicError):
    """Raised when authentication fails (HTTP 403)."""


class QuicNotFoundError(QuicError):
    """Raised when a resource is not found (HTTP 404)."""


class QuicAPIError(QuicError):
    """Raised for unexpected API errors."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status
