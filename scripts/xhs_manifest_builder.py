#!/usr/bin/env python3
"""Build assets/manifest.json from asset metadata files."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def role_from_meta(path: Path) -> str:
    return path.name[:-10] if path.name.endswith(".meta.json") else path.stem


def load_meta(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid metadata JSON: {path}")
    return data


def build_manifest(pack_dir: Path) -> dict[str, object]:
    assets_dir = pack_dir / "assets"
    if not assets_dir.exists():
        raise SystemExit(f"Assets directory not found: {assets_dir}")

    entries: list[dict[str, object]] = []
    for meta_path in sorted(assets_dir.glob("*.meta.json")):
        data = load_meta(meta_path)
        output = str(data.get("output", "")).strip()
        if not output:
            raise SystemExit(f"Missing output in metadata: {meta_path}")
        entries.append(
            {
                "path": output,
                "role": role_from_meta(meta_path),
                "model": str(data.get("model", "")).strip(),
                "prompt_hash": str(data.get("prompt_hash", "")).strip(),
                "status": str(data.get("status", "")).strip() or "generated",
                "width": data.get("width"),
                "height": data.get("height"),
                "bytes": data.get("bytes"),
            }
        )

    if not entries:
        raise SystemExit(f"No asset metadata files found in: {assets_dir}")

    return {"pack_dir": str(pack_dir.resolve()), "assets": entries, "updated_at": now_iso()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build XiaoHongShu asset manifest from meta files.")
    parser.add_argument("--pack-dir", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    pack_dir = Path(args.pack_dir)
    if not pack_dir.exists():
        raise SystemExit(f"Pack not found: {pack_dir}")

    manifest = build_manifest(pack_dir)
    output_path = Path(args.output) if args.output else pack_dir / "assets" / "manifest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
