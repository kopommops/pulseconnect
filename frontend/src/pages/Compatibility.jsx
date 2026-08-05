import { useEffect, useState } from 'react';
import { useFilters } from '../lib/FiltersContext';
import { api } from '../lib/api';
import { DriverAvatar, TeamCrest, CircuitArt } from '../components/Identity';
import { Gauge, RadarChart, MiniBar, AXES } from '../components/Viz';

export default function Compatibility() {
  const f = useFilters();
  const [driverDetail, setDriverDetail] = useState(null);
  const [trackDna, setTrackDna] = useState(null);
  const [compat, setCompat] = useState(null);
  const [heat, setHeat] = useState({});

  useEffect(() => {
    if (!f.driverId) return;
    api.driver(f.driverId).then(setDriverDetail).catch(() => {});
  }, [f.driverId]);

  useEffect(() => {
    if (!f.circuit) return;
    api.trackDna(f.circuit.id).then(setTrackDna).catch(() => {});
  }, [f.circuit?.id]);

  useEffect(() => {
    if (!f.driverId || !f.circuit) return;
    api.compatibility(f.driverId, f.circuit.id).then(setCompat).catch(() => {});
  }, [f.driverId, f.circuit?.id]);

  useEffect(() => {
    if (!f.team) return;
    const load = async () => {
      const next = {};
      for (const driverId of f.team.drivers) {
        next[driverId] = {};
        for (const c of f.circuits.slice(0, 8)) {
          try { next[driverId][c.id] = await api.compatibility(driverId, c.id); } catch { next[driverId][c.id] = 'unknown'; }
        }
      }
      setHeat(next);
    };
    load();
  }, [f.team, f.circuits]);

  if (!f.driver || !f.circuit) return null;
  const accent = f.team.accent;
  const focusKey = AXES.find(a => a.label === f.metricFocus)?.key;
  const topAxis = driverDetail && driverDetail.traits !== 'unknown'
    ? AXES.reduce((best, a) => driverDetail.traits[a.key] > driverDetail.traits[best.key] ? a : best, AXES[0])
    : null;

  return (
    <div>
      <div className="grid lg:grid-cols-2 gap-4 mb-4">
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-4 mb-5">
            <DriverAvatar driver={f.driver} team={f.team} size={64} active />
            <div className="flex-1 min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-wider" style={{ color: 'var(--ink-faint)' }}>{f.team.name}</div>
              <h2 className="font-display font-bold text-2xl truncate">{f.driver.name}</h2>
              <div className="font-mono text-xs mt-0.5" style={{ color: accent }}>#{f.driver.num} · {f.driver.country}</div>
            </div>
            <TeamCrest team={f.team} size={40} />
          </div>
          <div className="space-y-2.5">
            {driverDetail && driverDetail.traits !== 'unknown'
              ? AXES.map(a => <MiniBar key={a.key} value={driverDetail.traits[a.key]} accent={accent} label={a.label} />)
              : <div className="font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>unknown — no trait data for this driver yet</div>}
          </div>
          {topAxis && (
            <div className="mt-5 pt-4 font-mono text-xs" style={{ borderTop: '1px solid var(--border)', color: 'var(--ink-muted)' }}>
              Strongest trait: <span style={{ color: 'var(--ink)' }}>{topAxis.label}</span> ({driverDetail.traits[topAxis.key]}) ·
              Style cluster: <span style={{ color: 'var(--ink)' }}>{typeof driverDetail.style_cluster === 'number' ? driverDetail.style_cluster : 'unknown'}</span>
            </div>
          )}
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-wider" style={{ color: 'var(--ink-faint)' }}>{f.circuit.country}</div>
              <h2 className="font-display font-bold text-xl leading-tight max-w-[80%]">{f.circuit.name}</h2>
            </div>
            <span className="font-mono text-[10px] uppercase px-2.5 py-1 rounded-full shrink-0" style={{ background: 'var(--glass-strong)', color: 'var(--ink-muted)' }}>{f.circuit.type}</span>
          </div>
          <CircuitArt circuit={f.circuit} accent={accent} size={210} />
          <div className="grid grid-cols-2 gap-3 mt-3 font-mono text-xs">
            <div><span style={{ color: 'var(--ink-faint)' }}>Length</span><div style={{ color: 'var(--ink)' }}>{f.circuit.length_km} km</div></div>
            <div><span style={{ color: 'var(--ink-faint)' }}>Corners</span><div style={{ color: 'var(--ink)' }}>{f.circuit.corners}</div></div>
          </div>
        </div>
      </div>

      <div className="glass-strong rounded-2xl p-6 md:p-8 mb-4">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-3 mb-6">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--red)' }}>Compatibility Engine · ML prediction</div>
            <h3 className="font-display font-bold text-2xl">{f.driver.name} → {f.circuit.name}</h3>
          </div>
          <div className="font-mono text-xs" style={{ color: 'var(--ink-muted)' }}>{f.season} · {f.session} · Focus: {f.metricFocus}</div>
        </div>
        <div className="grid lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-3 flex justify-center">
            <Gauge value={compat && typeof compat === 'object' ? compat.score : 'unknown'} accent={accent} label="Compatibility"
              sub={compat && typeof compat === 'object' ? `predicted ${compat.predicted_delta_s >= 0 ? '+' : ''}${compat.predicted_delta_s}s delta` : undefined} />
          </div>
          <div className="lg:col-span-5 flex justify-center">
            <RadarChart driverTraits={driverDetail?.traits ?? 'unknown'} circuitDemand={trackDna?.demand} accent={accent} focusKey={focusKey} size={280} />
          </div>
          <div className="lg:col-span-4 space-y-4">
            <p className="text-sm leading-relaxed" style={{ color: 'var(--ink-muted)' }}>
              {compat && typeof compat === 'object' ? (
                <>Model predicts a <span style={{ color: accent, fontWeight: 600 }}>{compat.score}/100</span> fit for
                  {' '}{f.driver.name} at {f.circuit.name}, a {f.circuit.type.toLowerCase()} circuit, trained on real
                  season race-pace data.</>
              ) : (
                <>No grounded prediction yet — this driver or circuit doesn't have enough historical data
                  (rookie, new team, or the real pipeline hasn't been run against this pairing).</>
              )}
            </p>
            <div className="flex gap-4 font-mono text-xs pt-3" style={{ borderTop: '1px solid var(--border)' }}>
              <div><div style={{ color: 'var(--ink-faint)' }}>Solid line</div><div style={{ color: 'var(--ink)' }}>Driver trait</div></div>
              <div><div style={{ color: 'var(--ink-faint)' }}>Dashed line</div><div style={{ color: 'var(--ink)' }}>Circuit demand</div></div>
            </div>
          </div>
        </div>
      </div>

      <div className="glass rounded-2xl p-6 overflow-x-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display font-bold text-lg">{f.team.name} — Cross-Circuit Cluster</h3>
          <span className="font-mono text-[10px]" style={{ color: 'var(--ink-faint)' }}>ML-predicted score, first 8 circuits</span>
        </div>
        <div className="min-w-[560px]">
          <div className="grid grid-cols-[140px_repeat(8,1fr)] gap-1.5 mb-1.5">
            <div />
            {f.circuits.slice(0, 8).map(c => (
              <div key={c.id} className="font-mono text-[9px] text-center truncate px-1" style={{ color: 'var(--ink-faint)' }} title={c.name}>{c.name.split(' ')[0]}</div>
            ))}
          </div>
          {f.team.drivers.map(driverId => {
            const d = f.drivers.find(x => x.id === driverId);
            if (!d) return null;
            return (
              <div key={driverId} className="grid grid-cols-[140px_repeat(8,1fr)] gap-1.5 mb-1.5 items-center">
                <div className="font-mono text-xs truncate pr-2" style={{ color: driverId === f.driverId ? accent : 'var(--ink-muted)', fontWeight: driverId === f.driverId ? 700 : 400 }}>{d.name}</div>
                {f.circuits.slice(0, 8).map(c => {
                  const cell = heat[driverId]?.[c.id];
                  const score = cell && typeof cell === 'object' ? cell.score : null;
                  return (
                    <button key={c.id} onClick={() => { f.setDriverId(driverId); f.setCircuitId(c.id); f.setTrackType('All'); }}
                      className="h-9 rounded-md font-mono text-[10px] flex items-center justify-center transition-transform hover:scale-105"
                      style={{
                        background: score != null ? `color-mix(in srgb, ${accent} ${Math.round(score * 0.85)}%, var(--glass-strong))` : 'var(--glass)',
                        color: score != null && score > 60 ? '#fff' : 'var(--ink-muted)',
                      }}>
                      {score ?? '—'}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
