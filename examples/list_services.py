"""List all service IDs associated with your Quic account."""

import asyncio

from quicnz import QuicClient

from _auth import load_api_key


async def main() -> None:
    async with QuicClient(api_key=load_api_key()) as client:
        service_ids = await client.get_services()

    if not service_ids:
        print("No services found for this API key.")
        return

    print(f"Found {len(service_ids)} service(s):")
    for sid in service_ids:
        print(f"  {sid}")


if __name__ == "__main__":
    asyncio.run(main())
