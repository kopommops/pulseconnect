import { motion } from 'framer-motion';
import { DriverFullBody } from './Identity';

const RISER_HEIGHT = { 1: 130, 2: 90, 3: 60 };
const RISER_ORDER = [2, 1, 3]; // classic ceremony left-to-right
const RANK_COLOR = { 1: '#FFD447', 2: '#C7CDD6', 3: '#D0894F' };

export default function PodiumStage({ podium, driverTeamMap }) {
  const byRank = {};
  podium.forEach((row, i) => { byRank[i + 1] = row; });

  return (
    <div className="relative flex items-end justify-center gap-3 md:gap-6 pt-14 pb-2">
      {RISER_ORDER.map((rank) => {
        const row = byRank[rank];
        if (!row) return null;
        const team = driverTeamMap[row.driver_id] || { accent: 'var(--red)', short: '' };
        const accent = team.accent || 'var(--red)';
        const h = RISER_HEIGHT[rank];
        const rankColor = RANK_COLOR[rank];
        return (
          <div key={rank} className="relative flex flex-col items-center" style={{ width: rank === 1 ? 140 : 108 }}>
            <div
              className="absolute -top-4 left-1/2 -translate-x-1/2 w-32 h-32 rounded-full pointer-events-none"
              style={{ background: `radial-gradient(circle, ${accent}38, transparent 70%)`, filter: 'blur(3px)' }}
            />
            <div className="relative z-10 h-36 md:h-44 w-full flex items-end justify-center pointer-events-none">
              <DriverFullBody driver={row.driver} team={team} className="h-full" />
            </div>
            <motion.div
              className="relative z-0 w-full rounded-t-md flex items-start justify-center pt-2"
              style={{ background: `linear-gradient(180deg, ${accent}35, ${accent}0d)`, borderTop: `2px solid ${accent}` }}
              initial={{ height: 0 }}
              animate={{ height: h }}
              transition={{ type: 'spring', stiffness: 120, damping: 18, delay: rank === 1 ? 0.2 : 0.05 }}
            >
              <div className="font-display font-bold text-3xl" style={{ color: rankColor }}>P{rank}</div>
            </motion.div>
            <div className="mt-2 text-center">
              <div className="font-display font-bold text-sm leading-tight">{row.driver.name}</div>
              <div className="font-mono text-[10px]" style={{ color: 'var(--ink-faint)' }}>{team.short}</div>
              <div className="font-mono text-[10px] mt-1" style={{ color: accent }}>{row.score}/100</div>
              <div className="font-mono text-[9px]" style={{ color: 'var(--ink-muted)' }}>
                {row.predicted_delta_s >= 0 ? '+' : ''}{row.predicted_delta_s}s
              </div>
            </div>
          </div>
        );
      })}
      <div className="absolute bottom-0 inset-x-4 h-px" style={{ background: 'var(--border-strong)' }} />
    </div>
  );
}
