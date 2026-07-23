import json
from pathlib import Path

import pytest

import magicmd.quality as quality_module
from magicmd.quality import build_package_quality, scan_markdown_quality, write_batch_report


def test_scan_markdown_quality_flags_known_wechat_regressions():
    markdown = """
正文

````
````

### Image

推**荐****阅****读**

第**九十一****号**

***3.*****[Linux 学习指南](https://example.com)

**① headroom: **压缩 LLM 输入

**② addyosmani/agent-skills:**Google 工程师整理的 Skills 合集。
"""

    issues = scan_markdown_quality(markdown)

    assert "empty_code_fence" in issues
    assert "image_used_as_heading" in issues
    assert "fragmented_recommendation_text" in issues
    assert "fragmented_bold_text" in issues
    assert "broken_numbered_link_emphasis" in issues
    assert "broken_strong_boundary" in issues


def test_scan_markdown_quality_does_not_flag_adjacent_non_empty_code_fences():
    markdown = """
```python
print("one")
```

```
print("two")
```
"""

    issues = scan_markdown_quality(markdown)

    assert "empty_code_fence" not in issues


def test_scan_markdown_quality_ignores_markdown_inside_code_fences():
    markdown = """
正文

```
content='**天气状况**：阴，多云\\n**温度**：14.94°C'
```
"""

    issues = scan_markdown_quality(markdown)

    assert "fragmented_bold_text" not in issues


def test_scan_markdown_quality_allows_adjacent_inline_bold_terms():
    markdown = """
可以省去类型检查，通过添加 **!** **断言**，**不推荐**。
例如 **clientX**、**clientY** 都是鼠标事件属性。
**AI**时代需要稳定输出。
**① headroom:** 压缩 LLM 输入。
"""

    issues = scan_markdown_quality(markdown)

    assert "fragmented_bold_text" not in issues
    assert "broken_strong_boundary" not in issues


def test_scan_markdown_quality_flags_punctuation_boundaries_and_orphan_markers():
    markdown = """
Text Extractor **内置 OCR 一键截图取文字，**ColorPicker 取色。

Chatwoot 是一个**客服系统的开源项目，**目前累计 3.2 万 Star。

**第一步，偷偷查你是谁。**它会读取系统时区。

**

![Image](images/example.png)

**

****嵌套加粗****

提示词：*正文中出现了未闭合的**加粗标记*

打开 http://localhost:3000，顶部工具栏会显示内容。
"""

    issues = scan_markdown_quality(markdown)

    assert "broken_strong_boundary" in issues
    assert "orphan_emphasis_marker" in issues
    assert "redundant_emphasis_marker" in issues
    assert "unbalanced_emphasis_marker" in issues
    assert "broken_bare_url_boundary" in issues


def test_scan_markdown_quality_ignores_valid_inline_and_code_emphasis():
    markdown = """
它是一个真正的**代码记忆**机制。
**AI**时代需要稳定输出。
它给自己的定位是 **100 倍速**替代品。

`content = "**标签，**正文"`

**发送指令：*使用浏览器获取三篇文章***

```python
content = "**标签，**正文"
```
"""

    issues = scan_markdown_quality(markdown)

    assert "broken_strong_boundary" not in issues
    assert "orphan_emphasis_marker" not in issues
    assert "unbalanced_emphasis_marker" not in issues
    assert "broken_bare_url_boundary" not in issues


@pytest.mark.parametrize(
    ("markdown", "expected_issue"),
    [
        ("![Image]()", "empty_image_target"),
        ("[视频](videos/video_001.mp4)", "relative_local_video"),
        (r"\*\*重点\*\*", "escaped_strong_marker"),
        ("```bash\nnpm\u00a0install demo\n```", "code_contains_nbsp"),
        ("```javascript\nnpm install demo\n```", "suspicious_code_language"),
        (
            "```javascript\n开源地址：https://github.com/a/b\n```",
            "address_only_code_fence",
        ),
        ("## 二级\n\n#### 四级", "heading_level_jump"),
        (
            "![图](https://mmbiz.qpic.cn/demo.png)",
            "external_media_not_rewritten",
        ),
    ],
)
def test_scan_markdown_quality_flags_new_quality_codes(markdown, expected_issue):
    issues = scan_markdown_quality(markdown)

    assert expected_issue in issues


