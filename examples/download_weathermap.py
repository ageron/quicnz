"""Download the Quic network weather map and save it as a JPEG file.

Usage:
    python download_weathermap.py              # saves to weathermap.jpg
    python download_weathermap.py ~/map.jpg    # custom output path
"""

import asyncio
import sys
from pathlib import Path

from quicnz import QuicClient

from _auth import load_api_key

DEFAULT_OUTPUT = Path("weathermap.jpg")


async def main(output: Path) -> None:
    async with QuicClient(api_key=load_api_key()) as client:
        data = await client.get_weathermap()

    output.write_bytes(data)
    print(f"Weather map saved to {output} ({len(data):,} bytes)")


if __name__ == "__main__":
    out = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_OUTPUT
    asyncio.run(main(out))
