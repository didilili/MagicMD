import json
from pathlib import Path

from pagemd.models import Article, ExtractionInfo
from pagemd.output import write_article_package


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
