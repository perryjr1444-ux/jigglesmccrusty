export type MetricTrend = 'up' | 'down';

export interface MetricDefinition {
  id: string;
  label: string;
  value: string;
  delta: number;
  trend: MetricTrend;
  accent?: string;
}

export const metrics: MetricDefinition[] = [
  {
    id: 'fit',
    label: 'Framework Fit',
    value: '92%',
    delta: 14,
    trend: 'up'
  },
  {
    id: 'velocity',
    label: 'Adoption velocity',
    value: '38 teams',
    delta: 8,
    trend: 'up',
    accent: 'from-emerald-400 to-teal-500'
  },
  {
    id: 'impact',
    label: 'Time to impact',
    value: '5.5 wks',
    delta: 11,
    trend: 'down',
    accent: 'from-rose-500 to-orange-500'
  }
];
