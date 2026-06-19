from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_config_builder_keeps_source_block_template_independent_from_cli_language():
    component = (ROOT / "website/.vitepress/components/ConfigBuilder.vue").read_text(
        encoding="utf-8"
    )

    assert "> 来源：{platform}" not in component
    assert "> 来源：" not in component
    assert "> Source: {platform}" in component
    assert "> Source:" in component


def test_config_builder_includes_docx_export_options():
    component = (ROOT / "website/.vitepress/components/ConfigBuilder.vue").read_text(
        encoding="utf-8"
    )

    assert 'docx = "article.docx"' in component
    assert "[docx]" in component
    assert 'pandoc_path = "pandoc"' in component


def test_config_builder_includes_wechat_cover_toggle():
    component = (ROOT / "website/.vitepress/components/ConfigBuilder.vue").read_text(
        encoding="utf-8"
    )

    assert "includeCoverImage" in component
    assert "include_cover_image = ${state.includeCoverImage}" in component
    assert "显示微信封面图" in component
    assert "Show WeChat cover image" in component
    assert "![cover](images/cover.jpg)" in component


def test_config_builder_desktop_layout_keeps_document_like_side_gutters():
    style = (ROOT / "website/.vitepress/theme/style.css").read_text(encoding="utf-8")

    assert ".VPDoc:has(._config-builder) .container" in style
    assert "width: min(1360px, calc(100vw - 96px));" in style
    assert "max-width: min(1360px, calc(100vw - 96px)) !important;" in style
    assert "calc(100vw - 80px)" not in style
