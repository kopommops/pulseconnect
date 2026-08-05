import Media from './Media';

export function LogoChip({ team, size = 56 }) {
  const fallback = (
    <div
      className="rounded-full flex items-center justify-center shrink-0 font-display font-bold"
      style={{ width: size, height: size, background: `${team.accent}22`, color: '#fff', fontSize: size * 0.3 }}
    >
      {team.short}
    </div>
  );
  return (
    <div
      className="rounded-2xl flex items-center justify-center shrink-0 p-2.5"
      style={{ width: size, height: size, background: '#0a0a0b', border: '1px solid rgba(255,255,255,0.08)' }}
    >
      <Media src={`/assets/teams/${team.id}.avif`} alt={team.name} fallback={fallback}
        className="w-full h-full object-contain" />
    </div>
  );
}

export function TeamCrest({ team, size = 40 }) {
  const fallback = (
    <div
      className="rounded-full flex items-center justify-center shrink-0 font-display font-bold"
      style={{
        width: size, height: size,
        background: `linear-gradient(155deg, ${team.accent}26, transparent 65%)`,
        border: `1px solid ${team.accent}55`,
        color: 'var(--ink)', fontSize: size * 0.3,
      }}
    >
      {team.short}
    </div>
  );
  return (
    <div style={{ width: size, height: size }} className="shrink-0">
      <Media src={`/assets/teams/${team.id}.avif`} alt={team.name} fallback={fallback}
        className="w-full h-full object-contain" />
    </div>
  );
}

export function DriverAvatar({ driver, team, size = 56, active }) {
  const fallback = (
    <div
      className="w-full h-full rounded-full flex items-center justify-center font-display font-bold"
      style={{
        background: `radial-gradient(circle at 32% 28%, ${team.accent}3a, var(--glass) 70%)`,
        border: `1.5px solid ${active ? team.accent : 'var(--border-strong)'}`,
        color: 'var(--ink)', fontSize: size * 0.32,
        boxShadow: active ? `0 0 0 4px ${team.accent}1c` : 'none',
      }}
    >
      {driver.id}
    </div>
  );
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <div className="w-full h-full rounded-full overflow-hidden">
        <Media src={`/assets/drivers/${driver.id}.webp`} alt={driver.name} fallback={fallback}
          className="w-full h-full object-cover" />
      </div>
      <div
        className="absolute -bottom-1 -right-1 rounded-full font-mono font-bold flex items-center justify-center"
        style={{
          width: size * 0.42, height: size * 0.42, fontSize: size * 0.18,
          background: 'var(--bg)', border: `1px solid ${team.accent}`, color: team.accent,
        }}
      >
        {driver.num}
      </div>
    </div>
  );
}

export function DriverFullBody({ driver, team, className }) {
  const fallback = (
    <div className={`w-full h-full flex items-end justify-center ${className || ''}`}>
      <span
        className="font-display font-bold select-none"
        style={{
          fontSize: 'clamp(6rem, 22vw, 16rem)',
          lineHeight: 0.8,
          color: 'transparent',
          WebkitTextStroke: `2px ${team.accent}55`,
        }}
      >
        {driver.id}
      </span>
    </div>
  );
  return (
    <Media src={`/assets/drivers-full/${driver.id}.avif`} alt={driver.name} fallback={fallback}
      className={`w-full h-full object-contain object-bottom ${className || ''}`} />
  );
}

export function CarCutout({ team, size = 120 }) {
  const fallback = (
    <div className="flex items-center justify-center h-full opacity-40 font-mono text-[10px]" style={{ color: 'var(--ink-faint)' }}>
      car image pending
    </div>
  );
  return (
    <div style={{ height: size }}>
      <Media src={`/assets/cars/${team.id}.avif`} alt={`${team.name} car`} fallback={fallback}
        className="w-full h-full object-contain" />
    </div>
  );
}

const FALLBACK_PATHS = {
  Power: "M40,150 L260,150 L260,90 L320,90 L320,150 L460,150 Q480,150 480,170 L480,220 Q480,240 460,240 L120,240 Q40,240 40,190 Z",
  Street: "M60,180 Q60,120 120,110 L280,90 Q340,85 350,130 Q360,170 320,180 L400,200 Q460,215 450,260 Q440,300 380,290 L160,280 Q60,270 60,220 Z",
  Balanced: "M80,140 Q60,100 110,90 L300,80 Q360,78 370,120 Q378,150 340,160 L420,175 Q470,185 455,225 Q440,260 390,250 L150,260 Q70,255 70,200 Z",
  'High-Speed': "M50,220 Q40,160 100,140 L160,100 Q190,80 220,105 L260,140 Q300,175 350,150 L410,110 Q450,85 470,130 Q485,165 450,190 L300,260 Q160,300 90,270 Q50,255 50,220 Z",
  Technical: "M60,120 L260,120 Q300,120 300,150 Q300,175 270,180 L180,190 Q150,195 155,225 Q160,255 200,255 L400,255 Q450,255 450,210 L450,150 Q450,110 400,110 L340,110",
  Mixed: "M70,130 Q160,90 250,120 Q300,135 280,175 Q265,205 300,220 L380,240 Q430,252 415,285 Q400,310 350,295 L140,270 Q60,258 65,200 Z",
};

export function CircuitArt({ circuit, accent = 'var(--red)', size = 220 }) {
  const fallback = (
    <svg viewBox="0 0 520 340" width="100%" height={size}>
      <path d={FALLBACK_PATHS[circuit.type] || FALLBACK_PATHS.Balanced} fill="none"
        stroke={accent} strokeOpacity="0.9" strokeWidth="4.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d={FALLBACK_PATHS[circuit.type] || FALLBACK_PATHS.Balanced} fill="none"
        stroke={accent} strokeOpacity="0.15" strokeWidth="14" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
  return (
    <div style={{ height: size }}>
      <Media src={`/assets/circuits/${circuit.id}.svg`} alt={circuit.name} fallback={fallback}
        className="w-full h-full object-contain" />
    </div>
  );
}
