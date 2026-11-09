import React from 'react';
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';
import HealthIndex from './HealthIndex.jsx';
import { severityHex } from '../../utils/status.js';

function TrendIcon({ trend }) {
  if (trend === 'DEGRADING' || trend === 'CRITICAL') return <TrendingDown size={12} color={severityHex.critical} />;
  if (trend === 'IMPROVING') return <TrendingUp size={12} color={severityHex.normal} />;
  return <Minus size={12} color={severityHex.offline} />;
}

function MetricBar({ label, value, invert = false }) {
  const color = invert
    ? value > 50
      ? severityHex.critical
      : value > 25
      ? severityHex.warning
      : severityHex.normal
    : value > 80
    ? severityHex.normal
    : value > 55
    ? severityHex.warning
    : severityHex.critical;

  return (
    <div className="bar-row">
      <div className="bar-row-top">
        <span className="scalar-label">{label}</span>
        <span className="mono" style={{ color }}>{value}%</span>
      </div>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  );
}

export default function MissionReliability({ health, mission }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">MISSION RELIABILITY INDEX</span>
        <span className="scalar-unit mono">{mission.missionId}</span>
      </div>
      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ flex: '0 0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <HealthIndex value={health.index} size={82} strokeWidth={7} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="scalar-row">
              <span className="scalar-label">Trend</span>
              <span className="scalar-value" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <TrendIcon trend={health.trend} /> {health.trend}
              </span>
            </div>
            <div className="scalar-row">
              <span className="scalar-label">Remaining Useful Life</span>
              <span className="mono" style={{ color: 'var(--signal)', fontWeight: 700 }}>{health.rulHours} HRS</span>
            </div>
            <div className="scalar-row">
              <span className="scalar-label">RUL Confidence</span>
              <span className="scalar-value">{health.rulConfidence}% · {health.rulTrend}</span>
            </div>
          </div>
        </div>

        <MetricBar label="Mission Health" value={mission.missionHealth} />
        <MetricBar label="Engine Reliability Index" value={mission.engineReliability} />
        <MetricBar label="Health Index" value={health.index} />
        <MetricBar label="Mission Risk" value={mission.missionRisk} invert />
        <MetricBar label="Mission Progress" value={mission.progress} />
        <div className="scalar-row" style={{ flexWrap: 'wrap', rowGap: 2 }}>
          <span className="scalar-label">Predicted Outcome</span>
          <span className="scalar-value" style={{ color: 'var(--text-primary)', fontSize: 11, textAlign: 'right' }}>
            {mission.predictedOutcome}
          </span>
        </div>
      </div>
    </div>
  );
}
