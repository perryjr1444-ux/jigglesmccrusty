import { FC } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader } from './ui/card';
import { PersonaDefinition } from '../data/personas';

interface PersonaConfiguratorProps {
  personas: PersonaDefinition[];
}

const PersonaConfigurator: FC<PersonaConfiguratorProps> = ({ personas }) => {
  if (!personas.length) {
    return (
      <Card>
        <CardHeader>
          <div>
            <h2 className="text-lg font-semibold text-white">Persona orbit</h2>
            <p className="mt-1 text-sm text-gray-400">Create audience personas to unlock tailored playbook drafts.</p>
          </div>
        </CardHeader>
        <CardContent className="text-sm text-gray-500">
          No personas configured yet. Add personas to shape tone, rituals, and success criteria automatically.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="relative overflow-hidden">
      <div className="pointer-events-none absolute -top-40 right-0 h-80 w-80 rounded-full bg-accent/10 blur-3xl" />
      <CardHeader className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Persona orbit</h2>
          <p className="mt-1 text-sm text-gray-400">Blend stakeholders to co-create your perfect delivery crew.</p>
        </div>
        <Button variant="outline" className="uppercase tracking-[0.3em]">
          Auto-match
        </Button>
      </CardHeader>
      <CardContent className="grid gap-5 md:grid-cols-3">
        {personas.map((persona, index) => (
          <article
            key={persona.name}
            className={`group relative overflow-hidden rounded-3xl bg-gradient-to-br ${persona.color} p-[1px] shadow-lg transition-transform duration-700 hover:-translate-y-1`}
          >
            <div className="glass-panel h-full rounded-[calc(1.5rem-1px)] p-5">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">{persona.name}</h3>
                <Badge variant="glow">#{index + 1}</Badge>
              </div>
              <p className="mt-4 text-sm text-gray-200">{persona.focus}</p>
              <div className="mt-4 space-y-1">
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">Preferred tone</p>
                <p className="text-sm font-medium text-white">{persona.tone}</p>
              </div>
              <div className="mt-6 flex items-center justify-between text-xs text-gray-300">
                <Badge className="border-white/10 bg-white/5">{persona.templates ?? 0} templates</Badge>
                <Badge className="border-white/10 bg-white/5">{persona.aiReady ? 'AI pair ready' : 'Manual setup'}</Badge>
              </div>
            </div>
          </article>
        ))}
      </CardContent>
    </Card>
  );
};

export default PersonaConfigurator;
