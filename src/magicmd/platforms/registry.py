from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from magicmd.models import Article
from magicmd.platforms.csdn import parse_csdn_html
from magicmd.platforms.generic import parse_generic_html
from magicmd.platforms.juejin import parse_juejin_html
from magicmd.platforms.wechat import parse_wechat_html


@dataclass(frozen=True)
class PlatformAdapter:
    name: str
    host_patterns: tuple[str, ...]
    default_browser: str
    default_wait_selector: str
    parser: Callable[[str, str], Article]


_ADAPTERS: tuple[PlatformAdapter, ...] = (
    PlatformAdapter(
        name="wechat",
        host_patterns=("mp.weixin.qq.com",),
        default_browser="camoufox",
        default_wait_selector="#js_content",
        parser=parse_wechat_html,
    ),
    PlatformAdapter(
        name="juejin",
        host_patterns=("juejin.cn",),
        default_browser="camoufox",
        default_wait_selector="article",
        parser=parse_juejin_html,
    ),
    PlatformAdapter(
        name="csdn",
        host_patterns=("csdn.net",),
        default_browser="camoufox",
        default_wait_selector="#content_views",
        parser=parse_csdn_html,
    ),
    PlatformAdapter(
        name="generic",
        host_patterns=(),
        default_browser="http",
        default_wait_selector="",
        parser=parse_generic_html,
    ),
)

_ADAPTER_BY_NAME = {adapter.name: adapter for adapter in _ADAPTERS}


def platform_adapters() -> tuple[PlatformAdapter, ...]:
    return _ADAPTERS


def platform_names() -> tuple[str, ...]:
    return tuple(adapter.name for adapter in _ADAPTERS)


def get_platform_adapter(name: str) -> PlatformAdapter:
    return _ADAPTER_BY_NAME[name]


def match_platform_by_host(host: str) -> str:
    normalized_host = host.lower()
    for adapter in _ADAPTERS:
        if any(pattern in normalized_host for pattern in adapter.host_patterns):
            return adapter.name
    return "generic"
