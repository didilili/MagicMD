import { defineConfig } from 'vitepress';

export default defineConfig({
  lang: 'zh-CN',
  title: 'MagicMD',
  description: '强大易用的文章转 Markdown 工具，一键转换微信公众号、掘金、CSDN 等公开文章。',
  base: '/',
  outDir: 'dist',
  srcExclude: ['README.md'],
  cleanUrls: true,
  lastUpdated: true,
  head: [
    ['meta', { name: 'theme-color', content: '#0f9f6e' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:site_name', content: 'MagicMD' }],
    ['meta', { property: 'og:locale', content: 'zh_CN' }]
  ],
  themeConfig: {
    logo: '/favicon.svg',
    siteTitle: 'MagicMD',
    nav: [
      { text: '快速开始', link: '/quick-start' },
      { text: '配置生成器', link: '/config-builder' },
      { text: '支持站点', link: '/supported-sites' },
      {
        text: '文档',
        items: [
          { text: '配置说明', link: '/config' },
          { text: '故障排查', link: '/troubleshooting' },
          { text: 'Release Notes', link: 'https://github.com/didilili/MagicMD/releases' }
        ]
      }
    ],
    sidebar: [
      {
        text: '开始使用',
        items: [
          { text: '快速开始', link: '/quick-start' },
          { text: '配置生成器', link: '/config-builder' },
          { text: '配置说明', link: '/config' }
        ]
      },
      {
        text: '能力边界',
        items: [
          { text: '支持站点', link: '/supported-sites' },
          { text: '故障排查', link: '/troubleshooting' }
        ]
      }
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/didilili/MagicMD' }
    ],
    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索'
          },
          modal: {
            displayDetails: '显示详细结果',
            resetButtonTitle: '清空搜索',
            backButtonTitle: '关闭搜索',
            noResultsText: '没有找到相关内容',
            footer: {
              selectText: '选择',
              selectKeyAriaLabel: '回车',
              navigateText: '切换',
              navigateUpKeyAriaLabel: '上箭头',
              navigateDownKeyAriaLabel: '下箭头',
              closeText: '关闭',
              closeKeyAriaLabel: 'Esc'
            }
          }
        }
      }
    },
    outline: {
      label: '本页目录',
      level: [2, 3]
    },
    docFooter: {
      prev: '上一页',
      next: '下一页'
    },
    lastUpdated: {
      text: '最后更新'
    },
    editLink: {
      pattern: 'https://github.com/didilili/MagicMD/edit/main/website/:path',
      text: '在 GitHub 上编辑此页'
    },
    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2026 didilili'
    },
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    sidebarMenuLabel: '菜单',
    returnToTopLabel: '返回顶部',
    skipToContentLabel: '跳到正文',
    externalLinkIcon: true
  }
});
