<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useData } from 'vitepress';

type Preset = 'default' | 'plain' | 'hugo' | 'docusaurus';
type FrontMatter = 'yaml' | 'none';
type PreviewTab = 'toml' | 'markdown' | 'structure';
type UiLanguage = 'zh-CN' | 'en-US';
type HelpKey =
  | 'preset'
  | 'uiLanguage'
  | 'packageName'
  | 'markdownName'
  | 'metadataName'
  | 'reportName'
  | 'frontMatter'
  | 'includeSourceBlock'
  | 'includeCoverImage'
  | 'imagePath'
  | 'videoPath'
  | 'docxEnabled'
  | 'downloadImages'
  | 'downloadVideos'
  | 'outputPreview'
  | 'generated'
  | 'publishEnabled'
  | 'publishRepo'
  | 'publishTargetDir'
  | 'publishBranch'
  | 'publishCommitMessage'
  | 'publishCreatePr'
  | 'publishOverwrite';

type BuilderState = {
  preset: Preset;
  uiLanguage: UiLanguage;
  packageName: string;
  markdownName: string;
  metadataName: string;
  reportName: string;
  frontMatter: FrontMatter;
  includeSourceBlock: boolean;
  includeCoverImage: boolean;
  imagePath: string;
  videoPath: string;
  downloadImages: boolean;
  downloadVideos: boolean;
  docxEnabled: boolean;
  publishEnabled: boolean;
  publishRepo: string;
  publishTargetDir: string;
  publishBranch: string;
  publishCommitMessage: string;
  publishCreatePr: boolean;
  publishOverwrite: boolean;
};

const presetDefaults: Record<Preset, Partial<BuilderState>> = {
  default: {
    markdownName: 'article.md',
    frontMatter: 'yaml',
    includeSourceBlock: true,
    includeCoverImage: true,
    imagePath: '{directory}/{filename}',
    videoPath: '{directory}/{filename}'
  },
  plain: {
    markdownName: 'article.md',
    frontMatter: 'none',
    includeSourceBlock: false,
    includeCoverImage: false,
    imagePath: '{directory}/{filename}',
    videoPath: '{directory}/{filename}'
  },
  hugo: {
    markdownName: 'index.md',
    frontMatter: 'yaml',
    includeSourceBlock: true,
    includeCoverImage: true,
    imagePath: '{directory}/{filename}',
    videoPath: '{directory}/{filename}'
  },
  docusaurus: {
    markdownName: 'index.md',
    frontMatter: 'yaml',
    includeSourceBlock: false,
    includeCoverImage: true,
    imagePath: './{directory}/{filename}',
    videoPath: './{directory}/{filename}'
  }
};

const state = reactive<BuilderState>({
  preset: 'default',
  uiLanguage: 'zh-CN',
  packageName: '{date}-{slug}',
  markdownName: 'article.md',
  metadataName: 'metadata.json',
  reportName: 'extraction-report.json',
  frontMatter: 'yaml',
  includeSourceBlock: true,
  includeCoverImage: true,
  imagePath: '{directory}/{filename}',
  videoPath: '{directory}/{filename}',
  downloadImages: true,
  downloadVideos: true,
  docxEnabled: false,
  publishEnabled: false,
  publishRepo: 'owner/content',
  publishTargetDir: 'content/posts/{date}-{slug}',
  publishBranch: 'magicmd/{slug}',
  publishCommitMessage: 'Add article: {title}',
  publishCreatePr: true,
  publishOverwrite: false
});

const copyState = ref<'idle' | 'copied' | 'failed'>('idle');
const activePreview = ref<PreviewTab>('toml');
const advancedOpen = ref(false);

const demoArticle = {
  title: '今夜，库克终极绝唱！25亿苹果设备用AI重生',
  author: '新智元',
  platform: 'wechat',
  sourceUrl: 'https://mp.weixin.qq.com/s/zkLfLEtX-o8d2GFaPAYVeA',
  publishedAt: '2026-06-09T06:00:00+08:00'
};

const { lang } = useData();

const isEnglish = computed(() => lang.value.startsWith('en'));

