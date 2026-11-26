import type { StorybookConfig } from '@storybook/svelte-vite';

const config: StorybookConfig = {
  stories: ['../src/**/*.mdx', '../src/**/*.stories.@(ts|js)'],
  addons: ['@storybook/addon-docs', '@storybook/addon-a11y'],
  // Serve only the brand folder (not the site's _headers/CSP) so logo masks resolve in stories.
  staticDirs: [{ from: '../../../apps/web/public/brand', to: '/brand' }],
  framework: { name: '@storybook/svelte-vite', options: {} },
  core: { disableTelemetry: true },
};
export default config;
