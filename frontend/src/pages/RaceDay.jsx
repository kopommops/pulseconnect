import { useEffect, useMemo, useState } from 'react';
import { useFilters } from '../lib/FiltersContext';
import { api } from '../lib/api';
import { DriverAvatar, TeamCrest, CircuitArt } from '../components/Identity';
import { Gauge } from '../components/Viz';
import Media from '../components/Media';

const TABS = ['Predictions', 'Standings', 'Car Performance', 'Strategy Sim'];
const RED = 'var(--red)';

export default function RaceDay() {
  const f = useFilters();
  const [tab, setTab] = useState('Predictions');
  const [nextRace, setNextRace] = useState(null);
  const [roster, setRoster] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [standings, setStandings] = useState(null);
  const [actual, setActual] = useState(null);

  useEffect(() => { api.nextRace(2026).then(setNextRace).catch(() => setNextRace({ error: 'Could not reach the API.' })); }, []);

  useEffect(() => {
    if (!nextRace || nextRace.error) return;
    const { season, round } = nextRace;
    api.raceRoster(season, round).then(setRoster).catch(() => {});
    api.racePredictions(season, round).then(setPredictions).catch(() => {});
    api.raceActual(season, round).then(setActual).catch(() => {});
    api.standings(season).then(setStandings).catch(() => {});
  }, [nextRace?.season, nextRace?.round]);

  // Which team a driver is racing for THIS weekend (not the static default —
  // matters exactly when there's a swap like Lawson -> Red Bull).
  const driverTeamMap = useMemo(() => {
    const map = {};
    (roster?.teams || []).forEach(({ team, drivers }) => {
      drivers.forEach((d) => { map[d.id] = team; });
    });
    return map;
  }, [roster]);

  if (!nextRace) {
    return <Centered>Loading race weekend...</Centered>;
  }
  if (nextRace.error) {
    return <Centered>{nextRace.error}</Centered>;
  }

  const circuit = nextRace.circuit;

  return (
    <div className="max-w-6xl mx-auto px-5 pb-24">
      <div className="glass-strong rounded-2xl p-6 md:p-8 mt-8 mb-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider mb-1" style={{ color: RED }}>
            Round {nextRace.round}
            {nextRace.status === 'race_weekend' && ' · This weekend'}
            {nextRace.status === 'upcoming' && ' · Upcoming'}
            {nextRace.status === 'season_complete' && ' · Season complete'}
            {nextRace.format === 'sprint' && ' · Sprint format'}
          </div>
          <h1 className="font-display font-bold text-3xl">{nextRace.event_name}</h1>
          <div className="font-mono text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>
            {circuit?.name} · {circuit?.country} · {nextRace.race_date}
          </div>
          {nextRace.source === 'seed' && (
            <div className="font-mono text-[10px] mt-2" style={{ color: 'var(--ink-faint)' }}>
        
            </div>
          )}
        </div>
        {circuit && <CircuitArt circuit={circuit} accent={RED} size={140} />}
      </div>

      <div className="flex gap-2 mb-6 flex-wrap">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="font-mono text-xs uppercase tracking-wider px-4 py-2 rounded-full transition-colors"
            style={{
              background: tab === t ? RED : 'var(--glass)',
              color: tab === t ? '#fff' : 'var(--ink-muted)',
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'Predictions' && (
        <PredictionsTab predictions={predictions} actual={actual} driverTeamMap={driverTeamMap} />
      )}
      {tab === 'Standings' && <StandingsTab standings={standings} teams={f.teams} />}
      {tab === 'Car Performance' && <CarPerformanceTab roster={roster} predictions={predictions} />}
      {tab === 'Strategy Sim' && (
        <StrategyTab nextRace={nextRace} drivers={f.drivers} driverTeamMap={driverTeamMap} />
      )}
    </div>
  );
}

function Centered({ children }) {
  return (
    <div className="max-w-6xl mx-auto px-5 pt-24 text-center font-mono text-sm" style={{ color: 'var(--ink-muted)' }}>
      {children}
    </div>
  );
}

function Unknown({ children = 'unknown — no data for this yet' }) {
  return <div className="font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>{children}</div>;
}

// ---------------------------------------------------------------- Predictions

function PredictionsTab({ predictions, actual, driverTeamMap }) {
  if (!predictions) return <Unknown>Loading predictions...</Unknown>;
  if (predictions.error) return <Unknown>{predictions.error}</Unknown>;

  return (
    <div className="space-y-4">
      <div className="glass rounded-2xl p-6">
        <div className="font-mono text-[10px] uppercase tracking-wider mb-4" style={{ color: RED }}>
          Predicted Podium · Compatibility model + driver clusters
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {predictions.podium.map((row, i) => (
            <PodiumCard key={row.driver_id} rank={i + 1} row={row} team={driverTeamMap[row.driver_id]} />
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="glass rounded-2xl p-6">
          <div className="font-mono text-[10px] uppercase tracking-wider mb-3" style={{ color: RED }}>
            Pulse Pick — one to watch
          </div>
          {predictions.pulse_pick ? (
            <div className="flex items-center gap-4">
              <DriverAvatar driver={predictions.pulse_pick.driver} team={driverTeamMap[predictions.pulse_pick.driver_id] || { accent: RED }} size={56} active />
              <div>
                <div className="font-display font-bold text-lg">{predictions.pulse_pick.driver.name}</div>
                <div className="font-mono text-xs" style={{ color: 'var(--ink-muted)' }}>
                  {predictions.pulse_pick.score}/100 compatibility · style cluster {predictions.pulse_pick.style_cluster}
                </div>
              </div>
            </div>
          ) : <Unknown />}
        </div>

        <div className="glass rounded-2xl p-6 flex items-center justify-between">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-wider mb-1" style={{ color: RED }}>Chaos Index</div>
            <p className="text-xs max-w-[220px]" style={{ color: 'var(--ink-muted)' }}>
              How bunched the top compatibility scores are — tighter spread, harder to call.
            </p>
          </div>
          <Gauge value={predictions.chaos_index} accent={RED} size={120} label="Chaos" />
        </div>
      </div>

      {actual && actual.status === 'complete' && (
        <div className="glass-strong rounded-2xl p-6">
          <div className="font-mono text-[10px] uppercase tracking-wider mb-4" style={{ color: RED }}>
            Predicted vs. Actual — {actual.podium_accuracy_pct}% podium accuracy ({actual.podium_hits}/3)
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <div className="font-mono text-[10px] uppercase mb-2" style={{ color: 'var(--ink-faint)' }}>Predicted</div>
              {actual.predicted_podium.map((d) => <div key={d.id} className="text-sm py-1">{d.name}</div>)}
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase mb-2" style={{ color: 'var(--ink-faint)' }}>Actual</div>
              {actual.actual_podium.map((d) => <div key={d.id} className="text-sm py-1">{d.name}</div>)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PodiumCard({ rank, row, team }) {
  const accent = team?.accent || RED;
  return (
    <div className="rounded-xl p-4" style={{ background: 'var(--glass-strong)', border: `1px solid ${accent}33` }}>
      <div className="flex items-center gap-3 mb-3">
        <div className="font-display font-bold text-2xl w-8" style={{ color: accent }}>P{rank}</div>
        <DriverAvatar driver={row.driver} team={team || { accent: RED }} size={48} active />
        <div className="min-w-0">
          <div className="font-display font-bold truncate">{row.driver.name}</div>
          {team && <div className="font-mono text-[10px]" style={{ color: 'var(--ink-faint)' }}>{team.short}</div>}
        </div>
      </div>
      <div className="font-mono text-xs" style={{ color: 'var(--ink-muted)' }}>
        {row.score}/100 · {row.predicted_delta_s >= 0 ? '+' : ''}{row.predicted_delta_s}s predicted delta
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ Standings

function StandingsTab({ standings, teams }) {
  const [view, setView] = useState('drivers');
  if (!standings) return <Unknown>Loading standings...</Unknown>;
  if (standings.error) return <Unknown>{standings.error}</Unknown>;

  const rows = view === 'drivers' ? standings.drivers : standings.constructors;

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="font-mono text-[10px] uppercase tracking-wider" style={{ color: RED }}>
          {standings.season} Standings · {standings.rounds_counted} rounds counted
        </div>
        <div className="flex gap-2">
          {['drivers', 'constructors'].map((v) => (
            <button key={v} onClick={() => setView(v)}
              className="font-mono text-[10px] uppercase px-3 py-1.5 rounded-full"
              style={{ background: view === v ? RED : 'var(--glass-strong)', color: view === v ? '#fff' : 'var(--ink-muted)' }}>
              {v}
            </button>
          ))}
        </div>
      </div>
      <div className="space-y-1">
        {rows.map((r) => {
          const team = view === 'constructors' ? teams.find((t) => t.id === r.team_id) : null;
          return (
            <div key={r.driver_id || r.team_id} className="flex items-center gap-3 px-3 py-2.5 rounded-lg" style={{ background: 'var(--glass-strong)' }}>
              <div className="font-mono text-xs w-6" style={{ color: 'var(--ink-faint)' }}>{r.position}</div>
              {team && <TeamCrest team={team} size={24} />}
              <div className="flex-1 font-display font-bold text-sm truncate">{r.name}</div>
              {view === 'drivers' && (
                <div className="font-mono text-[10px]" style={{ color: 'var(--ink-muted)' }}>
                  {r.wins}W · {r.podiums}P
                </div>
              )}
              <div className="font-mono text-sm font-bold w-16 text-right">{r.points}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// -------------------------------------------------------------- Car Performance

function CarPerformanceTab({ roster, predictions }) {
  if (!roster) return <Unknown>Loading lineup...</Unknown>;

  const scoreByDriver = {};
  [...(predictions?.top5 || []), predictions?.pulse_pick].filter(Boolean).forEach((r) => {
    scoreByDriver[r.driver_id] = r.score;
  });

  return (
    <div className="grid md:grid-cols-2 gap-4">
      {roster.teams.map(({ team, drivers, source }) => (
        <div key={team.id} className="glass rounded-2xl p-5" style={{ borderTop: `2px solid ${team.accent}` }}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <TeamCrest team={team} size={28} />
              <div className="font-display font-bold text-sm">{team.name}</div>
            </div>
            {source !== 'default' && (
              <span className="font-mono text-[9px] uppercase px-2 py-0.5 rounded-full" style={{ background: `${team.accent}22`, color: team.accent }}>
                {source === 'override' ? 'Swap this weekend' : source}
              </span>
            )}
          </div>
          <div className="rounded-xl overflow-hidden mb-3" style={{ background: '#0a0a0b' }}>
            <Media
              src={`/assets/cars/${team.id}.avif`}
              alt={`${team.name} car`}
              className="w-full h-28 object-contain p-2"
              fallback={<div className="w-full h-28 flex items-center justify-center font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>{team.short}</div>}
            />
          </div>
          <div className="flex gap-4">
            {drivers.map((d) => (
              <div key={d.id} className="flex items-center gap-2">
                <DriverAvatar driver={d} team={team} size={36} />
                <div>
                  <div className="font-mono text-xs">{d.name}</div>
                  <div className="font-mono text-[10px]" style={{ color: 'var(--ink-faint)' }}>
                    {scoreByDriver[d.id] != null ? `${scoreByDriver[d.id]}/100 fit` : '—'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ------------------------------------------------------------------ Strategy

const COMPOUNDS = ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET'];

function StrategyTab({ nextRace, drivers, driverTeamMap }) {
  const [driverId, setDriverId] = useState('VER');
  const [stints, setStints] = useState([{ compound: 'MEDIUM', laps: 25 }, { compound: 'HARD', laps: 30 }]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const updateStint = (i, field, value) => {
    setStints((prev) => prev.map((s, idx) => (idx === i ? { ...s, [field]: value } : s)));
  };
  const addStint = () => setStints((prev) => [...prev, { compound: 'MEDIUM', laps: 15 }]);
  const removeStint = (i) => setStints((prev) => prev.filter((_, idx) => idx !== i));

  const run = () => {
    setLoading(true);
    api.simulateStrategy(nextRace.season, nextRace.round, {
      driver_id: driverId, circuit_id: nextRace.circuit.id, season: nextRace.season, stints,
    }).then(setResult).catch((e) => setResult({ error: e.message })).finally(() => setLoading(false));
  };

  const team = driverTeamMap[driverId];

  return (
    <div className="grid lg:grid-cols-2 gap-4">
      <div className="glass rounded-2xl p-6">
        <div className="font-mono text-[10px] uppercase tracking-wider mb-4" style={{ color: RED }}>
          Tyre / Pit Strategy — What If
        </div>
        <label className="font-mono text-xs block mb-1" style={{ color: 'var(--ink-muted)' }}>Driver</label>
        <select value={driverId} onChange={(e) => setDriverId(e.target.value)}
          className="w-full mb-4 px-3 py-2 rounded-lg font-mono text-sm" style={{ background: 'var(--glass-strong)', color: 'var(--ink)' }}>
          {drivers.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>

        {stints.map((s, i) => (
          <div key={i} className="flex gap-2 mb-2 items-center">
            <select value={s.compound} onChange={(e) => updateStint(i, 'compound', e.target.value)}
              className="flex-1 px-3 py-2 rounded-lg font-mono text-xs" style={{ background: 'var(--glass-strong)', color: 'var(--ink)' }}>
              {COMPOUNDS.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <input type="number" min="1" value={s.laps} onChange={(e) => updateStint(i, 'laps', Number(e.target.value))}
              className="w-20 px-3 py-2 rounded-lg font-mono text-xs" style={{ background: 'var(--glass-strong)', color: 'var(--ink)' }} />
            <span className="font-mono text-[10px]" style={{ color: 'var(--ink-faint)' }}>laps</span>
            {stints.length > 1 && (
              <button onClick={() => removeStint(i)} className="font-mono text-xs px-2" style={{ color: 'var(--ink-faint)' }}>✕</button>
            )}
          </div>
        ))}
        <div className="flex gap-2 mt-3">
          <button onClick={addStint} className="font-mono text-[10px] uppercase px-3 py-1.5 rounded-full" style={{ background: 'var(--glass-strong)', color: 'var(--ink-muted)' }}>
            + Add stint
          </button>
          <button onClick={run} disabled={loading} className="font-mono text-[10px] uppercase px-4 py-1.5 rounded-full" style={{ background: RED, color: '#fff' }}>
            {loading ? 'Simulating...' : 'Run simulation'}
          </button>
        </div>
      </div>

      <div className="glass rounded-2xl p-6">
        <div className="font-mono text-[10px] uppercase tracking-wider mb-4" style={{ color: RED }}>Result</div>
        {!result && <Unknown>Run a simulation to see predicted race-time delta.</Unknown>}
        {result?.error && <Unknown>{result.error}</Unknown>}
        {result && !result.error && (
          <div>
            <div className="flex items-center gap-3 mb-4">
              {team && <DriverAvatar driver={{ id: driverId, name: driverId, num: '' }} team={team} size={36} />}
              <div className="font-display font-bold text-2xl">
                {result.total_predicted_delta_vs_field_s >= 0 ? '+' : ''}{result.total_predicted_delta_vs_field_s}s
              </div>
              <div className="font-mono text-xs" style={{ color: 'var(--ink-muted)' }}>vs. field, {result.num_stops} stop(s)</div>
            </div>
            <div className="space-y-2 mb-4">
              {result.stints.map((s, i) => (
                <div key={i} className="flex justify-between font-mono text-xs px-3 py-2 rounded-lg" style={{ background: 'var(--glass-strong)' }}>
                  <span>{s.compound} × {s.laps} laps {!s.degradation_known && '(no real deg. data)'}</span>
                  <span>{s.stint_delta_s >= 0 ? '+' : ''}{s.stint_delta_s}s</span>
                </div>
              ))}
            </div>
            {/*<p className="text-xs" style={{ color: 'var(--ink-faint)' }}>{result.basis}</p>*/}
          </div>
        )}
      </div>
    </div>
  );
}
