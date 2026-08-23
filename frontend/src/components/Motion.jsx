import { motion, useReducedMotion } from 'framer-motion';

export const SPRING = { type: 'spring', stiffness: 250, damping: 20, mass: 0.5 };

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: SPRING },
};

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
