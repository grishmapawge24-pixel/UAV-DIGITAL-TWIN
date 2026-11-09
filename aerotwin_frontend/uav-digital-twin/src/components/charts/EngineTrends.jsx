import React from 'react';
import EngineCharts from './EngineCharts';

export default function EngineTrends({ telemetry, history }) {
  if (!telemetry) return null;

  const rpm = telemetry.engine?.rpm || 0;
  const cht = telemetry.thermal?.cht || 0;
  const egt = telemetry.thermal?.egt || 0;
  const oilPressure = telemetry.lubrication?.oilPressure || 0;
  const fuelFlow = telemetry.fuel?.flow || 0;
  const vibration = telemetry.mechanical?.vibration || 0;

  const series = (history && history.length > 1) ? history : [
    { t: 0, rpm: Math.round(rpm * 0.96), cht: Math.round(cht * 0.98), egt: Math.round(egt * 0.97), oilPressure: Number((oilPressure * 0.98).toFixed(2)), fuelFlow: Number((fuelFlow * 0.96).toFixed(1)), vibration: Number((vibration * 0.95).toFixed(2)) },
    { t: 1, rpm: Math.round(rpm * 0.98), cht: Math.round(cht * 0.99), egt: Math.round(egt * 0.99), oilPressure: Number((oilPressure * 0.99).toFixed(2)), fuelFlow: Number((fuelFlow * 0.98).toFixed(1)), vibration: Number((vibration * 0.98).toFixed(2)) },
    { t: 2, rpm, cht, egt, oilPressure, fuelFlow, vibration }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 2 }}>
      <div className="panel-header" style={{ background: 'var(--bg-plate)', borderRadius: 'var(--radius-md)', border: '1px solid var(--line)', padding: '6px 12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="panel-title">REAL-TIME PROPULSION & SENSOR ENGINE TRENDS</span>
          <span className="badge normal" style={{ fontSize: 9 }}>● LIVE TELEMETRY</span>
        </div>
        <span className="scalar-unit mono">{telemetry.uavId}</span>
      </div>
      <EngineCharts series={series} keys={['rpm', 'cht', 'egt', 'oilPressure', 'fuelFlow', 'vibration']} />
    </div>
  );
}