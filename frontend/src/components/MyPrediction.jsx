import { useEffect, useState } from 'react';
import { DriverAvatar } from './Identity';

const storageKey = (season, round) => `pulseconnect:my-prediction:${season}-${round}`;

export default function MyPrediction({ season, round, activeDrivers, driverTeamMap, actual, onResolved }) {
  const [saved, setSaved] = useState(undefined); // undefined = not checked yet, null = none saved
  const [skipped, setSkipped] = useState(false);
  const [picks, setPicks] = useState(['', '', '']);

  useEffect(() => {
    let record = null;
    try {
      const raw = localStorage.getItem(storageKey(season, round));
      if (raw) record = JSON.parse(raw);
    } catch { /* ignore malformed storage */ }
    setSaved(record);
    setSkipped(false);
    setPicks(['', '', '']);
  }, [season, round]);

  const raceComplete = actual?.status === 'complete';
  const resolved = saved || skipped || raceComplete;

  useEffect(() => {
    if (resolved) onResolved?.();
  }, [resolved]); // eslint-disable-line react-hooks/exhaustive-deps

  if (saved === undefined) return null; // storage not checked yet

  const submit = () => {
    if (picks.some((p) => !p) || new Set(picks).size !== 3) return;
    const record = { picks, submittedAt: new Date().toISOString() };
    try { localStorage.setItem(storageKey(season, round), JSON.stringify(record)); } catch { /* storage unavailable */ }
    setSaved(record);
  };

  const clearPick = () => {
    try { localStorage.removeItem(storageKey(season, round)); } catch { /* ignore */ }
    setSaved(null);
  };

  if (raceComplete) {
    const actualIds = actual.actual_podium.map((d) => d.id);
    const modelIds = actual.predicted_podium.map((d) => d.id);
    const yourIds = saved?.picks || null;
    const hits = (ids) => (ids ? ids.filter((id) => actualIds.includes(id)).length : null);

    return (
      <div className="glass-strong rounded-lg p-6">
        <div className="font-mono text-[10px] uppercase tracking-wider mb-4" style={{ color: 'var(--red)' }}>
          You vs. The Model vs. Reality
        </div>
        <div className="grid sm:grid-cols-3 gap-4">
          <CompareColumn title="Your call" ids={yourIds} activeDrivers={activeDrivers} hitsLabel={yourIds ? `${hits(yourIds)}/3` : null} />
          <CompareColumn title="Model" ids={modelIds} activeDrivers={activeDrivers} hitsLabel={`${hits(modelIds)}/3`} />
          <CompareColumn title="Actual" ids={actualIds} activeDrivers={activeDrivers} />
        </div>
      </div>
    );
  }

  if (saved) {
    return (
      <div className="glass rounded-lg p-4 flex items-center justify-between flex-wrap gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--ink-faint)' }}>Your podium call</div>
          <div className="flex gap-2">
            {saved.picks.map((id) => {
              const d = activeDrivers.find((x) => x.id === id);
              const team = driverTeamMap[id] || { accent: 'var(--red)' };
              return d ? <DriverAvatar key={id} driver={d} team={team} size={32} /> : null;
            })}
          </div>
        </div>
        <button onClick={clearPick} className="font-mono text-[10px] uppercase" style={{ color: 'var(--ink-faint)' }}>Edit pick</button>
      </div>
    );
  }

  if (skipped) return null; // nothing saved, model reveals below with no comparison card

  return (
    <div className="glass-strong rounded-lg p-6">
      <div className="font-mono text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--red)' }}>Your Call</div>
      <p className="text-sm mb-4" style={{ color: 'var(--ink-muted)' }}>
        Lock in your own podium before the model's prediction is revealed below.
      </p>
      <div className="grid sm:grid-cols-3 gap-2 mb-4">
        {[0, 1, 2].map((i) => (
          <select
            key={i}
            value={picks[i]}
            onChange={(e) => setPicks((p) => p.map((x, idx) => (idx === i ? e.target.value : x)))}
            className="px-3 py-2 rounded-md font-mono text-xs"
            style={{ background: 'var(--glass-strong)', color: 'var(--ink)' }}
          >
            <option value="">P{i + 1}...</option>
            {activeDrivers.map((d) => (
              <option key={d.id} value={d.id} disabled={picks.includes(d.id) && picks[i] !== d.id}>{d.name}</option>
            ))}
          </select>
        ))}
      </div>
      <div className="flex gap-2">
        <button
          onClick={submit}
          disabled={picks.some((p) => !p) || new Set(picks).size !== 3}
          className="font-mono text-[10px] uppercase px-4 py-1.5 rounded-full disabled:opacity-40"
          style={{ background: 'var(--red)', color: '#fff' }}
        >
          Lock in podium
        </button>
        <button
          onClick={() => setSkipped(true)}
          className="font-mono text-[10px] uppercase px-4 py-1.5 rounded-full"
          style={{ background: 'var(--glass-strong)', color: 'var(--ink-muted)' }}
        >
          Skip, just show me
        </button>
      </div>
    </div>
  );
}

function CompareColumn({ title, ids, activeDrivers, hitsLabel }) {
  return (
    <div className="rounded-md p-4" style={{ background: 'var(--glass-strong)' }}>
      <div className="flex items-center justify-between mb-2">
        <div className="font-mono text-[10px] uppercase" style={{ color: 'var(--ink-faint)' }}>{title}</div>
        {hitsLabel && <div className="font-mono text-[10px]" style={{ color: 'var(--ink-muted)' }}>{hitsLabel}</div>}
      </div>
      {ids ? ids.map((id, i) => {
        const d = activeDrivers.find((x) => x.id === id) || { id, name: id };
        return <div key={id + i} className="font-mono text-xs py-1">{i + 1}. {d.name}</div>;
      }) : <div className="font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>no pick made</div>}
    </div>
  );
}
