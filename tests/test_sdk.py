import json
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from magicmd import (
    FetchError,
    ParseError,
    UnsupportedPlatformError,
    convert_article,
)
from magicmd.cli import app
from magicmd.models import Article, ExtractionInfo, ImageAsset
from magicmd.sdk import _resolve_media_local_path


runner = CliRunner()


def _article(url: str = "https://example.com/post") -> Article:
    return Article(
        title="SDK 文章",
        author="MagicMD",
        platform="generic",
        source_url=url,
        canonical_url=url,
        published_at="2026-06-07T12:00:00+08:00",
        excerpt="SDK 摘要",
        content_markdown="正文\n\n![示意图](https://example.com/a.png)",
        images=[ImageAsset(source_url="https://example.com/a.png", alt="示意图")],
        extraction=ExtractionInfo(platform="generic", parser="generic", warnings=["demo_warning"]),
    )


def test_convert_article_returns_markdown_and_metadata_without_writing(tmp_path: Path):
    def fake_fetch(url, platform, config_path):
        return "<html>ok</html>"

    def fake_parse(platform, html, url):
        return _article(url)

    result = convert_article(
        "https://example.com/post",
        platform="generic",
        output_dir=None,
        download_images=False,
        _fetch_for_platform=fake_fetch,
        _parse_article=fake_parse,
    )

    assert result.package_dir is None
    assert result.title == "SDK 文章"
    assert result.author == "MagicMD"
    assert result.platform == "generic"
    assert result.source_url == "https://example.com/post"
    assert result.canonical_url == "https://example.com/post"
    assert result.published_at == "2026-06-07T12:00:00+08:00"
    assert result.excerpt == "SDK 摘要"
    assert "# SDK 文章" in result.markdown
    assert "正文" in result.markdown
    assert result.content_hash
    assert result.images[0].source_url == "https://example.com/a.png"
    assert result.images[0].alt == "示意图"
    assert result.warnings == ["demo_warning"]
    assert result.report["parser"] == "generic"
    assert result.metadata["title"] == "SDK 文章"
    assert list(tmp_path.iterdir()) == []


def test_convert_article_writes_package_when_output_dir_is_set(tmp_path: Path):
    def fake_fetch(url, platform, config_path):
        return "<html>ok</html>"

    def fake_parse(platform, html, url):
        return _article(url)

    result = convert_article(
        "https://example.com/post",
        platform="generic",
        output_dir=tmp_path,
        download_images=False,
        _fetch_for_platform=fake_fetch,
        _parse_article=fake_parse,
    )

    assert result.package_dir is not None
    package_dir = Path(result.package_dir)
    assert package_dir.parent == tmp_path
    assert (package_dir / "article.md").exists()
    assert (package_dir / "metadata.json").exists()
    assert (package_dir / "extraction-report.json").exists()
    metadata = json.loads((package_dir / "metadata.json").read_text(encoding="utf-8"))
    report = json.loads((package_dir / "extraction-report.json").read_text(encoding="utf-8"))
    assert metadata["title"] == "SDK 文章"
    assert report["warnings"] == ["demo_warning"]
    assert result.markdown == (package_dir / "article.md").read_text(encoding="utf-8")
    assert result.docx_path is None


def test_convert_article_writes_docx_when_enabled(monkeypatch, tmp_path: Path):
    def fake_fetch(url, platform, config_path):
        return "<html>ok</html>"

    def fake_parse(platform, html, url):
        return _article(url)

    def fake_write_docx(markdown_path, docx_path, config):
        docx_path.write_bytes(b"docx")

    monkeypatch.setattr("magicmd.output.write_docx_from_markdown", fake_write_docx)

    result = convert_article(
        "https://example.com/post",
        platform="generic",
        output_dir=tmp_path,
        download_images=False,
        docx=True,
        _fetch_for_platform=fake_fetch,
        _parse_article=fake_parse,
    )

    assert result.package_dir is not None
    assert result.docx_path == str(Path(result.package_dir) / "article.docx")
    assert Path(result.docx_path).read_bytes() == b"docx"


