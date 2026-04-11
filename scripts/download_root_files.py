#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.atlas_download import ensure_atlas_open_data_downloaded


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download ATLAS Open Data ROOT files using the benchmark atlas_download utility."
    )
    parser.add_argument("--release", default="2025e-13tev-beta", help="ATLAS Open Data release.")
    parser.add_argument("--dataset", default="data", help="Dataset name, e.g. data or mc.")
    parser.add_argument("--skim", required=True, help="Skim/channel, e.g. GamGam or 2muons.")
    parser.add_argument("--protocol", default="https", help="Transfer protocol passed to atlasopenmagic.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Destination directory. Defaults to <project>/shared_input/<release>/<dataset>/<skim>.",
    )
    parser.add_argument("--max-files", type=int, default=0, help="Maximum number of files to fetch. 0 means all.")
    parser.add_argument("--workers", type=int, default=6, help="Parallel download workers.")
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional path to write the returned download metadata as JSON.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable verbose downloader logging.",
    )
    args = parser.parse_args()

    output_dir = args.output_dir or str(
        PROJECT_ROOT / "shared_input" / args.release / args.dataset / args.skim
    )

    result = ensure_atlas_open_data_downloaded(
        skim=args.skim,
        release=args.release,
        dataset=args.dataset,
        protocol=args.protocol,
        output_dir=output_dir,
        max_files=args.max_files,
        workers=args.workers,
        verbose=not args.quiet,
    )

    print(json.dumps(result, indent=2))

    output_path = Path(args.json_output) if args.json_output else Path(output_dir) / "download_manifest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote metadata to {output_path}")


if __name__ == "__main__":
    main()
