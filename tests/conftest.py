"""Shared fixtures for the quicnz test suite."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses


@pytest.fixture
def mock_aiohttp():
    """Yield an aioresponses context that mocks all aiohttp calls."""
    with aioresponses() as m:
        yield m
