import type { Meta, StoryObj } from '@storybook/svelte-vite';
import ActionBar from './ActionBar.svelte';
import { L, SAMPLE_PASSAGE, SAMPLE_CENSUS, SAMPLE_IMAGES, searchSample, placeholderImage } from '../stories/fixtures';

const meta = {
  title: 'Content/ActionBar',
  component: ActionBar,
  tags: ['autodocs'],
  args: { label: 'Page actions', labels: L.actions, onshare: () => {}, oncite: () => {}, oncorrect: () => {}, onlisten: () => {} },
} satisfies Meta<typeof ActionBar>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Compact: Story = { args: { compact: true } };
