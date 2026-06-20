from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import webbrowser
from contextlib import contextmanager
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from magicmd import __version__
from magicmd.config import load_config
from magicmd.exceptions import MagicMDError
from magicmd.publish.errors import PublishError
from magicmd.publish.models import GithubPublishOptions
from magicmd.publish.planner import build_github_publish_plan
from magicmd.quality import build_package_quality
from magicmd.sdk import ArticleConversionResult, convert_article


Converter = Callable[..., ArticleConversionResult]
PathOpener = Callable[[Path], None]
Announcer = Callable[[str], None]


@dataclass(frozen=True)
class StudioServices:
    convert_article: Converter = convert_article
    open_path: PathOpener = lambda path: open_path_in_system(path)


class StudioRequestError(ValueError):
    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        self.status = status
        super().__init__(message)


class StudioHTTPServer(ThreadingHTTPServer):
    daemon_threads = True


def create_studio_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    cwd: Path | None = None,
    token: str | None = None,
    services: StudioServices | None = None,
) -> StudioHTTPServer:
    resolved_cwd = (cwd or Path.cwd()).expanduser().resolve()
    resolved_token = token or secrets.token_urlsafe(32)

    class Handler(StudioRequestHandler):
        studio_cwd = resolved_cwd
        studio_token = resolved_token
        studio_services = services or StudioServices()

    return StudioHTTPServer((host, port), Handler)


def run_studio_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    open_browser: bool = True,
    announce: Announcer | None = None,
) -> str:
    server = create_studio_server(host=host, port=port)
    url = _server_url(server, host)
    if announce:
        announce(url)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return url


