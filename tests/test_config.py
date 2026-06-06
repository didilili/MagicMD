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