@pytest.mark.parametrize(
    ("markdown", "unexpected_issue"),
    [
        ("![Image](images/image_001.png)", "empty_image_target"),
        ("![Image]((image_001.png))", "empty_image_target"),
        ("[视频](https://example.com/video.mp4)", "relative_local_video"),
        (r"正文 \*\*未闭合", "escaped_strong_marker"),
        (r"`\*\*重点\*\*`", "escaped_strong_marker"),
        ("```\n![Image]()\n\\*\\*重点\\*\\*\n```", "empty_image_target"),
        ("```\n![Image]()\n\\*\\*重点\\*\\*\n```", "escaped_strong_marker"),
        ("正文含有不间断空格：npm\u00a0install", "code_contains_nbsp"),
        ("```bash\nnpm install demo\n```", "suspicious_code_language"),
        ("```javascript\nexport default config\n```", "suspicious_code_language"),
        ("```go\ngo func() {}\n```", "suspicious_code_language"),
        ("开源地址：https://github.com/a/b", "address_only_code_fence"),
        ("## 二级\n\n### 三级\n\n## 二级", "heading_level_jump"),
        (
            "![图](https://example.com/demo.png)",
            "external_media_not_rewritten",
        ),
        (
            "[微信文档](https://mmbiz.qpic.cn/demo.png)",
            "external_media_not_rewritten",
        ),
    ],
)
def test_scan_markdown_quality_avoids_new_code_false_positives(markdown, unexpected_issue):
    issues = scan_markdown_quality(markdown)

    assert unexpected_issue not in issues


def test_scan_markdown_quality_treats_unclosed_fence_as_code():
    markdown = "```javascript\n![Image]()\n\\*\\*重点\\*\\*\nnpm\u00a0install demo\n"

    issues = scan_markdown_quality(markdown)

    assert "empty_image_target" not in issues
    assert "escaped_strong_marker" not in issues
    assert "code_contains_nbsp" in issues


@pytest.mark.parametrize(
    "markdown",
    [
        "**跨行\n加粗**",
        "**粗体 *斜体\n跨行* 文本**",
        "[链接](https://example.com/**path**)",
        "![图](images/**asset**.png)",
    ],
)
def test_scan_markdown_quality_allows_balanced_multiline_and_destination_emphasis(
    markdown,
):
    issues = scan_markdown_quality(markdown)

    assert "unbalanced_emphasis_marker" not in issues


@pytest.mark.parametrize(
    "markdown",
    [
        "**未闭合\n正文",
        "**未闭合\n\n正文**",
        "[**未闭合](https://example.com/ok)",
    ],
)
def test_scan_markdown_quality_still_flags_unbalanced_prose_emphasis(markdown):
    issues = scan_markdown_quality(markdown)

    assert "unbalanced_emphasis_marker" in issues


def test_scan_markdown_quality_separates_removed_inline_code_from_url_neighbors():
    markdown = "打开 http://localhost:3000`/demo`，顶部工具栏会显示内容。"

    issues = scan_markdown_quality(markdown)

    assert "broken_bare_url_boundary" not in issues


@pytest.mark.parametrize(
    ("markdown", "expected_issue"),
    [
        ("> > ```\n> > \n> > ```", "empty_code_fence"),
        (
            "> > ```javascript\n> > 开源地址：https://github.com/a/b\n> > ```",
            "address_only_code_fence",
        ),
        (
            "> > - ```javascript\n> >   npm install demo\n> >   ```",
            "suspicious_code_language",
        ),
        (
            "- ```javascript\n  npm install demo\n  ```",
            "suspicious_code_language",
        ),
    ],
)
def test_scan_markdown_quality_normalizes_fence_container_prefixes(markdown, expected_issue):
    issues = scan_markdown_quality(markdown)

    assert expected_issue in issues


