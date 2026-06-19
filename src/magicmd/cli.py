from __future__ import annotations

import json
import shutil
import sys
from time import perf_counter
from importlib import resources
from pathlib import Path
from typing import Any, Optional

import typer
import click
from rich.console import Console
from rich.text import Text

from magicmd import __version__
from magicmd.config import GithubPublishConfig, load_config
from magicmd.detect import detect_platform
from magicmd.diagnostics import (
    build_doctor_json_payload,
    build_doctor_report,
    render_doctor_report,
)
from magicmd.exceptions import MagicMDError
from magicmd.fetchers.browser import fetch_browser
from magicmd.fetchers.http import fetch_http
from magicmd.i18n import ui_text
from magicmd.platforms.registry import get_platform_adapter
from magicmd.quality import (
    build_failure_quality,
    build_package_quality,
    build_skipped_quality,
    write_batch_report,
)
from magicmd.publish.models import GithubPublishOptions
from magicmd.publish.planner import build_github_publish_plan
from magicmd.sdk import convert_article, download_configured_media

app = typer.Typer(help="Convert public article links into Markdown packages.", no_args_is_help=True)
publish_app = typer.Typer(help="Publish converted article packages.")
app.add_typer(publish_app, name="publish")


def _version_callback(value: bool):
    if value:
        typer.echo(f"MagicMD {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show MagicMD version and exit.",
    ),
):
    return None


class ConversionStageError(click.ClickException):
    def __init__(self, stage: str, error: Exception):
        self.stage = stage
        self.original_error = error
        super().__init__(f"{stage}: {error}")


class ProgressReporter:
    def __init__(self, enabled: bool = False, console: Console | None = None):
        self.enabled = enabled
        self.console = console or Console(no_color=False)

    def run(self, index: int, total: int, message: str, operation):
        if not self.enabled:
            return operation()
        status_text = f"[cyan]⠋ [{index}/{total}] {message}...[/cyan]"
        with self.console.status(status_text, spinner="dots"):
            result = operation()
        line = Text()
        line.append("✓", style="green")
        line.append(f" [{index}/{total}] {message}")
        self.console.print(line)
        return result


def parse_article(platform: str, html: str, url: str):
    try:
        adapter = get_platform_adapter(platform)
    except KeyError:
        adapter = get_platform_adapter("generic")
    return adapter.parser(html, url)


def fetch_for_platform(url: str, platform: str, config_path: Optional[Path] = None) -> str:
    config = load_config(config_path)
    platform_config = config.platforms.get(platform)
    if platform_config and platform_config.browser == "camoufox":
        return fetch_browser(
            url,
            wait_selector=platform_config.wait_selector,
            timeout_ms=config.fetch.browser_timeout_seconds * 1000,
            attempts=config.fetch.browser_attempts,
        )
    return fetch_http(
        url, timeout_seconds=config.fetch.timeout_seconds, user_agent=config.fetch.user_agent
    )


def entrypoint():
    if len(sys.argv) > 1 and sys.argv[1].startswith(("http://", "https://")):
        sys.argv.insert(1, "convert")
    try:
        app(standalone_mode=False)
    except Exception as exc:
        if hasattr(exc, "show") and hasattr(exc, "exit_code"):
            exc.show()
            raise SystemExit(exc.exit_code) from exc
        raise


def _resolve_output(output: Path | None, config_path: Optional[Path]) -> Path:
    if output is not None:
        return output
    return Path(load_config(config_path).output.directory)


def _display_path(path: str | Path) -> str:
    return str(Path(path).expanduser().resolve())


def _batch_context(url: str, platform: str, config_path: Optional[Path]) -> dict[str, Any]:
    config = load_config(config_path)
    resolved_platform = detect_platform(url) if platform == "auto" else platform
    platform_config = config.platforms.get(resolved_platform)
    fetcher = platform_config.browser if platform_config else "http"
    max_attempts = config.fetch.browser_attempts if fetcher == "camoufox" else 1
    return {
        "platform": resolved_platform,
        "fetcher": fetcher,
        "max_attempts": max_attempts,
        "retry_enabled": max_attempts > 1,
    }


def _decorate_batch_result(
    item: dict[str, Any],
    context: dict[str, Any],
    elapsed_ms: int,
    stage: str,
) -> dict[str, Any]:
    result = dict(item)
    result.update(context)
    result["elapsed_ms"] = elapsed_ms
    result["stage"] = (
        _quality_failure_stage(result, stage) if result.get("status") == "fail" else stage
    )
    return result


def _quality_failure_stage(item: dict[str, Any], fallback: str) -> str:
    error = str(item.get("error") or "")
    if error.endswith("_content_not_found"):
        return "parse"
    return fallback


def _find_existing_package(
    output: Path,
    url: str,
    markdown_filename: str = "article.md",
    metadata_filename: str = "metadata.json",
) -> Path | None:
    if not output.exists():
        return None
    for metadata_path in sorted(output.rglob(metadata_filename)):
        package_dir = metadata_path.parent
        if not (package_dir / markdown_filename).exists():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(metadata, dict):
            continue
        if url in {metadata.get("source_url"), metadata.get("canonical_url")}:
            return package_dir
    return None


