import { NavLink } from 'react-router-dom';

const SECTIONS = [
  { to: '/dashboard/profile', label: 'Profile', icon: 'profile' },
  { to: '/dashboard/compatibility', label: 'Compatibility', icon: 'target' },
  { to: '/dashboard/consistency', label: 'Consistency', icon: 'chart' },
  { to: '/dashboard/track-dna', label: 'Track DNA', icon: 'track' },
  { to: '/dashboard/head-to-head', label: 'Head to Head', icon: 'versus' },
];

const ICONS = {
  profile: <><circle cx="12" cy="8" r="4" /><path d="M4 20c0-4 4-6 8-6s8 2 8 6" /></>,
  target: <><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3" /></>,
  chart: <><path d="M4 20V10M12 20V4M20 20v-7" /></>,
  track: <><path d="M4 15 Q4 5 14 5 Q20 5 20 10 Q20 15 14 15 L8 15 Q4 15 4 19" /></>,
  versus: <><circle cx="7" cy="12" r="4" /><circle cx="17" cy="12" r="4" /></>,
};

export default function Sidebar() {
  return (
    <aside className="w-56 shrink-0 hidden lg:block">
      <div className="glass rounded-2xl p-3 sticky top-28 flex flex-col gap-1">
        {SECTIONS.map(s => (
          <NavLink key={s.to} to={s.to}
            className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 rounded-xl font-mono text-xs uppercase tracking-wider transition-colors`}
            style={({ isActive }) => ({
              background: isActive ? 'var(--red-soft)' : 'transparent',
              color: isActive ? 'var(--red)' : 'var(--ink-muted)',
            })}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">{ICONS[s.icon]}</svg>
            {s.label}
          </NavLink>
        ))}
      </div>
    </aside>
  );
}
