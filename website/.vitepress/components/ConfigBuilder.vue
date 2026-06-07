<script setup lang="ts">
import { computed, reactive, ref } from 'vue';

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

const presetLabels: Record<Preset, string> = {
  default: '通用 Markdown',
  plain: '纯净 Markdown',
  hugo: 'Hugo 内容包',
  docusaurus: 'Docusaurus 文档'
};

const outputPreview = computed(() => {
  return `${state.packageName}/${state.markdownName}`;
});

const mediaPreview = computed(() => {
  if (!state.downloadImages && !state.downloadVideos) return '只保留远程链接';
  if (state.downloadImages && state.downloadVideos) return 'images/ + videos/';
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
          'title: "MagicMD 示例文章"',
          'author: "公众号作者"',
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
        '> Author: 公众号作者',
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
    '# MagicMD 示例文章',
    '',
    ...sourceBlock,
    '## 转换后的正文',
    '',
    'MagicMD 会把文章正文、标题、链接、图片、视频和代码块整理成可维护的 Markdown。',
    '',
    '[查看原文](https://mp.weixin.qq.com/s/example)',
    '',
    `![文章配图](${imagePath})`,
    '',
    `[视频](${videoPath})`,
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
        <span>Step 1</span>
        <strong>把输出规则定下来</strong>
        <p>选择发布目标后，再微调文件名和媒体路径。</p>
      </div>

      <div class="field-group">
        <label for="preset">发布目标</label>
        <select id="preset" v-model="state.preset" @change="applyPreset(state.preset)">
          <option value="default">默认 Markdown</option>
          <option value="plain">Plain Markdown</option>
          <option value="hugo">Hugo</option>
          <option value="docusaurus">Docusaurus</option>
        </select>
      </div>

      <div class="field-grid">
        <label class="wide-field">
          内容包目录
          <input v-model="state.packageName" />
        </label>
        <label>
          Markdown 文件名
          <input v-model="state.markdownName" />
        </label>
        <label>
          Metadata 文件名
          <input v-model="state.metadataName" />
        </label>
        <label>
          报告文件名
          <input v-model="state.reportName" />
        </label>
      </div>

      <div class="field-grid">
        <label>
          Front matter
          <select v-model="state.frontMatter">
            <option value="yaml">生成 YAML</option>
            <option value="none">不生成</option>
          </select>
        </label>
        <label class="wide-field">
          图片 Markdown 路径
          <input v-model="state.imagePath" />
        </label>
        <label class="wide-field">
          视频 Markdown 路径
          <input v-model="state.videoPath" />
        </label>
      </div>

      <div class="toggle-row">
        <label>
          <input v-model="state.includeSourceBlock" type="checkbox" />
          显示来源信息块
        </label>
        <label>
          <input v-model="state.downloadImages" type="checkbox" />
          下载图片
        </label>
        <label>
          <input v-model="state.downloadVideos" type="checkbox" />
          下载视频
        </label>
      </div>
    </div>

    <div class="toml-panel">
      <div class="toml-toolbar">
        <div>
          <span>.magicmd.toml</span>
          <small>实时生成，可直接落到项目根目录</small>
        </div>
        <div>
          <button type="button" @click="copyToml">
            {{ copyState === 'copied' ? '已复制' : copyState === 'failed' ? '复制失败' : '复制' }}
          </button>
          <button type="button" @click="downloadToml">下载</button>
        </div>
      </div>
      <pre>{{ toml }}</pre>
      <p class="cli-hint">保存后运行：magicmd URL --config .magicmd.toml</p>
    </div>

    <aside class="builder-side">
      <div class="side-card side-card-primary">
        <span>当前预设</span>
        <strong>{{ presetLabels[state.preset] }}</strong>
        <p>{{ outputPreview }}</p>
        <div class="preset-chip-list">
          <code>{{ state.frontMatter === 'yaml' ? 'YAML front matter' : 'No front matter' }}</code>
          <code>{{ mediaPreview }}</code>
        </div>
      </div>

      <div class="side-card markdown-preview-card">
        <div class="markdown-preview-heading">
          <span>生成后的 {{ state.markdownName }} 示例</span>
          <small>随左侧配置实时变化</small>
        </div>
        <pre>{{ markdownExample }}</pre>
      </div>
    </aside>
  </section>
</template>
