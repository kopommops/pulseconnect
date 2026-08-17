import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Select from '../components/Select';
import { useFilters } from '../lib/FiltersContext';

export default function DashboardLayout() {
  const f = useFilters();

  if (f.loading) {
    return (
      <div className="max-w-6xl mx-auto px-5 pt-24 text-center font-mono text-sm" style={{ color: 'var(--ink-muted)' }}>
        Loading grid data...
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-5 pb-24">
      <div className="glass rounded-2xl p-4 mt-8 mb-6 flex flex-wrap gap-4">
        <Select label="Season" value={f.season} onChange={f.setSeason} options={f.SEASONS} getLabel={s => String(s)} getValue={s => String(s)} />
        <Select label="Team" value={f.teamId} onChange={id => { f.setTeamId(id); const t = f.teams.find(x => x.id === id); if (t) f.setDriverId(t.drivers[0]); }} options={f.teams} getLabel={t => t.name} getValue={t => t.id} />
        <Select label="Driver" value={f.driverId} onChange={f.setDriverId} options={f.drivers.filter(d => f.team?.drivers.includes(d.id))} getLabel={d => `${d.name} #${d.num}`} getValue={d => d.id} />
        <Select label="Track Type" value={f.trackType} onChange={f.setTrackType} options={f.trackTypes} />
        <Select label="Circuit" value={f.circuitId} onChange={f.setCircuitId} options={f.filteredCircuits} getLabel={c => c.name} getValue={c => c.id} />
        <Select label="Metric Focus" value={f.metricFocus} onChange={f.setMetricFocus} options={f.METRIC_FOCUS} />
        <Select label="Session" value={f.session} onChange={f.setSession} options={f.SESSIONS} />
      </div>

      <div className="flex gap-4">
        <Sidebar />
        <div className="flex-1 min-w-0">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
