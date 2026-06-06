from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Optional

import typer

from pagemd.config import load_config
from pagemd.detect import detect_platform
from pagemd.diagnostics import save_debug_html, save_extraction_report
from pagemd.fetchers.browser import fetch_browser
from pagemd.fetchers.http import fetch_http
from pagemd.output import write_article_package
from pagemd.platforms.generic import parse_generic_html
from pagemd.platforms.csdn import parse_csdn_html
from pagemd.platforms.juejin import parse_juejin_html
from pagemd.platforms.wechat import parse_wechat_html

app = typer.Typer(help="Convert public article links into Markdown packages.", no_args_is_help=True)


def parse_article(platform: str, html: str, url: str):
    if platform == "wechat":
        return parse_wechat_html(html, url)
    if platform == "juejin":
        return parse_juejin_html(html, url)
    if platform == "csdn":
        return parse_csdn_html(html, url)
    return parse_generic_html(html, url)


def fetch_for_platform(url: str, platform: str, config_path: Optional[Path] = None) -> str:
    config = load_config(config_path)
    platform_config = config.platforms.get(platform)
    if platform_config and platform_config.browser == "camoufox":
        return fetch_browser(url, wait_selector=platform_config.wait_selector)
    return fetch_http(url, timeout_seconds=config.fetch.timeout_seconds, user_agent=config.fetch.user_agent)


def entrypoint():
    if len(sys.argv) > 1 and sys.argv[1].startswith(("http://", "https://")):
        package_dir = convert_url(sys.argv[1], Path("output"))
        typer.echo(f"Created output package: {package_dir}")
        return
    app()


def convert_url(
    url: str,
    output: Path,
    platform: str = "auto",
    config_path: Optional[Path] = None,
    debug: bool = False,
    overwrite: bool = False,
    download_images_enabled: bool = True,
) -> Path:
    config = load_config(config_path)
    resolved_platform = detect_platform(url) if platform == "auto" else platform
    html = fetch_for_platform(url, resolved_platform, config_path)
    article = parse_article(resolved_platform, html, url)
    package_dir = write_article_package(article, output, overwrite=overwrite or config.output.overwrite)
    if debug:
        save_debug_html(package_dir, html)
    if download_images_enabled and config.images.download:
        from pagemd.assets import download_images

        article = download_images(article, package_dir, config.images.directory)
        write_article_package(article, output, overwrite=True)
    save_extraction_report(package_dir, article.to_metadata()["extraction"])
    return package_dir


@app.command()
def convert(
    url: str,
    output: Path = typer.Option(Path("output"), "--output", "-o", help="Output directory."),
    platform: str = typer.Option("auto", "--platform", help="auto, wechat, juejin, csdn, generic."),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path."),
    no_images: bool = typer.Option(False, "--no-images", help="Do not download images."),
    debug: bool = typer.Option(False, "--debug", help="Save debug HTML."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite output package."),
):
    package_dir = convert_url(
        url,
        output,
        platform=platform,
        config_path=config_path,
        debug=debug,
        overwrite=overwrite,
        download_images_enabled=not no_images,
    )
    typer.echo(f"Created output package: {package_dir}")


@app.command()
def batch(
    file: Path,
    output: Path = typer.Option(Path("output"), "--output", "-o", help="Output directory."),
    platform: str = typer.Option("auto", "--platform", help="auto, wechat, juejin, csdn, generic."),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path."),
    no_images: bool = typer.Option(False, "--no-images", help="Do not download images."),
    debug: bool = typer.Option(False, "--debug", help="Save debug HTML."),
):
    urls = [
        line.strip()
        for line in file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    for url in urls:
        try:
            package_dir = convert_url(
                url,
                output,
                platform=platform,
                config_path=config_path,
                debug=debug,
                download_images_enabled=not no_images,
            )
            typer.echo(f"OK {url} -> {package_dir}")
        except Exception as exc:
            typer.echo(f"FAIL {url}: {exc}", err=True)


config_app = typer.Typer(help="Manage PageMD config.")
app.add_typer(config_app, name="config")


@config_app.command("init")
def config_init(path: Path = typer.Option(Path(".pagemd.toml"), "--path", help="Config path.")):
    if path.exists():
        typer.echo(f"Config already exists: {path}")
        return
    example = Path(__file__).resolve().parents[2] / ".pagemd.example.toml"
    if example.exists():
        shutil.copyfile(example, path)
    else:
        path.write_text("[output]\ndirectory = \"output\"\n", encoding="utf-8")
    typer.echo(f"Created config: {path}")


@app.command()
def doctor():
    typer.echo("PageMD doctor: ok")
