import json
from pathlib import Path

from magicmd.config import OutputConfig, OutputNamingConfig
from magicmd.models import Article, ExtractionInfo
from magicmd.output import write_article_package


def test_write_article_package_creates_markdown_and_metadata(tmp_path: Path):
    article = Article(
        title="Codex 实战",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    package_dir = write_article_package(article, tmp_path)

    assert (package_dir / "article.md").exists()
    metadata = json.loads((package_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["title"] == "Codex 实战"


def test_write_article_package_uses_configured_output_names(tmp_path: Path):
    article = Article(
        title="Codex 实战",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-06T12:00:00+08:00",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    output_config = OutputConfig(
        naming=OutputNamingConfig(
            package="{date}/{slug}",
            markdown="index.md",
            metadata="meta.json",
            report="report.json",
        )
    )

    package_dir = write_article_package(article, tmp_path, output_config=output_config)

    assert package_dir == tmp_path / "2026-06-06" / "codex-实战"
    assert (package_dir / "index.md").exists()
    assert (package_dir / "meta.json").exists()
