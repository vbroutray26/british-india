import type { Meta, StoryObj } from '@storybook/svelte-vite';
import PlaceSummary from './PlaceSummary.svelte';
import { L, SAMPLE_SUMMARY } from '../stories/fixtures';

const meta = {
  title: 'Content/PlaceSummary',
  component: PlaceSummary,
  tags: ['autodocs'],
  args: { ...SAMPLE_SUMMARY, method: 'llm', review: 'unreviewed', labels: L.summary },
} satisfies Meta<typeof PlaceSummary>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Reviewed: Story = { args: { method: 'manual', review: 'accepted' } };
export const EnglishOnOdiaPage: Story = {
  args: {
    lang: 'en',
    labels: { heading: 'ସାରାଂଶ', ai: 'ତଳ ଅଂଶରୁ AI ଦ୍ୱାରା ଲିଖିତ', longer: 'ଦୀର୍ଘ ସାରାଂଶ ପଢ଼ନ୍ତୁ', reviewed: 'ସମୀକ୍ଷିତ', unreviewed: 'ସମୀକ୍ଷା ହୋଇନାହିଁ', note: 'ଏହି ସାରାଂଶ ଇଂରାଜୀରେ ଅଛି; ସମୀକ୍ଷା ପରେ ଅନୁବାଦ ହେବ।' },
  },
};
