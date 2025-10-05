import { FC } from 'react';
import { Bell, Flame, Search, Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

const TopBar: FC = () => {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <p className="text-xs uppercase tracking-[0.5em] text-accent-soft">Mission control</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Shape your framework into a living product</h1>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative hidden overflow-hidden rounded-2xl border border-white/5 bg-white/5 px-4 py-2 text-sm text-gray-300 shadow-inner md:flex md:min-w-[220px]">
          <Search className="mr-2 h-4 w-4 text-gray-500" />
          <input
            className="w-full bg-transparent placeholder:text-gray-500 focus:outline-none"
            placeholder="Search modules, rituals, assets"
          />
        </div>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <Badge variant="danger" className="absolute -right-1 -top-1 border-none px-2 py-0 text-[10px] tracking-[0.2em]">
            3
          </Badge>
        </Button>
        <Button>
          <Sparkles className="mr-2 h-4 w-4" />
          Auto-tune
        </Button>
        <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm">
          <Flame className="h-4 w-4 text-amber-400" />
          <span className="text-xs uppercase tracking-[0.3em] text-gray-300">Momentum</span>
          <span className="text-sm font-semibold text-white">82%</span>
        </div>
      </div>
    </header>
  );
};

export default TopBar;
