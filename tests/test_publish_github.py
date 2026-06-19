import subprocess
from pathlib import Path

import pytest

from magicmd.publish.github import publish_to_git_worktree
from magicmd.publish.models import PublishFile, PublishPlan


def _run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "magicmd@example.com")
    _run_git(repo, "config", "user.name", "MagicMD")
    (repo / "README.md").write_text("# Content\n", encoding="utf-8")
    _run_git(repo, "add", "README.md")
    _run_git(repo, "commit", "-m", "Initial commit")
    return repo


def _plan(package_dir: Path) -> PublishPlan:
    article = package_dir / "article.md"
    article.write_text("# Article\n", encoding="utf-8")
    return PublishPlan(
        repo="owner/repo",
        target_dir="content/posts",
        branch="magicmd/article",
        commit_message="Add article",
        title="Article",
        platform="generic",
        source_url="https://example.com/post",
        package_dir=str(package_dir),
        files=[
            PublishFile(
                source_path=str(article),
                target_path="content/posts/article.md",
                size_bytes=article.stat().st_size,
            )
        ],
    )


def test_publish_to_git_worktree_commits_planned_files(tmp_path: Path):
    repo = _repo(tmp_path)
    package_dir = tmp_path / "package"
    package_dir.mkdir()

    result = publish_to_git_worktree(_plan(package_dir), repo)

    assert result.branch == "magicmd/article"
    assert result.commit_sha
    assert (repo / "content/posts/article.md").read_text(encoding="utf-8") == "# Article\n"
    assert _run_git(repo, "branch", "--show-current") == "magicmd/article"
    assert _run_git(repo, "log", "-1", "--pretty=%s") == "Add article"


def test_publish_to_git_worktree_rejects_existing_files_without_overwrite(tmp_path: Path):
    repo = _repo(tmp_path)
    target = repo / "content/posts"
    target.mkdir(parents=True)
    (target / "article.md").write_text("existing", encoding="utf-8")
    package_dir = tmp_path / "package"
    package_dir.mkdir()

    with pytest.raises(Exception, match="Target file already exists"):
        publish_to_git_worktree(_plan(package_dir), repo)
