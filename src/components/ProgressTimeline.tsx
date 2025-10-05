import { FC } from 'react';
import { CheckCircle2, Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader } from './ui/card';
import { TimelineStep } from '../data/timeline';

interface ProgressTimelineProps {
  steps: TimelineStep[];
}

const ProgressTimeline: FC<ProgressTimelineProps> = ({ steps }) => {
  if (!steps.length) {
    return (
      <Card>
        <CardHeader>
          <div>
            <h2 className="text-lg font-semibold text-white">Framework runway</h2>
            <p className="mt-1 text-sm text-gray-400">As soon as you set milestones, we will visualize momentum here.</p>
          </div>
        </CardHeader>
        <CardContent className="text-sm text-gray-500">
          No timeline data available. Add a first milestone to unlock predictive guidance.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Framework runway</h2>
          <p className="mt-1 text-sm text-gray-400">Track where you are in the lifecycle and unlock the next module.</p>
        </div>
        <Button variant="outline" className="gap-2">
          <Sparkles className="h-4 w-4 text-accent-soft" />
          Predict next
        </Button>
      </CardHeader>
      <CardContent className="space-y-6">
        {steps.map((step) => (
          <div key={step.stage} className="flex items-start gap-4 rounded-3xl border border-white/5 p-4 transition hover:border-white/15">
            <div
              className={`relative flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-surface ${
                step.status === 'active' ? 'shadow-glow border-accent/60' : ''
              }`}
            >
              <step.icon className="h-6 w-6 text-accent-soft" />
              {step.status === 'complete' && <CheckCircle2 className="absolute -right-1 -top-1 h-5 w-5 text-emerald-400" />}
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <h3 className="text-base font-semibold text-white">{step.stage}</h3>
                <Badge
                  variant={
                    step.status === 'complete'
                      ? 'success'
                      : step.status === 'active'
                      ? 'glow'
                      : 'default'
                  }
                >
                  {step.status === 'complete' ? 'Complete' : step.status === 'active' ? 'In flight' : 'Queued'}
                </Badge>
              </div>
              <p className="max-w-xl text-sm text-gray-400">{step.description}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default ProgressTimeline;
