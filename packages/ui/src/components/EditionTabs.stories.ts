import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Demo from '../stories/demos/EditionTabsDemo.svelte';

const meta = { title: 'Content/EditionTabs', component: Demo, tags: ['autodocs'] } satisfies Meta<typeof Demo>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: {} };
