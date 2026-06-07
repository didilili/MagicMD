# MagicMD 官网与配置生成器方案

## 目标

MagicMD 需要一个长期可维护的官网，而不是只有 README。

第一阶段官网重点解决三个问题：

- 让新用户一眼明白 MagicMD 能做什么。
- 让用户快速安装并完成第一次转换。
- 让用户不用手写 TOML，也能生成可用的 `.magicmd.toml`。

因此官网第一版采用：

```text
Astro + Starlight + TypeScript + React island
```

Astro 负责官网和静态构建，Starlight 负责文档体系，React island 负责在线配置生成器。

## 为什么选择 Astro + Starlight

MagicMD 后续不只是文档站，还会包含产品首页、配置生成器、示例展示、支持站点说明和 Agent Skill 使用说明。

相比其它方案：

- VitePress 很适合纯文档，但产品官网和工具页的自由度相对弱一些。
- Docusaurus 成熟稳定，但默认气质偏传统开源文档站。
- Next.js 适合完整 Web App，但当前 GitHub Pages 静态部署场景偏重。
- Astro + Starlight 同时适合产品首页、文档、静态部署和局部交互组件。

## 第一版页面

### 首页

路径：

```text
/
```

首页要像产品官网，而不是 README 的复制版。

核心信息：

- MagicMD 是什么：把微信公众号、掘金、CSDN 等公开文章转换成 Markdown 内容包。
- 适合谁：内容归档、技术写作、个人博客、知识库、Agent 自动化。
- 为什么好用：图片本地化、代码块清理、链接修复、批量报告、可配置输出。
- 快速安装：

```bash
uv tool install magicmd
magicmd doctor
```

### 快速开始

路径：

```text
/docs/quick-start/
```

覆盖：

- 安装方式：`uv tool install`、`pipx install`、`npm install -g`
- 单篇转换
- 批量转换
- `--skip-existing`
- `--no-images`
- 输出目录结构

### 配置生成器

路径：

```text
/config-builder/
```

用户通过表单选择配置，右侧实时生成 TOML。

第一版支持：

- 发布目标：默认 Markdown、Hugo、Docusaurus、自定义。
- 输出目录命名：`{date}-{slug}`、`{platform}/{date}-{slug}`、自定义。
- Markdown 文件名：`article.md`、`index.md`、自定义。
- metadata/report 文件名。
- 是否生成 Front matter。
- Front matter 字段选择。
- 是否显示来源信息块。
- 图片路径模板。
- 视频路径模板。
- 是否下载图片和视频。

操作按钮：

- 复制 TOML。
- 下载 `.magicmd.toml`。
- 显示对应 CLI 命令。

### 配置说明

路径：

```text
/docs/config/
```

解释 `.magicmd.toml` 的字段含义，和配置生成器互相链接。

### 支持站点

路径：

```text
/docs/supported-sites/
```

从现有 `docs/supported-sites.md` 迁移。

重点说明：

- 微信公众号支持情况。
- 掘金支持情况。
- CSDN 支持情况。
- 通用网页的边界。
- 哪些情况需要人工复核。

### 故障排查

路径：

```text
/docs/troubleshooting/
```

从现有 `docs/troubleshooting.md` 迁移。

## 目录结构建议

```text
website/
├── astro.config.mjs
├── package.json
├── tsconfig.json
├── public/
│   └── favicon.svg
├── src/
│   ├── pages/
│   │   ├── index.astro
│   │   └── config-builder.astro
│   ├── components/
│   │   ├── ConfigBuilder.tsx
│   │   ├── TomlPreview.tsx
│   │   └── CopyButton.tsx
│   ├── content/
│   │   └── docs/
│   │       ├── quick-start.md
│   │       ├── config.md
│   │       ├── supported-sites.md
│   │       └── troubleshooting.md
│   └── styles/
│       └── custom.css
└── README.md
```

## 配置生成器数据模型

前端内部使用结构化状态，再序列化成 TOML。

示例：

```ts
type ConfigBuilderState = {
  preset: "default" | "plain" | "hugo" | "docusaurus" | "custom";
  output: {
    directory: string;
    package: string;
    markdown: string;
    metadata: string;
    report: string;
  };
  markdown: {
    frontMatter: "yaml" | "none";
    includeTitle: boolean;
    includeSourceBlock: boolean;
    headingOffset: number;
    frontMatterFields: string[];
  };
  images: {
    download: boolean;
    directory: string;
    markdownPath: string;
  };
  videos: {
    download: boolean;
    directory: string;
    markdownPath: string;
  };
};
```

## TOML 生成原则

- 生成结果必须和 `.magicmd.example.toml` 的字段保持一致。
- 第一版只生成 MagicMD 已经支持的字段，不生成未来字段。
- 生成的 TOML 应该尽量短，避免把所有默认值都塞进去。
- 但“下载完整示例”可以提供完整版本。
- 复制出来的配置必须能被 `magicmd config` 正常读取。

## 部署方式

使用 GitHub Actions 部署到 GitHub Pages。

正式入口：

```text
https://magicmd.cn/
```

GitHub Pages 默认域名只作为底层托管能力，不再作为用户侧入口；文档、README 和对外传播统一使用 `magicmd.cn`。

## 第一阶段不做什么

第一阶段不做在线文章转换。

原因：

- 微信文章抓取有反爬和登录态问题。
- 视频、图片下载涉及带宽和热链限制。
- 服务端转换会引入隐私和版权边界。
- 当前更重要的是让用户理解和使用本地 CLI。

## 验收标准

- GitHub Pages 可以打开官网。
- 首页能在 10 秒内让用户理解 MagicMD 的价值。
- 文档里能完成安装、转换、配置三件事。
- 配置生成器能生成可复制的 `.magicmd.toml`。
- 生成的 TOML 能被 MagicMD 本地 CLI 正常读取。
- 官网不依赖后端服务。

## 推荐实施顺序

1. 初始化 `website/` 项目。
2. 配置 Astro + Starlight + GitHub Pages base path。
3. 做首页第一版。
4. 迁移快速开始、配置说明、支持站点、故障排查文档。
5. 做配置生成器 MVP。
6. 增加 GitHub Actions Pages 部署。
7. 在 README 中增加官网入口。
