import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useFilters } from '../lib/FiltersContext';
import { api } from '../lib/api';
import { DriverAvatar, TeamCrest, CircuitArt } from '../components/Identity';
import { Gauge } from '../components/Viz';
import Media from '../components/Media';
import ScrambleValue from '../components/ScrambleValue';
import FlagBand from '../components/FlagBand';
import PodiumStage from '../components/PodiumStage';
import MyPrediction from '../components/MyPrediction';
import { FadeIn, SPRING, Stagger, StaggerItem, SuitReveal } from '../components/Motion';

const TABS = ['Predictions', 'Standings', 'Car Performance', 'Strategy Sim'];
const RED = 'var(--red)';
const COMPOUND_COLORS = { SOFT: '#FF3333', MEDIUM: '#FFD400', HARD: '#EEEEEE', INTERMEDIATE: '#43B02A', WET: '#2E86D6' };

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
    api.racePredictions(season, round).then(setPredictions).catch((e) => setPredictions({ error: `Could not load predictions: ${e.message}` }));
    api.raceActual(season, round).then(setActual).catch((e) => setActual({ error: `Could not load actual results: ${e.message}` }));
    api.standings(season).then(setStandings).catch((e) => setStandings({ error: `Could not load standings: ${e.message}` }));
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

  const activeDrivers = useMemo(
    () => (roster?.teams || []).flatMap(({ drivers }) => drivers),
    [roster]
  );

  if (!nextRace) {
    return <Centered>Loading race weekend...</Centered>;
  }
  if (nextRace.error) {
    return <Centered>{nextRace.error}</Centered>;
  }

  const circuit = nextRace.circuit;

  return (
    <div className="max-w-6xl mx-auto px-5 pb-24">
      <FadeIn className="glass-strong rounded-lg p-6 md:p-8 mt-8 mb-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {circuit?.country && <FlagBand country={circuit.country} width={32} height={20} />}
            <div className="font-mono text-[10px] uppercase tracking-wider" style={{ color: RED }}>
              Round {nextRace.round}
              {nextRace.status === 'race_weekend' && ' · This weekend'}
              {nextRace.status === 'upcoming' && ' · Upcoming'}
              {nextRace.status === 'season_complete' && ' · Season complete'}
              {nextRace.format === 'sprint' && ' · Sprint format'}
            </div>
          </div>
          <h1 className="font-display font-bold text-3xl">{nextRace.event_name}</h1>
          <div className="font-mono text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>
            {circuit?.name} · {circuit?.country} · {nextRace.race_date}
          </div>
          {nextRace.source === 'seed' && (
            <div className="font-mono text-[10px] mt-2" style={{ color: 'var(--ink-faint)' }}>
              seed calendar — run the pipeline for FastF1-confirmed dates
            </div>
          )}
        </div>
        {circuit && <CircuitArt circuit={circuit} accent={RED} size={140} />}
      </FadeIn>

      <Stagger delay={0.12} className="flex gap-2 mb-6 flex-wrap">
        {TABS.map((t) => (
          <StaggerItem key={t}>
            <button
              onClick={() => setTab(t)}
              className="font-mono text-xs uppercase tracking-wider px-4 py-2 rounded-full transition-colors"
              style={{
                background: tab === t ? RED : 'var(--glass)',
                color: tab === t ? '#fff' : 'var(--ink-muted)',
              }}
            >
              {t}
            </button>
          </StaggerItem>
        ))}
      </Stagger>

      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={SPRING}
        >
          {tab === 'Predictions' && (
            <PredictionsTab
              nextRace={nextRace}
              predictions={predictions}
              actual={actual}
              driverTeamMap={driverTeamMap}
              activeDrivers={activeDrivers}
            />
          )}
          {tab === 'Standings' && <StandingsTab standings={standings} teams={f.teams} />}
          {tab === 'Car Performance' && <CarPerformanceTab roster={roster} predictions={predictions} />}
          {tab === 'Strategy Sim' && (
            <StrategyTab nextRace={nextRace} drivers={f.drivers} driverTeamMap={driverTeamMap} />
          )}
        </motion.div>
      </AnimatePresence>
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

function PredictionsTab({ nextRace, predictions, actual, driverTeamMap, activeDrivers }) {
  const [showModel, setShowModel] = useState(false);

  useEffect(() => {
    if (actual?.status === 'complete') setShowModel(true);
  }, [actual?.status]);

  if (!activeDrivers.length) return <Unknown>Loading roster...</Unknown>;

  return (
    <div className="space-y-4">
      <MyPrediction
        season={nextRace.season}
        round={nextRace.round}
        activeDrivers={activeDrivers}
        driverTeamMap={driverTeamMap}
        actual={actual}
        onResolved={() => setShowModel(true)}
      />

      {showModel && (!predictions ? (
        <Unknown>Loading predictions...</Unknown>
      ) : predictions.error ? (
        <Unknown>{predictions.error}</Unknown>
      ) : (
        <SuitReveal triggerKey={`${nextRace.season}-${nextRace.round}`} className="space-y-4">
          <div className="glass rounded-lg p-6">
            <div className="font-mono text-[10px] uppercase tracking-wider mb-2" style={{ color: RED }}>
              Predicted Podium · Compatibility model + driver clusters
            </div>
            <PodiumStage podium={predictions.podium} driverTeamMap={driverTeamMap} />
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="glass rounded-lg p-6">
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

            <ChaosIndexCard predictions={predictions} />
            <WinProbabilityCard predictions={predictions} driverTeamMap={driverTeamMap} />
          </div>
        </SuitReveal>
      ))}

      {actual && actual.status === 'complete' && (
        <div className="glass-strong rounded-lg p-6">
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

// Chaos index gets an actual explanation, not just a number under a gauge.
function ChaosIndexCard({ predictions }) {
  const scored = [...(predictions.podium || []), ...(predictions.top5 || [])]
    .filter((r, i, arr) => arr.findIndex((x) => x.driver_id === r.driver_id) === i)
    .sort((a, b) => b.score - a.score);
  const top = scored[0]?.score;
  const bottom = scored[scored.length - 1]?.score;
  const spread = top != null && bottom != null ? top - bottom : null;

  return (
    <div className="glass rounded-lg p-6">
      <div className="flex items-start justify-between gap-4 mb-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider mb-1" style={{ color: RED }}>Chaos Index</div>
          <p className="text-xs max-w-[220px]" style={{ color: 'var(--ink-muted)' }}>
            How bunched the top compatibility scores are — tighter spread, harder to call.
          </p>
        </div>
        <Gauge value={predictions.chaos_index} accent={RED} size={110} label="Chaos" />
      </div>
      {spread != null && (
        <div className="mt-3 pt-3 font-mono text-[11px] space-y-1" style={{ borderTop: '1px solid var(--border)', color: 'var(--ink-muted)' }}>
          <div>Top-8 score spread: <span style={{ color: 'var(--ink)' }}>{spread} pts</span> ({top} → {bottom})</div>
          <div style={{ color: 'var(--ink-faint)' }}>{predictions.chaos_index_basis}</div>
        </div>
      )}
    </div>
  );
}

const SOURCE_LABEL = { 'real (grid-confirmed)': 'grid-confirmed', 'real (form)': 'form' };

// Deliberately a SEPARATE ranking from the compatibility podium above —
// this is the trained podium/top-5 classifier's own order, not the
// compatibility model's. Two real signals, shown as two real signals,
// never silently blended into one.
function WinProbabilityCard({ predictions, driverTeamMap }) {
  const ranking = predictions.win_probability_ranking || [];
  return (
    <div className="glass rounded-lg p-6">
      <div className="font-mono text-[10px] uppercase tracking-wider mb-1" style={{ color: RED }}>
        Win Probability · Podium / Top-5 model
      </div>
      <p className="text-xs mb-4" style={{ color: 'var(--ink-muted)' }}>
        A separate trained classifier's own ranking — not the compatibility model above. Independent signal, can disagree.
      </p>
      {ranking.length === 0 ? (
        <Unknown>unknown — this model hasn't cleared its real-data accuracy bar yet for this round</Unknown>
      ) : (
        <div className="space-y-2">
          {ranking.map((r) => {
            const team = driverTeamMap[r.driver_id] || { accent: RED };
            return (
              <div key={r.driver_id} className="flex items-center gap-3 px-3 py-2 rounded-md" style={{ background: 'var(--glass-strong)' }}>
                <DriverAvatar driver={r.driver} team={team} size={32} />
                <div className="flex-1 min-w-0">
                  <div className="font-display font-bold text-sm truncate">{r.driver.name}</div>
                  <div className="font-mono text-[9px]" style={{ color: 'var(--ink-faint)' }}>
                    {SOURCE_LABEL[r.win_probability_source] || r.win_probability_source}
                  </div>
                </div>
                <div className="text-right font-mono text-xs">
                  {r.podium_probability != null && <div style={{ color: 'var(--ink)' }}>{Math.round(r.podium_probability * 100)}% podium</div>}
                  {r.top5_probability != null && <div style={{ color: 'var(--ink-muted)' }}>{Math.round(r.top5_probability * 100)}% top 5</div>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ------------------------------------------------------------------ Standings

function StandingsTab({ standings, teams }) {
  const [view, setView] = useState('drivers');
  if (!standings) return <Unknown>Loading standings...</Unknown>;
  if (standings.error) return <Unknown>{standings.error}</Unknown>;

  const rows = view === 'drivers' ? standings.drivers : standings.constructors;
  const top3 = rows.slice(0, 3);
  const rest = rows.slice(3);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
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

      <Stagger key={view} className="grid md:grid-cols-3 gap-4">
        {top3.map((r, i) => {
          const team = view === 'constructors' ? teams.find((t) => t.id === r.team_id) : teams.find((t) => t.drivers?.includes(r.driver_id));
          return (
            <StaggerItem key={r.driver_id || r.team_id}>
              <TopThreeCard rank={i + 1} row={r} team={team} view={view} />
            </StaggerItem>
          );
        })}
      </Stagger>

      <div className="glass rounded-lg p-4">
        <div className="space-y-1">
          {rest.map((r) => {
            const team = view === 'constructors' ? teams.find((t) => t.id === r.team_id) : null;
            return (
              <div key={r.driver_id || r.team_id} className="flex items-center gap-3 px-3 py-2.5 rounded-md" style={{ background: 'var(--glass-strong)' }}>
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
    </div>
  );
}

const RANK_COLOR = { 1: '#FFD447', 2: '#C7CDD6', 3: '#D0894F' };

function TopThreeCard({ rank, row, team, view }) {
  const accent = team?.accent || RED;
  const rankColor = RANK_COLOR[rank];
  return (
    <div
      className="rounded-md p-5 relative overflow-hidden"
      style={{ background: 'var(--glass-strong)', border: `1px solid ${rankColor}55` }}
    >
      <div
        className="absolute -top-6 -right-6 w-24 h-24 rounded-full"
        style={{ background: `radial-gradient(circle, ${rankColor}33, transparent 70%)` }}
      />
      <div className="relative flex items-center justify-between mb-3">
        <div className="font-display font-bold text-3xl" style={{ color: rankColor }}>#{rank}</div>
        {team && <TeamCrest team={team} size={30} />}
      </div>
      {view === 'drivers' ? (
        <div className="relative flex items-center gap-3">
          <DriverAvatar driver={{ id: row.driver_id, name: row.name, num: '' }} team={team || { accent }} size={44} active />
          <div className="min-w-0">
            <div className="font-display font-bold truncate">{row.name}</div>
            <div className="font-mono text-[10px]" style={{ color: 'var(--ink-faint)' }}>{row.wins}W · {row.podiums}P</div>
          </div>
        </div>
      ) : (
        <div className="relative font-display font-bold truncate">{row.name}</div>
      )}
      <div className="relative font-mono text-2xl font-bold mt-3" style={{ color: 'var(--ink)' }}>
        {row.points}<span className="text-xs" style={{ color: 'var(--ink-faint)' }}> pts</span>
      </div>
    </div>
  );
}

// -------------------------------------------------------------- Car Performance

function CarPerformanceTab({ roster, predictions }) {
  const [selected, setSelected] = useState(null);
  if (!roster) return <Unknown>Loading lineup...</Unknown>;

  const scoreByDriver = {};
  [...(predictions?.top5 || []), predictions?.pulse_pick].filter(Boolean).forEach((r) => {
    scoreByDriver[r.driver_id] = r.score;
  });

  const teamScores = roster.teams.map(({ team, drivers }) => {
    const scores = drivers.map((d) => scoreByDriver[d.id]).filter((s) => s != null);
    const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null;
    return { team, avg };
  });
  const maxAvg = Math.max(...teamScores.map((t) => t.avg || 0), 1);

  return (
    <div>
      <p className="font-mono text-[11px] mb-4" style={{ color: 'var(--ink-faint)' }}>
        Click a car to compare its predicted this-weekend fit against the rest of the grid.
      </p>
      <Stagger className="grid md:grid-cols-2 gap-4" staggerMs={0.06}>
        {roster.teams.map(({ team, drivers, source }) => {
          const isSelected = selected === team.id;
          const avg = teamScores.find((t) => t.team.id === team.id)?.avg;
          return (
            <StaggerItem key={team.id}>
              <motion.div
                layout
                onClick={() => setSelected(isSelected ? null : team.id)}
                className="glass rounded-md p-5 cursor-pointer"
                style={{ borderTop: `2px solid ${team.accent}`, outline: isSelected ? `2px solid ${team.accent}` : 'none' }}
                whileHover={{ y: -3 }}
                whileTap={{ scale: 0.98 }}
                transition={SPRING}
              >
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
                <div className="rounded-md overflow-hidden mb-3" style={{ background: '#0a0a0b' }}>
                  <Media
                    src={`/assets/cars/${team.id}.avif`}
                    alt={`${team.name} car`}
                    className="w-full h-28 object-contain p-2"
                    fallback={<div className="w-full h-28 flex items-center justify-center font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>{team.short}</div>}
                  />
                </div>

                {avg != null && (
                  <div className="mb-3">
                    <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
                      <motion.div
                        className="h-full rounded-full"
                        style={{ background: team.accent }}
                        initial={{ width: 0 }}
                        animate={{ width: `${(avg / maxAvg) * 100}%` }}
                        transition={SPRING}
                      />
                    </div>
                    <div className="font-mono text-[10px] mt-1" style={{ color: 'var(--ink-faint)' }}>
                      avg predicted fit this weekend: {avg.toFixed(0)}/100
                    </div>
                  </div>
                )}

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

                <AnimatePresence>
                  {isSelected && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={SPRING}
                      className="mt-3 pt-3 font-mono text-[11px]"
                      style={{ borderTop: '1px solid var(--border)', color: 'var(--ink-muted)' }}
                    >
                      Engine: {team.engine} · {avg != null
                        ? `ranked ${teamScores.filter((t) => (t.avg || 0) > avg).length + 1} of ${teamScores.length} on predicted fit this weekend`
                        : 'no scored driver for this weekend yet'}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </StaggerItem>
          );
        })}
      </Stagger>
    </div>
  );
}

// ------------------------------------------------------------------ Strategy

const COMPOUNDS = ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET'];

function CompoundDot({ compound, glow }) {
  const c = COMPOUND_COLORS[compound] || '#888';
  return (
    <span
      className="inline-block rounded-full mr-1.5"
      style={{ width: 8, height: 8, background: c, boxShadow: glow ? `0 0 6px ${c}` : 'none' }}
    />
  );
}

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
    setResult(null);
    api.simulateStrategy(nextRace.season, nextRace.round, {
      driver_id: driverId, circuit_id: nextRace.circuit.id, season: nextRace.season, stints,
    }).then(setResult).catch((e) => setResult({ error: e.message })).finally(() => setLoading(false));
  };

  const team = driverTeamMap[driverId];

  return (
    <div className="grid lg:grid-cols-2 gap-4">
      <div className="glass rounded-lg p-6">
        <div className="font-mono text-[10px] uppercase tracking-wider mb-4" style={{ color: RED }}>
          Tyre / Pit Strategy — What If
        </div>
        <label className="font-mono text-xs block mb-1" style={{ color: 'var(--ink-muted)' }}>Driver</label>
        <select value={driverId} onChange={(e) => setDriverId(e.target.value)}
          className="w-full mb-4 px-3 py-2 rounded-md font-mono text-sm" style={{ background: 'var(--glass-strong)', color: 'var(--ink)' }}>
          {drivers.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>

        {stints.map((s, i) => (
          <div key={i} className="flex gap-2 mb-2 items-center">
            <div className="flex-1 flex items-center px-3 py-2 rounded-md" style={{ background: 'var(--glass-strong)' }}>
              <CompoundDot compound={s.compound} />
              <select value={s.compound} onChange={(e) => updateStint(i, 'compound', e.target.value)}
                className="flex-1 bg-transparent font-mono text-xs" style={{ color: 'var(--ink)' }}>
                {COMPOUNDS.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <input type="number" min="1" value={s.laps} onChange={(e) => updateStint(i, 'laps', Number(e.target.value))}
              className="w-20 px-3 py-2 rounded-md font-mono text-xs" style={{ background: 'var(--glass-strong)', color: 'var(--ink)' }} />
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
          <motion.button onClick={run} disabled={loading} whileTap={{ scale: 0.95 }}
            className="font-mono text-[10px] uppercase px-4 py-1.5 rounded-full" style={{ background: RED, color: '#fff' }}>
            {loading ? 'Simulating...' : 'Run simulation'}
          </motion.button>
        </div>
      </div>

      <div className="glass rounded-lg p-6">
        <div className="font-mono text-[10px] uppercase tracking-wider mb-4" style={{ color: RED }}>Result</div>
        {!result && <Unknown>Run a simulation to see predicted race-time delta.</Unknown>}
        {result?.error && <Unknown>{result.error}</Unknown>}
        {result && !result.error && (
          <SuitReveal triggerKey={result.total_predicted_delta_vs_field_s + '-' + Date.now()}>
            <div className="flex items-center gap-3 mb-4">
              {team && <DriverAvatar driver={{ id: driverId, name: driverId, num: '' }} team={team} size={36} />}
              <div className="font-display font-bold text-2xl">
                <ScrambleValue value={`${result.total_predicted_delta_vs_field_s >= 0 ? '+' : ''}${result.total_predicted_delta_vs_field_s}s`} />
              </div>
              <div className="font-mono text-xs" style={{ color: 'var(--ink-muted)' }}>vs. field, {result.num_stops} stop(s)</div>
            </div>
            <div className="space-y-2 mb-4">
              {result.stints.map((s, i) => (
                <div key={i} className="flex justify-between items-center font-mono text-xs px-3 py-2 rounded-md" style={{ background: 'var(--glass-strong)' }}>
                  <span className="flex items-center"><CompoundDot compound={s.compound} glow />{s.compound} × {s.laps} laps {!s.degradation_known && '(no real deg. data)'}</span>
                  <ScrambleValue value={`${s.stint_delta_s >= 0 ? '+' : ''}${s.stint_delta_s}s`} duration={350} />
                </div>
              ))}
            </div>
            <p className="text-xs" style={{ color: 'var(--ink-faint)' }}>{result.basis}</p>
          </SuitReveal>
        )}
      </div>
    </div>
  );
}
