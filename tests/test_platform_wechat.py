from pathlib import Path

import pytest

from magicmd.platforms.shared.content import _normalize_code_text
from magicmd.platforms.wechat import parse_wechat_html


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_wechat_html_extracts_title_author_body_and_images():
    html = (FIXTURES / "wechat" / "basic.html").read_text(encoding="utf-8")

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/demo")

    assert article.title == "微信文章标题"
    assert article.author == "MagicMD"
    assert article.platform == "wechat"
    assert "第一段正文" in article.content_markdown
    assert 'print("hello")' in article.content_markdown
    assert article.images[0].source_url == "https://example.com/wechat.png"


def test_parse_wechat_html_extracts_cover_images_from_metadata_and_scripts():
    html = """
    <html>
      <head>
        <meta property="og:image" content="http://mmbiz.qpic.cn/cover/0?wx_fmt=jpeg" />
        <script>
          var msg_cdn_url = "http://mmbiz.qpic.cn/fallback/0?wx_fmt=jpeg";
          var cdn_url_1_1 = "http://mmbiz.qpic.cn/share/0?wx_fmt=png";
        </script>
      </head>
      <body>
        <h1 id="activity-name">带封面文章</h1>
        <div id="js_content"><p>正文</p></div>
      </body>
    </html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/cover")

    assert article.cover_image is not None
    assert article.cover_image.source_url == "https://mmbiz.qpic.cn/cover/0?wx_fmt=jpeg"
    assert article.share_cover_image is not None
    assert article.share_cover_image.source_url == "https://mmbiz.qpic.cn/share/0?wx_fmt=png"
    assert "cover/0" not in article.content_markdown


def test_parse_wechat_html_prefers_wechat_wide_cover_over_square_open_graph_image():
    html = """
    <html>
      <head>
        <meta property="og:image" content="https://mmbiz.qpic.cn/square/0?wx_fmt=jpeg" />
        <script>
          var msg_cdn_url = "https://mmbiz.qpic.cn/square/0?wx_fmt=jpeg";
          var cdn_url_1_1 = "https://mmbiz.qpic.cn/square/0?wx_fmt=jpeg";
          cdn_url_235_1 = "https://mmbiz.qpic.cn/wide/0?wx_fmt=jpeg";
        </script>
      </head>
      <body>
        <h1 id="activity-name">横版封面文章</h1>
        <div id="js_content"><p>正文</p></div>
      </body>
    </html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/wide-cover")

    assert article.cover_image is not None
    assert article.cover_image.source_url == "https://mmbiz.qpic.cn/wide/0?wx_fmt=jpeg"
    assert article.share_cover_image is not None
    assert article.share_cover_image.source_url == "https://mmbiz.qpic.cn/square/0?wx_fmt=jpeg"


def test_parse_wechat_html_uses_msg_cdn_url_when_open_graph_cover_is_missing():
    html = """
    <html>
      <head>
        <script>
          var msg_cdn_url = "http://mmbiz.qpic.cn/script-cover/0?wx_fmt=jpeg";
        </script>
      </head>
      <body>
        <h1 id="activity-name">脚本封面文章</h1>
        <div id="js_content"><p>正文</p></div>
      </body>
    </html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/script-cover")

    assert article.cover_image is not None
    assert article.cover_image.source_url == ("https://mmbiz.qpic.cn/script-cover/0?wx_fmt=jpeg")
    assert article.share_cover_image is None


def test_parse_wechat_html_normalizes_rich_sections_styles_and_images():
    html = """
    <html>
      <body>
        <h1 id="activity-name">富文本文章</h1>
        <a id="js_name">MagicMD</a>
        <div id="js_content">
          <section>
            <section style="font-size: 14px;">
              <span style="font-weight: bold;">现在，ChatGPT 的记忆系统更像人了。</span>
            </section>
            <p>OpenAI 近期推出了一套全新的记忆系统。</p>
            <section style="font-weight: 600; font-size: 21px; color:#FD4606;">
              不再从零开始，ChatGPT 全新记忆系统登场
            </section>
            <section><strong>01</strong></section>
            <section><strong>把代码变成知识图谱</strong></section>
            <section style="font-weight: 600; font-size: 21px; color:#00B38B;">
              3<strong>GPU 之外，视频模型还有一张更贵的账单</strong>
            </section>
            <section style="margin-left: 8px; margin-right: 8px; line-height: 2em; margin-bottom: 16px;">
              <strong><span style="font-weight: bold;">andrej-karpathy-skills：</span>根据 Karpathy 观察 LLM 写代码的坑。</strong>
            </section>
            <section style="margin-left: 8px; margin-right: 8px; line-height: 2em; margin-bottom: 16px;">
              <strong><span style="font-weight: bold;">mattpocock/skills：</span>Claude Code 技能包。</strong>
            </section>
            <section><img data-src="https://example.com/cover.png" /></section>
            <section>图片后的下一行文字。</section>
          </section>
        </div>
      </body>
    </html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/rich")

    assert "**现在，ChatGPT 的记忆系统更像人了。**" in article.content_markdown
    assert "## 不再从零开始，ChatGPT 全新记忆系统登场" in article.content_markdown
    assert "## 01 把代码变成知识图谱" in article.content_markdown
    assert "## 3 GPU 之外，视频模型还有一张更贵的账单" in article.content_markdown
    assert (
        "根据 Karpathy 观察 LLM 写代码的坑。**\n\n**mattpocock/skills：" in article.content_markdown
    )
    assert (
        "![Image](https://example.com/cover.png)\n\n图片后的下一行文字。"
        in article.content_markdown
    )


