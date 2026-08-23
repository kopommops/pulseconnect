import { useEffect, useRef, useState } from 'react';

const DIGITS = '0123456789';
const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

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
