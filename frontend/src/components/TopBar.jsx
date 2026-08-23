import { Link, useLocation } from 'react-router-dom';

export default function TopBar({ theme, toggleTheme }) {
  const { pathname } = useLocation();
  const onDashboard = pathname.startsWith('/dashboard');
  const onRaceDay = pathname.startsWith('/race-day');
  const onHome = !onDashboard && !onRaceDay;
  return (
    <div className="sticky top-0 z-40 px-6 pt-6">
      <nav className="max-w-6xl mx-auto flex items-center justify-end gap-8">
        <div className="flex items-center gap-6">
          <Link to="/" className="font-mono text-xs uppercase tracking-wider pb-0.5 transition-colors"
            style={{
              color: onHome ? 'var(--red)' : 'var(--ink-muted)',
              borderBottom: onHome ? '1px solid var(--red)' : '1px solid transparent',
            }}>
            Home
          </Link>
          <Link to="/dashboard/profile" className="font-mono text-xs uppercase tracking-wider pb-0.5 transition-colors"
            style={{
              color: onDashboard ? 'var(--red)' : 'var(--ink-muted)',
              borderBottom: onDashboard ? '1px solid var(--red)' : '1px solid transparent',
            }}>
            Dashboard
          </Link>
          <Link to="/race-day" className="font-mono text-xs uppercase tracking-wider pb-0.5 transition-colors"
            style={{
              color: onRaceDay ? 'var(--red)' : 'var(--ink-muted)',
              borderBottom: onRaceDay ? '1px solid var(--red)' : '1px solid transparent',
            }}>
            Race Day
          </Link>
        </div>
        <button onClick={toggleTheme} aria-label="Toggle theme"
          className="w-6 h-6 flex items-center justify-center">
          {theme === 'dark' ? (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--ink-muted)" strokeWidth="2"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--ink-muted)" strokeWidth="2"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" /></svg>
          )}
        </button>
      </nav>
    </div>
  );
}