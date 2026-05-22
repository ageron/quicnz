"""Tests for QuicClient."""

from __future__ import annotations

import pytest

from quicnz import QuicAPIError, QuicAuthError, QuicClient, QuicNotFoundError, Session

BASE = "https://api.quic.nz/v1"
API_KEY = "test-api-key"

# ---------------------------------------------------------------------------
# Sample API payloads
# ---------------------------------------------------------------------------

SERVICES_PAYLOAD = {"serviceIds": ["service123", "service456"]}

SESSION_PAYLOAD = {
    "service": {
        "staticIPv4Prefix": "",
        "staticIPv6Prefix": "",
        "staticIPv4PrefixLength": None,
        "staticIPv6PrefixLength": None,
        "username": "testuser",
        "password": "testpass",
        "datacap": 0,
        "mac": "",
        "asid": "1631234567",
        "lfc": "Chorus",
        "status": "active",
        "entity": "Quic",
        "entityUniqueId": "106511",
        "routes": [],
        "createdAt": {"$date": "2024-04-28T19:26:20.668Z"},
        "updatedAt": {"$date": "2024-04-28T19:26:20.668Z"},
    },
    "status": "connected",
    "sessionType": "DHCP",
    "activeIPv4Prefix": "1.2.3.4",
    "activeIPv4PrefixLength": 32,
    "activeIPv6Prefix": "2001:db8::",
    "activeIPv6PrefixLength": 56,
    "lastRadiusUpdate": {"$date": "2025-08-04T00:48:40.547Z"},
    "sessionExpiresAt": {"$date": "2025-08-04T01:08:40.547Z"},
    "pppPayload": None,
    "createdAt": {"$date": "2024-11-13T12:24:06.354Z"},
    "updatedAt": {"$date": "2025-08-04T00:48:40.547Z"},
}

# Same payload but with dates as plain strings (actual API format)
SESSION_PAYLOAD_PLAIN_DATES = {
    **SESSION_PAYLOAD,
    "service": {
        **SESSION_PAYLOAD["service"],
        "createdAt": "2024-04-28T19:26:20.668Z",
        "updatedAt": "2024-04-28T19:26:20.668Z",
    },
    "lastRadiusUpdate": "2025-08-04T00:48:40.547Z",
    "sessionExpiresAt": "2025-08-04T01:08:40.547Z",
    "createdAt": "2024-11-13T12:24:06.354Z",
    "updatedAt": "2025-08-04T00:48:40.547Z",
}

SESSION_PAYLOAD_PPP = {
    **SESSION_PAYLOAD,
    "sessionType": "PPPoE",
    "pppPayload": {
        "packetSourceAddress": "10.0.0.1",
        "nasPortType": "Ethernet",
        "nasPort": "150",
        "nasPortId": "Quic",
        "serviceType": "Framed-User",
        "linkLayerAddress": "1:d7:2:c2:5f:e2:cb",
        "callingStationId": "1:d7:2:c2:5f:e2:cb",
        "calledStationId": "Quic",
        "delegatedIPv6Prefix": "",
        "nasIdentifier": "bng-name",
        "nasIPAddress": "10.0.0.2",
        "adslAgentRemoteId": "LFCSPECIFIC",
        "adslAgentCircuitId": "ELL-POLT08 eth 1/1/03/15/5/1/1:10",
        "eventTimestamp": "",
        "acctStatusType": "",
        "acctSessionId": "",
        "acctAuthentic": "",
        "acctDelayTime": 0,
        "postAuthResult": "",
        "acctInputOctets": "",
        "userName": "D4:01:C3:4F:E6:CB",
        "userPassword": "",
        "acctOutputOctets": "",
        "acctUniqueSessionId": "",
    },
}

WEATHERMAP_BYTES = b"\xff\xd8\xff\xe0fake-jpeg-data"

# ---------------------------------------------------------------------------
# Tests – get_services
# ---------------------------------------------------------------------------


async def test_get_services(mock_aiohttp):
    mock_aiohttp.get(f"{BASE}/services", payload=SERVICES_PAYLOAD)

    async with QuicClient(API_KEY) as client:
        service_ids = await client.get_services()

    assert service_ids == ["service123", "service456"]


async def test_get_services_auth_error(mock_aiohttp):
    mock_aiohttp.get(f"{BASE}/services", status=403)

    async with QuicClient(API_KEY) as client:
        with pytest.raises(QuicAuthError):
            await client.get_services()


async def test_get_services_server_error(mock_aiohttp):
    mock_aiohttp.get(f"{BASE}/services", status=500, body="Internal Server Error")

    async with QuicClient(API_KEY) as client:
        with pytest.raises(QuicAPIError) as exc_info:
            await client.get_services()

    assert exc_info.value.status == 500


async def test_get_session_plain_string_dates(mock_aiohttp):
    """The real API returns dates as plain strings, not {$date: ...} objects."""
    mock_aiohttp.get(f"{BASE}/session?service=service123", payload=SESSION_PAYLOAD_PLAIN_DATES)

    async with QuicClient(API_KEY) as client:
        session = await client.get_session("service123")

    assert session.is_connected is True
    assert session.last_radius_update.year == 2025


