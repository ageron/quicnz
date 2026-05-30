"""Download the Quic network weather map and save it as a JPEG file.

Usage:
    python download_weathermap.py              # saves to weathermap.jpg
    python download_weathermap.py ~/map.jpg    # custom output path
    python download_weathermap.py --wait-minutes 6
"""

import argparse
import asyncio
from pathlib import Path
from typing import Literal

from quicnz import QuicClient

from _auth import load_api_key

DEFAULT_OUTPUT = Path("weathermap.jpg")


async def main(output: Path, wait_minutes: float, source: Literal["api", "website"]) -> None:
    if wait_minutes > 0:
        wait_seconds = wait_minutes * 60
        print(f"Waiting {wait_minutes:g} minutes before download...")
        await asyncio.sleep(wait_seconds)

    async with QuicClient(api_key=load_api_key()) as client:
        data = await client.get_weathermap(source=source)

    output.write_bytes(data)
    print(f"Weather map saved to {output} ({len(data):,} bytes)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        default=str(DEFAULT_OUTPUT),
        help="Output file path (default: weathermap.jpg)",
    )
    parser.add_argument(
        "--wait-minutes",
        type=float,
        default=0.0,
        help="Minutes to wait before downloading (useful because maps regenerate every ~6 minutes)",
    )
    parser.add_argument(
        "--source",
        choices=("api", "website"),
        default="website",
        help="Weather map source to use (default: website)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    out = Path(args.output).expanduser()
    asyncio.run(main(out, wait_minutes=args.wait_minutes, source=args.source))
