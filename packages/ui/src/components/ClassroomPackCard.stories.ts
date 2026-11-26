import type { Meta, StoryObj } from '@storybook/svelte-vite';
import ClassroomPackCard from './ClassroomPackCard.svelte';

const meta = {
  title: 'Content/ClassroomPackCard',
  component: ClassroomPackCard,
  tags: ['autodocs'],
  args: { title: 'Sample classroom pack', summary: 'Teacher note, source passages with questions, a map, printable PDF.', href: '#', contents: ['1-page teacher note', '6 source passages with questions', 'Map'], downloads: [{ text: 'English PDF', href: '#en.pdf', lang: 'en' }, { text: 'ଓଡ଼ିଆ PDF', href: '#or.pdf', lang: 'or' }, { text: 'हिन्दी PDF', href: '#hi.pdf', lang: 'hi' }], labels: { includes: 'Includes', download: 'Download' } },
} satisfies Meta<typeof ClassroomPackCard>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
