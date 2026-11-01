#!/usr/bin/env python3
"""Convert user-facing localization and obvious application labels to Zeus.

Preserve original Hermes identifiers: URLs, env names, Python modules,
TypeScript symbols, command strings, telemetry ownership and legal notices.
"""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
WHOLE_BRAND = re.compile(r"(?<![A-Za-z0-9_$])Hermes(?![A-Za-z0-9_$])")


def update(path, before, after, changed):
    if before != after:
        path.write_text(after, encoding="utf-8")
        changed.append(path.relative_to(ROOT).as_posix())


def apply():
    if not (ROOT / "LICENSE").exists():
        raise RuntimeError("No upstream LICENSE; abort")
    changed = []
    for dirname in ("web/src/i18n", "apps/desktop/src/i18n"):
        directory = ROOT / dirname
        if not directory.is_dir():
            raise RuntimeError(f"missing locale source: {dirname}")
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix not in (".ts", ".tsx", ".json"):
                continue
            if ".test." in path.name:
                continue
            before = path.read_text(encoding="utf-8")
            after = WHOLE_BRAND.sub("Zeus", before)
            after = re.sub(r'(\bbrandShort:\s*["\x27])HA(?=["\x27])', r'\g<1>ZA', after)
            update(path, before, after, changed)

    # Plain display strings only, never internal handlers or API names.
    substitutions = {
        "web/src/App.tsx": {
            "This restarts the Hermes gateway process.": "This restarts the Zeus gateway process.",
        },
        "website/docusaurus.config.ts": {
            "alt: 'Hermes Agent',": "alt: 'Zeus Agent',",
        },
    }
    for name, pairs in substitutions.items():
        path = ROOT / name
        before = path.read_text(encoding="utf-8")
        after = before
        for old, new in pairs.items():
            after = after.replace(old, new)
        update(path, before, after, changed)
    return changed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        parser.error("use --apply on a work branch")
    print(json.dumps({"updated": apply()}, indent=2))