@pytest.mark.parametrize(
    ("markdown", "expected_issue"),
    [
        ('![图](<> "占位")', "empty_image_target"),
        ('[视频](/Videos/DEMO.MP4?download=1 "演示")', "relative_local_video"),
        ("[视频](../videos/demo.webm)", "relative_local_video"),
        ("[视频](./VIDEOS/demo.mp4)", "relative_local_video"),
        (
            '![图](//mmbiz.qpic.cn/demo.png "结构图")',
            "external_media_not_rewritten",
        ),
        (
            "[任意标签](//mpvideo.qpic.cn/demo.mp4?auth=1)",
            "external_media_not_rewritten",
        ),
        (
            "[演示](https://mpvideo.qpic.cn/demo.mp4)",
            "external_media_not_rewritten",
        ),
    ],
)
def test_scan_markdown_quality_parses_media_destinations(markdown, expected_issue):
    issues = scan_markdown_quality(markdown)

    assert expected_issue in issues


@pytest.mark.parametrize(
    ("markdown", "unexpected_issue"),
    [
        ("[文档](/videos/readme)", "relative_local_video"),
        ("[文档](../videos/demo.txt)", "relative_local_video"),
        (
            "[普通链接](//mmbiz.qpic.cn/document)",
            "external_media_not_rewritten",
        ),
        (
            "![普通图片](//example.com/demo.png)",
            "external_media_not_rewritten",
        ),
        ("![未闭合](<", "empty_image_target"),
    ],
)
def test_scan_markdown_quality_ignores_valid_or_malformed_non_media_destinations(
    markdown, unexpected_issue
):
    issues = scan_markdown_quality(markdown)

    assert unexpected_issue not in issues


@pytest.mark.parametrize(
    "markdown",
    [
        "```shell-session\nnpm install demo\n```",
        "```sh-session\nnpm install demo\n```",
        "```makefile\ninstall:\n\tnpm install\n```",
        "```yaml\nscript: |\n  npm install\n```",
    ],
)
def test_scan_markdown_quality_allows_shell_sessions_and_command_container_languages(
    markdown,
):
    issues = scan_markdown_quality(markdown)

    assert "suspicious_code_language" not in issues


@pytest.mark.parametrize(
    ("markdown", "expected_issue"),
    [
        (
            "[![图](https://mmbiz.qpic.cn/demo.png)](/article)",
            "external_media_not_rewritten",
        ),
        ("[![图]()](/article)", "empty_image_target"),
    ],
)
def test_scan_markdown_quality_discovers_nested_destinations_once(markdown, expected_issue):
    issues = scan_markdown_quality(markdown)

    assert issues.count(expected_issue) == 1


def test_scan_markdown_quality_does_not_infer_title_only_image_as_empty():
    issues = scan_markdown_quality('![图]( "说明")')

    assert "empty_image_target" not in issues


@pytest.mark.parametrize(
    "markdown",
    [
        "[ref]: https://example.com/**/b",
        ("[ref]: https://example.com/first\n[REF]: https://example.com/**/duplicate"),
        "<https://example.com/**/b>",
        "<ftp://example.com/**/b>",
        "<git+ssh://example.com/**/repo>",
        "<user**tag@example.com>",
    ],
)
def test_scan_markdown_quality_masks_reference_definitions_and_autolinks(markdown):
    issues = scan_markdown_quality(markdown)

    assert "unbalanced_emphasis_marker" not in issues


def test_scan_markdown_quality_does_not_mask_ordinary_angle_text():
    issues = scan_markdown_quality("<普通 **未闭合>")

    assert "unbalanced_emphasis_marker" in issues


