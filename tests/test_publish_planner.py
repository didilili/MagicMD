from pathlib import Path

import pytest

from magicmd.publish.models import GithubPublishOptions
from magicmd.publish.planner import (
    build_github_publish_plan,
    build_publish_template_vars,
    render_publish_template,
    sanitize_branch_name,
)
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


@pytest.mark.parametrize("branch", ["release.lock", "magicmd/.hidden", "@"])
def test_sanitize_branch_name_rejects_invalid_git_refs(branch: str):
    with pytest.raises(Exception, match="Branch template produced"):
        sanitize_branch_name(branch)


def test_github_publish_options_defaults_are_safe():
    options = GithubPublishOptions(repo="owner/repo", target_dir="content/posts")

    assert options.branch == "magicmd/{slug}"
    assert options.commit_message == "Add article: {title}"
    assert options.create_pr is False
    assert options.overwrite is False


def test_build_github_publish_plan_collects_package_files(tmp_path: Path):
    package_dir = tmp_path / "package"
    image_dir = package_dir / "images"
    image_dir.mkdir(parents=True)
    (package_dir / "article.md").write_text("# Title\n", encoding="utf-8")
    (package_dir / "metadata.json").write_text("{}", encoding="utf-8")
    (image_dir / "img_001.png").write_bytes(b"png")

    plan = build_github_publish_plan(
        _result(package_dir),
        GithubPublishOptions(repo="owner/repo", target_dir="content/posts"),
    )

    assert plan.repo == "owner/repo"
    assert plan.target_dir == "content/posts"
    assert plan.branch == "magicmd/magicmd-发布测试"
    assert plan.commit_message == "Add article: MagicMD 发布测试"
    assert [file.target_path for file in plan.files] == [
        "content/posts/article.md",
        "content/posts/images/img_001.png",
        "content/posts/metadata.json",
    ]


def test_build_github_publish_plan_renders_target_dir_template(tmp_path: Path):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "article.md").write_text("# Title\n", encoding="utf-8")

    plan = build_github_publish_plan(
        _result(package_dir),
        GithubPublishOptions(repo="owner/repo", target_dir="content/posts/{date}-{slug}"),
    )

    assert plan.target_dir == "content/posts/2026-06-19-magicmd-发布测试"
    assert [file.target_path for file in plan.files] == [
        "content/posts/2026-06-19-magicmd-发布测试/article.md",
    ]


def test_build_github_publish_plan_requires_package_dir(tmp_path: Path):
    result = _result(tmp_path).model_copy(update={"package_dir": None})

    with pytest.raises(Exception, match="requires a written package_dir"):
        build_github_publish_plan(
            result,
            GithubPublishOptions(repo="owner/repo", target_dir="content/posts"),
        )


def test_build_github_publish_plan_rejects_empty_file_package(tmp_path: Path):
    package_dir = tmp_path / "empty"
    package_dir.mkdir()

    with pytest.raises(Exception, match="does not contain files"):
        build_github_publish_plan(
            _result(package_dir),
            GithubPublishOptions(repo="owner/repo", target_dir="content/posts"),
        )
