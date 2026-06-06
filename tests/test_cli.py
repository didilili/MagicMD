from pathlib import Path

import json
import io
import sys

from rich.console import Console
from typer.testing import CliRunner

from pagemd.cli import ProgressReporter, app, entrypoint
from pagemd.cli import convert_url


runner = CliRunner()


def test_doctor_command():
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "ok" in result.stdout


def test_convert_command_writes_package(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="掘金文章标题"></head>
      <body><article><p>掘金正文</p></article></body>
    </html>
    """

    monkeypatch.setattr("pagemd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--output",
            str(tmp_path),
            "--no-images",
        ],
    )

    assert result.exit_code == 0
    assert "Created output package" in result.stdout
    assert list(tmp_path.glob("*/article.md"))
    assert list(tmp_path.glob("*/metadata.json"))


def test_convert_command_prints_progress_steps(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="进度文章"></head>
      <body><article><p>正文</p></article></body>
    </html>
    """
    monkeypatch.setattr("pagemd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--output",
            str(tmp_path),
            "--no-images",
        ],
    )

    assert result.exit_code == 0
    assert "✓ [1/6] Detecting platform" in result.stdout
    assert "✓ [2/6] Fetching article" in result.stdout
    assert "✓ [3/6] Parsing article" in result.stdout
    assert "✓ [4/6] Writing Markdown package" in result.stdout
    assert "✓ [5/6] Skipping image download" in result.stdout
    assert "✓ [6/6] Saving extraction report" in result.stdout


def test_progress_reporter_prints_green_completion():
    output = io.StringIO()
    console = Console(
        file=output,
        force_terminal=True,
        color_system="standard",
        no_color=False,
        width=100,
    )
    reporter = ProgressReporter(enabled=True, console=console)

    result = reporter.run(1, 1, "Testing progress", lambda: "done")

    assert result == "done"
    rendered = output.getvalue()
    assert "\x1b[32m✓\x1b[0m" in rendered
    assert "Testing progress" in rendered


def test_root_url_alias_converts_with_default_output(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="根命令文章"></head>
      <body><article><p>正文</p></article></body>
    </html>
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("pagemd.cli.fetch_for_platform", lambda url, platform, config_path: html)
    monkeypatch.setattr(sys, "argv", ["pagemd", "https://juejin.cn/post/demo"])

    entrypoint()

    assert list((tmp_path / "output").glob("*/article.md"))


def test_root_url_alias_honors_output_debug_and_no_images_options(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="根命令参数文章"></head>
      <body><article><p>正文</p><img src="https://example.com/a.png" /></article></body>
    </html>
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("pagemd.cli.fetch_for_platform", lambda url, platform, config_path: html)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pagemd",
            "https://juejin.cn/post/demo",
            "--output",
            str(tmp_path / "custom"),
            "--debug",
            "--no-images",
        ],
    )

    entrypoint()

    package_dirs = list((tmp_path / "custom").glob("*"))
    assert len(package_dirs) == 1
    assert (package_dirs[0] / "debug.html").exists()
    assert not (package_dirs[0] / "images").exists()


def test_batch_command_ignores_comments(monkeypatch, tmp_path: Path):
    urls = tmp_path / "urls.txt"
    urls.write_text(
        "# comment\nhttps://juejin.cn/post/demo\n\n",
        encoding="utf-8",
    )
    calls = []

    def fake_convert_url(url, output, **kwargs):
        calls.append(url)
        package = tmp_path / "pkg"
        package.mkdir(exist_ok=True)
        return package

    monkeypatch.setattr("pagemd.cli.convert_url", fake_convert_url)

    result = runner.invoke(app, ["batch", str(urls), "--output", str(tmp_path)])

    assert result.exit_code == 0
    assert calls == ["https://juejin.cn/post/demo"]


def test_batch_command_writes_quality_report(monkeypatch, tmp_path: Path):
    urls = tmp_path / "urls.txt"
    urls.write_text(
        "https://juejin.cn/post/ok\nhttps://juejin.cn/post/fail\n",
        encoding="utf-8",
    )

    def fake_convert_url(url, output, **kwargs):
        if url.endswith("/fail"):
            raise RuntimeError("fetch failed")
        package = tmp_path / "pkg"
        package.mkdir(exist_ok=True)
        (package / "article.md").write_text("# OK\n\n正文", encoding="utf-8")
        (package / "metadata.json").write_text(
            json.dumps(
                {
                    "title": "OK",
                    "source_url": url,
                    "images": [],
                    "extraction": {"warnings": []},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return package

    monkeypatch.setattr("pagemd.cli.convert_url", fake_convert_url)

    result = runner.invoke(app, ["batch", str(urls), "--output", str(tmp_path)])

    assert result.exit_code == 0
    report = json.loads((tmp_path / "batch-report.json").read_text(encoding="utf-8"))
    assert report["summary"]["total"] == 2
    assert report["summary"]["ok"] == 1
    assert report["summary"]["failed"] == 1
    assert (tmp_path / "batch-report.md").exists()
    assert "Batch report" in result.stdout


def test_duplicate_url_with_image_download_does_not_overwrite_first_package(
    monkeypatch, tmp_path: Path
):
    html = """
    <html>
      <head><meta property="og:title" content="重复文章"></head>
      <body><article><p>正文</p><img src="https://example.com/a.png" /></article></body>
    </html>
    """
    download_calls = 0

    monkeypatch.setattr("pagemd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    def fake_download_images(article, package_dir, image_dir_name):
        nonlocal download_calls
        download_calls += 1
        return article.model_copy(
            update={"content_markdown": f"{article.content_markdown}\ndownloaded-{download_calls}"}
        )

    monkeypatch.setattr("pagemd.assets.download_images", fake_download_images)

    first_dir = convert_url("https://juejin.cn/post/demo", tmp_path)
    second_dir = convert_url("https://juejin.cn/post/demo", tmp_path)

    assert first_dir != second_dir
    assert "downloaded-1" in (first_dir / "article.md").read_text(encoding="utf-8")
    assert "downloaded-2" in (second_dir / "article.md").read_text(encoding="utf-8")
    assert "downloaded-2" not in (first_dir / "article.md").read_text(encoding="utf-8")


def test_convert_url_downloads_videos_in_media_step(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <body>
        <h1 id="activity-name">视频文章</h1>
        <div id="js_content"><p>[视频](https://mpvideo.qpic.cn/demo.mp4)</p></div>
      </body>
    </html>
    """
    monkeypatch.setattr("pagemd.cli.fetch_for_platform", lambda url, platform, config_path: html)
    monkeypatch.setattr("pagemd.assets.download_images", lambda article, package_dir, image_dir_name: article)

    def fake_download_videos(article, package_dir):
        return article.model_copy(update={"content_markdown": article.content_markdown + "\nvideo-downloaded"})

    monkeypatch.setattr("pagemd.assets.download_videos", fake_download_videos)

    package_dir = convert_url("https://mp.weixin.qq.com/s/demo", tmp_path)

    assert "video-downloaded" in (package_dir / "article.md").read_text(encoding="utf-8")
