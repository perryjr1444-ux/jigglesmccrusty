import { FC, useEffect, useState } from 'react';
import { cn } from '../lib/utils';
import { Badge } from './ui/badge';
import { MetricDefinition } from '../data/metrics';

type MetricCardProps = Omit<MetricDefinition, 'id'>;

const MetricCard: FC<MetricCardProps> = ({ label, value, delta, trend, accent = 'from-accent to-purple-500' }) => {
  const [pulse, setPulse] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => setPulse((prev) => prev + 1), 6000);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <div className="relative overflow-hidden rounded-3xl p-[1px] transition-[box-shadow] duration-700 hover:shadow-glow">
      <div className={cn('card-sheen relative h-full rounded-[calc(1.5rem-1px)] bg-gradient-to-br p-0.5', accent)}>
        <div className="glass-panel h-full rounded-[calc(1.5rem-1px)] p-6">
          <p className="text-xs uppercase tracking-[0.4em] text-accent-soft/70">{label}</p>
          <div className="mt-6 flex items-end gap-3">
            <p key={pulse} className="metric-pulse text-4xl font-semibold text-white">
              {value}
            </p>
            <Badge variant={trend === 'up' ? 'success' : 'danger'} className="tracking-[0.2em]">
              {trend === 'up' ? '+' : '-'}{delta}%
            </Badge>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricCard;
