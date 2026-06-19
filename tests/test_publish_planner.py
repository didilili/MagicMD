from pathlib import Path

import pytest

from magicmd.publish.models import GithubPublishOptions
from magicmd.publish.planner import build_publish_template_vars, render_publish_template
from magicmd.sdk import ArticleConversionResult


def _result(package_dir: Path) -> ArticleConversionResult:
    return ArticleConversionResult(
        title="MagicMD 发布测试",
        author="didilili",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/example",
        canonical_url="https://mp.weixin.qq.com/s/example",
        published_at="2026-06-19T12:00:00+08:00",
        markdown="# MagicMD 发布测试\n\n正文",
        content_hash="abcdef123456",
        package_dir=str(package_dir),
    )


def test_build_publish_template_vars_from_conversion_result(tmp_path: Path):
    variables = build_publish_template_vars(_result(tmp_path))

    assert variables["title"] == "MagicMD 发布测试"
    assert variables["slug"] == "magicmd-发布测试"
    assert variables["date"] == "2026-06-19"
    assert variables["platform"] == "wechat"
    assert variables["short_hash"] == "abcdef"


def test_render_publish_template_reports_unknown_fields(tmp_path: Path):
    with pytest.raises(ValueError, match="Unknown template field: missing"):
        render_publish_template("magicmd/{missing}", _result(tmp_path))


def test_github_publish_options_defaults_are_safe():
    options = GithubPublishOptions(repo="owner/repo", target_dir="content/posts")

    assert options.branch == "magicmd/{slug}"
    assert options.commit_message == "Add article: {title}"
    assert options.create_pr is False
    assert options.overwrite is False
