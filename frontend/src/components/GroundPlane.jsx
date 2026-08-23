export default function GroundPlane({ accent = 'var(--red)', width = 560, className = '' }) {
  return (
    <div className={`pointer-events-none select-none ${className}`} style={{ width, maxWidth: '92%' }}>
      {/* contact shadow */}
      <div
        style={{
          height: 90,
          background: `radial-gradient(ellipse 55% 100% at 50% 0%, ${accent}2e, transparent 72%)`,
          filter: 'blur(1px)',
        }}
      />
      {/* isometric grid, fading toward the horizon */}
      <div
        style={{
          height: 110,
          marginTop: -60,
          backgroundImage:
            `linear-gradient(${accent}22 1px, transparent 1px), linear-gradient(90deg, ${accent}22 1px, transparent 1px)`,
          backgroundSize: '26px 26px',
          transform: 'perspective(380px) rotateX(63deg)',
          maskImage: 'linear-gradient(to bottom, black, transparent 85%)',
          WebkitMaskImage: 'linear-gradient(to bottom, black, transparent 85%)',
        }}
      />
    </div>
  );
}
