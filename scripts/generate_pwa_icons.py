#!/usr/bin/env python3
"""Generate minimal PWA icons (192 + 512) without external deps."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static"


def _png_rgb(size: int, r: int, g: int, b: int) -> bytes:
    """Solid-color RGB PNG."""
    row = b"\x00" + bytes([r, g, b]) * size
    raw = row * size
    compressed = zlib.compress(raw, 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Cyan accent #22d3ee on dark #0a0a0f — simple cyan square for launch
    for size, name in ((192, "icon-192.png"), (512, "icon-512.png")):
        path = OUT / name
        path.write_bytes(_png_rgb(size, 34, 211, 238))
        print(f"Created {path} ({size}x{size})")


if __name__ == "__main__":
    main()
