import type { Preview } from '@storybook/svelte-vite';
import '../src/fonts.css';
import '../dist/tokens.css';
import '../src/base.css';

// Toolbar switches mirror the site: language (FR-LANG), Then/Now (spec §11.1), light/dark.
const preview: Preview = {
  globalTypes: {
    lang: {
      description: 'Language', defaultValue: 'en',
      toolbar: { title: 'Language', icon: 'globe', items: [{ value: 'en', title: 'English' }, { value: 'or', title: 'ଓଡ଼ିଆ' }, { value: 'hi', title: 'हिन्दी' }], dynamicTitle: true },
    },
    mode: {
      description: 'Then / Now', defaultValue: 'then',
      toolbar: { title: 'Mode', icon: 'contrast', items: [{ value: 'then', title: 'Then' }, { value: 'now', title: 'Now' }], dynamicTitle: true },
    },
    theme: {
      description: 'Colour scheme', defaultValue: 'light',
      toolbar: { title: 'Theme', icon: 'mirror', items: [{ value: 'light', title: 'Light' }, { value: 'dark', title: 'Dark' }], dynamicTitle: true },
    },
  },
  decorators: [
    (story, ctx) => {
      const html = document.documentElement;
      html.lang = ctx.globals.lang ?? 'en';
      html.dataset.mode = ctx.globals.mode ?? 'then';
      html.dataset.theme = ctx.globals.theme ?? 'light';
      return story();
    },
  ],
  parameters: {
    layout: 'padded',
    a11y: { test: 'error' },
    controls: { expanded: true },
    options: { storySort: { order: ['Introduction', 'Foundations', 'Primitives', 'Shell', 'Content', 'Interactive', 'Data', 'Media'] } },
    backgrounds: { disable: true },
  },
};
export default preview;