const ui = computed(() =>
  isEnglish.value
    ? {
        step: 'Step 1',
        panelTitle: 'Lock in your output rules',
        panelDescription: 'Pick a publishing target, then tune filenames and media paths.',
        preset: 'Publishing target',
        presetHint: 'Choose where this package will be published.',
        uiLanguage: 'Terminal language',
        chinese: 'Chinese',
        english: 'English',
        presetOptions: {
          default: 'Default Markdown',
          plain: 'Plain Markdown',
          hugo: 'Hugo website bundle',
          docusaurus: 'Docusaurus docs site'
        },
        presetDetails: {
          default: 'Balanced output for archives, notes, and knowledge bases.',
          plain: 'No front matter or source block. Keep the article body lean.',
          hugo: 'Hugo builds static blogs/sites from Markdown. This preset uses index.md for a Hugo-style page bundle.',
          docusaurus:
            'Docusaurus builds documentation websites. This preset uses index.md and docs-friendly relative media paths.'
        },
        help: {
          preset:
            'A preset fills in sensible defaults for a target. Hugo is a static site generator for blogs and content sites; Docusaurus is a documentation site generator. You can still edit every field afterwards.',
          uiLanguage:
            'Controls the language of MagicMD terminal progress messages. Markdown metadata keys stay compatible with publishing tools.',
          packageName:
            'The folder created for each article. {date} becomes the publish date, and {slug} becomes a safe title slug.',
          markdownName:
            'The Markdown file inside the package. Use article.md for archives, or index.md for Hugo/Docusaurus content folders.',
          metadataName:
            'Stores structured article metadata such as title, author, platform, source URL, and publish time.',
          reportName:
            'Stores extraction warnings and media download details. Useful when checking batch conversion quality.',
          frontMatter:
            'YAML front matter is the metadata block at the top of a Markdown file. Static site generators often use it for title, date, tags, and author.',
          includeSourceBlock:
            'Adds a small source block below the title so readers can see the original platform, author, and URL.',
          includeCoverImage:
            'Shows the WeChat article card cover below the source block, separated from the body by a horizontal rule.',
          imagePath:
            'The path written into Markdown image links. {directory} uses the image folder, and {filename} uses the downloaded file name.',
          videoPath:
            'The path written into Markdown video links. Keep this relative if the article package will be moved as a folder.',
          docxEnabled:
            'Generate article.docx next to the Markdown package. This requires Pandoc on the machine running MagicMD.',
          downloadImages:
            'Download article images into the output package instead of leaving remote image URLs in Markdown.',
          downloadVideos:
            'Try to download videos into the output package. Some WeChat videos may still require manual review.',
          outputPreview:
            'This is the final Markdown file path that MagicMD will create for one article.',
          generated:
            'Copy this file as .magicmd.toml and run MagicMD with --config to use these rules.',
          publishEnabled:
            'Adds the optional [publish.github] block. Enable it when you want magicmd publish github to reuse the same repository and branch settings.',
          publishRepo:
            'Target GitHub repository in owner/name format. Replace owner/content with your real content repository.',
          publishTargetDir:
            'Directory inside the target repository. Use templates like content/posts/{date}-{slug} so each article gets its own folder.',
          publishBranch:
            'Branch template for MagicMD publishes. {slug}, {date}, {platform}, and {short_hash} are supported.',
          publishCommitMessage:
            'Commit message template for the publish commit. Keep it readable because it will appear in the target repository history.',
          publishCreatePr:
            'Create a Pull Request after pushing the publish branch. Real publishing still requires GITHUB_TOKEN.',
          publishOverwrite:
            'Allow planned target files to be overwritten. Leave this off unless you intentionally republish the same path.'
        },
        helpTitle: 'What is this?',
        basicSection: 'Basic',
        advancedSection: 'Advanced settings',
        showAdvanced: 'Show advanced settings',
        hideAdvanced: 'Hide advanced settings',
        markdownSection: 'Markdown',
        mediaSection: 'Media',
        githubSection: 'GitHub publishing',
        packageName: 'Package directory',
        markdownName: 'Markdown filename',
        metadataName: 'Metadata filename',
        reportName: 'Report filename',
        frontMatter: 'Front matter',
        yaml: 'Generate YAML',
        none: 'Do not generate',
        imagePath: 'Image Markdown path',
        videoPath: 'Video Markdown path',
        includeSourceBlock: 'Show source block',
        includeCoverImage: 'Show WeChat cover image',
        downloadImages: 'Download images',
        downloadVideos: 'Download videos',
        docxEnabled: 'Generate Word document',
        publishEnabled: 'Generate GitHub publishing config',
        publishRepo: 'Repository',
        publishTargetDir: 'Target directory',
        publishBranch: 'Publish branch',
        publishCommitMessage: 'Commit message',
        publishCreatePr: 'Create Pull Request',
        publishOverwrite: 'Allow overwrite',
        generated: 'Generated in real time. Save it at your project root.',
        previewTabs: {
          toml: '.magicmd.toml',
          markdown: 'article.md preview',
          structure: 'Output tree'
        },
        copied: 'Copied',
        copyFailed: 'Copy failed',
        copy: 'Copy',
        download: 'Download',
        cliHint: 'Save it, then run: magicmd URL --config .magicmd.toml',
        outputSummary: 'Output preview',
        metadataOn: 'YAML metadata',
        metadataOff: 'No metadata block',
        terminalChinese: 'Chinese CLI',
        terminalEnglish: 'English CLI',
        localOnly: 'Keep remote media',
        imagesAndVideos: 'Download images and videos',
        imagesOnly: 'Download images',
        videosOnly: 'Download videos',
        wordOutput: 'Word output',
        githubOutput: 'GitHub publishing',
        markdownPreviewTitle: (name: string) => `Preview of ${name}`,
        markdownPreviewHint: 'Updates as you change the config',
        sampleHeading: 'Converted preview',
        sampleBody:
          'This real WeChat article keeps its source metadata, local image paths, and a clean Markdown structure after conversion.',
        sampleLink: 'Read original',
        outputRoot: 'Package includes',
        imagesDir: 'images',
        videosDir: 'videos'
      }
    : {
        step: 'Step 1',
        panelTitle: '把输出规则定下来',
        panelDescription: '选择发布目标后，再微调文件名和媒体路径。',
        preset: '发布目标',
        presetHint: '先选发布目标，下面的文件名和路径会自动跟着调整。',
        uiLanguage: '终端语言',
        chinese: '中文',
        english: '英文',
        presetOptions: {
          default: '通用 Markdown',
          plain: '纯净 Markdown',
          hugo: 'Hugo 网站内容包',
          docusaurus: 'Docusaurus 文档站'
        },
        presetDetails: {
          default: '适合归档、笔记、知识库，保留常用元信息。',
          plain: '不生成 front matter 和来源块，只保留干净正文。',
          hugo: 'Hugo 是把 Markdown 生成博客/网站的静态网站生成器。这个预设使用 index.md，更贴近 Hugo 内容包结构。',
          docusaurus:
            'Docusaurus 是常用于开源项目文档站的生成器。这个预设使用 index.md 和更适合文档目录的相对媒体路径。'
        },
        help: {
          preset:
            '预设会根据发布目标自动填一组默认配置。Hugo 是静态网站生成器，常用来把 Markdown 生成博客/内容网站；Docusaurus 是文档站生成器，常用于开源项目文档。选完后下面字段仍然可以手动改。',
          uiLanguage:
            '控制 MagicMD 终端进度提示的语言。Markdown 元信息字段名仍保持发布工具更容易识别的标准键。',
          packageName:
            '每篇文章生成的文件夹名称。{date} 会替换成发布日期，{slug} 会替换成安全的标题短名，不需要你手动填真实日期。',
          markdownName:
            '内容包里的正文 Markdown 文件名。归档常用 article.md，Hugo / Docusaurus 通常用 index.md。',
          metadataName:
            '保存文章结构化信息，比如标题、作者、平台、原文链接、发布时间，方便后续系统读取。',
          reportName:
            '保存抓取和转换报告，包括 warning、图片/视频下载情况，批量转换后很适合用来排查问题。',
          frontMatter:
            'Markdown 顶部的 YAML 元信息块。Hugo、Docusaurus、博客系统常用它识别标题、作者、日期等字段。',
          includeSourceBlock:
            '在正文标题下方增加来源信息块，显示原平台、作者和原文链接，方便以后回溯。',
          includeCoverImage: '在来源信息块下方展示微信公众号文章卡片封面，并用分割线和正文隔开。',
          imagePath:
            '写入 Markdown 图片链接里的路径。{directory} 表示图片目录，{filename} 表示下载后的图片文件名。',
          videoPath: '写入 Markdown 视频链接里的路径。如果你要整体移动文章目录，建议保持相对路径。',
          docxEnabled:
            '在 Markdown 内容包旁额外生成 article.docx。运行 MagicMD 的机器需要安装 Pandoc。',
          downloadImages:
            '开启后会把文章图片下载到输出目录，而不是在 Markdown 里继续引用远程图片链接。',
          downloadVideos:
            '开启后会尝试下载视频。微信公众号视频可能有防盗链或临时签名，失败时仍需人工复核。',
          outputPreview: '这里展示 MagicMD 最终会生成的正文 Markdown 文件路径。',
          generated:
            '复制这份内容保存为 .magicmd.toml，再用 --config 参数运行 MagicMD，就会按这些规则输出。',
          publishEnabled:
            '追加可选的 [publish.github] 配置块。你要反复发布到同一个 GitHub 内容仓库时再开启。',
          publishRepo:
            '目标 GitHub 仓库，格式是 owner/name。请把 owner/content 换成你的真实内容仓库。',
          publishTargetDir:
            '目标仓库内的目录。建议使用 content/posts/{date}-{slug} 这样的模板，让每篇文章都有自己的目录。',
          publishBranch:
            'MagicMD 发布分支模板，支持 {slug}、{date}、{platform}、{short_hash} 等变量。',
          publishCommitMessage:
            '发布 commit 的提交信息模板。它会出现在目标仓库历史里，建议保持清晰可读。',
          publishCreatePr: 'push 发布分支后自动创建 Pull Request。真实发布仍然需要 GITHUB_TOKEN。',
          publishOverwrite: '允许覆盖计划内的目标文件。除非你确认要重复发布同一路径，否则建议关闭。'
        },
        helpTitle: '这是什么？',
        basicSection: '基础设置',
        advancedSection: '高级设置',
        showAdvanced: '展开高级设置',
        hideAdvanced: '收起高级设置',
        markdownSection: 'Markdown 设置',
        mediaSection: '媒体设置',
        githubSection: 'GitHub 发布',
        packageName: '内容包目录',
        markdownName: 'Markdown 文件名',
        metadataName: 'Metadata 文件名',
        reportName: '报告文件名',
        frontMatter: 'Front matter',
        yaml: '生成 YAML',
        none: '不生成',
        imagePath: '图片 Markdown 路径',
        videoPath: '视频 Markdown 路径',
        includeSourceBlock: '显示来源信息块',
        includeCoverImage: '显示微信封面图',
        downloadImages: '下载图片',
        downloadVideos: '下载视频',
        docxEnabled: '生成 Word 文档',
        publishEnabled: '生成 GitHub 发布配置',
        publishRepo: '目标仓库',
        publishTargetDir: '目标目录',
        publishBranch: '发布分支',
        publishCommitMessage: 'Commit message',
        publishCreatePr: '创建 Pull Request',
        publishOverwrite: '允许覆盖',
        generated: '实时生成，可直接落到项目根目录',
        previewTabs: {
          toml: '.magicmd.toml',
          markdown: 'article.md 示例',
          structure: '输出结构'
        },
        copied: '已复制',
        copyFailed: '复制失败',
        copy: '复制',
        download: '下载',
        cliHint: '保存后运行：magicmd URL --config .magicmd.toml',
        outputSummary: '输出预览',
        metadataOn: '生成 YAML 元信息',
        metadataOff: '不生成元信息块',
        terminalChinese: '中文终端',
        terminalEnglish: '英文终端',
        localOnly: '保留远程媒体链接',
        imagesAndVideos: '下载图片和视频',
        imagesOnly: '下载图片',
        videosOnly: '下载视频',
        wordOutput: 'Word 文档',
        githubOutput: 'GitHub 发布',
        markdownPreviewTitle: (name: string) => `生成后的 ${name} 示例`,
        markdownPreviewHint: '随左侧配置实时变化',
        sampleHeading: '真实转换示例',
        sampleBody:
          '这是一篇真实微信公众号文章的转换预览：保留来源信息，图片改成本地路径，正文结构整理成干净的 Markdown。',
        sampleLink: '查看原文',
        outputRoot: '内容包包含',
        imagesDir: '图片目录',
        videosDir: '视频目录'
      }
);

