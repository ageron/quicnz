"""Show the active session status for a Quic service.

Usage:
    python session_status.py              # uses the first service on your account
    python session_status.py <service-id> # specify a service ID explicitly
"""

import asyncio
import sys
from datetime import timezone

from quicnz import QuicClient, QuicNotFoundError

from _auth import load_api_key


async def main(service_id: str | None) -> None:
    async with QuicClient(api_key=load_api_key()) as client:
        if service_id is None:
            service_ids = await client.get_services()
            if not service_ids:
                sys.exit("No services found for this API key.")
            service_id = service_ids[0]
            if len(service_ids) > 1:
                print(f"Multiple services found; showing first: {service_id}")

        try:
            session = await client.get_session(service_id)
        except QuicNotFoundError:
            sys.exit(f"No active session found for service '{service_id}'.")

    # ---- service configuration ----
    svc = session.service
    print(f"Service ID   : {service_id}")
    print(f"LFC          : {svc.lfc}")
    print(f"Entity       : {svc.entity} (ID: {svc.entity_unique_id})")
    print(f"Service status: {svc.status}")
    print(f"Username     : {svc.username}")
    if svc.datacap:
        print(f"Data cap     : {svc.datacap} GB")
    else:
        print(f"Data cap     : uncapped")

    # ---- session ----
    print()
    connected = "YES" if session.is_connected else "NO"
    print(f"Connected    : {connected}  ({session.status})")
    print(f"Session type : {session.session_type}")
    print(f"IPv4 address : {session.active_ipv4_prefix}/{session.active_ipv4_prefix_length}")
    print(f"IPv6 prefix  : {session.active_ipv6_prefix}/{session.active_ipv6_prefix_length}")

    local_expires = session.session_expires_at.astimezone()
    print(f"Session expires : {local_expires.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    local_updated = session.last_radius_update.astimezone()
    print(f"Last RADIUS update: {local_updated.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # ---- PPPoE details (if present) ----
    if session.ppp_payload:
        ppp = session.ppp_payload
        print()
        print("PPPoE details:")
        print(f"  NAS identifier  : {ppp.nas_identifier}")
        print(f"  Circuit ID      : {ppp.adsl_agent_circuit_id}")
        print(f"  Remote ID       : {ppp.adsl_agent_remote_id}")
        print(f"  Calling station : {ppp.calling_station_id}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(arg))
