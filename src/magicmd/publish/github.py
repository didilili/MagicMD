from __future__ import annotations

import os
import base64
import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx

from magicmd.publish.errors import PublishGitError, PublishGitHubError
from magicmd.publish.models import PublishFile, PublishPlan, PublishResult


GIT_USER_NAME = "MagicMD"
GIT_USER_EMAIL = "magicmd@example.com"


def _git_env(extra: dict[str, str] | None = None) -> dict[str, str] | None:
    if extra is None:
        return None
    env = os.environ.copy()
    env.update(extra)
    return env


def _run_git(repo_dir: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        text=True,
        capture_output=True,
        env=_git_env(env),
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        raise PublishGitError(message or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _has_git_config(repo_dir: Path, key: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "config", "--get", key],
        text=True,
        capture_output=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def _ensure_git_identity(repo_dir: Path) -> None:
    if not _has_git_config(repo_dir, "user.name"):
        _run_git(repo_dir, "config", "user.name", GIT_USER_NAME)
    if not _has_git_config(repo_dir, "user.email"):
        _run_git(repo_dir, "config", "user.email", GIT_USER_EMAIL)


def _remote_branch_exists(repo_dir: Path, branch: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "--verify", f"origin/{branch}"],
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def _checkout_publish_branch(repo_dir: Path, branch: str) -> None:
    if _remote_branch_exists(repo_dir, branch):
        _run_git(repo_dir, "checkout", "-B", branch, f"origin/{branch}")
    else:
        _run_git(repo_dir, "checkout", "-B", branch)


def _resolve_repo_target(repo_dir: Path, repo_path: str) -> Path:
    raw_path = Path(repo_path)
    if raw_path.is_absolute():
        raise PublishGitError(f"Target path must stay inside the repository: {repo_path}")
    target_path = (repo_dir / raw_path).resolve()
    if target_path != repo_dir and repo_dir not in target_path.parents:
        raise PublishGitError(f"Target path must stay inside the repository: {repo_path}")
    return target_path


def _has_unplanned_files(target_dir: Path, planned_targets: set[Path]) -> bool:
    if target_dir.is_file():
        return True
    if not target_dir.exists():
        return False
    for child in target_dir.rglob("*"):
        if child.is_file() and child.resolve() not in planned_targets:
            return True
    return False


def _copy_planned_files(plan: PublishPlan, repo_dir: Path) -> None:
    target_dir = _resolve_repo_target(repo_dir, plan.target_dir)
    planned_files: list[tuple[PublishFile, Path]] = []
    for file in plan.files:
        target_path = _resolve_repo_target(repo_dir, file.target_path)
        if target_path.exists() and not plan.overwrite:
            raise PublishGitError(f"Target file already exists: {file.target_path}")
        planned_files.append((file, target_path))
    planned_targets = {target_path for _, target_path in planned_files}
    if not plan.overwrite and _has_unplanned_files(target_dir, planned_targets):
        raise PublishGitError(
            f"Target directory already exists and is not empty: {plan.target_dir}"
        )
    for file, target_path in planned_files:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file.source_path, target_path)


def publish_to_git_worktree(plan: PublishPlan, repo_dir: Path) -> PublishResult:
    repo_dir = repo_dir.resolve()
    if not (repo_dir / ".git").exists():
        raise PublishGitError(f"Not a git repository: {repo_dir}")

    _ensure_git_identity(repo_dir)
    _checkout_publish_branch(repo_dir, plan.branch)
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


def require_github_token(token: str | None = None) -> str:
    resolved = token or os.environ.get("GITHUB_TOKEN", "")
    if not resolved:
        raise PublishGitHubError(
            "GITHUB_TOKEN is required for real GitHub publishing. Use --dry-run to preview only."
        )
    return resolved


def _github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def create_github_pull_request(
    repo: str,
    branch: str,
    title: str,
    body: str,
    token: str,
    client: httpx.Client | None = None,
) -> str:
    owns_client = client is None
    http_client = client or httpx.Client(timeout=20)
    try:
        try:
            repo_response = http_client.get(
                f"https://api.github.com/repos/{repo}",
                headers=_github_headers(token),
            )
            if repo_response.status_code >= 400:
                raise PublishGitHubError(f"GitHub repo lookup failed: {repo_response.text}")
            default_branch = repo_response.json().get("default_branch") or "main"

            pr_response = http_client.post(
                f"https://api.github.com/repos/{repo}/pulls",
                headers=_github_headers(token),
                json={
                    "title": title,
                    "head": branch,
                    "base": default_branch,
                    "body": body,
                },
            )
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPError) as exc:
            raise PublishGitHubError(f"GitHub PR request failed: {exc}") from exc
        if pr_response.status_code >= 400:
            raise PublishGitHubError(f"GitHub PR creation failed: {pr_response.text}")
        return str(pr_response.json().get("html_url", ""))
    finally:
        if owns_client:
            http_client.close()


def build_github_remote_url(repo: str) -> str:
    return f"https://github.com/{repo}.git"


def build_authenticated_remote_url(repo: str, _token: str) -> str:
    return build_github_remote_url(repo)


def _github_git_auth_header(token: str) -> str:
    credential = base64.b64encode(f"x-access-token:{token}".encode("utf-8")).decode("ascii")
    return f"Authorization: Basic {credential}"


def _github_git_auth_env(repo: str, token: str) -> dict[str, str]:
    remote_url = build_github_remote_url(repo)
    return {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": f"http.{remote_url}.extraHeader",
        "GIT_CONFIG_VALUE_0": _github_git_auth_header(token),
    }


def mask_token(message: str, token: str) -> str:
    return message.replace(token, "***") if token else message


def publish_to_github(
    plan: PublishPlan,
    token: str | None = None,
) -> PublishResult:
    resolved_token = require_github_token(token)
    with tempfile.TemporaryDirectory(prefix="magicmd-publish-") as temp_dir:
        worktree = Path(temp_dir) / "repo"
        remote_url = build_github_remote_url(plan.repo)
        auth_env = _github_git_auth_env(plan.repo, resolved_token)
        try:
            subprocess.run(
                ["git", "clone", remote_url, str(worktree)],
                text=True,
                capture_output=True,
                check=True,
                env=_git_env(auth_env),
            )
            result = publish_to_git_worktree(plan, worktree)
            _run_git(worktree, "push", "origin", plan.branch, env=auth_env)
            _run_git(worktree, "remote", "set-url", "origin", f"https://github.com/{plan.repo}.git")
            if plan.create_pr:
                result.pr_url = create_github_pull_request(
                    repo=plan.repo,
                    branch=plan.branch,
                    title=plan.commit_message,
                    body=f"Generated by MagicMD from {plan.source_url}",
                    token=resolved_token,
                )
            return result
        except subprocess.CalledProcessError as exc:
            message = mask_token(exc.stderr or exc.stdout or str(exc), resolved_token)
            raise PublishGitError(message) from exc
        except PublishGitError as exc:
            raise PublishGitError(mask_token(str(exc), resolved_token)) from exc
