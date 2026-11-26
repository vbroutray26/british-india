import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Gallery from './Gallery.svelte';
import { L, SAMPLE_PASSAGE, SAMPLE_CENSUS, SAMPLE_IMAGES, searchSample, placeholderImage } from '../stories/fixtures';

const meta = {
  title: 'Media/Gallery',
  component: Gallery,
  tags: ['autodocs'],
  args: { label: 'Images', items: SAMPLE_IMAGES, labels: L.gallery },
} satisfies Meta<typeof Gallery>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