const presetLabels = computed<Record<Preset, string>>(() => ui.value.presetOptions);
const presetDetails = computed<Record<Preset, string>>(() => ui.value.presetDetails);
const presetList: Preset[] = ['default', 'plain', 'hugo', 'docusaurus'];
const previewTabs: PreviewTab[] = ['toml', 'markdown', 'structure'];

function helpText(key: HelpKey) {
  return ui.value.help[key];
}

const outputPreview = computed(() => {
  return `${state.packageName}/${state.markdownName}`;
});

const outputTitle = computed(() => {
  return state.markdownName || outputPreview.value;
});

const mediaPreview = computed(() => {
  if (!state.downloadImages && !state.downloadVideos) return ui.value.localOnly;
  if (state.downloadImages && state.downloadVideos) return ui.value.imagesAndVideos;
  return state.downloadImages ? ui.value.imagesOnly : ui.value.videosOnly;
});

const outputTree = computed(() => {
  const entries = [
    state.markdownName,
    state.metadataName,
    state.reportName,
    ...(state.docxEnabled ? ['article.docx'] : []),
    ...(state.downloadImages ? ['images/\n        └── img_001.jpg'] : []),
    ...(state.downloadVideos ? ['videos/\n        └── video_001.mp4'] : [])
  ];

  return [
    'output/',
    `└── ${state.packageName}/`,
    ...entries.map((entry, index) => {
      const prefix = index === entries.length - 1 ? '    └── ' : '    ├── ';
      return `${prefix}${entry}`;
    })
  ].join('\n');
});

