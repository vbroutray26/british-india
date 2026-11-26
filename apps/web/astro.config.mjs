// @ts-check
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';

// Static output only (spec §7.1). Language lives in the URL (FR-LANG-02).
export default defineConfig({
  site: 'https://british-india.british-india-towns.workers.dev',
  output: 'static',
  trailingSlash: 'always',
  integrations: [svelte()],
  i18n: {
    locales: ['en', 'or', 'hi'],
    defaultLocale: 'en',
    routing: { prefixDefaultLocale: true, redirectToDefaultLocale: false },
  },
  build: { inlineStylesheets: 'never' }, // NFR-SEC-01: strict CSP, no inline
  vite: { build: { assetsInlineLimit: 0 } }, // keep scripts out of HTML
});
