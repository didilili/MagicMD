"""Example CMS import pipeline built on the MagicMD SDK."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from shutil import copy2

from magicmd import convert_article


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert an article and prepare a CMS payload.")
    parser.add_argument("url", help="Public article URL.")
    parser.add_argument("--workdir", default="output/cms-import-demo", help="MagicMD package directory.")
    parser.add_argument("--media-prefix", default="/media/articles", help="Public media URL prefix.")
    return parser.parse_args()


def copy_media_and_rewrite(markdown: str, images: list, media_dir: Path, media_prefix: str) -> tuple[str, list[dict]]:
    media_dir.mkdir(parents=True, exist_ok=True)
    media_rows: list[dict] = []

    for image in images:
        if not image.local_path:
            continue

        source_path = Path(image.local_path)
        target_path = media_dir / source_path.name
        copy2(source_path, target_path)

        public_url = f"{media_prefix.rstrip('/')}/{media_dir.name}/{source_path.name}"
        markdown = markdown.replace(image.markdown_path, public_url)
        media_rows.append(
            {
                "source_url": image.source_url,
                "storage_path": str(target_path),
                "public_url": public_url,
                "alt": image.alt,
            }
        )

    return markdown, media_rows


def main() -> int:
    args = parse_args()
    workdir = Path(args.workdir)

    result = convert_article(args.url, output_dir=workdir, download_images=True)
    media_dir = workdir / "cms-media" / result.content_hash
    markdown, media_rows = copy_media_and_rewrite(
        result.markdown,
        result.images,
        media_dir,
        args.media_prefix,
    )

    payload = {
        "title": result.title,
        "author": result.author,
        "platform": result.platform,
        "source_url": result.canonical_url or result.source_url,
        "published_at": result.published_at,
        "content_hash": result.content_hash,
        "markdown": markdown,
        "media": media_rows,
        "warnings": result.warnings,
        "report": result.report,
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