function quote(value: string) {
  return `"${value.replaceAll('\\', '\\\\').replaceAll('"', '\\"')}"`;
}

function renderMediaPath(template: string, directory: string, filename: string) {
  return template.replaceAll('{directory}', directory).replaceAll('{filename}', filename);
}

function applyPreset(preset: Preset) {
  Object.assign(state, { preset }, presetDefaults[preset]);
}

const toml = computed(() => {
  const sourceBlock = state.includeSourceBlock
    ? `\nsource_block_template = """\n> Source: {platform}\n> Author: {author}\n> Original: {source_url}\n"""\n`
    : '\n';

  const frontMatterFields =
    state.frontMatter === 'yaml'
      ? `\n[markdown.front_matter_fields]\ntitle = "{title}"\nauthor = "{author}"\nplatform = "{platform}"\nsource_url = "{source_url}"\npublished_at = "{published_at}"\n`
      : '';

  const publishGithub = state.publishEnabled
    ? `\n[publish.github]\nrepo = ${quote(state.publishRepo)}\ntarget_dir = ${quote(state.publishTargetDir)}\nbranch = ${quote(state.publishBranch)}\ncommit_message = ${quote(state.publishCommitMessage)}\ncreate_pr = ${state.publishCreatePr}\noverwrite = ${state.publishOverwrite}\n`
    : '';

  return `[output]\ndirectory = "output"\n\n[output.naming]\npackage = ${quote(state.packageName)}\nmarkdown = ${quote(state.markdownName)}\nmetadata = ${quote(state.metadataName)}\nreport = ${quote(state.reportName)}\ndocx = "article.docx"\n\n[ui]\nlanguage = ${quote(state.uiLanguage)}\n${publishGithub}\n[markdown]\npreset = ${quote(state.preset)}\nfront_matter = ${quote(state.frontMatter)}\ninclude_title = true\ninclude_source_block = ${state.includeSourceBlock}\ninclude_cover_image = ${state.includeCoverImage}\nheading_offset = 0\n${sourceBlock}${frontMatterFields}\n[images]\ndownload = ${state.downloadImages}\ndirectory = "images"\nfilename_pattern = "img_{index:03d}.{ext}"\nmarkdown_path = ${quote(state.imagePath)}\n\n[videos]\ndownload = ${state.downloadVideos}\ndirectory = "videos"\nfilename_pattern = "video_{index:03d}.{ext}"\nmarkdown_path = ${quote(state.videoPath)}\n\n[docx]\nenabled = ${state.docxEnabled}\npandoc_path = "pandoc"\nreference_doc = ""\n`;
});

