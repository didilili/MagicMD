from __future__ import annotations

import re
from pathlib import Path

from magicmd.publish.errors import PublishPlanError
from magicmd.publish.models import GithubPublishOptions, PublishFile, PublishPlan
from magicmd.sdk import ArticleConversionResult
from magicmd.template_vars import format_template


def slugify_publish_title(title: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title.lower(), flags=re.UNICODE).strip("-")
    return slug[:80] or "article"


def build_publish_template_vars(result: ArticleConversionResult) -> dict[str, str]:
    date = result.published_at[:10] if result.published_at else "undated"
    content_hash = result.content_hash or ""
    return {
        "title": result.title,
        "slug": slugify_publish_title(result.title),
        "date": date,
        "published_at": result.published_at,
        "author": result.author,
        "platform": result.platform,
        "source_url": result.source_url,
        "canonical_url": result.canonical_url or result.source_url,
        "content_hash": content_hash,
        "short_hash": content_hash[:6],
    }


def sanitize_branch_name(branch: str) -> str:
    sanitized = re.sub(r"\s+", "-", branch.strip())
    sanitized = re.sub(r"[~^:?*\[\]\\]+", "-", sanitized)
    sanitized = sanitized.replace("..", "-").replace("@{", "-")
    sanitized = sanitized.strip("/.")
    if not sanitized:
        raise PublishPlanError("Branch template produced an empty branch name")
    _ensure_valid_branch_name(sanitized)
    return sanitized


def _ensure_valid_branch_name(branch: str) -> None:
    if branch == "@":
        raise PublishPlanError("Branch template produced an invalid branch name: @")
    if any(ord(character) < 32 or ord(character) == 127 for character in branch):
        raise PublishPlanError("Branch template produced a branch name with control characters")
    if branch.endswith(".lock"):
        raise PublishPlanError("Branch template produced a branch name ending with .lock")
    for component in branch.split("/"):
        if not component:
            raise PublishPlanError("Branch template produced an invalid branch path")
        if component.startswith("."):
            raise PublishPlanError(
                "Branch template produced an invalid branch path component starting with ."
            )
        if component.endswith(".lock"):
            raise PublishPlanError(
                "Branch template produced an invalid branch path component ending with .lock"
            )


def render_publish_template(template: str, result: ArticleConversionResult) -> str:
    return format_template(template, build_publish_template_vars(result))


def _normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip("/")
    if not normalized:
        raise PublishPlanError("target_dir must not be empty")
    if normalized.startswith("../") or "/../" in f"/{normalized}/":
        raise PublishPlanError("target_dir must stay inside the repository")
    return normalized


def _collect_package_files(package_dir: Path, target_dir: str) -> list[PublishFile]:
    files: list[PublishFile] = []
    for source_path in sorted(path for path in package_dir.rglob("*") if path.is_file()):
        relative_path = source_path.relative_to(package_dir).as_posix()
        files.append(
            PublishFile(
                source_path=str(source_path),
                target_path=f"{target_dir}/{relative_path}",
                size_bytes=source_path.stat().st_size,
            )
        )
    return files


def build_github_publish_plan(
    result: ArticleConversionResult,
    options: GithubPublishOptions,
) -> PublishPlan:
    if result.package_dir is None:
        raise PublishPlanError("Publishing requires a written package_dir")
    package_dir = Path(result.package_dir)
    if not package_dir.exists():
        raise PublishPlanError(f"package_dir does not exist: {package_dir}")

    target_dir = _normalize_repo_path(render_publish_template(options.target_dir, result))
    files = _collect_package_files(package_dir, target_dir)
    if not files:
        raise PublishPlanError(f"package_dir does not contain files: {package_dir}")

    branch = sanitize_branch_name(render_publish_template(options.branch, result))
    commit_message = render_publish_template(options.commit_message, result).strip()
    if not commit_message:
        raise PublishPlanError("commit_message template produced an empty commit message")

    return PublishPlan(
        repo=options.repo,
        target_dir=target_dir,
        branch=branch,
        commit_message=commit_message,
        create_pr=options.create_pr,
        overwrite=options.overwrite,
        title=result.title,
        platform=result.platform,
        source_url=result.source_url,
        package_dir=str(package_dir),
        files=files,
    )
