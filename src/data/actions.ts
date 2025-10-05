import type { LucideIcon } from 'lucide-react';
import { BrainCircuit, FileSpreadsheet, LineChart } from 'lucide-react';

export interface QuickAction {
  title: string;
  icon: LucideIcon;
  description: string;
  tags: string[];
}

export const quickActions: QuickAction[] = [
  {
    title: 'Import your framework assets',
    icon: FileSpreadsheet,
    description: 'Connect Notion, Confluence, or CSV and let us weave them into structured rituals.',
    tags: ['5 min', 'automated parsing']
  },
  {
    title: 'Activate success metrics',
    icon: LineChart,
    description: 'Map KPIs to each module and blend them with qualitative signals in one view.',
    tags: ['telemetry', 'insights']
  },
  {
    title: 'Design onboarding narrative',
    icon: BrainCircuit,
    description: 'Co-create an interactive story that trains teams on why the framework matters.',
    tags: ['story mode', 'AI assisted']
  }
];
