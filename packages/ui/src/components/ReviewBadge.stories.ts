import type { Meta, StoryObj } from '@storybook/svelte-vite';
import ReviewBadge from './ReviewBadge.svelte';
import { L, SAMPLE_PASSAGE, SAMPLE_CENSUS, SAMPLE_IMAGES, searchSample, placeholderImage } from '../stories/fixtures';

const meta = {
  title: 'Content/ReviewBadge',
  component: ReviewBadge,
  tags: ['autodocs'],
  args: { status: 'accepted', labels: L.review, reviewer: 'owner', date: '2026-12-20' },
} satisfies Meta<typeof ReviewBadge>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Reviewed: Story = {};
export const Edited: Story = { args: { status: 'edited' } };
export const Unreviewed: Story = { args: { status: 'unreviewed', reviewer: undefined, date: undefined } };
