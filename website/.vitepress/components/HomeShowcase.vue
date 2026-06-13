<script setup lang="ts">
import { computed, ref } from 'vue';
import { useData } from 'vitepress';

const { lang } = useData();

const isEnglish = computed(() => lang.value.startsWith('en'));

const outputTitle = computed(() => (isEnglish.value ? 'Output package' : '输出内容包'));
const copyState = ref<'idle' | 'copied' | 'failed'>('idle');

const command = `uv tool install magicmd
magicmd "https://mp.weixin.qq.com/s/example"`;

const batchCommand = `magicmd batch urls.txt -o output/`;

const heroCopy = computed(() =>
  isEnglish.value
    ? {
        eyebrow: 'Fast start',
        title: 'Your first polished Markdown package in 2 commands',
        description:
          'Install the CLI, paste an article URL, and let MagicMD optimize media, code blocks, metadata, and reports for you.',
        single: 'Instant conversion',
        batch: 'Batch mode',
        copy: 'Copy',
        copied: 'Copied',
        failed: 'Copy failed',
        outputHint: 'Ready-to-use output'
      }
    : {
        eyebrow: '极速上手',
        title: '2 条命令，生成第一份高质量 Markdown 内容包',
        description: '安装 CLI，粘贴公开文章链接，MagicMD 会自动完成正文提取、媒体本地化、代码块清理、来源信息和转换报告生成。',
        single: '极速单篇转换',
        batch: '批量模式',
        copy: '复制命令',
        copied: '已复制',
        failed: '复制失败',
        outputHint: '开箱即用的输出'
      }
);

const features = computed(() =>
  isEnglish.value
    ? [
        {
          title: 'Deep WeChat optimization',
          detail: 'Downloads images, extracts video links, filters editor assets, and keeps source metadata.'
        },
        {
          title: 'Direct, cleaner links',
          detail: 'Restores redirect wrappers where possible, so Markdown links open the real target.'
        },
        {
          title: 'Polished code blocks',
          detail: 'Removes copy controls, line numbers, language noise, and article chrome.'
        },
        {
          title: 'Traceable batch runs',
          detail: 'Convert a urls.txt file and inspect a report for failures, warnings, and review items.'
        },
        {
          title: 'Custom output rules',
          detail: 'Tune package folders, Markdown names, metadata, reports, and media paths.'
        },
        {
          title: 'CLI and Skill ready',
          detail: 'The local CLI, npm wrapper, PyPI package, and Agent Skill share the same core.'
        }
      ]
    : [
        {
          title: '微信公众号深度优化',
          detail: '下载图片，提取视频链接并尝试本地化，过滤编辑器素材和空 GIF，保留来源与转换报告。'
        },
        {
          title: '掘金链接飞速净化',
          detail: '尽量还原跳转链接背后的真实目标地址，让 Markdown 里的链接可以直接打开。'
        },
        {
          title: 'CSDN 代码块深度清理',
          detail: '清理复制按钮、行号、语言标签错乱和编辑器控件，减少技术文章里的无关噪声。'
        },
        {
          title: '批量转换可追踪',
          detail: '一份 urls.txt 可以批量转换，并生成报告，方便你知道哪些文章需要人工复核。'
        },
        {
          title: '支持自定义输出',
          detail: '自定义内容包目录、Markdown 文件名、metadata、报告文件名和媒体路径。'
        },
        {
          title: 'CLI 与 Agent Skill 共用核心',
          detail: '本地命令行、npm wrapper、PyPI 安装和 Agent Skill 都走同一套转换能力。'
        }
      ]
);

const useCases = computed(() =>
  isEnglish.value
    ? ['Fast conversion', 'Batch processing', 'Custom output', 'AI knowledge input']
    : ['极速转换', '批量处理', '自定义输出', 'AI 知识库输入']
);

async function copyCommand() {
  try {
    await navigator.clipboard.writeText(command);
    copyState.value = 'copied';
  } catch {
    copyState.value = 'failed';
  } finally {
    window.setTimeout(() => {
      copyState.value = 'idle';
    }, 1600);
  }
}
</script>

<template>
  <section class="mm-showcase">
    <div class="mm-start">
      <div class="mm-start-copy">
        <span>{{ heroCopy.eyebrow }}</span>
        <h2>{{ heroCopy.title }}</h2>
        <p>{{ heroCopy.description }}</p>
      </div>
      <button type="button" class="mm-copy-button" @click="copyCommand">
        {{ copyState === 'copied' ? heroCopy.copied : copyState === 'failed' ? heroCopy.failed : heroCopy.copy }}
      </button>
    </div>

    <div class="mm-flow">
      <div class="mm-command">
        <span class="mm-dot"></span>
        <span class="mm-dot"></span>
        <span class="mm-dot"></span>
        <p>{{ heroCopy.single }}</p>
        <pre><code>{{ command }}</code></pre>
        <p>{{ heroCopy.batch }}</p>
        <pre><code>{{ batchCommand }}</code></pre>
      </div>

      <div class="mm-output">
        <p class="mm-output-title">{{ heroCopy.outputHint }}</p>
        <strong>{{ outputTitle }}</strong>
        <pre><code>output/article-title/
├── article.md
├── metadata.json
├── extraction-report.json
└── images/
    ├── img_001.png
    └── img_002.png</code></pre>
      </div>
    </div>

    <div class="mm-use-cases" aria-label="MagicMD workflows">
      <span v-for="item in useCases" :key="item">{{ item }}</span>
    </div>

    <div class="mm-features">
      <article v-for="feature in features" :key="feature.title">
        <strong>{{ feature.title }}</strong>
        <span>{{ feature.detail }}</span>
      </article>
    </div>
  </section>
</template>
