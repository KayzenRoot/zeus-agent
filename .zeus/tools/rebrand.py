#!/usr/bin/env python3
"""ZEUS-001, safe first-pass branding overlay. Requires imported upstream MIT LICENSE."""
import argparse
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[2]
REPLACEMENTS = {
    "web/index.html": (
        ('<title>Hermes Agent - Dashboard</title>', '<title>Zeus Agent - Dashboard</title>'),
        ('type="image/svg+xml" href="/favicon.ico"', 'type="image/svg+xml" href="/zeus-mark.svg"'),
    ),
    "apps/desktop/index.html": (
        ('<title>Hermes</title>', '<title>Zeus Agent</title>'),
        ('<link rel="icon" type="image/png" sizes="180x180" href="/apple-touch-icon.png" />',
         '<link rel="icon" type="image/svg+xml" href="/zeus-mark.svg" />'),
    ),
    "apps/desktop/package.json": (
        ('"productName": "Hermes"', '"productName": "Zeus Agent"'),
        ('"description": "Native desktop shell for Hermes Agent."',
         '"description": "Native desktop shell for Zeus Agent."'),
    ),
    "website/docusaurus.config.ts": (
        ("title: 'Hermes Agent',", "title: 'Zeus Agent',"),
        ("favicon: 'img/favicon.ico',", "favicon: 'img/zeus-mark.svg',"),
        ("image: 'img/hermes-agent-banner.png',", "image: 'img/zeus-banner.svg',"),
    ),
    # README now has a Zeus-owned structure; do not overwrite it with upstream anchors.
}


def update_text_file(root, relative, pairs):
    target = root / relative
    original = target.read_text(encoding="utf-8")
    content = original
    for old, new in pairs:
        if old not in content and new not in content:
            raise ValueError(f"Expected upstream branding anchor not found in {relative}: {old!r}")
        content = content.replace(old, new)
    if content != original:
        target.write_text(content, encoding="utf-8")
        return True
    return False


def in_bolt(x, y):
    pts = ((76, 16), (37, 71), (62, 71), (54, 112), (93, 50), (67, 50))
    hit = False
    ax, ay = pts[-1]
    for bx, by in pts:
        if (ay > y) != (by > y):
            cut = (bx - ax) * (y - ay) / (by - ay) + ax
            if x < cut:
                hit = not hit
        ax, ay = bx, by
    return hit


def png_icon(size=128):
    if not 1 <= size <= 256:
        raise ValueError("Icon size out of range")

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)

    scanlines = bytearray()
    for row in range(size):
        scanlines.append(0)
        for col in range(size):
            x, y = (col + .5) * 128 / size, (row + .5) * 128 / size
            scanlines.extend((249, 192, 72, 255) if in_bolt(x, y) else (22, 29, 71, 255))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(bytes(scanlines), level=9)) +
            chunk(b"IEND", b""))


def ico_icon():
    payload = png_icon(128)
    return (struct.pack("<HHH", 0, 1, 1) +
            struct.pack("<BBBBHHII", 128, 128, 0, 0, 1, 32, len(payload), 22) + payload)


def apply_brand(root):
    license_path = root / "LICENSE"
    if not license_path.is_file() or "Nous Research" not in license_path.read_text(encoding="utf-8"):
        raise RuntimeError("Import original Hermes source and MIT LICENSE before applying brand")

    icon = (root / ".zeus/brand/zeus-mark.svg").read_text(encoding="utf-8")
    wordmark = (root / ".zeus/brand/zeus-wordmark.svg").read_text(encoding="utf-8")
    ET.fromstring(icon)
    ET.fromstring(wordmark)
    missing = [name for name in REPLACEMENTS if not (root / name).is_file()]
    if missing:
        raise RuntimeError("Unexpected upstream file layout: " + ", ".join(missing))

    changed = []
    for name, replacements in REPLACEMENTS.items():
        if update_text_file(root, name, replacements):
            changed.append(name)

    payloads = {
        "web/public/zeus-mark.svg": icon.encode(),
        "web/public/favicon.ico": ico_icon(),
        "apps/desktop/public/zeus-mark.svg": icon.encode(),
        "apps/desktop/public/apple-touch-icon.png": png_icon(),
        "website/static/img/zeus-mark.svg": icon.encode(),
        "website/static/img/zeus-banner.svg": wordmark.encode(),
        "website/static/img/favicon.ico": ico_icon(),
        "website/static/img/apple-touch-icon.png": png_icon(),
        "assets/zeus-banner.svg": wordmark.encode(),
        "assets/zeus-mark.svg": icon.encode(),
        "assets/icon-master.svg": icon.encode(),
        "assets/icon-master-dark.svg": icon.encode(),
    }
    for relative, data in payloads.items():
        dest = root / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.read_bytes() != data:
            dest.write_bytes(data)
            changed.append(relative)

    # Only replace complete visible phrases in translation content.
    # Do not rename Python modules, JSON-RPC methods, CLI or environment keys.
    for directory_name in ("web/src/i18n", "apps/desktop/src/i18n"):
        directory = root / directory_name
        if directory.is_dir():
            for file in directory.rglob("*"):
                if not file.is_file() or file.suffix not in (".json", ".ts", ".tsx"):
                    continue
                if ".test." in file.name:
                    continue
                original = file.read_text(encoding="utf-8")
                revised = original.replace("Hermes Agent", "Zeus Agent").replace("Hermes Desktop", "Zeus Desktop")
                if revised != original:
                    file.write_text(revised, encoding="utf-8")
                    changed.append(file.relative_to(root).as_posix())

    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        parser.error("use --apply on a local work branch after importing Hermes")
    changes = apply_brand(ROOT)
    print(json.dumps({"changed_files": changes, "count": len(changes)}, indent=2))
    print("First visual branding pass only. Review residual upstream UI strings before approving.")


if __name__ == "__main__":
    main()
