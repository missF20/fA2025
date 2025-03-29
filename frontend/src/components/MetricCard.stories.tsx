import type { Meta, StoryObj } from '@storybook/react';
import { MetricCard } from './MetricCard';
import { MessageSquare } from 'lucide-react';

const meta = {
  title: 'Components/MetricCard',
  component: MetricCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof MetricCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: 'Total Responses',
    value: 1234,
    icon: <MessageSquare size={24} />,
    description: 'AI responses across all platforms',
    trend: {
      value: 12,
      isPositive: true,
    },
  },
};

export const WithBreakdown: Story = {
  args: {
    ...Default.args,
    breakdown: {
      facebook: 500,
      instagram: 400,
      whatsapp: 334,
    },
  },
};