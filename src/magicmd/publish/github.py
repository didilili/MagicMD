from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from magicmd.publish.errors import PublishGitError
from magicmd.publish.models import PublishPlan, PublishResult


def _run_git(repo_dir: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        raise PublishGitError(message or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _copy_planned_files(plan: PublishPlan, repo_dir: Path) -> None:
    for file in plan.files:
        target_path = repo_dir / file.target_path
        if target_path.exists() and not plan.overwrite:
            raise PublishGitError(f"Target file already exists: {file.target_path}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file.source_path, target_path)


def publish_to_git_worktree(plan: PublishPlan, repo_dir: Path) -> PublishResult:
    repo_dir = repo_dir.resolve()
    if not (repo_dir / ".git").exists():
        raise PublishGitError(f"Not a git repository: {repo_dir}")

    _run_git(repo_dir, "checkout", "-B", plan.branch)
    _copy_planned_files(plan, repo_dir)
    _run_git(repo_dir, "add", "--", plan.target_dir)
    status = _run_git(repo_dir, "status", "--porcelain", "--", plan.target_dir)
    if not status:
        raise PublishGitError("No publish changes to commit")
    _run_git(repo_dir, "commit", "-m", plan.commit_message)
    commit_sha = _run_git(repo_dir, "rev-parse", "HEAD")
    return PublishResult(
        repo=plan.repo,
        branch=plan.branch,
        commit_sha=commit_sha,
        files=plan.files,
    )