def convert_url(
    url: str,
    output: Path,
    platform: str = "auto",
    config_path: Optional[Path] = None,
    debug: bool = False,
    overwrite: bool = False,
    download_images_enabled: bool = True,
    docx: bool | None = None,
    show_progress: bool = False,
) -> Path:
    progress = ProgressReporter(show_progress)
    try:
        result = convert_article(
            url=url,
            platform=platform,
            output_dir=output,
            download_images=download_images_enabled,
            config_path=config_path,
            docx=docx,
            _fetch_for_platform=fetch_for_platform,
            _parse_article=parse_article,
            _progress=progress.run,
            _debug=debug,
            _overwrite=overwrite,
        )
    except MagicMDError as exc:
        raise ConversionStageError(exc.stage, exc) from exc
    if result.package_dir is None:
        raise ConversionStageError("write", RuntimeError("package_dir missing"))
    return Path(result.package_dir)


def _download_configured_media(article, package_dir: Path, config):
    return download_configured_media(article, package_dir, config)


def _resolve_docx_override(output_format: str) -> bool | None:
    normalized = output_format.strip().lower()
    if normalized in {"auto", ""}:
        return None
    if normalized in {"markdown", "md"}:
        return False
    if normalized in {"docx", "word"}:
        return True
    raise click.ClickException("--format must be one of: auto, markdown, docx")


def _resolve_github_publish_options(
    config_values: GithubPublishConfig,
    repo: str | None,
    target_dir: str | None,
    branch: str | None,
    commit_message: str | None,
    create_pr: bool,
    overwrite: bool,
) -> GithubPublishOptions:
    resolved_repo = repo or config_values.repo
    resolved_target_dir = target_dir or config_values.target_dir
    if not resolved_repo:
        raise click.ClickException("--repo is required unless [publish.github].repo is set")
    if not resolved_target_dir:
        raise click.ClickException(
            "--target-dir is required unless [publish.github].target_dir is set"
        )
    return GithubPublishOptions(
        repo=resolved_repo,
        target_dir=resolved_target_dir,
        branch=branch or config_values.branch,
        commit_message=commit_message or config_values.commit_message,
        create_pr=create_pr or config_values.create_pr,
        overwrite=overwrite or config_values.overwrite,
    )


def _render_publish_plan(plan) -> str:
    lines = [
        "Publish plan",
        f"Repository: {plan.repo}",
        f"Branch: {plan.branch}",
        f"Target directory: {plan.target_dir}",
        f"Commit message: {plan.commit_message}",
        f"Create PR: {plan.create_pr}",
        "Files:",
    ]
    for file in plan.files:
        lines.append(f"- {file.target_path} ({file.size_bytes} bytes)")
    lines.append("Dry run only: no remote writes were performed.")
    return "\n".join(lines)


