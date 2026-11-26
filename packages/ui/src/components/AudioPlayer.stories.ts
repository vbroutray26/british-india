import type { Meta, StoryObj } from '@storybook/svelte-vite';
import AudioPlayer from './AudioPlayer.svelte';

const meta = {
  title: 'Media/AudioPlayer',
  component: AudioPlayer,
  tags: ['autodocs'],
  args: { src: '', title: 'Listen: Puri in one minute', lang: 'en', transcript: 'Sample transcript of the short narration.', duration: '1:04', labels: { transcript: 'Transcript', aiVoice: 'Narrated with a synthetic voice' } },
} satisfies Meta<typeof AudioPlayer>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
