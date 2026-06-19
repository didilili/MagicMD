from pathlib import Path
from importlib import resources

import pytest

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


def test_load_config_defaults_cli_ui_language_to_chinese():
    config = load_config()

    assert config.ui.language == "zh-CN"


def test_load_config_accepts_cli_ui_language(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [ui]
        language = "en-US"
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.ui.language == "en-US"


def test_load_config_accepts_v02_output_and_markdown_templates(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [output.naming]
        package = "{date}/{slug}"
        markdown = "index.md"
        metadata = "meta.json"
        report = "report.json"
        docx = "article.docx"

        [markdown]
        preset = "hugo"
        front_matter = "yaml"
        include_title = false
        include_cover_image = false
        source_block_template = "> From: {source_url}"

        [markdown.front_matter_fields]
        title = "{title}"
        url = "{source_url}"

        [images]
        markdown_path = "../images/{filename}"

        [videos]
        download = false
        directory = "media/videos"
        filename_pattern = "clip_{index:03d}.{ext}"
        markdown_path = "../videos/{filename}"

        [docx]
        enabled = true
        pandoc_path = "/usr/local/bin/pandoc"
        reference_doc = "templates/reference.docx"
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.output.naming.package == "{date}/{slug}"
    assert config.output.naming.markdown == "index.md"
    assert config.output.naming.metadata == "meta.json"
    assert config.output.naming.report == "report.json"
    assert config.output.naming.docx == "article.docx"
    assert config.markdown.preset == "hugo"
    assert config.markdown.include_title is False
    assert config.markdown.include_cover_image is False
    assert config.markdown.source_block_template == "> From: {source_url}"
    assert config.markdown.front_matter_fields == {
        "title": "{title}",
        "url": "{source_url}",
    }
    assert config.images.markdown_path == "../images/{filename}"
    assert config.videos.download is False
    assert config.videos.directory == "media/videos"
    assert config.videos.filename_pattern == "clip_{index:03d}.{ext}"
    assert config.videos.markdown_path == "../videos/{filename}"
    assert config.docx.enabled is True
    assert config.docx.pandoc_path == "/usr/local/bin/pandoc"
    assert config.docx.reference_doc == "templates/reference.docx"


def test_load_config_disables_docx_by_default():
    config = load_config()

    assert config.docx.enabled is False
    assert config.output.naming.docx == "article.docx"


def test_load_config_accepts_publish_github_config(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [publish.github]
        repo = "didilili/content"
        target_dir = "content/posts"
        branch = "magicmd/{slug}"
        commit_message = "Add article: {title}"
        create_pr = true
        overwrite = true
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.publish.github.repo == "didilili/content"
    assert config.publish.github.target_dir == "content/posts"
    assert config.publish.github.branch == "magicmd/{slug}"
    assert config.publish.github.commit_message == "Add article: {title}"
    assert config.publish.github.create_pr is True
    assert config.publish.github.overwrite is True


def test_load_config_defaults_publish_github_to_disabled():
    config = load_config()

    assert config.publish.github.repo == ""
    assert config.publish.github.target_dir == ""
    assert config.publish.github.branch == "magicmd/{slug}"
    assert config.publish.github.commit_message == "Add article: {title}"
    assert config.publish.github.create_pr is False
    assert config.publish.github.overwrite is False


def test_load_config_includes_wechat_cover_image_by_default():
    config = load_config()

    assert config.markdown.include_cover_image is True


def test_load_config_applies_plain_preset(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [markdown]
        preset = "plain"
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.markdown.front_matter == "none"
    assert config.markdown.include_source_block is False
    assert config.markdown.include_cover_image is False


def test_load_config_applies_hugo_preset(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [markdown]
        preset = "hugo"
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.output.naming.markdown == "index.md"
    assert config.markdown.front_matter == "yaml"
    assert config.markdown.include_source_block is True


def test_load_config_preserves_explicit_values_over_preset(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [markdown]
        preset = "hugo"
        include_source_block = false

        [output.naming]
        markdown = "article.md"
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.output.naming.markdown == "article.md"
    assert config.markdown.include_source_block is False


def test_load_config_applies_docusaurus_preset(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [markdown]
        preset = "docusaurus"
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.output.naming.markdown == "index.md"
    assert config.markdown.front_matter == "yaml"
    assert config.markdown.include_source_block is False
    assert config.images.markdown_path == "./{directory}/{filename}"


def test_load_config_rejects_unknown_preset(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [markdown]
        preset = "mystery"
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown markdown preset: mystery"):
        load_config(config_path)


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
    assert "[ui]" in template_text
    assert 'language = "zh-CN"' in template_text
    assert "[output.naming]" in template_text
    assert 'package = "{date}-{slug}"' in template_text
    assert 'markdown = "article.md"' in template_text
    assert 'metadata = "metadata.json"' in template_text
    assert 'report = "extraction-report.json"' in template_text
    assert 'docx = "article.docx"' in template_text
    assert "[markdown.front_matter_fields]" in template_text
    assert "include_cover_image = true" in template_text
    assert "[videos]" in template_text
    assert 'markdown_path = "{directory}/{filename}"' in template_text
    assert "[docx]" in template_text
    assert "enabled = false" in template_text
    assert "[publish.github]" in template_text
    assert 'branch = "magicmd/{slug}"' in template_text
    assert 'commit_message = "Add article: {title}"' in template_text


def test_root_and_packaged_config_templates_match():
    root_template = Path(".magicmd.example.toml").read_text(encoding="utf-8")
    packaged_template = resources.files("magicmd").joinpath("templates/magicmd.example.toml")

    assert packaged_template.read_text(encoding="utf-8") == root_template


def test_example_config_template_loads():
    config = load_config(".magicmd.example.toml")

    assert config.output.naming.package == "{date}-{slug}"
    assert config.output.naming.markdown == "article.md"
    assert config.markdown.preset == "default"
    assert config.markdown.include_title is True
    assert config.markdown.include_cover_image is True
    assert config.markdown.front_matter_fields["source_url"] == "{source_url}"
    assert config.ui.language == "zh-CN"
    assert config.images.markdown_path == "{directory}/{filename}"
    assert config.videos.filename_pattern == "video_{index:03d}.{ext}"
    assert config.docx.enabled is False
