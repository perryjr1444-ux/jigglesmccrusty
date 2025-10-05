import { CalendarIcon, Gauge, Layers, Lightbulb, Rocket, Settings, Users } from 'lucide-react';

export const navigation = [
  { label: 'Control Center', icon: Gauge, active: true },
  { label: 'Use Case Builder', icon: Layers },
  { label: 'Personas', icon: Users },
  { label: 'Playbooks', icon: Lightbulb },
  { label: 'Launchpad', icon: Rocket },
  { label: 'Governance', icon: Settings },
  { label: 'Roadmap', icon: CalendarIcon }
];