def test_parse_wechat_html_merges_plain_section_number_with_detected_heading():
    html = """
    <html><body>
      <h1 id="activity-name">章节序号文章</h1>
      <div id="js_content">
        <section>01</section>
        <section style="font-size: 22px; font-weight: 700;">概要</section>
        <p>第一节正文。</p>
        <section>02</section>
        <section style="font-size: 22px; font-weight: 700;">02 全文</section>
        <p>第二节正文。</p>
        <section>2026</section>
        <section style="font-size: 22px; font-weight: 700;">未来</section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/plain-section-number")

    assert article.content_markdown == (
        "## 01 概要\n\n第一节正文。\n\n## 02 全文\n\n第二节正文。\n\n2026\n\n## 未来"
    )


def test_parse_wechat_html_splits_section_number_stuck_to_image_caption():
    html = """
    <html><body>
      <h1 id="activity-name">图片说明章节序号文章</h1>
      <div id="js_content">
        <section><img data-src="https://example.com/ranking.png" /></section>
        <section>AA 排名<span>04</span></section>
        <section style="font-size: 22px; font-weight: 700;">大模型的味道</section>
        <section><img data-src="https://example.com/report.png" /></section>
        <section>年度报告2026</section>
        <section style="font-size: 22px; font-weight: 700;">未来</section>
        <section><img data-src="https://example.com/figure.png" /></section>
        <section>图 24</section>
        <section style="font-size: 22px; font-weight: 700;">附录</section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/image-caption-section-number")

    assert article.content_markdown == (
        "![Image](https://example.com/ranking.png)\n\n"
        "AA 排名\n\n## 04 大模型的味道\n\n"
        "![Image](https://example.com/report.png)\n\n"
        "年度报告2026\n\n## 未来\n\n"
        "![Image](https://example.com/figure.png)\n\n"
        "图 24\n\n## 附录"
    )


def test_parse_wechat_html_closes_skipped_body_heading_levels():
    html = """
    <html><body>
      <h1 id="activity-name">营销 Skills</h1>
      <div id="js_content">
        <h2>功能详情</h2>
        <h4>所有 Skill 先读同一份产品档案</h4>
        <h5>产品档案内容</h5>
        <h4>转化率优化拆得很细</h4>
        <h3>快速开始</h3>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/skipped-heading")

    lines = article.content_markdown.splitlines()
    assert "## 功能详情" in lines
    assert "### 所有 Skill 先读同一份产品档案" in lines
    assert "#### 产品档案内容" in lines
    assert "### 转化率优化拆得很细" in lines
    assert "### 快速开始" in lines


def test_parse_wechat_html_separates_bold_label_from_following_text():
    html = """
    <html><body>
      <h1 id="activity-name">加粗标签文章</h1>
      <div id="js_content">
        <p><strong>① headroom:</strong>压缩 LLM 输入，比如工具输出、日志、RAG chunks。</p>
        <p><strong>② addyosmani/agent-skills: </strong>Google 工程师整理的 AI 编码 Skills 合集。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/bold-label")

    assert "**① headroom:**压缩" not in article.content_markdown
    assert "**② addyosmani/agent-skills: **Google" not in article.content_markdown
    assert "**① headroom:** 压缩 LLM 输入" in article.content_markdown
    assert "**② addyosmani/agent-skills:** Google 工程师" in article.content_markdown


