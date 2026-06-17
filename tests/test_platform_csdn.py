from pathlib import Path

from magicmd.platforms.csdn import parse_csdn_html


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_csdn_html_extracts_basic_article():
    html = (FIXTURES / "csdn" / "basic.html").read_text(encoding="utf-8")

    article = parse_csdn_html(html, "https://blog.csdn.net/demo/article/details/1")

    assert article.title == "CSDN 文章标题"
    assert article.author == "CSDN Author"
    assert article.platform == "csdn"
    assert "CSDN 正文" in article.content_markdown
    assert article.images[0].source_url == "https://example.com/csdn.png"


def test_parse_csdn_html_normalizes_body_heading_depth_to_start_at_h2():
    html = """
    <html><body>
      <h1 class="title-article">CSDN 标题文章</h1>
      <div id="content_views">
        <h3>一、准备工作</h3>
        <p>准备正文。</p>
        <h4>1. 安装依赖</h4>
        <p>安装正文。</p>
      </div>
    </body></html>
    """

    article = parse_csdn_html(html, "https://blog.csdn.net/demo/article/details/heading")

    lines = article.content_markdown.splitlines()
    assert "## 一、准备工作" in lines
    assert "### 1. 安装依赖" in lines
    assert "### 一、准备工作" not in lines


def test_parse_csdn_html_cleans_code_widget_noise():
    html = """
    <html><body>
      <h1 class="title-article">CSDN 代码文章</h1>
      <div class="article-info-box">
        <span class="time">已于&nbsp;2024-10-25 17:19:43&nbsp;修改</span>
        <div class="up-time">于&nbsp;2024-10-25 17:19:23&nbsp;首次发布</div>
      </div>
      <div id="content_views">
        <p>正文前。</p>
        <pre class="new-version set-code-height set-code-hide prettyprint" data-index="0" name="code">
          <code class="has-numbering">print("hello")
print("world")</code>
          <div class="opt-box"><button class="btn-code-notes">一键获取完整项目代码</button></div>
          <div class="hide-preCode-box">
            <img class="look-more-preCode contentImg-no-view"
                 src="https://csdnimg.cn/release/blogv2/dist/pc/img/runCode/icon-arrowwhite.png" />
          </div>
          <ul class="pre-numbering"><li>1</li><li>2</li></ul>
        </pre>
        <pre><code>counter(line)</code></pre>
        <p>正文后。</p>
      </div>
    </body></html>
    """

    article = parse_csdn_html(html, "https://blog.csdn.net/demo/article/details/2")

    assert article.published_at == "2024-10-25 17:19:23"
    assert 'print("hello")' in article.content_markdown
    assert 'print("world")' in article.content_markdown
    assert "counter(line)" not in article.content_markdown
    assert "AI写代码" not in article.content_markdown
    assert "一键获取完整项目代码" not in article.content_markdown
    assert "icon-arrowwhite.png" not in article.content_markdown
    assert "\n- 1\n- 2\n" not in article.content_markdown
    assert "```\n```" not in article.content_markdown


def test_parse_csdn_html_preserves_highlighted_code_line_breaks():
    html = """
    <html><body>
      <h1 class="title-article">CSDN 高亮代码文章</h1>
      <div id="content_views">
        <p>正文前。</p>
        <pre class="has new-version hljs set-code-show" data-index="0" name="code">
          <code class="language-python hljs">
            <ol class="hljs-ln">
              <li>
                <div class="hljs-ln-numbers"><div class="hljs-ln-line hljs-ln-n" data-line-number="1"></div></div>
                <div class="hljs-ln-code"><div class="hljs-ln-line"><span class="hljs-keyword">def</span> <span class="hljs-title">foo</span>():</div></div>
              </li>
              <li>
                <div class="hljs-ln-numbers"><div class="hljs-ln-line hljs-ln-n" data-line-number="2"></div></div>
                <div class="hljs-ln-code"><div class="hljs-ln-line">    <span class="hljs-built_in">print</span>(<span class="hljs-string">"starting..."</span>)</div></div>
              </li>
              <li>
                <div class="hljs-ln-numbers"><div class="hljs-ln-line hljs-ln-n" data-line-number="3"></div></div>
                <div class="hljs-ln-code"><div class="hljs-ln-line">    <span class="hljs-keyword">while</span> <span class="hljs-literal">True</span>:</div></div>
              </li>
              <li>
                <div class="hljs-ln-numbers"><div class="hljs-ln-line hljs-ln-n" data-line-number="4"></div></div>
                <div class="hljs-ln-code"><div class="hljs-ln-line">        res = <span class="hljs-keyword">yield</span> <span class="hljs-number">4</span></div></div>
              </li>
            </ol>
          </code>
          <div class="opt-box"><span class="code-language" data-language="python">python</span></div>
        </pre>
      </div>
    </body></html>
    """

    article = parse_csdn_html(html, "https://blog.csdn.net/demo/article/details/highlighted-code")

    assert (
        'def foo():\n    print("starting...")\n    while True:\n        res = yield 4'
        in article.content_markdown
    )
    assert 'def foo():    print("starting...")' not in article.content_markdown


