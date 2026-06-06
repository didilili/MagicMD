from pagemd.models import Article, ExtractionInfo
from pagemd.renderers.markdown import render_markdown


def test_render_markdown_includes_front_matter_and_source_block():
    article = Article(
        title="Codex 实战",
        author="HaoGit",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-06T12:00:00+08:00",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    md = render_markdown(article)

    assert 'title: "Codex 实战"' in md
    assert 'platform: "wechat"' in md
    assert "# Codex 实战" in md
    assert "> Original: https://mp.weixin.qq.com/s/demo" in md
    assert md.rstrip().endswith("正文")

