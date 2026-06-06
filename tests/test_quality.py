import json
from pathlib import Path

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
"""

    issues = scan_markdown_quality(markdown)

    assert "empty_code_fence" in issues
    assert "image_used_as_heading" in issues
    assert "fragmented_recommendation_text" in issues
    assert "fragmented_bold_text" in issues
    assert "broken_numbered_link_emphasis" in issues


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
"""

    issues = scan_markdown_quality(markdown)

    assert "fragmented_bold_text" not in issues


def test_build_package_quality_reads_metadata_and_article(tmp_path: Path):
    package = tmp_path / "article-package"
    package.mkdir()
    (package / "article.md").write_text("# Demo\n\n![Image](images/img_001.png)\n", encoding="utf-8")
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
        "failed": 1,
        "with_warnings": 0,
        "with_quality_issues": 0,
    }
    assert "Batch Quality Report" in markdown
    assert "wechat_content_not_found" in markdown