@pytest.mark.parametrize(
    ("markdown", "expected_issue"),
    [
        ('![图][img]\n\n[img]: <> "占位"', "empty_image_target"),
        (
            "![图][Diagram One]\n\n[ diagram   one ]: //mmbiz.qpic.cn/demo.png",
            "external_media_not_rewritten",
        ),
        (
            "[观看][vid]\n\n[VID]: ../VIDEOS/demo.MP4?download=1",
            "relative_local_video",
        ),
        (
            "[任意标签][vid]\n\n[vid]: //mpvideo.qpic.cn/demo.mp4",
            "external_media_not_rewritten",
        ),
        (
            "![图][]\n\n[图]: //mmbiz.qpic.cn/collapsed.png",
            "external_media_not_rewritten",
        ),
        (
            "![img]\n\n[IMG]: //mmbiz.qpic.cn/shortcut.png",
            "external_media_not_rewritten",
        ),
    ],
)
def test_scan_markdown_quality_resolves_reference_style_media(markdown, expected_issue):
    issues = scan_markdown_quality(markdown)

    assert issues.count(expected_issue) == 1


@pytest.mark.parametrize(
    "markdown",
    [
        "[unused]: //mmbiz.qpic.cn/demo.png",
        ("[duplicate]: //mpvideo.qpic.cn/demo.mp4\n[duplicate]: https://example.com/ignored"),
    ],
)
def test_scan_markdown_quality_ignores_unused_external_media_definition(markdown):

    issues = scan_markdown_quality(markdown)

    assert "external_media_not_rewritten" not in issues


def test_scan_markdown_quality_handles_large_parent_relative_video_path():
    parent_prefix = "../" * 20_000
    markdown = f"[观看]({parent_prefix}videos/demo.mp4)"

    issues = scan_markdown_quality(markdown)

    assert "relative_local_video" in issues


def test_scan_markdown_quality_skips_each_malformed_link_payload_once(monkeypatch):
    original_parser = quality_module._parse_markdown_destination_payload
    parse_calls = 0

    def counting_parser(markdown, payload_start):
        nonlocal parse_calls
        parse_calls += 1
        return original_parser(markdown, payload_start)

    monkeypatch.setattr(
        quality_module,
        "_parse_markdown_destination_payload",
        counting_parser,
    )

    scan_markdown_quality("[x](" * 1_000)

    assert parse_calls == 1


@pytest.mark.parametrize(
    ("markdown", "expected_issue"),
    [
        (
            "![图][img]\n\n> [img]: //mmbiz.qpic.cn/blockquote.png",
            "external_media_not_rewritten",
        ),
        (
            "![图][img]\n\n> > [img]: //mmbiz.qpic.cn/nested.png",
            "external_media_not_rewritten",
        ),
        (
            "![图][img]\n\n   [img]: //mmbiz.qpic.cn/three-spaces.png",
            "external_media_not_rewritten",
        ),
        (
            "[观看][vid]\n\n[vid]:\n  ../videos/demo.mp4",
            "relative_local_video",
        ),
        (
            "[观看][vid]\n\n> > [vid]:\n> >   ../VIDEOS/demo.MP4",
            "relative_local_video",
        ),
        (
            "![图][img]\n\n[img]:\n//mmbiz.qpic.cn/zero-indent.png",
            "external_media_not_rewritten",
        ),
        (
            "![图][img]\n\n[img]:\n    //mmbiz.qpic.cn/four-spaces.png",
            "external_media_not_rewritten",
        ),
        (
            "[观看][vid]\n\n[vid]:\n\t../videos/tab-demo.mp4",
            "relative_local_video",
        ),
        (
            "![图][img]\n\n> [img]:\n//mmbiz.qpic.cn/lazy.png",
            "external_media_not_rewritten",
        ),
        (
            "[观看][vid]\n\n> > [vid]:\n../videos/lazy-demo.mp4",
            "relative_local_video",
        ),
    ],
)
def test_scan_markdown_quality_resolves_container_reference_definitions(markdown, expected_issue):
    issues = scan_markdown_quality(markdown)

    assert expected_issue in issues


@pytest.mark.parametrize(
    "markdown",
    [
        "[ref]:\n  https://example.com/**/continued",
        "> [ref]:\n>   https://example.com/**/blockquote",
    ],
)
def test_scan_markdown_quality_masks_continued_definition_destinations(markdown):
    issues = scan_markdown_quality(markdown)

    assert "unbalanced_emphasis_marker" not in issues