def test_parse_wechat_html_normalizes_nbsp_and_fused_command_in_code_snippet():
    html = """
    <html><body>
      <h1 id="activity-name">代码空格文章</h1>
      <div id="js_content">
        <div class="code-snippet__fix">
          <pre data-lang="shell"><code># 安装到全局npm&nbsp;install -g demo</code></pre>
        </div>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/code-whitespace")

    assert article.content_markdown == ("```shell\n# 安装到全局\nnpm install -g demo\n```")


def test_parse_wechat_html_preserves_br_line_breaks_in_wechat_code_snippet():
    html = (
        '<html><body><h1 id="activity-name">微信代码片段换行文章</h1>'
        '<div id="js_content"><div class="code-snippet__fix">'
        '<pre data-lang="javascript"><code>'
        "<span>const styles = stylex.create({</span><br />"
        "<span>&nbsp;&nbsp;card: {</span><br />"
        "<span>&nbsp;&nbsp;&nbsp;&nbsp;padding: 16,</span><br />"
        "<span>&nbsp;&nbsp;},</span><br />"
        "<span>});</span>"
        "</code></pre></div></div></body></html>"
    )

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/code-snippet-breaks")

    assert article.content_markdown == (
        "```javascript\nconst styles = stylex.create({\n  card: {\n    padding: 16,\n  },\n});\n```"
    )


def test_parse_wechat_html_preserves_br_line_breaks_in_mdnice_code_block():
    html = (
        '<html><body><h1 id="activity-name">mdnice 代码文章</h1><div id="js_content">'
        '<pre data-tool="mdnice编辑器"><code>'
        "<span>import</span><span>&nbsp;*&nbsp;</span><span>as</span><span>&nbsp;stylex&nbsp;</span>"
        "<span>from</span><span>&nbsp;'@stylexjs/stylex';</span><span><br /></span>"
        "<span><br /></span>"
        "<span>const styles = stylex.create({</span><span><br /></span>"
        "<span>&nbsp;&nbsp;</span><span>&lt;</span><span>div</span><span>&gt;</span><span><br /></span>"
        "<span>&nbsp;&nbsp;</span><span>&lt;/</span><span>div</span><span>&gt;</span>"
        "</code></pre></div></body></html>"
    )

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/mdnice-code-breaks")

    assert article.content_markdown == (
        "```\n"
        "import * as stylex from '@stylexjs/stylex';\n\n"
        "const styles = stylex.create({\n"
        "  <div>\n"
        "  </div>\n"
        "```"
    )


def test_parse_wechat_html_preserves_scrollable_text_panel_as_text_fence():
    html = """
    <html><body>
      <h1 id="activity-name">滚动提示词文章</h1>
      <div id="js_content">
        <section data-tools="135编辑器" data-id="85709">
          <section style="background: #f5f5f4; padding: 1em 0;">
            <section data-brushtype="text"><strong>提示词（可上下滚动）</strong></section>
            <section style="height: 180px; overflow-x: hidden; overflow-y: scroll;">
              <section data-autoskip="1">
                <p>在 Django 部署了两个应用：</p>
                <p><br /></p>
                <p>/myapp/ → 应用 A</p>
                <p>/myapplication/ → 应用 B</p>
                <p><br /></p>
                <p>你帮我看看是怎么回事？</p>
              </section>
            </section>
          </section>
        </section>
        <p>提示词后的正文。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/scrollable-text-panel")

    assert article.content_markdown == (
        "**提示词（可上下滚动）**\n\n"
        "```text\n"
        "在 Django 部署了两个应用：\n\n"
        "/myapp/ → 应用 A\n"
        "/myapplication/ → 应用 B\n\n"
        "你帮我看看是怎么回事？\n"
        "```\n\n"
        "提示词后的正文。"
    )


def test_parse_wechat_html_does_not_fence_scrollable_image_panel():
    html = """
    <html><body>
      <h1 id="activity-name">滚动图片文章</h1>
      <div id="js_content">
        <section style="height: 180px; overflow-y: scroll;">
          <section data-autoskip="1">
            <img data-src="https://example.com/scrollable-image.png" />
            <p>可以上下滚动的图片</p>
          </section>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/scrollable-image-panel")

    assert "```text" not in article.content_markdown
    assert "![Image](https://example.com/scrollable-image.png)" in article.content_markdown
    assert "可以上下滚动的图片" in article.content_markdown


def test_parse_wechat_html_does_not_fence_generic_overflow_container():
    html = """
    <html><body>
      <h1 id="activity-name">普通滚动布局文章</h1>
      <div id="js_content">
        <section style="height: 180px; overflow-y: auto;">
          <p>普通页面布局中的滚动正文。</p>
          <p>没有微信公众号文本框标记。</p>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/generic-overflow")

    assert "```text" not in article.content_markdown
    assert "普通页面布局中的滚动正文。" in article.content_markdown


@pytest.mark.parametrize(
    "code",
    [
        "sprint value",
        "blueprint value",
        "console.print value",
        "myimport value",
        "pnpm install",
        "mypnpm install",
    ],
)
def test_normalize_code_text_keeps_identifiers_and_standalone_commands(code):
    assert _normalize_code_text(code) == code


def test_normalize_code_text_splits_command_after_cjk_or_punctuation_prose():
    assert _normalize_code_text("安装说明npm install demo") == "安装说明\nnpm install demo"
    assert _normalize_code_text("说明：pip install demo") == "说明：\npip install demo"


@pytest.mark.parametrize("quote", ['"', "'", "`"])
@pytest.mark.parametrize(
    "literal",
    [
        "安装说明：npm install demo",
        "python=3.11conda activate env",
        "print(x)print(y)",
    ],
)
def test_normalize_code_text_keeps_fusion_patterns_inside_strings(quote, literal):
    code = f"msg = {quote}{literal}{quote}"

    assert _normalize_code_text(code) == code


@pytest.mark.parametrize(
    "code",
    [
        'msg = "他说：\\"安装说明npm install demo\\""',
        "msg = 'value=\\'python=3.11conda activate env\\''",
        "msg = `value=\\`print(x)print(y)\\``",
    ],
)
def test_normalize_code_text_keeps_escaped_quotes_inside_strings(code):
    assert _normalize_code_text(code) == code


