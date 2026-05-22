"""Async HTTP client for the Quic broadband API."""

from __future__ import annotations

import os
from types import TracebackType
from typing import Any

import aiohttp

from .exceptions import QuicAPIError, QuicAuthError, QuicNotFoundError
from .models import Session

BASE_URL = "https://api.quic.nz/v1"


class QuicClient:
    """Async client for the Quic broadband API.

    Usage::

        async with QuicClient(api_key="your-key") as client:
            service_ids = await client.get_services()
            session = await client.get_session(service_ids[0])
            print(session.status, session.active_ipv4_prefix)

    If *api_key* is omitted the ``QUICNZ_API_KEY`` environment variable is used
    instead::

        # export QUICNZ_API_KEY=your-key
        async with QuicClient() as client:
            ...

    You may also pass an existing :class:`aiohttp.ClientSession` to share a
    connection pool with other code::

        async with aiohttp.ClientSession() as http_session:
            client = QuicClient(api_key="your-key", session=http_session)
            session = await client.get_session("service123")
    """

    def __init__(
        self,
        api_key: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        resolved = api_key or os.environ.get("QUICNZ_API_KEY")
        if not resolved:
            raise ValueError(
                "An API key is required. "
                "Pass api_key= or set the QUICNZ_API_KEY environment variable."
            )
        self._api_key = resolved
        self._external_session = session
        self._session: aiohttp.ClientSession | None = session

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> QuicClient:
        if self._external_session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._external_session is None and self._session is not None:
            await self._session.close()
            self._session = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self._api_key}

    def _require_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError(
                "No active HTTP session. "
                "Either use QuicClient as an async context manager or pass a "
                "aiohttp.ClientSession to the constructor."
            )
        return self._session

    async def _get_json(self, path: str, **params: str) -> Any:
        """Perform a GET request and return the decoded JSON body."""
        session = self._require_session()
        url = f"{BASE_URL}{path}"
        async with session.get(url, headers=self._headers, params=params) as resp:
            await self._raise_for_status(resp)
            return await resp.json(content_type=None)

    async def _get_bytes(self, path: str) -> bytes:
        """Perform a GET request and return the raw response body."""
        session = self._require_session()
        url = f"{BASE_URL}{path}"
        async with session.get(url, headers=self._headers) as resp:
            await self._raise_for_status(resp)
            return await resp.read()

    @staticmethod
    async def _raise_for_status(resp: aiohttp.ClientResponse) -> None:
        if resp.status == 403:
            raise QuicAuthError("Forbidden: invalid or missing API key")
        if resp.status == 404:
            raise QuicNotFoundError("Resource not found")
        if resp.status >= 400:
            body = await resp.text()
            raise QuicAPIError(
                f"API returned HTTP {resp.status}: {body}",
                status=resp.status,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_services(self) -> list[str]:
        """Return the list of service IDs authorised for this API key.

        Corresponds to ``GET /v1/services``.
        """
        data: dict[str, list[str]] = await self._get_json("/services")
        return data.get("serviceIds", [])

    async def get_session(self, service_id: str) -> Session:
        """Return session data for *service_id*.

        Corresponds to ``GET /v1/session?service=<service_id>``.
        Session details are cached server-side for 5 minutes.

        :raises QuicAuthError: if the API key is invalid or the service is not
            authorised for this key.
        :raises QuicNotFoundError: if no active session exists for the service.
        """
        data = await self._get_json("/session", service=service_id)
        return Session.from_api(data)

    async def get_weathermap(self) -> bytes:
        """Return the Quic network weather map as raw JPEG bytes.

        Corresponds to ``GET /v1/weathermap``.
        The image is cached server-side for 6 minutes.
        """
        return await self._get_bytes("/weathermap")
