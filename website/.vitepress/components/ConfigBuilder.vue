<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useData } from 'vitepress';

type Preset = 'default' | 'plain' | 'hugo' | 'docusaurus';
type FrontMatter = 'yaml' | 'none';

type BuilderState = {
  preset: Preset;
  packageName: string;
  markdownName: string;
  metadataName: string;
  reportName: string;
  frontMatter: FrontMatter;
  includeSourceBlock: boolean;
  imagePath: string;
  videoPath: string;
  downloadImages: boolean;
  downloadVideos: boolean;
};

const presetDefaults: Record<Preset, Partial<BuilderState>> = {
  default: {
    markdownName: 'article.md',
    frontMatter: 'yaml',
    includeSourceBlock: true,
    imagePath: '{directory}/{filename}',
    videoPath: '{directory}/{filename}'
  },
  plain: {
    markdownName: 'article.md',
    frontMatter: 'none',
    includeSourceBlock: false,
    imagePath: '{directory}/{filename}',
    videoPath: '{directory}/{filename}'
  },
  hugo: {
    markdownName: 'index.md',
    frontMatter: 'yaml',
    includeSourceBlock: true,
    imagePath: '{directory}/{filename}',
    videoPath: '{directory}/{filename}'
  },
  docusaurus: {
    markdownName: 'index.md',
    frontMatter: 'yaml',
    includeSourceBlock: false,
    imagePath: './{directory}/{filename}',
    videoPath: './{directory}/{filename}'
  }
};

const state = reactive<BuilderState>({
  preset: 'default',
  packageName: '{date}-{slug}',
  markdownName: 'article.md',
  metadataName: 'metadata.json',
  reportName: 'extraction-report.json',
  frontMatter: 'yaml',
  includeSourceBlock: true,
  imagePath: '{directory}/{filename}',
  videoPath: '{directory}/{filename}',
  downloadImages: true,
  downloadVideos: true
});

const copyState = ref<'idle' | 'copied' | 'failed'>('idle');

const { lang } = useData();

const isEnglish = computed(() => lang.value.startsWith('en'));

const ui = computed(() =>
  isEnglish.value
    ? {
        step: 'Step 1',
        panelTitle: 'Lock in your output rules',
        panelDescription: 'Pick a publishing target, then tune filenames and media paths.',
        preset: 'Publishing target',
        presetOptions: {
          default: 'Default Markdown',
          plain: 'Plain Markdown',
          hugo: 'Hugo content bundle',
          docusaurus: 'Docusaurus docs'
        },
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
        downloadImages: 'Download images',
        downloadVideos: 'Download videos',
        generated: 'Generated in real time. Save it at your project root.',
        copied: 'Copied',
        copyFailed: 'Copy failed',
        copy: 'Copy',
        download: 'Download',
        cliHint: 'Save it, then run: magicmd URL --config .magicmd.toml',
        currentPreset: 'Current preset',
        localOnly: 'remote links only',
        imagesAndVideos: 'images/ + videos/',
        markdownPreviewTitle: (name: string) => `Preview of ${name}`,
        markdownPreviewHint: 'Updates as you change the config',
        sampleTitle: 'A sample article converted by MagicMD',
        sampleAuthor: 'Article Author',
        sampleHeading: 'Converted content',
        sampleBody:
          'MagicMD turns article body text, headings, links, images, videos, and code blocks into maintainable Markdown.',
        sampleLink: 'Read original'
      }
    : {
        step: 'Step 1',
        panelTitle: '把输出规则定下来',
        panelDescription: '选择发布目标后，再微调文件名和媒体路径。',
        preset: '发布目标',
        presetOptions: {
          default: '通用 Markdown',
          plain: '纯净 Markdown',
          hugo: 'Hugo 内容包',
          docusaurus: 'Docusaurus 文档'
        },
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
        downloadImages: '下载图片',
        downloadVideos: '下载视频',
        generated: '实时生成，可直接落到项目根目录',
        copied: '已复制',
        copyFailed: '复制失败',
        copy: '复制',
        download: '下载',
        cliHint: '保存后运行：magicmd URL --config .magicmd.toml',
        currentPreset: '当前预设',
        localOnly: '只保留远程链接',
        imagesAndVideos: 'images/ + videos/',
        markdownPreviewTitle: (name: string) => `生成后的 ${name} 示例`,
        markdownPreviewHint: '随左侧配置实时变化',
        sampleTitle: 'MagicMD 示例文章',
        sampleAuthor: '公众号作者',
        sampleHeading: '转换后的正文',
        sampleBody: 'MagicMD 会把文章正文、标题、链接、图片、视频和代码块整理成可维护的 Markdown。',
        sampleLink: '查看原文'
      }
);

const presetLabels = computed<Record<Preset, string>>(() => ui.value.presetOptions);

const outputPreview = computed(() => {
  return `${state.packageName}/${state.markdownName}`;
});

const mediaPreview = computed(() => {
  if (!state.downloadImages && !state.downloadVideos) return ui.value.localOnly;
  if (state.downloadImages && state.downloadVideos) return ui.value.imagesAndVideos;
  return state.downloadImages ? 'images/' : 'videos/';
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

  return `[output]\ndirectory = "output"\n\n[output.naming]\npackage = ${quote(state.packageName)}\nmarkdown = ${quote(state.markdownName)}\nmetadata = ${quote(state.metadataName)}\nreport = ${quote(state.reportName)}\n\n[markdown]\npreset = ${quote(state.preset)}\nfront_matter = ${quote(state.frontMatter)}\ninclude_title = true\ninclude_source_block = ${state.includeSourceBlock}\nheading_offset = 0\n${sourceBlock}${frontMatterFields}\n[images]\ndownload = ${state.downloadImages}\ndirectory = "images"\nfilename_pattern = "img_{index:03d}.{ext}"\nmarkdown_path = ${quote(state.imagePath)}\n\n[videos]\ndownload = ${state.downloadVideos}\ndirectory = "videos"\nfilename_pattern = "video_{index:03d}.{ext}"\nmarkdown_path = ${quote(state.videoPath)}\n`;
});