def test_parse_wechat_html_normalizes_punctuation_at_bold_boundaries():
    html = """
    <html><body>
      <h1 id="activity-name">加粗标点边界文章</h1>
      <div id="js_content">
        <p>Text Extractor <strong>内置 OCR 一键截图取文字，</strong>ColorPicker 取色。</p>
        <p>Chatwoot 是一个<strong>客服系统的开源项目，</strong>目前累计 3.2 万 Star。</p>
        <p><strong>第一步，偷偷查你是谁。</strong>它会读取系统时区。</p>
        <p><strong>【新智元导读】</strong>全球第一。</p>
        <p>必须打开<strong>思考模式（Thinking）</strong>才能发挥性能。</p>
        <p>灵活性太差<strong>，源文件类型、数量都被卡死。</strong></p>
        <p>核心思路很直接<strong>：把终端重新做一遍。</strong></p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/bold-punctuation")

    assert "**内置 OCR 一键截图取文字**，ColorPicker 取色。" in article.content_markdown
    assert "一个**客服系统的开源项目**，目前累计" in article.content_markdown
    assert "**第一步，偷偷查你是谁**。它会读取系统时区。" in article.content_markdown
    assert "【**新智元导读**】全球第一。" in article.content_markdown
    assert "**思考模式**（**Thinking**）才能发挥性能。" in article.content_markdown
    assert "灵活性太差，**源文件类型、数量都被卡死。**" in article.content_markdown
    assert "核心思路很直接：**把终端重新做一遍。**" in article.content_markdown


def test_parse_wechat_html_removes_bold_markers_around_images():
    html = """
    <html><body>
      <h1 id="activity-name">加粗图片文章</h1>
      <div id="js_content">
        <p><strong><img data-src="https://example.com/bold-image.png" /></strong></p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/bold-image")

    assert article.content_markdown == "![Image](https://example.com/bold-image.png)"


def test_parse_wechat_html_collapses_nested_bold_markers():
    html = """
    <html><body>
      <h1 id="activity-name">嵌套加粗文章</h1>
      <div id="js_content">
        <p><strong><strong>摄像头气泡</strong></strong></p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/nested-bold")

    assert article.content_markdown == "**摄像头气泡**"


def test_parse_wechat_html_flattens_mixed_nested_emphasis():
    html = """
    <html><body>
      <h1 id="activity-name">混合强调文章</h1>
      <div id="js_content">
        <p>
          今年搞了<strong>小林训练营（<em>想要报名，+vx：<strong>xiaolincoding</strong></em>）。</strong>
        </p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/mixed-emphasis")

    assert article.content_markdown == (
        "今年搞了**小林训练营（*想要报名，+vx：xiaolincoding*）。**"
    )


def test_parse_wechat_html_preserves_strong_inside_emphasis():
    html = """
    <html><body>
      <h1 id="activity-name">斜体嵌套粗体文章</h1>
      <div id="js_content">
        <p><em><strong>重点术语</strong></em></p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/em-strong")

    assert article.content_markdown == "***重点术语***"


def test_parse_wechat_html_preserves_emphasis_inside_strong():
    html = """
    <html><body>
      <h1 id="activity-name">粗体嵌套斜体文章</h1>
      <div id="js_content">
        <p><strong><em>重点术语</em></strong></p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/strong-em")

    assert article.content_markdown == "***重点术语***"


def test_parse_wechat_html_separates_bare_urls_from_chinese_prose():
    html = """
    <html><body>
      <h1 id="activity-name">裸链接边界文章</h1>
      <div id="js_content">
        <p>打开 http://localhost:3000，顶部工具栏<strong>会自动显示内容。</strong></p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/bare-url")

    assert (
        "打开 <http://localhost:3000>，顶部工具栏**会自动显示内容。**" in article.content_markdown
    )


def test_parse_wechat_html_removes_bold_markers_from_standalone_symbols():
    html = """
    <html><body>
      <h1 id="activity-name">符号加粗文章</h1>
      <div id="js_content">
        <p><strong>一起</strong>“点赞”三连<strong>↓</strong></p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/bold-symbol")

    assert article.content_markdown == "**一起**“点赞”三连↓"


def test_parse_wechat_html_keeps_adjacent_bold_terms_unchanged():
    html = """
    <html><body>
      <h1 id="activity-name">相邻加粗文章</h1>
      <div id="js_content">
        <p>可以省去类型检查，通过添加 <strong>!</strong> <strong>断言</strong>，<strong>不推荐</strong>。</p>
        <p>例如 <strong>clientX</strong>、<strong>clientY</strong> 都是鼠标事件属性。</p>
        <p><strong>AI</strong>时代需要稳定输出。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/adjacent-bold")

    assert "**!** **断言**，**不推荐**" in article.content_markdown
    assert "**clientX**、**clientY**" in article.content_markdown
    assert "**AI**时代" in article.content_markdown


def test_parse_wechat_html_does_not_promote_ordinary_bold_paragraphs_to_headings():
    html = """
    <html><body>
      <h1 id="activity-name">普通强调文章</h1>
      <div id="js_content">
        <p><strong>看完这个新闻，我当时就震惊了：</strong></p>
        <p style="font-size: 20px; font-weight: 400; color: rgb(42, 42, 42);">千问云刚发布没多久。</p>
        <p><strong>很多人觉得这是AI新闻。但我看到的是另一件事：</strong></p>
        <section style="font-weight: 600; font-size: 21px; color:#7A4AEA;">真正的小标题</section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/bold")

    assert "## 看完这个新闻" not in article.content_markdown
    assert "## 千问云刚发布" not in article.content_markdown
    assert "千问云刚发布没多久。" in article.content_markdown
    assert "**看完这个新闻，我当时就震惊了：**" in article.content_markdown
    assert "## 真正的小标题" in article.content_markdown