def test_convert_article_writes_docx_from_config(monkeypatch, tmp_path: Path):
    def fake_fetch(url, platform, config_path):
        return "<html>ok</html>"

    def fake_parse(platform, html, url):
        return _article(url)

    def fake_write_docx(markdown_path, docx_path, config):
        docx_path.write_bytes(b"docx")

    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [docx]
        enabled = true
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr("magicmd.output.write_docx_from_markdown", fake_write_docx)

    result = convert_article(
        "https://example.com/post",
        platform="generic",
        output_dir=tmp_path,
        download_images=False,
        config_path=config_path,
        _fetch_for_platform=fake_fetch,
        _parse_article=fake_parse,
    )

    assert result.package_dir is not None
    assert result.docx_path == str(Path(result.package_dir) / "article.docx")


def test_convert_article_separates_image_local_path_from_markdown_path(monkeypatch, tmp_path: Path):
    def fake_fetch(url, platform, config_path):
        return "<html>ok</html>"

    def fake_parse(platform, html, url):
        return _article(url)

    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [images]
        directory = "assets/images"
        filename_pattern = "cover_{index:02d}.{ext}"
        markdown_path = "/static/{directory}/{filename}"
        """,
        encoding="utf-8",
    )

    def fake_download_images(
        article,
        package_dir,
        image_dir_name,
        filename_pattern="img_{index:03d}.{ext}",
        markdown_path_pattern="{directory}/{filename}",
    ):
        image_dir = package_dir / image_dir_name
        image_dir.mkdir(parents=True, exist_ok=True)
        filename = filename_pattern.format(index=1, ext="png")
        (image_dir / filename).write_bytes(b"image")
        markdown_path = markdown_path_pattern.format(
            directory=image_dir_name,
            filename=filename,
            index=1,
            ext="png",
        )
        next_image = article.images[0].model_copy(update={"local_path": markdown_path})
        return article.model_copy(
            update={
                "images": [next_image],
                "content_markdown": article.content_markdown.replace(
                    "https://example.com/a.png", markdown_path
                ),
            }
        )

    monkeypatch.setattr("magicmd.assets.download_images", fake_download_images)

    result = convert_article(
        "https://example.com/post",
        platform="generic",
        output_dir=tmp_path,
        config_path=config_path,
        _fetch_for_platform=fake_fetch,
        _parse_article=fake_parse,
    )

    package_dir = Path(result.package_dir or "")
    assert result.images[0].markdown_path == "/static/assets/images/cover_01.png"
    assert result.images[0].local_path == str(package_dir / "assets/images/cover_01.png")


def test_convert_article_returns_downloaded_video_paths(monkeypatch, tmp_path: Path):
    video_url = "https://mpvideo.qpic.cn/demo.mp4"

    def fake_fetch(url, platform, config_path):
        return "<html>ok</html>"

    def fake_parse(platform, html, url):
        return Article(
            title="SDK 视频文章",
            platform="generic",
            source_url=url,
            content_markdown=f"[视频]({video_url})",
            extraction=ExtractionInfo(platform="generic", parser="generic"),
        )

    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [images]
        download = false

        [videos]
        download = true
        """,
        encoding="utf-8",
    )

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "video/mp4"},
            content=b"mp4-data",
        )

    monkeypatch.setattr("magicmd.assets._video_transport", lambda: httpx.MockTransport(handler))

    result = convert_article(
        "https://example.com/post",
        platform="generic",
        output_dir=tmp_path,
        config_path=config_path,
        _fetch_for_platform=fake_fetch,
        _parse_article=fake_parse,
    )

    result_package = Path(result.package_dir or "")
    assert result.videos[0].source_url == video_url
    assert result.videos[0].markdown_path == "videos/video_001.mp4"
    assert result.videos[0].local_path == str(result_package / "videos/video_001.mp4")
    assert result.videos[0].extension == ".mp4"


