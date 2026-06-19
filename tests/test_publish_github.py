import base64
import subprocess
from pathlib import Path

import httpx
import pytest

from magicmd.publish.github import (
    build_authenticated_remote_url,
    build_github_remote_url,
    create_github_pull_request,
    load_dotenv_values,
    mask_token,
    publish_to_github,
    publish_to_git_worktree,
    require_github_token,
)
from magicmd.publish.errors import PublishGitHubError
from magicmd.publish.models import PublishFile, PublishPlan, PublishResult


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


def test_publish_to_git_worktree_rejects_nonempty_target_dir_without_overwrite(tmp_path: Path):
    repo = _repo(tmp_path)
    target = repo / "content/posts"
    target.mkdir(parents=True)
    (target / "other.md").write_text("existing", encoding="utf-8")
    package_dir = tmp_path / "package"
    package_dir.mkdir()

    with pytest.raises(Exception, match="Target directory already exists"):
        publish_to_git_worktree(_plan(package_dir), repo)


@pytest.mark.parametrize("case", ["absolute", "relative_parent"])
def test_publish_to_git_worktree_rejects_target_paths_outside_repo(tmp_path: Path, case: str):
    repo = _repo(tmp_path)
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    article = package_dir / "article.md"
    article.write_text("# Article\n", encoding="utf-8")
    if case == "absolute":
        outside_path = tmp_path / "outside-absolute.md"
        target_path = str(outside_path)
    else:
        target_path = "../../outside-relative.md"
        outside_path = (repo / target_path).resolve()
    if outside_path.exists():
        outside_path.unlink()
    plan = _plan(package_dir).model_copy(
        update={
            "target_dir": "content/posts",
            "files": [
                PublishFile(
                    source_path=str(article),
                    target_path=target_path,
                    size_bytes=article.stat().st_size,
                )
            ],
        }
    )

    with pytest.raises(Exception, match="Target path must stay inside the repository"):
        publish_to_git_worktree(plan, repo)

    assert not outside_path.exists()


def test_publish_to_git_worktree_bases_existing_remote_branch(tmp_path: Path):
    repo = _repo(tmp_path)
    default_branch = _run_git(repo, "branch", "--show-current")
    _run_git(repo, "checkout", "-b", "magicmd/article")
    (repo / "remote.md").write_text("remote branch content\n", encoding="utf-8")
    _run_git(repo, "add", "remote.md")
    _run_git(repo, "commit", "-m", "Remote branch change")
    remote_sha = _run_git(repo, "rev-parse", "HEAD")
    _run_git(repo, "checkout", default_branch)
    _run_git(repo, "branch", "-D", "magicmd/article")
    _run_git(repo, "update-ref", "refs/remotes/origin/magicmd/article", remote_sha)
    package_dir = tmp_path / "package"
    package_dir.mkdir()

    publish_to_git_worktree(_plan(package_dir), repo)

    assert _run_git(repo, "rev-parse", "HEAD^") == remote_sha


def test_publish_to_git_worktree_sets_local_git_identity(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "missing-global-gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init")
    package_dir = tmp_path / "package"
    package_dir.mkdir()

    result = publish_to_git_worktree(_plan(package_dir), repo)

    assert result.commit_sha
    assert _run_git(repo, "config", "user.name") == "MagicMD"
    assert _run_git(repo, "config", "user.email") == "magicmd@example.com"


def test_require_github_token_rejects_missing_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    with pytest.raises(Exception, match="GITHUB_TOKEN"):
        require_github_token()


def test_require_github_token_reads_project_dotenv(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        """
        # Local publishing token
        GITHUB_TOKEN="dotenv-token"
        """,
        encoding="utf-8",
    )

    assert require_github_token(dotenv_path=dotenv_path) == "dotenv-token"


def test_require_github_token_prefers_environment_over_dotenv(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("GITHUB_TOKEN", "environment-token")
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("GITHUB_TOKEN=dotenv-token\n", encoding="utf-8")

    assert require_github_token(dotenv_path=dotenv_path) == "environment-token"


def test_load_dotenv_values_ignores_comments_and_supports_export(tmp_path: Path):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        """
        # ignored
        export GITHUB_TOKEN=dotenv-token # local only
        INVALID LINE
        OTHER='quoted value'
        """,
        encoding="utf-8",
    )

    assert load_dotenv_values(dotenv_path) == {
        "GITHUB_TOKEN": "dotenv-token",
        "OTHER": "quoted value",
    }


