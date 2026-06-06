from pathlib import Path

import sys

from typer.testing import CliRunner

from pagemd.cli import app, entrypoint


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
    assert "[1/5] Detecting platform" in result.stdout
    assert "[2/5] Fetching article" in result.stdout
    assert "[3/5] Parsing article" in result.stdout
    assert "[4/5] Writing Markdown package" in result.stdout
    assert "[5/5] Saving extraction report" in result.stdout


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
