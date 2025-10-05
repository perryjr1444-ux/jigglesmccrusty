import type { LucideIcon } from 'lucide-react';
import { BarChart3, Leaf, Radar } from 'lucide-react';

export interface InsightDefinition {
  title: string;
  description: string;
  icon: LucideIcon;
  hue: string;
}

export const insights: InsightDefinition[] = [
  {
    title: 'Momentum pulse',
    description: 'Engagement surged 24% after the async rituals were introduced.',
    icon: Radar,
    hue: 'from-cyan-500/40 to-blue-500/10'
  },
  {
    title: 'Adoption lift',
    description: 'Teams following the guided missions ship outcomes 32% faster.',
    icon: BarChart3,
    hue: 'from-emerald-500/40 to-emerald-500/10'
  },
  {
    title: 'Sustainability nudge',
    description: 'Your playbooks reuse 68% of assets across cohorts, reducing ramp-up fatigue.',
    icon: Leaf,
    hue: 'from-amber-500/40 to-amber-500/10'
  }
];