def test_parse_wechat_html_promotes_descendant_styled_visual_heading_levels():
    html = """
    <html><body>
      <h1 id="activity-name">后代样式标题文章</h1>
      <div id="js_content">
        <p style="margin: 0 0 24px;">
          <strong><span style="font-size: 20px; color: rgb(0, 82, 255); font-weight: bold;">章节标题</span></strong>
        </p>
        <section style="background: rgb(245, 248, 255); border-left: 4px solid rgb(0, 82, 255);">
          <p>
            <strong><span style="font-size: 18px; color: rgb(34, 34, 34);">编号子标题</span></strong>
          </p>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/descendant-heading")

    assert article.content_markdown == "## 章节标题\n\n### 编号子标题"


def test_parse_wechat_html_promotes_visual_heading_inside_nested_sections():
    html = """
    <html><body>
      <h1 id="activity-name">嵌套标题文章</h1>
      <div id="js_content">
        <section>
          <section>
            <section style="margin-left: 8px; margin-right: 8px;">
              <strong>
                <span style="font-size: 17px; font-weight: normal;">
                  <span style="font-size: 20px; color: rgb(0, 82, 255); font-weight: bold;">AR手势控制</span>
                </span>
              </strong>
            </section>
          </section>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/nested-heading")

    assert article.content_markdown == "## AR手势控制"


def test_parse_wechat_html_keeps_large_lazy_images_with_tiny_css_width():
    html = """
    <html><body>
      <h1 id="activity-name">懒加载图片文章</h1>
      <div id="js_content">
        <p>正文前。</p>
        <img data-src="https://example.com/content.png" data-w="651" data-ratio="0.55"
             style="width: 3px !important; height: 1px !important;" />
        <p>正文后。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/image")

    assert "https://example.com/content.png" in article.content_markdown
    assert [img.source_url for img in article.images] == ["https://example.com/content.png"]


def test_parse_wechat_html_handles_linked_images_without_broken_brackets():
    html = """
    <html><body>
      <h1 id="activity-name">链接图片文章</h1>
      <div id="js_content">
        <a href="https://mp.weixin.qq.com/mp/appmsgalbum?album_id=1">
          <img data-src="https://example.com/album.png" />
        </a>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/linked-image")

    assert "[\n\n![Image]" not in article.content_markdown
    assert "\n\n](https://mp.weixin.qq.com/mp/appmsgalbum" not in article.content_markdown
    assert (
        "[![Image](https://example.com/album.png)](https://mp.weixin.qq.com/mp/appmsgalbum?album_id=1)"
        in article.content_markdown
    )


def test_parse_wechat_html_treats_non_code_pre_as_plain_content():
    html = """
    <html><body>
      <h1 id="activity-name">尾部推广文章</h1>
      <div id="js_content">
        <p>你知道的或者使用的在 Linux 终端中的更多网络监视工具还有哪些？</p>
        <pre><section><strong><span>-End-</span></strong></section></pre>
        <pre><section>读到这里说明你喜欢本公众号的文章。</section></pre>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/pre")

    assert "```" not in article.content_markdown
    assert "## -End-" not in article.content_markdown
    assert "**-End-**" in article.content_markdown
    assert "读到这里说明你喜欢本公众号的文章。" in article.content_markdown


def test_parse_wechat_html_cleans_fragmented_bold_recommendation_text():
    html = """
    <html><body>
      <h1 id="activity-name">推荐区文章</h1>
      <div id="js_content">
        <p>
          <strong>推</strong><strong>荐</strong><strong>阅</strong><strong>读</strong>
        </p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/recommend-title")

    assert "**推****荐****阅****读**" not in article.content_markdown
    assert "**推荐阅读**" in article.content_markdown


def test_parse_wechat_html_cleans_bold_italic_numbered_link_list_item():
    html = """
    <html><body>
      <h1 id="activity-name">推荐区文章</h1>
      <div id="js_content">
        <p>
          <strong><em>3.</em></strong><strong><a href="https://example.com/linux">Linux 学习指南 （收藏篇）</a></strong>
        </p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/recommend-link")

    assert "***3.*****[" not in article.content_markdown
    assert "**[Linux 学习指南 （收藏篇）]" not in article.content_markdown
    assert "3. [Linux 学习指南 （收藏篇）](https://example.com/linux)" in article.content_markdown


def test_parse_wechat_html_cleans_heavily_fragmented_bold_text():
    html = """
    <html><body>
      <h1 id="activity-name">碎片加粗文章</h1>
      <div id="js_content">
        <p>
          <strong>第</strong><strong><strong>九十一</strong></strong><strong>号</strong>
        </p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/fragmented-bold")

    assert "******" not in article.content_markdown
    assert "**第九十一号**" in article.content_markdown