const markdownExample = computed(() => {
  const frontMatter =
    state.frontMatter === 'yaml'
      ? [
          '---',
          `title: "${ui.value.sampleTitle}"`,
          `author: "${ui.value.sampleAuthor}"`,
          'platform: "wechat"',
          'source_url: "https://mp.weixin.qq.com/s/example"',
          'published_at: "2026-06-07T09:30:00+08:00"',
          '---',
          ''
        ]
      : [];

  const sourceBlock = state.includeSourceBlock
    ? [
        '> Source: wechat',
        `> Author: ${ui.value.sampleAuthor}`,
        '> Original: https://mp.weixin.qq.com/s/example',
        ''
      ]
    : [];

  const imagePath = state.downloadImages
    ? renderMediaPath(state.imagePath, 'images', 'img_001.png')
    : 'https://mmbiz.qpic.cn/example.png';
  const videoPath = state.downloadVideos
    ? renderMediaPath(state.videoPath, 'videos', 'video_001.mp4')
    : 'https://mpvideo.qpic.cn/example.mp4';

  return [
    ...frontMatter,
    `# ${ui.value.sampleTitle}`,
    '',
    ...sourceBlock,
    `## ${ui.value.sampleHeading}`,
    '',
    ui.value.sampleBody,
    '',
    `[${ui.value.sampleLink}](https://mp.weixin.qq.com/s/example)`,
    '',
    `![${isEnglish.value ? 'Article image' : '文章配图'}](${imagePath})`,
    '',
    `[${isEnglish.value ? 'Video' : '视频'}](${videoPath})`,
    '',
    '```ts',
    "const url = 'https://mp.weixin.qq.com/s/example';",
    'await magicmd(url);',
    '```'
  ].join('\n');
});

async function copyToml() {
  try {
    await navigator.clipboard.writeText(toml.value);
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
  const blob = new Blob([toml.value], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = '.magicmd.toml';
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <section class="config-builder">
    <div class="builder-panel">
      <div class="panel-heading">
        <span>{{ ui.step }}</span>
        <strong>{{ ui.panelTitle }}</strong>
        <p>{{ ui.panelDescription }}</p>
      </div>

      <div class="field-group">
        <label for="preset">{{ ui.preset }}</label>
        <select id="preset" v-model="state.preset" @change="applyPreset(state.preset)">
          <option value="default">{{ ui.presetOptions.default }}</option>
          <option value="plain">{{ ui.presetOptions.plain }}</option>
          <option value="hugo">{{ ui.presetOptions.hugo }}</option>
          <option value="docusaurus">{{ ui.presetOptions.docusaurus }}</option>
        </select>
      </div>

      <div class="field-grid">
        <label class="wide-field">
          {{ ui.packageName }}
          <input v-model="state.packageName" />
        </label>
        <label>
          {{ ui.markdownName }}
          <input v-model="state.markdownName" />
        </label>
        <label>
          {{ ui.metadataName }}
          <input v-model="state.metadataName" />
        </label>
        <label>
          {{ ui.reportName }}
          <input v-model="state.reportName" />
        </label>
      </div>

      <div class="field-grid">
        <label>
          {{ ui.frontMatter }}
          <select v-model="state.frontMatter">
            <option value="yaml">{{ ui.yaml }}</option>
            <option value="none">{{ ui.none }}</option>
          </select>
        </label>
        <label class="wide-field">
          {{ ui.imagePath }}
          <input v-model="state.imagePath" />
        </label>
        <label class="wide-field">
          {{ ui.videoPath }}
          <input v-model="state.videoPath" />
        </label>
      </div>

      <div class="toggle-row">
        <label>
          <input v-model="state.includeSourceBlock" type="checkbox" />
          {{ ui.includeSourceBlock }}
        </label>
        <label>
          <input v-model="state.downloadImages" type="checkbox" />
          {{ ui.downloadImages }}
        </label>
        <label>
          <input v-model="state.downloadVideos" type="checkbox" />
          {{ ui.downloadVideos }}
        </label>
      </div>
    </div>

    <div class="toml-panel">
      <div class="toml-toolbar">
        <div>
          <span>.magicmd.toml</span>
          <small>{{ ui.generated }}</small>
        </div>
        <div>
          <button type="button" @click="copyToml">
            {{ copyState === 'copied' ? ui.copied : copyState === 'failed' ? ui.copyFailed : ui.copy }}
          </button>
          <button type="button" @click="downloadToml">{{ ui.download }}</button>
        </div>
      </div>
      <pre>{{ toml }}</pre>
      <p class="cli-hint">{{ ui.cliHint }}</p>
    </div>

    <aside class="builder-side">
      <div class="side-card side-card-primary">
        <span>{{ ui.currentPreset }}</span>
        <strong>{{ presetLabels[state.preset] }}</strong>
        <p>{{ outputPreview }}</p>
        <div class="preset-chip-list">
          <code>{{ state.frontMatter === 'yaml' ? 'YAML front matter' : 'No front matter' }}</code>
          <code>{{ mediaPreview }}</code>
        </div>
      </div>

      <div class="side-card markdown-preview-card">
        <div class="markdown-preview-heading">
          <span>{{ ui.markdownPreviewTitle(state.markdownName) }}</span>
          <small>{{ ui.markdownPreviewHint }}</small>
        </div>
        <pre>{{ markdownExample }}</pre>
      </div>
    </aside>
  </section>
</template>
