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
