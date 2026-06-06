from __future__ import annotations

import shutil
import sys
from importlib import resources
from pathlib import Path
from typing import Optional

import typer
import click
from rich.console import Console
from rich.text import Text

from magicmd.config import load_config
from magicmd.detect import detect_platform
from magicmd.diagnostics import save_debug_html, save_extraction_report
from magicmd.fetchers.browser import fetch_browser
from magicmd.fetchers.http import fetch_http
from magicmd.output import write_article_files, write_article_package
from magicmd.platforms.registry import get_platform_adapter
from magicmd.quality import build_failure_quality, build_package_quality, write_batch_report

app = typer.Typer(help="Convert public article links into Markdown packages.", no_args_is_help=True)


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
    return fetch_http(url, timeout_seconds=config.fetch.timeout_seconds, user_agent=config.fetch.user_agent)


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


def _ensure_platform_enabled(platform: str, config_path: Optional[Path]) -> None:
    config = load_config(config_path)
    platform_config = config.platforms.get(platform)
    if platform_config and not platform_config.enabled:
        raise click.ClickException(f"Platform disabled: {platform}")


def _should_save_debug_html(debug: bool, save_mode: str, warnings: list[str]) -> bool:
    normalized = save_mode.lower()
    return debug or normalized == "always" or (normalized == "on_failure" and bool(warnings))


def convert_url(
    url: str,
    output: Path,
    platform: str = "auto",
    config_path: Optional[Path] = None,
    debug: bool = False,
    overwrite: bool = False,
    download_images_enabled: bool = True,
    show_progress: bool = False,
) -> Path:
    progress = ProgressReporter(show_progress)
    config = load_config(config_path)
    resolved_platform = progress.run(
        1,
        6,
        "Detecting platform",
        lambda: detect_platform(url) if platform == "auto" else platform,
    )
    _ensure_platform_enabled(resolved_platform, config_path)
    html = progress.run(
        2,
        6,
        f"Fetching article ({resolved_platform})",
        lambda: fetch_for_platform(url, resolved_platform, config_path),
    )
    article = progress.run(
        3,
        6,
        "Parsing article",
        lambda: parse_article(resolved_platform, html, url),
    )
    package_dir = progress.run(
        4,
        6,
        "Writing Markdown package",
        lambda: write_article_package(
            article,
            output,
            overwrite=overwrite or config.output.overwrite,
            markdown_config=config.markdown,
        ),
    )
    if _should_save_debug_html(debug, config.output.save_debug_html, article.extraction.warnings):
        save_debug_html(package_dir, html)
    if download_images_enabled and config.images.download:
        from magicmd.assets import download_images, download_videos

        article = progress.run(
            5,
            6,
            "Downloading media",
            lambda: download_videos(
                download_images(
                    article,
                    package_dir,
                    config.images.directory,
                    config.images.filename_pattern,
                ),
                package_dir,
            ),
        )
        write_article_files(article, package_dir, markdown_config=config.markdown)
    else:
        progress.run(5, 6, "Skipping image download", lambda: article)
    progress.run(
        6,
        6,
        "Saving extraction report",
        lambda: save_extraction_report(package_dir, article.to_metadata()["extraction"]),
    )
    return package_dir


@app.command()
def convert(
    url: str,
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory."),
    platform: str = typer.Option("auto", "--platform", help="auto, wechat, juejin, csdn, generic."),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path."),
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
        show_progress=True,
    )
    quality = build_package_quality(url, package_dir)
    if quality["status"] == "fail":
        raise click.ClickException(
            f"Extraction failed: {quality.get('error')}. Debug package saved at: {package_dir}"
        )
    typer.echo(f"Created output package: {package_dir}")


@app.command()
def batch(
    file: Path,
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory."),
    platform: str = typer.Option("auto", "--platform", help="auto, wechat, juejin, csdn, generic."),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path."),
    no_images: bool = typer.Option(False, "--no-images", help="Do not download images."),
    debug: bool = typer.Option(False, "--debug", help="Save debug HTML."),
):
    resolved_output = _resolve_output(output, config_path)
    urls = [
        line.strip()
        for line in file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    results = []
    for url in urls:
        try:
            package_dir = convert_url(
                url,
                resolved_output,
                platform=platform,
                config_path=config_path,
                debug=debug,
                download_images_enabled=not no_images,
                show_progress=True,
            )
            results.append(build_package_quality(url, package_dir))
            typer.echo(f"OK {url} -> {package_dir}")
        except Exception as exc:
            results.append(build_failure_quality(url, exc))
            typer.echo(f"FAIL {url}: {exc}", err=True)
    report_paths = write_batch_report(results, resolved_output)
    typer.echo(f"Batch report: {report_paths['markdown']}")


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
        path.write_text("[output]\ndirectory = \"output\"\n", encoding="utf-8")
    typer.echo(f"Created config: {path}")


@app.command()
def doctor():
    typer.echo("MagicMD doctor: ok")
