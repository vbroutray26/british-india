import type { Meta, StoryObj } from '@storybook/svelte-vite';
import ImageFigure from './ImageFigure.svelte';
import { L, SAMPLE_PASSAGE, SAMPLE_CENSUS, SAMPLE_IMAGES, searchSample, placeholderImage } from '../stories/fixtures';

const meta = {
  title: 'Media/ImageFigure',
  component: ImageFigure,
  tags: ['autodocs'],
  args: { src: placeholderImage(1200, 800, 'Sample image'), width: 1200, height: 800, alt: 'Sample placeholder', caption: 'Sample caption', date: 'c. 1900', credit: 'Sample credit line', sourceHref: '#', sourceLabel: 'Source' },
} satisfies Meta<typeof ImageFigure>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Evidence: Story = {};
export const Decorative: Story = { args: { use: 'decorative' } };
