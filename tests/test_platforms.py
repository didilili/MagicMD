from pathlib import Path

from pagemd.platforms.csdn import parse_csdn_html
from pagemd.platforms.generic import parse_generic_html
from pagemd.platforms.juejin import parse_juejin_html
from pagemd.platforms.wechat import parse_wechat_html


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_wechat_html_extracts_title_author_body_and_images():
    html = (FIXTURES / "wechat" / "basic.html").read_text(encoding="utf-8")

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/demo")

    assert article.title == "微信文章标题"
    assert article.author == "PageMD"
    assert article.platform == "wechat"
    assert "第一段正文" in article.content_markdown
    assert 'print("hello")' in article.content_markdown
    assert article.images[0].source_url == "https://example.com/wechat.png"


def test_parse_juejin_html_extracts_basic_article():
    html = (FIXTURES / "juejin" / "basic.html").read_text(encoding="utf-8")

    article = parse_juejin_html(html, "https://juejin.cn/post/demo")

    assert article.title == "掘金文章标题"
    assert article.author == "Juejin Author"
    assert "掘金正文" in article.content_markdown
    assert article.images[0].source_url == "https://example.com/juejin.png"


def test_parse_generic_html_uses_article_element():
    html = (FIXTURES / "generic" / "basic.html").read_text(encoding="utf-8")

    article = parse_generic_html(html, "https://example.com/a")

    assert article.title == "通用文章标题"
    assert article.author == "Generic Author"
    assert "通用正文" in article.content_markdown


def test_parse_csdn_html_extracts_basic_article():
    html = (FIXTURES / "csdn" / "basic.html").read_text(encoding="utf-8")

    article = parse_csdn_html(html, "https://blog.csdn.net/demo/article/details/1")

    assert article.title == "CSDN 文章标题"
    assert article.author == "CSDN Author"
    assert article.platform == "csdn"
    assert "CSDN 正文" in article.content_markdown
    assert article.images[0].source_url == "https://example.com/csdn.png"
