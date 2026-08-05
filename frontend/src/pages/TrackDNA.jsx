import { useEffect, useState } from 'react';
import { useFilters } from '../lib/FiltersContext';
import { api } from '../lib/api';
import { CircuitArt } from '../components/Identity';
import { MiniBar } from '../components/Viz';

export default function TrackDNA() {
  const f = useFilters();
  const [dna, setDna] = useState(null);

  useEffect(() => { if (f.circuit) api.trackDna(f.circuit.id).then(setDna).catch(() => {}); }, [f.circuit?.id]);

  if (!f.circuit || !dna) return null;

  return (
    <div className="space-y-4">
      <div className="glass-strong rounded-2xl p-6 md:p-8">
        <div className="grid lg:grid-cols-2 gap-8 items-center">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--red)' }}>Track DNA</div>
            <h2 className="font-display font-bold text-3xl mb-2">{f.circuit.name}</h2>
            <div className="font-mono text-xs mb-6" style={{ color: 'var(--ink-muted)' }}>{f.circuit.country}</div>
            <div className="grid grid-cols-3 gap-4 font-mono text-sm">
              <div><div style={{ color: 'var(--ink-faint)' }} className="text-[10px] uppercase">Length</div>{f.circuit.length_km} km</div>
              <div><div style={{ color: 'var(--ink-faint)' }} className="text-[10px] uppercase">Corners</div>{f.circuit.corners}</div>
              <div><div style={{ color: 'var(--ink-faint)' }} className="text-[10px] uppercase">Type</div>{f.circuit.type}</div>
            </div>
            <div className="grid grid-cols-2 gap-4 font-mono text-sm mt-4 pt-4" style={{ borderTop: '1px solid var(--border)' }}>
              <div><div style={{ color: 'var(--ink-faint)' }} className="text-[10px] uppercase">Tyre wear</div>{dna.tyre_wear_index}</div>
              <div><div style={{ color: 'var(--ink-faint)' }} className="text-[10px] uppercase">Avg pit stops</div>{dna.avg_pit_stops}</div>
            </div>
          </div>
          <CircuitArt circuit={f.circuit} accent={f.team?.accent} size={240} />
        </div>
      </div>

      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display font-semibold text-lg">Best Recorded Sectors</h3>
          
        </div>
        <div className="grid grid-cols-3 gap-3">
          {['s1', 's2', 's3'].map((key, i) => {
            const driverId = dna.best_sector_holders?.[key];
            const driver = f.drivers.find(d => d.id === driverId);
            return (
              <div key={key} className="rounded-xl p-3 text-center" style={{ background: 'var(--glass-strong)' }}>
                <div className="font-mono text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--ink-faint)' }}>Sector {i + 1}</div>
                <div className="font-display font-bold">{driver?.name || driverId}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="glass rounded-2xl p-6">
        <h3 className="font-display font-semibold text-lg mb-1">Technical Demand Profile</h3>
        <p className="text-sm mb-5" style={{ color: 'var(--ink-muted)' }}>
          What this circuit rewards, on the same six-axis scale used by the compatibility engine.
        </p>
        <div className="space-y-2.5 max-w-md">
          {Object.entries(dna.demand).map(([key, value]) => (
            <MiniBar key={key} value={value} accent={f.team?.accent || 'var(--red)'} label={key} />
          ))}
        </div>
      </div>

      <div className="glass rounded-2xl p-6">
        <h3 className="font-display font-semibold text-lg mb-3">All Circuits — Track Type</h3>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-2">
          {f.circuits.map(c => (
            <button key={c.id} onClick={() => { f.setCircuitId(c.id); f.setTrackType('All'); }}
              className="text-left rounded-xl p-3 transition-colors"
              style={{
                background: c.id === f.circuit.id ? 'var(--red-soft)' : 'var(--glass)',
                border: `1px solid ${c.id === f.circuit.id ? 'var(--red)' : 'var(--border)'}`,
              }}>
              <div className="font-mono text-xs font-semibold truncate" style={{ color: 'var(--ink)' }}>{c.name}</div>
              <div className="font-mono text-[10px] mt-0.5" style={{ color: 'var(--ink-faint)' }}>{c.type} · {c.corners} corners</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