def test_parse_wechat_html_filters_tiny_placeholder_background_gifs():
    html = """
    <html><body>
      <h1 id="activity-name">装饰动图文章</h1>
      <div id="js_content">
        <img data-src="https://example.com/header.gif" data-type="gif" data-w="1079" data-ratio="0.216"
             class="rich_pages __bg_gif" style="width: 1px !important;" />
        <img data-src="https://example.com/arrow.gif" data-type="gif" data-w="300" data-ratio="0.74"
             class="js_img_placeholder wx_img_placeholder __bg_gif"
             style="width: 22px !important; height: auto !important;" />
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/decorative-gif")

    assert "https://example.com/header.gif" in article.content_markdown
    assert "https://example.com/arrow.gif" not in article.content_markdown
    assert [image.source_url for image in article.images] == ["https://example.com/header.gif"]


def test_parse_wechat_html_narrows_block_link_to_colored_span():
    html = """
    <html><body>
      <h1 id="activity-name">局部链接文章</h1>
      <div id="js_content">
        <section>
          <a href="https://example.com/rule" title="https://example.com/rule">
            <p>
              <span style="color: rgb(15, 15, 15);">根据相关规定，将视为</span>
              <span style="color: rgb(36, 110, 255);">《微信公众平台运营规范》4.20 第三方商业营销内容违规</span>
              <span style="color: rgb(15, 15, 15);">。平台将按照规范限制。</span>
            </p>
          </a>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/narrow-link")

    assert "[根据相关规定" not in article.content_markdown
    assert "根据相关规定，将视为" in article.content_markdown
    assert (
        "[《微信公众平台运营规范》4.20 第三方商业营销内容违规](https://example.com/rule"
        in article.content_markdown
    )
    assert "。平台将按照规范限制。" in article.content_markdown


def test_parse_wechat_html_treats_visually_plain_body_h1_as_paragraph():
    html = """
    <html><body>
      <h1 id="activity-name">正文一级标签文章</h1>
      <div id="js_content">
        <h1 style="margin-left: 8px; margin-right: 8px; line-height: 2em;">
          <span style="color: rgba(0, 0, 0, 0.9); font-size: 14px; font-weight: normal;">
            这是一段普通正文。
          </span>
        </h1>
        <h1><span style="font-size: 24px; font-weight: bold;">真正的一级标题</span></h1>
        <h2>真正的二级标题</h2>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/plain-body-h1")

    assert article.content_markdown == (
        "这是一段普通正文。\n\n## 真正的一级标题\n\n### 真正的二级标题"
    )


def test_parse_wechat_html_keeps_images_wrapped_in_layout_headings():
    html = """
    <html><body>
      <h1 id="activity-name">图片标题容器文章</h1>
      <div id="js_content">
        <h3 style="color: rgb(34, 34, 34); background-color: rgb(255, 255, 255);">
          <section><img data-src="https://example.com/cover.jpg" data-w="1080" data-ratio="0.425" alt="Image" /></section>
        </h3>
        <h3 style="color: rgb(34, 34, 34); background-color: rgb(255, 255, 255);">
          <section><p><strong><span style="font-size: 18px; color: rgb(255, 255, 255); background-color: rgb(127, 127, 127);">新智元报道</span></strong></p></section>
        </h3>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/layout-heading-image")

    assert "### Image" not in article.content_markdown
    assert "### 新智元报道" not in article.content_markdown
    assert "![Image](https://example.com/cover.jpg)" in article.content_markdown
    assert "**新智元报道**" in article.content_markdown
    assert article.images[0].source_url == "https://example.com/cover.jpg"


def test_parse_wechat_html_treats_intro_card_heading_as_plain_text():
    html = """
    <html><body>
      <h1 id="activity-name">导读卡片文章</h1>
      <div id="js_content">
        <section>
          <h5 style="margin: 10px 8px 0px; padding: 10px; font-size: 14px; background-color: rgb(248, 248, 248); color: rgb(0, 0, 0); line-height: 1.75em;">
            <span><strong>【新智元导读】</strong>这是一段导读文字，不应该成为五级标题。</span>
          </h5>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/intro-card")

    assert "##### 【新智元导读】" not in article.content_markdown
    assert "【**新智元导读**】这是一段导读文字，不应该成为五级标题。" in article.content_markdown


def test_parse_wechat_html_replaces_video_player_with_link_or_placeholder():
    html_with_src = """
    <html><body>
      <h1 id="activity-name">视频文章</h1>
      <div id="js_content">
        <p>视频前。</p>
        <span class="video_iframe rich_pages">
          已关注 Follow Replay Share Like Close
          <div class="js_mpvedio page_video_wrapper">
            <video src="https://mpvideo.qpic.cn/demo.mp4?token=1">Your browser does not support video tags</video>
            <a href="javascript:;">Play</a>
          </div>
          <div class="interact_video"><a href="javascript:;">Video Details</a></div>
        </span>
        <p>视频后。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html_with_src, "https://mp.weixin.qq.com/s/video")

    assert "[视频](https://mpvideo.qpic.cn/demo.mp4?token=1)" in article.content_markdown
    assert "Your browser does not support video tags" not in article.content_markdown
    assert "Play" not in article.content_markdown
    assert "Follow" not in article.content_markdown
    assert "Video Details" not in article.content_markdown

    html_without_src = html_with_src.replace(' src="https://mpvideo.qpic.cn/demo.mp4?token=1"', "")
    placeholder_article = parse_wechat_html(html_without_src, "https://mp.weixin.qq.com/s/video")

    assert "[视频] 原文包含视频，未能提取视频链接。" in placeholder_article.content_markdown


