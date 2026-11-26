import type { Meta, StoryObj } from '@storybook/svelte-vite';
import GlossaryTerm from './GlossaryTerm.svelte';

const meta = {
  title: 'Content/GlossaryTerm',
  component: GlossaryTerm,
  tags: ['autodocs'],
  args: { term: 'pargana', definition: 'A revenue sub-division grouping several villages.', moreHref: '#', moreLabel: 'Glossary' },
} satisfies Meta<typeof GlossaryTerm>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
