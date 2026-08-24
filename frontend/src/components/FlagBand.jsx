import { FLAG_THEMES } from '../lib/flagThemes';

export default function FlagBand({ country, width = 44, height = 28, className = '' }) {
  const theme = FLAG_THEMES[country];
  if (!theme) return null;
  const { colors, dir, bar } = theme;
  const isH = dir === 'h';

  return (
    <div
      className={`flag-wave rounded-sm overflow-hidden shrink-0 ${className}`}
      style={{ width, height, boxShadow: '0 2px 8px rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.15)' }}
      title={`${country} — host nation`}
    >
      <div className="w-full h-full flex" style={{ flexDirection: isH ? 'column' : 'row' }}>
        {bar && <div style={{ width: isH ? '100%' : '18%', height: isH ? '18%' : '100%', background: bar }} />}
        {colors.map((c, i) => (
          <div key={i} style={{ flex: 1, background: c }} />
        ))}
      </div>
    </div>
  );
}
