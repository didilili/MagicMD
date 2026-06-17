import json
from pathlib import Path

from magicmd.config import DocxConfig, OutputConfig, OutputNamingConfig
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
            docx="article.docx",
        )
    )

    package_dir = write_article_package(article, tmp_path, output_config=output_config)

    assert package_dir == tmp_path / "2026-06-06" / "codex-实战"
    assert (package_dir / "index.md").exists()
    assert (package_dir / "meta.json").exists()


def test_write_article_package_does_not_write_docx_by_default(tmp_path: Path):
    article = Article(
        title="Codex 实战",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    package_dir = write_article_package(article, tmp_path)

    assert (package_dir / "article.md").exists()
    assert not (package_dir / "article.docx").exists()


def test_write_article_package_writes_docx_when_enabled(monkeypatch, tmp_path: Path):
    article = Article(
        title="Codex 实战",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    calls = []

    def fake_write_docx(markdown_path, docx_path, config):
        calls.append((markdown_path, docx_path, config))
        docx_path.write_bytes(b"docx")

    monkeypatch.setattr("magicmd.output.write_docx_from_markdown", fake_write_docx)

    package_dir = write_article_package(
        article,
        tmp_path,
        docx_config=DocxConfig(enabled=True),
    )

    assert (package_dir / "article.md").exists()
    assert (package_dir / "article.docx").read_bytes() == b"docx"
    assert calls == [
        (
            package_dir / "article.md",
            package_dir / "article.docx",
            DocxConfig(enabled=True),
        )
    ]


def test_write_article_package_uses_configured_docx_name(monkeypatch, tmp_path: Path):
    article = Article(
        title="Codex 实战",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    def fake_write_docx(markdown_path, docx_path, config):
        docx_path.write_bytes(b"docx")

    monkeypatch.setattr("magicmd.output.write_docx_from_markdown", fake_write_docx)

    package_dir = write_article_package(
        article,
        tmp_path,
        output_config=OutputConfig(naming=OutputNamingConfig(docx="word-export.docx")),
        docx_config=DocxConfig(enabled=True),
    )

    assert (package_dir / "word-export.docx").exists()
    assert not (package_dir / "article.docx").exists()


def test_write_article_package_clears_stale_generated_files_when_overwriting(
    tmp_path: Path,
):
    article = Article(
        title="Codex 实战",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="第一版",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    package_dir = write_article_package(article, tmp_path)
    image_dir = package_dir / "images"
    image_dir.mkdir()
    stale_image = image_dir / "img_999.png"
    stale_image.write_bytes(b"old")
    stale_docx = package_dir / "article.docx"
    stale_docx.write_bytes(b"old docx")

    updated_article = article.model_copy(update={"content_markdown": "第二版"})

    next_package_dir = write_article_package(updated_article, tmp_path, overwrite=True)

    assert next_package_dir == package_dir
    assert (package_dir / "article.md").read_text(encoding="utf-8").endswith("第二版\n")
    assert not stale_image.exists()
    assert not stale_docx.exists()


def test_write_article_package_does_not_delete_output_root_when_package_is_root(
    tmp_path: Path,
):
    article = Article(
        title="Codex 实战",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    output_config = OutputConfig(naming=OutputNamingConfig(package=""))
    keep_file = tmp_path / "keep.txt"
    keep_file.write_text("user note", encoding="utf-8")
    stale_image_dir = tmp_path / "images"
    stale_image_dir.mkdir()
    stale_image = stale_image_dir / "img_999.png"
    stale_image.write_bytes(b"old")

    package_dir = write_article_package(
        article,
        tmp_path,
        overwrite=True,
        output_config=output_config,
    )

    assert package_dir == tmp_path
    assert keep_file.read_text(encoding="utf-8") == "user note"
    assert not stale_image.exists()
    assert (tmp_path / "article.md").exists()


def test_write_article_package_does_not_remove_directory_outside_output_root(
    tmp_path: Path,
):
    article = Article(
        title="Codex 实战",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    outside_dir = tmp_path / "outside-package"
    outside_dir.mkdir()
    keep_file = outside_dir / "keep.txt"
    keep_file.write_text("do not delete", encoding="utf-8")
    output_config = OutputConfig(naming=OutputNamingConfig(package="../outside-package"))

    package_dir = write_article_package(
        article,
        output_dir,
        overwrite=True,
        output_config=output_config,
    )

    assert package_dir == output_dir / "../outside-package"
    assert keep_file.read_text(encoding="utf-8") == "do not delete"
    assert (outside_dir / "article.md").exists()
