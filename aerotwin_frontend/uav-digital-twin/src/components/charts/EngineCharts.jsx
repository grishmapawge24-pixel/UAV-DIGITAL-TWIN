import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const CHART_DEFS = [
  { key: 'rpm', label: 'Engine RPM', color: '#1f6f66', unit: 'rpm' },
  { key: 'cht', label: 'Cylinder Head (CHT)', color: '#b8860b', unit: '°C' },
  { key: 'egt', label: 'Exhaust Gas (EGT)', color: '#c1671a', unit: '°C' },
  { key: 'oilPressure', label: 'Oil Pressure', color: '#2f6690', unit: 'bar' },
  { key: 'fuelFlow', label: 'Fuel Flow', color: '#2e7d46', unit: 'L/h' },
  { key: 'vibration', label: 'Vibration', color: '#b3261e', unit: 'mm/s' }
];

function MiniChart({ def, series, xKey }) {
  const currentVal = series && series.length > 0 ? series[series.length - 1][def.key] : '—';

  return (
    <div className="panel" style={{ minHeight: 140, padding: 0 }}>
      <div className="panel-header" style={{ padding: '6px 10px', minHeight: 32 }}>
        <span className="panel-title" style={{ fontSize: 10.5, fontWeight: 700 }}>{def.label.toUpperCase()}</span>
        <span className="mono" style={{ fontSize: 12, fontWeight: 800, color: def.color }}>
          {currentVal} <span className="scalar-unit" style={{ fontSize: 9 }}>{def.unit}</span>
        </span>
      </div>
      <div style={{ flex: 1, padding: '4px 6px 2px', minHeight: 95 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={series} margin={{ top: 4, right: 8, bottom: 0, left: -24 }}>
            <defs>
              <linearGradient id={`grad-${def.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={def.color} stopOpacity={0.2} />
                <stop offset="95%" stopColor={def.color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#eef0ea" strokeDasharray="2 2" />
            <XAxis dataKey={xKey} tick={{ fill: '#8b9284', fontSize: 8 }} axisLine={{ stroke: '#d7dbcd' }} tickLine={false} />
            <YAxis tick={{ fill: '#8b9284', fontSize: 8 }} axisLine={{ stroke: '#d7dbcd' }} tickLine={false} width={32} domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{ background: '#ffffff', border: '1px solid #b7bfa8', borderRadius: 4, fontSize: 10, color: '#1a2420', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.08)', padding: '4px 8px' }}
              labelStyle={{ color: '#6d7869', fontWeight: 600 }}
            />
            <Area type="monotone" dataKey={def.key} stroke={def.color} strokeWidth={2} fill={`url(#grad-${def.key})`} dot={false} isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function EngineCharts({ series, xKey = 't', keys }) {
  const defs = keys ? CHART_DEFS.filter((d) => keys.includes(d.key)) : CHART_DEFS;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
      {defs.map((def) => (
        <MiniChart key={def.key} def={def} series={series} xKey={xKey} />
      ))}
    </div>
  );
}
