import { useEffect, useState } from 'react';
import { useFilters } from '../lib/FiltersContext';
import { api } from '../lib/api';
import { BoxPlot } from '../components/Viz';

export default function Consistency() {
  const f = useFilters();
  const [data, setData] = useState(null);

  useEffect(() => { api.consistency(f.season).then(setData).catch(() => {}); }, [f.season]);

  const accentFor = (driverId) => {
    const team = f.teams.find(t => t.drivers.includes(driverId));
    return team?.accent || 'var(--red)';
  };

  if (!data) return null;
  const isSeed = data.source === 'seed';

  return (
    <div className="space-y-4">
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between mb-1">
          <h2 className="font-display font-bold text-xl">Race Finish Consistency — {f.season}</h2>
          {isSeed && <span className="font-mono text-[10px] px-2.5 py-1 rounded-full" style={{ background: 'var(--glass-strong)', color: 'var(--ink-faint)' }}>sample data</span>}
        </div>
        <p className="text-sm mb-6" style={{ color: 'var(--ink-muted)' }}>
          Box = interquartile range of finishing position across the season. Whiskers = min/max. Sorted by median.
        </p>
        <BoxPlot data={data.consistency} accentFor={accentFor} />
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="glass rounded-2xl p-6">
          <h3 className="font-display font-semibold text-lg mb-4">Race Pace Delta (vs. field median)</h3>
          <div className="space-y-2">
            {Object.entries(data.race_pace)
              .filter(([, v]) => v !== 'unknown')
              .sort((a, b) => a[1] - b[1])
              .map(([driverId, val]) => (
                <div key={driverId} className="flex items-center justify-between font-mono text-xs">
                  <span style={{ color: 'var(--ink-muted)' }}>{driverId}</span>
                  <span style={{ color: val < 0 ? 'var(--good)' : 'var(--bad)' }}>{val > 0 ? '+' : ''}{val}s</span>
                </div>
              ))}
          </div>
        </div>
        <div className="glass rounded-2xl p-6">
          <h3 className="font-display font-semibold text-lg mb-4">Qualifying → Race Delta</h3>
          <p className="text-xs mb-3" style={{ color: 'var(--ink-faint)' }}>Positive = gains positions on race day.</p>
          <div className="space-y-2">
            {Object.entries(data.quali_race_delta)
              .filter(([, v]) => v !== 'unknown')
              .sort((a, b) => b[1] - a[1])
              .map(([driverId, val]) => (
                <div key={driverId} className="flex items-center justify-between font-mono text-xs">
                  <span style={{ color: 'var(--ink-muted)' }}>{driverId}</span>
                  <span style={{ color: val >= 0 ? 'var(--good)' : 'var(--bad)' }}>{val > 0 ? '+' : ''}{val}</span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
