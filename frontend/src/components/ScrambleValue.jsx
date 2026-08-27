import { useEffect, useRef, useState } from 'react';

const DIGITS = '0123456789';
const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

/**
 * Displays `value` (already-formatted, e.g. "-61.48s") by cycling random
 * digits before locking onto the real characters left-to-right. The number
 * shown is always the real computed result — this only changes how it's
 * revealed, never what it says, so it stays honest while making a fast
 * backend call feel like a heavier computation just resolved.
 */
export default function ScrambleValue({ value, duration = 500, className, style }) {
  const [display, setDisplay] = useState(value);
  const frameRef = useRef(null);

  useEffect(() => {
    const target = String(value);
    if (prefersReducedMotion()) {
      setDisplay(target);
      return;
    }
    const start = performance.now();
    const isDigit = (c) => DIGITS.includes(c);

    function tick(now) {
      const progress = Math.min(1, (now - start) / duration);
      // Ease-in on the lock count so it accelerates toward the end —
      // reads as "resolving," not a flat linear countdown.
      const lockedCount = Math.floor(progress * progress * target.length);
      const next = target
        .split('')
        .map((ch, i) => (!isDigit(ch) || i < lockedCount ? ch : DIGITS[Math.floor(Math.random() * 10)]))
        .join('');
      setDisplay(next);
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      } else {
        setDisplay(target);
      }
    }
    frameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameRef.current);
  }, [value, duration]);

  return <span className={className} style={style}>{display}</span>;
}