def test_create_github_pull_request_uses_default_branch():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"default_branch": "main"})
        return httpx.Response(201, json={"html_url": "https://github.com/owner/repo/pull/1"})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    pr_url = create_github_pull_request(
        repo="owner/repo",
        branch="magicmd/article",
        title="Add article",
        body="Generated by MagicMD.",
        token="secret",
        client=client,
    )

    assert pr_url == "https://github.com/owner/repo/pull/1"
    assert requests[0].method == "GET"
    assert requests[1].method == "POST"
    assert requests[1].url.path == "/repos/owner/repo/pulls"
    assert '"head":"magicmd/article"' in requests[1].content.decode()
    assert '"base":"main"' in requests[1].content.decode()


@pytest.mark.parametrize(
    "error",
    [
        httpx.TimeoutException("timed out"),
        httpx.TransportError("connection failed"),
        httpx.HTTPError("http failed"),
    ],
)
def test_create_github_pull_request_wraps_httpx_errors(error):
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(PublishGitHubError, match="GitHub PR request failed"):
        create_github_pull_request(
            repo="owner/repo",
            branch="magicmd/article",
            title="Add article",
            body="Generated by MagicMD.",
            token="secret",
            client=client,
        )


def test_build_authenticated_remote_url_for_https_clone():
    url = build_authenticated_remote_url("owner/repo", "secret-token")

    assert url == "https://github.com/owner/repo.git"
    assert "secret-token" not in url


def test_build_github_remote_url_for_https_clone():
    url = build_github_remote_url("owner/repo")

    assert url == "https://github.com/owner/repo.git"


def test_mask_token_removes_token_from_messages():
    message = "https://x-access-token:secret-token@github.com/owner/repo.git failed"

    assert "secret-token" not in mask_token(message, "secret-token")


def test_publish_to_github_does_not_pass_token_in_git_argv(monkeypatch, tmp_path: Path):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    commands: list[list[str]] = []
    clone_envs: list[dict[str, str]] = []
    expected_header = "Authorization: Basic " + base64.b64encode(
        b"x-access-token:secret-token"
    ).decode("ascii")

    def fake_subprocess_run(args, **kwargs):
        command = [str(arg) for arg in args]
        commands.append(command)
        assert "secret-token" not in " ".join(command)
        if command[:2] == ["git", "clone"]:
            clone_envs.append(kwargs["env"])
            Path(command[-1]).mkdir(parents=True, exist_ok=True)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    def fake_publish_to_git_worktree(plan, repo_dir):
        return PublishResult(
            repo=plan.repo, branch=plan.branch, commit_sha="abc123", files=plan.files
        )

    def fake_run_git(repo_dir, *args, env=None):
        command = ["git", "-C", str(repo_dir), *args]
        commands.append(command)
        assert "secret-token" not in " ".join(command)
        assert env is None or env["GIT_CONFIG_VALUE_0"] == expected_header
        return ""

    monkeypatch.setattr("magicmd.publish.github.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "magicmd.publish.github.publish_to_git_worktree", fake_publish_to_git_worktree
    )
    monkeypatch.setattr("magicmd.publish.github._run_git", fake_run_git)

    publish_to_github(_plan(package_dir), token="secret-token")

    assert commands
    assert commands[0][:2] == ["git", "clone"]
    assert commands[0][2] == "https://github.com/owner/repo.git"
    assert clone_envs
    clone_env = clone_envs[0]
    assert clone_env["GIT_CONFIG_KEY_0"] == ("http.https://github.com/owner/repo.git.extraHeader")
    assert clone_env["GIT_CONFIG_VALUE_0"] == expected_header
    auth_scheme, encoded_credentials = (
        clone_env["GIT_CONFIG_VALUE_0"].removeprefix("Authorization: ").split(" ", 1)
    )
    assert auth_scheme == "Basic"
    assert base64.b64decode(encoded_credentials).decode("utf-8") == ("x-access-token:secret-token")
