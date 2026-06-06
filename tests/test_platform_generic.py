from pathlib import Path

from magicmd.platforms.generic import parse_generic_html


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_generic_html_uses_article_element():
    html = (FIXTURES / "generic" / "basic.html").read_text(encoding="utf-8")

    article = parse_generic_html(html, "https://example.com/a")

    assert article.title == "通用文章标题"
    assert article.author == "Generic Author"
    assert "通用正文" in article.content_markdown


def test_parse_generic_html_normalizes_body_heading_depth_to_start_at_h2():
    html = """
    <html><head><title>通用文章标题</title></head><body>
      <article>
        <h4>第一节</h4>
        <p>第一节正文。</p>
        <h5>第一小节</h5>
        <p>第一小节正文。</p>
      </article>
    </body></html>
    """

    article = parse_generic_html(html, "https://example.com/heading")

    lines = article.content_markdown.splitlines()
    assert "## 第一节" in lines
    assert "### 第一小节" in lines
    assert "#### 第一节" not in lines
