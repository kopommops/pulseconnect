export default function Select({ label, value, onChange, options, getLabel = (o) => o, getValue = (o) => o }) {
  return (
    <label className="flex flex-col gap-1.5 min-w-[150px]">
      <span className="font-mono text-[10px] uppercase tracking-wider" style={{ color: 'var(--ink-faint)' }}>{label}</span>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="font-mono text-xs rounded-lg px-3 py-2 cursor-pointer"
        style={{ background: 'var(--glass-strong)', border: '1px solid var(--border)', color: 'var(--ink)' }}>
        {options.map((o, i) => (
          <option key={i} value={getValue(o)} style={{ background: 'var(--bg-2)' }}>{getLabel(o)}</option>
        ))}
      </select>
    </label>
  );
}