@app.command()
def convert(
    url: str,
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory."),
    platform: str = typer.Option("auto", "--platform", help="auto, wechat, juejin, csdn, generic."),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path."),
    output_format: str = typer.Option(
        "auto",
        "--format",
        help="auto, markdown, docx. docx also keeps the Markdown package.",
    ),
    no_images: bool = typer.Option(False, "--no-images", help="Do not download images."),
    debug: bool = typer.Option(False, "--debug", help="Save debug HTML."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite output package."),
):
    resolved_output = _resolve_output(output, config_path)
    package_dir = convert_url(
        url,
        resolved_output,
        platform=platform,
        config_path=config_path,
        debug=debug,
        overwrite=overwrite,
        download_images_enabled=not no_images,
        docx=_resolve_docx_override(output_format),
        show_progress=True,
    )
    config = load_config(config_path)
    quality = build_package_quality(
        url,
        package_dir,
        markdown_filename=config.output.naming.markdown,
        metadata_filename=config.output.naming.metadata,
    )
    if quality["status"] == "fail":
        raise click.ClickException(
            "Extraction failed: "
            f"{quality.get('error')}. Debug package saved at: {_display_path(package_dir)}"
        )
    typer.echo(ui_text(config.ui.language, "created_package", path=_display_path(package_dir)))


@publish_app.command("github")
def publish_github(
    url: str,
    repo: Optional[str] = typer.Option(None, "--repo", help="GitHub repository owner/name."),
    target_dir: Optional[str] = typer.Option(None, "--target-dir", help="Repository target path."),
    branch: Optional[str] = typer.Option(None, "--branch", help="Publish branch template."),
    commit_message: Optional[str] = typer.Option(
        None, "--commit-message", help="Commit message template."
    ),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Local output directory."),
    platform: str = typer.Option("auto", "--platform", help="auto, wechat, juejin, csdn, generic."),
    no_images: bool = typer.Option(False, "--no-images", help="Do not download images."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview the publish plan only."),
    create_pr: bool = typer.Option(False, "--pr", help="Create a Pull Request after pushing."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite planned target files."),
):
    config = load_config(config_path)
    try:
        options = _resolve_github_publish_options(
            config.publish.github,
            repo,
            target_dir,
            branch,
            commit_message,
            create_pr,
            overwrite,
        )
    except click.ClickException as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    try:
        result = convert_article(
            url=url,
            platform=platform,
            output_dir=_resolve_output(output, config_path),
            download_images=not no_images,
            config_path=config_path,
            _fetch_for_platform=fetch_for_platform,
            _parse_article=parse_article,
        )
    except MagicMDError as exc:
        raise ConversionStageError(exc.stage, exc) from exc
    plan = build_github_publish_plan(result, options)
    if dry_run:
        typer.echo(_render_publish_plan(plan))
        return
    raise click.ClickException("Real GitHub publishing is not implemented yet. Use --dry-run.")


@app.command()
def batch(
    file: Path,
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory."),
    platform: str = typer.Option("auto", "--platform", help="auto, wechat, juejin, csdn, generic."),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path."),
    output_format: str = typer.Option(
        "auto",
        "--format",
        help="auto, markdown, docx. docx also keeps the Markdown package.",
    ),
    no_images: bool = typer.Option(False, "--no-images", help="Do not download images."),
    debug: bool = typer.Option(False, "--debug", help="Save debug HTML."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite output package."),
    skip_existing: bool = typer.Option(
        False, "--skip-existing", help="Skip URLs already present in output metadata."
    ),
):
    resolved_output = _resolve_output(output, config_path)
    urls = [
        line.strip()
        for line in file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    config = load_config(config_path)
    results = []
    for url in urls:
        started_at = perf_counter()
        context = _batch_context(url, platform, config_path)
        try:
            if skip_existing:
                existing_package = _find_existing_package(
                    resolved_output,
                    url,
                    markdown_filename=config.output.naming.markdown,
                    metadata_filename=config.output.naming.metadata,
                )
                if existing_package:
                    elapsed_ms = int((perf_counter() - started_at) * 1000)
                    results.append(
                        _decorate_batch_result(
                            build_skipped_quality(
                                url,
                                existing_package,
                                markdown_filename=config.output.naming.markdown,
                                metadata_filename=config.output.naming.metadata,
                            ),
                            context,
                            elapsed_ms,
                            "skip",
                        )
                    )
                    typer.echo(
                        ui_text(
                            config.ui.language,
                            "batch_skipped",
                            url=url,
                            path=_display_path(existing_package),
                        )
                    )
                    continue
            package_dir = convert_url(
                url,
                resolved_output,
                platform=platform,
                config_path=config_path,
                debug=debug,
                overwrite=overwrite,
                download_images_enabled=not no_images,
                docx=_resolve_docx_override(output_format),
                show_progress=True,
            )
            elapsed_ms = int((perf_counter() - started_at) * 1000)
            results.append(
                _decorate_batch_result(
                    build_package_quality(
                        url,
                        package_dir,
                        markdown_filename=config.output.naming.markdown,
                        metadata_filename=config.output.naming.metadata,
                    ),
                    context,
                    elapsed_ms,
                    "complete",
                )
            )
            typer.echo(
                ui_text(config.ui.language, "batch_ok", url=url, path=_display_path(package_dir))
            )
        except Exception as exc:
            elapsed_ms = int((perf_counter() - started_at) * 1000)
            stage = exc.stage if isinstance(exc, ConversionStageError) else "convert"
            results.append(
                _decorate_batch_result(
                    build_failure_quality(url, exc),
                    context,
                    elapsed_ms,
                    stage,
                )
            )
            typer.echo(ui_text(config.ui.language, "batch_failed", url=url, error=exc), err=True)
    report_paths = write_batch_report(results, resolved_output)
    typer.echo(
        ui_text(config.ui.language, "batch_report", path=_display_path(report_paths["markdown"]))
    )


config_app = typer.Typer(help="Manage MagicMD config.")
app.add_typer(config_app, name="config")


@config_app.command("init")
def config_init(path: Path = typer.Option(Path(".magicmd.toml"), "--path", help="Config path.")):
    if path.exists():
        typer.echo(f"Config already exists: {path}")
        return
    package_template = resources.files("magicmd").joinpath("templates/magicmd.example.toml")
    if package_template.is_file():
        path.write_text(package_template.read_text(encoding="utf-8"), encoding="utf-8")
        typer.echo(f"Created config: {path}")
        return
    example = Path(__file__).resolve().parents[2] / ".magicmd.example.toml"
    if example.exists():
        shutil.copyfile(example, path)
    else:
        path.write_text('[output]\ndirectory = "output"\n', encoding="utf-8")
    typer.echo(f"Created config: {path}")


@app.command()
def doctor(
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path."),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory to check."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
):
    report = build_doctor_report(config_path=config_path, output_dir=output)
    if json_output:
        typer.echo(json.dumps(build_doctor_json_payload(report), ensure_ascii=False, indent=2))
    else:
        typer.echo(render_doctor_report(report), nl=False)
    if not report["ok"]:
        typer.echo("MagicMD doctor found issues.", err=True)
        raise SystemExit(1)
