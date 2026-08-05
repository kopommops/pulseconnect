import { useState } from 'react';


export default function Media({ src, alt, fallback, className }) {
  const [failed, setFailed] = useState(false);
  if (failed || !src) return fallback;
  return (
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => setFailed(true)}
    />
  );
}
