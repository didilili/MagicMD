<script setup lang="ts">
import { computed } from 'vue';
import { useData } from 'vitepress';

const { lang } = useData();

const isEnglish = computed(() => lang.value.startsWith('en'));

const outputTitle = computed(() => (isEnglish.value ? 'Output package' : '输出内容包'));

const platforms = computed(() =>
  isEnglish.value
    ? [
        {
          name: 'WeChat Official Accounts',
          detail: 'Local images, video links/downloads, editor asset filtering, and source metadata.'
        },
        {
          name: 'Juejin',
          detail: 'Normalized headings, reliable code blocks, and direct outbound links.'
        },
        {
          name: 'CSDN',
          detail: 'Removes copy controls, line numbers, noisy code widgets, and keeps article structure.'
        }
      ]
    : [
        {
          name: '微信公众号',
          detail: '图片本地化、视频链接/下载、过滤编辑器素材、保留来源信息'
        },
        {
          name: '掘金',
          detail: '标题层级归一、代码块保真、外链直达真实目标地址'
        },
        {
          name: 'CSDN',
          detail: '清理复制控件、行号和异常代码块，保留技术文章结构'
        }
      ]
);
</script>

<template>
  <section class="mm-showcase">
    <div class="mm-flow">
      <div class="mm-command">
        <span class="mm-dot"></span>
        <span class="mm-dot"></span>
        <span class="mm-dot"></span>
        <pre><code>magicmd "https://mp.weixin.qq.com/s/example"
magicmd batch urls.txt -o output/</code></pre>
      </div>

      <div class="mm-output">
        <p class="mm-output-title">{{ outputTitle }}</p>
        <pre><code>output/article-title/
├── article.md
├── metadata.json
├── extraction-report.json
└── images/
    ├── img_001.png
    └── img_002.png</code></pre>
      </div>
    </div>

    <div class="mm-platforms">
      <article v-for="platform in platforms" :key="platform.name">
        <strong>{{ platform.name }}</strong>
        <span>{{ platform.detail }}</span>
      </article>
    </div>
  </section>
</template>
