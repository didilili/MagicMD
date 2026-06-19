from pathlib import Path

import json
import io
import sys

import pytest
from rich.console import Console
from typer.testing import CliRunner

from magicmd import __version__
from magicmd.cli import ConversionStageError, ProgressReporter, app, entrypoint
from magicmd.cli import convert_url, fetch_for_platform
from magicmd.sdk import ArticleConversionResult


runner = CliRunner()


def test_version_option():
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert f"MagicMD {__version__}" in result.stdout


def test_doctor_command():
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "MagicMD doctor" in result.stdout
    assert "Python:" in result.stdout
    assert "MagicMD:" in result.stdout
    assert "Config:" in result.stdout
    assert "Output:" in result.stdout
    assert "Camoufox:" in result.stdout
    assert "Platforms:" in result.stdout
    assert "wechat: camoufox, #js_content" in result.stdout
    assert "generic: http" in result.stdout


def test_doctor_command_honors_config_and_output_options(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    output_dir = tmp_path / "custom-output"
    config_path.write_text(
        """
        [output]
        directory = "configured-output"

        [platforms.juejin]
        browser = "http"
        wait_selector = ""
        """,
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "doctor",
            "--config",
            str(config_path),
            "--output",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert f"Config: {config_path} loaded" in result.stdout
    assert f"Output: {output_dir}" in result.stdout
    assert "juejin: http" in result.stdout


def test_doctor_command_json_output(tmp_path: Path):
    output_dir = tmp_path / "json-output"

    result = runner.invoke(app, ["doctor", "--json", "--output", str(output_dir)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["python"]["version"]
    assert payload["magicmd"]["version"] == __version__
    assert payload["config"]["loaded"] is False
    assert payload["output"]["directory"] == str(output_dir)
    assert payload["output"]["writable"] is True
    assert payload["camoufox"]["available"] is True
    assert {
        "name": "wechat",
        "fetcher": "camoufox",
        "wait_selector": "#js_content",
        "enabled": True,
    } in payload["platforms"]
    assert payload["warnings"] == []
    assert payload["errors"] == []
    assert "MagicMD doctor" not in result.stdout


def test_doctor_command_reports_invalid_config_without_traceback(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text("[output\n", encoding="utf-8")

    result = runner.invoke(app, ["doctor", "--config", str(config_path)])

    rendered = result.stdout + result.stderr
    assert result.exit_code != 0
    assert f"Config: {config_path} invalid" in rendered
    assert "MagicMD doctor found issues" in rendered
    assert "Traceback" not in rendered


def test_doctor_command_json_reports_invalid_config_without_traceback(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text("[output\n", encoding="utf-8")

    result = runner.invoke(app, ["doctor", "--json", "--config", str(config_path)])

    rendered = result.stdout + result.stderr
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["config"]["path"] == str(config_path)
    assert payload["config"]["loaded"] is False
    assert any(str(config_path) in error for error in payload["errors"])
    assert "MagicMD doctor found issues" in rendered
    assert "Traceback" not in rendered


def test_entrypoint_doctor_json_invalid_config_exits_nonzero(monkeypatch, capsys, tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text("[output\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["magicmd", "doctor", "--json", "--config", str(config_path)])

    with pytest.raises(SystemExit) as exc_info:
        entrypoint()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exc_info.value.code == 1
    assert payload["ok"] is False
    assert payload["config"]["path"] == str(config_path)
    assert "MagicMD doctor found issues" in captured.err
    assert "Traceback" not in captured.out + captured.err


def test_convert_command_writes_package(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="掘金文章标题"></head>
      <body><article><p>掘金正文</p></article></body>
    </html>
    """

    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

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
    assert "已生成内容包" in result.stdout
    assert list(tmp_path.glob("*/article.md"))
    assert list(tmp_path.glob("*/metadata.json"))


def test_convert_command_prints_absolute_package_path_for_relative_output(
    monkeypatch, tmp_path: Path
):
    html = """
    <html>
      <head><meta property="og:title" content="相对输出文章"></head>
      <body><article><p>正文</p></article></body>
    </html>
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--output",
            "relative-output",
            "--no-images",
        ],
    )

    package_dir = next((tmp_path / "relative-output").glob("*"))
    assert result.exit_code == 0
    assert f"已生成内容包：{package_dir.resolve()}" in result.stdout


def test_convert_command_writes_docx_when_format_is_docx(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="Word 文章"></head>
      <body><article><p>正文</p></article></body>
    </html>
    """

    def fake_write_docx(markdown_path, docx_path, config):
        docx_path.write_bytes(b"docx")

    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)
    monkeypatch.setattr("magicmd.output.write_docx_from_markdown", fake_write_docx)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--output",
            str(tmp_path),
            "--no-images",
            "--format",
            "docx",
        ],
    )

    assert result.exit_code == 0
    package_dir = next(tmp_path.glob("*"))
    assert (package_dir / "article.md").exists()
    assert (package_dir / "article.docx").read_bytes() == b"docx"


def test_convert_command_writes_docx_from_config(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="配置 Word 文章"></head>
      <body><article><p>正文</p></article></body>
    </html>
    """
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [docx]
        enabled = true
        """,
        encoding="utf-8",
    )

    def fake_write_docx(markdown_path, docx_path, config):
        docx_path.write_bytes(b"docx")

    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)
    monkeypatch.setattr("magicmd.output.write_docx_from_markdown", fake_write_docx)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--output",
            str(tmp_path),
            "--config",
            str(config_path),
            "--no-images",
        ],
    )

    assert result.exit_code == 0
    package_dir = next(path for path in tmp_path.iterdir() if path.is_dir())
    assert (package_dir / "article.md").exists()
    assert (package_dir / "article.docx").read_bytes() == b"docx"


def test_entrypoint_reports_cli_errors_without_traceback(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["magicmd", "convert", "--bad-option"])

    with pytest.raises(SystemExit) as exc_info:
        entrypoint()

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    assert exc_info.value.code != 0
    assert "No such option" in rendered
    assert "Traceback" not in rendered


def test_convert_command_uses_configured_output_directory(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="配置输出文章"></head>
      <body><article><p>正文</p></article></body>
    </html>
    """
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [output]
        directory = "configured-output"
        """,
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--config",
            str(config_path),
            "--no-images",
        ],
    )

    assert result.exit_code == 0
    assert list((tmp_path / "configured-output").glob("*/article.md"))


def test_convert_command_uses_configured_output_names(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="配置命名文章"></head>
      <body><article><p>正文</p></article></body>
    </html>
    """
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [output]
        directory = "configured-output"

        [output.naming]
        package = "{date}/{slug}"
        markdown = "index.md"
        metadata = "meta.json"
        """,
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--config",
            str(config_path),
            "--no-images",
        ],
    )

    package_dir = tmp_path / "configured-output" / "undated" / "配置命名文章"
    assert result.exit_code == 0
    assert (package_dir / "index.md").exists()
    assert (package_dir / "meta.json").exists()
    assert not (package_dir / "article.md").exists()
    assert not (package_dir / "metadata.json").exists()


def test_convert_command_uses_configured_report_name(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="配置报告文章"></head>
      <body><article><p>正文</p></article></body>
    </html>
    """
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [output]
        directory = "configured-output"

        [output.naming]
        report = "report.json"
        """,
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--config",
            str(config_path),
            "--no-images",
        ],
    )

    package_dir = next((tmp_path / "configured-output").glob("*/"))
    assert result.exit_code == 0
    assert (package_dir / "report.json").exists()
    assert not (package_dir / "extraction-report.json").exists()


def test_convert_command_honors_markdown_config(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="Markdown 配置文章"></head>
      <body><article><h2>小标题</h2><p>正文</p></article></body>
    </html>
    """
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [markdown]
        front_matter = "none"
        include_source_block = false
        heading_offset = 1
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--output",
            str(tmp_path),
            "--config",
            str(config_path),
            "--no-images",
        ],
    )

    assert result.exit_code == 0
    article_md = next(tmp_path.glob("*/article.md")).read_text(encoding="utf-8")
    assert not article_md.startswith("---")
    assert "> Original:" not in article_md
    assert "## Markdown 配置文章" in article_md
    assert "### 小标题" in article_md


def test_convert_command_saves_debug_html_from_config(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="调试文章"></head>
      <body><article><p>正文</p></article></body>
    </html>
    """
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [output]
        save_debug_html = "always"
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--output",
            str(tmp_path),
            "--config",
            str(config_path),
            "--no-images",
        ],
    )

    assert result.exit_code == 0
    assert next(tmp_path.glob("*/debug.html")).read_text(encoding="utf-8") == html


def test_convert_command_reports_content_not_found_as_failure(monkeypatch, tmp_path: Path):
    html = "<html><body>Please wait...</body></html>"

    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

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

    assert result.exit_code != 0
    assert result.exception is not None
    assert "Extraction failed: juejin_content_not_found" in str(result.exception)
    package_dir = next(tmp_path.glob("*"))
    assert (package_dir / "debug.html").exists()
    metadata = json.loads((package_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["extraction"]["status"] == "failed"


def test_convert_command_rejects_disabled_platform(monkeypatch, tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [platforms.juejin]
        enabled = false
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "magicmd.cli.fetch_for_platform",
        lambda url, platform, config_path: pytest.fail("disabled platform should not fetch"),
    )

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code != 0
    assert result.exception is not None
    assert "Platform disabled: juejin" in str(result.exception)


def test_fetch_for_platform_passes_browser_fetch_options(monkeypatch, tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [fetch]
        browser_timeout_seconds = 7
        browser_attempts = 4
        """,
        encoding="utf-8",
    )

    def fake_fetch_browser(url, wait_selector="", timeout_ms=0, attempts=0):
        assert url == "https://juejin.cn/post/demo"
        assert wait_selector == "article"
        assert timeout_ms == 7000
        assert attempts == 4
        return "<html>ok</html>"

    monkeypatch.setattr("magicmd.cli.fetch_browser", fake_fetch_browser)

    assert (
        fetch_for_platform("https://juejin.cn/post/demo", "juejin", config_path)
        == "<html>ok</html>"
    )


def test_convert_url_marks_fetch_stage_failures(monkeypatch, tmp_path: Path):
    def fail_fetch(url, platform, config_path):
        raise RuntimeError("network failed")

    monkeypatch.setattr("magicmd.cli.fetch_for_platform", fail_fetch)

    with pytest.raises(ConversionStageError) as exc_info:
        convert_url("https://juejin.cn/post/demo", tmp_path, download_images_enabled=False)

    assert exc_info.value.stage == "fetch"
    assert "network failed" in str(exc_info.value)


def test_convert_command_prints_progress_steps(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="进度文章"></head>
      <body><article><p>正文</p></article></body>
    </html>
    """
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

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
    assert "✓ [1/6] 识别平台" in result.stdout
    assert "✓ [2/6] 抓取文章" in result.stdout
    assert "✓ [3/6] 解析文章" in result.stdout
    assert "✓ [4/6] 写入 Markdown 内容包" in result.stdout
    assert "✓ [5/6] 跳过图片下载" in result.stdout
    assert "✓ [6/6] 保存转换报告" in result.stdout


def test_convert_command_can_print_english_progress_from_ui_config(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <head><meta property="og:title" content="Progress Article"></head>
      <body><article><p>Body</p></article></body>
    </html>
    """
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [ui]
        language = "en-US"
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    result = runner.invoke(
        app,
        [
            "convert",
            "https://juejin.cn/post/demo",
            "--output",
            str(tmp_path),
            "--config",
            str(config_path),
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
    assert "Created output package" in result.stdout


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
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)
    monkeypatch.setattr(sys, "argv", ["magicmd", "https://juejin.cn/post/demo"])

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
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "magicmd",
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

    monkeypatch.setattr("magicmd.cli.convert_url", fake_convert_url)

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

    monkeypatch.setattr("magicmd.cli.convert_url", fake_convert_url)

    result = runner.invoke(app, ["batch", str(urls), "--output", str(tmp_path)])

    assert result.exit_code == 0
    report = json.loads((tmp_path / "batch-report.json").read_text(encoding="utf-8"))
    assert report["summary"]["total"] == 2
    assert report["summary"]["ok"] == 1
    assert report["summary"]["failed"] == 1
    assert (tmp_path / "batch-report.md").exists()
    assert "批量报告" in result.stdout


def test_batch_command_prints_absolute_package_path_for_relative_package(
    monkeypatch, tmp_path: Path
):
    urls = tmp_path / "urls.txt"
    urls.write_text("https://juejin.cn/post/ok\n", encoding="utf-8")
    package = Path("relative-output/pkg")

    def fake_convert_url(url, output, **kwargs):
        package.mkdir(parents=True, exist_ok=True)
        (package / "article.md").write_text("# OK\n\n正文", encoding="utf-8")
        (package / "metadata.json").write_text(
            json.dumps(
                {
                    "title": "OK",
                    "source_url": url,
                    "platform": "juejin",
                    "images": [],
                    "extraction": {"warnings": []},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return package

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("magicmd.cli.convert_url", fake_convert_url)

    result = runner.invoke(app, ["batch", str(urls), "--output", "relative-output"])

    assert result.exit_code == 0
    assert f"完成 https://juejin.cn/post/ok -> {(tmp_path / package).resolve()}" in result.stdout


def test_batch_command_passes_overwrite_to_convert_url(monkeypatch, tmp_path: Path):
    urls = tmp_path / "urls.txt"
    urls.write_text("https://juejin.cn/post/demo\n", encoding="utf-8")
    seen_kwargs = {}

    def fake_convert_url(url, output, **kwargs):
        seen_kwargs.update(kwargs)
        package = tmp_path / "pkg"
        package.mkdir(exist_ok=True)
        (package / "article.md").write_text("# OK\n", encoding="utf-8")
        (package / "metadata.json").write_text(
            json.dumps(
                {
                    "title": "OK",
                    "source_url": url,
                    "platform": "juejin",
                    "images": [],
                    "extraction": {"warnings": []},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return package

    monkeypatch.setattr("magicmd.cli.convert_url", fake_convert_url)

    result = runner.invoke(app, ["batch", str(urls), "--output", str(tmp_path), "--overwrite"])

    assert result.exit_code == 0
    assert seen_kwargs["overwrite"] is True


def test_batch_command_skip_existing_uses_existing_package(monkeypatch, tmp_path: Path):
    url = "https://juejin.cn/post/existing"
    urls = tmp_path / "urls.txt"
    urls.write_text(url + "\n", encoding="utf-8")
    package = tmp_path / "existing-package"
    package.mkdir()
    (package / "article.md").write_text("# Existing\n\n正文", encoding="utf-8")
    (package / "metadata.json").write_text(
        json.dumps(
            {
                "title": "Existing",
                "source_url": url,
                "canonical_url": url,
                "platform": "juejin",
                "images": [],
                "extraction": {"warnings": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fail_convert_url(url, output, **kwargs):
        raise AssertionError("existing package should be skipped")

    monkeypatch.setattr("magicmd.cli.convert_url", fail_convert_url)

    result = runner.invoke(app, ["batch", str(urls), "--output", str(tmp_path), "--skip-existing"])

    assert result.exit_code == 0
    assert f"跳过 {url} -> {package}" in result.stdout
    report = json.loads((tmp_path / "batch-report.json").read_text(encoding="utf-8"))
    assert report["summary"]["skipped"] == 1
    item = report["items"][0]
    assert item["status"] == "skipped"
    assert item["stage"] == "skip"
    assert item["package_dir"] == str(package)


def test_batch_command_skip_existing_uses_configured_output_names(monkeypatch, tmp_path: Path):
    url = "https://juejin.cn/post/existing"
    urls = tmp_path / "urls.txt"
    urls.write_text(url + "\n", encoding="utf-8")
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [output.naming]
        markdown = "index.md"
        metadata = "meta.json"
        """,
        encoding="utf-8",
    )
    package = tmp_path / "existing-package"
    package.mkdir()
    (package / "index.md").write_text("# Existing\n\n正文", encoding="utf-8")
    (package / "meta.json").write_text(
        json.dumps(
            {
                "title": "Existing",
                "source_url": url,
                "canonical_url": url,
                "platform": "juejin",
                "images": [],
                "extraction": {"warnings": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fail_convert_url(url, output, **kwargs):
        raise AssertionError("existing package should be skipped")

    monkeypatch.setattr("magicmd.cli.convert_url", fail_convert_url)

    result = runner.invoke(
        app,
        [
            "batch",
            str(urls),
            "--output",
            str(tmp_path),
            "--config",
            str(config_path),
            "--skip-existing",
        ],
    )

    assert result.exit_code == 0
    assert f"跳过 {url} -> {package}" in result.stdout
    report = json.loads((tmp_path / "batch-report.json").read_text(encoding="utf-8"))
    assert report["summary"]["skipped"] == 1
    assert report["items"][0]["package_dir"] == str(package)


def test_batch_command_adds_diagnostic_fields_to_report(monkeypatch, tmp_path: Path):
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
                    "platform": "juejin",
                    "images": [],
                    "extraction": {"warnings": []},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return package

    monkeypatch.setattr("magicmd.cli.convert_url", fake_convert_url)

    result = runner.invoke(app, ["batch", str(urls), "--output", str(tmp_path)])

    assert result.exit_code == 0
    report = json.loads((tmp_path / "batch-report.json").read_text(encoding="utf-8"))
    ok_item, fail_item = report["items"]
    assert ok_item["platform"] == "juejin"
    assert ok_item["fetcher"] == "camoufox"
    assert ok_item["stage"] == "complete"
    assert ok_item["elapsed_ms"] >= 0
    assert ok_item["max_attempts"] == 2
    assert ok_item["retry_enabled"] is True
    assert fail_item["platform"] == "juejin"
    assert fail_item["fetcher"] == "camoufox"
    assert fail_item["stage"] == "convert"
    assert fail_item["elapsed_ms"] >= 0


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

    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    def fake_download_images(
        article,
        package_dir,
        image_dir_name,
        filename_pattern="img_{index:03d}.{ext}",
        markdown_path_pattern="{directory}/{filename}",
    ):
        nonlocal download_calls
        download_calls += 1
        return article.model_copy(
            update={"content_markdown": f"{article.content_markdown}\ndownloaded-{download_calls}"}
        )

    monkeypatch.setattr("magicmd.assets.download_images", fake_download_images)

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
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)
    monkeypatch.setattr(
        "magicmd.assets.download_images",
        lambda article, package_dir, image_dir_name, filename_pattern="img_{index:03d}.{ext}", markdown_path_pattern="{directory}/{filename}": (
            article
        ),
    )

    def fake_download_videos(
        article,
        package_dir,
        video_dir_name="videos",
        filename_pattern="video_{index:03d}.{ext}",
        markdown_path_pattern="{directory}/{filename}",
    ):
        return article.model_copy(
            update={"content_markdown": article.content_markdown + "\nvideo-downloaded"}
        )

    monkeypatch.setattr("magicmd.assets.download_videos", fake_download_videos)

    package_dir = convert_url("https://mp.weixin.qq.com/s/demo", tmp_path)

    assert "video-downloaded" in (package_dir / "article.md").read_text(encoding="utf-8")


def test_convert_url_passes_configured_media_path_templates(monkeypatch, tmp_path: Path):
    html = """
    <html>
      <body>
        <h1 id="activity-name">媒体配置文章</h1>
        <div id="js_content">
          <p>正文</p>
          <img src="https://example.com/a.png" />
          <p>[视频](https://mpvideo.qpic.cn/demo.mp4)</p>
        </div>
      </body>
    </html>
    """
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [images]
        directory = "assets/images"
        filename_pattern = "cover_{index:02d}.{ext}"
        markdown_path = "/static/{directory}/{filename}"

        [videos]
        directory = "assets/videos"
        filename_pattern = "clip_{index:02d}.{ext}"
        markdown_path = "/static/{directory}/{filename}"
        """,
        encoding="utf-8",
    )
    seen = {}
    monkeypatch.setattr("magicmd.cli.fetch_for_platform", lambda url, platform, config_path: html)

    def fake_download_images(
        article,
        package_dir,
        image_dir_name,
        filename_pattern="img_{index:03d}.{ext}",
        markdown_path_pattern="{directory}/{filename}",
    ):
        seen["images"] = (image_dir_name, filename_pattern, markdown_path_pattern)
        return article

    def fake_download_videos(
        article,
        package_dir,
        video_dir_name="videos",
        filename_pattern="video_{index:03d}.{ext}",
        markdown_path_pattern="{directory}/{filename}",
    ):
        seen["videos"] = (video_dir_name, filename_pattern, markdown_path_pattern)
        return article

    monkeypatch.setattr("magicmd.assets.download_images", fake_download_images)
    monkeypatch.setattr("magicmd.assets.download_videos", fake_download_videos)

    convert_url("https://mp.weixin.qq.com/s/demo", tmp_path, config_path=config_path)

    assert seen["images"] == (
        "assets/images",
        "cover_{index:02d}.{ext}",
        "/static/{directory}/{filename}",
    )
    assert seen["videos"] == (
        "assets/videos",
        "clip_{index:02d}.{ext}",
        "/static/{directory}/{filename}",
    )


def test_publish_github_dry_run_prints_plan(monkeypatch, tmp_path: Path):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "article.md").write_text("# Dry Run\n", encoding="utf-8")

    def fake_convert_article(**kwargs):
        return ArticleConversionResult(
            title="Dry Run",
            platform="wechat",
            source_url=kwargs["url"],
            markdown="# Dry Run\n",
            content_hash="abc123456",
            package_dir=str(package_dir),
        )

    monkeypatch.setattr("magicmd.cli.convert_article", fake_convert_article)

    result = runner.invoke(
        app,
        [
            "publish",
            "github",
            "https://mp.weixin.qq.com/s/example",
            "--repo",
            "owner/repo",
            "--target-dir",
            "content/posts",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Publish plan" in result.stdout
    assert "owner/repo" in result.stdout
    assert "content/posts/article.md" in result.stdout
    assert "Dry run only" in result.stdout


def test_publish_github_requires_repo_or_config(monkeypatch, tmp_path: Path):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "article.md").write_text("# Missing Repo\n", encoding="utf-8")

    def fake_convert_article(**kwargs):
        return ArticleConversionResult(
            title="Missing Repo",
            platform="wechat",
            source_url=kwargs["url"],
            markdown="# Missing Repo\n",
            content_hash="abc123456",
            package_dir=str(package_dir),
        )

    monkeypatch.setattr("magicmd.cli.convert_article", fake_convert_article)

    result = runner.invoke(
        app,
        [
            "publish",
            "github",
            "https://mp.weixin.qq.com/s/example",
            "--target-dir",
            "content/posts",
            "--dry-run",
        ],
    )

    assert result.exit_code != 0
    assert "--repo is required" in (result.stdout + result.stderr)