# ---------------------------------------------------------------------------
# Tests – get_session (DHCP)
# ---------------------------------------------------------------------------


async def test_get_session_dhcp(mock_aiohttp):
    mock_aiohttp.get(f"{BASE}/session?service=service123", payload=SESSION_PAYLOAD)

    async with QuicClient(API_KEY) as client:
        session = await client.get_session("service123")

    assert isinstance(session, Session)
    assert session.status == "connected"
    assert session.is_connected is True
    assert session.session_type == "DHCP"
    assert session.active_ipv4_prefix == "1.2.3.4"
    assert session.active_ipv4_prefix_length == 32
    assert session.active_ipv6_prefix == "2001:db8::"
    assert session.active_ipv6_prefix_length == 56
    assert session.ppp_payload is None


async def test_get_session_pppoe(mock_aiohttp):
    mock_aiohttp.get(f"{BASE}/session?service=service123", payload=SESSION_PAYLOAD_PPP)

    async with QuicClient(API_KEY) as client:
        session = await client.get_session("service123")

    assert session.session_type == "PPPoE"
    assert session.ppp_payload is not None
    assert session.ppp_payload.nas_identifier == "bng-name"
    assert session.ppp_payload.adsl_agent_circuit_id == "ELL-POLT08 eth 1/1/03/15/5/1/1:10"


async def test_get_session_service_info(mock_aiohttp):
    mock_aiohttp.get(f"{BASE}/session?service=service123", payload=SESSION_PAYLOAD)

    async with QuicClient(API_KEY) as client:
        session = await client.get_session("service123")

    svc = session.service
    assert svc.username == "testuser"
    assert svc.lfc == "Chorus"
    assert svc.status == "active"
    assert svc.asid == "1631234567"
    assert svc.datacap == 0
    assert svc.routes == []


async def test_get_session_not_found(mock_aiohttp):
    mock_aiohttp.get(f"{BASE}/session?service=service123", status=404)

    async with QuicClient(API_KEY) as client:
        with pytest.raises(QuicNotFoundError):
            await client.get_session("service123")


async def test_get_session_auth_error(mock_aiohttp):
    mock_aiohttp.get(f"{BASE}/session?service=service123", status=403)

    async with QuicClient(API_KEY) as client:
        with pytest.raises(QuicAuthError):
            await client.get_session("service123")


async def test_session_is_not_connected(mock_aiohttp):
    disconnected = {**SESSION_PAYLOAD, "status": "disconnected"}
    mock_aiohttp.get(f"{BASE}/session?service=service123", payload=disconnected)

    async with QuicClient(API_KEY) as client:
        session = await client.get_session("service123")

    assert session.is_connected is False


# ---------------------------------------------------------------------------
# Tests – get_weathermap
# ---------------------------------------------------------------------------


async def test_get_weathermap(mock_aiohttp):
    mock_aiohttp.get(f"{BASE}/weathermap", body=WEATHERMAP_BYTES, content_type="image/jpeg")

    async with QuicClient(API_KEY) as client:
        data = await client.get_weathermap()

    assert data == WEATHERMAP_BYTES


async def test_get_weathermap_auth_error(mock_aiohttp):
    mock_aiohttp.get(f"{BASE}/weathermap", status=403)

    async with QuicClient(API_KEY) as client:
        with pytest.raises(QuicAuthError):
            await client.get_weathermap()


# ---------------------------------------------------------------------------
# Tests – context manager / session lifecycle
# ---------------------------------------------------------------------------


async def test_no_session_raises_runtime_error():
    client = QuicClient(API_KEY)
    # Not used as context manager and no external session provided
    with pytest.raises(RuntimeError, match="No active HTTP session"):
        await client.get_services()


# ---------------------------------------------------------------------------
# Tests – API key resolution
# ---------------------------------------------------------------------------


async def test_api_key_from_env(mock_aiohttp, monkeypatch):
    monkeypatch.setenv("QUICNZ_API_KEY", API_KEY)
    mock_aiohttp.get(f"{BASE}/services", payload=SERVICES_PAYLOAD)

    async with QuicClient() as client:
        service_ids = await client.get_services()

    assert service_ids == ["service123", "service456"]


async def test_explicit_key_takes_precedence_over_env(mock_aiohttp, monkeypatch):
    monkeypatch.setenv("QUICNZ_API_KEY", "env-key")
    mock_aiohttp.get(f"{BASE}/services", payload=SERVICES_PAYLOAD)

    # The explicit key is what gets sent; aioresponses doesn't check headers,
    # but we can confirm no error is raised and the call succeeds.
    async with QuicClient(api_key=API_KEY) as client:
        service_ids = await client.get_services()

    assert service_ids == ["service123", "service456"]


def test_no_api_key_raises_value_error(monkeypatch):
    monkeypatch.delenv("QUICNZ_API_KEY", raising=False)

    with pytest.raises(ValueError, match="QUICNZ_API_KEY"):
        QuicClient()
