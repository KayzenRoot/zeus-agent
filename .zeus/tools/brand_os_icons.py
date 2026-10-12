#!/usr/bin/env python3
"""Deterministic Zeus Windows/macOS icons, standard library only."""
import argparse
import json
from pathlib import Path
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]


def bolt(x, y):
    points = ((76, 16), (37, 71), (62, 71), (54, 112), (93, 50), (67, 50))
    inside = False
    ax, ay = points[-1]
    for bx, by in points:
        if (ay > y) != (by > y):
            cross = (bx - ax) * (y - ay) / (by - ay) + ax
            if x < cross:
                inside = not inside
        ax, ay = bx, by
    return inside


def png(width, height, transparent=False):
    if min(width, height) < 1 or max(width, height) > 1024:
        raise ValueError("invalid icon dimensions")
    side = min(width, height)
    cx, cy = (width - side) / 2, (height - side) / 2
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            u, v = (x - cx + 0.5) * 128 / side, (y - cy + 0.5) * 128 / side
            rows.extend((250, 193, 73, 255) if bolt(u, v)
                        else ((0, 0, 0, 0) if transparent else (22, 29, 71, 255)))

    def chunk(kind, value):
        return (struct.pack(">I", len(value)) + kind + value +
                struct.pack(">I", zlib.crc32(kind + value) & 0xffffffff))

    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(bytes(rows), 9)) +
            chunk(b"IEND", b""))


def ico():
    sizes = (16, 32, 48, 64, 128, 256)
    images = [png(n, n) for n in sizes]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    for size, data in zip(sizes, images):
        encoded_size = size if size < 256 else 0
        header += struct.pack("<BBBBHHII", encoded_size, encoded_size, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return header + b"".join(images)


def icns():
    chunks = []
    for size, kind in ((16, b"icp4"), (32, b"icp5"), (64, b"icp6"), (128, b"ic07"),
                       (256, b"ic08"), (512, b"ic09"), (1024, b"ic10")):
        data = png(size, size)
        chunks.append(kind + struct.pack(">I", len(data) + 8) + data)
    payload = b"".join(chunks)
    return b"icns" + struct.pack(">I", len(payload) + 8) + payload


def dimensions(path):
    name = path.name
    square = re.match(r"^Square(\d+)x(\d+)Logo", name)
    if square:
        width, height = map(int, square.groups())
    elif name.startswith("Wide310x150Logo"):
        width, height = 310, 150
    elif name.startswith("StoreLogo"):
        width, height = 50, 50
    else:
        raise ValueError(f"unrecognized MSIX tile: {name}")
    sized = re.search(r"\.targetsize-(\d+)", name)
    scaled = re.search(r"\.scale-(\d+)", name)
    if sized:
        width = height = int(sized.group(1))
    elif scaled:
        f = int(scaled.group(1)) / 100
        width, height = round(width * f), round(height * f)
    return width, height


def generate():
    if not (ROOT / "LICENSE").exists():
        raise RuntimeError("upstream license absent; abort")
    assets = ROOT / "apps/desktop/assets"
    if not assets.is_dir():
        raise RuntimeError("upstream Electron assets absent; abort")
    updates = []

    def save(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != content:
            path.write_bytes(content)
            updates.append(path.relative_to(ROOT).as_posix())

    for name in ("icon.ico", "icon-dark.ico"):
        save(assets / name, ico())
    for name in ("icon.icns", "icon-dark.icns"):
        save(assets / name, icns())
    for name in ("icon.png", "icon-dark.png", "icon-mac.png"):
        save(assets / name, png(512, 512))
    for name in ("art-dark.png", "art-light.png", "mono.png"):
        save(assets / "icon.icon/Assets" / name, png(1024, 1024, transparent=True))
    tiles = sorted((assets / "appx").glob("*.png"))
    if len(tiles) < 10:
        raise RuntimeError("MSIX tile inventory unexpectedly empty")
    for path in tiles:
        w, h = dimensions(path)
        save(path, png(w, h))
    return updates


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        parser.error("use --apply to update the checkout")
    print(json.dumps({"updated": generate()}, indent=2))
