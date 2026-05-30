# quicnz

Async Python library for the [Quic broadband](https://quic.nz) API.

Quic exposes an API at `https://api.quic.nz/v1/` that gives customers access
to their service configuration, live session data (connection status, assigned
IP addresses, PPPoE/DHCP details), and a network weather map.  This library
wraps that API with a clean, fully-typed async interface built on
[aiohttp](https://docs.aiohttp.org/).

> **Home Assistant integration:** A separate `ha-quicnz` custom integration
> that uses this library as a dependency is maintained at
> https://github.com/ageron/ha-quicnz

> **Disclaimer:** This project is an independent, community-maintained library
> and is **not affiliated with, endorsed by, or supported by Quic Broadband /
> Vetta Trading Ltd** in any way.  Use it at your own risk.

---

## Requirements

- Python 3.11+
- aiohttp ≥ 3.9

## Installation

```bash
pip install quicnz
```

## Getting an API key

Log in to the [Quic portal](https://account.quic.nz/), select a service, navigate to the bottom of the page, below your product details, and you should find your API key. If the field is empty, click "Roll API Key" to generate the key.

## Quick start

```python
import asyncio
from quicnz import QuicClient

async def main():
    # api_key can also be supplied via the QUICNZ_API_KEY environment variable
    async with QuicClient(api_key="YOUR_API_KEY") as client:
        # List all services associated with your account
        service_ids = await client.get_services()
        print("Services:", service_ids)

        # Fetch the active session for the first service
        session = await client.get_session(service_ids[0])
        print("Connected:", session.is_connected)
        print("IPv4:", session.active_ipv4_prefix)
        print("IPv6:", session.active_ipv6_prefix)
        print("LFC:", session.service.lfc)

asyncio.run(main())
```

Or omit `api_key` and set the environment variable instead:

```bash
export QUICNZ_API_KEY="YOUR_API_KEY"
```

```python
async with QuicClient() as client:
    ...
```

## Reusing an aiohttp session

If your application already manages an `aiohttp.ClientSession` you can pass it
in to avoid creating an extra connection pool:

```python
import aiohttp
from quicnz import QuicClient

async with aiohttp.ClientSession() as http_session:
    client = QuicClient(api_key="YOUR_API_KEY", session=http_session)
    session = await client.get_session("service123")
```

## API reference

### `QuicClient(api_key=None, *, session=None)`

Main entry point.  Use as an async context manager or pass an existing
`aiohttp.ClientSession`.  If `api_key` is omitted, the `QUICNZ_API_KEY`
environment variable is used.  A `ValueError` is raised if neither is provided.

| Method | Returns | Description |
|---|---|---|
| `get_services()` | `list[str]` | Service IDs authorised for this API key |
| `get_session(service_id)` | `Session` | Active session for a service |
| `get_weathermap(source="website")` | `bytes` | Weather map image bytes (website or API source) |

### `Session`

| Attribute | Type | Description |
|---|---|---|
| `status` | `str` | e.g. `"connected"` |
| `is_connected` | `bool` | `True` when `status == "connected"` |
| `session_type` | `str` | `"DHCP"` or `"PPPoE"` |
| `active_ipv4_prefix` | `str` | Assigned IPv4 address |
| `active_ipv4_prefix_length` | `int` | IPv4 prefix length |
| `active_ipv6_prefix` | `str` | Assigned IPv6 prefix |
| `active_ipv6_prefix_length` | `int` | IPv6 prefix length |
| `last_radius_update` | `datetime` | Last RADIUS accounting update |
| `session_expires_at` | `datetime` | When the session expires |
| `ppp_payload` | `PPPPayload \| None` | PPPoE session details (PPPoE only) |
| `service` | `ServiceInfo` | Static service configuration |
| `created_at` | `datetime` | |
| `updated_at` | `datetime` | |

### `ServiceInfo`

| Attribute | Type | Description |
|---|---|---|
| `username` | `str` | PPPoE/DHCP username |
| `lfc` | `str` | Local Fibre Company (e.g. `"Chorus"`) |
| `status` | `str` | Service status (e.g. `"active"`) |
| `asid` | `str` | AS identifier |
| `datacap` | `float` | Data cap (0 = uncapped) |
| `static_ipv4_prefix` | `str` | Static IPv4 prefix (if any) |
| `static_ipv6_prefix` | `str` | Static IPv6 prefix (if any) |
| `routes` | `list[str]` | Announced routes |

### Exceptions

| Exception | When raised |
|---|---|
| `QuicAuthError` | HTTP 403 – invalid or missing API key |
| `QuicNotFoundError` | HTTP 404 – resource not found |
| `QuicAPIError` | Any other HTTP error; has `.status: int` attribute |
| `QuicError` | Base class for all quicnz exceptions |

## Rate limits

The Quic API enforces a limit of **120 requests per minute**.  Session data is
cached server-side for 5 minutes; the weather map is cached for 6 minutes.

The default weather map source is the website endpoint. Use the API endpoint explicitly if preferred:

```python
image = await client.get_weathermap(source="api")
```

## Development

```bash
# Clone and install in editable mode with dev extras
git clone https://github.com/ageron/quicnz
cd quicnz
pip install -e ".[dev]"

# Run tests
pytest

# Lint / type-check
ruff check src tests
mypy src
```

## Licence

[MIT](LICENSE)
