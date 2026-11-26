import type { Meta, StoryObj } from '@storybook/svelte-vite';
import DataTable from './DataTable.svelte';
import type { Column } from './types';
import { L, SAMPLE_PASSAGE, SAMPLE_CENSUS, SAMPLE_IMAGES, searchSample, placeholderImage } from '../stories/fixtures';

const meta = {
  title: 'Data/DataTable',
  component: DataTable,
  tags: ['autodocs'],
  args: { caption: 'Sample table', emptyText: 'Not recorded', sortable: true, columns: [{ key: 'year', label: 'Year' }, { key: 'value', label: 'Population', numeric: true }, { key: 'unit', label: 'Unit' }] as Column<any>[], rows: SAMPLE_CENSUS },
} satisfies Meta<typeof DataTable>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const NotSortable: Story = { args: { sortable: false } };