def test_parse_csdn_html_splits_joined_code_statements():
    html = """
    <html><body>
      <h1 class="title-article">CSDN 粘连代码文章</h1>
      <div id="content_views">
        <pre class="has new-version hljs set-code-show" data-index="0" name="code">
          <code class="language-python">conda&nbsp;create -n pytorch_env python=3.11conda&nbsp;activate pytorch_env
print(x.reshape(6, 4).shape)print(x.unsqueeze(0).shape)</code>
        </pre>
      </div>
    </body></html>
    """

    article = parse_csdn_html(html, "https://blog.csdn.net/demo/article/details/joined-code")

    assert "python=3.11\nconda activate pytorch_env" in article.content_markdown
    assert "print(x.reshape(6, 4).shape)\nprint(x.unsqueeze(0).shape)" in article.content_markdown


def test_parse_csdn_html_keeps_later_code_blocks_from_placeholder_collision():
    pre_blocks = "\n".join(
        f"""
        <p>代码块 {index}</p>
        <pre class="new-version prettyprint" data-index="{index}" name="code">
          <code class="language-bash">echo block-{index}</code>
          <div class="opt-box"><span class="code-language" data-language="bash">bash</span></div>
          <ul class="pre-numbering"><li>1</li></ul>
        </pre>
        """
        for index in range(11)
    )
    html = f"""
    <html><body>
      <h1 class="title-article">CSDN 多代码块文章</h1>
      <div id="content_views">{pre_blocks}</div>
    </body></html>
    """

    article = parse_csdn_html(html, "https://blog.csdn.net/demo/article/details/many-code-blocks")

    assert "echo block-1\n```\n0" not in article.content_markdown
    assert "echo block-10" in article.content_markdown
    assert "echo block-9" in article.content_markdown
    assert "```bash\n" in article.content_markdown


def test_parse_csdn_html_removes_generated_toc_with_dead_internal_links():
    html = """
    <html><body>
      <h1 class="title-article">CSDN 目录文章</h1>
      <div id="content_views">
        <div class="toc">
          <h4><a name="t1"></a>文章目录</h4>
          <ul><li><a href="#__28" target="_self">第一节</a></li></ul>
        </div>
        <h2><a id="__28"></a>第一节</h2>
        <p>正文。</p>
      </div>
    </body></html>
    """

    article = parse_csdn_html(html, "https://blog.csdn.net/demo/article/details/toc")

    assert "文章目录" not in article.content_markdown
    assert "](#__28)" not in article.content_markdown
    assert "## 第一节" in article.content_markdown
    assert "正文。" in article.content_markdown


def test_parse_csdn_html_preserves_mermaid_svg_as_raw_html():
    html = """
    <html><body>
      <h1 class="title-article">CSDN Mermaid 文章</h1>
      <div id="content_views">
        <h4>🧐 排查流程图</h4>
        <div class="mermaid mermaid-newversion mermaid-flowchart">
          <svg class="flowchart" viewBox="0 0 100 40" xmlns="http://www.w3.org/2000/svg">
            <text>ALL / index</text>
            <path d="M 1 1 L 99 39"></path>
          </svg>
        </div>
      </div>
    </body></html>
    """

    article = parse_csdn_html(html, "https://blog.csdn.net/demo/article/details/mermaid")

    assert '<div class="mermaid mermaid-newversion mermaid-flowchart">' in article.content_markdown
    assert "<svg" in article.content_markdown
    assert "ALL / index\n\n" not in article.content_markdown
