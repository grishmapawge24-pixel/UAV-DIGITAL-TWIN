import React from 'react';

export default function OfflineMap({ route, currentIndex, size = 100 }) {
  const toXY = ([x, y]) => [x * size, y * size];
  const points = route.map(toXY);
  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${p[1]}`).join(' ');
  const current = points[Math.min(currentIndex, points.length - 1)] || points[0];

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width="100%" height="100%" preserveAspectRatio="none" role="img" aria-label="Offline flight path map">
      <defs>
        <pattern id="mapGrid" width={size / 10} height={size / 10} patternUnits="userSpaceOnUse">
          <path d={`M ${size / 10} 0 L 0 0 0 ${size / 10}`} fill="none" stroke="#d7dbcd" strokeWidth="0.5" />
        </pattern>
      </defs>
      <rect width={size} height={size} fill="#f4f5ef" />
      <rect width={size} height={size} fill="url(#mapGrid)" />

      {points.length > 1 && (
        <path d={pathD} fill="none" stroke="#8b9284" strokeWidth="1" strokeDasharray="2 1.5" />
      )}
      {points.length > 1 && (
        <path
          d={points
            .slice(0, currentIndex + 1)
            .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${p[1]}`)
            .join(' ')}
          fill="none"
          stroke="#1f6f66"
          strokeWidth="1.6"
        />
      )}

      {points.map((p, i) => (
        <circle key={i} cx={p[0]} cy={p[1]} r={i === currentIndex ? 0 : 1} fill="#6d7869" />
      ))}

      {current && (
        <g transform={`translate(${current[0]}, ${current[1]})`}>
          <circle r="3.5" fill="#4b5622" opacity="0.25" />
          <circle r="1.6" fill="#4b5622" />
        </g>
      )}
    </svg>
  );
}
