"""Convert an article URL with MagicMD and print a JSON payload."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from magicmd import MagicMDError, convert_article


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert an article URL to MagicMD JSON.")
    parser.add_argument("url", help="Public article URL.")
    parser.add_argument("--output-dir", help="Optional output directory for a content package.")
    parser.add_argument("--config", help="Optional .magicmd.toml path.")
    parser.add_argument("--platform", default="auto", help="Platform key, default: auto.")
    parser.add_argument("--no-images", action="store_true", help="Skip image downloads.")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        result = convert_article(
            url=args.url,
            platform=args.platform,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            download_images=not args.no_images,
            config_path=Path(args.config) if args.config else None,
        )
    except MagicMDError as exc:
        print(
            json.dumps(
                {"ok": False, "error": exc.__class__.__name__, "message": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    indent = None if args.compact else 2
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
