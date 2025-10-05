import { FC } from 'react';
import { navigation } from '../data/navigation';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

const Sidebar: FC = () => {
  return (
    <aside className="glass-panel h-full w-72 shrink-0 rounded-3xl p-6 text-sm shadow-card">
      <div className="flex items-center gap-3 pb-10">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-accent via-purple-500 to-blue-500 shadow-glow">
          <span className="text-xl font-semibold">FX</span>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-accent-soft">Framework</p>
          <h1 className="text-lg font-semibold text-white">Control Studio</h1>
        </div>
      </div>
      <nav className="flex flex-col gap-2">
        {navigation.map((item) => (
          <button
            key={item.label}
            className={`group flex items-center gap-3 rounded-2xl px-4 py-3 transition-colors duration-300 ${
              item.active
                ? 'bg-gradient-to-r from-accent/80 to-accent-soft text-white shadow-glow'
                : 'text-gray-400 hover:bg-surfaceMuted/40 hover:text-white'
            }`}
          >
            <item.icon className="h-5 w-5" />
            <span className="font-medium tracking-wide">{item.label}</span>
            {!item.active && (
              <Badge className="ml-auto" variant="default">
                soon
              </Badge>
            )}
          </button>
        ))}
      </nav>
      <div className="mt-12 rounded-3xl bg-surfaceMuted/70 p-5">
        <p className="text-xs uppercase tracking-[0.4em] text-accent-soft">Live Guide</p>
        <h2 className="mt-2 text-lg font-semibold text-white">Adaptive assistant</h2>
        <p className="mt-3 text-sm text-gray-400">
          Drop in your objective and our orchestrator will tailor the framework into bite-sized missions.
        </p>
        <Button className="mt-6 w-full" variant="ghost">
          Summon co-pilot
        </Button>
      </div>
    </aside>
  );
};

export default Sidebar;
