export interface PersonaDefinition {
  name: string;
  focus: string;
  tone: string;
  color: string;
  templates?: number;
  aiReady?: boolean;
}

export const personas: PersonaDefinition[] = [
  {
    name: 'Strategist',
    focus: 'Vision & orchestration',
    tone: 'Executive clarity',
    color: 'from-purple-500/90 via-accent to-blue-500/80',
    templates: 42,
    aiReady: true
  },
  {
    name: 'Builder',
    focus: 'Feature acceleration',
    tone: 'Action oriented',
    color: 'from-emerald-500/80 via-teal-500/60 to-cyan-500/60',
    templates: 36,
    aiReady: true
  },
  {
    name: 'Guardian',
    focus: 'Governance & trust',
    tone: 'Compliance ready',
    color: 'from-rose-500/80 via-orange-500/60 to-yellow-500/60',
    templates: 28,
    aiReady: false
  }
];