class StudioRequestHandler(BaseHTTPRequestHandler):
    studio_cwd: Path
    studio_token: str
    studio_services: StudioServices

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/status":
            self._send_json(build_status_payload(self.studio_cwd))
            return
        if path == "/api/config":
            self._send_json(build_config_payload(self.studio_cwd))
            return
        if path in {"/", "/index.html"}:
            self._send_static("index.html", "text/html; charset=utf-8")
            return
        if path == "/studio.css":
            self._send_static("studio.css", "text/css; charset=utf-8")
            return
        if path == "/studio.js":
            self._send_static("studio.js", "text/javascript; charset=utf-8")
            return
        self._send_error_json("Not found", HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if not self._request_is_authorized():
            self._send_error_json(
                "Studio request token is invalid or missing",
                HTTPStatus.FORBIDDEN,
            )
            return
        try:
            payload = self._read_json_body()
            if path == "/api/convert":
                self._send_json(
                    convert_from_payload(payload, self.studio_cwd, self.studio_services)
                )
                return
            if path == "/api/batch":
                self._send_json(batch_from_payload(payload, self.studio_cwd, self.studio_services))
                return
            if path == "/api/publish/plan":
                self._send_json(
                    build_publish_plan_from_payload(payload, self.studio_cwd, self.studio_services)
                )
                return
            if path == "/api/open-path":
                self._send_json(
                    open_path_from_payload(payload, self.studio_cwd, self.studio_services)
                )
                return
            if path == "/api/config/save":
                self._send_json(save_config_from_payload(payload, self.studio_cwd))
                return
            self._send_error_json("Not found", HTTPStatus.NOT_FOUND)
        except StudioRequestError as exc:
            self._send_error_json(str(exc), exc.status)
        except (MagicMDError, PublishError, ValueError) as exc:
            self._send_error_json(str(exc), HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: Any) -> None:
        return None

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise StudioRequestError("Request body must be valid JSON") from exc
        if not isinstance(payload, dict):
            raise StudioRequestError("Request body must be a JSON object")
        return payload

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message: str, status: HTTPStatus) -> None:
        self._send_json({"ok": False, "error": message}, status)

    def _send_static(self, name: str, content_type: str) -> None:
        resource = resources.files("magicmd.studio").joinpath(name)
        if name == "index.html":
            body = (
                resource.read_text(encoding="utf-8")
                .replace("__MAGICMD_STUDIO_TOKEN__", self.studio_token)
                .encode("utf-8")
            )
        else:
            body = resource.read_bytes()
        self.send_response(HTTPStatus.OK.value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _request_is_authorized(self) -> bool:
        header_token = self.headers.get("X-MagicMD-Studio-Token", "")
        return bool(header_token) and secrets.compare_digest(header_token, self.studio_token)


def build_status_payload(cwd: Path) -> dict[str, Any]:
    config_path = cwd / ".magicmd.toml"
    return {
        "ok": True,
        "version": __version__,
        "cwd": str(cwd),
        "config": {
            "path": str(config_path),
            "exists": config_path.exists(),
        },
        "github": {
            "tokenConfigured": bool(os.environ.get("GITHUB_TOKEN")),
        },
    }


def build_config_payload(cwd: Path) -> dict[str, Any]:
    config_path = cwd / ".magicmd.toml"
    config = load_config(config_path)
    return {
        "ok": True,
        "path": str(config_path),
        "exists": config_path.exists(),
        "configText": config_path.read_text(encoding="utf-8") if config_path.exists() else "",
        "config": config.model_dump(mode="json"),
    }


def convert_from_payload(
    payload: dict[str, Any],
    cwd: Path,
    services: StudioServices,
) -> dict[str, Any]:
    url = _require_url(payload)
    output_dir = _resolve_path(payload.get("output") or "output", cwd)
    with _config_path_from_payload(payload, cwd) as config_path:
        result = services.convert_article(
            url=url,
            platform=str(payload.get("platform") or "auto"),
            output_dir=output_dir,
            download_images=bool(payload.get("downloadImages", True)),
            config_path=config_path,
            docx=_optional_bool(payload.get("docx")),
        )
    return _conversion_response(result)


def batch_from_payload(
    payload: dict[str, Any],
    cwd: Path,
    services: StudioServices,
) -> dict[str, Any]:
    urls = _batch_urls(payload)
    if not urls:
        raise StudioRequestError("请至少输入一条文章链接")
    output_dir = _resolve_path(payload.get("output") or "output", cwd)
    items: list[dict[str, Any]] = []
    with _config_path_from_payload(payload, cwd) as config_path:
        for url in urls:
            try:
                result = services.convert_article(
                    url=url,
                    platform=str(payload.get("platform") or "auto"),
                    output_dir=output_dir,
                    download_images=bool(payload.get("downloadImages", True)),
                    config_path=config_path,
                    docx=_optional_bool(payload.get("docx")),
                )
                item = _conversion_response(result)
                item["url"] = url
                items.append(item)
            except Exception as exc:
                items.append({"ok": False, "url": url, "error": str(exc)})
    success = sum(1 for item in items if item.get("ok") is True)
    failed = len(items) - success
    return {
        "ok": failed == 0,
        "summary": {"total": len(items), "success": success, "failed": failed},
        "items": items,
    }


def build_publish_plan_from_payload(
    payload: dict[str, Any],
    cwd: Path,
    services: StudioServices,
) -> dict[str, Any]:
    url = _require_url(payload)
    output_dir = _resolve_path(payload.get("output") or "output", cwd)
    with _config_path_from_payload(payload, cwd) as config_path:
        config = load_config(config_path)
        options = _resolve_github_publish_options(config.publish.github, payload)
        result = services.convert_article(
            url=url,
            platform=str(payload.get("platform") or "auto"),
            output_dir=output_dir,
            download_images=bool(payload.get("downloadImages", True)),
            config_path=config_path,
            docx=_optional_bool(payload.get("docx")),
        )
    plan = build_github_publish_plan(result, options)
    quality = build_package_quality(
        url,
        Path(plan.package_dir),
        markdown_filename=config.output.naming.markdown,
        metadata_filename=config.output.naming.metadata,
    )
    return {
        "ok": True,
        "repo": plan.repo,
        "targetDir": plan.target_dir,
        "branch": plan.branch,
        "commitMessage": plan.commit_message,
        "createPr": plan.create_pr,
        "overwrite": plan.overwrite,
        "title": plan.title,
        "platform": plan.platform,
        "sourceUrl": plan.source_url,
        "packageDir": plan.package_dir,
        "files": [
            {"targetPath": item.target_path, "sizeBytes": item.size_bytes} for item in plan.files
        ],
        "quality": quality,
    }


def open_path_from_payload(
    payload: dict[str, Any],
    cwd: Path,
    services: StudioServices,
) -> dict[str, Any]:
    value = str(payload.get("path") or "").strip()
    if not value:
        raise StudioRequestError("缺少要打开的路径")
    path = _resolve_path(value, cwd)
    if not path.exists():
        raise StudioRequestError(f"路径不存在：{path}", HTTPStatus.NOT_FOUND)
    services.open_path(path)
    return {"ok": True, "path": str(path)}


def save_config_from_payload(payload: dict[str, Any], cwd: Path) -> dict[str, Any]:
    config_text = str(payload.get("configText") or "")
    if not config_text.strip():
        raise StudioRequestError("配置内容不能为空")
    path = _resolve_path(payload.get("path") or ".magicmd.toml", cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(config_text)
        temp_path = Path(handle.name)
    try:
        config = load_config(temp_path)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)
    return {
        "ok": True,
        "path": str(path),
        "exists": True,
        "config": config.model_dump(mode="json"),
    }


def open_path_in_system(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
        return
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
        return
    subprocess.Popen(["xdg-open", str(path)])


def _conversion_response(result: ArticleConversionResult) -> dict[str, Any]:
    return {
        "ok": True,
        "title": result.title,
        "author": result.author,
        "platform": result.platform,
        "sourceUrl": result.source_url,
        "publishedAt": result.published_at,
        "packageDir": result.package_dir,
        "docxPath": result.docx_path,
        "warnings": result.warnings,
        "files": _package_files(Path(result.package_dir)) if result.package_dir else [],
    }


def _resolve_github_publish_options(
    config_values: Any, payload: dict[str, Any]
) -> GithubPublishOptions:
    repo = payload.get("repo") or config_values.repo
    target_dir = payload.get("targetDir") or payload.get("target_dir") or config_values.target_dir
    if not repo:
        raise StudioRequestError("请先在配置文件或界面里填写 GitHub 仓库，例如 owner/content")
    if not target_dir:
        raise StudioRequestError("请先填写发布目录，例如 content/posts")
    create_pr = payload.get("createPr")
    overwrite = payload.get("overwrite")
    return GithubPublishOptions(
        repo=_normalize_github_repo(str(repo)),
        target_dir=str(target_dir),
        branch=str(payload.get("branch") or config_values.branch),
        commit_message=str(payload.get("commitMessage") or config_values.commit_message),
        create_pr=config_values.create_pr if create_pr is None else bool(create_pr),
        overwrite=config_values.overwrite if overwrite is None else bool(overwrite),
    )


def _normalize_github_repo(repo: str) -> str:
    normalized = repo.strip()
    if normalized.startswith("https://github.com/"):
        normalized = normalized.removeprefix("https://github.com/").removesuffix(".git")
    elif normalized.startswith("http://github.com/"):
        normalized = normalized.removeprefix("http://github.com/").removesuffix(".git")
    elif normalized.startswith("git@github.com:"):
        normalized = normalized.removeprefix("git@github.com:").removesuffix(".git")
    normalized = normalized.strip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", normalized):
        raise StudioRequestError("GitHub 仓库请使用 owner/name 格式，例如 didilili/content")
    return normalized


def _batch_urls(payload: dict[str, Any]) -> list[str]:
    values = payload.get("urls")
    if isinstance(values, list):
        candidates = [str(value).strip() for value in values]
    else:
        candidates = [
            line.strip()
            for line in str(payload.get("batchText") or "").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    urls = []
    for value in candidates:
        if not value:
            continue
        if not value.startswith(("http://", "https://")):
            raise StudioRequestError(f"批量链接必须以 http:// 或 https:// 开头：{value}")
        urls.append(value)
    return urls


@contextmanager
def _config_path_from_payload(payload: dict[str, Any], cwd: Path):
    config_text = str(payload.get("configText") or "")
    if not config_text.strip():
        yield _optional_path(payload.get("config"), cwd)
        return

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=cwd,
        prefix=".magicmd-studio-",
        suffix=".toml",
        delete=False,
    ) as handle:
        handle.write(config_text)
        temp_path = Path(handle.name)
    try:
        yield temp_path
    finally:
        temp_path.unlink(missing_ok=True)


def _require_url(payload: dict[str, Any]) -> str:
    url = str(payload.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        raise StudioRequestError("请输入以 http:// 或 https:// 开头的文章链接")
    return url


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _optional_path(value: Any, cwd: Path) -> Path | None:
    if value in {None, ""}:
        return None
    return _resolve_path(value, cwd)


def _resolve_path(value: Any, cwd: Path) -> Path:
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = cwd / path
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(cwd)
    except ValueError as exc:
        raise StudioRequestError("路径必须位于 Studio 工作目录内") from exc
    return resolved


def _package_files(package_dir: Path) -> list[dict[str, Any]]:
    if not package_dir.exists():
        return []
    return [
        {
            "path": path.relative_to(package_dir).as_posix(),
            "sizeBytes": path.stat().st_size,
        }
        for path in sorted(package_dir.rglob("*"))
        if path.is_file()
    ]


def _server_url(server: ThreadingHTTPServer, host: str) -> str:
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    return f"http://{display_host}:{server.server_port}"
