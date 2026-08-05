import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { LogoChip } from '../components/Identity';

const NEXT_RACE = { name: 'Dutch GP', circuit: 'Circuit Zandvoort', date: 'AUG 21–23', round: 'Round 12' };


export default function Landing() {
  const [teams, setTeams] = useState([]);
  useEffect(() => { api.teams().then(d => setTeams(d.teams)).catch(() => {}); }, []);

  return (
    <div>
      {/* ============ HERO ============ */}
      <section className="relative max-w-6xl mx-auto px-5 pt-10 pb-4 overflow-hidden">
        <div className="relative min-h-[640px] md:min-h-[720px]">

          {/* pull-quote, top-left 
          <div className="absolute top-0 left-0 z-20 max-w-[280px]">
            <div className="font-display text-4xl mb-1" style={{ color: 'var(--red)' }}>&ldquo;</div>
            <p className="font-display text-lg leading-snug" style={{ color: 'var(--ink)' }}>
              Every driver has a shape. Every circuit demands one.
            </p>
            <div className="font-mono text-[10px] uppercase tracking-wider mt-2" style={{ color: 'var(--ink-faint)' }}>
              — The Compatibility Engine
            </div>
          </div>*/}

          {/* giant headline, behind/around the car */}
          <div className="absolute inset-x-0 top-16 md:top-10 z-0 text-center select-none pointer-events-none">
            <div
              className="font-display font-bold tracking-tight"
              style={{ fontSize: 'clamp(3.5rem, 11vw, 8.5rem)', lineHeight: 0.92, color: 'var(--ink)' }}
            >
              PULSE<span style={{ color: 'var(--red)' }}>CONNECT</span>
            </div>
          </div>

          {/* car render, layered above the headline */}
          <div className="absolute inset-x-0 top-32 md:top-24 z-10 flex justify-center pointer-events-none">
            <img
              src="/assets/hero/landing-car.png"
              alt="Formula 1 car, front view"
              className="w-[85%] max-w-2xl drop-shadow-[0_30px_60px_rgba(226,16,28,0.25)]"
            />
          </div>

          {/* next race card, bottom-right */}
          <div className="absolute bottom-0 right-0 z-20 w-64 glass-strong rounded-2xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-[10px] uppercase tracking-wider" style={{ color: 'var(--red)' }}>Next on the grid</span>
              <span className="font-mono text-[10px]" style={{ color: 'var(--ink-faint)' }}>{NEXT_RACE.round}</span>
            </div>
            <div className="font-display font-bold text-lg leading-tight">{NEXT_RACE.name}</div>
            <div className="font-mono text-xs mt-0.5" style={{ color: 'var(--ink-muted)' }}>{NEXT_RACE.circuit}</div>
            <div className="font-mono text-xs mt-3" style={{ color: 'var(--ink)' }}>{NEXT_RACE.date}</div>
          </div>

          {/* two small preview cards, bottom-left */}
          <div className="absolute bottom-0 left-0 z-20 flex gap-3">
            <Link to="/dashboard/compatibility" className="glass rounded-2xl p-4 w-40 hover:-translate-y-0.5 transition-transform">
              <div className="font-mono text-[9px] uppercase tracking-wider mb-2" style={{ color: 'var(--ink-faint)' }}>Compatibility</div>
              <div className="font-display font-bold text-sm">Score any driver, any circuit</div>
              <div className="font-mono text-[10px] mt-2" style={{ color: 'var(--red)' }}>Open →</div>
            </Link>
            <Link to="/dashboard/consistency" className="glass rounded-2xl p-4 w-40 hover:-translate-y-0.5 transition-transform hidden sm:block">
              <div className="font-mono text-[9px] uppercase tracking-wider mb-2" style={{ color: 'var(--ink-faint)' }}>Consistency</div>
              <div className="font-display font-bold text-sm">Season-long finish spread</div>
              <div className="font-mono text-[10px] mt-2" style={{ color: 'var(--red)' }}>Open →</div>
            </Link>
          </div>
        </div>

        <div className="flex justify-center mt-6">
          <Link to="/dashboard/profile"
            className="font-mono text-sm uppercase tracking-wider px-7 py-3 rounded-full transition-transform hover:-translate-y-0.5"
            style={{ background: 'var(--red)', color: '#fff' }}>
            Open Dashboard →
          </Link>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-5">
        {/* ============ HOW IT WORKS ============ */}
        <section id="how" className="grid md:grid-cols-2 gap-10 items-center py-20">
          <div>
            <div className="font-mono text-xs uppercase tracking-[0.25em] mb-4" style={{ color: 'var(--red)' }}>How it works</div>
            <h2 className="font-display font-bold text-3xl mb-4">Real telemetry in, a trained model out.</h2>
            <ul className="space-y-4 text-sm" style={{ color: 'var(--ink-muted)' }}>
              <li><span style={{ color: 'var(--ink)', fontWeight: 600 }}>Compatibility Engine —</span> a gradient-boosted model trained on real historical race pace scores every driver against every circuit on a six-axis technique profile.</li>
              <li><span style={{ color: 'var(--ink)', fontWeight: 600 }}>Driver Style Clustering —</span> KMeans groups the grid from real braking, tyre-degradation and qualifying-delta data.</li>
              <li><span style={{ color: 'var(--ink)', fontWeight: 600 }}>Consistency & Track DNA —</span> season-long finishing spread and per-circuit technical breakdowns, straight from FastF1 session data.</li>
            </ul>
          </div>
          <div className="flex justify-center">
            <img src="/assets/hero/landing-car-secondary.webp" alt="Formula 1 car, top-down view" className="w-full max-w-sm opacity-90" />
          </div>
        </section>

        {teams.length > 0 && (
          <section className="pb-16">
            <div className="font-mono text-xs uppercase tracking-[0.25em] text-center mb-6" style={{ color: 'var(--ink-faint)' }}>
              Full 2026 grid — {teams.length} teams, {teams.reduce((n, t) => n + t.drivers.length, 0)} drivers
            </div>
            <div className="glass rounded-2xl py-8 px-4">
              <div className="flex flex-wrap items-center justify-center gap-4">
                {teams.map((t, i) => (
                  <div key={i} className="flex flex-col items-center gap-2 w-24">
                    <LogoChip team={t} size={56} />
                    <span className="font-mono text-[10px] text-center leading-tight" style={{ color: 'var(--ink-muted)' }}>{t.short}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/*<section className="pb-24">
          <div className="font-mono text-xs uppercase tracking-[0.25em] text-center mb-6" style={{ color: 'var(--ink-faint)' }}>
            Built with
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {['React', 'FastAPI', 'FastF1', 'scikit-learn', 'pandas'].map((t, i) => (
              <span key={i} className="font-mono text-xs px-4 py-2 rounded-full glass" style={{ color: 'var(--ink-muted)' }}>{t}</span>
            ))}
          </div>
        </section>

        <footer className="text-center pb-10 font-mono text-[11px]" style={{ color: 'var(--ink-faint)' }}>
          PulseConnect v2 — real historical data via FastF1, ML predictions via scikit-learn.
        </footer>*/}
      </div>
    </div>
  );
}
