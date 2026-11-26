import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Demo from '../stories/demos/HeaderDemo.svelte';

const meta = { title: 'Shell/Header', component: Demo, tags: ['autodocs'] } satisfies Meta<typeof Demo>;
export default meta;
type Story = StoryObj<typeof meta>;

export const English: Story = { args: { lang: 'en' } };
export const Odia: Story = { args: { lang: 'or' } };
export const Hindi: Story = { args: { lang: 'hi' } };
