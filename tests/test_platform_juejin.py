from pathlib import Path

from magicmd.platforms.juejin import parse_juejin_html


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_juejin_html_extracts_basic_article():
    html = (FIXTURES / "juejin" / "basic.html").read_text(encoding="utf-8")

    article = parse_juejin_html(html, "https://juejin.cn/post/demo")

    assert article.title == "掘金文章标题"
    assert article.author == "Juejin Author"
    assert "掘金正文" in article.content_markdown
    assert article.images[0].source_url == "https://example.com/juejin.png"


def test_parse_juejin_html_prefers_rendered_body_over_article_shell():
    html = """
    <html><body>
      <article>
        <h1>程序员副业 | 2026年4月复盘</h1>
        <a class="author-name" href="/user/3368559354851470/posts">嘟嘟MD</a>
        <time datetime="2026-05-03">2026-05-03</time>
        <span>11,734</span>
        <span>阅读9分钟</span>
        <div class="markdown-body">
          <p>本文首发于公众号：嘟爷创业日记。</p>
          <h2>一、月度大事</h2>
          <p>这是正文。</p>
        </div>
      </article>
    </body></html>
    """

    article = parse_juejin_html(html, "https://juejin.cn/post/demo")

    assert article.title == "程序员副业 | 2026年4月复盘"
    assert article.author == "嘟嘟MD"
    assert article.published_at == "2026-05-03"
    assert "本文首发于公众号" in article.content_markdown
    assert "## 一、月度大事" in article.content_markdown
    assert "# 程序员副业" not in article.content_markdown
    assert "嘟嘟MD" not in article.content_markdown
    assert "11,734" not in article.content_markdown
    assert "阅读9分钟" not in article.content_markdown


def test_parse_juejin_html_extracts_team_author_name():
    html = """
    <html><body>
      <article>
        <h1>React + TypeScript实践</h1>
        <div class="container team-follow">
          <a href="/team/6930802337313210381/posts"><span class="title">字节前端</span></a>
          <time datetime="2021-04-19">2021-04-19</time>
        </div>
        <div class="markdown-body">
          <p>正文内容。</p>
        </div>
      </article>
    </body></html>
    """

    article = parse_juejin_html(html, "https://juejin.cn/post/team")

    assert article.author == "字节前端"
    assert article.published_at == "2021-04-19"
    assert "正文内容。" in article.content_markdown


def test_parse_juejin_html_cleans_code_copy_widget_prefixes():
    html = """
    <html><body>
      <article>
        <h1>掘金代码文章</h1>
        <a class="author-name">MagicMD</a>
        <div class="markdown-body">
          <pre><code>js复制代码import React from 'react'</code></pre>
          <pre><code>复制代码npm install</code></pre>
        </div>
      </article>
    </body></html>
    """

    article = parse_juejin_html(html, "https://juejin.cn/post/code")

    assert "复制代码" not in article.content_markdown
    assert "import React from 'react'" in article.content_markdown
    assert "npm install" in article.content_markdown


def test_parse_juejin_html_uses_link_title_as_direct_target_for_wrapped_external_links():
    html = """
    <html><body>
      <article>
        <h1>掘金链接文章</h1>
        <a class="author-name">MagicMD</a>
        <div class="markdown-body">
          <p>
            前端劝退指南：
            <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2Froger-hiro%2FBlogFN"
               title="https://github.com/roger-hiro/BlogFN">github.com/roger-hiro/...</a>
          </p>
          <p>
            参考
            <a href="https://link.juejin.cn?target=https%3A%2F%2Fvuejs.org%2Fguide"
               title="https://vuejs.org/guide">官方文档</a>
          </p>
        </div>
      </article>
    </body></html>
    """

    article = parse_juejin_html(html, "https://juejin.cn/post/link")

    assert "<https://github.com/roger-hiro/BlogFN>" in article.content_markdown
    assert "github.com/roger-hiro/..." not in article.content_markdown
    assert "[官方文档](https://vuejs.org/guide)" in article.content_markdown
    assert "link.juejin.cn?target=" not in article.content_markdown


def test_parse_juejin_html_normalizes_body_heading_depth_to_start_at_h2():
    html = """
    <html><body>
      <article>
        <h1>TypeScript高频面试题及解析</h1>
        <a class="author-name">MagicMD</a>
        <div class="markdown-body">
          <p>正文开头。</p>
          <h4>1. 什么是TypeScript</h4>
          <p>TypeScript 是一种语言。</p>
          <h5>1.1 类型系统</h5>
          <p>类型系统正文。</p>
          <h4>2. 类型声明和类型推断的区别</h4>
          <p>更多正文。</p>
          <h4>3. 什么是接口</h4>
          <p>接口正文。</p>
          <h3>结尾</h3>
          <p>结尾正文。</p>
        </div>
      </article>
    </body></html>
    """

    article = parse_juejin_html(html, "https://juejin.cn/post/7321542773076082699#heading-0")

    lines = article.content_markdown.splitlines()
    assert "## 1. 什么是TypeScript" in lines
    assert "### 1.1 类型系统" in lines
    assert "## 结尾" in lines
    assert "#### 1. 什么是TypeScript" not in lines