def test_parse_wechat_html_filters_decorative_images_by_default():
    html = """
    <html><body>
      <h1 id="activity-name">装饰图文章</h1>
      <div id="js_content">
        <p>正文前。</p>
        <img data-src="https://example.com/decor.png" class="rich_pages wxw-img wx_img_placeholder_mini"
             data-w="1080" data-ratio="0.851" style="width: 18px !important; height: auto;" />
        <img data-src="https://example.com/content.png" data-w="882" data-ratio="0.365" />
        <p>正文后。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/decor")

    assert "https://example.com/decor.png" not in article.content_markdown
    assert "https://example.com/content.png" in article.content_markdown
    assert [img.source_url for img in article.images] == ["https://example.com/content.png"]


def test_parse_wechat_html_filters_tiny_images_in_decorative_layout_boxes():
    html = """
    <html><body>
      <h1 id="activity-name">微型装饰图文章</h1>
      <div id="js_content">
        <p>正文前。</p>
        <section style="width: 100%; padding: 0 10px;">
          <section style="width: 14px; height: 13px; display: flex; margin: 0 0 -9px -1px;">
            <img data-src="https://example.com/open-quote.png" data-w="28"
                 data-ratio="0.9285714285714286" class="rich_pages wxw-img"
                 style="background-color: transparent;" />
          </section>
          <section style="width: 11px; height: 6px; display: flex; flex-shrink: 0;">
            <img data-src="https://example.com/triangle.png" data-w="24"
                 data-ratio="0.5833333333333334" class="rich_pages wxw-img"
                 style="background-color: transparent;" />
          </section>
          <p>引用正文。</p>
          <section style="width: 14px; height: 13px; display: flex; align-self: flex-end;">
            <img data-src="https://example.com/close-quote.png" data-w="28"
                 data-ratio="0.9285714285714286" class="rich_pages wxw-img"
                 style="background-color: transparent;" />
          </section>
        </section>
        <p>正文后。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/tiny-decorative-layout")

    assert article.content_markdown == "正文前。\n\n引用正文。\n\n正文后。"
    assert article.images == []


def test_parse_wechat_html_keeps_meaningful_tiny_linked_image():
    html = """
    <html><body>
      <h1 id="activity-name">微型正文图片文章</h1>
      <div id="js_content">
        <section style="width: 14px; height: 13px; display: flex;">
          <a href="https://example.com/status">
            <img data-src="https://example.com/status.png" data-w="24" data-ratio="1"
                 class="rich_pages wxw-img" alt="项目状态" />
          </a>
        </section>
        <p>当前服务正常。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/tiny-content-image")

    assert "[![项目状态](https://example.com/status.png)](https://example.com/status)" in (
        article.content_markdown
    )
    assert [image.source_url for image in article.images] == ["https://example.com/status.png"]


def test_parse_wechat_html_normalizes_newzhiyuan_single_line_chapter_heading():
    html = """
    <html><body>
      <h1 id="activity-name">新智元单行章节标题文章</h1>
      <div id="js_content">
        <section style="text-align: center; margin-top: 0px; margin-bottom: 0px;">
          <span>
            <img data-src="https://example.com/chapter-mark.png" data-w="112"
                 data-ratio="0.5267857142857143" class="rich_pages wxw-img"
                 style="width: 85px; height: 40px;" />
            <img class="rich_pages wxw-img" />
            <img class="rich_pages wxw-img" />
          </span>
        </section>
        <section style="text-align: center; margin: 8px 0 0; line-height: 1.75em;">
          <span style="color: rgb(0, 0, 0); font-size: 19px; letter-spacing: 1px;">
            <strong><span>三巨头只剩两个</span></strong>
          </span>
        </section>
        <p>章节正文。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/newzhiyuan-single")

    assert article.content_markdown == "## 三巨头只剩两个\n\n章节正文。"
    assert article.images == []


