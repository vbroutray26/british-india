import type { Meta, StoryObj } from '@storybook/svelte-vite';
import FactCard from './FactCard.svelte';
import { L, SAMPLE_PASSAGE, SAMPLE_CENSUS, SAMPLE_IMAGES, searchSample, placeholderImage } from '../stories/fixtures';

const meta = {
  title: 'Content/FactCard',
  component: FactCard,
  tags: ['autodocs'],
  args: { icon: 'population', label: 'Population', value: '00,000', unit: 'sample', year: '1908', source: 'Sample source', passageHref: '#', review: 'accepted', method: 'rule', correctHref: '#', labels: L.fact },
} satisfies Meta<typeof FactCard>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Reviewed: Story = {};
export const MachineExtracted: Story = { args: { icon: 'crop', label: 'Crops', value: 'Sample crop list', unit: undefined, review: 'unreviewed', method: 'llm' } };
export const Approximate: Story = { args: { approximate: true, review: 'edited' } };
export const NotRecorded: Story = { args: { icon: 'school', label: 'Schools', value: undefined, review: 'unreviewed' } };
export const LongOdia: Story = { args: { label: 'ଜନସଂଖ୍ୟା', value: 'ନମୁନା ମୂଲ୍ୟ ଯାହା ବହୁତ ଲମ୍ବା ହୋଇପାରେ', source: 'ନମୁନା ସୂତ୍ର' } };

export const TextValues: Story = { args: { icon: 'temple', label: 'Temples', value: 'Lingarāj; Rājarānī; Mukteswar and 12 more', valueKind: 'text', method: 'llm', year: undefined } };
