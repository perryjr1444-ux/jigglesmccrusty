import { FC, useEffect, useMemo, useState } from 'react';
import { BrainCircuit, Sparkles, Wand2 } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader } from './ui/card';
import { QuickAction } from '../data/actions';

interface ActionBoardProps {
  items: QuickAction[];
}

const ActionBoard: FC<ActionBoardProps> = ({ items }) => {
  const [selected, setSelected] = useState<QuickAction | null>(() => items[0] ?? null);

  useEffect(() => {
    setSelected((current) => {
      if (!items.length) {
        return null;
      }
      if (!current) {
        return items[0];
      }
      const stillExists = items.find((item) => item.title === current.title);
      return stillExists ?? items[0];
    });
  }, [items]);

  const decoratedItems = useMemo(
    () =>
      items.map((item) => ({
        ...item,
        active: selected ? item.title === selected.title : false
      })),
    [items, selected]
  );

  if (!items.length) {
    return (
      <Card className="relative overflow-hidden">
        <CardHeader>
          <div>
            <h2 className="text-lg font-semibold text-white">Use case accelerator</h2>
            <p className="mt-1 text-sm text-gray-400">We will surface quick-start plays once you add your first module.</p>
          </div>
          <Button variant="outline" disabled>
            <Sparkles className="mr-2 h-4 w-4 text-accent-soft" />
            Generate
          </Button>
        </CardHeader>
        <CardContent className="flex min-h-[220px] items-center justify-center text-sm text-gray-500">
          Upload framework context to unlock guided accelerators.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="relative overflow-hidden">
      <div className="pointer-events-none absolute -left-24 top-1/3 h-56 w-56 rounded-full bg-accent/10 blur-3xl" />
      <CardHeader className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Use case accelerator</h2>
          <p className="mt-1 text-sm text-gray-400">Pick a starting workflow and we will scaffold the framework around it.</p>
        </div>
        <Button variant="outline" className="gap-2">
          <Sparkles className="h-4 w-4 text-accent-soft" />
          Generate
        </Button>
      </CardHeader>
      <CardContent className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <div className="space-y-3">
          {decoratedItems.map((item) => (
            <button
              key={item.title}
              onClick={() => setSelected(item)}
              className={`group relative flex w-full items-start gap-4 overflow-hidden rounded-3xl border border-white/5 px-4 py-4 text-left transition duration-500 ${
                item.active ? 'bg-white/5 shadow-glow' : 'bg-white/10 hover:bg-white/20 hover:border-white/20'
              }`}
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-accent/20 text-accent-soft">
                <item.icon className="h-5 w-5" />
              </div>
              <div className="space-y-2">
                <h3 className="text-base font-semibold text-white">{item.title}</h3>
                <p className="text-sm text-gray-400">{item.description}</p>
                <div className="flex flex-wrap gap-2 text-xs text-gray-300">
                  {item.tags.map((tag) => (
                    <Badge key={tag} className="border-white/10 bg-white/5">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </button>
          ))}
        </div>
        <div className="glass-panel relative flex h-full min-h-[280px] flex-col justify-between overflow-hidden rounded-3xl p-6">
          <div className="fade-slide-up space-y-4" key={selected?.title ?? 'empty-preview'}>
            <p className="text-xs uppercase tracking-[0.4em] text-accent-soft/70">Outcome preview</p>
            <h3 className="text-2xl font-semibold text-white">{selected?.title}</h3>
            <p className="text-sm text-gray-300">{selected?.description}</p>
          </div>
          <div className="space-y-3 text-sm text-gray-200">
            <div className="fade-slide-up flex items-center gap-3 rounded-2xl bg-white/5 px-4 py-3">
              <Wand2 className="h-4 w-4 text-accent-soft" />
              We will auto-generate facilitation scripts tailored to your persona mix.
            </div>
            <div className="fade-slide-up flex items-center gap-3 rounded-2xl bg-white/5 px-4 py-3">
              <BrainCircuit className="h-4 w-4 text-accent-soft" />
              Connect framework heuristics with telemetry feeds to watch adoption in real-time.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ActionBoard;