def test_parse_wechat_html_merges_newzhiyuan_two_line_chapter_heading():
    html = """
    <html><body>
      <h1 id="activity-name">新智元双行章节标题文章</h1>
      <div id="js_content">
        <h2 style="margin: 0 8px; line-height: 1.75em;"><span><br /></span></h2>
        <section style="text-align: center; margin-top: 0px; margin-bottom: 0px;">
          <span>
            <img data-src="https://example.com/chapter-mark.png" data-w="112"
                 data-ratio="0.5267857142857143" class="rich_pages wxw-img"
                 style="width: 85px; height: 40px;" />
          </span>
        </section>
        <section style="text-align: center; margin-bottom: 0px; margin-top: 8px; line-height: 1.75em;">
          <span style="color: rgb(0, 0, 0); font-size: 19px; letter-spacing: 1px;">
            <strong><span>软硬协同：</span></strong>
          </span>
        </section>
        <section style="text-align: center; margin-bottom: 0px; margin-top: 8px; line-height: 1.75em;">
          <span style="color: rgb(0, 0, 0); font-size: 19px; letter-spacing: 1px;">
            <strong><span>释放超智融合澎湃算力</span></strong>
          </span>
        </section>
        <h2 style="margin: 0 8px; line-height: 1.75em;"><strong><span><br /></span></strong></h2>
        <p>HPC 与 AI 深度协同。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/newzhiyuan-double")

    assert article.content_markdown == "## 软硬协同：释放超智融合澎湃算力\n\nHPC 与 AI 深度协同。"
    assert article.images == []


def test_parse_wechat_html_keeps_same_size_content_image_without_chapter_template():
    html = """
    <html><body>
      <h1 id="activity-name">同尺寸正文图片文章</h1>
      <div id="js_content">
        <section style="text-align: center;">
          <img data-src="https://example.com/status-chart.png" data-w="112"
               data-ratio="0.5267857142857143" class="rich_pages wxw-img"
               style="width: 85px; height: 40px;" alt="服务状态图" />
        </section>
        <p>这是一张有正文意义的小图。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/same-size-content-image")

    assert "![服务状态图](https://example.com/status-chart.png)" in article.content_markdown
    assert [image.source_url for image in article.images] == [
        "https://example.com/status-chart.png"
    ]


def test_parse_wechat_html_does_not_promote_reverse_nested_bold_text_without_template():
    html = """
    <html><body>
      <h1 id="activity-name">普通居中强调文章</h1>
      <div id="js_content">
        <section style="text-align: center; line-height: 1.75em;">
          <span style="color: rgb(0, 0, 0); font-size: 19px; letter-spacing: 1px;">
            <strong><span>这只是普通居中强调文字</span></strong>
          </span>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/reverse-nested-bold")

    assert article.content_markdown == "**这只是普通居中强调文字**"


def test_parse_wechat_html_drops_empty_layout_headings():
    html = """
    <html><body>
      <h1 id="activity-name">空布局标题文章</h1>
      <div id="js_content">
        <p>正文前。</p>
        <h2 style="margin: 0 8px; line-height: 1.75em;"><strong><span><br /></span></strong></h2>
        <p>正文后。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/empty-layout-heading")

    assert article.content_markdown == "正文前。\n\n正文后。"


def test_parse_wechat_html_simplifies_poster_template_heading_frames():
    html = """
    <html><body>
      <h1 id="activity-name">2026年小班秋季招生公告</h1>
      <a id="js_name">福州市马尾第三实验幼儿园</a>
      <div id="js_content">
        <section style="background-color: rgb(149, 140, 185);">
          <section>
            <img data-src="https://example.com/follow.png" data-w="329" data-ratio="0.10"
                 class="rich_pages wxw-img" />
          </section>
          <section>
            <img data-src="https://example.com/cover.png" data-w="683" data-ratio="0.58"
                 class="rich_pages wxw-img" />
          </section>
          <section>
            <img data-src="https://example.com/frame.png" data-w="655" data-ratio="0.265"
                 class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" />
          </section>
          <section style="grid-column-start: 1; grid-row-start: 1; display: flex;">
            <section style="font-size: 22px; color: rgb(149, 140, 185);">
              <p><span>计划招生数</span></p>
            </section>
          </section>
          <section>
            <p>小班：4个班，每班25人，共100人。</p>
          </section>
          <section>
            <img data-src="https://example.com/qr.png" data-w="500" data-ratio="1"
                 class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" />
          </section>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/poster")

    assert "https://example.com/follow.png" not in article.content_markdown
    assert "https://example.com/frame.png" not in article.content_markdown
    assert "![Image](https://example.com/cover.png)" in article.content_markdown
    assert "![Image](https://example.com/qr.png)" in article.content_markdown
    assert "## 计划招生数" in article.content_markdown
    assert "小班：4个班，每班25人，共100人。" in article.content_markdown
    assert [img.source_url for img in article.images] == [
        "https://example.com/cover.png",
        "https://example.com/qr.png",
    ]


def test_parse_wechat_html_keeps_real_wide_placeholder_images():
    html = """
    <html><body>
      <h1 id="activity-name">真实横幅文章</h1>
      <div id="js_content">
        <p>正文前。</p>
        <img data-src="https://example.com/real-chart.png" data-w="800" data-ratio="0.25"
             class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" />
        <p>这是图片说明。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/real-banner")

    assert "![Image](https://example.com/real-chart.png)" in article.content_markdown
    assert "这是图片说明。" in article.content_markdown
    assert [img.source_url for img in article.images] == ["https://example.com/real-chart.png"]
