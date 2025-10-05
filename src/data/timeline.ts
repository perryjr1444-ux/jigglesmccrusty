import type { LucideIcon } from 'lucide-react';
import { Compass, FlaskConical, Rocket } from 'lucide-react';

export type TimelineStatus = 'complete' | 'active' | 'pending';

export interface TimelineStep {
  stage: string;
  icon: LucideIcon;
  description: string;
  status: TimelineStatus;
}

export const timelineSteps: TimelineStep[] = [
  {
    stage: 'Sense',
    icon: Compass,
    description: 'Clarify the outcome, audit signals, and surface opportunity areas.',
    status: 'complete'
  },
  {
    stage: 'Shape',
    icon: FlaskConical,
    description: 'Prototype pathways that translate your framework into guided experiments.',
    status: 'active'
  },
  {
    stage: 'Scale',
    icon: Rocket,
    description: 'Operationalize rituals, governance, and telemetry for ongoing delivery.',
    status: 'pending'
  }
];
