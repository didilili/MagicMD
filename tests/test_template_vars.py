import pytest

from magicmd.models import Article, ExtractionInfo
from magicmd.template_vars import build_article_template_vars, format_template


def make_article() -> Article:
    return Article(
        title="Codex 实战",
        author="HaoGit",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        canonical_url="https://example.com/canonical",
        published_at="2026-06-06T12:00:00+08:00",
        content_markdown="正文",
        content_hash="abcdef123456",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )


def test_build_article_template_vars():
    variables = build_article_template_vars(make_article())

    assert variables["title"] == "Codex 实战"
    assert variables["slug"] == "codex-实战"
    assert variables["date"] == "2026-06-06"
    assert variables["short_hash"] == "abcdef"


def test_format_template_raises_clear_error_for_unknown_field():
    with pytest.raises(ValueError, match="Unknown template field: missing"):
        format_template("{missing}", {"title": "demo"})
