"""Shared helper: load the Quic API key for example scripts.

The key is read from ~/.quicnz_api.key (plain text, one line).
If that file does not exist, the QUICNZ_API_KEY environment variable is used
as a fallback.

See examples/README.md for setup instructions.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

_KEY_FILE = Path("~/.quicnz_api.key").expanduser()


def load_api_key() -> str:
    """Return the API key, or exit with a helpful message if it cannot be found."""
    if _KEY_FILE.exists():
        _warn_if_permissive(_KEY_FILE)
        key = _KEY_FILE.read_text().strip()
        if key:
            return key

    env_key = os.environ.get("QUICNZ_API_KEY", "").strip()
    if env_key:
        return env_key

    sys.exit(
        f"No API key found.\n"
        f"  Create {_KEY_FILE} containing your Quic API key, then run:\n"
        f"    chmod og-rwx {_KEY_FILE}\n"
        f"  Or set the QUICNZ_API_KEY environment variable."
    )


def _warn_if_permissive(path: Path) -> None:
    """Warn when the key file is readable by group or others."""
    mode = path.stat().st_mode
    if mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH):
        print(
            f"Warning: {path} is readable by others. "
            f"Run: chmod og-rwx {path}",
            file=sys.stderr,
        )
