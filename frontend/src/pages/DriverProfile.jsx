import { useEffect, useState } from 'react';
import { useFilters } from '../lib/FiltersContext';
import { api } from '../lib/api';
import { DriverFullBody, TeamCrest } from '../components/Identity';
import { AXES } from '../components/Viz';

export default function DriverProfile() {
  const f = useFilters();
  const [insights, setInsights] = useState(null);

  useEffect(() => { if (f.driverId) api.driverInsights(f.driverId).then(setInsights).catch(() => {}); }, [f.driverId]);

  if (!f.driver || !f.team) return null;
  const accent = f.team.accent;

  const topAxisLabel = f.driver.traits !== 'unknown'
    ? AXES.reduce((best, a) => f.driver.traits[a.key] > f.driver.traits[best.key] ? a : best, AXES[0]).label
    : null;

  return (
    <div>
      <div className="relative min-h-[560px] mb-8">
 
        <div className="absolute inset-x-0 top-10 z-0 text-center select-none pointer-events-none px-4">
          <div
            className="font-display font-bold tracking-tight uppercase"
            style={{ fontSize: 'clamp(2.5rem, 9vw, 6.5rem)', lineHeight: 0.9, color: 'var(--ink)' }}
          >
            {f.driver.name}
          </div>
        </div>

        

        {/* full body photo */}
        <div className="absolute inset-x-0 top-24 bottom-0 z-10 flex justify-center pointer-events-none">
          <DriverFullBody driver={f.driver} team={f.team} className="max-h-full" />
        </div>

        

        {/* best track card, bottom-right */}
        <div className="absolute bottom-0 right-0 z-20 w-64 glass-strong rounded-2xl p-4">
          <div className="font-mono text-[10px] uppercase tracking-wider mb-2" style={{ color: accent }}>Best predicted track</div>
          {insights && insights.best_track !== 'unknown' ? (
            <>
              <div className="font-display font-bold text-lg leading-tight">{insights.best_track.circuit.name}</div>
              <div className="font-mono text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>{insights.best_track.circuit.type} circuit</div>
              <div className="font-mono text-2xl font-bold mt-3" style={{ color: accent }}>{insights.best_track.score}<span className="text-xs" style={{ color: 'var(--ink-faint)' }}>/100</span></div>
            </>
          ) : (
            <div className="font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>unknown — no prediction yet</div>
          )}
        </div>

        {/* team badge, bottom-left */}
        <div className="absolute bottom-0 left-0 z-20 flex items-center gap-3 glass rounded-2xl p-3 pr-5">
          <TeamCrest team={f.team} size={44} />
          <div>
            <div className="font-display font-semibold text-sm">{f.team.name}</div>
            <div className="font-mono text-[10px]" style={{ color: 'var(--ink-faint)' }}>#{f.driver.num} · {f.driver.country}</div>
          </div>
        </div>
      </div>

      {/* ============ KPI BAND ============ */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="glass rounded-2xl p-6">
          <div className="font-mono text-[10px] uppercase tracking-wider mb-3" style={{ color: 'var(--ink-faint)' }}>
            Consistency {insights?.latest_consistency_season ? `· ${insights.latest_consistency_season}` : ''}
          </div>
          {insights && insights.latest_consistency !== 'unknown' ? (
            <>
              <div className="font-mono text-3xl font-bold">{insights.latest_consistency.median}</div>
              <div className="font-mono text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>
                median finish · range {insights.latest_consistency.min}–{insights.latest_consistency.max}
              </div>
            </>
          ) : <div className="font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>unknown</div>}
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="font-mono text-[10px] uppercase tracking-wider mb-3" style={{ color: 'var(--ink-faint)' }}>Tyre Degradation (avg, s/lap)</div>
          {insights && insights.avg_tyre_degradation !== 'unknown' ? (
            <div className="space-y-1.5">
              {Object.entries(insights.avg_tyre_degradation).map(([compound, val]) => (
                <div key={compound} className="flex justify-between font-mono text-xs">
                  <span style={{ color: 'var(--ink-muted)' }}>{compound}</span>
                  <span style={{ color: 'var(--ink)' }}>{val}</span>
                </div>
              ))}
            </div>
          ) : <div className="font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>unknown</div>}
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="font-mono text-[10px] uppercase tracking-wider mb-3" style={{ color: 'var(--ink-faint)' }}>Style Cluster</div>
          <div className="font-display font-bold text-lg">
            {typeof f.driver.style_cluster === 'number' ? `Cluster ${f.driver.style_cluster}` : 'unknown'}
          </div>
          <div className="font-mono text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>from KMeans on real KPI vectors</div>
        </div>
      </div>
    </div>
  );
}
