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

const agentPrompt = computed(() =>
  isEnglish.value
    ? 'Use MagicMD to convert these public article links into Markdown packages, then tell me which ones need manual review.'
    : '请用 MagicMD 把这些公开文章链接转换成 Markdown 内容包，并告诉我哪些需要人工复核。'
);

const heroCopy = computed(() =>
  isEnglish.value
    ? {
        eyebrow: 'Fast start',
        title: 'CLI, Agent Skill, or SDK: one conversion core',
        description:
          'Start from a command line, a natural-language Agent request, or a Python backend. MagicMD keeps the output package consistent either way.',
        single: 'Instant conversion',
        batch: 'Batch mode',
        agent: 'Agent request',
        copy: 'Copy',
        copied: 'Copied',
        failed: 'Copy failed',
        outputHint: 'Ready-to-use output'
      }
    : {
        eyebrow: '极速上手',
        title: 'CLI、Agent Skill、SDK，共用同一套转换核心',
        description:
          '你可以从命令行开始，也可以让 Agent 用一句话批量整理，或者在 Python 后端直接 import。MagicMD 保持同一套内容包输出规则。',
        single: '极速单篇转换',
        batch: '批量模式',
        agent: 'Agent 一句话入口',
        copy: '复制命令',
        copied: '已复制',
        failed: '复制失败',
        outputHint: '开箱即用的输出'
      }
);

const entrypoints = computed(() =>
  isEnglish.value
    ? [
        {
          label: 'CLI',
          title: 'For local archiving',
          detail:
            'Install once, convert one URL or a whole urls.txt list, and keep reports beside the Markdown.'
        },
        {
          label: 'Agent Skill',
          title: 'For natural-language batches',
          detail:
            'Ask Codex, Claude Code, or another agent to convert, inspect warnings, and flag manual review items.'
        },
        {
          label: 'Python SDK',
          title: 'For backend workflows',
          detail:
            'Import MagicMD from Python and store Markdown, metadata, reports, and media paths in your own system.'
        }
      ]
    : [
        {
          label: 'CLI',
          title: '本地归档入口',
          detail: '安装一次，转换单条链接或整份 urls.txt，让 Markdown、metadata 和报告一起落盘。'
        },
        {
          label: 'Agent Skill',
          title: '自然语言批量整理',
          detail:
            '让 Codex、Claude Code 等 Agent 调用 MagicMD，转换后检查 warning 并标记人工复核项。'
        },
        {
          label: 'Python SDK',
          title: '后端系统接入',
          detail:
            '在 Python 项目里直接 import，把 Markdown、metadata、报告和媒体路径写入自己的系统。'
        }
      ]
);

const features = computed(() =>
  isEnglish.value
    ? [
        {
          title: 'Deep WeChat optimization',
          detail:
            'Downloads images, extracts video links, filters editor assets, and keeps source metadata.'
        },
        {
          title: 'Direct, cleaner links',
          detail:
            'Restores redirect wrappers where possible, so Markdown links open the real target.'
        },
        {
          title: 'Polished code blocks',
          detail: 'Removes copy controls, line numbers, language noise, and article chrome.'
        },
        {
          title: 'Traceable batch runs',
          detail:
            'Convert a urls.txt file and inspect a report for failures, warnings, and review items.'
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
        {{
          copyState === 'copied'
            ? heroCopy.copied
            : copyState === 'failed'
              ? heroCopy.failed
              : heroCopy.copy
        }}
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
        <p>{{ heroCopy.agent }}</p>
        <pre><code>{{ agentPrompt }}</code></pre>
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

    <div class="mm-entrypoints">
      <article v-for="entrypoint in entrypoints" :key="entrypoint.label">
        <span>{{ entrypoint.label }}</span>
        <strong>{{ entrypoint.title }}</strong>
        <p>{{ entrypoint.detail }}</p>
      </article>
    </div>

    <div class="mm-features">
      <article v-for="feature in features" :key="feature.title">
        <strong>{{ feature.title }}</strong>
        <span>{{ feature.detail }}</span>
      </article>
    </div>
  </section>
</template>
