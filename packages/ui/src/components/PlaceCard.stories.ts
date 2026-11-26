import type { Meta, StoryObj } from '@storybook/svelte-vite';
import PlaceCard from './PlaceCard.svelte';
import { L, SAMPLE_PASSAGE, SAMPLE_CENSUS, SAMPLE_IMAGES, searchSample, placeholderImage } from '../stories/fixtures';

const meta = {
  title: 'Content/PlaceCard',
  component: PlaceCard,
  tags: ['autodocs'],
  args: { name: 'Puri', otherNames: 'ପୁରୀ · पुरी', type: 'Town', districtThen: 'Puri (1908)', districtNow: 'Puri', href: '#', labels: { then: 'Then', now: 'Now' } },
} satisfies Meta<typeof PlaceCard>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const WithThumb: Story = { args: { thumb: { src: placeholderImage(96, 96, 'img'), alt: '' } } };
export const Ghost: Story = { args: { name: 'Sample lost village', type: 'Village', ghost: 'No longer exists', districtNow: undefined } };
