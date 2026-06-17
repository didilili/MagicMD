from pathlib import Path
import subprocess

import pytest

from magicmd.config import DocxConfig
from magicmd.exceptions import ConversionError
from magicmd.renderers.docx import write_docx_from_markdown


def test_write_docx_from_markdown_invokes_pandoc_with_reference_doc(monkeypatch, tmp_path: Path):
    markdown_path = tmp_path / "article.md"
    docx_path = tmp_path / "article.docx"
    reference_doc = tmp_path / "reference.docx"
    markdown_path.write_text("# 标题\n\n正文", encoding="utf-8")
    reference_doc.write_bytes(b"reference")
    calls = []

    def fake_run(cmd, check, capture_output, text, cwd, input=None):
        calls.append(
            {
                "cmd": cmd,
                "check": check,
                "capture_output": capture_output,
                "text": text,
                "cwd": cwd,
                "input": input,
            }
        )
        docx_path.write_bytes(b"docx")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("magicmd.renderers.docx.subprocess.run", fake_run)

    result = write_docx_from_markdown(
        markdown_path,
        docx_path,
        DocxConfig(pandoc_path="pandoc-custom", reference_doc=str(reference_doc)),
    )

    assert result == docx_path
    assert calls == [
        {
            "cmd": [
                "pandoc-custom",
                "-",
                "-f",
                "markdown-implicit_figures",
                "-t",
                "docx",
                "-o",
                "article.docx",
                "--reference-doc",
                str(reference_doc),
            ],
            "check": True,
            "capture_output": True,
            "text": True,
            "cwd": tmp_path,
            "input": "# 标题\n\n正文\n",
        }
    ]
    assert docx_path.read_bytes() == b"docx"


def test_write_docx_from_markdown_uses_article_dir_relative_paths(monkeypatch, tmp_path: Path):
    article_dir = tmp_path / "output" / "article-package"
    article_dir.mkdir(parents=True)
    markdown_path = Path("output/article-package/article.md")
    docx_path = Path("output/article-package/article.docx")
    (tmp_path / markdown_path).write_text("# 标题\n\n正文", encoding="utf-8")
    calls = []

    def fake_run(cmd, check, capture_output, text, cwd, input=None):
        calls.append(
            {
                "cmd": cmd,
                "check": check,
                "capture_output": capture_output,
                "text": text,
                "cwd": cwd,
                "input": input,
            }
        )
        assert Path(cwd) == Path("output/article-package")
        assert cmd[1] == "-"
        assert cmd[7] == "article.docx"
        assert input == "# 标题\n\n正文\n"
        (tmp_path / docx_path).write_bytes(b"docx")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("magicmd.renderers.docx.subprocess.run", fake_run)

    result = write_docx_from_markdown(markdown_path, docx_path, DocxConfig())

    assert result == docx_path
    assert calls
    assert (tmp_path / docx_path).read_bytes() == b"docx"


def test_write_docx_from_markdown_uses_docx_ready_markdown(monkeypatch, tmp_path: Path):
    markdown_path = tmp_path / "article.md"
    docx_path = tmp_path / "article.docx"
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    (image_dir / "img_001.jpg").write_bytes(b"jpg")
    (image_dir / "img_002.gif").write_bytes(
        b"GIF89a" + (640).to_bytes(2, "little") + (100).to_bytes(2, "little")
    )
    markdown_path.write_text(
        """---
title: "重复标题"
author: "InfoQ"
platform: "wechat"
source_url: "https://mp.weixin.qq.com/s/demo"
---

# 重复标题

> Source: wechat
> Author: InfoQ
> Original: https://mp.weixin.qq.com/s/demo

---

![Image](images/img_001.jpg)

![Image](images/img_002.gif)

正文
""",
        encoding="utf-8",
    )
    calls = []

    def fake_run(cmd, check, capture_output, text, cwd, input=None):
        calls.append({"cmd": cmd, "input": input, "cwd": cwd})
        docx_path.write_bytes(b"docx")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("magicmd.renderers.docx.subprocess.run", fake_run)

    write_docx_from_markdown(markdown_path, docx_path, DocxConfig())

    prepared = calls[0]["input"]
    assert calls[0]["cmd"][1] == "-"
    assert calls[0]["cmd"][3] == "markdown-implicit_figures"
    assert 'title: "重复标题"' in prepared
    assert "# 重复标题" not in prepared
    assert "> Source:" not in prepared
    assert "> Author:" not in prepared
    assert "> Original:" not in prepared
    assert "![Image]" not in prepared
    assert "![](images/img_001.jpg)" in prepared
    assert "img_002.gif" not in prepared
    assert "正文" in prepared
    assert "> Source: wechat" in markdown_path.read_text(encoding="utf-8")


def test_write_docx_from_markdown_raises_clear_error_when_pandoc_is_missing(
    monkeypatch, tmp_path: Path
):
    markdown_path = tmp_path / "article.md"
    docx_path = tmp_path / "article.docx"
    markdown_path.write_text("# 标题\n\n正文", encoding="utf-8")

    def fail_run(*args, **kwargs):
        raise FileNotFoundError("pandoc")

    monkeypatch.setattr("magicmd.renderers.docx.subprocess.run", fail_run)

    with pytest.raises(ConversionError, match="Pandoc not found"):
        write_docx_from_markdown(markdown_path, docx_path, DocxConfig())


def test_write_docx_from_markdown_reports_pandoc_stdout_when_stderr_is_empty(
    monkeypatch, tmp_path: Path
):
    markdown_path = tmp_path / "article.md"
    docx_path = tmp_path / "article.docx"
    markdown_path.write_text("# 标题\n\n正文", encoding="utf-8")

    def fail_run(cmd, *args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=cmd,
            output="article.md: withBinaryFile: does not exist",
            stderr="",
        )

    monkeypatch.setattr("magicmd.renderers.docx.subprocess.run", fail_run)

    with pytest.raises(ConversionError, match="withBinaryFile: does not exist"):
        write_docx_from_markdown(markdown_path, docx_path, DocxConfig())
