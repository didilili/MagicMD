import type { Theme } from 'vitepress';
import DefaultTheme from 'vitepress/theme';
import ConfigBuilder from '../components/ConfigBuilder.vue';
import HomeShowcase from '../components/HomeShowcase.vue';
import './style.css';

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('ConfigBuilder', ConfigBuilder);
    app.component('HomeShowcase', HomeShowcase);
  }
} satisfies Theme;
