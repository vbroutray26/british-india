import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Demo from '../stories/demos/AppShellDemo.svelte';

const meta = { title: 'Shell/AppShell', component: Demo, tags: ['autodocs'] } satisfies Meta<typeof Demo>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Then: Story = { args: { mode: 'then' } };
export const Now: Story = { args: { mode: 'now' } };
