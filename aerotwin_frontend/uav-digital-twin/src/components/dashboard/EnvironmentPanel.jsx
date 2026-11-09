import React from 'react';
import { Link } from 'react-router-dom';
import OfflineMap from './OfflineMap.jsx';

function EnvRow({ label, value }) {
  return (
    <div className="scalar-row">
      <span className="scalar-label">{label}</span>
      <span className="scalar-value mono" style={{ color: 'var(--text-primary)' }}>{value}</span>
    </div>
  );
}

export default function EnvironmentPanel({ environment, mechanical, flightPath }) {
  return (
    <div className="panel" style={{ flex: 1 }}>
      <div className="panel-header">
        <span className="panel-title">ATMOSPHERIC CONDITIONS</span>
      </div>
      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <EnvRow label="Altitude" value={`${environment.altitudeFt.toLocaleString()} ft`} />
        <EnvRow label="Pressure" value={`${environment.pressureKpa} kPa`} />
        <EnvRow label="Temperature" value={`${environment.temperatureC}°C`} />
        <EnvRow label="Humidity" value={`${environment.humidityPct}%`} />
        <EnvRow label="Wind" value={`${environment.windSpeedKmh} km/h`} />
        <EnvRow label="Wind Direction" value={environment.windDirection} />
        <EnvRow label="Vibration" value={`${mechanical.vibration} mm/s`} />

        <div className="category" style={{ marginTop: 8 }}>
          <div className="category-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>OFFLINE MAP</span>
            <Link to="/map-simulation" style={{ fontSize: 10, color: 'var(--ember)', textDecoration: 'none', fontWeight: 700 }}>
              FULL VIEW →
            </Link>
          </div>
          <div className="map-wrap" style={{ marginTop: 4 }}>
            <OfflineMap route={flightPath.route} currentIndex={flightPath.currentIndex} />
          </div>
        </div>
      </div>
    </div>
  );
}
