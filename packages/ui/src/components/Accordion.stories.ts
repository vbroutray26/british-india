import type { Meta, StoryObj } from '@storybook/svelte-vite';
import Accordion from './Accordion.svelte';

const meta = {
  title: 'Primitives/Accordion',
  component: Accordion,
  tags: ['autodocs'],
  args: { items: [{ id: 'a', title: 'How were these facts extracted?', content: 'Rules first, then AI with exact quotes, then a verifier.' }, { id: 'b', title: 'Who reviewed them?', content: 'Reviewed items carry a badge with reviewer and date.' }], open: ['a'] },
} satisfies Meta<typeof Accordion>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
