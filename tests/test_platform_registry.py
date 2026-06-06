from magicmd.platforms.registry import get_platform_adapter, platform_names


def test_platform_registry_exposes_supported_platforms():
    assert platform_names() == ("wechat", "juejin", "csdn", "generic")


def test_platform_registry_keeps_adapter_details_together():
    adapter = get_platform_adapter("juejin")

    assert adapter.name == "juejin"
    assert "juejin.cn" in adapter.host_patterns
    assert adapter.default_browser == "camoufox"
    assert adapter.default_wait_selector == "article"
    assert adapter.parser.__name__ == "parse_juejin_html"