@pytest.mark.parametrize(
    "markdown",
    [
        "> [unused]: //mmbiz.qpic.cn/unused.png",
        "![图][img]\n\n\t[img]: //mmbiz.qpic.cn/tab-start.png",
        "![图][img]\n\n    [img]: //mmbiz.qpic.cn/four-space-start.png",
    ],
)
def test_scan_markdown_quality_ignores_unused_or_invalid_container_definitions(
    markdown,
):
    issues = scan_markdown_quality(markdown)

    assert "external_media_not_rewritten" not in issues


@pytest.mark.parametrize(
    "markdown",
    [
        "![图][a\\]b]\n\n[a\\]b]: //mmbiz.qpic.cn/escaped-label.png",
        ("![图][A\\]   B]\n\n[a\\] b]: //mmbiz.qpic.cn/normalized-label.png"),
    ],
)
def test_scan_markdown_quality_resolves_escaped_reference_labels(markdown):
    issues = scan_markdown_quality(markdown)

    assert "external_media_not_rewritten" in issues


def test_build_package_quality_reads_metadata_and_article(tmp_path: Path):
    package = tmp_path / "article-package"
    package.mkdir()
    (package / "article.md").write_text(
        "# Demo\n\n![Image](images/img_001.png)\n", encoding="utf-8"
    )
    (package / "metadata.json").write_text(
        json.dumps(
            {
                "title": "Demo",
                "source_url": "https://mp.weixin.qq.com/s/demo",
                "images": [{"local_path": "images/img_001.png"}],
                "extraction": {"warnings": ["missing_publish_time"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    item = build_package_quality(
        url="https://mp.weixin.qq.com/s/demo",
        package_dir=package,
    )

    assert item["status"] == "ok"
    assert item["title"] == "Demo"
    assert item["image_count"] == 1
    assert item["warnings"] == ["missing_publish_time"]
    assert item["quality_issues"] == []


def test_build_package_quality_marks_content_not_found_warning_as_failed(tmp_path: Path):
    package = tmp_path / "empty-juejin-package"
    package.mkdir()
    (package / "article.md").write_text("# https://juejin.cn/post/demo\n", encoding="utf-8")
    (package / "metadata.json").write_text(
        json.dumps(
            {
                "title": "https://juejin.cn/post/demo",
                "source_url": "https://juejin.cn/post/demo",
                "images": [],
                "extraction": {"warnings": ["juejin_content_not_found"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    item = build_package_quality(
        url="https://juejin.cn/post/demo",
        package_dir=package,
    )

    assert item["status"] == "fail"
    assert item["error"] == "juejin_content_not_found"
    assert item["warnings"] == ["juejin_content_not_found"]


def test_write_batch_report_creates_machine_and_human_reports(tmp_path: Path):
    results = [
        {
            "url": "https://mp.weixin.qq.com/s/ok",
            "status": "ok",
            "title": "OK",
            "platform": "wechat",
            "fetcher": "camoufox",
            "stage": "complete",
            "elapsed_ms": 123,
            "package_dir": "output/ok",
            "warnings": [],
            "quality_issues": [],
            "image_count": 2,
            "video_count": 1,
        },
        {
            "url": "https://mp.weixin.qq.com/s/fail",
            "status": "fail",
            "error": "wechat_content_not_found",
            "title": "",
            "platform": "wechat",
            "fetcher": "camoufox",
            "stage": "parse",
            "elapsed_ms": 45,
            "package_dir": "",
            "warnings": [],
            "quality_issues": [],
            "image_count": 0,
            "video_count": 0,
        },
    ]

    paths = write_batch_report(results, tmp_path)

    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    markdown = paths["markdown"].read_text(encoding="utf-8")
    assert payload["summary"] == {
        "total": 2,
        "ok": 1,
        "skipped": 0,
        "failed": 1,
        "with_warnings": 0,
        "with_quality_issues": 0,
    }
    assert "Batch Quality Report" in markdown
    assert "wechat_content_not_found" in markdown
    assert "| Status | Platform | Fetcher | Stage | Time | Title |" in markdown
    assert "| ok | wechat | camoufox | complete | 123 ms | OK |" in markdown
