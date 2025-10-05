import { FC } from 'react';
import { Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader } from './ui/card';
import { InsightDefinition } from '../data/insights';

interface InsightStackProps {
  insights: InsightDefinition[];
}

const InsightStack: FC<InsightStackProps> = ({ insights }) => {
  if (!insights.length) {
    return (
      <Card className="flex h-full flex-col gap-4">
        <CardHeader>
          <div>
            <h2 className="text-lg font-semibold text-white">Signals decoded</h2>
            <p className="mt-1 text-sm text-gray-400">Connect telemetry to activate automated insight generation.</p>
          </div>
        </CardHeader>
        <CardContent className="flex flex-1 items-center justify-center text-sm text-gray-500">
          Once data sources sync, we will surface live insights here.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex h-full flex-col gap-4">
      <CardHeader className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Signals decoded</h2>
          <p className="mt-1 text-sm text-gray-400">Automated insights derived from your telemetry feeds.</p>
        </div>
        <Button variant="outline" className="gap-2">
          <Sparkles className="h-4 w-4 text-accent-soft" />
          Refresh
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {insights.map((insight, index) => (
          <article
            key={insight.title}
            className={`group relative overflow-hidden rounded-3xl border border-white/5 bg-gradient-to-br ${insight.hue} p-5 transition duration-500 hover:-translate-y-1 hover:shadow-glow`}
          >
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10 text-accent-soft">
                <insight.icon className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">{insight.title}</h3>
                <p className="mt-2 text-sm text-gray-200">{insight.description}</p>
              </div>
            </div>
            <div className="pointer-events-none absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-white/5 to-transparent opacity-0 transition group-hover:opacity-100" />
            <p className="mt-4 text-xs uppercase tracking-[0.3em] text-white/40">Insight {index + 1}</p>
          </article>
        ))}
      </CardContent>
    </Card>
  );
};

export default InsightStack;
