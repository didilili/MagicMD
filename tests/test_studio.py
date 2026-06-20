from __future__ import annotations

import json
import threading
from pathlib import Path
from importlib import resources
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from typer.testing import CliRunner

from magicmd.cli import app
from magicmd.sdk import ArticleConversionResult


runner = CliRunner()


def _studio_headers(token: str) -> dict[str, str]:
    return {"X-MagicMD-Studio-Token": token}


def _request_json(
    url: str,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
) -> dict:
    if payload is None:
        with urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _request_json_error(
    url: str, payload: dict, headers: dict[str, str] | None = None
) -> tuple[int, dict]:
    try:
        _request_json(url, payload, headers=headers)
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    raise AssertionError("Expected request to fail")


def _start_server(server):
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


def _fake_result(package_dir: Path) -> ArticleConversionResult:
    return ArticleConversionResult(
        title="本地控制台文章",
        author="MagicMD",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        canonical_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-20T09:00:00+08:00",
        excerpt="Studio 测试",
        markdown="# 本地控制台文章\n\n正文",
        content_hash="abc123",
        package_dir=str(package_dir),
        metadata={"title": "本地控制台文章"},
    )


def test_studio_status_endpoint_reports_local_environment(monkeypatch, tmp_path: Path):
    from magicmd.studio.server import create_studio_server

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_demo")
    (tmp_path / ".magicmd.toml").write_text('[output]\ndirectory = "output"\n', encoding="utf-8")
    server = create_studio_server(host="127.0.0.1", port=0, cwd=tmp_path)
    _start_server(server)

    try:
        payload = _request_json(f"http://127.0.0.1:{server.server_port}/api/status")
    finally:
        server.shutdown()
        server.server_close()

    assert payload["ok"] is True
    assert payload["cwd"] == str(tmp_path)
    assert payload["config"]["exists"] is True
    assert payload["github"]["tokenConfigured"] is True


def test_studio_convert_endpoint_returns_package_summary(tmp_path: Path):
    from magicmd.studio.server import StudioServices, create_studio_server

    token = "test-token"
    package_dir = tmp_path / "output" / "2026-06-20-studio"
    package_dir.mkdir(parents=True)
    (package_dir / "article.md").write_text("# 本地控制台文章\n\n正文", encoding="utf-8")
    (package_dir / "metadata.json").write_text('{"title": "本地控制台文章"}', encoding="utf-8")

    def fake_convert_article(**kwargs):
        assert kwargs["url"] == "https://mp.weixin.qq.com/s/demo"
        assert kwargs["output_dir"] == tmp_path / "output"
        assert kwargs["download_images"] is True
        return _fake_result(package_dir)

    server = create_studio_server(
        host="127.0.0.1",
        port=0,
        cwd=tmp_path,
        token=token,
        services=StudioServices(convert_article=fake_convert_article),
    )
    _start_server(server)

    try:
        payload = _request_json(
            f"http://127.0.0.1:{server.server_port}/api/convert",
            {
                "url": "https://mp.weixin.qq.com/s/demo",
                "output": "output",
                "downloadImages": True,
            },
            headers=_studio_headers(token),
        )
    finally:
        server.shutdown()
        server.server_close()

    assert payload["ok"] is True
    assert payload["title"] == "本地控制台文章"
    assert payload["packageDir"] == str(package_dir)
    assert {
        "path": "article.md",
        "sizeBytes": (package_dir / "article.md").stat().st_size,
    } in payload["files"]


