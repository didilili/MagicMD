# PageMD

PageMD converts public article links into clean Markdown packages.

It is designed as a stronger, more extensible successor to single-platform article converters:

- One URL in, Markdown package out.
- Configurable Markdown front matter and output layout.
- Platform adapters for WeChat, Juejin, and generic public article pages.
- Local image downloading and Markdown link rewriting.
- Metadata JSON for later publishing to GitHub, HaoGit, or other sites.
- Debug artifacts for extraction failures.

## Install

```bash
uv sync --extra dev
```

## Usage

```bash
uv run pagemd "https://mp.weixin.qq.com/s/example" -o output/
uv run pagemd convert "https://juejin.cn/post/example" -o output/
uv run pagemd batch urls.txt -o output/
uv run pagemd config init
uv run pagemd doctor
```

Output:

```text
output/
└── undated-article-title/
    ├── article.md
    ├── metadata.json
    └── images/
```

## Safety

PageMD only targets public article pages. It does not bypass login, paywalls, private content, CAPTCHA, or platform access controls.

