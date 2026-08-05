import { useEffect, useState } from 'react';
import { useFilters } from '../lib/FiltersContext';
import { api } from '../lib/api';
import { DriverAvatar } from '../components/Identity';
import { RadarChart, AXES } from '../components/Viz';
import Select from '../components/Select';

export default function HeadToHead() {
  const f = useFilters();
  const [data, setData] = useState(null);

  useEffect(() => {
    if (f.driverId && f.driverBId) {
      api.headToHead(f.driverId, f.driverBId, f.season).then(setData).catch(() => {});
    }
  }, [f.driverId, f.driverBId, f.season]);

  if (!data || data.error) return null;
  const { driver_a: a, driver_b: b } = data;
  const teamA = f.teams.find(t => t.drivers.includes(a.id));
  const teamB = f.teams.find(t => t.drivers.includes(b.id));

  const Row = ({ label, va, vb, lowerIsBetter = false }) => {
    const bothKnown = va !== 'unknown' && vb !== 'unknown';
    const aWins = bothKnown && (lowerIsBetter ? va < vb : va > vb);
    const bWins = bothKnown && (lowerIsBetter ? vb < va : vb > va);
    return (
      <div className="grid grid-cols-3 items-center py-2.5 font-mono text-sm" style={{ borderBottom: '1px solid var(--border)' }}>
        <div className="text-left" style={{ color: aWins ? teamA?.accent : 'var(--ink-muted)', fontWeight: aWins ? 700 : 400 }}>
          {va === 'unknown' ? 'unknown' : va}
        </div>
        <div className="text-center text-[10px] uppercase tracking-wider" style={{ color: 'var(--ink-faint)' }}>{label}</div>
        <div className="text-right" style={{ color: bWins ? teamB?.accent : 'var(--ink-muted)', fontWeight: bWins ? 700 : 400 }}>
          {vb === 'unknown' ? 'unknown' : vb}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="glass rounded-2xl p-4 flex justify-end">
        <Select label="Compare against" value={f.driverBId} onChange={f.setDriverBId} options={f.drivers} getLabel={d => d.name} getValue={d => d.id} />
      </div>

      <div className="glass-strong rounded-2xl p-6 md:p-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <DriverAvatar driver={a} team={teamA} size={56} active />
            <div>
              <div className="font-display font-bold text-lg">{a.name}</div>
              <div className="font-mono text-xs" style={{ color: teamA?.accent }}>{teamA?.short}</div>
            </div>
          </div>
          <div className="font-display text-2xl" style={{ color: 'var(--ink-faint)' }}>VS</div>
          <div className="flex items-center gap-3 flex-row-reverse text-right">
            <DriverAvatar driver={b} team={teamB} size={56} active />
            <div>
              <div className="font-display font-bold text-lg">{b.name}</div>
              <div className="font-mono text-xs" style={{ color: teamB?.accent }}>{teamB?.short}</div>
            </div>
          </div>
        </div>

        <Row label="Median finish" va={a.consistency !== 'unknown' ? a.consistency.median : 'unknown'} vb={b.consistency !== 'unknown' ? b.consistency.median : 'unknown'} lowerIsBetter />
        <Row label="Race pace delta (s)" va={a.race_pace} vb={b.race_pace} lowerIsBetter />

        <div className="grid md:grid-cols-2 gap-6 mt-8">
          <div className="flex flex-col items-center">
            <RadarChart driverTraits={a.traits} accent={teamA?.accent} size={240} />
          </div>
          <div className="flex flex-col items-center">
            <RadarChart driverTraits={b.traits} accent={teamB?.accent} size={240} />
          </div>
        </div>
      </div>
    </div>
  );
}
