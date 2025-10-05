import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import MetricCard from './components/MetricCard';
import ActionBoard from './components/ActionBoard';
import PersonaConfigurator from './components/PersonaConfigurator';
import ProgressTimeline from './components/ProgressTimeline';
import InsightStack from './components/InsightStack';
import { metrics } from './data/metrics';
import { quickActions } from './data/actions';
import { insights } from './data/insights';
import { personas } from './data/personas';
import { timelineSteps } from './data/timeline';

const App = () => {
  return (
    <div className="flex min-h-screen gap-6 bg-transparent p-6">
      <Sidebar />
      <main className="flex-1 space-y-6 overflow-hidden rounded-[2.5rem] border border-white/5 bg-surface/60 p-8 shadow-card">
        <TopBar />
        <section className="grid gap-4 md:grid-cols-3">
          {metrics.map(({ id, ...metric }) => (
            <MetricCard key={id} {...metric} />
          ))}
        </section>
        <section className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
          <ActionBoard items={quickActions} />
          <InsightStack insights={insights} />
        </section>
        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <PersonaConfigurator personas={personas} />
          <ProgressTimeline steps={timelineSteps} />
        </section>
      </main>
    </div>
  );
};

export default App;
