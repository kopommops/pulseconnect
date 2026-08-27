import { motion, useReducedMotion } from 'framer-motion';

// Tight spring, not an ease curve — this is what gives the "snap into place"
// feel instead of a soft CSS fade. Shared everywhere so the whole app moves
// with one consistent tempo.
export const SPRING = { type: 'spring', stiffness: 250, damping: 20, mass: 0.5 };

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: SPRING },
};

/** Wrap a group of StaggerItem children — they cascade in with a rapid,
 * rhythmic delay between each rather than all popping in at once. */
export function Stagger({ children, className, style, delay = 0, staggerMs = 0.05 }) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className} style={style}>{children}</div>;
  return (
    <motion.div
      className={className}
      style={style}
      initial="hidden"
      animate="visible"
      variants={{ hidden: {}, visible: { transition: { staggerChildren: staggerMs, delayChildren: delay } } }}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({ children, className, style }) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className} style={style}>{children}</div>;
  return (
    <motion.div className={className} style={style} variants={itemVariants}>
      {children}
    </motion.div>
  );
}

/** A stylized "assembling" reveal — a clip-path panel wipe with a light
 * sweep passing across in sync. Not a literal panel-by-panel nanobot
 * build (that's a lot of discrete pieces for the payoff); this reads as
 * "locking into place" with two moving parts instead of dozens.
 * `triggerKey` re-runs the animation when it changes (e.g. a new result). */
export function SuitReveal({ children, triggerKey, delay = 0, className }) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className}>{children}</div>;
  const EASE = [0.16, 1, 0.3, 1];
  return (
    <motion.div key={triggerKey} className={`relative overflow-hidden ${className || ''}`}>
      <motion.div
        initial={{ clipPath: 'inset(0 100% 0 0)' }}
        animate={{ clipPath: 'inset(0 0% 0 0)' }}
        transition={{ duration: 0.55, ease: EASE, delay }}
      >
        {children}
      </motion.div>
      <motion.div
        className="pointer-events-none absolute inset-y-0"
        style={{
          width: '18%',
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)',
          mixBlendMode: 'overlay',
        }}
        initial={{ left: '-20%' }}
        animate={{ left: '105%' }}
        transition={{ duration: 0.55, ease: EASE, delay }}
      />
    </motion.div>
  );
}

export function FadeIn({ children, className, style, delay = 0, y = 20, scale }) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className} style={style}>{children}</div>;
  return (
    <motion.div
      className={className}
      style={style}
      initial={{ opacity: 0, y, ...(scale ? { scale } : {}) }}
      animate={{ opacity: 1, y: 0, ...(scale ? { scale: 1 } : {}) }}
      transition={{ ...SPRING, delay }}
    >
      {children}
    </motion.div>
  );
}