def test_resolve_media_local_path_prefers_configured_file_over_absolute_markdown_path(
    tmp_path: Path,
):
    package_dir = tmp_path / "package"
    configured_path = package_dir / "assets" / "videos" / "clip.mp4"
    configured_path.parent.mkdir(parents=True)
    configured_path.write_bytes(b"package-video")
    public_path = tmp_path / "public" / "clip.mp4"
    public_path.parent.mkdir()
    public_path.write_bytes(b"outside-video")

    resolved = _resolve_media_local_path(
        str(public_path),
        package_dir,
        "assets/videos",
    )

    assert resolved == str(configured_path)


def test_resolve_media_local_path_rejects_parent_traversal(tmp_path: Path):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    outside_path = tmp_path / "outside.mp4"
    outside_path.write_bytes(b"outside-video")

    resolved = _resolve_media_local_path(
        "../outside.mp4",
        package_dir,
        "videos",
    )

    assert resolved == ""


def test_convert_article_does_not_force_media_download_without_output_dir(monkeypatch):
    def fake_fetch(url, platform, config_path):
        return "<html>ok</html>"

    def fake_parse(platform, html, url):
        return _article(url)

    def fail_download(*args, **kwargs):
        raise AssertionError("media download should require output_dir")

    monkeypatch.setattr("magicmd.assets.download_images", fail_download)

    result = convert_article(
        "https://example.com/post",
        platform="generic",
        output_dir=None,
        download_images=True,
        _fetch_for_platform=fake_fetch,
        _parse_article=fake_parse,
    )

    assert result.package_dir is None
    assert result.images[0].markdown_path == ""


def test_convert_article_raises_unsupported_platform():
    with pytest.raises(UnsupportedPlatformError) as exc_info:
        convert_article("https://example.com/post", platform="unknown", output_dir=None)

    assert exc_info.value.stage == "detect"
    assert "Unsupported platform" in str(exc_info.value)


def test_convert_article_raises_fetch_error():
    def fail_fetch(url, platform, config_path):
        raise RuntimeError("network failed")

    with pytest.raises(FetchError) as exc_info:
        convert_article(
            "https://example.com/post",
            platform="generic",
            output_dir=None,
            _fetch_for_platform=fail_fetch,
        )

    assert exc_info.value.stage == "fetch"
    assert "network failed" in str(exc_info.value)


def test_convert_article_raises_parse_error():
    def fake_fetch(url, platform, config_path):
        return "<html>broken</html>"

    def fail_parse(platform, html, url):
        raise RuntimeError("parse failed")

    with pytest.raises(ParseError) as exc_info:
        convert_article(
            "https://example.com/post",
            platform="generic",
            output_dir=None,
            _fetch_for_platform=fake_fetch,
            _parse_article=fail_parse,
        )

    assert exc_info.value.stage == "parse"
    assert "parse failed" in str(exc_info.value)


def test_cli_convert_reuses_convert_article(monkeypatch, tmp_path: Path):
    called = {}
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "article.md").write_text("# SDK CLI\n\n正文", encoding="utf-8")
    (package_dir / "metadata.json").write_text(
        json.dumps(
            {
                "title": "SDK CLI",
                "source_url": "https://example.com/post",
                "canonical_url": "https://example.com/post",
                "platform": "generic",
                "images": [],
                "extraction": {"warnings": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class FakeResult:
        pass

    fake_result = FakeResult()
    fake_result.package_dir = str(package_dir)

    def fake_convert_article(**kwargs):
        called.update(kwargs)
        return fake_result

    monkeypatch.setattr("magicmd.cli.convert_article", fake_convert_article)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://example.com/post",
            "--platform",
            "generic",
            "--output",
            str(tmp_path),
            "--no-images",
            "--format",
            "docx",
        ],
    )

    assert result.exit_code == 0
    assert called["url"] == "https://example.com/post"
    assert called["platform"] == "generic"
    assert called["output_dir"] == tmp_path
    assert called["download_images"] is False
    assert called["docx"] is True
    assert callable(called["_fetch_for_platform"])
    assert callable(called["_parse_article"])
