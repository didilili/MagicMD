from pathlib import Path
from importlib import resources

from magicmd.config import load_config


def test_load_config_merges_toml_file(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [output]
        directory = "articles"

        [images]
        download = false
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.output.directory == "articles"
    assert config.images.download is False
    assert config.images.directory == "images"


def test_load_config_accepts_browser_fetch_options(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [fetch]
        browser_timeout_seconds = 7
        browser_attempts = 4
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.fetch.browser_timeout_seconds == 7
    assert config.fetch.browser_attempts == 4


def test_load_config_accepts_v02_output_and_markdown_templates(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [output.naming]
        package = "{date}/{slug}"
        markdown = "index.md"
        metadata = "meta.json"
        report = "report.json"

        [markdown]
        preset = "hugo"
        front_matter = "yaml"
        include_title = false
        source_block_template = "> From: {source_url}"

        [markdown.front_matter_fields]
        title = "{title}"
        url = "{source_url}"

        [videos]
        download = false
        directory = "media/videos"
        filename_pattern = "clip_{index:03d}.{ext}"
        markdown_path = "../videos/{filename}"
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.output.naming.package == "{date}/{slug}"
    assert config.output.naming.markdown == "index.md"
    assert config.output.naming.metadata == "meta.json"
    assert config.output.naming.report == "report.json"
    assert config.markdown.preset == "hugo"
    assert config.markdown.include_title is False
    assert config.markdown.source_block_template == "> From: {source_url}"
    assert config.markdown.front_matter_fields == {
        "title": "{title}",
        "url": "{source_url}",
    }
    assert config.videos.download is False
    assert config.videos.directory == "media/videos"
    assert config.videos.filename_pattern == "clip_{index:03d}.{ext}"
    assert config.videos.markdown_path == "../videos/{filename}"


def test_default_platform_fetch_modes_match_live_validation_baseline():
    config = load_config()

    assert config.platforms["wechat"].browser == "camoufox"
    assert config.platforms["wechat"].wait_selector == "#js_content"
    assert config.platforms["csdn"].browser == "camoufox"
    assert config.platforms["csdn"].wait_selector == "#content_views"
    assert config.platforms["juejin"].browser == "camoufox"
    assert config.platforms["juejin"].wait_selector == "article"


def test_packaged_config_template_is_available():
    template = resources.files("magicmd").joinpath("templates/magicmd.example.toml")

    template_text = template.read_text(encoding="utf-8")

    assert template.is_file()
    assert "[platforms.wechat]" in template_text
    assert "[platforms.juejin]" in template_text
    assert "[platforms.csdn]" in template_text
    assert 'wait_selector = "article"' in template_text
    assert 'wait_selector = "#content_views"' in template_text
    assert "browser_timeout_seconds = 15" in template_text
    assert "browser_attempts = 2" in template_text
    assert "v0.2 design notes" in template_text
    assert "[output.naming]" in template_text
    assert "[markdown.front_matter_fields]" in template_text