const markdownExample = computed(() => {
  const frontMatter =
    state.frontMatter === 'yaml'
      ? [
          '---',
          `title: "${demoArticle.title}"`,
          `author: "${demoArticle.author}"`,
          `platform: "${demoArticle.platform}"`,
          `source_url: "${demoArticle.sourceUrl}"`,
          `published_at: "${demoArticle.publishedAt}"`,
          '---',
          ''
        ]
      : [];

  const sourceBlock = state.includeSourceBlock
    ? [
        `> Source: ${demoArticle.platform}`,
        `> Author: ${demoArticle.author}`,
        `> Original: ${demoArticle.sourceUrl}`,
        ''
      ]
    : [];

  const imagePath = state.downloadImages
    ? renderMediaPath(state.imagePath, 'images', 'img_001.jpg')
    : 'https://mmbiz.qpic.cn/example.png';
  const coverImage = state.downloadImages
    ? state.imagePath === '{directory}/{filename}'
      ? '![cover](images/cover.jpg)'
      : `![cover](${renderMediaPath(state.imagePath, 'images', 'cover.jpg')})`
    : '![cover](https://mmbiz.qpic.cn/cover.jpg)';
  const coverBlock = state.includeCoverImage ? [coverImage, '', '---', ''] : [];

  return [
    ...frontMatter,
    `# ${demoArticle.title}`,
    '',
    ...sourceBlock,
    ...(sourceBlock.length ? ['---', ''] : []),
    ...coverBlock,
    `## ${ui.value.sampleHeading}`,
    '',
    ui.value.sampleBody,
    '',
    `[${ui.value.sampleLink}](${demoArticle.sourceUrl})`,
    '',
    `![${isEnglish.value ? 'WeChat article image' : '微信公众号文章配图'}](${imagePath})`,
    '',
    '```ts',
    `const url = '${demoArticle.sourceUrl}';`,
    'await magicmd(url);',
    '```'
  ].join('\n');
});