def test_studio_convert_endpoint_accepts_inline_config_text(tmp_path: Path):
    from magicmd.studio.server import StudioServices, create_studio_server

    token = "test-token"
    package_dir = tmp_path / "output" / "2026-06-20-studio"
    package_dir.mkdir(parents=True)
    (package_dir / "index.md").write_text("# 本地控制台文章\n\n正文", encoding="utf-8")

    def fake_convert_article(**kwargs):
        config_path = kwargs["config_path"]
        assert config_path is not None
        assert config_path.exists()
        assert 'markdown = "index.md"' in config_path.read_text(encoding="utf-8")
        return _fake_result(package_dir)

    server = create_studio_server(
        host="127.0.0.1",
        port=0,
        cwd=tmp_path,
        token=token,
        services=StudioServices(convert_article=fake_convert_article),
    )
    _start_server(server)

    try:
        payload = _request_json(
            f"http://127.0.0.1:{server.server_port}/api/convert",
            {
                "url": "https://mp.weixin.qq.com/s/demo",
                "output": "output",
                "configText": '[output.naming]\nmarkdown = "index.md"\n',
            },
            headers=_studio_headers(token),
        )
    finally:
        server.shutdown()
        server.server_close()

    assert payload["ok"] is True


def test_studio_publish_plan_endpoint_uses_config_file(tmp_path: Path):
    from magicmd.studio.server import StudioServices, create_studio_server

    token = "test-token"
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [publish.github]
        repo = "owner/content"
        target_dir = "content/posts"
        branch = "magicmd/{slug}"
        commit_message = "发布文章：{title}"
        create_pr = true
        """,
        encoding="utf-8",
    )
    package_dir = tmp_path / "output" / "2026-06-20-studio"
    package_dir.mkdir(parents=True)
    (package_dir / "article.md").write_text("# 本地控制台文章\n\n正文", encoding="utf-8")
    (package_dir / "metadata.json").write_text('{"title": "本地控制台文章"}', encoding="utf-8")

    def fake_convert_article(**kwargs):
        assert kwargs["config_path"] == config_path
        return _fake_result(package_dir)

    server = create_studio_server(
        host="127.0.0.1",
        port=0,
        cwd=tmp_path,
        token=token,
        services=StudioServices(convert_article=fake_convert_article),
    )
    _start_server(server)

    try:
        payload = _request_json(
            f"http://127.0.0.1:{server.server_port}/api/publish/plan",
            {
                "url": "https://mp.weixin.qq.com/s/demo",
                "config": ".magicmd.toml",
            },
            headers=_studio_headers(token),
        )
    finally:
        server.shutdown()
        server.server_close()

    assert payload["ok"] is True
    assert payload["repo"] == "owner/content"
    assert payload["targetDir"] == "content/posts"
    assert payload["branch"] == "magicmd/本地控制台文章"
    assert payload["commitMessage"] == "发布文章：本地控制台文章"
    assert payload["createPr"] is True
    assert {
        "targetPath": "content/posts/article.md",
        "sizeBytes": (package_dir / "article.md").stat().st_size,
    } in payload["files"]


def test_studio_batch_endpoint_converts_multiple_urls(tmp_path: Path):
    from magicmd.studio.server import StudioServices, create_studio_server

    token = "test-token"
    calls = []

    def fake_convert_article(**kwargs):
        calls.append(kwargs["url"])
        index = len(calls)
        package_dir = tmp_path / "output" / f"article-{index}"
        package_dir.mkdir(parents=True)
        (package_dir / "article.md").write_text(f"# 文章 {index}\n", encoding="utf-8")
        return ArticleConversionResult(
            title=f"文章 {index}",
            author="MagicMD",
            platform="wechat",
            source_url=kwargs["url"],
            markdown=f"# 文章 {index}\n",
            content_hash=f"hash-{index}",
            package_dir=str(package_dir),
        )

    server = create_studio_server(
        host="127.0.0.1",
        port=0,
        cwd=tmp_path,
        token=token,
        services=StudioServices(convert_article=fake_convert_article),
    )
    _start_server(server)

    try:
        payload = _request_json(
            f"http://127.0.0.1:{server.server_port}/api/batch",
            {
                "batchText": "\n".join(
                    [
                        "https://mp.weixin.qq.com/s/one",
                        "",
                        "# comment",
                        "https://mp.weixin.qq.com/s/two",
                    ]
                ),
                "output": "output",
            },
            headers=_studio_headers(token),
        )
    finally:
        server.shutdown()
        server.server_close()

    assert payload["ok"] is True
    assert payload["summary"] == {"total": 2, "success": 2, "failed": 0}
    assert calls == ["https://mp.weixin.qq.com/s/one", "https://mp.weixin.qq.com/s/two"]
    assert [item["title"] for item in payload["items"]] == ["文章 1", "文章 2"]


def test_studio_batch_endpoint_returns_partial_failure_summary(tmp_path: Path):
    from magicmd.studio.server import StudioServices, create_studio_server

    token = "test-token"

    def fake_convert_article(**kwargs):
        if kwargs["url"].endswith("/bad"):
            raise RuntimeError("fetch failed")
        package_dir = tmp_path / "output" / "article-ok"
        package_dir.mkdir(parents=True)
        (package_dir / "article.md").write_text("# 成功文章\n", encoding="utf-8")
        return ArticleConversionResult(
            title="成功文章",
            author="MagicMD",
            platform="wechat",
            source_url=kwargs["url"],
            markdown="# 成功文章\n",
            content_hash="hash-ok",
            package_dir=str(package_dir),
        )

    server = create_studio_server(
        host="127.0.0.1",
        port=0,
        cwd=tmp_path,
        token=token,
        services=StudioServices(convert_article=fake_convert_article),
    )
    _start_server(server)

    try:
        payload = _request_json(
            f"http://127.0.0.1:{server.server_port}/api/batch",
            {
                "batchText": "\n".join(
                    [
                        "https://mp.weixin.qq.com/s/good",
                        "https://mp.weixin.qq.com/s/bad",
                    ]
                ),
                "output": "output",
            },
            headers=_studio_headers(token),
        )
    finally:
        server.shutdown()
        server.server_close()

    assert payload["ok"] is False
    assert payload["summary"] == {"total": 2, "success": 1, "failed": 1}
    assert payload["items"][0]["ok"] is True
    assert payload["items"][1] == {
        "ok": False,
        "url": "https://mp.weixin.qq.com/s/bad",
        "error": "fetch failed",
    }


def test_studio_config_endpoints_load_and_save_magicmd_toml(tmp_path: Path):
    from magicmd.studio.server import create_studio_server

    token = "test-token"
    server = create_studio_server(host="127.0.0.1", port=0, cwd=tmp_path, token=token)
    _start_server(server)

    try:
        before = _request_json(f"http://127.0.0.1:{server.server_port}/api/config")
        saved = _request_json(
            f"http://127.0.0.1:{server.server_port}/api/config/save",
            {
                "path": ".magicmd.toml",
                "configText": '[output]\ndirectory = "articles"\n',
            },
            headers=_studio_headers(token),
        )
        after = _request_json(f"http://127.0.0.1:{server.server_port}/api/config")
    finally:
        server.shutdown()
        server.server_close()

    assert before["exists"] is False
    assert saved["ok"] is True
    assert saved["path"] == str(tmp_path / ".magicmd.toml")
    assert after["exists"] is True
    assert after["config"]["output"]["directory"] == "articles"
    assert (tmp_path / ".magicmd.toml").read_text(encoding="utf-8") == (
        '[output]\ndirectory = "articles"\n'
    )


def test_studio_index_injects_request_token(tmp_path: Path):
    from magicmd.studio.server import create_studio_server

    token = "test-token"
    server = create_studio_server(host="127.0.0.1", port=0, cwd=tmp_path, token=token)
    _start_server(server)

    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=5) as response:
            html = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()

    assert "window.MAGICMD_STUDIO_TOKEN = 'test-token';" in html
    assert "__MAGICMD_STUDIO_TOKEN__" not in html


def test_studio_rejects_unauthorized_post_and_paths_outside_workspace(tmp_path: Path):
    from magicmd.studio.server import create_studio_server

    token = "test-token"
    server = create_studio_server(host="127.0.0.1", port=0, cwd=tmp_path, token=token)
    _start_server(server)

    try:
        status, payload = _request_json_error(
            f"http://127.0.0.1:{server.server_port}/api/config/save",
            {"path": ".magicmd.toml", "configText": '[output]\ndirectory = "ok"\n'},
        )
        outside_status, outside_payload = _request_json_error(
            f"http://127.0.0.1:{server.server_port}/api/config/save",
            {
                "path": "../outside.toml",
                "configText": '[output]\ndirectory = "ok"\n',
            },
            headers=_studio_headers(token),
        )
    finally:
        server.shutdown()
        server.server_close()

    assert status == 403
    assert payload == {"ok": False, "error": "Studio request token is invalid or missing"}
    assert outside_status == 400
    assert outside_payload == {"ok": False, "error": "路径必须位于 Studio 工作目录内"}
    assert not (tmp_path.parent / "outside.toml").exists()


def test_studio_open_path_endpoint_opens_existing_directory(tmp_path: Path):
    from magicmd.studio.server import StudioServices, create_studio_server

    token = "test-token"
    opened = []
    package_dir = tmp_path / "output" / "article"
    package_dir.mkdir(parents=True)

    def fake_open_path(path):
        opened.append(path)

    server = create_studio_server(
        host="127.0.0.1",
        port=0,
        cwd=tmp_path,
        token=token,
        services=StudioServices(open_path=fake_open_path),
    )
    _start_server(server)

    try:
        payload = _request_json(
            f"http://127.0.0.1:{server.server_port}/api/open-path",
            {"path": str(package_dir)},
            headers=_studio_headers(token),
        )
    finally:
        server.shutdown()
        server.server_close()

    assert payload == {"ok": True, "path": str(package_dir)}
    assert opened == [package_dir]


def test_studio_command_starts_local_console(monkeypatch):
    called = {}

    def fake_run_studio_server(**kwargs):
        announce = kwargs.pop("announce")
        called.update(kwargs)
        announce("http://127.0.0.1:9876")
        return "http://127.0.0.1:9876"

    monkeypatch.setattr("magicmd.cli.run_studio_server", fake_run_studio_server)

    result = runner.invoke(
        app,
        [
            "studio",
            "--host",
            "127.0.0.1",
            "--port",
            "0",
            "--no-open",
        ],
    )

    assert result.exit_code == 0
    assert "MagicMD Studio" in result.stdout
    assert "http://127.0.0.1:9876" in result.stdout
    assert called == {"host": "127.0.0.1", "port": 0, "open_browser": False}


def test_studio_static_assets_keep_accessible_workbench_details():
    html = resources.files("magicmd.studio").joinpath("index.html").read_text(encoding="utf-8")
    css = resources.files("magicmd.studio").joinpath("studio.css").read_text(encoding="utf-8")
    js = resources.files("magicmd.studio").joinpath("studio.js").read_text(encoding="utf-8")

    assert "<h2>转换工作台</h2>" in html
    assert "预览发布计划" in html
    assert 'id="rail-nav"' not in html
    assert 'class="rail"' not in html
    assert 'class="brand-mark"' not in html
    assert "data-scroll-target" not in html
    assert 'placeholder="https://mp.weixin.qq.com/s/…"' in html
    assert 'autocomplete="off"' in html
    assert ":focus-visible" in css
    assert "outline: none" not in css
    assert "[hidden]" in css
    assert "touch-action: manipulation" in css
    assert ".rail" not in css
    assert ".brand-mark" not in css
    assert "grid-template-columns: 68px" not in css
    assert "Intl.NumberFormat" in js
    assert 'id="batch-urls"' in html
    assert 'id="config-panel"' in html
    assert 'id="loading-state"' in html
    assert 'id="open-folder-toggle"' in html
    assert 'id="save-config-button"' in html
    assert "/api/batch" in js
    assert "/api/open-path" in js
    assert "/api/config/save" in js
    assert "X-MagicMD-Studio-Token" in js
    assert "allowFalseOk" in js
    assert "生成 .magicmd.toml" in html
    assert "Studio 后端需要重启" in js
    assert "当前 Studio 后端不支持自动打开目录" in js
    assert "scrollIntoView" not in js
    assert "setActiveRailLink" not in js
