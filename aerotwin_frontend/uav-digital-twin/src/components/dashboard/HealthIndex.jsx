import React from 'react';
import { severityHex } from '../../utils/status.js';

function gaugeColor(value) {
  if (value >= 85) return severityHex.normal;
  if (value >= 65) return severityHex.warning;
  if (value >= 45) return severityHex.major;
  return severityHex.critical;
}

export default function HealthIndex({ value, size = 108, strokeWidth = 9 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value / 100);
  const color = gaugeColor(value);

  return (
    <div className="health-gauge-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--bg-inset)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
        <text x="50%" y="52%" textAnchor="middle" className="health-gauge-value">
          {Math.round(value)}%
        </text>
      </svg>
      <span className="health-gauge-label">ENGINE HEALTH</span>
    </div>
  );
}