async function copyToml() {
  const content =
    activePreview.value === 'toml'
      ? toml.value
      : activePreview.value === 'markdown'
        ? markdownExample.value
        : outputTree.value;

  try {
    await navigator.clipboard.writeText(content);
    copyState.value = 'copied';
  } catch {
    copyState.value = 'failed';
  } finally {
    window.setTimeout(() => {
      copyState.value = 'idle';
    }, 1800);
  }
}

function downloadToml() {
  const content =
    activePreview.value === 'toml'
      ? toml.value
      : activePreview.value === 'markdown'
        ? markdownExample.value
        : outputTree.value;
  const filename =
    activePreview.value === 'toml'
      ? '.magicmd.toml'
      : activePreview.value === 'markdown'
        ? state.markdownName
        : 'output-structure.txt';
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <section class="config-builder">
    <div class="preset-strip" aria-label="MagicMD presets">
      <button
        v-for="preset in presetList"
        :key="preset"
        :class="{ active: state.preset === preset }"
        type="button"
        @click="applyPreset(preset)"
      >
        <span>{{ presetLabels[preset] }}</span>
        <small>{{ presetDetails[preset] }}</small>
      </button>
    </div>

    <div class="builder-workspace">
      <div class="builder-panel">
        <div class="panel-heading">
          <span>{{ ui.step }}</span>
          <strong>{{ ui.panelTitle }}</strong>
          <p>{{ ui.panelDescription }}</p>
        </div>

        <section class="builder-section">
          <div class="section-title">
            <span>{{ ui.basicSection }}</span>
          </div>

          <div class="field-grid">
            <label>
              <span class="field-label">
                <span>{{ ui.uiLanguage }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('uiLanguage')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('uiLanguage') }}</span>
                </span>
              </span>
              <select v-model="state.uiLanguage" name="uiLanguage">
                <option value="zh-CN">{{ ui.chinese }}</option>
                <option value="en-US">{{ ui.english }}</option>
              </select>
            </label>
            <label class="wide-field">
              <span class="field-label">
                <span>{{ ui.packageName }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('packageName')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('packageName') }}</span>
                </span>
              </span>
              <input v-model="state.packageName" name="packageName" autocomplete="off" />
            </label>
            <label>
              <span class="field-label">
                <span>{{ ui.markdownName }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('markdownName')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('markdownName') }}</span>
                </span>
              </span>
              <input v-model="state.markdownName" name="markdownName" autocomplete="off" />
            </label>
            <label v-if="advancedOpen">
              <span class="field-label">
                <span>{{ ui.metadataName }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('metadataName')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('metadataName') }}</span>
                </span>
              </span>
              <input v-model="state.metadataName" name="metadataName" autocomplete="off" />
            </label>
            <label v-if="advancedOpen">
              <span class="field-label">
                <span>{{ ui.reportName }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('reportName')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('reportName') }}</span>
                </span>
              </span>
              <input v-model="state.reportName" name="reportName" autocomplete="off" />
            </label>
          </div>

          <button
            class="advanced-toggle"
            type="button"
            :aria-expanded="advancedOpen.toString()"
            @click="advancedOpen = !advancedOpen"
          >
            {{ advancedOpen ? ui.hideAdvanced : ui.showAdvanced }}
          </button>
        </section>

        <section v-if="advancedOpen" class="builder-section">
          <div class="section-title">
            <span>{{ ui.advancedSection }}</span>
          </div>

          <div class="section-title compact-title">
            <span>{{ ui.markdownSection }}</span>
          </div>

          <div class="field-grid">
            <label>
              <span class="field-label">
                <span>{{ ui.frontMatter }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('frontMatter')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('frontMatter') }}</span>
                </span>
              </span>
              <select v-model="state.frontMatter" name="frontMatter">
                <option value="yaml">{{ ui.yaml }}</option>
                <option value="none">{{ ui.none }}</option>
              </select>
            </label>
          </div>

          <div class="toggle-row">
            <label>
              <input v-model="state.includeSourceBlock" type="checkbox" />
              <span>{{ ui.includeSourceBlock }}</span>
              <span class="help-tip" tabindex="0" :aria-label="helpText('includeSourceBlock')">
                <span class="help-icon">?</span>
                <span class="help-popover">{{ helpText('includeSourceBlock') }}</span>
              </span>
            </label>
            <label>
              <input v-model="state.includeCoverImage" type="checkbox" />
              <span>{{ ui.includeCoverImage }}</span>
              <span class="help-tip" tabindex="0" :aria-label="helpText('includeCoverImage')">
                <span class="help-icon">?</span>
                <span class="help-popover">{{ helpText('includeCoverImage') }}</span>
              </span>
            </label>
          </div>
        </section>

        <section v-if="advancedOpen" class="builder-section">
          <div class="section-title">
            <span>{{ ui.mediaSection }}</span>
          </div>

          <div class="field-grid">
            <label class="wide-field">
              <span class="field-label">
                <span>{{ ui.imagePath }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('imagePath')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('imagePath') }}</span>
                </span>
              </span>
              <input v-model="state.imagePath" name="imagePath" autocomplete="off" />
            </label>
            <label class="wide-field">
              <span class="field-label">
                <span>{{ ui.videoPath }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('videoPath')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('videoPath') }}</span>
                </span>
              </span>
              <input v-model="state.videoPath" name="videoPath" autocomplete="off" />
            </label>
          </div>

          <div class="toggle-row">
            <label>
              <input v-model="state.downloadImages" type="checkbox" />
              <span>{{ ui.downloadImages }}</span>
              <span class="help-tip" tabindex="0" :aria-label="helpText('downloadImages')">
                <span class="help-icon">?</span>
                <span class="help-popover">{{ helpText('downloadImages') }}</span>
              </span>
            </label>
            <label>
              <input v-model="state.downloadVideos" type="checkbox" />
              <span>{{ ui.downloadVideos }}</span>
              <span class="help-tip" tabindex="0" :aria-label="helpText('downloadVideos')">
                <span class="help-icon">?</span>
                <span class="help-popover">{{ helpText('downloadVideos') }}</span>
              </span>
            </label>
          </div>
        </section>

        <section v-if="advancedOpen" class="builder-section">
          <div class="section-title">
            <span>{{ ui.githubSection }}</span>
          </div>

          <div class="toggle-row">
            <label>
              <input v-model="state.publishEnabled" type="checkbox" />
              <span>{{ ui.publishEnabled }}</span>
              <span class="help-tip" tabindex="0" :aria-label="helpText('publishEnabled')">
                <span class="help-icon">?</span>
                <span class="help-popover">{{ helpText('publishEnabled') }}</span>
              </span>
            </label>
          </div>

          <div v-if="state.publishEnabled" class="field-grid">
            <label class="wide-field">
              <span class="field-label">
                <span>{{ ui.publishRepo }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('publishRepo')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('publishRepo') }}</span>
                </span>
              </span>
              <input v-model="state.publishRepo" name="publishRepo" autocomplete="off" />
            </label>
            <label>
              <span class="field-label">
                <span>{{ ui.publishTargetDir }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('publishTargetDir')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('publishTargetDir') }}</span>
                </span>
              </span>
              <input v-model="state.publishTargetDir" name="publishTargetDir" autocomplete="off" />
            </label>
            <label>
              <span class="field-label">
                <span>{{ ui.publishBranch }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('publishBranch')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('publishBranch') }}</span>
                </span>
              </span>
              <input v-model="state.publishBranch" name="publishBranch" autocomplete="off" />
            </label>
            <label class="wide-field">
              <span class="field-label">
                <span>{{ ui.publishCommitMessage }}</span>
                <span class="help-tip" tabindex="0" :aria-label="helpText('publishCommitMessage')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('publishCommitMessage') }}</span>
                </span>
              </span>
              <input
                v-model="state.publishCommitMessage"
                name="publishCommitMessage"
                autocomplete="off"
              />
            </label>
          </div>

          <div v-if="state.publishEnabled" class="toggle-row">
            <label>
              <input v-model="state.publishCreatePr" type="checkbox" />
              <span>{{ ui.publishCreatePr }}</span>
              <span class="help-tip" tabindex="0" :aria-label="helpText('publishCreatePr')">
                <span class="help-icon">?</span>
                <span class="help-popover">{{ helpText('publishCreatePr') }}</span>
              </span>
            </label>
            <label>
              <input v-model="state.publishOverwrite" type="checkbox" />
              <span>{{ ui.publishOverwrite }}</span>
              <span class="help-tip" tabindex="0" :aria-label="helpText('publishOverwrite')">
                <span class="help-icon">?</span>
                <span class="help-popover">{{ helpText('publishOverwrite') }}</span>
              </span>
            </label>
          </div>
        </section>

        <section v-if="advancedOpen" class="builder-section">
          <div class="toggle-row">
            <label>
              <input v-model="state.docxEnabled" type="checkbox" />
              <span>{{ ui.docxEnabled }}</span>
              <span class="help-tip" tabindex="0" :aria-label="helpText('docxEnabled')">
                <span class="help-icon">?</span>
                <span class="help-popover">{{ helpText('docxEnabled') }}</span>
              </span>
            </label>
          </div>
        </section>
      </div>

      <div class="preview-panel">
        <div class="preview-summary">
          <div>
            <span>{{ ui.outputSummary }}</span>
            <strong>{{ outputTitle }}</strong>
            <p>
              {{ outputPreview }}
              <span class="help-tip" tabindex="0" :aria-label="helpText('outputPreview')">
                <span class="help-icon">?</span>
                <span class="help-popover">{{ helpText('outputPreview') }}</span>
              </span>
            </p>
          </div>
          <div class="preset-chip-list">
            <code>{{ state.frontMatter === 'yaml' ? ui.metadataOn : ui.metadataOff }}</code>
            <code>{{
              state.uiLanguage === 'zh-CN' ? ui.terminalChinese : ui.terminalEnglish
            }}</code>
            <code>{{ mediaPreview }}</code>
            <code v-if="state.docxEnabled">{{ ui.wordOutput }}</code>
            <code v-if="state.publishEnabled">{{ ui.githubOutput }}</code>
          </div>
        </div>

        <div class="toml-panel">
          <div class="toml-toolbar">
            <div>
              <span>
                {{ ui.previewTabs[activePreview] }}
                <span class="help-tip" tabindex="0" :aria-label="helpText('generated')">
                  <span class="help-icon">?</span>
                  <span class="help-popover">{{ helpText('generated') }}</span>
                </span>
              </span>
              <small>{{ ui.generated }}</small>
            </div>
            <div>
              <button type="button" @click="copyToml">
                {{
                  copyState === 'copied'
                    ? ui.copied
                    : copyState === 'failed'
                      ? ui.copyFailed
                      : ui.copy
                }}
              </button>
              <button type="button" @click="downloadToml">{{ ui.download }}</button>
            </div>
          </div>

          <div class="preview-tabs" role="tablist">
            <button
              v-for="tab in previewTabs"
              :key="tab"
              :class="{ active: activePreview === tab }"
              type="button"
              role="tab"
              @click="activePreview = tab"
            >
              {{ ui.previewTabs[tab] }}
            </button>
          </div>

          <pre v-if="activePreview === 'toml'">{{ toml }}</pre>
          <pre v-else-if="activePreview === 'markdown'" class="markdown-preview-code">{{
            markdownExample
          }}</pre>
          <pre v-else class="structure-preview-code">{{ outputTree }}</pre>

          <p class="cli-hint">{{ ui.cliHint }}</p>
        </div>

        <div class="usage-strip">
          <span>{{ ui.outputRoot }}</span>
          <code v-if="state.downloadImages">{{ ui.imagesDir }}</code>
          <code v-if="state.downloadVideos">{{ ui.videosDir }}</code>
        </div>
      </div>
    </div>
  </section>
</template>
