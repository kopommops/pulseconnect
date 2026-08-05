const AXES = [
  { key: 'braking', label: 'Braking' },
  { key: 'traction', label: 'Traction' },
  { key: 'apexSpeed', label: 'Apex Speed' },
  { key: 'tyreMgmt', label: 'Tyre Mgmt' },
  { key: 'aero', label: 'Aero Sens.' },
  { key: 'technical', label: 'Technical' },
];
export { AXES };

export function Gauge({ value, accent, size = 168, label, sub }) {
  if (value === 'unknown' || value == null) {
    return (
      <div className="flex flex-col items-center justify-center font-mono text-xs" style={{ width: size, height: size, color: 'var(--ink-faint)' }}>
        unknown — no historical data
      </div>
    );
  }
  const r = size * 0.4, stroke = size * 0.09;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value)) / 100;
  const arcFrac = 0.75;
  const dash = c * arcFrac * pct;
  return (
    <div className="flex flex-col items-center">
      <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} style={{ transform: 'rotate(135deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={stroke}
          strokeDasharray={`${c * arcFrac} ${c}`} strokeLinecap="round" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={accent} strokeWidth={stroke}
          strokeDasharray={`${dash} ${c}`} strokeLinecap="round" />
      </svg>
      <div className="-mt-[58%] text-center">
        <div className="font-mono font-bold" style={{ fontSize: size * 0.22, color: 'var(--ink)' }}>{value}</div>
        {label && <div className="font-mono uppercase tracking-wider" style={{ fontSize: size * 0.062, color: 'var(--ink-muted)' }}>{label}</div>}
      </div>
      {sub && <div className="font-mono text-[11px] mt-1" style={{ color: 'var(--ink-muted)' }}>{sub}</div>}
    </div>
  );
}

export function RadarChart({ driverTraits, circuitDemand, accent, focusKey, size = 280 }) {
  if (driverTraits === 'unknown') {
    return (
      <div className="flex items-center justify-center font-mono text-xs" style={{ width: size, height: size, color: 'var(--ink-faint)' }}>
        unknown — driver has no trait data yet
      </div>
    );
  }
  const cx = size / 2, cy = size / 2, maxR = size * 0.36;
  const n = AXES.length;
  const pt = (i, r) => {
    const angle = -Math.PI / 2 + i * (2 * Math.PI / n);
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
  };
  const ring = (frac) => AXES.map((_, i) => pt(i, maxR * frac).join(',')).join(' ');
  const poly = (getVal) => AXES.map((a, i) => pt(i, maxR * (getVal(a.key) / 100)).join(',')).join(' ');

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width="100%" height={size}>
      {[0.25, 0.5, 0.75, 1].map((f, idx) => (
        <polygon key={idx} points={ring(f)} fill="none" stroke="var(--border)" strokeWidth="1" />
      ))}
      {AXES.map((a, i) => {
        const [x, y] = pt(i, maxR);
        return <line key={a.key} x1={cx} y1={cy} x2={x} y2={y} stroke="var(--border)" strokeWidth="1" />;
      })}
      {circuitDemand && (
        <polygon points={poly(k => circuitDemand[k])} fill="none" stroke="var(--ink-muted)" strokeWidth="1.75" strokeDasharray="5,4" />
      )}
      <polygon points={poly(k => driverTraits[k])} fill={accent} fillOpacity="0.16" stroke={accent} strokeWidth="2.25" />
      {AXES.map((a, i) => {
        const [x, y] = pt(i, maxR * (driverTraits[a.key] / 100));
        return <circle key={a.key} cx={x} cy={y} r={a.key === focusKey ? 4.5 : 2.75} fill={accent} />;
      })}
      {AXES.map((a, i) => {
        const [x, y] = pt(i, maxR * 1.24);
        return (
          <text key={a.key} x={x} y={y} textAnchor="middle" dominantBaseline="middle"
            className="font-mono" fontSize="10.5"
            fill={a.key === focusKey ? accent : 'var(--ink-muted)'}
            fontWeight={a.key === focusKey ? 700 : 400}>
            {a.label}
          </text>
        );
      })}
    </svg>
  );
}


export function BoxPlot({ data, accentFor, maxScale = 22, height = 420 }) {
  const entries = Object.entries(data).filter(([, v]) => v !== 'unknown');
  const unknownCount = Object.values(data).filter(v => v === 'unknown').length;
  const sorted = entries.sort((a, b) => a[1].median - b[1].median);
  const colW = 34;
  const width = Math.max(600, sorted.length * colW + 60);
  const plotH = height - 40;
  const y = (pos) => 20 + (pos - 1) / (maxScale - 1) * plotH;

  return (
    <div className="overflow-x-auto">
      <svg width={width} height={height} className="font-mono">
        {Array.from({ length: maxScale }, (_, i) => i + 1).filter(p => p % 2 === 1).map(p => (
          <g key={p}>
            <line x1={40} y1={y(p)} x2={width} y2={y(p)} stroke="var(--border)" strokeWidth="1" />
            <text x={10} y={y(p) + 3} fontSize="9" fill="var(--ink-faint)">{p}</text>
          </g>
        ))}
        {sorted.map(([driverId, v], i) => {
          const x = 55 + i * colW;
          const accent = accentFor(driverId);
          return (
            <g key={driverId}>
              <line x1={x} y1={y(v.min)} x2={x} y2={y(v.max)} stroke={accent} strokeWidth="1.5" />
              <rect x={x - 8} y={y(v.q3)} width="16" height={Math.max(2, y(v.q1) - y(v.q3))} fill={accent} fillOpacity="0.75" rx="2" />
              <line x1={x - 8} y1={y(v.median)} x2={x + 8} y2={y(v.median)} stroke="var(--bg)" strokeWidth="2" />
              <text x={x} y={height - 8} fontSize="9.5" textAnchor="middle" fill="var(--ink-muted)">{driverId}</text>
            </g>
          );
        })}
      </svg>
      {unknownCount > 0 && (
        <div className="font-mono text-[11px] mt-2" style={{ color: 'var(--ink-faint)' }}>
          {unknownCount} driver{unknownCount > 1 ? 's' : ''} omitted — no data for this season (rookie / new entry)
        </div>
      )}
    </div>
  );
}

export function MiniBar({ value, accent, label }) {
  if (value === 'unknown' || value == null) {
    return (
      <div className="flex items-center gap-3">
        <span className="font-mono text-[11px] w-24 shrink-0" style={{ color: 'var(--ink-muted)' }}>{label}</span>
        <span className="font-mono text-[11px]" style={{ color: 'var(--ink-faint)' }}>unknown</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-3">
      <span className="font-mono text-[11px] w-24 shrink-0" style={{ color: 'var(--ink-muted)' }}>{label}</span>
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
        <div className="h-full rounded-full" style={{ width: `${value}%`, background: accent }} />
      </div>
      <span className="font-mono text-[11px] w-8 text-right" style={{ color: 'var(--ink)' }}>{value}</span>
    </div>
  );
}
