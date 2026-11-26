import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Callout from './Callout.svelte';

const meta = {
  title: 'Content/Callout',
  component: Callout,
  tags: ['autodocs'],
  args: { kind: 'critical', title: 'Critical note', body: 'This passage reflects how revenue officials classified land; it says little about who worked it.', meta: 'Sample note · project team · 2026' },
} satisfies Meta<typeof Callout>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Critical: Story = {};
export const ContentNote: Story = { args: { kind: 'content-note', title: 'Content note', body: 'The table below uses caste and tribe categories created by the colonial census. They may be inaccurate or offensive.', meta: undefined, link: { href: '#', text: 'How to read this record' } } };
export const Silence: Story = { args: { kind: 'silence', title: 'What the record leaves out', body: 'Women, labourers and tribal communities are barely mentioned in this entry.', meta: undefined } };
export const Info: Story = { args: { kind: 'info', title: undefined, body: 'Not yet translated — showing English.', meta: undefined } };
export const Warning: Story = { args: { kind: 'warning', title: 'No longer exists', body: 'This village was lost to the sea; best-known location shown.', meta: undefined } };
